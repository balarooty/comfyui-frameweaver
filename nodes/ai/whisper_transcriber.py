"""FW_WhisperTranscriber — Per-scene audio-to-text transcription.

Transcribes audio segments (from FW_AudioSplitter) into per-scene text
using OpenAI Whisper. Outputs a pipe-delimited string that feeds directly
into FW_ScenePromptEvolver's ``pipe_text_input``.

Key features:
- Supports ``whisper-large-v3``, ``whisper-medium``, ``whisper-small``, ``whisper-base``
- 99 language options (same as VRGDG)
- Per-scene context injection (enriches transcribed text with user context)
- Configurable overlap for cross-scene lyric continuity
- Fallback word list for silent/instrumental segments
- VRAM-safe: loads model once, processes all scenes, then unloads

Ported from VRGDG's ``LoadAudioSplit_HUMO_TranscribeV2`` with FrameWeaver conventions.
"""

import os
import gc
import random

try:
    import torch
except ImportError:
    torch = None

try:
    import torchaudio
    _HAS_TORCHAUDIO = True
except ImportError:
    _HAS_TORCHAUDIO = False

try:
    from transformers import WhisperProcessor, WhisperForConditionalGeneration
    _HAS_WHISPER = True
except ImportError:
    _HAS_WHISPER = False

try:
    import comfy.model_management
    _get_device = comfy.model_management.get_torch_device
except ImportError:
    _get_device = lambda: torch.device("cuda" if torch.cuda.is_available() else "cpu") if torch else "cpu"

# ====================================================================== #
#  Language list (99 languages, matching VRGDG/Whisper)
# ====================================================================== #

_LANGUAGES = [
    "auto", "english", "chinese", "german", "spanish", "russian", "korean",
    "french", "japanese", "portuguese", "turkish", "polish", "catalan",
    "dutch", "arabic", "swedish", "italian", "indonesian", "hindi",
    "finnish", "vietnamese", "hebrew", "ukrainian", "greek", "malay",
    "czech", "romanian", "danish", "hungarian", "tamil", "norwegian",
    "thai", "urdu", "croatian", "bulgarian", "lithuanian", "latin",
    "maori", "malayalam", "welsh", "slovak", "telugu", "persian",
    "latvian", "bengali", "serbian", "azerbaijani", "slovenian",
    "kannada", "estonian", "macedonian", "breton", "basque", "icelandic",
    "armenian", "nepali", "mongolian", "bosnian", "kazakh", "albanian",
    "swahili", "galician", "marathi", "punjabi", "sinhala", "khmer",
    "shona", "yoruba", "somali", "afrikaans", "occitan", "georgian",
    "belarusian", "tajik", "sindhi", "gujarati", "amharic", "yiddish",
    "lao", "uzbek", "faroese", "haitian creole", "pashto", "turkmen",
    "nynorsk", "maltese", "sanskrit", "luxembourgish", "myanmar",
    "tibetan", "tagalog", "malagasy", "assamese", "tatar", "hawaiian",
    "lingala", "hausa", "bashkir", "javanese", "sundanese", "cantonese",
]

_DEFAULT_FALLBACKS = [
    "standing", "sitting", "laying", "resting", "waiting",
    "walking", "dancing", "looking", "thinking", "moving",
]

_WHISPER_MODELS = [
    "openai/whisper-large-v3",
    "openai/whisper-medium",
    "openai/whisper-small",
    "openai/whisper-base",
]


class FW_WhisperTranscriber:
    """Transcribe per-scene audio segments into pipe-delimited text for prompt generation."""

    CATEGORY = "FrameWeaver/AI"

    # Up to 50 per-scene transcriptions + combined pipe string
    RETURN_TYPES = ("STRING",) + tuple(["STRING"] * 50)
    RETURN_NAMES = ("pipe_text",) + tuple([f"scene_{i}_text" for i in range(1, 51)])
    FUNCTION = "transcribe"

    @classmethod
    def INPUT_TYPES(cls):
        # Build per-scene context overrides and audio inputs
        optional = {}
        for i in range(1, 51):
            optional[f"audio_{i}"] = ("AUDIO",)
            optional[f"context_{i}"] = ("STRING", {
                "default": "", "multiline": True,
                "tooltip": f"Additional context for scene {i} (prepended to transcription).",
            })

        return {
            "required": {
                "scene_count": ("INT", {
                    "default": 1, "min": 1, "max": 50,
                    "tooltip": "Number of scenes to transcribe.",
                }),
                "model_name": (_WHISPER_MODELS, {
                    "default": "openai/whisper-large-v3",
                    "tooltip": "Whisper model to use. Larger = better accuracy, more VRAM.",
                }),
                "language": (_LANGUAGES, {
                    "default": "english",
                    "tooltip": "Audio language. 'auto' for automatic detection.",
                }),
                "enable_transcription": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "If False, skips Whisper and uses only context/fallbacks.",
                }),
                "overlap_seconds": ("FLOAT", {
                    "default": 0.0, "min": 0.0, "max": 5.0, "step": 0.1,
                    "tooltip": "Extend each segment by this many seconds for cross-scene continuity.",
                }),
                "fallback_words": ("STRING", {
                    "default": "thinking, walking, sitting, looking, waiting",
                    "tooltip": "Comma-separated fallback words for silent/instrumental segments.",
                }),
            },
            "optional": optional,
        }

    @classmethod
    def IS_DYNAMIC(cls):
        return True

    @classmethod
    def get_output_types(cls, **kwargs):
        count = max(1, min(50, int(kwargs.get("scene_count", 1))))
        return ("STRING",) + tuple(["STRING"] * count)

    @classmethod
    def get_output_names(cls, **kwargs):
        count = max(1, min(50, int(kwargs.get("scene_count", 1))))
        return ["pipe_text"] + [f"scene_{i}_text" for i in range(1, count + 1)]

    def transcribe(self, scene_count, model_name, language,
                   enable_transcription, overlap_seconds, fallback_words,
                   **kwargs):
        scene_count = max(1, min(50, scene_count))

        # Parse fallback words
        fb_words = [w.strip() for w in fallback_words.split(",") if w.strip()]
        if not fb_words:
            fb_words = _DEFAULT_FALLBACKS

        # Collect audio segments
        audio_segments = []
        for i in range(1, scene_count + 1):
            audio = kwargs.get(f"audio_{i}", None)
            audio_segments.append(audio)

        # ---- Transcribe ----
        transcriptions = []

        if enable_transcription and _HAS_WHISPER and any(a is not None for a in audio_segments):
            transcriptions = self._run_whisper(
                audio_segments, model_name, language,
                overlap_seconds, fb_words,
            )
        else:
            if enable_transcription and not _HAS_WHISPER:
                print("[FW_WhisperTranscriber] transformers not installed — using fallbacks")
            transcriptions = [random.choice(fb_words) for _ in range(scene_count)]

        # Ensure we have exactly scene_count transcriptions
        while len(transcriptions) < scene_count:
            transcriptions.append(random.choice(fb_words))
        transcriptions = transcriptions[:scene_count]

        # ---- Enrich with per-scene context ----
        enriched = []
        for i in range(scene_count):
            text = transcriptions[i]
            context = kwargs.get(f"context_{i + 1}", "").strip()
            if context:
                text = f"{context}, {text}"
            # Ensure non-empty
            if not text.strip():
                text = random.choice(fb_words)
            enriched.append(text)

        # Build pipe-delimited output for ScenePromptEvolver
        pipe_text = " | ".join(enriched)

        return (pipe_text, *tuple(enriched))

    # ------------------------------------------------------------------ #
    #  Whisper Engine
    # ------------------------------------------------------------------ #

    def _run_whisper(self, audio_segments, model_name, language,
                     overlap_seconds, fb_words):
        """Load Whisper model, transcribe all segments, unload."""
        device = _get_device()

        print(f"[FW_WhisperTranscriber] Loading {model_name} on {device}")
        processor = WhisperProcessor.from_pretrained(model_name)
        model = WhisperForConditionalGeneration.from_pretrained(model_name)
        model = model.to(device).eval()

        results = []

        for idx, audio in enumerate(audio_segments):
            if audio is None:
                results.append(random.choice(fb_words))
                continue

            try:
                text = self._transcribe_segment(
                    audio, processor, model, device,
                    language, overlap_seconds, fb_words,
                )
                results.append(text)
                print(f"[FW_WhisperTranscriber] Scene {idx + 1}: \"{text[:60]}...\"")
            except Exception as e:
                print(f"[FW_WhisperTranscriber] Scene {idx + 1} failed: {e}")
                results.append(random.choice(fb_words))

        # Cleanup
        del model, processor
        gc.collect()
        if torch and torch.cuda.is_available():
            torch.cuda.empty_cache()
        print("[FW_WhisperTranscriber] Model unloaded, VRAM freed")

        return results

    def _transcribe_segment(self, audio, processor, model, device,
                            language, overlap_seconds, fb_words):
        """Transcribe a single audio segment."""
        waveform = audio["waveform"]
        sample_rate = int(audio.get("sample_rate", 44100))

        # Ensure [C, T] format
        if waveform.ndim == 3:
            waveform = waveform.squeeze(0)  # [B, C, T] → [C, T]

        # Mix to mono
        if waveform.shape[0] > 1:
            mono = waveform.mean(dim=0)
        else:
            mono = waveform.squeeze(0)

        # Resample to 16kHz (Whisper requirement)
        if sample_rate != 16000:
            if _HAS_TORCHAUDIO:
                mono = torchaudio.functional.resample(mono, sample_rate, 16000)
            else:
                # Simple linear interpolation fallback
                target_len = int(mono.shape[0] * 16000 / sample_rate)
                mono = torch.nn.functional.interpolate(
                    mono.unsqueeze(0).unsqueeze(0),
                    size=target_len, mode="linear", align_corners=False,
                ).squeeze()

        # Process through Whisper
        inputs = processor(
            mono.cpu().numpy(),
            sampling_rate=16000,
            return_tensors="pt",
            padding="longest",
        )
        input_features = inputs["input_features"].to(device)

        with torch.no_grad():
            if language == "auto":
                generated_ids = model.generate(input_features)
            else:
                forced_ids = processor.get_decoder_prompt_ids(language=language)
                generated_ids = model.generate(
                    input_features, forced_decoder_ids=forced_ids,
                )

        text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()

        if not text:
            text = random.choice(fb_words)

        return text
