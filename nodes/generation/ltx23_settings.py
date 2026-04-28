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
                "frames": ("INT", {"default": 97, "min": 9, "max": 241, "step": 8}),
                "fps": ("INT", {"default": 24, "min": 1, "max": 60, "step": 1}),
                "checkpoint_name": (checkpoints, {"default": checkpoints[0]}),
                "distilled_lora_name": (loras, {"default": loras[0]}),
                "text_encoder_name": (text_encoders, {"default": text_encoders[0]}),
                "upscale_model_name": (upscalers, {"default": upscalers[0]}),
            },
        }

    def settings(
        self,
        width,
        height,
        frames,
        fps,
        checkpoint_name,
        distilled_lora_name,
        text_encoder_name,
        upscale_model_name,
    ):
        width, height = normalize_dimensions(width, height, 32)
        frames = nearest_valid_frame_count(frames)
        fps = max(1, int(fps))
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
