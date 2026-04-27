class FW_LatentGuideInjector:
    CATEGORY = "FrameWeaver/Generation"
    RETURN_TYPES = ("LATENT", "IMAGE", "FLOAT")
    RETURN_NAMES = ("latent", "guide_image", "reference_strength")
    FUNCTION = "inject"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "latent": ("LATENT",),
                "guide_image": ("IMAGE",),
                "reference_strength": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 1.0, "step": 0.05}),
            }
        }

    def inject(self, latent, guide_image, reference_strength):
        latent = dict(latent)
        latent["frameweaver_reference_strength"] = float(reference_strength)
        return (latent, guide_image, float(reference_strength))
