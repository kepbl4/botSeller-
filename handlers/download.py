from __future__ import annotations

from aiogram import Router
from aiogram.types import CallbackQuery

from config import Config
from services.access import AccessService
from ui.pages import download_keyboard


def create_router(config: Config, access: AccessService):
    router = Router()

    @router.callback_query(lambda c: c.data == "download:guide")
    async def on_download(callback: CallbackQuery) -> None:
        if not callback.from_user or not callback.message:
            return
        user_id = callback.from_user.id
        if access.has_access(user_id):
            await callback.message.edit_reply_markup(
                reply_markup=download_keyboard(True, config.guide.url if config.guide.mode == "url" else None)
            )
            await callback.answer("Посилання оновлено", show_alert=False)
        else:
            await callback.answer("Немає доступу. Оформіть покупку ✨", show_alert=True)

    return router
