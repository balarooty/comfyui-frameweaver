# 🎬 ComfyUI-FrameWeaver

**FrameWeaver** is a 30-node stateful video generation system for ComfyUI, built around **LTX Video 2.3**. It solves the biggest problem with long-form AI video: **continuity**. Instead of naive frame-chaining, FrameWeaver introduces scene-awareness, prompt evolution, style anchoring, audio-driven timing, AI transcription, and cinematic post-processing — all wired together as modular ComfyUI nodes.

![ComfyUI](https://img.shields.io/badge/ComfyUI-Custom_Node-blue)
![LTX Video](https://img.shields.io/badge/LTX_Video-2.3-green)
![Nodes](https://img.shields.io/badge/Nodes-30-purple)
![Status](https://img.shields.io/badge/Status-v3.0-brightgreen)

---

## 🚀 Quick Start

1. **Install the node pack:**
   ```bash
   cd /path/to/ComfyUI/custom_nodes
   git clone https://github.com/balarooty/comfyui-frameweaver.git
   ```

2. **Install optional dependencies** (only if you need post-processing, audio, or whisper):
   ```bash
   cd comfyui-frameweaver
   pip install -e ".[all]"
   ```

3. **Restart ComfyUI** (full restart, not just browser refresh).

4. **Load a workflow** — Drag any JSON from the `workflows/` folder onto the ComfyUI canvas.

5. **Generate!** The simplest entry point is `frameweaver_ltx23_i2v_single_scene.json`.

---

## 🌟 Why FrameWeaver?

Standard multi-scene workflows are **stateless** — each generation starts from scratch, causing character mutation, style drift, and jarring cuts. FrameWeaver fixes this:

| Problem | FrameWeaver Solution |
|---|---|
| Character mutation across scenes | `FW_StyleAnchor` + `FW_ContinuityEncoder` persist identity text |
| Prompt rewriting per scene | `FW_ScenePromptEvolver` with cumulative/replace modes |
| Invalid frame counts | `FW_LTX23Settings` enforces 8n+1 automatically |
| Manual scene timing | `FW_AudioSplitter` + `FW_SpeechLengthCalc` compute durations |
| No audio sync | `FW_WhisperTranscriber` extracts lyrics → prompt injection |
| Flat video output | 5-node post-processing suite (ColorMatch, FilmGrain, CinematicPolish, LUT) |
| Manual re-queuing | `FW_AutoQueue` orchestrates multi-chunk generation |

---

## 🛠 Architecture

ComfyUI workflows are DAGs and don't natively loop. FrameWeaver embraces this with modular, connectable nodes that wrap around the stock LTX 2.3 nodes. Heavy lifting (model loading, VAE decode) is delegated to official LTX nodes for forward compatibility.

### Node Categories (30 Nodes)

| # | Node | Category | Description |
|---|---|---|---|
| 1 | `FW_ScenePromptEvolver` | 📥 Input | Define narrative across scenes with cumulative or replace evolution |
| 2 | `FW_ScenePromptSelector` | 📥 Input | Select which scene prompt to use for current generation |
| 3 | `FW_SceneDurationList` | 📥 Input | Configure per-scene durations with 8n+1 enforcement |
| 4 | `FW_LoadStarterFrame` | 📥 Input | Load and resize starter image to LTX-safe dimensions |
| 5 | `FW_MultiImageLoader` | 📥 Input | Load multiple reference images as a gallery batch |
| 6 | `FW_SpeechLengthCalc` | 📥 Input | Calculate scene duration from word count and WPM |
| 7 | `FW_GlobalSequencer` | 🔗 Sequencing | Central hub that syncs FPS, resolution, scene index across all nodes |
| 8 | `FW_StyleAnchor` | 🔒 Continuity | Persist style + identity descriptions with a reference image |
| 9 | `FW_ContinuityEncoder` | 🔒 Continuity | Combine scene prompt + style anchor into final positive prompt |
| 10 | `FW_LTX23Settings` | ⚡ Generation | Validate and normalize width, height, frames, FPS for LTX 2.3 |
| 11 | `FW_LTXSequencer` | ⚡ Generation | Multi-guide FFLF (First Frame, Last Frame) sequencing |
| 12 | `FW_PrerollCompensator` | ⚡ Generation | Add preroll (+6) and tail compensation (+8) frames |
| 13 | `FW_FrameTrimmer` | ⚡ Generation | Trim preroll/tail frames after generation |
| 14 | `FW_LatentVideoInit` | ⚡ Generation | Initialize empty latent video tensors |
| 15 | `FW_LatentGuideInjector` | ⚡ Generation | Inject conditioning into latent space |
| 16 | `FW_SceneSampler` | ⚡ Generation | Sampling wrapper with scene-aware settings |
| 17 | `FW_DecodeVideo` | ⚡ Generation | VAE decode with automatic format handling |
| 18 | `FW_LastFrameExtractor` | 🌉 Bridge | Extract the last frame from a generated scene |
| 19 | `FW_FrameBridge` | 🌉 Bridge | Prepare keep/change prompts for Qwen-powered scene transitions |
| 20 | `FW_SceneCollector` | 📤 Output | Accumulate scene frames and metadata across generations |
| 21 | `FW_SmartAssembler` | 📤 Output | Trim/pad + crossfade + FFmpeg mux into final video |
| 22 | `FW_AutoQueue` | 📤 Output | Multi-chunk orchestrator with folder-based indexing |
| 23 | `FW_QuickPipeline` | ✨ UX | One-click wrapper for rapid single-scene generation |
| 24 | `FW_ColorMatch` | 🎨 PostProcess | LAB color space matching against a reference image |
| 25 | `FW_FilmGrain` | 🎨 PostProcess | Cinematic film grain with configurable intensity |
| 26 | `FW_CinematicPolish` | 🎨 PostProcess | Sharpening with 3 modes (unsharp, laplacian, sobel) |
| 27 | `FW_LUTApply` | 🎨 PostProcess | Apply .cube LUT files for professional color grading |
| 28 | `FW_LUTCreate` | 🎨 PostProcess | Generate LUT from hex color palette |
| 29 | `FW_AudioSplitter` | 🎵 Audio | Split audio into per-scene chunks with 8n+1 frame alignment |
| 30 | `FW_WhisperTranscriber` | 🧠 AI | Whisper STT for lyrics/narration → prompt injection |

---

## 🎥 Included Workflows (5)

All workflows are in the `workflows/` directory. Drag onto the ComfyUI canvas to load.

### 1. Single-Scene I2V — `frameweaver_ltx23_i2v_single_scene.json`
Foundational Image-to-Video setup using FrameWeaver's prompt evolver, settings validator, and continuity encoder around the stock LTX 2.3 subgraph.

### 2. Single-Scene IA2V — `frameweaver_ltx23_ia2v_single_scene.json`
Image + Audio to Video. Same as above but pre-wired for audio reactivity.

### 3. Multi-Scene FFLF — `frameweaver_ltx23_multi_scene_fflf.json`
3-scene image-to-video with continuity bridging. Demonstrates `FW_LastFrameExtractor` → next scene input pattern with `FW_PrerollCompensator` and `FW_FrameTrimmer`.

### 4. Music Video Pipeline — `frameweaver_ltx23_music_video.json`
Audio-driven pipeline: `FW_AudioSplitter` → `FW_WhisperTranscriber` → auto-prompted scenes → `FW_AutoQueue` → post-processing chain → `FW_SmartAssembler` with audio mux.

### 5. Post-Processing Demo — `frameweaver_postprocess_demo.json`
Standalone color grading chain: `FW_ColorMatch` → `FW_CinematicPolish` → `FW_FilmGrain` → `FW_LUTApply`. Works with any image batch — no LTX required.

---

## 📦 Installation

### Full Setup (Node Pack + Models)

```bash
COMFYUI_DIR=/workspace/ComfyUI bash scripts/setup_frameweaver.sh
```

### Full Setup with All Features

```bash
INCLUDE_QWEN_EDIT=1 INCLUDE_WHISPER=1 INSTALL_DEPS=all \
  COMFYUI_DIR=/workspace/ComfyUI bash scripts/setup_frameweaver.sh
```

### Node Pack Only

```bash
COMFYUI_DIR=/workspace/ComfyUI bash scripts/install_custom_node.sh
```

With optional dependencies (groups: `all`, `postprocess`, `audio`, `whisper`, `test`):
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

With Whisper model pre-caching (for offline use):
```bash
INCLUDE_WHISPER=1 COMFYUI_DIR=/workspace/ComfyUI bash scripts/download_models.sh
```

With Hugging Face auth:
```bash
HF_TOKEN=hf_your_token COMFYUI_DIR=/workspace/ComfyUI bash scripts/download_models.sh
```

### Required Models (LTX 2.3 Core)

| Model | Location | Purpose |
|---|---|---|
| `ltx-2.3-22b-dev-fp8.safetensors` | `models/checkpoints/` | Main diffusion model (22B fp8) |
| `ltx-2.3-22b-distilled-lora-384.safetensors` | `models/loras/` | Distilled LoRA (faster inference) |
| `gemma_3_12B_it_fp4_mixed.safetensors` | `models/text_encoders/` | Gemma 3 12B text encoder |
| `gemma-3-12b-it-abliterated_lora_rank64_bf16.safetensors` | `models/loras/` | Abliterated text encoder LoRA |
| `ltx-2.3-spatial-upscaler-x2-1.1.safetensors` | `models/latent_upscale_models/` | Spatial upscaler 2x |

### Optional Models (Qwen Bridge — `INCLUDE_QWEN_EDIT=1`)

| Model | Location | Purpose |
|---|---|---|
| `qwen_image_vae.safetensors` | `models/vae/` | Qwen Image VAE |
| `qwen_2.5_vl_7b_fp8_scaled.safetensors` | `models/text_encoders/` | Qwen 2.5 VL text encoder |
| `qwen_image_edit_2511_bf16.safetensors` | `models/diffusion_models/` | Qwen Image Edit diffusion model |
| `Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors` | `models/loras/` | Lightning 4-step LoRA |

### Optional Models (Whisper — `INCLUDE_WHISPER=1`)

Whisper models are downloaded from Hugging Face Hub to the local transformers cache. Set `WHISPER_MODEL` to choose a variant (default: `openai/whisper-large-v3`). Available: `whisper-large-v3`, `whisper-medium`, `whisper-small`, `whisper-base`.

---

## 📋 Dependencies

FrameWeaver core nodes use only `torch` and `numpy`, which are bundled with ComfyUI. Optional features require additional packages:

| Feature | Package | Install |
|---|---|---|
| Post-Processing (Phase 3) | `kornia>=0.7` | `pip install -e ".[postprocess]"` |
| Audio Splitting (Phase 4) | `torchaudio>=2.0` | `pip install -e ".[audio]"` |
| Whisper STT (Phase 5) | `transformers>=4.36`, `torchaudio>=2.0` | `pip install -e ".[whisper]"` |
| Everything | All above | `pip install -e ".[all]"` |
| Testing | `pytest>=8` | `pip install -e ".[test]"` |

---

## 🧠 Advanced: The Qwen Bridge

For true narrative transitions, FrameWeaver supports bridging scenes using **Qwen Image Edit**. Instead of passing the last frame of Scene 1 directly to Scene 2, pass it through `FW_FrameBridge` with a structured "Keep/Change" prompt. This allows smooth environment transitions (e.g., "Keep the character, change the background to a sunset") before starting the next video generation.

---

## 🧪 Testing

```bash
pip install -e ".[test]"
python -m pytest tests/ -v
```

The test suite covers all 30 nodes across 5 phases: registry validation, 8n+1 frame math, audio splitting, post-processing schemas, Whisper fallback modes, auto-queue logic, and smart assembler configuration.

---

## 🎨 Frontend Features

FrameWeaver includes two ComfyUI JS extensions (loaded automatically from `web/`):

- **Node Colors & Badges** (`fw_node_appearance.js`): Each category gets a distinct background color and emoji badge for visual organization.
- **Sequencer Sync** (`fw_sequencer_sync.js`): Changes to `FW_GlobalSequencer` widgets broadcast in real-time to all FrameWeaver nodes on the canvas.

Right-click any FrameWeaver node to access:
- 📖 **FrameWeaver Docs** — opens the GitHub README
- 🎬 **Example Workflow** — shows which example workflow features the node

---

## 🤝 Contributing

FrameWeaver is designed to be highly modular. Contributions welcome for:
- New transition types in `FW_SmartAssembler`
- Optical flow improvements in `FW_FrameBridge`
- Checkpoint resume features
- Additional post-processing nodes

## 📄 License

MIT License. See `LICENSE` for details.
