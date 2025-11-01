from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from services.files import locked_file, read_json, write_json


@dataclass(slots=True)
class AccessRecord:
    has_access: bool
    last_charge_id: str
    ts: int


class AccessService:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> Dict[str, dict]:
        return read_json(self.path, default={})

    def set_access(self, user_id: int, charge_id: str) -> AccessRecord:
        now = int(time.time())
        data = self.load()
        record = {
            "has_access": True,
            "last_charge_id": charge_id,
            "ts": now,
        }
        data[str(user_id)] = record
        write_json(self.path, data)
        return AccessRecord(**record)

    def has_access(self, user_id: int) -> bool:
        data = self.load()
        return data.get(str(user_id), {}).get("has_access", False)

    def get(self, user_id: int) -> AccessRecord | None:
        data = self.load()
        record = data.get(str(user_id))
        if not record:
            return None
        return AccessRecord(**record)
