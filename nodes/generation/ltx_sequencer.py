"""FW_LTXSequencer — Multi-guide keyframe injector for LTX 2.3 video latents.

Ported from WhatDreamsCost's ``LTXKeyframer`` with FrameWeaver conventions:
- Accepts up to 50 images via ``multi_input`` (from FW_MultiImageLoader)
- Per-image ``insert_frame`` + ``strength`` via kwargs
- ``insert_mode``: seconds or frames toggle
- Negative frame indexing (e.g. -1 = last frame)
- Proper ``noise_mask`` management for FFLF (First Frame / Last Frame) workflows
- Falls back gracefully when ``comfy.utils`` is not available
"""

try:
    import torch
except ImportError:
    torch = None

try:
    import comfy.utils as comfy_utils
except ImportError:
    comfy_utils = None


_MAX_GUIDES = 50


class FW_LTXSequencer:
    """Insert keyframe images into LTX 2.3 video latents at specific frames.

    This node replaces specific latent frames with VAE-encoded images
    and updates the noise mask so the sampler treats those frames as
    conditioning (not noise). Use it for FFLF workflows where you want
    to anchor the first and/or last frame of each scene.

    Connects to:
    - ``FW_MultiImageLoader.multi_output`` → ``multi_input``
    - ``FW_LatentVideoInit`` → ``latent``
    - Stock ``VAELoader`` → ``vae``
    """

    CATEGORY = "FrameWeaver/Generation"

    RETURN_TYPES = ("LATENT",)
    RETURN_NAMES = ("latent",)
    FUNCTION = "inject_keyframes"

    @classmethod
    def INPUT_TYPES(cls):
        required = {
            "vae": ("VAE", {"tooltip": "Video VAE used to encode keyframe images into latent space."}),
            "latent": ("LATENT", {"tooltip": "Video latent to insert keyframe images into."}),
            "num_images": ("INT", {
                "default": 1, "min": 0, "max": _MAX_GUIDES, "step": 1,
                "tooltip": "How many images from multi_input to inject as keyframes.",
            }),
            "insert_mode": (["frames", "seconds"], {
                "default": "frames",
                "tooltip": "Interpret insert positions as frame indices or seconds.",
            }),
            "fps": ("INT", {
                "default": 24, "min": 1, "max": 120, "step": 1,
                "tooltip": "FPS for seconds→frames conversion (only used when insert_mode='seconds').",
            }),
        }

        optional = {
            "multi_input": ("IMAGE", {
                "tooltip": "Batched images from FW_MultiImageLoader or any IMAGE batch.",
            }),
        }

        # Per-image insert position + strength widgets
        for i in range(1, _MAX_GUIDES + 1):
            optional[f"insert_at_{i}"] = ("FLOAT", {
                "default": 0.0 if i == 1 else -1.0,
                "min": -9999.0, "max": 9999.0, "step": 1.0,
                "tooltip": f"Insert position for image {i}. Negative values count from end. In 'seconds' mode, this is seconds from start.",
            })
            optional[f"strength_{i}"] = ("FLOAT", {
                "default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01,
                "tooltip": f"Conditioning strength for image {i}. 1.0 = full replacement, 0.0 = pure noise.",
            })

        return {"required": required, "optional": optional}

    def inject_keyframes(self, vae, latent, num_images, insert_mode, fps, multi_input=None, **kwargs):
        if torch is None:
            raise RuntimeError("FW_LTXSequencer requires PyTorch (running inside ComfyUI).")

        samples = latent["samples"].clone()

        # Get VAE spatial/temporal scale factors
        scale_factors = vae.downscale_index_formula
        time_scale_factor, height_scale_factor, width_scale_factor = scale_factors

        batch, channels, latent_frames, latent_height, latent_width = samples.shape
        pixel_width = latent_width * width_scale_factor
        pixel_height = latent_height * height_scale_factor
        pixel_frame_count = (latent_frames - 1) * time_scale_factor + 1

        # Existing or fresh noise mask
        if "noise_mask" in latent:
            noise_mask = latent["noise_mask"].clone()
        else:
            noise_mask = torch.ones(
                (batch, 1, latent_frames, 1, 1),
                dtype=torch.float32,
                device=samples.device,
            )

        # Determine batch size of input images
        img_batch_size = 0
        if multi_input is not None:
            img_batch_size = multi_input.shape[0]

        # Process each keyframe
        num_to_process = min(num_images, _MAX_GUIDES)
        for i in range(1, num_to_process + 1):
            # Skip if no image available at this index
            if i > img_batch_size:
                continue

            insert_at = kwargs.get(f"insert_at_{i}")
            if insert_at is None:
                continue

            strength = kwargs.get(f"strength_{i}", 1.0)
            insert_at = float(insert_at)

            # Convert seconds to frames if needed
            if insert_mode == "seconds":
                insert_frame = int(round(insert_at * fps))
            else:
                insert_frame = int(insert_at)

            # Handle negative indexing (e.g. -1 = last pixel frame)
            if insert_frame < 0:
                insert_frame = int(pixel_frame_count) + insert_frame

            # Clamp to valid pixel range
            insert_frame = max(0, min(insert_frame, int(pixel_frame_count) - 1))

            # Extract the single image
            image = multi_input[i - 1:i]  # [1, H, W, C]

            # Resize if dimensions don't match the latent space
            if image.shape[1] != pixel_height or image.shape[2] != pixel_width:
                if comfy_utils is not None:
                    pixels = comfy_utils.common_upscale(
                        image.movedim(-1, 1), pixel_width, pixel_height, "bilinear", "center"
                    ).movedim(1, -1)
                else:
                    import torch.nn.functional as F
                    pixels = F.interpolate(
                        image.movedim(-1, 1),
                        size=(pixel_height, pixel_width),
                        mode="bilinear",
                        align_corners=False,
                    ).movedim(1, -1)
            else:
                pixels = image

            # Encode to latent (only RGB channels)
            encode_pixels = pixels[:, :, :, :3]
            encoded = vae.encode(encode_pixels)

            # Convert pixel frame index to latent frame index
            latent_idx = insert_frame // time_scale_factor
            latent_idx = max(0, min(latent_idx, latent_frames - 1))

            # Calculate how many latent frames the encoded image spans
            end_idx = min(latent_idx + encoded.shape[2], latent_frames)

            # Replace latent frames
            samples[:, :, latent_idx:end_idx] = encoded[:, :, :end_idx - latent_idx]

            # Update noise mask (strength 1.0 → mask 0.0 = fully conditioned)
            noise_mask[:, :, latent_idx:end_idx] = 1.0 - strength

        result = {"samples": samples, "noise_mask": noise_mask}

        # Preserve any extra keys from the input latent
        for key in latent:
            if key not in result:
                result[key] = latent[key]

        return (result,)
