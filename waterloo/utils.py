from typing import Optional

from prompt_toolkit import HTML, print_formatted_text
from prompt_toolkit.styles import Style

from waterloo.types import LogLevel


class StylePrinter:
    DEFAULT_STYLES = Style.from_dict(
        {
            "debug": "fg:#b8b8b8",
            "info": "fg:ansigray",
            "warning": "fg:ansiyellow",
            "error": "fg:ansired",
        }
    )

    style: Style
    log_level: LogLevel

    def __init__(
        self, style: Optional[Style] = None, log_level: LogLevel = LogLevel.INFO,
    ):
        self.style = style or self.DEFAULT_STYLES
        self.log_level = log_level

    def debug(self, msg: str):
        if self.log_level.value <= LogLevel.DEBUG.value:
            self._print_level(msg, "debug")

    def info(self, msg: str):
        if self.log_level.value <= LogLevel.INFO.value:
            self._print_level(msg, "info")

    def warning(self, msg: str):
        if self.log_level.value <= LogLevel.WARNING.value:
            self._print_level(msg, "warning")

    def error(self, msg: str):
        if self.log_level.value <= LogLevel.ERROR.value:
            self._print_level(msg, "error")

    def _print_level(self, msg: str, level: str):
        self.print(f"<{level}>{msg}</{level}>")

    def print(self, msg: str):
        print_formatted_text(HTML(msg), style=self.style)
