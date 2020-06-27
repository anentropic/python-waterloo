from typing import Optional

from prompt_toolkit import HTML, print_formatted_text
from prompt_toolkit.styles import Style


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

    def __init__(self, verbose_echo: bool, style: Optional[Style] = None):
        self.style = style or self.DEFAULT_STYLES
        self.verbose_echo = verbose_echo

    def debug(self, msg: str, verbose: bool):
        self._print_level(msg, "debug", verbose)

    def info(self, msg: str, verbose: bool):
        self._print_level(msg, "info", verbose)

    def warning(self, msg: str, verbose: bool):
        self._print_level(msg, "warning", verbose)

    def error(self, msg: str, verbose: bool):
        self._print_level(msg, "error", verbose)

    def _print_level(self, msg: str, level: str, verbose: bool):
        if not verbose or (verbose and self.verbose_echo):
            self.print(f"<{level}>{msg}</{level}>")

    def print(self, msg: str):
        print_formatted_text(HTML(msg), style=self.style)
