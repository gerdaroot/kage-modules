# ---------------------------------------------------------------------------------
#  /\_/\  🌐 This module was loaded through https://t.me/hikkamods_bot
# ( o.o )  🔐 Licensed under the GNU GPLv3.
#  > ^ <   ⚠️ Owner of heta.hikariatama.ru doesn't take any responsibilities or intellectual property rights regarding this script
# ---------------------------------------------------------------------------------
# Name: swmute
# Description: Deletes messages from certain users
# Author: iamnalinor
# Commands:
# .swmute | .swunmute | .swmutelist | .swmuteclear
# ---------------------------------------------------------------------------------


# Deletes messages from certain users
# Copyright © 2022 https://t.me/nalinor

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# Modified for Kage by gerdaroot (https://github.com/gerdaroot/kage-modules), 2026-09-25

# meta developer: @nalinormods
# scope: heroku_min 2.0.0

import contextlib
import logging
import re
import time
from typing import Any, List

from telethon.errors import RPCError
from telethon.hints import Entity
from telethon.tl.custom import Message
from telethon.utils import get_peer_id

from .. import loader, security, utils

logger = logging.getLogger(__name__)

USER_ID_RE = re.compile(r"^(-100)?\d+$")


# pylint: disable=invalid-name
def s2time(string) -> int:
    """Parse time from text `string`"""
    r = {}  # results

    # `m(?!on)` keeps "2mon" from also counting as 2 minutes
    for time_type, pattern in [
        ("mon", "mon"), ("w", "w"), ("d", "d"), ("h", "h"), ("m", "m(?!on)"), ("s", "s")
    ]:
        try:
            r[time_type] = int(re.search(rf"(\d+)\s*{pattern}", string)[1])
        except TypeError:
            r[time_type] = 0

    return (
        r["mon"] * 86400 * 30
        + r["w"] * 86400 * 7
        + r["d"] * 86400
        + r["h"] * 3600
        + r["m"] * 60
        + r["s"]
    )


# pylint: disable=consider-using-f-string
def get_link(user: Entity) -> str:
    """Return permanent link to `user`"""
    return "<a href='tg://user?id={id}'>{name}</a>".format(
        id=user.id,
        name=utils.escape_html(
            (user.first_name if hasattr(user, "first_name") else user.title)
            or "Deleted Account"
        ),
    )


def plural_number(n: int) -> str:
    """Pluralize number `n`"""
    return (
        "one"
        if n % 10 == 1 and n % 100 != 11
        else "few" if 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20) else "many"
    )


# noinspection PyCallingNonCallable,PyAttributeOutsideInit
# pylint: disable=not-callable,attribute-defined-outside-init,invalid-name
@loader.tds
class SwmuteMod(loader.Module):
    """Deletes messages from certain users"""

    strings = {
        "name": "Swmute",
        "not_group": "🚫 <b>This command is for groups only</b>",
        "muted": "🔇 <b>Swmuted {user} for {time}</b>",
        "muted_forever": "🔇 <b>Swmuted {user} indefinitely</b>",
        "unmuted": "🔉 <b>Removed swmute from {user}</b>",
        "not_muted": "🚫 <b>This user wasn't muted</b>",
        "invalid_user": "🚫 <b>Provided username/id {entity} is invalid</b>",
        "no_mute_target": "🧐 <b>Whom should I mute?</b>",
        "no_unmute_target": "🧐 <b>Whom should I unmute?</b>",
        "mutes_empty": "😔 <b>There's no mutes in this group</b>",
        "muted_users": "📃 <b>Swmuted users at the moment:</b>\n{names}",
        "cleared": "🧹 <b>Cleared mutes in this chat</b>",
        "cleared_all": "🧹 <b>Cleared all mutes</b>",
        "s_one": "second",
        "s_few": "seconds",
        "s_many": "seconds",
        "m_one": "minute",
        "m_few": "minutes",
        "m_many": "minutes",
        "h_one": "hour",
        "h_few": "hours",
        "h_many": "hours",
        "d_one": "day",
        "d_few": "days",
        "d_many": "days",
    }

    strings_ru = {
        "_cls_doc": "Удаляет сообщения от выбранных пользователей",
        "_cmd_doc_swmute": (
            "<reply/username/id> <время> — Добавить пользователя в список swmute"
        ),
        "_cmd_doc_swunmute": (
            "<reply/username/id> — Удалить пользователя из списка swmute"
        ),
        "_cmd_doc_swmutelist": "Получить пользователей в списке swmute",
        "_cmd_doc_swmuteclear": (
            "<all> — Удалить всех пользователей из списка swmute в этом/всех чатах"
        ),
        "not_group": "🚫 <b>Эта команда предназначена только для групп</b>",
        "muted": "🔇 <b>{user} добавлен в список swmute на {time}</b>",
        "muted_forever": "🔇 <b>{user} добавлен в список swmute навсегда</b>",
        "unmuted": "🔉 <b>{user} удалён из списка swmute</b>",
        "not_muted": "🚫 <b>Этот пользователь не был в муте</b>",
        "invalid_user": "🚫 <b>Предоставленный юзернейм/айди {entity} некорректный</b>",
        "no_mute_target": "🧐 <b>Кого я должен замутить?</b>",
        "no_unmute_target": "🧐 <b>Кого я должен размутить?</b>",
        "mutes_empty": "😔 <b>В этой группе никто не в муте</b>",
        "muted_users": "📃 <b>Пользователи в списке swmute:</b>\n{names}",
        "cleared": "🧹 <b>Муты в этой группе очищены</b>",
        "cleared_all": "🧹 <b>Все муты очищены</b>",
        "s_one": "секунда",
        "s_few": "секунды",
        "s_many": "секунд",
        "m_one": "минута",
        "m_few": "минуты",
        "m_many": "минут",
        "h_one": "час",
        "h_few": "часа",
        "h_many": "часов",
        "d_one": "день",
        "d_few": "дня",
        "d_many": "дней",
    }

    async def client_ready(self):
        self.cleanup()

    def get(self, key: str, default: Any = None):
        """Get value from database"""
        return self.db.get(self.strings("name"), key, default)

    def set(self, key: str, value: Any):
        """Set value in database"""
        return self.db.set(self.strings("name"), key, value)

    def format_time(self, seconds: int, max_words: int = None) -> str:
        """Format time to human-readable variant"""
        words = []
        time_dict = {
            "d": seconds // 86400,
            "h": seconds % 86400 // 3600,
            "m": seconds % 3600 // 60,
            "s": seconds % 60,
        }

        for time_type, count in time_dict.items():
            if max_words and len(words) >= max_words:
                break

            if count != 0:
                words.append(
                    f"{count} {self.strings(time_type + '_' + plural_number(count))}"
                )

        return " ".join(words)

    def mute(self, chat_id: int, user_id: int, until_time: int = 0):
        """Add user to mute list"""
        chat_id = str(chat_id)
        user_id = str(user_id)

        mutes = self.get("mutes", {})
        mutes.setdefault(chat_id, {})
        mutes[chat_id][user_id] = until_time
        self.set("mutes", mutes)

        logger.debug("Muted user %s in chat %s", user_id, chat_id)

    def unmute(self, chat_id: int, user_id: int):
        """Remove user from mute list"""
        chat_id = str(chat_id)
        user_id = str(user_id)

        mutes = self.get("mutes", {})
        if chat_id in mutes and user_id in mutes[chat_id]:
            mutes[chat_id].pop(user_id)
        self.set("mutes", mutes)

        logger.debug("Unmuted user %s in chat %s", user_id, chat_id)

    def get_mutes(self, chat_id: int) -> List[int]:
        """Get current mutes for specified chat"""
        return [
            int(user_id)
            for user_id, until_time in self.get("mutes", {})
            .get(str(chat_id), {})
            .items()
            if until_time > time.time() or until_time == 0
        ]

    def get_mute_time(self, chat_id: int, user_id: int) -> int:
        """Get mute expiration timestamp"""
        return self.get("mutes", {}).get(str(chat_id), {}).get(str(user_id))

    def cleanup(self):
        """Cleanup expired mutes"""
        mutes = {}

        for chat_id, chat_mutes in self.get("mutes", {}).items():
            if new_chat_mutes := {
                user_id: until_time
                for user_id, until_time in chat_mutes.items()
                if until_time == 0 or until_time > time.time()
            }:
                mutes[chat_id] = new_chat_mutes

        self.set("mutes", mutes)

    def clear_mutes(self, chat_id: int = None):
        """Clear all mutes for given or all chats"""
        if chat_id:
            mutes = self.get("mutes", {})
            mutes.pop(str(chat_id), None)
            self.set("mutes", mutes)
        else:
            self.set("mutes", {})

    async def swmutecmd(self, message: Message):
        """<reply/username/id> <time> — Add user to swmute list"""
        if not message.is_group:
            return await utils.answer(message, self.strings("not_group"))

        args = utils.get_args(message)
        reply = await message.get_reply_message()

        if reply and reply.sender_id:
            user_id = reply.sender_id
            user = await self.client.get_entity(reply.sender_id)
            string_time = " ".join(args) if args else False
        elif args:
            try:
                user = await self.client.get_entity(
                    int(args[0]) if USER_ID_RE.match(args[0]) else args[0]
                )
                user_id = get_peer_id(user)
            except ValueError:
                return await utils.answer(message, self.strings("no_mute_target"))
            string_time = " ".join(args[1:]) if len(args) else False
        else:
            return await utils.answer(message, self.strings("no_mute_target"))

        if string_time:
            if mute_seconds := s2time(string_time):
                self.mute(message.chat_id, user_id, int(time.time() + mute_seconds))
                return await utils.answer(
                    message,
                    self.strings("muted").format(
                        time=self.format_time(mute_seconds), user=get_link(user)
                    ),
                )

        self.mute(message.chat_id, user_id)
        await utils.answer(
            message, self.strings("muted_forever").format(user=get_link(user))
        )

    async def swunmutecmd(self, message: Message):
        """<reply/username/id> — Remove swmute from user"""
        if not message.is_group:
            return await utils.answer(message, self.strings("not_group"))

        args = utils.get_args(message)
        reply = await message.get_reply_message()

        if reply and reply.sender_id:
            user_id = reply.sender_id
            user = await self.client.get_entity(reply.sender_id)
        elif args:
            try:
                user = await self.client.get_entity(
                    int(args[0]) if USER_ID_RE.match(args[0]) else args[0]
                )
                user_id = get_peer_id(user)
            except ValueError:
                return await utils.answer(message, self.strings("no_unmute_target"))
        else:
            return await utils.answer(message, self.strings("no_unmute_target"))

        self.unmute(message.chat_id, user_id)
        await utils.answer(message, self.strings("unmuted").format(user=get_link(user)))

    async def swmutelistcmd(self, message: Message):
        """Get list of swmuted users"""
        if not message.is_group:
            return await utils.answer(message, self.strings("not_group"))

        mutes = self.get_mutes(message.chat_id)
        if not mutes:
            return await utils.answer(message, self.strings("mutes_empty"))

        self.cleanup()

        muted_users = []
        for mute_id in mutes:
            text = "• "

            try:
                text += (
                    f"<i>{get_link(await self.client.get_entity(mute_id))}</i> "
                    f"(<code>{mute_id}</code>)"
                )
            except ValueError:
                text += f"<code>{mute_id}</code>"

            if until_ts := self.get_mute_time(message.chat_id, mute_id):
                time_formatted = self.format_time(
                    int(until_ts - time.time()),
                    max_words=2,
                )
                text += f" <b>({time_formatted} left)</b>"

            muted_users.append(text)

        await utils.answer(
            message, self.strings("muted_users").format(names="\n".join(muted_users))
        )

    async def swmuteclearcmd(self, message: Message):
        """<all> — Clear all swmutes in this chat/in all chats"""
        if "all" in utils.get_args_raw(
            message
        ) and await self.allmodules.check_security(
            message, security.OWNER | security.SUDO
        ):
            self.clear_mutes()
            await utils.answer(message, self.strings("cleared_all"))
        else:
            self.clear_mutes(message.chat_id)
            await utils.answer(message, self.strings("cleared"))

    async def watcher(self, message: Message):
        """Handles incoming messages"""
        if (
            isinstance(message, Message)
            and not message.out
            and message.is_group
            and message.sender_id in self.get_mutes(message.chat_id)
        ):
            # Without delete rights in the chat this fails on every message; stay quiet
            with contextlib.suppress(RPCError):
                await message.delete()

            logger.debug(
                "Deleted message from user %s in chat %s",
                message.sender_id,
                message.chat_id,
            )
