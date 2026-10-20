"""Native launch guard wire, freshness and process-generation regressions."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from typing import Callable

from steam_offline_state_contract import NativeEvidence, ProbeResult, ProcessIdentity, SourceIdentity
from steam_offline_native_provider_v1 import (
    IMAGE_BYTES, IMAGE_SHA256, IMAGE_SIZE, PRODUCER, PRODUCER_RVA, STEAM_VERSION,
    TRAY_MANAGER_RVA, TRAY_OFFSET, VALUE_RVA,
)
from steam_native_launch_guard_v1 import (
    CurrentSteamGeneration, CurrentSteamSourceStat,
    require_steam_native_launch_v1, validate_steam_native_launch_document,
    steam_native_current_generation, steam_native_require_running,
)

NOW = datetime(2026, 10, 20, 17, 0, tzinfo=timezone.utc)


def fixture() -> ProbeResult:
    steam = ProcessIdentity(42, "134362593935766296", "C:/Steam/steam.exe", STEAM_VERSION)
    source = SourceIdentity("C:/Steam/SteamUI.dll", IMAGE_BYTES, IMAGE_SHA256,
                            "88664617663956600", "1788403032000000000")
    base = 140734276698112
    evidence = NativeEvidence(
        "fixture-machine", NOW.isoformat(), "f" * 32, str(base), IMAGE_SIZE,
        str(VALUE_RVA), str(base + VALUE_RVA), str(PRODUCER_RVA), PRODUCER.hex(),
        hashlib.sha256(PRODUCER).hexdigest(), (1, 1), steam, steam, source, source,
        str(TRAY_MANAGER_RVA), "2678335344384", str(TRAY_OFFSET), (4, 4),
    )
    return ProbeResult("fixture-machine", NOW.isoformat(), "f" * 32, "offline",
                       "observed", steam, source, None, (),
                       "native_current_user_byte", evidence)


def validate(value: object, *, at: datetime = NOW,
             generation: CurrentSteamGeneration | None = None,
             source_stat: CurrentSteamSourceStat | None = None) -> ProbeResult:
    return validate_steam_native_launch_document(
        value, machine_id="fixture-machine", at_utc=at,
        current_steam=generation or CurrentSteamGeneration(
            42, "134362593935766296", "C:/Steam/steam.exe"),
        current_source_stat=source_stat or CurrentSteamSourceStat(
            IMAGE_BYTES, "88664617663956600", "1788403032000000000"),
    )



class FakeCall:
    def __init__(self, name: str, action: Callable[[tuple[object, ...]], int],
                 trace: list[tuple[str, tuple[object, ...]]]) -> None:
        self.name, self.action, self.trace = name, action, trace
        self.argtypes: object = None
        self.restype: object = None

    def __call__(self, *args: object) -> int:
        self.trace.append((self.name, args))
        return self.action(args)


def fake_kernel(waits: list[int]) -> tuple[SimpleNamespace, list[tuple[str, tuple[object, ...]]]]:
    trace: list[tuple[str, tuple[object, ...]]] = []
    sequence = list(waits)
    def times(args: tuple[object, ...]) -> int:
        born = getattr(args[1], "_obj")
        setattr(born, "dwHighDateTime", 1)
        setattr(born, "dwLowDateTime", 2)
        return 1
    def image(args: tuple[object, ...]) -> int:
        setattr(args[2], "value", "fixture-steam.exe")
        return 1
    result = SimpleNamespace(
        OpenProcess=FakeCall("open", lambda _: 17, trace),
        GetProcessTimes=FakeCall("times", times, trace),
        QueryFullProcessImageNameW=FakeCall("image", image, trace),
        WaitForSingleObject=FakeCall("wait", lambda _: sequence.pop(0), trace),
        CloseHandle=FakeCall("close", lambda _: 1, trace),
    )
    return result, trace


class SteamNativeLaunchGuardTests(unittest.TestCase):

    def test_kernel_alive_is_checked_before_and_after_generation_reads(self) -> None:
        kernel, trace = fake_kernel([258, 258])
        with patch("steam_native_launch_guard_v1.ctypes.WinDLL", return_value=kernel):
            current = steam_native_current_generation(42)
        self.assertEqual(current.birth_filetime, "4294967298")
        self.assertEqual([name for name, _ in trace],
                         ["open", "wait", "times", "image", "wait", "close"])
        self.assertEqual(trace[0][1], (0x00101000, False, 42))
        self.assertEqual([args for name, args in trace if name == "wait"],
                         [(17, 0), (17, 0)])

    def test_kernel_exit_unknown_and_exit_during_query_are_rejected(self) -> None:
        for waits in ([0], [0xFFFFFFFF], [258, 0], [258, 0xFFFFFFFF]):
            kernel, trace = fake_kernel(waits)
            with self.subTest(waits=waits), patch(
                "steam_native_launch_guard_v1.ctypes.WinDLL", return_value=kernel,
            ), self.assertRaises(ValueError):
                steam_native_current_generation(42)
            self.assertEqual(trace[-1][0], "close")
        for wrong in (True, 258.0, 259, None):
            with self.subTest(wrong=wrong), self.assertRaises(ValueError):
                steam_native_require_running(wrong)

    def test_current_native_offline_wire_is_accepted(self) -> None:
        proof = fixture()
        self.assertEqual(validate(json.loads(json.dumps(proof.to_wire()))), proof)

    def test_freshness_uses_observation_not_file_timestamp(self) -> None:
        wire = fixture().to_wire()
        self.assertEqual(validate(wire, at=NOW + timedelta(seconds=600)), fixture())
        for at in (NOW + timedelta(seconds=601), NOW - timedelta(seconds=11),
                   NOW.replace(tzinfo=None)):
            with self.subTest(at=at), self.assertRaises(ValueError):
                validate(wire, at=at)

    def test_other_machine_and_wrong_provider_are_rejected(self) -> None:
        for key, value in (("machine_id", "other-machine"),
                           ("observation_method", "cef_app_getters"),
                           ("status", "online"), ("status", "unavailable")):
            wire = json.loads(json.dumps(fixture().to_wire()))
            wire[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                validate(wire)

    def test_reused_pid_wrong_image_and_lossy_birth_are_rejected(self) -> None:
        wrong = (
            CurrentSteamGeneration(42, "134362593935766297", "C:/Steam/steam.exe"),
            CurrentSteamGeneration(42, "134362593935766296", "C:/Other/steam.exe"),
            CurrentSteamGeneration(True, "134362593935766296", "C:/Steam/steam.exe"),
        )
        for generation in wrong:
            with self.subTest(generation=generation), self.assertRaises(ValueError):
                validate(fixture().to_wire(), generation=generation)

    def test_source_replacement_is_not_accepted_as_current(self) -> None:
        for stat in (
            CurrentSteamSourceStat(IMAGE_BYTES, "88664617663956601", "1788403032000000000"),
            CurrentSteamSourceStat(IMAGE_BYTES, "88664617663956600", "1788403032000000001"),
            CurrentSteamSourceStat(IMAGE_BYTES + 1, "88664617663956600", "1788403032000000000"),
        ):
            with self.subTest(stat=stat), self.assertRaises(ValueError):
                validate(fixture().to_wire(), source_stat=stat)

    def test_well_formed_unknown_source_registry_is_rejected(self) -> None:
        old = fixture()
        if old.source is None or old.native_evidence is None:
            self.fail("fixture requires native source")
        source = replace(old.source, sha256="a" * 64)
        evidence = replace(old.native_evidence, source_before=source, source_after=source)
        with self.assertRaises(ValueError):
            validate(replace(old, source=source, native_evidence=evidence).to_wire())

    def test_missing_wrong_types_and_native_zero_never_authorize(self) -> None:
        for mutation in ("bool_pid", "float_pid", "numeric_birth", "native_zero",
                         "tray_voice", "missing_evidence"):
            wire = json.loads(json.dumps(fixture().to_wire()))
            if mutation == "bool_pid": wire["steam"]["pid"] = True
            elif mutation == "float_pid": wire["steam"]["pid"] = 42.0
            elif mutation == "numeric_birth": wire["steam"]["birth_filetime"] = 134362593935766296
            elif mutation == "native_zero": wire["native_evidence"]["raw_samples"] = [0, 0]
            elif mutation == "tray_voice": wire["native_evidence"]["tray_state_samples"] = [5, 5]
            else: del wire["native_evidence"]
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                validate(wire)

    def test_bound_and_explicit_timezone_are_strict(self) -> None:
        for bound in (True, 0, 601):
            with self.subTest(bound=bound), self.assertRaises(ValueError):
                validate_steam_native_launch_document(
                    fixture().to_wire(), machine_id="fixture-machine", at_utc=NOW,
                    current_steam=CurrentSteamGeneration(42, "134362593935766296", "C:/Steam/steam.exe"),
                    current_source_stat=CurrentSteamSourceStat(
                        IMAGE_BYTES, "88664617663956600", "1788403032000000000"),
                    max_age_seconds=bound,
                )

    def test_exact_reference_load_has_no_screen_and_no_cached_result(self) -> None:
        data = json.dumps(fixture().to_wire()).encode()
        path = Path("fixture-native-state.json")
        reference = {"path": str(path), "bytes": len(data),
                     "sha256": hashlib.sha256(data).hexdigest()}
        receipt_stat = SimpleNamespace(st_size=len(data), st_ino=17, st_mtime_ns=19)
        source_stat = SimpleNamespace(st_size=IMAGE_BYTES, st_ino=88664617663956600,
                                      st_mtime_ns=1788403032000000000)
        def stat_for(actual: Path) -> SimpleNamespace:
            return source_stat if actual.name.lower() == "steamui.dll" else receipt_stat
        with patch.object(Path, "stat", stat_for), patch.object(Path, "read_bytes", return_value=data) as reader, patch(
            "steam_native_launch_guard_v1.steam_native_current_generation",
            return_value=CurrentSteamGeneration(42, "134362593935766296", "C:/Steam/steam.exe"),
        ) as generation:
            first = require_steam_native_launch_v1(
                path, reference, machine_id="fixture-machine", at_utc=NOW)
            second = require_steam_native_launch_v1(
                path, reference, machine_id="fixture-machine", at_utc=NOW)
        self.assertEqual(first, second)
        self.assertEqual(reader.call_count, 2)
        self.assertEqual(generation.call_count, 2)


if __name__ == "__main__":
    unittest.main()
