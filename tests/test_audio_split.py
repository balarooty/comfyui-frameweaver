"""Tests for FW_AudioSplitter node."""

import pytest
from nodes.inputs.audio_splitter import FW_AudioSplitter, _nearest_valid_frame_count


class TestAudioSplitterSchema:
    def test_required_inputs(self):
        it = FW_AudioSplitter.INPUT_TYPES()
        for key in ["audio", "scene_count", "scene_duration_seconds", "fps", "enforce_8n1"]:
            assert key in it["required"], f"Missing required input: {key}"

    def test_optional_inputs(self):
        it = FW_AudioSplitter.INPUT_TYPES()
        assert "custom_durations_csv" in it["optional"]
        assert "set_index" in it["optional"]

    def test_category(self):
        assert FW_AudioSplitter.CATEGORY == "FrameWeaver/Audio"

    def test_function_name(self):
        assert FW_AudioSplitter.FUNCTION == "split_audio"

    def test_is_dynamic(self):
        assert FW_AudioSplitter.IS_DYNAMIC() is True


class TestAudioSplitterDynamicOutputs:
    def test_output_types_match_scene_count(self):
        ot = FW_AudioSplitter.get_output_types(scene_count=3)
        assert ot[0] == "FW_AUDIO_META"
        assert ot[1] == "FLOAT"
        assert len(ot) == 5  # meta + duration + 3 audio

    def test_output_names_match_scene_count(self):
        on = FW_AudioSplitter.get_output_names(scene_count=5)
        assert on[0] == "audio_meta"
        assert on[1] == "total_duration"
        assert on[-1] == "audio_5"
        assert len(on) == 7

    def test_clamped_at_50(self):
        ot = FW_AudioSplitter.get_output_types(scene_count=100)
        assert len(ot) == 52  # meta + duration + 50

    def test_minimum_1(self):
        ot = FW_AudioSplitter.get_output_types(scene_count=0)
        assert len(ot) == 3  # meta + duration + 1


class TestAudioSplitter8n1:
    def test_standard_values(self):
        assert _nearest_valid_frame_count(96) == 97
        assert _nearest_valid_frame_count(97) == 97
        assert _nearest_valid_frame_count(9) == 9

    def test_all_results_are_valid(self):
        for v in [1, 10, 50, 96, 97, 98, 100, 150, 200]:
            result = _nearest_valid_frame_count(v)
            assert (result - 1) % 8 == 0, f"_nearest_valid_frame_count({v}) = {result}"

    def test_minimum(self):
        assert _nearest_valid_frame_count(1) == 9
