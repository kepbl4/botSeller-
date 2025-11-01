from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.types import LabeledPrice, Message, PreCheckoutQuery

from config import Config
from services.access import AccessService
from services.metrics import MetricsService
from services.storage import StorageService
from services.users import UserService
from ui.pages import download_keyboard

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(
        self,
        bot: Bot,
        config: Config,
        storage: StorageService,
        access: AccessService,
        metrics: MetricsService,
        users: UserService,
    ) -> None:
        self.bot = bot
        self.config = config
        self.storage = storage
        self.access = access
        self.metrics = metrics
        self.users = users

    async def create_invoice(self, message: Message) -> None:
        user = message.from_user
        if not user:
            return

        self.metrics.ensure_user("buy_clicks", user.id)
        price = self.config.guide.price_stars
        payload = self.config.guide.payload
        self.storage.add_order(user_id=user.id, payload=payload, amount=price, status="створено")

        prices = [LabeledPrice(label="Guide", amount=price)]
        try:
            await message.answer_invoice(
                title="XTR Guide",
                description="Гайд доступний після оплати",
                payload=payload,
                provider_token="",
                currency="XTR",
                prices=prices,
            )
        except Exception as exc:
            logger.exception("Не вдалося відправити інвойс")
            self.storage.add_order(
                user.id,
                payload,
                price,
                status="помилка",
                reason=str(exc),
            )
            self.metrics.increment("purchases_fail")
            return

    async def handle_pre_checkout(self, query: PreCheckoutQuery) -> None:
        await query.answer(ok=True)

    async def handle_successful_payment(self, message: Message) -> None:
        user = message.from_user
        payment = message.successful_payment
        if not user or not payment:
            return

        charge_id = payment.telegram_payment_charge_id
        if self.storage.charge_exists(charge_id):
            logger.info("Повторний платіж %s проігноровано", charge_id)
            return

        payload = payment.invoice_payload
        amount = self.config.guide.price_stars
        self.storage.add_purchase(user.id, charge_id, amount, payload)
        self.storage.add_order(user.id, payload, amount, status="успіх")
        self.access.set_access(user.id, charge_id)
        self.metrics.increment("purchases_success")
        self.users.mark_purchase(user.id)

        await message.answer(
            "Оплата успішна ✅",
            reply_markup=download_keyboard(True, self.config.guide.url if self.config.guide.mode == "url" else None),
        )

    async def refund(self, _requester_id: int, charge_id: str) -> bool:
        purchase = self.storage.find_purchase(charge_id)
        if not purchase:
            logger.warning("Чардж %s не знайдено для повернення", charge_id)
            return False
        user_id = int(purchase["user_id"])
        try:
            result = await self.bot.refund_star_payment(user_id=user_id, telegram_payment_charge_id=charge_id)
        except Exception:
            logger.exception("Не вдалося виконати повернення для %s", charge_id)
            return False
        if result:
            self.storage.add_ledger_entry(user_id, -self.config.guide.price_stars, "refund", charge_id=charge_id)
        return bool(result)
