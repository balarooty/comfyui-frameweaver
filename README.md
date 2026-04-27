# 🎬 ComfyUI-FrameWeaver

**FrameWeaver** is a stateful video generation system and custom node pack for ComfyUI. 

It solves the biggest problem with long-form AI video generation: **continuity**. Instead of naive frame-chaining, FrameWeaver introduces scene-awareness, prompt evolution, and continuity preservation for LTX Video 2.3 workflows, ensuring that your characters, styles, and environments remain consistent across multiple scenes.

![ComfyUI](https://img.shields.io/badge/ComfyUI-Custom_Node-blue)
![LTX Video](https://img.shields.io/badge/LTX_Video-2.3-green)
![Status](https://img.shields.io/badge/Status-Beta-orange)

## 🌟 Why FrameWeaver?

Standard multi-scene generation in ComfyUI often results in character mutation, style drift, and jarring transitions because workflows are stateless. FrameWeaver introduces a **Continuity Layer**:

- **Prompt Evolution:** Inherit, blend, or delta-update prompts from scene to scene instead of rewriting them.
- **Style Anchors:** Persist a reference image plus stable style and identity text across your DAG.
- **Stateful Bridging:** Smart frame extraction and Qwen-powered edits for seamless scene transitions.
- **VRAM Smart:** Built for 24GB consumer GPUs. Designed to load and unload heavy models (LTX 22B + Qwen 20B) sequentially without crashing.

---

## 🛠 Architecture & DAG Strategy

ComfyUI workflows are Directed Acyclic Graphs (DAGs) and do not natively loop. FrameWeaver embraces this by providing modular, connectable nodes that wrap around the stock **LTX 2.3** nodes.

We intentionally delegate the heavy lifting (model loading, VAE decoding) to the official LTX nodes so that your workflows remain compatible with future ComfyUI updates.

### Core Node Categories

1. **Input & Planning (`FW_ScenePromptEvolver`, `FW_SceneDurationList`)**
   Define your entire narrative in one place. Enforces LTX's strict `8n+1` frame count rules automatically.
2. **Continuity (`FW_StyleAnchor`, `FW_ContinuityEncoder`)**
   Extracts style embeddings from a starter frame and blends them with your evolving scene prompts.
3. **Generation Helpers (`FW_LatentVideoInit`, `FW_LTX23Settings`)**
   Generic latent initializers and validated settings emitters that hook cleanly into stock LTX nodes.
4. **Output & Assembly (`FW_SceneCollector`, `FW_SmartAssembler`)**
   Accumulates scene frames and metadata, then intelligently concatenates or crossfades them into a final MP4.

---

## 📦 Installation

### One-shot install

```bash
COMFYUI_DIR=/workspace/ComfyUI bash scripts/setup_frameweaver.sh
```

### Install only the custom node

```bash
COMFYUI_DIR=/workspace/ComfyUI bash scripts/install_custom_node.sh
```

This clones or updates:

```text
https://github.com/balarooty/comfyui-frameweaver.git
```

into:

```text
/workspace/ComfyUI/custom_nodes/comfyui-frameweaver
```

### Download only the models

```bash
COMFYUI_DIR=/workspace/ComfyUI bash scripts/download_models.sh
```

To include the optional Qwen Image Edit bridge model bundle:

```bash
COMFYUI_DIR=/workspace/ComfyUI INCLUDE_QWEN_EDIT=1 bash scripts/download_models.sh
```

The downloader supports private/gated Hugging Face downloads with:

```bash
HF_TOKEN=hf_your_token COMFYUI_DIR=/workspace/ComfyUI bash scripts/download_models.sh
```

Restart ComfyUI after installing nodes or downloading models.

### Required Models
Place these in their respective ComfyUI model folders (as documented by the stock LTX example workflows):
- `ltx-2.3-22b-dev-fp8.safetensors`
- `ltx-2.3-22b-distilled-lora-384.safetensors`
- `gemma_3_12B_it_fp4_mixed.safetensors`
- `ltx-2.3-spatial-upscaler-x2-1.1.safetensors` (Optional)

---

## 🚀 Included Workflows

FrameWeaver comes with ready-to-use JSON workflows located in the `workflows/` directory.

### 1. `frameweaver_ltx23_i2v_single_scene.json`
A foundational Image-to-Video setup. It uses the stock LTX 2.3 subgraph but connects FrameWeaver's prompt evolver, duration validator, and settings nodes to expose a cleaner, safer UX.

### 2. `frameweaver_ltx23_ia2v_single_scene.json`
The Image + Audio to Video workflow. Similar to the above, but pre-wired for audio reactivity and synchronization using LTX's audio features.

*Note: For multi-scene generation, duplicate the core scene block and use `FW_LastFrameExtractor` to bridge the output of Scene N into the input of Scene N+1.*

---

## 🧠 Advanced Usage: The Qwen Bridge

For true narrative transitions, FrameWeaver supports bridging scenes using **Qwen Image Edit**. 
Instead of simply passing the last frame of Scene 1 to Scene 2, you pass it through `FW_FrameBridge` along with a structured "Keep/Change" prompt. This allows you to smoothly transition environments (e.g., "Keep the character, change the background to a sunset") before starting the next video generation.

*(Example workflows for Qwen bridging are currently in development in the `example-workflow/` directory).*

---

## 🤝 Contributing

We welcome contributions! FrameWeaver is designed to be highly modular. If you want to add new transition types to `FW_SmartAssembler`, improve the optical flow in the `FW_FrameBridge`, or add checkpoint resume features, please submit a Pull Request.

## 📄 License

MIT License. See `LICENSE` for details.

The generation nodes in this pack are helpers and generic fallbacks. For LTX 2.3
fp8 + distilled LoRA, use the stock LTX nodes preserved in the workflows.
