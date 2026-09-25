# ---------------------------------------------------------------------------------
#  /\_/\  🌐 This module was loaded through https://t.me/hikkamods_bot
# ( o.o )  🔐 Licensed under the GNU AGPLv3.
#  > ^ <   ⚠️ Owner of heta.hikariatama.ru doesn't take any responsibilities or intellectual property rights regarding this script
# ---------------------------------------------------------------------------------
# Name: surl
# Author: hikariatama
# Commands:
# .autosurl | .surl
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

# meta pic: https://img.icons8.com/external-xnimrodx-lineal-color-xnimrodx/512/000000/external-short-shopping-mall-xnimrodx-lineal-color-xnimrodx.png
# meta banner: https://mods.hikariatama.ru/badges/surl.jpg
# meta developer: @hikarimods
# scope: hikka_only

import logging

import aiohttp
from telethon.tl.types import Message, MessageEntityUrl
from telethon.utils import get_inner_text

from .. import loader, utils

logger = logging.getLogger(__name__)

# gg.gg and owo.vc no longer create links, so only engines with a working API are offered.
ENGINES = {
    "isgd": ("https://is.gd/create.php", {"format": "simple"}),
    "tinyurl": ("https://tinyurl.com/api-create.php", {}),
}
DEFAULT_ENGINE = "tinyurl"
TIMEOUT = aiohttp.ClientTimeout(total=15)


def extract_urls(message: Message) -> list[str]:
    entities = [
        entity
        for entity in getattr(message, "entities", None) or []
        if isinstance(entity, MessageEntityUrl)
    ]
    return get_inner_text(message.raw_text, entities) if entities else []


@loader.tds
class AutoShortenerMod(loader.Module):
    """Automatically shortens urls in your messages, which are larger than specified threshold"""

    strings = {
        "name": "AutoShortener",
        "state": "🔗 <b>Automatic url shortener is now {}</b>",
        "no_args": "🔗 <b>No link to shorten</b>",
        "on": "on",
        "off": "off",
    }

    strings_ru = {
        "state": "🔗 <b>Автоматический сократитель ссылок теперь {}</b>",
        "no_args": "🔗 <b>Не указана ссылка для сокращения</b>",
        "_cmd_doc_autosurl": "Включить\\выключить автоматическое сокращение ссылок",
        "_cmd_doc_surl": "[ссылка] [движок]- Сократить ссылку",
        "_cls_doc": (
            "Автоматически сокращает ссылки в твоих сообщениях, если они длиннее"
            " значения в конфиге"
        ),
        "on": "включен",
        "off": "выключен",
    }

    strings_de = {
        "state": "🔗 <b>Automatisches URL-Kürzen ist jetzt {}</b>",
        "no_args": "🔗 <b>Kein Link zum Kürzen</b>",
        "_cmd_doc_autosurl": (
            "Aktivieren\\Deaktivieren Sie das automatische Kürzen von URLs"
        ),
        "_cmd_doc_surl": "[URL] [Engine] - URL kürzen",
        "_cls_doc": (
            "Kürzt automatisch URLs in Ihren Nachrichten, wenn sie länger sind als"
            " Wert in der Konfiguration"
        ),
        "on": "Aktiviert",
        "off": "Deaktiviert",
    }

    strings_tr = {
        "state": "🔗 <b>Otomatik URL kısaltıcı şimdi {}</b>",
        "no_args": "🔗 <b>Kısaltılacak URL yok</b>",
        "_cmd_doc_autosurl": (
            "URL'leri otomatik olarak kısaltmayı etkinleştirin\\devre dışı bırakın"
        ),
        "_cmd_doc_surl": "[URL] [motor] - URL kısalt",
        "_cls_doc": (
            "URL'leri, yapılandırmanın değerinden daha uzun olduğunda mesajlarınızda"
            " otomatik olarak kısaltır"
        ),
        "on": "açık",
        "off": "kapalı",
    }

    strings_hi = {
        "state": "🔗 <b>ऑटो यूआरएल शॉर्टनर अब {} है</b>",
        "no_args": "🔗 <b>संक्षिप्त करने के लिए कोई लिंक नहीं</b>",
        "_cmd_doc_autosurl": "URL को स्वचालित रूप से छोटा करना चालू\\बंद करें",
        "_cmd_doc_surl": "[URL] [Engine] - URL को छोटा करें",
        "_cls_doc": (
            "अपने संदेशों में यूआरएल को छोटा करता है, जब वे विन्यास में निर्दिष्ट मान"
            " से अधिक होते हैं"
        ),
        "on": "चालू",
        "off": "बंद",
    }

    strings_uz = {
        "state": "🔗 <b>URL avtomatik qisqartiruvchisi hozir {}</b>",
        "no_args": "🔗 <b>Qisqartiladigan URL yo'q</b>",
        "_cmd_doc_autosurl": "URL'ni avtomatik ravishda qisqartishni yoqish\\o'chirish",
        "_cmd_doc_surl": "[URL] [mashina] - URL'ni qisqartirish",
        "_cls_doc": (
            "So'rovlarizdagi URL'ni konfiguratsiyadagi qiymatdan katta bo'lganda"
            " avtomatik ravishda qisqartadi"
        ),
        "on": "yoqilgan",
        "off": "o'chirilgan",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "threshold",
                80,
                lambda: "Urls larger than this value will be automatically shortened",
                validator=loader.validators.Integer(minimum=50),
            ),
            loader.ConfigValue(
                "auto_engine",
                DEFAULT_ENGINE,
                lambda: "Engine to auto-shorten urls with",
                validator=loader.validators.Choice(list(ENGINES)),
            ),
        )

    async def autosurlcmd(self, message: Message):
        """Toggle automatic url shortener"""
        state = not self.get("state", False)
        self.set("state", state)
        await utils.answer(
            message, self.strings("state").format(self.strings("on" if state else "off"))
        )

    async def surlcmd(self, message: Message):
        """[url] [engine] - Shorten url"""
        args = utils.get_args(message)
        engine = args[-1] if args and args[-1] in ENGINES else DEFAULT_ENGINE

        if urls := extract_urls(message):
            shortened = [await self.shorten(url, engine) for url in urls]
            await utils.answer(message, utils.escape_html(" | ".join(shortened)))
            return

        reply = await message.get_reply_message()
        if not reply or not (urls := extract_urls(reply)):
            await utils.answer(message, self.strings("no_args"))
            return

        text = reply.text
        for url in urls:
            text = text.replace(url, await self.shorten(url, engine))

        await utils.answer(message, text)

    @staticmethod
    async def shorten(url: str, engine: str = DEFAULT_ENGINE) -> str:
        """Return the short link, or the original url if every engine fails"""
        # shorteners go down now and then (is.gd answers "database insert failed"), so fall back to the others
        order = [engine] + [name for name in ENGINES if name != engine]
        async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
            for name in order:
                endpoint, params = ENGINES.get(name, ENGINES[DEFAULT_ENGINE])
                try:
                    async with session.get(endpoint, params={**params, "url": url}) as resp:
                        short = (await resp.text()).strip()
                except (aiohttp.ClientError, TimeoutError):
                    logger.debug("Failed to shorten %s with %s", url, name, exc_info=True)
                    continue
                if resp.status == 200 and short.startswith("https://"):
                    return short
        return url

    async def watcher(self, message: Message):
        if (
            not self.get("state", False)
            or not getattr(message, "out", False)
            or not getattr(message, "raw_text", None)
            or message.raw_text.lower().startswith(self.get_prefix())
        ):
            return

        urls = [
            url
            for url in extract_urls(message)
            if len(url) > int(self.config["threshold"])
        ]
        if not urls:
            return

        text = message.text
        for url in urls:
            text = text.replace(url, await self.shorten(url, self.config["auto_engine"]))

        if text != message.text:
            await message.edit(text)
