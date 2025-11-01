from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict

from config import Config
from services.files import read_json, write_json


class SettingsService:
    def __init__(self, path: Path) -> None:
        self.path = path

    def _load(self) -> Dict[str, Any]:
        return read_json(self.path, default={})

    def _save(self, data: Dict[str, Any]) -> None:
        write_json(self.path, data)

    def apply(self, config: Config) -> None:
        data = self._load()
        if "price_uah" in data:
            config.guide.price_uah = int(data["price_uah"])
        if "old_price_uah" in data:
            config.guide.old_price_uah = int(data["old_price_uah"])
        if "guide_url" in data:
            config.guide.url = str(data["guide_url"])
        if "sales_enabled" in data:
            config.sales_enabled = bool(data["sales_enabled"])

    def set_price(self, price_uah: int, old_price_uah: int | None = None) -> None:
        data = self._load()
        data["price_uah"] = price_uah
        if old_price_uah is not None:
            data["old_price_uah"] = old_price_uah
        self._save(data)

    def set_guide_url(self, url: str) -> None:
        data = self._load()
        data["guide_url"] = url
        self._save(data)

    def set_sales_enabled(self, enabled: bool) -> None:
        data = self._load()
        data["sales_enabled"] = enabled
        self._save(data)
