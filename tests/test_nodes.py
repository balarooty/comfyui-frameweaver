from nodes import NODE_CLASS_MAPPINGS


def test_node_registry_contains_expected_nodes():
    for name in [
        "FW_ScenePromptEvolver",
        "FW_ContinuityEncoder",
        "FW_LTX23Settings",
        "FW_FrameBridge",
        "FW_SmartAssembler",
    ]:
        assert name in NODE_CLASS_MAPPINGS


def test_ltx_settings_defaults():
    cls = NODE_CLASS_MAPPINGS["FW_LTX23Settings"]
    result = cls().settings(
        1281,
        721,
        96,
        24,
        "ltx-2.3-22b-dev-fp8.safetensors",
        "ltx-2.3-22b-distilled-lora-384.safetensors",
        "gemma_3_12B_it_fp4_mixed.safetensors",
        "ltx-2.3-spatial-upscaler-x2-1.1.safetensors",
    )
    assert result[:4] == (1280, 704, 97, 24)
    assert result[5] == "ltx-2.3-22b-dev-fp8.safetensors"


def test_continuity_encoder_does_not_fake_clip_embeddings():
    anchor = {"style_description": "same lens", "identity_description": "same character"}
    prompt, state = NODE_CLASS_MAPPINGS["FW_ContinuityEncoder"]().encode(anchor, "walk forward", 0.5)
    assert "same lens" in prompt
    assert "same character" in prompt
    assert state["scene_count"] == 1
