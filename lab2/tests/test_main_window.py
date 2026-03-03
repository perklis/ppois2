from __future__ import annotations

import unittest

from PyQt6.QtGui import QStandardItem, QStandardItemModel

from tests._qt import ensure_app
from views.main_window import MainWindow


class TestMainWindow(unittest.TestCase):
    def setUp(self) -> None:
        ensure_app()
        self.window = MainWindow()

    def test_switch_between_table_and_tree(self) -> None:
        self.window.show_tree()
        self.assertTrue(self.window.view_tree_action.isChecked())
        self.assertFalse(self.window.view_table_action.isChecked())

        self.window.show_table()
        self.assertTrue(self.window.view_table_action.isChecked())
        self.assertFalse(self.window.view_tree_action.isChecked())

    def test_set_table_model_hides_id_column(self) -> None:
        model = QStandardItemModel(0, 6)
        model.appendRow([QStandardItem("1") for _ in range(6)])

        self.window.set_table_model(model)

        self.assertIs(self.window.table_view.model(), model)
        self.assertTrue(self.window.table_view.isColumnHidden(0))

    def test_set_tree_rows_builds_children(self) -> None:
        rows = [
            {
                "pet_name": "Murka",
                "birth_date": "2020-01-01",
                "last_visit_date": "2024-01-01",
                "vet_name": "Ivanov",
                "diagnosis": "otit",
            }
        ]

        self.window.set_tree_rows(rows)

        self.assertEqual(self.window.tree_model.rowCount(), 1)
        root = self.window.tree_model.item(0, 0)
        self.assertEqual(root.text(), "Murka")
        self.assertEqual(root.rowCount(), 4)

