/**
 * FrameWeaver — Node Appearance System
 *
 * Assigns category-specific background colors, badge emojis, and branded
 * header strips to all FrameWeaver nodes. Injects context menu links for
 * documentation and example workflows.
 *
 * ComfyUI extension: registers once, hooks into nodeCreated to apply
 * node cosmetics on instantiation and onDrawForeground for live decorations.
 */

import { app } from "../../scripts/app.js";

// ------------------------------------------------------------------ //
//  Category → color + badge mapping
// ------------------------------------------------------------------ //

const FW_CATEGORY_THEME = {
    "FrameWeaver/Input":       { color: "#2563eb", bgcolor: "#1e3a8a", badge: "📥", label: "INPUT" },
    "FrameWeaver/Sequencing":  { color: "#0d9488", bgcolor: "#134e4a", badge: "🔗", label: "SEQ" },
    "FrameWeaver/Continuity":  { color: "#7c3aed", bgcolor: "#4c1d95", badge: "🔒", label: "CONT" },
    "FrameWeaver/Generation":  { color: "#6d28d9", bgcolor: "#3b0764", badge: "⚡", label: "GEN" },
    "FrameWeaver/Bridge":      { color: "#ea580c", bgcolor: "#7c2d12", badge: "🌉", label: "BRIDGE" },
    "FrameWeaver/Output":      { color: "#059669", bgcolor: "#064e3b", badge: "📤", label: "OUT" },
    "FrameWeaver/PostProcess": { color: "#e11d48", bgcolor: "#881337", badge: "🎨", label: "POST" },
    "FrameWeaver/Audio":       { color: "#d97706", bgcolor: "#78350f", badge: "🎵", label: "AUDIO" },
    "FrameWeaver/AI":          { color: "#4f46e5", bgcolor: "#312e81", badge: "🧠", label: "AI" },
    "FrameWeaver/UX":          { color: "#0891b2", bgcolor: "#164e63", badge: "✨", label: "UX" },
    "FrameWeaver/Quick":       { color: "#0891b2", bgcolor: "#164e63", badge: "✨", label: "QUICK" },
};

// Node name → category lookup
const FW_NODE_CATEGORIES = {
    // Input
    "FW_ScenePromptEvolver":  "FrameWeaver/Input",
    "FW_ScenePromptSelector": "FrameWeaver/Input",
    "FW_SceneDurationList":   "FrameWeaver/Input",
    "FW_LoadStarterFrame":    "FrameWeaver/Input",
    "FW_MultiImageLoader":    "FrameWeaver/Input",
    "FW_SpeechLengthCalc":    "FrameWeaver/Input",
    // Sequencing
    "FW_GlobalSequencer":     "FrameWeaver/Sequencing",
    // Continuity
    "FW_StyleAnchor":         "FrameWeaver/Continuity",
    "FW_ContinuityEncoder":   "FrameWeaver/Continuity",
    // Generation
    "FW_LTX23Settings":       "FrameWeaver/Generation",
    "FW_LTXSequencer":        "FrameWeaver/Generation",
    "FW_PrerollCompensator":  "FrameWeaver/Generation",
    "FW_FrameTrimmer":        "FrameWeaver/Generation",
    "FW_LatentVideoInit":     "FrameWeaver/Generation",
    "FW_LatentGuideInjector": "FrameWeaver/Generation",
    "FW_SceneSampler":        "FrameWeaver/Generation",
    "FW_DecodeVideo":         "FrameWeaver/Generation",
    // Bridge
    "FW_FrameBridge":         "FrameWeaver/Bridge",
    "FW_LastFrameExtractor":  "FrameWeaver/Bridge",
    // Output
    "FW_SceneCollector":      "FrameWeaver/Output",
    "FW_SmartAssembler":      "FrameWeaver/Output",
    "FW_AutoQueue":           "FrameWeaver/Output",
    // PostProcess
    "FW_ColorMatch":          "FrameWeaver/PostProcess",
    "FW_FilmGrain":           "FrameWeaver/PostProcess",
    "FW_CinematicPolish":     "FrameWeaver/PostProcess",
    "FW_LUTApply":            "FrameWeaver/PostProcess",
    "FW_LUTCreate":           "FrameWeaver/PostProcess",
    // Audio
    "FW_AudioSplitter":       "FrameWeaver/Audio",
    // AI
    "FW_WhisperTranscriber":  "FrameWeaver/AI",
    // UX / Quick
    "FW_QuickPipeline":       "FrameWeaver/Quick",
};

// Short descriptions shown in the header strip
const FW_NODE_DESCRIPTIONS = {
    "FW_ScenePromptEvolver":  "Build scene prompts with style inheritance",
    "FW_ScenePromptSelector": "Select a single scene from a prompt list",
    "FW_SceneDurationList":   "Define per-scene durations",
    "FW_LoadStarterFrame":    "Load and prepare the first frame",
    "FW_MultiImageLoader":    "Load multiple keyframe images",
    "FW_SpeechLengthCalc":    "Calculate frame counts from speech duration",
    "FW_GlobalSequencer":     "Central parameter hub — syncs FPS, resolution, scene index",
    "FW_StyleAnchor":         "Lock style identity across scenes",
    "FW_ContinuityEncoder":   "Encode continuity state for cross-scene coherence",
    "FW_LTX23Settings":       "LTX 2.3 model paths, resolution, and frame settings",
    "FW_LTXSequencer":        "Inject keyframe images into LTX latents",
    "FW_PrerollCompensator":  "Calculate over-generation frames for clean cuts",
    "FW_FrameTrimmer":        "Trim preroll/tail frames from decoded output",
    "FW_LatentVideoInit":     "Initialize empty video latent tensor",
    "FW_LatentGuideInjector": "Blend guide image into latent space",
    "FW_SceneSampler":        "Seed, sampler, and sigma schedule per scene",
    "FW_DecodeVideo":         "Decode video latent to frames",
    "FW_FrameBridge":         "Bridge frames between scenes with edit prompts",
    "FW_LastFrameExtractor":  "Extract the last frame from a video batch",
    "FW_SceneCollector":      "Collect generated scenes for assembly",
    "FW_SmartAssembler":      "Assemble scenes with crossfade and audio mux",
    "FW_AutoQueue":           "Auto-queue multi-chunk generation runs",
    "FW_ColorMatch":          "Match color palette to a reference image",
    "FW_FilmGrain":           "Apply cinematic film grain overlay",
    "FW_CinematicPolish":     "Apply professional cinematic post-processing",
    "FW_LUTApply":            "Apply .cube LUT color grading",
    "FW_LUTCreate":           "Generate LUT from a color palette",
    "FW_AudioSplitter":       "Split audio into per-scene chunks",
    "FW_WhisperTranscriber":  "Transcribe audio to per-scene text",
    "FW_QuickPipeline":       "2-scene quick setup with minimal config",
};

// Nodes featured in example workflows
const FW_WORKFLOW_LINKS = {
    "FW_ScenePromptEvolver":  "frameweaver_ltx23_multi_scene_fflf.json",
    "FW_ScenePromptSelector": "frameweaver_ltx23_multi_scene_fflf.json",
    "FW_StyleAnchor":         "frameweaver_ltx23_multi_scene_fflf.json",
    "FW_ContinuityEncoder":   "frameweaver_ltx23_multi_scene_fflf.json",
    "FW_LTX23Settings":       "frameweaver_ltx23_ia2v_single_scene.json",
    "FW_PrerollCompensator":  "frameweaver_ltx23_multi_scene_fflf.json",
    "FW_FrameTrimmer":        "frameweaver_ltx23_multi_scene_fflf.json",
    "FW_LastFrameExtractor":  "frameweaver_ltx23_multi_scene_fflf.json",
    "FW_SceneCollector":      "frameweaver_ltx23_multi_scene_fflf.json",
    "FW_DecodeVideo":         "frameweaver_ltx23_multi_scene_fflf.json",
    "FW_AudioSplitter":       "frameweaver_ltx23_music_video.json",
    "FW_WhisperTranscriber":  "frameweaver_ltx23_music_video.json",
    "FW_AutoQueue":           "frameweaver_ltx23_music_video.json",
    "FW_SmartAssembler":      "frameweaver_ltx23_music_video.json",
    "FW_ColorMatch":          "frameweaver_postprocess_demo.json",
    "FW_FilmGrain":           "frameweaver_postprocess_demo.json",
    "FW_CinematicPolish":     "frameweaver_postprocess_demo.json",
    "FW_LUTApply":            "frameweaver_postprocess_demo.json",
    "FW_LUTCreate":           "frameweaver_postprocess_demo.json",
    "FW_GlobalSequencer":     "frameweaver_ltx23_multi_scene_fflf.json",
    "FW_LatentVideoInit":     "frameweaver_ltx23_ia2v_single_scene.json",
    "FW_LTXSequencer":        "frameweaver_ltx23_ia2v_single_scene.json",
    "FW_LoadStarterFrame":    "frameweaver_ltx23_i2v_single_scene.json",
    "FW_MultiImageLoader":    "frameweaver_ltx23_ia2v_single_scene.json",
    "FW_QuickPipeline":       "frameweaver_ltx23_i2v_single_scene.json",
};

const FW_DOCS_URL = "https://github.com/balarooty/comfyui-frameweaver";

// ------------------------------------------------------------------ //
//  Utility: hex to rgba
// ------------------------------------------------------------------ //

function hexToRgba(hex, alpha) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r},${g},${b},${alpha})`;
}

// ------------------------------------------------------------------ //
//  Extension registration
// ------------------------------------------------------------------ //

app.registerExtension({
    name: "FrameWeaver.NodeAppearance",

    nodeCreated(node) {
        const category = FW_NODE_CATEGORIES[node.type];
        if (!category) return;

        const theme = FW_CATEGORY_THEME[category];
        if (!theme) return;

        // ---- Apply category colors ----
        node.color = theme.color;
        node.bgcolor = theme.bgcolor;

        // ---- Prepend badge to title ----
        if (node.title && !node.title.startsWith(theme.badge)) {
            node.title = `${theme.badge} ${node.title}`;
        }

        // ---- Draw branded header strip ----
        const originalDraw = node.onDrawForeground;
        node.onDrawForeground = function (ctx) {
            if (typeof originalDraw === "function") {
                originalDraw.call(this, ctx);
            }

            // Category tag in top-right corner
            const tagText = theme.label;
            ctx.save();
            ctx.font = "bold 9px Inter, sans-serif";
            const tagWidth = ctx.measureText(tagText).width + 10;
            const tagX = this.size[0] - tagWidth - 6;
            const tagY = -20;

            // Pill background
            ctx.fillStyle = hexToRgba(theme.color, 0.85);
            ctx.beginPath();
            ctx.roundRect(tagX, tagY, tagWidth, 16, 4);
            ctx.fill();

            // Pill text
            ctx.fillStyle = "#fff";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText(tagText, tagX + tagWidth / 2, tagY + 8);

            // Accent line below title
            ctx.fillStyle = hexToRgba(theme.color, 0.5);
            ctx.fillRect(0, 0, this.size[0], 2);

            ctx.restore();
        };

        // ---- Context menu: docs + example workflow ----
        const originalMenuOptions = node.getExtraMenuOptions;

        node.getExtraMenuOptions = function (canvas, options) {
            if (typeof originalMenuOptions === "function") {
                originalMenuOptions.call(this, canvas, options);
            }

            options.push(null); // separator

            // Node description
            const desc = FW_NODE_DESCRIPTIONS[node.type];
            if (desc) {
                options.push({
                    content: `ℹ️ ${desc}`,
                    disabled: true,
                });
            }

            // Docs link
            options.push({
                content: "📖 FrameWeaver Docs",
                callback: () => {
                    window.open(FW_DOCS_URL, "_blank");
                },
            });

            // Example workflow link
            const workflowFile = FW_WORKFLOW_LINKS[node.type];
            if (workflowFile) {
                options.push({
                    content: `🎬 Example: ${workflowFile.replace(".json", "")}`,
                    callback: () => {
                        alert(
                            `Load workflow: workflows/${workflowFile}\n\n` +
                            `Drag the JSON file from the workflows/ folder onto the ComfyUI canvas.`
                        );
                    },
                });
            }
        };
    },
});
