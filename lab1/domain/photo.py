from exceptions import ValidationError
from domain.entity_id import EntityId


class Photo:
    def __init__(self, photo_id: EntityId, title: str, file_path: str) -> None:
        self.id = photo_id

        self.title = title.strip()
        if not self.title:
            raise ValidationError("Название фотографии не может быть пустым")

        self.file_path = file_path.strip()
        if not self.file_path:
            raise ValidationError("Путь к файлу фотографии не может быть пустым")
