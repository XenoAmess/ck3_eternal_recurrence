"""Test-only materialization of an inert, immutable historical launcher source."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path


@dataclass(frozen=True)
class FrozenLauncherFixtureV1:
    bytes: int
    sha256: str


LEGACY_LAUNCHER_V1 = FrozenLauncherFixtureV1(
    17792, "7d3c30118fb92401a744b6bc784f6c35ba52fa855c5e9eb657bb86dc052b180b",
)


def legacy_launcher_source_v1() -> bytes:
    source = Path(__file__).resolve().parent / "fixtures" / (
        "ck3_mod_acceptance_supervisor_refusal/launcher-pre-background-v1.py.bin"
    )
    raw = source.read_bytes()
    if len(raw) != LEGACY_LAUNCHER_V1.bytes or hashlib.sha256(raw).hexdigest() != LEGACY_LAUNCHER_V1.sha256:
        raise ValueError("historical launcher fixture bytes changed")
    return raw


def materialize_legacy_launcher_fixture_v1(directory: Path) -> Path:
    """Copy exact bytes for pin checks; never import or execute this source."""
    raw = legacy_launcher_source_v1()
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / "ck3_mod_acceptance_launcher.py"
    with target.open("xb") as stream:
        stream.write(raw)
    return target
