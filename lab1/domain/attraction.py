from exceptions import ValidationError
from domain.entity_id import EntityId
from domain.photo import Photo


class Attraction:
    def __init__(
        self,
        attraction_id: EntityId,
        name: str,
        description: str,
        cell_id: str,
        tags: list[str] | None = None,
        photo_ids: list[EntityId] | None = None,
    ) -> None:
        self.id = attraction_id

        self.name = name.strip()
        if not self.name:
            raise ValidationError("Название не может быть пустым")

        self.description = description.strip()
        if not self.description:
            raise ValidationError("Описание не может быть пустым")

        self.cell_id = self._validate_cell_id(cell_id)

        self.tags = list(tags) if tags is not None else []
        self.photo_ids = list(photo_ids) if photo_ids is not None else []

    def add_photo(self, photo: Photo) -> None:
        if photo.id not in self.photo_ids:
            self.photo_ids.append(photo.id)

    def _validate_cell_id(self, value: str) -> str:
        v = value.strip().upper()
        if len(v) < 2:
            raise ValidationError("Клетка карты задана некорректно (пример: A1)")

        row = v[0]
        col = v[1:]

        if not ("A" <= row <= "Z"):
            raise ValidationError("Строка должна быть буквой")
        if not col.isdigit():
            raise ValidationError("Столбец должен быть числом")
        if int(col) <= 0:
            raise ValidationError("Столбец должен быть > 0")

        return v
