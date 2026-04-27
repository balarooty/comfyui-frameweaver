from utils.validation import clamp_float


class FW_ContinuityEncoder:
    CATEGORY = "FrameWeaver/Continuity"
    RETURN_TYPES = ("STRING", "FW_SCENE_STATE")
    RETURN_NAMES = ("positive_prompt", "scene_state")
    FUNCTION = "encode"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "style_anchor": ("FW_STYLE_ANCHOR",),
                "scene_prompt": ("STRING", {"multiline": True}),
                "style_strength": ("FLOAT", {"default": 0.35, "min": 0.0, "max": 1.0, "step": 0.05}),
            },
            "optional": {
                "previous_scene_state": ("FW_SCENE_STATE",),
                "bridge_prompt": ("STRING", {"multiline": True, "default": ""}),
            },
        }

    def encode(self, style_anchor, scene_prompt, style_strength, previous_scene_state=None, bridge_prompt=""):
        strength = clamp_float(style_strength, 0.0, 1.0)
        style = style_anchor.get("style_description", "") if isinstance(style_anchor, dict) else ""
        identity = style_anchor.get("identity_description", "") if isinstance(style_anchor, dict) else ""
        previous_count = 0
        if isinstance(previous_scene_state, dict):
            previous_count = int(previous_scene_state.get("scene_count", 0))

        continuity_parts = [scene_prompt.strip()]
        if style and strength > 0:
            continuity_parts.append(f"continuity strength {strength:.2f}: {style}")
        if identity and strength > 0:
            continuity_parts.append(identity)
        if bridge_prompt:
            continuity_parts.append(f"transition note: {bridge_prompt.strip()}")
        if previous_count:
            continuity_parts.append("continue naturally from the previous scene without visual discontinuity")

        prompt = ", ".join(part for part in continuity_parts if part)
        state = {
            "scene_count": previous_count + 1,
            "last_prompt": prompt,
            "style_strength": strength,
        }
        return (prompt, state)
