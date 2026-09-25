# meta developer: @gerdacod
# meta banner: https://raw.githubusercontent.com/gerdaroot/kage-modules/main/assets/banner.png
# scope: heroku_min 2.0.0

import aiohttp

from herokutl.tl.types import InputMediaDocumentExternal, InputMediaPhotoExternal
from herokutl.types import Message

from .. import loader, utils

API_URL = "https://api.waifu.im/images"

# adult-only content tags; "uniform" is left out on purpose (school uniforms)
NSFW_TAGS = ("hentai", "ero", "ecchi", "oppai", "milf", "ass", "paizuri", "oral", "maid")
SFW_TAGS = ("waifu", "maid", "uniform", "selfies", "genshin-impact", "raiden-shogun", "kamisato-ayaka", "mori-calliope")

# characters who are minors in canon (and school uniforms) never appear in NSFW results;
# any image carrying one of these tags is dropped even if the API filter misses it
MINOR_TAGS = frozenset({"marin-kitagawa", "rem", "loli", "shota", "child", "kid", "teen"})
NSFW_EXCLUDED_TAGS = MINOR_TAGS | {"uniform"}

MAX_ATTEMPTS = 5


@loader.tds
class HentaiMod(loader.Module):
    """Random adult anime art (18+) and SFW waifus from waifu.im"""

    strings = {
        "name": "Hentai",
        "loading": "🔞 <b>Looking…</b>",
        "unknown_tag": "🚫 <b>Unknown tag</b> <code>{tag}</code>\n\n🔞 NSFW: {nsfw}\n🌸 SFW: {sfw}",
        "tags": "🔞 <b>NSFW:</b> {nsfw}\n🌸 <b>SFW:</b> {sfw}\n\n<code>{prefix}hentai [tag]</code> · <code>{prefix}waifu [tag]</code>",
        "not_found": "🙈 <b>Nothing found, try again or another tag</b>",
        "api_error": "🚫 <b>waifu.im didn't answer:</b> <code>{error}</code>",
        "caption": "🎨 {artist}{source}",
        "unknown_artist": "unknown artist",
        "cfg_spoiler": "Send pictures hidden under a spoiler",
    }

    strings_ru = {
        "loading": "🔞 <b>Ищу…</b>",
        "unknown_tag": "🚫 <b>Нет такого тега</b> <code>{tag}</code>\n\n🔞 NSFW: {nsfw}\n🌸 SFW: {sfw}",
        "tags": "🔞 <b>NSFW:</b> {nsfw}\n🌸 <b>SFW:</b> {sfw}\n\n<code>{prefix}hentai [тег]</code> · <code>{prefix}waifu [тег]</code>",
        "not_found": "🙈 <b>Ничего не нашлось, попробуй ещё раз или другой тег</b>",
        "api_error": "🚫 <b>waifu.im не ответил:</b> <code>{error}</code>",
        "unknown_artist": "неизвестный автор",
        "cfg_spoiler": "Отправлять картинки под спойлером",
        "_cls_doc": "Случайные аниме-арты 18+ и SFW-вайфу с waifu.im",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "spoiler",
                True,
                lambda: self.strings("cfg_spoiler"),
                validator=loader.validators.Boolean(),
            ),
        )

    async def _fetch(self, tag: str, nsfw: bool) -> dict | None:
        params = [
            ("IncludedTags", tag),
            ("IsNsfw", str(nsfw).lower()),
            ("OrderBy", "Random"),
            ("PageSize", "1"),
        ]
        if nsfw:
            # the API rejects comma lists: every excluded tag needs its own parameter
            params += [("ExcludedTags", t) for t in sorted(NSFW_EXCLUDED_TAGS)]

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
            for _ in range(MAX_ATTEMPTS):
                async with session.get(API_URL, params=params) as response:
                    response.raise_for_status()
                    items = (await response.json()).get("items") or []
                if not items:
                    return None
                image = items[0]
                blocked = NSFW_EXCLUDED_TAGS if nsfw else MINOR_TAGS
                if image.get("isNsfw") is nsfw and not {t.get("slug") for t in image.get("tags", [])} & blocked:
                    return image
        return None

    def _caption(self, image: dict) -> str:
        artist = next(iter(image.get("artists") or []), {}).get("name") or self.strings("unknown_artist")
        source = image.get("source")
        return self.strings("caption").format(
            artist=utils.escape_html(artist),
            source=f' · <a href="{utils.escape_html(source)}">source</a>' if source else "",
        )

    async def _send(self, message: Message, nsfw: bool):
        tags = NSFW_TAGS if nsfw else SFW_TAGS
        tag = (utils.get_args_raw(message) or tags[0]).strip().lower()
        prefix = utils.escape_html(self.get_prefix())

        if tag == "tags":
            await utils.answer(
                message,
                self.strings("tags").format(nsfw=", ".join(NSFW_TAGS), sfw=", ".join(SFW_TAGS), prefix=prefix),
            )
            return
        if tag not in tags:
            await utils.answer(
                message,
                self.strings("unknown_tag").format(
                    tag=utils.escape_html(tag), nsfw=", ".join(NSFW_TAGS), sfw=", ".join(SFW_TAGS)
                ),
            )
            return

        status = await utils.answer(message, self.strings("loading"))
        try:
            image = await self._fetch(tag, nsfw)
        except (aiohttp.ClientError, TimeoutError) as e:
            await utils.answer(status, self.strings("api_error").format(error=utils.escape_html(str(e)[:200])))
            return
        if not image:
            await utils.answer(status, self.strings("not_found"))
            return

        spoiler = self.config["spoiler"]
        # gifs go as documents, otherwise Telegram shows a static frame
        media = (
            InputMediaDocumentExternal(image["url"], spoiler=spoiler)
            if image.get("isAnimated")
            else InputMediaPhotoExternal(image["url"], spoiler=spoiler)
        )
        reply = await message.get_reply_message()
        await utils.answer_file(status, media, caption=self._caption(image), reply_to=reply.id if reply else None)

    @loader.command(ru_doc="[тег | tags] — случайный арт 18+ (hentai, ero, milf…)")
    async def hentai(self, message: Message):
        """[tag | tags] — random 18+ art (hentai, ero, milf…)"""
        await self._send(message, nsfw=True)

    @loader.command(ru_doc="[тег | tags] — случайная SFW-вайфу")
    async def waifu(self, message: Message):
        """[tag | tags] — random SFW waifu"""
        await self._send(message, nsfw=False)
