# ---------------------------------------------------------------------------------
# ░█▀▄░▄▀▀▄░█▀▄░█▀▀▄░█▀▀▄░█▀▀▀░▄▀▀▄░░░█▀▄▀█
# ░█░░░█░░█░█░█░█▄▄▀░█▄▄█░█░▀▄░█░░█░░░█░▀░█
# ░▀▀▀░░▀▀░░▀▀░░▀░▀▀░▀░░▀░▀▀▀▀░░▀▀░░░░▀░░▒▀
# Name: StickerToEmoji
# Description: Convert static, TGS animated, and WEBM video stickers/packs into custom Telegram emoji packs directly via Telegram API
# Author: @codrago_m
# ---------------------------------------------------------------------------------
# 🔒    Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html
# Modified for Kage by gerdaroot (https://github.com/gerdaroot/kage-modules), 2026-09-25
# ---------------------------------------------------------------------------------
# Commands: s2e, s1e
# scope: heroku_only
# scope: ffmpeg
# scope: heroku_min 2.0.0
# meta developer: @codrago_m
# meta banner: https://raw.githubusercontent.com/coddrago/modules/refs/heads/main/banner.png
# requires: pillow
# ---------------------------------------------------------------------------------

import asyncio
import contextlib
import io
import os
import random
import re
import shutil
import string
import tempfile

from PIL import Image
from telethon.errors import FloodWaitError
from telethon.tl import functions
from telethon.tl.functions.messages import GetStickerSetRequest, UploadMediaRequest
from telethon.tl.types import (
    DocumentAttributeCustomEmoji,
    DocumentAttributeFilename,
    DocumentAttributeImageSize,
    DocumentAttributeSticker,
    DocumentAttributeVideo,
    InputDocument,
    InputMediaUploadedDocument,
    InputPeerSelf,
    InputStickerSetEmpty,
    InputStickerSetID,
    InputStickerSetItem,
    InputStickerSetShortName,
    InputUserSelf,
    Message,
)

from .. import loader, utils

MAX_EMOJI_VIDEO_SIZE = 63 * 1024
MAX_PACK_SIZE = 200
PARALLEL_CONVERSIONS = 4
UPLOAD_ATTEMPTS = 3
PROGRESS_EDIT_INTERVAL = 2.0

KIND_BY_MIME = {
    "application/x-tgsticker": "animated",
    "video/webm": "video",
    "video/mp4": "video",
    "image/webp": "static",
    "image/png": "static",
    "image/jpeg": "static",
}
UPLOAD_FORMAT = {
    "animated": ("application/x-tgsticker", "emoji.tgs"),
    "video": ("video/webm", "emoji.webm"),
    "static": ("image/webp", "emoji.webp"),
}


def doc_kind(doc) -> str | None:
    return KIND_BY_MIME.get(doc.mime_type or "")


def pack_kind_label(docs: list) -> str:
    kinds = {doc_kind(doc) for doc in docs}
    return kinds.pop() if len(kinds) == 1 else "mixed"


@loader.tds
class StickerToEmojiMod(loader.Module):
    """Converts stickers and sticker packs (static, TGS, and WEBM) into custom Telegram emoji packs via Telegram API."""

    strings = {
        "name": "StickerToEmoji",
        "no_args": (
            "<tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> "
            "Reply to a sticker or provide a sticker pack link/shortname."
        ),
        "no_reply": (
            "<tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> "
            "Reply to a sticker to convert it into an emoji pack."
        ),
        "fetch_err": (
            "<tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> "
            "Failed to fetch sticker pack: <code>{}</code>"
        ),
        "empty_pack": (
            "<tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> "
            "Sticker pack is empty."
        ),
        "no_stickers": (
            "<tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> "
            "No suitable stickers of type <code>{}</code> found."
        ),
        "unsupported": (
            "<tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> "
            "Unsupported sticker format."
        ),
        "no_ffmpeg": (
            "<tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> "
            "FFmpeg is required on the server to convert video stickers (.webm)."
        ),
        "loading": (
            "<tg-emoji emoji-id=4911656069207426158>💘</tg-emoji> "
            "<i>Fetching sticker info...</i>"
        ),
        "processing": (
            "<tg-emoji emoji-id=4911656069207426158>💘</tg-emoji> "
            "Creating <b>{}</b> emojis «<b>{}</b>»\n"
            "<b>Progress:</b> <code>{}/{}</code>"
        ),
        "success": (
            "<tg-emoji emoji-id=4911656069207426158>💘</tg-emoji> "
            "Emoji pack successfully created!\n\n"
            "<b>Title:</b> <code>{}</code>\n"
            "<b>Type:</b> <code>{}</code>\n"
            "<b>Link:</b> <a href='{}'>Add Emoji Pack</a>"
        ),
        "btn_add": "Add Pack",
        "error": (
            "<tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> "
            "Error: <code>{}</code>"
        ),
    }

    strings_ru = {
        "no_args": (
            "<tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> "
            "Ответьте на стикер или укажите ссылку/шортнейм пака."
        ),
        "no_reply": (
            "<tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> "
            "Ответьте на стикер, чтобы превратить его в эмодзи-пак."
        ),
        "fetch_err": (
            "<tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> "
            "Не удалось найти стикерпак: <code>{}</code>"
        ),
        "empty_pack": (
            "<tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> "
            "Стикерпак пуст."
        ),
        "no_stickers": (
            "<tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> "
            "Не найдено подходящих стикеров типа <code>{}</code>."
        ),
        "unsupported": (
            "<tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> "
            "Неподдерживаемый формат стикера."
        ),
        "no_ffmpeg": (
            "<tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> "
            "Для конвертации видео-стикеров (.webm) необходим FFmpeg на сервере."
        ),
        "loading": (
            "<tg-emoji emoji-id=4911656069207426158>💘</tg-emoji> "
            "<i>Получаю информацию о стикере...</i>"
        ),
        "processing": (
            "<tg-emoji emoji-id=4911656069207426158>💘</tg-emoji> "
            "Создаю <b>{}</b> эмодзи «<b>{}</b>»\n"
            "<b>Прогресс:</b> <code>{}/{}</code>"
        ),
        "success": (
            "<tg-emoji emoji-id=4911656069207426158>💘</tg-emoji> "
            "Эмодзи-пак успешно создан!\n\n"
            "<b>Название:</b> <code>{}</code>\n"
            "<b>Тип:</b> <code>{}</code>\n"
            "<b>Ссылка:</b> <a href='{}'>Добавить эмодзи</a>"
        ),
        "btn_add": "Добавить пак",
        "error": (
            "<tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> "
            "Ошибка: <code>{}</code>"
        ),
    }

    @staticmethod
    def _clean_short_name(raw_name: str) -> str:
        name = re.sub(r"_by_.*$", "", raw_name, flags=re.IGNORECASE)
        name = re.sub(r"[^a-zA-Z0-9_]", "", name)
        name = re.sub(r"_+", "_", name).strip("_")
        name = name[:16].rstrip("_")
        return name or "pack"

    @staticmethod
    async def _edit(form, text: str, reply_markup=None):
        with contextlib.suppress(Exception):
            await form.edit(text=text, reply_markup=reply_markup)

    def _error_text(self, exc: Exception) -> str:
        return self.strings("error").format(utils.escape_html(str(exc)))

    @staticmethod
    def _sticker_set_of(reply) -> InputStickerSetShortName | InputStickerSetID | None:
        if not reply or not reply.document:
            return None
        for attr in reply.document.attributes:
            if isinstance(attr, DocumentAttributeSticker) and isinstance(
                attr.stickerset, (InputStickerSetShortName, InputStickerSetID)
            ):
                return attr.stickerset
        return None

    @loader.command(
        ru_doc="<пак / реплай> — конвертировать стикерпак в Premium Emoji через API",
        en_doc="<pack / reply> — convert sticker pack into Premium Emoji via API",
    )
    async def s2ecmd(self, message: Message):
        args = utils.get_args_raw(message).strip()
        sticker_set = self._sticker_set_of(await message.get_reply_message())
        if not sticker_set and args:
            sticker_set = InputStickerSetShortName(short_name=args.split("/")[-1])

        if not sticker_set:
            await self.inline.form(text=self.strings("no_args"), message=message, silent=True)
            return

        form = await self.inline.form(text=self.strings("loading"), message=message, silent=True)

        try:
            full_set = await message.client(GetStickerSetRequest(stickerset=sticker_set, hash=0))
        except Exception as exc:
            await self._edit(form, self.strings("fetch_err").format(utils.escape_html(str(exc))))
            return

        if not full_set.documents:
            await self._edit(form, self.strings("empty_pack"))
            return

        # Sticker sets can mix static, animated and video stickers, so every document is typed on its own.
        docs = [doc for doc in full_set.documents if doc_kind(doc)][:MAX_PACK_SIZE]
        if not docs:
            await self._edit(form, self.strings("no_stickers").format("any"))
            return

        if any(doc_kind(doc) == "video" for doc in docs) and not shutil.which("ffmpeg"):
            await self._edit(form, self.strings("no_ffmpeg"))
            return

        await self._create_pack(
            message=message,
            form=form,
            docs=docs,
            title=f"{full_set.set.title[:50]} Emojis",
            clean_name=self._clean_short_name(full_set.set.short_name or "pack"),
        )

    @loader.command(
        ru_doc="<реплай на стикер> [название] — конвертировать стикер в отдельный эмодзи-пак через API",
        en_doc="<reply to sticker> [title] — convert single sticker into an emoji pack via API",
    )
    async def s1ecmd(self, message: Message):
        reply = await message.get_reply_message()
        if not reply or not reply.document:
            await self.inline.form(text=self.strings("no_reply"), message=message, silent=True)
            return

        doc = reply.document
        kind = doc_kind(doc)
        if not kind:
            await self.inline.form(text=self.strings("unsupported"), message=message, silent=True)
            return

        form = await self.inline.form(text=self.strings("loading"), message=message, silent=True)

        if kind == "video" and not shutil.which("ffmpeg"):
            await self._edit(form, self.strings("no_ffmpeg"))
            return

        args = utils.get_args_raw(message).strip()
        rnd_hash = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))

        await self._create_pack(
            message=message,
            form=form,
            docs=[doc],
            title=args[:50] if args else f"Emoji {rnd_hash.upper()}",
            clean_name=f"s_{rnd_hash}",
        )

    async def _prepare_file(self, client, doc) -> io.BytesIO:
        raw = await client.download_media(doc, bytes)
        kind = doc_kind(doc)
        if kind == "video":
            return await self._resize_video(raw)
        if kind == "static":
            return await asyncio.to_thread(self._resize_static, raw)

        file_obj = io.BytesIO(raw)
        file_obj.name = "emoji.tgs"
        return file_obj

    async def _convert_one(self, client, doc) -> InputStickerSetItem | None:
        emoji = next(
            (
                attr.alt
                for attr in doc.attributes
                if isinstance(attr, (DocumentAttributeSticker, DocumentAttributeCustomEmoji))
                and getattr(attr, "alt", None)
            ),
            "⭐",
        )

        for attempt in range(UPLOAD_ATTEMPTS):
            try:
                file_obj = await self._prepare_file(client, doc)
                return await self._upload_item(client, file_obj, emoji, doc_kind(doc))
            except FloodWaitError as fwe:
                await asyncio.sleep(fwe.seconds + 1)
            except Exception:
                if attempt == UPLOAD_ATTEMPTS - 1:
                    return None
                await asyncio.sleep(1)
        return None

    async def _create_pack(self, message: Message, form, docs: list, title: str, clean_name: str):
        total = len(docs)
        pack_type = pack_kind_label(docs)
        safe_title = utils.escape_html(title)
        me = await message.client.get_me()
        my_name = me.username or f"id{me.id}"
        rnd_hash = "".join(random.choices(string.ascii_lowercase + string.digits, k=5))
        clean_base = self._clean_short_name(clean_name)[:16]
        short_name = f"e_{rnd_hash}_{clean_base}_by_{my_name}"[:64].rstrip("_")

        await self._edit(form, self.strings("processing").format(pack_type, safe_title, 0, total))

        # Download, ffmpeg and upload all run under the semaphore so a 200-sticker pack
        # does not spawn 200 ffmpeg processes at once.
        sem = asyncio.Semaphore(PARALLEL_CONVERSIONS)
        loop = asyncio.get_running_loop()
        done = 0
        last_edit = 0.0

        async def worker(doc):
            nonlocal done, last_edit
            async with sem:
                item = await self._convert_one(message.client, doc)

            done += 1
            if total > 1 and loop.time() - last_edit >= PROGRESS_EDIT_INTERVAL:
                last_edit = loop.time()
                filled = int(done / total * 12)
                bar = "█" * filled + "░" * (12 - filled)
                await self._edit(
                    form,
                    f"{self.strings('processing').format(pack_type, safe_title, done, total)}\n"
                    f"<code>[{bar}]</code> {int(done / total * 100)}%",
                )
            return item

        results = await asyncio.gather(*(worker(doc) for doc in docs))
        items = [item for item in results if item is not None]

        if not items:
            await self._edit(form, self.strings("no_stickers").format(pack_type))
            return

        try:
            final_sn = await self._safe_create_set(
                client=message.client,
                title=title,
                short_name=short_name,
                stickers=items,
            )
        except Exception as exc:
            await self._edit(form, self._error_text(exc))
            return

        link = f"https://t.me/addemoji/{final_sn}"
        await self._edit(
            form,
            self.strings("success").format(safe_title, pack_type, link),
            [[{"text": self.strings("btn_add"), "url": link}]],
        )

    @staticmethod
    async def _safe_create_set(client, title: str, short_name: str, stickers: list, retries: int = 3) -> str:
        for i in range(retries):
            sn = (short_name if i == 0 else f"{short_name}_{i + 1}")[:64]
            try:
                await client(
                    functions.stickers.CreateStickerSetRequest(
                        user_id=InputUserSelf(),
                        title=title,
                        short_name=sn,
                        stickers=stickers,
                        emojis=True,
                    )
                )
                return sn
            except Exception as e:
                err = str(e)
                name_taken = (
                    "SHORT_NAME_OCCUPIED" in err
                    or "already exists" in err.lower()
                    or "STICKERSET_INVALID" in err
                )
                if not name_taken or i == retries - 1:
                    raise
        raise RuntimeError("SHORT_NAME_OCCUPIED")

    @staticmethod
    async def _upload_item(client, file_obj: io.BytesIO, emoji_str: str, kind: str) -> InputStickerSetItem:
        mime_type, file_name = UPLOAD_FORMAT[kind]
        attributes = [
            DocumentAttributeFilename(file_name=file_name),
            DocumentAttributeCustomEmoji(
                alt=emoji_str,
                stickerset=InputStickerSetEmpty(),
                free=False,
                text_color=False,
            ),
        ]
        if kind == "video":
            attributes.append(DocumentAttributeVideo(duration=3, w=100, h=100))
        elif kind == "static":
            attributes.append(DocumentAttributeImageSize(w=100, h=100))

        file_obj.seek(0)
        uploaded = await client.upload_file(file_obj, file_name=file_name)
        media = InputMediaUploadedDocument(file=uploaded, mime_type=mime_type, attributes=attributes)
        doc = (await client(UploadMediaRequest(peer=InputPeerSelf(), media=media))).document
        return InputStickerSetItem(
            document=InputDocument(
                id=doc.id,
                access_hash=doc.access_hash,
                file_reference=doc.file_reference,
            ),
            emoji=emoji_str,
        )

    @staticmethod
    def _resize_static(image_bytes: bytes) -> io.BytesIO:
        im = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        im.thumbnail((100, 100), Image.Resampling.LANCZOS)

        canvas = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        canvas.alpha_composite(im, dest=((100 - im.width) // 2, (100 - im.height) // 2))

        output = io.BytesIO()
        output.name = "emoji.webp"
        canvas.save(output, format="WEBP", lossless=True)
        output.seek(0)
        return output

    @staticmethod
    async def _encode_video(in_path: str, out_path: str, preset: dict, use_vpx_decoder: bool) -> bool:
        vf_filter = (
            "format=rgba,"
            "scale=100:100:force_original_aspect_ratio=decrease:flags=bicubic,"
            "pad=100:100:(ow-iw)/2:(oh-ih)/2:color=0x00000000,"
            "format=yuva420p"
        )
        # The native webm decoder drops the alpha channel; libvpx-vp9 keeps it but cannot read mp4.
        decoder = ["-c:v", "libvpx-vp9"] if use_vpx_decoder else []
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-y", *decoder,
            "-i", in_path,
            "-t", "2.99",
            "-vf", vf_filter,
            "-c:v", "libvpx-vp9",
            "-pix_fmt", "yuva420p",
            "-auto-alt-ref", "0",
            "-metadata:s:v:0", "alpha_mode=1",
            "-crf", preset["crf"],
            "-b:v", preset["b"],
            "-minrate", "20k",
            "-maxrate", preset["maxrate"],
            "-bufsize", preset["bufsize"],
            "-r", "30",
            "-an",
            out_path,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()
        return proc.returncode == 0 and os.path.exists(out_path)

    async def _resize_video(self, video_bytes: bytes) -> io.BytesIO:
        presets = [
            {"crf": "34", "b": "110k", "maxrate": "130k", "bufsize": "80k"},
            {"crf": "40", "b": "80k", "maxrate": "100k", "bufsize": "60k"},
            {"crf": "48", "b": "50k", "maxrate": "65k", "bufsize": "40k"},
            {"crf": "54", "b": "35k", "maxrate": "45k", "bufsize": "30k"},
        ]
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as in_file:
            in_path = in_file.name
            in_file.write(video_bytes)

        out_path = in_path + "_out.webm"
        try:
            for use_vpx_decoder in (True, False):
                encoded = False
                for preset in presets:
                    if not await self._encode_video(in_path, out_path, preset, use_vpx_decoder):
                        break
                    encoded = True
                    if os.path.getsize(out_path) <= MAX_EMOJI_VIDEO_SIZE:
                        break
                if encoded:
                    break

            if not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
                raise RuntimeError("Failed to compress video sticker with transparency")

            with open(out_path, "rb") as f:
                output = io.BytesIO(f.read())
            output.name = "emoji.webm"
            return output
        finally:
            for path in (in_path, out_path):
                with contextlib.suppress(FileNotFoundError):
                    os.remove(path)
