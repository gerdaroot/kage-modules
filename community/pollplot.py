# ---------------------------------------------------------------------------------
#  /\_/\  🌐 This module was loaded through https://t.me/hikkamods_bot
# ( o.o )  🔐 Licensed under the GNU AGPLv3.
#  > ^ <   ⚠️ Owner of heta.hikariatama.ru doesn't take any responsibilities or intellectual property rights regarding this script
# ---------------------------------------------------------------------------------
# Name: pollplot
# Author: hikariatama
# Commands:
# .plot
# ---------------------------------------------------------------------------------

#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html
# Modified for Kage by gerdaroot (https://github.com/gerdaroot/kage-modules), 2026-09-25

# meta pic: https://static.dan.tatar/pollplot_icon.png
# meta banner: https://mods.hikariatama.ru/badges/pollplot.jpg
# requires: matplotlib
# meta developer: @hikarimods
# scope: hikka_only
# scope: hikka_min 1.2.10
# scope: heroku_min 2.0.0

import asyncio
import io

from matplotlib.figure import Figure
from telethon.tl.types import Message

from .. import loader, utils


def render_pie(sizes: list[int], labels: list[str]) -> bytes:
    # A standalone Figure avoids pyplot's global state, which is not thread-safe and leaks figures.
    fig = Figure()
    ax = fig.subplots()
    ax.pie(
        sizes,
        explode=[0.05] * len(sizes),
        labels=labels,
        textprops={"color": "white", "size": "large"},
    )
    fig.patch.set_facecolor("#303841")
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    return buf.getvalue()


@loader.tds
class PollPlotMod(loader.Module):
    """Visualises polls as plots"""

    strings = {
        "name": "PollPlot",
        "no_reply": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Reply to a poll is"
            " required!</b>"
        ),
        "no_answers": (
            "<emoji document_id=5197183257367552085>😢</emoji> <b>This poll has not"
            " answers yet.</b>"
        ),
    }

    strings_ru = {
        "no_reply": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Нужен ответ на"
            " опрос!</b>"
        ),
        "no_answers": (
            "<emoji document_id=5197183257367552085>😢</emoji> <b>В этом опросе"
            " пока что"
            " нет участников.</b>"
        ),
        "_cmd_doc_plot": "<reply> - Создать визуализацию опроса",
        "_cls_doc": "Визуализирует опросы в виде графиков",
    }

    strings_de = {
        "no_reply": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Antwort auf eine"
            " Umfrage erforderlich!</b>"
        ),
        "no_answers": (
            "<emoji document_id=5197183257367552085>😢</emoji> <b>Diese Umfrage hat"
            " noch"
            " keine Antworten.</b>"
        ),
        "_cmd_doc_plot": "<reply> - Erstelle eine Visualisierung von Umfragen",
        "_cls_doc": "Visualisiert Umfragen als Diagramme",
    }

    strings_hi = {
        "no_reply": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>एक पोल पर जवाब आवश्यक"
            " है!</b>"
        ),
        "no_answers": (
            "<emoji document_id=5197183257367552085>😢</emoji> <b>इस पोल में अभी तक कोई"
            " उत्तर नहीं है।</b>"
        ),
        "_cmd_doc_plot": "<reply> - पोल को बनाने के लिए प्लॉट करें",
        "_cls_doc": "पोल को प्लॉट के रूप में दर्शाता है",
    }

    strings_uz = {
        "no_reply": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Javob berilgan savol"
            " kerak!</b>"
        ),
        "no_answers": (
            "<emoji document_id=5197183257367552085>😢</emoji> <b>Ushbu savolda hali"
            " hech qanday javob yo'q.</b>"
        ),
        "_cmd_doc_plot": "<reply> - Savolni chizishga o'tkazish",
        "_cls_doc": "Savollarni chizishlar shaklida ko'rsatadi",
    }

    strings_tr = {
        "no_reply": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Bir anket yanıtı"
            " gerekli!</b>"
        ),
        "no_answers": (
            "<emoji document_id=5197183257367552085>😢</emoji> <b>Bu anket henüz cevap"
            " yok.</b>"
        ),
        "_cmd_doc_plot": "<yanıt> - Bir anketi çizimden oluşturun",
        "_cls_doc": "Anketleri çizimler şeklinde gösterir",
    }

    async def plotcmd(self, message: Message):
        """<reply> - Create plot from poll"""
        reply = await message.get_reply_message()
        if not reply or not getattr(reply, "poll", False):
            await utils.answer(message, self.strings("no_reply"))
            return

        results = reply.poll.results.results or []
        voters = {result.option: result.voters or 0 for result in results}
        answers = reply.poll.poll.answers
        sizes = [voters.get(answer.option, 0) for answer in answers]
        total = sum(sizes)

        if not total:
            await utils.answer(message, self.strings("no_answers"))
            return

        labels = [
            f"{getattr(answer.text, 'text', answer.text)} [{size}] ({round(size / total * 100, 1)}%)"
            for answer, size in zip(answers, sizes, strict=True)
        ]

        image = await asyncio.to_thread(render_pie, sizes, labels)
        await self._client.send_file(message.peer_id, image, reply_to=reply)

        if message.out:
            await message.delete()
