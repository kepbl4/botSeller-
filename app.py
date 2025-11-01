from __future__ import annotations

import asyncio
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from aiogram import Bot, Dispatcher

from config import config
from handlers import admin as admin_handlers
from handlers import buy as buy_handlers
from handlers import download as download_handlers
from handlers import main_menu as main_menu_handlers
from handlers import membership as membership_handlers
from services.access import AccessService
from services.admins import AdminService
from services.alerts import AlertService
from services.content import ContentService
from services.metrics import MetricsService
from services.payments import PaymentService
from services.settings import SettingsService
from services.storage import StorageService
from services.users import UserService


def setup_directories(*paths: Path) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def setup_logging(logs_dir: Path) -> None:
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / "app.log"
    handler = RotatingFileHandler(log_file, maxBytes=5_000_000, backupCount=5, encoding="utf-8")
    logging.basicConfig(
        level=logging.INFO,
        handlers=[handler, logging.StreamHandler()],
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


async def main() -> None:
    setup_directories(config.data_dir, config.logs_dir)
    setup_logging(config.logs_dir)

    settings = SettingsService(config.settings_file)
    settings.apply(config)

    content_service = ContentService(config.content_file)
    access_service = AccessService(config.access_file)
    storage_service = StorageService(config.purchases_file, config.orders_file, config.ledger_file)
    metrics_service = MetricsService(config.metrics_file)
    user_service = UserService(config.users_file)
    alert_service = AlertService(config.alerts_file)
    admin_service = AdminService(config.admin_file, config.admin_ids)

    bot = Bot(token=config.bot_token, parse_mode="HTML")
    payment_service = PaymentService(bot, config, storage_service, access_service, metrics_service, user_service)

    faq_text = content_service.get_faq()

    dp = Dispatcher()

    dp.include_router(
        main_menu_handlers.create_router(
            config=config,
            content=content_service,
            users=user_service,
            metrics=metrics_service,
            admins=admin_service,
            storage=storage_service,
            faq_text=faq_text,
        )
    )
    dp.include_router(buy_handlers.create_router(config, payment_service, user_service))
    dp.include_router(download_handlers.create_router(config, access_service))
    dp.include_router(membership_handlers.create_router(metrics_service, user_service))

    admin_context = admin_handlers.AdminContext(
        config=config,
        content=content_service,
        storage=storage_service,
        access=access_service,
        metrics=metrics_service,
        alerts=alert_service,
        users=user_service,
        admins=admin_service,
        payments=payment_service,
        settings=settings,
    )
    dp.include_router(admin_handlers.create_router(admin_context))

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
