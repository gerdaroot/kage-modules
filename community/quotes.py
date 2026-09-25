# ---------------------------------------------------------------------------------
#  /\_/\  🌐 This module was loaded through https://t.me/hikkamods_bot
# ( o.o )  🔐 Licensed under the GNU GPLv3.
#  > ^ <   ⚠️ Owner of heta.hikariatama.ru doesn't take any responsibilities or intellectual property rights regarding this script
# ---------------------------------------------------------------------------------
# Name: quotes
# Description: Quote a message using Mishase Quotes API
# Author: HitaloSama
# Commands:
# .quote | .fquote
# ---------------------------------------------------------------------------------


#    Friendly Telegram (telegram userbot)
#    Copyright (C) 2018-2019 The Authors

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
# Modified for Kage by gerdaroot (https://github.com/gerdaroot/kage-modules), 2026-09-25

# API & module author: @mishase

# scope: heroku_min 2.0.0

import base64
import hashlib
import io
import logging

import aiohttp
from telethon.tl import types
from telethon.tl.types import Message
from telethon.utils import get_display_name

from .. import loader, utils

logger = logging.getLogger(__name__)

# quotes.mishase.dev is gone; LyoSU quote-api is the maintained successor
# (https://github.com/LyoSU/quote-api) and can be self-hosted.
DEFAULT_API_URL = "https://quote.yuri.ly/generate.webp"

ENTITY_TYPES = {
    types.MessageEntityBold: "bold",
    types.MessageEntityItalic: "italic",
    types.MessageEntityUnderline: "underline",
    types.MessageEntityStrike: "strikethrough",
    types.MessageEntitySpoiler: "spoiler",
    types.MessageEntityCode: "code",
    types.MessageEntityPre: "pre",
    types.MessageEntityUrl: "url",
    types.MessageEntityPhone: "phone_number",
    types.MessageEntityTextUrl: "text_link",
    types.MessageEntityMention: "mention",
    types.MessageEntityMentionName: "mention",
    types.MessageEntityHashtag: "hashtag",
    types.MessageEntityCashtag: "cashtag",
    types.MessageEntityBotCommand: "bot_command",
}


def encode_entities(entities: list | None) -> list[dict]:
    return [
        {
            "type": ENTITY_TYPES[type(entity)],
            "offset": entity.offset,
            "length": entity.length,
        }
        for entity in entities or []
        if type(entity) in ENTITY_TYPES
    ]


def media_placeholder(message: Message) -> str:
    if message.photo:
        return "📷 Photo"
    if message.sticker:
        return "🖼 Sticker"
    return "💾 File" if message.media else ""


def message_text(message: Message) -> str:
    return message.message or media_placeholder(message)


@loader.tds
class QuotesMod(loader.Module):
    """Quote messages as stickers via LyoSU quote-api"""

    strings = {
        "name": "Quotes",
        "quote_messages_limit_doc": "Messages Limit",
        "max_width_doc": "Max width (px)",
        "scale_factor_doc": "Scale factor",
        "background_color_doc": "Background color",
        "api_url_doc": "LyoSU quote-api endpoint that returns webp images",
        "no_reply": "<b>No reply message</b>",
        "processing": "<b>Processing...</b>",
        "no_messages": "<b>No messages to quote</b>",
        "api_error": "<b>Quote API error:</b> <code>{}</code>",
        "bad_args": "<b>Incorrect args</b>",
        "user_not_found": "<b>User not found</b>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "QUOTE_MESSAGES_LIMIT",
                50,
                lambda: self.strings("quote_messages_limit_doc"),
                validator=loader.validators.Integer(minimum=1),
            ),
            loader.ConfigValue(
                "MAX_WIDTH",
                384,
                lambda: self.strings("max_width_doc"),
                validator=loader.validators.Integer(minimum=100),
            ),
            loader.ConfigValue(
                "SCALE_FACTOR",
                5,
                lambda: self.strings("scale_factor_doc"),
                validator=loader.validators.Integer(minimum=1, maximum=20),
            ),
            loader.ConfigValue(
                "BACKGROUND_COLOR",
                "#162330",
                lambda: self.strings("background_color_doc"),
            ),
            loader.ConfigValue(
                "API_URL",
                DEFAULT_API_URL,
                lambda: self.strings("api_url_doc"),
                validator=loader.validators.Link(),
            ),
        )

    @loader.ratelimit
    async def quotecmd(self, message: Message):
        """Quote a message. Args: ?<count> ?file"""
        reply = await message.get_reply_message()
        if not reply:
            await utils.answer(message, self.strings("no_reply"))
            return

        args = utils.get_args(message)
        count = next((int(arg) for arg in args if arg.isdigit()), 1)
        count = max(1, min(self.config["QUOTE_MESSAGES_LIMIT"], count))

        message = await utils.answer(message, self.strings("processing"))
        if count == 1:
            quoted = [reply]
        else:
            quoted = await self._client.get_messages(
                reply.peer_id,
                offset_id=reply.id,
                reverse=True,
                add_offset=1,
                limit=count,
            )

        avatars: dict[int, str | None] = {}
        packed = [
            item
            for item in [await self._pack(msg, avatars) for msg in quoted]
            if item
        ]
        await self._send_quote(message, packed, force_document="file" in args)

    @loader.ratelimit
    async def fquotecmd(self, message: Message):
        """Fake message quote. Args: @<username>/<id>/<reply> <text>"""
        args = utils.get_args_raw(message)
        reply = await message.get_reply_message()
        target, _, text = args.partition(" ")
        if text and (target.startswith("@") or target.lstrip("-").isdigit()):
            user = target[1:] if target.startswith("@") else int(target)
        elif reply and args:
            user, text = reply.sender_id, args
        else:
            await utils.answer(message, self.strings("bad_args"))
            return

        try:
            entity = await self._client.get_entity(user)
        except Exception:
            await utils.answer(message, self.strings("user_not_found"))
            return

        message = await utils.answer(message, self.strings("processing"))
        author = await self._encode_author(entity, {})
        await self._send_quote(
            message, [{"from": author, "text": text, "avatar": True}]
        )

    async def _send_quote(
        self,
        message: Message,
        packed: list[dict],
        force_document: bool = False,
    ):
        if not packed:
            await utils.answer(message, self.strings("no_messages"))
            return

        try:
            image = await self._render(packed)
        except (aiohttp.ClientError, TimeoutError, ValueError) as e:
            await utils.answer(
                message, self.strings("api_error").format(utils.escape_html(str(e)))
            )
            return

        image.name = "quote.webp"
        await utils.answer_file(message, image, force_document=force_document)
        if message.out:
            await message.delete()

    async def _render(self, packed: list[dict]) -> io.BytesIO:
        payload = {
            "type": "quote",
            "format": "webp",
            "backgroundColor": self.config["BACKGROUND_COLOR"],
            "width": self.config["MAX_WIDTH"],
            "height": self.config["MAX_WIDTH"] * 2,
            "scale": self.config["SCALE_FACTOR"],
            "messages": packed,
        }
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=99)
        ) as session:
            async with session.post(self.config["API_URL"], json=payload) as resp:
                body = await resp.read()
                if resp.status != 200 or resp.content_type != "image/webp":
                    raise ValueError(f"HTTP {resp.status}: {body[:200]!r}")
        return io.BytesIO(body)

    async def _pack(self, message: Message, avatars: dict) -> dict | None:
        text = message_text(message)
        if not text:
            return None

        packed = {
            "from": await self._get_author(message, avatars),
            "text": text,
            "entities": encode_entities(message.entities) if message.message else [],
            "avatar": True,
        }

        if reply := await message.get_reply_message():
            reply_author = await self._get_author(reply, avatars, with_avatar=False)
            packed["replyMessage"] = {
                "name": reply_author["name"],
                "text": message_text(reply),
                "entities": encode_entities(reply.entities) if reply.message else [],
                "chatId": reply_author["id"],
            }

        return packed

    async def _get_author(
        self,
        message: Message,
        avatars: dict,
        with_avatar: bool = True,
    ) -> dict:
        forward = message.fwd_from
        if forward and not forward.from_id:
            # Hidden forwards only expose a display name; derive a stable fake id
            # from it so the API still picks a consistent name color.
            name = forward.from_name or forward.post_author or "Unknown"
            fake_id = int(hashlib.shake_256(name.encode()).hexdigest(6), 16)
            return {"id": fake_id, "name": name}

        peer = forward.from_id if forward else (message.from_id or message.peer_id)
        try:
            entity = await self._client.get_entity(peer)
        except Exception:
            entity = await message.get_chat()

        if not with_avatar:
            return {"id": entity.id, "name": get_display_name(entity)}
        return await self._encode_author(entity, avatars)

    async def _encode_author(self, entity, avatars: dict) -> dict:
        author = {"id": entity.id, "name": get_display_name(entity)}
        if entity.id not in avatars:
            avatars[entity.id] = await self._download_avatar(entity)
        if avatars[entity.id]:
            author["photo"] = {"url": avatars[entity.id]}
        return author

    async def _download_avatar(self, entity) -> str | None:
        photo = getattr(entity, "photo", None)
        if not photo or isinstance(
            photo, (types.ChatPhotoEmpty, types.UserProfilePhotoEmpty)
        ):
            return None
        data = await self._client.download_profile_photo(entity, bytes)
        if not data:
            return None
        return "data:image/jpeg;base64," + base64.b64encode(data).decode()
