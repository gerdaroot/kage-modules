# ---------------------------------------------------------------------------------
#░█▀▄░▄▀▀▄░█▀▄░█▀▀▄░█▀▀▄░█▀▀▀░▄▀▀▄░░░█▀▄▀█
#░█░░░█░░█░█░█░█▄▄▀░█▄▄█░█░▀▄░█░░█░░░█░▀░█
#░▀▀▀░░▀▀░░▀▀░░▀░▀▀░▀░░▀░▀▀▀▀░░▀▀░░░░▀░░▒▀
# Name: Password Generator
# Description: Generate password
# Author: @codrago_m
# ---------------------------------------------------------------------------------
# 🔒    Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html
# Modified for Kage by gerdaroot (https://github.com/gerdaroot/kage-modules), 2026-09-25
# ---------------------------------------------------------------------------------
# Author: @codrago
# Commands: pass, passg
# meta developer: @codrago_m
# meta banner: https://raw.githubusercontent.com/coddrago/modules/refs/heads/main/banner.png
# meta pic: https://envs.sh/Hoe.webp
# scope: heroku_min 2.0.0
# ---------------------------------------------------------------------------------

import secrets
import string

from .. import loader, utils

SIMPLE_ALPHABET = string.ascii_lowercase + string.digits
FULL_ALPHABET = string.ascii_letters + string.digits + string.punctuation
# Keeps the reply well under Telegram's 4096-character message limit
MAX_LENGTH = 1024


@loader.tds
class PassGen(loader.Module):
    """Generate password"""

    strings = {
        "name": "PassGen",
        "no_args": "<emoji document_id=5328145443106873128>✖️</emoji> <b>Where args?</b>",
        "pass": "<emoji document_id=5832546462478635761>🔒</emoji> <b>Here your password:</b> ",
    }

    strings_ru = {
        "no_args": "<emoji document_id=5328145443106873128>✖️</emoji> <b>Где аргументы?</b>",
        "pass": "<emoji document_id=5832546462478635761>🔒</emoji> <b>Твой пароль:</b> ",
    }

    async def _send_password(self, message, alphabet: str):
        args = utils.get_args_raw(message).strip()
        if not args.isdigit() or not 0 < int(args) <= MAX_LENGTH:
            await utils.answer(message, self.strings("no_args"))
            return

        password = "".join(secrets.choice(alphabet) for _ in range(int(args)))
        await utils.answer(
            message, f"{self.strings('pass')}<code>{utils.escape_html(password)}</code>"
        )

    @loader.command()
    async def passcmd(self, message):
        """<length> | Generate password from utils"""
        await self._send_password(message, SIMPLE_ALPHABET)

    @loader.command()
    async def passgcmd(self, message):
        """<length> | Generate password from string"""
        await self._send_password(message, FULL_ALPHABET)
