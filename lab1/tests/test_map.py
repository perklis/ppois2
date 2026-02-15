from unittest import TestCase

from domain.map_view import MapView
from exceptions import ValidationError


class TestMapView(TestCase):
    def test_empty_rows(self) -> None:
        with self.assertRaises(ValidationError) as cm:
            MapView(rows=[], cols=5)
        self.assertEqual(str(cm.exception), "Карта должна иметь хотя бы одну строку")

    def test_negative_cols(self) -> None:
        with self.assertRaises(ValidationError) as cm:
            MapView(rows=["A"], cols=0)
        self.assertEqual(str(cm.exception), "Карта должна иметь хотя бы один столбец")

    def test_normalize_cell_id_rows_cols(self) -> None:
        mv = MapView(rows=[" a ", "b"], cols=3)
        self.assertEqual(mv.rows, ["A", "B"])
        self.assertEqual(mv.cols, 3)

    def test_normalize_cell_id_raises_when_too_short(self) -> None:
        mv = MapView(rows=["A"], cols=1)
        with self.assertRaises(ValidationError) as cm:
            mv.normalize_cell_id("A")
        self.assertEqual(str(cm.exception), "Введите клетку карты(A1)")

    def test_normalize_cell_id(self) -> None:
        mv = MapView(rows=["A"], cols=1)
        self.assertEqual(mv.normalize_cell_id("  b2 "), "B2")

    def test_render_contains_header_rows_legend_and_marks(self) -> None:
        mv = MapView(rows=["A", "B"], cols=3)
        occupied = {"A2": "d1"}  # занята только A2

        text = mv.render(occupied)
        lines = text.splitlines()

        self.assertEqual(len(lines), 1 + 2 + 1 + 1)

        self.assertIn("1", lines[0])
        self.assertIn("2", lines[0])
        self.assertIn("3", lines[0])

        self.assertTrue(lines[1].startswith("  A"))
        self.assertIn("X", lines[1])
        self.assertIn(".", lines[1])

        self.assertTrue(lines[2].startswith("  B"))
        self.assertIn(".", lines[2])
        self.assertNotIn("X", lines[2])
        self.assertEqual(lines[3], "")
        self.assertEqual(lines[4], "X — достопримечательность,. — пусто")

    def test_render_shows_x_and_dot_in_same_row(self) -> None:
        mv = MapView(rows=["A"], cols=2)
        text = mv.render({"A1": "d1"})
        map_row = text.splitlines()[1]
        self.assertIn("X", map_row)
        self.assertIn(".", map_row)
