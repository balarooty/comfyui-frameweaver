try:
    from ...utils.prompt_utils import build_scene_prompts
    from ...utils.validation import nearest_valid_frame_count, normalize_dimensions
except ImportError:
    from utils.prompt_utils import build_scene_prompts
    from utils.validation import nearest_valid_frame_count, normalize_dimensions


class FW_QuickPipeline:
    CATEGORY = "FrameWeaver/Quick"
    RETURN_TYPES = ("FW_PROMPT_LIST", "STRING", "STRING", "INT", "INT", "INT", "INT")
    RETURN_NAMES = ("prompt_list", "scene_1_prompt", "scene_2_prompt", "width", "height", "frames", "fps")
    FUNCTION = "prepare"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "base_style": (
                    "STRING",
                    {"multiline": True, "default": "cinematic, coherent subject identity, high quality motion"},
                ),
                "negative": (
                    "STRING",
                    {"multiline": True, "default": "blurry, low quality, flicker, inconsistent character"},
                ),
                "scene_1": ("STRING", {"multiline": True, "default": "Scene one action."}),
                "scene_2": ("STRING", {"multiline": True, "default": "Scene two action."}),
                "width": ("INT", {"default": 1280, "min": 64, "max": 4096, "step": 32}),
                "height": ("INT", {"default": 720, "min": 64, "max": 4096, "step": 32}),
                "frames_per_scene": ("INT", {"default": 97, "min": 9, "max": 241, "step": 8}),
                "fps": ("INT", {"default": 24, "min": 1, "max": 60, "step": 1}),
            }
        }

    def prepare(self, base_style, negative, scene_1, scene_2, width, height, frames_per_scene, fps):
        prompts = build_scene_prompts(base_style, negative, scene_1, scene_2)
        width, height = normalize_dimensions(width, height, 32)
        frames = nearest_valid_frame_count(frames_per_scene)
        scene_1_prompt = prompts[0]["positive"] if prompts else ""
        scene_2_prompt = prompts[1]["positive"] if len(prompts) > 1 else ""
        return (prompts, scene_1_prompt, scene_2_prompt, width, height, frames, int(fps))
