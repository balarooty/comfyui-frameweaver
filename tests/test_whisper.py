"""Tests for FW_WhisperTranscriber node."""

import pytest
from nodes.ai.whisper_transcriber import FW_WhisperTranscriber, _LANGUAGES, _WHISPER_MODELS


class TestWhisperSchema:
    def test_required_inputs(self):
        it = FW_WhisperTranscriber.INPUT_TYPES()
        for key in ["scene_count", "model_name", "language", "enable_transcription",
                     "overlap_seconds", "fallback_words"]:
            assert key in it["required"], f"Missing required input: {key}"

    def test_optional_per_scene_inputs(self):
        it = FW_WhisperTranscriber.INPUT_TYPES()
        for i in range(1, 51):
            assert f"audio_{i}" in it["optional"]
            assert f"context_{i}" in it["optional"]
        assert len(it["optional"]) == 100

    def test_category(self):
        assert FW_WhisperTranscriber.CATEGORY == "FrameWeaver/AI"

    def test_model_list(self):
        assert len(_WHISPER_MODELS) == 4
        assert "openai/whisper-large-v3" in _WHISPER_MODELS
        assert "openai/whisper-base" in _WHISPER_MODELS

    def test_language_list(self):
        assert "auto" in _LANGUAGES
        assert "english" in _LANGUAGES
        assert "hindi" in _LANGUAGES
        assert "tamil" in _LANGUAGES
        assert len(_LANGUAGES) >= 90


class TestWhisperDynamicOutputs:
    def test_output_types(self):
        ot = FW_WhisperTranscriber.get_output_types(scene_count=3)
        assert ot[0] == "STRING"  # pipe_text
        assert len(ot) == 4  # pipe + 3 scenes

    def test_output_names(self):
        on = FW_WhisperTranscriber.get_output_names(scene_count=2)
        assert on == ["pipe_text", "scene_1_text", "scene_2_text"]


class TestWhisperFallbackMode:
    def test_fallback_when_disabled(self):
        wt = FW_WhisperTranscriber()
        result = wt.transcribe(
            scene_count=3,
            model_name="openai/whisper-base",
            language="english",
            enable_transcription=False,
            overlap_seconds=0.0,
            fallback_words="walking, sitting, thinking",
        )
        pipe_text = result[0]
        scene_texts = result[1:]

        assert isinstance(pipe_text, str)
        assert "|" in pipe_text
        assert len(scene_texts) == 3
        for t in scene_texts:
            assert t in ["walking", "sitting", "thinking"]

    def test_context_enrichment(self):
        wt = FW_WhisperTranscriber()
        result = wt.transcribe(
            scene_count=2,
            model_name="openai/whisper-base",
            language="english",
            enable_transcription=False,
            overlap_seconds=0.0,
            fallback_words="dancing",
            context_1="girl in red dress",
            context_2="boy in blue shirt",
        )
        assert "girl in red dress" in result[1]
        assert "boy in blue shirt" in result[2]

    def test_pipe_output_format(self):
        wt = FW_WhisperTranscriber()
        result = wt.transcribe(
            scene_count=3,
            model_name="openai/whisper-base",
            language="english",
            enable_transcription=False,
            overlap_seconds=0.0,
            fallback_words="moving",
        )
        pipe = result[0]
        parts = [p.strip() for p in pipe.split("|")]
        assert len(parts) == 3
