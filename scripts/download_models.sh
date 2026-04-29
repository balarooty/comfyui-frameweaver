#!/usr/bin/env bash
# ================================================================== #
#  FrameWeaver — Complete Model Downloader
#
#  Downloads all models required for FrameWeaver workflows:
#    - LTX 2.3 fp8 generation stack (core)
#    - Qwen Image Edit bridge stack (optional, INCLUDE_QWEN_EDIT=1)
#    - Whisper STT models (optional, INCLUDE_WHISPER=1)
#
#  Usage:
#    # Core models only (LTX 2.3)
#    COMFYUI_DIR=/workspace/ComfyUI bash scripts/download_models.sh
#
#    # Include Qwen bridge
#    INCLUDE_QWEN_EDIT=1 COMFYUI_DIR=/workspace/ComfyUI bash scripts/download_models.sh
#
#    # Include Whisper (pre-cached for offline use)
#    INCLUDE_WHISPER=1 COMFYUI_DIR=/workspace/ComfyUI bash scripts/download_models.sh
#
#    # Everything
#    INCLUDE_QWEN_EDIT=1 INCLUDE_WHISPER=1 COMFYUI_DIR=/workspace/ComfyUI bash scripts/download_models.sh
#
#    # With Hugging Face auth (for gated models)
#    HF_TOKEN=hf_xxxxx COMFYUI_DIR=/workspace/ComfyUI bash scripts/download_models.sh
#
#    # Custom whisper model size
#    WHISPER_MODEL=openai/whisper-medium INCLUDE_WHISPER=1 COMFYUI_DIR=/workspace/ComfyUI bash scripts/download_models.sh
# ================================================================== #
set -euo pipefail

COMFYUI_DIR="${COMFYUI_DIR:-/workspace/ComfyUI}"
BASE_DIR="${COMFYUI_DIR}/models"
INCLUDE_QWEN_EDIT="${INCLUDE_QWEN_EDIT:-0}"
INCLUDE_WHISPER="${INCLUDE_WHISPER:-0}"
WHISPER_MODEL="${WHISPER_MODEL:-openai/whisper-large-v3}"

ARIA2_CONNECTIONS="${ARIA2_CONNECTIONS:-16}"
ARIA2_SPLITS="${ARIA2_SPLITS:-16}"
ARIA2_CHUNK_SIZE="${ARIA2_CHUNK_SIZE:-1M}"

# ------------------------------------------------------------------ #
#  Helpers
# ------------------------------------------------------------------ #

log() { echo "==> $*"; }
warn() { echo "WARNING: $*" >&2; }
die() { echo "ERROR: $*" >&2; exit 1; }

install_aria2() {
    if command -v aria2c >/dev/null 2>&1; then
        log "aria2 already installed ($(aria2c --version | head -1))"
        return
    fi

    log "aria2 not found, installing..."
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update -qq
        sudo apt-get install -y aria2
    elif command -v apt >/dev/null 2>&1; then
        sudo apt update -qq
        sudo apt install -y aria2
    elif command -v brew >/dev/null 2>&1; then
        brew install aria2
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -Sy --noconfirm aria2
    else
        die "Could not install aria2 automatically. Install aria2 and rerun."
    fi
}

download_file() {
    local target_dir="$1"
    local output_name="$2"
    local url="$3"
    local target_path="${target_dir}/${output_name}"

    mkdir -p "${target_dir}"

    if [ -s "${target_path}" ]; then
        local size
        size=$(du -h "${target_path}" 2>/dev/null | cut -f1)
        log "Skipping existing ${output_name} (${size})"
        return
    fi

    log "Downloading ${output_name}..."
    local args=(
        -x "${ARIA2_CONNECTIONS}"
        -s "${ARIA2_SPLITS}"
        -k "${ARIA2_CHUNK_SIZE}"
        --continue=true
        --auto-file-renaming=false
        --allow-overwrite=true
        --summary-interval=30
        -d "${target_dir}"
        -o "${output_name}"
    )

    if [ -n "${HF_TOKEN:-}" ]; then
        args+=(--header "Authorization: Bearer ${HF_TOKEN}")
    fi

    if ! aria2c "${args[@]}" "${url}"; then
        warn "Failed to download ${output_name} from ${url}"
        return 1
    fi

    local final_size
    final_size=$(du -h "${target_path}" 2>/dev/null | cut -f1)
    log "Downloaded ${output_name} (${final_size})"
}

find_python() {
    # Try ComfyUI's venv first, then system python3, then python
    if [ -x "${COMFYUI_DIR}/venv/bin/python" ]; then
        echo "${COMFYUI_DIR}/venv/bin/python"
    elif command -v python3 >/dev/null 2>&1; then
        echo "python3"
    elif command -v python >/dev/null 2>&1; then
        echo "python"
    fi
}

# ------------------------------------------------------------------ #
#  Banner
# ------------------------------------------------------------------ #

echo ""
echo "  ╔══════════════════════════════════════════╗"
echo "  ║   🎬 FrameWeaver Model Downloader v3.0   ║"
echo "  ╚══════════════════════════════════════════╝"
echo ""
log "ComfyUI dir:      ${COMFYUI_DIR}"
log "Models dir:       ${BASE_DIR}"
log "Qwen bridge:      $([ "${INCLUDE_QWEN_EDIT}" = "1" ] && echo "ENABLED" || echo "disabled")"
log "Whisper models:   $([ "${INCLUDE_WHISPER}" = "1" ] && echo "ENABLED (${WHISPER_MODEL})" || echo "disabled")"
[ -n "${HF_TOKEN:-}" ] && log "HF auth:          token provided" || log "HF auth:          none (public repos only)"
echo ""

install_aria2

# ------------------------------------------------------------------ #
#  Create directory structure
# ------------------------------------------------------------------ #

log "Creating model directories..."
mkdir -p \
    "${BASE_DIR}/checkpoints" \
    "${BASE_DIR}/loras" \
    "${BASE_DIR}/text_encoders" \
    "${BASE_DIR}/latent_upscale_models" \
    "${BASE_DIR}/vae" \
    "${BASE_DIR}/diffusion_models"

# ================================================================== #
#  1. CORE: LTX 2.3 fp8 stack (required)
# ================================================================== #

echo ""
log "━━━ Downloading LTX 2.3 fp8 generation stack ━━━"
echo ""

# Main diffusion model (~22B params, fp8 quantized)
download_file \
    "${BASE_DIR}/checkpoints" \
    "ltx-2.3-22b-dev-fp8.safetensors" \
    "https://huggingface.co/Lightricks/LTX-2.3-fp8/resolve/main/ltx-2.3-22b-dev-fp8.safetensors"

# Distilled LoRA for faster inference (384 rank)
download_file \
    "${BASE_DIR}/loras" \
    "ltx-2.3-22b-distilled-lora-384.safetensors" \
    "https://huggingface.co/Lightricks/LTX-2.3/resolve/main/ltx-2.3-22b-distilled-lora-384.safetensors"

# Gemma 3 12B text encoder (fp4 mixed)
download_file \
    "${BASE_DIR}/text_encoders" \
    "gemma_3_12B_it_fp4_mixed.safetensors" \
    "https://huggingface.co/Comfy-Org/ltx-2/resolve/main/split_files/text_encoders/gemma_3_12B_it_fp4_mixed.safetensors"

# Gemma abliterated LoRA (uncensored text encoder)
download_file \
    "${BASE_DIR}/loras" \
    "gemma-3-12b-it-abliterated_lora_rank64_bf16.safetensors" \
    "https://huggingface.co/Comfy-Org/ltx-2/resolve/main/split_files/loras/gemma-3-12b-it-abliterated_lora_rank64_bf16.safetensors"

# Spatial upscaler 2x (optional but recommended)
download_file \
    "${BASE_DIR}/latent_upscale_models" \
    "ltx-2.3-spatial-upscaler-x2-1.1.safetensors" \
    "https://huggingface.co/Lightricks/LTX-2.3/resolve/main/ltx-2.3-spatial-upscaler-x2-1.1.safetensors"

# ================================================================== #
#  2. OPTIONAL: Qwen Image Edit bridge stack
# ================================================================== #

if [ "${INCLUDE_QWEN_EDIT}" = "1" ]; then
    echo ""
    log "━━━ Downloading Qwen Image Edit bridge stack ━━━"
    echo ""

    # Qwen Image VAE
    download_file \
        "${BASE_DIR}/vae" \
        "qwen_image_vae.safetensors" \
        "https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/vae/qwen_image_vae.safetensors"

    # Qwen 2.5 VL 7B text encoder (fp8)
    download_file \
        "${BASE_DIR}/text_encoders" \
        "qwen_2.5_vl_7b_fp8_scaled.safetensors" \
        "https://huggingface.co/Comfy-Org/HunyuanVideo_1.5_repackaged/resolve/main/split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors"

    # Qwen Image Edit diffusion model (bf16)
    download_file \
        "${BASE_DIR}/diffusion_models" \
        "qwen_image_edit_2511_bf16.safetensors" \
        "https://huggingface.co/Comfy-Org/Qwen-Image-Edit_ComfyUI/resolve/main/split_files/diffusion_models/qwen_image_edit_2511_bf16.safetensors"

    # Qwen Image Edit Lightning LoRA (4-step acceleration)
    download_file \
        "${BASE_DIR}/loras" \
        "Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors" \
        "https://huggingface.co/lightx2v/Qwen-Image-Edit-2511-Lightning/resolve/main/Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors"
fi

# ================================================================== #
#  3. OPTIONAL: Whisper STT models (pre-cache for offline use)
# ================================================================== #

if [ "${INCLUDE_WHISPER}" = "1" ]; then
    echo ""
    log "━━━ Pre-caching Whisper model: ${WHISPER_MODEL} ━━━"
    echo ""

    PYTHON_BIN=$(find_python)

    if [ -z "${PYTHON_BIN}" ]; then
        warn "No Python executable found — cannot pre-cache Whisper model."
        warn "Whisper will auto-download on first use if transformers is installed."
    else
        log "Using Python: ${PYTHON_BIN}"

        # Ensure transformers is installed
        if ! "${PYTHON_BIN}" -c "import transformers" 2>/dev/null; then
            log "Installing transformers for Whisper support..."
            "${PYTHON_BIN}" -m pip install "transformers>=4.36" "torchaudio>=2.0" 2>/dev/null || \
                warn "Could not install transformers. Install manually: pip install transformers>=4.36 torchaudio>=2.0"
        fi

        # Pre-download the Whisper model to HF cache
        log "Downloading Whisper model to local cache (this may take a few minutes)..."
        "${PYTHON_BIN}" -c "
import os, sys
try:
    from transformers import WhisperProcessor, WhisperForConditionalGeneration
    model_name = '${WHISPER_MODEL}'
    print(f'  Downloading processor for {model_name}...')
    WhisperProcessor.from_pretrained(model_name)
    print(f'  Downloading model weights for {model_name}...')
    WhisperForConditionalGeneration.from_pretrained(model_name)
    print(f'  ✅ {model_name} cached successfully')
except ImportError:
    print('  WARNING: transformers not available — skipping Whisper pre-cache', file=sys.stderr)
except Exception as e:
    print(f'  WARNING: Failed to cache Whisper model: {e}', file=sys.stderr)
" 2>&1 || warn "Whisper pre-caching had issues (model will auto-download on first use)"
    fi
fi

# ================================================================== #
#  Summary
# ================================================================== #

echo ""
echo "  ╔══════════════════════════════════════════╗"
echo "  ║   🎬 Download Summary                    ║"
echo "  ╚══════════════════════════════════════════╝"
echo ""

count_models() {
    local dir="$1"
    if [ -d "${dir}" ]; then
        find "${dir}" -maxdepth 1 -name "*.safetensors" -type f 2>/dev/null | wc -l | tr -d ' '
    else
        echo "0"
    fi
}

log "Models downloaded:"
log "  checkpoints:          $(count_models "${BASE_DIR}/checkpoints") files"
log "  loras:                $(count_models "${BASE_DIR}/loras") files"
log "  text_encoders:        $(count_models "${BASE_DIR}/text_encoders") files"
log "  latent_upscale:       $(count_models "${BASE_DIR}/latent_upscale_models") files"
log "  vae:                  $(count_models "${BASE_DIR}/vae") files"
log "  diffusion_models:     $(count_models "${BASE_DIR}/diffusion_models") files"

echo ""
log "All requested downloads completed."
log "Restart ComfyUI or click Refresh in the UI."
echo ""
