class FW_SmartAssembler:
    CATEGORY = "FrameWeaver/Output"
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("frames", "summary")
    FUNCTION = "assemble"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "scene_collection": ("FW_SCENE_COLLECTION",),
                "blend_mode": (["cut", "crossfade"], {"default": "cut"}),
                "blend_frames": ("INT", {"default": 0, "min": 0, "max": 30, "step": 1}),
            }
        }

    def assemble(self, scene_collection, blend_mode, blend_frames):
        try:
            import torch
        except Exception as exc:
            raise RuntimeError("FW_SmartAssembler requires torch inside ComfyUI.") from exc

        items = [scene_collection[key] for key in sorted(scene_collection)]
        if not items:
            raise ValueError("Scene collection is empty.")
        frames = [item["frames"] for item in items]
        if blend_mode == "crossfade" and blend_frames > 0 and len(frames) > 1:
            combined = self._crossfade(frames, int(blend_frames))
        else:
            combined = torch.cat(frames, dim=0)
        summary = f"assembled {len(items)} scenes into {int(combined.shape[0])} frames using {blend_mode}"
        return (combined, summary)

    def _crossfade(self, frame_batches, blend_frames):
        import torch

        output = frame_batches[0]
        for next_batch in frame_batches[1:]:
            n = min(blend_frames, int(output.shape[0]), int(next_batch.shape[0]))
            if n <= 0:
                output = torch.cat([output, next_batch], dim=0)
                continue
            weights = torch.linspace(0.0, 1.0, n, device=output.device, dtype=output.dtype).view(n, 1, 1, 1)
            blended = output[-n:] * (1.0 - weights) + next_batch[:n] * weights
            output = torch.cat([output[:-n], blended, next_batch[n:]], dim=0)
        return output
