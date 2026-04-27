try:
    from ...utils.vram_manager import cleanup_vram
except ImportError:
    from utils.vram_manager import cleanup_vram


class FW_SceneSampler:
    CATEGORY = "FrameWeaver/Generation"
    RETURN_TYPES = ("INT", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("seed", "sampler_name", "sigma_schedule", "cleanup_status")
    FUNCTION = "settings"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "seed": ("INT", {"default": 42, "min": 0, "max": 0xFFFFFFFFFFFFFFFF}),
                "sampler_name": (
                    ["euler_cfg_pp", "euler_ancestral_cfg_pp", "euler", "dpmpp_2m"],
                    {"default": "euler_cfg_pp"},
                ),
                "sigma_schedule": (
                    "STRING",
                    {"default": "1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0"},
                ),
                "cleanup_before_next_stage": ("BOOLEAN", {"default": False}),
            }
        }

    def settings(self, seed, sampler_name, sigma_schedule, cleanup_before_next_stage):
        status = cleanup_vram() if cleanup_before_next_stage else "cleanup_disabled"
        return (int(seed), sampler_name, sigma_schedule, status)
