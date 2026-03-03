from __future__ import annotations

from pathlib import Path
from datetime import date

from PyQt6.QtSql import QSqlDatabase, QSqlQuery

from models.vet_record import VetRecord, QueryCriteria, build_where_clause


_SCHEMA_SQL = (
    "CREATE TABLE IF NOT EXISTS vet_records ("
    "id INTEGER PRIMARY KEY AUTOINCREMENT,"
    "pet_name TEXT NOT NULL,"
    "birth_date DATE NOT NULL,"
    "last_visit_date DATE NOT NULL,"
    "vet_name TEXT NOT NULL,"
    "diagnosis TEXT NOT NULL)"
)

_SELECT_ALL_SQL = (
    "SELECT id, pet_name, birth_date, last_visit_date, vet_name, diagnosis "
    "FROM vet_records ORDER BY id"
)

_INSERT_SQL = (
    "INSERT INTO vet_records "
    "(pet_name, birth_date, last_visit_date, vet_name, diagnosis) "
    "VALUES (:pet_name, :birth_date, :last_visit_date, :vet_name, :diagnosis)"
)


class DatabaseManager:
    def __init__(self, db_path: Path, connection_name: str = "vet_connection") -> None:
        self._connection_name = connection_name
        self._db_path = Path(db_path)
        self._db = self._open_connection(self._db_path)
        self.ensure_schema()

    @property
    def db(self) -> QSqlDatabase:
        return self._db

    def switch_database(self, db_path: Path) -> None:
        self._db_path = Path(db_path)
        if self._db.isOpen():
            self._db.close()
        self._db.setDatabaseName(str(self._db_path))
        if not self._db.open():
            raise RuntimeError(self._db.lastError().text())
        self.ensure_schema()

    def ensure_schema(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._exec(_SCHEMA_SQL)

    def fetch_all_records(self) -> list[VetRecord]:
        query = QSqlQuery(self._db)
        if not query.exec(_SELECT_ALL_SQL):
            raise RuntimeError(query.lastError().text())

        records: list[VetRecord] = []
        while query.next():
            records.append(
                VetRecord(
                    pet_name=str(query.value(1)),
                    birth_date=date.fromisoformat(str(query.value(2))),
                    last_visit_date=date.fromisoformat(str(query.value(3))),
                    vet_name=str(query.value(4)),
                    diagnosis=str(query.value(5)),
                )
            )
        return records

    def insert_record(self, record: VetRecord) -> None:
        query = QSqlQuery(self._db)
        if not query.prepare(_INSERT_SQL):
            raise RuntimeError(query.lastError().text())

        query.bindValue(":pet_name", record.pet_name)
        query.bindValue(":birth_date", record.birth_date.isoformat())
        query.bindValue(":last_visit_date", record.last_visit_date.isoformat())
        query.bindValue(":vet_name", record.vet_name)
        query.bindValue(":diagnosis", record.diagnosis)

        if not query.exec():
            raise RuntimeError(query.lastError().text())

    def replace_all_records(self, records: list[VetRecord]) -> None:
        if not self._db.transaction():
            raise RuntimeError(self._db.lastError().text())

        try:
            self._exec("DELETE FROM vet_records")

            insert = QSqlQuery(self._db)
            if not insert.prepare(_INSERT_SQL):
                raise RuntimeError(insert.lastError().text())

            for r in records:
                insert.bindValue(":pet_name", r.pet_name)
                insert.bindValue(":birth_date", r.birth_date.isoformat())
                insert.bindValue(":last_visit_date", r.last_visit_date.isoformat())
                insert.bindValue(":vet_name", r.vet_name)
                insert.bindValue(":diagnosis", r.diagnosis)

                if not insert.exec():
                    raise RuntimeError(insert.lastError().text())

            if not self._db.commit():
                raise RuntimeError(self._db.lastError().text())

        except Exception:
            self._db.rollback()
            raise

    def delete_by_criteria(self, criteria: QueryCriteria) -> int:
        where, params = build_where_clause(criteria)
        if not where:
            return 0

        query = QSqlQuery(self._db)
        if not query.prepare(f"DELETE FROM vet_records WHERE {where}"):
            raise RuntimeError(query.lastError().text())

        for key, value in params.items():
            query.bindValue(key, value)

        if not query.exec():
            raise RuntimeError(query.lastError().text())

        return max(0, int(query.numRowsAffected()))

    def _open_connection(self, db_path: Path) -> QSqlDatabase:
        db_path.parent.mkdir(parents=True, exist_ok=True)

        if QSqlDatabase.contains(self._connection_name):
            db = QSqlDatabase.database(self._connection_name)
        else:
            db = QSqlDatabase.addDatabase("QSQLITE", self._connection_name)

        db.setDatabaseName(str(db_path))

        if not db.open():
            raise RuntimeError(db.lastError().text())

        return db

    def _exec(self, sql: str) -> None:
        query = QSqlQuery(self._db)
        if not query.exec(sql):
            raise RuntimeError(query.lastError().text())