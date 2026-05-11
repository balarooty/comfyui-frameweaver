"""Tests for FW_SceneQueue — multi-run FFLF scene orchestrator."""

import os
import tempfile
import shutil
import pytest

from nodes.output.scene_queue import FW_SceneQueue


class TestSceneQueueSchema:
    def test_required_inputs(self):
        it = FW_SceneQueue.INPUT_TYPES()
        for key in ["scene_count", "frames_per_scene", "fps",
                     "output_folder_name", "enable_auto_queue"]:
            assert key in it["required"]

    def test_optional_inputs(self):
        it = FW_SceneQueue.INPUT_TYPES()
        assert "override_scene_index" in it["optional"]
        assert "trigger" in it["optional"]

    def test_return_types(self):
        assert FW_SceneQueue.RETURN_TYPES == ("INT", "INT", "STRING", "STRING")
        assert FW_SceneQueue.RETURN_NAMES == ("scene_index", "total_scenes", "status", "output_folder")

    def test_output_node(self):
        assert FW_SceneQueue.OUTPUT_NODE is True

    def test_category(self):
        assert FW_SceneQueue.CATEGORY == "FrameWeaver/Output"

    def test_function_name(self):
        assert FW_SceneQueue.FUNCTION == "orchestrate"


class TestSceneQueueFolderIndexing:
    def test_empty_folder_returns_zero(self):
        td = tempfile.mkdtemp()
        try:
            sq = FW_SceneQueue()
            assert sq._count_scenes_from_folder(td) == 0
        finally:
            shutil.rmtree(td)

    def test_counts_completed_scenes(self):
        td = tempfile.mkdtemp()
        try:
            for i in range(1, 6):
                open(os.path.join(td, f"scene_{i:04d}_frame.png"), "w").close()
            sq = FW_SceneQueue()
            assert sq._count_scenes_from_folder(td) == 5
        finally:
            shutil.rmtree(td)

    def test_nonexistent_folder_returns_zero(self):
        sq = FW_SceneQueue()
        assert sq._count_scenes_from_folder("/nonexistent/path/12345") == 0

    def test_ignores_non_matching_files(self):
        td = tempfile.mkdtemp()
        try:
            open(os.path.join(td, "random_file.txt"), "w").close()
            open(os.path.join(td, "scene_0003_frame.png"), "w").close()
            sq = FW_SceneQueue()
            assert sq._count_scenes_from_folder(td) == 3
        finally:
            shutil.rmtree(td)

    def test_ignores_scene_files_with_wrong_suffix(self):
        td = tempfile.mkdtemp()
        try:
            open(os.path.join(td, "scene_0001_frame.jpg"), "w").close()
            open(os.path.join(td, "scene_0002_frame.png"), "w").close()
            sq = FW_SceneQueue()
            assert sq._count_scenes_from_folder(td) == 2
        finally:
            shutil.rmtree(td)

    def test_mixed_valid_and_invalid(self):
        td = tempfile.mkdtemp()
        try:
            open(os.path.join(td, "scene_0001_frame.png"), "w").close()
            open(os.path.join(td, "scene_notanumber_frame.png"), "w").close()
            open(os.path.join(td, "scene_0005_frame.png"), "w").close()
            sq = FW_SceneQueue()
            assert sq._count_scenes_from_folder(td) == 5
        finally:
            shutil.rmtree(td)


class TestSceneQueueStatusMessages:
    def setup_method(self):
        self.sq = FW_SceneQueue()
        self.fps = 24
        self.frames = 97

    def test_single_scene(self):
        status = self.sq._build_status(1, 1, True, self.frames, self.fps)
        assert "Single scene" in status
        assert "1 of 1" in status

    def test_first_scene_auto_queue(self):
        status = self.sq._build_status(1, 10, True, self.frames, self.fps)
        assert "10 scenes required" in status
        assert "Auto-queue enabled" in status
        assert "9 additional runs" in status

    def test_first_scene_manual(self):
        status = self.sq._build_status(1, 10, False, self.frames, self.fps)
        assert "DISABLED" in status
        assert "manually click" in status.lower()

    def test_middle_scene(self):
        status = self.sq._build_status(5, 10, True, self.frames, self.fps)
        assert "scene 5 of 10" in status
        assert "5 scenes remaining" in status

    def test_final_scene(self):
        status = self.sq._build_status(10, 10, True, self.frames, self.fps)
        assert "Final scene" in status

    def test_includes_frame_info(self):
        status = self.sq._build_status(3, 10, True, self.frames, self.fps)
        assert "97 frames" in status
        assert "24fps" in status


class TestSceneQueueOrchestrate:
    def test_basic_orchestrate_no_auto_queue(self):
        sq = FW_SceneQueue()
        result = sq.orchestrate(10, 97, 24, "test_folder", enable_auto_queue=False)
        assert result[0] == 1  # scene_index starts at 1
        assert result[1] == 10  # total_scenes
        assert "DISABLED" in result[2]  # status
        assert result[3]  # output_folder is non-empty

    def test_override_scene_index_disables_auto_queue(self):
        sq = FW_SceneQueue()
        result = sq.orchestrate(10, 97, 24, "test_folder", enable_auto_queue=True,
                                override_scene_index=3)
        assert result[0] == 3
        assert "Auto-queue is DISABLED" not in result[2]  # Override message
        assert "Override scene_index=3" not in result[2]  # Print, not in return

    def test_scene_index_clamped(self):
        sq = FW_SceneQueue()
        result = sq.orchestrate(5, 97, 24, "test_folder", enable_auto_queue=False,
                                override_scene_index=99)
        assert result[0] == 5  # clamped to max

    def test_frames_enforced_8n1(self):
        sq = FW_SceneQueue()
        result = sq.orchestrate(3, 100, 24, "test_folder", enable_auto_queue=False)
        assert result[0] >= 1
        assert result[1] == 3

    def test_triggers_ignore(self):
        sq = FW_SceneQueue()
        result = sq.orchestrate(1, 97, 24, "test_folder", enable_auto_queue=False,
                                trigger="anything")
        assert result[0] == 1
