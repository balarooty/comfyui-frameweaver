try:
    import folder_paths as _fp

    def _ls(folder, fallback=""):
        try:
            files = _fp.get_filename_list(folder)
            return files if files else [fallback]
        except Exception:
            return [fallback]

except ImportError:
    def _ls(_folder, fallback=""):
        return [fallback]

try:
    from ...utils.validation import nearest_valid_frame_count, normalize_dimensions
except ImportError:
    from utils.validation import nearest_valid_frame_count, normalize_dimensions


class FW_LTX23Settings:
    """Central settings node for LTX 2.3 video generation.

    Enhancements in v3:
    - ``duration_mode``: choose between specifying frames directly or seconds
      (seconds are auto-converted to frames using FPS, then 8n+1 enforced)
    - ``duration_seconds``: visible when duration_mode='seconds'
    - Accepts optional ``override_frames`` from upstream nodes (e.g. SpeechLengthCalc,
      GlobalSequencer) which takes priority over the widget value
    - Outputs both ``frames`` and ``duration_seconds`` for downstream flexibility
    """

    CATEGORY = "FrameWeaver/Generation"
    RETURN_TYPES = ("INT", "INT", "INT", "INT", "FLOAT", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = (
        "width",
        "height",
        "frames",
        "fps",
        "duration_seconds",
        "checkpoint_name",
        "distilled_lora_name",
        "text_encoder_name",
        "upscale_model_name",
    )
    FUNCTION = "settings"

    @classmethod
    def INPUT_TYPES(cls):
        checkpoints = _ls("checkpoints", "ltx-2.3-22b-dev-fp8.safetensors")
        loras = _ls("loras", "ltx-2.3-22b-distilled-lora-384.safetensors")
        text_encoders = _ls("text_encoders", "gemma_3_12B_it_fp4_mixed.safetensors")
        upscalers = _ls("latent_upscale_models", "ltx-2.3-spatial-upscaler-x2-1.1.safetensors")

        return {
            "required": {
                "width": ("INT", {"default": 1280, "min": 64, "max": 4096, "step": 32}),
                "height": ("INT", {"default": 720, "min": 64, "max": 4096, "step": 32}),
                "duration_mode": (["frames", "seconds"], {
                    "default": "frames",
                    "tooltip": "Choose whether to specify duration as a frame count or in seconds.",
                }),
                "frames": ("INT", {
                    "default": 97, "min": 9, "max": 241, "step": 8,
                    "tooltip": "Frame count (used when duration_mode='frames'). Auto-adjusted to 8n+1.",
                }),
                "duration_seconds": ("FLOAT", {
                    "default": 4.0, "min": 0.1, "max": 30.0, "step": 0.1,
                    "tooltip": "Duration in seconds (used when duration_mode='seconds'). Converted to frames using FPS.",
                }),
                "fps": ("INT", {"default": 24, "min": 1, "max": 60, "step": 1}),
                "checkpoint_name": (checkpoints, {"default": checkpoints[0]}),
                "distilled_lora_name": (loras, {"default": loras[0]}),
                "text_encoder_name": (text_encoders, {"default": text_encoders[0]}),
                "upscale_model_name": (upscalers, {"default": upscalers[0]}),
            },
            "optional": {
                "override_frames": ("INT", {
                    "forceInput": True,
                    "tooltip": "If connected (e.g. from GlobalSequencer or SpeechLengthCalc), overrides the frame count.",
                }),
            },
        }

    def settings(
        self,
        width,
        height,
        duration_mode,
        frames,
        duration_seconds,
        fps,
        checkpoint_name,
        distilled_lora_name,
        text_encoder_name,
        upscale_model_name,
        override_frames=None,
    ):
        width, height = normalize_dimensions(width, height, 32)
        fps = max(1, int(fps))

        # Priority: override_frames > duration_mode calculation
        if override_frames is not None and int(override_frames) > 0:
            frames = int(override_frames)
        elif duration_mode == "seconds":
            # Convert seconds to frames, then enforce 8n+1
            raw_frames = int(round(duration_seconds * fps))
            frames = raw_frames
        # else: use the frames widget value directly

        frames = nearest_valid_frame_count(frames)
        duration = frames / fps

        return (
            width,
            height,
            frames,
            fps,
            float(duration),
            checkpoint_name,
            distilled_lora_name,
            text_encoder_name,
            upscale_model_name,
        )
