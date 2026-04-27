try:
    from ...utils.tensor_utils import last_frame
except ImportError:
    from utils.tensor_utils import last_frame


class FW_LastFrameExtractor:
    CATEGORY = "FrameWeaver/Bridge"
    RETURN_TYPES = ("IMAGE", "INT")
    RETURN_NAMES = ("last_frame", "source_frame_count")
    FUNCTION = "extract"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"scene_video": ("IMAGE",)}}

    def extract(self, scene_video):
        return (last_frame(scene_video), int(scene_video.shape[0]))
