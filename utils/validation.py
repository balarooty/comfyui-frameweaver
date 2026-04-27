def nearest_valid_frame_count(value: int, minimum: int = 9, maximum: int = 241) -> int:
    frames = int(round(value))
    frames = max(minimum, min(maximum, frames))
    remainder = (frames - 1) % 8
    lower = frames - remainder
    upper = lower + 8
    candidates = [c for c in (lower, upper) if minimum <= c <= maximum and (c - 1) % 8 == 0]
    if not candidates:
        return minimum
    return min(candidates, key=lambda c: (abs(c - frames), c))


def floor_to_multiple(value: int, multiple: int) -> int:
    value = int(value)
    return max(multiple, value - (value % multiple))


def normalize_dimensions(width: int, height: int, multiple: int = 32) -> tuple[int, int]:
    return floor_to_multiple(width, multiple), floor_to_multiple(height, multiple)


def clamp_float(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, float(value)))
