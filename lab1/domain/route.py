from exceptions import OperationError, ValidationError
from domain.entity_id import EntityId
from domain.route_status import RouteStatus


class Route:
    def __init__(
        self,
        route_id: EntityId,
        name: str,
        status: RouteStatus = RouteStatus.DRAFT,
        attraction_ids: list[EntityId] | None = None,
    ) -> None:
        self.id = route_id

        self.name = name.strip()
        if not self.name:
            raise ValidationError("Название маршрута не может быть пустым")

        self.status = status
        self.attraction_ids = list(attraction_ids) if attraction_ids is not None else []

    def add_stop(self, attraction_id: EntityId) -> None:
        if self.status != RouteStatus.DRAFT:
            raise OperationError("Изменять маршрут можно если он черновик")
        if attraction_id not in self.attraction_ids:
            self.attraction_ids.append(attraction_id)

    def remove_stop(self, attraction_id: EntityId) -> None:
        if self.status != RouteStatus.DRAFT:
            raise OperationError("Изменять маршрут можно если он черновик")
        if attraction_id in self.attraction_ids:
            self.attraction_ids.remove(attraction_id)

    def publish(self) -> None:
        if self.status == RouteStatus.ARCHIVED:
            raise OperationError("Архивированный маршрут нельзя опубликовать")
        if self.status == RouteStatus.PUBLISHED:
            return
        if len(self.attraction_ids) == 0:
            raise OperationError("Нельзя опубликовать пустой маршрут")
        self.status = RouteStatus.PUBLISHED

    def archive(self) -> None:
        if self.status == RouteStatus.ARCHIVED:
            return
        self.status = RouteStatus.ARCHIVED

    def unpublish_to_draft(self) -> None:
        if self.status != RouteStatus.PUBLISHED:
            raise OperationError("В черновик можно вернуть только опубликованный маршрут")
        self.status = RouteStatus.DRAFT
