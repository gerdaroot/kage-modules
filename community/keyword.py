# ---------------------------------------------------------------------------------
#  /\_/\  🌐 This module was loaded through https://t.me/hikkamods_bot
# ( o.o )  🔐 Licensed under the GNU AGPLv3.
#  > ^ <   ⚠️ Owner of heta.hikariatama.ru doesn't take any responsibilities or intellectual property rights regarding this script
# ---------------------------------------------------------------------------------
# Name: keyword
# Author: hikariatama
# Commands:
# .kword | .kwords | .kwbl | .kwbllist
# ---------------------------------------------------------------------------------

#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html
# Modified for Kage by gerdaroot (https://github.com/gerdaroot/kage-modules), 2026-09-25

# scope: hikka_min 1.2.10

# meta pic: https://img.icons8.com/fluency/48/000000/macbook-chat.png
# meta banner: https://mods.hikariatama.ru/badges/keyword.jpg
# meta developer: @hikarimods
# scope: hikka_only

import contextlib
import re
import time

from telethon.tl.types import Message, PeerChannel, PeerChat
from telethon.utils import get_display_name

from .. import loader, utils

# other people can trigger replies from the owner's account; without a pause a spammed keyword means FloodWait
REPLY_COOLDOWN = 5

BOT_MARK = "🤖 "
FLAGS = ("r", "m", "l", "e", "c")


@loader.tds
class KeywordMod(loader.Module):
    """Allows you to create custom filters with regexes, commands and unlimited funcionality"""

    strings = {
        "name": "Keyword",
        "args": "🚫 <b>Args are incorrect</b>",
        "kw_404": '🚫 <b>Keyword "{}" not found</b>',
        "kw_added": "✅ <b>New keyword:\nTrigger: {}\nMessage: {}\n{}{}{}{}{}</b>",
        "kw_removed": '✅ <b>Keyword "{}" removed</b>',
        "kwbl_list": "🦊 <b>Blacklisted chats:</b>\n{}",
        "bl_added": "✅ <b>This chat is now blacklisted for Keywords</b>",
        "bl_removed": "✅ <b>This chat is now whitelisted for Keywords</b>",
        "sent": "🦊 <b>[Keywords]: Sent message to {}, triggered by {}:\n{}</b>",
        "kwords": "🦊 <b>Current keywords:\n</b>{}",
        "no_command": (
            "🚫 <b>Execution of command forbidden, because message contains reply</b>"
        ),
    }

    strings_ru = {
        "args": "🚫 <b>Неверные аргументы</b>",
        "kw_404": '🚫 <b>Кейворд "{}" не найден</b>',
        "kw_added": "✅ <b>Новый кейворд:\nТриггер: {}\nСообщение: {}\n{}{}{}{}{}</b>",
        "kw_removed": '✅ <b>Кейворд "{}" удален</b>',
        "kwbl_list": "🦊 <b>Чаты в черном списке:</b>\n{}",
        "bl_added": "✅ <b>Этот чат теперь в черном списке Кейвордов</b>",
        "bl_removed": "✅ <b>Этот чат больше не в черном списке Кейвордов</b>",
        "sent": "🦊 <b>[Кейворды]: Отправлено сообщение в {}, активировано {}:\n{}</b>",
        "kwords": "🦊 <b>Текущие кейворды:\n</b>{}",
        "no_command": (
            "🚫 <b>Команда не была выполнена, так как сообщение содержит реплай</b>"
        ),
        "_cmd_doc_kword": (
            "<кейворд | можно в кавычках | & для нескольких слов, которые должны быть в"
            " сообщении в любом порядке> <сообщение | оставь пустым для удаления"
            " кейворда> [-r для полного совпадения] [-m для автопрочтения сообщения]"
            " [-l для включения логирования] [-e для включения регулярных выражений]"
        ),
        "_cmd_doc_kwords": "Показать активные кейворды",
        "_cmd_doc_kwbl": "Добавить чат в черный список кейвордов",
        "_cmd_doc_kwbllist": "Показать чаты в черном списке",
        "_cls_doc": "Создавай кастомные кейворды с регулярными выражениями и командами",
    }

    strings_de = {
        "args": "🚫 <b>Falsche Argumente</b>",
        "kw_404": '🚫 <b>Keyword "{}" nicht gefunden</b>',
        "kw_added": "✅ <b>Neuer Keyword:\nTrigger: {}\nNachricht: {}\n{}{}{}{}{}</b>",
        "kw_removed": '✅ <b>Keyword "{}" entfernt</b>',
        "kwbl_list": "🦊 <b>Blacklisted Chats:</b>\n{}",
        "bl_added": "✅ <b>Dieser Chat ist nun blacklisted für Keywords</b>",
        "bl_removed": "✅ <b>Dieser Chat ist nun whitelisted für Keywords</b>",
        "sent": "🦊 <b>[Keywords]: Nachricht an {}, getriggert durch {}:\n{}</b>",
        "kwords": "🦊 <b>Aktuelle Keywords:\n</b>{}",
        "no_command": (
            "🚫 <b>Kommando nicht ausgeführt, da die Nachricht einen Reply enthält</b>"
        ),
        "_cmd_doc_kword": (
            "<keyword | kann in Anführungszeichen | & für mehrere Wörter, die in"
            " Nachricht in irgendeiner Reihenfolge sein müssen> <Nachricht | leer"
            " lassen um Keyword zu löschen> [-r für exakte Übereinstimmung] [-m für"
            " automatische Nachrichtenlöschung] [-l für Logging] [-e für reguläre"
            " Ausdrücke]"
        ),
        "_cmd_doc_kwords": "Zeige aktive Keywords",
        "_cmd_doc_kwbl": "Füge Chat zur Keyword Blacklist hinzu",
        "_cmd_doc_kwbllist": "Zeige Chats in der Keyword Blacklist",
        "_cls_doc": "Erstelle eigene Keywords mit regulären Ausdrücken und Befehlen",
    }

    strings_hi = {
        "args": "🚫 <b>गलत तर्क</b>",
        "kw_404": '🚫 <b>"{}" कीवर्ड नहीं मिला</b>',
        "kw_added": "✅ <b>नया कीवर्ड:\nट्रिगर: {}\nसंदेश: {}\n{}{}{}{}{}</b>",
        "kw_removed": '✅ <b>"{}" कीवर्ड हटा दिया</b>',
        "kwbl_list": "🦊 <b>ब्लैकलिस्टेड चैट्स:</b>\n{}",
        "bl_added": "✅ <b>यह चैट अब कीवर्ड ब्लैकलिस्ट में है</b>",
        "bl_removed": "✅ <b>यह चैट अब कीवर्ड व्हाइटलिस्ट में है</b>",
        "sent": "🦊 <b>[कीवर्ड्स]: {} को, {} ने ट्रिगर किया:\n{}</b>",
        "kwords": "🦊 <b>वर्तमान कीवर्ड्स:\n</b>{}",
        "no_command": (
            "🚫 <b>कमांड नहीं चलाया क्योंकि संदेश रिप्लाई का सामना कर रहा है</b>"
        ),
        "_cmd_doc_kword": (
            "<कीवर्ड | उदाहरण के लिए & | & के बाद एक से अधिक शब्द, जो संदेश में किसी भी"
            " क्रम में होने चाहिए> <संदेश | खाली छोड़ने से कीवर्ड हट जाएगा> [-r बिल्कुल"
            " मेल के लिए] [-m स्वचालित संदेश हटाने के लिए] [-l लॉगिंग के लिए] [-e"
            " रेगुलर एक्सप्रेशन के लिए]"
        ),
        "_cmd_doc_kwords": "वर्तमान कीवर्ड्स दिखाएं",
        "_cmd_doc_kwbl": "कीवर्ड ब्लैकलिस्ट में चैट जोड़ें",
        "_cmd_doc_kwbllist": "कीवर्ड ब्लैकलिस्ट में चैट दिखाएं",
        "_cls_doc": "रेगुलर एक्सप्रेशन और कमांड के साथ अपने कीवर्ड बनाएं",
    }

    strings_uz = {
        "args": "🚫 <b>Noto'g'ri argument</b>",
        "kw_404": '🚫 <b>"{}" kalit so\'z topilmadi</b>',
        "kw_added": "✅ <b>Yangi kalit so'z:\nTriger: {}\nXabar: {}\n{}{}{}{}{}</b>",
        "kw_removed": "✅ <b>\"{}\" kalit so'z o'chirildi</b>",
        "kwbl_list": "🦊 <b>Qora ro'yxatli guruhlar:</b>\n{}",
        "bl_added": "✅ <b>Bu guruh kalit so'zlarni qora ro'yxatga qo'shildi</b>",
        "bl_removed": "✅ <b>Bu guruh kalit so'zlarni oq ro'yxatga qo'shildi</b>",
        "sent": "🦊 <b>[Kalit so'zlarni]: {} ga, {} guruhga xabar jo'natdi:\n{}</b>",
        "kwords": "🦊 <b>Hozirgi kalit so'zlarni:\n</b>{}",
        "no_command": "🚫 <b>Komanda bajarilmadi chunki xabar javob qaytaradi</b>",
        "_cmd_doc_kword": (
            "<kalit so'z | & orqali bir nechta so'zlarni | & keyingi bir nechta so'z,"
            " xabarda biror tartibda bo'lishi kerak> <xabar | bo'sh qoldirish kalit"
            " so'zni o'chiradi> [-r to'g'ri moslik uchun] [-m avtomatik xabar o'chirish"
            " uchun] [-l yozuvni qayd etish uchun] [-e regular ifodalar uchun]"
        ),
        "_cmd_doc_kwords": "Hozirgi kalit so'zlarni ko'rsatish",
        "_cmd_doc_kwbl": "Qora ro'yxatga guruh qo'shish",
        "_cmd_doc_kwbllist": "Qora ro'yxatda guruhlar ro'yxatini ko'rsatish",
        "_cls_doc": "Regular ifodalarni va buyruqlarni ishlatib kalit so'z yarating",
    }

    strings_tr = {
        "args": "🚫 <b>Yanlış argüman</b>",
        "kw_404": '🚫 <b>"{}" anahtar kelime bulunamadı</b>',
        "kw_added": "✅ <b>Yeni anahtar kelime:\nTriger: {}\nMesaj: {}\n{}{}{}{}{}</b>",
        "kw_removed": '✅ <b>"{}" anahtar kelime kaldırıldı</b>',
        "kwbl_list": "🦊 <b>Kara liste sohbetler:</b>\n{}",
        "bl_added": "✅ <b>Bu sohbet anahtar kelimeleri kara listeye eklendi</b>",
        "bl_removed": "✅ <b>Bu sohbet anahtar kelimeleri açık listeye eklendi</b>",
        "sent": "🦊 <b>[Anahtar Kelimeler]: {}'a, {} sohbetine mesaj gönderdi:\n{}</b>",
        "kwords": "🦊 <b>Geçerli anahtar kelimeler:\n</b>{}",
        "no_command": "🚫 <b>Komut yürütülemedi çünkü mesaj yanıt veriyor</b>",
        "_cmd_doc_kword": (
            "<anahtar kelime | & ile birden çok sözcük | & sonra birden çok sözcük,"
            " mesajda herhangi bir sırayla olmalıdır> <mesaj | boş bırakmak anahtar"
            " kelimeyi kaldırır> [-r tam eşleme için] [-m otomatik mesaj silmek için]"
            " [-l kayıt için] [-e düzenli ifadeler için]"
        ),
        "_cmd_doc_kwords": "Geçerli anahtar kelimeleri göster",
        "_cmd_doc_kwbl": "Sohbeti kara listeye ekle",
        "_cmd_doc_kwbllist": "Kara listede sohbetleri göster",
        "_cls_doc": (
            "Anahtar kelimeleri oluşturmak için düzenli ifadeleri ve komutları kullanın"
        ),
    }

    async def client_ready(self):
        self._last_reply: dict[str, float] = {}
        self.keywords = self.get("keywords", {})
        self.bl = self.get("bl", [])

    async def kwordcmd(self, message: Message):
        """<keyword | could be in quotes | & for multiple words that should be in msg> <message | empty to remove keyword> [-r for full match] [-m for autoreading msg] [-l to log in pm] [-e for regular expressions]"""
        args = utils.get_args_raw(message)
        flags = {}
        for flag in FLAGS:
            pattern = rf"(?:^|\s)-{flag}(?=\s|$)"
            flags[flag] = bool(re.search(pattern, args))
            args = re.sub(pattern, "", args)

        restrict, ar, log, e, c = (flags[flag] for flag in FLAGS)
        args = args.strip()
        if not args:
            await utils.answer(message, self.strings("args"))
            return

        if args[0] == "'":
            kw = args[1 : args.find("'", 1)]
            args = args[args.find("'", 1) + 1 :]
        elif args[0] == '"':
            kw = args[1 : args.find('"', 1)]
            args = args[args.find('"', 1) + 1 :]
        else:
            kw = args.split()[0]
            try:
                args = args.split(maxsplit=1)[1]
            except Exception:
                args = ""

        if ph := args:
            ph = ph.strip()
            kw = kw.strip()
            self.keywords[kw] = [f"{BOT_MARK}{ph}", restrict, ar, log, e, c]
            self.set("keywords", self.keywords)
            return await utils.answer(
                message,
                self.strings("kw_added").format(
                    utils.escape_html(kw),
                    utils.escape_html(ph),
                    ("Restrict: yes\n" if restrict else ""),
                    ("Auto-read: yes\n" if ar else ""),
                    ("Log: yes" if log else ""),
                    ("Regex: yes" if e else ""),
                    ("Command: yes" if c else ""),
                ),
            )
        else:
            if kw not in self.keywords:
                return await utils.answer(
                    message, self.strings("kw_404").format(utils.escape_html(kw))
                )

            del self.keywords[kw]

            self.set("keywords", self.keywords)
            return await utils.answer(
                message, self.strings("kw_removed").format(utils.escape_html(kw))
            )

    async def kwordscmd(self, message: Message):
        """List current kwords"""
        res = ""
        for kw, ph in self.keywords.items():
            res += (
                "<code>"
                + utils.escape_html(kw)
                + "</code>\n<b>Message: "
                + utils.escape_html(ph[0])
                + "\n"
                + ("Restrict: yes\n" if ph[1] else "")
                + ("Auto-read: yes\n" if ph[2] else "")
                + ("Log: yes" if ph[3] else "")
                + ("Regex: yes" if len(ph) > 4 and ph[4] else "")
                + ("Command: yes" if len(ph) > 5 and ph[5] else "")
                + "</b>"
            )
            if res[-1] != "\n":
                res += "\n"

            res += "\n"

        await utils.answer(message, self.strings("kwords").format(res))

    @loader.group_admin_ban_users
    async def kwblcmd(self, message: Message):
        """Blacklist chat from answering keywords"""
        cid = utils.get_chat_id(message)
        if cid not in self.bl:
            self.bl.append(cid)
            self.set("bl", self.bl)
            return await utils.answer(message, self.strings("bl_added"))
        else:
            self.bl.remove(cid)
            self.set("bl", self.bl)
            return await utils.answer(message, self.strings("bl_removed"))

    async def kwbllistcmd(self, message: Message):
        """List blacklisted chats"""
        res = ""
        for chat_id in self.bl:
            title = await self._resolve_title(chat_id)
            res += f"  👺 {utils.escape_html(title)} (<code>{chat_id}</code>)\n"

        if not res:
            res = "<i>No</i>"

        return await utils.answer(message, self.strings("kwbl_list").format(res))

    async def _resolve_title(self, chat_id: int) -> str:
        # Blacklist stores ids without the -100 prefix, so the peer type is unknown
        for peer in (chat_id, PeerChannel(chat_id), PeerChat(chat_id)):
            with contextlib.suppress(Exception):
                return get_display_name(await self._client.get_entity(peer))
        return str(chat_id)

    def _is_own_service_message(self, message: Message) -> bool:
        # Our own replies and commands also reach the watcher; answering them would loop
        return message.out and message.raw_text.startswith(
            (BOT_MARK, self.get_prefix())
        )

    async def watcher(self, message: Message):
        with contextlib.suppress(Exception):
            cid = utils.get_chat_id(message)
            if cid in self.bl or self._is_own_service_message(message):
                return

            for kw, ph in self.keywords.copy().items():
                if len(ph) > 4 and ph[4]:
                    try:
                        if not re.match(kw, message.raw_text):
                            continue
                    except Exception:
                        continue
                else:
                    kws = [
                        _.strip() for _ in ([kw] if "&" not in kw else kw.split("&"))
                    ]
                    text = message.raw_text.lower()
                    trigger = False
                    for k in kws:
                        if k.lower() in text:
                            trigger = True
                            if not ph[1]:
                                break
                        elif ph[1]:
                            trigger = False
                            break

                    if not trigger:
                        continue

                now = time.monotonic()
                if now - self._last_reply.get(cid, 0) < REPLY_COOLDOWN:
                    return
                self._last_reply[cid] = now

                offset = 2

                if (
                    len(ph) > 5
                    and ph[5]
                    and ph[0][offset:].startswith(self.get_prefix())
                ):
                    offset += 1

                if ph[2]:
                    await self._client.send_read_acknowledge(
                        message.chat_id, clear_mentions=True
                    )

                if ph[3]:
                    chat = await message.get_chat()
                    await self._client.send_message(
                        "me",
                        self.strings("sent").format(
                            utils.escape_html(get_display_name(chat)),
                            utils.escape_html(kw),
                            utils.escape_html(ph[0]),
                        ),
                    )

                if not message.reply_to_msg_id:
                    ms = await utils.answer(message, ph[0])
                else:
                    ms = await message.respond(ph[0])

                ms.text = ph[0][2:]

                if len(ph) > 5 and ph[5]:
                    if ph[0][offset:].split()[0] == "del":
                        await message.delete()
                        await ms.delete()
                    elif not message.reply_to_msg_id:
                        cmd = ph[0][offset:].split()[0]
                        if cmd in self.allmodules.commands:
                            await self.allmodules.commands[cmd](ms)
                    else:
                        await ms.respond(self.strings("no_command"))
