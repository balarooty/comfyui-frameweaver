def cleanup_vram() -> str:
    try:
        import gc
        import torch

        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
        return "cleanup_complete"
    except Exception as exc:
        return f"cleanup_skipped: {exc}"


def free_vram_gb() -> float:
    try:
        import torch

        if not torch.cuda.is_available():
            return 0.0
        free, _total = torch.cuda.mem_get_info()
        return free / (1024**3)
    except Exception:
        return 0.0
