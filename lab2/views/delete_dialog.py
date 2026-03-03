from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class DeleteDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Удаление записей")
        self.resize(500, 350)

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

        ok_btn = QPushButton("Удалить")
        cancel_btn = QPushButton("Отмена")

        buttons = QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(buttons)

        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)

    def _wrap(self, checkbox: QCheckBox, widget: QWidget) -> QWidget:
        layout = QHBoxLayout()
        layout.addWidget(checkbox)
        layout.addWidget(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        container = QWidget()
        container.setLayout(layout)
        return container

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
