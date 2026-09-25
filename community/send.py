# ---------------------------------------------------------------------------------
#░█▀▄░▄▀▀▄░█▀▄░█▀▀▄░█▀▀▄░█▀▀▀░▄▀▀▄░░░█▀▄▀█
#░█░░░█░░█░█░█░█▄▄▀░█▄▄█░█░▀▄░█░░█░░░█░▀░█
#░▀▀▀░░▀▀░░▀▀░░▀░▀▀░▀░░▀░▀▀▀▀░░▀▀░░░░▀░░▒▀
# Name: send
# Description: феля не бей меня попросили
# Author: @codrago_m
# ---------------------------------------------------------------------------------
# 🔒    Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html
# Modified for Kage by gerdaroot (https://github.com/gerdaroot/kage-modules), 2026-09-25
# ---------------------------------------------------------------------------------
# Author: @codrago
# Commands: id, chatid, userid
# scope: hikka_only
# meta developer: @codrago_m
# meta banner: https://raw.githubusercontent.com/coddrago/modules/refs/heads/main/banner.png
# meta pic: https://kappa.lol/p3wVI
# ---------------------------------------------------------------------------------

from .. import loader, utils


@loader.tds
class Send(loader.Module):
    """| module to send messages"""

    strings = {
        "name": "Send",
        "no_args": "<b>Where args?</b>",
        "nobody_s": "<b>Who should i send it to?</b>",
        "succesfully_send": "<b>Message succesfully sended</b>",
        "error": "<pre><code class='language-python'>{}</code></pre>",
    }

    async def _deliver(self, message, peer, content):
        try:
            await self.client.send_message(peer, content)
        except Exception as e:
            await utils.answer(message, self.strings("error").format(utils.escape_html(str(e))))
            return
        await utils.answer(message, self.strings("succesfully_send"))

    @loader.command()
    async def send(self, message):
        """[user] [text] | Send message to user"""
        args = utils.get_args_raw(message).split(maxsplit=1)
        if not args:
            await utils.answer(message, self.strings("nobody_s"))
            return
        if len(args) < 2:
            await utils.answer(message, self.strings("no_args"))
            return

        user, text = args
        peer = int(user) if user.lstrip("-").isdigit() else user
        await self._deliver(message, peer, text)

    @loader.command()
    async def sendsm(self, message):
        """[reply or text] | send message to saved messages"""
        content = utils.get_args_raw(message) or await message.get_reply_message()
        if not content:
            await utils.answer(message, self.strings("no_args"))
            return

        await self._deliver(message, "me", content)
