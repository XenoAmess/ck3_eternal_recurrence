"""Contract tests with an injected clipboard API; no system clipboard access."""
from __future__ import annotations

import unittest

from windows_unicode_clipboard import temporary_unicode_text


class ClipboardError(Exception):
    pass


class FakeClipboard:
    CF_UNICODETEXT = 13
    error = ClipboardError

    def __init__(self, previous=None, *, advertised=None, read_error=None):
        self.text = previous
        self.advertised = previous is not None if advertised is None else advertised
        self.read_error = read_error
        self.open = False
        self.events = []
        self.write_error = None

    def OpenClipboard(self):
        if self.open:
            raise RuntimeError("clipboard already open")
        self.open = True
        self.events.append("open")

    def CloseClipboard(self):
        if not self.open:
            raise RuntimeError("clipboard already closed")
        self.open = False
        self.events.append("close")

    def IsClipboardFormatAvailable(self, format):
        self.assert_format(format)
        self.events.append("available")
        return self.advertised

    def GetClipboardData(self, format):
        self.assert_format(format)
        self.events.append("get")
        if self.read_error:
            raise self.read_error
        return self.text

    def EmptyClipboard(self):
        if not self.open:
            raise RuntimeError("clipboard not open")
        self.events.append("empty")
        self.text = None

    def SetClipboardText(self, text, format):
        self.assert_format(format)
        self.events.append(("set", text))
        if self.write_error:
            error, self.write_error = self.write_error, None
            raise error
        self.text = text

    def assert_format(self, format):
        if not self.open or format != self.CF_UNICODETEXT:
            raise RuntimeError("clipboard API contract mismatch")


class ClipboardTests(unittest.TestCase):
    def test_empty_or_non_unicode_format_skips_get_and_restores_empty(self):
        for advertised in (False, 0):
            with self.subTest(advertised=advertised):
                api = FakeClipboard(advertised=advertised)
                with temporary_unicode_text("临时 command", clipboard=api):
                    self.assertEqual(api.text, "临时 command")
                    self.assertFalse(api.open)
                self.assertIsNone(api.text)
                self.assertNotIn("get", api.events)
                self.assertFalse(api.open)

    def test_unicode_and_empty_unicode_text_restore_exactly(self):
        for previous in ("原文本\nsecond line 😃", ""):
            with self.subTest(previous=previous):
                api = FakeClipboard(previous)
                with temporary_unicode_text("temporary", clipboard=api):
                    self.assertEqual(api.text, "temporary")
                    self.assertFalse(api.open)
                self.assertEqual(api.text, previous)
                self.assertFalse(api.open)

    def test_actual_code_zero_get_failure_is_absent_and_body_can_run(self):
        api = FakeClipboard(advertised=True,
            read_error=ClipboardError(0, "GetClipboardData", "No error message is available"))
        with temporary_unicode_text("allowed command", clipboard=api):
            self.assertEqual(api.text, "allowed command")
        self.assertIsNone(api.text)
        self.assertEqual(api.events.count("get"), 1)
        self.assertFalse(api.open)

    def test_other_api_errors_propagate_before_any_write(self):
        for details in ((5, "GetClipboardData", "Access denied"), (0, "OtherAPI", "unknown")):
            with self.subTest(details=details):
                failure = ClipboardError(*details)
                api = FakeClipboard("original", read_error=failure)
                with self.assertRaises(ClipboardError) as caught:
                    with temporary_unicode_text("temporary", clipboard=api):
                        self.fail("body must not run")
                self.assertIs(caught.exception, failure)
                self.assertEqual(api.text, "original")
                self.assertNotIn("empty", api.events)
                self.assertFalse(api.open)

    def test_body_failure_still_restores_previous_unicode(self):
        api = FakeClipboard("original")
        with self.assertRaisesRegex(RuntimeError, "consumer failed"):
            with temporary_unicode_text("temporary", clipboard=api):
                raise RuntimeError("consumer failed")
        self.assertEqual(api.text, "original")
        self.assertFalse(api.open)

    def test_replacement_failure_restores_previous_unicode(self):
        api = FakeClipboard("original")
        api.write_error = RuntimeError("write failed")
        with self.assertRaisesRegex(RuntimeError, "write failed"):
            with temporary_unicode_text("temporary", clipboard=api):
                self.fail("body must not run")
        self.assertEqual(api.text, "original")
        self.assertFalse(api.open)

    def test_non_text_input_fails_without_opening_clipboard(self):
        api = FakeClipboard("original")
        with self.assertRaises(TypeError):
            with temporary_unicode_text(None, clipboard=api):
                self.fail("body must not run")
        self.assertEqual(api.events, [])


if __name__ == "__main__":
    unittest.main()
