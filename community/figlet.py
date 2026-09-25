# ---------------------------------------------------------------------------------
#░█▀▄░▄▀▀▄░█▀▄░█▀▀▄░█▀▀▄░█▀▀▀░▄▀▀▄░░░█▀▄▀█
#░█░░░█░░█░█░█░█▄▄▀░█▄▄█░█░▀▄░█░░█░░░█░▀░█
#░▀▀▀░░▀▀░░▀▀░░▀░▀▀░▀░░▀░▀▀▀▀░░▀▀░░░░▀░░▒▀
# Name: Figlet
# Description: Tool for Figlet
# Author: @codrago_m
# ---------------------------------------------------------------------------------
# 🔒    Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html
# Modified for Kage by gerdaroot (https://github.com/gerdaroot/kage-modules), 2026-09-25
# ---------------------------------------------------------------------------------
# Author: @codrago
# Commands: figlet
# scope: hikka_only
# meta developer: @codrago_m
# meta banner: https://raw.githubusercontent.com/coddrago/modules/refs/heads/main/banner.png
# meta pic: https://envs.sh/Hou.webp
# ---------------------------------------------------------------------------------

__version__ = (1, 0, 0)

import asyncio

from .. import loader, utils

@loader.tds
class Figlet(loader.Module):
    """Tool for work with figlet"""

    strings = {
    "name": "Figlet",
    "not_installed": "<emoji document_id=5328145443106873128>✖️</emoji> <b>You don't have Figlet installed! Install it with <code>.terminal sudo apt install figlet -y</code></b>",
    "no_args": "<emoji document_id=5328145443106873128>✖️</emoji> <b>Where args?</b>",
    "failed": "<emoji document_id=5328145443106873128>✖️</emoji> <b>Figlet failed:</b>\n<pre>{}</pre>",
    }

    strings_ru = {
    "not_installed": "<emoji document_id=5328145443106873128>✖️</emoji> <b>У вас не установлен Figlet! Установите его командой <code>.terminal sudo apt install figlet -y</code></b>",
    "no_args": "<emoji document_id=5328145443106873128>✖️</emoji> <b>Где аргументы?</b>",
    "failed": "<emoji document_id=5328145443106873128>✖️</emoji> <b>Ошибка Figlet:</b>\n<pre>{}</pre>",
}

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "font",
                "standard",
                "Select font for figlet",
                validator=loader.validators.String(),
            ),
        )

    async def figletcmd(self, message):
        """[args] | run figlet command"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings["no_args"])
            return

        try:
            process = await asyncio.create_subprocess_exec(
                "figlet", "-f", self.config["font"], "--", args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError:
            await utils.answer(message, self.strings["not_installed"])
            return

        stdout, stderr = await process.communicate()
        if process.returncode:
            error = stderr.decode(errors="replace").strip()
            await utils.answer(message, self.strings["failed"].format(utils.escape_html(error)))
            return

        # The leading Hangul filler keeps Telegram from stripping the art's leading spaces
        output = stdout.decode(errors="replace")
        await utils.answer(message, f"<pre>ᅠ\n{utils.escape_html(output)}</pre>")

    async def figlistcmd(self, message):
        """| see list of all fonts"""
        fonts = [
            "banner",
            "big",
            "block",
            "bubble",
            "digital",
            "ivrit",
            "lean",
            "mini",
            "mnemonic",
            "script",
            "shadow",
            "slant",
            "small",
            "smscript",
            "smshadow",
            "smslant",
        ]
        await utils.answer(message, "<b>List of available fonts:</b>\n" + "\n".join(fonts))