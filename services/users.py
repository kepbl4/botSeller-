from __future__ import annotations

import time
from pathlib import Path
from typing import Dict

from services.files import read_json, write_json


class UserService:
    def __init__(self, path: Path) -> None:
        self.path = path

    def _load(self) -> Dict[str, dict]:
        return read_json(self.path, default={})

    def _save(self, data: Dict[str, dict]) -> None:
        write_json(self.path, data)

    def register_start(self, user_id: int, username: str | None) -> None:
        data = self._load()
        user_key = str(user_id)
        entry = data.get(user_key, {})
        entry.setdefault("first_seen", int(time.time()))
        entry["username"] = username
        entry["started"] = True
        data[user_key] = entry
        self._save(data)

    def mark_buy_click(self, user_id: int) -> None:
        data = self._load()
        user_key = str(user_id)
        entry = data.get(user_key, {})
        entry["buy_clicks"] = entry.get("buy_clicks", 0) + 1
        data[user_key] = entry
        self._save(data)

    def mark_purchase(self, user_id: int) -> None:
        data = self._load()
        user_key = str(user_id)
        entry = data.get(user_key, {})
        entry["purchased"] = entry.get("purchased", 0) + 1
        data[user_key] = entry
        self._save(data)

    def mark_blocked(self, user_id: int) -> None:
        data = self._load()
        user_key = str(user_id)
        entry = data.get(user_key, {})
        entry["blocked"] = entry.get("blocked", 0) + 1
        data[user_key] = entry
        self._save(data)

    def stats(self) -> Dict[str, int]:
        data = self._load()
        total_users = len(data)
        started = sum(1 for item in data.values() if item.get("started"))
        buy_clicks = sum(1 for item in data.values() if item.get("buy_clicks"))
        purchased = sum(1 for item in data.values() if item.get("purchased"))
        blocked = sum(1 for item in data.values() if item.get("blocked"))
        return {
            "total": total_users,
            "started": started,
            "buy_clicked": buy_clicks,
            "purchased": purchased,
            "blocked": blocked,
        }

    def all_user_ids(self) -> list[int]:
        return [int(user_id) for user_id in self._load().keys()]
