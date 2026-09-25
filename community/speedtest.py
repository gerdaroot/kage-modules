# ---------------------------------------------------------------------------------
#░█▀▄░▄▀▀▄░█▀▄░█▀▀▄░█▀▀▄░█▀▀▀░▄▀▀▄░░░█▀▄▀█
#░█░░░█░░█░█░█░█▄▄▀░█▄▄█░█░▀▄░█░░█░░░█░▀░█
#░▀▀▀░░▀▀░░▀▀░░▀░▀▀░▀░░▀░▀▀▀▀░░▀▀░░░░▀░░▒▀
# Name: Speedtest
# Description: Module to run speedtest using speedtest library
# Author: @codrago_m
# ---------------------------------------------------------------------------------
# 🔒    Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html
# Modified for Kage by gerdaroot (https://github.com/gerdaroot/kage-modules), 2026-09-25
# ---------------------------------------------------------------------------------
# Author: @codrago
# Commands: speedtest
# scope: hikka_only
# meta developer: @codrago_m
# requires: speedtest-cli
# meta banner: https://raw.githubusercontent.com/coddrago/modules/refs/heads/main/banner.png
# meta pic: https://envs.sh/HoD.webp
# ---------------------------------------------------------------------------------

import asyncio

import speedtest

from .. import loader, utils


def run_speedtest() -> dict:
    st = speedtest.Speedtest(secure=True)
    st.download()
    st.upload()
    return st.results.dict()


@loader.tds
class SpeedTestMod(loader.Module):
    """Module to run speedtest using speedtest library"""

    strings = {
        "name": "SpeedTest",
        "running": "<emoji document_id=5870718740236079262>🌐</emoji> <b>Running speedtest...</b>",
        "results": "<emoji document_id=5870718740236079262>🌐</emoji> <b>Speedtest Results:</b>\n\n"
                   "<emoji document_id=5870718740236079262>🌐</emoji> <b>Download:</b> <code>{download} Mbps</code>\n"
                   "<emoji document_id=5870729082517328189>📊</emoji> <b>Upload:</b> <code>{upload} Mbps</code>\n"
                   "<emoji document_id=5222108309795908493>✨</emoji> <b>Ping:</b> {ping} ms",
        "error": "🚫 <b>Error running speedtest:</b> <code>{error}</code>",
    }

    strings_ru = {
        "running": "<emoji document_id=5870718740236079262>🌐</emoji> <b>Запуск теста скорости...</b>",
        "results": "<emoji document_id=5870718740236079262>🌐</emoji> <b>Результаты теста скорости:</b>\n\n"
                   "<emoji document_id=5870718740236079262>🌐</emoji> <b>Скачивание:</b> <code>{download} Мбит/с</code>\n"
                   "<emoji document_id=5870729082517328189>📊</emoji> <b>Загрузка:</b> <code>{upload} Мбит/с</code>\n"
                   "<emoji document_id=5222108309795908493>✨</emoji> Пинг: {ping} мс",
        "error": "🚫 <b>Ошибка при запуске теста скорости:</b> <code>{error}</code>",
    }

    async def speedtestcmd(self, message):
        """Speedtest of your server internet"""
        message = await utils.answer(message, self.strings("running"))

        try:
            results = await asyncio.to_thread(run_speedtest)
        except Exception as e:
            await utils.answer(
                message, self.strings("error").format(error=utils.escape_html(str(e)))
            )
            return

        await utils.answer(
            message,
            self.strings("results").format(
                ping=round(results["ping"], 2),
                download=round(results["download"] / 1_000_000, 2),
                upload=round(results["upload"] / 1_000_000, 2),
            ),
        )
