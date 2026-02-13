from exceptions import ValidationError


class EntityId:
    def __init__(self, value: str) -> None:
        clean_value = value.strip()
        if not clean_value:
            raise ValidationError("Идентификатор не может быть пустым")
        self._value = clean_value

    @property
    def value(self) -> str:
        return self._value

    def __str__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return f"EntityId({self._value!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EntityId):
            return False
        return self._value == other._value

    def __hash__(self) -> int:
        return hash(self._value)
