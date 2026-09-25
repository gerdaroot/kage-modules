# ---------------------------------------------------------------------------------
# ░█▀▄░▄▀▀▄░█▀▄░█▀▀▄░█▀▀▄░█▀▀▀░▄▀▀▄░░░█▀▄▀█
# ░█░░░█░░█░█░█░█▄▄▀░█▄▄█░█░▀▄░█░░█░░░█░▀░█
# ░▀▀▀░░▀▀░░▀▀░░▀░▀▀░▀░░▀░▀▀▀▀░░▀▀░░░░▀░░▒▀
#
#  _____      _   _                  
# | ____|_  _| |_| |_ __ _ ___ _   _ 
# |  _| \ \/ / __| __/ _` / __| | | |
# | |___ >  <| |_| || (_| \__ \ |_| |
# |_____/_/\_\\__|\__\__,_|___/\__, |
#                               |___/ 
# Name: PMBan
# Description: Ban in pm for time
# Author: @codrago_m, @exttasy1
# ---------------------------------------------------------------------------------
# 🔒    Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html
# Modified for Kage by gerdaroot (https://github.com/gerdaroot/kage-modules), 2026-09-25
# ---------------------------------------------------------------------------------
# Author: @codrago, @exttasy1
# Commands: pmban, pmunban
# scope: hikka_only
# meta developer: @codrago_m, @exttasy1
# meta banner: https://raw.githubusercontent.com/coddrago/modules/refs/heads/main/banner.png
# meta pic: https://envs.sh/Hoh.webp
# ---------------------------------------------------------------------------------

__version__ = (1, 1, 0)

import logging
import re
import time

from telethon.tl.functions.contacts import BlockRequest, UnblockRequest

from .. import loader, utils

logger = logging.getLogger(__name__)

DURATION_RE = re.compile(r"^(\d+)([dhms]?)$")
UNIT_SECONDS = {"d": 86400, "h": 3600, "m": 60, "s": 1, "": 1}
TIME_UNITS = (("day", 86400), ("hour", 3600), ("minute", 60), ("second", 1))


def parse_duration(text: str) -> int | None:
    """Parse `30`, `30s`, `10m`, `2h`, `1d` into seconds; None if malformed."""
    match = DURATION_RE.match(text.strip().lower())
    if not match:
        return None
    return int(match[1]) * UNIT_SECONDS[match[2]]


def format_duration(seconds: int) -> str:
    if seconds <= 0:
        return "forever"

    parts = []
    for name, size in TIME_UNITS:
        count, seconds = divmod(seconds, size)
        if count:
            parts.append(f"{count} {name}{'' if count == 1 else 's'}")
    return "for " + " ".join(parts)


@loader.tds
class PMBan(loader.Module):
    """Ban in pm for time"""

    strings = {
        "name": "PMBan",
        "banned": "<b><emoji document_id=5021905410089550576>✅</emoji> User succesfully banned {}.</b>",
        "already_banned": "<b><emoji document_id=5980953710157632545>❌</emoji> User already has been banned</b>",
        "unbanned": "<b><emoji document_id=5021905410089550576>✅</emoji> User succesfully unbanned.</b>",
        "not_banned": "<b><emoji document_id=5980953710157632545>❌</emoji> User not banned</b>",
        "not_pm": "<b><emoji document_id=5980953710157632545>❌</emoji> Use this command in a private chat with the user.</b>",
        "no_target": "<b><emoji document_id=5980953710157632545>❌</emoji> User not found, use this command in a private chat or in response to user messages.</b>",
        "bad_time": "<b><emoji document_id=5980953710157632545>❌</emoji> Invalid time. Examples: 30s, 10m, 2h, 1d</b>",
        "unban_notice": "<b><emoji document_id=5021905410089550576>✅</emoji> You have been successfully unbanned.</b>",
    }

    def _bans(self) -> dict[str, int]:
        """user_id -> unix time the ban ends, 0 for a permanent ban."""
        return self.get("bans", {})

    @loader.loop(interval=10, autostart=True)
    async def _unban_expired(self):
        bans = self._bans()
        now = time.time()
        expired = [uid for uid, until in bans.items() if until and until <= now]
        if not expired:
            return

        # Drop entries before calling Telegram so a failing unblock can't repeat forever
        self.set("bans", {uid: until for uid, until in bans.items() if uid not in expired})
        for user_id in map(int, expired):
            try:
                await self.client(UnblockRequest(id=user_id))
                await self.client.send_message(user_id, self.strings["unban_notice"])
            except Exception:
                logger.exception("Failed to lift PM ban for %s", user_id)

    @loader.command()
    async def pmban(self, message):
        """[time: 30s/10m/2h/1d] | ban in PM for time, forever if no time given"""
        if not message.is_private:
            await utils.answer(message, self.strings["not_pm"])
            return

        user_id = message.chat_id
        bans = self._bans()
        if str(user_id) in bans:
            await utils.answer(message, self.strings["already_banned"])
            return

        args = utils.get_args_raw(message)
        duration = parse_duration(args) if args else 0
        if duration is None:
            await utils.answer(message, self.strings["bad_time"])
            return

        await self.client(BlockRequest(id=user_id))
        bans[str(user_id)] = int(time.time()) + duration if duration else 0
        self.set("bans", bans)
        await utils.answer(message, self.strings["banned"].format(format_duration(duration)))

    @loader.command()
    async def pmunban(self, message):
        """[reply] | unban in PM"""
        reply = await message.get_reply_message()
        if reply:
            user_id = reply.sender_id
        elif message.is_private:
            user_id = message.chat_id
        else:
            await utils.answer(message, self.strings["no_target"])
            return

        bans = self._bans()
        if bans.pop(str(user_id), None) is None:
            await utils.answer(message, self.strings["not_banned"])
            return

        self.set("bans", bans)
        await self.client(UnblockRequest(id=user_id))
        await utils.answer(message, self.strings["unbanned"])
