"""FrameWeaver — ComfyUI Custom Node Pack

Root package init. Ensures sys.path includes this directory so that
internal imports (utils.validation, utils.prompt_utils, etc.) always
resolve correctly regardless of how ComfyUI loads the package.
"""

import os
import sys

# Inject package root into sys.path BEFORE any node imports.
# This ensures fallback imports like "from utils.validation import ..."
# resolve to THIS package's utils directory.
_PACKAGE_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PACKAGE_ROOT not in sys.path:
    sys.path.insert(0, _PACKAGE_ROOT)

try:
    from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
except ImportError as e:
    print(f"[FrameWeaver] ❌ Critical import error: {e}")
    import traceback
    traceback.print_exc()
    NODE_CLASS_MAPPINGS = {}
    NODE_DISPLAY_NAME_MAPPINGS = {}

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
