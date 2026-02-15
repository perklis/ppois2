from unittest import TestCase

from domain.attraction import Attraction
from domain.entity_id import EntityId
from domain.photo import Photo
from exceptions import ValidationError


class TestAttraction(TestCase):
    def _make_valid(self) -> Attraction:
        return Attraction(
            attraction_id=EntityId("d1"),
            name="Тест",
            description="Описание",
            cell_id="A1",
            tags=["тег"],
            photo_ids=[],
        )

    def test_creating_obj(self) -> None:
        a = Attraction(
            attraction_id=EntityId("d1"),
            name="  Парк  ",
            description="  Красивое место  ",
            cell_id="  b2  ",
            tags=None,
            photo_ids=None,
        )
        self.assertEqual(a.id, EntityId("d1"))
        self.assertEqual(a.name, "Парк")
        self.assertEqual(a.description, "Красивое место")
        self.assertEqual(a.cell_id, "B2")
        self.assertEqual(a.tags, [])
        self.assertEqual(a.photo_ids, [])

    def test_empty_name(self) -> None:
        with self.assertRaises(ValidationError) as cm:
            Attraction(
                attraction_id=EntityId("d1"),
                name="   ",
                description="Описание",
                cell_id="A1",
            )
        self.assertEqual(str(cm.exception), "Название не может быть пустым")

    def test_empty_description(self) -> None:
        with self.assertRaises(ValidationError) as cm:
            Attraction(
                attraction_id=EntityId("d1"),
                name="Название",
                description="   ",
                cell_id="A1",
            )
        self.assertEqual(str(cm.exception), "Описание не может быть пустым")

    def test_incorrect_map_cell(self) -> None:
        with self.assertRaises(ValidationError) as cm:
            Attraction(
                attraction_id=EntityId("d1"),
                name="Название",
                description="Описание",
                cell_id="A",
            )
        self.assertEqual(
            str(cm.exception), "Клетка карты задана некорректно (пример: A1)"
        )

    def test_cell_reversed(self) -> None:
        with self.assertRaises(ValidationError) as cm:
            Attraction(
                attraction_id=EntityId("d1"),
                name="Название",
                description="Описание",
                cell_id="1A",
            )
        self.assertEqual(str(cm.exception), "Строка должна быть буквой")

    def test_cell_without_number(self) -> None:
        with self.assertRaises(ValidationError) as cm:
            Attraction(
                attraction_id=EntityId("d1"),
                name="Название",
                description="Описание",
                cell_id="AA",
            )
        self.assertEqual(str(cm.exception), "Столбец должен быть числом")

    def test_incorrect_zero_cell_id(self) -> None:
        with self.assertRaises(ValidationError) as cm:
            Attraction(
                attraction_id=EntityId("d1"),
                name="Название",
                description="Описание",
                cell_id="A0",
            )
        self.assertEqual(str(cm.exception), "Столбец должен быть > 0")

    def test_negative_number_in_cell_id(self) -> None:
        with self.assertRaises(ValidationError) as cm:
            Attraction(
                attraction_id=EntityId("d1"),
                name="Название",
                description="Описание",
                cell_id="A-1",
            )
        self.assertEqual(str(cm.exception), "Столбец должен быть числом")

    def test_add_photo_adds_id_once(self) -> None:
        a = self._make_valid()
        p = Photo(photo_id=EntityId("p1"), title="Фото", file_path="photos/x.jpg")

        self.assertEqual(a.photo_ids, [])
        a.add_photo(p)
        self.assertEqual(a.photo_ids, [EntityId("p1")])

        a.add_photo(p)
        self.assertEqual(a.photo_ids, [EntityId("p1")])
