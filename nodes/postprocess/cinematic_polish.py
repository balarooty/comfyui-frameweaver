"""FW_CinematicPolish — Unified sharpening with 3 kernel modes.

Combines Unsharp Mask, Laplacian, and Sobel edge enhancement into a
single node with GPU and CPU dual-path execution.

Ported from VRGameDevGirl's ``FastUnsharpSharpen``, ``FastLaplacianSharpen``,
and ``FastSobelSharpen`` — consolidated into one node for cleaner workflows.
"""

import torch
import torch.nn.functional as F
import numpy as np

try:
    import comfy.model_management
    _get_device = comfy.model_management.get_torch_device
    _intermediate = comfy.model_management.intermediate_device
except ImportError:
    _get_device = lambda: torch.device("cuda" if torch.cuda.is_available() else "cpu")
    _intermediate = lambda: torch.device("cpu")


class FW_CinematicPolish:
    """Apply sharpening to video frames using one of three kernel modes."""

    CATEGORY = "FrameWeaver/PostProcess"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "sharpen"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE", {"tooltip": "Video frames [N, H, W, C]."}),
                "mode": (["unsharp", "laplacian", "sobel"], {
                    "default": "unsharp",
                    "tooltip": "Sharpening algorithm. Unsharp=subtle, Laplacian=edges, Sobel=strong edges.",
                }),
                "strength": ("FLOAT", {
                    "default": 0.5, "min": 0.0, "max": 2.0, "step": 0.01,
                    "tooltip": "Sharpening intensity. 0.3-0.7 is generally cinematic.",
                }),
                "use_gpu": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Use GPU for processing. Disable for CPU-only systems.",
                }),
            },
        }

    def sharpen(self, images, mode, strength, use_gpu):
        if mode == "unsharp":
            return self._unsharp(images, strength, use_gpu)
        elif mode == "laplacian":
            return self._laplacian(images, strength, use_gpu)
        else:
            return self._sobel(images, strength, use_gpu)

    # ------------------------------------------------------------------ #
    #  Unsharp Mask
    # ------------------------------------------------------------------ #

    def _unsharp(self, images, strength, use_gpu):
        if use_gpu:
            device = _get_device()
            x = images.to(device).permute(0, 3, 1, 2)  # NHWC → NCHW
            blur = F.avg_pool2d(x, kernel_size=3, stride=1, padding=1)
            out = (x + strength * (x - blur)).clamp(0.0, 1.0)
            return (out.permute(0, 2, 3, 1).to(_intermediate()),)

        # CPU path
        img = images.cpu().contiguous().numpy()
        p = np.pad(img, ((0, 0), (1, 1), (1, 1), (0, 0)), mode="edge")
        blur = (
            p[:, 0:-2, 0:-2] + p[:, 0:-2, 1:-1] + p[:, 0:-2, 2:] +
            p[:, 1:-1, 0:-2] + p[:, 1:-1, 1:-1] + p[:, 1:-1, 2:] +
            p[:, 2:, 0:-2]   + p[:, 2:, 1:-1]   + p[:, 2:, 2:]
        ) / 9.0
        out = np.clip(img + strength * (img - blur), 0.0, 1.0)
        return (torch.from_numpy(out),)

    # ------------------------------------------------------------------ #
    #  Laplacian
    # ------------------------------------------------------------------ #

    def _laplacian(self, images, strength, use_gpu):
        if use_gpu:
            device = _get_device()
            x = images.to(device).permute(0, 3, 1, 2)
            kernel = torch.tensor(
                [[0, -1, 0], [-1, 4, -1], [0, -1, 0]],
                dtype=torch.float32, device=device,
            ).expand(3, 1, 3, 3)
            edges = F.conv2d(x, kernel, padding=1, groups=3)
            out = (x + strength * edges).clamp(0.0, 1.0)
            return (out.permute(0, 2, 3, 1).to(_intermediate()),)

        # CPU path
        img = images.cpu().contiguous().numpy()
        p = np.pad(img, ((0, 0), (1, 1), (1, 1), (0, 0)), mode="edge")
        lap = (
            p[:, 1:-1, 0:-2] + p[:, 0:-2, 1:-1] +
            p[:, 2:, 1:-1]   + p[:, 1:-1, 2:] -
            4.0 * img
        )
        out = np.clip(img + strength * lap, 0.0, 1.0)
        return (torch.from_numpy(out),)

    # ------------------------------------------------------------------ #
    #  Sobel
    # ------------------------------------------------------------------ #

    def _sobel(self, images, strength, use_gpu):
        if use_gpu:
            device = _get_device()
            x = images.to(device).permute(0, 3, 1, 2)
            sobel_x = torch.tensor(
                [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]],
                dtype=torch.float32, device=device,
            ).expand(3, 1, 3, 3)
            sobel_y = torch.tensor(
                [[-1, -2, -1], [0, 0, 0], [1, 2, 1]],
                dtype=torch.float32, device=device,
            ).expand(3, 1, 3, 3)
            gx = F.conv2d(x, sobel_x, padding=1, groups=3)
            gy = F.conv2d(x, sobel_y, padding=1, groups=3)
            edges = torch.sqrt(gx * gx + gy * gy + 1e-6)
            out = (x + strength * edges).clamp(0.0, 1.0)
            return (out.permute(0, 2, 3, 1).to(_intermediate()),)

        # CPU path
        img = images.cpu().contiguous().numpy()
        p = np.pad(img, ((0, 0), (1, 1), (1, 1), (0, 0)), mode="edge")
        gx = (
            -p[:, 0:-2, 0:-2] - 2 * p[:, 1:-1, 0:-2] - p[:, 2:, 0:-2] +
             p[:, 0:-2, 2:]   + 2 * p[:, 1:-1, 2:]   + p[:, 2:, 2:]
        )
        gy = (
            -p[:, 0:-2, 0:-2] - 2 * p[:, 0:-2, 1:-1] - p[:, 0:-2, 2:] +
             p[:, 2:, 0:-2]   + 2 * p[:, 2:, 1:-1]   + p[:, 2:, 2:]
        )
        edges = np.sqrt(gx * gx + gy * gy)
        out = np.clip(img + strength * edges, 0.0, 1.0)
        return (torch.from_numpy(out),)
