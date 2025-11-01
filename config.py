from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Set

import os


class ConfigError(RuntimeError):
    """Raised when mandatory configuration is missing."""


def _parse_int_list(value: Optional[str]) -> List[int]:
    if not value:
        return []
    result: List[int] = []
    for chunk in value.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            result.append(int(chunk))
        except ValueError as exc:
            raise ConfigError(f"Cannot parse integer value from '{chunk}'") from exc
    return result


def _parse_bool(value: Optional[str], *, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ConfigError(f"Environment variable {name} is required")
    return value


@dataclass(slots=True)
class GuideConfig:
    mode: str
    url: str
    payload: str
    price_uah: int
    old_price_uah: int
    uah_per_star: float
    ton_per_star: float
    ton_wallet: Optional[str]

    @property
    def price_stars(self) -> int:
        return round(self.price_uah / self.uah_per_star)


@dataclass(slots=True)
class AdminSystemConfig:
    allow_systemd: bool
    service_name: str


@dataclass(slots=True)
class Config:
    bot_token: str
    admin_ids: Set[int]
    alert_chat_ids: List[int]
    guide: GuideConfig
    sales_enabled: bool
    data_dir: Path
    logs_dir: Path
    admin_file: Path
    alerts_file: Path
    users_file: Path
    access_file: Path
    purchases_file: Path
    orders_file: Path
    ledger_file: Path
    metrics_file: Path
    content_file: Path
    settings_file: Path
    admin_system: AdminSystemConfig

    @classmethod
    def load(cls) -> "Config":
        bot_token = _require_env("BOT_TOKEN")
        admin_ids = set(_parse_int_list(os.getenv("ADMIN_IDS")))
        alert_chat_ids = _parse_int_list(os.getenv("ALERT_CHAT_IDS"))
        guide_mode = os.getenv("GUIDE_MODE", "url")
        guide_url = os.getenv("GUIDE_URL", "")
        payload = os.getenv("PAYLOAD", "guide_500")
        price_uah = int(os.getenv("PRICE_UAH", "299"))
        old_price_uah = int(os.getenv("OLD_PRICE_UAH", "699"))
        uah_per_star = float(os.getenv("UAH_PER_STAR", "0.55"))
        ton_per_star = float(os.getenv("TON_PER_STAR", "0.0015"))
        ton_wallet = os.getenv("TON_WALLET")
        sales_enabled = _parse_bool(os.getenv("SALES_ENABLED"), default=True)
        allow_systemd = _parse_bool(os.getenv("ALLOW_SYSTEMD"), default=False)
        service_name = os.getenv("SERVICE_NAME", "xtrbot.service")

        base_data_dir = Path(os.getenv("DATA_DIR", "data"))
        base_logs_dir = Path(os.getenv("LOGS_DIR", "logs"))

        return cls(
            bot_token=bot_token,
            admin_ids=admin_ids,
            alert_chat_ids=alert_chat_ids,
            guide=GuideConfig(
                mode=guide_mode,
                url=guide_url,
                payload=payload,
                price_uah=price_uah,
                old_price_uah=old_price_uah,
                uah_per_star=uah_per_star,
                ton_per_star=ton_per_star,
                ton_wallet=ton_wallet,
            ),
            sales_enabled=sales_enabled,
            data_dir=base_data_dir,
            logs_dir=base_logs_dir,
            admin_file=base_data_dir / "admins.json",
            alerts_file=base_data_dir / "alerts.json",
            users_file=base_data_dir / "users.json",
            access_file=base_data_dir / "access.json",
            purchases_file=base_data_dir / "purchases.jsonl",
            orders_file=base_data_dir / "orders.jsonl",
            ledger_file=base_data_dir / "ledger.jsonl",
            metrics_file=base_data_dir / "metrics.json",
            content_file=base_data_dir / "content.json",
            settings_file=base_data_dir / "settings.json",
            admin_system=AdminSystemConfig(
                allow_systemd=allow_systemd,
                service_name=service_name,
            ),
        )


config = Config.load()
