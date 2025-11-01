from __future__ import annotations

import asyncio

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from . import AdminContext


class BroadcastStates(StatesGroup):
    waiting_message = State()


def create_router(context: AdminContext) -> Router:
    router = Router()

    async def _ensure_admin(callback: CallbackQuery) -> bool:
        if not callback.from_user or not context.is_admin(callback.from_user.id):
            await callback.answer("Доступ заборонено", show_alert=True)
            return False
        return True

    @router.callback_query(lambda c: c.data == "admin:broadcast")
    async def ask_message(callback: CallbackQuery, state: FSMContext) -> None:
        if not await _ensure_admin(callback):
            return
        await state.set_state(BroadcastStates.waiting_message)
        await callback.answer("Надішліть повідомлення для розсилки", show_alert=True)

    @router.message(BroadcastStates.waiting_message)
    async def send_broadcast(message: Message, state: FSMContext) -> None:
        if not context.is_admin(message.from_user.id):
            return
        text = message.text or message.caption
        if not text:
            await message.answer("Порожнє повідомлення")
            return
        user_ids = context.users.all_user_ids()
        sent = 0
        failed = 0
        for user_id in user_ids:
            try:
                await message.bot.send_message(user_id, text)
                sent += 1
                context.alerts.increment("sent")
            except Exception:
                failed += 1
                context.alerts.increment("failed")
            await asyncio.sleep(0.1)
        await message.answer(f"Розсилку завершено. Успішно: {sent}, помилки: {failed}")
        await state.clear()

    return router
