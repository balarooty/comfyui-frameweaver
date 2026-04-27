#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

"${SCRIPT_DIR}/install_custom_node.sh"
"${SCRIPT_DIR}/download_models.sh"

echo "==> FrameWeaver setup complete."
