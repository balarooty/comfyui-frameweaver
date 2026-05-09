/**
 * FrameWeaver — Global Sequencer Real-Time Sync
 *
 * Broadcasts widget changes from FW_GlobalSequencer nodes to all connected
 * FrameWeaver nodes in the graph. This ensures FPS, resolution, and scene
 * index stay in sync across the UI before execution.
 *
 * Also syncs between multiple FW_GlobalSequencer instances (if the user
 * places more than one for visual clarity).
 */

import { app } from "../../scripts/app.js";

const FW_SYNCED_WIDGETS = [
    "width", "height", "frames_per_scene", "fps",
    "scene_count", "current_scene",
];

const FW_SEQUENCER_TYPE = "FW_GlobalSequencer";

// Widget names that should propagate to other FW_ nodes
const FW_DOWNSTREAM_WIDGETS = new Set([
    "width", "height", "fps", "scene_count", "current_scene",
]);

/**
 * Sync a widget value from one sequencer to peer sequencers
 * and to downstream FrameWeaver nodes that share the same widget name.
 */
function broadcastWidgetChange(sourceNode, widgetName, value) {
    if (!app.graph || !app.graph._nodes) return;

    // Collect IDs of nodes directly or indirectly connected from sourceNode
    const connectedIds = new Set();
    const queue = [sourceNode.id];
    const visited = new Set(queue);

    while (queue.length > 0) {
        const currentId = queue.shift();
        for (const link of Object.values(app.graph.links)) {
            if (!link) continue;
            if (link.origin_id === currentId && !visited.has(link.target_id)) {
                visited.add(link.target_id);
                queue.push(link.target_id);
                connectedIds.add(link.target_id);
            }
        }
    }

    for (const node of app.graph._nodes) {
        if (node.id === sourceNode.id) continue;

        // Sync between sequencer instances (always)
        if (node.type === FW_SEQUENCER_TYPE) {
            const widget = node.widgets?.find((w) => w.name === widgetName);
            if (widget && widget.value !== value) {
                widget.value = value;
                node.setDirtyCanvas(true, true);
            }
            continue;
        }

        // Only sync to connected downstream FrameWeaver nodes
        if (
            node.type?.startsWith("FW_") &&
            FW_DOWNSTREAM_WIDGETS.has(widgetName) &&
            connectedIds.has(node.id)
        ) {
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

        // Attach broadcast listeners to synced widgets
        for (const widget of node.widgets || []) {
            if (!FW_SYNCED_WIDGETS.includes(widget.name)) continue;

            const originalCallback = widget.callback;

            widget.callback = function (value) {
                if (typeof originalCallback === "function") {
                    originalCallback.call(this, value);
                }
                broadcastWidgetChange(node, widget.name, value);
            };
        }
    },
});
