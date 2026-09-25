# ---------------------------------------------------------------------------------
#  /\_/\  🌐 This module was loaded through https://t.me/hikkamods_bot
# ( o.o )  🔐 Licensed under the GNU AGPLv3.
#  > ^ <   ⚠️ Owner of heta.hikariatama.ru doesn't take any responsibilities or intellectual property rights regarding this script
# ---------------------------------------------------------------------------------
# Name: img2pdf
# Author: hikariatama
# Commands:
# .img2pdf
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

# meta pic: https://img.icons8.com/stickers/500/000000/pdf.png
# meta banner: https://mods.hikariatama.ru/badges/img2pdf.jpg
# meta developer: @hikarimods
# requires: Pillow

import asyncio
import io

from PIL import Image, UnidentifiedImageError
from telethon.tl.types import Message

from .. import loader, utils


def is_image(message: Message) -> bool:
    return bool(
        message.photo
        or (message.document and (message.file.mime_type or "").startswith("image/"))
    )


def open_image(data: bytes) -> Image.Image | None:
    try:
        image = Image.open(io.BytesIO(data))
        # PDF pages can't carry alpha or palette modes
        return image.convert("RGB")
    except UnidentifiedImageError:
        return None


def pack_pdf(images: list[Image.Image]) -> bytes:
    file = io.BytesIO()
    images[0].save(
        file,
        "PDF",
        resolution=100.0,
        save_all=True,
        append_images=images[1:],
    )
    return file.getvalue()


@loader.tds
class Img2PdfMod(loader.Module):
    """Packs images to pdf"""

    strings = {
        "name": "Img2Pdf",
        "no_file": "🚫 <b>Send or reply to a series of images</b>",
        "processing": (
            "<emoji document_id=5307865634032329170>🫥</emoji> <b>Processing"
            " files...</b>"
        ),
    }
    strings_ru = {
        "processing": (
            "<emoji document_id=5307865634032329170>🫥</emoji> <b>Обрабатываю"
            " файлы...</b>"
        ),
        "no_file": "🚫 <b>Отправь изображения или ответь на серию изображений</b>",
    }
    strings_es = {
        "processing": (
            "<emoji document_id=5307865634032329170>🫥</emoji> <b>Procesando"
            " archivos...</b>"
        )
    }
    strings_de = {
        "processing": (
            "<emoji document_id=5307865634032329170>🫥</emoji> <b>Dateien werden"
            " verarbeitet...</b>"
        )
    }
    strings_tr = {
        "processing": (
            "<emoji document_id=5307865634032329170>🫥</emoji> <b>Dosyalar"
            " işleniyor...</b>"
        )
    }

    async def img2pdfcmd(self, message: Message):
        """<filename | optional> - Pack images into pdf"""
        reply = await message.get_reply_message()
        start = message if is_image(message) else reply
        if not start or not is_image(start):
            await utils.answer(message, self.strings("no_file"))
            return

        filename = utils.get_args_raw(message) or "packed_images"
        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"

        message = await utils.answer(message, self.strings("processing"))

        images = []
        async for ms in self._client.iter_messages(
            message.peer_id, offset_id=start.id - 1, reverse=True
        ):
            if not is_image(ms):
                break
            image = await asyncio.to_thread(
                open_image, await self._client.download_media(ms, bytes)
            )
            if image is None:
                break
            images.append(image)

        if not images:
            await utils.answer(message, self.strings("no_file"))
            return

        file = io.BytesIO(await asyncio.to_thread(pack_pdf, images))
        file.name = filename
        await self._client.send_file(message.peer_id, file)
        await message.delete()
