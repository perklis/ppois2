from __future__ import annotations
from pathlib import Path
from fastapi import FastAPI, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .state import LAB1_DIR, guide, load_state, save_state
from lab1.domain.entity_id import EntityId
from lab1.exceptions import AppError


app = FastAPI(title="AroundMinsk", version="1.0")
app.mount("/photos", StaticFiles(directory=str(LAB1_DIR / "photos")), name="photos")
app.mount("/static", StaticFiles(directory=str(Path(__file__).resolve().parent / "static")), name="static")
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))


def _render(request: Request, **context):
    attractions = guide.list_attractions()
    routes = guide.list_routes()
    attraction_name_by_id = {attraction.id.value: attraction.name for attraction in attractions}
    route_stops = {}
    for route in routes:
        route_stops[route.id.value] = [
            {
                "id": attraction_id.value,
                "name": attraction_name_by_id.get(attraction_id.value, "Неизвестная точка"),
            }
            for attraction_id in route.attraction_ids
        ]

    base = {
        "request": request,
        "map_text": guide.map_text(),
        "attractions": attractions,
        "routes": routes,
        "route_stops": route_stops,
    }
    base.update(context)
    return templates.TemplateResponse("index.html", base)


@app.get("/")
def index(request: Request):
    load_state()
    return _render(request)


@app.post("/select")
def select_on_map(request: Request, cell_id: str = Form(...)):
    try:
        load_state()
        attraction_id = guide.select_attraction_on_map(cell_id)
        return _render(request, selected_attraction=attraction_id.value)
    except AppError as exc:
        return _render(request, error=str(exc))


@app.post("/attraction")
def attraction_info(request: Request, attraction_id: str = Form(...)):
    try:
        load_state()
        info = guide.attraction_info(EntityId(attraction_id))
        return _render(request, attraction_info=info)
    except AppError as exc:
        return _render(request, error=str(exc))


@app.post("/photos-list")
def photos(request: Request, attraction_id: str = Form(...)):
    try:
        load_state()
        items = guide.list_photos_for_attraction(EntityId(attraction_id))
        if not items:
            return _render(request, message="Фото не найдено")
        links = []
        for p in items:
            filename = Path(p.file_path).name
            links.append({"title": p.title, "href": f"/photos/{filename}"})
        return _render(request, photos=links)
    except AppError as exc:
        return _render(request, error=str(exc))


@app.get("/photos-list")
def photos_get(request: Request):
    return _render(request, message="Чтобы увидеть фото, выберите достопримечательность и отправьте форму.")


@app.post("/review")
def publish_review(
    request: Request,
    attraction_id: str = Form(...),
    author: str = Form(...),
    rating: int = Form(...),
    text: str = Form(...),
):
    try:
        load_state()
        review_id = guide.publish_review(EntityId(attraction_id), author, int(rating), text)
        save_state()
        return _render(request, message=f"Отзыв опубликован: {review_id.value}")
    except AppError as exc:
        return _render(request, error=str(exc))


@app.post("/reviews")
def reviews(request: Request, attraction_id: str = Form(...)):
    try:
        load_state()
        items = guide.list_reviews_for_attraction(EntityId(attraction_id))
        if not items:
            return _render(request, message="Отзывов пока нет")
        reviews_list = [
            {
                "created_at": r.created_at_iso,
                "author": r.author,
                "rating": r.rating,
                "text": r.text,
            }
            for r in items
        ]
        return _render(request, reviews=reviews_list)
    except AppError as exc:
        return _render(request, error=str(exc))


@app.post("/route/create")
def route_create(request: Request, name: str = Form(...)):
    try:
        load_state()
        route_id = guide.create_route(name)
        save_state()
        return _render(request, message=f"Маршрут создан: {route_id.value}")
    except AppError as exc:
        return _render(request, error=str(exc))


@app.post("/route/add")
def route_add(request: Request, route_id: str = Form(...), attraction_id: str = Form(...)):
    try:
        load_state()
        guide.add_stop_to_route(EntityId(route_id), EntityId(attraction_id))
        save_state()
        return _render(request, message="Точка добавлена в маршрут")
    except AppError as exc:
        return _render(request, error=str(exc))


@app.post("/route/remove")
def route_remove(request: Request, route_id: str = Form(...), attraction_id: str = Form(...)):
    try:
        load_state()
        guide.remove_stop_from_route(EntityId(route_id), EntityId(attraction_id))
        save_state()
        return _render(request, message="Точка удалена из маршрута")
    except AppError as exc:
        return _render(request, error=str(exc))


@app.post("/route/publish")
def route_publish(request: Request, route_id: str = Form(...)):
    try:
        load_state()
        guide.publish_route(EntityId(route_id))
        save_state()
        return _render(request, message="Маршрут опубликован")
    except AppError as exc:
        return _render(request, error=str(exc))


@app.post("/route/unpublish")
def route_unpublish(request: Request, route_id: str = Form(...)):
    try:
        load_state()
        guide.unpublish_route(EntityId(route_id))
        save_state()
        return _render(request, message="Маршрут возвращён в черновик")
    except AppError as exc:
        return _render(request, error=str(exc))


@app.post("/route/archive")
def route_archive(request: Request, route_id: str = Form(...)):
    try:
        load_state()
        guide.archive_route(EntityId(route_id))
        save_state()
        return _render(request, message="Маршрут архивирован")
    except AppError as exc:
        return _render(request, error=str(exc))


@app.post("/route/stops")
def route_stops(request: Request, route_id: str = Form(...)):
    try:
        load_state()
        route = guide.get_route(EntityId(route_id))
        attractions = guide.list_attractions()
        attraction_name_by_id = {attraction.id.value: attraction.name for attraction in attractions}
        selected_route_stops = [
            {
                "id": attraction_id.value,
                "name": attraction_name_by_id.get(attraction_id.value, "Неизвестная точка"),
            }
            for attraction_id in route.attraction_ids
        ]
        return _render(
            request,
            selected_route_id=route.id.value,
            selected_route_name=route.name,
            selected_route_stops=selected_route_stops,
        )
    except AppError as exc:
        return _render(request, error=str(exc))
