from utils.validation import normalize_dimensions


class FW_LoadStarterFrame:
    CATEGORY = "FrameWeaver/Input"
    RETURN_TYPES = ("IMAGE", "INT", "INT")
    RETURN_NAMES = ("image", "width", "height")
    FUNCTION = "prepare"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "target_width": ("INT", {"default": 1280, "min": 64, "max": 4096, "step": 32}),
                "target_height": ("INT", {"default": 720, "min": 64, "max": 4096, "step": 32}),
            }
        }

    def prepare(self, image, target_width, target_height):
        width, height = normalize_dimensions(target_width, target_height, 32)
        try:
            import torch.nn.functional as F

            if int(image.shape[1]) == height and int(image.shape[2]) == width:
                return (image, width, height)
            channels_first = image.movedim(-1, 1)
            resized = F.interpolate(channels_first, size=(height, width), mode="bilinear", align_corners=False)
            return (resized.movedim(1, -1).clamp(0.0, 1.0), width, height)
        except Exception:
            return (image, width, height)
