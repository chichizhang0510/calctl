# src/calctl/color.py
import sys

class Color:
    """
    Minimal ANSI color helper.
    - enabled: controlled by --no-color
    - only colorize when output is a TTY (avoid polluting redirected output)
    """
    def __init__(self, enabled: bool, *, stream: str = "stdout"):
        if stream == "stderr":
            is_tty = sys.stderr.isatty()
        else:
            is_tty = sys.stdout.isatty()

        self.enabled = enabled and is_tty

    def _wrap(self, text: str, code: str) -> str:
        if not self.enabled:
            return text
        return f"\033[{code}m{text}\033[0m"

    def green(self, text: str) -> str:
        return self._wrap(text, "32")

    def red(self, text: str) -> str:
        return self._wrap(text, "31")

    def yellow(self, text: str) -> str:
        return self._wrap(text, "33")

    def bold(self, text: str) -> str:
        return self._wrap(text, "1")
