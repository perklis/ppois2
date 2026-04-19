from __future__ import annotations

from pathlib import Path

from lab1.domain.map_view import MapView
from lab1.domain.guide import Guide
from lab1.persistence.json_storage import JsonStorage
from lab1.services.id_generator import IdGenerator


BASE_DIR = Path(__file__).resolve().parent
LAB1_DIR = BASE_DIR.parent / "lab1"

storage = JsonStorage(str(LAB1_DIR / "data" / "storage.json"))
guide = Guide(map_view=MapView(rows=["A", "B", "C", "D"], cols=5), ids=IdGenerator())


def load_state() -> None:
    data = storage.load()
    guide.import_state(data)
    guide.seed_if_empty()


def save_state() -> None:
    storage.save(guide.export_state())


load_state()
