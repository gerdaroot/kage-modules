# ---------------------------------------------------------------------------------
#░█▀▄░▄▀▀▄░█▀▄░█▀▀▄░█▀▀▄░█▀▀▀░▄▀▀▄░░░█▀▄▀█
#░█░░░█░░█░█░█░█▄▄▀░█▄▄█░█░▀▄░█░░█░░░█░▀░█
#░▀▀▀░░▀▀░░▀▀░░▀░▀▀░▀░░▀░▀▀▀▀░░▀▀░░░░▀░░▒▀
# Name: PinterestDownloader
# Description: Gives a link to download a file from Pinterest
# Author: @codrago_m
# ---------------------------------------------------------------------------------
# 🔒    Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html
# Modified for Kage by gerdaroot (https://github.com/gerdaroot/kage-modules), 2026-09-25
# ---------------------------------------------------------------------------------
# Author: @codrago
# Commands: pinterest
# scope: hikka_only
# meta developer: @codrago_m
# meta banner: https://raw.githubusercontent.com/coddrago/modules/refs/heads/main/banner.png
# meta pic: https://envs.sh/HJV.webp
# ---------------------------------------------------------------------------------

__version__ = (1, 1, 0)

import re

import aiohttp

from .. import loader, utils

PIN_INFO_URL = "https://widgets.pinterest.com/v3/pidgets/pins/info/"
PIN_ID_RE = re.compile(r"pinterest\.[a-z.]+/pin/(?:[^/?#]*--)?(\d+)")
SHORT_LINK_RE = re.compile(r"https?://pin\.it/\S+")
TIMEOUT = aiohttp.ClientTimeout(total=20)


async def resolve_pin_id(session: aiohttp.ClientSession, link: str) -> str | None:
    if SHORT_LINK_RE.match(link):
        async with session.get(link, allow_redirects=True) as resp:
            link = str(resp.url)
    match = PIN_ID_RE.search(link)
    return match.group(1) if match else None


def pick_media_url(pin: dict) -> str | None:
    videos = (pin.get("videos") or {}).get("video_list") or {}
    mp4 = [v["url"] for k, v in videos.items() if not k.startswith("V_HLS")]
    if mp4:
        return mp4[0]
    images = pin.get("images") or {}
    if not images:
        return None
    # The widget API only lists previews up to 564px; the "originals" path serves full size.
    preview = next(reversed(images.values()))["url"]
    return re.sub(r"/\d+x/", "/originals/", preview, count=1)


@loader.tds
class PinterestDownloader(loader.Module):
    """Gives a link to download a file from Pinterest"""

    strings = {
        "name": "PinterestDownloader",
        "Error": "<emoji document_id=5328145443106873128>✖️</emoji> Where args?",
        "ready": (
            "<emoji document_id=5319172556345851345>✨</emoji> <b><u>Pin ready to"
            " download!</u></b>\n\n<emoji document_id=5316719099227684154>🌕</emoji>"
            " <b>Link for download:</b> <i><a href=\"{}\">just tap here</a></i>"
        ),
        "invalid": (
            "<emoji document_id=5319088379281815108>🤷‍♀️</emoji> '{}' <b>is not a"
            " Pinterest pin link</b>"
        ),
        "not_found": (
            "<emoji document_id=5328145443106873128>✖️</emoji> <b>Pin not found or"
            " has no media</b>"
        ),
    }

    strings_ru = {
        "Error": "<emoji document_id=5328145443106873128>✖️</emoji> Где аргументы?",
        "invalid": (
            "<emoji document_id=5319088379281815108>🤷‍♀️</emoji> '{}' <b>не ссылка на"
            " пин Pinterest</b>"
        ),
        "not_found": (
            "<emoji document_id=5328145443106873128>✖️</emoji> <b>Пин не найден или"
            " в нём нет медиа</b>"
        ),
    }

    async def pinterestcmd(self, message):
        """<pin.it or pinterest.com/pin link> - Gives a link to download"""
        link = utils.get_args_raw(message).strip()
        if not link:
            await utils.answer(message, self.strings["Error"])
            return

        try:
            async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
                pin_id = await resolve_pin_id(session, link)
                if not pin_id:
                    await utils.answer(
                        message,
                        self.strings["invalid"].format(utils.escape_html(link)),
                    )
                    return

                async with session.get(
                    PIN_INFO_URL, params={"pin_ids": pin_id}
                ) as resp:
                    pins = (await resp.json(content_type=None)).get("data") or []
        except (aiohttp.ClientError, TimeoutError, ValueError):
            pins = []

        media_url = pick_media_url(pins[0]) if pins else None
        if not media_url:
            await utils.answer(message, self.strings["not_found"])
            return

        await utils.answer(
            message, self.strings["ready"].format(utils.escape_quotes(media_url))
        )
