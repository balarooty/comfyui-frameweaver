"""FW_AutoQueue — Multi-run orchestrator for long-form video generation.

Manages the automatic queuing of additional ComfyUI runs for video
sequences that span multiple chunks (e.g. a 3-minute song → 45 scenes → 
3 auto-queued runs of 16 scenes each).

Key features:
- ``PromptServer.send_sync("impact-add-queue", {})`` for auto-queue
- Folder-based index detection (counts completed ``*-audio.mp4`` files)
- Override index for re-rendering specific chunks
- Status instructions for the user (progress display)
- Signal passthrough for triggering downstream nodes

Ported from VRGDG's ``LoadAudioSplit_General`` auto-queue logic.
"""

import os
import re
import math

try:
    from server import PromptServer
    _HAS_SERVER = True
except ImportError:
    _HAS_SERVER = False

try:
    import folder_paths
    _OUTPUT_DIR = folder_paths.get_output_directory()
except ImportError:
    _OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "output")


class FW_AutoQueue:
    """Auto-queue multiple ComfyUI runs for multi-chunk video generation."""

    CATEGORY = "FrameWeaver/Output"
    RETURN_TYPES = ("INT", "INT", "STRING", "STRING")
    RETURN_NAMES = ("chunk_index", "total_chunks", "instructions", "output_folder")
    FUNCTION = "orchestrate"
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio_meta": ("FW_AUDIO_META", {
                    "tooltip": "Audio metadata from FW_AudioSplitter.",
                }),
                "folder_name": ("STRING", {
                    "default": "FrameWeaver_Video",
                    "tooltip": "Base folder name in ComfyUI's output directory.",
                }),
                "enable_auto_queue": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Auto-queue remaining chunks after the first run.",
                }),
                "overwrite_mode": (["overwrite", "backup"], {
                    "default": "overwrite",
                    "tooltip": "overwrite: replace existing files. backup: rename old files.",
                }),
            },
            "optional": {
                "override_chunk_index": ("INT", {
                    "default": -1, "min": -1,
                    "tooltip": "Force a specific chunk index (-1 = auto-detect from folder).",
                }),
                "trigger": ("*", {
                    "tooltip": "Optional trigger signal from upstream (e.g. seed counter).",
                }),
            },
        }

    def orchestrate(self, audio_meta, folder_name, enable_auto_queue,
                    overwrite_mode, override_chunk_index=-1, trigger=None):
        # ---- Extract metadata ----
        total_chunks = int(audio_meta.get("total_sets", 1))
        scene_count = int(audio_meta.get("scene_count", 1))

        # ---- Resolve output folder ----
        base_name = (folder_name or "FrameWeaver_Video").strip()
        output_folder = self._resolve_output_folder(base_name)

        # ---- Determine chunk index ----
        if override_chunk_index >= 0:
            chunk_index = override_chunk_index
            enable_auto_queue = False  # Disable when overriding
            print(f"[FW_AutoQueue] Override chunk_index={chunk_index}")
        else:
            chunk_index = self._count_index_from_folder(output_folder)
            if overwrite_mode == "overwrite":
                pass  # Normal sequential flow
            print(f"[FW_AutoQueue] Auto-detected chunk_index={chunk_index}")

        # ---- Generate instructions ----
        instructions = self._build_instructions(
            chunk_index, total_chunks, enable_auto_queue,
        )

        # ---- Auto-queue remaining runs (only on first chunk) ----
        if enable_auto_queue and chunk_index == 0 and total_chunks > 1:
            self._auto_queue(total_chunks)

        return (chunk_index, total_chunks, instructions, output_folder)

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #

    def _resolve_output_folder(self, base_name):
        """Find or create the output folder for this run."""
        from datetime import datetime

        # Check for existing run folders
        if os.path.isdir(_OUTPUT_DIR):
            existing = sorted(
                d for d in os.listdir(_OUTPUT_DIR)
                if d.startswith(base_name + "_")
                and os.path.isdir(os.path.join(_OUTPUT_DIR, d))
            )
            if existing:
                return os.path.join(_OUTPUT_DIR, existing[-1])

        # Create new timestamped folder
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        folder = os.path.join(_OUTPUT_DIR, f"{base_name}_{timestamp}")
        os.makedirs(folder, exist_ok=True)
        return folder

    def _count_index_from_folder(self, folder_path):
        """Count completed video files to determine the next chunk index."""
        try:
            if not os.path.isdir(folder_path):
                return 0
            indices = []
            for f in os.listdir(folder_path):
                # Match: video_0003_00001-audio.mp4 → captures 0003
                m = re.match(r".*?_(\d{4})_\d+-audio\.mp4$", f)
                if m:
                    indices.append(int(m.group(1)))
            return (max(indices) + 1) if indices else 0
        except Exception as e:
            print(f"[FW_AutoQueue] Folder scan error: {e}")
            return 0

    def _build_instructions(self, chunk_index, total_chunks, auto_queue):
        """Build human-readable progress instructions."""
        run_num = chunk_index + 1
        remaining = total_chunks - run_num

        if total_chunks <= 1:
            return (
                f"✅ Single chunk — no additional runs needed\n"
                f"🎬 Rendering chunk 1 of 1"
            )

        if chunk_index == 0:
            if auto_queue:
                return (
                    f"⚠️ {total_chunks} chunks required\n"
                    f"✅ Auto-queue enabled — {remaining} additional runs will be queued automatically\n"
                    f"🎬 Rendering chunk {run_num} of {total_chunks}"
                )
            else:
                return (
                    f"⚠️ {total_chunks} chunks required\n"
                    f"🔴 Auto-queue is DISABLED\n"
                    f"❗ Manually click 'Queue' {remaining} more times\n"
                    f"🎬 Rendering chunk {run_num} of {total_chunks}"
                )

        if run_num < total_chunks:
            return (
                f"🎬 Rendering chunk {run_num} of {total_chunks}\n"
                f"⏳ {remaining} chunks remaining"
            )

        return (
            f"🏁 Final chunk — rendering {run_num} of {total_chunks}\n"
            f"✅ All chunks will be complete after this run"
        )

    def _auto_queue(self, total_chunks):
        """Queue additional runs using ComfyUI's PromptServer."""
        if not _HAS_SERVER:
            print("[FW_AutoQueue] PromptServer not available — cannot auto-queue")
            return

        runs = total_chunks - 1
        print(f"[FW_AutoQueue] Queuing {runs} additional chunks")

        for _ in range(runs):
            try:
                PromptServer.instance.send_sync("impact-add-queue", {})
            except Exception as e:
                print(f"[FW_AutoQueue] Queue error: {e}")
                break
