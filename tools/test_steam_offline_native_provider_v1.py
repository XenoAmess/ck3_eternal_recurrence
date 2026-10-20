"""Regression fixtures for the native producer-to-evidence path; no live reads."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import struct
import unittest

from steam_offline_native_provider_v1 import (
    ANCHORS, IMAGE_BYTES, IMAGE_SHA256, IMAGE_SIZE, TRAY_OFFSET, TRAY_MANAGER_RVA,
    VALUE_RVA, Module, NativeObserved, NativeUnavailable, _probe_bound, _state,
)
from steam_offline_state_contract import ProcessIdentity, SourceIdentity


STEAM = ProcessIdentity(165096, "134362593935766296",
                        str(Path("steam.exe").resolve()), "10.96.30.42")
SOURCE = SourceIdentity(str(Path("steamui.dll").resolve()), IMAGE_BYTES,
                        IMAGE_SHA256, "88664617663956600", "1788403032000000000")
BASE = 0x13A000000
MANAGER = 0x200000000


class Reader:
    def __init__(self, changed: bool = False) -> None:
        self.calls = 0
        self.changed = changed

    def identity(self, pid: int) -> ProcessIdentity:
        if pid != STEAM.pid:
            raise ValueError("unexpected pid")
        self.calls += 1
        return replace(STEAM, birth_filetime="134362593935766297") if (
            self.changed and self.calls > 1) else STEAM

    def file_version(self, path: str) -> str:
        return "10.96.30.42"


class FakeBackend:
    def __init__(self, raw: tuple[int, int] = (1, 1),
                 tray: tuple[int, int] = (4, 4), *,
                 bad_anchor: bool = False, source_change: bool = False) -> None:
        self.raw = raw
        self.tray = tray
        self.bad_anchor = bad_anchor
        self.source_change = source_change
        self.raw_index = 0
        self.tray_index = 0
        self.source_calls = 0
        self.closed = False
        self.reads: list[tuple[int, int]] = []

    def source(self, path: str) -> SourceIdentity:
        self.source_calls += 1
        return replace(SOURCE, file_id="88664617663956601") if (
            self.source_change and self.source_calls > 1) else SOURCE

    def module(self, pid: int, path: str) -> Module:
        return Module(BASE, IMAGE_SIZE, SOURCE.path)

    def open(self, pid: int) -> None:
        if pid != STEAM.pid:
            raise ValueError("unexpected pid")

    def read(self, address: int, count: int) -> bytes:
        self.reads.append((address, count))
        for rva, expected in ANCHORS:
            if address == BASE + rva and count == len(expected):
                return bytes(len(expected)) if self.bad_anchor else expected
        if address == BASE + TRAY_MANAGER_RVA and count == 8:
            return struct.pack("<Q", MANAGER)
        if address == BASE + VALUE_RVA and count == 1:
            index = self.raw_index
            self.raw_index += 1
            return bytes((self.raw[index],))
        if address == MANAGER + TRAY_OFFSET and count == 4:
            index = self.tray_index
            self.tray_index += 1
            return struct.pack("<I", self.tray[index])
        raise ValueError("unexpected/unbounded read")

    def close(self) -> None:
        self.closed = True


class NativeProviderTests(unittest.TestCase):
    def test_observed_binds_exact_producer_and_lifecycle(self) -> None:
        backend = FakeBackend()
        result = _probe_bound("fixture-machine", "fixture-nonce", STEAM, Reader(), backend)
        self.assertIsInstance(result, NativeObserved)
        if not isinstance(result, NativeObserved):
            self.fail(str(result))
        self.assertTrue(result.offline_mode)
        self.assertEqual(result.evidence.raw_samples, (1, 1))
        self.assertEqual(result.evidence.tray_state_samples, (4, 4))
        self.assertEqual(result.evidence.value_address, str(BASE + VALUE_RVA))
        self.assertEqual(result.evidence.source_before, result.evidence.source_after)
        self.assertEqual(result.evidence.steam_before, result.evidence.steam_after)
        wire = result.evidence.to_wire()
        self.assertEqual(wire["raw_samples"], [1, 1])
        self.assertEqual(wire["tray_state_samples"], [4, 4])
        self.assertTrue(backend.closed)
        self.assertEqual(len(backend.reads), 18)
        self.assertEqual(sum(count for _, count in backend.reads), 274)

    def test_native_zero_is_not_inferred_online(self) -> None:
        result = _probe_bound("fixture-machine", "nonce", STEAM, Reader(),
                              FakeBackend((0, 0), (5, 5)))
        self.assertIsInstance(result, NativeUnavailable)
        if isinstance(result, NativeUnavailable):
            self.assertEqual(result.reason, "native_online_not_qualified")

    def test_bootstrap_reset_is_unavailable(self) -> None:
        result = _probe_bound("fixture-machine", "nonce", STEAM, Reader(),
                              FakeBackend((0, 0), (1, 1)))
        self.assertIsInstance(result, NativeUnavailable)
        if isinstance(result, NativeUnavailable):
            self.assertEqual(result.reason, "native_online_not_qualified")

    def test_qualified_change_is_unavailable(self) -> None:
        result = _probe_bound("fixture-machine", "nonce", STEAM, Reader(),
                              FakeBackend((1, 1), (4, 5)))
        self.assertIsInstance(result, NativeUnavailable)
        if isinstance(result, NativeUnavailable):
            self.assertEqual(result.reason, "tray_state_unavailable")

    def test_birth_and_source_replacement_are_rejected(self) -> None:
        for reader, backend, reason in (
            (Reader(True), FakeBackend(), "steam_instance_changed"),
            (Reader(), FakeBackend(source_change=True), "source_not_qualified"),
        ):
            result = _probe_bound("fixture-machine", "nonce", STEAM, reader, backend)
            self.assertIsInstance(result, NativeUnavailable)
            if isinstance(result, NativeUnavailable):
                self.assertEqual(result.reason, reason)
            self.assertTrue(backend.closed)

    def test_anchor_mismatch_prevents_any_data_read(self) -> None:
        backend = FakeBackend(bad_anchor=True)
        result = _probe_bound("fixture-machine", "nonce", STEAM, Reader(), backend)
        self.assertIsInstance(result, NativeUnavailable)
        if isinstance(result, NativeUnavailable):
            self.assertEqual(result.reason, "anchor_mismatch")
        self.assertEqual(backend.raw_index, 0)
        self.assertEqual(backend.tray_index, 0)

    def test_boolean_float_and_invalid_mode_are_rejected(self) -> None:
        # object boundary uses callable to exercise validation without false typing.
        for raw, tray in ((True, 4), (1.0, 4), (1, True), (2, 4), (0, 4)):
            with self.assertRaises(ValueError):
                self._untyped_state(raw, tray)

    @staticmethod
    def _untyped_state(raw: object, tray: object) -> bool:
        # Runtime exact validators precede any construction of the typed sample.
        from steam_offline_state_contract import exact_int
        return _state(exact_int(raw, 0, 1), exact_int(tray, 0, 6))


if __name__ == "__main__":
    unittest.main()
