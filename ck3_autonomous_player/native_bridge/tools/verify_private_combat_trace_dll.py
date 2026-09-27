"""Offline prelaunch gate for a private combat trace DLL and its CMake cache."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


OPTION = "XAR_CK3_ENABLE_EXPERIMENTAL_COMBAT_PHASE_TRACE_MANAGED_V1"
MARKERS = (
    b"experimental-combat-phase-event-trace-begin-v1",
    b"experimental-combat-phase-event-trace-finish-v1",
    b"capture_runtime_counter_output",
    b"capture_runtime_advantage_components",
    b"native_cache_0x2308d50_original_calls",
)


def verify(dll: Path, cache: Path) -> dict[str, object]:
    data = dll.read_bytes()
    cache_text = cache.read_text(encoding="utf-8")
    enabled = f"{OPTION}:BOOL=ON" in cache_text.splitlines()
    present = {marker.decode("ascii"): marker in data for marker in MARKERS}
    result = {
        "dll_path": str(dll.resolve()),
        "dll_sha256": hashlib.sha256(data).hexdigest().upper(),
        "cmake_cache_path": str(cache.resolve()),
        "private_trace_option_on": enabled,
        "required_strings": present,
        "ready": data.startswith(b"MZ") and enabled and all(present.values()),
    }
    if not result["ready"]:
        raise ValueError(json.dumps(result, sort_keys=True))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dll", type=Path, required=True)
    parser.add_argument("--cmake-cache", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.dll, args.cmake_cache), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
