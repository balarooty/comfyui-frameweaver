#!/usr/bin/env bash
set -euo pipefail

COMFYUI_DIR="${COMFYUI_DIR:-/workspace/ComfyUI}"
BASE_DIR="${COMFYUI_DIR}/models"
INCLUDE_QWEN_EDIT="${INCLUDE_QWEN_EDIT:-0}"

ARIA2_CONNECTIONS="${ARIA2_CONNECTIONS:-16}"
ARIA2_SPLITS="${ARIA2_SPLITS:-16}"
ARIA2_CHUNK_SIZE="${ARIA2_CHUNK_SIZE:-1M}"

echo "==> FrameWeaver model downloader"
echo "ComfyUI dir: ${COMFYUI_DIR}"
echo "Models dir:  ${BASE_DIR}"

install_aria2() {
    if command -v aria2c >/dev/null 2>&1; then
        echo "aria2 already installed"
        return
    fi

    echo "aria2 not found, installing..."
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update
        sudo apt-get install -y aria2
    elif command -v apt >/dev/null 2>&1; then
        sudo apt update
        sudo apt install -y aria2
    elif command -v brew >/dev/null 2>&1; then
        brew install aria2
    else
        echo "ERROR: Could not install aria2 automatically. Install aria2 and rerun."
        exit 1
    fi
}

download_file() {
    local target_dir="$1"
    local output_name="$2"
    local url="$3"
    local target_path="${target_dir}/${output_name}"

    mkdir -p "${target_dir}"

    if [ -s "${target_path}" ]; then
        echo "==> Skipping existing ${target_path}"
        return
    fi

    echo "==> Downloading ${output_name}"
    local args=(
        -x "${ARIA2_CONNECTIONS}"
        -s "${ARIA2_SPLITS}"
        -k "${ARIA2_CHUNK_SIZE}"
        --continue=true
        --auto-file-renaming=false
        --allow-overwrite=true
        -d "${target_dir}"
        -o "${output_name}"
    )

    if [ -n "${HF_TOKEN:-}" ]; then
        args+=(--header "Authorization: Bearer ${HF_TOKEN}")
    fi

    aria2c "${args[@]}" "${url}"
}

install_aria2

echo "==> Creating model directories..."
mkdir -p \
    "${BASE_DIR}/checkpoints" \
    "${BASE_DIR}/loras" \
    "${BASE_DIR}/text_encoders" \
    "${BASE_DIR}/latent_upscale_models" \
    "${BASE_DIR}/vae" \
    "${BASE_DIR}/diffusion_models"

echo "==> Downloading LTX 2.3 fp8 stack..."
download_file \
    "${BASE_DIR}/checkpoints" \
    "ltx-2.3-22b-dev-fp8.safetensors" \
    "https://huggingface.co/Lightricks/LTX-2.3-fp8/resolve/main/ltx-2.3-22b-dev-fp8.safetensors"

download_file \
    "${BASE_DIR}/loras" \
    "ltx-2.3-22b-distilled-lora-384.safetensors" \
    "https://huggingface.co/Lightricks/LTX-2.3/resolve/main/ltx-2.3-22b-distilled-lora-384.safetensors"

download_file \
    "${BASE_DIR}/text_encoders" \
    "gemma_3_12B_it_fp4_mixed.safetensors" \
    "https://huggingface.co/Comfy-Org/ltx-2/resolve/main/split_files/text_encoders/gemma_3_12B_it_fp4_mixed.safetensors"

download_file \
    "${BASE_DIR}/loras" \
    "gemma-3-12b-it-abliterated_lora_rank64_bf16.safetensors" \
    "https://huggingface.co/Comfy-Org/ltx-2/resolve/main/split_files/loras/gemma-3-12b-it-abliterated_lora_rank64_bf16.safetensors"

download_file \
    "${BASE_DIR}/latent_upscale_models" \
    "ltx-2.3-spatial-upscaler-x2-1.1.safetensors" \
    "https://huggingface.co/Lightricks/LTX-2.3/resolve/main/ltx-2.3-spatial-upscaler-x2-1.1.safetensors"

if [ "${INCLUDE_QWEN_EDIT}" = "1" ]; then
    echo "==> Downloading optional Qwen Image Edit 2511 bridge stack..."
    download_file \
        "${BASE_DIR}/vae" \
        "qwen_image_vae.safetensors" \
        "https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/vae/qwen_image_vae.safetensors"

    download_file \
        "${BASE_DIR}/text_encoders" \
        "qwen_2.5_vl_7b_fp8_scaled.safetensors" \
        "https://huggingface.co/Comfy-Org/HunyuanVideo_1.5_repackaged/resolve/main/split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors"

    download_file \
        "${BASE_DIR}/diffusion_models" \
        "qwen_image_edit_2511_bf16.safetensors" \
        "https://huggingface.co/Comfy-Org/Qwen-Image-Edit_ComfyUI/resolve/main/split_files/diffusion_models/qwen_image_edit_2511_bf16.safetensors"

    download_file \
        "${BASE_DIR}/loras" \
        "Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors" \
        "https://huggingface.co/lightx2v/Qwen-Image-Edit-2511-Lightning/resolve/main/Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors"
fi

echo "==> All requested downloads completed."
echo "Restart ComfyUI or click Refresh in the UI."
