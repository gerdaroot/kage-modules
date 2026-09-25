# ---------------------------------------------------------------------------------
#  /\_/\  🌐 This module was loaded through https://t.me/hikkamods_bot
# ( o.o )  🔐 Licensed under the GNU AGPLv3.
#  > ^ <   ⚠️ Owner of heta.hikariatama.ru doesn't take any responsibilities or intellectual property rights regarding this script
# ---------------------------------------------------------------------------------
# Name: dl_yt_previews
# Author: Den4ikSuperOstryyPer4ik
# Commands:
# .ytp
# ---------------------------------------------------------------------------------

#
# 	 @@@@@@    @@@@@@   @@@@@@@  @@@@@@@    @@@@@@   @@@@@@@@@@    @@@@@@   @@@@@@@   @@@  @@@  @@@       @@@@@@@@   @@@@@@
# 	@@@@@@@@  @@@@@@@   @@@@@@@  @@@@@@@@  @@@@@@@@  @@@@@@@@@@@  @@@@@@@@  @@@@@@@@  @@@  @@@  @@@       @@@@@@@@  @@@@@@@
# 	@@!  @@@  !@@         @@!    @@!  @@@  @@!  @@@  @@! @@! @@!  @@!  @@@  @@!  @@@  @@!  @@@  @@!       @@!       !@@
# 	!@!  @!@  !@!         !@!    !@!  @!@  !@!  @!@  !@! !@! !@!  !@!  @!@  !@!  @!@  !@!  @!@  !@!       !@!       !@!
# 	@!@!@!@!  !!@@!!      @!!    @!@!!@!   @!@  !@!  @!! !!@ @!@  @!@  !@!  @!@  !@!  @!@  !@!  @!!       @!!!:!    !!@@!!
# 	!!!@!!!!   !!@!!!     !!!    !!@!@!    !@!  !!!  !@!   ! !@!  !@!  !!!  !@!  !!!  !@!  !!!  !!!       !!!!!:     !!@!!!
# 	!!:  !!!       !:!    !!:    !!: :!!   !!:  !!!  !!:     !!:  !!:  !!!  !!:  !!!  !!:  !!!  !!:       !!:            !:!
# 	:!:  !:!      !:!     :!:    :!:  !:!  :!:  !:!  :!:     :!:  :!:  !:!  :!:  !:!  :!:  !:!   :!:      :!:           !:!
# 	::   :::  :::: ::      ::    ::   :::  ::::: ::  :::     ::   ::::: ::   :::: ::  ::::: ::   :: ::::   :: ::::  :::: ::
# 	 :   : :  :: : :       :      :   : :   : :  :    :      :     : :  :   :: :  :    : :  :   : :: : :  : :: ::   :: : :
#
#                                             © Copyright 2023
#
#                                    https://t.me/Den4ikSuperOstryyPer4ik
#                                                  and
#                                          https://t.me/ToXicUse
#
#                                    🔒 Licensed under the GNU AGPLv3
#                                 https://www.gnu.org/licenses/agpl-3.0.html
# Modified for Kage by gerdaroot (https://github.com/gerdaroot/kage-modules), 2026-09-25
#
# meta developer: @AstroModules
# scope: hikka_only
# scope: hikka_min 1.3.0

import re

from telethon.tl.types import Message

from .. import loader, utils
from ..inline.types import InlineCall

# watch?v=, youtu.be/, shorts/, embed/, live/ links; video IDs are always 11 chars
VIDEO_ID_RE = re.compile(
    r"(?:v=|youtu\.be/|/shorts/|/embed/|/live/)([\w-]{11})|^([\w-]{11})$"
)
PREVIEW_URL = "https://i.ytimg.com/vi/{video_id}/{quality}.jpg"
QUALITY_ROWS = (
    ("maxresdefault", "sddefault"),
    ("hqdefault", "mqdefault"),
    ("default",),
)


def extract_video_id(link: str) -> str | None:
    match = VIDEO_ID_RE.search(link.strip())
    return match and (match.group(1) or match.group(2))


@loader.tds
class YTPreviewMod(loader.Module):
    """Скачивает превью с ютуба"""

    strings = {
        "name": "YT-Preview",
        "choice": "<b>Select YouTube preview extension:</b>",
        "caption": "<b>You have selected an extension: {}</b>",
        "error": (
            "There doesn't seem to be an extension for this video...Choose another."
        ),
        "no_link": "<b>Specify a YouTube video link</b>",
    }

    strings_ru = {
        "choice": "<b>Выберите расширение для превью ролика YouTube:</b>",
        "caption": "<b>Вы выбрали расширение: {}</b>",
        "error": "Кажется этого расширения для этого видео нету...Выберите другое.",
        "no_link": "<b>Укажите ссылку на видео YouTube</b>",
    }

    @loader.command(ru_doc="<link> --> скачивает превью")
    async def ytpcmd(self, message: Message):
        """<link> --> download YouTube video preview"""
        video_id = extract_video_id(utils.get_args_raw(message))
        if not video_id:
            await utils.answer(message, self.strings("no_link"))
            return

        await self.inline.form(
            text=self.strings("choice"),
            reply_markup=[
                [
                    {
                        "text": quality,
                        "callback": self._send_preview,
                        "args": (message.chat_id, video_id, quality),
                    }
                    for quality in row
                ]
                for row in QUALITY_ROWS
            ],
            message=message,
        )

    async def _send_preview(
        self, call: InlineCall, chat_id: int, video_id: str, quality: str
    ):
        try:
            await self._client.send_file(
                chat_id,
                file=PREVIEW_URL.format(video_id=video_id, quality=quality),
                caption=self.strings("caption").format(quality),
            )
        except Exception:
            # Telegram rejects the URL when YouTube has no preview of this size (404)
            await call.answer(self.strings("error"))
