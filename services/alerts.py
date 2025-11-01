from __future__ import annotations

from pathlib import Path
from typing import Dict

from services.files import read_json, write_json


class AlertService:
    def __init__(self, path: Path) -> None:
        self.path = path

    def _load(self) -> Dict[str, int]:
        return read_json(self.path, default={"sent": 0, "failed": 0})

    def increment(self, key: str, amount: int = 1) -> None:
        data = self._load()
        data[key] = data.get(key, 0) + amount
        write_json(self.path, data)

    def snapshot(self) -> Dict[str, int]:
        return self._load()
