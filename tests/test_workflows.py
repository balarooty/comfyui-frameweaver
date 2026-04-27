import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT / "workflows" / name).read_text(encoding="utf-8"))


def test_i2v_workflow_uses_frameweaver_and_ltx23_defaults():
    workflow = load("frameweaver_ltx23_i2v_single_scene.json")
    node_types = {node["type"] for node in workflow["nodes"]}
    assert "FW_LTX23Settings" in node_types
    assert "FW_ContinuityEncoder" in node_types
    subgraph_nodes = workflow["definitions"]["subgraphs"][0]["nodes"]
    distilled = [node for node in subgraph_nodes if node["type"] == "LoraLoaderModelOnly"][0]
    ckpt = [node for node in subgraph_nodes if node["type"] == "CheckpointLoaderSimple"][0]
    assert distilled["widgets_values"][0] == "ltx-2.3-22b-distilled-lora-384.safetensors"
    assert ckpt["widgets_values"][0] == "ltx-2.3-22b-dev-fp8.safetensors"


def test_i2v_workflow_links_have_existing_nodes():
    workflow = load("frameweaver_ltx23_i2v_single_scene.json")
    node_ids = {node["id"] for node in workflow["nodes"]}
    for link in workflow["links"]:
        assert link[1] in node_ids
        assert link[3] in node_ids


def test_ia2v_workflow_is_connected_to_frameweaver_prompt_and_audio():
    workflow = load("frameweaver_ltx23_ia2v_single_scene.json")
    node_types = {node["type"] for node in workflow["nodes"]}
    assert "FW_ContinuityEncoder" in node_types
    ltx_node = [node for node in workflow["nodes"] if node["type"] == "98ee9e5b-467b-40aa-a534-36033f27d0b4"][0]
    inputs = {item["name"]: item for item in ltx_node["inputs"]}
    assert inputs["audio"]["link"] is not None
    assert inputs["value"]["link"] is not None
    assert inputs["lora_name"]["link"] is None


def test_ltx_combo_inputs_are_not_linked_to_generic_outputs():
    for name, ltx_type in [
        ("frameweaver_ltx23_i2v_single_scene.json", "b94257db-cdc1-45d3-8913-ca61e782d9c1"),
        ("frameweaver_ltx23_ia2v_single_scene.json", "98ee9e5b-467b-40aa-a534-36033f27d0b4"),
    ]:
        workflow = load(name)
        ltx_node = [node for node in workflow["nodes"] if node["type"] == ltx_type][0]
        inputs = {item["name"]: item for item in ltx_node["inputs"]}
        for combo_name in ["ckpt_name", "lora_name", "text_encoder", "model_name"]:
            assert inputs[combo_name]["link"] is None
