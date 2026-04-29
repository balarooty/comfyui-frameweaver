from .ai.whisper_transcriber import FW_WhisperTranscriber
from .bridge.frame_bridge import FW_FrameBridge
from .bridge.last_frame_extractor import FW_LastFrameExtractor
from .continuity.continuity_encoder import FW_ContinuityEncoder
from .continuity.style_anchor import FW_StyleAnchor
from .generation.decode_video import FW_DecodeVideo
from .generation.latent_guide_injector import FW_LatentGuideInjector
from .generation.latent_video_init import FW_LatentVideoInit
from .generation.ltx23_settings import FW_LTX23Settings
from .generation.ltx_sequencer import FW_LTXSequencer
from .generation.preroll_compensator import FW_PrerollCompensator, FW_FrameTrimmer
from .generation.scene_sampler import FW_SceneSampler
from .inputs.load_starter_frame import FW_LoadStarterFrame
from .inputs.multi_image_loader import FW_MultiImageLoader
from .inputs.scene_duration_list import FW_SceneDurationList
from .inputs.scene_prompt_evolver import FW_ScenePromptEvolver, FW_ScenePromptSelector
from .inputs.speech_length_calc import FW_SpeechLengthCalc
from .inputs.audio_splitter import FW_AudioSplitter
from .output.auto_queue import FW_AutoQueue
from .output.scene_collector import FW_SceneCollector
from .output.smart_assembler import FW_SmartAssembler
from .postprocess.color_match import FW_ColorMatch
from .postprocess.film_grain import FW_FilmGrain
from .postprocess.cinematic_polish import FW_CinematicPolish
from .postprocess.lut_system import FW_LUTApply, FW_LUTCreate
from .sequencing.global_sequencer import FW_GlobalSequencer
from .ux.quick_pipeline import FW_QuickPipeline

NODE_CLASS_MAPPINGS = {
    "FW_ScenePromptEvolver": FW_ScenePromptEvolver,
    "FW_ScenePromptSelector": FW_ScenePromptSelector,
    "FW_SceneDurationList": FW_SceneDurationList,
    "FW_LoadStarterFrame": FW_LoadStarterFrame,
    "FW_MultiImageLoader": FW_MultiImageLoader,
    "FW_SpeechLengthCalc": FW_SpeechLengthCalc,
    "FW_GlobalSequencer": FW_GlobalSequencer,
    "FW_StyleAnchor": FW_StyleAnchor,
    "FW_ContinuityEncoder": FW_ContinuityEncoder,
    "FW_LTX23Settings": FW_LTX23Settings,
    "FW_LTXSequencer": FW_LTXSequencer,
    "FW_PrerollCompensator": FW_PrerollCompensator,
    "FW_FrameTrimmer": FW_FrameTrimmer,
    "FW_LatentVideoInit": FW_LatentVideoInit,
    "FW_LatentGuideInjector": FW_LatentGuideInjector,
    "FW_SceneSampler": FW_SceneSampler,
    "FW_DecodeVideo": FW_DecodeVideo,
    "FW_LastFrameExtractor": FW_LastFrameExtractor,
    "FW_FrameBridge": FW_FrameBridge,
    "FW_SceneCollector": FW_SceneCollector,
    "FW_SmartAssembler": FW_SmartAssembler,
    "FW_QuickPipeline": FW_QuickPipeline,
    "FW_ColorMatch": FW_ColorMatch,
    "FW_FilmGrain": FW_FilmGrain,
    "FW_CinematicPolish": FW_CinematicPolish,
    "FW_LUTApply": FW_LUTApply,
    "FW_LUTCreate": FW_LUTCreate,
    "FW_AudioSplitter": FW_AudioSplitter,
    "FW_AutoQueue": FW_AutoQueue,
    "FW_WhisperTranscriber": FW_WhisperTranscriber,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FW_ScenePromptEvolver": "FrameWeaver Scene Prompt Evolver",
    "FW_ScenePromptSelector": "FrameWeaver Scene Prompt Selector",
    "FW_SceneDurationList": "FrameWeaver Scene Duration List",
    "FW_LoadStarterFrame": "FrameWeaver Starter Frame",
    "FW_MultiImageLoader": "FrameWeaver Multi Image Loader",
    "FW_SpeechLengthCalc": "FrameWeaver Speech Length Calculator",
    "FW_GlobalSequencer": "FrameWeaver Global Sequencer",
    "FW_StyleAnchor": "FrameWeaver Style Anchor",
    "FW_ContinuityEncoder": "FrameWeaver Continuity Encoder",
    "FW_LTX23Settings": "FrameWeaver LTX 2.3 Settings",
    "FW_LTXSequencer": "FrameWeaver LTX Sequencer",
    "FW_PrerollCompensator": "FrameWeaver Preroll Compensator",
    "FW_FrameTrimmer": "FrameWeaver Frame Trimmer",
    "FW_LatentVideoInit": "FrameWeaver Latent Video Init",
    "FW_LatentGuideInjector": "FrameWeaver Latent Guide Injector",
    "FW_SceneSampler": "FrameWeaver Scene Sampler",
    "FW_DecodeVideo": "FrameWeaver Decode Video",
    "FW_LastFrameExtractor": "FrameWeaver Last Frame Extractor",
    "FW_FrameBridge": "FrameWeaver Frame Bridge",
    "FW_SceneCollector": "FrameWeaver Scene Collector",
    "FW_SmartAssembler": "FrameWeaver Smart Assembler",
    "FW_QuickPipeline": "FrameWeaver Quick Pipeline",
    "FW_ColorMatch": "FrameWeaver Color Match",
    "FW_FilmGrain": "FrameWeaver Film Grain",
    "FW_CinematicPolish": "FrameWeaver Cinematic Polish",
    "FW_LUTApply": "FrameWeaver LUT Apply",
    "FW_LUTCreate": "FrameWeaver LUT Create",
    "FW_AudioSplitter": "FrameWeaver Audio Splitter",
    "FW_AutoQueue": "FrameWeaver Auto Queue",
    "FW_WhisperTranscriber": "FrameWeaver Whisper Transcriber",
}
