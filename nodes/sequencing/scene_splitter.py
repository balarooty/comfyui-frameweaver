"""FW_SceneSplitter — Parse a stacked scene/prompt/time table.

Extracts per-scene data for the current queue run, outputting the
current scene's prompt, global prompt, PromptRelay-compatible
local_prompts and segment_lengths strings, and time calculations.

Supports three input syntaxes (auto-detected):
  • Block headers:  Scene 1:\ntext\nScene 2:\ntext
  • Smart inline:   text [0-50] | text [50-100] | text [100-150]
  • Plain pipe:     scene one | scene two | scene three
"""

try:
    from ...utils.prompt_relay.parser import parse_smart_prompt
except ImportError:
    from utils.prompt_relay.parser import parse_smart_prompt

try:
    from ...utils.validation import nearest_valid_frame_count
except ImportError:
    from utils.validation import nearest_valid_frame_count


class FW_SceneSplitter:
    """Parse a stacked scene table and extract per-scene data for the current queue run."""

    CATEGORY = "FrameWeaver/Sequencing"
    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "INT", "INT", "INT", "FLOAT")
    RETURN_NAMES = (
        "current_prompt",
        "global_prompt",
        "local_prompts",
        "segment_lengths",
        "scene_count",
        "scene_start_frame",
        "scene_end_frame",
        "scene_duration_sec",
    )
    FUNCTION = "split"
    DESCRIPTION = (
        "Parses a stacked scene/prompt/time table and extracts the current scene's data. "
        "Supports smart syntax ([0-50] tags), block headers (Scene 1:), and pipe-delimited text. "
        "Connect scene_index from FW_SceneIterator to iterate through scenes on each queue run."
    )
    SEARCH_ALIASES = ["scene split", "stacked prompts", "scene table", "temporal split", "queue adjust"]

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "stacked_prompts": ("STRING", {
                    "multiline": True,
                    "default": (
                        "Scene 1:\n"
                        "walking through a forest\n"
                        "Scene 2:\n"
                        "arriving at a cabin\n"
                        "Scene 3:\n"
                        "opening the door"
                    ),
                    "tooltip": (
                        "Stacked scene definitions. Supports:\n"
                        "• Block: 'Scene 1:\\ntext\\nScene 2:\\ntext'\n"
                        "• Smart: 'text [0-50] | text [50-100]'\n"
                        "• Pipe: 'scene 1 | scene 2 | scene 3'"
                    ),
                }),
                "base_style": ("STRING", {
                    "multiline": True,
                    "default": "cinematic, high quality, coherent motion, detailed",
                    "tooltip": "Global style prompt prepended to every scene.",
                }),
                "scene_index": ("INT", {
                    "default": 1, "min": 1, "max": 50, "step": 1,
                    "tooltip": "Which scene to extract (1-indexed). Connect from FW_SceneIterator.",
                }),
                "fps": ("INT", {"default": 24, "min": 1, "max": 120}),
                "frames_per_scene": ("INT", {
                    "default": 97, "min": 9, "max": 241, "step": 8,
                    "tooltip": "Frames per scene (8n+1 for LTX 2.3). Used for time calculations.",
                }),
            },
            "optional": {
                "whisper_override": ("STRING", {
                    "forceInput": True,
                    "tooltip": "If connected (from FW_WhisperTranscriber), overrides stacked_prompts.",
                }),
            },
        }

    @classmethod
    def VALIDATE_INPUTS(cls, stacked_prompts, **kwargs):
        if not stacked_prompts or not stacked_prompts.strip():
            return "stacked_prompts cannot be empty"
        return True

    def split(self, stacked_prompts, base_style, scene_index, fps, frames_per_scene,
              whisper_override=None):
        # Whisper override takes priority
        source_text = stacked_prompts
        if whisper_override and isinstance(whisper_override, str) and whisper_override.strip():
            source_text = whisper_override.strip()

        # Parse the stacked prompts using the smart parser
        segments = parse_smart_prompt(source_text)

        # Filter out empty segments
        valid_segments = [s for s in segments if s["text"].strip()]
        if not valid_segments:
            valid_segments = [{"text": "default scene", "weight": 1.0}]

        scene_count = len(valid_segments)
        # Clamp scene_index to valid range
        scene_idx = max(1, min(scene_index, scene_count))
        current_seg = valid_segments[scene_idx - 1]

        # ---- Build outputs ----

        # Current scene prompt with base style
        current_prompt = self._join(base_style, current_seg["text"])

        # Global prompt: base style + current scene (for PromptRelay global context)
        global_prompt = self._join(base_style, current_seg["text"])

        # Local prompts: all scene prompts as pipe-delimited string
        local_prompts = " | ".join(s["text"] for s in valid_segments)

        # Segment lengths: proportional frame counts from weights
        total_weight = sum(s["weight"] for s in valid_segments)
        if total_weight <= 0:
            total_weight = float(scene_count)

        total_frames = frames_per_scene * scene_count
        segment_lengths_list = []
        for s in valid_segments:
            proportion = s["weight"] / total_weight
            seg_frames = max(1, int(round(proportion * total_frames)))
            segment_lengths_list.append(seg_frames)

        # Adjust to ensure exact total
        diff = total_frames - sum(segment_lengths_list)
        if diff != 0 and segment_lengths_list:
            # Add/subtract from the largest segment
            max_idx = max(range(len(segment_lengths_list)),
                          key=lambda i: segment_lengths_list[i])
            segment_lengths_list[max_idx] += diff

        segment_lengths = ", ".join(str(f) for f in segment_lengths_list)

        # Time calculations for the current scene
        scene_start_frame = sum(segment_lengths_list[:scene_idx - 1])
        scene_end_frame = scene_start_frame + segment_lengths_list[scene_idx - 1] - 1
        scene_duration_sec = round(segment_lengths_list[scene_idx - 1] / max(fps, 1), 4)

        return (
            current_prompt,
            global_prompt,
            local_prompts,
            segment_lengths,
            scene_count,
            scene_start_frame,
            scene_end_frame,
            scene_duration_sec,
        )

    @staticmethod
    def _join(*parts):
        """Join non-empty string parts with comma separator."""
        return ", ".join(p.strip() for p in parts if isinstance(p, str) and p.strip())
