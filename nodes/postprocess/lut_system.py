"""FW_LUTApply — 3D LUT application with trilinear interpolation.
FW_LUTCreate — Generate 3D LUT from hex color palette.

Supports standard ``.cube`` files and palette-based LUT generation.

Ported from VRGameDevGirl's LUT system with FrameWeaver conventions:
- Pure-torch trilinear interpolation (no external deps)
- VRAM-safe batching for long video sequences
- Strength blending for subtle color grading
"""

import os
import torch
import numpy as np

try:
    import comfy.model_management
    _get_device = comfy.model_management.get_torch_device
    _intermediate = comfy.model_management.intermediate_device
except ImportError:
    _get_device = lambda: torch.device("cuda" if torch.cuda.is_available() else "cpu")
    _intermediate = lambda: torch.device("cpu")

try:
    import folder_paths
    _LUTS_DIR = os.path.join(folder_paths.models_dir, "luts")
except ImportError:
    _LUTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "models", "luts")


# ====================================================================== #
#  .cube Parser
# ====================================================================== #

def _parse_cube_file(filepath):
    """Parse a .cube LUT file and return a 3D tensor [size, size, size, 3]."""
    size = None
    data = []

    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.upper().startswith("TITLE"):
                continue
            if line.upper().startswith("DOMAIN_MIN"):
                continue
            if line.upper().startswith("DOMAIN_MAX"):
                continue
            if line.upper().startswith("LUT_3D_SIZE"):
                size = int(line.split()[-1])
                continue

            parts = line.split()
            if len(parts) >= 3:
                try:
                    data.append([float(parts[0]), float(parts[1]), float(parts[2])])
                except ValueError:
                    continue

    if size is None:
        # Try to infer size from data count
        n = len(data)
        size = round(n ** (1.0 / 3.0))
        if size ** 3 != n:
            raise ValueError(f"Cannot determine LUT size from {n} entries")

    expected = size ** 3
    if len(data) != expected:
        raise ValueError(f"Expected {expected} entries for LUT size {size}, got {len(data)}")

    lut = np.array(data, dtype=np.float32).reshape(size, size, size, 3)
    return torch.from_numpy(lut), size


def _list_lut_files():
    """List all .cube files in the LUTs directory."""
    if not os.path.isdir(_LUTS_DIR):
        return ["No LUT files found"]
    files = sorted(
        [f for f in os.listdir(_LUTS_DIR) if f.lower().endswith((".cube", ".3dl"))],
        key=str.lower,
    )
    return files if files else ["No LUT files found"]


# ====================================================================== #
#  Trilinear 3D LUT Interpolation
# ====================================================================== #

def _apply_lut_trilinear(images, lut, strength=1.0, device=None):
    """Apply a 3D LUT to images using trilinear interpolation.

    Args:
        images: [N, H, W, 3] tensor, values in [0, 1]
        lut: [S, S, S, 3] tensor
        strength: blend factor (0 = original, 1 = fully graded)
        device: target device
    """
    if device is None:
        device = images.device

    lut = lut.to(device)
    original = images

    S = lut.shape[0]
    scale = float(S - 1)

    # Flatten spatial dims for vectorized indexing
    N, H, W, C = images.shape
    flat = images.reshape(-1, 3)  # [N*H*W, 3]

    # Scale to LUT coordinates
    coords = flat * scale

    # Floor and ceil indices
    lo = coords.long().clamp(0, S - 2)
    hi = (lo + 1).clamp(0, S - 1)
    frac = coords - lo.float()

    r0, g0, b0 = lo[:, 0], lo[:, 1], lo[:, 2]
    r1, g1, b1 = hi[:, 0], hi[:, 1], hi[:, 2]
    fr, fg, fb = frac[:, 0:1], frac[:, 1:2], frac[:, 2:3]

    # Trilinear interpolation (8 corners)
    c000 = lut[r0, g0, b0]
    c001 = lut[r0, g0, b1]
    c010 = lut[r0, g1, b0]
    c011 = lut[r0, g1, b1]
    c100 = lut[r1, g0, b0]
    c101 = lut[r1, g0, b1]
    c110 = lut[r1, g1, b0]
    c111 = lut[r1, g1, b1]

    c00 = c000 * (1 - fb) + c001 * fb
    c01 = c010 * (1 - fb) + c011 * fb
    c10 = c100 * (1 - fb) + c101 * fb
    c11 = c110 * (1 - fb) + c111 * fb

    c0 = c00 * (1 - fg) + c01 * fg
    c1 = c10 * (1 - fg) + c11 * fg

    result = c0 * (1 - fr) + c1 * fr
    result = result.reshape(N, H, W, 3).clamp(0.0, 1.0)

    # Blend with original
    if strength < 1.0:
        result = strength * result + (1.0 - strength) * original

    return result


# ====================================================================== #
#  Palette → LUT Generator
# ====================================================================== #

_NAMED_COLORS = {
    "red": "ff0000", "green": "00ff00", "blue": "0000ff",
    "cyan": "00ffff", "magenta": "ff00ff", "yellow": "ffff00",
    "white": "ffffff", "black": "000000", "orange": "ff8800",
    "purple": "8800ff", "pink": "ff88cc", "teal": "008888",
    "gold": "ffd700", "silver": "c0c0c0", "coral": "ff7f50",
    "navy": "000080", "olive": "808000", "maroon": "800000",
}


def _parse_hex(token):
    """Parse a hex color string to [R, G, B] in [0, 1]."""
    token = token.strip().lower()
    if token in _NAMED_COLORS:
        token = _NAMED_COLORS[token]
    if token.startswith("#"):
        token = token[1:]
    if len(token) == 3:
        token = "".join(c * 2 for c in token)
    if len(token) != 6:
        raise ValueError(f"Invalid color: '{token}'")
    return np.array([
        int(token[0:2], 16) / 255.0,
        int(token[2:4], 16) / 255.0,
        int(token[4:6], 16) / 255.0,
    ], dtype=np.float32)


def _build_palette_lut(colors_text, lut_size=32):
    """Build a 3D LUT from a comma-separated color palette."""
    parts = [p.strip() for p in colors_text.split(",") if p.strip()]
    if not parts:
        raise ValueError("Provide at least one color (e.g. '#ff8800, #3344ff').")

    palette = np.stack([_parse_hex(p) for p in parts], axis=0)  # [K, 3]
    S = int(lut_size)

    axis = np.linspace(0.0, 1.0, S, dtype=np.float32)
    b_grid, g_grid, r_grid = np.meshgrid(axis, axis, axis, indexing="ij")
    source = np.stack([r_grid, g_grid, b_grid], axis=-1)  # [S, S, S, 3]

    # Luminance of source
    luma = 0.2126 * source[..., 0] + 0.7152 * source[..., 1] + 0.0722 * source[..., 2]

    # Interpolate palette along luminance
    if palette.shape[0] == 1:
        target = np.broadcast_to(palette[0], source.shape).copy()
    else:
        positions = np.linspace(0.0, 1.0, palette.shape[0], dtype=np.float32)
        flat_luma = luma.ravel()
        target = np.stack(
            [np.interp(flat_luma, positions, palette[:, c]) for c in range(3)],
            axis=-1,
        ).reshape(source.shape).astype(np.float32)

    # Preserve luminance structure
    target_luma = 0.2126 * target[..., 0] + 0.7152 * target[..., 1] + 0.0722 * target[..., 2]
    scale = luma / np.maximum(target_luma, 1e-6)
    target = np.clip(target * scale[..., None], 0.0, 1.0)

    # Blend: 82% graded + 18% original chroma
    source_chroma = source - luma[..., None]
    output = np.clip(target * 0.82 + (target + source_chroma) * 0.18, 0.0, 1.0)

    return torch.from_numpy(output.astype(np.float32))


# ====================================================================== #
#  Nodes
# ====================================================================== #

class FW_LUTApply:
    """Load and apply a .cube 3D LUT to video frames."""

    CATEGORY = "FrameWeaver/PostProcess"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "apply_lut"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE", {"tooltip": "Video frames [N, H, W, C]."}),
                "lut_file": (_list_lut_files(), {
                    "tooltip": "Select a .cube LUT file from the models/luts directory.",
                }),
                "strength": ("FLOAT", {
                    "default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01,
                    "tooltip": "Blend between original (0) and fully graded (1).",
                }),
                "batch_size": ("INT", {
                    "default": 8, "min": 1, "max": 500, "step": 1,
                    "tooltip": "Frames per GPU batch.",
                }),
            },
        }

    def apply_lut(self, images, lut_file, strength, batch_size):
        if lut_file == "No LUT files found":
            print("[FW_LUTApply] No LUT file selected. Passing through.")
            return (images,)

        lut_path = os.path.join(_LUTS_DIR, lut_file)
        if not os.path.exists(lut_path):
            print(f"[FW_LUTApply] LUT file not found: {lut_path}")
            return (images,)

        lut, lut_size = _parse_cube_file(lut_path)
        device = _get_device()

        outputs = []
        for i in range(0, images.shape[0], batch_size):
            batch = images[i:i + batch_size].to(device)
            graded = _apply_lut_trilinear(batch, lut, strength, device)
            outputs.append(graded.cpu())
            del batch, graded
            torch.cuda.empty_cache()

        result = torch.cat(outputs, dim=0)
        return (result.to(_intermediate()),)


class FW_LUTCreate:
    """Generate a 3D LUT from a hex color palette and optionally save as .cube."""

    CATEGORY = "FrameWeaver/PostProcess"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "create_and_apply"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE", {"tooltip": "Video frames to grade [N, H, W, C]."}),
                "colors": ("STRING", {
                    "default": "#1a1a2e, #16213e, #0f3460, #e94560",
                    "multiline": False,
                    "tooltip": "Comma-separated hex colors or named colors. Maps shadows→highlights.",
                }),
                "lut_size": ("INT", {
                    "default": 32, "min": 8, "max": 64, "step": 1,
                    "tooltip": "Resolution of the generated LUT cube (32 is standard).",
                }),
                "strength": ("FLOAT", {
                    "default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01,
                }),
                "batch_size": ("INT", {
                    "default": 8, "min": 1, "max": 500, "step": 1,
                }),
            },
            "optional": {
                "save_filename": ("STRING", {
                    "default": "",
                    "tooltip": "If non-empty, saves the generated LUT as a .cube file to models/luts/.",
                }),
            },
        }

    def create_and_apply(self, images, colors, lut_size, strength, batch_size, save_filename=""):
        lut = _build_palette_lut(colors, lut_size)
        device = _get_device()

        # Optionally save to disk
        if save_filename and save_filename.strip():
            self._save_cube(lut, lut_size, save_filename.strip())

        outputs = []
        for i in range(0, images.shape[0], batch_size):
            batch = images[i:i + batch_size].to(device)
            graded = _apply_lut_trilinear(batch, lut, strength, device)
            outputs.append(graded.cpu())
            del batch, graded
            torch.cuda.empty_cache()

        result = torch.cat(outputs, dim=0)
        return (result.to(_intermediate()),)

    def _save_cube(self, lut, lut_size, filename):
        """Save the generated LUT as a .cube file."""
        os.makedirs(_LUTS_DIR, exist_ok=True)
        if not filename.endswith(".cube"):
            filename += ".cube"
        filepath = os.path.join(_LUTS_DIR, filename)

        S = int(lut_size)
        lut_np = lut.numpy()

        with open(filepath, "w") as f:
            f.write(f"# Generated by FrameWeaver\n")
            f.write(f"TITLE \"{filename}\"\n")
            f.write(f"LUT_3D_SIZE {S}\n")
            f.write(f"DOMAIN_MIN 0.0 0.0 0.0\n")
            f.write(f"DOMAIN_MAX 1.0 1.0 1.0\n\n")
            for r in range(S):
                for g in range(S):
                    for b in range(S):
                        f.write(f"{lut_np[r, g, b, 0]:.6f} {lut_np[r, g, b, 1]:.6f} {lut_np[r, g, b, 2]:.6f}\n")

        print(f"[FW_LUTCreate] Saved LUT to {filepath}")
