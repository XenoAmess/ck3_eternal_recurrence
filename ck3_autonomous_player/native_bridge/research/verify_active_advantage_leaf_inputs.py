"""Hash-bound CK3 1.19.0.6 leaves feeding original advantage helpers."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pefile

from extract_active_advantage_sources import verify_component_sources


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
# Name, RVA, instruction size, exact bytes frozen from the pinned image.
SITES = (
    ("side_to_character_r8", 0x2307E7A, 3, "4C8BC6"),
    ("side_calls_commander", 0x2307E88, 5, "E8F3F7FFFF"),
    ("commander_keeps_character", 0x23076AF, 3, "4D8BF8"),
    ("commander_character_int32", 0x23076B8, 7, "496390D8000000"),
    ("commander_scales_100000", 0x23076BF, 7, "4869FAA0860100"),
    ("commander_writes_initial_qword", 0x23076C6, 3, "48893E"),
    ("side_adds_commander_return", 0x2307E90, 4, "49010C24"),
    ("side_calls_aggregator", 0x2307EB5, 5, "E876F3FFFF"),
    ("aggregator_keeps_combat", 0x230725D, 3, "4C8BF9"),
    ("aggregator_combat_flag", 0x23074C9, 8, "4180BFFD06000000"),
    ("aggregator_skips_flag_block", 0x23074D1, 6, "0F8412010000"),
    ("aggregator_adds_flag_block", 0x23075E6, 3, "480113"),
    ("side_adds_aggregator_return", 0x2307EBD, 4, "49010C24"),
)


def verify_image(image: pefile.PE) -> dict[str, object]:
    source = verify_component_sources(image)
    if not source["cache_chain_verified_on_same_image"]:
        raise ValueError("original cache chain is not closed")
    anchors = {}
    for name, rva, size, expected_hex in SITES:
        actual = image.get_data(rva, size)
        if len(actual) != size:
            raise ValueError(f"{name}: truncated instruction")
        actual_hex = actual.hex().upper()
        if actual_hex != expected_hex:
            raise ValueError(f"{name}: expected {expected_hex}, got {actual_hex}")
        anchors[name] = {"rva": f"0x{rva:X}", "bytes_hex": actual_hex}
    branch = image.get_data(0x23074D1, 6)
    if branch[:2] != b"\x0f\x84" or (
        0x23074D1 + 6 + int.from_bytes(branch[2:], "little", signed=True)
        != 0x23075E9
    ):
        raise ValueError("aggregator flag branch target differs")
    if not (
        0x2307E7A < 0x2307E88 < 0x2307E90 < 0x2307EB5 < 0x2307EBD
        and 0x23076AF < 0x23076B8 < 0x23076BF < 0x23076C6
        and 0x230725D < 0x23074C9 < 0x23074D1 < 0x23075E6 < 0x23075E9
    ):
        raise ValueError("helper call or leaf order differs")
    return {"schema": "ck3.native_active_advantage_leaf_inputs.v1",
            "game_build": "1.19.0.6", "exe_sha256": EXE_SHA256,
            "cache_chain_verified_on_same_image": True,
            "anchors": anchors,
            "aggregator_zero_flag_branch_target_rva": "0x23075E9",
            "proof_layer": "exact-build-instructions-and-control-flow"}


def verify_exe(exe: Path) -> dict[str, object]:
    raw = exe.read_bytes()
    actual_sha = hashlib.sha256(raw).hexdigest().upper()
    if actual_sha != EXE_SHA256:
        raise ValueError(f"ck3.exe SHA mismatch: {actual_sha}")
    return verify_image(pefile.PE(data=raw, fast_load=True))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--expected", type=Path)
    args = parser.parse_args()
    actual = verify_exe(args.exe)
    if args.expected is not None:
        expected = json.loads(args.expected.read_text(encoding="utf-8"))
        if actual != expected:
            raise ValueError("advantage leaf fixture differs from exact EXE")
    print(json.dumps(actual, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
