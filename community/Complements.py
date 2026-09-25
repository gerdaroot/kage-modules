# ---------------------------------------------------------------------------------
#  /\_/\  🌐 This module was loaded through https://t.me/hikkamods_bot
# ( o.o )  🔐 Licensed under the GNU AGPLv3.
#  > ^ <   ⚠️ Owner of heta.hikariatama.ru doesn't take any responsibilities or intellectual property rights regarding this script
# ---------------------------------------------------------------------------------
# Name: Complements
# Description: Модуль который дарит комплементы девушке/парню
# Author: SkillsAngels
# Commands:
# .cg | .cb
# ---------------------------------------------------------------------------------


__version__ = (0, 0, 1)
#
# _           _            _ _
# | |         | |          (_) |
# | |     ___ | |_ ___  ___ _| | __
# | |    / _ \| __/ _ \/ __| | |/ /
# | |___| (_) | || (_) \__ \ |   <
# \_____/\___/ \__\___/|___/_|_|\_\
#
#              © Copyright 2022
#
#         developed by @lotosiiik, @byateblan
#
# 🔒 Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html
# Modified for Kage by gerdaroot (https://github.com/gerdaroot/kage-modules), 2026-09-25

# meta developer: @hikkaftgmods
# meta banner: https://i.imgur.com/kDshq0N.jpeg
# meta pic: https://i.imgur.com/xC4oVi6.jpeg
# scope: heroku_min 2.0.0

import asyncio

from telethon.tl.types import Message

from .. import loader, utils

GIRL_COMPLIMENTS = (
    "Пожалуйста прочти до конца",
    "......",
    "Ты прекрасна как всегда",
    "Ты просто неповторима",
    "Сногшибательна",
    "Идеальна",
    "Красива",
    "Умопомрачительна",
    "Незабываемая",
    "Лучшая",
    "Маленькое солнышко",
    "Чудо",
)

BOY_COMPLIMENTS = (
    "Пожалуйста прочти до конца",
    "......",
    "Ты прекрасный как всегда",
    "Ты просто неповторимый",
    "Сногшибательный",
    "Идеальный",
    "Красивый",
    "Умопомрачительный",
    "Незабываемый",
    "Лучший",
    "Маленькое солнышко",
    "Чудо",
)


@loader.tds
class ComplementsMod(loader.Module):
    """Модуль который дарит комплементы девушке/парню"""

    strings = {"name": "Complements"}

    async def _play(self, message: Message, lines: tuple[str, ...]):
        for line in lines:
            message = await utils.answer(message, line)
            await asyncio.sleep(1)

    async def cgcmd(self, message: Message):
        """Эта команда дарит комплементы девушке"""
        await self._play(message, GIRL_COMPLIMENTS)

    async def cbcmd(self, message: Message):
        """Эта команда дарит комплементы парню"""
        await self._play(message, BOY_COMPLIMENTS)
