# meta developer: @gerdacod
# meta banner: https://raw.githubusercontent.com/gerdaroot/kage-modules/main/assets/tiktok.png
# scope: heroku_min 2.0.0
# requires: yt-dlp[default,curl-cffi]

import asyncio
import os
import re
import shutil
import tempfile

from herokutl.tl.types import DocumentAttributeAudio, DocumentAttributeVideo
from herokutl.types import Message

from .. import loader, utils

ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
TIKTOK_URL_RE = re.compile(
    r"https?://(?:(?:www|m|vm|vt)\.)?tiktok\.com/[^\s<>\"']+",
    re.IGNORECASE,
)

# h264 with sound plays inline in every Telegram client; h265-only streams often don't
VIDEO_FORMAT = "best[vcodec^=h264][acodec!=none]/best[acodec!=none]/best"


def _human_count(value: int | None) -> str:
    if value is None:
        return "—"
    for limit, suffix in ((1_000_000_000, "B"), (1_000_000, "M"), (1_000, "K")):
        if value >= limit:
            return f"{value / limit:.1f}".rstrip("0").rstrip(".") + suffix
    return str(value)


@loader.tds
class TikTokMod(loader.Module):
    """Download TikTok videos without watermark and their sound"""

    strings = {
        "name": "TikTok",
        "no_link": "🎵 <b>Send a TikTok link or reply to a message with one</b>",
        "downloading": "⏳ <b>Downloading from TikTok…</b>",
        "too_big": "📦 <b>The file is {size} MB, the limit is {limit} MB</b> (<code>{prefix}config TikTok</code>)",
        "failed": "🚫 <b>Couldn't download it:</b> <code>{error}</code>",
        "photo_post": "🖼 <b>Photo posts aren't supported yet — only videos</b>",
        "no_ffmpeg": "🚫 <b>ffmpeg is needed to extract the sound</b>",
        "caption": "🎵 <b>{author}</b>\n{description}\n👁 {views}  ❤️ {likes}  💬 {comments}\n🔗 <a href=\"{url}\">TikTok</a>",
        "cfg_max_size": "Largest file to send, MB",
        "cfg_caption": "Add author, description and stats under the video",
        "cfg_auto": "Download automatically when you send a message that is just a TikTok link",
    }

    strings_ru = {
        "no_link": "🎵 <b>Пришли ссылку на TikTok или ответь на сообщение с ней</b>",
        "downloading": "⏳ <b>Скачиваю из TikTok…</b>",
        "too_big": "📦 <b>Файл {size} МБ, лимит {limit} МБ</b> (<code>{prefix}config TikTok</code>)",
        "failed": "🚫 <b>Не получилось скачать:</b> <code>{error}</code>",
        "photo_post": "🖼 <b>Фото-посты пока не поддерживаются — только видео</b>",
        "no_ffmpeg": "🚫 <b>Для извлечения звука нужен ffmpeg</b>",
        "caption": "🎵 <b>{author}</b>\n{description}\n👁 {views}  ❤️ {likes}  💬 {comments}\n🔗 <a href=\"{url}\">TikTok</a>",
        "cfg_max_size": "Максимальный размер файла для отправки, МБ",
        "cfg_caption": "Добавлять автора, описание и статистику под видео",
        "cfg_auto": "Скачивать автоматически, когда ты отправляешь сообщение, в котором только ссылка на TikTok",
        "_cls_doc": "Скачивает видео из TikTok без водяного знака и их звук",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "max_size_mb",
                200,
                lambda: self.strings("cfg_max_size"),
                validator=loader.validators.Integer(minimum=1, maximum=2000),
            ),
            loader.ConfigValue(
                "caption",
                True,
                lambda: self.strings("cfg_caption"),
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "auto_download",
                False,
                lambda: self.strings("cfg_auto"),
                validator=loader.validators.Boolean(),
            ),
        )

    async def _find_link(self, message: Message) -> str | None:
        for text in (utils.get_args_raw(message), getattr(await message.get_reply_message(), "raw_text", "")):
            if match := TIKTOK_URL_RE.search(text or ""):
                return match.group(0)
        return None

    def _download(self, url: str, workdir: str, audio: bool) -> dict:
        import yt_dlp

        options = {
            "outtmpl": os.path.join(workdir, "%(id)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "noplaylist": True,
            # a profile link would otherwise download every video on it
            "playlist_items": "1",
            "socket_timeout": 20,
            "max_filesize": self.config["max_size_mb"] * 1024 * 1024,
        }
        if audio:
            # "audio" is TikTok's original sound (mp3 128k); the track inside the video is only aac 64k.
            # preferredcodec "best" copies the stream as is — re-encoding lossy audio is what made it sound bad
            if shutil.which("ffmpeg"):
                options |= {
                    "format": "audio/bestaudio/best",
                    "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "best"}],
                }
            else:
                options["format"] = "audio/bestaudio"
        else:
            options["format"] = VIDEO_FORMAT
            if shutil.which("ffmpeg"):
                # Telegram needs a JPEG cover; TikTok serves webp/heic
                options |= {
                    "writethumbnail": True,
                    "postprocessors": [{"key": "FFmpegThumbnailsConvertor", "format": "jpg", "when": "before_dl"}],
                }

        with yt_dlp.YoutubeDL(options) as ydl:
            return ydl.extract_info(url, download=True)

    @staticmethod
    def _attribute(info: dict, audio: bool):
        # without these Telegram shows a 1x1, 0-second file
        duration = int(info.get("duration") or 0)
        if audio:
            return DocumentAttributeAudio(
                duration=duration,
                title=info.get("track") or info.get("title") or "TikTok",
                performer=info.get("artist") or info.get("uploader"),
            )
        return DocumentAttributeVideo(
            duration=duration,
            w=int(info.get("width") or 0),
            h=int(info.get("height") or 0),
            supports_streaming=True,
        )

    def _caption(self, info: dict, url: str) -> str | None:
        if not self.config["caption"]:
            return None

        description = (info.get("description") or info.get("title") or "").strip()
        if len(description) > 300:
            description = description[:299].rstrip() + "…"

        return self.strings("caption").format(
            author=utils.escape_html(info.get("uploader") or info.get("creator") or "TikTok"),
            description=utils.escape_html(description),
            views=_human_count(info.get("view_count")),
            likes=_human_count(info.get("like_count")),
            comments=_human_count(info.get("comment_count")),
            url=utils.escape_html(info.get("webpage_url") or url),
        )

    async def _send(self, message: Message, url: str, audio: bool = False, auto: bool = False):
        if "/photo/" in url:
            await utils.answer(message, self.strings("photo_post"))
            return

        # auto mode answers under the user's own message instead of replacing it
        if auto:
            status = await message.reply(self.strings("downloading"))
            reply_to = message.id
        else:
            status = await utils.answer(message, self.strings("downloading"))
            reply = await message.get_reply_message()
            reply_to = reply.id if reply else None
        with tempfile.TemporaryDirectory(prefix="kage-tiktok-") as workdir:
            try:
                info = await asyncio.to_thread(self._download, url, workdir, audio)
            except Exception as e:
                if audio and not shutil.which("ffmpeg"):
                    await utils.answer(status, self.strings("no_ffmpeg"))
                    return
                error = ANSI_RE.sub("", str(e))
                error = re.sub(r"^\s*ERROR:\s*(\[[^\]]+\]\s*)?(\d+:\s*)?", "", error).strip()
                await utils.answer(status, self.strings("failed").format(error=utils.escape_html(error[:300])))
                return

            files = [os.path.join(workdir, name) for name in os.listdir(workdir)]
            thumb = next((f for f in files if f.endswith(".jpg")), None)
            media = next((f for f in files if f != thumb), None)
            if not media:
                # yt-dlp skips files over max_filesize silently instead of raising
                size = (info.get("filesize") or info.get("filesize_approx") or 0) / 1024 / 1024
                await utils.answer(
                    status,
                    self.strings("too_big").format(
                        size=round(size) or "?",
                        limit=self.config["max_size_mb"],
                        prefix=utils.escape_html(self.get_prefix()),
                    ),
                )
                return

            await utils.answer_file(
                status,
                media,
                caption=self._caption(info, url),
                reply_to=reply_to,
                thumb=thumb,
                attributes=[self._attribute(info, audio)],
                supports_streaming=not audio,
            )

    @loader.command(
        ru_doc="<ссылка> — скачать видео из TikTok без водяного знака",
        alias="tt",
    )
    async def tiktok(self, message: Message):
        """<link> — download a TikTok video without watermark"""
        if not (url := await self._find_link(message)):
            await utils.answer(message, self.strings("no_link"))
            return
        await self._send(message, url)

    @loader.command(ru_doc="<ссылка> — скачать звук из видео TikTok")
    async def tta(self, message: Message):
        """<link> — download the sound of a TikTok video"""
        if not (url := await self._find_link(message)):
            await utils.answer(message, self.strings("no_link"))
            return
        await self._send(message, url, audio=True)

    @loader.watcher(out=True, only_messages=True, no_commands=True)
    async def watcher(self, message: Message):
        if not self.config["auto_download"]:
            return
        text = (message.raw_text or "").strip()
        if (match := TIKTOK_URL_RE.fullmatch(text)):
            await self._send(message, match.group(0), auto=True)
