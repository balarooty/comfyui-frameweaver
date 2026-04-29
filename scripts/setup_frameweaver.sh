#!/usr/bin/env bash
# ================================================================== #
#  FrameWeaver — Complete Setup
#
#  One-command installation: custom nodes + all models + dependencies.
#
#  Usage:
#    # Standard setup (core nodes + LTX 2.3 models)
#    COMFYUI_DIR=/workspace/ComfyUI bash scripts/setup_frameweaver.sh
#
#    # Full setup with all features
#    INCLUDE_QWEN_EDIT=1 INCLUDE_WHISPER=1 INSTALL_DEPS=all \
#      COMFYUI_DIR=/workspace/ComfyUI bash scripts/setup_frameweaver.sh
#
#    # With HF auth
#    HF_TOKEN=hf_xxxxx COMFYUI_DIR=/workspace/ComfyUI bash scripts/setup_frameweaver.sh
#
#  Environment variables (all optional):
#    COMFYUI_DIR          ComfyUI root directory (default: /workspace/ComfyUI)
#    INSTALL_DEPS         Dependency group: all, postprocess, audio, whisper, none (default: none)
#    INCLUDE_QWEN_EDIT    Set to 1 to download Qwen bridge models
#    INCLUDE_WHISPER      Set to 1 to pre-cache Whisper models
#    WHISPER_MODEL        Whisper model variant (default: openai/whisper-large-v3)
#    HF_TOKEN             Hugging Face auth token for gated models
# ================================================================== #
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "  ╔══════════════════════════════════════════════╗"
echo "  ║   🎬 FrameWeaver Complete Setup v3.0          ║"
echo "  ╠══════════════════════════════════════════════╣"
echo "  ║   Step 1: Install custom node pack            ║"
echo "  ║   Step 2: Download models                     ║"
echo "  ╚══════════════════════════════════════════════╝"
echo ""

# Step 1: Install custom node (+ optional Python deps)
"${SCRIPT_DIR}/install_custom_node.sh"

# Step 2: Download models
"${SCRIPT_DIR}/download_models.sh"

echo ""
echo "  ╔══════════════════════════════════════════════╗"
echo "  ║   🎬 FrameWeaver setup complete!              ║"
echo "  ║                                               ║"
echo "  ║   Restart ComfyUI to load the new nodes.      ║"
echo "  ║   Load workflows from the workflows/ folder.  ║"
echo "  ╚══════════════════════════════════════════════╝"
echo ""
