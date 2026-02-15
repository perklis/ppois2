from time import strftime

from domain.attraction import Attraction
from domain.entity_id import EntityId
from domain.map_view import MapView
from domain.photo import Photo
from domain.review import Review
from domain.route import Route
from domain.route_status import RouteStatus
from exceptions import DuplicateError, NotFoundError, ValidationError
from services.id_generator import IdGenerator


class Guide:
    def __init__(self, map_view: MapView, ids: IdGenerator) -> None:
        self._map_view = map_view
        self._ids = ids

        self._attractions: dict[str, Attraction] = {}
        self._routes: dict[str, Route] = {}
        self._photos: dict[str, Photo] = {}
        self._reviews: dict[str, Review] = {}

    def map_text(self) -> str:
        occupied = {a.cell_id: a.id.value for a in self._attractions.values()}
        return self._map_view.render(occupied)

    def select_attraction_on_map(self, cell_id: str) -> EntityId:
        normalized = self._map_view.normalize_cell_id(cell_id)
        for a in self._attractions.values():
            if a.cell_id == normalized:
                return a.id
        raise NotFoundError("Тут нет достопримечательности")

    def list_attractions(self) -> list[Attraction]:
        return list(self._attractions.values())

    def get_attraction(self, attraction_id: EntityId) -> Attraction:
        attraction = self._attractions.get(attraction_id.value)
        if attraction is None:
            raise NotFoundError("Достопримечательность не найдена")
        return attraction

    def attraction_info(self, attraction_id: EntityId) -> str:
        attraction = self.get_attraction(attraction_id)
        tags_text = ", ".join(attraction.tags) if attraction.tags else "нет"
        return (
            f"Название: {attraction.name}\n"
            f"Описание: {attraction.description}\n"
            f"Клетка на карте: {attraction.cell_id}\n"
            f"Теги: {tags_text}\n"
        )

    def add_photo(self, photo: Photo) -> None:
        self._photos[photo.id.value] = photo

    def get_photo(self, photo_id: EntityId) -> Photo:
        photo = self._photos.get(photo_id.value)
        if photo is None:
            raise NotFoundError("Фотография не найдена")
        return photo

    def list_photos_for_attraction(self, attraction_id: EntityId) -> list[Photo]:
        attraction = self.get_attraction(attraction_id)
        return [self.get_photo(pid) for pid in attraction.photo_ids]

    def list_routes(self) -> list[Route]:
        return list(self._routes.values())

    def get_route(self, route_id: EntityId) -> Route:
        route = self._routes.get(route_id.value)
        if route is None:
            raise NotFoundError("Маршрут не найден")
        return route

    def create_route(self, name: str) -> EntityId:
        base_id = self._ids.new_id("route")  #routeYYYYMMDD
        route_id_text = self._ensure_unique_id(base_id, self._routes)
        route_id = EntityId(route_id_text)

        route = Route(route_id, name, RouteStatus.DRAFT, [])
        self._routes[route.id.value] = route
        return route.id

    def _ensure_unique_id(self, base_id: str, storage: dict[str, object]) -> str:
        if base_id not in storage:
            return base_id

        counter = 2
        while True:
            candidate = f"{base_id}_{counter}"
            if candidate not in storage:
                return candidate
            counter += 1

    def add_stop_to_route(self, route_id: EntityId, attraction_id: EntityId) -> None:
        self.get_attraction(attraction_id)
        self.get_route(route_id).add_stop(attraction_id)

    def remove_stop_from_route(self, route_id: EntityId, attraction_id: EntityId) -> None:
        self.get_route(route_id).remove_stop(attraction_id)

    def publish_route(self, route_id: EntityId) -> None:
        self.get_route(route_id).publish()

    def unpublish_route(self, route_id: EntityId) -> None:
        self.get_route(route_id).unpublish_to_draft()

    def archive_route(self, route_id: EntityId) -> None:
        self.get_route(route_id).archive()

    def publish_review(self, attraction_id: EntityId, author: str, rating: int, text: str) -> EntityId:
        self.get_attraction(attraction_id)

        base_id = self._ids.new_id("review")  #reviewYYYYMMDD
        review_id_text = self._ensure_unique_id(base_id, self._reviews)
        review_id = EntityId(review_id_text)

        created_at_iso = strftime("%Y-%m-%dT%H:%M:%S")
        review = Review(
            review_id=review_id,
            attraction_id=attraction_id,
            author=author,
            rating=rating,
            text=text,
            created_at_iso=created_at_iso,
        )
        self._reviews[review.id.value] = review
        return review.id

    def list_reviews_for_attraction(self, attraction_id: EntityId) -> list[Review]:
        self.get_attraction(attraction_id)
        return [r for r in self._reviews.values() if r.attraction_id == attraction_id]

    def seed_if_empty(self) -> None:
        if self._attractions:
            return

        a1 = Attraction(
            attraction_id=EntityId("d1"),
            name="Площадь Победы",
            description="Известная городская площадь и мемориальный комплекс.",
            cell_id="B2",
            tags=["история", "прогулка"],
            photo_ids=[EntityId("p1")],
        )
        p1 = Photo(photo_id=EntityId("p1"), title="Вид на площадь", file_path="photos/pobedy.jpg")

        a2 = Attraction(
            attraction_id=EntityId("d2"),
            name="Троицкое предместье",
            description="Исторический район для прогулок и фотографий.",
            cell_id="C3",
            tags=["архитектура", "прогулка"],
            photo_ids=[EntityId("p2")],
        )
        p2 = Photo(photo_id=EntityId("p2"), title="Улицы предместья", file_path="photos/trinity.jpg")

        a3 = Attraction(
            attraction_id=EntityId("d3"),
            name="Привокзальная площадь",
            description="ВИзитная карточка Минска",
            cell_id="D4",
            tags=["архитектура", "здания"],
            photo_ids=[EntityId("p3")],
        )
        p3 = Photo(photo_id=EntityId("p3"), title="Вокзал", file_path="photos/station.jpg")        

        if a1.id.value in self._attractions or a2.id.value in self._attractions or a3.id.value in self._attractions:
            raise DuplicateError("Ошибка заполнения базы знаний: дублирующиеся id достопримечательностей.")

        self._attractions[a1.id.value] = a1
        self._attractions[a2.id.value] = a2
        self._attractions[a3.id.value] = a3
        self._photos[p1.id.value] = p1
        self._photos[p2.id.value] = p2
        self._photos[p3.id.value] = p3

    def export_state(self) -> dict:
        return {
            "dostoprimechatelnosti": [self._attraction_to_dict(a) for a in self._attractions.values()],
            "marshruty": [self._route_to_dict(r) for r in self._routes.values()],
            "fotografii": [self._photo_to_dict(p) for p in self._photos.values()],
            "otzyvy": [self._review_to_dict(r) for r in self._reviews.values()],
        }

    def import_state(self, data: dict) -> None:
        self._attractions.clear()
        self._routes.clear()
        self._photos.clear()
        self._reviews.clear()

        for row in data.get("dostoprimechatelnosti", []):
            attraction = self._attraction_from_dict(row)
            self._attractions[attraction.id.value] = attraction

        for row in data.get("fotografii", []):
            photo = self._photo_from_dict(row)
            self._photos[photo.id.value] = photo

        for row in data.get("marshruty", []):
            route = self._route_from_dict(row)
            self._routes[route.id.value] = route

        for row in data.get("otzyvy", []):
            review = self._review_from_dict(row)
            self._reviews[review.id.value] = review

    def _attraction_to_dict(self, attraction: Attraction) -> dict:
        return {
            "id": attraction.id.value,
            "name": attraction.name,
            "description": attraction.description,
            "cell_id": attraction.cell_id,
            "tags": list(attraction.tags),
            "photo_ids": [pid.value for pid in attraction.photo_ids],
        }

    def _attraction_from_dict(self, d: dict) -> Attraction:
        return Attraction(
            attraction_id=EntityId(str(d["id"])),
            name=str(d["name"]),
            description=str(d["description"]),
            cell_id=str(d["cell_id"]),
            tags=[str(x) for x in d.get("tags", [])],
            photo_ids=[EntityId(str(x)) for x in d.get("photo_ids", [])],
        )

    def _photo_to_dict(self, photo: Photo) -> dict:
        return {"id": photo.id.value, "title": photo.title, "file_path": photo.file_path}

    def _photo_from_dict(self, d: dict) -> Photo:
        return Photo(
            photo_id=EntityId(str(d["id"])),
            title=str(d["title"]),
            file_path=str(d["file_path"]),
        )

    def _route_to_dict(self, route: Route) -> dict:
        return {
            "id": route.id.value,
            "name": route.name,
            "status": route.status.value,
            "attraction_ids": [aid.value for aid in route.attraction_ids],
        }

    def _route_from_dict(self, d: dict) -> Route:
        status_text = str(d.get("status", RouteStatus.DRAFT.value))
        status = self._parse_route_status(status_text)
        return Route(
            route_id=EntityId(str(d["id"])),
            name=str(d["name"]),
            status=status,
            attraction_ids=[EntityId(str(x)) for x in d.get("attraction_ids", [])],
        )

    def _parse_route_status(self, value: str) -> RouteStatus:
        for s in RouteStatus:
            if s.value == value:
                return s
        raise ValidationError("Некорректный статус маршрута в файле хранения.")

    def _review_to_dict(self, review: Review) -> dict:
        return {
            "id": review.id.value,
            "attraction_id": review.attraction_id.value,
            "author": review.author,
            "rating": review.rating,
            "text": review.text,
            "created_at_iso": review.created_at_iso,
        }

    def _review_from_dict(self, d: dict) -> Review:
        return Review(
            review_id=EntityId(str(d["id"])),
            attraction_id=EntityId(str(d["attraction_id"])),
            author=str(d.get("author", "Аноним")),
            rating=int(d["rating"]),
            text=str(d["text"]),
            created_at_iso=str(d["created_at_iso"]),
        )
