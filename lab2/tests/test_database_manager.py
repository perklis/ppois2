from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path
from uuid import uuid4

from PyQt6.QtSql import QSqlDatabase

from models.database import DatabaseManager
from models.vet_record import QueryCriteria, VetRecord
from tests._qt import ensure_app


class TestDatabaseManager(unittest.TestCase):
    def setUp(self) -> None:
        ensure_app()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.connection_name = f"test_conn_{uuid4().hex}"
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.manager = DatabaseManager(self.db_path, connection_name=self.connection_name)

    def tearDown(self) -> None:
        db = self.manager.db
        db.close()
        del db
        del self.manager
        if QSqlDatabase.contains(self.connection_name):
            QSqlDatabase.removeDatabase(self.connection_name)
        self.temp_dir.cleanup()

    def test_insert_and_fetch(self) -> None:
        self.manager.insert_record(
            VetRecord(
                pet_name="Murka",
                birth_date=date(2020, 1, 1),
                last_visit_date=date(2024, 1, 1),
                vet_name="Doctor A",
                diagnosis="otit",
            )
        )

        records = self.manager.fetch_all_records()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].pet_name, "Murka")
        self.assertEqual(records[0].birth_date.isoformat(), "2020-01-01")

    def test_replace_all_records(self) -> None:
        new_records = [
            VetRecord("A", date(2020, 1, 1), date(2024, 1, 1), "V1", "d1"),
            VetRecord("B", date(2021, 1, 1), date(2024, 2, 1), "V2", "d2"),
        ]
        self.manager.replace_all_records(new_records)

        loaded = self.manager.fetch_all_records()
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[1].pet_name, "B")

    def test_delete_by_all_supported_modes(self) -> None:
        records = [
            VetRecord("Murka", date(2020, 1, 1), date(2024, 1, 1), "Doctor A", "otit"),
            VetRecord("Barsik", date(2021, 2, 2), date(2024, 3, 3), "Doctor B", "cold"),
            VetRecord("Miya", date(2022, 4, 4), date(2025, 1, 1), "Doctor C", "otit severe"),
        ]
        self.manager.replace_all_records(records)

        deleted = self.manager.delete_by_criteria(
            QueryCriteria(pet_name="mUrKa", birth_date=date(2020, 1, 1))
        )
        self.assertEqual(deleted, 1)

        deleted = self.manager.delete_by_criteria(
            QueryCriteria(last_visit_date=date(2024, 3, 3), vet_name="doctor b")
        )
        self.assertEqual(deleted, 1)

        deleted = self.manager.delete_by_criteria(QueryCriteria(diagnosis_phrase="otit"))
        self.assertEqual(deleted, 1)

        self.assertEqual(len(self.manager.fetch_all_records()), 0)

    def test_delete_invalid_criteria_returns_zero(self) -> None:
        self.manager.insert_record(
            VetRecord("Murka", date(2020, 1, 1), date(2024, 1, 1), "Doctor", "diag")
        )

        deleted = self.manager.delete_by_criteria(QueryCriteria(pet_name="Murka"))
        self.assertEqual(deleted, 0)
        self.assertEqual(len(self.manager.fetch_all_records()), 1)

    def test_switch_database(self) -> None:
        self.manager.insert_record(
            VetRecord("Murka", date(2020, 1, 1), date(2024, 1, 1), "Doctor", "diag")
        )
        self.assertEqual(len(self.manager.fetch_all_records()), 1)

        second_db = Path(self.temp_dir.name) / "second.db"
        self.manager.switch_database(second_db)

        self.assertTrue(second_db.exists())
        self.assertEqual(len(self.manager.fetch_all_records()), 0)

