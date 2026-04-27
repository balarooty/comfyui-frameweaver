#!/usr/bin/env bash
set -euo pipefail

COMFYUI_DIR="${COMFYUI_DIR:-/workspace/ComfyUI}"
REPO_URL="${FRAMEWEAVER_REPO_URL:-https://github.com/balarooty/comfyui-frameweaver.git}"
NODE_DIR="${COMFYUI_DIR}/custom_nodes/comfyui-frameweaver"

echo "==> FrameWeaver custom node installer"
echo "ComfyUI dir: ${COMFYUI_DIR}"
echo "Repo URL:    ${REPO_URL}"

if ! command -v git >/dev/null 2>&1; then
    echo "ERROR: git is required but was not found."
    exit 1
fi

mkdir -p "${COMFYUI_DIR}/custom_nodes"

if [ -d "${NODE_DIR}/.git" ]; then
    echo "==> Existing install found. Updating..."
    git -C "${NODE_DIR}" fetch --all --prune
    git -C "${NODE_DIR}" pull --ff-only
elif [ -e "${NODE_DIR}" ]; then
    echo "ERROR: ${NODE_DIR} exists but is not a git checkout."
    echo "Move it away or remove it, then run this script again."
    exit 1
else
    echo "==> Cloning FrameWeaver..."
    git clone "${REPO_URL}" "${NODE_DIR}"
fi

if [ -f "${NODE_DIR}/requirements.txt" ]; then
    PYTHON_BIN="${PYTHON_BIN:-}"
    if [ -z "${PYTHON_BIN}" ]; then
        if [ -x "${COMFYUI_DIR}/venv/bin/python" ]; then
            PYTHON_BIN="${COMFYUI_DIR}/venv/bin/python"
        elif command -v python3 >/dev/null 2>&1; then
            PYTHON_BIN="python3"
        elif command -v python >/dev/null 2>&1; then
            PYTHON_BIN="python"
        fi
    fi

    if [ -n "${PYTHON_BIN}" ]; then
        echo "==> Installing Python requirements with ${PYTHON_BIN}..."
        "${PYTHON_BIN}" -m pip install -r "${NODE_DIR}/requirements.txt"
    else
        echo "WARNING: No Python executable found; skipped requirements install."
    fi
fi

echo "==> FrameWeaver custom node installed."
echo "Restart ComfyUI or click Refresh in the UI."
