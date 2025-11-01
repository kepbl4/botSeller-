from __future__ import annotations

from aiogram import Router
from aiogram.filters import SuccessfulPaymentFilter
from aiogram.types import CallbackQuery, Message

from config import Config
from services.payments import PaymentService
from services.users import UserService


def create_router(config: Config, payments: PaymentService, users: UserService):
    router = Router()

    @router.callback_query(lambda c: c.data == "buy:start")
    async def on_buy(callback: CallbackQuery) -> None:
        if not callback.message or not callback.from_user:
            return
        if not config.sales_enabled:
            await callback.answer("Продаж тимчасово недоступний", show_alert=True)
            return
        users.mark_buy_click(callback.from_user.id)
        await payments.create_invoice(callback.message)
        await callback.answer()

    @router.pre_checkout_query()
    async def pre_checkout(query):
        await payments.handle_pre_checkout(query)

    @router.message(SuccessfulPaymentFilter(True))
    async def successful_payment(message: Message) -> None:
        await payments.handle_successful_payment(message)

    return router
