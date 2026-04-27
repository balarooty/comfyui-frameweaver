try:
    from ...utils.validation import nearest_valid_frame_count
except ImportError:
    from utils.validation import nearest_valid_frame_count


class FW_SceneDurationList:
    CATEGORY = "FrameWeaver/Input"
    RETURN_TYPES = ("FW_DURATION_LIST", "INT", "INT", "INT", "INT", "INT", "INT")
    RETURN_NAMES = (
        "duration_list",
        "scene_1_frames",
        "scene_2_frames",
        "scene_3_frames",
        "scene_4_frames",
        "scene_5_frames",
        "total_frames",
    )
    FUNCTION = "build"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "scene_1_frames": ("INT", {"default": 97, "min": 9, "max": 241, "step": 8}),
                "scene_2_frames": ("INT", {"default": 97, "min": 9, "max": 241, "step": 8}),
                "scene_3_frames": ("INT", {"default": 97, "min": 9, "max": 241, "step": 8}),
                "scene_4_frames": ("INT", {"default": 97, "min": 9, "max": 241, "step": 8}),
                "scene_5_frames": ("INT", {"default": 97, "min": 9, "max": 241, "step": 8}),
                "scene_count": ("INT", {"default": 1, "min": 1, "max": 5, "step": 1}),
            }
        }

    def build(self, scene_1_frames, scene_2_frames, scene_3_frames, scene_4_frames, scene_5_frames, scene_count):
        raw = [scene_1_frames, scene_2_frames, scene_3_frames, scene_4_frames, scene_5_frames]
        frames = [nearest_valid_frame_count(value) for value in raw]
        active = frames[: int(scene_count)]
        return (
            active,
            frames[0],
            frames[1],
            frames[2],
            frames[3],
            frames[4],
            sum(active),
        )
