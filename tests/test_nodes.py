"""Node registry tests — verifies all 30 nodes are registered correctly."""

from nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS


# All 30 nodes by phase
PHASE_1_NODES = [
    "FW_ScenePromptEvolver", "FW_ScenePromptSelector", "FW_SceneDurationList",
    "FW_LoadStarterFrame", "FW_MultiImageLoader", "FW_SpeechLengthCalc",
    "FW_GlobalSequencer", "FW_StyleAnchor", "FW_ContinuityEncoder",
    "FW_LatentVideoInit", "FW_LastFrameExtractor", "FW_FrameBridge",
    "FW_SceneCollector", "FW_QuickPipeline",
]

PHASE_2_NODES = [
    "FW_LTX23Settings", "FW_LTXSequencer", "FW_PrerollCompensator",
    "FW_FrameTrimmer", "FW_LatentGuideInjector", "FW_SceneSampler",
    "FW_DecodeVideo",
]

PHASE_3_NODES = [
    "FW_ColorMatch", "FW_FilmGrain", "FW_CinematicPolish",
    "FW_LUTApply", "FW_LUTCreate",
]

PHASE_4_NODES = [
    "FW_AudioSplitter", "FW_AutoQueue", "FW_SmartAssembler",
]

PHASE_5_NODES = [
    "FW_WhisperTranscriber",
]

ALL_NODES = PHASE_1_NODES + PHASE_2_NODES + PHASE_3_NODES + PHASE_4_NODES + PHASE_5_NODES


def test_total_node_count():
    assert len(NODE_CLASS_MAPPINGS) == 30, f"Expected 30 nodes, got {len(NODE_CLASS_MAPPINGS)}"


def test_all_nodes_registered():
    for name in ALL_NODES:
        assert name in NODE_CLASS_MAPPINGS, f"Missing from NODE_CLASS_MAPPINGS: {name}"


def test_all_display_names_exist():
    for name in ALL_NODES:
        assert name in NODE_DISPLAY_NAME_MAPPINGS, f"Missing display name: {name}"


def test_display_names_start_with_frameweaver():
    for name, display in NODE_DISPLAY_NAME_MAPPINGS.items():
        assert display.startswith("FrameWeaver"), f"{name} display name should start with 'FrameWeaver': {display}"


def test_all_classes_have_function():
    for name, cls in NODE_CLASS_MAPPINGS.items():
        assert hasattr(cls, "FUNCTION"), f"{name} missing FUNCTION attribute"
        assert isinstance(cls.FUNCTION, str), f"{name}.FUNCTION should be a string"


def test_all_classes_have_category():
    for name, cls in NODE_CLASS_MAPPINGS.items():
        assert hasattr(cls, "CATEGORY"), f"{name} missing CATEGORY attribute"
        assert cls.CATEGORY.startswith("FrameWeaver"), f"{name}.CATEGORY should start with 'FrameWeaver': {cls.CATEGORY}"


def test_all_classes_have_input_types():
    for name, cls in NODE_CLASS_MAPPINGS.items():
        assert hasattr(cls, "INPUT_TYPES"), f"{name} missing INPUT_TYPES"
        it = cls.INPUT_TYPES()
        assert "required" in it, f"{name} INPUT_TYPES must have 'required'"


def test_all_classes_have_return_types():
    for name, cls in NODE_CLASS_MAPPINGS.items():
        assert hasattr(cls, "RETURN_TYPES"), f"{name} missing RETURN_TYPES"
        assert isinstance(cls.RETURN_TYPES, tuple), f"{name}.RETURN_TYPES should be a tuple"


def test_ltx_settings_defaults():
    cls = NODE_CLASS_MAPPINGS["FW_LTX23Settings"]
    result = cls().settings(
        1281, 721, 96, 24,
        "ltx-2.3-22b-dev-fp8.safetensors",
        "ltx-2.3-22b-distilled-lora-384.safetensors",
        "gemma_3_12B_it_fp4_mixed.safetensors",
        "ltx-2.3-spatial-upscaler-x2-1.1.safetensors",
    )
    assert result[:4] == (1280, 704, 97, 24)
    assert result[5] == "ltx-2.3-22b-dev-fp8.safetensors"


def test_continuity_encoder_prompt_injection():
    anchor = {"style_description": "same lens", "identity_description": "same character"}
    prompt, state = NODE_CLASS_MAPPINGS["FW_ContinuityEncoder"]().encode(anchor, "walk forward", 0.5)
    assert "same lens" in prompt
    assert "same character" in prompt
    assert state["scene_count"] == 1
