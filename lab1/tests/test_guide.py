from unittest import TestCase

from domain.attraction import Attraction
from domain.entity_id import EntityId
from domain.map_view import MapView
from domain.photo import Photo
from exceptions import NotFoundError
from domain.guide import Guide
from services.id_generator import IdGenerator


class TestGuide(TestCase):
    def setUp(self) -> None:
        self.map_view = MapView(rows=["A", "B"], cols=2)
        self.ids = IdGenerator()
        self.g = Guide(map_view=self.map_view, ids=self.ids)

        a1 = Attraction(
            attraction_id=EntityId("d1"),
            name="Место 1",
            description="Описание 1",
            cell_id="A1",
            tags=["тег"],
            photo_ids=[EntityId("p1")],
        )
        p1 = Photo(photo_id=EntityId("p1"), title="Фото 1", file_path="photos/1.jpg")

        self.g._attractions[a1.id.value] = a1
        self.g._photos[p1.id.value] = p1

    def test_map_text_contains_legend_and_x(self) -> None:
        text = self.g.map_text()
        self.assertIn("достопримечательность", text)
        self.assertIn("X", text)

    def test_select_attraction_on_map_ok(self) -> None:
        attraction_id = self.g.select_attraction_on_map(" a1 ")
        self.assertEqual(attraction_id, EntityId("d1"))

    def test_select_attraction_on_map_raises_when_empty_cell(self) -> None:
        with self.assertRaises(NotFoundError):
            self.g.select_attraction_on_map("B2")

    def test_get_attraction_and_info_ok(self) -> None:
        a = self.g.get_attraction(EntityId("d1"))
        self.assertEqual(a.name, "Место 1")

        info = self.g.attraction_info(EntityId("d1"))
        self.assertIn("Название:", info)
        self.assertIn("Клетка на карте:", info)

    def test_get_photo_raises(self) -> None:
        with self.assertRaises(NotFoundError):
            self.g.get_photo(EntityId("p999"))

    def test_list_photos_for_attraction_ok(self) -> None:
        photos = self.g.list_photos_for_attraction(EntityId("d1"))
        self.assertEqual(len(photos), 1)
        self.assertEqual(photos[0].id, EntityId("p1"))

    def test_create_route_unique_suffix_when_taken(self) -> None:
        rid1 = self.g.create_route("Маршрут 1")
        rid2 = self.g.create_route("Маршрут 2")

        self.assertNotEqual(rid1.value, rid2.value)
        self.assertTrue(rid2.value.endswith("_2"))

    def test_publish_review_creates_review_and_can_list(self) -> None:
        review_id = self.g.publish_review(
            attraction_id=EntityId("d1"),
            author="Я",
            rating=5,
            text="Классно",
        )
        self.assertTrue(review_id.value.startswith("review"))

        reviews = self.g.list_reviews_for_attraction(EntityId("d1"))
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0].text, "Классно")

    def test_export_import_state_roundtrip(self) -> None:
        state = self.g.export_state()

        g2 = Guide(map_view=self.map_view, ids=self.ids)
        g2.import_state(state)

        self.assertEqual(len(g2.list_attractions()), 1)
        self.assertEqual(g2.get_attraction(EntityId("d1")).cell_id, "A1")
        self.assertEqual(len(g2.list_photos_for_attraction(EntityId("d1"))), 1)

    def test_seed_if_empty_populates_when_empty(self) -> None:
        g = Guide(map_view=MapView(rows=["A", "B", "C", "D"], cols=5), ids=IdGenerator())

        self.assertEqual(len(g._attractions), 0)
        self.assertEqual(len(g._photos), 0)

        g.seed_if_empty()

        self.assertEqual(len(g._attractions), 3)
        self.assertEqual(len(g._photos), 3)

        self.assertIn("d1", g._attractions)
        self.assertIn("d2", g._attractions)
        self.assertIn("d3", g._attractions)

        self.assertIn("p1", g._photos)
        self.assertIn("p2", g._photos)
        self.assertIn("p3", g._photos)
    
        self.assertEqual(g._attractions["d1"].photo_ids[0], EntityId("p1"))

