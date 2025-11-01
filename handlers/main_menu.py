from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from services.content import ContentService
from services.users import UserService
from services.metrics import MetricsService
from services.admins import AdminService
from services.storage import StorageService
from ui import pages
from config import Config


def create_router(
    config: Config,
    content: ContentService,
    users: UserService,
    metrics: MetricsService,
    admins: AdminService,
    storage: StorageService,
    faq_text: str,
):
    router = Router()

    def _has_admin(user_id: int) -> bool:
        return user_id in admins.get_admin_ids()

    def _username(message: Message) -> str:
        user = message.from_user
        if not user:
            return "гість"
        return user.username or user.full_name or "гість"

    @router.message(CommandStart())
    async def on_start(message: Message) -> None:
        user = message.from_user
        if not user:
            return
        metrics.ensure_user("unique_users_started", user.id)
        users.register_start(user.id, user.username)
        balance = storage.compute_user_balance(user.id)
        page = pages.main_page(
            config,
            content,
            _username(message),
            balance=balance,
            has_admin=_has_admin(user.id),
        )
        await message.answer_photo(
            photo=page.media.media,
            caption=page.media.caption,
            reply_markup=page.reply_markup,
        )

    @router.callback_query(lambda c: c.data == "page:main")
    async def to_main(callback: CallbackQuery) -> None:
        if not callback.message or not callback.from_user:
            return
        balance = storage.compute_user_balance(callback.from_user.id)
        page = pages.main_page(
            config,
            content,
            callback.from_user.username or callback.from_user.full_name or "гість",
            balance=balance,
            has_admin=_has_admin(callback.from_user.id),
        )
        await callback.message.edit_media(page.media, reply_markup=page.reply_markup)
        await callback.answer()

    @router.callback_query(lambda c: c.data == "page:faq")
    async def to_faq(callback: CallbackQuery) -> None:
        if not callback.message or not callback.from_user:
            return
        page = pages.faq_page(config, faq_text, has_admin=_has_admin(callback.from_user.id))
        await callback.message.edit_media(page.media, reply_markup=page.reply_markup)
        await callback.answer()

    return router
