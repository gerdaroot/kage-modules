# ---------------------------------------------------------------------------------
#  /\_/\  🌐 This module was loaded through https://t.me/hikkamods_bot
# ( o.o )  🔐 Licensed under the GNU AGPLv3.
#  > ^ <   ⚠️ Owner of heta.hikariatama.ru doesn't take any responsibilities or intellectual property rights regarding this script
# ---------------------------------------------------------------------------------
# Name: httpsc
# Description: Dictionary of http status codes
# Author: hikariatama
# Commands:
# .httpsc | .httpscs
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
# scope: heroku_min 2.0.0

# meta pic: https://img.icons8.com/external-flaticons-lineal-color-flat-icons/512/000000/external-status-agile-flaticons-lineal-color-flat-icons-2.png
# meta banner: https://mods.hikariatama.ru/badges/httpsc.jpg
# meta developer: @hikarimods

from telethon.tl.types import Message

from .. import loader, utils

responses = {
    100: ("ℹ️ Continue", "Запрос принят, продолжай"),
    101: ("ℹ️ Switching Protocols", "Изменение протокола; подчинйся Upgrade хедеру"),
    200: ("✅ OK", "Запрос успешный, контент отображен"),
    201: ("✅ Created", "Запрос создан, url прилагается"),
    202: ("✅ Accepted", "Запрос принят и обрабатывается оффлайн"),
    203: ("✅ Non-Authoritative Information", "Загружено из кэша"),
    204: ("✅ No Content", "Запрос успешный, нет контента"),
    205: ("✅ Reset Content", "Очистить форму для продолжения"),
    206: ("✅ Partial Content", "Частичный контент прилагается"),
    300: ("↩️ Multiple Choices", "У объекта есть несколько источников"),
    301: ("↩️ Moved Permanently", "Адрес изменен навсегда"),
    302: ("↩️ Found", "Адрес изменен временно"),
    303: ("↩️ See Other", "Адрес и\\или объект изменен"),
    304: ("↩️ Not Modified", "Контент не изменился с предыдущего запроса"),
    305: ("↩️ Use Proxy", "Неверная локация"),
    307: ("↩️ Temporary Redirect", "Временное перенаправление"),
    400: ("🚫 Bad Request", "Ошибка формирования запроса со стороны клиента"),
    401: ("🚫 Unauthorized", "Не авторизован"),
    402: ("🚫 Payment Required", "Не оплачено"),
    403: ("🚫 Forbidden", "Доступ запрещен - бан / нехватка прав"),
    404: ("🚫 Not Found", "Не найдено"),
    405: ("🚫 Method Not Allowed", "Метод запрещен"),
    406: ("🚫 Not Acceptable", "Метод недоступен"),
    407: ("🚫 Proxy Authentication Required", "Не хватает авторизации прокси"),
    408: ("🚫 Request Timeout", "Время ожидания истекло"),
    409: ("🚫 Conflict", "Конфликт запросов"),
    410: ("🚫 Gone", "Адрес не существует и был перемещен"),
    411: ("🚫 Length Required", "Требуется указание длины контента запроса"),
    412: ("🚫 Precondition Failed", "Предусловие в хедерах неверно"),
    413: ("🚫 Request Entity Too Large", "Запрос слишком большой"),
    414: ("🚫 Request-URI Too Long", "Ссылка слишком большая"),
    415: ("🚫 Unsupported Media Type", "Неподдерживаеый формат контента"),
    416: ("🚫 Requested Range Not Satisfiable", "Не входит в разрешенный диапазон"),
    417: ("🚫 Expectation Failed", "Ожидания не выполняются"),
    500: ("💢 Internal Server Error", "Ошибка сервера"),
    501: ("💢 Not Implemented", "Операция не поддерживается"),
    502: ("💢 Bad Gateway", "Прокси \\ шлюз недоступен"),
    503: ("💢 Service Unavailable", "Перегрузка сервера"),
    504: ("💢 Gateway Timeout", "Таймаут прокси \\ шлюза"),
    505: ("💢 HTTP Version Not Supported", "Версия HTTP не соответствует требованиям"),
}


@loader.tds
class HttpErrorsMod(loader.Module):
    """Dictionary of http status codes"""

    strings = {
        "name": "HttpStatusCodes",
        "args_incorrect": "<b>Incorrect args</b>",
        "not_found": "<b>Code not found</b>",
        "syntax_error": "<b>Args are mandatory</b>",
        "scode": "<b>{} {}</b>\n⚜️ Описание кода: <i>{}</i>",
    }

    strings_ru = {
        "args_incorrect": "<b>Неверные аргументы</b>",
        "not_found": "<b>Код не найден</b>",
        "syntax_error": "<b>Аргументы обязательны</b>",
        "_cmd_doc_httpsc": "<код> - Получить информацию о HTTP-коде",
        "_cmd_doc_httpscs": "Показать все доступные коды",
        "_cls_doc": "Словарь HTTP-кодов",
    }

    async def httpsccmd(self, message: Message):
        """<statuscode> - Get status code info"""
        args = utils.get_args(message)
        if not args:
            await utils.answer(message, self.strings("syntax_error", message))
            return

        try:
            code = int(args[0])
        except ValueError:
            await utils.answer(message, self.strings("args_incorrect", message))
            return

        if code not in responses:
            await utils.answer(message, self.strings("not_found", message))
            return

        title, description = responses[code]
        await utils.answer(
            message,
            self.strings("scode", message).format(title, code, description),
        )

    async def httpscscmd(self, message: Message):
        """Get all http status codes"""
        await utils.answer(
            message,
            "\n".join(
                f"<b>{code}: {title[0]} {description}</b>"
                for code, (title, description) in responses.items()
            ),
        )
