"""FrameWeaver — Node Registry

Each node is imported in its own try/except so a single broken node
never prevents the other nodes from loading. Uses relative imports
to avoid collision with ComfyUI's own nodes.py module.
"""

import os
import sys

# Ensure the package root is on sys.path for fallback bare imports
# inside individual node files (e.g. "from utils.validation import ...").
_PKG_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PKG_ROOT not in sys.path:
    sys.path.insert(0, _PKG_ROOT)

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
_IMPORT_ERRORS = []


def _reg(class_name, display_name, cls):
    """Register a successfully imported node class."""
    NODE_CLASS_MAPPINGS[class_name] = cls
    NODE_DISPLAY_NAME_MAPPINGS[class_name] = display_name


# ---- Input nodes ---- #
try:
    from .inputs.scene_prompt_evolver import FW_ScenePromptEvolver, FW_ScenePromptSelector
    _reg("FW_ScenePromptEvolver", "FrameWeaver Scene Prompt Evolver", FW_ScenePromptEvolver)
    _reg("FW_ScenePromptSelector", "FrameWeaver Scene Prompt Selector", FW_ScenePromptSelector)
except Exception as e:
    _IMPORT_ERRORS.append(("FW_ScenePromptEvolver/Selector", str(e)))

try:
    from .inputs.scene_duration_list import FW_SceneDurationList
    _reg("FW_SceneDurationList", "FrameWeaver Scene Duration List", FW_SceneDurationList)
except Exception as e:
    _IMPORT_ERRORS.append(("FW_SceneDurationList", str(e)))

try:
    from .inputs.load_starter_frame import FW_LoadStarterFrame
    _reg("FW_LoadStarterFrame", "FrameWeaver Starter Frame", FW_LoadStarterFrame)
except Exception as e:
    _IMPORT_ERRORS.append(("FW_LoadStarterFrame", str(e)))

try:
    from .inputs.multi_image_loader import FW_MultiImageLoader
    _reg("FW_MultiImageLoader", "FrameWeaver Multi Image Loader", FW_MultiImageLoader)
except Exception as e:
    _IMPORT_ERRORS.append(("FW_MultiImageLoader", str(e)))

try:
    from .inputs.speech_length_calc import FW_SpeechLengthCalc
    _reg("FW_SpeechLengthCalc", "FrameWeaver Speech Length Calculator", FW_SpeechLengthCalc)
except Exception as e:
    _IMPORT_ERRORS.append(("FW_SpeechLengthCalc", str(e)))

try:
    from .inputs.audio_splitter import FW_AudioSplitter
    _reg("FW_AudioSplitter", "FrameWeaver Audio Splitter", FW_AudioSplitter)
except Exception as e:
    _IMPORT_ERRORS.append(("FW_AudioSplitter", str(e)))

# ---- Sequencing ---- #
try:
    from .sequencing.global_sequencer import FW_GlobalSequencer
    _reg("FW_GlobalSequencer", "FrameWeaver Global Sequencer", FW_GlobalSequencer)
except Exception as e:
    _IMPORT_ERRORS.append(("FW_GlobalSequencer", str(e)))

try:
    from .sequencing.scene_splitter import FW_SceneSplitter
    _reg("FW_SceneSplitter", "FrameWeaver Scene Splitter", FW_SceneSplitter)
except Exception as e:
    _IMPORT_ERRORS.append(("FW_SceneSplitter", str(e)))

# ---- Continuity ---- #
try:
    from .continuity.style_anchor import FW_StyleAnchor
    _reg("FW_StyleAnchor", "FrameWeaver Style Anchor", FW_StyleAnchor)
except Exception as e:
    _IMPORT_ERRORS.append(("FW_StyleAnchor", str(e)))

try:
    from .continuity.continuity_encoder import FW_ContinuityEncoder
    _reg("FW_ContinuityEncoder", "FrameWeaver Continuity Encoder", FW_ContinuityEncoder)
except Exception as e:
    _IMPORT_ERRORS.append(("FW_ContinuityEncoder", str(e)))

# ---- Generation ---- #
try:
    from .generation.ltx23_settings import FW_LTX23Settings
    _reg("FW_LTX23Settings", "FrameWeaver LTX 2.3 Settings", FW_LTX23Settings)
except Exception as e:
    _IMPORT_ERRORS.append(("FW_LTX23Settings", str(e)))

try:
    from .generation.ltx_sequencer import FW_LTXSequencer
    _reg("FW_LTXSequencer", "FrameWeaver LTX Sequencer", FW_LTXSequencer)
except Exception as e:
    _IMPORT_ERRORS.append(("FW_LTXSequencer", str(e)))

try:
    from .generation.preroll_compensator import FW_PrerollCompensator, FW_FrameTrimmer
    _reg("FW_PrerollCompensator", "FrameWeaver Preroll Compensator", FW_PrerollCompensator)
    _reg("FW_FrameTrimmer", "FrameWeaver Frame Trimmer", FW_FrameTrimmer)
except Exception as e:
    _IMPORT_ERRORS.append(("FW_PrerollCompensator/FrameTrimmer", str(e)))

try:
    from .generation.latent_video_init import FW_LatentVideoInit
    _reg("FW_LatentVideoInit", "FrameWeaver Latent Video Init", FW_LatentVideoInit)
except Exception as e:
    _IMPORT_ERRORS.append(("FW_LatentVideoInit", str(e)))

try:
    from .generation.latent_guide_injector import FW_LatentGuideInjector
    _reg("FW_LatentGuideInjector", "FrameWeaver Latent Guide Injector", FW_LatentGuideInjector)
except Exception as e:
    _IMPORT_ERRORS.append(("FW_LatentGuideInjector", str(e)))

try:
    from .generation.scene_sampler import FW_SceneSampler
    _reg("FW_SceneSampler", "FrameWeaver Scene Sampler", FW_SceneSampler)
except Exception as e:
    _IMPORT_ERRORS.append(("FW_SceneSampler", str(e)))

try:
    from .generation.decode_video import FW_DecodeVideo
    _reg("FW_DecodeVideo", "FrameWeaver Decode Video", FW_DecodeVideo)
except Exception as e:
    _IMPORT_ERRORS.append(("FW_DecodeVideo", str(e)))

try:
    from .generation.temporal_prompt_encode import FW_TemporalPromptEncode
    _reg("FW_TemporalPromptEncode", "FrameWeaver Temporal Prompt Encode", FW_TemporalPromptEncode)
except Exception as e:
    _IMPORT_ERRORS.append(("FW_TemporalPromptEncode", str(e)))

try:
    from .generation.relay_options import FW_RelayOptions
    _reg("FW_RelayOptions", "FrameWeaver Relay Options", FW_RelayOptions)
except Exception as e:
    _IMPORT_ERRORS.append(("FW_RelayOptions", str(e)))

try:
    from .generation.relay_bridge_encoder import FW_RelayBridgeEncoder
    _reg("FW_RelayBridgeEncoder", "FrameWeaver Relay Bridge Encoder", FW_RelayBridgeEncoder)
except Exception as e:
    _IMPORT_ERRORS.append(("FW_RelayBridgeEncoder", str(e)))

# ---- Bridge ---- #
try:
    from .bridge.last_frame_extractor import FW_LastFrameExtractor
    _reg("FW_LastFrameExtractor", "FrameWeaver Last Frame Extractor", FW_LastFrameExtractor)
except Exception as e:
    _IMPORT_ERRORS.append(("FW_LastFrameExtractor", str(e)))

try:
    from .bridge.frame_bridge import FW_FrameBridge
    _reg("FW_FrameBridge", "FrameWeaver Frame Bridge", FW_FrameBridge)
except Exception as e:
    _IMPORT_ERRORS.append(("FW_FrameBridge", str(e)))

# ---- Output ---- #
try:
    from .output.scene_collector import FW_SceneCollector
    _reg("FW_SceneCollector", "FrameWeaver Scene Collector", FW_SceneCollector)
except Exception as e:
    _IMPORT_ERRORS.append(("FW_SceneCollector", str(e)))

try:
    from .output.smart_assembler import FW_SmartAssembler
    _reg("FW_SmartAssembler", "FrameWeaver Smart Assembler", FW_SmartAssembler)
except Exception as e:
    _IMPORT_ERRORS.append(("FW_SmartAssembler", str(e)))

try:
    from .output.auto_queue import FW_AutoQueue
    _reg("FW_AutoQueue", "FrameWeaver Auto Queue", FW_AutoQueue)
except Exception as e:
    _IMPORT_ERRORS.append(("FW_AutoQueue", str(e)))

try:
    from .output.scene_queue import FW_SceneQueue
    _reg("FW_SceneQueue", "FrameWeaver Scene Queue", FW_SceneQueue)
except Exception as e:
    _IMPORT_ERRORS.append(("FW_SceneQueue", str(e)))

try:
    from .output.scene_iterator import FW_SceneIterator
    _reg("FW_SceneIterator", "FrameWeaver Scene Iterator", FW_SceneIterator)
except Exception as e:
    _IMPORT_ERRORS.append(("FW_SceneIterator", str(e)))

# ---- PostProcess ---- #
try:
    from .postprocess.color_match import FW_ColorMatch
    _reg("FW_ColorMatch", "FrameWeaver Color Match", FW_ColorMatch)
except Exception as e:
    _IMPORT_ERRORS.append(("FW_ColorMatch", str(e)))

try:
    from .postprocess.film_grain import FW_FilmGrain
    _reg("FW_FilmGrain", "FrameWeaver Film Grain", FW_FilmGrain)
except Exception as e:
    _IMPORT_ERRORS.append(("FW_FilmGrain", str(e)))

try:
    from .postprocess.cinematic_polish import FW_CinematicPolish
    _reg("FW_CinematicPolish", "FrameWeaver Cinematic Polish", FW_CinematicPolish)
except Exception as e:
    _IMPORT_ERRORS.append(("FW_CinematicPolish", str(e)))

try:
    from .postprocess.lut_system import FW_LUTApply, FW_LUTCreate
    _reg("FW_LUTApply", "FrameWeaver LUT Apply", FW_LUTApply)
    _reg("FW_LUTCreate", "FrameWeaver LUT Create", FW_LUTCreate)
except Exception as e:
    _IMPORT_ERRORS.append(("FW_LUTApply/Create", str(e)))

# ---- AI ---- #
try:
    from .ai.whisper_transcriber import FW_WhisperTranscriber
    _reg("FW_WhisperTranscriber", "FrameWeaver Whisper Transcriber", FW_WhisperTranscriber)
except Exception as e:
    _IMPORT_ERRORS.append(("FW_WhisperTranscriber", str(e)))

# ---- UX ---- #
try:
    from .ux.quick_pipeline import FW_QuickPipeline
    _reg("FW_QuickPipeline", "FrameWeaver Quick Pipeline", FW_QuickPipeline)
except Exception as e:
    _IMPORT_ERRORS.append(("FW_QuickPipeline", str(e)))


# ---- Report ---- #
_TOTAL = 36
_LOADED = len(NODE_CLASS_MAPPINGS)

if _IMPORT_ERRORS:
    print(f"\n[FrameWeaver] ⚠️  {_LOADED}/{_TOTAL} nodes loaded. {len(_IMPORT_ERRORS)} failed:")
    for name, err in _IMPORT_ERRORS:
        print(f"  ❌ {name}: {err}")
    print()
else:
    print(f"[FrameWeaver] ✅ All {_LOADED} nodes loaded successfully")
