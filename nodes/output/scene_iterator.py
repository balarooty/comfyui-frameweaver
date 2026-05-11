"""FW_SceneIterator — Unified scene iteration with auto-queue and last-frame bridging.

Manages scene-by-scene video generation across multiple queue runs:
  • Determines the current scene index from filesystem state
  • Loads the previous scene's last frame as the start image for FFLF continuity
  • Saves the current scene's rendered video frames to the output folder
  • Auto-queues remaining scenes via PromptServer

Designed for the Stacked Scene → PromptRelay → LTX 2.3 I2V pipeline.
"""

import os
import re

try:
    import torch
except ImportError:
    torch = None

try:
    import numpy as np
except ImportError:
    np = None

try:
    from PIL import Image
except ImportError:
    Image = None

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
    from ...utils.validation import nearest_valid_frame_count
except ImportError:
    try:
        from utils.validation import nearest_valid_frame_count
    except ImportError:
        nearest_valid_frame_count = lambda x: x


class FW_SceneIterator:
    """Unified scene iteration with auto-queue, last-frame bridging, and video saving."""

    CATEGORY = "FrameWeaver/Output"
    RETURN_TYPES = ("INT", "INT", "IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("scene_index", "total_scenes", "start_image", "status", "output_folder")
    FUNCTION = "iterate"
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Manages scene-by-scene video generation. On each queue run: determines the current scene, "
        "loads the previous scene's last frame as the start image (or uses input_image for scene 1), "
        "saves the rendered video, and auto-queues the next run. "
        "Connect scene_index to FW_SceneSplitter and start_image to FW_LTXSequencer."
    )
    SEARCH_ALIASES = [
        "scene loop", "auto queue", "scene iterate",
        "scene bridge", "video queue", "scene iterator",
    ]

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "scene_count": ("INT", {
                    "default": 5, "min": 1, "max": 50,
                    "tooltip": "Total scenes. Connect from FW_SceneSplitter.scene_count.",
                }),
                "frames_per_scene": ("INT", {
                    "default": 97, "min": 9, "max": 241, "step": 8,
                    "tooltip": "Frames per scene (8n+1 for LTX 2.3).",
                }),
                "fps": ("INT", {"default": 24, "min": 1, "max": 60}),
                "output_folder_name": ("STRING", {
                    "default": "FrameWeaver_Relay",
                    "tooltip": "Base folder name in ComfyUI output directory.",
                }),
                "enable_auto_queue": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Auto-queue remaining scenes after the first run.",
                }),
            },
            "optional": {
                "input_image": ("IMAGE", {
                    "tooltip": "Starter image for scene 1. If not connected, scene 1 starts from noise.",
                }),
                "scene_video": ("IMAGE", {
                    "tooltip": "Current scene's rendered frames (from VAEDecode). Saved to output folder.",
                }),
                "override_scene_index": ("INT", {
                    "default": 0, "min": 0,
                    "tooltip": "Force a specific scene (0 = auto-detect from folder).",
                }),
            },
        }

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Always re-execute — state is filesystem-based (counts saved scene files)
        return float("nan")

    def iterate(self, scene_count, frames_per_scene, fps, output_folder_name,
                enable_auto_queue, input_image=None, scene_video=None,
                override_scene_index=0):
        total_scenes = max(1, int(scene_count))
        valid_frames = nearest_valid_frame_count(int(frames_per_scene))

        # ---- Resolve output folder ----
        base_name = (output_folder_name or "FrameWeaver_Relay").strip()
        output_folder = self._resolve_output_folder(base_name)

        # ---- Determine current scene index ----
        if override_scene_index > 0:
            scene_index = int(override_scene_index)
            enable_auto_queue = False
            print(f"[FW_SceneIterator] Override scene_index={scene_index}")
        else:
            scene_index = self._detect_scene_index(output_folder)
            print(f"[FW_SceneIterator] Auto-detected scene_index={scene_index}")

        # Clamp to valid range (1-indexed)
        scene_index = max(1, min(scene_index, total_scenes))

        # ---- Save current scene video (if provided) ----
        if scene_video is not None and torch is not None:
            self._save_scene_video(scene_video, scene_index, output_folder)

        # ---- Determine start image ----
        start_image = self._get_start_image(
            scene_index, input_image, output_folder
        )

        # ---- Build status string ----
        status = self._build_status(
            scene_index, total_scenes, enable_auto_queue, valid_frames, fps,
        )

        # ---- Auto-queue remaining scenes ----
        if enable_auto_queue and scene_index == 1 and total_scenes > 1:
            self._auto_queue(total_scenes)

        return (scene_index, total_scenes, start_image, status, output_folder)

    # ------------------------------------------------------------------ #
    #  Output folder management
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

    # ------------------------------------------------------------------ #
    #  Scene index detection
    # ------------------------------------------------------------------ #

    def _detect_scene_index(self, folder_path):
        """Count completed scene files to determine which scene to render next.

        Looks for files matching: scene_NNNN_lastframe.png
        Returns the next scene index (1-indexed).
        """
        try:
            if not os.path.isdir(folder_path):
                return 1
            indices = []
            for f in os.listdir(folder_path):
                m = re.match(r"scene_(\d{4})_lastframe\.png$", f)
                if m:
                    indices.append(int(m.group(1)))
            return (max(indices) + 1) if indices else 1
        except Exception as e:
            print(f"[FW_SceneIterator] Folder scan error: {e}")
            return 1

    # ------------------------------------------------------------------ #
    #  Save scene video & last frame
    # ------------------------------------------------------------------ #

    def _save_scene_video(self, scene_video, scene_index, output_folder):
        """Save the scene's rendered frames and extract the last frame as a bridge."""
        if torch is None or np is None:
            print("[FW_SceneIterator] PyTorch/NumPy not available — cannot save")
            return

        os.makedirs(output_folder, exist_ok=True)

        # Extract and save the last frame as PNG for bridging
        last_frame = scene_video[-1:]  # [1, H, W, C]
        last_frame_np = (last_frame.squeeze(0).cpu().numpy() * 255).clip(0, 255).astype(np.uint8)

        lastframe_path = os.path.join(
            output_folder, f"scene_{scene_index:04d}_lastframe.png"
        )

        if Image is not None:
            img = Image.fromarray(last_frame_np)
            img.save(lastframe_path)
            print(f"[FW_SceneIterator] Saved last frame: {lastframe_path}")
        else:
            # Fallback: save as raw numpy
            np.save(lastframe_path.replace(".png", ".npy"), last_frame_np)
            print(f"[FW_SceneIterator] Saved last frame (npy): {lastframe_path}")

        # Also save the first frame for reference
        first_frame = scene_video[:1]
        first_frame_np = (first_frame.squeeze(0).cpu().numpy() * 255).clip(0, 255).astype(np.uint8)
        firstframe_path = os.path.join(
            output_folder, f"scene_{scene_index:04d}_firstframe.png"
        )
        if Image is not None:
            img = Image.fromarray(first_frame_np)
            img.save(firstframe_path)

    # ------------------------------------------------------------------ #
    #  Start image resolution
    # ------------------------------------------------------------------ #

    def _get_start_image(self, scene_index, input_image, output_folder):
        """Get the start image for the current scene.

        Scene 1: use input_image (or return a placeholder if None).
        Scene N: load last frame from scene N-1.
        """
        if scene_index == 1:
            if input_image is not None:
                return input_image
            # Return a small placeholder — downstream nodes handle noise start
            if torch is not None:
                return torch.zeros(1, 64, 64, 3)
            return None

        # Load the previous scene's last frame
        prev_lastframe_path = os.path.join(
            output_folder, f"scene_{scene_index - 1:04d}_lastframe.png"
        )

        if os.path.exists(prev_lastframe_path) and Image is not None and torch is not None:
            try:
                img = Image.open(prev_lastframe_path).convert("RGB")
                img_np = np.array(img).astype(np.float32) / 255.0
                img_tensor = torch.from_numpy(img_np).unsqueeze(0)  # [1, H, W, 3]
                print(f"[FW_SceneIterator] Loaded previous last frame: {prev_lastframe_path}")
                return img_tensor
            except Exception as e:
                print(f"[FW_SceneIterator] Error loading last frame: {e}")

        # Fallback: try .npy format
        npy_path = prev_lastframe_path.replace(".png", ".npy")
        if os.path.exists(npy_path) and torch is not None:
            try:
                img_np = np.load(npy_path).astype(np.float32) / 255.0
                img_tensor = torch.from_numpy(img_np).unsqueeze(0)
                return img_tensor
            except Exception as e:
                print(f"[FW_SceneIterator] Error loading npy: {e}")

        # No previous frame available — return placeholder
        if input_image is not None:
            print(f"[FW_SceneIterator] No previous last frame found, using input_image")
            return input_image

        if torch is not None:
            print(f"[FW_SceneIterator] No previous last frame found, using placeholder")
            return torch.zeros(1, 64, 64, 3)

        return None

    # ------------------------------------------------------------------ #
    #  Status display
    # ------------------------------------------------------------------ #

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
                    f"✅ Auto-queue enabled — {remaining} additional runs queued\n"
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

    # ------------------------------------------------------------------ #
    #  Auto-queue
    # ------------------------------------------------------------------ #

    def _auto_queue(self, total_scenes):
        """Queue additional runs using ComfyUI's PromptServer."""
        if not _HAS_SERVER:
            print("[FW_SceneIterator] PromptServer not available — cannot auto-queue")
            return

        runs = total_scenes - 1
        print(f"[FW_SceneIterator] Queuing {runs} additional scenes")

        for _ in range(runs):
            try:
                PromptServer.instance.send_sync("impact-add-queue", {})
            except Exception as e:
                print(f"[FW_SceneIterator] Queue error: {e}")
                break
