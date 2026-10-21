"""Typed synthetic background observations for public-runtime tests only.

All identities and observations here are fixtures. Only OS identity/source
readers are substituted; receipt decoding, profile selection, freshness and
pre-Popen receipt checks stay in the real production gate. Nothing observes
Steam, manipulates the desktop, or admits a real game.
"""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from unittest.mock import patch

from ck3_mod_acceptance_steam_gate import OfflineAdmission, validate_receipt
from steam_offline_native_profiles import NativeOfflineProfile, PROFILE_1112
from steam_offline_state_contract import (
    NativeEvidence, ProbeResult, ProcessIdentity, SourceIdentity, parse_result,
)


@dataclass(frozen=True)
class FixtureIdentityReader:
    steam: ProcessIdentity

    def identity(self, pid: int) -> ProcessIdentity:
        if type(pid) is not int or pid != self.steam.pid:
            raise ValueError("fixture reader refuses another Steam PID")
        return self.steam


def _write_result(path: Path, result: ProbeResult) -> Path:
    wire = result.to_wire()
    if parse_result(wire) != result:
        raise AssertionError("shared observation roundtrip differs")
    raw = json.dumps(wire, ensure_ascii=False, sort_keys=True, allow_nan=False).encode("utf-8")
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    if path.read_bytes() != raw:
        raise AssertionError("fixture receipt readback differs")
    return path


def write_unavailable_receipt_fixture(root: Path, *, machine_id: str) -> Path:
    """Path-forwarding fixture; unavailable has no offline_mode boolean."""
    result = ProbeResult(machine_id, datetime.now(timezone.utc).isoformat(),
        "0" * 32, "unavailable", "source_not_qualified", None, None, None,
        ("fixture_no_actual_Steam_read",))
    return _write_result(root / "steam-unavailable-fixture.json", result)


@dataclass(frozen=True)
class BackgroundSteamFixtureV1:
    result: ProbeResult
    steam: ProcessIdentity
    source: SourceIdentity
    receipt_path: Path
    reader: FixtureIdentityReader

    def write_receipt(self) -> Path:
        return _write_result(self.receipt_path, self.result)

    def qualified_source(self, path: str) -> SourceIdentity:
        if Path(path).resolve() != Path(self.source.path).resolve():
            raise ValueError("fixture refuses another source path")
        return self.source

    @contextmanager
    def os_boundaries(self) -> Iterator[None]:
        with patch("steam_offline_state_probe.WindowsReader", return_value=self.reader), \
             patch("ck3_mod_acceptance_steam_gate._qualified_source",
                   side_effect=self.qualified_source):
            yield

    def admission(self) -> OfflineAdmission:
        with self.os_boundaries():
            return validate_receipt(self.receipt_path, machine_id=self.result.machine_id,
                                    reader=self.reader)


def make_background_fixture(
    root: Path, *, machine_id: str = "synthetic-background-fixture",
    now: datetime | None = None, profile: NativeOfflineProfile = PROFILE_1112,
) -> BackgroundSteamFixtureV1:
    """Build one full typed synthetic native observation without OS reads."""
    stamp = (now or datetime.now(timezone.utc)).isoformat()
    nonce = "a" * 32
    steam = ProcessIdentity(12001, "134000000000000001",
                            str((root / "steam.exe").resolve()), profile.steam_version)
    source = SourceIdentity(str((root / "steamui.dll").resolve()), profile.image_bytes,
                            profile.image_sha256, "1", "2")
    base, manager = 0x180000000, 0x200000000
    evidence = NativeEvidence(
        machine_id, stamp, nonce, str(base), profile.image_size,
        str(profile.value_rva), str(base + profile.value_rva),
        str(profile.producer_rva), profile.producer.hex(),
        hashlib.sha256(profile.producer).hexdigest(), (1, 1),
        steam, steam, source, source, str(profile.tray_manager_rva),
        str(manager), str(profile.tray_offset), (4, 4),
    )
    result = ProbeResult(machine_id, stamp, nonce, "offline", "observed",
        steam, source, None, ("fixture_no_actual_Steam_read",),
        "native_current_user_byte", evidence)
    if parse_result(result.to_wire()) != result:
        raise AssertionError("synthetic native model is not a valid shared wire")
    return BackgroundSteamFixtureV1(result, steam, source,
        root / "steam-offline-fixture.json", FixtureIdentityReader(steam))
