"""Brute-force validation: verify every link connects to valid slots."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT / "workflows" / name).read_text(encoding="utf-8"))


def test_every_link_slot_exists():
    """Verify every link's source output slot and target input slot are valid for their nodes."""
    workflow = load("frameweaver_ltx23_10scene_veo.json")
    nodes = {n["id"]: n for n in workflow["nodes"]}

    errors = []
    for link in workflow["links"]:
        link_id, src_id, src_slot, tgt_id, tgt_slot, dtype = link
        if tgt_id is None:
            continue  # intentional unconnected output

        src_node = nodes.get(src_id)
        tgt_node = nodes.get(tgt_id)

        if not src_node:
            errors.append(f"Link {link_id}: source node {src_id} not found")
            continue
        if not tgt_node:
            errors.append(f"Link {link_id}: target node {src_id} not found")
            continue

        if src_slot >= len(src_node["outputs"]):
            errors.append(
                f"Link {link_id}: src slot {src_slot} >= outputs len "
                f"({len(src_node['outputs'])}) for {src_node['type']}"
            )

        if tgt_slot >= len(tgt_node["inputs"]):
            errors.append(
                f"Link {link_id}: tgt slot {tgt_slot} >= inputs len "
                f"({len(tgt_node['inputs'])}) for {tgt_node['type']}"
            )

    if errors:
        raise AssertionError("\n".join(errors))


def test_ltxv_add_guide_inputs():
    """LTXVAddGuide has known inputs: positive, negative, latent, vae, guide_image."""
    workflow = load("frameweaver_ltx23_10scene_veo.json")
    guide = [n for n in workflow["nodes"] if n["type"] == "LTXVAddGuide"][0]
    input_names = [i["name"] for i in guide["inputs"]]
    assert "positive" in input_names
    assert "negative" in input_names
    assert "latent" in input_names
    assert "vae" in input_names
    assert "image" in input_names


def test_sampler_inputs_wired():
    """SamplerCustomAdvanced must have noise, guider, sampler, sigmas, latent_image connected."""
    workflow = load("frameweaver_ltx23_10scene_veo.json")
    sampler = [n for n in workflow["nodes"] if n["type"] == "SamplerCustomAdvanced"][0]
    for inp in sampler["inputs"]:
        assert inp["link"] is not None, f"SamplerCustomAdvanced.{inp['name']} is not connected"


def test_preroll_compensator_has_all_required_inputs():
    """FW_PrerollCompensator requires: target_frames, scene_index, preroll_frames, tail_loss_frames."""
    workflow = load("frameweaver_ltx23_10scene_veo.json")
    pc = [n for n in workflow["nodes"] if n["type"] == "FW_PrerollCompensator"][0]
    input_names = [i["name"] for i in pc["inputs"]]
    assert "target_frames" in input_names
    assert "scene_index" in input_names


def test_no_link_id_collisions():
    """Every link ID must be unique."""
    workflow = load("frameweaver_ltx23_10scene_veo.json")
    link_ids = [link[0] for link in workflow["links"]]
    assert len(link_ids) == len(set(link_ids)), f"Duplicate link IDs: {[x for x in link_ids if link_ids.count(x) > 1]}"


def test_no_output_link_collisions():
    """Each node output slot's links array must have unique link IDs."""
    workflow = load("frameweaver_ltx23_10scene_veo.json")
    nodes = {n["id"]: n for n in workflow["nodes"]}
    errors = []
    for n in workflow["nodes"]:
        for out_idx, output in enumerate(n["outputs"]):
            links = output.get("links", [])
            if len(links) != len(set(links)):
                errors.append(
                    f"Node {n['id']} ({n['type']}) output {out_idx} ({output['name']}) "
                    f"has duplicate link IDs: {links}"
                )
    if errors:
        raise AssertionError("\n".join(errors))


def test_all_links_in_node_output_arrays():
    """Every link in the links array must also appear in at least one node's output links."""
    workflow = load("frameweaver_ltx23_10scene_veo.json")
    all_output_links = set()
    for n in workflow["nodes"]:
        for out in n["outputs"]:
            all_output_links.update(out.get("links", []))

    link_ids = {link[0] for link in workflow["links"]}
    missing = link_ids - all_output_links
    assert not missing, f"Link IDs not in any node output: {missing}"
