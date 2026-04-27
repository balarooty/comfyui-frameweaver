class FW_DecodeVideo:
    CATEGORY = "FrameWeaver/Generation"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "decode"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "latent": ("LATENT",),
                "vae": ("VAE",),
                "use_tiling": ("BOOLEAN", {"default": True}),
            }
        }

    def decode(self, latent, vae, use_tiling):
        samples = latent.get("samples", latent)
        if use_tiling and hasattr(vae, "decode_tiled"):
            return (vae.decode_tiled(samples),)
        if hasattr(vae, "decode"):
            return (vae.decode(samples),)
        raise RuntimeError("The provided VAE does not expose decode or decode_tiled.")
