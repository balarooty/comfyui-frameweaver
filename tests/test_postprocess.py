"""Tests for Phase 3 post-processing nodes."""

import pytest


class TestColorMatchSchema:
    def test_required_inputs(self):
        from nodes.postprocess.color_match import FW_ColorMatch
        it = FW_ColorMatch.INPUT_TYPES()
        assert "images" in it["required"]
        assert "reference_image" in it["required"]
        assert FW_ColorMatch.CATEGORY == "FrameWeaver/PostProcess"

    def test_return_types(self):
        from nodes.postprocess.color_match import FW_ColorMatch
        assert "IMAGE" in FW_ColorMatch.RETURN_TYPES


class TestFilmGrainSchema:
    def test_required_inputs(self):
        from nodes.postprocess.film_grain import FW_FilmGrain
        it = FW_FilmGrain.INPUT_TYPES()
        assert "images" in it["required"]
        assert "intensity" in it["required"]
        assert FW_FilmGrain.CATEGORY == "FrameWeaver/PostProcess"

    def test_intensity_range(self):
        from nodes.postprocess.film_grain import FW_FilmGrain
        it = FW_FilmGrain.INPUT_TYPES()
        cfg = it["required"]["intensity"][1]
        assert cfg["min"] >= 0.0
        assert cfg["max"] <= 1.0


class TestCinematicPolishSchema:
    def test_required_inputs(self):
        from nodes.postprocess.cinematic_polish import FW_CinematicPolish
        it = FW_CinematicPolish.INPUT_TYPES()
        assert "images" in it["required"]
        assert "mode" in it["required"]
        assert FW_CinematicPolish.CATEGORY == "FrameWeaver/PostProcess"

    def test_modes_available(self):
        from nodes.postprocess.cinematic_polish import FW_CinematicPolish
        it = FW_CinematicPolish.INPUT_TYPES()
        modes = it["required"]["mode"][0]
        assert "unsharp" in modes
        assert "laplacian" in modes
        assert "sobel" in modes


class TestLUTSystemSchema:
    def test_lut_apply_inputs(self):
        from nodes.postprocess.lut_system import FW_LUTApply
        it = FW_LUTApply.INPUT_TYPES()
        assert "images" in it["required"]
        assert FW_LUTApply.CATEGORY == "FrameWeaver/PostProcess"

    def test_lut_create_inputs(self):
        from nodes.postprocess.lut_system import FW_LUTCreate
        it = FW_LUTCreate.INPUT_TYPES()
        assert "palette_hex" in it["required"]
        assert FW_LUTCreate.CATEGORY == "FrameWeaver/PostProcess"
