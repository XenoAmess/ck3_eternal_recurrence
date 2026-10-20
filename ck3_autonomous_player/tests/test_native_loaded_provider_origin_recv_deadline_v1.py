"""Whole-receive deadline regressions; fake transport never calls Win32."""
from __future__ import annotations

import ctypes
from ctypes import wintypes as w
import unittest
from unittest.mock import patch

from xar_autoplayer.bridge import native_loaded_provider_origin_io_v1 as originio


class FakeClockV1:
    def __init__(self) -> None:
        self.now = 0.0

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


def _count_v1(pointer: object, value: int) -> None:
    target: object = getattr(pointer, "_obj", None)
    if not isinstance(target, w.DWORD):
        raise AssertionError("actual DWORD byref required")
    target.value = value


class FakeAPIV1:
    def _ok(self, value: object, reason: str) -> None:
        if value is not True:
            raise OSError(reason)


class FakeReceiverV1:
    def __init__(self, chunks: list[bytes], *, peek_seconds: float = 0.0,
                 read_seconds: float = 0.0, read_limit: int | None = None) -> None:
        self.clock = FakeClockV1()
        self.timeout = 10.0
        self.startup_timeout = 30.0
        self.rx: dict[int, bytes] = {}
        self.api = FakeAPIV1()
        self.chunks = list(chunks)
        self.pending = b""
        self.peek_seconds, self.read_seconds = peek_seconds, read_seconds
        self.read_limit = read_limit
        self.peeks, self.reads = 0, 0

    def _peek(self, handle: int, buffer: object, count: int, read: object,
              available: object, left: object) -> bool:
        self.peeks += 1
        self.clock.now += self.peek_seconds
        if not self.pending and self.chunks:
            self.pending = self.chunks.pop(0)
        _count_v1(available, len(self.pending))
        return True

    def _read(self, handle: int, buffer: object, count: int,
              read: object, overlapped: object) -> bool:
        self.reads += 1
        self.clock.now += self.read_seconds
        size = min(count, len(self.pending))
        if self.read_limit is not None:
            size = min(size, self.read_limit)
        if not isinstance(buffer, ctypes.Array) or buffer._type_ is not ctypes.c_char:
            raise AssertionError("actual ctypes byte buffer required")
        ctypes.memmove(buffer, self.pending[:size], size)
        self.pending = self.pending[size:]
        _count_v1(read, size)
        return True

    def receive(self, handle: int = 123, *, startup: bool = False) -> dict[str, object]:
        with patch.object(originio.time, "monotonic", self.clock.monotonic), patch.object(
                originio.time, "sleep", self.clock.sleep):
            value: object = originio.OriginKernelIOV1.recv(self, handle, startup=startup)
        if not isinstance(value, dict):
            raise AssertionError("actual recv must return a JSON object")
        result: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise AssertionError("actual JSON key must be text")
            result[key] = item
        return result


class OriginReceiveDeadlineV1Tests(unittest.TestCase):
    def test_continuous_data_cannot_exceed_whole_deadline(self) -> None:
        receiver = FakeReceiverV1([b"{", b'"ok":', b"true}\n"], peek_seconds=6.0)
        with self.assertRaises(TimeoutError):
            receiver.receive()
        self.assertLessEqual(receiver.peeks, 2)
        self.assertEqual(receiver.rx, {})

    def test_final_read_crossing_deadline_is_rejected(self) -> None:
        receiver = FakeReceiverV1([b'{"ok":true}\n'], read_seconds=11.0)
        with self.assertRaises(TimeoutError):
            receiver.receive()
        self.assertEqual(receiver.reads, 1)

    def test_exact_deadline_is_expired(self) -> None:
        receiver = FakeReceiverV1([b'{"ok":true}\n'], read_seconds=10.0)
        with self.assertRaises(TimeoutError):
            receiver.receive()

    def test_timely_data_and_json_roundtrip(self) -> None:
        receiver = FakeReceiverV1([b'{"ok":true,"items":[null,1,"x"]}\n'], peek_seconds=0.1)
        self.assertEqual(receiver.receive(), {"ok": True, "items": [None, 1, "x"]})

    def test_startup_keeps_its_explicit_budget(self) -> None:
        receiver = FakeReceiverV1([b"{", b'"ok":', b"true}\n"], peek_seconds=6.0)
        self.assertEqual(receiver.receive(startup=True), {"ok": True})
        self.assertEqual(receiver.clock.now, 18.0)

    def test_idle_timeout(self) -> None:
        receiver = FakeReceiverV1([], peek_seconds=11.0)
        with self.assertRaises(TimeoutError):
            receiver.receive()
        self.assertEqual(receiver.peeks, 1)
        self.assertEqual(receiver.reads, 0)

    def test_sleep_does_not_restart_deadline(self) -> None:
        receiver = FakeReceiverV1([])
        with self.assertRaises(TimeoutError):
            receiver.receive()
        self.assertGreaterEqual(receiver.clock.now, 10.0)
        self.assertLess(receiver.clock.now, 10.01)

    def test_partial_reads_keep_bytes(self) -> None:
        receiver = FakeReceiverV1([b'{"value":123}\n'], peek_seconds=0.1, read_limit=3)
        self.assertEqual(receiver.receive(), {"value": 123})
        self.assertGreater(receiver.reads, 1)

    def test_partial_message_timeout(self) -> None:
        receiver = FakeReceiverV1([b'{"value":'], peek_seconds=6.0)
        with self.assertRaises(TimeoutError):
            receiver.receive()
        self.assertEqual(receiver.reads, 1)

    def test_tail_is_retained_without_extra_transport(self) -> None:
        receiver = FakeReceiverV1([b'{"a":1}\n{"b":2}\n'])
        self.assertEqual(receiver.receive(), {"a": 1})
        before = (receiver.peeks, receiver.reads)
        self.assertEqual(receiver.receive(), {"b": 2})
        self.assertEqual((receiver.peeks, receiver.reads), before)
        self.assertEqual(receiver.rx[123], b"")

    def test_exact_byte_cap_stays_valid(self) -> None:
        raw = b'{"x":"' + b"a" * (16384 - len(b'{"x":""}\n')) + b'"}\n'
        self.assertEqual(len(raw), 16384)
        receiver = FakeReceiverV1([raw])
        self.assertEqual(receiver.receive(), {"x": "a" * (16384 - len(b'{"x":""}\n'))})

    def test_byte_cap_is_enforced_before_read(self) -> None:
        receiver = FakeReceiverV1([b"x" * 16385])
        with self.assertRaisesRegex(ValueError, "exceeds bound"):
            receiver.receive()
        self.assertEqual(receiver.reads, 0)

    def test_nonobject_json_is_rejected(self) -> None:
        for raw in (b"null\n", b"true\n", b"1\n", b"[]\n"):
            with self.subTest(raw=raw), self.assertRaisesRegex(ValueError, "object"):
                FakeReceiverV1([raw]).receive()

    def test_decode_crossing_deadline_is_rejected(self) -> None:
        receiver = FakeReceiverV1([b'{"ok":true}\n'])
        original = originio.json.loads
        def delayed_decode(value: bytes) -> object:
            result: object = original(value)
            receiver.clock.now += 11.0
            return result
        with patch.object(originio.json, "loads", delayed_decode), self.assertRaises(TimeoutError):
            receiver.receive()

    def test_startup_flag_rejects_equal_integer(self) -> None:
        # Call the public boundary dynamically to exercise a deliberately wrong type.
        method: object = getattr(FakeReceiverV1([b"{}\n"]), "receive")
        self.assertTrue(callable(method))
        if callable(method):
            with self.assertRaisesRegex(ValueError, "startup"):
                method(startup=1)

    def test_handle_rejects_wrong_integer_domain(self) -> None:
        for handle in (True, 1.0, 0, -1):
            method: object = getattr(FakeReceiverV1([b"{}\n"]), "receive")
            if not callable(method):
                raise AssertionError("bound receive required")
            with self.subTest(handle=handle), self.assertRaisesRegex(ValueError, "handle"):
                method(handle)


if __name__ == "__main__":
    unittest.main()
