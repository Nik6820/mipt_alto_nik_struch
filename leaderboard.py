import json
import os

LEADERBOARD_FILE = "leaderboard.json"
MAX_ENTRIES = 10


class Leaderboard:
    def __init__(self, path=LEADERBOARD_FILE):
        self.path = path
        self.entries = []
        self.load()

    def load(self):
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                self.entries = [
                    e for e in data
                    if isinstance(e, dict) and "score" in e and "name" in e
                ]
        except (json.JSONDecodeError, OSError):
            self.entries = []
        self._sort_and_trim()

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.entries, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def _sort_and_trim(self):
        self.entries.sort(key=lambda e: e["score"], reverse=True)
        self.entries = self.entries[:MAX_ENTRIES]

    def qualifies(self, score):
        if score <= 0:
            return False
        if len(self.entries) < MAX_ENTRIES:
            return True
        return score > self.entries[-1]["score"]

    def add(self, name, score, distance, coins):
        entry = {
            "name": (name.strip() or "Player")[:14],
            "score": int(score),
            "distance": int(distance),
            "coins": int(coins),
        }
        self.entries.append(entry)
        self._sort_and_trim()
        self.save()
        return entry

    def rank_of(self, entry):
        for i, e in enumerate(self.entries):
            if e is entry:
                return i + 1
        return -1
