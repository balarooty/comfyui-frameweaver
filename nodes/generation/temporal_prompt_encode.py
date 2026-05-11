import logging

try:
    from ...utils.prompt_relay.engine import encode_relay
except ImportError:
    from utils.prompt_relay.engine import encode_relay

log = logging.getLogger(__name__)


class FW_TemporalPromptEncode:
    CATEGORY = "FrameWeaver/Generation"
    RETURN_TYPES = ("MODEL", "CONDITIONING")
    RETURN_NAMES = ("model", "positive")
    FUNCTION = "encode"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "latent": ("LATENT",),
                "global_prompt": ("STRING", {"multiline": True, "default": ""}),
                "local_prompts": ("STRING", {"multiline": True, "default": ""}),
                "segment_lengths": ("STRING", {"default": ""}),
                "epsilon": ("FLOAT", {"default": 0.001, "min": 0.000001, "max": 0.99, "step": 0.0001}),
            },
            "optional": {
                "relay_options": ("FW_RELAY_OPTIONS",),
            },
        }

    def encode(self, model, clip, latent, global_prompt, local_prompts,
               segment_lengths, epsilon, relay_options=None):
        patched, conditioning = encode_relay(
            model, clip, latent, global_prompt, local_prompts,
            segment_lengths, epsilon, relay_options,
        )
        return (patched, conditioning)
