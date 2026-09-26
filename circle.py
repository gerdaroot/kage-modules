# meta developer: @gerdacod
# scope: heroku_min 2.0.0

import asyncio
import contextlib
import os
import shutil
import tempfile

from herokutl.tl.types import DocumentAttributeAudio, DocumentAttributeVideo
from herokutl.types import Message
from herokutl.utils import encode_waveform

from .. import loader, utils

# Telegram's limits for round video messages
CIRCLE_SIZE = 640
CIRCLE_MAX_SECONDS = 60
WAVEFORM_BARS = 100


async def _run(*args: str) -> tuple[int, bytes, bytes]:
    proc = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    out, err = await proc.communicate()
    return proc.returncode, out, err


async def _duration(path: str) -> float:
    code, out, _ = await _run(
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", path,
    )
    with contextlib.suppress(ValueError):
        return float(out.decode().strip()) if code == 0 else 0.0
    return 0.0


async def _has_stream(path: str, kind: str) -> bool:
    code, out, _ = await _run(
        "ffprobe", "-v", "error", "-select_streams", kind,
        "-show_entries", "stream=index", "-of", "csv=p=0", path,
    )
    return code == 0 and bool(out.strip())


async def _waveform(path: str) -> bytes | None:
    """Peaks of the sound as Telegram's 5-bit waveform, so the voice message doesn't show a flat line"""
    code, pcm, _ = await _run(
        "ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "8000", "-f", "u8", "-",
    )
    if code != 0 or not pcm:
        return None
    return await asyncio.to_thread(_encode_peaks, pcm)


def _encode_peaks(pcm: bytes) -> bytes:
    step = max(1, len(pcm) // WAVEFORM_BARS)
    peaks = [max(abs(b - 128) for b in pcm[i:i + step]) for i in range(0, len(pcm), step)][:WAVEFORM_BARS]
    loudest = max(peaks) or 1
    return encode_waveform(bytes(round(p / loudest * 31) for p in peaks))


@loader.tds
class CircleMod(loader.Module):
    """Turns a video into a round video message or any media with sound into a voice message"""

    strings = {
        "name": "Circle",
        "no_reply": "🎬 <b>Reply to a video, GIF, round video, voice or audio</b>",
        "no_video": "🎬 <b>There is no picture in this media — a round video needs a video or GIF</b>",
        "no_audio": "🔇 <b>There is no sound in this media</b>",
        "bad_start": "⏱ <b>The start must be a number of seconds, e.g.</b> <code>{prefix}circle 15</code>",
        "no_ffmpeg": "🚫 <b>ffmpeg isn't installed</b>",
        "working": "⏳ <b>Converting…</b>",
        "failed": "🚫 <b>ffmpeg couldn't convert it:</b>\n<code>{error}</code>",
        "send_failed": "🚫 <b>Telegram didn't accept it:</b> <code>{error}</code>",
    }

    strings_ru = {
        "no_reply": "🎬 <b>Ответь на видео, GIF, кружок, голосовое или аудио</b>",
        "no_video": "🎬 <b>В этом медиа нет картинки — для кружка нужно видео или GIF</b>",
        "no_audio": "🔇 <b>В этом медиа нет звука</b>",
        "bad_start": "⏱ <b>Начало укажи числом секунд, например</b> <code>{prefix}circle 15</code>",
        "no_ffmpeg": "🚫 <b>Не установлен ffmpeg</b>",
        "working": "⏳ <b>Конвертирую…</b>",
        "failed": "🚫 <b>ffmpeg не смог сконвертировать:</b>\n<code>{error}</code>",
        "send_failed": "🚫 <b>Telegram не принял файл:</b> <code>{error}</code>",
        "_cls_doc": "Делает из видео кружок, а из любого медиа со звуком — голосовое",
    }

    async def _source(self, message: Message) -> Message | None:
        reply = await message.get_reply_message()
        media = reply and (reply.video or reply.video_note or reply.gif or reply.voice or reply.audio or reply.document)
        return reply if media else None

    async def _convert(self, message: Message, build) -> None:
        if not shutil.which("ffmpeg"):
            await utils.answer(message, self.strings("no_ffmpeg"))
            return
        if not (source := await self._source(message)):
            await utils.answer(message, self.strings("no_reply"))
            return

        status = await utils.answer(message, self.strings("working"))
        with tempfile.TemporaryDirectory(prefix="kage-circle-") as workdir:
            path = await source.download_media(file=os.path.join(workdir, "source"))
            result = await build(path, workdir)
            if isinstance(result, str):
                await utils.answer(status, result)
                return

            file, kwargs = result
            try:
                await self._client.send_file(
                    message.peer_id, file, reply_to=source.id, **kwargs
                )
            except Exception as e:
                await utils.answer(status, self.strings("send_failed").format(error=utils.escape_html(str(e))[:300]))
                return
        with contextlib.suppress(Exception):
            await status.delete()

    def _ffmpeg_error(self, err: bytes) -> str:
        tail = "\n".join(err.decode(errors="replace").strip().splitlines()[-4:])
        return self.strings("failed").format(error=utils.escape_html(tail)[:600])

    @loader.command(ru_doc="[с какой секунды] — сделать кружок из видео (ответом, до 60 с)", alias="krug")
    async def circle(self, message: Message):
        """[start second] — make a round video message from a video (reply, up to 60 s)"""
        arg = utils.get_args_raw(message).strip()
        try:
            start = float(arg.replace(",", ".")) if arg else 0.0
        except ValueError:
            await utils.answer(message, self.strings("bad_start").format(prefix=utils.escape_html(self.get_prefix())))
            return

        async def build(path: str, workdir: str):
            if not await _has_stream(path, "v"):
                return self.strings("no_video")
            out = os.path.join(workdir, "circle.mp4")
            code, _, err = await _run(
                "ffmpeg", "-v", "error", "-y", "-ss", str(max(start, 0.0)), "-i", path,
                "-t", str(CIRCLE_MAX_SECONDS),
                # centre square crop: round messages are always square
                "-vf", f"crop='min(iw,ih)':'min(iw,ih)',scale={CIRCLE_SIZE}:{CIRCLE_SIZE},fps=30,format=yuv420p",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
                "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out,
            )
            if code != 0 or not os.path.exists(out):
                return self._ffmpeg_error(err)
            duration = await _duration(out)
            return out, {
                "video_note": True,
                "attributes": [
                    DocumentAttributeVideo(
                        duration=duration, w=CIRCLE_SIZE, h=CIRCLE_SIZE,
                        round_message=True, supports_streaming=True,
                    )
                ],
            }

        await self._convert(message, build)

    @loader.command(ru_doc="— сделать голосовое из видео, кружка или аудио (ответом)", alias="tovoice")
    async def gs(self, message: Message):
        """— make a voice message from a video, round video or audio (reply)"""

        async def build(path: str, workdir: str):
            if not await _has_stream(path, "a"):
                return self.strings("no_audio")
            out = os.path.join(workdir, "voice.ogg")
            # voice messages are mono Opus in Ogg; anything else shows up as a plain audio file
            code, _, err = await _run(
                "ffmpeg", "-v", "error", "-y", "-i", path, "-vn",
                "-ac", "1", "-ar", "48000", "-c:a", "libopus", "-b:a", "64k", out,
            )
            if code != 0 or not os.path.exists(out):
                return self._ffmpeg_error(err)
            return out, {
                "voice_note": True,
                "attributes": [
                    DocumentAttributeAudio(
                        duration=round(await _duration(out)), voice=True, waveform=await _waveform(out),
                    )
                ],
            }

        await self._convert(message, build)
