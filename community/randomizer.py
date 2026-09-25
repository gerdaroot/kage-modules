# ---------------------------------------------------------------------------------
#░█▀▄░▄▀▀▄░█▀▄░█▀▀▄░█▀▀▄░█▀▀▀░▄▀▀▄░░░█▀▄▀█
#░█░░░█░░█░█░█░█▄▄▀░█▄▄█░█░▀▄░█░░█░░░█░▀░█
#░▀▀▀░░▀▀░░▀▀░░▀░▀▀░▀░░▀░▀▀▀▀░░▀▀░░░░▀░░▒▀
# Name: randomizer
# Description: Random it your life!
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
# meta pic: https://envs.sh/HJy.webp
# ---------------------------------------------------------------------------------

__version__ = (1, 0, 1)

import random

from .. import loader, utils


def user_link(user) -> str:
    name = utils.escape_html(user.first_name or "Deleted Account")
    return f'<a href="tg://user?id={user.id}">{name}</a>'


@loader.tds
class Randomizer(loader.Module):
    """Random - it's life!"""
    strings = {
    "name": "Randomizer",
    "not_args": "<emoji document_id=5328145443106873128>✖️</emoji> Your arguments were not stated.",
    "Num1": "Number 1 for RandomCMD",
    "Num2": "Number 2 for RandomCMD",
    "Not_chat": "<emoji document_id=5328145443106873128>✖️</emoji> This is not a chat!",
    "Error_num": "<emoji document_id=5328145443106873128>✖️</emoji> Error with numbers! Check your config",
    }

    strings_ru = {
    "not_args": "<emoji document_id=5328145443106873128>✖️</emoji> Ваши аргументы не были указаны.",
    "Num1": "Число 1 для RandomCMD",
    "Num2": "Число 2 для RandomCMD",
    "Not_chat": "<emoji document_id=5328145443106873128>✖️</emoji> Это не чат!",
    "Error_num": "<emoji document_id=5328145443106873128>✖️</emoji> Ошибка с числами! Проверьте ваш конфиг",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "Num_1",
                1,
                lambda: self.strings["Num1"],
                validator=loader.validators.Integer(),
            ),
            loader.ConfigValue(
                "Num_2",
                10,
                lambda: self.strings["Num2"],
                validator=loader.validators.Integer(),
            ),
        )

    async def chancecmd(self, message):
        """[args] | A chance for your success!"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings["not_args"])
            return

        chance = random.randint(1, 100)
        await utils.answer(message, f"<emoji document_id=5298620403395074835>🤩</emoji> The chance that {utils.escape_html(args)} is equal to {chance}%!")

    async def randomcmd(self, message):
        """!cfg | random number"""
        min_num = min(self.config["Num_1"], self.config["Num_2"])
        max_num = max(self.config["Num_1"], self.config["Num_2"])
        if min_num == max_num:
            await utils.answer(message, self.strings["Error_num"])
            return

        random_num = random.randint(min_num, max_num)
        await utils.answer(message, f"<emoji document_id=5406611523487411073>😇</emoji> Your random number in the range {min_num} - {max_num}: {random_num}")

    async def _participants(self, message) -> list | None:
        if message.is_private:
            await utils.answer(message, self.strings["Not_chat"])
            return None
        return await self.client.get_participants(message.peer_id)

    async def shipcmd(self, message):
        """| Ship from iris?"""
        if not (participants := await self._participants(message)):
            return

        first, second = random.choice(participants), random.choice(participants)
        await utils.answer(message, f'<emoji document_id=5341674117642854617>❤️</emoji> Random ship: {user_link(first)} + {user_link(second)}\n\n<emoji document_id=5341364514925321015>🌹</emoji> Love and appreciate each other!')

    async def randusercmd(self, message):
        """| Random user!"""
        if not (participants := await self._participants(message)):
            return

        await utils.answer(message, f'<emoji document_id=5287404392654319394>🔥</emoji> Your random user: {user_link(random.choice(participants))}')
