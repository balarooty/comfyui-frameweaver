# ComfyUI-FrameWeaver

FrameWeaver adds scene-planning and continuity helper nodes for ComfyUI LTX 2.3
video workflows.

The included workflows are based on the stock files in `example-workflow/` and
keep LTX generation on the official LTX nodes:

- `ltx-2.3-22b-dev-fp8.safetensors`
- `ltx-2.3-22b-distilled-lora-384.safetensors`
- `gemma_3_12B_it_fp4_mixed.safetensors`
- `gemma-3-12b-it-abliterated_lora_rank64_bf16.safetensors`
- `ltx-2.3-spatial-upscaler-x2-1.1.safetensors`

## Workflows

- `workflows/frameweaver_ltx23_i2v_single_scene.json`
- `workflows/frameweaver_ltx23_ia2v_single_scene.json`

Load these in ComfyUI after installing the LTX node pack and placing the model
files in the same folders documented by the stock example workflow.

## Nodes

FrameWeaver nodes live under the `FrameWeaver/*` categories. The important MVP
nodes are:

- `FW_ScenePromptEvolver`
- `FW_ScenePromptSelector`
- `FW_StyleAnchor`
- `FW_ContinuityEncoder`
- `FW_LTX23Settings`
- `FW_LoadStarterFrame`
- `FW_LastFrameExtractor`
- `FW_FrameBridge`
- `FW_SceneCollector`
- `FW_SmartAssembler`

The generation nodes in this pack are helpers and generic fallbacks. For LTX 2.3
fp8 + distilled LoRA, use the stock LTX nodes preserved in the workflows.
