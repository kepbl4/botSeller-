from __future__ import annotations

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from . import AdminContext


class ActionStates(StatesGroup):
    waiting_price = State()
    waiting_url = State()
    waiting_admin = State()
    waiting_refund = State()
    waiting_withdrawal = State()
    waiting_award = State()
    waiting_correction = State()


def create_router(context: AdminContext) -> Router:
    router = Router()

    def _keyboard():
        builder = InlineKeyboardBuilder()
        builder.button(text="Змінити ціну", callback_data="admin:actions:price")
        builder.button(text="Змінити GUIDE_URL", callback_data="admin:actions:url")
        builder.button(text="🔻 Списати зірки", callback_data="admin:actions:withdrawal")
        builder.button(text="🔺 Нарахувати зірки", callback_data="admin:actions:award")
        builder.button(text="♻️ Корекція", callback_data="admin:actions:correction")
        builder.button(text="Повернення (refund)", callback_data="admin:actions:refund")
        builder.button(text="⬅️ Назад", callback_data="admin:menu")
        builder.adjust(1)
        return builder.as_markup()

    async def _ensure_admin(callback: CallbackQuery) -> bool:
        if not callback.from_user or not context.is_admin(callback.from_user.id):
            await callback.answer("Доступ заборонено", show_alert=True)
            return False
        return True

    def _format_info() -> str:
        ton = context.config.guide.price_stars * context.config.guide.ton_per_star
        return (
            "Керування пропозицією\n"
            f"Ціна: {context.config.guide.price_uah} UAH (~{context.config.guide.old_price_uah})\n"
            f"Вартість у зірках: {context.config.guide.price_stars}\n"
            f"≈ {ton:.4f} TON\n"
            f"GUIDE_URL: {context.config.guide.url}"
        )

    @router.callback_query(lambda c: c.data == "admin:actions")
    async def open_actions(callback: CallbackQuery, state: FSMContext) -> None:
        if not callback.message or not await _ensure_admin(callback):
            return
        await state.clear()
        await callback.message.edit_caption(_format_info(), reply_markup=_keyboard())
        await callback.answer()

    @router.callback_query(lambda c: c.data == "admin:actions:price")
    async def ask_price(callback: CallbackQuery, state: FSMContext) -> None:
        if not callback.message or not await _ensure_admin(callback):
            return
        await state.set_state(ActionStates.waiting_price)
        await callback.answer("Введіть нову ціну у форматі '299,699'", show_alert=True)

    @router.callback_query(lambda c: c.data == "admin:actions:url")
    async def ask_url(callback: CallbackQuery, state: FSMContext) -> None:
        if not callback.message or not await _ensure_admin(callback):
            return
        await state.set_state(ActionStates.waiting_url)
        await callback.answer("Надішліть новий GUIDE_URL", show_alert=True)

    @router.callback_query(lambda c: c.data == "admin:add")
    async def ask_admin(callback: CallbackQuery, state: FSMContext) -> None:
        if not callback.message or not await _ensure_admin(callback):
            return
        await state.set_state(ActionStates.waiting_admin)
        await callback.answer("Вкажіть user_id нового адміна", show_alert=True)

    async def _ask_manual(callback: CallbackQuery, state: FSMContext, target_state: State, prompt: str) -> None:
        if not callback.message or not await _ensure_admin(callback):
            return
        await state.set_state(target_state)
        await callback.answer(prompt, show_alert=True)

    @router.callback_query(lambda c: c.data == "admin:actions:withdrawal")
    async def ask_withdrawal(callback: CallbackQuery, state: FSMContext) -> None:
        await _ask_manual(
            callback,
            state,
            ActionStates.waiting_withdrawal,
            "Формат: user_id, сума, коментар (необов'язково)",
        )

    @router.callback_query(lambda c: c.data == "admin:actions:award")
    async def ask_award(callback: CallbackQuery, state: FSMContext) -> None:
        await _ask_manual(
            callback,
            state,
            ActionStates.waiting_award,
            "Формат: user_id, сума, коментар (необов'язково)",
        )

    @router.callback_query(lambda c: c.data == "admin:actions:correction")
    async def ask_correction(callback: CallbackQuery, state: FSMContext) -> None:
        await _ask_manual(
            callback,
            state,
            ActionStates.waiting_correction,
            "Формат: user_id, +/-сума, коментар",
        )

    @router.callback_query(lambda c: c.data == "admin:actions:refund")
    async def ask_refund(callback: CallbackQuery, state: FSMContext) -> None:
        if not callback.message or not await _ensure_admin(callback):
            return
        await state.set_state(ActionStates.waiting_refund)
        await callback.answer("Надішліть charge_id для повернення", show_alert=True)

    def _parse_manual_payload(text: str) -> tuple[int, int, str | None]:
        parts = [part.strip() for part in text.split(",", 2) if part.strip()]
        if len(parts) < 2:
            raise ValueError("Очікую щонайменше user_id та суму")
        user_id = int(parts[0])
        amount = int(parts[1])
        comment = parts[2] if len(parts) > 2 else None
        return user_id, amount, comment

    @router.message(ActionStates.waiting_price)
    async def set_price(message: Message, state: FSMContext) -> None:
        if not context.is_admin(message.from_user.id):
            return
        parts = [part.strip() for part in message.text.split(",") if part.strip()]
        if not parts:
            await message.answer("Формат: нова_ціна, стара_ціна")
            return
        try:
            price = int(parts[0])
            old_price = int(parts[1]) if len(parts) > 1 else context.config.guide.old_price_uah
        except ValueError:
            await message.answer("Невірне число")
            return
        context.config.guide.price_uah = price
        context.config.guide.old_price_uah = old_price
        context.settings.set_price(price, old_price)
        await message.answer(
            f"Ціну оновлено. Нова вартість: {context.config.guide.price_uah} UAH / {context.config.guide.price_stars}⭐️"
        )
        await state.clear()

    @router.message(ActionStates.waiting_url)
    async def set_url(message: Message, state: FSMContext) -> None:
        if not context.is_admin(message.from_user.id):
            return
        url = message.text.strip()
        context.config.guide.url = url
        context.settings.set_guide_url(url)
        await message.answer("GUIDE_URL оновлено")
        await state.clear()

    @router.message(ActionStates.waiting_admin)
    async def set_admin(message: Message, state: FSMContext) -> None:
        if not context.is_admin(message.from_user.id):
            return
        try:
            user_id = int(message.text.strip())
        except ValueError:
            await message.answer("Очікую ціле число")
            return
        admins = context.admins.add_admin(user_id)
        await message.answer(f"Адмінів тепер: {', '.join(map(str, sorted(admins)))}")
        await state.clear()

    async def _handle_manual(message: Message, state: FSMContext, *, kind: str, expect_positive: bool | None) -> None:
        if not context.is_admin(message.from_user.id):
            return
        try:
            user_id, amount, comment = _parse_manual_payload(message.text)
        except (ValueError, TypeError):
            await message.answer("Формат: user_id, сума, коментар")
            return
        if expect_positive is True and amount <= 0:
            await message.answer("Сума має бути більшою за 0")
            return
        adjusted_amount = amount
        if kind == "withdrawal":
            adjusted_amount = -abs(amount)
        elif kind == "award":
            adjusted_amount = abs(amount)
        elif kind == "correction":
            adjusted_amount = amount

        record = context.storage.add_ledger_entry(
            user_id,
            adjusted_amount,
            kind,
            comment=comment,
        )
        await message.answer(
            f"Запис створено: user={record.user_id} amount={record.amount} kind={record.kind}"
        )
        await state.clear()

    @router.message(ActionStates.waiting_withdrawal)
    async def handle_withdrawal(message: Message, state: FSMContext) -> None:
        await _handle_manual(message, state, kind="withdrawal", expect_positive=True)

    @router.message(ActionStates.waiting_award)
    async def handle_award(message: Message, state: FSMContext) -> None:
        await _handle_manual(message, state, kind="award", expect_positive=True)

    @router.message(ActionStates.waiting_correction)
    async def handle_correction(message: Message, state: FSMContext) -> None:
        await _handle_manual(message, state, kind="correction", expect_positive=None)

    @router.message(ActionStates.waiting_refund)
    async def process_refund(message: Message, state: FSMContext) -> None:
        if not context.is_admin(message.from_user.id):
            return
        charge_id = message.text.strip()
        success = await context.payments.refund(message.from_user.id, charge_id)
        if success:
            await message.answer("Повернення виконано")
        else:
            await message.answer("Повернення не вдалось")
        await state.clear()

    return router
