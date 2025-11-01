from __future__ import annotations

from dataclasses import dataclass

from aiogram import Router
from aiogram.types import CallbackQuery

from config import Config
from services.access import AccessService
from services.admins import AdminService
from services.alerts import AlertService
from services.content import ContentService
from services.metrics import MetricsService
from services.payments import PaymentService
from services.settings import SettingsService
from services.storage import StorageService
from services.users import UserService
from ui import pages

from . import actions, broadcast, edit_menu_text, log_menu, maintenance, system


@dataclass(slots=True)
class AdminContext:
    config: Config
    content: ContentService
    storage: StorageService
    access: AccessService
    metrics: MetricsService
    alerts: AlertService
    users: UserService
    admins: AdminService
    payments: PaymentService
    settings: SettingsService

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admins.get_admin_ids()


MAIN_TEXT = "Адмін-меню 🤖\nОберіть потрібний розділ"


def create_router(context: AdminContext) -> Router:
    router = Router()

    def admin_keyboard():
        from aiogram.utils.keyboard import InlineKeyboardBuilder

        builder = InlineKeyboardBuilder()
        builder.button(text="Журнали", callback_data="admin:logs")
        builder.button(text="Дії", callback_data="admin:actions")
        builder.button(text="Технічне обслуговування", callback_data="admin:maintenance")
        builder.button(text="Розсилка", callback_data="admin:broadcast")
        builder.button(text="Додати адміна", callback_data="admin:add")
        builder.button(text="🤖 Система", callback_data="admin:system")
        builder.button(text="✏️ Редагувати меню", callback_data="admin:edit_text")
        builder.button(text="⬅️ До меню", callback_data="page:main")
        builder.adjust(2, 2, 2, 1, 1)
        return builder.as_markup()

    @router.callback_query(lambda c: c.data == "admin:menu")
    async def open_admin(callback: CallbackQuery) -> None:
        if not callback.message or not callback.from_user:
            return
        if not context.is_admin(callback.from_user.id):
            await callback.answer("Доступ заборонено", show_alert=True)
            return
        await callback.message.edit_caption(MAIN_TEXT, reply_markup=admin_keyboard())
        await callback.answer()

    router.include_router(log_menu.create_router(context))
    router.include_router(actions.create_router(context))
    router.include_router(maintenance.create_router(context))
    router.include_router(broadcast.create_router(context))
    router.include_router(system.create_router(context))
    router.include_router(edit_menu_text.create_router(context))

    return router
