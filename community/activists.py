# ---------------------------------------------------------------------------------
#  /\_/\  🌐 This module was loaded through https://t.me/hikkamods_bot
# ( o.o )  🔐 Licensed under the GNU AGPLv3.
#  > ^ <   ⚠️ Owner of heta.hikariatama.ru doesn't take any responsibilities or intellectual property rights regarding this script
# ---------------------------------------------------------------------------------
# Name: activists
# Author: hikariatama
# Commands:
# .activists
# ---------------------------------------------------------------------------------

#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html
# Modified for Kage by gerdaroot (https://github.com/gerdaroot/kage-modules), 2026-09-25

# meta pic: https://static.dan.tatar/activists_icon.png
# meta banner: https://mods.hikariatama.ru/badges/activists.jpg
# meta developer: @hikarimods
# scope: hikka_only
# scope: hikka_min 1.4.0

import collections
import time
import typing

from telethon.tl.types import Chat, Message, User
from telethon.utils import get_display_name

from .. import loader, utils


@loader.tds
class ActivistsMod(loader.Module):
    """Looks for the most active users in chat"""

    strings = {
        "name": "Activists",
        "searching": (
            "<emoji document_id=5188311512791393083>🔎</emoji> <b>Looking for the most"
            " active users in chat...\nThis might take a while.</b>"
        ),
        "user": (
            '<emoji document_id=5314541718312328811>👤</emoji> {}. <a href="{}">{}</a>:'
            " {} messages"
        ),
        "active": (
            "<emoji document_id=5312361425409156767>⬆️</emoji> <b>The most active users"
            " in this chat:</b>\n\n{}\n<i>Request took: {}s</i>"
        ),
    }

    strings_ru = {
        "searching": (
            "<emoji document_id=5188311512791393083>🔎</emoji> <b>Поиск самых активных"
            " участников чата...\nЭто может занять некоторое время.</b>"
        ),
        "active": (
            "<emoji document_id=5312361425409156767>⬆️</emoji> <b>Самые активные"
            " пользователи в чате:</b>\n\n{}\n<i>Подсчет занял: {}s</i>"
        ),
        "_cmd_doc_activists": (
            "[количество] [-m <int>] - Найти наиболее активных пользователей чата"
        ),
        "_cls_doc": "Ищет наиболее активных пользователей чата",
    }

    strings_de = {
        "searching": (
            "<emoji document_id=5188311512791393083>🔎</emoji> <b>Suche nach den"
            " aktivsten Benutzern im Chat...\nDies kann eine Weile dauern.</b>"
        ),
        "active": (
            "<emoji document_id=5312361425409156767>⬆️</emoji> <b>Die aktivsten"
            " Benutzer in diesem Chat:</b>\n\n{}\n<i>Anfrage dauerte: {}s</i>"
        ),
        "_cmd_doc_activists": (
            "[Anzahl] [-m <int>] - Finde die aktivsten Benutzer im Chat"
        ),
        "_cls_doc": "Sucht nach den aktivsten Benutzern im Chat",
    }

    strings_hi = {
        "searching": (
            "<emoji document_id=5188311512791393083>🔎</emoji> <b>चैट में सबसे सक्रिय"
            " उपयोगकर्ताओं की तलाश कर रहा हूं...\nयह थोड़ा समय लेने सकता है।</b>"
        ),
        "active": (
            "<emoji document_id=5312361425409156767>⬆️</emoji> <b>इस चैट में सबसे"
            " सक्रिय उपयोगकर्ता:</b>\n\n{}\n<i>अनुरोध लिया: {}s</i>"
        ),
        "_cmd_doc_activists": (
            "[संख्या] [-m <int>] - चैट में सबसे सक्रिय उपयोगकर्ताओं की तलाश करें"
        ),
        "_cls_doc": "चैट में सबसे सक्रिय उपयोगकर्ताओं की तलाश करता है",
    }

    strings_uz = {
        "searching": (
            "<emoji document_id=5188311512791393083>🔎</emoji> <b>Chatdagi eng faol"
            " foydalanuvchilarni qidirish...\nBu bir necha vaqt olishi mumkin.</b>"
        ),
        "active": (
            "<emoji document_id=5312361425409156767>⬆️</emoji> <b>Ushbu chatdagi eng"
            " faol foydalanuvchilar:</b>\n\n{}\n<i>Talab: {}s</i>"
        ),
        "_cmd_doc_activists": (
            "[soni] [-m <int>] - Chatdagi eng faol foydalanuvchilarni qidirish"
        ),
        "_cls_doc": "Chatdagi eng faol foydalanuvchilarni qidiradi",
    }

    async def check_admin(
        self,
        chat: typing.Union[int, Chat],
        user_id: typing.Union[int, User],
    ) -> bool:
        try:
            return (await self._client.get_perms_cached(chat, user_id)).is_admin
        except Exception:
            return False

    async def activistscmd(self, message: Message):
        """[quantity] [-m <int>] - Find top active users in chat"""
        args = utils.get_args_raw(message)
        limit = None
        if "-m" in args:
            digits = "".join(ch for ch in args[args.find("-m") + 2 :] if ch.isdigit())
            limit = int(digits) if digits else None
            args = args[: args.find("-m")].strip()

        quantity = int(args) if args.isdigit() else 15

        message = await utils.answer(message, self.strings("searching"))

        st = time.perf_counter()

        counts = collections.Counter()
        async for msg in self._client.iter_messages(message.peer_id, limit=limit):
            if sender_id := getattr(msg, "sender_id", None):
                counts[sender_id] += 1

        top_users = []
        for sender_id, sent in counts.most_common():
            if len(top_users) >= quantity:
                break

            if await self.check_admin(message.peer_id, sender_id):
                continue

            try:
                entity = await self._client.get_entity(sender_id)
            except Exception:
                # Deleted accounts and senders missing from the entity cache can't be resolved
                continue

            top_users.append((entity, sent))

        top_users_formatted = [
            self.strings("user").format(
                i + 1,
                utils.get_link(entity),
                utils.escape_html(get_display_name(entity)),
                sent,
            )
            for i, (entity, sent) in enumerate(top_users)
        ]

        await utils.answer(
            message,
            self.strings("active").format(
                "\n".join(top_users_formatted), round(time.perf_counter() - st, 2)
            ),
        )
