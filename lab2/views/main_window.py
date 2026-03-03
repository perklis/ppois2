from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QAction, QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QTableView,
    QToolBar,
    QTreeView,
    QVBoxLayout,
    QWidget,
)


class PaginationPanel(QWidget):
    first_requested = pyqtSignal()
    previous_requested = pyqtSignal()
    next_requested = pyqtSignal()
    last_requested = pyqtSignal()
    page_size_changed = pyqtSignal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.first_button = QPushButton("<<")
        self.prev_button = QPushButton("<")
        self.next_button = QPushButton(">")
        self.last_button = QPushButton(">>")

        self.page_size_spin = QSpinBox()
        self.page_size_spin.setRange(1, 1000)
        self.page_size_spin.setValue(10)

        self.page_label = QLabel("Страница 0 из 0")
        self.records_label = QLabel("Записей на странице: 0 | Всего записей: 0")

        layout.addWidget(self.first_button)
        layout.addWidget(self.prev_button)
        layout.addWidget(self.next_button)
        layout.addWidget(self.last_button)
        layout.addWidget(QLabel("На странице:"))
        layout.addWidget(self.page_size_spin)
        layout.addWidget(self.page_label)
        layout.addWidget(self.records_label)
        layout.addStretch(1)

        self.first_button.clicked.connect(self.first_requested.emit)
        self.prev_button.clicked.connect(self.previous_requested.emit)
        self.next_button.clicked.connect(self.next_requested.emit)
        self.last_button.clicked.connect(self.last_requested.emit)
        self.page_size_spin.valueChanged.connect(self.page_size_changed.emit)

    def set_info(self, page: int, total_pages: int, on_page: int, total: int) -> None:
        self.page_label.setText(f"Страница {page} из {total_pages}")
        self.records_label.setText(
            f"Записей на странице: {on_page} | Всего записей: {total}"
        )

    def set_page_size(self, value: int) -> None:
        if self.page_size_spin.value() != value:
            self.page_size_spin.setValue(value)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Ветеринарные приёмы")
        self.resize(1200, 720)

        self.tree_model = QStandardItemModel()
        self.tree_model.setHorizontalHeaderLabels(["Поле", "Значение"])

        self._build_actions()
        self._build_menu_and_toolbar()
        self._build_central_area()


    def _build_actions(self) -> None:
        self.add_action = self._make_action("Добавить запись")
        self.search_action = self._make_action("Поиск")
        self.delete_action = self._make_action("Удаление")

        self.save_xml_action = self._make_action("Сохранить XML")
        self.load_xml_action = self._make_action("Загрузить XML")
        self.open_db_action = self._make_action("Выбрать БД")

        self.view_table_action = self._make_action("Таблица")
        self.view_tree_action = self._make_action("Дерево")

        self.exit_action = self._make_action("Выход")

        self.view_table_action.setCheckable(True)
        self.view_tree_action.setCheckable(True)
        self.view_table_action.setChecked(True)

    def _build_menu_and_toolbar(self) -> None:
        file_menu = self.menuBar().addMenu("Файл")
        file_menu.addAction(self.open_db_action)
        file_menu.addAction(self.save_xml_action)
        file_menu.addAction(self.load_xml_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        records_menu = self.menuBar().addMenu("Приёмы")
        records_menu.addAction(self.add_action)
        records_menu.addAction(self.search_action)
        records_menu.addAction(self.delete_action)

        view_menu = self.menuBar().addMenu("Вид")
        view_menu.addAction(self.view_table_action)
        view_menu.addAction(self.view_tree_action)

        toolbar = QToolBar("Инструменты")
        self.addToolBar(toolbar)

        toolbar.addAction(self.open_db_action)
        toolbar.addAction(self.save_xml_action)
        toolbar.addAction(self.load_xml_action)
        toolbar.addSeparator()
        toolbar.addAction(self.add_action)
        toolbar.addAction(self.search_action)
        toolbar.addAction(self.delete_action)
        toolbar.addSeparator()
        toolbar.addAction(self.view_table_action)
        toolbar.addAction(self.view_tree_action)

    def _build_central_area(self) -> None:
        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table_view.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.verticalHeader().setVisible(False)

        self.tree_view = QTreeView()
        self.tree_view.setModel(self.tree_model)
        self.tree_view.header().setStretchLastSection(True)
        self.tree_view.setAlternatingRowColors(True)

        self.stacked_view = QStackedWidget()
        self.stacked_view.addWidget(self.table_view)
        self.stacked_view.addWidget(self.tree_view)

        self.pagination = PaginationPanel()

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(self.stacked_view)
        layout.addWidget(self.pagination)

        self.setCentralWidget(central)

    
    def set_table_model(self, model) -> None:
        self.table_view.setModel(model)
        self.table_view.hideColumn(0) 
        self.table_view.resizeColumnsToContents()

    def set_tree_rows(self, rows: list[dict[str, str]]) -> None:
        self.tree_model.removeRows(0, self.tree_model.rowCount())

        for row in rows:
            root = QStandardItem(row["pet_name"])

            root.appendRow(
                [QStandardItem("Дата рождения"), QStandardItem(row["birth_date"])]
            )
            root.appendRow(
                [QStandardItem("Дата последнего приема"), QStandardItem(row["last_visit_date"])]
            )
            root.appendRow(
                [QStandardItem("Ветеринар"), QStandardItem(row["vet_name"])]
            )
            root.appendRow(
                [QStandardItem("Диагноз"), QStandardItem(row["diagnosis"])]
            )

            self.tree_model.appendRow([root, QStandardItem("")])

        self.tree_view.expandAll()

    def show_table(self) -> None:
        self.view_table_action.setChecked(True)
        self.view_tree_action.setChecked(False)
        self.stacked_view.setCurrentWidget(self.table_view)

    def show_tree(self) -> None:
        self.view_table_action.setChecked(False)
        self.view_tree_action.setChecked(True)
        self.stacked_view.setCurrentWidget(self.tree_view)

    def _make_action(self, text: str) -> QAction:
        return QAction(text, self)
