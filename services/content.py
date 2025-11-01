from __future__ import annotations

from pathlib import Path

from services.files import read_json, write_json

DEFAULT_PAGE_ONE = (
    "✨ Ласкаво просимо, {username}!\n"
    "Поточний баланс зірок - {balance} ⭐️\n"
    "Наше керівництво завжди свіже, корисне та потужне!\n\n"
    "Думайте про це як свій шлях до успіху.\n\n"
    "➡️Друга сторінка з FAQ 📚\n\n"
    "⚡️Дуже швидка, зручна а головне - безпечна оплата!\n\n"
    "Не чекайте, просто почніть трансформуватись зараз! 🚀"
)

DEFAULT_FAQ = (
    "📚 FAQ\n\n"
    "1. Що входить у гайд? — Найактуальніші методики та стратегії.\n"
    "2. Коли я отримаю доступ? — Відразу після оплати.\n"
    "3. Як завантажити гайд? — Натисніть «📥 Скачати» у повідомленні після оплати.\n"
    "4. Чи є гарантії? — Ми постійно оновлюємо гайд і підтримуємо покупців.\n"
)


class ContentService:
    def __init__(self, path: Path) -> None:
        self.path = path

    def get_page_one(self) -> str:
        data = read_json(self.path, default={})
        return data.get("page_one", DEFAULT_PAGE_ONE)

    def get_faq(self) -> str:
        data = read_json(self.path, default={})
        return data.get("faq", DEFAULT_FAQ)

    def update_page_one(self, text: str) -> None:
        data = read_json(self.path, default={})
        data["page_one"] = text
        write_json(self.path, data)

    def update_faq(self, text: str) -> None:
        data = read_json(self.path, default={})
        data["faq"] = text
        write_json(self.path, data)
