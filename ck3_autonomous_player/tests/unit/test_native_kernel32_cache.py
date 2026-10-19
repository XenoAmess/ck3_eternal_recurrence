"""Only DLL/function bindings are cached; transport calls remain independent."""
from pathlib import Path
import ctypes
from ctypes import wintypes
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from xar_autoplayer.bridge import native_driver as driver


def kernel():
    return SimpleNamespace(**{name: Mock(name=name) for name in (
        "CreateNamedPipeW", "ConnectNamedPipe", "PeekNamedPipe", "ReadFile",
        "WriteFile", "DisconnectNamedPipe", "CancelIoEx", "CloseHandle")})


class Kernel32CacheTests(unittest.TestCase):
    def setUp(self):
        driver._kernel32.cache_clear()
        self.addCleanup(driver._kernel32.cache_clear)

    def test_repeated_lookup_initializes_once_and_preserves_every_binding(self):
        api = kernel()
        with patch.object(driver.ctypes, "WinDLL", return_value=api, create=True) as load:
            self.assertIs(driver._kernel32(), api)
            self.assertIs(driver._kernel32(), api)
        load.assert_called_once_with("kernel32", use_last_error=True)
        expected = {
            "CreateNamedPipeW": ([wintypes.LPCWSTR, *([wintypes.DWORD] * 6), wintypes.LPVOID], wintypes.HANDLE),
            "ConnectNamedPipe": ([wintypes.HANDLE, wintypes.LPVOID], wintypes.BOOL),
            "PeekNamedPipe": ([wintypes.HANDLE, wintypes.LPVOID, wintypes.DWORD,
                               wintypes.LPVOID, ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID], wintypes.BOOL),
            "ReadFile": ([wintypes.HANDLE, wintypes.LPVOID, wintypes.DWORD,
                          ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID], wintypes.BOOL),
            "WriteFile": ([wintypes.HANDLE, wintypes.LPVOID, wintypes.DWORD,
                           ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID], wintypes.BOOL),
            "DisconnectNamedPipe": ([wintypes.HANDLE], wintypes.BOOL),
            "CancelIoEx": ([wintypes.HANDLE, wintypes.LPVOID], wintypes.BOOL),
            "CloseHandle": ([wintypes.HANDLE], wintypes.BOOL),
        }
        for name, (args, result) in expected.items():
            function = getattr(api, name)
            self.assertEqual(function.argtypes, args, name)
            self.assertIs(function.restype, result, name)
            function.assert_not_called()

    def test_failed_initialization_is_retried_then_cached(self):
        api = kernel()
        with patch.object(driver.ctypes, "WinDLL", side_effect=[OSError("offline fixture"), api], create=True) as load:
            with self.assertRaisesRegex(OSError, "offline fixture"):
                driver._kernel32()
            self.assertEqual(driver._kernel32.cache_info().currsize, 0)
            self.assertIs(driver._kernel32(), api)
            self.assertIs(driver._kernel32(), api)
        self.assertEqual(load.call_count, 2)

    def test_cache_clear_keeps_separate_mock_scopes_isolated(self):
        first, second = kernel(), kernel()
        with patch.object(driver.ctypes, "WinDLL", return_value=first, create=True):
            self.assertIs(driver._kernel32(), first)
        driver._kernel32.cache_clear()
        with patch.object(driver.ctypes, "WinDLL", return_value=second, create=True) as load:
            self.assertIs(driver._kernel32(), second)
        load.assert_called_once()

    def test_cached_bindings_do_not_cache_read_write_results_or_last_error(self):
        api = kernel()
        payloads = iter((b"abc", b"def"))
        availability = iter((3, 7))

        def peek(handle, target, size, copied, available, remaining):
            available._obj.value = next(availability)
            return True

        def read(handle, target, size, count, overlapped):
            payload = next(payloads)
            ctypes.memmove(target, payload, len(payload))
            count._obj.value = len(payload)
            return True

        sent = []
        def write(handle, source, size, count, overlapped):
            sent.append((handle, ctypes.string_at(source, size)))
            count._obj.value = size
            return True

        api.PeekNamedPipe.side_effect = peek
        api.ReadFile.side_effect = read
        api.WriteFile.side_effect = write
        api.ConnectNamedPipe.return_value = False
        with (
            patch.object(driver.ctypes, "WinDLL", return_value=api, create=True) as load,
            patch.object(driver.ctypes, "set_last_error", create=True) as reset,
            patch.object(driver.ctypes, "get_last_error", side_effect=[536, 232], create=True) as error,
        ):
            self.assertEqual([driver._peek_available(42), driver._peek_available(42)], [3, 7])
            self.assertEqual([driver._read_exact(42, 3), driver._read_exact(42, 3)], [b"abc", b"def"])
            self.assertTrue(driver._write_all(42, b"one"))
            self.assertTrue(driver._write_all(43, b"two"))
            self.assertEqual(driver._connect_named_pipe(42), (False, 536))
            self.assertEqual(driver._connect_named_pipe(43), (False, 232))
        load.assert_called_once()
        self.assertEqual(sent, [(42, b"one"), (43, b"two")])
        self.assertEqual(api.ReadFile.call_count, 2)
        self.assertEqual(api.ConnectNamedPipe.call_count, 2)
        self.assertEqual(reset.call_count, 2)
        self.assertEqual(error.call_count, 2)


if __name__ == "__main__":
    unittest.main()
