from pathlib import Path

from config_loader import load_json, save_json


class HighScoreTable:
    """High score storage per mode backed by JSON."""

    def __init__(self, path, mode, limit=10):
        self.path = Path(path)
        self.mode = mode
        self.limit = limit
        self.entries = []
        self.data = {}
        self.load()

    def load(self):
        data = load_json(self.path, default={"time": [], "score": []})
        self.data = data
        self.entries = data.get(self.mode, [])
        self.entries.sort(key=lambda x: x.get("score", 0), reverse=True)
        self.entries = self.entries[: self.limit]

    def save(self):
        self.data[self.mode] = self.entries
        save_json(self.path, self.data)

    def top_score(self):
        if not self.entries:
            return 0
        return self.entries[0].get("score", 0)

    def is_new_record(self, score):
        return score > self.top_score()

    def add(self, name, score, timestamp):
        self.entries.append({"name": name, "score": int(score), "timestamp": timestamp})
        self.entries.sort(key=lambda x: x.get("score", 0), reverse=True)
        self.entries = self.entries[: self.limit]
        self.save()

    def get_entries(self):
        return list(self.entries)
