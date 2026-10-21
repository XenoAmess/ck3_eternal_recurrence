"""Verify the small Native32 source candidate; never compile or call the Game."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / "native31_passive_journal_20261020"
SOURCE_NAMES = (
    "native/include/xar_bridge/native_time_command_observer_12004.hpp",
    "native/src/native_time_command_observer_12004.cpp",
    "native/tests/native32_core_fixture.cpp",
    "cold/observer_journal_v1.py", "cold/test_observer_journal_v1.py",
    "cold/qualify_host_fixture.py", "README.md", "verify.py",
)
BASE_PINS = (
    ("native/include/xar_bridge/native_time_command_observer_12004.hpp", 4176,
     "f0beb8ff286bcda8854fcfe74529ae47943f67db206b8b7855d1081ec8254e11"),
    ("native/src/native_time_command_observer_12004.cpp", 14322,
     "a0973832477b55bda0bc6917854fd5ec595209ab8b356f2bb07a5bd35aaaad7a"),
    ("native/src/native_time_command_observer_12004_install.cpp", 9790,
     "95888a0ca45293704dedc8915edf817c5dabb12af42c93b4f536f080994ed545"),
)


def _obj(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("JSON object required")
    result: dict[str, object] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("text key required")
        result[key] = item
    return result


def verify_source_v1(root: Path = ROOT, baseline: Path = BASE) -> int:
    raw: object = json.loads((root / "MANIFEST.json").read_bytes())
    manifest = _obj(raw)
    if (manifest.get("schema") != "xar.native32.passive-journal-source-candidate/v1"
            or manifest.get("runtime_admission_granted") is not False
            or manifest.get("production_dll_sha256") is not None
            or manifest.get("abi_qualified") is not False
            or type(manifest.get("machine_id")) is not str
            or not manifest["machine_id"]):
        raise ValueError("source-only qualification boundary differs")
    pins = manifest.get("source_files")
    if not isinstance(pins, list) or len(pins) != len(SOURCE_NAMES):
        raise ValueError("exact candidate pin set required")
    seen: set[str] = set()
    for pin in pins:
        row = _obj(pin)
        if set(row) != {"name", "bytes", "sha256"}:
            raise ValueError("exact pin fields required")
        name, size, digest = row["name"], row["bytes"], row["sha256"]
        if (type(name) is not str or name not in SOURCE_NAMES or name in seen
                or type(size) is not int or size < 1 or type(digest) is not str
                or len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest)):
            raise ValueError("canonical source pin required")
        path = (root / name).resolve(strict=True)
        if root.resolve(strict=True) not in path.parents:
            raise ValueError("candidate source escaped root")
        data = path.read_bytes()
        if len(data) != size or hashlib.sha256(data).hexdigest() != digest:
            raise ValueError("candidate source bytes differ")
        seen.add(name)
    if seen != set(SOURCE_NAMES):
        raise ValueError("missing candidate source pin")
    for name, size, digest in BASE_PINS:
        data = (baseline / name).read_bytes()
        if len(data) != size or hashlib.sha256(data).hexdigest() != digest:
            raise ValueError("frozen Native31 source changed")
    return len(seen)


def main() -> int:
    print("SOURCE_LEAVES_VERIFIED", verify_source_v1())
    print("runtime_admission_granted=false Game_calls=0 build_calls=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
