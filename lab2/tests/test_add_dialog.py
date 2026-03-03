from __future__ import annotations

import unittest
from datetime import date

from PyQt6.QtCore import QDate

from tests._qt import ensure_app
from views.add_dialog import AddDialog


class TestAddDialog(unittest.TestCase):
    def setUp(self) -> None:
        ensure_app()
        self.dialog = AddDialog()

    def test_get_data_returns_typed_values(self) -> None:
        self.dialog.pet_name_edit.setText("Murka")
        self.dialog.birth_date_edit.setDate(QDate(2020, 1, 2))
        self.dialog.last_visit_edit.setDate(QDate(2024, 3, 4))
        self.dialog.vet_name_edit.setText("Ivanov")
        self.dialog.diagnosis_edit.setPlainText("otit")

        data = self.dialog.get_data()

        self.assertEqual(data["pet_name"], "Murka")
        self.assertEqual(data["birth_date"], date(2020, 1, 2))
        self.assertEqual(data["last_visit_date"], date(2024, 3, 4))
        self.assertEqual(data["vet_name"], "Ivanov")
        self.assertEqual(data["diagnosis"], "otit")


