from __future__ import annotations

from PyQt6.QtCore import QModelIndex, QSortFilterProxyModel, Qt

from models.vet_record import (
    PET_NAME_COL,
    BIRTH_DATE_COL,
    LAST_VISIT_DATE_COL,
    VET_NAME_COL,
    DIAGNOSIS_COL,
    QueryCriteria,
)


class VetFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._criteria: QueryCriteria | None = None
        self.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

    def set_criteria(self, criteria: QueryCriteria | None) -> None:
        self._criteria = criteria.normalized() if criteria else None
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        if self._criteria is None or self._criteria.is_empty():
            return True

        model = self.sourceModel()
        if model is None:
            return False

        c = self._criteria

        pet_name = str(
            model.data(model.index(source_row, PET_NAME_COL, source_parent), Qt.ItemDataRole.DisplayRole) or ""
        )
        birth_date = str(
            model.data(model.index(source_row, BIRTH_DATE_COL, source_parent), Qt.ItemDataRole.DisplayRole) or ""
        )
        last_visit_date = str(
            model.data(model.index(source_row, LAST_VISIT_DATE_COL, source_parent), Qt.ItemDataRole.DisplayRole) or ""
        )
        vet_name = str(
            model.data(model.index(source_row, VET_NAME_COL, source_parent), Qt.ItemDataRole.DisplayRole) or ""
        )
        diagnosis = str(
            model.data(model.index(source_row, DIAGNOSIS_COL, source_parent), Qt.ItemDataRole.DisplayRole) or ""
        )

        if c.pet_name and c.birth_date:
            return (
                pet_name.casefold() == c.pet_name.casefold()
                and birth_date == c.birth_date.isoformat()
            )

        if c.last_visit_date and c.vet_name:
            return (
                last_visit_date == c.last_visit_date.isoformat()
                and vet_name.casefold() == c.vet_name.casefold()
            )
    
        if c.diagnosis_phrase:
            return c.diagnosis_phrase.casefold() in diagnosis.casefold()

        return False

class PagingProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._page_size = 10
        self._current_page = 1

    @property
    def page_size(self) -> int:
        return self._page_size

    @property
    def current_page(self) -> int:
        return self._current_page

    @property
    def total_rows(self) -> int:
        model = self.sourceModel()
        return 0 if model is None else model.rowCount()

    @property
    def total_pages(self) -> int:
        if self.total_rows == 0:
            return 0
        return (self.total_rows + self._page_size - 1) // self._page_size

    def set_page_size(self, value: int) -> None:
        self._page_size = max(1, value)
        self._current_page = 1
        self.invalidateFilter()

    def set_page(self, value: int) -> None:
        if self.total_pages == 0:
            self._current_page = 1
            self.invalidateFilter()
            return
        self._current_page = min(max(1, value), self.total_pages)
        self.invalidateFilter()

    def first_page(self) -> None:
        self.set_page(1)

    def last_page(self) -> None:
        self.set_page(self.total_pages)

    def next_page(self) -> None:
        self.set_page(self._current_page + 1)

    def previous_page(self) -> None:
        self.set_page(self._current_page - 1)

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        if self.total_rows == 0:
            return False
        start = (self._current_page - 1) * self._page_size
        end = start + self._page_size
        return start <= source_row < end