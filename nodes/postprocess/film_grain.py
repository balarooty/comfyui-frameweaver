"""FW_FilmGrain — Lightweight cinematic film grain with VRAM-safe batching.

Adds photographic grain with channel-weighted noise (heavier on red/blue)
and a saturation mix control for monochromatic vs. chromatic grain.

Ported from VRGameDevGirl's ``FastFilmGrain`` with FrameWeaver conventions.
"""

import torch

try:
    import comfy.model_management
    _get_device = comfy.model_management.get_torch_device
    _intermediate = comfy.model_management.intermediate_device
except ImportError:
    _get_device = lambda: torch.device("cuda" if torch.cuda.is_available() else "cpu")
    _intermediate = lambda: torch.device("cpu")


class FW_FilmGrain:
    """Add controllable cinematic film grain to video frames."""

    CATEGORY = "FrameWeaver/PostProcess"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "apply_grain"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE", {"tooltip": "Video frames [N, H, W, C]."}),
                "grain_intensity": ("FLOAT", {
                    "default": 0.04, "min": 0.001, "max": 1.0, "step": 0.001,
                    "tooltip": "Overall grain strength. 0.02-0.06 is subtle cinematic, 0.1+ is heavy.",
                }),
                "saturation_mix": ("FLOAT", {
                    "default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01,
                    "tooltip": "0.0 = pure monochrome grain (classic B&W film). 1.0 = full color grain.",
                }),
                "batch_size": ("INT", {
                    "default": 8, "min": 1, "max": 500, "step": 1,
                    "tooltip": "Frames per GPU batch. Lower = less VRAM, slower.",
                }),
            },
        }

    def apply_grain(self, images, grain_intensity, saturation_mix, batch_size):
        device = _get_device()
        images = images.to(device)

        outputs = []
        for i in range(0, images.shape[0], batch_size):
            batch = images[i:i + batch_size]

            # Generate random noise matching the frame dimensions
            grain = torch.randn_like(batch)

            # Channel weighting — red and blue channels get more grain
            # (mimics the uneven silver halide response of analog film)
            grain[:, :, :, 0] *= 2.0  # red
            grain[:, :, :, 2] *= 3.0  # blue

            # Saturation mix: blend between per-channel grain and monochrome grain
            gray_grain = grain[:, :, :, 1:2].expand_as(grain)
            grain = saturation_mix * grain + (1.0 - saturation_mix) * gray_grain

            output = (batch + grain * grain_intensity).clamp(0.0, 1.0)
            outputs.append(output)

        result = torch.cat(outputs, dim=0)
        return (result.to(_intermediate()),)
