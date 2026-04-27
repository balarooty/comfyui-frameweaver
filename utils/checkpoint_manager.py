import json
import os
from pathlib import Path


class CheckpointManager:
    def __init__(self, output_dir="output/frameweaver_checkpoints"):
        self.checkpoint_dir = Path(output_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def scene_path(self, scene_index: int) -> Path:
        return self.checkpoint_dir / f"scene_{int(scene_index):03d}"

    def save_metadata(self, scene_index: int, metadata: dict) -> Path:
        path = self.scene_path(scene_index)
        path.mkdir(parents=True, exist_ok=True)
        final_path = path / "metadata.json"
        tmp_path = path / "metadata.json.tmp"
        with open(tmp_path, "w", encoding="utf-8") as handle:
            json.dump(metadata, handle, indent=2, sort_keys=True)
        os.replace(tmp_path, final_path)
        return final_path

    def load_metadata(self, scene_index: int) -> dict:
        with open(self.scene_path(scene_index) / "metadata.json", encoding="utf-8") as handle:
            return json.load(handle)

    def get_resume_index(self) -> int:
        completed = sorted(self.checkpoint_dir.glob("scene_*/metadata.json"))
        if not completed:
            return 1
        last_name = completed[-1].parent.name
        return int(last_name.split("_")[-1]) + 1
