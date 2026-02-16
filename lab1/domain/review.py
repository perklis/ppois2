from exceptions import ValidationError
from domain.entity_id import EntityId


class Review:
    def __init__(
        self,
        review_id: EntityId,
        attraction_id: EntityId,
        author: str,
        rating: int,
        text: str,
        created_at_iso: str,
    ) -> None:
        self.id = review_id
        self.attraction_id = attraction_id

        self.author = author.strip() or "Аноним"

        try:
            self.rating = int(rating)
        except (TypeError, ValueError):
            raise ValidationError("Оценка должна быть целым числом от 1 до 5")

        if self.rating < 1 or self.rating > 5:
            raise ValidationError("Оценка должна быть от 1 до 5")

        self.text = text.strip()
        if not self.text:
            raise ValidationError("Текст отзыва не может быть пустым")

        self.created_at_iso = created_at_iso.strip()
        if not self.created_at_iso:
            raise ValidationError("Дата создания отзыва не задана")
