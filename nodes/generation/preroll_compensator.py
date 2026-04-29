"""FW_PrerollCompensator — Frame padding for LTX generation continuity.

LTX 2.3 has two empirical issues with frame boundaries:
1. **Preroll loss:** The first few frames tend to be low-quality or repeat
   the conditioning image. Adding 6 extra frames at the start and trimming
   them after generation produces cleaner openings.
2. **Tail loss:** The last 7-8 frames tend to degrade or freeze. Adding 8
   extra frames at the end and trimming them produces cleaner endings.

This node calculates the over-generation frame count (with 8n+1 enforcement)
and provides the trim offsets to apply after VAE decoding.

Ported from VRGameDevGirl's ``add_preroll_frames`` + tail-loss logic.
"""

try:
    from ...utils.validation import nearest_valid_frame_count
except ImportError:
    from utils.validation import nearest_valid_frame_count


# Empirically tested values for LTX 2.3
_DEFAULT_PREROLL = 6
_DEFAULT_TAIL_LOSS = 8


class FW_PrerollCompensator:
    """Calculate over-generation frame count and trim offsets for LTX 2.3.

    Usage flow:
    1. Connect ``frames_for_generation`` to the LTX video latent init node
    2. After VAE decoding, connect the decoded frames + this node's offsets
       to ``FW_FrameTrimmer`` to extract the clean segment

    For scene index 0 (first scene), no preroll is added since there's no
    preceding scene to blend with.
    """

    CATEGORY = "FrameWeaver/Generation"

    RETURN_TYPES = ("INT", "INT", "INT", "INT", "INT")
    RETURN_NAMES = (
        "frames_for_generation",
        "target_frames",
        "preroll_frames",
        "tail_loss_frames",
        "trim_start",
    )
    FUNCTION = "compensate"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "target_frames": ("INT", {
                    "default": 97, "min": 9, "max": 241, "step": 8,
                    "tooltip": "Desired output frame count (the 'clean' frames you actually want).",
                }),
                "scene_index": ("INT", {
                    "default": 0, "min": 0,
                    "tooltip": "0-based scene index. Scene 0 skips preroll (no preceding scene).",
                }),
                "preroll_frames": ("INT", {
                    "default": _DEFAULT_PREROLL, "min": 0, "max": 32, "step": 1,
                    "tooltip": "Extra frames to prepend for temporal warm-up (trimmed after generation).",
                }),
                "tail_loss_frames": ("INT", {
                    "default": _DEFAULT_TAIL_LOSS, "min": 0, "max": 32, "step": 1,
                    "tooltip": "Extra frames to append to compensate for LTX tail degradation.",
                }),
            },
        }

    def compensate(self, target_frames, scene_index, preroll_frames, tail_loss_frames):
        target_frames = nearest_valid_frame_count(target_frames)

        # First scene: no preroll (there's nothing to blend from)
        actual_preroll = preroll_frames if scene_index > 0 else 0

        # Calculate total frames to generate
        raw_gen_frames = target_frames + actual_preroll + tail_loss_frames

        # Enforce 8n+1 on the generation frame count
        gen_frames = nearest_valid_frame_count(raw_gen_frames)

        # Recalculate actual tail padding to match the enforced count
        # gen_frames = target_frames + actual_preroll + actual_tail
        # actual_tail = gen_frames - target_frames - actual_preroll
        actual_tail = gen_frames - target_frames - actual_preroll

        # trim_start = how many frames to skip from the beginning of the decoded output
        trim_start = actual_preroll

        return (
            gen_frames,          # Pass this to latent init / LTX settings
            target_frames,       # The clean frame count you'll end up with
            actual_preroll,      # Actual preroll applied (0 for scene 0)
            actual_tail,         # Actual tail padding applied
            trim_start,          # Skip this many frames when trimming
        )


class FW_FrameTrimmer:
    """Trim preroll and tail-loss frames from decoded video output.

    Takes the raw decoded frames and removes the extra frames that were
    added by FW_PrerollCompensator for generation stability.
    """

    CATEGORY = "FrameWeaver/Generation"

    RETURN_TYPES = ("IMAGE", "INT")
    RETURN_NAMES = ("trimmed_frames", "frame_count")
    FUNCTION = "trim"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE", {"tooltip": "Raw decoded video frames from VAE."}),
                "trim_start": ("INT", {
                    "default": 0, "min": 0,
                    "tooltip": "Number of frames to remove from the start (preroll).",
                }),
                "target_frames": ("INT", {
                    "default": 97, "min": 1,
                    "tooltip": "How many frames to keep after trimming.",
                }),
            },
        }

    def trim(self, images, trim_start, target_frames):
        total = images.shape[0]
        start = min(trim_start, total)
        end = min(start + target_frames, total)

        trimmed = images[start:end]

        # If we somehow ended up with fewer frames than requested, log it
        actual_count = trimmed.shape[0]
        if actual_count < target_frames:
            print(f"[FW_FrameTrimmer] Warning: requested {target_frames} frames but only got {actual_count} after trimming (total was {total}, trim_start={trim_start})")

        return (trimmed, actual_count)
