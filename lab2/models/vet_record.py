from __future__ import annotations
from dataclasses import dataclass
from datetime import date

ID_COL = 0
PET_NAME_COL = 1
BIRTH_DATE_COL = 2
LAST_VISIT_DATE_COL = 3
VET_NAME_COL = 4
DIAGNOSIS_COL = 5

TABLE_HEADERS = {
    PET_NAME_COL: "Имя питомца",
    BIRTH_DATE_COL: "Дата рождения",
    LAST_VISIT_DATE_COL: "Дата последнего приема",
    VET_NAME_COL: "ФИО ветеринара",
    DIAGNOSIS_COL: "Диагноз",
}


@dataclass(slots=True)
class VetRecord:
    pet_name: str
    birth_date: date
    last_visit_date: date
    vet_name: str
    diagnosis: str


@dataclass(slots=True)
class QueryCriteria:
    pet_name: str | None = None
    birth_date: date | None = None
    last_visit_date: date | None = None
    vet_name: str | None = None
    diagnosis_phrase: str | None = None

    def normalized(self) -> "QueryCriteria":
        return QueryCriteria(
            pet_name=_normalize_text(self.pet_name),
            birth_date=self.birth_date,
            last_visit_date=self.last_visit_date,
            vet_name=_normalize_text(self.vet_name),
            diagnosis_phrase=_normalize_text(self.diagnosis_phrase),
        )

    def is_empty(self) -> bool:
        n = self.normalized()
        return all(
            value is None
            for value in (
                n.pet_name,
                n.birth_date,
                n.last_visit_date,
                n.vet_name,
                n.diagnosis_phrase,
            )
        )


def build_where_clause(criteria: QueryCriteria) -> tuple[str, dict[str, object]]:
    normalized = criteria.normalized()

    if normalized.pet_name and normalized.birth_date:
        return (
            "LOWER(pet_name) = LOWER(:pet_name) AND birth_date = :birth_date",
            {
                ":pet_name": normalized.pet_name,
                ":birth_date": normalized.birth_date.isoformat(),
            },
        )

    if normalized.last_visit_date and normalized.vet_name:
        return (
            "last_visit_date = :last_visit_date AND LOWER(vet_name) = LOWER(:vet_name)",
            {
                ":last_visit_date": normalized.last_visit_date.isoformat(),
                ":vet_name": normalized.vet_name,
            },
        )

    if normalized.diagnosis_phrase:
        return (
            "LOWER(diagnosis) LIKE LOWER(:diagnosis)",
            {
                ":diagnosis": f"%{normalized.diagnosis_phrase}%",
            },
        )

    return "", {}


def _normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None
