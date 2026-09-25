# ---------------------------------------------------------------------------------
#  /\_/\  🌐 This module was loaded through https://t.me/hikkamods_bot
# ( o.o )  🔐 Licensed under the GNU AGPLv3.
#  > ^ <   ⚠️ Owner of heta.hikariatama.ru doesn't take any responsibilities or intellectual property rights regarding this script
# ---------------------------------------------------------------------------------
# Name: instsave
# Author: AmoreForever
# Commands:
# .instas
# ---------------------------------------------------------------------------------

# █ █ █ █▄▀ ▄▀█ █▀▄▀█ █▀█ █▀█ █ █
# █▀█ █ █ █ █▀█ █ ▀ █ █▄█ █▀▄ █▄█

# 🔒 Licensed under the GNU GPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html
# 👤 https://t.me/hikamoru
# Modified for Kage by gerdaroot (https://github.com/gerdaroot/kage-modules), 2026-09-25

# meta developer: @hikamorumods
# meta pic: https://te.legra.ph/file/0251f5d602a8f32cd7368.png
# meta banner: https://raw.githubusercontent.com/AmoreForever/assets/master/Instsave.jpg
# scope: heroku_min 2.0.0

__version__ = (1, 0, 0)

import asyncio

from .. import loader, utils

chat = "@SaveAsBot"
# SaveAsBot often answers with a text status first, so skip a few replies before giving up.
MAX_BOT_REPLIES = 5


class InstagramMod(loader.Module):
    """Download video from instagram without watermark"""

    strings = {
        "name": "InstSave",
        "processing": (
            "<emoji document_id='6318766236746384900'>🕔</emoji> <b>Processing...</b>"
        ),
        "no_args": "<b>Specify an Instagram link</b>",
        "failed": "<b>SaveAsBot did not send any media</b>",
        "mods": (
            "<b>Successfuly downloaded</b> <emoji"
            " document_id='6320882302708614449'>🚀</emoji>"
        ),
    }

    @loader.command(ru_doc="<линк> - Скачать видео из инстаграм")
    async def instascmd(self, message):
        """instagram video/reels/photo url"""
        text = utils.get_args_raw(message)
        if not text:
            await utils.answer(message, self.strings("no_args"))
            return

        message = await utils.answer(message, self.strings("processing"))
        media = None
        msgs = []
        async with self._client.conversation(chat) as conv:
            try:
                msgs.append(await conv.send_message("/start"))
                msgs.append(await conv.get_response())
                msgs.append(await conv.send_message(text))
                for _ in range(MAX_BOT_REPLIES):
                    response = await conv.get_response()
                    msgs.append(response)
                    if response.media:
                        media = response.media
                        break
            except asyncio.TimeoutError:
                pass

        if not media:
            await utils.answer(message, self.strings("failed"))
        else:
            await self._client.send_file(
                message.peer_id,
                media,
                caption=self.strings("mods"),
                reply_to=message.reply_to_msg_id,
            )
            if message.out:
                await message.delete()

        for msg in msgs:
            await msg.delete()

        await self._client.delete_dialog(chat)
