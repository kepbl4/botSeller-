from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from aiogram.types import (
    BufferedInputFile,
    FSInputFile,
    InlineKeyboardMarkup,
    InputMediaPhoto,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import Config
from services.content import ContentService, DEFAULT_PAGE_ONE


@dataclass(slots=True)
class PageData:
    media: InputMediaPhoto
    reply_markup: InlineKeyboardMarkup


def _build_base_keyboard(config: Config, *, forward: bool, has_admin: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"✨ Купити • {config.guide.price_uah} UAH ( ~{config.guide.old_price_uah} )",
        callback_data="buy:start",
    )
    if forward:
        builder.button(text="➡️ Далі", callback_data="page:faq")
    else:
        builder.button(text="⏪ Назад", callback_data="page:main")
    builder.adjust(1, 1)
    if has_admin:
        builder.button(text="Керування 🤖", callback_data="admin:menu")
        builder.adjust(1)
    return builder.as_markup()


PLACEHOLDER_MAIN = base64.b64decode(
    b"iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAACXBIWXMAAAsTAAALEwEAmpwYAAABfElEQVR4nO2ZMU7DMBBF3yYxABWwAAmYwAMswASZgADIwCRmEAFWwAeSClSE37ZfgNJszc7rK3S2ens7mQkCIIgCIIgCIIgCIIgCIIg+EVp0pP7o26h1qzX9o7Z0n4W1nZp6/oiup8QeixcIo5dDS9ozJpFNGSg7LJkJXQNXmYwDQasWCNq1ayFFxHDxF/TxXdKtK63QLNXjMYawRCB7wzU1zbXsYULyy3GUOAFo01lvy7hVMy3slMfiE0eYwgWF5KnGc0KMxBMXNDfy8B95qtTZ2Tr8RhR9riFZlwwDHX+Gdg2YFydil1wNlHVpY40DZx1aVONQMcj0qs3A9U9aliGwHFPrlYtQDXP0qsrwABHHVaXOcAQx12lbnIBGHXTVucQEQx11VZzgCmUUo50eZ5m9N/w8ngn5InVZbuzrcDutvQcHBwcHBwcHBweHfwPD94DeaG5yZUFw9U5+XVuAGD+U/5rxGt2mMFuwJZmVjY2NjoHtn/v2w6QnlX3gZBGiKc2u8/55e7BymdSSGlHxMTExMTExMTExMTExUT8BHwDU70zHzK5YLIAAAAASUVORK5CYII="
)

PLACEHOLDER_FAQ = base64.b64decode(
    b"iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAACXBIWXMAAAsTAAALEwEAmpwYAAABdUlEQVR4nO2ZMU7DMBBF30ZiAAmYgAxMgAGZgABMwABMwASZgABMwAAmYgBBsgUuux7r1iNINmdvYdV11e7f9zLy7t3twxAEARBEARBEARBEARBEEP4L7bU+sb0bOjZ9R7c6PoTrtXD9U5mQV5UhwETfFBqNqdw2Wkq5LXlBaBaG/QbFx+0oOOEtKGqXgjjCXOmkgXZRSBw1rULGT4LH7pfa+ubzmX2zMltYnmYg6Hk3bozeQmy0QlwrJHIZYbNm0FHnaowk5ElT7QLId62aZ4BNvtBpbaELbRpNoWGG1RT0HhvhT9/x5XFmHz8dzMqyKXj4cNJcBVvYFjuaYHBlN+jwHZXCHUoqE4MBG3gNVTejwGlfQn0m+djM2ulEHJRmfR65RXbQmAfk7qcSzGE97ZlpfZqL84AqLkXGR6oFV3ZL86A6rdVxkOqBVd2S+OgOK31cZDqhVXdkvjQDq21XGQqoEVXZL86A4rfVx0Mn4wfDnwJ3QoOYsKzv7cD19n4ODg4ODg4ODg8PP4PvN7+AHdjTszIpjqt2Xlp4RQNm/kf/e8xrVZV0mYBszKxsbGxs7N7c/37YdITyj/wMgTxFGZ3mfvlrsHKZ1JkaUeExMTExMTExMTExMTUxP5CeR0rjHeGy/1AAAAAElFTkSuQmCC"
)


def _build_media(path: Path, placeholder: bytes, filename: str, caption: str) -> InputMediaPhoto:
    if path.exists():
        return InputMediaPhoto(media=FSInputFile(path), caption=caption)
    return InputMediaPhoto(
        media=BufferedInputFile(placeholder, filename=filename),
        caption=caption,
    )


def main_page(config: Config, content: ContentService, username: str, balance: int, has_admin: bool) -> PageData:
    template = content.get_page_one()
    try:
        text = template.format(username=username, balance=balance)
    except KeyError:
        text = template
    media = _build_media(Path("assets/main.jpg"), PLACEHOLDER_MAIN, "main.jpg", text)
    return PageData(
        media=media,
        reply_markup=_build_base_keyboard(config, forward=True, has_admin=has_admin),
    )


def faq_page(config: Config, faq_text: str, has_admin: bool) -> PageData:
    media = _build_media(Path("assets/faq.jpg"), PLACEHOLDER_FAQ, "faq.jpg", faq_text)
    return PageData(
        media=media,
        reply_markup=_build_base_keyboard(config, forward=False, has_admin=has_admin),
    )


def download_keyboard(has_access: bool, url: str | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if has_access and url:
        builder.button(text="📥 Скачати", url=url)
    else:
        builder.button(text="📥 Скачати", callback_data="download:guide")
    return builder.as_markup()
