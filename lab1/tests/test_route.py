from unittest import TestCase
from domain.entity_id import EntityId
from domain.route import Route
from domain.route_status import RouteStatus
from exceptions import OperationError, ValidationError


class TestRoute(TestCase):
    def test_init_raises_when_name_empty(self) -> None:
        with self.assertRaises(ValidationError) as cm:
            Route(route_id=EntityId("r1"), name="   ")
        self.assertEqual(str(cm.exception), "Название маршрута не может быть пустым")

    def test_add_stop_in_draft_adds_once(self) -> None:
        r = Route(route_id=EntityId("r1"), name="Маршрут", status=RouteStatus.DRAFT, attraction_ids=[])
        a1 = EntityId("d1")

        r.add_stop(a1)
        self.assertEqual(r.attraction_ids, [a1])

        r.add_stop(a1)
        self.assertEqual(r.attraction_ids, [a1])

    def test_add_stop_not_draft(self) -> None:
        r = Route(route_id=EntityId("r1"), name="Маршрут", status=RouteStatus.PUBLISHED, attraction_ids=[])
        with self.assertRaises(OperationError) as cm:
            r.add_stop(EntityId("d1"))
        self.assertEqual(str(cm.exception), "Изменять маршрут можно если он черновик")

    def test_remove_stop_in_draft_removes_if_present(self) -> None:
        a1 = EntityId("d1")
        a2 = EntityId("d2")
        r = Route(route_id=EntityId("r1"), name="Маршрут", status=RouteStatus.DRAFT, attraction_ids=[a1, a2])

        r.remove_stop(a1)
        self.assertEqual(r.attraction_ids, [a2])

    def test_remove_stop_in_draft_does_nothing_if_absent(self) -> None:
        a1 = EntityId("d1")
        r = Route(route_id=EntityId("r1"), name="Маршрут", status=RouteStatus.DRAFT, attraction_ids=[a1])

        r.remove_stop(EntityId("d2"))
        self.assertEqual(r.attraction_ids, [a1])

    def test_remove_stop_not_draft(self) -> None:
        r = Route(route_id=EntityId("r1"), name="Маршрут", status=RouteStatus.PUBLISHED, attraction_ids=[])
        with self.assertRaises(OperationError) as cm:
            r.remove_stop(EntityId("d1"))
        self.assertEqual(str(cm.exception), "Изменять маршрут можно если он черновик")

    def test_publish_raises_when_archived(self) -> None:
        r = Route(route_id=EntityId("r1"), name="Маршрут", status=RouteStatus.ARCHIVED, attraction_ids=[EntityId("d1")])
        with self.assertRaises(OperationError) as cm:
            r.publish()
        self.assertEqual(str(cm.exception), "Архивированный маршрут нельзя опубликовать")

    def test_publish_returns_when_already_published(self) -> None:
        r = Route(route_id=EntityId("r1"), name="Маршрут", status=RouteStatus.PUBLISHED, attraction_ids=[EntityId("d1")])
        r.publish()
        self.assertEqual(r.status, RouteStatus.PUBLISHED)

    def test_publish_raises_when_empty(self) -> None:
        r = Route(route_id=EntityId("r1"), name="Маршрут", status=RouteStatus.DRAFT, attraction_ids=[])
        with self.assertRaises(OperationError) as cm:
            r.publish()
        self.assertEqual(str(cm.exception), "Нельзя опубликовать пустой маршрут")

    def test_publish_success_changes_status(self) -> None:
        r = Route(route_id=EntityId("r1"), name="Маршрут", status=RouteStatus.DRAFT, attraction_ids=[EntityId("d1")])
        r.publish()
        self.assertEqual(r.status, RouteStatus.PUBLISHED)

    def test_archive_from_draft_changes_status(self) -> None:
        r = Route(route_id=EntityId("r1"), name="Маршрут", status=RouteStatus.DRAFT, attraction_ids=[])
        r.archive()
        self.assertEqual(r.status, RouteStatus.ARCHIVED)

    def test_archive_when_already_archived_returns(self) -> None:
        r = Route(route_id=EntityId("r1"), name="Маршрут", status=RouteStatus.ARCHIVED, attraction_ids=[])
        r.archive()
        self.assertEqual(r.status, RouteStatus.ARCHIVED)

    def test_unpublish_to_draft_raises_when_not_published(self) -> None:
        r = Route(route_id=EntityId("r1"), name="Маршрут", status=RouteStatus.DRAFT, attraction_ids=[EntityId("d1")])
        with self.assertRaises(OperationError) as cm:
            r.unpublish_to_draft()
        self.assertEqual(str(cm.exception), "В черновик можно вернуть только опубликованный маршрут")

    def test_unpublish_to_draft_success(self) -> None:
        r = Route(route_id=EntityId("r1"), name="Маршрут", status=RouteStatus.PUBLISHED, attraction_ids=[EntityId("d1")])
        r.unpublish_to_draft()
        self.assertEqual(r.status, RouteStatus.DRAFT)
