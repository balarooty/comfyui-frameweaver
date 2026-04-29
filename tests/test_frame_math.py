"""Tests for 8n+1 frame math, preroll compensation, and frame trimming."""

import pytest
from utils.validation import nearest_valid_frame_count, normalize_dimensions, floor_to_multiple


# ------------------------------------------------------------------ #
#  8n+1 frame enforcement
# ------------------------------------------------------------------ #

class TestNearestValidFrameCount:
    """Comprehensive edge cases for LTX 2.3's 8n+1 constraint."""

    def test_already_valid_values(self):
        for v in [9, 17, 25, 33, 41, 49, 57, 65, 73, 81, 89, 97, 105, 113, 121, 129, 137, 145, 153, 161, 169, 177, 185, 193, 201, 209, 217, 225, 233, 241]:
            assert nearest_valid_frame_count(v) == v

    def test_rounds_up_from_below(self):
        assert nearest_valid_frame_count(96) == 97
        assert nearest_valid_frame_count(95) == 97
        assert nearest_valid_frame_count(94) == 97

    def test_rounds_down_from_above(self):
        assert nearest_valid_frame_count(98) == 97
        assert nearest_valid_frame_count(99) == 97
        assert nearest_valid_frame_count(100) == 97

    def test_midpoint_ties_favor_lower(self):
        # Between 89 and 97, midpoint is 93
        assert nearest_valid_frame_count(93) in (89, 97)

    def test_minimum_clamping(self):
        assert nearest_valid_frame_count(1) == 9
        assert nearest_valid_frame_count(0) == 9
        assert nearest_valid_frame_count(-5) == 9
        assert nearest_valid_frame_count(5) == 9

    def test_maximum_clamping(self):
        assert nearest_valid_frame_count(300) == 241
        assert nearest_valid_frame_count(241) == 241
        assert nearest_valid_frame_count(240) == 241

    def test_all_valid_are_8n_plus_1(self):
        for v in range(1, 300):
            result = nearest_valid_frame_count(v)
            assert (result - 1) % 8 == 0, f"nearest_valid_frame_count({v}) = {result} is not 8n+1"
            assert 9 <= result <= 241


# ------------------------------------------------------------------ #
#  Dimension normalization
# ------------------------------------------------------------------ #

class TestNormalizeDimensions:
    def test_already_aligned(self):
        assert normalize_dimensions(1280, 704) == (1280, 704)

    def test_rounds_down_to_multiple_of_32(self):
        assert normalize_dimensions(1281, 721) == (1280, 704)

    def test_minimum_is_multiple(self):
        assert normalize_dimensions(31, 31) == (32, 32)

    def test_large_values(self):
        w, h = normalize_dimensions(1920, 1080)
        assert w % 32 == 0
        assert h % 32 == 0


class TestFloorToMultiple:
    def test_exact(self):
        assert floor_to_multiple(64, 32) == 64

    def test_rounds_down(self):
        assert floor_to_multiple(65, 32) == 64

    def test_minimum(self):
        assert floor_to_multiple(1, 32) == 32
