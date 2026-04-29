/**
 * FrameWeaver — Node Appearance System
 *
 * Assigns category-specific background colors and badge emojis to all
 * FrameWeaver nodes. Also injects context menu links for documentation
 * and related example workflows.
 *
 * ComfyUI extension pattern: registers once, hooks into nodeCreated to
 * override node colors on instantiation.
 */

import { app } from "../../scripts/app.js";

// ------------------------------------------------------------------ //
//  Category → color + badge mapping
// ------------------------------------------------------------------ //

const FW_CATEGORY_THEME = {
    "FrameWeaver/Input":       { color: "#2d5a27", badge: "📥" },
    "FrameWeaver/Sequencing":  { color: "#1a4a6e", badge: "🔗" },
    "FrameWeaver/Continuity":  { color: "#5a2d5a", badge: "🔒" },
    "FrameWeaver/Generation":  { color: "#6e4a1a", badge: "⚡" },
    "FrameWeaver/Bridge":      { color: "#4a1a1a", badge: "🌉" },
    "FrameWeaver/Output":      { color: "#1a6e4a", badge: "📤" },
    "FrameWeaver/PostProcess":  { color: "#6e1a4a", badge: "🎨" },
    "FrameWeaver/Audio":       { color: "#4a6e1a", badge: "🎵" },
    "FrameWeaver/AI":          { color: "#1a1a6e", badge: "🧠" },
    "FrameWeaver/UX":          { color: "#6e6e1a", badge: "✨" },
};

// Node name → category lookup (built from the Python NODE_CLASS_MAPPINGS)
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
    // UX
    "FW_QuickPipeline":       "FrameWeaver/UX",
};

// Nodes featured in example workflows → workflow filename
const FW_WORKFLOW_LINKS = {
    "FW_ScenePromptEvolver":  "frameweaver_ltx23_multi_scene_fflf.json",
    "FW_ScenePromptSelector": "frameweaver_ltx23_multi_scene_fflf.json",
    "FW_StyleAnchor":         "frameweaver_ltx23_multi_scene_fflf.json",
    "FW_ContinuityEncoder":   "frameweaver_ltx23_multi_scene_fflf.json",
    "FW_LTX23Settings":       "frameweaver_ltx23_multi_scene_fflf.json",
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
};

const FW_DOCS_URL = "https://github.com/balarooty/comfyui-frameweaver";

// ------------------------------------------------------------------ //
//  Utility: lighten a hex color for the title bar
// ------------------------------------------------------------------ //

function lightenHex(hex, amount) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    const lr = Math.min(255, Math.round(r + (255 - r) * amount));
    const lg = Math.min(255, Math.round(g + (255 - g) * amount));
    const lb = Math.min(255, Math.round(b + (255 - b) * amount));
    return `#${lr.toString(16).padStart(2, "0")}${lg.toString(16).padStart(2, "0")}${lb.toString(16).padStart(2, "0")}`;
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

        // Apply node background color
        node.color = theme.color;
        node.bgcolor = lightenHex(theme.color, 0.15);

        // Prepend badge to title
        if (node.title && !node.title.startsWith(theme.badge)) {
            node.title = `${theme.badge} ${node.title}`;
        }

        // ---------------------------------------------------------- //
        //  Context menu: docs + example workflow links
        // ---------------------------------------------------------- //

        const originalMenuOptions = node.getExtraMenuOptions;

        node.getExtraMenuOptions = function (canvas, options) {
            // Call original if it exists
            if (typeof originalMenuOptions === "function") {
                originalMenuOptions.call(this, canvas, options);
            }

            // Separator
            options.push(null);

            // Docs link
            options.push({
                content: "📖 FrameWeaver Docs",
                callback: () => {
                    window.open(FW_DOCS_URL, "_blank");
                },
            });

            // Example workflow link (if this node is featured)
            const workflowFile = FW_WORKFLOW_LINKS[node.type];
            if (workflowFile) {
                options.push({
                    content: `🎬 Example: ${workflowFile.replace(".json", "")}`,
                    callback: () => {
                        // Attempt to load the workflow via ComfyUI's built-in loader
                        const workflowUrl = `workflows/${workflowFile}`;
                        alert(`Load workflow: ${workflowUrl}\n\nDrag the JSON file from the workflows/ folder onto the ComfyUI canvas.`);
                    },
                });
            }
        };
    },
});
