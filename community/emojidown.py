# ---------------------------------------------------------------------------------
#░█▀▄░▄▀▀▄░█▀▄░█▀▀▄░█▀▀▄░█▀▀▀░▄▀▀▄░░░█▀▄▀█
#░█░░░█░░█░█░█░█▄▄▀░█▄▄█░█░▀▄░█░░█░░░█░▀░█
#░▀▀▀░░▀▀░░▀▀░░▀░▀▀░▀░░▀░▀▀▀▀░░▀▀░░░░▀░░▒▀
# Name: EmojiDownloader
# Description: Download emoji from reply
# Author: @codrago_m
# ---------------------------------------------------------------------------------
# 🔒    Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html
# Modified for Kage by gerdaroot (https://github.com/gerdaroot/kage-modules), 2026-09-25
# ---------------------------------------------------------------------------------
# Author: @codrago
# Commands: emojidown
# scope: hikka_only
# meta developer: @codrago_m
# meta banner: https://raw.githubusercontent.com/coddrago/modules/refs/heads/main/banner.png
# meta pic: https://envs.sh/Hod.webp
# ---------------------------------------------------------------------------------

__version__ = (1, 0, 0)

import asyncio

from telethon.tl.types import Message

from .. import loader, utils

BOT = "@emojidownloadbot"
ERROR_EMOJI = "<emoji document_id=5328145443106873128>✖️</emoji>"


@loader.tds
class EmojiDownloadMod(loader.Module):
    """Download emoji from reply"""

    strings = {
        "name": "EmojiDownload",
        "no_reply": f"{ERROR_EMOJI} Where is reply for your emoji?",
        "no_premium": f"{ERROR_EMOJI} Sorry, but module only for premium users",
        "bot_timeout": f"{ERROR_EMOJI} {BOT} did not respond, try again later",
    }

    async def on_dlmod(self):
        await utils.dnd(self._client, BOT, True)

    async def emojidowncmd(self, message: Message):
        """[reply] | Download emoji from reply"""
        reply = await message.get_reply_message()
        if not reply:
            await utils.answer(message, self.strings["no_reply"])
            return

        # Non-premium accounts can't send custom emoji, so the bot would get plain text.
        if not self._client.hikka_me.premium:
            await utils.answer(message, self.strings["no_premium"])
            return

        try:
            async with self._client.conversation(BOT) as conv:
                await conv.send_message(reply)
                emoji = await conv.get_response()
                await conv.mark_read()
        except asyncio.TimeoutError:
            await utils.answer(message, self.strings["bot_timeout"])
            return
        except ValueError:
            await utils.answer(message, self.strings["no_reply"])
            return

        await utils.answer(message, emoji)
