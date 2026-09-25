# ---------------------------------------------------------------------------------
# ░█▀▄░▄▀▀▄░█▀▄░█▀▀▄░█▀▀▄░█▀▀▀░▄▀▀▄░░░█▀▄▀█
# ░█░░░█░░█░█░█░█▄▄▀░█▄▄█░█░▀▄░█░░█░░░█░▀░█
# ░▀▀▀░░▀▀░░▀▀░░▀░▀▀░▀░░▀░▀▀▀▀░░▀▀░░░░▀░░▒▀
# Name: GuestBotCleaner
# Description: Deletes messages sent by guest bots not participating in the chat
# Author: @codrago_m
# ---------------------------------------------------------------------------------
# 🔒    Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html
# Modified for Kage by gerdaroot (https://github.com/gerdaroot/kage-modules), 2026-09-25
# ---------------------------------------------------------------------------------
# Author: @codrago
# Commands: guestbotcleaner, gbc
# scope: heroku_only
# scope: heroku_min 2.0.0
# meta developer: @codrago_m
# meta banner: https://raw.githubusercontent.com/coddrago/modules/refs/heads/main/banner.png
# ---------------------------------------------------------------------------------

__version__ = (1, 3)

import logging
import time

from telethon.errors import UserNotParticipantError
from telethon.tl.functions.channels import GetParticipantRequest

from .. import loader, utils

logger = logging.getLogger(__name__)

# Membership is checked with an API call per bot message, so cache it to stay clear of flood limits.
MEMBERSHIP_CACHE_TTL = 600


@loader.tds
class GuestBotCleanerMod(loader.Module):
    """Deletes messages from guest bots — bots that are not members of the chat"""

    strings = {
        "name": "GuestBotCleaner",
        "_cfg_doc_enabled": "Включить/выключить удаление сообщений гостевых ботов.",
        "_cfg_doc_watched_chats": "Список ID чатов, в которых работает модуль (пусто = все чаты).",
        "_cfg_doc_whitelist_bots": "Список ID ботов, которых НЕ нужно трогать (белый список).",
        "_cfg_doc_notify": "Слать уведомление в топик при удалении.",
        "deleted": (
            "<tg-emoji emoji-id=5219776129669276751>❌</tg-emoji> "
            "<b>GuestBotCleaner:</b> удалено сообщение от гостевого бота "
            "<code>{bot_id}</code> (@{username}) в чате <code>{chat_id}</code>."
        ),
        "enabled": "<tg-emoji emoji-id=5208808350858364013>✅</tg-emoji> <b>GuestBotCleaner включён.</b>",
        "disabled": "<tg-emoji emoji-id=5219776129669276751>❌</tg-emoji> <b>GuestBotCleaner выключен.</b>",
    }

    strings_en = {
        "name": "GuestBotCleaner",
        "_cfg_doc_enabled": "Enable/disable guest bot message deletion.",
        "_cfg_doc_watched_chats": "List of chat IDs where the module is active (empty = all chats).",
        "_cfg_doc_whitelist_bots": "List of bot IDs that should never be touched (whitelist).",
        "_cfg_doc_notify": "Send a notification to a forum topic when a message is deleted.",
        "deleted": (
            "<tg-emoji emoji-id=5219776129669276751>❌</tg-emoji> "
            "<b>GuestBotCleaner:</b> deleted message from guest bot "
            "<code>{bot_id}</code> (@{username}) in chat <code>{chat_id}</code>."
        ),
        "enabled": "<tg-emoji emoji-id=5208808350858364013>✅</tg-emoji> <b>GuestBotCleaner enabled.</b>",
        "disabled": "<tg-emoji emoji-id=5219776129669276751>❌</tg-emoji> <b>GuestBotCleaner disabled.</b>",
    }

    def __init__(self):
        self._notif_topic = None
        self._membership: dict[tuple[int, int], tuple[bool, float]] = {}
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "enabled",
                # off until the owner opts in: when on it deletes bot messages in every group they admin
                False,
                doc=lambda: self.strings("_cfg_doc_enabled"),
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "watched_chats",
                [],
                doc=lambda: self.strings("_cfg_doc_watched_chats"),
                validator=loader.validators.Series(
                    validator=loader.validators.TelegramID()
                ),
            ),
            loader.ConfigValue(
                "whitelist_bots",
                [],
                doc=lambda: self.strings("_cfg_doc_whitelist_bots"),
                validator=loader.validators.Series(
                    validator=loader.validators.TelegramID()
                ),
            ),
            loader.ConfigValue(
                "notify",
                False,
                doc=lambda: self.strings("_cfg_doc_notify"),
                validator=loader.validators.Boolean(),
            ),
        )

    async def _get_notif_topic(self):
        # Created lazily: asset_forum_topic raises without an assets channel, which would break loading.
        if not self._notif_topic:
            self._notif_topic = await utils.asset_forum_topic(
                self._client,
                self._db,
                self._assets_channel_id(),
                self.strings("name"),
                description="Notifications about deleted guest bot messages.",
            )
        return self._notif_topic

    def _assets_channel_id(self) -> int:
        return self._db.get("heroku.forums", "channel_id", 0)

    async def _is_member(self, chat_id: int, user_id: int) -> bool:
        """Check if user_id is a member of chat_id"""
        key = (chat_id, user_id)
        cached = self._membership.get(key)
        if cached and cached[1] > time.monotonic():
            return cached[0]

        try:
            await self._client(
                GetParticipantRequest(channel=chat_id, participant=user_id)
            )
            is_member = True
        except UserNotParticipantError:
            is_member = False
        except Exception:
            # Unknown state (basic group, no rights, network): never delete on doubt.
            return True

        self._membership[key] = (is_member, time.monotonic() + MEMBERSHIP_CACHE_TTL)
        return is_member

    async def _notify(self, bot_id: int, username: str, chat_id: int):
        try:
            topic = await self._get_notif_topic()
            await self.inline.bot.send_message(
                # The bot client needs the marked -100 form; the DB stores the bare channel id.
                int(f"-100{self._assets_channel_id()}"),
                self.strings("deleted").format(
                    bot_id=bot_id,
                    username=utils.escape_html(username),
                    chat_id=chat_id,
                ),
                disable_web_page_preview=True,
                message_thread_id=topic.id,
            )
        except Exception:
            logger.exception("Failed to send GuestBotCleaner notification")

    @loader.command(alias="gbc")
    async def guestbotcleaner(self, message):
        """Toggle guest bot message deletion"""
        self.config["enabled"] = not self.config["enabled"]
        status_key = "enabled" if self.config["enabled"] else "disabled"
        await utils.answer(message, self.strings(status_key))

    @loader.watcher("only_groups")
    async def watcher(self, message):
        """Watch group messages and remove non-member bot posts"""
        if not self.config["enabled"] or not getattr(message, "sender_id", None):
            return

        chat_id = utils.get_chat_id(message)
        if self.config["watched_chats"] and chat_id not in self.config["watched_chats"]:
            return

        sender = getattr(message, "sender", None)
        if sender is None:
            try:
                sender = await self._client.get_entity(message.sender_id)
            except Exception:
                return

        if not getattr(sender, "bot", False) or sender.id in self.config["whitelist_bots"]:
            return

        if await self._is_member(chat_id, sender.id):
            return

        try:
            await message.delete()
        except Exception:
            return

        if self.config["notify"]:
            await self._notify(sender.id, getattr(sender, "username", None) or str(sender.id), chat_id)
