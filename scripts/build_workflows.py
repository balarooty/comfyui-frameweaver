import copy
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def next_ids(workflow):
    node_id = max(node["id"] for node in workflow["nodes"] if isinstance(node.get("id"), int)) + 1
    link_id = max((link[0] for link in workflow.get("links", [])), default=0) + 1
    return node_id, link_id


def node(node_id, node_type, pos, size=(360, 160), title=None, widgets=None, inputs=None, outputs=None):
    data = {
        "id": node_id,
        "type": node_type,
        "pos": list(pos),
        "size": list(size),
        "flags": {},
        "order": node_id,
        "mode": 0,
        "inputs": inputs or [],
        "outputs": outputs or [],
        "properties": {"Node name for S&R": node_type},
        "widgets_values": widgets or [],
    }
    if title:
        data["title"] = title
    return data


def output(name, typ, links=None):
    return {"name": name, "type": typ, "links": links or []}


def input_socket(name, typ, link=None, label=None):
    data = {"name": name, "type": typ, "link": link}
    if label:
        data["label"] = label
    return data


def add_link(workflow, link_id, origin_id, origin_slot, target_id, target_slot, typ):
    workflow["links"].append([link_id, origin_id, origin_slot, target_id, target_slot, typ])


def reset_links(nodes):
    for nd in nodes:
        for out in nd.get("outputs", []) or []:
            if out.get("links") is None:
                out["links"] = []


def add_i2v_frameweaver_nodes(workflow):
    reset_links(workflow["nodes"])
    node_id, link_id = next_ids(workflow)
    ltx_node = next(nd for nd in workflow["nodes"] if nd["type"] == "b94257db-cdc1-45d3-8913-ca61e782d9c1")
    image_node = next(nd for nd in workflow["nodes"] if nd["type"] == "LoadImage")

    # Replace the direct LoadImage -> LTX link with LoadImage -> StarterFrame -> LTX.
    original_image_link = next(link for link in workflow["links"] if link[1] == image_node["id"] and link[3] == ltx_node["id"])
    workflow["links"].remove(original_image_link)
    image_node["outputs"][0]["links"] = []
    ltx_node["inputs"][0]["link"] = None

    ids = {}
    ids["settings"] = node_id
    node_id += 1
    ids["starter"] = node_id
    node_id += 1
    ids["prompts"] = node_id
    node_id += 1
    ids["selector"] = node_id
    node_id += 1
    ids["anchor"] = node_id
    node_id += 1
    ids["continuity"] = node_id
    node_id += 1

    workflow["nodes"].extend(
        [
            node(
                ids["settings"],
                "FW_LTX23Settings",
                (-1040, 4130),
                (420, 260),
                widgets=[1280, 720, 97, 24],
                outputs=[
                    output("width", "INT"),
                    output("height", "INT"),
                    output("frames", "INT"),
                    output("fps", "INT"),
                    output("duration_seconds", "FLOAT"),
                    output("checkpoint_name", "STRING"),
                    output("distilled_lora_name", "STRING"),
                    output("text_encoder_name", "STRING"),
                    output("upscale_model_name", "STRING"),
                ],
            ),
            node(
                ids["starter"],
                "FW_LoadStarterFrame",
                (-1040, 4450),
                (420, 180),
                widgets=[1280, 720],
                inputs=[
                    input_socket("image", "IMAGE"),
                    input_socket("target_width", "INT"),
                    input_socket("target_height", "INT"),
                ],
                outputs=[output("image", "IMAGE"), output("width", "INT"), output("height", "INT")],
            ),
            node(
                ids["prompts"],
                "FW_ScenePromptEvolver",
                (-1540, 4130),
                (440, 430),
                widgets=[
                    "cinematic, coherent identity, high quality motion",
                    "blurry, low quality, flicker, inconsistent identity",
                    "A character starts moving through the first scene with clear physical action.",
                    "cumulative",
                ],
                outputs=[
                    output("prompt_list", "FW_PROMPT_LIST"),
                    output("scene_1_positive", "STRING"),
                    output("negative", "STRING"),
                    output("scene_count", "INT"),
                ],
            ),
            node(
                ids["selector"],
                "FW_ScenePromptSelector",
                (-1040, 4680),
                (360, 140),
                widgets=[1],
                inputs=[input_socket("prompt_list", "FW_PROMPT_LIST"), input_socket("scene_index", "INT")],
                outputs=[
                    output("positive", "STRING"),
                    output("negative", "STRING"),
                    output("bridge_prompt", "STRING"),
                    output("selected_index", "INT"),
                ],
            ),
            node(
                ids["anchor"],
                "FW_StyleAnchor",
                (-560, 4450),
                (420, 220),
                widgets=[
                    "Preserve subject identity, wardrobe, lighting, palette, and lens.",
                    "The same primary character remains recognizable across scenes.",
                ],
                inputs=[
                    input_socket("reference_image", "IMAGE"),
                    input_socket("style_description", "STRING"),
                    input_socket("identity_description", "STRING"),
                ],
                outputs=[output("style_anchor", "FW_STYLE_ANCHOR"), output("reference_image", "IMAGE")],
            ),
            node(
                ids["continuity"],
                "FW_ContinuityEncoder",
                (-560, 4720),
                (420, 190),
                widgets=[0.35],
                inputs=[
                    input_socket("style_anchor", "FW_STYLE_ANCHOR"),
                    input_socket("scene_prompt", "STRING"),
                    input_socket("style_strength", "FLOAT"),
                    input_socket("bridge_prompt", "STRING"),
                ],
                outputs=[output("positive_prompt", "STRING"), output("scene_state", "FW_SCENE_STATE")],
            ),
        ]
    )

    # Add missing subgraph proxy inputs so settings and prompt can be wired.
    ltx_node["inputs"] = [
        input_socket("input", "IMAGE,MASK", label="first_frame"),
        input_socket("value", "STRING", label="prompt"),
        input_socket("value_1", "BOOLEAN", label="disable_i2v"),
        input_socket("value_2", "INT", label="width"),
        input_socket("value_3", "INT", label="height"),
        input_socket("value_4", "INT", label="length"),
        input_socket("ckpt_name", "COMBO"),
        input_socket("lora_name", "COMBO", label="distilled_lora"),
        input_socket("text_encoder", "COMBO"),
        input_socket("model_name", "COMBO", label="latent_upscale_model"),
        input_socket("lora_name_1", "COMBO", label="prompt_lora"),
        input_socket("value_5", "INT", label="fps"),
    ]

    def wire(origin, slot, target, target_slot, typ):
        nonlocal link_id
        add_link(workflow, link_id, origin, slot, target, target_slot, typ)
        workflow["nodes_by_id"][origin]["outputs"][slot].setdefault("links", []).append(link_id)
        workflow["nodes_by_id"][target]["inputs"][target_slot]["link"] = link_id
        link_id += 1

    workflow["nodes_by_id"] = {nd["id"]: nd for nd in workflow["nodes"]}
    wire(image_node["id"], 0, ids["starter"], 0, "IMAGE")
    wire(ids["settings"], 0, ids["starter"], 1, "INT")
    wire(ids["settings"], 1, ids["starter"], 2, "INT")
    wire(ids["starter"], 0, ltx_node["id"], 0, "IMAGE")
    wire(ids["prompts"], 0, ids["selector"], 0, "FW_PROMPT_LIST")
    wire(ids["starter"], 0, ids["anchor"], 0, "IMAGE")
    wire(ids["anchor"], 0, ids["continuity"], 0, "FW_STYLE_ANCHOR")
    wire(ids["selector"], 0, ids["continuity"], 1, "STRING")
    wire(ids["selector"], 2, ids["continuity"], 3, "STRING")
    wire(ids["continuity"], 0, ltx_node["id"], 1, "STRING")
    wire(ids["settings"], 0, ltx_node["id"], 3, "INT")
    wire(ids["settings"], 1, ltx_node["id"], 4, "INT")
    wire(ids["settings"], 2, ltx_node["id"], 5, "INT")
    wire(ids["settings"], 3, ltx_node["id"], 11, "INT")

    del workflow["nodes_by_id"]
    workflow["last_link_id"] = link_id - 1
    workflow["last_node_id"] = node_id - 1


def add_ia2v_frameweaver_nodes(workflow):
    reset_links(workflow["nodes"])
    node_id, link_id = next_ids(workflow)
    ltx_node = next(nd for nd in workflow["nodes"] if nd["type"] == "98ee9e5b-467b-40aa-a534-36033f27d0b4")
    image_node = next(nd for nd in workflow["nodes"] if nd["type"] == "LoadImage")

    original_image_link = next(link for link in workflow["links"] if link[1] == image_node["id"] and link[3] == ltx_node["id"])
    original_audio_link = next((link for link in workflow["links"] if link[3] == ltx_node["id"] and link[4] == 1), None)
    workflow["links"].remove(original_image_link)
    image_node["outputs"][0]["links"] = []
    ltx_node["inputs"][0]["link"] = None

    ids = {}
    ids["settings"] = node_id
    node_id += 1
    ids["starter"] = node_id
    node_id += 1
    ids["prompts"] = node_id
    node_id += 1
    ids["selector"] = node_id
    node_id += 1
    ids["anchor"] = node_id
    node_id += 1
    ids["continuity"] = node_id
    node_id += 1

    workflow["nodes"].extend(
        [
            node(
                ids["settings"],
                "FW_LTX23Settings",
                (-1040, 4130),
                (420, 260),
                widgets=[1280, 720, 217, 24],
                outputs=[
                    output("width", "INT"),
                    output("height", "INT"),
                    output("frames", "INT"),
                    output("fps", "INT"),
                    output("duration_seconds", "FLOAT"),
                    output("checkpoint_name", "STRING"),
                    output("distilled_lora_name", "STRING"),
                    output("text_encoder_name", "STRING"),
                    output("upscale_model_name", "STRING"),
                ],
            ),
            node(
                ids["starter"],
                "FW_LoadStarterFrame",
                (-1040, 4450),
                (420, 180),
                widgets=[1280, 720],
                inputs=[
                    input_socket("image", "IMAGE"),
                    input_socket("target_width", "INT"),
                    input_socket("target_height", "INT"),
                ],
                outputs=[output("image", "IMAGE"), output("width", "INT"), output("height", "INT")],
            ),
            node(
                ids["prompts"],
                "FW_ScenePromptEvolver",
                (-1540, 4130),
                (440, 430),
                widgets=[
                    "cinematic, coherent identity, high quality audio-synced motion",
                    "blurry, low quality, flicker, inconsistent identity",
                    "A character performs a clear action that matches the audio.",
                    "cumulative",
                ],
                outputs=[
                    output("prompt_list", "FW_PROMPT_LIST"),
                    output("scene_1_positive", "STRING"),
                    output("negative", "STRING"),
                    output("scene_count", "INT"),
                ],
            ),
            node(
                ids["selector"],
                "FW_ScenePromptSelector",
                (-1040, 4680),
                (360, 140),
                widgets=[1],
                inputs=[input_socket("prompt_list", "FW_PROMPT_LIST"), input_socket("scene_index", "INT")],
                outputs=[
                    output("positive", "STRING"),
                    output("negative", "STRING"),
                    output("bridge_prompt", "STRING"),
                    output("selected_index", "INT"),
                ],
            ),
            node(
                ids["anchor"],
                "FW_StyleAnchor",
                (-560, 4450),
                (420, 220),
                widgets=[
                    "Preserve subject identity, wardrobe, lighting, palette, and lens.",
                    "The same primary character remains recognizable across scenes.",
                ],
                inputs=[
                    input_socket("reference_image", "IMAGE"),
                    input_socket("style_description", "STRING"),
                    input_socket("identity_description", "STRING"),
                ],
                outputs=[output("style_anchor", "FW_STYLE_ANCHOR"), output("reference_image", "IMAGE")],
            ),
            node(
                ids["continuity"],
                "FW_ContinuityEncoder",
                (-560, 4720),
                (420, 190),
                widgets=[0.35],
                inputs=[
                    input_socket("style_anchor", "FW_STYLE_ANCHOR"),
                    input_socket("scene_prompt", "STRING"),
                    input_socket("style_strength", "FLOAT"),
                    input_socket("bridge_prompt", "STRING"),
                ],
                outputs=[output("positive_prompt", "STRING"), output("scene_state", "FW_SCENE_STATE")],
            ),
        ]
    )

    ltx_node["inputs"] = [
        input_socket("input", "IMAGE,MASK", label="first_frame"),
        input_socket("audio", "AUDIO", link=original_audio_link[0] if original_audio_link else None),
        input_socket("value", "STRING", label="prompt"),
        input_socket("value_1", "INT", label="width"),
        input_socket("value_2", "INT", label="height"),
        input_socket("value_3", "INT", label="fps"),
        input_socket("start_index", "FLOAT", label="audio_start"),
        input_socket("value_4", "FLOAT", label="duration"),
        input_socket("ckpt_name", "COMBO"),
        input_socket("lora_name", "COMBO", label="distilled_lora"),
        input_socket("text_encoder", "COMBO"),
        input_socket("model_name", "COMBO", label="upscale_model"),
    ]

    workflow["nodes_by_id"] = {nd["id"]: nd for nd in workflow["nodes"]}

    def wire(origin, slot, target, target_slot, typ):
        nonlocal link_id
        add_link(workflow, link_id, origin, slot, target, target_slot, typ)
        workflow["nodes_by_id"][origin]["outputs"][slot].setdefault("links", []).append(link_id)
        workflow["nodes_by_id"][target]["inputs"][target_slot]["link"] = link_id
        link_id += 1

    wire(image_node["id"], 0, ids["starter"], 0, "IMAGE")
    wire(ids["settings"], 0, ids["starter"], 1, "INT")
    wire(ids["settings"], 1, ids["starter"], 2, "INT")
    wire(ids["starter"], 0, ltx_node["id"], 0, "IMAGE")
    wire(ids["prompts"], 0, ids["selector"], 0, "FW_PROMPT_LIST")
    wire(ids["starter"], 0, ids["anchor"], 0, "IMAGE")
    wire(ids["anchor"], 0, ids["continuity"], 0, "FW_STYLE_ANCHOR")
    wire(ids["selector"], 0, ids["continuity"], 1, "STRING")
    wire(ids["selector"], 2, ids["continuity"], 3, "STRING")
    wire(ids["continuity"], 0, ltx_node["id"], 2, "STRING")
    wire(ids["settings"], 0, ltx_node["id"], 3, "INT")
    wire(ids["settings"], 1, ltx_node["id"], 4, "INT")
    wire(ids["settings"], 3, ltx_node["id"], 5, "INT")
    wire(ids["settings"], 4, ltx_node["id"], 7, "FLOAT")

    del workflow["nodes_by_id"]
    workflow["last_link_id"] = link_id - 1
    workflow["last_node_id"] = node_id - 1


def write_workflow(src_name, dst_name, transform):
    workflow = json.loads((ROOT / "example-workflow" / src_name).read_text(encoding="utf-8"))
    workflow = copy.deepcopy(workflow)
    transform(workflow)
    (ROOT / "workflows" / dst_name).write_text(json.dumps(workflow, indent=2), encoding="utf-8")


def main():
    write_workflow("video_ltx2_3_i2v.json", "frameweaver_ltx23_i2v_single_scene.json", add_i2v_frameweaver_nodes)
    write_workflow("video_ltx2_3_ia2v.json", "frameweaver_ltx23_ia2v_single_scene.json", add_ia2v_frameweaver_nodes)


if __name__ == "__main__":
    main()
