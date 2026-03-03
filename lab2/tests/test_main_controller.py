from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from PyQt6.QtSql import QSqlDatabase

from controllers.main_controller import MainController
from models.database import DatabaseManager
from models.vet_record import VetRecord
from tests._qt import ensure_app
from views.main_window import MainWindow


class _FakeSignal:
    def __init__(self) -> None:
        self._callbacks = []

    def connect(self, callback) -> None:
        self._callbacks.append(callback)

    def emit(self, *args, **kwargs) -> None:
        for callback in list(self._callbacks):
            callback(*args, **kwargs)


class TestMainController(unittest.TestCase):
    def setUp(self) -> None:
        ensure_app()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.connection_name = f"controller_conn_{uuid4().hex}"
        db_path = Path(self.temp_dir.name) / "controller.db"
        self.db = DatabaseManager(db_path, connection_name=self.connection_name)
        self.db.replace_all_records(
            [
                VetRecord("Murka", date(2020, 1, 1), date(2024, 1, 1), "Doctor A", "otit"),
                VetRecord("Barsik", date(2019, 5, 5), date(2024, 3, 3), "Doctor B", "healthy"),
                VetRecord("Miya", date(2021, 2, 2), date(2025, 1, 1), "Doctor C", "otit severe"),
            ]
        )
        self.window = MainWindow()
        self.controller = MainController(self.window, self.db)

    def tearDown(self) -> None:
        self.window.table_view.setModel(None)
        self.controller.table_model = None
        self.controller.filter_proxy = None
        self.controller.page_proxy = None
        self.window.close()
        db = self.db.db
        db.close()
        del db
        del self.controller
        del self.window
        del self.db
        if QSqlDatabase.contains(self.connection_name):
            QSqlDatabase.removeDatabase(self.connection_name)
        self.temp_dir.cleanup()

    def test_show_tree_and_rebuild_tree_rows(self) -> None:
        self.controller._show_tree()
        self.assertEqual(self.window.tree_model.rowCount(), self.controller.page_proxy.rowCount())

        self.controller.page_proxy = None
        self.controller._rebuild_tree_rows()
        self.assertEqual(self.window.tree_model.rowCount(), 0)

    def test_add_record_accepted_and_rejected(self) -> None:
        class AddDialogAccepted:
            def __init__(self, _parent) -> None:
                pass

            def exec(self) -> int:
                return 1

            def get_data(self) -> dict:
                return {
                    "pet_name": "NewPet",
                    "birth_date": date(2022, 1, 1),
                    "last_visit_date": date(2025, 1, 2),
                    "vet_name": "Doctor Z",
                    "diagnosis": "check",
                }

        class AddDialogRejected:
            def __init__(self, _parent) -> None:
                pass

            def exec(self) -> int:
                return 0

        with patch("controllers.main_controller.AddDialog", AddDialogAccepted):
            before = len(self.db.fetch_all_records())
            self.controller._add_record()
            after = len(self.db.fetch_all_records())
            self.assertEqual(after, before + 1)

        with patch("controllers.main_controller.AddDialog", AddDialogRejected):
            before = len(self.db.fetch_all_records())
            self.controller._add_record()
            after = len(self.db.fetch_all_records())
            self.assertEqual(after, before)

    def test_delete_records_branches(self) -> None:
        class DeleteDialogInvalid:
            def __init__(self, _parent) -> None:
                pass

            def exec(self) -> int:
                return 1

            def get_criteria(self) -> dict:
                return {
                    "pet_name": "Murka",
                    "birth_date": None,
                    "last_visit_date": None,
                    "vet_name": None,
                    "diagnosis_phrase": None,
                }

        class DeleteDialogValid:
            def __init__(self, _parent) -> None:
                pass

            def exec(self) -> int:
                return 1

            def get_criteria(self) -> dict:
                return {
                    "pet_name": None,
                    "birth_date": None,
                    "last_visit_date": None,
                    "vet_name": None,
                    "diagnosis_phrase": "otit",
                }

        class DeleteDialogRejected:
            def __init__(self, _parent) -> None:
                pass

            def exec(self) -> int:
                return 0

        with patch("controllers.main_controller.DeleteDialog", DeleteDialogInvalid), patch(
            "controllers.main_controller.QMessageBox.warning"
        ) as warning:
            self.controller._delete_records()
            warning.assert_called_once()

        with patch("controllers.main_controller.DeleteDialog", DeleteDialogValid), patch(
            "controllers.main_controller.QMessageBox.information"
        ) as info:
            self.controller._delete_records()
            info.assert_called_once()

        with patch("controllers.main_controller.DeleteDialog", DeleteDialogRejected), patch(
            "controllers.main_controller.QMessageBox.warning"
        ) as warning:
            self.controller._delete_records()
            warning.assert_not_called()

    def test_save_load_and_choose_database(self) -> None:
        xml_path = Path(self.temp_dir.name) / "out.xml"

        with patch("controllers.main_controller.QFileDialog.getSaveFileName", return_value=("", "")):
            self.controller._save_xml()

        with patch(
            "controllers.main_controller.QFileDialog.getSaveFileName",
            return_value=(str(xml_path.with_suffix("")), ""),
        ), patch("controllers.main_controller.QMessageBox.information") as info:
            self.controller._save_xml()
            self.assertTrue(xml_path.exists())
            info.assert_called_once()

        with patch("controllers.main_controller.QFileDialog.getOpenFileName", return_value=("", "")):
            self.controller._load_xml()

        with patch(
            "controllers.main_controller.QFileDialog.getOpenFileName",
            return_value=(str(xml_path), ""),
        ), patch("controllers.main_controller.QMessageBox.information") as info:
            self.controller._load_xml()
            info.assert_called_once()

        new_db = Path(self.temp_dir.name) / "new_base.db"
        with patch("controllers.main_controller.QFileDialog.getSaveFileName", return_value=("", "")):
            self.controller._choose_database()

        with patch(
            "controllers.main_controller.QFileDialog.getSaveFileName",
            return_value=(str(new_db), ""),
        ):
            self.controller._choose_database()
            self.assertTrue(new_db.exists())

    def test_search_records_executes_connected_callbacks(self) -> None:
        created_dialogs = []

        class FakeSearchDialog:
            def __init__(self, _parent) -> None:
                self.search_requested = _FakeSignal()
                self.first_requested = _FakeSignal()
                self.previous_requested = _FakeSignal()
                self.next_requested = _FakeSignal()
                self.last_requested = _FakeSignal()
                self.page_size_changed = _FakeSignal()
                self.model = None
                self.page_size = None
                self.pagination_info = None
                created_dialogs.append(self)

            def set_model(self, model) -> None:
                self.model = model

            def set_page_size(self, value: int) -> None:
                self.page_size = value

            def set_pagination_info(self, page: int, total_pages: int, on_page: int, total: int) -> None:
                self.pagination_info = (page, total_pages, on_page, total)

            def exec(self) -> int:
                self.first_requested.emit()
                self.next_requested.emit()
                self.previous_requested.emit()
                self.last_requested.emit()
                self.page_size_changed.emit(2)
                self.search_requested.emit(
                    {
                        "pet_name": None,
                        "birth_date": None,
                        "last_visit_date": None,
                        "vet_name": None,
                        "diagnosis_phrase": "otit",
                    }
                )
                return 1

        with patch("controllers.main_controller.SearchDialog", FakeSearchDialog):
            self.controller._search_records()

        self.assertEqual(len(created_dialogs), 1)
        dialog = created_dialogs[0]
        self.assertIs(dialog.model, self.controller.page_proxy)
        self.assertEqual(dialog.page_size, 10)
        self.assertIsNotNone(dialog.pagination_info)
        self.assertEqual(self.controller.page_proxy.page_size, 2)
        self.assertEqual(self.controller.filter_proxy.rowCount(), 2)

