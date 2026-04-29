"""FW_SmartAssembler — Meta-driven video assembly with audio muxing.

Assembles collected scene videos into a final output with:
- Meta-driven trim/pad using FW_AUDIO_META durations
- Crossfade blending between scenes
- FFmpeg audio muxing for final video output
- Scene count validation and error reporting

Enhanced from the original FW_SmartAssembler with VRGDG's CombineVideosV2 patterns.
"""

import os
import subprocess
import tempfile

try:
    import torch
except ImportError:
    torch = None

try:
    import numpy as np
except ImportError:
    np = None

try:
    import folder_paths
    _OUTPUT_DIR = folder_paths.get_output_directory()
except ImportError:
    _OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "output")


def _find_ffmpeg():
    """Find system ffmpeg or fall back to imageio-ffmpeg."""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return "ffmpeg"
    except (subprocess.CalledProcessError, FileNotFoundError):
        try:
            import imageio_ffmpeg
            return imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            return None


class FW_SmartAssembler:
    """Assemble scene videos with meta-driven trim/pad, crossfade, and audio mux."""

    CATEGORY = "FrameWeaver/Output"
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("frames", "summary")
    FUNCTION = "assemble"
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "scene_collection": ("FW_SCENE_COLLECTION", {
                    "tooltip": "Scene collection from FW_SceneCollector.",
                }),
                "blend_mode": (["cut", "crossfade"], {
                    "default": "cut",
                    "tooltip": "How to join scenes. 'cut' = hard cut, 'crossfade' = blend overlap.",
                }),
                "blend_frames": ("INT", {
                    "default": 0, "min": 0, "max": 30, "step": 1,
                    "tooltip": "Number of frames to crossfade between scenes (0 = hard cut).",
                }),
            },
            "optional": {
                "audio_meta": ("FW_AUDIO_META", {
                    "tooltip": "Audio metadata for duration-driven trim/pad.",
                }),
                "audio": ("AUDIO", {
                    "tooltip": "Audio to mux into final video output.",
                }),
                "fps": ("FLOAT", {
                    "default": 24.0, "min": 1.0, "max": 120.0,
                    "tooltip": "FPS for audio muxing and trim calculations.",
                }),
                "output_filename": ("STRING", {
                    "default": "frameweaver_final",
                    "tooltip": "Output filename (without extension).",
                }),
                "save_video": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "If True, saves the assembled video as .mp4 via ffmpeg.",
                }),
            },
        }

    def assemble(self, scene_collection, blend_mode, blend_frames,
                 audio_meta=None, audio=None, fps=24.0,
                 output_filename="frameweaver_final", save_video=False):
        items = [scene_collection[key] for key in sorted(scene_collection)]
        if not items:
            raise ValueError("Scene collection is empty.")

        frames = [item["frames"] for item in items]
        scene_count = len(frames)

        # ---- Meta-driven trim/pad ----
        if audio_meta and "frames_per_scene" in audio_meta:
            target_frames_list = audio_meta["frames_per_scene"]
            frames = self._meta_trim_pad(frames, target_frames_list, fps)

        # ---- Blend ----
        if blend_mode == "crossfade" and blend_frames > 0 and len(frames) > 1:
            combined = self._crossfade(frames, int(blend_frames))
        else:
            combined = torch.cat(frames, dim=0)

        total_frames = int(combined.shape[0])
        duration_sec = total_frames / fps

        # ---- Summary ----
        summary_parts = [
            f"assembled {scene_count} scenes",
            f"{total_frames} frames",
            f"{duration_sec:.2f}s @ {fps}fps",
            f"mode={blend_mode}",
        ]

        # ---- Optional: save video with audio mux ----
        saved_path = ""
        if save_video:
            saved_path = self._save_video(combined, audio, fps, output_filename)
            if saved_path:
                summary_parts.append(f"saved: {saved_path}")

        summary = " | ".join(summary_parts)
        return (combined, summary)

    # ------------------------------------------------------------------ #
    #  Meta-driven trim/pad
    # ------------------------------------------------------------------ #

    def _meta_trim_pad(self, frame_batches, target_frames_list, fps):
        """Trim or pad each scene's frames to match the target from audio_meta."""
        result = []
        for idx, batch in enumerate(frame_batches):
            if idx < len(target_frames_list):
                target = int(target_frames_list[idx])
            else:
                target = int(batch.shape[0])

            current = int(batch.shape[0])

            if current > target:
                # Trim excess frames
                batch = batch[:target]
            elif current < target:
                # Pad with last frame repeated
                need = target - current
                last = batch[-1:].clone()
                pad = last.repeat(need, 1, 1, 1)
                batch = torch.cat([batch, pad], dim=0)

            result.append(batch)
        return result

    # ------------------------------------------------------------------ #
    #  Crossfade
    # ------------------------------------------------------------------ #

    def _crossfade(self, frame_batches, blend_frames):
        """Apply linear crossfade between adjacent scenes."""
        output = frame_batches[0]
        for next_batch in frame_batches[1:]:
            n = min(blend_frames, int(output.shape[0]), int(next_batch.shape[0]))
            if n <= 0:
                output = torch.cat([output, next_batch], dim=0)
                continue
            weights = torch.linspace(
                0.0, 1.0, n,
                device=output.device, dtype=output.dtype,
            ).view(n, 1, 1, 1)
            blended = output[-n:] * (1.0 - weights) + next_batch[:n] * weights
            output = torch.cat([output[:-n], blended, next_batch[n:]], dim=0)
        return output

    # ------------------------------------------------------------------ #
    #  Video save with FFmpeg audio mux
    # ------------------------------------------------------------------ #

    def _save_video(self, frames, audio, fps, filename):
        """Save assembled frames as .mp4, optionally muxing in audio via FFmpeg."""
        ffmpeg = _find_ffmpeg()
        if ffmpeg is None:
            print("[FW_SmartAssembler] FFmpeg not found — cannot save video")
            return ""

        os.makedirs(_OUTPUT_DIR, exist_ok=True)
        output_path = os.path.join(_OUTPUT_DIR, f"{filename}.mp4")

        # Convert frames to numpy [N, H, W, 3] uint8
        frames_np = (frames.cpu().numpy() * 255).clip(0, 255).astype(np.uint8)
        N, H, W, C = frames_np.shape

        # Write raw frames via pipe to ffmpeg
        video_cmd = [
            ffmpeg,
            "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{W}x{H}",
            "-pix_fmt", "rgb24",
            "-r", str(fps),
            "-i", "-",
        ]

        # If we have audio, write it to a temp file and mux
        audio_temp = None
        if audio is not None:
            try:
                import torchaudio
                audio_temp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                waveform = audio["waveform"]
                if waveform.ndim == 3:
                    waveform = waveform.squeeze(0)
                torchaudio.save(audio_temp.name, waveform.cpu(), int(audio["sample_rate"]))
                audio_temp.close()
                video_cmd.extend(["-i", audio_temp.name])
            except Exception as e:
                print(f"[FW_SmartAssembler] Audio write error: {e}")
                audio_temp = None

        video_cmd.extend([
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "fast",
            "-crf", "18",
        ])

        if audio_temp:
            video_cmd.extend(["-c:a", "aac", "-b:a", "192k", "-shortest"])

        video_cmd.append(output_path)

        try:
            proc = subprocess.Popen(video_cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            proc.stdin.write(frames_np.tobytes())
            proc.stdin.close()
            _, stderr = proc.communicate(timeout=300)

            if proc.returncode != 0:
                print(f"[FW_SmartAssembler] FFmpeg error: {stderr.decode()[-500:]}")
                return ""

            print(f"[FW_SmartAssembler] Saved video: {output_path}")
            return output_path

        except Exception as e:
            print(f"[FW_SmartAssembler] Save error: {e}")
            return ""
        finally:
            if audio_temp and os.path.exists(audio_temp.name):
                os.unlink(audio_temp.name)
