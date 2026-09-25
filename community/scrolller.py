# ---------------------------------------------------------------------------------
#  /\_/\  🌐 This module was loaded through https://t.me/hikkamods_bot
# ( o.o )  🔐 Licensed under the GNU AGPLv3.
#  > ^ <   ⚠️ Owner of heta.hikariatama.ru doesn't take any responsibilities or intellectual property rights regarding this script
# ---------------------------------------------------------------------------------
# Name: scrolller
# Author: hikariatama
# Commands:
# .gallery | .gallerycat
# ---------------------------------------------------------------------------------

#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html
# Modified for Kage by gerdaroot (https://github.com/gerdaroot/kage-modules), 2026-09-25

# meta pic: https://static.dan.tatar/scrolller_icon.png
# meta banner: https://mods.hikariatama.ru/badges/scrolller.jpg
# meta developer: @hikarimods
# scope: hikka_only
# scope: hikka_min 1.2.10
# scope: heroku_min 2.0.0

import functools
import random

import aiohttp
from telethon.tl.types import Message
from telethon.utils import get_display_name

from .. import loader, utils
from ..inline.types import InlineQuery

API_URL = "https://api.scrolller.com/admin"
# Cloudflare in front of the API rejects default library user agents with 403.
HEADERS = {"user-agent": "Mozilla/5.0", "accept": "*/*"}
# Telegram fetches inline photos by URL and rejects huge originals, so prefer a mid-size JPEG.
MAX_PHOTO_WIDTH = 1280
PHOTOS_PER_PAGE = 15


class ScrolllerError(Exception):
    pass


async def graphql(query: str, variables: dict) -> dict:
    async with aiohttp.ClientSession(
        headers=HEADERS, timeout=aiohttp.ClientTimeout(total=20)
    ) as session:
        async with session.post(
            API_URL,
            json={"query": query, "variables": variables, "authorization": None},
        ) as response:
            response.raise_for_status()
            answer = await response.json(content_type=None)

    if answer.get("errors"):
        raise ScrolllerError(answer["errors"][0].get("message"))

    return answer["data"]


def pick_photo(media_sources: list[dict]) -> str | None:
    jpegs = sorted(
        (source for source in media_sources if source.get("type") == "JPEG"),
        key=lambda source: source.get("width") or 0,
    )
    fitting = [source for source in jpegs if (source.get("width") or 0) <= MAX_PHOTO_WIDTH]
    if chosen := (fitting[-1] if fitting else jpegs[0] if jpegs else None):
        return chosen["url"]
    return None


def subreddit_path(subreddit: str) -> str:
    return subreddit if subreddit.startswith("/r/") else f"/r/{subreddit.strip('/')}"


async def get_subreddit(subreddit: str) -> dict | None:
    """Returns subreddit info, or None if it does not exist"""
    data = await graphql(
        "query SubredditQuery($url: String!) {"
        " getSubreddit(data: {url: $url, limit: 1}) {"
        " url title secondaryTitle description isNsfw } }",
        {"url": subreddit_path(subreddit)},
    )
    return data["getSubreddit"]


async def photos(subreddit: str, quantity: int) -> list[str]:
    """Loads `quantity` random photos from `subreddit` on scrolller.com"""
    data = await graphql(
        "query SubredditQuery($url: String!, $limit: Int!) {"
        " getSubreddit(data: {url: $url, filter: PICTURE, limit: $limit, sortBy: RANDOM}) {"
        " children { items { mediaSources { url width type } } } } }",
        {"url": subreddit_path(subreddit), "limit": quantity},
    )
    if not data["getSubreddit"]:
        return []

    posts = data["getSubreddit"]["children"]["items"]
    return [url for post in posts if (url := pick_photo(post["mediaSources"]))]


def caption(subreddit: dict) -> str:
    return (
        f"{'🔞' if subreddit['is_nsfw'] else '👨‍👩‍👧'} <b>{utils.escape_html(subreddit['secondary_title'])} ({utils.escape_html(subreddit['url'])})</b>\n\n<i>{utils.escape_html(subreddit['description'] or '')}</i>\n\n<i>Enjoy!"
        f" {utils.ascii_face()}</i>"
    )


async def search_subreddit(query: str) -> list[dict]:
    """Searches for subreddits using `query`"""
    # isNsfw: true returns SFW and NSFW results together, like null did in the old API.
    data = await graphql(
        "query SearchSubredditsQuery($query: String!) {"
        " searchSubreddits(data: {query: $query, isNsfw: true, limit: 50, pageIndex: 0}) {"
        " url secondary_title description is_nsfw } }",
        {"query": query},
    )
    res = data["searchSubreddits"] or []
    random.shuffle(res)
    return res[:30]


async def fetch_multiple_subreddits(subreddits: list[str]) -> list[str | None]:
    """Fetches one preview photo per subreddit, in the same order"""
    args = " ".join(f"$url_{i}: String!" for i in range(len(subreddits)))
    funcs = " ".join(
        f"s_{i}: getSubreddit(data: {{url: $url_{i}, filter: PICTURE, limit: 1}}) {{"
        " children { items { mediaSources { url width type } } } }"
        for i in range(len(subreddits))
    )
    data = await graphql(
        f"query SubredditQuery({args}) {{ {funcs} }}",
        {f"url_{i}": subreddit_path(subreddit) for i, subreddit in enumerate(subreddits)},
    )

    thumbs = []
    for i in range(len(subreddits)):
        items = ((data.get(f"s_{i}") or {}).get("children") or {}).get("items") or []
        thumbs.append(pick_photo(items[0]["mediaSources"]) if items else None)
    return thumbs


@loader.tds
class ScrolllerMod(loader.Module):
    """Sends pictures from scrolller.com via inline gallery"""

    strings = {
        "name": "Scrolller",
        "sreddit404": "🚫 <b>Subreddit not found</b>",
        "default_subreddit": "🙂 <b>Set new default subreddit: </b><code>{}</code>",
    }

    strings_ru = {
        "sreddit404": "🚫 <b>Сабреддит не найден</b>",
        "default_subreddit": (
            "🙂 <b>Установил новый сабреддит по умолчанию: </b><code>{}</code>"
        ),
        "_cmd_doc_gallery": (
            "<сабреддит> [-n <количество | 1 по умолчанию>] - Отправляет случайную 18+"
            " картинку"
        ),
        "_cmd_doc_gallerycat": "<сабреддит> - Установить новый сабреддит по умолчанию",
        "_cls_doc": "Отправляет изображения с scrolller.com в виде инлайн галереи",
    }

    async def gallerycmd(self, message: Message):
        """<subreddit | default> - Send inline gallery with photos from subreddit"""
        args = utils.get_args_raw(message) or self.get("default_subreddit", "cat")
        reply = await message.get_reply_message()

        if reply:
            for_ = (
                "<b>❤️ Special for"
                f" {utils.escape_html(get_display_name(reply.sender))}</b>"
            )
        else:
            for_ = ""

        subreddit = subreddit_path(args)
        if not await get_subreddit(subreddit):
            await utils.answer(message, self.strings("sreddit404", message))
            return

        await self.inline.gallery(
            message=message,
            next_handler=functools.partial(photos, subreddit=subreddit, quantity=PHOTOS_PER_PAGE),
            caption=lambda: f"<i>Enjoy this {utils.escape_html(subreddit)} photos &lt;3\n{utils.ascii_face()}</i>\n\n{for_}",
            always_allow=[reply.sender_id] if reply else [],
        )

    async def gallerycatcmd(self, message: Message):
        """<subreddit> - Set new default subreddit"""
        args = utils.get_args_raw(message) or "cat"

        if not await get_subreddit(args):
            await utils.answer(message, self.strings("sreddit404", message))
            return

        self.set("default_subreddit", args)
        await utils.answer(
            message,
            self.strings("default_subreddit", message).format(utils.escape_html(args)),
        )

    async def gallery_inline_handler(self, query: InlineQuery):
        """
        Search for Scrolller subreddits
        """
        subreddits = await search_subreddit(query.args or self.get("default_subreddit", "cat"))
        if not subreddits:
            await query.e404()
            return

        thumbs = await fetch_multiple_subreddits([i["url"] for i in subreddits])
        results = [
            (subreddit, thumb)
            for subreddit, thumb in zip(subreddits, thumbs, strict=True)
            if thumb
        ]
        if not results:
            await query.e404()
            return

        await self.inline.query_gallery(
            query,
            [
                {
                    "title": (
                        f"{'🔞' if subreddit['is_nsfw'] else '👨‍👩‍👧'} {subreddit['secondary_title']} ({subreddit['url']})"
                    ),
                    "description": subreddit["description"] or "",
                    "next_handler": functools.partial(
                        photos,
                        subreddit=subreddit["url"],
                        quantity=PHOTOS_PER_PAGE,
                    ),
                    "thumb_handler": [thumb],
                    "caption": functools.partial(
                        caption,
                        subreddit=subreddit,
                    ),
                }
                for subreddit, thumb in results
            ],
        )
