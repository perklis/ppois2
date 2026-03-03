from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableView,
    QVBoxLayout,
    QWidget,
)


class SearchDialog(QDialog):
    search_requested = pyqtSignal(dict)
    first_requested = pyqtSignal()
    previous_requested = pyqtSignal()
    next_requested = pyqtSignal()
    last_requested = pyqtSignal()
    page_size_changed = pyqtSignal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Поиск записей")
        self.resize(900, 550)

        self.pet_name_edit = QLineEdit()
        self.vet_name_edit = QLineEdit()
        self.diagnosis_edit = QLineEdit()

        self.birth_date_edit = QDateEdit()
        self.birth_date_edit.setCalendarPopup(True)

        self.last_visit_edit = QDateEdit()
        self.last_visit_edit.setCalendarPopup(True)

        self.pet_checkbox = QCheckBox()
        self.birth_checkbox = QCheckBox()
        self.visit_checkbox = QCheckBox()
        self.vet_checkbox = QCheckBox()
        self.diagnosis_checkbox = QCheckBox()

        form = QFormLayout()

        form.addRow("Имя питомца:", self._wrap(self.pet_checkbox, self.pet_name_edit))
        form.addRow("Дата рождения:", self._wrap(self.birth_checkbox, self.birth_date_edit))
        form.addRow("Дата последнего приема:", self._wrap(self.visit_checkbox, self.last_visit_edit))
        form.addRow("Ветеринар:", self._wrap(self.vet_checkbox, self.vet_name_edit))
        form.addRow("Фраза диагноза:", self._wrap(self.diagnosis_checkbox, self.diagnosis_edit))

        self.search_btn = QPushButton("Найти")

        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.horizontalHeader().setStretchLastSection(True)

        self.first_button = QPushButton("<<")
        self.prev_button = QPushButton("<")
        self.next_button = QPushButton(">")
        self.last_button = QPushButton(">>")
        self.page_size_spin = QSpinBox()
        self.page_size_spin.setRange(1, 1000)
        self.page_size_spin.setValue(10)
        self.page_label = QLabel("Страница 0 из 0")
        self.records_label = QLabel("Записей на странице: 0 | Всего записей: 0")

        pagination_layout = QHBoxLayout()
        pagination_layout.addWidget(self.first_button)
        pagination_layout.addWidget(self.prev_button)
        pagination_layout.addWidget(self.next_button)
        pagination_layout.addWidget(self.last_button)
        pagination_layout.addWidget(QLabel("На странице:"))
        pagination_layout.addWidget(self.page_size_spin)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.records_label)
        pagination_layout.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.search_btn)
        layout.addWidget(self.table_view)
        layout.addLayout(pagination_layout)

        self.search_btn.clicked.connect(self._emit_search)
        self.first_button.clicked.connect(self.first_requested.emit)
        self.prev_button.clicked.connect(self.previous_requested.emit)
        self.next_button.clicked.connect(self.next_requested.emit)
        self.last_button.clicked.connect(self.last_requested.emit)
        self.page_size_spin.valueChanged.connect(self.page_size_changed.emit)

    def _wrap(self, checkbox: QCheckBox, widget: QWidget) -> QWidget:
        layout = QHBoxLayout()
        layout.addWidget(checkbox)
        layout.addWidget(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        container = QWidget()
        container.setLayout(layout)
        return container

    def _emit_search(self) -> None:
        criteria = self.get_criteria()
    
        filled = [
            criteria["pet_name"] and criteria["birth_date"],
            criteria["last_visit_date"] and criteria["vet_name"],
            criteria["diagnosis_phrase"],
        ]
    
        if sum(bool(x) for x in filled) != 1:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "Ошибка",
                "Выберите один корректный режим поиска:\n"
                "1) Имя + дата рождения\n"
                "2) Дата последнего приема + ветеринар\n"
                "3) Фраза диагноза"
            )
            return
    
        self.search_requested.emit(criteria)

    def get_criteria(self) -> dict:
        return {
            "pet_name": self.pet_name_edit.text() if self.pet_checkbox.isChecked() else None,
            "birth_date": self.birth_date_edit.date().toPyDate()
                if self.birth_checkbox.isChecked() else None,
            "last_visit_date": self.last_visit_edit.date().toPyDate()
                if self.visit_checkbox.isChecked() else None,
            "vet_name": self.vet_name_edit.text() if self.vet_checkbox.isChecked() else None,
            "diagnosis_phrase": self.diagnosis_edit.text()
                if self.diagnosis_checkbox.isChecked() else None,
        }

    def set_model(self, model) -> None:
        self.table_view.setModel(model)
        self.table_view.hideColumn(0)

    def set_pagination_info(self, page: int, total_pages: int, on_page: int, total: int) -> None:
        self.page_label.setText(f"Страница {page} из {total_pages}")
        self.records_label.setText(
            f"Записей на странице: {on_page} | Всего записей: {total}"
        )

    def set_page_size(self, value: int) -> None:
        if self.page_size_spin.value() != value:
            self.page_size_spin.setValue(value)
