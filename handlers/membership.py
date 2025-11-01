from __future__ import annotations

from aiogram import Router
from aiogram.enums import ChatMemberStatus
from aiogram.types import ChatMemberUpdated

from services.metrics import MetricsService
from services.users import UserService


def create_router(metrics: MetricsService, users: UserService) -> Router:
    router = Router()

    @router.my_chat_member()
    async def on_my_chat_member(event: ChatMemberUpdated) -> None:
        new_status = event.new_chat_member.status
        if new_status in {ChatMemberStatus.BANNED, ChatMemberStatus.LEFT, ChatMemberStatus.RESTRICTED}:
            metrics.increment("blocked_bot")
            if event.from_user:
                users.mark_blocked(event.from_user.id)

    return router
