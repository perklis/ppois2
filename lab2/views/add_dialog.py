from __future__ import annotations

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QDateEdit,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)


class AddDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Добавить приём")

        self.pet_name_edit = QLineEdit()
        self.birth_date_edit = QDateEdit()
        self.birth_date_edit.setCalendarPopup(True)

        self.last_visit_edit = QDateEdit()
        self.last_visit_edit.setCalendarPopup(True)
        self.last_visit_edit.setDate(QDate.currentDate())

        self.vet_name_edit = QLineEdit()
        self.diagnosis_edit = QTextEdit()

        form = QFormLayout()
        form.addRow("Имя питомца:", self.pet_name_edit)
        form.addRow("Дата рождения:", self.birth_date_edit)
        form.addRow("Дата последнего приема:", self.last_visit_edit)
        form.addRow("ФИО ветеринара:", self.vet_name_edit)
        form.addRow("Диагноз:", self.diagnosis_edit)

        ok_btn = QPushButton("Добавить")
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

    def get_data(self) -> dict:
        return {
            "pet_name": self.pet_name_edit.text(),
            "birth_date": self.birth_date_edit.date().toPyDate(),
            "last_visit_date": self.last_visit_edit.date().toPyDate(),
            "vet_name": self.vet_name_edit.text(),
            "diagnosis": self.diagnosis_edit.toPlainText(),
        }
