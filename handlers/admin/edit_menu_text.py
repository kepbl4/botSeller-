from __future__ import annotations

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from . import AdminContext


class EditStates(StatesGroup):
    waiting_page_one = State()


def create_router(context: AdminContext) -> Router:
    router = Router()

    async def _ensure_admin(callback: CallbackQuery) -> bool:
        if not callback.from_user or not context.is_admin(callback.from_user.id):
            await callback.answer("Доступ заборонено", show_alert=True)
            return False
        return True

    @router.callback_query(lambda c: c.data == "admin:edit_text")
    async def ask_text(callback: CallbackQuery, state: FSMContext) -> None:
        if not await _ensure_admin(callback):
            return
        await state.set_state(EditStates.waiting_page_one)
        await callback.answer("Надішліть новий текст для головної сторінки", show_alert=True)

    @router.message(EditStates.waiting_page_one)
    async def set_text(message: Message, state: FSMContext) -> None:
        if not context.is_admin(message.from_user.id):
            return
        text = message.text
        if not text:
            await message.answer("Очікую текст")
            return
        context.content.update_page_one(text)
        await message.answer("Текст оновлено")
        await state.clear()

    return router
