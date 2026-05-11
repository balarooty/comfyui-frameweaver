"""FW_SceneQueue — Multi-run orchestrator for scene-based video generation.

Manages the automatic queuing of additional ComfyUI runs for multi-scene
video sequences without requiring audio input. Each scene renders in its
own queue run, with last-frame continuity bridging between scenes.

Key features:
- ``PromptServer.send_sync("impact-add-queue", {})`` for auto-queue
- Folder-based scene index detection (counts completed scene files)
- Override index for re-rendering specific scenes
- Status display for progress tracking
- Filesystem-based state survives ComfyUI restarts

Designed for the "Veo-style" 10-scene FFLF (First-Frame Last-Frame)
sequential generation pattern.
"""

import os
import re

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

try:
    from ..utils.validation import nearest_valid_frame_count
except ImportError:
    try:
        from utils.validation import nearest_valid_frame_count
    except ImportError:
        nearest_valid_frame_count = lambda x: x


class FW_SceneQueue:
    """Auto-queue multiple ComfyUI runs for multi-scene FFLF video generation."""

    CATEGORY = "FrameWeaver/Output"
    RETURN_TYPES = ("INT", "INT", "STRING", "STRING")
    RETURN_NAMES = ("scene_index", "total_scenes", "status", "output_folder")
    FUNCTION = "orchestrate"
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "scene_count": ("INT", {
                    "default": 10, "min": 1, "max": 50,
                    "tooltip": "Total number of scenes to generate.",
                }),
                "frames_per_scene": ("INT", {
                    "default": 97, "min": 9, "max": 241, "step": 8,
                    "tooltip": "Frames per scene. Enforced to 8n+1 for LTX 2.3.",
                }),
                "fps": ("INT", {
                    "default": 24, "min": 1, "max": 60,
                    "tooltip": "Frames per second for duration calculations.",
                }),
                "output_folder_name": ("STRING", {
                    "default": "FrameWeaver_Veo",
                    "tooltip": "Base folder name in ComfyUI's output directory.",
                }),
                "enable_auto_queue": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Auto-queue remaining scenes after the first run.",
                }),
            },
            "optional": {
                "override_scene_index": ("INT", {
                    "default": 0, "min": 0,
                    "tooltip": "Force a specific 1-based scene index (0 = auto-detect from folder).",
                }),
                "trigger": ("*", {
                    "tooltip": "Optional trigger signal from upstream for graph ordering.",
                }),
            },
        }

    def orchestrate(self, scene_count, frames_per_scene, fps,
                    output_folder_name, enable_auto_queue,
                    override_scene_index=0, trigger=None):
        total_scenes = int(scene_count)
        valid_frames = nearest_valid_frame_count(int(frames_per_scene))

        # ---- Resolve output folder ----
        base_name = (output_folder_name or "FrameWeaver_Veo").strip()
        output_folder = self._resolve_output_folder(base_name)

        # ---- Determine current scene index ----
        if override_scene_index > 0:
            scene_index = int(override_scene_index)
            enable_auto_queue = False
            print(f"[FW_SceneQueue] Override scene_index={scene_index}")
        else:
            scene_index = self._count_scenes_from_folder(output_folder) + 1
            print(f"[FW_SceneQueue] Auto-detected scene_index={scene_index}")

        # Clamp
        scene_index = max(1, min(scene_index, total_scenes))
        scene_zero_index = scene_index - 1  # 0-based for preroll logic

        # ---- Build status string ----
        status = self._build_status(scene_index, total_scenes, enable_auto_queue,
                                    valid_frames, fps)

        # ---- Auto-queue remaining runs (only on first scene) ----
        if enable_auto_queue and scene_index == 1 and total_scenes > 1:
            self._auto_queue(total_scenes)

        return (scene_index, total_scenes, status, output_folder)

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #

    def _resolve_output_folder(self, base_name):
        """Find or create the output folder for this run."""
        from datetime import datetime

        if os.path.isdir(_OUTPUT_DIR):
            existing = sorted(
                d for d in os.listdir(_OUTPUT_DIR)
                if d.startswith(base_name + "_")
                and os.path.isdir(os.path.join(_OUTPUT_DIR, d))
            )
            if existing:
                return os.path.join(_OUTPUT_DIR, existing[-1])

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        folder = os.path.join(_OUTPUT_DIR, f"{base_name}_{timestamp}")
        os.makedirs(folder, exist_ok=True)
        return folder

    def _count_scenes_from_folder(self, folder_path):
        """Count completed scene files to determine which scene to render next.

        Matches scene save files like 'scene_0003_frame.png' and returns
        the highest detected scene index (0-based, so 3 completed → 2 returned,
        meaning next scene_index = 3).
        """
        try:
            if not os.path.isdir(folder_path):
                return 0
            indices = []
            for f in os.listdir(folder_path):
                m = re.match(r"scene_(\d+)_frame\.png$", f)
                if m:
                    indices.append(int(m.group(1)))
            return max(indices) if indices else 0
        except Exception as e:
            print(f"[FW_SceneQueue] Folder scan error: {e}")
            return 0

    def _build_status(self, scene_index, total_scenes, auto_queue,
                      frames_per_scene, fps):
        """Build human-readable progress status."""
        scene_duration = frames_per_scene / max(fps, 1)
        remaining = total_scenes - scene_index

        if total_scenes <= 1:
            return (
                f"✅ Single scene — no additional runs needed\n"
                f"🎬 Rendering scene 1 of 1 ({frames_per_scene} frames, "
                f"{scene_duration:.1f}s @ {fps}fps)"
            )

        if scene_index == 1:
            if auto_queue:
                return (
                    f"⚠️ {total_scenes} scenes required\n"
                    f"✅ Auto-queue enabled — {remaining} additional runs will be queued automatically\n"
                    f"🎬 Rendering scene {scene_index} of {total_scenes} "
                    f"({frames_per_scene} frames, {scene_duration:.1f}s @ {fps}fps)"
                )
            else:
                return (
                    f"⚠️ {total_scenes} scenes required\n"
                    f"🔴 Auto-queue is DISABLED\n"
                    f"❗ Manually click 'Queue' {remaining} more times\n"
                    f"🎬 Rendering scene {scene_index} of {total_scenes} "
                    f"({frames_per_scene} frames, {scene_duration:.1f}s @ {fps}fps)"
                )

        if scene_index < total_scenes:
            return (
                f"🎬 Rendering scene {scene_index} of {total_scenes}\n"
                f"⏳ {remaining} scenes remaining "
                f"({frames_per_scene} frames, {scene_duration:.1f}s @ {fps}fps)"
            )

        return (
            f"🏁 Final scene — rendering {scene_index} of {total_scenes}\n"
            f"✅ All scenes will be complete after this run\n"
            f"🎬 {frames_per_scene} frames, {scene_duration:.1f}s @ {fps}fps"
        )

    def _auto_queue(self, total_scenes):
        """Queue additional runs using ComfyUI's PromptServer."""
        if not _HAS_SERVER:
            print("[FW_SceneQueue] PromptServer not available — cannot auto-queue")
            return

        runs = total_scenes - 1
        print(f"[FW_SceneQueue] Queuing {runs} additional scenes")

        for _ in range(runs):
            try:
                PromptServer.instance.send_sync("impact-add-queue", {})
            except Exception as e:
                print(f"[FW_SceneQueue] Queue error: {e}")
                break
