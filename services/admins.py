from __future__ import annotations

from pathlib import Path
from typing import List, Set

from services.files import read_json, write_json


class AdminService:
    def __init__(self, path: Path, initial: Set[int]) -> None:
        self.path = path
        self.initial = set(initial)

    def _load(self) -> Set[int]:
        data = read_json(self.path, default={"extra": []})
        return self.initial | set(data.get("extra", []))

    def get_admin_ids(self) -> Set[int]:
        return self._load()

    def add_admin(self, user_id: int) -> Set[int]:
        data = read_json(self.path, default={"extra": []})
        extra = set(data.get("extra", []))
        extra.add(user_id)
        write_json(self.path, {"extra": sorted(extra)})
        return self._load()
