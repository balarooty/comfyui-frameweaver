from utils.validation import nearest_valid_frame_count, normalize_dimensions


def test_nearest_valid_frame_count():
    assert nearest_valid_frame_count(97) == 97
    assert nearest_valid_frame_count(96) == 97
    assert nearest_valid_frame_count(93) == 89
    assert nearest_valid_frame_count(1) == 9


def test_normalize_dimensions():
    assert normalize_dimensions(1281, 721) == (1280, 704)
    assert normalize_dimensions(31, 31) == (32, 32)
