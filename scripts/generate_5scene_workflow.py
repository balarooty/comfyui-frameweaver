#!/usr/bin/env python3
"""Generate FrameWeaver 5-scene, 10s/scene workflow JSON.

Valid ComfyUI workflow format with proper node inputs/outputs and links.
"""

import json
import sys


def make_node(node_id, node_type, pos, widgets=None, size=None):
    """Build a ComfyUI node dict."""
    return {
        "id": node_id,
        "type": node_type,
        "pos": pos,
        "size": size or [320, 180],
        "flags": {},
        "order": node_id,
        "mode": 0,
        "inputs": [],
        "outputs": [],
        "properties": {},
        "widgets_values": widgets or [],
    }


def make_slot(name, stype, shape=None):
    s = {"name": name, "type": stype, "links": []}
    if shape is not None:
        s["shape"] = shape
    return s


def make_input_slot(name, stype, link=None):
    return {"name": name, "type": stype, "link": link}


def main():
    nodes = []
    links = []
    link_id = 1
    nid = 1

    def add(node):
        nonlocal nid
        nodes.append(node)
        nid += 1
        return node["id"]

    def connect(from_node_idx, from_slot, to_node_idx, to_slot):
        nonlocal link_id
        links.append([link_id, from_node_idx, from_slot, to_node_idx, to_slot, "*"])
        # Update node slot references
        for n in nodes:
            if n["id"] == from_node_idx:
                while len(n["outputs"]) <= from_slot:
                    n["outputs"].append(None)
                if n["outputs"][from_slot] is None:
                    n["outputs"][from_slot] = make_slot(f"output_{from_slot}", "*")
                n["outputs"][from_slot]["links"].append(link_id)
            if n["id"] == to_node_idx:
                while len(n["inputs"]) <= to_slot:
                    n["inputs"].append(None)
                if n["inputs"][to_slot] is None:
                    n["inputs"][to_slot] = make_input_slot(f"input_{to_slot}", "*")
                n["inputs"][to_slot]["link"] = link_id
        link_id += 1

    # ------------------------------------------------------------------ #
    #  GLOBAL SETUP
    # ------------------------------------------------------------------ #

    load_image = add(make_node(nid, "LoadImage", [-1100, -250], ["starter_image.png"], [300, 80]))
    nodes[-1]["outputs"] = [make_slot("IMAGE", "IMAGE")]

    style_anchor = add(make_node(nid, "FW_StyleAnchor", [-1100, -130],
        ["Preserve the same subject identity, wardrobe, art direction, lighting, lens, and color palette.",
         "The same primary character remains recognizable across all scenes."], [340, 140]))
    nodes[-1]["inputs"] = [make_input_slot("reference_image", "IMAGE")]
    nodes[-1]["outputs"] = [make_slot("style_anchor", "FW_STYLE_ANCHOR"), make_slot("reference_image", "IMAGE")]
    connect(load_image, 0, style_anchor, 0)

    prompt_evolver = add(make_node(nid, "FW_ScenePromptEvolver", [-1100, 80],
        ["cinematic, high quality, coherent character identity, stable wardrobe, detailed motion",
         "blurry, low quality, warped anatomy, flicker, inconsistent identity, static shot",
         "Scene 1: The character begins their journey, walking through an open field at dawn.",
         "cumulative",
         "Scene 2: They arrive at a mysterious ancient gate, hesitation in their step.",
         "Scene 3: Pushing through the gate, they enter a luminous forest filled with floating lights.",
         "Scene 4: A sudden storm rolls in — wind, rain, and dramatic lightning.",
         "Scene 5: As the storm clears, they stand on a cliff edge, looking out at a vast new world.",
         "", "", "", "", "", ""], [360, 340]))
    nodes[-1]["outputs"] = [make_slot("prompt_list", "FW_PROMPT_LIST"), make_slot("scene_1_positive", "STRING"),
                            make_slot("negative", "STRING"), make_slot("scene_count", "INT")]

    ltx_settings = add(make_node(nid, "FW_LTX23Settings", [-600, -250],
        [1280, 720, "frames", 241, 4.0, 24,
         "ltx-2.3-22b-dev-fp8.safetensors",
         "ltx-2.3-22b-distilled-lora-384.safetensors",
         "gemma_3_12B_it_fp4_mixed.safetensors",
         "ltx-2.3-spatial-upscaler-x2-1.1.safetensors"], [340, 280]))
    nodes[-1]["outputs"] = [make_slot("width", "INT"), make_slot("height", "INT"), make_slot("frames", "INT"),
                            make_slot("fps", "INT"), make_slot("duration_seconds", "FLOAT"),
                            make_slot("checkpoint_name", "STRING"), make_slot("distilled_lora_name", "STRING"),
                            make_slot("text_encoder_name", "STRING"), make_slot("upscale_model_name", "STRING")]

    empty_latent = add(make_node(nid, "EmptyLTXVLatentVideo", [-600, 80],
        [1280, 720, 241, 1], [300, 120]))
    nodes[-1]["outputs"] = [make_slot("LATENT", "LATENT")]

    # ------------------------------------------------------------------ #
    #  MODEL LOADING
    # ------------------------------------------------------------------ #

    checkpoint_loader = add(make_node(nid, "CheckpointLoaderSimple", [-200, -650],
        ["ltx-2.3-22b-dev-fp8.safetensors"], [300, 100]))
    nodes[-1]["outputs"] = [make_slot("MODEL", "MODEL"), make_slot("CLIP", "CLIP"), make_slot("VAE", "VAE")]

    clip_loader = add(make_node(nid, "LTXVGemmaCLIPModelLoader", [-200, -520],
        ["gemma_3_12B_it_fp4_mixed.safetensors"], [300, 80]))
    nodes[-1]["outputs"] = [make_slot("CLIP", "CLIP")]

    dual_clip = add(make_node(nid, "DualCLIPLoader", [-200, -410],
        ["ltx", "default"], [300, 100]))
    nodes[-1]["inputs"] = [make_input_slot("clip_name1", "CLIP"), make_input_slot("clip_name2", "CLIP")]
    nodes[-1]["outputs"] = [make_slot("CLIP", "CLIP")]
    connect(checkpoint_loader, 1, dual_clip, 0)
    connect(clip_loader, 0, dual_clip, 1)

    scheduler = add(make_node(nid, "LTXVScheduler", [-200, -280],
        ["simple", 25, 3.0, "denoise"], [300, 120]))
    nodes[-1]["outputs"] = [make_slot("SIGMAS", "SIGMAS")]

    noise = add(make_node(nid, "RandomNoise", [-200, -130],
        [42, "fixed"], [300, 80]))
    nodes[-1]["outputs"] = [make_slot("NOISE", "NOISE")]

    ksampler_select = add(make_node(nid, "KSamplerSelect", [-200, 10],
        ["euler_cfg_pp"], [300, 60]))
    nodes[-1]["outputs"] = [make_slot("SAMPLER", "SAMPLER")]

    basic_guider = add(make_node(nid, "BasicGuider", [200, -130],
        [], [300, 80]))
    nodes[-1]["inputs"] = [make_input_slot("model", "MODEL"), make_input_slot("conditioning", "CONDITIONING")]
    nodes[-1]["outputs"] = [make_slot("GUIDER", "GUIDER")]
    connect(checkpoint_loader, 0, basic_guider, 0)

    sampler = add(make_node(nid, "SamplerCustomAdvanced", [550, -130],
        [], [300, 160]))
    nodes[-1]["inputs"] = [
        make_input_slot("noise", "NOISE"), make_input_slot("guider", "GUIDER"),
        make_input_slot("sampler", "SAMPLER"), make_input_slot("sigmas", "SIGMAS"),
        make_input_slot("latent_image", "LATENT")
    ]
    nodes[-1]["outputs"] = [make_slot("LATENT", "LATENT"), make_slot("LATENT", "LATENT")]
    connect(noise, 0, sampler, 0)
    connect(basic_guider, 0, sampler, 1)
    connect(ksampler_select, 0, sampler, 2)
    connect(scheduler, 0, sampler, 3)

    # ------------------------------------------------------------------ #
    #  SCENE 1
    # ------------------------------------------------------------------ #
    sx, sy = 150, 180

    sel1 = add(make_node(nid, "FW_ScenePromptSelector", [sx, sy], [1], [300, 100]))
    nodes[-1]["inputs"] = [make_input_slot("prompt_list", "FW_PROMPT_LIST")]
    nodes[-1]["outputs"] = [make_slot("positive", "STRING"), make_slot("negative", "STRING"),
                            make_slot("bridge_prompt", "STRING"), make_slot("selected_index", "INT")]
    connect(prompt_evolver, 0, sel1, 0)

    enc1 = add(make_node(nid, "FW_ContinuityEncoder", [sx, sy + 130], [0.35], [300, 120]))
    nodes[-1]["inputs"] = [make_input_slot("style_anchor", "FW_STYLE_ANCHOR"),
                           make_input_slot("scene_prompt", "STRING")]
    nodes[-1]["outputs"] = [make_slot("positive_prompt", "STRING"), make_slot("scene_state", "FW_SCENE_STATE")]
    connect(style_anchor, 0, enc1, 0)
    connect(sel1, 0, enc1, 1)

    clip_pos1 = add(make_node(nid, "CLIPTextEncode", [sx + 380, sy],
        ["Scene 1: The character begins their journey, walking through an open field at dawn."], [300, 100]))
    nodes[-1]["inputs"] = [make_input_slot("clip", "CLIP")]
    nodes[-1]["outputs"] = [make_slot("CONDITIONING", "CONDITIONING")]
    connect(dual_clip, 0, clip_pos1, 0)

    clip_neg1 = add(make_node(nid, "CLIPTextEncode", [sx + 380, sy + 130],
        ["blurry, low quality, warped anatomy, flicker, inconsistent identity, static shot"], [300, 100]))
    nodes[-1]["inputs"] = [make_input_slot("clip", "CLIP")]
    nodes[-1]["outputs"] = [make_slot("CONDITIONING", "CONDITIONING")]
    connect(dual_clip, 0, clip_neg1, 0)

    guide1 = add(make_node(nid, "LTXVAddGuide", [sx + 380, sy + 260],
        [0, 1.0, 35, 0, "lanczos", "disabled"], [320, 200]))
    nodes[-1]["inputs"] = [
        make_input_slot("positive", "CONDITIONING"), make_input_slot("negative", "CONDITIONING"),
        make_input_slot("vae", "VAE"), make_input_slot("latent", "LATENT"), make_input_slot("image", "IMAGE")
    ]
    nodes[-1]["outputs"] = [make_slot("positive", "CONDITIONING"), make_slot("negative", "CONDITIONING"),
                            make_slot("latent", "LATENT")]
    connect(clip_pos1, 0, guide1, 0)
    connect(clip_neg1, 0, guide1, 1)
    connect(checkpoint_loader, 2, guide1, 2)
    connect(empty_latent, 0, guide1, 3)
    connect(load_image, 0, guide1, 4)

    connect(guide1, 0, basic_guider, 1)
    connect(guide1, 2, sampler, 4)

    vae_decode1 = add(make_node(nid, "VAEDecode", [sx + 760, sy + 130], [], [300, 80]))
    nodes[-1]["inputs"] = [make_input_slot("samples", "LATENT"), make_input_slot("vae", "VAE")]
    nodes[-1]["outputs"] = [make_slot("IMAGE", "IMAGE")]
    connect(sampler, 0, vae_decode1, 0)
    connect(checkpoint_loader, 2, vae_decode1, 1)

    last_frame1 = add(make_node(nid, "FW_LastFrameExtractor", [sx + 760, sy + 240], [], [300, 80]))
    nodes[-1]["inputs"] = [make_input_slot("scene_video", "IMAGE")]
    nodes[-1]["outputs"] = [make_slot("last_frame", "IMAGE"), make_slot("source_frame_count", "INT")]
    connect(vae_decode1, 0, last_frame1, 0)

    coll1 = add(make_node(nid, "FW_SceneCollector", [sx + 1140, sy + 130], [1, 42], [300, 140]))
    nodes[-1]["inputs"] = [make_input_slot("scene_video", "IMAGE"), make_input_slot("prompt_used", "STRING")]
    nodes[-1]["outputs"] = [make_slot("scene_collection", "FW_SCENE_COLLECTION"), make_slot("metadata_json", "STRING")]
    connect(vae_decode1, 0, coll1, 0)
    connect(sel1, 0, coll1, 1)

    prev_last_frame = last_frame1
    prev_coll = coll1

    # ------------------------------------------------------------------ #
    #  SCENES 2-5
    # ------------------------------------------------------------------ #
    for scene_idx in range(2, 6):
        sy_off = sy + (scene_idx - 1) * 450

        sel = add(make_node(nid, "FW_ScenePromptSelector", [sx, sy_off], [scene_idx], [300, 100]))
        nodes[-1]["inputs"] = [make_input_slot("prompt_list", "FW_PROMPT_LIST")]
        nodes[-1]["outputs"] = [make_slot("positive", "STRING"), make_slot("negative", "STRING"),
                                make_slot("bridge_prompt", "STRING"), make_slot("selected_index", "INT")]
        connect(prompt_evolver, 0, sel, 0)

        enc = add(make_node(nid, "FW_ContinuityEncoder", [sx, sy_off + 130], [0.35], [300, 120]))
        nodes[-1]["inputs"] = [make_input_slot("style_anchor", "FW_STYLE_ANCHOR"),
                               make_input_slot("scene_prompt", "STRING")]
        nodes[-1]["outputs"] = [make_slot("positive_prompt", "STRING"), make_slot("scene_state", "FW_SCENE_STATE")]
        connect(style_anchor, 0, enc, 0)
        connect(sel, 0, enc, 1)

        clip_pos = add(make_node(nid, "CLIPTextEncode", [sx + 380, sy_off],
            [f"Scene {scene_idx} prompt"], [300, 100]))
        nodes[-1]["inputs"] = [make_input_slot("clip", "CLIP")]
        nodes[-1]["outputs"] = [make_slot("CONDITIONING", "CONDITIONING")]
        connect(dual_clip, 0, clip_pos, 0)

        clip_neg = add(make_node(nid, "CLIPTextEncode", [sx + 380, sy_off + 130],
            ["blurry, low quality, warped anatomy, flicker, inconsistent identity, static shot"], [300, 100]))
        nodes[-1]["inputs"] = [make_input_slot("clip", "CLIP")]
        nodes[-1]["outputs"] = [make_slot("CONDITIONING", "CONDITIONING")]
        connect(dual_clip, 0, clip_neg, 0)

        empty_latent_s = add(make_node(nid, "EmptyLTXVLatentVideo", [sx + 380, sy_off + 260],
            [1280, 720, 241, 1], [300, 120]))
        nodes[-1]["outputs"] = [make_slot("LATENT", "LATENT")]

        guide = add(make_node(nid, "LTXVAddGuide", [sx + 380, sy_off + 400],
            [0, 1.0, 35, 0, "lanczos", "disabled"], [320, 200]))
        nodes[-1]["inputs"] = [
            make_input_slot("positive", "CONDITIONING"), make_input_slot("negative", "CONDITIONING"),
            make_input_slot("vae", "VAE"), make_input_slot("latent", "LATENT"), make_input_slot("image", "IMAGE")
        ]
        nodes[-1]["outputs"] = [make_slot("positive", "CONDITIONING"), make_slot("negative", "CONDITIONING"),
                                make_slot("latent", "LATENT")]
        connect(clip_pos, 0, guide, 0)
        connect(clip_neg, 0, guide, 1)
        connect(checkpoint_loader, 2, guide, 2)
        connect(empty_latent_s, 0, guide, 3)
        connect(prev_last_frame, 0, guide, 4)

        # Each scene needs its own sampler + guider because prompts differ
        guider_s = add(make_node(nid, "BasicGuider", [sx + 760, sy_off - 50], [], [300, 80]))
        nodes[-1]["inputs"] = [make_input_slot("model", "MODEL"), make_input_slot("conditioning", "CONDITIONING")]
        nodes[-1]["outputs"] = [make_slot("GUIDER", "GUIDER")]
        connect(checkpoint_loader, 0, guider_s, 0)
        connect(guide, 0, guider_s, 1)

        sampler_s = add(make_node(nid, "SamplerCustomAdvanced", [sx + 760, sy_off + 80], [], [300, 160]))
        nodes[-1]["inputs"] = [
            make_input_slot("noise", "NOISE"), make_input_slot("guider", "GUIDER"),
            make_input_slot("sampler", "SAMPLER"), make_input_slot("sigmas", "SIGMAS"),
            make_input_slot("latent_image", "LATENT")
        ]
        nodes[-1]["outputs"] = [make_slot("LATENT", "LATENT"), make_slot("LATENT", "LATENT")]
        connect(noise, 0, sampler_s, 0)
        connect(guider_s, 0, sampler_s, 1)
        connect(ksampler_select, 0, sampler_s, 2)
        connect(scheduler, 0, sampler_s, 3)
        connect(guide, 2, sampler_s, 4)

        vae_dec = add(make_node(nid, "VAEDecode", [sx + 1140, sy_off + 80], [], [300, 80]))
        nodes[-1]["inputs"] = [make_input_slot("samples", "LATENT"), make_input_slot("vae", "VAE")]
        nodes[-1]["outputs"] = [make_slot("IMAGE", "IMAGE")]
        connect(sampler_s, 0, vae_dec, 0)
        connect(checkpoint_loader, 2, vae_dec, 1)

        last_frame = add(make_node(nid, "FW_LastFrameExtractor", [sx + 1140, sy_off + 190], [], [300, 80]))
        nodes[-1]["inputs"] = [make_input_slot("scene_video", "IMAGE")]
        nodes[-1]["outputs"] = [make_slot("last_frame", "IMAGE"), make_slot("source_frame_count", "INT")]
        connect(vae_dec, 0, last_frame, 0)

        coll = add(make_node(nid, "FW_SceneCollector", [sx + 1520, sy_off + 80],
            [scene_idx, 42 + scene_idx], [300, 160]))
        nodes[-1]["inputs"] = [make_input_slot("scene_video", "IMAGE"), make_input_slot("prompt_used", "STRING"),
                               make_input_slot("existing_collection", "FW_SCENE_COLLECTION")]
        nodes[-1]["outputs"] = [make_slot("scene_collection", "FW_SCENE_COLLECTION"), make_slot("metadata_json", "STRING")]
        connect(vae_dec, 0, coll, 0)
        connect(sel, 0, coll, 1)
        connect(prev_coll, 0, coll, 2)

        prev_last_frame = last_frame
        prev_coll = coll

    # ------------------------------------------------------------------ #
    #  ASSEMBLY
    # ------------------------------------------------------------------ #
    assembler = add(make_node(nid, "FW_SmartAssembler",
        [sx + 1920, sy + 200], ["crossfade", 12], [320, 180]))
    nodes[-1]["inputs"] = [make_input_slot("scene_collection", "FW_SCENE_COLLECTION")]
    nodes[-1]["outputs"] = [make_slot("frames", "IMAGE"), make_slot("summary", "STRING")]
    connect(prev_coll, 0, assembler, 0)

    # ------------------------------------------------------------------ #
    #  Build JSON
    # ------------------------------------------------------------------ #
    workflow = {
        "last_node_id": nid - 1,
        "last_link_id": link_id - 1,
        "nodes": nodes,
        "links": links,
        "groups": [
            {"title": "🌐 Global Setup", "bounding": [-1100, -300, 1640, 560], "color": "#3f789e"},
            {"title": "🎬 Scene 1", "bounding": [120, 140, 1000, 400], "color": "#5e9e7e"},
            {"title": "🎬 Scene 2", "bounding": [120, 590, 1000, 400], "color": "#9e7e5e"},
            {"title": "🎬 Scene 3", "bounding": [120, 1040, 1000, 400], "color": "#7e5e9e"},
            {"title": "🎬 Scene 4", "bounding": [120, 1490, 1000, 400], "color": "#9e5e7e"},
            {"title": "🎬 Scene 5", "bounding": [120, 1940, 1000, 400], "color": "#5e7e9e"},
            {"title": "🎞️ Assembly", "bounding": [1980, 140, 520, 400], "color": "#7e9e5e"},
        ],
        "config": {},
        "extra": {},
        "version": 0.4,
    }

    output_path = sys.argv[1] if len(sys.argv) > 1 else "workflows/frameweaver_ltx23_5scene_10sec.json"
    with open(output_path, "w") as f:
        json.dump(workflow, f, indent=2)

    print(f"Generated workflow: {output_path}")
    print(f"  Nodes: {len(nodes)}")
    print(f"  Links: {len(links)}")
    print(f"  Scenes: 5 × 241 frames (~10s each)")
    print(f"  Total: ~{5 * 241} frames (~50s)")


if __name__ == "__main__":
    main()
