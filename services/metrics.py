from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from services.files import read_json, write_json


@dataclass(slots=True)
class MetricsSnapshot:
    unique_users_started: int
    buy_clicks: int
    purchases_success: int
    purchases_fail: int
    blocked_bot: int


class MetricsService:
    def __init__(self, path: Path) -> None:
        self.path = path

    def _load(self) -> Dict[str, int]:
        return read_json(
            self.path,
            default={
                "unique_users_started": 0,
                "buy_clicks": 0,
                "purchases_success": 0,
                "purchases_fail": 0,
                "blocked_bot": 0,
            },
        )

    def _save(self, data: Dict[str, int]) -> None:
        write_json(self.path, data)

    def increment(self, key: str, amount: int = 1) -> None:
        data = self._load()
        data[key] = data.get(key, 0) + amount
        self._save(data)

    def ensure_user(self, key: str, user_id: int) -> None:
        marker_key = f"__users_{key}"
        data = self._load()
        seen = set(data.get(marker_key, []))
        if user_id in seen:
            return
        seen.add(user_id)
        data[marker_key] = list(seen)
        data[key] = data.get(key, 0) + 1
        self._save(data)

    def snapshot(self) -> MetricsSnapshot:
        data = self._load()
        return MetricsSnapshot(
            unique_users_started=data.get("unique_users_started", 0),
            buy_clicks=data.get("buy_clicks", 0),
            purchases_success=data.get("purchases_success", 0),
            purchases_fail=data.get("purchases_fail", 0),
            blocked_bot=data.get("blocked_bot", 0),
        )
