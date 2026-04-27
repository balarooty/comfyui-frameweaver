from .bridge.frame_bridge import FW_FrameBridge
from .bridge.last_frame_extractor import FW_LastFrameExtractor
from .continuity.continuity_encoder import FW_ContinuityEncoder
from .continuity.style_anchor import FW_StyleAnchor
from .generation.decode_video import FW_DecodeVideo
from .generation.latent_guide_injector import FW_LatentGuideInjector
from .generation.latent_video_init import FW_LatentVideoInit
from .generation.ltx23_settings import FW_LTX23Settings
from .generation.scene_sampler import FW_SceneSampler
from .inputs.load_starter_frame import FW_LoadStarterFrame
from .inputs.scene_duration_list import FW_SceneDurationList
from .inputs.scene_prompt_evolver import FW_ScenePromptEvolver, FW_ScenePromptSelector
from .output.scene_collector import FW_SceneCollector
from .output.smart_assembler import FW_SmartAssembler
from .ux.quick_pipeline import FW_QuickPipeline

NODE_CLASS_MAPPINGS = {
    "FW_ScenePromptEvolver": FW_ScenePromptEvolver,
    "FW_ScenePromptSelector": FW_ScenePromptSelector,
    "FW_SceneDurationList": FW_SceneDurationList,
    "FW_LoadStarterFrame": FW_LoadStarterFrame,
    "FW_StyleAnchor": FW_StyleAnchor,
    "FW_ContinuityEncoder": FW_ContinuityEncoder,
    "FW_LTX23Settings": FW_LTX23Settings,
    "FW_LatentVideoInit": FW_LatentVideoInit,
    "FW_LatentGuideInjector": FW_LatentGuideInjector,
    "FW_SceneSampler": FW_SceneSampler,
    "FW_DecodeVideo": FW_DecodeVideo,
    "FW_LastFrameExtractor": FW_LastFrameExtractor,
    "FW_FrameBridge": FW_FrameBridge,
    "FW_SceneCollector": FW_SceneCollector,
    "FW_SmartAssembler": FW_SmartAssembler,
    "FW_QuickPipeline": FW_QuickPipeline,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FW_ScenePromptEvolver": "FrameWeaver Scene Prompt Evolver",
    "FW_ScenePromptSelector": "FrameWeaver Scene Prompt Selector",
    "FW_SceneDurationList": "FrameWeaver Scene Duration List",
    "FW_LoadStarterFrame": "FrameWeaver Starter Frame",
    "FW_StyleAnchor": "FrameWeaver Style Anchor",
    "FW_ContinuityEncoder": "FrameWeaver Continuity Encoder",
    "FW_LTX23Settings": "FrameWeaver LTX 2.3 Settings",
    "FW_LatentVideoInit": "FrameWeaver Latent Video Init",
    "FW_LatentGuideInjector": "FrameWeaver Latent Guide Injector",
    "FW_SceneSampler": "FrameWeaver Scene Sampler",
    "FW_DecodeVideo": "FrameWeaver Decode Video",
    "FW_LastFrameExtractor": "FrameWeaver Last Frame Extractor",
    "FW_FrameBridge": "FrameWeaver Frame Bridge",
    "FW_SceneCollector": "FrameWeaver Scene Collector",
    "FW_SmartAssembler": "FrameWeaver Smart Assembler",
    "FW_QuickPipeline": "FrameWeaver Quick Pipeline",
}
