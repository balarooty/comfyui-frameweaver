#!/usr/bin/env bash
# ================================================================== #
#  FrameWeaver — Custom Node Installer
#
#  Clones or updates the FrameWeaver custom node pack into ComfyUI's
#  custom_nodes directory, then optionally installs Python dependencies.
#
#  Usage:
#    # Basic install (core nodes only, no extra deps)
#    COMFYUI_DIR=/workspace/ComfyUI bash scripts/install_custom_node.sh
#
#    # Install with all optional dependencies
#    INSTALL_DEPS=all COMFYUI_DIR=/workspace/ComfyUI bash scripts/install_custom_node.sh
#
#    # Install with specific feature groups
#    INSTALL_DEPS=postprocess COMFYUI_DIR=/workspace/ComfyUI bash scripts/install_custom_node.sh
#    INSTALL_DEPS=audio COMFYUI_DIR=/workspace/ComfyUI bash scripts/install_custom_node.sh
#    INSTALL_DEPS=whisper COMFYUI_DIR=/workspace/ComfyUI bash scripts/install_custom_node.sh
#
#  Environment variables:
#    COMFYUI_DIR         ComfyUI installation root (default: /workspace/ComfyUI)
#    FRAMEWEAVER_REPO_URL  Git clone URL (default: GitHub)
#    INSTALL_DEPS        Dependency group to install: all, postprocess, audio, whisper, test, none (default: none)
#    PYTHON_BIN          Python executable to use (auto-detected if not set)
# ================================================================== #
set -euo pipefail

COMFYUI_DIR="${COMFYUI_DIR:-/workspace/ComfyUI}"
REPO_URL="${FRAMEWEAVER_REPO_URL:-https://github.com/balarooty/comfyui-frameweaver.git}"
NODE_DIR="${COMFYUI_DIR}/custom_nodes/comfyui-frameweaver"
INSTALL_DEPS="${INSTALL_DEPS:-none}"

# ------------------------------------------------------------------ #
#  Helpers
# ------------------------------------------------------------------ #

log() { echo "==> $*"; }
warn() { echo "WARNING: $*" >&2; }
die() { echo "ERROR: $*" >&2; exit 1; }

echo ""
echo "  ╔══════════════════════════════════════════╗"
echo "  ║   🎬 FrameWeaver Node Installer v3.0     ║"
echo "  ╚══════════════════════════════════════════╝"
echo ""
log "ComfyUI dir: ${COMFYUI_DIR}"
log "Repo URL:    ${REPO_URL}"
log "Install dir: ${NODE_DIR}"
log "Deps group:  ${INSTALL_DEPS}"
echo ""

# ------------------------------------------------------------------ #
#  Prerequisites
# ------------------------------------------------------------------ #

if ! command -v git >/dev/null 2>&1; then
    die "git is required but was not found."
fi

# ------------------------------------------------------------------ #
#  Clone or update
# ------------------------------------------------------------------ #

mkdir -p "${COMFYUI_DIR}/custom_nodes"

if [ -d "${NODE_DIR}/.git" ]; then
    log "Existing install found. Updating..."
    git -C "${NODE_DIR}" fetch --all --prune
    git -C "${NODE_DIR}" pull --ff-only
    log "Updated to $(git -C "${NODE_DIR}" rev-parse --short HEAD)"
elif [ -e "${NODE_DIR}" ]; then
    die "${NODE_DIR} exists but is not a git checkout. Move it away or remove it, then rerun."
else
    log "Cloning FrameWeaver..."
    git clone "${REPO_URL}" "${NODE_DIR}"
    log "Cloned at $(git -C "${NODE_DIR}" rev-parse --short HEAD)"
fi

# ------------------------------------------------------------------ #
#  Find Python
# ------------------------------------------------------------------ #

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

# ------------------------------------------------------------------ #
#  Install dependencies
# ------------------------------------------------------------------ #

if [ "${INSTALL_DEPS}" != "none" ] && [ -n "${PYTHON_BIN}" ]; then
    echo ""
    log "Installing Python dependencies (group: ${INSTALL_DEPS})..."
    log "Using Python: ${PYTHON_BIN} ($(${PYTHON_BIN} --version 2>&1))"

    case "${INSTALL_DEPS}" in
        all)
            log "Installing ALL optional dependencies: kornia, torchaudio, transformers"
            "${PYTHON_BIN}" -m pip install -e "${NODE_DIR}[all]"
            ;;
        postprocess)
            log "Installing post-processing dependencies: kornia"
            "${PYTHON_BIN}" -m pip install -e "${NODE_DIR}[postprocess]"
            ;;
        audio)
            log "Installing audio dependencies: torchaudio"
            "${PYTHON_BIN}" -m pip install -e "${NODE_DIR}[audio]"
            ;;
        whisper)
            log "Installing Whisper dependencies: transformers, torchaudio"
            "${PYTHON_BIN}" -m pip install -e "${NODE_DIR}[whisper]"
            ;;
        test)
            log "Installing test dependencies: pytest"
            "${PYTHON_BIN}" -m pip install -e "${NODE_DIR}[test]"
            ;;
        *)
            warn "Unknown dependency group: ${INSTALL_DEPS}"
            warn "Valid groups: all, postprocess, audio, whisper, test, none"
            ;;
    esac
elif [ "${INSTALL_DEPS}" != "none" ] && [ -z "${PYTHON_BIN}" ]; then
    warn "No Python executable found — skipped dependency installation."
    warn "Install manually with: pip install -e '${NODE_DIR}[${INSTALL_DEPS}]'"
fi

# ------------------------------------------------------------------ #
#  Summary
# ------------------------------------------------------------------ #

echo ""
log "━━━ Installed Node Pack Contents ━━━"
log "  Nodes:      30"
log "  Workflows:  5"
log "  JS extensions: 2"
echo ""

# Count node files for verification
if [ -d "${NODE_DIR}/nodes" ]; then
    NODE_FILES=$(find "${NODE_DIR}/nodes" -name "*.py" ! -name "__init__.py" | wc -l | tr -d ' ')
    log "  Python node files found: ${NODE_FILES}"
fi

echo ""
log "FrameWeaver custom node installed successfully."
log "Restart ComfyUI or click Refresh in the UI."
echo ""

# ------------------------------------------------------------------ #
#  Optional dependency status
# ------------------------------------------------------------------ #

if [ -n "${PYTHON_BIN}" ]; then
    echo "  Dependency status:"
    "${PYTHON_BIN}" -c "
deps = {
    'kornia':       'PostProcess (ColorMatch, FilmGrain, CinematicPolish, LUT)',
    'torchaudio':   'Audio (AudioSplitter)',
    'transformers': 'AI (WhisperTranscriber)',
}
for pkg, desc in deps.items():
    try:
        __import__(pkg)
        print(f'    ✅ {pkg:15s} → {desc}')
    except ImportError:
        print(f'    ❌ {pkg:15s} → {desc} (not installed)')
" 2>/dev/null || true
    echo ""
fi
