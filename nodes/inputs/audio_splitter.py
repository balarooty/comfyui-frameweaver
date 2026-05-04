"""FW_AudioSplitter — Scene-driven audio chunking.

Splits an AUDIO input into per-scene chunks based on either a fixed
duration or custom per-scene durations from the SceneDurationList.

Key features:
- Fixed-duration mode: each scene gets ``scene_duration_seconds`` of audio
- Custom-duration mode: reads per-scene durations from an upstream float list
- Silence padding: if audio runs short, pads with silence
- Resamples to 44.1kHz for consistent frame calculations
- Stereo enforcement for VHS/media player compatibility

Ported from VRGDG's ``LoadAudioSplit_General`` with FrameWeaver conventions.
"""

import os
import math

try:
    import torch
    import torch.nn.functional as F
except ImportError:
    torch = None

try:
    import comfy.model_management
    _get_device = comfy.model_management.get_torch_device
except ImportError:
    _get_device = lambda: "cpu"


try:
    from ...utils.validation import nearest_valid_frame_count
except ImportError:
    from utils.validation import nearest_valid_frame_count


class FW_AudioSplitter:
    """Split audio into per-scene chunks with duration-driven segmentation."""

    CATEGORY = "FrameWeaver/Audio"

    # Dynamic output: up to 50 AUDIO chunks + meta + total_duration
    RETURN_TYPES = ("FW_AUDIO_META", "FLOAT") + tuple(["AUDIO"] * 50)
    RETURN_NAMES = ("audio_meta", "total_duration") + tuple([f"audio_{i}" for i in range(1, 51)])
    FUNCTION = "split_audio"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio": ("AUDIO", {"tooltip": "Input audio to split."}),
                "scene_count": ("INT", {
                    "default": 1, "min": 1, "max": 50,
                    "tooltip": "Number of scenes to split audio into.",
                }),
                "scene_duration_seconds": ("FLOAT", {
                    "default": 4.0, "min": 0.5, "max": 30.0, "step": 0.1,
                    "tooltip": "Duration of each scene in seconds (used in fixed-duration mode).",
                }),
                "fps": ("INT", {
                    "default": 24, "min": 1, "max": 120,
                    "tooltip": "Video FPS — used to compute frame-aligned durations.",
                }),
                "enforce_8n1": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "If True, aligns frame counts to 8n+1 for LTX 2.3.",
                }),
            },
            "optional": {
                "custom_durations_csv": ("STRING", {
                    "default": "",
                    "tooltip": "Comma-separated per-scene durations in seconds. Overrides fixed duration.",
                }),
                "set_index": ("INT", {
                    "default": 0, "min": 0,
                    "tooltip": "For multi-run workflows: which set (0-indexed) to extract.",
                }),
            },
        }

    @classmethod
    def IS_DYNAMIC(cls):
        return True

    @classmethod
    def get_output_types(cls, **kwargs):
        count = max(1, min(50, int(kwargs.get("scene_count", 1))))
        return ("FW_AUDIO_META", "FLOAT") + tuple(["AUDIO"] * count)

    @classmethod
    def get_output_names(cls, **kwargs):
        count = max(1, min(50, int(kwargs.get("scene_count", 1))))
        return ["audio_meta", "total_duration"] + [f"audio_{i}" for i in range(1, count + 1)]

    def split_audio(self, audio, scene_count, scene_duration_seconds, fps,
                    enforce_8n1=True, custom_durations_csv="", set_index=0):
        waveform = audio["waveform"]
        sample_rate = int(audio.get("sample_rate", 44100))

        # Ensure batch dimension [B, C, T]
        if waveform.ndim == 2:
            waveform = waveform.unsqueeze(0)

        # Resample to 44100 for consistent frame math
        target_sr = 44100
        if sample_rate != target_sr:
            print(f"[FW_AudioSplitter] Resampling {sample_rate} → {target_sr}")
            waveform = F.interpolate(
                waveform, scale_factor=target_sr / sample_rate,
                mode="linear", align_corners=False,
            )
            sample_rate = target_sr

        total_samples = waveform.shape[-1]
        total_duration = float(total_samples) / float(sample_rate)

        scene_count = max(1, min(50, scene_count))

        # Parse per-scene durations
        if custom_durations_csv and custom_durations_csv.strip():
            try:
                durations_sec = [float(d.strip()) for d in custom_durations_csv.split(",") if d.strip()]
                # Pad or truncate to scene_count
                while len(durations_sec) < scene_count:
                    durations_sec.append(scene_duration_seconds)
                durations_sec = durations_sec[:scene_count]
            except ValueError:
                print("[FW_AudioSplitter] Invalid custom_durations_csv, using fixed duration")
                durations_sec = [scene_duration_seconds] * scene_count
        else:
            durations_sec = [scene_duration_seconds] * scene_count

        # Compute frame counts and samples per scene
        frames_per_scene = []
        samples_per_scene = []
        for dur in durations_sec:
            raw_frames = int(round(fps * dur))
            if enforce_8n1:
                raw_frames = nearest_valid_frame_count(raw_frames)
            frames_per_scene.append(raw_frames)
            # Audio samples for this scene
            real_dur = raw_frames / fps
            samples_per_scene.append(int(round(real_dur * sample_rate)))

        # Calculate offset for set_index (multi-run support)
        total_samples_per_set = sum(samples_per_scene)
        offset_samples = set_index * total_samples_per_set

        # Split audio into segments
        segments = []
        current_offset = offset_samples

        for idx in range(scene_count):
            start_samp = current_offset
            end_samp = start_samp + samples_per_scene[idx]

            if start_samp >= total_samples:
                # Entirely past audio — fill with silence
                seg = torch.zeros((1, waveform.shape[1], samples_per_scene[idx]),
                                  dtype=waveform.dtype)
                print(f"[FW_AudioSplitter] Scene {idx + 1}: silence (past end)")
            else:
                end_samp_clamped = min(total_samples, end_samp)
                seg = waveform[..., start_samp:end_samp_clamped].contiguous().clone()

                # Pad with silence if short
                cur_len = seg.shape[-1]
                if cur_len < samples_per_scene[idx]:
                    pad_amount = samples_per_scene[idx] - cur_len
                    seg = F.pad(seg, (0, pad_amount))
                    print(f"[FW_AudioSplitter] Scene {idx + 1}: padded {pad_amount} samples")

            # Ensure stereo
            if seg.shape[1] == 1:
                seg = seg.repeat(1, 2, 1)

            segments.append({"waveform": seg, "sample_rate": sample_rate})
            current_offset = end_samp

        # Build metadata
        meta = {
            "scene_count": scene_count,
            "fps": fps,
            "sample_rate": sample_rate,
            "set_index": set_index,
            "total_duration": total_duration,
            "durations_sec": durations_sec,
            "frames_per_scene": frames_per_scene,
            "samples_per_scene": samples_per_scene,
            "total_sets": max(1, math.ceil(total_duration / sum(d for d in durations_sec))),
        }

        return (meta, total_duration, *tuple(segments))
