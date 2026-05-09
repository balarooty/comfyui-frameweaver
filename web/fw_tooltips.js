/**
 * FrameWeaver — Tooltip Overlay System
 *
 * Provides rich tooltip descriptions for all FrameWeaver node outputs
 * and connections. When hovering over output slots, shows the data type
 * and usage guidance.
 *
 * Also adds a help panel that shows when double-clicking a FW_ node,
 * displaying a formatted description with input/output documentation.
 */

import { app } from "../../scripts/app.js";

// ------------------------------------------------------------------ //
//  Output slot descriptions
// ------------------------------------------------------------------ //

const FW_OUTPUT_TOOLTIPS = {
    "FW_GlobalSequencer": {
        "width": "Video width in pixels (multiple of 32)",
        "height": "Video height in pixels (multiple of 32)",
        "frames_per_scene": "Frame count per scene (8n+1 enforced for LTX 2.3)",
        "fps": "Frames per second",
        "scene_count": "Total number of scenes in the project",
        "current_scene": "Currently active scene index (1-based)",
        "scene_duration_seconds": "Duration of one scene in seconds",
        "total_duration_seconds": "Total project duration in seconds",
    },
    "FW_LTX23Settings": {
        "width": "Video width (multiple of 32)",
        "height": "Video height (multiple of 32)",
        "frames": "Frame count (8n+1 enforced)",
        "fps": "Frames per second",
        "duration_seconds": "Computed duration based on frames / fps",
        "checkpoint_name": "Selected LTX checkpoint filename → UNETLoader",
        "distilled_lora_name": "Distilled LoRA filename → LoraLoader",
        "text_encoder_name": "Text encoder filename → DualCLIPLoader",
        "upscale_model_name": "Spatial upscaler filename → UpscaleModelLoader",
    },
    "FW_ScenePromptEvolver": {
        "prompt_list": "FW_PROMPT_LIST — Array of scene prompt dicts",
        "scene_1_positive": "First scene's positive prompt (for preview)",
        "negative": "Shared negative prompt",
        "scene_count": "Number of scenes generated",
    },
    "FW_ScenePromptSelector": {
        "positive": "Selected scene's positive prompt",
        "negative": "Selected scene's negative prompt",
        "bridge_prompt": "Transition prompt to next scene",
        "selected_index": "Actual scene index used (clamped)",
    },
    "FW_PrerollCompensator": {
        "frames_for_generation": "Total frames to generate (includes preroll + tail padding)",
        "target_frames": "Clean frame count after trimming",
        "preroll_frames": "Frames added at start (0 for scene 0)",
        "tail_loss_frames": "Frames added at end for LTX tail compensation",
        "trim_start": "Number of frames to skip when trimming",
    },
    "FW_FrameTrimmer": {
        "trimmed_frames": "Clean frames after removing preroll/tail",
        "frame_count": "Actual number of frames in output",
    },
    "FW_AudioSplitter": {
        "audio_meta": "FW_AUDIO_META — Duration, frame, and set metadata",
        "total_duration": "Total audio duration in seconds",
    },
    "FW_AutoQueue": {
        "chunk_index": "Current chunk being processed (0-based)",
        "total_chunks": "Total number of chunks needed",
        "instructions": "Human-readable progress instructions",
        "output_folder": "Path to the output folder for this run",
    },
    "FW_SmartAssembler": {
        "frames": "All assembled frames as IMAGE tensor",
        "summary": "Assembly summary with stats",
    },
    "FW_StyleAnchor": {
        "style_anchor": "FW_STYLE_ANCHOR — Style identity lock data",
        "reference_image": "Pass-through of the reference image",
    },
    "FW_ContinuityEncoder": {
        "positive_prompt": "Continuity-enhanced positive prompt",
        "scene_state": "FW_SCENE_STATE — Cross-scene coherence data",
    },
    "FW_LastFrameExtractor": {
        "last_frame": "Extracted last frame as IMAGE",
        "source_frame_count": "Original batch frame count",
    },
    "FW_FrameBridge": {
        "bridge_image": "Prepared bridge/edit image",
        "edit_prompt": "Generated edit prompt for the bridge",
    },
    "FW_LatentVideoInit": {
        "latent": "Empty video latent tensor",
        "width": "Computed width",
        "height": "Computed height",
        "frames": "Computed frame count",
    },
    "FW_LatentGuideInjector": {
        "latent": "Latent with guide image blended in",
        "guide_image": "Processed guide image (resized if needed)",
        "reference_strength": "Applied conditioning strength",
    },
    "FW_SceneSampler": {
        "seed": "Random seed for this scene",
        "sampler_name": "Selected sampler algorithm",
        "sigma_schedule": "Selected sigma schedule",
        "cleanup_status": "VRAM cleanup status message",
    },
    "FW_LoadStarterFrame": {
        "image": "Loaded and prepared starter frame",
        "width": "Image width",
        "height": "Image height",
    },
    "FW_SceneCollector": {
        "scene_collection": "FW_SCENE_COLLECTION — Dict of collected scenes",
        "metadata_json": "JSON string of collection metadata",
    },
    "FW_WhisperTranscriber": {
        "pipe_text": "All scenes pipe-delimited (scene1 | scene2 | ...)",
    },
    "FW_SpeechLengthCalc": {
        "slow_frames": "Frame count at 100 WPM (slow speech)",
        "avg_frames": "Frame count at 130 WPM (average speech)",
        "fast_frames": "Frame count at 160 WPM (fast speech)",
        "slow_seconds": "Duration at 100 WPM",
        "avg_seconds": "Duration at 130 WPM",
        "fast_seconds": "Duration at 160 WPM",
        "word_count": "Total words detected in quoted text",
    },
    "FW_LTXSequencer": {
        "latent": "Video latent with keyframe images injected",
    },
    "FW_DecodeVideo": {
        "images": "Decoded video frames as IMAGE tensor",
    },
    "FW_ColorMatch": {
        "images": "Color-matched frames",
    },
    "FW_FilmGrain": {
        "images": "Frames with film grain applied",
    },
    "FW_CinematicPolish": {
        "images": "Cinematically polished frames",
    },
    "FW_LUTApply": {
        "images": "LUT-graded frames",
    },
    "FW_LUTCreate": {
        "images": "Frames with generated LUT applied",
    },
};

// ------------------------------------------------------------------ //
//  Connection guidance — what to connect where
// ------------------------------------------------------------------ //

const FW_CONNECTION_GUIDE = {
    "FW_GlobalSequencer": "Connect outputs to all downstream FW nodes that need FPS, resolution, or scene index.",
    "FW_LTX23Settings": "Connect model names to loaders (UNETLoader, LoraLoader, DualCLIPLoader). Connect frames/fps to LatentVideoInit.",
    "FW_ScenePromptEvolver": "Connect prompt_list → FW_ScenePromptSelector. Or connect scene_1_positive → CLIPTextEncode.",
    "FW_PrerollCompensator": "Connect frames_for_generation → LatentVideoInit. Connect trim_start + target_frames → FW_FrameTrimmer.",
    "FW_AudioSplitter": "Connect audio_meta → FW_AutoQueue. Connect audio_N → VHS_VideoCombine or FW_SmartAssembler.",
    "FW_AutoQueue": "Terminal node — auto-queues additional runs. Connect audio_meta from FW_AudioSplitter.",
    "FW_SmartAssembler": "Connect scene_collection from FW_SceneCollector. Optional: audio + audio_meta for muxing.",
    "FW_LTXSequencer": "Connect vae from VAELoader, latent from FW_LatentVideoInit, multi_input from FW_MultiImageLoader.",
    "FW_LastFrameExtractor": "Connect output last_frame → next scene's FW_FrameBridge or FW_LatentGuideInjector.",
    "FW_StyleAnchor": "Connect reference_image → FW_ContinuityEncoder. Connect style_anchor → FW_ContinuityEncoder.",
};

// ------------------------------------------------------------------ //
//  Apply tooltips to output slots
// ------------------------------------------------------------------ //

app.registerExtension({
    name: "FrameWeaver.Tooltips",

    nodeCreated(node) {
        if (!node.type?.startsWith("FW_")) return;

        const tooltips = FW_OUTPUT_TOOLTIPS[node.type];
        if (!tooltips) return;

        // Apply tooltips to output slots
        setTimeout(() => {
            if (!node.outputs) return;
            for (const output of node.outputs) {
                const tip = tooltips[output.name];
                if (tip) {
                    output.tooltip = tip;
                }
            }
        }, 100);

        // ---- Double-click help panel ----
        const guide = FW_CONNECTION_GUIDE[node.type];
        if (guide) {
            const origDblClick = node.onDblClick;
            node.onDblClick = function (e) {
                if (typeof origDblClick === "function") {
                    origDblClick.call(this, e);
                }
                // Show a brief help panel via alert (simple but effective)
                const outputList = node.outputs
                    ? node.outputs.map((o) => `  ${o.name} (${o.type})`).join("\n")
                    : "  (none)";
                alert(
                    `🎬 ${node.type}\n\n` +
                    `📋 Connection Guide:\n${guide}\n\n` +
                    `📤 Outputs:\n${outputList}`
                );
            };
        }
    },
});
