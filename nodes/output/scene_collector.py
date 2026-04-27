from utils.checkpoint_manager import CheckpointManager
from utils.tensor_utils import image_batch_length, image_resolution


class FW_SceneCollector:
    CATEGORY = "FrameWeaver/Output"
    RETURN_TYPES = ("FW_SCENE_COLLECTION", "STRING")
    RETURN_NAMES = ("scene_collection", "metadata_json")
    FUNCTION = "collect"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "scene_video": ("IMAGE",),
                "scene_index": ("INT", {"default": 1, "min": 1, "max": 99, "step": 1}),
                "prompt_used": ("STRING", {"multiline": True}),
                "seed_used": ("INT", {"default": 42, "min": 0, "max": 0xFFFFFFFFFFFFFFFF}),
            },
            "optional": {
                "existing_collection": ("FW_SCENE_COLLECTION",),
                "save_checkpoint_metadata": ("BOOLEAN", {"default": False}),
            },
        }

    def collect(self, scene_video, scene_index, prompt_used, seed_used, existing_collection=None, save_checkpoint_metadata=False):
        import json

        collection = dict(existing_collection or {})
        width, height = image_resolution(scene_video)
        metadata = {
            "scene_index": int(scene_index),
            "prompt": prompt_used,
            "seed": int(seed_used),
            "resolution": {"width": width, "height": height},
            "frame_count": image_batch_length(scene_video),
            "dtype": str(getattr(scene_video, "dtype", "unknown")),
        }
        collection[int(scene_index)] = {"frames": scene_video, "metadata": metadata}
        if save_checkpoint_metadata:
            CheckpointManager().save_metadata(scene_index, metadata)
        return (collection, json.dumps(metadata, indent=2, sort_keys=True))
