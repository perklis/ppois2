from unittest import TestCase
from unittest.mock import Mock, patch

from menu import Menu  


class TestMenu(TestCase):
    def test_exit_0_prints_goodbye(self) -> None:
        guide = Mock()
        menu = Menu(guide)

        with patch("builtins.input", side_effect=["0"]), patch("builtins.print") as p:
            menu.run()

        p.assert_any_call("До свидания!")

    def test_unknown_command_prints_try_again(self) -> None:
        guide = Mock()
        menu = Menu(guide)

        with patch("builtins.input", side_effect=["99", "0"]), patch("builtins.print") as p:
            menu.run()

        p.assert_any_call("Попробуйте снова.")
        p.assert_any_call("До свидания!")

    def test_choice_1_calls_guide_map_text_and_prints_map(self) -> None:
        guide = Mock()
        guide.map_text.return_value = "MAP"
        menu = Menu(guide)

        with patch("builtins.input", side_effect=["1", "0"]), patch("builtins.print") as p:
            menu.run()

        guide.map_text.assert_called()
        p.assert_any_call("MAP")

    def test_choice_2_select_on_map_uses_entered_cell(self) -> None:
        guide = Mock()
        selected_id = Mock()
        selected_id.value = "d1"
        guide.select_attraction_on_map.return_value = selected_id

        menu = Menu(guide)

        with patch("builtins.input", side_effect=["2", "A1", "0"]), patch("builtins.print") as p:
            menu.run()

        guide.select_attraction_on_map.assert_called_with("A1")
        p.assert_any_call("Вы выбрали достопримечательность с id: d1")

    def test_choice_4_no_photos_prints_message(self) -> None:
        guide = Mock()
        guide.list_photos_for_attraction.return_value = []

        menu = Menu(guide)

        with patch("builtins.input", side_effect=["4", "d1", "0"]), patch("builtins.print") as p:
            menu.run()

        p.assert_any_call("Фото нет")

    def test_value_error_prints_message(self) -> None:
        guide = Mock()
        menu = Menu(guide)
        with patch(
            "builtins.input",
            side_effect=["5", "d1", "Автор", "abc", "Текст", "0"],
        ), patch("builtins.print") as p:
            menu.run()

        p.assert_any_call("Некорректный формат числа")

    def test_app_error_prints_message(self) -> None:
        from exceptions import AppError

        guide = Mock()
        guide.map_text.side_effect = AppError("boom")
        menu = Menu(guide)

        with patch("builtins.input", side_effect=["1", "0"]), patch("builtins.print") as p:
            menu.run()

        p.assert_any_call("Ошибка: boom")
