# ---------------------------------------------------------------------------------
#░█▀▄░▄▀▀▄░█▀▄░█▀▀▄░█▀▀▄░█▀▀▀░▄▀▀▄░░░█▀▄▀█
#░█░░░█░░█░█░█░█▄▄▀░█▄▄█░█░▀▄░█░░█░░░█░▀░█
#░▀▀▀░░▀▀░░▀▀░░▀░▀▀░▀░░▀░▀▀▀▀░░▀▀░░░░▀░░▒▀
# Name: ID
# Description: Tool for ID's
# Author: @codrago_m
# ---------------------------------------------------------------------------------
# 🔒    Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html
# Modified for Kage by gerdaroot (https://github.com/gerdaroot/kage-modules), 2026-09-25
# ---------------------------------------------------------------------------------
# Author: @codrago
# Commands: id, chatid, userid
# scope: hikka_only
# meta developer: @codrago_m
# meta banner: https://raw.githubusercontent.com/coddrago/modules/refs/heads/main/banner.png
# meta pic: https://envs.sh/HJX.webp
# ---------------------------------------------------------------------------------

__version__ = (1, 0, 0)

from telethon.tl.types import User
from telethon.utils import get_display_name, get_peer_id

from .. import loader, utils

PLANET = "<emoji document_id=5301034196490268401>🪐</emoji>"
SLEEPY = "<emoji document_id=5314260526803462610>😴</emoji>"


@loader.tds
class ID(loader.Module):
    """ID of all!"""

    strings = {
        "name": "ID",
        "Error_reply": "<emoji document_id=5328145443106873128>✖️</emoji> <b>Where your reply?</b>",
        "not_chat": "<emoji document_id=5328145443106873128>✖️</emoji> <b>This is not a chat!</b>",
    }

    strings_ru = {
        "Error_reply": "<emoji document_id=5328145443106873128>✖️</emoji> <b>Где твой реплай?</b>",
        "not_chat": "<emoji document_id=5328145443106873128>✖️</emoji> <b>Это не чат!</b>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "bot_api_id",
                True,
                "Bot API id for channels and chats",
                validator=loader.validators.Boolean(),
            ),
        )

    def _format_id(self, entity) -> int:
        return get_peer_id(entity) if self.config["bot_api_id"] else entity.id

    async def useridcmd(self, message):
        """[reply or username] | Get User ID"""
        args = utils.get_args_raw(message)
        reply = await message.get_reply_message()

        try:
            if args:
                target = int(args) if args.lstrip("-").isdigit() else args
            else:
                target = reply.sender_id if reply else message.sender_id
            entity = await message.client.get_entity(target)
        except ValueError:
            entity = await message.client.get_entity(message.sender_id)

        name = utils.escape_html(get_display_name(entity))
        entity_id = entity.id if isinstance(entity, User) else self._format_id(entity)
        await utils.answer(
            message,
            f"{PLANET} <b>User:</b> <code>{name}</code>\n"
            f"{SLEEPY} <b>User ID:</b> <code>{entity_id}</code>",
        )

    async def idcmd(self, message):
        """| Get your ID"""
        me = await message.client.get_me()
        await utils.answer(
            message,
            f"{PLANET}<b> Your Nick:</b> {utils.escape_html(get_display_name(me))}\n"
            f"{SLEEPY} <b>Your ID</b>: <code>{me.id}</code>",
        )

    async def chatidcmd(self, message):
        """| Get chat ID"""
        if message.is_private:
            await utils.answer(message, self.strings("not_chat"))
            return

        chat = await message.get_chat()
        await utils.answer(
            message,
            f"{PLANET}<code> {utils.escape_html(get_display_name(chat))}</code>\n"
            f"{SLEEPY} <b>Chat ID</b>: <code>{self._format_id(chat)}</code>",
        )
