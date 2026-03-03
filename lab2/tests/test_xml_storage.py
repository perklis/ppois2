from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from models.vet_record import VetRecord
from models.xml_storage import read_records_from_xml, write_records_to_xml


class TestXmlStorage(unittest.TestCase):
    def test_write_and_read_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "records.xml"
            records = [
                VetRecord(
                    pet_name="Murka",
                    birth_date=date(2020, 1, 1),
                    last_visit_date=date(2024, 1, 2),
                    vet_name="Ivanov I.I.",
                    diagnosis="otit",
                ),
                VetRecord(
                    pet_name="Barsik",
                    birth_date=date(2019, 5, 3),
                    last_visit_date=date(2025, 2, 4),
                    vet_name="Petrov P.P.",
                    diagnosis="healthy",
                ),
            ]

            write_records_to_xml(records, path)
            loaded = read_records_from_xml(path)

            self.assertEqual(len(loaded), 2)
            self.assertEqual(loaded[0].pet_name, "Murka")
            self.assertEqual(loaded[1].diagnosis, "healthy")
            self.assertEqual(loaded[1].last_visit_date.isoformat(), "2025-02-04")

    def test_read_invalid_date_falls_back_to_today(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "invalid.xml"
            path.write_text(
                """<?xml version=\"1.0\" encoding=\"utf-8\"?>
<vet_records>
  <record>
    <pet_name>Murka</pet_name>
    <birth_date>not-a-date</birth_date>
    <last_visit_date>2024-02-02</last_visit_date>
    <vet_name>Ivanov</vet_name>
    <diagnosis>otit</diagnosis>
  </record>
</vet_records>
""",
                encoding="utf-8",
            )

            loaded = read_records_from_xml(path)

            self.assertEqual(len(loaded), 1)
