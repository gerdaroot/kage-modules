# meta developer: @gerdacod
# scope: heroku_min 2.0.0

import asyncio
import os
import platform
import re
import shutil
import time

import psutil
from herokutl.tl.functions.updates import GetStateRequest
from herokutl.types import Message

from .. import loader, utils

LOGO = [
    # Telegram trims a leading space off the message; U+2800 is a blank it keeps
    "\u2800▄██▄ ▄██▄ ",
    "███████████",
    " ▀███████▀ ",
    "   ▀███▀   ",
    "     ▀     ",
]
# phones fit about 38 monospace characters per line before wrapping
VALUE_WIDTH = 20
LABEL_WIDTH = 7

CPU_NOISE = re.compile(r"\((?:R|TM)\)|\bCPU\b|\bProcessor\b|@.*$|\s+\d+-Core", re.IGNORECASE)


def _human_bytes(value: float) -> str:
    for unit in ("B", "K", "M", "G", "T"):
        if value < 1024 or unit == "T":
            return f"{value:.0f}{unit}" if unit in "BK" else f"{value:.1f}{unit}"
        value /= 1024
    return f"{value:.1f}T"


def _human_duration(seconds: float) -> str:
    minutes, _ = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    parts = [f"{days}d"] if days else []
    parts += [f"{hours}h"] if hours or days else []
    return " ".join(parts + [f"{minutes}m"])


def _os_name() -> str:
    try:
        release = platform.freedesktop_os_release()
        name = release.get("PRETTY_NAME") or release.get("NAME", "Linux")
        name = re.sub(r"\s+", " ", re.sub(r"GNU/Linux|\(.*?\)", "", name)).strip()
    except OSError:
        name = f"macOS {platform.mac_ver()[0]}" if platform.system() == "Darwin" else f"{platform.system()} {platform.release()}"
    if os.path.exists("/.dockerenv") or "DOCKER" in os.environ:
        name += " · Docker"
    return name


def _cpu_name() -> str:
    model = ""
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as f:
            model = next((line.split(":", 1)[1] for line in f if line.startswith(("model name", "Model"))), "")
    except OSError:
        model = platform.processor()
    return re.sub(r"\s+", " ", CPU_NOISE.sub("", model)).strip() or platform.machine()


def _collect() -> dict[str, str]:
    """Blocking system reads (cpu_percent sleeps); runs in a thread"""
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/data" if os.path.isdir("/data") else "/")
    cpu_load = psutil.cpu_percent(interval=0.5)
    return {
        "OS": _os_name(),
        "Kernel": platform.release().split("-")[0],
        "Uptime": _human_duration(time.time() - psutil.boot_time()),
        "CPU": _cpu_name(),
        "Load": f"{cpu_load:.0f}% · {psutil.cpu_count() or '?'} cores",
        "RAM": f"{_human_bytes(memory.used)} / {_human_bytes(memory.total)} ({memory.percent:.0f}%)",
        "Disk": f"{_human_bytes(disk.used)} / {_human_bytes(disk.total)} ({disk.percent:.0f}%)",
        "Python": platform.python_version(),
    }


def _fit(value: str) -> str:
    return value if len(value) <= VALUE_WIDTH else value[: VALUE_WIDTH - 1] + "…"


@loader.tds
class NeofetchMod(loader.Module):
    """System information in neofetch style"""

    strings = {
        "name": "Neofetch",
        "no_binary": "🚫 <b>The neofetch program isn't installed — run</b> <code>{prefix}neofetch</code> <b>without</b> <code>-n</code>",
        "failed": "🚫 <b>neofetch failed:</b> <code>{error}</code>",
        "cfg_logo": "Show the Kage heart next to the info",
    }

    strings_ru = {
        "no_binary": "🚫 <b>Программа neofetch не установлена — используй</b> <code>{prefix}neofetch</code> <b>без</b> <code>-n</code>",
        "failed": "🚫 <b>neofetch завершился с ошибкой:</b> <code>{error}</code>",
        "cfg_logo": "Показывать сердце Kage рядом с информацией",
        "_cls_doc": "Информация о системе в стиле neofetch",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "logo",
                True,
                lambda: self.strings("cfg_logo"),
                validator=loader.validators.Boolean(),
            ),
        )

    async def _ping_ms(self) -> float:
        start = time.perf_counter()
        await self._client(GetStateRequest())
        return (time.perf_counter() - start) * 1000

    async def _bot_line(self) -> str:
        try:
            from .. import version

            name = f"Kage {version.kage_version}"
        except (ImportError, AttributeError):
            name = "Userbot"
        return f"{name} · {_human_duration(utils.uptime())}"

    async def _render(self) -> str:
        info = await asyncio.to_thread(_collect)
        info["Bot"] = await self._bot_line()
        info["Mods"] = str(len(self.allmodules.modules))
        info["Ping"] = f"{await self._ping_ms():.0f} ms"

        me = self._client.kage_me if hasattr(self._client, "kage_me") else await self._client.get_me()
        title = f"{me.username or me.first_name or 'user'}@{platform.node() or 'kage'}"
        lines = [_fit(title), "─" * min(len(title), VALUE_WIDTH)]
        lines += [f"{label:<{LABEL_WIDTH}}{_fit(value)}" for label, value in info.items()]

        if self.config["logo"]:
            pad = " " * len(LOGO[0])
            lines = [
                f"{LOGO[i] if i < len(LOGO) else pad} {line}" for i, line in enumerate(lines)
            ]
        return "<pre>" + utils.escape_html("\n".join(lines)) + "</pre>"

    async def _native(self) -> str:
        if not shutil.which("neofetch"):
            return self.strings("no_binary").format(prefix=utils.escape_html(self.get_prefix()))
        proc = await asyncio.create_subprocess_exec(
            "neofetch", "--stdout", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        out, err = await proc.communicate()
        if proc.returncode != 0:
            return self.strings("failed").format(error=utils.escape_html(err.decode(errors="replace")[:300]))
        return "<pre>" + utils.escape_html(out.decode(errors="replace").strip()) + "</pre>"

    @loader.command(ru_doc="[-n] — информация о системе (-n: вывод самой программы neofetch)")
    async def neofetch(self, message: Message):
        """[-n] — system info (-n: output of the neofetch program itself)"""
        native = "-n" in utils.get_args(message)
        await utils.answer(message, await (self._native() if native else self._render()))
