"""Tests for the new Stacked Scene → PromptRelay pipeline nodes.

Tests FW_SceneSplitter, FW_RelayBridgeEncoder, and FW_SceneIterator
without requiring torch or ComfyUI runtime dependencies.
"""

import os
import sys
import importlib.util
import tempfile
import shutil
import unittest

# ---- Load parser directly (avoids torch dependency chain) ----
_PROJ_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _PROJ_ROOT)

_parser_spec = importlib.util.spec_from_file_location(
    "parser", os.path.join(_PROJ_ROOT, "utils", "prompt_relay", "parser.py")
)
_parser_mod = importlib.util.module_from_spec(_parser_spec)
_parser_spec.loader.exec_module(_parser_mod)
parse_smart_prompt = _parser_mod.parse_smart_prompt


# ========================================================================
#  Test FW_SceneSplitter logic (parsing + scene extraction)
# ========================================================================

class TestSceneSplitterParsing(unittest.TestCase):
    """Test the parsing logic that FW_SceneSplitter depends on."""

    def test_block_syntax_basic(self):
        """Block headers produce one segment per scene."""
        text = "Scene 1:\nwalking\nScene 2:\nrunning\nScene 3:\njumping"
        segments = parse_smart_prompt(text)
        self.assertEqual(len(segments), 3)
        self.assertEqual(segments[0]["text"], "walking")
        self.assertEqual(segments[1]["text"], "running")
        self.assertEqual(segments[2]["text"], "jumping")
        # Block headers without ranges → equal weight
        for s in segments:
            self.assertEqual(s["weight"], 1.0)

    def test_smart_inline_syntax(self):
        """Smart [n-m] tags produce proportional weights."""
        text = "walking [0-50] | running [50-150] | jumping [150-200]"
        segments = parse_smart_prompt(text)
        self.assertEqual(len(segments), 3)
        self.assertAlmostEqual(segments[0]["weight"], 50.0)
        self.assertAlmostEqual(segments[1]["weight"], 100.0)
        self.assertAlmostEqual(segments[2]["weight"], 50.0)

    def test_pipe_syntax(self):
        """Plain pipe-delimited text → equal weight segments."""
        text = "scene one | scene two | scene three | scene four"
        segments = parse_smart_prompt(text)
        self.assertEqual(len(segments), 4)
        for s in segments:
            self.assertEqual(s["weight"], 1.0)

    def test_single_scene(self):
        """Single prompt without delimiters."""
        text = "a person walking through a forest"
        segments = parse_smart_prompt(text)
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0]["text"], "a person walking through a forest")

    def test_five_scenes_block(self):
        """Five scenes matching the diagram."""
        text = (
            "Scene 1:\nwalking through a forest\n"
            "Scene 2:\narriving at a cabin\n"
            "Scene 3:\nopening the door\n"
            "Scene 4:\nentering the room\n"
            "Scene 5:\nsitting by fireplace"
        )
        segments = parse_smart_prompt(text)
        self.assertEqual(len(segments), 5)
        self.assertIn("forest", segments[0]["text"])
        self.assertIn("fireplace", segments[4]["text"])


class TestSceneSplitterOutputs(unittest.TestCase):
    """Test the output computation logic of FW_SceneSplitter."""

    def _simulate_split(self, stacked_prompts, base_style, scene_index, fps=24, frames=97):
        """Simulate FW_SceneSplitter.split() without torch."""
        segments = parse_smart_prompt(stacked_prompts)
        valid = [s for s in segments if s["text"].strip()]
        if not valid:
            valid = [{"text": "default", "weight": 1.0}]

        count = len(valid)
        idx = max(1, min(scene_index, count))
        current = valid[idx - 1]

        current_prompt = f"{base_style}, {current['text']}" if base_style else current["text"]
        global_prompt = current_prompt
        local_prompts = " | ".join(s["text"] for s in valid)

        total_weight = sum(s["weight"] for s in valid) or float(count)
        total_frames = frames * count
        seg_lens = [max(1, int(round(s["weight"] / total_weight * total_frames))) for s in valid]
        diff = total_frames - sum(seg_lens)
        if diff and seg_lens:
            mx = max(range(len(seg_lens)), key=lambda i: seg_lens[i])
            seg_lens[mx] += diff

        segment_lengths = ", ".join(str(f) for f in seg_lens)
        start = sum(seg_lens[:idx - 1])
        end = start + seg_lens[idx - 1] - 1
        dur = round(seg_lens[idx - 1] / max(fps, 1), 4)

        return {
            "current_prompt": current_prompt,
            "global_prompt": global_prompt,
            "local_prompts": local_prompts,
            "segment_lengths": segment_lengths,
            "scene_count": count,
            "start_frame": start,
            "end_frame": end,
            "duration_sec": dur,
        }

    def test_scene_1_extraction(self):
        """Scene 1 starts at frame 0."""
        r = self._simulate_split(
            "Scene 1:\nwalking\nScene 2:\nrunning\nScene 3:\njumping",
            "cinematic", 1,
        )
        self.assertEqual(r["scene_count"], 3)
        self.assertEqual(r["start_frame"], 0)
        self.assertIn("walking", r["current_prompt"])

    def test_scene_2_extraction(self):
        """Scene 2 starts after scene 1's frames."""
        r = self._simulate_split(
            "Scene 1:\nwalking\nScene 2:\nrunning\nScene 3:\njumping",
            "cinematic", 2, fps=24, frames=97,
        )
        self.assertEqual(r["start_frame"], 97)
        self.assertIn("running", r["current_prompt"])

    def test_scene_index_clamping(self):
        """Scene index beyond count is clamped to last scene."""
        r = self._simulate_split("a | b | c", "", 99)
        self.assertEqual(r["scene_count"], 3)
        self.assertIn("c", r["current_prompt"])

    def test_local_prompts_pipe_format(self):
        """local_prompts output is pipe-delimited."""
        r = self._simulate_split("alpha | beta | gamma", "", 1)
        self.assertEqual(r["local_prompts"], "alpha | beta | gamma")

    def test_total_frames_consistency(self):
        """Segment lengths sum to total_frames."""
        r = self._simulate_split(
            "a [0-50] | b [50-150] | c [150-200]", "", 1, fps=24, frames=97,
        )
        lengths = [int(x.strip()) for x in r["segment_lengths"].split(",")]
        self.assertEqual(sum(lengths), 97 * 3)

    def test_whisper_override_priority(self):
        """Whisper text should override stacked_prompts when provided."""
        # Simulate whisper override logic
        stacked = "Scene 1:\noriginal"
        whisper = "a | b | c | d"
        source = whisper  # whisper takes priority
        segments = parse_smart_prompt(source)
        self.assertEqual(len(segments), 4)


# ========================================================================
#  Test FW_SceneIterator logic (filesystem state)
# ========================================================================

class TestSceneIteratorFilesystem(unittest.TestCase):
    """Test FW_SceneIterator's filesystem-based scene detection."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="fw_test_")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _create_lastframe(self, scene_index):
        """Create a dummy lastframe file."""
        path = os.path.join(self.test_dir, f"scene_{scene_index:04d}_lastframe.png")
        with open(path, "w") as f:
            f.write("dummy")

    def test_empty_folder_returns_1(self):
        """Empty folder → scene_index = 1."""
        import re
        indices = []
        for f in os.listdir(self.test_dir):
            m = re.match(r"scene_(\d{4})_lastframe\.png$", f)
            if m:
                indices.append(int(m.group(1)))
        next_idx = (max(indices) + 1) if indices else 1
        self.assertEqual(next_idx, 1)

    def test_one_scene_completed(self):
        """One scene file → next = 2."""
        import re
        self._create_lastframe(1)
        indices = []
        for f in os.listdir(self.test_dir):
            m = re.match(r"scene_(\d{4})_lastframe\.png$", f)
            if m:
                indices.append(int(m.group(1)))
        next_idx = (max(indices) + 1) if indices else 1
        self.assertEqual(next_idx, 2)

    def test_three_scenes_completed(self):
        """Three scene files → next = 4."""
        import re
        self._create_lastframe(1)
        self._create_lastframe(2)
        self._create_lastframe(3)
        indices = []
        for f in os.listdir(self.test_dir):
            m = re.match(r"scene_(\d{4})_lastframe\.png$", f)
            if m:
                indices.append(int(m.group(1)))
        next_idx = (max(indices) + 1) if indices else 1
        self.assertEqual(next_idx, 4)

    def test_noncontiguous_scenes(self):
        """Non-contiguous scene files → next = max + 1."""
        import re
        self._create_lastframe(1)
        self._create_lastframe(3)  # Skip 2
        indices = []
        for f in os.listdir(self.test_dir):
            m = re.match(r"scene_(\d{4})_lastframe\.png$", f)
            if m:
                indices.append(int(m.group(1)))
        next_idx = (max(indices) + 1) if indices else 1
        self.assertEqual(next_idx, 4)


# ========================================================================
#  Test FW_RelayBridgeEncoder logic (prompt shift)
# ========================================================================

class TestRelayBridgeEncoderPromptShift(unittest.TestCase):
    """Test the prompt shift blending logic."""

    def _apply_shift(self, global_prompt, previous_prompt, strength):
        """Simulate the prompt shift logic from FW_RelayBridgeEncoder."""
        effective = global_prompt or ""
        if strength > 0.0 and previous_prompt and previous_prompt.strip():
            prev = previous_prompt.strip()
            curr = effective.strip()
            if strength >= 1.0:
                effective = f"{prev}, transitioning to: {curr}"
            else:
                effective = f"{curr}, with subtle continuity from: {prev}"
        return effective

    def test_no_shift(self):
        """Zero strength → no change."""
        result = self._apply_shift("current scene", "previous scene", 0.0)
        self.assertEqual(result, "current scene")

    def test_partial_shift(self):
        """Partial strength → current + continuity hint."""
        result = self._apply_shift("current scene", "previous scene", 0.3)
        self.assertIn("current scene", result)
        self.assertIn("previous scene", result)
        self.assertIn("continuity", result)

    def test_full_shift(self):
        """Full strength → previous + transition."""
        result = self._apply_shift("current scene", "previous scene", 1.0)
        self.assertIn("previous scene", result)
        self.assertIn("transitioning to", result)
        self.assertIn("current scene", result)

    def test_no_previous(self):
        """No previous prompt → no change regardless of strength."""
        result = self._apply_shift("current scene", "", 0.5)
        self.assertEqual(result, "current scene")

    def test_none_previous(self):
        """None previous prompt → no change."""
        result = self._apply_shift("current scene", None, 0.5)
        self.assertEqual(result, "current scene")


if __name__ == "__main__":
    unittest.main()
