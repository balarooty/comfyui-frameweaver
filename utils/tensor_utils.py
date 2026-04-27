def image_batch_length(image) -> int:
    shape = getattr(image, "shape", None)
    if not shape:
        return 0
    return int(shape[0])


def image_resolution(image) -> tuple[int, int]:
    shape = getattr(image, "shape", None)
    if not shape or len(shape) < 3:
        return 0, 0
    return int(shape[2]), int(shape[1])


def last_frame(image):
    if image is None:
        raise ValueError("No image tensor was provided.")
    if len(image.shape) < 4:
        raise ValueError(f"Expected IMAGE tensor [B,H,W,C], got shape {tuple(image.shape)}")
    return image[-1:].clone()
