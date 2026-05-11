import json

# Load the FrameWeaver workflow
with open('/Users/balaji/projects/comfyui-frameweaver/workflows/frameweaver_ltx23_10scene_veo.json', 'r') as f:
    wf = json.load(f)

def get_node(node_id):
    for n in wf['nodes']:
        if n['id'] == node_id:
            return n
    return None

links = wf['links']

# Helper to find link by (from_id, from_out, to_id, to_in)
def find_link(from_id, from_out, to_id, to_in):
    for i, l in enumerate(links):
        if l[1] == from_id and l[2] == from_out and l[3] == to_id and l[4] == to_in:
            return i, l[0]
    return None, None

# =============================================================================
# 1. Change scheduler steps: 20 -> 8
# =============================================================================
get_node(17)['widgets_values'][0] = 8

# =============================================================================
# 2. Replace node 15 BasicGuider -> CFGGuider
# =============================================================================
# Current link 23: 13(output 0) -> 15(input 1) [positive conditioning -> guider conditioning]
# Current link 26: 15(output 0) -> 21(input 1) [guider -> sampler guider]
# We keep link 26. We need to add link for negative: 14(output 0) -> 15(input 2)
# And link 17 currently goes 10->15 model; we'll reroute via patches.

# Update link 23 to go to CFGGuider positive (input 1)
idx_23, _ = find_link(13, 0, 15, 1)
if idx_23 is not None:
    links[idx_23][4] = 1  # now input 1 (positive)

# Replace node 15
n15 = get_node(15)
n15.update({
    "type": "CFGGuider",
    "size": [300, 106],
    "inputs": [
        {"name": "model", "type": "MODEL", "link": None},
        {"name": "positive", "type": "CONDITIONING", "link": links[idx_23][0] if idx_23 is not None else None},
        {"name": "negative", "type": "CONDITIONING", "link": None}
    ],
    "outputs": [
        {"name": "GUIDER", "type": "GUIDER", "links": [26]}
    ],
    "properties": {
        "cnr_id": "comfy-core",
        "ver": "0.3.64",
        "Node name for S&R": "CFGGuider"
    },
    "widgets_values": [1]
})

# =============================================================================
# 3. Replace node 22 VAEDecode -> VAEDecodeTiled
# =============================================================================
n22 = get_node(22)
n22.update({
    "type": "VAEDecodeTiled",
    "size": [300, 150],
    "inputs": [
        {"name": "samples", "type": "LATENT", "link": 32},
        {"name": "vae", "type": "VAE", "link": 20}
    ],
    "outputs": [
        {"name": "IMAGE", "type": "IMAGE", "links": [33]}
    ],
    "properties": {
        "cnr_id": "comfy-core",
        "ver": "0.7.0",
        "Node name for S&R": "VAEDecodeTiled"
    },
    "widgets_values": [512, 64, 4096, 8]
})

# =============================================================================
# 4. Add model pipeline nodes
# =============================================================================
# Reroute link 17: 10(MODEL) -> 31(LoraLoader) instead of 10 -> 15
idx_17, lid_17 = find_link(10, 0, 15, 0)
if idx_17 is not None:
    links[idx_17][3] = 31
    links[idx_17][4] = 0

new_nodes = [
    {
        "id": 31,
        "type": "LoraLoaderModelOnly",
        "pos": [-200, -780],
        "size": [340, 82],
        "flags": {},
        "order": 31,
        "mode": 0,
        "inputs": [
            {"name": "model", "type": "MODEL", "link": lid_17}
        ],
        "outputs": [
            {"name": "MODEL", "type": "MODEL", "links": [64]}
        ],
        "properties": {
            "cnr_id": "comfy-core",
            "ver": "0.3.75",
            "Node name for S&R": "LoraLoaderModelOnly"
        },
        "widgets_values": ["ltx-2.3-22b-distilled-lora-384.safetensors", 0.6]
    },
    {
        "id": 32,
        "type": "PathchSageAttentionKJ",
        "pos": [-200, -680],
        "size": [270, 82],
        "flags": {"collapsed": True},
        "order": 32,
        "mode": 0,
        "inputs": [
            {"name": "model", "type": "MODEL", "link": 64}
        ],
        "outputs": [
            {"name": "MODEL", "type": "MODEL", "links": [65]}
        ],
        "properties": {
            "cnr_id": "comfyui-kjnodes",
            "ver": "204f6d5aae73b10c0fe2fb26e61405fd6337bb77",
            "Node name for S&R": "PathchSageAttentionKJ"
        },
        "widgets_values": ["auto", False]
    },
    {
        "id": 33,
        "type": "LTX2MemoryEfficientSageAttentionPatch",
        "pos": [-200, -580],
        "size": [275, 58],
        "flags": {"collapsed": True},
        "order": 33,
        "mode": 0,
        "inputs": [
            {"name": "model", "type": "MODEL", "link": 65}
        ],
        "outputs": [
            {"name": "model", "type": "MODEL", "links": [66]}
        ],
        "properties": {
            "cnr_id": "comfyui-kjnodes",
            "ver": "2acdef1766026ff3be00daf3c45f6a064db9100f",
            "Node name for S&R": "LTX2MemoryEfficientSageAttentionPatch"
        },
        "widgets_values": [True]
    },
    {
        "id": 34,
        "type": "LTX2AttentionTunerPatch",
        "pos": [-200, -480],
        "size": [283, 178],
        "flags": {"collapsed": True},
        "order": 34,
        "mode": 0,
        "inputs": [
            {"name": "model", "type": "MODEL", "link": 66}
        ],
        "outputs": [
            {"name": "model", "type": "MODEL", "links": [67]}
        ],
        "properties": {
            "cnr_id": "comfyui-kjnodes",
            "ver": "5b38397a6430fdb16c7bd14a6bd64c2b0e69a5f0",
            "Node name for S&R": "LTX2AttentionTunerPatch"
        },
        "widgets_values": ["", 1, 1, 1, 1, True]
    },
    {
        "id": 35,
        "type": "LTXVChunkFeedForward",
        "pos": [-200, -380],
        "size": [272, 82],
        "flags": {"collapsed": True},
        "order": 35,
        "mode": 0,
        "inputs": [
            {"name": "model", "type": "MODEL", "link": 67}
        ],
        "outputs": [
            {"name": "model", "type": "MODEL", "links": [68]}
        ],
        "properties": {
            "cnr_id": "comfyui-kjnodes",
            "ver": "0ea5ece1793263d9fb0ad97bb067f96b83a9dea3",
            "Node name for S&R": "LTXVChunkFeedForward"
        },
        "widgets_values": [2, 4096]
    },
    {
        "id": 36,
        "type": "LTXVImgToVideoInplaceKJ",
        "pos": [100, -500],
        "size": [300, 214],
        "flags": {},
        "order": 36,
        "mode": 0,
        "inputs": [
            {"name": "vae", "type": "VAE", "link": None},
            {"name": "latent", "type": "LATENT", "link": None},
            {"label": "strength_1", "name": "num_images.strength_1", "shape": 7, "type": "FLOAT", "link": None},
            {"label": "image_1", "name": "num_images.image_1", "shape": 7, "type": "IMAGE", "link": None}
        ],
        "outputs": [
            {"name": "latent", "type": "LATENT", "links": [70]}
        ],
        "properties": {
            "cnr_id": "comfyui-kjnodes",
            "ver": "71578cf49e48978cf1c6714494b669b1e571777b",
            "Node name for S&R": "LTXVImgToVideoInplaceKJ"
        },
        "widgets_values": ["1", 1, 0]
    }
]

wf['nodes'].extend(new_nodes)

# =============================================================================
# 5. Reroute latent chain: EmptyLTXVLatentVideo -> LTXVImgToVideoInplaceKJ -> LTXVAddGuide
# =============================================================================
# Current link 30: [30, 19, 0, 20, 3, "*"]  (19 EmptyLTXV -> 20 LTXVAddGuide latent)
idx_30, lid_30 = find_link(19, 0, 20, 3)
if idx_30 is not None:
    links[idx_30][3] = 36
    links[idx_30][4] = 1  # LTXVImgToVideoInplaceKJ latent input

# =============================================================================
# 6. Add new links
# =============================================================================
new_links = [
    [64, 31, 0, 32, 0, "*"],
    [65, 32, 0, 33, 0, "*"],
    [66, 33, 0, 34, 0, "*"],
    [67, 34, 0, 35, 0, "*"],
    [68, 35, 0, 15, 0, "*"],   # patched model -> CFGGuider model
    [69, 14, 0, 15, 2, "*"],   # negative conditioning -> CFGGuider negative
    [70, 36, 0, 20, 3, "*"],   # LTXVImgToVideoInplaceKJ latent -> LTXVAddGuide latent
    [71, 10, 2, 36, 0, "*"],   # VAE -> LTXVImgToVideoInplaceKJ vae
    [72, 2, 0, 36, 3, "*"]     # starter image -> LTXVImgToVideoInplaceKJ image_1
]

for nl in new_links:
    links.append(nl)

# =============================================================================
# 7. Update node input link references for nodes whose inputs changed
# =============================================================================
# Node 15 CFGGuider: model link = 68, positive = old link 23, negative = 69
get_node(15)['inputs'][0]['link'] = 68
get_node(15)['inputs'][2]['link'] = 69

# Node 36 LTXVImgToVideoInplaceKJ: vae=71, latent=lid_30, image_1=72
n36 = get_node(36)
n36['inputs'][0]['link'] = 71
n36['inputs'][1]['link'] = lid_30 if idx_30 is not None else None
n36['inputs'][3]['link'] = 72

# Node 20 LTXVAddGuide: latent now comes from link 70
get_node(20)['inputs'][3]['link'] = 70

# Node 31 LoraLoaderModelOnly: model from link 17
get_node(31)['inputs'][0]['link'] = lid_17

# =============================================================================
# 8. Update metadata
# =============================================================================
wf['last_node_id'] = 36
wf['last_link_id'] = 72

# =============================================================================
# 9. Save
# =============================================================================
out_path = '/Users/balaji/projects/comfyui-frameweaver/workflows/frameweaver_ltx23_10scene_veo_RuneXX_Edits.json'
with open(out_path, 'w') as f:
    json.dump(wf, f, indent=2)

print(f"Saved edited workflow to: {out_path}")
print(f"Total nodes: {len(wf['nodes'])}")
print(f"Total links: {len(wf['links'])}")

# Verify key connections
print("\n=== Verification ===")
for n in wf['nodes']:
    if n['type'] == 'CFGGuider':
        print(f"CFGGuider inputs: model={n['inputs'][0]['link']}, positive={n['inputs'][1]['link']}, negative={n['inputs'][2]['link']}")
    if n['type'] == 'LTXVImgToVideoInplaceKJ':
        print(f"LTXVImgToVideoInplaceKJ inputs: vae={n['inputs'][0]['link']}, latent={n['inputs'][1]['link']}, image={n['inputs'][3]['link']}")
    if n['type'] == 'LTXVAddGuide':
        print(f"LTXVAddGuide latent input link: {n['inputs'][3]['link']}")
    if n['type'] == 'LTXVScheduler':
        print(f"Scheduler steps: {n['widgets_values'][0]}")
    if n['type'] == 'LoraLoaderModelOnly':
        print(f"LoRA: {n['widgets_values']}")
    if n['type'] == 'VAEDecodeTiled':
        print(f"VAEDecodeTiled: tile_size={n['widgets_values'][0]}")

# Verify link integrity
link_targets = {}
for l in wf['links']:
    to_node, to_in = l[3], l[4]
    link_targets.setdefault((to_node, to_in), []).append(l[0])

for (to_node, to_in), lids in link_targets.items():
    if len(lids) > 1:
        print(f"WARNING: multiple links into node {to_node} input {to_in}: {lids}")
