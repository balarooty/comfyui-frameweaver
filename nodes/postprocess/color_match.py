"""FW_ColorMatch — LAB color-space matching with VRAM-safe batching.

Aligns the color statistics (mean + std) of input frames to a reference
image using CIE-LAB color space. This preserves luminance structure while
transferring the reference's color palette.

Ported from VRGameDevGirl's ``ColorMatchToReference`` with improvements:
- Graceful kornia fallback (pure-torch LAB conversion when kornia is missing)
- Configurable batch_size to prevent OOM on long videos
- Optional ``match_luminance`` toggle to preserve or transfer brightness
"""

import torch
import torch.nn.functional as F

try:
    import comfy.model_management
    _get_device = comfy.model_management.get_torch_device
    _intermediate = comfy.model_management.intermediate_device
except ImportError:
    _get_device = lambda: torch.device("cuda" if torch.cuda.is_available() else "cpu")
    _intermediate = lambda: torch.device("cpu")

# Try kornia first, fall back to manual LAB conversion
try:
    import kornia.color
    _HAS_KORNIA = True
except ImportError:
    _HAS_KORNIA = False


def _rgb_to_lab_manual(rgb):
    """Pure-torch sRGB→LAB (D65 illuminant). Input/output: [N, 3, H, W]."""
    # Linearize sRGB
    linear = torch.where(rgb > 0.04045, ((rgb + 0.055) / 1.055) ** 2.4, rgb / 12.92)
    r, g, b = linear[:, 0:1], linear[:, 1:2], linear[:, 2:3]

    # sRGB → XYZ (D65)
    x = 0.4124564 * r + 0.3575761 * g + 0.1804375 * b
    y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b
    z = 0.0193339 * r + 0.1191920 * g + 0.9503041 * b

    # Normalize by D65 white point
    x, y, z = x / 0.95047, y / 1.0, z / 1.08883

    def _f(t):
        delta = 6.0 / 29.0
        return torch.where(t > delta ** 3, t ** (1.0 / 3.0), t / (3.0 * delta ** 2) + 4.0 / 29.0)

    fx, fy, fz = _f(x), _f(y), _f(z)
    L = 116.0 * fy - 16.0
    a = 500.0 * (fx - fy)
    b_ch = 200.0 * (fy - fz)
    return torch.cat([L, a, b_ch], dim=1)


def _lab_to_rgb_manual(lab):
    """Pure-torch LAB→sRGB (D65 illuminant). Input/output: [N, 3, H, W]."""
    L, a, b_ch = lab[:, 0:1], lab[:, 1:2], lab[:, 2:3]
    fy = (L + 16.0) / 116.0
    fx = a / 500.0 + fy
    fz = fy - b_ch / 200.0

    delta = 6.0 / 29.0

    def _inv_f(t):
        return torch.where(t > delta, t ** 3, 3.0 * delta ** 2 * (t - 4.0 / 29.0))

    x = 0.95047 * _inv_f(fx)
    y = 1.0 * _inv_f(fy)
    z = 1.08883 * _inv_f(fz)

    # XYZ → linear sRGB
    r = 3.2404542 * x - 1.5371385 * y - 0.4985314 * z
    g = -0.9692660 * x + 1.8760108 * y + 0.0415560 * z
    b = 0.0556434 * x - 0.2040259 * y + 1.0572252 * z

    rgb = torch.cat([r, g, b], dim=1).clamp(0, 1)
    # Gamma encode
    return torch.where(rgb > 0.0031308, 1.055 * rgb ** (1.0 / 2.4) - 0.055, 12.92 * rgb)


def _to_lab(rgb_nchw):
    if _HAS_KORNIA:
        return kornia.color.rgb_to_lab(rgb_nchw)
    return _rgb_to_lab_manual(rgb_nchw)


def _to_rgb(lab_nchw):
    if _HAS_KORNIA:
        return kornia.color.lab_to_rgb(lab_nchw)
    return _lab_to_rgb_manual(lab_nchw)


class FW_ColorMatch:
    """Match the color palette of video frames to a reference image using LAB statistics."""

    CATEGORY = "FrameWeaver/PostProcess"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "match_color"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE", {"tooltip": "Video frames to color-match [N, H, W, C]."}),
                "reference_image": ("IMAGE", {"tooltip": "Reference image whose color palette to adopt."}),
                "match_strength": ("FLOAT", {
                    "default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01,
                    "tooltip": "Blend between original (0) and fully matched (1).",
                }),
                "match_luminance": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "If True, also match brightness (L channel). If False, only match color (a, b channels).",
                }),
                "batch_size": ("INT", {
                    "default": 4, "min": 1, "max": 500, "step": 1,
                    "tooltip": "Process this many frames at once to avoid VRAM overflow.",
                }),
            },
        }

    def match_color(self, images, reference_image, match_strength, match_luminance, batch_size):
        device = _get_device()

        # NHWC → NCHW for color conversion
        ref = reference_image.permute(0, 3, 1, 2).to(device)

        with torch.no_grad():
            ref_lab = _to_lab(ref)
            ref_mean = ref_lab.mean(dim=[2, 3], keepdim=True)
            ref_std = ref_lab.std(dim=[2, 3], keepdim=True) + 1e-5

        images_nchw = images.permute(0, 3, 1, 2)  # stays on CPU
        outputs = []

        with torch.no_grad():
            for i in range(0, images_nchw.shape[0], batch_size):
                batch = images_nchw[i:i + batch_size].to(device)

                img_lab = _to_lab(batch)
                img_mean = img_lab.mean(dim=[2, 3], keepdim=True)
                img_std = img_lab.std(dim=[2, 3], keepdim=True) + 1e-5

                matched_lab = (img_lab - img_mean) / img_std * ref_std + ref_mean

                if not match_luminance:
                    # Keep original luminance, only transfer chrominance
                    matched_lab[:, 0:1] = img_lab[:, 0:1]

                blended_lab = match_strength * matched_lab + (1.0 - match_strength) * img_lab
                output = _to_rgb(blended_lab)
                outputs.append(output.cpu())

                del batch, img_lab, matched_lab, blended_lab, output
                torch.cuda.empty_cache()

        result = torch.cat(outputs, dim=0).clamp(0.0, 1.0)
        result = result.permute(0, 2, 3, 1)  # NCHW → NHWC
        return (result.to(_intermediate()),)
