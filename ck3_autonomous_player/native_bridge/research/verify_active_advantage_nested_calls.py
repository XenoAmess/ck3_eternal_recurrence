"""Pin the two direct 0x2307230 aggregator call sites on CK3 1.19.0.6."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pefile

from extract_active_advantage_sources import verify_component_sources


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
SITES = {
    "commander_nested_call": (0x23079FE, "E82DF8FFFF"),
    "commander_nested_return": (0x2307A03, "488B08"),
    "commander_nested_add": (0x2307A06, "48010E"),
    "side_primary_call": (0x2307EB5, "E876F3FFFF"),
    "side_primary_return": (0x2307EBA, "488B08"),
    "side_primary_add": (0x2307EBD, "49010C24"),
}


def verify_exe(exe: Path) -> dict[str, object]:
    raw = exe.read_bytes()
    actual_sha = hashlib.sha256(raw).hexdigest().upper()
    if actual_sha != EXE_SHA256:
        raise ValueError(f"ck3.exe SHA mismatch: {actual_sha}")
    image = pefile.PE(data=raw, fast_load=True)
    proof = verify_component_sources(image)
    spans = proof["function_spans"]
    commander = spans["commander"]
    side = spans["side_total"]
    if not (int(commander["begin_rva"], 16) <= 0x23079FE <
            int(commander["end_rva_exclusive"], 16)
            and int(side["begin_rva"], 16) <= 0x2307EB5 <
            int(side["end_rva_exclusive"], 16)):
        raise ValueError("nested/primary call owners differ")
    anchors = {}
    for name, (rva, expected_hex) in SITES.items():
        expected = bytes.fromhex(expected_hex)
        actual = image.get_data(rva, len(expected))
        if actual != expected:
            raise ValueError(f"{name} differs at 0x{rva:X}")
        anchors[name] = {"rva": f"0x{rva:X}", "bytes_hex": expected_hex}
    for call_rva in (0x23079FE, 0x2307EB5):
        code = image.get_data(call_rva, 5)
        target = call_rva + 5 + int.from_bytes(code[1:], "little", signed=True)
        if code[0] != 0xE8 or target != 0x2307230:
            raise ValueError("aggregator direct-call target differs")
    direct_callers = set()
    for section in image.sections:
        if not section.Characteristics & 0x20000000:
            continue
        start = int(section.VirtualAddress)
        code = section.get_data()
        for index in range(len(code) - 4):
            if code[index] == 0xE8 and (
                start + index + 5 +
                int.from_bytes(code[index + 1:index + 5], "little", signed=True)
                == 0x2307230
            ):
                direct_callers.add(start + index)
    if direct_callers != {0x23079FE, 0x2307EB5}:
        raise ValueError(f"aggregator direct callers differ: {direct_callers}")
    return {"game_build": "1.19.0.6", "exe_sha256": actual_sha,
            "nested_call_owner": "commander", "primary_call_owner": "side_total",
            "common_target_rva": "0x2307230",
            "direct_caller_rvas": ["0x23079FE", "0x2307EB5"],
            "anchors": anchors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify_exe(args.exe), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
