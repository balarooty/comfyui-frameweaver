class FW_StyleAnchor:
    CATEGORY = "FrameWeaver/Continuity"
    RETURN_TYPES = ("FW_STYLE_ANCHOR", "IMAGE")
    RETURN_NAMES = ("style_anchor", "reference_image")
    FUNCTION = "anchor"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "reference_image": ("IMAGE",),
                "style_description": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "Preserve the same subject identity, wardrobe, art direction, lighting, lens, and color palette.",
                    },
                ),
                "identity_description": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "The same primary character remains recognizable across all scenes.",
                    },
                ),
            }
        }

    def anchor(self, reference_image, style_description, identity_description):
        anchor = {
            "style_description": style_description.strip(),
            "identity_description": identity_description.strip(),
            "has_reference_image": True,
        }
        return (anchor, reference_image)
