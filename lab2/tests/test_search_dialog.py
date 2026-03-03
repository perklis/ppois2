from __future__ import annotations

import unittest
from datetime import date
from unittest.mock import patch

from PyQt6.QtCore import QDate

from tests._qt import ensure_app
from views.search_dialog import SearchDialog


class TestSearchDialog(unittest.TestCase):
    def setUp(self) -> None:
        ensure_app()
        self.dialog = SearchDialog()

    def test_get_criteria_checked_fields(self) -> None:
        self.dialog.pet_checkbox.setChecked(True)
        self.dialog.pet_name_edit.setText("Murka")
        self.dialog.birth_checkbox.setChecked(True)
        self.dialog.birth_date_edit.setDate(QDate(2020, 1, 1))

        criteria = self.dialog.get_criteria()

        self.assertEqual(criteria["pet_name"], "Murka")
        self.assertEqual(criteria["birth_date"], date(2020, 1, 1))
        self.assertIsNone(criteria["vet_name"])

    def test_emit_search_invalid_mode_shows_warning(self) -> None:
        self.dialog.pet_checkbox.setChecked(True)
        self.dialog.pet_name_edit.setText("OnlyName")

        with patch("PyQt6.QtWidgets.QMessageBox.warning") as warning:
            self.dialog._emit_search()

        warning.assert_called_once()

    def test_emit_search_valid_mode_emits_signal(self) -> None:
        captured = []
        self.dialog.search_requested.connect(captured.append)

        self.dialog.diagnosis_checkbox.setChecked(True)
        self.dialog.diagnosis_edit.setText("otit")
        self.dialog._emit_search()

        self.assertEqual(len(captured), 1)
        self.assertEqual(captured[0]["diagnosis_phrase"], "otit")
