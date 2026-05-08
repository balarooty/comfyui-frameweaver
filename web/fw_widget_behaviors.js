/**
 * FrameWeaver — Widget Behaviors
 *
 * Dynamic widget visibility, live status calculations, and interactive
 * behaviors for all FrameWeaver nodes.
 *
 * Features:
 * - FW_LTX23Settings: toggle frames/seconds widgets based on duration_mode
 * - FW_LTXSequencer: show/hide per-image widgets based on num_images
 * - FW_GlobalSequencer: live duration readout in node title
 * - FW_PrerollCompensator: show computed generation frames in title
 * - FW_AudioSplitter: show computed scene count in title
 * - FW_AutoQueue: show chunk progress in title
 * - FW_SmartAssembler: show blend mode indicator
 * - FW_ScenePromptEvolver: toggle pipe/individual modes
 */

import { app } from "../../scripts/app.js";

// ------------------------------------------------------------------ //
//  Helpers
// ------------------------------------------------------------------ //

/**
 * Find a widget on a node by name.
 */
function findWidget(node, name) {
    return node.widgets?.find((w) => w.name === name);
}

/**
 * Show or hide a widget. Hiding a widget collapses it so it takes no space.
 */
function setWidgetVisible(node, widgetName, visible) {
    const w = findWidget(node, widgetName);
    if (!w) return;

    if (visible) {
        w.type = w._fw_original_type || w.type;
        // Restore the original computeSize if we stored one
        if (w._fw_orig_computeSize) {
            w.computeSize = w._fw_orig_computeSize;
        }
    } else {
        // Store original type for restoration
        if (!w._fw_original_type && w.type !== "hidden") {
            w._fw_original_type = w.type;
        }
        w.type = "hidden";
        // Override computeSize to return zero height
        if (!w._fw_orig_computeSize) {
            w._fw_orig_computeSize = w.computeSize;
        }
        w.computeSize = () => [0, -4];
    }

    // Force node to recalculate size
    node.setSize(node.computeSize());
    node.setDirtyCanvas(true, true);
}

/**
 * Nearest valid frame count for LTX 2.3 (8n+1 rule).
 */
function nearestValid8n1(frames) {
    if (frames <= 9) return 9;
    return Math.round((frames - 1) / 8) * 8 + 1;
}

/**
 * Format seconds to mm:ss.f
 */
function formatDuration(seconds) {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const mins = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(1);
    return `${mins}m ${secs}s`;
}

// ------------------------------------------------------------------ //
//  FW_LTX23Settings — Duration mode toggle
// ------------------------------------------------------------------ //

function setupLTX23Settings(node) {
    const modeWidget = findWidget(node, "duration_mode");
    if (!modeWidget) return;

    function updateVisibility() {
        const mode = modeWidget.value;
        setWidgetVisible(node, "frames", mode === "frames");
        setWidgetVisible(node, "duration_seconds", mode === "seconds");
    }

    // Initial state
    updateVisibility();

    // On change
    const originalCallback = modeWidget.callback;
    modeWidget.callback = function (value) {
        if (typeof originalCallback === "function") {
            originalCallback.call(this, value);
        }
        updateVisibility();
    };

    // Live title update showing computed values
    const origTitle = node.title;
    const updateTitle = () => {
        const fps = findWidget(node, "fps")?.value || 24;
        const mode = modeWidget.value;
        let frames, dur;
        if (mode === "seconds") {
            const secs = findWidget(node, "duration_seconds")?.value || 4.0;
            frames = nearestValid8n1(Math.round(secs * fps));
            dur = frames / fps;
        } else {
            frames = nearestValid8n1(findWidget(node, "frames")?.value || 97);
            dur = frames / fps;
        }
        node.title = `${origTitle} [${frames}f / ${dur.toFixed(1)}s]`;
        node.setDirtyCanvas(true, false);
    };

    // Attach title updater to relevant widgets
    for (const wName of ["duration_mode", "frames", "duration_seconds", "fps"]) {
        const w = findWidget(node, wName);
        if (!w) continue;
        const origCb = w.callback;
        w.callback = function (value) {
            if (typeof origCb === "function") origCb.call(this, value);
            updateTitle();
        };
    }

    // Delay initial title update to let widgets initialize
    setTimeout(updateTitle, 100);
}

// ------------------------------------------------------------------ //
//  FW_LTXSequencer — Dynamic per-image widget visibility
// ------------------------------------------------------------------ //

function setupLTXSequencer(node) {
    const numWidget = findWidget(node, "num_images");
    if (!numWidget) return;

    function updatePerImageWidgets() {
        const count = parseInt(numWidget.value) || 0;
        for (let i = 1; i <= 50; i++) {
            const show = i <= count;
            setWidgetVisible(node, `insert_at_${i}`, show);
            setWidgetVisible(node, `strength_${i}`, show);
        }
    }

    updatePerImageWidgets();

    const origCb = numWidget.callback;
    numWidget.callback = function (value) {
        if (typeof origCb === "function") origCb.call(this, value);
        updatePerImageWidgets();
    };

    // Title shows active guide count
    const origTitle = node.title;
    const updateTitle = () => {
        const n = parseInt(numWidget.value) || 0;
        node.title = `${origTitle} [${n} guide${n !== 1 ? "s" : ""}]`;
        node.setDirtyCanvas(true, false);
    };
    numWidget.callback = function (value) {
        if (typeof origCb === "function") origCb.call(this, value);
        updatePerImageWidgets();
        updateTitle();
    };
    setTimeout(updateTitle, 100);
}

// ------------------------------------------------------------------ //
//  FW_GlobalSequencer — Live duration readout
// ------------------------------------------------------------------ //

function setupGlobalSequencer(node) {
    const origTitle = node.title;

    const updateTitle = () => {
        const fps = findWidget(node, "fps")?.value || 24;
        const frames = nearestValid8n1(findWidget(node, "frames_per_scene")?.value || 97);
        const scenes = findWidget(node, "scene_count")?.value || 3;
        const current = findWidget(node, "current_scene")?.value || 1;
        const sceneDur = frames / fps;
        const totalDur = scenes * sceneDur;
        node.title = `${origTitle} [Scene ${current}/${scenes} • ${formatDuration(totalDur)}]`;
        node.setDirtyCanvas(true, false);
    };

    for (const wName of ["fps", "frames_per_scene", "scene_count", "current_scene"]) {
        const w = findWidget(node, wName);
        if (!w) continue;
        const origCb = w.callback;
        w.callback = function (value) {
            if (typeof origCb === "function") origCb.call(this, value);
            updateTitle();
        };
    }

    setTimeout(updateTitle, 100);
}

// ------------------------------------------------------------------ //
//  FW_PrerollCompensator — Show computed frame counts
// ------------------------------------------------------------------ //

function setupPrerollCompensator(node) {
    const origTitle = node.title;

    const updateTitle = () => {
        const target = nearestValid8n1(findWidget(node, "target_frames")?.value || 97);
        const sceneIdx = findWidget(node, "scene_index")?.value || 0;
        const preroll = sceneIdx > 0 ? (findWidget(node, "preroll_frames")?.value || 6) : 0;
        const tail = findWidget(node, "tail_loss_frames")?.value || 8;
        const genFrames = nearestValid8n1(target + preroll + tail);
        node.title = `${origTitle} [${target}→${genFrames}f]`;
        node.setDirtyCanvas(true, false);
    };

    for (const wName of ["target_frames", "scene_index", "preroll_frames", "tail_loss_frames"]) {
        const w = findWidget(node, wName);
        if (!w) continue;
        const origCb = w.callback;
        w.callback = function (value) {
            if (typeof origCb === "function") origCb.call(this, value);
            updateTitle();
        };
    }

    setTimeout(updateTitle, 100);
}

// ------------------------------------------------------------------ //
//  FW_AudioSplitter — Scene count in title
// ------------------------------------------------------------------ //

function setupAudioSplitter(node) {
    const origTitle = node.title;

    const updateTitle = () => {
        const count = findWidget(node, "scene_count")?.value || 1;
        const dur = findWidget(node, "scene_duration_seconds")?.value || 4.0;
        const fps = findWidget(node, "fps")?.value || 24;
        const frames = nearestValid8n1(Math.round(dur * fps));
        node.title = `${origTitle} [${count} scenes × ${frames}f]`;
        node.setDirtyCanvas(true, false);
    };

    for (const wName of ["scene_count", "scene_duration_seconds", "fps"]) {
        const w = findWidget(node, wName);
        if (!w) continue;
        const origCb = w.callback;
        w.callback = function (value) {
            if (typeof origCb === "function") origCb.call(this, value);
            updateTitle();
        };
    }

    setTimeout(updateTitle, 100);
}

// ------------------------------------------------------------------ //
//  FW_AutoQueue — Chunk progress indicator
// ------------------------------------------------------------------ //

function setupAutoQueue(node) {
    const origTitle = node.title;

    const updateTitle = () => {
        const autoQ = findWidget(node, "enable_auto_queue")?.value;
        const label = autoQ ? "AUTO" : "MANUAL";
        node.title = `${origTitle} [${label}]`;
        node.setDirtyCanvas(true, false);
    };

    const w = findWidget(node, "enable_auto_queue");
    if (w) {
        const origCb = w.callback;
        w.callback = function (value) {
            if (typeof origCb === "function") origCb.call(this, value);
            updateTitle();
        };
    }

    setTimeout(updateTitle, 100);
}

// ------------------------------------------------------------------ //
//  FW_SmartAssembler — Blend mode indicator
// ------------------------------------------------------------------ //

function setupSmartAssembler(node) {
    const origTitle = node.title;

    const updateTitle = () => {
        const mode = findWidget(node, "blend_mode")?.value || "cut";
        const blendFrames = findWidget(node, "blend_frames")?.value || 0;
        const label = mode === "crossfade" && blendFrames > 0
            ? `crossfade ${blendFrames}f`
            : "hard cut";
        node.title = `${origTitle} [${label}]`;
        node.setDirtyCanvas(true, false);
    };

    for (const wName of ["blend_mode", "blend_frames"]) {
        const w = findWidget(node, wName);
        if (!w) continue;
        const origCb = w.callback;
        w.callback = function (value) {
            if (typeof origCb === "function") origCb.call(this, value);
            updateTitle();
        };
    }

    // Toggle blend_frames visibility based on blend_mode
    const modeW = findWidget(node, "blend_mode");
    if (modeW) {
        const origModeCb = modeW.callback;
        modeW.callback = function (value) {
            if (typeof origModeCb === "function") origModeCb.call(this, value);
            setWidgetVisible(node, "blend_frames", value === "crossfade");
            updateTitle();
        };
        // Initial visibility
        setTimeout(() => {
            setWidgetVisible(node, "blend_frames", modeW.value === "crossfade");
        }, 100);
    }

    setTimeout(updateTitle, 100);
}

// ------------------------------------------------------------------ //
//  FW_ScenePromptEvolver — Pipe mode indicator
// ------------------------------------------------------------------ //

function setupScenePromptEvolver(node) {
    const origTitle = node.title;

    const updateTitle = () => {
        const pipeText = findWidget(node, "pipe_text")?.value || "";
        if (pipeText.trim()) {
            const sceneCount = pipeText.split("|").filter((s) => s.trim()).length;
            node.title = `${origTitle} [pipe: ${sceneCount} scenes]`;
        } else {
            node.title = `${origTitle} [individual]`;
        }
        node.setDirtyCanvas(true, false);
    };

    const pipeW = findWidget(node, "pipe_text");
    if (pipeW) {
        const origCb = pipeW.callback;
        pipeW.callback = function (value) {
            if (typeof origCb === "function") origCb.call(this, value);
            updateTitle();
        };
    }

    setTimeout(updateTitle, 100);
}

// ------------------------------------------------------------------ //
//  FW_FilmGrain — Intensity label
// ------------------------------------------------------------------ //

function setupFilmGrain(node) {
    const origTitle = node.title;

    const updateTitle = () => {
        const intensity = findWidget(node, "intensity")?.value || 0.04;
        let label;
        if (intensity < 0.03) label = "subtle";
        else if (intensity < 0.07) label = "cinematic";
        else if (intensity < 0.15) label = "heavy";
        else label = "extreme";
        node.title = `${origTitle} [${label}]`;
        node.setDirtyCanvas(true, false);
    };

    const w = findWidget(node, "intensity");
    if (w) {
        const origCb = w.callback;
        w.callback = function (value) {
            if (typeof origCb === "function") origCb.call(this, value);
            updateTitle();
        };
    }

    setTimeout(updateTitle, 100);
}

// ------------------------------------------------------------------ //
//  FW_LUTCreate — Palette preview strip
// ------------------------------------------------------------------ //

function setupLUTCreate(node) {
    const origDraw = node.onDrawForeground;

    node.onDrawForeground = function (ctx) {
        if (typeof origDraw === "function") {
            origDraw.call(this, ctx);
        }

        // Find the palette widget
        const paletteW = findWidget(this, "palette_hex");
        if (!paletteW || !paletteW.value) return;

        const colors = paletteW.value
            .split(",")
            .map((c) => c.trim())
            .filter((c) => c.startsWith("#") && (c.length === 4 || c.length === 7));

        if (colors.length === 0) return;

        // Draw color strip at the bottom of the node
        const stripHeight = 8;
        const y = this.size[1] - stripHeight - 4;
        const segWidth = this.size[0] / colors.length;

        ctx.save();
        for (let i = 0; i < colors.length; i++) {
            ctx.fillStyle = colors[i];
            ctx.fillRect(i * segWidth, y, segWidth, stripHeight);
        }
        // Border around the strip
        ctx.strokeStyle = "rgba(255,255,255,0.2)";
        ctx.lineWidth = 1;
        ctx.strokeRect(0, y, this.size[0], stripHeight);
        ctx.restore();
    };
}

// ------------------------------------------------------------------ //
//  FW_SpeechLengthCalc — Duration readout
// ------------------------------------------------------------------ //

function setupSpeechLengthCalc(node) {
    const origTitle = node.title;

    const updateTitle = () => {
        const wpm = findWidget(node, "words_per_minute")?.value || 150;
        const fps = findWidget(node, "fps")?.value || 24;
        node.title = `${origTitle} [${wpm} WPM @ ${fps}fps]`;
        node.setDirtyCanvas(true, false);
    };

    for (const wName of ["words_per_minute", "fps"]) {
        const w = findWidget(node, wName);
        if (!w) continue;
        const origCb = w.callback;
        w.callback = function (value) {
            if (typeof origCb === "function") origCb.call(this, value);
            updateTitle();
        };
    }

    setTimeout(updateTitle, 100);
}

// ------------------------------------------------------------------ //
//  FW_QuickPipeline — Scene count + resolution
// ------------------------------------------------------------------ //

function setupQuickPipeline(node) {
    const origTitle = node.title;

    const updateTitle = () => {
        const w = findWidget(node, "width")?.value || 1280;
        const h = findWidget(node, "height")?.value || 720;
        const fps = findWidget(node, "fps")?.value || 24;
        const frames = nearestValid8n1(findWidget(node, "frames_per_scene")?.value || 97);
        node.title = `${origTitle} [${w}×${h} @ ${fps}fps]`;
        node.setDirtyCanvas(true, false);
    };

    for (const wName of ["width", "height", "fps", "frames_per_scene"]) {
        const w = findWidget(node, wName);
        if (!w) continue;
        const origCb = w.callback;
        w.callback = function (value) {
            if (typeof origCb === "function") origCb.call(this, value);
            updateTitle();
        };
    }

    setTimeout(updateTitle, 100);
}

// ------------------------------------------------------------------ //
//  Registration
// ------------------------------------------------------------------ //

const NODE_SETUP_MAP = {
    "FW_LTX23Settings":       setupLTX23Settings,
    "FW_LTXSequencer":        setupLTXSequencer,
    "FW_GlobalSequencer":     setupGlobalSequencer,
    "FW_PrerollCompensator":  setupPrerollCompensator,
    "FW_AudioSplitter":       setupAudioSplitter,
    "FW_AutoQueue":           setupAutoQueue,
    "FW_SmartAssembler":      setupSmartAssembler,
    "FW_ScenePromptEvolver":  setupScenePromptEvolver,
    "FW_FilmGrain":           setupFilmGrain,
    "FW_LUTCreate":           setupLUTCreate,
    "FW_SpeechLengthCalc":    setupSpeechLengthCalc,
    "FW_QuickPipeline":       setupQuickPipeline,
};

app.registerExtension({
    name: "FrameWeaver.WidgetBehaviors",

    nodeCreated(node) {
        const setup = NODE_SETUP_MAP[node.type];
        if (setup) {
            // Delay setup to ensure widgets are fully initialized
            setTimeout(() => setup(node), 50);
        }
    },
});
