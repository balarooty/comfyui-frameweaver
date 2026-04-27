try:
    from ...utils.validation import nearest_valid_frame_count, normalize_dimensions
except ImportError:
    from utils.validation import nearest_valid_frame_count, normalize_dimensions


class FW_LatentVideoInit:
    CATEGORY = "FrameWeaver/Generation"
    RETURN_TYPES = ("LATENT", "INT", "INT", "INT")
    RETURN_NAMES = ("latent", "width", "height", "frames")
    FUNCTION = "create"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "width": ("INT", {"default": 768, "min": 64, "max": 4096, "step": 32}),
                "height": ("INT", {"default": 512, "min": 64, "max": 4096, "step": 32}),
                "frames": ("INT", {"default": 97, "min": 9, "max": 241, "step": 8}),
                "batch_size": ("INT", {"default": 1, "min": 1, "max": 16, "step": 1}),
            }
        }

    def create(self, width, height, frames, batch_size):
        width, height = normalize_dimensions(width, height, 32)
        frames = nearest_valid_frame_count(frames)
        try:
            import torch

            samples = torch.zeros((int(batch_size), frames, 4, height // 8, width // 8))
        except Exception:
            samples = None
        return ({"samples": samples, "frameweaver_shape": [batch_size, frames, 4, height // 8, width // 8]}, width, height, frames)
