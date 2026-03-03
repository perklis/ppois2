from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from controllers.main_controller import MainController
from models.database import DatabaseManager
from views.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)

    data_dir = Path(__file__).resolve().parent / "data"
    db_manager = DatabaseManager(data_dir / "library.db")
    window = MainWindow()
    controller = MainController(window, db_manager)
    window.controller = controller

    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())