class FW_RelayOptions:
    CATEGORY = "FrameWeaver/Generation"
    RETURN_TYPES = ("FW_RELAY_OPTIONS",)
    RETURN_NAMES = ("relay_options",)
    FUNCTION = "build"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 10.0, "step": 0.05}),
                "video_window_scale": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 4.0, "step": 0.05}),
                "audio_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 10.0, "step": 0.05}),
                "audio_window_scale": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 4.0, "step": 0.05}),
            },
            "optional": {
                "audio_epsilon": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 0.99, "step": 0.0001}),
            },
        }

    def build(self, video_strength, video_window_scale, audio_strength,
              audio_window_scale, audio_epsilon=0.0):
        opts = {
            "video_strength": video_strength,
            "video_window_scale": video_window_scale,
            "audio_epsilon": audio_epsilon if audio_epsilon > 0 else None,
            "audio_strength": audio_strength,
            "audio_window_scale": audio_window_scale,
        }
        return (opts,)
