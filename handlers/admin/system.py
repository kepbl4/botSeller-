from __future__ import annotations

import subprocess

from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from . import AdminContext


def create_router(context: AdminContext) -> Router:
    router = Router()

    def _keyboard():
        builder = InlineKeyboardBuilder()
        builder.button(text="⏸️ Пауза", callback_data="admin:system:pause")
        builder.button(text="▶️ Старт", callback_data="admin:system:resume")
        layout = [2]
        if context.config.admin_system.allow_systemd:
            builder.button(text="🔁 Перезапуск", callback_data="admin:system:restart")
            layout.append(1)
        builder.button(text="⬅️ Назад", callback_data="admin:menu")
        layout.append(1)
        builder.adjust(*layout)
        return builder.as_markup()

    async def _ensure_admin(callback: CallbackQuery) -> bool:
        if not callback.from_user or not context.is_admin(callback.from_user.id):
            await callback.answer("Доступ заборонено", show_alert=True)
            return False
        return True

    def _text() -> str:
        state = "увімкнено" if context.config.sales_enabled else "на паузі"
        extra = "systemd доступний" if context.config.admin_system.allow_systemd else "systemd заборонено"
        return f"Стан продажу: {state}\nSystemd: {extra}"

    @router.callback_query(lambda c: c.data == "admin:system")
    async def open_menu(callback: CallbackQuery) -> None:
        if not callback.message or not await _ensure_admin(callback):
            return
        await callback.message.edit_caption(_text(), reply_markup=_keyboard())
        await callback.answer()

    @router.callback_query(lambda c: c.data == "admin:system:pause")
    async def pause(callback: CallbackQuery) -> None:
        if not callback.message or not await _ensure_admin(callback):
            return
        context.config.sales_enabled = False
        context.settings.set_sales_enabled(False)
        await callback.message.edit_caption(_text(), reply_markup=_keyboard())
        await callback.answer("Продаж поставлено на паузу")

    @router.callback_query(lambda c: c.data == "admin:system:resume")
    async def resume(callback: CallbackQuery) -> None:
        if not callback.message or not await _ensure_admin(callback):
            return
        context.config.sales_enabled = True
        context.settings.set_sales_enabled(True)
        await callback.message.edit_caption(_text(), reply_markup=_keyboard())
        await callback.answer("Продаж відновлено")

    @router.callback_query(lambda c: c.data == "admin:system:restart")
    async def restart(callback: CallbackQuery) -> None:
        if not callback.message or not await _ensure_admin(callback):
            return
        if not context.config.admin_system.allow_systemd:
            await callback.answer("Перезапуск заборонений", show_alert=True)
            return
        try:
            subprocess.run(
                ["sudo", "systemctl", "restart", context.config.admin_system.service_name],
                check=True,
                capture_output=True,
                text=True,
            )
            await callback.answer("Перезапуск виконано")
        except subprocess.CalledProcessError as exc:
            await callback.answer(f"Помилка restart: {exc.stderr}", show_alert=True)
        await callback.message.edit_caption(_text(), reply_markup=_keyboard())

    return router
