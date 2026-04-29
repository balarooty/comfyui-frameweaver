try:
    from ...utils.validation import nearest_valid_frame_count, normalize_dimensions
except ImportError:
    from utils.validation import nearest_valid_frame_count, normalize_dimensions


class FW_GlobalSequencer:
    """Central parameter hub that synchronizes FPS, resolution,
    scene count, and current scene index across all FrameWeaver nodes.

    Design notes
    ------------
    * This node acts as a single source of truth — connect its outputs to
      every downstream node that needs FPS, width/height, or the current
      scene index.
    * The JS companion (``web/fw_sequencer_sync.js``) broadcasts widget
      changes to all connected FrameWeaver nodes in real-time so the UI
      stays in sync *before* execution.
    * ``total_duration_seconds`` is computed from ``scene_count * frames_per_scene / fps``.
    * ``frames_per_scene`` is always enforced to 8n+1 for LTX 2.3 compatibility.
    """

    CATEGORY = "FrameWeaver/Sequencing"

    RETURN_TYPES = ("INT", "INT", "INT", "INT", "INT", "INT", "FLOAT", "FLOAT")
    RETURN_NAMES = (
        "width",
        "height",
        "frames_per_scene",
        "fps",
        "scene_count",
        "current_scene",
        "scene_duration_seconds",
        "total_duration_seconds",
    )
    FUNCTION = "sync"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "width": ("INT", {
                    "default": 1280, "min": 64, "max": 4096, "step": 32,
                    "tooltip": "Output width (will be floored to multiple of 32).",
                }),
                "height": ("INT", {
                    "default": 720, "min": 64, "max": 4096, "step": 32,
                    "tooltip": "Output height (will be floored to multiple of 32).",
                }),
                "frames_per_scene": ("INT", {
                    "default": 97, "min": 9, "max": 241, "step": 8,
                    "tooltip": "Frames per scene. Auto-adjusted to 8n+1 for LTX 2.3.",
                }),
                "fps": ("INT", {
                    "default": 24, "min": 1, "max": 120, "step": 1,
                }),
                "scene_count": ("INT", {
                    "default": 3, "min": 1, "max": 50, "step": 1,
                    "tooltip": "Total number of scenes in the project.",
                }),
                "current_scene": ("INT", {
                    "default": 1, "min": 1, "max": 50, "step": 1,
                    "tooltip": "Which scene is currently being generated (1-indexed).",
                }),
            },
            "optional": {
                "override_frames": ("INT", {
                    "forceInput": True,
                    "tooltip": "If connected (e.g. from SpeechLengthCalc), overrides frames_per_scene.",
                }),
            },
        }

    def sync(self, width, height, frames_per_scene, fps, scene_count, current_scene, override_frames=None):
        width, height = normalize_dimensions(width, height, 32)
        fps = max(1, int(fps))
        scene_count = max(1, int(scene_count))
        current_scene = max(1, min(current_scene, scene_count))

        # Override frames if connected (e.g. from FW_SpeechLengthCalc)
        if override_frames is not None and int(override_frames) > 0:
            frames_per_scene = int(override_frames)

        frames_per_scene = nearest_valid_frame_count(frames_per_scene)

        scene_duration = frames_per_scene / fps
        total_duration = scene_count * scene_duration

        return (
            width,
            height,
            frames_per_scene,
            fps,
            scene_count,
            current_scene,
            round(scene_duration, 4),
            round(total_duration, 4),
        )
