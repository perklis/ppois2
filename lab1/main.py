from menu import Menu
from domain.map_view import MapView
from domain.guide import Guide
from persistence.json_storage import JsonStorage
from services.id_generator import IdGenerator


def main() -> None:
    storage = JsonStorage("data/storage.json")

    map_view = MapView(rows=["A", "B", "C", "D"], cols=5)
    guide = Guide(map_view=map_view, ids=IdGenerator())

    data = storage.load()
    guide.import_state(data)
    guide.seed_if_empty()

    menu = Menu(guide)
    try:
        menu.run()
    finally:
        storage.save(guide.export_state())


if __name__ == "__main__":
    main()
