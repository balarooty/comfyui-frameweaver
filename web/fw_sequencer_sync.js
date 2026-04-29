/**
 * FrameWeaver — Global Sequencer Real-Time Sync
 *
 * Broadcasts widget changes from FW_GlobalSequencer nodes to all connected
 * FrameWeaver nodes in the graph. This ensures FPS, resolution, and scene
 * index stay in sync across the UI before execution.
 *
 * Also provides tooltip descriptions for synced widgets so users understand
 * what each parameter controls without consulting external docs.
 *
 * Pattern inspired by WhatDreamsCost's LTXSequencer JS sync implementation.
 */

import { app } from "../../scripts/app.js";

const FW_SYNCED_WIDGETS = ["width", "height", "frames_per_scene", "fps", "scene_count", "current_scene"];
const FW_SEQUENCER_TYPE = "FW_GlobalSequencer";

/**
 * Tooltip descriptions for each synced widget.
 */
const FW_WIDGET_TOOLTIPS = {
    width:            "Output video width in pixels. Rounded to nearest multiple of 32 for LTX 2.3 compatibility.",
    height:           "Output video height in pixels. Rounded to nearest multiple of 32 for LTX 2.3 compatibility.",
    frames_per_scene: "Number of frames per scene. Enforced to 8n+1 for LTX 2.3 (e.g. 9, 17, 25, …, 97, …, 241).",
    fps:              "Frames per second for the output video. Standard values: 24 (film), 25 (PAL), 30 (NTSC).",
    scene_count:      "Total number of scenes in your project. Controls prompt evolver and duration list sizing.",
    current_scene:    "Which scene is currently being generated (1-indexed). Synced to all FW nodes in the graph.",
};

/**
 * Find all FW_GlobalSequencer nodes currently in the graph.
 */
function findSequencerNodes() {
    if (!app.graph || !app.graph._nodes) return [];
    return app.graph._nodes.filter((n) => n.type === FW_SEQUENCER_TYPE);
}

/**
 * Sync a widget value from one sequencer to all other sequencer nodes
 * and to all downstream FrameWeaver nodes that share the same widget name.
 */
function broadcastWidgetChange(sourceNode, widgetName, value) {
    if (!app.graph || !app.graph._nodes) return;

    for (const node of app.graph._nodes) {
        if (node.id === sourceNode.id) continue;

        // Sync between sequencer instances
        if (node.type === FW_SEQUENCER_TYPE) {
            const widget = node.widgets?.find((w) => w.name === widgetName);
            if (widget && widget.value !== value) {
                widget.value = value;
                node.setDirtyCanvas(true, true);
            }
            continue;
        }

        // Sync to downstream FrameWeaver nodes that accept this widget
        if (node.type?.startsWith("FW_")) {
            const widget = node.widgets?.find((w) => w.name === widgetName);
            if (widget && widget.value !== value) {
                widget.value = value;
                node.setDirtyCanvas(true, true);
            }
        }
    }
}

app.registerExtension({
    name: "FrameWeaver.SequencerSync",

    nodeCreated(node) {
        if (node.type !== FW_SEQUENCER_TYPE) return;

        // Attach change listeners and tooltips to synced widgets
        for (const widget of node.widgets || []) {
            if (!FW_SYNCED_WIDGETS.includes(widget.name)) continue;

            // Inject tooltip if ComfyUI supports it
            const tooltip = FW_WIDGET_TOOLTIPS[widget.name];
            if (tooltip) {
                widget.tooltip = tooltip;
            }

            const originalCallback = widget.callback;

            widget.callback = function (value) {
                // Call the original callback if one existed
                if (typeof originalCallback === "function") {
                    originalCallback.call(this, value);
                }

                // Broadcast the change to all other nodes
                broadcastWidgetChange(node, widget.name, value);
            };
        }
    },
});
