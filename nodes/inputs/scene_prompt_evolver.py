from utils.prompt_utils import build_scene_prompts, select_scene


class FW_ScenePromptEvolver:
    CATEGORY = "FrameWeaver/Input"
    RETURN_TYPES = ("FW_PROMPT_LIST", "STRING", "STRING", "INT")
    RETURN_NAMES = ("prompt_list", "scene_1_positive", "negative", "scene_count")
    FUNCTION = "build_evolved_list"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "base_style": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "cinematic, high quality, coherent character identity, stable wardrobe, detailed motion",
                    },
                ),
                "base_negative": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "blurry, low quality, warped anatomy, flicker, inconsistent identity, static shot",
                    },
                ),
                "scene_1": ("STRING", {"multiline": True, "default": "A character starts moving through the scene."}),
                "inheritance_mode": (["cumulative", "replace", "blend"], {"default": "cumulative"}),
            },
            "optional": {
                "scene_2": ("STRING", {"multiline": True, "default": ""}),
                "scene_3": ("STRING", {"multiline": True, "default": ""}),
                "scene_4": ("STRING", {"multiline": True, "default": ""}),
                "scene_5": ("STRING", {"multiline": True, "default": ""}),
                "bridge_1_to_2": ("STRING", {"multiline": True, "default": ""}),
                "bridge_2_to_3": ("STRING", {"multiline": True, "default": ""}),
                "bridge_3_to_4": ("STRING", {"multiline": True, "default": ""}),
                "bridge_4_to_5": ("STRING", {"multiline": True, "default": ""}),
            },
        }

    def build_evolved_list(self, base_style, base_negative, scene_1, inheritance_mode, **kwargs):
        scenes = build_scene_prompts(
            base_style=base_style,
            base_negative=base_negative,
            scene_1=scene_1,
            scene_2=kwargs.get("scene_2", ""),
            scene_3=kwargs.get("scene_3", ""),
            scene_4=kwargs.get("scene_4", ""),
            scene_5=kwargs.get("scene_5", ""),
            bridge_1_to_2=kwargs.get("bridge_1_to_2", ""),
            bridge_2_to_3=kwargs.get("bridge_2_to_3", ""),
            bridge_3_to_4=kwargs.get("bridge_3_to_4", ""),
            bridge_4_to_5=kwargs.get("bridge_4_to_5", ""),
            inheritance_mode=inheritance_mode,
        )
        first = scenes[0] if scenes else {"positive": "", "negative": base_negative}
        return (scenes, first["positive"], first["negative"], len(scenes))


class FW_ScenePromptSelector:
    CATEGORY = "FrameWeaver/Input"
    RETURN_TYPES = ("STRING", "STRING", "STRING", "INT")
    RETURN_NAMES = ("positive", "negative", "bridge_prompt", "selected_index")
    FUNCTION = "select"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt_list": ("FW_PROMPT_LIST",),
                "scene_index": ("INT", {"default": 1, "min": 1, "max": 5, "step": 1}),
            }
        }

    def select(self, prompt_list, scene_index):
        scene = select_scene(prompt_list, scene_index)
        return (scene["positive"], scene["negative"], scene["bridge"], int(scene["index"]))
