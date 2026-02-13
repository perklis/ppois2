from enum import Enum


class RouteStatus(Enum):
    DRAFT = "черновик"
    PUBLISHED = "опубликован"
    ARCHIVED = "архив"
