from __future__ import annotations

import unittest
from datetime import date

from PyQt6.QtCore import QDate

from tests._qt import ensure_app
from views.delete_dialog import DeleteDialog


class TestDeleteDialog(unittest.TestCase):
    def setUp(self) -> None:
        ensure_app()
        self.dialog = DeleteDialog()

    def test_get_criteria_uses_checked_fields_only(self) -> None:
        self.dialog.pet_name_edit.setText("Murka")
        self.dialog.pet_checkbox.setChecked(True)

        self.dialog.birth_date_edit.setDate(QDate(2020, 1, 1))
        self.dialog.birth_checkbox.setChecked(True)

        self.dialog.vet_name_edit.setText("Ivanov")
        self.dialog.vet_checkbox.setChecked(False)

        criteria = self.dialog.get_criteria()

        self.assertEqual(criteria["pet_name"], "Murka")
        self.assertEqual(criteria["birth_date"], date(2020, 1, 1))
        self.assertIsNone(criteria["vet_name"])
        self.assertIsNone(criteria["diagnosis_phrase"])
