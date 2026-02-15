from domain.entity_id import EntityId
from exceptions import AppError
from domain.guide import Guide


class Menu:
    def __init__(self, guide: Guide) -> None:
        self._guide = guide

    def run(self) -> None:
        actions = {
            "1": self._show_map,
            "2": self._select_on_map,
            "3": self._show_attraction_info,
            "4": self._show_photos,
            "5": self._publish_review,
            "6": self._create_route,
            "7": self._add_stop,
            "8": self._remove_stop,
            "9": self._publish_route,
            "10": self._unpublish_route,
            "11": self._archive_route,
            "12": self._list_attractions,
            "13": self._list_routes,
            "14": self._list_reviews,
        }

        while True:
            self._print_menu()
            choice = input("Ваш выбор: ").strip()

            if choice == "0":
                print("До свидания!")
                return

            try:
                action = actions.get(choice)
                if action is None:
                    print("Попробуйте снова.")
                    continue
                action()
            except AppError as exc:
                print(f"Ошибка: {exc}")
            except ValueError:
                print("Некорректный формат числа")

    def _print_menu(self) -> None:
        print("\nМеню")
        print("1. Показать карту")
        print("2. Выбрать достопримечательность на карте (по клетке)")
        print("3. Узнать о достопримечательности")
        print("4. Просмотреть фото достопримечательности")
        print("5. Опубликовать отзыв")
        print("6. Создать черновик маршрута")
        print("7. Добавить достопримечательность в маршрут-черновик")
        print("8. Удалить достопримечательность из маршрута-черновик")
        print("9. Опубликовать маршрут")
        print("10. Снять маршрут с публикации")
        print("11. Архивировать маршрут")
        print("12. Список достопримечательностей")
        print("13. Список маршрутов")
        print("14. Отзывы по достопримечательности")
        print("0. Выход")

    def _show_map(self) -> None:
        print(self._guide.map_text())

    def _select_on_map(self) -> None:
        cell_id = input("Введите клетку (напр A1): ").strip()
        attraction_id = self._guide.select_attraction_on_map(cell_id)
        print(f"Вы выбрали достопримечательность с id: {attraction_id.value}")

    def _show_attraction_info(self) -> None:
        attraction_id = EntityId(input("Введите id достопримечательности: ").strip())
        print(self._guide.attraction_info(attraction_id))

    def _show_photos(self) -> None:
        attraction_id = EntityId(input("Введите id достопримечательности: ").strip())
        photos = self._guide.list_photos_for_attraction(attraction_id)
        if not photos:
            print("Фото нет")
            return
        print("Фотографии:")
        for p in photos:
            print(f"- {p.title}. файл: {p.file_path} <- нажмите ctrl+сюда для просмотра фото")

    def _publish_review(self) -> None:
        attraction_id = EntityId(input("Введите id достопримечательности: ").strip())
        author = input("Автор: ").strip()
        rating = int(input("Оценка: ").strip())
        text = input("Текст отзыва: ").strip()
        review_id = self._guide.publish_review(attraction_id, author, rating, text)
        print(f"Отзыв опубликован. id: {review_id.value}")

    def _create_route(self) -> None:
        name = input("Введите название маршрута: ").strip()
        route_id = self._guide.create_route(name)
        print(f"Маршрут создан (черновик). id: {route_id.value}")

    def _add_stop(self) -> None:
        route_id = EntityId(input("Введите id маршрута: ").strip())
        attraction_id = EntityId(input("Введите id достопримечательности: ").strip())
        self._guide.add_stop_to_route(route_id, attraction_id)
        print("Достопримечательность добавлена")

    def _remove_stop(self) -> None:
        route_id = EntityId(input("Введите id маршрута: ").strip())
        attraction_id = EntityId(input("Введите id достопримечательности: ").strip())
        self._guide.remove_stop_from_route(route_id, attraction_id)
        print("Достопримечательность удалена")

    def _publish_route(self) -> None:
        route_id = EntityId(input("Введите id маршрута: ").strip())
        self._guide.publish_route(route_id)
        print("Маршрут опубликован")

    def _unpublish_route(self) -> None:
        route_id = EntityId(input("Введите id маршрута: ").strip())
        self._guide.unpublish_route(route_id)
        print("Маршрут возвращён в черновик")

    def _archive_route(self) -> None:
        route_id = EntityId(input("Введите id маршрута: ").strip())
        self._guide.archive_route(route_id)
        print("Маршрут архивирован")

    def _list_attractions(self) -> None:
        items = self._guide.list_attractions()
        if not items:
            print("Список достопримечательностей пуст")
            return
        print("Достопримечательности:")
        for a in items:
            print(f"- {a.id.value}: {a.name}, клетка: {a.cell_id}")

    def _list_routes(self) -> None:
        items = self._guide.list_routes()
        if not items:
            print("Список маршрутов пуст")
            return
        print("Маршруты:")
        for r in items:
            print(
                f"- {r.id.value}: {r.name}, статус: {r.status.value}, точек: {len(r.attraction_ids)}"
            )

    def _list_reviews(self) -> None:
        attraction_id = EntityId(input("Введите id достопримечательности: ").strip())
        reviews = self._guide.list_reviews_for_attraction(attraction_id)
        if not reviews:
            print("Отзывов пока нет")
            return
        print("Отзывы:")
        for r in reviews:
            print(f"- {r.created_at_iso}, {r.author}, {r.rating}/5")
            print(f"  {r.text}")
