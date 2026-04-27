from pathlib import Path


def safe_output_path(output_filename: str, extension: str = ".mp4") -> str:
    name = (output_filename or "frameweaver_output").strip()
    if not name.endswith(extension):
        name = f"{name}{extension}"
    return str(Path(name))
