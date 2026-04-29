import re
import math


class FW_SpeechLengthCalc:
    """Calculate video duration from speech dialogue length.

    Extracts words inside quotation marks from the input text and estimates
    how many frames are needed at three different speaking speeds:
    - Slow: 100 WPM
    - Average: 130 WPM
    - Fast: 160 WPM

    The frame counts are NOT auto-adjusted to 8n+1 — pipe the output through
    ``FW_LTX23Settings`` or ``FW_SceneDurationList`` for that constraint.

    Ported from WhatDreamsCost's SpeechLengthCalculator with improvements:
    - Supports smart/curly quotes (Unicode)
    - Outputs both frame count and seconds for flexibility
    - Accepts an optional external text_input for chained workflows
    """

    CATEGORY = "FrameWeaver/Input"

    RETURN_TYPES = ("INT", "INT", "INT", "FLOAT", "FLOAT", "FLOAT", "INT")
    RETURN_NAMES = (
        "slow_frames",
        "avg_frames",
        "fast_frames",
        "slow_seconds",
        "avg_seconds",
        "fast_seconds",
        "word_count",
    )
    FUNCTION = "calculate_speech"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {
                    "multiline": True,
                    "default": 'Enter your script here. "Make sure to put spoken words inside quotes!"',
                    "tooltip": "Words inside any type of quotation marks are treated as spoken dialogue.",
                }),
                "fps": ("INT", {
                    "default": 24, "min": 1, "max": 120, "step": 1,
                    "tooltip": "Frames per second for the target video.",
                }),
                "additional_time": ("FLOAT", {
                    "default": 0.0, "min": 0.0, "step": 0.1,
                    "tooltip": "Extra seconds to add (for pauses, intro/outro).",
                }),
            },
            "optional": {
                "text_input": ("STRING", {
                    "forceInput": True,
                    "tooltip": "If connected, overrides the text widget above.",
                }),
            },
        }

    def calculate_speech(self, text, fps, additional_time=0.0, text_input=None):
        # Prioritize connected text_input when available
        active_text = text
        if text_input is not None and isinstance(text_input, str) and text_input.strip():
            active_text = text_input

        # Extract words inside any type of quotation marks (straight, curly, single)
        matches = re.findall(
            r'"([^"]*)"'          # straight double quotes
            r"|'([^']*)'"          # straight single quotes
            r'|\u201c([^\u201d]*)\u201d'  # curly double quotes " "
            r'|\u2018([^\u2019]*)\u2019',  # curly single quotes ' '
            active_text,
        )

        # Flatten: each match is a tuple with one non-empty group
        quoted_text = " ".join(
            next((g for g in m if g), "") for m in matches
        )

        words = quoted_text.split()
        word_count = len(words)

        def _calc(wpm):
            if word_count == 0 and additional_time == 0:
                return 0, 0.0
            minutes = word_count / wpm
            seconds = (minutes * 60) + additional_time
            frames = math.ceil(seconds * fps)
            return frames, round(seconds, 2)

        slow_frames, slow_sec = _calc(100)
        avg_frames, avg_sec = _calc(130)
        fast_frames, fast_sec = _calc(160)

        return (slow_frames, avg_frames, fast_frames, slow_sec, avg_sec, fast_sec, word_count)
