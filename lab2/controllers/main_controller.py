from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtSql import QSqlTableModel
from PyQt6.QtWidgets import QFileDialog, QMessageBox

from models.database import DatabaseManager
from models.proxy_model import VetFilterProxyModel, PagingProxyModel
from models.vet_record import (
    TABLE_HEADERS,
    QueryCriteria,
)
from models.xml_storage import read_records_from_xml, write_records_to_xml
from views.main_window import MainWindow
from views.add_dialog import AddDialog
from views.search_dialog import SearchDialog
from views.delete_dialog import DeleteDialog


class MainController:
    def __init__(self, window: MainWindow, db: DatabaseManager) -> None:
        self.window = window
        self.db = db

        self.table_model: QSqlTableModel | None = None
        self.filter_proxy: VetFilterProxyModel | None = None
        self.page_proxy: PagingProxyModel | None = None

        self._setup_models()
        self._connect_signals()
        self._refresh_view()

    def _setup_models(self) -> None:
        self.table_model = QSqlTableModel(self.window, self.db.db)
        self.table_model.setTable("vet_records")
        self.table_model.setEditStrategy(QSqlTableModel.EditStrategy.OnManualSubmit)

        for column, header in TABLE_HEADERS.items():
            self.table_model.setHeaderData(
            column,
            Qt.Orientation.Horizontal,
            header,
        )
        if not self.table_model.select():
            raise RuntimeError(self.table_model.lastError().text())

        self.filter_proxy = VetFilterProxyModel(self.window)
        self.filter_proxy.setSourceModel(self.table_model)

        self.page_proxy = PagingProxyModel(self.window)
        self.page_proxy.setSourceModel(self.filter_proxy)

        self.window.set_table_model(self.page_proxy)
        self._update_pagination()

    def _connect_signals(self) -> None:
        self.window.pagination.first_requested.connect(self._first_page)
        self.window.pagination.previous_requested.connect(self._previous_page)
        self.window.pagination.next_requested.connect(self._next_page)
        self.window.pagination.last_requested.connect(self._last_page)
        self.window.pagination.page_size_changed.connect(self._change_page_size)
        self.window.add_action.triggered.connect(self._add_record)
        self.window.search_action.triggered.connect(self._search_records)
        self.window.delete_action.triggered.connect(self._delete_records)

        self.window.save_xml_action.triggered.connect(self._save_xml)
        self.window.load_xml_action.triggered.connect(self._load_xml)
        self.window.open_db_action.triggered.connect(self._choose_database)
        self.window.exit_action.triggered.connect(self.window.close)

        self.window.view_table_action.triggered.connect(self.window.show_table)
        self.window.view_tree_action.triggered.connect(self._show_tree)

    def _first_page(self):
        self.page_proxy.first_page()
        self._refresh_view()
        self._update_pagination()

    def _previous_page(self):
        self.page_proxy.previous_page()
        self._refresh_view()
        self._update_pagination()

    def _next_page(self):
        self.page_proxy.next_page()
        self._refresh_view()
        self._update_pagination()

    def _last_page(self):
        self.page_proxy.last_page()
        self._refresh_view()
        self._update_pagination()

    def _change_page_size(self, value: int):
        self.page_proxy.set_page_size(value)
        self._refresh_view()
        self._update_pagination()

    def _update_pagination(self):
        current, total_pages, on_page, total = self._current_pagination_stats()
        self.window.pagination.set_info(current, total_pages, on_page, total)
    
    def _add_record(self) -> None:
        dialog = AddDialog(self.window)
        if not dialog.exec():
            return

        from models.vet_record import VetRecord

        data = dialog.get_data()
        record = VetRecord(**data)
        self.db.insert_record(record)

        self._sync_after_change()

    def _search_records(self) -> None:
        dialog = SearchDialog(self.window)
        dialog.set_model(self.page_proxy)
        dialog.set_page_size(self.page_proxy.page_size)
        self._update_search_pagination(dialog)

        def _refresh_all() -> None:
            self._refresh_view()
            self._update_pagination()
            self._update_search_pagination(dialog)

        dialog.first_requested.connect(lambda: (self.page_proxy.first_page(), _refresh_all()))
        dialog.previous_requested.connect(lambda: (self.page_proxy.previous_page(), _refresh_all()))
        dialog.next_requested.connect(lambda: (self.page_proxy.next_page(), _refresh_all()))
        dialog.last_requested.connect(lambda: (self.page_proxy.last_page(), _refresh_all()))
        dialog.page_size_changed.connect(
            lambda value: (self.page_proxy.set_page_size(value), _refresh_all())
        )

        def apply_search(criteria_dict):
            criteria = QueryCriteria(**criteria_dict)
            self.filter_proxy.set_criteria(criteria)
            self.page_proxy.first_page()
            _refresh_all()

        dialog.search_requested.connect(apply_search)
        dialog.exec()

    def _delete_records(self) -> None:
        dialog = DeleteDialog(self.window)
        if not dialog.exec():
            return

        criteria = QueryCriteria(**dialog.get_criteria())

        normalized = criteria.normalized()

        valid_modes = [
            normalized.pet_name and normalized.birth_date,
            normalized.last_visit_date and normalized.vet_name,
            normalized.diagnosis_phrase,
        ]

        if sum(bool(x) for x in valid_modes) != 1:
            QMessageBox.warning(
                self.window,
                "Ошибка",
                "Выберите один корректный режим удаления(по имени питомца и дате рождения; по дате последнего приема и ФИО ветеринара; по фразе из диагноза)"
            )
            return

        count = self.db.delete_by_criteria(criteria)

        self._sync_after_change()

        QMessageBox.information(
            self.window,
            "Удаление",
            f"Удалено записей: {count}" if count else "Записи не найдены",
        )

    def _save_xml(self) -> None:
        filename, _ = QFileDialog.getSaveFileName(
            self.window,
            "Сохранить XML",
            "xml/",
            "XML Files (*.xml *.XML);;All Files (*)"
        )

        if not filename:
            return

        if not filename.lower().endswith(".xml"):
            filename += ".xml"

        records = self.db.fetch_all_records()
        write_records_to_xml(records, Path(filename))
        QMessageBox.information(self.window, "XML", "Данные сохранены")

    def _load_xml(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self.window, "Загрузить XML", "", "XML Files (*.xml *.XML);;All Files (*)"
        )
        if not filename:
            return

        records = read_records_from_xml(Path(filename))
        self.db.replace_all_records(records)
        self._sync_after_change()

        QMessageBox.information(self.window, "XML", "Данные загружены")

    def _choose_database(self) -> None:
        filename, _ = QFileDialog.getSaveFileName(
            self.window, "Выбрать БД", "", "SQLite (*.db)"
        )
        if not filename:
            return

        self.db.switch_database(Path(filename))
        self._setup_models()
        self._refresh_view()

    def _sync_after_change(self) -> None:
        
        self.table_model.select()
        self._update_pagination()
        self._refresh_view()

    def _refresh_view(self) -> None:
        self.page_proxy.invalidate()
        self._rebuild_tree_rows()
        self.window.table_view.resizeColumnsToContents()

    def _show_tree(self) -> None:
        self._rebuild_tree_rows()
        self.window.show_tree()

    def _rebuild_tree_rows(self) -> None:
        model = self.page_proxy
        if model is None:
            self.window.set_tree_rows([])
            return

        rows: list[dict[str, str]] = []
        for row_index in range(model.rowCount()):
            rows.append(
                {
                    "pet_name": str(model.index(row_index, 1).data() or ""),
                    "birth_date": str(model.index(row_index, 2).data() or ""),
                    "last_visit_date": str(model.index(row_index, 3).data() or ""),
                    "vet_name": str(model.index(row_index, 4).data() or ""),
                    "diagnosis": str(model.index(row_index, 5).data() or ""),
                }
            )

        self.window.set_tree_rows(rows)

    def _update_search_pagination(self, dialog: SearchDialog) -> None:
        page, total_pages, on_page, total = self._current_pagination_stats()
        dialog.set_pagination_info(page, total_pages, on_page, total)

    def _current_pagination_stats(self) -> tuple[int, int, int, int]:
        total = self.page_proxy.total_rows
        total_pages = self.page_proxy.total_pages
        current = self.page_proxy.current_page
        on_page = min(
            self.page_proxy.page_size,
            max(0, total - (current - 1) * self.page_proxy.page_size),
        )
        return current, total_pages, on_page, total
