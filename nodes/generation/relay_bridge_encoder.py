"""FW_RelayBridgeEncoder — Bridge FrameWeaver scenes into PromptRelay temporal encoding.

Takes scene data from FW_SceneSplitter and applies PromptRelay temporal
conditioning by patching the model's cross-attention with time-aligned masks.

Supports:
  • Direct connection from FW_SceneSplitter outputs
  • Optional prompt shift blending for scene continuity
  • Optional FW_RelayOptions for advanced per-stream tuning
"""

import logging

try:
    from ...utils.prompt_relay.engine import encode_relay
except ImportError:
    from utils.prompt_relay.engine import encode_relay

log = logging.getLogger(__name__)


class FW_RelayBridgeEncoder:
    """Bridge FrameWeaver scene data into PromptRelay temporal encoding."""

    CATEGORY = "FrameWeaver/Generation"
    RETURN_TYPES = ("MODEL", "CONDITIONING")
    RETURN_NAMES = ("model", "positive")
    FUNCTION = "encode"
    DESCRIPTION = (
        "Takes scene prompts from FW_SceneSplitter and applies PromptRelay temporal conditioning. "
        "Patches the model with cross-attention masks for time-aligned prompt control. "
        "Optionally blends previous scene context via prompt_shift_strength for continuity."
    )
    SEARCH_ALIASES = [
        "relay encode", "temporal encode", "prompt relay",
        "scene encode", "prompt shift", "bridge encoder",
    ]

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "latent": ("LATENT",),
                "global_prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Global style/identity prompt. Connect from FW_SceneSplitter.global_prompt.",
                }),
                "local_prompts": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Pipe-delimited temporal prompts. Connect from FW_SceneSplitter.local_prompts.",
                }),
                "segment_lengths": ("STRING", {
                    "default": "",
                    "tooltip": "Comma-separated frame counts. Connect from FW_SceneSplitter.segment_lengths.",
                }),
                "epsilon": ("FLOAT", {
                    "default": 0.001, "min": 0.000001, "max": 0.99, "step": 0.0001,
                    "tooltip": (
                        "PromptRelay penalty decay parameter. "
                        "Lower values produce sharper temporal boundaries (paper default 0.001). "
                        "For softer cross-scene transitions, try 0.5 or higher."
                    ),
                }),
            },
            "optional": {
                "prompt_shift_strength": ("FLOAT", {
                    "default": 0.0, "min": 0.0, "max": 1.0, "step": 0.05,
                    "tooltip": (
                        "Blend strength for previous scene context. "
                        "0 = no blending (hard scene cut), 1 = full carry-over. "
                        "0.2–0.4 is recommended for natural continuity."
                    ),
                }),
                "previous_prompt": ("STRING", {
                    "forceInput": True,
                    "tooltip": "Previous scene's prompt for continuity blending.",
                }),
                "relay_options": ("FW_RELAY_OPTIONS", {
                    "tooltip": "Advanced per-stream tuning from FW_RelayOptions.",
                }),
            },
        }

    @classmethod
    def VALIDATE_INPUTS(cls, global_prompt, local_prompts, segment_lengths, **kwargs):
        for name, val in (("global_prompt", global_prompt),
                          ("local_prompts", local_prompts),
                          ("segment_lengths", segment_lengths)):
            if val is None:
                return (
                    f"'{name}' is None. Likely causes: a stale workflow JSON "
                    "saved with null, or an upstream node returning None. "
                    "Set the field to an empty string or fix the upstream connection."
                )
        return True

    def encode(self, model, clip, latent, global_prompt, local_prompts,
               segment_lengths, epsilon, prompt_shift_strength=0.0,
               previous_prompt=None, relay_options=None):
        # ---- Prompt shift: blend previous scene context ----
        effective_global = global_prompt or ""

        if (prompt_shift_strength > 0.0
                and previous_prompt
                and isinstance(previous_prompt, str)
                and previous_prompt.strip()):

            prev = previous_prompt.strip()
            curr = effective_global.strip()

            if prompt_shift_strength >= 1.0:
                # Full carry-over: prepend previous prompt entirely
                effective_global = f"{prev}, transitioning to: {curr}"
            else:
                # Partial blend: weight the carry-over
                # Use PromptRelay-compatible weighting hint
                effective_global = (
                    f"{curr}, with subtle continuity from: {prev}"
                )
            log.info(
                "[FW_RelayBridgeEncoder] Prompt shift %.2f: blended previous scene context",
                prompt_shift_strength,
            )

        # Ensure we have valid strings (not None)
        effective_local = local_prompts or ""
        effective_segments = segment_lengths or ""

        # ---- Delegate to the PromptRelay engine ----
        patched_model, conditioning = encode_relay(
            model=model,
            clip=clip,
            latent=latent,
            global_prompt=effective_global,
            local_prompts=effective_local,
            segment_lengths=effective_segments,
            epsilon=epsilon,
            relay_options=relay_options,
        )

        return (patched_model, conditioning)
