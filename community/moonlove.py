# ---------------------------------------------------------------------------------
#  /\_/\  🌐 This module was loaded through https://t.me/hikkamods_bot
# ( o.o )  🔐 Licensed under the GNU AGPLv3.
#  > ^ <   ⚠️ Owner of heta.hikariatama.ru doesn't take any responsibilities or intellectual property rights regarding this script
# ---------------------------------------------------------------------------------
# Name: moonlove
# Author: hikariatama
# Commands:
# .moonlove | .moonlovei
# ---------------------------------------------------------------------------------

#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html
# Modified for Kage by gerdaroot (https://github.com/gerdaroot/kage-modules), 2026-09-25

# meta pic: https://static.dan.tatar/moonlove_icon.png
# meta banner: https://mods.hikariatama.ru/badges/moonlove.jpg
# meta developer: @hikarimods
# scope: hikka_only
# scope: hikka_min 1.2.10

from telethon.tl.types import Message

from .. import loader, utils

FRAMES = [
    "🌘🌗🌖🌕🌔🌓🌒\n🌙❤️❤️🌙❤️❤️🌙\n❤️💓💓❤️💓💓❤️\n❤️💓💓💓💓💓❤️\n🌙❤️💓💓💓❤️🌙\n🌙🌙❤️💓❤️🌙🌙\n🌙🌙🌙❤️🌙🌙🌙\n🌘🌗🌖🌕🌔🌓🌒",
    "🌗🌖🌕🌔🌓🌒🌘\n🌙❤️❤️🌙❤️❤️🌙\n❤️💓💓❤️💓💓❤️\n❤️💓💓💗💓💓❤️\n🌙❤️💓💓💓❤️🌙\n🌙🌙❤️💓❤️🌙🌙\n🌙🌙🌙❤️🌙🌙🌙\n🌗🌖🌕🌔🌓🌒🌘",
    "🌖🌕🌔🌓🌒🌘🌗\n🌙❤️❤️🌙❤️❤️🌙\n❤️💓💗❤️💗💓❤️\n❤️💓💗💗💗💓❤️\n🌙❤️💓💗💓❤️🌙\n🌙🌙❤️💓❤️🌙🌙\n🌙🌙🌙❤️🌙🌙🌙\n🌖🌕🌔🌓🌒🌘🌗",
    "🌕🌔🌓🌒🌘🌗🌖\n🌙❤️❤️🌙❤️❤️🌙\n❤️💗💗❤️💗💗❤️\n❤️💗💗💗💗💗❤️\n🌙❤️💗💗💗❤️🌙\n🌙🌙❤️💗❤️🌙🌙\n🌙🌙🌙❤️🌙🌙🌙\n🌕🌔🌓🌒🌘🌗🌖",
    "🌔🌓🌒🌘🌗🌖🌕\n🌙❤️❤️🌙❤️❤️🌙\n❤️💗💗❤️💗💗❤️\n❤️💗💗💖💗💗❤️\n🌙❤️💗💗💗❤️🌙\n🌙🌙❤️💗❤️🌙🌙\n🌙🌙🌙❤️🌙🌙🌙\n🌔🌓🌒🌘🌗🌖🌕",
    "🌓🌒🌘🌗🌖🌕🌔\n🌙❤️❤️🌙❤️❤️🌙\n❤️💗💖❤️💖💗❤️\n❤️💗💖💖💖💗❤️\n🌙❤️💗💖💗❤️🌙\n🌙🌙❤️💗❤️🌙🌙\n🌙🌙🌙❤️🌙🌙🌙\n🌓🌒🌘🌗🌖🌕🌔",
    "🌒🌘🌗🌖🌕🌔🌓\n🌙❤️❤️🌙❤️❤️🌙\n❤️💖💖❤️💖💖❤️\n❤️💖💖💖💖💖❤️\n🌙❤️💖💖💖❤️🌙\n🌙🌙❤️💖❤️🌙🌙\n🌙🌙🌙❤️🌙🌙🌙\n🌒🌘🌗🌖🌕🌔🌓",
    "🌘🌗🌖🌕🌔🌓🌒\n🌙❤️❤️🌙❤️❤️🌙\n❤️💖💖❤️💖💖❤️\n❤️💖💖💓💖💖❤️\n🌙❤️💖💖💖❤️🌙\n🌙🌙❤️💖❤️🌙🌙\n🌙🌙🌙❤️🌙🌙🌙\n🌘🌗🌖🌕🌔🌓🌒",
    "🌗🌖🌕🌔🌓🌒🌘\n🌙❤️❤️🌙❤️❤️🌙\n❤️💖💓❤️💓💖❤️\n❤️💖💓💓💓💖❤️\n🌙❤️💖💓💖❤️🌙\n🌙🌙❤️💖❤️🌙🌙\n🌙🌙🌙❤️🌙🌙🌙\n🌗🌖🌕🌔🌓🌒🌘",
] * 3 + [  # It's shit, I know. But it's the easiest solution tho
    "💓",
    "💗",
    "💖",
]


@loader.tds
class MoonLoveMod(loader.Module):
    """Animation with moon and hearts for your beloved"""

    strings = {"name": "MoonLove"}
    strings_ru = {
        "_cls_doc": "Анимация с лунами и сердечками для любимой",
        "_cmd_doc_moonlove": "[текст] - Люблю тебя невообразимо",
        "_cmd_doc_moonlovei": "[текст] - Люблю тебя невообразимо (инлайн)",
    }

    async def moonlovecmd(self, message: Message):
        """[text] - Love you to the moon"""
        m = await self.animate(
            message,
            FRAMES,
            interval=0.3,
            inline=False,
        )
        await m.edit(utils.get_args_raw(message) or "❤️")

    async def moonloveicmd(self, message: Message):
        """[text] - Love you to the moon [Inline]"""
        m = await self.animate(
            message,
            FRAMES,
            interval=0.3,
            inline=True,
        )
        # animate() returns False when the inline form could not be sent
        if m:
            await m.edit(utils.get_args_raw(message) or "❤️")
