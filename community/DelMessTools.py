# ---------------------------------------------------------------------------------
#░█▀▄░▄▀▀▄░█▀▄░█▀▀▄░█▀▀▄░█▀▀▀░▄▀▀▄░░░█▀▄▀█
#░█░░░█░░█░█░█░█▄▄▀░█▄▄█░█░▀▄░█░░█░░░█░▀░█
#░▀▀▀░░▀▀░░▀▀░░▀░▀▀░▀░░▀░▀▀▀▀░░▀▀░░░░▀░░▒▀
# Name: DelMessTools
# Description: Module to manage and delete your messages in the current chat
# Author: @codrago_m
# ---------------------------------------------------------------------------------
# 🔒    Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html
# Modified for Kage by gerdaroot (https://github.com/gerdaroot/kage-modules), 2026-09-25
# ---------------------------------------------------------------------------------
# Author: @codrago
# Commands: nopurge, purgetime, purgelength, purgekeyword, purge
# scope: hikka_only
# meta developer: @codrago_m
# meta banner: https://raw.githubusercontent.com/coddrago/modules/refs/heads/main/banner.png
# meta pic: https://envs.sh/HJx.webp
# ---------------------------------------------------------------------------------

__version__ = (1, 2, 0)

from collections.abc import Callable
from datetime import datetime, timezone

from hikkatl.tl.types import DocumentAttributeFilename, Message

from .. import loader, utils

TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
TYPE_FLAGS = {"-img": "img", "-voice": "voice", "-file": "file"}
EACH_TOPIC_FLAG = "-all"
DELETE_BATCH_SIZE = 100


class DelMessTools(loader.Module):
    """Module to manage and delete your messages in the current chat"""

    strings = {
        "name": "DelMessTools",
        "purge_complete": "All your messages have been deleted.",
        "purge_reply_complete": "Messages up to the replied message have been deleted.",
        "purge_keyword_complete": "Messages containing the keyword have been deleted.",
        "purge_time_complete": "Messages within the specified time range have been deleted.",
        "purge_length_complete": "Messages with the specified length have been deleted.",
        "enabled": "It's not operational now anyway.",
        "disabled": "Operation status changed to disabled.",
        "interrupted": "The deletion was interrupted because you changed your mind.",
        "none": "You didn't even intend to delete anything here, but anyway it's disabled now.",
        "no_args": "Please specify anything because you didn't.",
        "no_keyword": "Please specify a keyword to delete messages.",
        "bad_time": "Please specify the start and end time (UTC) in the format: YYYY-MM-DD HH:MM:SS YYYY-MM-DD HH:MM:SS",
        "bad_length": "Please specify a valid length.",
    }

    strings_ru = {
        "purge_complete": "Все ваши сообщения были удалены.",
        "purge_reply_complete": "Сообщения до указанного ответа были удалены.",
        "purge_keyword_complete": "Сообщения, содержащие ключевое слово, были удалены.",
        "purge_time_complete": "Сообщения в указанном временном диапазоне были удалены.",
        "purge_length_complete": "Сообщения указанной длины были удалены.",
        "enabled": "Оно итак сейчас не работает.",
        "disabled": "Режим работы изменен на выключено.",
        "interrupted": "Удаление было прервано т.к вы передумали.",
        "none": "Вы даже не пытались ничего здесь удалить, в любом случае сейчас оно выключено.",
        "no_args": "Укажите аргументы.",
        "no_keyword": "Укажите ключевое слово.",
        "bad_time": "Укажите начало и конец (UTC) в формате: YYYY-MM-DD HH:MM:SS YYYY-MM-DD HH:MM:SS",
        "bad_length": "Укажите корректную длину.",
    }

    def __init__(self):
        # chat_id -> True while a purge runs there, False once .nopurge was used
        self._running: dict[int, bool] = {}

    async def purgecmd(self, message: Message):
        """ [reply] [-img] [-voice] [-file] [-all] - delete all your messages in current chat or only ones up to the message you replied to
        -all - to delete messages in each topic if this is a forum otherwise the flag'll just be ingored
        """
        reply = await message.get_reply_message()
        _, types_filter, is_each = self._parse_args(message)
        min_id = reply.id - 1 if reply else 0

        if not await self._purge(message, types_filter, is_each, lambda _: True, min_id):
            return
        await utils.answer(
            message,
            self.strings["purge_reply_complete" if reply else "purge_complete"],
        )

    async def purgekeywordcmd(self, message: Message):
        """ <keyword> [-img] [-voice] [-file] [-all] - delete all your messages containing the specified keyword in the current chat
        -all - to delete messages in each topic if this is a forum otherwise the flag'll just be ingored
        """
        if not utils.get_args_raw(message):
            return await utils.answer(message, self.strings["no_args"])

        keyword, types_filter, is_each = self._parse_args(message)
        if not keyword:
            return await utils.answer(message, self.strings["no_keyword"])

        keyword = keyword.lower()
        if await self._purge(
            message,
            types_filter,
            is_each,
            lambda msg: keyword in (msg.raw_text or "").lower(),
        ):
            await utils.answer(message, self.strings["purge_keyword_complete"])

    async def purgetimecmd(self, message: Message):
        """ <start_time> <end_time> [-img] [-voice] [-file] [-all] - delete all your messages within the specified time range in the current chat
        -all - to delete messages in each topic if this is a forum otherwise the flag'll just be ingored
        Time format (UTC): YYYY-MM-DD HH:MM:SS
        """
        if not utils.get_args_raw(message):
            return await utils.answer(message, self.strings["no_args"])

        args, types_filter, is_each = self._parse_args(message)
        words = args.split()
        try:
            start_time, end_time = (
                datetime.strptime(" ".join(pair), TIME_FORMAT).replace(tzinfo=timezone.utc)
                for pair in (words[0:2], words[2:4])
            )
        except ValueError:
            return await utils.answer(message, self.strings["bad_time"])

        if await self._purge(
            message,
            types_filter,
            is_each,
            lambda msg: start_time <= msg.date <= end_time,
        ):
            await utils.answer(message, self.strings["purge_time_complete"])

    async def purgelengthcmd(self, message: Message):
        """ <length> [-img] [-voice] [-file] [-all] - delete all your messages with the specified length in the current chat
        -all - to delete messages in each topic if this is a forum otherwise the flag'll just be ingored
        """
        if not utils.get_args_raw(message):
            return await utils.answer(message, self.strings["no_args"])

        args, types_filter, is_each = self._parse_args(message)
        if not args.isdigit():
            return await utils.answer(message, self.strings["bad_length"])

        length = int(args)
        if await self._purge(
            message,
            types_filter,
            is_each,
            lambda msg: len(msg.raw_text or "") == length,
        ):
            await utils.answer(message, self.strings["purge_length_complete"])

    async def nopurgecmd(self, message: Message):
        """
        Interrupt the deletion process
        Use in the chat where you've previously started deletion
        """
        chat_id = utils.get_chat_id(message)
        previous = self._running.get(chat_id)
        self._running[chat_id] = False

        if previous is True:
            await utils.answer(message, self.strings["disabled"])
        elif previous is False:
            await utils.answer(message, self.strings["enabled"])
        else:
            await utils.answer(message, self.strings["none"])

    async def _purge(
        self,
        message: Message,
        types_filter: set[str],
        is_each: bool,
        matches: Callable[[Message], bool],
        min_id: int = 0,
    ) -> bool:
        """Delete own messages accepted by `matches`; return False if interrupted."""
        chat_id = utils.get_chat_id(message)
        self._running[chat_id] = True
        is_forum = getattr(await message.get_chat(), "forum", False)
        topic = utils.get_topic(message)
        pending: list[int] = []

        async for msg in self.client.iter_messages(
            message.peer_id, from_user="me", min_id=min_id
        ):
            if not self._running.get(chat_id):
                await self._delete(message, pending)
                await utils.answer(message, self.strings["interrupted"])
                return False

            if msg.id == message.id:
                continue
            if is_forum and not is_each and utils.get_topic(msg) != topic:
                continue
            if not (self._is_valid_type(msg, types_filter) and matches(msg)):
                continue

            pending.append(msg.id)
            if len(pending) >= DELETE_BATCH_SIZE:
                await self._delete(message, pending)

        await self._delete(message, pending)
        self._running[chat_id] = False
        return True

    async def _delete(self, message: Message, ids: list[int]):
        if ids:
            await self.client.delete_messages(message.peer_id, ids)
            ids.clear()

    @staticmethod
    def _parse_args(message: Message) -> tuple[str, set[str], bool]:
        """Split command args into (text, type filters, each-topic flag)."""
        words = utils.get_args_raw(message).split()
        types_filter = {TYPE_FLAGS[word] for word in words if word in TYPE_FLAGS}
        text = " ".join(
            word for word in words if word not in TYPE_FLAGS and word != EACH_TOPIC_FLAG
        )
        return text, types_filter, EACH_TOPIC_FLAG in words

    @staticmethod
    def _is_valid_type(message: Message, types_filter: set[str]) -> bool:
        if not types_filter:
            return True

        return (
            ("img" in types_filter and bool(message.photo))
            or ("voice" in types_filter and bool(message.voice))
            or (
                "file" in types_filter
                and message.document is not None
                and any(
                    isinstance(attr, DocumentAttributeFilename)
                    for attr in message.document.attributes
                )
            )
        )
