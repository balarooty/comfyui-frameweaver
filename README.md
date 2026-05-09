# 🎬 ComfyUI-FrameWeaver

**FrameWeaver** is a 30-node stateful video generation system for [ComfyUI](https://github.com/comfyanonymous/ComfyUI), purpose-built for **LTX Video 2.3**. It solves the biggest unsolved problem in long-form AI video — **scene-to-scene continuity** — by introducing prompt evolution, style anchoring, frame bridging, audio-driven timing, Whisper transcription, and cinematic post-processing, all wired together as modular, composable ComfyUI nodes.

![ComfyUI](https://img.shields.io/badge/ComfyUI-Custom_Node_Pack-blue)
![LTX Video](https://img.shields.io/badge/LTX_Video-2.3-green)
![Nodes](https://img.shields.io/badge/Nodes-30-purple)
![Workflows](https://img.shields.io/badge/Workflows-8-orange)
![Status](https://img.shields.io/badge/Status-v3.0.1-brightgreen)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## ✨ What Makes FrameWeaver Different

Standard multi-scene workflows are **stateless** — every generation starts from scratch, causing character mutation, wardrobe drift, and jarring transitions. FrameWeaver fixes all of that:

| Problem | FrameWeaver Solution |
|---|---|
| Characters change appearance across scenes | `FW_StyleAnchor` + `FW_ContinuityEncoder` lock identity and wardrobe |
| Rewriting prompts per scene is tedious | `FW_ScenePromptEvolver` with cumulative / replace / blend inheritance |
| Pipe-delimited mass prompting | Paste `scene1 \| scene2 \| scene3` or wire Whisper output directly |
| LTX requires exact 8n+1 frame counts | `FW_LTX23Settings` auto-enforces math for any duration input |
| No way to time scenes to audio | `FW_AudioSplitter` + `FW_SpeechLengthCalc` compute frame-accurate durations |
| Can't sync lyrics to visuals | `FW_WhisperTranscriber` extracts narration → auto-prompts each scene |
| Flat, ungraded video output | 5-node post-processing suite (ColorMatch, FilmGrain, CinematicPolish, LUT) |
| Manual re-queuing for multi-scene | `FW_AutoQueue` auto-queues sequential chunks |
| Scene transitions are jarring cuts | `FW_SmartAssembler` crossfade + FFmpeg audio mux |

---

## 🚀 Quick Start

```bash
# 1. Clone into ComfyUI custom_nodes
cd /path/to/ComfyUI/custom_nodes
git clone https://github.com/balarooty/comfyui-frameweaver.git

# 2. (Optional) Install extra dependencies for post-processing / audio / whisper
cd comfyui-frameweaver
pip install -e ".[all]"

# 3. Restart ComfyUI (full restart, not just browser refresh)

# 4. Drag any workflow JSON from workflows/ onto the canvas
```

The simplest entry point is **`frameweaver_ltx23_i2v_single_scene.json`** — a single image-to-video generation with FrameWeaver's settings validator and continuity encoder.

---

## 🛠 Architecture

ComfyUI workflows are DAGs — they don't natively loop. FrameWeaver embraces this constraint with modular, chainable nodes that wrap around the stock LTX 2.3 nodes. Heavy lifting (model loading, KSampler, VAE decode) is delegated to official ComfyUI nodes for forward compatibility. FrameWeaver handles orchestration, continuity state, and creative control.

### Node Map (30 Nodes · 9 Categories)

#### 📥 Input (6 nodes)

| Node | Description |
|---|---|
| `FW_ScenePromptEvolver` | Define narrative across scenes with cumulative/replace/blend inheritance. Supports pipe-delimited text (`scene1 \| scene2`) and external Whisper input. |
| `FW_ScenePromptSelector` | Select a specific scene's prompt from the evolved list |
| `FW_SceneDurationList` | Configure per-scene durations with automatic 8n+1 enforcement |
| `FW_LoadStarterFrame` | Load and resize a starter image to LTX-safe dimensions |
| `FW_MultiImageLoader` | Load multiple reference images as a gallery batch for FFLF sequencing |
| `FW_SpeechLengthCalc` | Calculate scene duration from word count at slow/avg/fast WPM rates |

#### 🔗 Sequencing (1 node)

| Node | Description |
|---|---|
| `FW_GlobalSequencer` | Central hub that syncs FPS, resolution, scene index, and duration across all downstream nodes |

#### 🔒 Continuity (2 nodes)

| Node | Description |
|---|---|
| `FW_StyleAnchor` | Persist character identity + wardrobe + style with a reference image |
| `FW_ContinuityEncoder` | Merge scene prompt + style anchor into a continuity-enhanced positive prompt |

#### ⚡ Generation (7 nodes)

| Node | Description |
|---|---|
| `FW_LTX23Settings` | Central settings: resolution, frames/seconds toggle, FPS, model selection (checkpoint, LoRA, text encoder, upscaler). Auto-enforces 8n+1. |
| `FW_LTXSequencer` | Multi-guide FFLF (First Frame, Last Frame) keyframe sequencing |
| `FW_PrerollCompensator` | Add preroll (+6) and tail compensation (+8) frames for clean transitions |
| `FW_FrameTrimmer` | Trim preroll/tail frames after generation |
| `FW_LatentVideoInit` | Initialize empty latent video tensors at correct dimensions |
| `FW_LatentGuideInjector` | Inject conditioning images into latent space |
| `FW_SceneSampler` | Sampling wrapper with scene-specific seed, sampler, and sigma schedule |

#### 🌉 Bridge (2 nodes)

| Node | Description |
|---|---|
| `FW_LastFrameExtractor` | Extract the final frame from a generated scene for continuity chaining |
| `FW_FrameBridge` | Prepare structured Keep/Change prompts for Qwen-powered scene transitions |

#### 📤 Output (3 nodes)

| Node | Description |
|---|---|
| `FW_SceneCollector` | Accumulate scene frames and metadata across sequential generations |
| `FW_SmartAssembler` | Trim, pad, crossfade, and FFmpeg-mux scenes into a final video file |
| `FW_AutoQueue` | Multi-chunk orchestrator — auto-queues next scene after each generation |

#### 🎨 Post-Processing (5 nodes)

| Node | Description |
|---|---|
| `FW_ColorMatch` | LAB color space matching against a reference image |
| `FW_FilmGrain` | Cinematic film grain with configurable intensity (subtle → extreme) |
| `FW_CinematicPolish` | Sharpening with 3 modes: unsharp mask, laplacian, sobel |
| `FW_LUTApply` | Apply `.cube` LUT files for professional color grading |
| `FW_LUTCreate` | Generate a custom LUT from a hex color palette |

#### 🎵 Audio (1 node)

| Node | Description |
|---|---|
| `FW_AudioSplitter` | Split audio into per-scene chunks with frame-aligned durations |

#### 🧠 AI (1 node)

| Node | Description |
|---|---|
| `FW_WhisperTranscriber` | Whisper STT — extracts lyrics or narration and outputs pipe-delimited text for auto-prompting |

#### ✨ UX (1 node)

| Node | Description |
|---|---|
| `FW_QuickPipeline` | One-click wrapper for rapid single-scene generation (resolution + FPS + frames in one node) |

#### ⚡ Generation Helper: `FW_DecodeVideo`

| Node | Description |
|---|---|
| `FW_DecodeVideo` | VAE decode with automatic format handling and optional tiling |

---

## 🎥 Included Workflows (8)

All workflows are in `workflows/`. Drag any JSON onto the ComfyUI canvas to load it.

### 1. Single-Scene I2V
**`frameweaver_ltx23_i2v_single_scene.json`**
Foundational image-to-video workflow. Uses `FW_LTX23Settings` → `FW_ScenePromptEvolver` → `FW_ContinuityEncoder` around the stock LTX 2.3 subgraph.

### 2. Single-Scene IA2V
**`frameweaver_ltx23_ia2v_single_scene.json`**
Image + Audio to Video. Same as above but pre-wired for audio-reactive generation.

### 3. Multi-Scene FFLF (3 scenes)
**`frameweaver_ltx23_multi_scene_fflf.json`**
3-scene continuity pipeline demonstrating `FW_LastFrameExtractor` → next scene chaining with `FW_PrerollCompensator` and `FW_FrameTrimmer` for clean transitions.

### 4. 5-Scene 10-Second Pipeline
**`frameweaver_ltx23_5scene_10sec.json`**
5-scene workflow generating ~10 seconds of continuous video with full prompt evolution, style anchoring, and frame bridging across all scenes.

### 5. Three-Act Feature
**`frameweaver_ltx23_three_act_feature.json`**
Long-form narrative structure with act-based scene organization for cinematic storytelling.

### 6. Video Piped (Audio → Auto-Prompted)
**`frameweaver_ltx23_video_piped.json`**
End-to-end audio-driven pipeline: `FW_AudioSplitter` → `FW_WhisperTranscriber` → pipe-delimited prompts → `FW_ScenePromptEvolver` → LTX 2.3 generation. Fully automated — just connect an audio file.

### 7. Music Video Pipeline
**`frameweaver_ltx23_music_video.json`**
Full music video production: audio splitting → Whisper transcription → auto-prompted scenes → `FW_AutoQueue` multi-chunk generation → post-processing chain → `FW_SmartAssembler` with audio mux.

### 8. Post-Processing Demo
**`frameweaver_postprocess_demo.json`**
Standalone color grading chain: `FW_ColorMatch` → `FW_CinematicPolish` → `FW_FilmGrain` → `FW_LUTApply`. Works with any image batch — no LTX models required.

---

## 📦 Installation

### One-Line Full Setup (Recommended)

Downloads the node pack, installs dependencies, and fetches all required models:

```bash
COMFYUI_DIR=/workspace/ComfyUI bash scripts/setup_frameweaver.sh
```

With all optional features (Qwen bridge + Whisper):

```bash
INCLUDE_QWEN_EDIT=1 INCLUDE_WHISPER=1 INSTALL_DEPS=all \
  COMFYUI_DIR=/workspace/ComfyUI bash scripts/setup_frameweaver.sh
```

### Node Pack Only

```bash
COMFYUI_DIR=/workspace/ComfyUI bash scripts/install_custom_node.sh
```

With optional dependency groups (`all`, `postprocess`, `audio`, `whisper`, `test`):

```bash
INSTALL_DEPS=all COMFYUI_DIR=/workspace/ComfyUI bash scripts/install_custom_node.sh
```

### Models Only

```bash
COMFYUI_DIR=/workspace/ComfyUI bash scripts/download_models.sh
```

With Qwen Image Edit bridge models:

```bash
INCLUDE_QWEN_EDIT=1 COMFYUI_DIR=/workspace/ComfyUI bash scripts/download_models.sh
```

With Whisper pre-caching (for offline use):

```bash
INCLUDE_WHISPER=1 COMFYUI_DIR=/workspace/ComfyUI bash scripts/download_models.sh
```

With Hugging Face auth (for gated models):

```bash
HF_TOKEN=hf_your_token COMFYUI_DIR=/workspace/ComfyUI bash scripts/download_models.sh
```

---

## 🧩 Required Models

### LTX 2.3 Core Stack

| Model | Location | Size | Purpose |
|---|---|---|---|
| `ltx-2.3-22b-dev-fp8.safetensors` | `models/checkpoints/` | ~12 GB | Main diffusion model (22B params, fp8) |
| `ltx-2.3-22b-distilled-lora-384.safetensors` | `models/loras/` | ~0.5 GB | Distilled LoRA for faster inference |
| `gemma_3_12B_it_fp4_mixed.safetensors` | `models/text_encoders/` | ~6 GB | Gemma 3 12B text encoder (fp4 mixed) |
| `gemma-3-12b-it-abliterated_lora_rank64_bf16.safetensors` | `models/loras/` | ~0.1 GB | Abliterated text encoder LoRA |
| `ltx-2.3-spatial-upscaler-x2-1.1.safetensors` | `models/latent_upscale_models/` | ~0.2 GB | Spatial 2x upscaler |

### Optional: Qwen Image Edit Bridge (`INCLUDE_QWEN_EDIT=1`)

| Model | Location | Purpose |
|---|---|---|
| `qwen_image_vae.safetensors` | `models/vae/` | Qwen Image VAE |
| `qwen_2.5_vl_7b_fp8_scaled.safetensors` | `models/text_encoders/` | Qwen 2.5 VL text encoder |
| `qwen_image_edit_2511_bf16.safetensors` | `models/diffusion_models/` | Qwen Image Edit diffusion model |
| `Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors` | `models/loras/` | Lightning 4-step acceleration LoRA |

### Optional: Whisper STT (`INCLUDE_WHISPER=1`)

Whisper models are downloaded from Hugging Face Hub to the local transformers cache.

Set `WHISPER_MODEL` to choose a variant (default: `openai/whisper-large-v3`). Options: `whisper-large-v3`, `whisper-medium`, `whisper-small`, `whisper-base`.

---

## 📋 Dependencies

FrameWeaver core nodes use only `torch` and `numpy`, which ship with ComfyUI. Optional features require additional packages:

| Feature | Packages | Install |
|---|---|---|
| Post-Processing | `kornia>=0.7` | `pip install -e ".[postprocess]"` |
| Audio Splitting | `torchaudio>=2.0` | `pip install -e ".[audio]"` |
| Whisper STT | `transformers>=4.36`, `torchaudio>=2.0` | `pip install -e ".[whisper]"` |
| Everything | All above | `pip install -e ".[all]"` |
| Testing | `pytest>=8` | `pip install -e ".[test]"` |

---

## 🧠 Advanced: The Qwen Bridge

For true narrative transitions between scenes, FrameWeaver supports bridging via **Qwen Image Edit**. Instead of passing the last frame of Scene 1 directly as the starter for Scene 2, route it through `FW_FrameBridge` with a structured "Keep/Change" prompt:

> *"Keep the character and wardrobe. Change the background to a sunset over mountains."*

This allows smooth environment transitions, wardrobe changes, or time-of-day shifts — all before the next video generation begins. The Qwen bridge is optional and requires the Qwen model stack.

---

## 🎨 Frontend Extensions

FrameWeaver includes 4 ComfyUI JavaScript extensions (loaded automatically from `web/`):

| Extension | What It Does |
|---|---|
| **Node Colors & Badges** (`fw_node_appearance.js`) | Category-specific background colors and emoji badges for visual organization |
| **Sequencer Sync** (`fw_sequencer_sync.js`) | Real-time broadcast of `FW_GlobalSequencer` values to all connected FW nodes |
| **Rich Tooltips** (`fw_tooltips.js`) | Output slot descriptions, connection guides, and double-click help panels |
| **Widget Behaviors** (`fw_widget_behaviors.js`) | Dynamic widget visibility (frames/seconds toggle), live title readouts (duration, scene count, progress), LUT palette previews |

**Right-click any FrameWeaver node** to access:
- 📖 **FrameWeaver Docs** — opens this README
- 🎬 **Example Workflow** — shows which workflow features the node

---

## 🧪 Testing

```bash
pip install -e ".[test]"
python -m pytest tests/ -v
```

The test suite covers:
- **Registry** — All 30 nodes register without import errors
- **Frame Math** — 8n+1 enforcement, preroll compensation, dimension normalization
- **Audio** — Splitting, duration calculation, frame alignment
- **Post-Processing** — ColorMatch, FilmGrain, CinematicPolish, LUT schemas
- **Whisper** — Transcription output, fallback modes, pipe format
- **AutoQueue** — Chunk indexing, folder management, re-queue logic
- **Workflows** — All 8 workflow JSONs parse, reference valid node types, and have valid links

---

## 📁 Project Structure

```
comfyui-frameweaver/
├── __init__.py                  # ComfyUI entry point (WEB_DIRECTORY, NODE_CLASS_MAPPINGS)
├── pyproject.toml               # Package metadata, optional deps, ComfyUI Manager config
├── nodes/
│   ├── __init__.py              # Node registry (30 nodes, isolated imports)
│   ├── inputs/                  # ScenePromptEvolver, LoadStarterFrame, AudioSplitter, ...
│   ├── sequencing/              # GlobalSequencer
│   ├── continuity/              # StyleAnchor, ContinuityEncoder
│   ├── generation/              # LTX23Settings, LTXSequencer, SceneSampler, ...
│   ├── bridge/                  # LastFrameExtractor, FrameBridge
│   ├── output/                  # SceneCollector, SmartAssembler, AutoQueue
│   ├── postprocess/             # ColorMatch, FilmGrain, CinematicPolish, LUT system
│   ├── ai/                      # WhisperTranscriber
│   └── ux/                      # QuickPipeline
├── utils/                       # Shared utilities (validation, prompt_utils, tensor_utils, ...)
├── web/                         # Frontend JS extensions (4 files)
├── scripts/                     # Setup, model download, and workflow generation scripts
├── workflows/                   # 8 example workflow JSONs
└── tests/                       # pytest test suite (9 test files + conftest)
```

---

## 🤝 Contributing

FrameWeaver is designed to be highly modular. Contributions are welcome:

- **New transition modes** in `FW_SmartAssembler` (wipes, dissolves, etc.)
- **Optical flow improvements** in `FW_FrameBridge`
- **Checkpoint resume** for interrupted multi-scene runs
- **Additional post-processing nodes** (vignette, anamorphic, bloom)
- **More workflow templates** for common use cases

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
