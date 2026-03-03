from __future__ import annotations

import unittest
from datetime import date

from PyQt6.QtGui import QStandardItem, QStandardItemModel

from models.proxy_model import PagingProxyModel, VetFilterProxyModel
from models.vet_record import QueryCriteria
from tests._qt import ensure_app


class TestProxyModels(unittest.TestCase):
    def setUp(self) -> None:
        ensure_app()
        self.model = QStandardItemModel(0, 6)
        self._append_row(1, "Murka", "2020-01-01", "2024-02-02", "Ivanov", "otit")
        self._append_row(2, "Barsik", "2019-05-01", "2024-03-03", "Petrov", "healthy")
        self._append_row(3, "Miya", "2021-09-09", "2025-01-01", "Sidorov", "otit severe")

    def _append_row(self, row_id: int, pet: str, birth: str, visit: str, vet: str, diag: str) -> None:
        self.model.appendRow(
            [
                QStandardItem(str(row_id)),
                QStandardItem(pet),
                QStandardItem(birth),
                QStandardItem(visit),
                QStandardItem(vet),
                QStandardItem(diag),
            ]
        )

    def test_vet_filter_proxy_modes(self) -> None:
        proxy = VetFilterProxyModel()
        proxy.setSourceModel(self.model)

        proxy.set_criteria(QueryCriteria(pet_name="murka", birth_date=date(2020, 1, 1)))
        self.assertEqual(proxy.rowCount(), 1)

        proxy.set_criteria(QueryCriteria(last_visit_date=date(2024, 3, 3), vet_name="petrov"))
        self.assertEqual(proxy.rowCount(), 1)

        proxy.set_criteria(QueryCriteria(diagnosis_phrase="otit"))
        self.assertEqual(proxy.rowCount(), 2)

    def test_vet_filter_proxy_invalid_and_empty(self) -> None:
        proxy = VetFilterProxyModel()
        proxy.setSourceModel(self.model)

        proxy.set_criteria(QueryCriteria(pet_name="Murka"))
        self.assertEqual(proxy.rowCount(), 0)

        proxy.set_criteria(None)
        self.assertEqual(proxy.rowCount(), 3)

    def test_paging_proxy(self) -> None:
        paging = PagingProxyModel()
        paging.setSourceModel(self.model)

        self.assertEqual(paging.total_rows, 3)
        self.assertEqual(paging.total_pages, 1)

        paging.set_page_size(2)
        self.assertEqual(paging.page_size, 2)
        self.assertEqual(paging.current_page, 1)
        self.assertEqual(paging.total_pages, 2)
        self.assertEqual(paging.rowCount(), 2)

        paging.next_page()
        self.assertEqual(paging.current_page, 2)
        self.assertEqual(paging.rowCount(), 1)

        paging.previous_page()
        self.assertEqual(paging.current_page, 1)

        paging.last_page()
        self.assertEqual(paging.current_page, 2)

        paging.first_page()
        self.assertEqual(paging.current_page, 1)

    def test_paging_proxy_empty_model(self) -> None:
        empty = QStandardItemModel(0, 6)
        paging = PagingProxyModel()
        paging.setSourceModel(empty)

        self.assertEqual(paging.total_rows, 0)
        self.assertEqual(paging.total_pages, 0)
        paging.last_page()
        self.assertEqual(paging.current_page, 1)
        self.assertEqual(paging.rowCount(), 0)


