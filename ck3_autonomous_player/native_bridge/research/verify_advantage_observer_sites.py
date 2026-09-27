"""Fail-closed exact-image admission for the optional original-call observer."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pefile


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
SITES = {
    "cache_entry": (0x2308D50, "48895C24184889742420574883EC20"),
    "side_entry": (0x2307CB0, "48895C241048896C2418565741544156"),
    "commander_entry": (0x2307680, "48895C2410488974241848897C2420"),
    "aggregator_entry": (0x2307230, "48895C241048896C24184889742420"),
    "side0_cache_call": (0x2308DAF, "E8FCEEFFFF"),
    "side1_cache_call": (0x2308DC6, "E8E5EEFFFF"),
    "commander_call": (0x2307E88, "E8F3F7FFFF"),
    "aggregator_call": (0x2307EB5, "E876F3FFFF"),
}


def verify(exe: Path) -> dict[str, object]:
    data = exe.read_bytes()
    actual_sha = hashlib.sha256(data).hexdigest().upper()
    if actual_sha != EXE_SHA256:
        raise ValueError(f"ck3.exe SHA mismatch: {actual_sha}")
    image = pefile.PE(data=data, fast_load=True)
    matches = {}
    for name, (rva, expected_hex) in SITES.items():
        expected = bytes.fromhex(expected_hex)
        actual = image.get_data(rva, len(expected))
        if actual != expected:
            raise ValueError(f"{name} bytes at 0x{rva:X}: {actual.hex().upper()}")
        matches[name] = {"rva": f"0x{rva:X}", "bytes_hex": expected.hex().upper()}
    return {"game_build": "1.19.0.6", "exe_sha256": actual_sha,
            "observer_sites": matches}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.exe), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
