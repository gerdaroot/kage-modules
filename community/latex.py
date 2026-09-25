# ---------------------------------------------------------------------------------
#  /\_/\  🌐 This module was loaded through https://t.me/hikkamods_bot
# ( o.o )  🔐 Licensed under the GNU AGPLv3.
#  > ^ <   ⚠️ Owner of heta.hikariatama.ru doesn't take any responsibilities or intellectual property rights regarding this script
# ---------------------------------------------------------------------------------
# Name: latex
# Description: Renders mathematical formulas in LaTeX pngs
# Author: hikariatama
# Commands:
# .latex
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

# meta pic: https://img.icons8.com/fluency/452/texshop.png
# meta banner: https://mods.hikariatama.ru/badges/latex.jpg
# meta developer: @hikarimods
# requires: matplotlib

import asyncio
import io
import logging

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from telethon.tl.types import Message

from .. import loader, utils

logger = logging.getLogger(__name__)


def render_formula(formula: str) -> bytes:
    # A standalone Figure avoids pyplot's global state, so rendering is safe in a worker thread
    fig = Figure()
    canvas = FigureCanvasAgg(fig)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()

    text = ax.text(
        0.5,
        0.5,
        f"${formula}$",
        horizontalalignment="center",
        verticalalignment="center",
        fontsize=25,
        color="black",
    )

    canvas.draw()

    bbox = text.get_window_extent()
    fig.set_size_inches(bbox.width / 80, bbox.height / 80)
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    return buf.getvalue()


@loader.tds
class LaTeXMod(loader.Module):
    """Renders mathematical formulas in LaTeX pngs"""

    strings = {
        "name": "LaTeX",
        "no_args": "🚫 <b>Specify a formula to render</b>",
        "cant_render": "🚫 <b>Can't render formula</b>",
    }

    strings_ru = {
        "no_args": "🚫 <b>Укажи формулу для рендера</b>",
        "cant_render": "🚫 <b>В формуле обнаружена ошибка</b>",
    }

    async def latexcmd(self, message: Message):
        """<formula> - Create LaTeX render"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings("no_args"))
            return

        try:
            image = await asyncio.to_thread(render_formula, args)
        except Exception:
            logger.exception("Can't render formula")
            await utils.answer(message, self.strings("cant_render"))
            return

        await self._client.send_file(
            message.peer_id,
            image,
            reply_to=message.reply_to_msg_id,
            caption=f"🧮 <b>LaTeX</b>: <code>{utils.escape_html(args)}</code>",
        )

        if message.out:
            await message.delete()
