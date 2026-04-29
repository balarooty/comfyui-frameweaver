# Phase 6 — Polish & Publish: Implementation Plan

> **Status:** ✅ Complete  
> **Prerequisite:** Phases 1–5 complete (30 nodes registered, all tests green)

---

## Full Codebase Audit

### 30 Registered Nodes

| # | Node | Category | Phase | Type |
|---|---|---|---|---|
| 1 | `FW_ScenePromptEvolver` | Input | P1 | Prompt builder |
| 2 | `FW_ScenePromptSelector` | Input | P1 | Scene picker |
| 3 | `FW_SceneDurationList` | Input | P1 | Duration config |
| 4 | `FW_LoadStarterFrame` | Input | P1 | Image loader |
| 5 | `FW_MultiImageLoader` | Input | P1 | Gallery loader |
| 6 | `FW_SpeechLengthCalc` | Input | P1 | WPM calculator |
| 7 | `FW_GlobalSequencer` | Sequencing | P1 | JS-synced hub |
| 8 | `FW_StyleAnchor` | Continuity | P1 | Style persistence |
| 9 | `FW_ContinuityEncoder` | Continuity | P1 | Prompt combiner |
| 10 | `FW_LTX23Settings` | Generation | P2 | Settings validator |
| 11 | `FW_LTXSequencer` | Generation | P2 | Multi-guide FFLF |
| 12 | `FW_PrerollCompensator` | Generation | P2 | Preroll +6, tail +8 |
| 13 | `FW_FrameTrimmer` | Generation | P2 | Post-gen trim |
| 14 | `FW_LatentVideoInit` | Generation | P1 | Latent initializer |
| 15 | `FW_LatentGuideInjector` | Generation | P2 | Conditioning injection |
| 16 | `FW_SceneSampler` | Generation | P2 | Sampling wrapper |
| 17 | `FW_DecodeVideo` | Generation | P2 | VAE decode |
| 18 | `FW_LastFrameExtractor` | Bridge | P1 | Frame extraction |
| 19 | `FW_FrameBridge` | Bridge | P1 | Qwen bridge prep |
| 20 | `FW_SceneCollector` | Output | P1 | Scene accumulator |
| 21 | `FW_SmartAssembler` | Output | P4 | Trim/pad + FFmpeg mux |
| 22 | `FW_QuickPipeline` | UX | P1 | One-click wrapper |
| 23 | `FW_ColorMatch` | PostProcess | P3 | LAB matching |
| 24 | `FW_FilmGrain` | PostProcess | P3 | Cinematic grain |
| 25 | `FW_CinematicPolish` | PostProcess | P3 | Sharpen (3 modes) |
| 26 | `FW_LUTApply` | PostProcess | P3 | .cube LUT apply |
| 27 | `FW_LUTCreate` | PostProcess | P3 | Palette → LUT |
| 28 | `FW_AudioSplitter` | Audio | P4 | Scene audio chunks |
| 29 | `FW_AutoQueue` | Output | P4 | Multi-run orchestrator |
| 30 | `FW_WhisperTranscriber` | AI | P5 | Whisper STT |

### Existing Assets

| Asset | Status | Gap |
|---|---|---|
| **Workflows** (2) | `i2v_single_scene`, `ia2v_single_scene` | Missing: Multi-scene FFLF, Music Video, Post-Processing |
| **Frontend JS** (1) | `fw_sequencer_sync.js` — widget sync only | Missing: node colors, category badges, tooltip overrides |
| **README.md** | Covers P1 nodes only (6 nodes) | Missing: P2–P5 nodes (24 nodes), new workflows, updated architecture |
| **tutorial.md** | Single-scene I2V/T2V only | Missing: multi-scene, audio, post-process, whisper |
| **pyproject.toml** | Bare minimum, no ComfyUI Manager metadata | Missing: `[project.urls]`, dependencies, `[tool.comfy]` |
| **requirements.txt** | Empty (comments only) | Missing: optional deps (kornia, torchaudio, transformers) |
| **Tests** (4 files) | 7 test functions total | Missing: Phase 3–5 node tests, audio split, 8n+1 edge cases |
| **.gitignore** | Minimal | Missing: `.venv/`, `*.egg-info/`, `dist/` |

---

## Work Streams

### 6.1 — Example Workflows (3 new workflows)

> [!IMPORTANT]
> These are ComfyUI workflow JSONs. They wire FrameWeaver nodes together with stock LTX 2.3 nodes and must be valid DAGs with correct node IDs, links, and widget values.

#### Workflow A: Multi-Scene FFLF (`frameweaver_ltx23_multi_scene_fflf.json`)

**Purpose:** 3-scene image-to-video with continuity bridging  
**Target user:** Anyone who wants multi-scene stories  

**Node wiring:**
```
LoadImage → FW_LoadStarterFrame → FW_StyleAnchor
                                      ↓
FW_ScenePromptEvolver (3 scenes, cumulative) → FW_ScenePromptSelector (scene_index=1)
                                                    ↓
FW_ContinuityEncoder → FW_LTX23Settings → [Stock LTX 2.3 Subgraph]
                                                    ↓
FW_DecodeVideo → FW_PrerollCompensator → FW_FrameTrimmer
                                                    ↓
                                    FW_LastFrameExtractor
                                         ↓           ↓
                              FW_SceneCollector    → next scene input
```

**Key config:**
- `FW_LTX23Settings`: 1280×704, 97 frames, 24fps
- `FW_PrerollCompensator`: preroll=6, tail_loss=8
- `FW_ScenePromptEvolver`: 3 scenes, cumulative mode
- Instructions as note: "Duplicate the scene block for scenes 2 and 3"

#### Workflow B: Music Video Pipeline (`frameweaver_ltx23_music_video.json`)

**Purpose:** Audio-driven video generation with Whisper lyrics → auto-queue  
**Target user:** Music video creators  

**Node wiring:**
```
LoadAudio → FW_AudioSplitter (scene_count=5, 4s each, 8n+1=True)
                ↓                      ↓
        FW_WhisperTranscriber    audio_1..audio_5
          (pipe_text output)           ↓
                ↓              [muxed into final]
FW_ScenePromptEvolver (pipe_text_input ← Whisper)
                ↓
FW_AutoQueue (auto_queue=True) → chunk_index
                ↓
FW_ScenePromptSelector (scene_index ← chunk_index+1)
                ↓
FW_ContinuityEncoder → [Stock LTX 2.3 Subgraph]
                ↓
FW_DecodeVideo → FW_ColorMatch → FW_FilmGrain → FW_CinematicPolish
                ↓
FW_SceneCollector → FW_SmartAssembler (save_video=True, audio mux)
```

**Key config:**
- `FW_AudioSplitter`: 5 scenes × 4s = 20s of music
- `FW_WhisperTranscriber`: `whisper-base` (fast), english
- `FW_AutoQueue`: enabled, folder="MusicVideo"
- `FW_SmartAssembler`: crossfade=4, save_video=True
- Post-processing chain: ColorMatch → FilmGrain (0.3) → CinematicPolish (unsharp)

#### Workflow C: Post-Processing Suite (`frameweaver_postprocess_demo.json`)

**Purpose:** Standalone post-processing chain for existing video frames  
**Target user:** Anyone who wants to color-grade generated video  

**Node wiring:**
```
LoadImage (batch) → FW_ColorMatch (reference image)
                        ↓
                  FW_CinematicPolish (unsharp, strength=0.5)
                        ↓
                  FW_FilmGrain (intensity=0.25, saturation=0.4)
                        ↓
                  FW_LUTApply (.cube file, strength=0.8)
                        ↓
                  SaveImage (output)
```

**Key point:** This workflow does NOT use LTX — it's a pure post-processing demo that works with any image batch.

---

### 6.2 — Frontend JS Polish

> [!NOTE]
> ComfyUI supports per-node color overrides, category nesting, and tooltip injection via the JS extension system.

#### 6.2a — Node Categorization Colors

Add a new JS extension `fw_node_appearance.js` that assigns background colors by category:

| Category | Color | Nodes |
|---|---|---|
| `FrameWeaver/Input` | `#2d5a27` (forest green) | Evolver, Selector, Duration, Starter, MultiImage, Speech |
| `FrameWeaver/Sequencing` | `#1a4a6e` (steel blue) | GlobalSequencer |
| `FrameWeaver/Continuity` | `#5a2d5a` (purple) | StyleAnchor, ContinuityEncoder |
| `FrameWeaver/Generation` | `#6e4a1a` (amber) | LTX23Settings, LTXSequencer, Preroll, Trimmer, LatentInit, GuideInjector, Sampler, Decode |
| `FrameWeaver/Bridge` | `#4a1a1a` (deep red) | FrameBridge, LastFrameExtractor |
| `FrameWeaver/Output` | `#1a6e4a` (teal) | SceneCollector, SmartAssembler, AutoQueue |
| `FrameWeaver/PostProcess` | `#6e1a4a` (magenta) | ColorMatch, FilmGrain, CinematicPolish, LUTApply, LUTCreate |
| `FrameWeaver/Audio` | `#4a6e1a` (olive) | AudioSplitter |
| `FrameWeaver/AI` | `#1a1a6e` (navy) | WhisperTranscriber |
| `FrameWeaver/UX` | `#6e6e1a` (gold) | QuickPipeline |

#### 6.2b — Tooltip Enhancement

Override `getExtraMenuOptions` to add:
- "📖 FrameWeaver Docs" link → GitHub README
- "🎬 Example Workflow" for each node that's featured in a workflow
- Badge emoji in node title based on category

---

### 6.3 — README & Documentation Rewrite

#### README.md changes needed:

1. **Update architecture diagram** — Add P2–P5 categories:
   - Generation Helpers → Generation Pipeline (8 nodes)
   - Post-Processing Suite (5 nodes)  
   - Audio Automation (2 nodes)
   - AI-Powered (1 node)

2. **Add node reference table** — All 30 nodes with 1-line descriptions

3. **Update workflow list** — 5 workflows (2 existing + 3 new)

4. **Add "Quick Start" section** for the most common use case

5. **Add dependency section** with optional vs required:
   - Required: `torch`, `numpy` (bundled with ComfyUI)
   - Optional: `kornia` (P3), `torchaudio` (P4), `transformers` (P5)

6. **Update installation** — Add `pip install` for optional deps

#### tutorial.md changes needed:

1. Add sections for:
   - Multi-scene FFLF workflow walkthrough
   - Music Video pipeline walkthrough
   - Post-processing chain usage
   - Whisper transcription configuration

2. Update node-by-node guide with P2–P5 nodes

---

### 6.4 — pyproject.toml for ComfyUI Manager

Current state: bare minimum. Needs:

```toml
[project]
name = "comfyui-frameweaver"
version = "3.0.0"
description = "30-node stateful video generation system for LTX 2.3 with continuity, post-processing, audio automation, and AI transcription."
license = {text = "MIT"}
requires-python = ">=3.10"
dependencies = []

[project.optional-dependencies]
postprocess = ["kornia>=0.7"]
audio = ["torchaudio>=2.0"]
whisper = ["transformers>=4.36", "torchaudio>=2.0"]
all = ["kornia>=0.7", "torchaudio>=2.0", "transformers>=4.36"]
test = ["pytest>=8"]

[project.urls]
Repository = "https://github.com/balarooty/comfyui-frameweaver"
Documentation = "https://github.com/balarooty/comfyui-frameweaver/blob/main/tutorial.md"

[tool.comfy]
PublisherId = "balarooty"
DisplayName = "FrameWeaver"
Icon = "🎬"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

Also update `requirements.txt` to list optional deps clearly.

---

### 6.5 — Unit Tests

#### Current test coverage:

| File | Tests | Coverage |
|---|---|---|
| `test_nodes.py` | 3 | Registry, LTX23Settings defaults, ContinuityEncoder |
| `test_prompt_utils.py` | 2 | Cumulative + replace mode |
| `test_validation.py` | 2 | 8n+1 frame math, dimension normalization |
| `test_workflows.py` | 4 | I2V + IA2V workflow structure validation |
| **Total** | **11** | Phase 1–2 only |

#### New tests needed:

| File | Tests to Add | Coverage |
|---|---|---|
| `test_nodes.py` | +6 | P3–P5 node registry, schema validation for new nodes |
| `test_frame_math.py` | +8 | 8n+1 edge cases, preroll compensation, frame trimming |
| `test_audio_split.py` | +5 | Fixed duration, custom CSV, set_index offset, silence pad, stereo enforcement |
| `test_postprocess.py` | +4 | ColorMatch schema, FilmGrain range, CinematicPolish modes, LUT system |
| `test_whisper.py` | +4 | Schema, fallback mode, context enrichment, pipe output format |
| `test_auto_queue.py` | +4 | Folder indexing, instructions builder, override mode, total chunks |
| `test_smart_assembler.py` | +3 | Meta trim/pad, crossfade math, FFmpeg path detection |
| **Total new** | **+34** | Comprehensive coverage for all phases |

---

## Task Checklist (Execution Order)

> [!TIP]
> Tasks are ordered by dependencies. Tests (6.5) come first because they validate the existing code before we touch docs/workflows. Workflows (6.1) come last because they depend on all other polish being done.

### Stream A: Testing Foundation (do first)
- [x] **6.5a** Create `test_frame_math.py` — 8n+1 edge cases, preroll, trimmer
- [x] **6.5b** Create `test_audio_split.py` — AudioSplitter unit tests
- [x] **6.5c** Create `test_postprocess.py` — Post-processing node tests
- [x] **6.5d** Create `test_whisper.py` — WhisperTranscriber tests
- [x] **6.5e** Create `test_auto_queue.py` — AutoQueue + SmartAssembler tests
- [x] **6.5f** Update `test_nodes.py` — Add P3–P5 registry checks

### Stream B: Package & Dependencies (do second)
- [x] **6.4a** Rewrite `pyproject.toml` with ComfyUI Manager metadata
- [x] **6.4b** Update `requirements.txt` with optional dependency groups
- [x] **6.4c** Update `.gitignore` with standard Python/IDE patterns

### Stream C: Frontend (do third)
- [x] **6.2a** Create `web/fw_node_appearance.js` — category colors + badges
- [x] **6.2b** Enhance `web/fw_sequencer_sync.js` — tooltip and menu links

### Stream D: Documentation (do fourth)
- [x] **6.3a** Rewrite `README.md` — Full 30-node architecture, quick start, deps
- [x] **6.3b** Update `tutorial.md` — Add multi-scene, music video, post-process sections

### Stream E: Workflows (do last)
- [x] **6.1a** Create `frameweaver_ltx23_multi_scene_fflf.json`
- [x] **6.1b** Create `frameweaver_ltx23_music_video.json`
- [x] **6.1c** Create `frameweaver_postprocess_demo.json`

---

## Estimated Deliverables

| Deliverable | Count |
|---|---|
| New test files | 5 |
| New test functions | ~34 |
| Updated test files | 1 |
| New JS files | 1 |
| Updated JS files | 1 |
| New workflow JSONs | 3 |
| Rewritten docs | 2 (README + tutorial) |
| Updated configs | 3 (pyproject.toml + requirements.txt + .gitignore) |

**Final node count: 30 nodes, 5 workflows, 45+ tests**
