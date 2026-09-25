# ---------------------------------------------------------------------------------
#  /\_/\  🌐 This module was loaded through https://t.me/hikkamods_bot
# ( o.o )  🔐 Licensed under the GNU AGPLv3.
#  > ^ <   ⚠️ Owner of heta.hikariatama.ru doesn't take any responsibilities or intellectual property rights regarding this script
# ---------------------------------------------------------------------------------
# Name: web2file
# Description: Download content from link and send it as file
# Author: hikariatama
# Commands:
# .web2file
# ---------------------------------------------------------------------------------


#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html
# Modified for Kage by gerdaroot (https://github.com/gerdaroot/kage-modules), 2026-09-25

# scope: hikka_min 1.2.10
# scope: heroku_min 2.0.0

# meta pic: https://img.icons8.com/fluency/240/000000/archive.png
# meta banner: https://mods.hikariatama.ru/badges/web2file.jpg
# meta developer: @hikarimods

import io
from urllib.parse import unquote, urlsplit

import aiohttp
from telethon.tl.types import Message

from .. import loader, utils

MAX_FILE_SIZE = 512 * 1024 * 1024
DOWNLOAD_TIMEOUT = aiohttp.ClientTimeout(total=300)


async def fetch(url: str) -> bytes:
    async with aiohttp.ClientSession(timeout=DOWNLOAD_TIMEOUT) as session:
        async with session.get(url) as response:
            response.raise_for_status()
            data = bytearray()
            async for chunk in response.content.iter_chunked(64 * 1024):
                data += chunk
                if len(data) > MAX_FILE_SIZE:
                    raise ValueError("File is too large")
            return bytes(data)


@loader.tds
class Web2fileMod(loader.Module):
    """Download content from link and send it as file"""

    strings = {
        "name": "Web2file",
        "no_args": "🚫 <b>Specify link</b>",
        "fetch_error": "🚫 <b>Download error</b>",
        "loading": "🦊 <b>Downloading...</b>",
    }

    strings_ru = {
        "no_args": "🚫 <b>Укажи ссылку</b>",
        "fetch_error": "🚫 <b>Ошибка загрузки</b>",
        "loading": "🦊 <b>Загрузка...</b>",
        "_cls_doc": "Скачивает содержимое ссылки и отправляет в виде файла",
    }

    async def web2filecmd(self, message: Message):
        """Send link content as file"""
        website = utils.get_args_raw(message).strip()
        if not website:
            await utils.answer(message, self.strings("no_args", message))
            return

        if "://" not in website:
            website = f"https://{website}"

        message = await utils.answer(message, self.strings("loading", message))
        try:
            f = io.BytesIO(await fetch(website))
        except Exception:
            await utils.answer(message, self.strings("fetch_error", message))
            return

        f.name = unquote(urlsplit(website).path.rstrip("/").split("/")[-1]) or "file"

        await message.respond(file=f)
        await message.delete()
