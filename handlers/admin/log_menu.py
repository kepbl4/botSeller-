from __future__ import annotations

from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from services.files import tail

from . import AdminContext


def create_router(context: AdminContext) -> Router:
    router = Router()

    def _keyboard() -> InlineKeyboardBuilder:
        builder = InlineKeyboardBuilder()
        builder.button(text="Баланс", callback_data="admin:logs:balance")
        builder.button(text="Платежі", callback_data="admin:logs:payments")
        builder.button(text="Інвойси", callback_data="admin:logs:orders")
        builder.button(text="Користувачі", callback_data="admin:logs:users")
        builder.button(text="Системний лог", callback_data="admin:logs:system")
        builder.button(text="Алерти", callback_data="admin:logs:alerts")
        builder.button(text="⬅️ Назад", callback_data="admin:menu")
        builder.adjust(2, 2, 2, 1)
        return builder

    async def _ensure_admin(callback: CallbackQuery) -> bool:
        if not callback.from_user or not context.is_admin(callback.from_user.id):
            await callback.answer("Доступ заборонено", show_alert=True)
            return False
        return True

    @router.callback_query(lambda c: c.data == "admin:logs")
    async def open_logs(callback: CallbackQuery) -> None:
        if not callback.message or not await _ensure_admin(callback):
            return
        await callback.message.edit_caption("Логи та статистика", reply_markup=_keyboard().as_markup())
        await callback.answer()

    @router.callback_query(lambda c: c.data == "admin:logs:balance")
    async def balance(callback: CallbackQuery) -> None:
        if not callback.message or not await _ensure_admin(callback):
            return
        balance_stars = context.storage.compute_balance()
        ton = balance_stars * context.config.guide.ton_per_star
        text = f"Баланс: {balance_stars} ⭐️\n≈ {ton:.4f} TON"
        if context.config.guide.ton_wallet:
            text += f"\nTON гаманець: {context.config.guide.ton_wallet}"
        await callback.message.edit_caption(text, reply_markup=_keyboard().as_markup())
        await callback.answer()

    @router.callback_query(lambda c: c.data == "admin:logs:payments")
    async def payments(callback: CallbackQuery) -> None:
        if not callback.message or not await _ensure_admin(callback):
            return
        purchases = context.storage.read_purchases(limit=20)
        lines = ["Успішні оплати:"]
        for item in reversed(purchases):
            lines.append(f"• user={item['user_id']} amount={item['amount']} payload={item['payload']} ts={item['ts']}")
        orders = [o for o in context.storage.read_orders(limit=20) if o.get("status") != "успіх"]
        if orders:
            lines.append("\nНевдалі/очікувані:")
            for item in reversed(orders):
                reason = item.get("reason")
                suffix = f" причина={reason}" if reason else ""
                lines.append(
                    f"• user={item['user_id']} status={item['status']} payload={item['payload']} ts={item['ts']}{suffix}"
                )
        await callback.message.edit_caption("\n".join(lines), reply_markup=_keyboard().as_markup())
        await callback.answer()

    @router.callback_query(lambda c: c.data == "admin:logs:orders")
    async def orders(callback: CallbackQuery) -> None:
        if not callback.message or not await _ensure_admin(callback):
            return
        orders = context.storage.read_orders(limit=100)
        lines = ["Останні інвойси:"]
        for item in reversed(orders):
            reason = item.get("reason")
            suffix = f" причина={reason}" if reason else ""
            lines.append(
                f"• user={item['user_id']} payload={item['payload']} amount={item['amount']} status={item['status']} ts={item['ts']}{suffix}"
            )
        await callback.message.edit_caption("\n".join(lines), reply_markup=_keyboard().as_markup())
        await callback.answer()

    @router.callback_query(lambda c: c.data == "admin:logs:users")
    async def users(callback: CallbackQuery) -> None:
        if not callback.message or not await _ensure_admin(callback):
            return
        stats = context.users.stats()
        metrics = context.metrics.snapshot()
        text = (
            "Користувачі:\n"
            f"Всього: {stats['total']}\n"
            f"Стартували: {stats['started']}\n"
            f"Натиснули «Купити»: {stats['buy_clicked']}\n"
            f"Придбали: {stats['purchased']}\n"
            f"Відписались: {stats['blocked']}\n\n"
            "Метрики:\n"
            f"Start: {metrics.unique_users_started}\n"
            f"Buy clicks: {metrics.buy_clicks}\n"
            f"Success: {metrics.purchases_success}\n"
            f"Fail: {metrics.purchases_fail}\n"
            f"Blocked: {metrics.blocked_bot}\n"
        )
        await callback.message.edit_caption(text, reply_markup=_keyboard().as_markup())
        await callback.answer()

    @router.callback_query(lambda c: c.data == "admin:logs:system")
    async def system_log(callback: CallbackQuery) -> None:
        if not callback.message or not await _ensure_admin(callback):
            return
        lines = tail(context.config.logs_dir / "app.log", 40)
        content = "Останні записи:\n" + "".join(lines[-40:]) if lines else "Логи порожні"
        await callback.message.edit_caption(content[-1024:], reply_markup=_keyboard().as_markup())
        await callback.answer()

    @router.callback_query(lambda c: c.data == "admin:logs:alerts")
    async def alerts(callback: CallbackQuery) -> None:
        if not callback.message or not await _ensure_admin(callback):
            return
        data = context.alerts.snapshot()
        text = f"Алерти: доставлено={data.get('sent', 0)} помилки={data.get('failed', 0)}"
        await callback.message.edit_caption(text, reply_markup=_keyboard().as_markup())
        await callback.answer()

    return router
