from prompt_toolkit import print_formatted_text, HTML
from prompt_toolkit.styles import Style


class StylePrinter:
    DEFAULT_STYLES = Style.from_dict({
        'debug': 'fg:ansigray',
        'info': 'fg:ansiwhite',
        'warning': 'fg:ansiyellow',
        'error': 'fg:ansired',
    })

    def __init__(self, style=DEFAULT_STYLES):
        self.style = style

    def debug(self, msg: str):
        self._print_level(msg, 'debug')

    def info(self, msg: str):
        self._print_level(msg, 'info')

    def warning(self, msg: str):
        self._print_level(msg, 'warning')

    def error(self, msg: str):
        self._print_level(msg, 'error')

    def _print_level(self, msg: str, level: str):
        self.print(f"<{level}>{msg}</{level}>")

    def print(self, msg: str):
        print_formatted_text(HTML(msg), style=self.style)
