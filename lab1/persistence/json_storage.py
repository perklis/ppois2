import json

from exceptions import StorageLoadError, StorageSaveError


class JsonStorage:
    def __init__(self, file_path: str) -> None:
        self._file_path = file_path

    def load(self) -> dict:
        try:
            try:
                with open(self._file_path, "r", encoding="utf-8") as f:
                    text = f.read()
            except FileNotFoundError:
                return {"dostoprimechatelnosti": [], "marshruty": [], "fotografii": [], "otzyvy": []}

            if not text.strip():
                return {"dostoprimechatelnosti": [], "marshruty": [], "fotografii": [], "otzyvy": []}

            data = json.loads(text)
            if not isinstance(data, dict):
                raise StorageLoadError("Файл хранения должен содержать JSON-объект.")
            return data
        except (OSError, json.JSONDecodeError) as exc:
            raise StorageLoadError(f"Ошибка чтения JSON: {exc}") from exc

    def save(self, data: dict) -> None:
        try:
            with open(self._file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError as exc:
            raise StorageSaveError(f"Ошибка записи JSON: {exc}") from exc
