# ---------------------------------------------------------------------------------
#░█▀▄░▄▀▀▄░█▀▄░█▀▀▄░█▀▀▄░█▀▀▀░▄▀▀▄░░░█▀▄▀█
#░█░░░█░░█░█░█░█▄▄▀░█▄▄█░█░▀▄░█░░█░░░█░▀░█
#░▀▀▀░░▀▀░░▀▀░░▀░▀▀░▀░░▀░▀▀▀▀░░▀▀░░░░▀░░▒▀
# Name: Avatars
# Description: Flexible profile avatar management & auto-setter
# Author: @codrago_m
# ---------------------------------------------------------------------------------
# 🔒    Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html
# Modified for Kage by gerdaroot (https://github.com/gerdaroot/kage-modules), 2026-09-25
# ---------------------------------------------------------------------------------
# Author: @codrago
# Commands: getava, delavas, setava, stopava, gifava
# scope: heroku_only
# scope: heroku_min 2.0.0
# meta developer: @codrago_m
# meta banner: https://raw.githubusercontent.com/coddrago/modules/refs/heads/main/banner.png
# ---------------------------------------------------------------------------------

import asyncio
import contextlib
import os
import shutil
import tempfile
import zipfile

from telethon.errors import FloodWaitError
from telethon.tl.functions.photos import (
    DeletePhotosRequest,
    UpdateProfilePhotoRequest,
    UploadProfilePhotoRequest,
)
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import DocumentAttributeVideo, InputPhoto, InputPhotoEmpty

from .. import loader, utils

PUBLIC_FLAGS = ("-p", "--public", "public", "паблик")
ALL_FLAGS = ("all", "все", "всё")
DELETE_CHUNK_SIZE = 100
GIFAVA_FRAME_DELAY = 10
# every avatar change is a profile-photo upload on the main account: keep loops short and slow
MAX_LOOP_COUNT = 50
MIN_LOOP_INTERVAL = 30.0
MAX_GIFAVA_FRAMES = 50


@loader.tds
class AvatarsMod(loader.Module):
    """Module for flexible profile avatar management"""

    strings = {
        "name": "Avatars",
        "no_avas": "<tg-emoji emoji-id=5287372146039861774>⛔️</tg-emoji> <b>User has no profile photos.</b>",
        "downloading": "<tg-emoji emoji-id=5872771279337033184>⬇️</tg-emoji> <b>Downloading avatar...</b>",
        "archiving": "<tg-emoji emoji-id=5872771279337033184>⬇️</tg-emoji> <b>Downloading all avatars to avatars.zip...</b>",
        "deleted": "<tg-emoji emoji-id=5255831443816327915>🗑</tg-emoji> <b>Successfully deleted avatars:</b> <code>{}</code>.",
        "deleted_public": "<tg-emoji emoji-id=5255831443816327915>🗑</tg-emoji> <b>Successfully deleted public avatar.</b>",
        "invalid_args": "<tg-emoji emoji-id=4916086774649848789>🔗</tg-emoji> <b>Specify a number, <code>all</code> or <code>-p</code>.</b>",
        "user_not_found": "<tg-emoji emoji-id=4916086774649848789>🔗</tg-emoji> <b>Specified user could not be found.</b>",
        "no_media_reply": "<tg-emoji emoji-id=4916086774649848789>🔗</tg-emoji> <b>Reply to a photo, video, or GIF.</b>",
        "unsupported_media": "<tg-emoji emoji-id=4916086774649848789>🔗</tg-emoji> <b>Only images and video files are supported.</b>",
        "avatar_set": "<tg-emoji emoji-id=4916086774649848789>🔗</tg-emoji> <b>Avatar successfully updated!</b>",
        "public_avatar_set": "<tg-emoji emoji-id=4916086774649848789>🔗</tg-emoji> <b>Public avatar successfully updated!</b>",
        "already_running": "<tg-emoji emoji-id=4916086774649848789>🔗</tg-emoji> <b>A process is already running! Stop it with <code>.stopava</code>.</b>",
        "not_running": "<tg-emoji emoji-id=4916086774649848789>🔗</tg-emoji> <b>No active avatar process found.</b>",
        "started": (
            "<tg-emoji emoji-id=4916086774649848789>🔗</tg-emoji> <b>Avatar loop process started!</b>\n"
            "<tg-emoji emoji-id=5873022839866527761>⚪️</tg-emoji> Type: <code>{}</code>\n"
            "<tg-emoji emoji-id=5873022839866527761>⚪️</tg-emoji> Amount: <code>{}</code>\n"
            "<tg-emoji emoji-id=5873022839866527761>⚪️</tg-emoji> Interval: <code>{}</code> sec."
        ),
        "progress": (
            "<tg-emoji emoji-id=4916086774649848789>🔗</tg-emoji> <b>Avatar loop in progress...</b>\n"
            "<tg-emoji emoji-id=5873022839866527761>⚪️</tg-emoji> Progress: <b>{}/{}</b>"
        ),
        "done": "<tg-emoji emoji-id=4916086774649848789>🔗</tg-emoji> <b>Successfully finished! Total avatars set:</b> <code>{}</code>.",
        "stopped": "<tg-emoji emoji-id=4916086774649848789>🔗</tg-emoji> <b>Avatar process stopped.</b>",
        "flood_wait": "<tg-emoji emoji-id=4916086774649848789>🔗</tg-emoji> <b>Telegram FloodWait received for <code>{}</code> seconds. Process stopped for safety.</b>",
        "error": "<tg-emoji emoji-id=4916086774649848789>🔗</tg-emoji> <b>Error:</b> <code>{}</code>",
        "invalid_setava_args": (
            "<tg-emoji emoji-id=4916086774649848789>🔗</tg-emoji> <b>Invalid arguments.</b>\n"
            "Usage:\n"
            "<tg-emoji emoji-id=5873022839866527761>⚪️</tg-emoji> <code>.setava [-p]</code> — set once instantly\n"
            "<tg-emoji emoji-id=5873022839866527761>⚪️</tg-emoji> <code>.setava [-p] &lt;interval_sec&gt; &lt;amount&gt;</code> — start loop"
        ),
        "extracting_frames": "<tg-emoji emoji-id=4916086774649848789>🔗</tg-emoji> <b>Extracting all video frames at native FPS...</b>",
        "gifava_progress": (
            "<tg-emoji emoji-id=4916086774649848789>🔗</tg-emoji> <b>Uploading animation frames (10s delay)...</b>\n"
            "<tg-emoji emoji-id=5873022839866527761>⚪️</tg-emoji> Progress: <b>{}/{}</b>"
        ),
        "gifava_done": "<tg-emoji emoji-id=4916086774649848789>🔗</tg-emoji> <b>Animation successfully created! Total frames uploaded:</b> <code>{}</code>.",
        "no_frames": "<tg-emoji emoji-id=4916086774649848789>🔗</tg-emoji> <b>Failed to extract frames from media.</b>",
        "btn_stop": "❌ Stop",
    }

    strings_ru = {
        "name": "Avatars",
        "no_avas": "<tg-emoji emoji-id=5287372146039861774>⛔️</tg-emoji> <b>У пользователя нет аватарок.</b>",
        "downloading": "<tg-emoji emoji-id=5872771279337033184>⬇️</tg-emoji> <b>Загрузка аватарки...</b>",
        "archiving": "<tg-emoji emoji-id=5872771279337033184>⬇️</tg-emoji> <b>Загрузка всех аватарок в avatars.zip...</b>",
        "deleted": "<tg-emoji emoji-id=5255831443816327915>🗑</tg-emoji> <b>Успешно удалено аватарок:</b> <code>{}</code>.",
        "deleted_public": "<tg-emoji emoji-id=5255831443816327915>🗑</tg-emoji> <b>Публичная аватарка успешно удалена.</b>",
        "invalid_args": "<tg-emoji emoji-id=4916086774649848789>🔗</tg-emoji> <b>Укажите число, <code>all</code> или <code>-p</code>.</b>",
        "user_not_found": "<tg-emoji emoji-id=4916086774649848789>🔗</tg-emoji> <b>Не удалось найти указанного пользователя.</b>",
        "no_media_reply": "<tg-emoji emoji-id=4916086774649848789>🔗</tg-emoji> <b>Ответьте реплаем на фото, видео или GIF.</b>",
        "unsupported_media": "<tg-emoji emoji-id=4916086774649848789>🔗</tg-emoji> <b>Поддерживаются только изображения и видеофайлы.</b>",
        "avatar_set": "<tg-emoji emoji-id=4916086774649848789>🔗</tg-emoji> <b>Аватарка успешно установлена!</b>",
        "public_avatar_set": "<tg-emoji emoji-id=4916086774649848789>🔗</tg-emoji> <b>Публичная аватарка успешно установлена!</b>",
        "already_running": "<tg-emoji emoji-id=4916086774649848789>🔗</tg-emoji> <b>Процесс уже активен! Остановите его командой <code>.stopava</code>.</b>",
        "not_running": "<tg-emoji emoji-id=4916086774649848789>🔗</tg-emoji> <b>На данный момент нет активного процесса.</b>",
        "started": (
            "<tg-emoji emoji-id=4916086774649848789>🔗</tg-emoji> <b>Запущен процесс установки аватарок!</b>\n"
            "<tg-emoji emoji-id=5873022839866527761>⚪️</tg-emoji> Тип: <code>{}</code>\n"
            "<tg-emoji emoji-id=5873022839866527761>⚪️</tg-emoji> Количество: <code>{}</code> шт.\n"
            "<tg-emoji emoji-id=5873022839866527761>⚪️</tg-emoji> Интервал: <code>{}</code> сек."
        ),
        "progress": (
            "<tg-emoji emoji-id=4916086774649848789>🔗</tg-emoji> <b>Автопостановка в процессе...</b>\n"
            "<tg-emoji emoji-id=5873022839866527761>⚪️</tg-emoji> Прогресс: <b>{}/{}</b>"
        ),
        "done": "<tg-emoji emoji-id=4916086774649848789>🔗</tg-emoji> <b>Успешно завершено! Установлено аватарок:</b> <code>{}</code>.",
        "stopped": "<tg-emoji emoji-id=4916086774649848789>🔗</tg-emoji> <b>Процесс остановлен.</b>",
        "flood_wait": "<tg-emoji emoji-id=4916086774649848789>🔗</tg-emoji> <b>Telegram выдал FloodWait на <code>{}</code> сек. Процесс прерван в целях безопасности.</b>",
        "error": "<tg-emoji emoji-id=4916086774649848789>🔗</tg-emoji> <b>Ошибка:</b> <code>{}</code>",
        "invalid_setava_args": (
            "<tg-emoji emoji-id=4916086774649848789>🔗</tg-emoji> <b>Неверные аргументы.</b>\n"
            "Использование:\n"
            "<tg-emoji emoji-id=5873022839866527761>⚪️</tg-emoji> <code>.setava [-p]</code> — установить 1 раз моментально\n"
            "<tg-emoji emoji-id=5873022839866527761>⚪️</tg-emoji> <code>.setava [-p] &lt;интервал_сек&gt; &lt;кол-во&gt;</code> — запустить цикл"
        ),
        "extracting_frames": "<tg-emoji emoji-id=4916086774649848789>🔗</tg-emoji> <b>Извлечение всех кадров видео в исходном FPS...</b>",
        "gifava_progress": (
            "<tg-emoji emoji-id=4916086774649848789>🔗</tg-emoji> <b>Загрузка кадров анимации (задержка 10с)...</b>\n"
            "<tg-emoji emoji-id=5873022839866527761>⚪️</tg-emoji> Прогресс: <b>{}/{}</b>"
        ),
        "gifava_done": "<tg-emoji emoji-id=4916086774649848789>🔗</tg-emoji> <b>Покадровая анимация успешно создана! Загружено кадров:</b> <code>{}</code>.",
        "no_frames": "<tg-emoji emoji-id=4916086774649848789>🔗</tg-emoji> <b>Не удалось извлечь кадры из медиа.</b>",
        "btn_stop": "❌ Остановить",
    }

    def __init__(self):
        self._task = None

    async def on_unload(self):
        if self._task and not self._task.done():
            self._task.cancel()

    async def _stop_callback(self, call):
        if self._task and not self._task.done():
            self._task.cancel()
            self._task = None
        await call.edit(self.strings("stopped"))

    def _stop_markup(self) -> list:
        return [[{"text": self.strings("btn_stop"), "callback": self._stop_callback}]]

    def _error(self, exc: Exception) -> str:
        return self.strings("error").format(utils.escape_html(str(exc)))

    @staticmethod
    def _temp_path(suffix: str) -> str:
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        return path

    @staticmethod
    def _remove(path: str):
        with contextlib.suppress(FileNotFoundError):
            os.remove(path)

    @staticmethod
    def _is_video(reply) -> bool:
        if getattr(reply, "video", None) or getattr(reply, "gif", None):
            return True
        document = reply.document
        if not document:
            return False
        return (document.mime_type or "").startswith("video/") or any(
            isinstance(attr, DocumentAttributeVideo) for attr in document.attributes
        )

    async def _get_full_user(self, target):
        full = await self.client(GetFullUserRequest(target))
        return getattr(full, "full_user", full)

    async def _upload_avatar(self, path: str, is_video: bool, fallback: bool = False):
        uploaded = await self.client.upload_file(path)
        if is_video:
            request = UploadProfilePhotoRequest(video=uploaded, video_start_ts=0.0, fallback=fallback)
        else:
            request = UploadProfilePhotoRequest(file=uploaded, fallback=fallback)
        await self.client(request)

    async def _delete_photos(self, photos) -> int:
        input_photos = [
            InputPhoto(id=p.id, access_hash=p.access_hash, file_reference=p.file_reference)
            for p in photos
        ]
        for i in range(0, len(input_photos), DELETE_CHUNK_SIZE):
            await self.client(DeletePhotosRequest(id=input_photos[i : i + DELETE_CHUNK_SIZE]))
        return len(input_photos)

    async def _delete_public_avatar(self) -> bool:
        """Removes the public (fallback) avatar; returns whether one existed"""
        try:
            fallback_photo = getattr(await self._get_full_user("me"), "fallback_photo", None)
            if fallback_photo:
                with contextlib.suppress(Exception):
                    await self._delete_photos([fallback_photo])
            await self.client(UpdateProfilePhotoRequest(id=InputPhotoEmpty(), fallback=True))
        except Exception:
            return False
        return bool(fallback_photo)

    async def _resolve_avatar(self, target, public=False):
        photo = None
        if not public:
            with contextlib.suppress(Exception):
                photos = await self.client.get_profile_photos(target, limit=1)
                if photos:
                    photo = photos[0]

        if not photo:
            with contextlib.suppress(Exception):
                full_user = await self._get_full_user(target)
                photo = getattr(full_user, "fallback_photo", None)
                if not public:
                    photo = photo or getattr(full_user, "profile_photo", None)

        return photo

    async def _download_avatar(self, photo, path: str):
        if getattr(photo, "video_sizes", None):
            return await self.client.download_media(photo, file=path, thumb=photo.video_sizes[-1])
        return await self.client.download_media(photo, file=path)

    async def _send_all_avatars(self, message, target):
        await utils.answer(message, self.strings("archiving"))
        try:
            photos = await self.client.get_profile_photos(target, limit=None)
        except Exception:
            return await utils.answer(message, self.strings("user_not_found"))

        if not photos:
            with contextlib.suppress(Exception):
                if fallback_photo := getattr(await self._get_full_user(target), "fallback_photo", None):
                    photos = [fallback_photo]

        if not photos:
            return await utils.answer(message, self.strings("no_avas"))

        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, "avatars.zip")
        try:
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for idx, photo in enumerate(photos, 1):
                    ext = ".mp4" if getattr(photo, "video_sizes", None) else ".jpg"
                    fname = f"avatar_{idx:03d}{ext}"
                    fpath = os.path.join(temp_dir, fname)
                    await self._download_avatar(photo, fpath)
                    zipf.write(fpath, arcname=fname)

            await utils.answer(message, "", file=zip_path)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    async def getavacmd(self, message):
        """[reply | username/id] [all] [-p] — get current avatar or download all to avatars.zip"""
        reply = await message.get_reply_message()
        public = download_all = False
        target = None

        for part in utils.get_args_raw(message).split():
            if part.lower() in PUBLIC_FLAGS:
                public = True
            elif part.lower() in ALL_FLAGS:
                download_all = True
            elif target is None:
                target = int(part) if part.lstrip("-").isdigit() else part

        if target is None:
            target = reply.sender_id if reply else "me"

        if download_all:
            return await self._send_all_avatars(message, target)

        photo = await self._resolve_avatar(target, public=public)
        if not photo:
            return await utils.answer(message, self.strings("no_avas"))

        if not getattr(photo, "video_sizes", None):
            return await utils.answer(message, "", file=photo)

        await utils.answer(message, self.strings("downloading"))
        temp_path = self._temp_path(".mp4")
        try:
            await utils.answer(message, "", file=await self._download_avatar(photo, temp_path))
        finally:
            self._remove(temp_path)

    async def delavascmd(self, message):
        """<count | all | -p> — delete specified number of avatars, all of them, or public avatar"""
        args = utils.get_args_raw(message).lower().strip()
        if not args:
            return await utils.answer(message, self.strings("invalid_args"))

        if args in (*PUBLIC_FLAGS, "fallback"):
            key = "deleted_public" if await self._delete_public_avatar() else "no_avas"
            return await utils.answer(message, self.strings(key))

        if args in ALL_FLAGS:
            deleted = await self._delete_photos(await self.client.get_profile_photos("me", limit=None))
            deleted += await self._delete_public_avatar()
            if not deleted:
                return await utils.answer(message, self.strings("no_avas"))
            return await utils.answer(message, self.strings("deleted").format(deleted))

        try:
            count = int(args)
        except ValueError:
            count = 0
        if count <= 0:
            return await utils.answer(message, self.strings("invalid_args"))

        photos = await self.client.get_profile_photos("me", limit=count)
        if not photos:
            return await utils.answer(message, self.strings("no_avas"))

        await utils.answer(message, self.strings("deleted").format(await self._delete_photos(photos)))

    @staticmethod
    def _parse_setava_args(raw_args: str) -> tuple[bool, float, int] | None:
        """Returns (public, interval, count); count 0 means set once without a loop"""
        parts = raw_args.split()
        public = any(p.lower() in PUBLIC_FLAGS for p in parts)
        numbers = [p for p in parts if p.lower() not in PUBLIC_FLAGS]
        try:
            match numbers:
                case []:
                    return public, 0.0, 0
                case [count]:
                    interval, count = 5.0, int(count)
                case [interval, count, *_]:
                    interval, count = float(interval), int(count)
        except ValueError:
            return None

        if interval < 0 or count <= 0:
            return None
        if count > 1:
            interval = max(interval, MIN_LOOP_INTERVAL)
        return public, interval, min(count, MAX_LOOP_COUNT)

    async def setavacmd(self, message):
        """[-p] <interval> <count> (reply) — set avatar once instantly or loop via inline form"""
        reply = await message.get_reply_message()
        if not reply or not reply.media:
            return await utils.answer(message, self.strings("no_media_reply"))

        is_video = self._is_video(reply)
        if not is_video and reply.document and not (reply.document.mime_type or "").startswith("image/"):
            return await utils.answer(message, self.strings("unsupported_media"))

        parsed = self._parse_setava_args(utils.get_args_raw(message))
        if parsed is None:
            return await utils.answer(message, self.strings("invalid_setava_args"))
        fallback, interval, count = parsed
        success_text = self.strings("public_avatar_set" if fallback else "avatar_set")
        temp_path = self._temp_path(".mp4" if is_video else ".jpg")

        if count <= 1:
            try:
                await self.client.download_media(reply, file=temp_path)
                await self._upload_avatar(temp_path, is_video, fallback)
                return await utils.answer(message, success_text)
            except Exception as e:
                return await utils.answer(message, self._error(e))
            finally:
                self._remove(temp_path)

        if self._task and not self._task.done():
            self._remove(temp_path)
            return await utils.answer(message, self.strings("already_running"))

        form = await self.inline.form(text=self.strings("downloading"), message=message)
        try:
            await self.client.download_media(reply, file=temp_path)
        except Exception as e:
            self._remove(temp_path)
            return await form.edit(text=self._error(e))

        self._task = asyncio.create_task(
            self._avatar_loop(form, temp_path, is_video, interval, count, fallback)
        )
        await form.edit(
            text=self.strings("started").format("Public" if fallback else "Profile", count, interval),
            reply_markup=self._stop_markup(),
        )

    async def _extract_frames(self, video_path: str, frames_dir: str) -> list[str]:
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-y",
            "-i",
            video_path,
            "-q:v",
            "2",
            os.path.join(frames_dir, "frame_%06d.jpg"),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()
        frames = sorted(
            os.path.join(frames_dir, f)
            for f in os.listdir(frames_dir)
            if f.startswith("frame_") and f.endswith(".jpg")
        )
        step = -(-len(frames) // MAX_GIFAVA_FRAMES)
        return frames[::step][:MAX_GIFAVA_FRAMES] if frames else frames

    async def gifavacmd(self, message):
        """(reply) — create frame-by-frame avatar animation from a video (up to 50 evenly spaced frames)"""
        reply = await message.get_reply_message()
        if not reply or not reply.media:
            return await utils.answer(message, self.strings("no_media_reply"))

        is_gif_file = reply.document and reply.document.mime_type == "image/gif"
        if not self._is_video(reply) and not is_gif_file:
            return await utils.answer(message, self.strings("unsupported_media"))

        if self._task and not self._task.done():
            return await utils.answer(message, self.strings("already_running"))

        form = await self.inline.form(text=self.strings("downloading"), message=message)
        video_path = self._temp_path(".mp4")
        frames_dir = tempfile.mkdtemp()

        def cleanup():
            self._remove(video_path)
            shutil.rmtree(frames_dir, ignore_errors=True)

        try:
            await self.client.download_media(reply, file=video_path)
            await form.edit(text=self.strings("extracting_frames"))
            frames = await self._extract_frames(video_path, frames_dir)
        except Exception as e:
            cleanup()
            return await form.edit(text=self._error(e))

        if not frames:
            cleanup()
            return await form.edit(text=self.strings("no_frames"))

        # Uploaded last-to-first so the first frame ends up as the current avatar.
        frames.reverse()
        self._task = asyncio.create_task(self._gifava_loop(form, frames, cleanup))
        await form.edit(
            text=self.strings("gifava_progress").format(0, len(frames)),
            reply_markup=self._stop_markup(),
        )

    async def stopavacmd(self, message):
        """— stop current avatar auto-set or animation process"""
        if not self._task or self._task.done():
            return await utils.answer(message, self.strings("not_running"))

        self._task.cancel()
        self._task = None
        await utils.answer(message, self.strings("stopped"))

    @staticmethod
    async def _safe_edit(form, text: str, reply_markup=None):
        with contextlib.suppress(Exception):
            await form.edit(text=text, reply_markup=reply_markup)

    async def _run_loop(self, form, steps, done_text: str, cleanup):
        """Runs an upload loop in the background and reports its final state in the form"""
        try:
            await steps
            await self._safe_edit(form, done_text)
        except asyncio.CancelledError:
            await self._safe_edit(form, self.strings("stopped"))
        except FloodWaitError as e:
            await self._safe_edit(form, self.strings("flood_wait").format(e.seconds))
        except Exception as e:
            await self._safe_edit(form, self._error(e))
        finally:
            cleanup()
            if self._task is asyncio.current_task():
                self._task = None

    async def _avatar_loop(self, form, file_path, is_video, interval, count, fallback=False):
        async def steps():
            for i in range(1, count + 1):
                await self._upload_avatar(file_path, is_video, fallback)
                if i == count:
                    break
                # Fast loops only refresh progress every 5th step to avoid edit flood limits.
                if interval >= 3.0 or i % 5 == 0:
                    await self._safe_edit(form, self.strings("progress").format(i, count), self._stop_markup())
                await asyncio.sleep(interval)

        await self._run_loop(
            form, steps(), self.strings("done").format(count), lambda: self._remove(file_path)
        )

    async def _gifava_loop(self, form, frames, cleanup):
        total = len(frames)

        async def steps():
            for i, frame_path in enumerate(frames, 1):
                await self._upload_avatar(frame_path, is_video=False)
                if i == total:
                    break
                await self._safe_edit(
                    form, self.strings("gifava_progress").format(i, total), self._stop_markup()
                )
                await asyncio.sleep(GIFAVA_FRAME_DELAY)

        await self._run_loop(form, steps(), self.strings("gifava_done").format(total), cleanup)
