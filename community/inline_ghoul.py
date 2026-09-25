# ---------------------------------------------------------------------------------
#  /\_/\  🌐 This module was loaded through https://t.me/hikkamods_bot
# ( o.o )  🔐 Licensed under the GNU AGPLv3.
#  > ^ <   ⚠️ Owner of heta.hikariatama.ru doesn't take any responsibilities or intellectual property rights regarding this script
# ---------------------------------------------------------------------------------
# Name: inline_ghoul
# Description: Non-spammy ghoul module
# Author: hikariatama
# Commands:
# .ghoul
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

# meta pic: https://img.icons8.com/color/480/000000/dota.png
# meta banner: https://mods.hikariatama.ru/badges/inline_ghoul.jpg
# meta developer: @hikarimods
# scope: inline
# scope: hikka_only

from telethon.tl.types import Message

from .. import loader


@loader.tds
class InlineGhoulMod(loader.Module):
    """Non-spammy ghoul module"""

    strings = {"name": "InlineGhoul", "tired": "😾 <b>Tired of counting!</b>"}

    strings_ru = {
        "tired": "😾 <b>Я устал считать!</b>",
        "_cmd_doc_ghoul": "Отправляет сообщение Гуля",
        "_cls_doc": "Неспамящий модуль Гуль",
    }

    async def ghoulcmd(self, message: Message):
        """Sends ghoul message"""
        await self.animate(
            message,
            [f"👊 <b>{x} - 7 = {x - 7}</b>" for x in range(1000, 900, -7)]
            + [self.strings("tired")],
            interval=1,
            inline=True,
        )
