# ---------------------------------------------------------------------------------
#  /\_/\  🌐 This module was loaded through https://t.me/hikkamods_bot
# ( o.o )  🔐 Licensed under the GNU AGPLv3.
#  > ^ <   ⚠️ Owner of heta.hikariatama.ru doesn't take any responsibilities or intellectual property rights regarding this script
# ---------------------------------------------------------------------------------
# Name: premium_sticks
# Author: hikariatama
# Commands:
# .premstick
# ---------------------------------------------------------------------------------

#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html
# Modified for Kage by gerdaroot (https://github.com/gerdaroot/kage-modules), 2026-09-25

# meta pic: https://0x0.st/ojP2.png
# meta banner: https://mods.hikariatama.ru/badges/premium_sticks.jpg
# meta developer: @hikarimods
# scope: heroku_min 2.0.0

import random

from telethon.tl.types import Message

from .. import loader


@loader.tds
class PremiumStickersMod(loader.Module):
    """Sends premium stickers for free"""

    strings = {"name": "PremiumStickers"}

    async def premstickcmd(self, message: Message):
        """Send random premium sticker without premium"""
        if message.out:
            await message.delete()

        await message.respond(
            (
                f'<a href="https://t.me/hikka_premum_stickers/{random.randint(2, 106)}">­</a>'
            ),
        )
