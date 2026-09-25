# ---------------------------------------------------------------------------------
#  /\_/\  🌐 This module was loaded through https://t.me/hikkamods_bot
# ( o.o )  🔐 Licensed under the GNU AGPLv3.
#  > ^ <   ⚠️ Owner of heta.hikariatama.ru doesn't take any responsibilities or intellectual property rights regarding this script
# ---------------------------------------------------------------------------------
# Name: lovemagic
# Author: hikariatama
# Commands:
# .ilyi | .ilygayi | .ily | .ilygay
# ---------------------------------------------------------------------------------

#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html
# Modified for Kage by gerdaroot (https://github.com/gerdaroot/kage-modules), 2026-09-25

# meta pic: https://static.dan.tatar/lovemagic_icon.png
# meta banner: https://mods.hikariatama.ru/badges/lovemagic.jpg
# meta developer: @hikarimods
# scope: inline
# scope: hikka_only
# scope: hikka_min 1.3.0

import asyncio

import aiohttp
from telethon.tl.types import Message

from .. import loader, utils
from ..inline.types import InlineCall

FRAME_URLS = {
    "classic": "https://gist.github.com/hikariatama/89d0246c72e5882e12af43be63f5bca5/raw/08a5df7255d5e925ab2ede1efc892d9dc93af8e1/ily_classic.json",
    "gay": "https://gist.github.com/hikariatama/3596a7c4f273a41e5289586ccff53a71/raw/f680c04f5855dcb02645b603d84d2496a8ea3350/ily_gay.json",
}
FINAL_TEXT_DELAY = 10


@loader.tds
class ILYMod(loader.Module):
    """Famous TikTok hearts animation implemented in Hikka w/o logspam"""

    strings = {
        "name": "LoveMagic",
        "message": "<b>❤️‍🔥 I want to tell you something...</b>\n<i>{}</i>",
        "frames_error": "🚫 <b>Could not download animation frames, try again later</b>",
    }

    strings_ru = {
        "message": "<b>❤️‍🔥 Я хочу тебе сказать кое-что...</b>\n<i>{}</i>",
        "frames_error": "🚫 <b>Не удалось загрузить кадры анимации, попробуй позже</b>",
        "_cls_doc": "Известная TikTok анимация сердечек без спама в логи и флудвейтов",
    }

    def __init__(self):
        self._frames: dict[str, list[str]] = {}

    async def _get_frames(self, kind: str) -> list[str] | None:
        if kind not in self._frames:
            try:
                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=20)
                ) as session:
                    async with session.get(FRAME_URLS[kind]) as resp:
                        resp.raise_for_status()
                        self._frames[kind] = await resp.json(content_type=None)
            except (aiohttp.ClientError, TimeoutError, ValueError):
                return None
        return self._frames[kind]

    async def _play(
        self,
        obj: InlineCall | Message,
        text: str,
        kind: str,
        inline: bool = False,
    ):
        frames = await self._get_frames(kind)
        if frames is None:
            await utils.answer(obj, self.strings("frames_error"))
            return

        words = text.split()
        obj = await self.animate(
            obj,
            frames + [f"<b>{' '.join(words[: i + 1])}</b>" for i in range(len(words))],
            interval=0.5,
            inline=inline,
        )

        if isinstance(obj, Message):
            return

        await asyncio.sleep(FINAL_TEXT_DELAY)
        await obj.edit(
            f"<b>{text}</b>",
            reply_markup={
                "text": "💔 Хочу также!",
                "url": "https://t.me/hikka_talks",
            },
        )
        await obj.unload()

    async def _send_form(self, message: Message, text: str, kind: str):
        await self.inline.form(
            self.strings("message").format("*" * len(text)),
            reply_markup={
                "text": "🧸 Open",
                "callback": self._play,
                "args": (text, kind),
                "kwargs": {"inline": True},
            },
            message=message,
            disable_security=True,
        )

    @loader.command(ru_doc="Отправить анимацию сердец в инлайне")
    async def ilyicmd(self, message: Message):
        """Send inline message with animated hearts"""
        text = utils.get_args_raw(message) or "I ❤️ you!"
        await self._send_form(message, text, "classic")

    @loader.command(ru_doc="Отправить анимацию сердец")
    async def ily(self, message: Message):
        """Send message with animated hearts"""
        await self._play(message, utils.get_args_raw(message) or "I ❤️ you!", "classic")

    @loader.command(ru_doc="Отправить гейскую анимацию сердец в инлайне")
    async def ilygayicmd(self, message: Message):
        """Send inline message with animated hearts (gay)"""
        text = utils.get_args_raw(message) or "I am gay and I 💙 you!"
        await self._send_form(message, text, "gay")

    @loader.command(ru_doc="Отправить гейскую анимацию сердец")
    async def ilygay(self, message: Message):
        """Send message with animated hearts (gay)"""
        await self._play(
            message, utils.get_args_raw(message) or "I am gay and I 💙 you!", "gay"
        )
