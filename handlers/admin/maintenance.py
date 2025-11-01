from __future__ import annotations

from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from . import AdminContext


def create_router(context: AdminContext) -> Router:
    router = Router()

    def _keyboard():
        builder = InlineKeyboardBuilder()
        status = "Вимкнути" if context.config.sales_enabled else "Увімкнути"
        builder.button(text=f"{status} продаж", callback_data="admin:maintenance:toggle")
        builder.button(text="⬅️ Назад", callback_data="admin:menu")
        builder.adjust(1)
        return builder.as_markup()

    async def _ensure_admin(callback: CallbackQuery) -> bool:
        if not callback.from_user or not context.is_admin(callback.from_user.id):
            await callback.answer("Доступ заборонено", show_alert=True)
            return False
        return True

    def _text() -> str:
        state = "увімкнено" if context.config.sales_enabled else "вимкнено"
        return f"Продаж зараз {state}."

    @router.callback_query(lambda c: c.data == "admin:maintenance")
    async def open_menu(callback: CallbackQuery) -> None:
        if not callback.message or not await _ensure_admin(callback):
            return
        await callback.message.edit_caption(_text(), reply_markup=_keyboard())
        await callback.answer()

    @router.callback_query(lambda c: c.data == "admin:maintenance:toggle")
    async def toggle(callback: CallbackQuery) -> None:
        if not callback.message or not await _ensure_admin(callback):
            return
        context.config.sales_enabled = not context.config.sales_enabled
        context.settings.set_sales_enabled(context.config.sales_enabled)
        await callback.message.edit_caption(_text(), reply_markup=_keyboard())
        await callback.answer("Стан оновлено")

    return router
