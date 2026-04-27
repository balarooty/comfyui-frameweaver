class FW_FrameBridge:
    CATEGORY = "FrameWeaver/Bridge"
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("bridge_image", "edit_prompt")
    FUNCTION = "build"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "last_frame": ("IMAGE",),
                "next_scene_prompt": ("STRING", {"multiline": True}),
                "keep": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "Keep the same character identity, clothing, face, lighting direction, and camera continuity.",
                    },
                ),
                "change": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "Change only the environment and action needed for the next scene.",
                    },
                ),
            },
            "optional": {
                "bridge_prompt": ("STRING", {"multiline": True, "default": ""}),
            },
        }

    def build(self, last_frame, next_scene_prompt, keep, change, bridge_prompt=""):
        sections = [
            "Edit this frame as a continuity bridge for the next video scene.",
            f"KEEP: {keep.strip()}",
            f"CHANGE: {change.strip()}",
            f"NEXT SCENE: {next_scene_prompt.strip()}",
        ]
        if bridge_prompt:
            sections.append(f"TRANSITION: {bridge_prompt.strip()}")
        sections.append("Avoid adding new characters unless explicitly requested. Avoid style drift.")
        return (last_frame, "\n".join(section for section in sections if section))
