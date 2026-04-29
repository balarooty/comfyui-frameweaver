import os
import torch
import torch.nn.functional as F
import numpy as np
from PIL import Image, ImageOps

try:
    import folder_paths
except ImportError:
    folder_paths = None

try:
    import comfy.utils as comfy_utils
except ImportError:
    comfy_utils = None

try:
    from ...utils.validation import floor_to_multiple
except ImportError:
    from utils.validation import floor_to_multiple


_MAX_IMAGES = 50
_MAX_RESOLUTION = 8192


class FW_MultiImageLoader:
    """Load multiple images from file paths with advanced resize, compression,
    and a batched multi_output for downstream sequencer nodes.

    Ported from WhatDreamsCost's MultiImageLoader with improvements:
    - Uses FrameWeaver's ``floor_to_multiple`` for alignment
    - Adds ``lanczos`` resize via ``comfy.utils`` when available
    - Provides both a batched ``multi_output`` and 50 individual outputs
    """

    CATEGORY = "FrameWeaver/Input"

    RETURN_TYPES = ("IMAGE",) * (_MAX_IMAGES + 1)
    RETURN_NAMES = ("multi_output",) + tuple(f"image_{i + 1}" for i in range(_MAX_IMAGES))

    FUNCTION = "load_images"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image_paths": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "One image path per line. Absolute or relative to ComfyUI input directory.",
                }),
                "width": ("INT", {"default": 0, "min": 0, "max": _MAX_RESOLUTION, "step": 1}),
                "height": ("INT", {"default": 0, "min": 0, "max": _MAX_RESOLUTION, "step": 1}),
                "interpolation": (
                    ["lanczos", "nearest", "bilinear", "bicubic", "area", "nearest-exact"],
                    {"default": "lanczos"},
                ),
                "resize_method": (
                    ["keep proportion", "stretch", "pad", "crop"],
                    {"default": "keep proportion"},
                ),
                "multiple_of": ("INT", {
                    "default": 32, "min": 0, "max": 512, "step": 1,
                    "tooltip": "Round final dimensions down to this multiple (0 = disabled). 32 for LTX compatibility.",
                }),
                "img_compression": ("INT", {
                    "default": 0, "min": 0, "max": 100, "step": 1,
                    "tooltip": "JPEG re-compression (0 = disabled). Useful for reducing VRAM on detailed source images.",
                }),
            },
        }

    # ------------------------------------------------------------------ #
    #  Resize
    # ------------------------------------------------------------------ #

    def _resize_image(self, image, width, height, resize_method, interpolation, multiple_of):
        """Resize a single image tensor [1, H, W, C] using the chosen method."""
        _, oh, ow, _ = image.shape
        x = y = x2 = y2 = 0
        pad_left = pad_right = pad_top = pad_bottom = 0

        if multiple_of > 1:
            width = width - (width % multiple_of) if width > 0 else width
            height = height - (height % multiple_of) if height > 0 else height

        if resize_method in ("keep proportion", "pad"):
            if width == 0 and oh < height:
                width = _MAX_RESOLUTION
            elif width == 0:
                width = ow
            if height == 0 and ow < width:
                height = _MAX_RESOLUTION
            elif height == 0:
                height = oh

            ratio = min(width / ow, height / oh)
            new_width = round(ow * ratio)
            new_height = round(oh * ratio)

            if resize_method == "pad":
                pad_left = (width - new_width) // 2
                pad_right = width - new_width - pad_left
                pad_top = (height - new_height) // 2
                pad_bottom = height - new_height - pad_top

            width = new_width
            height = new_height

        elif resize_method == "crop":
            width = width if width > 0 else ow
            height = height if height > 0 else oh
            ratio = max(width / ow, height / oh)
            new_width = round(ow * ratio)
            new_height = round(oh * ratio)
            x = (new_width - width) // 2
            y = (new_height - height) // 2
            x2 = x + width
            y2 = y + height
            if x2 > new_width:
                x -= x2 - new_width
            if x < 0:
                x = 0
            if y2 > new_height:
                y -= y2 - new_height
            if y < 0:
                y = 0
            width = new_width
            height = new_height
        else:
            # stretch
            width = width if width > 0 else ow
            height = height if height > 0 else oh

        # Apply resize
        outputs = image.permute(0, 3, 1, 2)  # NHWC → NCHW
        if interpolation == "lanczos" and comfy_utils is not None:
            outputs = comfy_utils.lanczos(outputs, width, height)
        else:
            mode = interpolation if interpolation != "lanczos" else "bilinear"
            outputs = F.interpolate(outputs, size=(height, width), mode=mode)

        # Apply padding
        if resize_method == "pad" and (pad_left > 0 or pad_right > 0 or pad_top > 0 or pad_bottom > 0):
            outputs = F.pad(outputs, (pad_left, pad_right, pad_top, pad_bottom), value=0)

        outputs = outputs.permute(0, 2, 3, 1)  # NCHW → NHWC

        # Apply crop
        if resize_method == "crop" and (x > 0 or y > 0 or x2 > 0 or y2 > 0):
            outputs = outputs[:, y:y2, x:x2, :]

        # Enforce multiple_of alignment on the final output
        if multiple_of > 1:
            final_h, final_w = outputs.shape[1], outputs.shape[2]
            if final_w % multiple_of != 0 or final_h % multiple_of != 0:
                trim_x = (final_w % multiple_of) // 2
                trim_y = (final_h % multiple_of) // 2
                trim_x2 = final_w - ((final_w % multiple_of) - trim_x)
                trim_y2 = final_h - ((final_h % multiple_of) - trim_y)
                outputs = outputs[:, trim_y:trim_y2, trim_x:trim_x2, :]

        return torch.clamp(outputs, 0, 1)

    # ------------------------------------------------------------------ #
    #  Main
    # ------------------------------------------------------------------ #

    def load_images(self, image_paths, width, height, interpolation, resize_method, multiple_of, img_compression):
        results = []
        valid_paths = [p.strip() for p in image_paths.split("\n") if p.strip()]

        for path in valid_paths:
            try:
                full_path = path
                if not os.path.exists(full_path) and folder_paths is not None:
                    full_path = os.path.join(folder_paths.get_input_directory(), path)

                if not os.path.exists(full_path):
                    print(f"[FW_MultiImageLoader] Warning: Image not found: {path}")
                    continue

                image = Image.open(full_path)
                image = ImageOps.exif_transpose(image)
                image = image.convert("RGB")

                image_np = np.array(image).astype(np.float32) / 255.0
                image_tensor = torch.from_numpy(image_np)[None,]  # [1, H, W, C]

                # Resize
                image_tensor = self._resize_image(
                    image_tensor, width, height, resize_method, interpolation, multiple_of
                )

                # Optional JPEG compression (reduces high-frequency noise before generation)
                if img_compression > 0:
                    import io as _io
                    img_np = (image_tensor[0].numpy() * 255).clip(0, 255).astype(np.uint8)
                    img_pil = Image.fromarray(img_np)
                    buf = _io.BytesIO()
                    img_pil.save(buf, format="JPEG", quality=max(1, 100 - img_compression))
                    img_pil = Image.open(buf)
                    image_tensor = torch.from_numpy(
                        np.array(img_pil).astype(np.float32) / 255.0
                    )[None,]

                results.append(image_tensor)
            except Exception as exc:
                print(f"[FW_MultiImageLoader] Error loading {path}: {exc}")

        # Build batched output
        if results:
            first_shape = results[0].shape
            all_same = all(r.shape == first_shape for r in results)
            if all_same:
                multi_output = torch.cat(results, dim=0)
            else:
                print("[FW_MultiImageLoader] Warning: images have different sizes after resize; cannot batch. Individual outputs still work.")
                multi_output = torch.zeros((1, 64, 64, 3))
        else:
            multi_output = torch.zeros((1, 64, 64, 3))
            results = [multi_output]

        # Pad individual outputs to exactly 50 slots
        placeholder = torch.zeros((1, 64, 64, 3))
        padded = results + [placeholder] * (_MAX_IMAGES - len(results))

        return (multi_output, *padded[:_MAX_IMAGES])
