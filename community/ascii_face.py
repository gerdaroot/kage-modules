# ---------------------------------------------------------------------------------
#░█▀▄░▄▀▀▄░█▀▄░█▀▀▄░█▀▀▄░█▀▀▀░▄▀▀▄░░░█▀▄▀█
#░█░░░█░░█░█░█░█▄▄▀░█▄▄█░█░▀▄░█░░█░░░█░▀░█
#░▀▀▀░░▀▀░░▀▀░░▀░▀▀░▀░░▀░▀▀▀▀░░▀▀░░░░▀░░▒▀
# Name: Ascii face
# Description: random ascii face from utils
# Author: @codrago_m
# ---------------------------------------------------------------------------------
# 🔒    Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html
# Modified for Kage by gerdaroot (https://github.com/gerdaroot/kage-modules), 2026-09-25
# ---------------------------------------------------------------------------------
# Author: @codrago
# Commands: ascii
# scope: hikka_only
# scope: heroku_min 2.0.0
# meta developer: @codrago_m
# meta banner: https://raw.githubusercontent.com/coddrago/modules/refs/heads/main/banner.png
# meta pic: https://envs.sh/HoE.webp
# ---------------------------------------------------------------------------------

__version__ = (1, 0, 0)

from .. import loader, utils


@loader.tds
class Ascii_face(loader.Module):
    """Random Ascii Face from utils"""

    strings = {
        "name": "Ascii_Face",
        "ascii_face": "<emoji document_id=5343719226450385808>😛</emoji> <b>Your random AsciiFace:</b> ",
    }

    strings_ru = {
        "ascii_face": "<emoji document_id=5343719226450385808>😛</emoji> <b>Ваш рандомный AsciiFace:</b> "
    }

    async def asciicmd(self, message):
        """| Get random ascii face"""
        await utils.answer(message, self.strings["ascii_face"] + f"<code>{utils.ascii_face()}</code>")
