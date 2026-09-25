# ---------------------------------------------------------------------------------
#  /\_/\  🌐 This module was loaded through https://t.me/hikkamods_bot
# ( o.o )  🔐 Licensed under the GNU AGPLv3.
#  > ^ <   ⚠️ Owner of heta.hikariatama.ru doesn't take any responsibilities or intellectual property rights regarding this script
# ---------------------------------------------------------------------------------
# Name: uploader
# Author: hikariatama
# Commands:
# .skynet | .imgur | .oxo
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

# meta pic: https://static.dan.tatar/uploader_icon.png
# meta banner: https://mods.hikariatama.ru/badges/uploader.jpg
# meta developer: @hikarimods
# scope: hikka_only
# scope: hikka_min 1.2.10

import io
import re

import aiohttp
from PIL import Image, UnidentifiedImageError
from telethon.errors.rpcerrorlist import YouBlockedUserError
from telethon.tl.types import Message

from .. import loader, utils

IMAGE_FORMATS = {"GIF", "PNG", "JPEG", "TIFF", "BMP"}
# 0x0.st blocks clients that pose as browsers and asks for a unique user agent
OXO_HEADERS = {"User-Agent": "Kage-Uploader/2.1 (+https://github.com/gerdaroot/kage-modules)"}
HTTP_TIMEOUT = aiohttp.ClientTimeout(total=120)
IMGUR_PAGE_RE = re.compile(r"https://(?:i\.)?imgur\.com/\S+$")


def is_image(file: io.BytesIO) -> bool:
    try:
        with Image.open(file) as image:
            return image.format in IMAGE_FORMATS
    except UnidentifiedImageError:
        return False
    finally:
        file.seek(0)


@loader.tds
class FileUploaderMod(loader.Module):
    """Different engines file uploader"""

    strings = {
        "name": "Uploader",
        "uploading": "🚀 <b>Uploading...</b>",
        "noargs": "🚫 <b>No file specified</b>",
        "err": "🚫 <b>Upload error</b>",
        "uploaded": '🎡 <b>File <a href="{0}">uploaded</a></b>!\n\n<code>{0}</code>',
        "imgur_blocked": "🚫 <b>Unban @ImgUploadBot</b>",
        "not_an_image": "🚫 <b>This platform only supports images</b>",
    }

    strings_ru = {
        "uploading": "🚀 <b>Загрузка...</b>",
        "noargs": "🚫 <b>Файл не указан</b>",
        "err": "🚫 <b>Ошибка загрузки</b>",
        "uploaded": '🎡 <b>Файл <a href="{0}">загружен</a></b>!\n\n<code>{0}</code>',
        "imgur_blocked": "🚫 <b>Разблокируй @ImgUploadBot</b>",
        "not_an_image": "🚫 <b>Эта платформа поддерживает только изображения</b>",
        "_cmd_doc_imgur": "Загрузить на imgur.com",
        "_cmd_doc_oxo": "Загрузить на 0x0.st (публичный хостинг, файлы видны всем по ссылке)",
        "_cls_doc": "Загружает файлы на различные хостинги",
    }

    async def get_media(self, message: Message):
        reply = await message.get_reply_message()
        m = None
        if reply and reply.media:
            m = reply
        elif message.media:
            m = message
        elif not reply:
            await utils.answer(message, self.strings("noargs"))
            return False

        if not m:
            file = io.BytesIO(bytes(reply.raw_text, "utf-8"))
            file.name = "file.txt"
        else:
            file = io.BytesIO(await self._client.download_media(m, bytes))
            file.name = m.file.name or utils.rand(16) + (m.file.ext or "")

        return file

    async def get_image(self, message: Message):
        file = await self.get_media(message)
        if not file:
            return False

        if not is_image(file):
            await utils.answer(message, self.strings("not_an_image"))
            return False

        return file

    async def imgurcmd(self, message: Message):
        """Upload to imgur.com"""
        message = await utils.answer(message, self.strings("uploading"))
        file = await self.get_image(message)
        if not file:
            return

        chat = "@ImgUploadBot"

        async with self._client.conversation(chat) as conv:
            try:
                m = await conv.send_message(file=file)
                response = await conv.get_response()
            except YouBlockedUserError:
                await utils.answer(message, self.strings("imgur_blocked"))
                return

            await m.delete()
            await response.delete()

        url = await self._direct_imgur_link(response.raw_text)
        await utils.answer(
            message, self.strings("uploaded").format(utils.escape_html(url))
        )

    @staticmethod
    async def _direct_imgur_link(page_url: str) -> str:
        """Resolve the imgur page the bot returns to the direct image URL."""
        if not IMGUR_PAGE_RE.match(page_url):
            return page_url

        try:
            async with aiohttp.ClientSession(timeout=HTTP_TIMEOUT) as session:
                async with session.get(page_url) as response:
                    page = await response.text()
        except (aiohttp.ClientError, TimeoutError, ValueError):
            return page_url

        match = re.search(r'<meta property="og:image"[^>]*content="(.*?)"', page)
        return match[1].split("?")[0] if match else page_url

    async def oxocmd(self, message: Message):
        """Upload to 0x0.st (public host, anyone with the link can see the file)"""
        message = await utils.answer(message, self.strings("uploading"))
        file = await self.get_media(message)
        if not file:
            return

        form = aiohttp.FormData()
        form.add_field("file", file, filename=file.name)
        form.add_field("secret", "")
        try:
            async with aiohttp.ClientSession(
                timeout=HTTP_TIMEOUT, headers=OXO_HEADERS
            ) as session:
                async with session.post("https://0x0.st", data=form) as response:
                    response.raise_for_status()
                    url = (await response.text()).strip()
        except (aiohttp.ClientError, TimeoutError):
            await utils.answer(message, self.strings("err"))
            return

        await utils.answer(
            message, self.strings("uploaded").format(utils.escape_html(url))
        )
