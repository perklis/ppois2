from pathlib import Path

from config_loader import load_json, save_json


class HighScoreTable:
    def __init__(self, path, mode, limit=10):
        self.path = Path(path)
        self.mode = mode
        self.limit = limit
        self.entries = []
        self.json_data = {}
        self.load()

    def load(self):
        data = load_json(self.path, default={"time": [], "score": []})
        self.json_data = data
        self.entries = data.get(self.mode, [])
        self.entries.sort(key=lambda x: x.get("score", 0), reverse=True)
        self.entries = self.entries[: self.limit]

    def save(self):
        self.json_data[self.mode] = self.entries
        save_json(self.path, self.json_data)

    def best_score(self):
        if not self.entries:
            return 0
        return self.entries[0].get("score", 0)

    def is_new_record(self, score):
        return score > self.best_score()

    def add(self, name, score, timestamp):
        self.entries.append({"name": name, "score": int(score), "timestamp": timestamp})
        self.entries.sort(key=lambda x: x.get("score", 0), reverse=True)
        self.entries = self.entries[: self.limit]
        self.save()

    def get_entries(self):
        return list(self.entries)
