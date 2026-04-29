# FrameWeaver LTX 2.3 Workflow Tutorial

This tutorial explains how to install FrameWeaver, download the required LTX
2.3 models, load the included workflows, and avoid the most common mistakes
when using image-to-video and text-to-video.

FrameWeaver does not replace the stock LTX 2.3 generation nodes. It adds helper
nodes for prompt planning, continuity text, frame validation, starter-frame
preparation, scene collection, and future multi-scene bridging.

## What You Get

FrameWeaver currently includes two ready-to-load workflows:

- `workflows/frameweaver_ltx23_i2v_single_scene.json`
- `workflows/frameweaver_ltx23_ia2v_single_scene.json`

The first is for image-to-video or text-to-video. The second is for image plus
audio to video.

Both workflows keep the stock LTX 2.3 subgraph intact and add these FrameWeaver
nodes around it:

- `FW_LTX23Settings`
- `FW_LoadStarterFrame`
- `FW_ScenePromptEvolver`
- `FW_ScenePromptSelector`
- `FW_StyleAnchor`
- `FW_ContinuityEncoder`

## Installation

The scripts assume ComfyUI is installed at `/workspace/ComfyUI`. If your ComfyUI
folder is somewhere else, set `COMFYUI_DIR`.

### Install Everything

From this repository:

```bash
COMFYUI_DIR=/workspace/ComfyUI bash scripts/setup_frameweaver.sh
```

This installs the custom node and downloads the LTX 2.3 model stack.

### Install Only the Custom Node

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

After installing, fully restart ComfyUI.

### Download Only the Models

```bash
COMFYUI_DIR=/workspace/ComfyUI bash scripts/download_models.sh
```

If Hugging Face requires authentication for your environment:

```bash
HF_TOKEN=hf_your_token COMFYUI_DIR=/workspace/ComfyUI bash scripts/download_models.sh
```

To also download the optional Qwen Image Edit bridge bundle:

```bash
COMFYUI_DIR=/workspace/ComfyUI INCLUDE_QWEN_EDIT=1 bash scripts/download_models.sh
```

## Required Model Files

The LTX 2.3 workflows expect these files:

```text
ComfyUI/models/checkpoints/ltx-2.3-22b-dev-fp8.safetensors
ComfyUI/models/loras/ltx-2.3-22b-distilled-lora-384.safetensors
ComfyUI/models/text_encoders/gemma_3_12B_it_fp4_mixed.safetensors
ComfyUI/models/loras/gemma-3-12b-it-abliterated_lora_rank64_bf16.safetensors
ComfyUI/models/latent_upscale_models/ltx-2.3-spatial-upscaler-x2-1.1.safetensors
```

The downloader places them in the correct folders.

## Loading the Workflow

1. Start or restart ComfyUI.
2. Open the ComfyUI UI in your browser.
3. Drag one of these workflow files onto the canvas:

```text
workflows/frameweaver_ltx23_i2v_single_scene.json
workflows/frameweaver_ltx23_ia2v_single_scene.json
```

4. If ComfyUI says FrameWeaver nodes are missing, confirm that this folder
   exists:

```text
ComfyUI/custom_nodes/comfyui-frameweaver
```

5. Restart ComfyUI after installing the node. Browser refresh alone is not
   enough when Python custom nodes have changed.

## The Most Important Choice: I2V vs T2V

The `frameweaver_ltx23_i2v_single_scene.json` workflow can be used in two ways.

### Image-to-Video Mode

Use image-to-video when the starter image already contains the main subject,
scene, composition, and props you want in the video.

Examples:

- The input image already shows two boys on a football field with a visible ball.
- You want the boys to start moving, kick the ball, or react naturally.
- You want to preserve the same character design and camera framing.

For this mode, set:

```text
Switch to Text-to-Video = False
```

The model will try to preserve the input image.

### Text-to-Video Mode

Use text-to-video when your prompt describes a scene that does not already exist
in the input image.

Examples:

- Your image shows two boys running in a village lane, but your prompt asks for
  football in an open field.
- Your prompt adds a new ball, a new girl, a new location, or a new action.
- You want the model to create the scene from the prompt instead of preserving
  the starter image.

For this mode, set:

```text
Switch to Text-to-Video = True
```

In the current generated workflow, this is wired and defaults to `True`.

## Why Your Football Prompt Failed in Image-to-Video

This prompt asks for a new scene:

```text
Cinematic anime scene: two boys playing football in an open field during golden hour,
warm sunlight, dynamic movement. A small girl runs in happily, trips and falls in
slow motion. The boys drop the ball and rush to help her, comforting her gently.
Emotional storytelling, expressive faces, soft glow lighting, smooth animation feel,
depth of field, high-quality anime rendering, wholesome and heartwarming scene
```

If the starter image shows two boys running in a village street, LTX image-to-video
will usually preserve that village street. It may not reliably invent:

- the open football field
- the football
- the small girl
- the fall
- the boys stopping and comforting her

That is too much story change for one image-to-video clip.

For that prompt, use text-to-video first, or generate a starter image that already
contains the football field, ball, two boys, and girl.

## Recommended Prompt Structure

LTX usually works better with clear action, visible props, and camera direction.
Avoid asking one short clip to contain too many story beats.

### Better Single-Clip Football Prompt

```text
Cinematic anime scene in an open grassy football field at golden hour. Two boys
play football together, a clear black-and-white football visible between them.
They run, pass, and chase the ball with energetic movement. Warm sunlight, soft
glow, expressive happy faces, dynamic camera tracking, shallow depth of field,
high-quality anime rendering, smooth animation feel.
```

This is easier because it focuses on one action: boys playing football.

### Better Multi-Scene Version

For the full emotional story, split it:

Scene 1:

```text
Cinematic anime scene in an open grassy football field at golden hour. Two boys
play football together, a clear football visible between them. They run, pass,
and chase the ball with energetic movement, warm sunlight, expressive faces,
smooth animation feel.
```

Scene 2:

```text
A small girl runs happily into the same football field toward the two boys. She
trips and falls in slow motion near the ball. The boys notice immediately and
stop playing. Emotional anime storytelling, soft glow lighting, gentle camera
push-in.
```

Scene 3:

```text
The two boys rush over and kneel beside the small girl, helping her sit up and
comforting her gently. The football rests nearby in the grass. Warm golden-hour
sunlight, wholesome emotional mood, expressive faces, high-quality anime render.
```

This gives the model one main event per clip.

## Node-by-Node Workflow Guide

### `LoadImage`

Loads the starter frame. In text-to-video mode, this image is less important.
In image-to-video mode, it strongly controls the result.

### `FW_LTX23Settings`

Controls basic generation settings:

- width
- height
- frame count
- fps

Frame count is normalized to LTX-safe values like:

```text
9, 17, 25, 33, 41, 49, 57, 65, 73, 81, 89, 97
```

### `FW_LoadStarterFrame`

Resizes the starter frame to LTX-safe dimensions. Width and height are rounded
to multiples of 32.

### `FW_ScenePromptEvolver`

Stores the base style, negative prompt, and scene prompts.

For single-scene generation, fill `scene_1`.

For multi-scene planning, fill `scene_1`, `scene_2`, `scene_3`, and so on.
The current workflow selects one scene at a time because ComfyUI graphs do not
natively loop.

### `FW_ScenePromptSelector`

Chooses which scene prompt from `FW_ScenePromptEvolver` is sent forward.

For the first clip:

```text
scene_index = 1
```

For a duplicated second clip:

```text
scene_index = 2
```

### `FW_StyleAnchor`

Stores continuity text and a reference image. It does not force a mismatched
starter image to become a different scene. It helps carry style and identity
wording into the final prompt.

### `FW_ContinuityEncoder`

Combines:

- selected scene prompt
- style anchor text
- bridge prompt, when present

Its output is the final positive prompt sent into the stock LTX subgraph.

### `Switch to Text-to-Video`

This is the practical switch that decides whether LTX should preserve the input
image or create mainly from text.

Use:

```text
True  = text-to-video behavior
False = image-to-video behavior
```

## Recommended Settings

Start conservative:

```text
width: 1280
height: 720
frames: 97
fps: 24
Switch to Text-to-Video: True for prompt-only scenes
Switch to Text-to-Video: False for matching starter images
```

If VRAM is tight, reduce resolution first:

```text
width: 960
height: 544
frames: 97
```

## Multi-Scene Workflow Pattern

ComfyUI does not natively loop, so multi-scene work is manual for now.

1. Generate Scene 1.
2. Use `FW_LastFrameExtractor` to extract the last frame.
3. Use `FW_FrameBridge` to create a keep/change prompt for a Qwen edit step.
4. Use the edited bridge image as the starter image for Scene 2.
5. Change `FW_ScenePromptSelector.scene_index` to `2`.
6. Generate Scene 2.
7. Repeat for later scenes.

For best results, keep each scene focused on one main action.

## Troubleshooting

### Missing `FW_*` Nodes

Symptom:

```text
This workflow has missing nodes
FW_ContinuityEncoder
FW_ScenePromptEvolver
FW_LTX23Settings
```

Fix:

```bash
cd /workspace/ComfyUI/custom_nodes/comfyui-frameweaver
git pull
```

Then fully restart ComfyUI.

If it still fails, read the ComfyUI terminal log. Look for import errors like:

```text
ModuleNotFoundError
Cannot import comfyui-frameweaver
```

### Combo Type Mismatch

Symptom:

```text
Return type mismatch between linked nodes
ckpt_name, received_type(COMBO) mismatch input_type([...])
```

Fix:

Use the regenerated workflow JSON. FrameWeaver no longer links generic outputs
into model selector combo inputs. The stock LTX subgraph keeps model selections
as normal widgets.

### Prompt Ignores Football or New Characters

Cause:

You are probably using image-to-video with a starter image that does not contain
the requested football scene.

Fix:

Set:

```text
Switch to Text-to-Video = True
```

Or generate/provide a starter image that already contains the football field,
ball, boys, and girl.

### Model File Missing

If the stock LTX subgraph cannot find the checkpoint, LoRA, text encoder, or
upscaler, run:

```bash
COMFYUI_DIR=/workspace/ComfyUI bash scripts/download_models.sh
```

Restart ComfyUI after downloading.

## Practical Recipe: Football Story

Use text-to-video for the first shot:

```text
Switch to Text-to-Video = True
```

Prompt:

```text
Cinematic anime scene in an open grassy football field at golden hour. Two boys
play football together, a clear black-and-white football visible between them.
They run, pass, and chase the ball with energetic movement. Warm sunlight, soft
glow, expressive happy faces, dynamic camera tracking, shallow depth of field,
high-quality anime rendering, smooth animation feel.
```

After you get a good football-field clip, use its last frame as a reference for
the next scene where the girl enters. This is much more reliable than asking one
clip to create the entire story from a mismatched starter image.

## Multi-Scene FFLF Workflow

The `frameweaver_ltx23_multi_scene_fflf.json` workflow demonstrates continuity
bridging across 3 scenes. FFLF stands for First Frame, Last Frame — FrameWeaver
extracts the last frame of each scene and feeds it into the next.

### How It Works

1. Load a starter image and set up `FW_StyleAnchor` with your style and identity
   descriptions.

2. `FW_ScenePromptEvolver` holds all 3 scene prompts in cumulative mode. Each
   scene inherits the base style plus its own action text.

3. For Scene 1:
   - `FW_ScenePromptSelector` picks `scene_index=1`
   - `FW_ContinuityEncoder` merges the scene prompt with the style anchor
   - `FW_LTX23Settings` validates dimensions and frame count (8n+1)
   - The stock LTX 2.3 subgraph generates the video
   - `FW_PrerollCompensator` adds 6 preroll + 8 tail frames
   - `FW_FrameTrimmer` removes them after generation
   - `FW_DecodeVideo` converts latents to pixel frames
   - `FW_LastFrameExtractor` pulls the last frame

4. For Scene 2:
   - The extracted last frame feeds into `FW_LoadStarterFrame`
   - `FW_ScenePromptSelector` picks `scene_index=2`
   - Same generation pipeline runs again
   - `FW_SceneCollector` accumulates both scenes

5. Scene 3 repeats the pattern with `scene_index=3`.

### Key Settings

```text
FW_LTX23Settings: 1280×704, 97 frames, 24fps
FW_PrerollCompensator: preroll=6, tail_loss=8
FW_ScenePromptEvolver: 3 scenes, cumulative mode
```

### Tips

- Keep each scene focused on one main action.
- The cumulative prompt mode means Scene 2 inherits Scene 1's context.
- If the scene changes dramatically (new location, new characters), consider
  using the Qwen Bridge for a smooth visual transition.

---

## Music Video Pipeline

The `frameweaver_ltx23_music_video.json` workflow is audio-driven. It uses
Whisper to extract lyrics, then generates video scenes timed to the music.

### How It Works

1. Load your music audio file.

2. `FW_AudioSplitter` divides it into equal chunks:
   - `scene_count=5`, `scene_duration_seconds=4`
   - `enforce_8n1=True` ensures frame counts are LTX-compatible
   - Outputs: `audio_1` through `audio_5` plus `audio_meta`

3. `FW_WhisperTranscriber` processes each audio chunk:
   - Model: `openai/whisper-base` for speed, or `openai/whisper-large-v3` for
     accuracy
   - Outputs: per-scene text and a pipe-delimited `pipe_text`
   - If transcription is disabled, use `fallback_words` for manual prompting

4. The transcribed text feeds into `FW_ScenePromptEvolver` as the `pipe_text`
   input. Each scene gets context from its lyrics.

5. `FW_AutoQueue` manages multi-chunk generation:
   - Tracks progress by counting completed files in the output folder
   - `enable_auto_queue=True` for fully automated runs
   - Outputs `chunk_index` and `total_chunks` for progress display

6. Each chunk goes through the post-processing chain:
   - `FW_ColorMatch` — match all scenes to a reference image for visual
     consistency
   - `FW_FilmGrain` — add cinematic texture (intensity 0.3)
   - `FW_CinematicPolish` — sharpen with unsharp mask

7. `FW_SmartAssembler` joins everything:
   - `blend_mode=crossfade`, `blend_frames=4`
   - `save_video=True` for automatic MP4 export
   - Audio mux using the original audio track

### Key Settings

```text
FW_AudioSplitter: 5 scenes × 4s = 20s of music
FW_WhisperTranscriber: whisper-base, english
FW_AutoQueue: enabled, folder="MusicVideo"
FW_SmartAssembler: crossfade=4, save_video=True
FW_FilmGrain: intensity=0.3
FW_CinematicPolish: mode=unsharp
```

---

## Post-Processing Chain

The `frameweaver_postprocess_demo.json` workflow is a standalone color grading
pipeline. It does not use LTX at all — it works with any image batch.

### Pipeline Order

The recommended order for post-processing is:

1. **FW_ColorMatch** — Match the color distribution of your frames to a
   reference image using LAB color space. This is the foundation step that
   ensures all scenes share a consistent look.

2. **FW_CinematicPolish** — Sharpen frames to bring out detail. Three modes:
   - `unsharp` — Classic unsharp mask. Best for most video.
   - `laplacian` — Edge-enhancing sharpness. Good for anime/illustration.
   - `sobel` — Gradient-based. Adds a subtle hand-drawn quality.
   - `strength` — Start at 0.5, increase to taste.

3. **FW_FilmGrain** — Add photographic film grain for a cinematic feel.
   - `intensity` — 0.1 for subtle, 0.3 for noticeable, 0.5 for heavy.
   - `saturation` — Controls grain color. 0.0 for monochrome, 0.4 for colored.

4. **FW_LUTApply** — Apply a .cube LUT file for professional-grade color
   grading. Many free LUTs are available online.
   - `strength` — 0.0 to 1.0 blend with original colors. Start at 0.8.

### Creating Custom LUTs

`FW_LUTCreate` generates a .cube LUT file from hex color values:

```text
palette_hex = "#FF6B35, #004E89, #1A1A2E, #FFD700"
lut_size = 33
output_filename = "my_palette.cube"
```

This creates a color-mapped LUT that shifts your video's palette toward the
specified colors.

---

## Whisper Transcription

`FW_WhisperTranscriber` converts audio to text for prompt injection. This is
useful for music videos, narrated stories, and dialogue-driven animations.

### Configuration

- **model_name**: Choose from `openai/whisper-base` (fast, 74M params) through
  `openai/whisper-large-v3` (accurate, 1.5B params).
- **language**: Set to `auto` for detection, or force a specific language.
  Supports 99+ languages including English, Hindi, Tamil, Spanish, etc.
- **enable_transcription**: Set to `False` to use fallback mode instead.
- **fallback_words**: Comma-separated words used when transcription is disabled.
  One word is assigned per scene cyclically.
- **overlap_seconds**: Overlap between audio segments for context continuity.

### Fallback Mode

When `enable_transcription=False`, the node distributes `fallback_words` across
scenes. This is useful for:
- Testing pipelines without GPU-heavy Whisper inference
- Manual prompt injection when lyrics aren't relevant
- Creating abstract mood-driven videos

### Context Enrichment

Each scene can receive additional context via `context_N` inputs:

```text
context_1 = "girl in red dress dancing"
context_2 = "boy in blue shirt standing"
```

The context text is prepended to the transcribed (or fallback) text for that
scene, giving you creative control over what the model generates.

### Output Format

- **pipe_text**: All scene texts joined with `|` delimiter. Wire this into
  `FW_ScenePromptEvolver.pipe_text_input`.
- **scene_N_text**: Individual scene transcriptions for direct use.

---

## Phase 2–5 Nodes: Quick Reference

### Generation Pipeline (Phase 2)

| Node | What It Does |
|---|---|
| `FW_LTX23Settings` | Validates width/height to 32-multiple, frames to 8n+1 |
| `FW_LTXSequencer` | Multi-guide FFLF: wires first and last frame conditioning |
| `FW_PrerollCompensator` | Adds extra frames so the model has room to "warm up" |
| `FW_FrameTrimmer` | Removes preroll/tail frames after generation |
| `FW_LatentGuideInjector` | Injects reference image conditioning into latent space |
| `FW_SceneSampler` | Sampling wrapper with scene-aware noise scheduling |
| `FW_DecodeVideo` | VAE decode with format normalization |

### Post-Processing Suite (Phase 3)

| Node | What It Does |
|---|---|
| `FW_ColorMatch` | LAB color matching to a reference image |
| `FW_FilmGrain` | Adds photographic grain with intensity and saturation control |
| `FW_CinematicPolish` | Three-mode sharpening (unsharp, laplacian, sobel) |
| `FW_LUTApply` | Applies .cube LUT files with adjustable strength |
| `FW_LUTCreate` | Generates a .cube LUT from a hex color palette |

### Audio + Output (Phase 4)

| Node | What It Does |
|---|---|
| `FW_AudioSplitter` | Splits audio into per-scene chunks with frame alignment |
| `FW_AutoQueue` | Tracks multi-chunk progress and auto-triggers next run |
| `FW_SmartAssembler` | Joins scenes with cut/crossfade + optional FFmpeg audio mux |

### AI-Powered (Phase 5)

| Node | What It Does |
|---|---|
| `FW_WhisperTranscriber` | Whisper-based speech-to-text for prompt injection |

---

## Final Checklist

Before generating:

- FrameWeaver custom node is installed under `ComfyUI/custom_nodes`.
- ComfyUI has been fully restarted.
- LTX 2.3 models are downloaded.
- Workflow JSON is the regenerated FrameWeaver workflow.
- `Switch to Text-to-Video` matches your goal.
- Prompt describes one main action per clip.
- The starter image matches the prompt if image-to-video is used.
- Optional dependencies installed if using post-processing, audio, or Whisper.
- For multi-scene: plan one main action per scene for best results.
