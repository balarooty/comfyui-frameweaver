"""Tests for FW_AutoQueue and enhanced FW_SmartAssembler."""

import os
import re
import tempfile
import shutil
import pytest

from nodes.output.auto_queue import FW_AutoQueue
from nodes.output.smart_assembler import FW_SmartAssembler


# ------------------------------------------------------------------ #
#  FW_AutoQueue
# ------------------------------------------------------------------ #

class TestAutoQueueSchema:
    def test_required_inputs(self):
        it = FW_AutoQueue.INPUT_TYPES()
        for key in ["audio_meta", "folder_name", "enable_auto_queue", "overwrite_mode"]:
            assert key in it["required"]

    def test_optional_inputs(self):
        it = FW_AutoQueue.INPUT_TYPES()
        assert "override_chunk_index" in it["optional"]

    def test_return_types(self):
        assert FW_AutoQueue.RETURN_TYPES == ("INT", "INT", "STRING", "STRING")
        assert FW_AutoQueue.RETURN_NAMES == ("chunk_index", "total_chunks", "instructions", "output_folder")

    def test_output_node(self):
        assert FW_AutoQueue.OUTPUT_NODE is True


class TestAutoQueueFolderIndexing:
    def test_empty_folder_returns_zero(self):
        td = tempfile.mkdtemp()
        try:
            aq = FW_AutoQueue()
            assert aq._count_index_from_folder(td) == 0
        finally:
            shutil.rmtree(td)

    def test_counts_completed_videos(self):
        td = tempfile.mkdtemp()
        try:
            for i in range(4):
                open(os.path.join(td, f"video_{i:04d}_00001-audio.mp4"), "w").close()
            aq = FW_AutoQueue()
            assert aq._count_index_from_folder(td) == 4
        finally:
            shutil.rmtree(td)

    def test_nonexistent_folder_returns_zero(self):
        aq = FW_AutoQueue()
        assert aq._count_index_from_folder("/nonexistent/path/12345") == 0

    def test_ignores_non_matching_files(self):
        td = tempfile.mkdtemp()
        try:
            open(os.path.join(td, "random_file.txt"), "w").close()
            open(os.path.join(td, "video_0000_00001-audio.mp4"), "w").close()
            aq = FW_AutoQueue()
            assert aq._count_index_from_folder(td) == 1
        finally:
            shutil.rmtree(td)


class TestAutoQueueInstructions:
    def setup_method(self):
        self.aq = FW_AutoQueue()

    def test_single_chunk(self):
        instr = self.aq._build_instructions(0, 1, True)
        assert "Single chunk" in instr

    def test_first_chunk_auto_queue(self):
        instr = self.aq._build_instructions(0, 5, True)
        assert "5 chunks required" in instr
        assert "Auto-queue enabled" in instr

    def test_first_chunk_manual(self):
        instr = self.aq._build_instructions(0, 5, False)
        assert "DISABLED" in instr

    def test_middle_chunk(self):
        instr = self.aq._build_instructions(2, 5, True)
        assert "chunk 3 of 5" in instr
        assert "2 chunks remaining" in instr

    def test_final_chunk(self):
        instr = self.aq._build_instructions(4, 5, True)
        assert "Final chunk" in instr


# ------------------------------------------------------------------ #
#  FW_SmartAssembler
# ------------------------------------------------------------------ #

class TestSmartAssemblerSchema:
    def test_required_inputs(self):
        it = FW_SmartAssembler.INPUT_TYPES()
        assert "scene_collection" in it["required"]
        assert "blend_mode" in it["required"]
        assert "blend_frames" in it["required"]

    def test_optional_inputs(self):
        it = FW_SmartAssembler.INPUT_TYPES()
        for key in ["audio_meta", "audio", "fps", "output_filename", "save_video"]:
            assert key in it["optional"]

    def test_blend_modes(self):
        it = FW_SmartAssembler.INPUT_TYPES()
        modes = it["required"]["blend_mode"][0]
        assert "cut" in modes
        assert "crossfade" in modes

    def test_output_node(self):
        assert FW_SmartAssembler.OUTPUT_NODE is True
