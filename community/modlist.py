# ---------------------------------------------------------------------------------
#░█▀▄░▄▀▀▄░█▀▄░█▀▀▄░█▀▀▄░█▀▀▀░▄▀▀▄░░░█▀▄▀█
#░█░░░█░░█░█░█░█▄▄▀░█▄▄█░█░▀▄░█░░█░░░█░▀░█
#░▀▀▀░░▀▀░░▀▀░░▀░▀▀░▀░░▀░▀▀▀▀░░▀▀░░░░▀░░▒▀
# Name: ModulesList.
# Description: Channels of modules for userbot Hikka.
# Author: @codrago
# ---------------------------------------------------------------------------------

# 🔒    Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html
# Modified for Kage by gerdaroot (https://github.com/gerdaroot/kage-modules), 2026-09-25

# meta developer: @codrago_m
# meta banner: https://raw.githubusercontent.com/coddrago/modules/refs/heads/main/banner.png
# meta pic: https://envs.sh/HJH.webp
# scope: heroku_min 2.0.0
# ---------------------------------------------------------------------------------

import re
import time

import aiohttp
from telethon.types import Message

from .. import loader, utils

REPLY_COOLDOWN = 3.5
EMOJI_TAG = re.compile(r"<emoji document_id=(\d+)>(.*?)</emoji>")


def render_emoji(raw: str) -> str:
    """Rebuilds a custom emoji tag from the remote list so no other HTML gets through."""
    if match := EMOJI_TAG.fullmatch(raw.strip()):
        return f"<emoji document_id={match[1]}>{utils.escape_html(match[2])}</emoji>"
    return utils.escape_html(raw)


@loader.tds
class ModulesList(loader.Module):
    """Модуль для быстрого доступа к каналам с модулями"""

    strings = {
        "name": "ModList",
        "added": "Chat <code>{}</code> added",
        "chat_added": "Chat already added!",
        "fetch_error": "Failed to load the modules list",
        "officialChannels": (
            "<emoji document_id=5188377234380954537>🌘</emoji> Community-made modules\n"
            "\n<emoji document_id=5445096582238181549>🦋</emoji> <b>@morisummermods</b>"
            "\n<emoji document_id=5449380056201697322>💚</emoji> <b>@nalinormods</b>"
            "\n<emoji document_id=5373026167722876724>🤩</emoji> <b>@AstroModules</b>"
            "\n<emoji document_id=5249042457731024510>💪</emoji> <b>@vsecoder_m</b>"
            "\n<emoji document_id=5371037748188683677>☺️</emoji> <b>@mm_mods</b>"
            "\n<emoji document_id=5370856741086960948>😈</emoji> <b>@apodiktum_modules</b>"
            "\n<emoji document_id=5370947515220761242>😇</emoji> <b>@wilsonmods</b>"
            "\n<emoji document_id=5467406098367521267>👑</emoji> <b>@DorotoroMods</b>"
            "\n<emoji document_id=5469986291380657759>✌️</emoji> <b>@HikkaFTGmods</b>"
            "\n<emoji document_id=5472091323571903308>🎈</emoji> <b>@nercymods</b>"
            "\n<emoji document_id=5298799263013151249>😐</emoji> <b>@sqlmerr_m</b>"
            "\n<emoji document_id=5231165412275668380>🥰</emoji> <b>@AuroraModules</b>"
            "\n<emoji document_id=5418360054338314186>📢</emoji> <b>@codrago_m</b>"
        ),
    }
    strings_ru = {
        "name": "ModList",
        "added": "Чат <code>{}</code> добавлен",
        "chat_added": "Чат уже добавлен!",
        "fetch_error": "Не удалось загрузить список модулей",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "ids",
                [],
                lambda: "айди где будет работать заметка BOT API ID REQUIRED",
                validator=loader.validators.Series(loader.validators.TelegramID()),
            ),
            loader.ConfigValue(
                "linktodata",
                "https://github.com/coddrago/modules/raw/main/modules.json",
                lambda: "link for modules",
                validator=loader.validators.Link(),
            ),
        )
        self._reply_cooldowns: dict[int, float] = {}

    async def get_data(self, *sections: str) -> list[str]:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
            async with session.get(self.config["linktodata"]) as response:
                response.raise_for_status()
                data = await response.json(content_type=None)

        return [
            f"{render_emoji(emoji)} <b>@{utils.escape_html(username)}</b>"
            for section in sections
            for username, emoji in data[section].items()
        ]

    async def _answer_list(self, message: Message, *sections: str):
        try:
            developers = await self.get_data(*sections)
        except Exception:
            await utils.answer(message, self.strings["fetch_error"])
            return

        await utils.answer(message, "\n".join(developers))

    @loader.watcher()
    async def watcher_modules(self, message: Message):
        chat_id = utils.get_chat_id(message)
        if message.raw_text != "#modules" or chat_id not in self.config["ids"]:
            return

        # Per chat, not per sender: several people spamming the hashtag must not flood from the owner's account.
        now = time.monotonic()
        if self._reply_cooldowns.get(chat_id, 0) > now:
            return

        self._reply_cooldowns[chat_id] = now + REPLY_COOLDOWN
        await message.reply(self.strings["officialChannels"])

    @loader.command(alias="mlist", ru_doc=" | Быстрый доступ к каналам с модулями ")
    async def modlist(self, message: Message):
        """ | Quick access to channels with modules"""
        await self._answer_list(message, "official", "unofficial")

    @loader.command(alias="offmlist", ru_doc=" | Оффициальные каналы с модулями ")
    async def offmodlist(self, message: Message):
        """ | Official channel with modules"""
        await self._answer_list(message, "official")

    @loader.command(ru_doc="[BOT API ID] | Добавить чат")
    async def addmchat(self, message: Message):
        """[BOT API ID] | add chat"""
        chat_id = utils.get_chat_id(message)
        if chat_id in self.config["ids"]:
            await utils.answer(message, self.strings["chat_added"])
            return

        self.config["ids"] = [*self.config["ids"], chat_id]
        await utils.answer(message, self.strings["added"].format(chat_id))
