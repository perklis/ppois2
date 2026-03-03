from __future__ import annotations

import unittest
from datetime import date

from models.vet_record import QueryCriteria, build_where_clause


class TestVetRecordModel(unittest.TestCase):
    def test_normalized_and_empty(self) -> None:
        criteria = QueryCriteria(pet_name="  Barsik  ", vet_name=" ", diagnosis_phrase="  ")
        normalized = criteria.normalized()

        self.assertEqual(normalized.pet_name, "Barsik")
        self.assertIsNone(normalized.vet_name)
        self.assertIsNone(normalized.diagnosis_phrase)

        empty = QueryCriteria(pet_name="  ", vet_name=None)
        self.assertTrue(empty.is_empty())

    def test_where_clause_mode_pet_and_birth(self) -> None:
        criteria = QueryCriteria(pet_name="Murka", birth_date=date(2020, 1, 2))
        where, params = build_where_clause(criteria)

        self.assertIn("LOWER(pet_name)", where)
        self.assertIn("birth_date", where)
        self.assertEqual(params[":pet_name"], "Murka")
        self.assertEqual(params[":birth_date"], "2020-01-02")

    def test_where_clause_mode_diagnosis(self) -> None:
        criteria = QueryCriteria(diagnosis_phrase="otit")
        where, params = build_where_clause(criteria)

        self.assertEqual(where, "LOWER(diagnosis) LIKE LOWER(:diagnosis)")
        self.assertEqual(params[":diagnosis"], "%otit%")

    def test_where_clause_invalid_combination(self) -> None:
        criteria = QueryCriteria(pet_name="Murka")
        where, params = build_where_clause(criteria)

        self.assertEqual(where, "")
        self.assertEqual(params, {})
