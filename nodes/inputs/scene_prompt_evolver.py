try:
    from ...utils.prompt_utils import build_scene_prompts, select_scene
except ImportError:
    from utils.prompt_utils import build_scene_prompts, select_scene


class FW_ScenePromptEvolver:
    """Build a list of scene prompts with style inheritance.

    Supports two input modes:
    1. **Individual fields** (scene_1…scene_5 + bridges) — fine-grained control
    2. **Pipe-delimited text** — type all scenes in one text box separated by ``|``
       (e.g. ``walking through a forest | arriving at a cabin | opening the door``)

    When ``pipe_text`` is non-empty it takes priority over the individual
    scene fields.  The ``scene_count`` output adjusts automatically.

    Pipe-mode is inspired by VRGDG ``PromptSplitter`` while keeping
    FrameWeaver's inheritance_mode (cumulative / replace / blend).
    """

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
                "pipe_text": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Pipe-delimited scene prompts (overrides individual fields when non-empty). Example: scene 1 | scene 2 | scene 3",
                }),
                "pipe_text_input": ("STRING", {
                    "forceInput": True,
                    "tooltip": "If connected (e.g. from Whisper), overrides pipe_text widget.",
                }),
            },
        }

    def build_evolved_list(self, base_style, base_negative, scene_1, inheritance_mode, **kwargs):
        pipe_text = kwargs.get("pipe_text", "").strip()
        pipe_text_input = kwargs.get("pipe_text_input", None)

        # External pipe input takes highest priority
        if pipe_text_input is not None and isinstance(pipe_text_input, str) and pipe_text_input.strip():
            pipe_text = pipe_text_input.strip()

        if pipe_text:
            # Pipe-delimited mode — split and map to scene slots
            parts = [p.strip() for p in pipe_text.split("|") if p.strip()]
            # Map to scene_1..scene_N
            scene_inputs = parts[:50]  # Cap at 50 scenes
            # Build using the existing utility but with dynamic scene count
            scenes = self._build_from_pipe(base_style, base_negative, scene_inputs, inheritance_mode)
        else:
            # Classic individual-field mode
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
        return (scenes, first["positive"], first.get("negative", base_negative), len(scenes))

    def _build_from_pipe(self, base_style, base_negative, scene_inputs, inheritance_mode):
        """Build scene prompts from a list of pipe-delimited strings."""
        def _join(*parts):
            return ", ".join(p.strip() for p in parts if isinstance(p, str) and p.strip())

        scenes = []
        inherited = ""

        for index, scene_text in enumerate(scene_inputs, start=1):
            scene_text = scene_text.strip()
            if not scene_text:
                continue

            if inheritance_mode == "replace" or not inherited:
                inherited = scene_text
            elif inheritance_mode == "blend":
                inherited = _join(inherited, f"then transition toward: {scene_text}")
            else:  # cumulative
                inherited = _join(inherited, scene_text)

            scenes.append({
                "index": index,
                "positive": _join(base_style, inherited),
                "negative": base_negative.strip(),
                "bridge": "",
                "delta": scene_text,
            })

        return scenes


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
                "scene_index": ("INT", {"default": 1, "min": 1, "max": 50, "step": 1}),
            }
        }

    def select(self, prompt_list, scene_index):
        scene = select_scene(prompt_list, scene_index)
        return (scene["positive"], scene["negative"], scene["bridge"], int(scene["index"]))
