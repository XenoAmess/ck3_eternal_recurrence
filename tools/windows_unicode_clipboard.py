"""Temporary Unicode clipboard text for internal, already-authorized consumers.

This helper does not focus a window, paste, send keys, or expose an MCP tool.
Its authoritative owner is this repository; projects consume it by import.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator, Protocol


class UnicodeClipboardAPI(Protocol):
    CF_UNICODETEXT: int
    error: type[Exception]

    def OpenClipboard(self) -> None: ...
    def CloseClipboard(self) -> None: ...
    def IsClipboardFormatAvailable(self, format: int) -> bool: ...
    def GetClipboardData(self, format: int) -> str: ...
    def EmptyClipboard(self) -> None: ...
    def SetClipboardText(self, text: str, format: int) -> None: ...


def _previous_unicode_text(clipboard: UnicodeClipboardAPI) -> str | None:
    if not clipboard.IsClipboardFormatAvailable(clipboard.CF_UNICODETEXT):
        return None
    try:
        previous = clipboard.GetClipboardData(clipboard.CF_UNICODETEXT)
    except clipboard.error as error:
        # Actual pywin32 receipt: (0, 'GetClipboardData', 'No error message ...').
        # An advertised format can still have no retrievable Unicode payload.
        if len(error.args) >= 2 and error.args[0:2] == (0, "GetClipboardData"):
            return None
        raise
    if not isinstance(previous, str):
        raise TypeError("CF_UNICODETEXT did not return Unicode text")
    return previous


@contextmanager
def temporary_unicode_text(text: str, *, clipboard: UnicodeClipboardAPI | None = None) -> Iterator[None]:
    """Set text while the body runs, then restore prior Unicode text or empty.

    The clipboard is closed before yielding. Non-text formats are outside this
    text-only contract. Injecting an API is for tests; production uses pywin32.
    """
    if not isinstance(text, str):
        raise TypeError("temporary clipboard text must be a string")
    if clipboard is None:
        import win32clipboard
        clipboard = win32clipboard
    previous = None
    changed = False
    try:
        clipboard.OpenClipboard()
        try:
            previous = _previous_unicode_text(clipboard)
            changed = True
            clipboard.EmptyClipboard()
            clipboard.SetClipboardText(text, clipboard.CF_UNICODETEXT)
        finally:
            clipboard.CloseClipboard()
        yield
    finally:
        if changed:
            clipboard.OpenClipboard()
            try:
                clipboard.EmptyClipboard()
                if previous is not None:
                    clipboard.SetClipboardText(previous, clipboard.CF_UNICODETEXT)
            finally:
                clipboard.CloseClipboard()
