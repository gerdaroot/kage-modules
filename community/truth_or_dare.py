# ---------------------------------------------------------------------------------
#  /\_/\  🌐 This module was loaded through https://t.me/hikkamods_bot
# ( o.o )  🔐 Licensed under the GNU AGPLv3.
#  > ^ <   ⚠️ Owner of heta.hikariatama.ru doesn't take any responsibilities or intellectual property rights regarding this script
# ---------------------------------------------------------------------------------
# Name: truth_or_dare
# Author: hikariatama
# Commands:
# .tod | .todlang
# ---------------------------------------------------------------------------------

__version__ = (2, 0, 1)

#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html
# Modified for Kage by gerdaroot (https://github.com/gerdaroot/kage-modules), 2026-09-25

# meta pic: https://static.dan.tatar/truth_or_date_icon.py
# meta banner: https://mods.hikariatama.ru/badges/truth_or_dare.jpg
# meta developer: @hikarimods
# scope: inline
# scope: hikka_only
# scope: hikka_min 1.2.10

import random

import aiohttp
from telethon.tl.types import Message

from .. import loader, utils
from ..inline.types import InlineCall

API_URL = "https://api.truthordarebot.xyz/v1/{}"
CATEGORY_RATINGS = {
    "classic": ("pg",),
    "kids": ("pg",),
    "party": ("pg13",),
    "hot": ("r",),
    "mixed": ("pg", "pg13", "r"),
}
LANGUAGES = {"ru", "en"}


@loader.tds
class TruthOrDareMod(loader.Module):
    """Truth or dare? Play your favorite game from inside the Telegram (en/ru)"""

    strings = {
        "name": "TruthOrDare",
        "choose_language": "👩‍🎤 <b>Choose language</b>",
        "truth_or_dare_ru": "🔴 <b>Правда</b> или <b>Действие</b>? 🔵",
        "truth_or_dare_en": "🔴 <b>Truth</b> or <b>Dare</b>? 🔵",
        "truth_ru": "🤵‍♀️ Правда",
        "dare_ru": "🥷 Действие",
        "truth_en": "🤵‍♀️ Truth",
        "dare_en": "🥷 Dare",
        "language_saved_ru": "🇷🇺 Язык сохранен",
        "language_saved_en": "🇬🇧 Language saved",
        "classic_ru": "🙂 Классика",
        "classic_en": "🙂 Classic",
        "kids_ru": "👨‍👦 Для детей",
        "kids_en": "👨‍👦 Kids",
        "party_ru": "🥳 Вечеринка",
        "party_en": "🥳 Party",
        "hot_ru": "❤️‍🔥 Горячее",
        "hot_en": "❤️‍🔥 Hot",
        "mixed_ru": "🔀 Разное",
        "mixed_en": "🔀 Mixed",
        "category_ru": "😇 <b>Выбери категорию игры:</b>",
        "category_en": "😇 <b>Choose game category:</b>",
        "args": "▫️ <code>.todlang en/ru</code>",
        "api_error": "🚫 <b>Truth or Dare API is unavailable, try again later</b>",
    }

    async def client_ready(self):
        if self.get("lang") in LANGUAGES:
            self._update_lang()

    def _lang_string(self, key: str) -> str:
        return self.strings(f"{key}_{self.get('lang')}")

    async def truth_or_dare(self, tod: str, category: str) -> str:
        # The API has no Russian pack, so questions are always in English.
        rating = random.choice(CATEGORY_RATINGS[category])
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=15)
            ) as session:
                async with session.get(
                    API_URL.format(tod), params={"rating": rating}
                ) as resp:
                    resp.raise_for_status()
                    question = (await resp.json())["question"]
        except (aiohttp.ClientError, TimeoutError, KeyError, ValueError):
            return self.strings("api_error")

        return utils.escape_html(question)

    async def _format_question(self, action: str, category: str) -> str:
        question = await self.truth_or_dare(action, category)
        return f"<b>{self._lang_string(action)}</b>:\n\n{question}"

    def _update_lang(self):
        def button(category: str) -> dict:
            return {
                "text": self._lang_string(category),
                "callback": self._inline_start,
                "args": (category,),
            }

        self._markup = [
            [button("classic"), button("kids")],
            [button("party"), button("hot")],
            [button("mixed")],
        ]

    def _action_markup(self, category: str) -> list:
        return [
            {
                "text": self._lang_string(action),
                "callback": self._inline_process,
                "args": (action, category),
            }
            for action in ("truth", "dare")
        ]

    async def _ask_language(self, message: Message):
        await self.inline.form(
            self.strings("choose_language"),
            message=message,
            reply_markup=[
                {
                    "text": "🇷🇺 Русский",
                    "callback": self._inline_set_language,
                    "args": ("ru",),
                },
                {
                    "text": "🇬🇧 English",
                    "callback": self._inline_set_language,
                    "args": ("en",),
                },
            ],
        )

    async def _inline_set_language(self, call: InlineCall, lang: str):
        self.set("lang", lang)
        await call.answer(self.strings(f"language_saved_{lang}"), show_alert=True)
        self._update_lang()
        await call.edit(self._lang_string("truth_or_dare"), reply_markup=self._markup)

    async def _inline_process(self, call: InlineCall, action: str, category: str):
        await call.edit(
            await self._format_question(action, category),
            reply_markup=self._action_markup(category),
        )

    async def _inline_start(self, call: InlineCall, category: str):
        await call.edit(
            self._lang_string("truth_or_dare"),
            reply_markup=self._action_markup(category),
        )

    async def todcmd(self, message: Message):
        """Get truth or dare"""
        if not self.get("lang"):
            await self._ask_language(message)
            return

        category = utils.get_args_raw(message).lower()
        if category not in CATEGORY_RATINGS:
            category = "mixed"

        action = random.choice(("truth", "dare"))
        await utils.answer(message, await self._format_question(action, category))

    async def todicmd(self, message: Message):
        """Start new truth or dare game"""
        if not self.get("lang"):
            await self._ask_language(message)
            return

        await self.inline.form(
            self._lang_string("category"),
            message=message,
            reply_markup=self._markup,
            disable_security=True,
        )

    async def todlangcmd(self, message: Message):
        """[en/ru] - Change language"""
        args = utils.get_args_raw(message).lower().strip()
        if args not in LANGUAGES:
            await utils.answer(message, self.strings("args"))
            return

        self.set("lang", args)
        self._update_lang()
        await utils.answer(message, f"<b>{self.strings(f'language_saved_{args}')}</b>")
