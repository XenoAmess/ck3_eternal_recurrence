"""Pin stored active-combat advantage leaves and their original read order."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pefile

from extract_active_advantage_sources import verify_component_sources


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
CONSTRUCTOR_SPAN = (0x2303CF0, 0x230402A)
# These are exact instructions, not claims that no indirect writer exists.
SITES = {
    "constructor_target_store": (0x2303D9C, "488986B8060000"),
    "constructor_flag_zero": (0x2303DEC, "66898EFD060000"),
    "constructor_target_read": (0x2303E70, "488B8EB8060000"),
    "constructor_province_predicate": (0x2303E77, "E864E68BFE"),
    "constructor_flag_write": (0x2303E7C, "8886FD060000"),
    "materialize_refresh_side0": (0x2308D66, "E8752F0C00"),
    "materialize_refresh_side1": (0x2308D72, "E8692F0C00"),
    "materialize_province_side0": (0x2308D82, "E829350C00"),
    "materialize_province_side1": (0x2308D95, "E816350C00"),
    "materialize_base_read": (0x2308D9A, "488B9EC8060000"),
    "materialize_side0_call": (0x2308DAF, "E8FCEEFFFF"),
    "materialize_side1_call": (0x2308DC6, "E8E5EEFFFF"),
    "materialize_cache_write": (0x2308DCE, "48899E10070000"),
    "selected_commander_id_read": (0x2307E2C, "458B843F94000000"),
    "selected_commander_generation_match": (0x2307E54, "44394618"),
    "selected_commander_fallback": (0x2307E5A, "488B35D7424003"),
    "commander_character_object": (0x2307E7A, "4C8BC6"),
    "commander_martial_read": (0x23076B8, "496390D8000000"),
    "commander_martial_scale": (0x23076BF, "4869FAA0860100"),
    "commander_modifier_set_call": (0x23077E2, "E8D9FA3000"),
    "commander_nested_aggregator_call": (0x23079FE, "E82DF8FFFF"),
    "primary_side_aggregator_call": (0x2307EB5, "E876F3FFFF"),
    "aggregator_combat_flag_read": (0x23074C9, "4180BFFD06000000"),
}
CALL_TARGETS = {
    "constructor_province_predicate": 0xBC24E0,
    "materialize_refresh_side0": 0x23CBCE0,
    "materialize_refresh_side1": 0x23CBCE0,
    "materialize_province_side0": 0x23CC2B0,
    "materialize_province_side1": 0x23CC2B0,
    "materialize_side0_call": 0x2307CB0,
    "materialize_side1_call": 0x2307CB0,
    "commander_modifier_set_call": 0x26172C0,
    "commander_nested_aggregator_call": 0x2307230,
    "primary_side_aggregator_call": 0x2307230,
}


def verify_image(image: pefile.PE) -> dict[str, object]:
    source = verify_component_sources(image)
    if not source["cache_chain_verified_on_same_image"]:
        raise ValueError("advantage cache source chain differs")
    # verify_component_sources has already loaded .pdata from this image.
    owners = [(int(row.struct.BeginAddress), int(row.struct.EndAddress))
              for row in image.DIRECTORY_ENTRY_EXCEPTION
              if int(row.struct.BeginAddress) <= CONSTRUCTOR_SPAN[0]
              < int(row.struct.EndAddress)]
    if owners != [CONSTRUCTOR_SPAN]:
        raise ValueError(f"combat constructor owner differs: {owners}")
    anchors = {}
    for name, (rva, expected_hex) in SITES.items():
        expected = bytes.fromhex(expected_hex)
        actual = image.get_data(rva, len(expected))
        if actual != expected:
            raise ValueError(f"{name} differs at 0x{rva:X}")
        anchors[name] = {"rva": f"0x{rva:X}", "bytes_hex": expected_hex}
        if name in CALL_TARGETS:
            if actual[0] != 0xE8 or (
                rva + 5 + int.from_bytes(actual[1:5], "little", signed=True)
                != CALL_TARGETS[name]
            ):
                raise ValueError(f"{name} call target differs")
    if not (
        0x2303D9C < 0x2303DEC < 0x2303E70 < 0x2303E77 < 0x2303E7C
        and 0x2308D66 < 0x2308D72 < 0x2308D82 < 0x2308D95
        < 0x2308D9A < 0x2308DAF < 0x2308DC6 < 0x2308DCE
        and 0x2307E2C < 0x2307E54 < 0x2307E5A < 0x2307E7A
        < 0x2307EB5
        and 0x23076B8 < 0x23076BF < 0x23077E2 < 0x23079FE
    ):
        raise ValueError("original input/order anchors differ")
    return {
        "schema": "ck3.native_active_advantage_pause_leaves.v1",
        "game_build": "1.19.0.6",
        "exe_sha256": EXE_SHA256,
        "constructor_span": [f"0x{x:X}" for x in CONSTRUCTOR_SPAN],
        "anchors": anchors,
        "proof_layer": "exact-build-instructions-call-targets-and-pdata",
    }


def verify_exe(exe: Path) -> dict[str, object]:
    raw = exe.read_bytes()
    sha = hashlib.sha256(raw).hexdigest().upper()
    if sha != EXE_SHA256:
        raise ValueError(f"ck3.exe SHA mismatch: {sha}")
    return verify_image(pefile.PE(data=raw, fast_load=True))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--expected", type=Path)
    parser.add_argument("--output", type=Path,
                        help="exclusively create a new exact-build fixture")
    args = parser.parse_args()
    result = verify_exe(args.exe)
    if args.expected is not None:
        expected = json.loads(args.expected.read_text(encoding="utf-8"))
        if result != expected:
            raise ValueError("pause leaf fixture differs from exact EXE")
    body = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output is None:
        print(body, end="")
    else:
        with args.output.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
