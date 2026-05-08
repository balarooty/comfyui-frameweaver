"""FrameWeaver — Node Registry

Bulletproof import system: each node is imported in its own try/except
so a single broken node never prevents the other nodes from loading.
Failed imports are logged to the ComfyUI console for easy debugging.
"""

import os
import sys
import traceback

# ------------------------------------------------------------------ #
#  Ensure the package root is on sys.path so that bare fallback
#  imports like "from utils.validation import ..." always resolve
#  to THIS package's utils directory, not something else on the path.
# ------------------------------------------------------------------ #
_PKG_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PKG_ROOT not in sys.path:
    sys.path.insert(0, _PKG_ROOT)


# ------------------------------------------------------------------ #
#  Per-node imports with individual error handling
# ------------------------------------------------------------------ #

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

_IMPORT_ERRORS = []


def _register(module_path, class_name, display_name):
    """Import a single node class and register it."""
    try:
        # Use relative import from this package
        parts = module_path.split(".")
        mod = __import__(f"nodes.{module_path}", fromlist=[class_name])  # noqa: F841
        cls = getattr(mod, class_name)
        NODE_CLASS_MAPPINGS[class_name] = cls
        NODE_DISPLAY_NAME_MAPPINGS[class_name] = display_name
    except Exception as e:
        _IMPORT_ERRORS.append((class_name, str(e)))
        # Also try the relative import path
        try:
            from importlib import import_module
            mod = import_module(f".{module_path}", package="nodes")
            cls = getattr(mod, class_name)
            NODE_CLASS_MAPPINGS[class_name] = cls
            NODE_DISPLAY_NAME_MAPPINGS[class_name] = display_name
            # Remove from errors since it succeeded on retry
            _IMPORT_ERRORS.pop()
        except Exception:
            pass


# ---- Input nodes ---- #
_register("inputs.scene_prompt_evolver", "FW_ScenePromptEvolver", "FrameWeaver Scene Prompt Evolver")
_register("inputs.scene_prompt_evolver", "FW_ScenePromptSelector", "FrameWeaver Scene Prompt Selector")
_register("inputs.scene_duration_list", "FW_SceneDurationList", "FrameWeaver Scene Duration List")
_register("inputs.load_starter_frame", "FW_LoadStarterFrame", "FrameWeaver Starter Frame")
_register("inputs.multi_image_loader", "FW_MultiImageLoader", "FrameWeaver Multi Image Loader")
_register("inputs.speech_length_calc", "FW_SpeechLengthCalc", "FrameWeaver Speech Length Calculator")
_register("inputs.audio_splitter", "FW_AudioSplitter", "FrameWeaver Audio Splitter")

# ---- Sequencing ---- #
_register("sequencing.global_sequencer", "FW_GlobalSequencer", "FrameWeaver Global Sequencer")

# ---- Continuity ---- #
_register("continuity.style_anchor", "FW_StyleAnchor", "FrameWeaver Style Anchor")
_register("continuity.continuity_encoder", "FW_ContinuityEncoder", "FrameWeaver Continuity Encoder")

# ---- Generation ---- #
_register("generation.ltx23_settings", "FW_LTX23Settings", "FrameWeaver LTX 2.3 Settings")
_register("generation.ltx_sequencer", "FW_LTXSequencer", "FrameWeaver LTX Sequencer")
_register("generation.preroll_compensator", "FW_PrerollCompensator", "FrameWeaver Preroll Compensator")
_register("generation.preroll_compensator", "FW_FrameTrimmer", "FrameWeaver Frame Trimmer")
_register("generation.latent_video_init", "FW_LatentVideoInit", "FrameWeaver Latent Video Init")
_register("generation.latent_guide_injector", "FW_LatentGuideInjector", "FrameWeaver Latent Guide Injector")
_register("generation.scene_sampler", "FW_SceneSampler", "FrameWeaver Scene Sampler")
_register("generation.decode_video", "FW_DecodeVideo", "FrameWeaver Decode Video")

# ---- Bridge ---- #
_register("bridge.last_frame_extractor", "FW_LastFrameExtractor", "FrameWeaver Last Frame Extractor")
_register("bridge.frame_bridge", "FW_FrameBridge", "FrameWeaver Frame Bridge")

# ---- Output ---- #
_register("output.scene_collector", "FW_SceneCollector", "FrameWeaver Scene Collector")
_register("output.smart_assembler", "FW_SmartAssembler", "FrameWeaver Smart Assembler")
_register("output.auto_queue", "FW_AutoQueue", "FrameWeaver Auto Queue")

# ---- PostProcess ---- #
_register("postprocess.color_match", "FW_ColorMatch", "FrameWeaver Color Match")
_register("postprocess.film_grain", "FW_FilmGrain", "FrameWeaver Film Grain")
_register("postprocess.cinematic_polish", "FW_CinematicPolish", "FrameWeaver Cinematic Polish")
_register("postprocess.lut_system", "FW_LUTApply", "FrameWeaver LUT Apply")
_register("postprocess.lut_system", "FW_LUTCreate", "FrameWeaver LUT Create")

# ---- AI ---- #
_register("ai.whisper_transcriber", "FW_WhisperTranscriber", "FrameWeaver Whisper Transcriber")

# ---- UX ---- #
_register("ux.quick_pipeline", "FW_QuickPipeline", "FrameWeaver Quick Pipeline")


# ------------------------------------------------------------------ #
#  Report results
# ------------------------------------------------------------------ #

_TOTAL = 30
_LOADED = len(NODE_CLASS_MAPPINGS)

if _IMPORT_ERRORS:
    print(f"\n[FrameWeaver] ⚠️  {_LOADED}/{_TOTAL} nodes loaded. {len(_IMPORT_ERRORS)} failed:")
    for name, err in _IMPORT_ERRORS:
        print(f"  ❌ {name}: {err}")
    print()
else:
    print(f"[FrameWeaver] ✅ All {_LOADED} nodes loaded successfully")
