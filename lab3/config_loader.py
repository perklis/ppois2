import json
from pathlib import Path

def load_json(path, default=None):
    file_path = Path(path)
    if not file_path.exists():
        return default if default is not None else {}
    try:
        with file_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default if default is not None else {}

def save_json(path, data):
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def resolve_path(base_dir, relative_path):
    base = Path(base_dir)
    return str((base / relative_path).resolve())
