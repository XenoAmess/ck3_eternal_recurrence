"""Check the exact-build dual-type boundary for Messina MAA RegimentID 87.

The frozen v3 counter reads CRegiment+0x18, whereas the stock effective-stat
path reads CRegiment+0x118. This checker never treats the two as equal, never
reads a live process, and never infers a modifier from the final 26.25 value.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pefile


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
IDENTITY_SHA256 = "69B906918120294000C8BB821A1AEEFE43BD210FB14610E8EACC1B0CFC1BC210"
V3_SHA256 = {
    11: "50F1FE7946F846E237AAC2003B98BF540363C133AA8EE93AB69F388E2472E2BE",
    21: "A8B257EE743B593DBE145ED2D6E152DC7791C092EB0B6C95BE8943B1C23AE1E1",
}
EXE_ANCHORS = {
    0x2C8F1D6: "4C8BAA18010000",  # CRegiment+0x118 -> effective-stat type
    0x2C8D6B7: "49638070020000",  # effective-stat type+0x270 -> class index
    0x2C8D94D: "450FB7472E",      # class row+0x2E -> toughness additive enum
    0x2C8D97E: "450FB7473A",      # class row+0x3A -> toughness multiplier enum
    0x2396490: "488B0531904203",  # known CRegiment storage slot +0x57BF4C8
    0x239649C: "8B5128",          # regiment+0x28 -> another regiment ID
    0x23964D5: "448B8040010000",  # resolved regiment+0x140 -> army ID
    0x2C8F3DB: "488B5F3848634744",  # resolved army regiment array
    0x23C2EE9: "4C8D4320BA03000000",  # Stats38+0x20 is toughness slot 3
    0x23C2F39: "4A8B14C8",       # indexed modifier add component
    0x23C2F3D: "490110",          # add vector component to stat
    0x23C2F55: "4E8B54C830",     # indexed multiplier component
    0x23C2F6C: "490FAFD2",       # fixed-point multiply before /100000
    0x23C2F8B: "498913",         # store adjusted stat
    0x2C8F924: "4C8B75184D037520",  # target vector toughness addition
}
READER_ENUMS = {
    0x2C8D8E0: 0x1AC,  # MAA toughness add
    0x2C8D902: 0x1AD,  # MAA toughness multiplier
    0x2C8D92B: 0x1A7,  # army toughness multiplier
}
CALLS = {
    0x2C8F374: 0x2396490,  # regiment -> same-army context
    0x2C8F78D: 0x2C8D6A0,  # effective-stat type -> class modifier reader
    0x2C8F7B9: 0x23C2DF0,  # Q100000 additive/multiplier application
    0x2C8F8FF: 0x2C88B10,  # target-context vector
}
BRIDGE_SOURCE_ANCHORS = (
    "constexpr std::size_t kRegimentMaaTypeOffset = 0x118;",
    "constexpr std::size_t kRegimentInnerTypeOffset = 0x18;",
    "constexpr std::size_t kRegimentCounterClassOffset = 0x270;",
    "inner_type, kRegimentCounterClassOffset",
    "row.class_index = LoadAt<std::int32_t>(",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def call_target(pe: pefile.PE, site: int) -> int:
    data = pe.get_data(site, 5)
    require(len(data) == 5 and data[0] == 0xE8, f"relative call missing: {site:#x}")
    return site + 5 + int.from_bytes(data[1:], "little", signed=True)


def check_v3(path: Path, day: int) -> dict:
    require(sha256(path) == V3_SHA256[day], f"day {day} v3 SHA mismatch")
    response = json.loads(path.read_text(encoding="utf-8"))
    body = response["body"]
    require(response["result"] == "CALL_COMPLETED" and body["status"] == "available"
            and body["target_province_id"] == 2633, f"day {day} v3 scope mismatch")
    armies = body["combat_simulation_inputs"]["base_inputs"]["armies"]
    matches = [(army, regiment) for army in armies for regiment in army["regiments"]
               if regiment["regiment_id"] == 87]
    require(len(matches) == 1, f"day {day} RegimentID 87 not unique")
    army, regiment = matches[0]
    require(army["army_id"] == 16777221
            and army["owner"]["character_id"] == 31549
            and regiment["kind"]["value"] == "men_at_arms"
            and regiment["maa_type"]["status"] == "absent"
            and regiment["maa_type"]["key"] is None
            and regiment["counter"]["status"] == "available"
            and regiment["counter"]["class_index"] == 0
            and regiment["effective_stats"]["toughness_raw"] == 2625000
            and regiment["effective_stats"]["source_target_province_id"] == 2633,
            f"day {day} MAA87 type/counter/stat observation changed")
    return {"source_day": day, "v3_sha256": V3_SHA256[day],
            "regiment_id": 87, "army_id": 16777221,
            "counter_class_index_from_inner_type": 0,
            "maa_type_key_in_v3": None,
            "effective_toughness_raw": 2625000,
            "target_province_id": 2633}


def project(args: argparse.Namespace) -> dict:
    require(sha256(args.exe) == EXE_SHA256, "CK3 EXE is not the exact build")
    require(sha256(args.identity_sidecar) == IDENTITY_SHA256,
            "source-save type identity sidecar changed")
    identity = json.loads(args.identity_sidecar.read_text(encoding="utf-8"))
    require(identity["maa_type"]["key"] == "mubarizun"
            and identity["maa_type"]["native_class_key"] == "heavy_infantry"
            and identity["maa_type"]["base_toughness"] == 25
            and identity["source_save_identity_only"] is True,
            "source-save type identity changed")
    bridge_text = args.bridge_source.read_text(encoding="utf-8")
    for anchor in BRIDGE_SOURCE_ANCHORS:
        require(anchor in bridge_text, f"bridge source anchor missing: {anchor}")
    pe = pefile.PE(data=args.exe.read_bytes(), fast_load=True)
    for site, hex_bytes in EXE_ANCHORS.items():
        expected = bytes.fromhex(hex_bytes)
        require(pe.get_data(site, len(expected)) == expected,
                f"EXE operand changed: {site:#x}")
    for site, native_enum in READER_ENUMS.items():
        require(pe.get_data(site, 6) == b"\x41\xb8" + native_enum.to_bytes(4, "little"),
                f"toughness enum changed: {site:#x}")
    for site, expected in CALLS.items():
        require(call_target(pe, site) == expected, f"EXE call changed: {site:#x}")
    rows = [check_v3(args.day11_v3, 11), check_v3(args.day21_v3, 21)]
    return {
        "schema": "ck3.maa87_dual_type_stat_source_boundary.v1",
        "game_build": "1.19.0.6",
        "exe_sha256": EXE_SHA256,
        "bridge_source_sha256": sha256(args.bridge_source),
        "source_save_identity_sha256": IDENTITY_SHA256,
        "frozen_v3_cases": rows,
        "effective_stat_type_pointer_offset": "CRegiment+0x118",
        "counter_class_type_pointer_offset": "CRegiment+0x18",
        "effective_stat_type_class_index_offset": "type+0x270",
        "counter_class_index_offset": "inner_type+0x270",
        "class_row_stride": "0x58",
        "toughness_class_row_enum_offsets": ["+0x2E", "+0x3A"],
        "fixed_toughness_enum_ids": ["0x1AC", "0x1AD", "0x1A7"],
        "army_source_path":
            "CRegiment+0x28 -> generation-resolved CRegiment+0x140 -> CArmy+0x38/+0x44",
        "pre_target_toughness_q100000_rule":
            "trunc_toward_zero((base_toughness_raw + accumulated_add_raw) * "
            "accumulated_multiplier_raw / 100000)",
        "target_toughness_vector_added_after_pre_target_rule": True,
        "same_regiment_type_pointers_observed_equal": False,
        "effective_stat_class_index_observed": False,
        "same_frame_modifier_values_observed": False,
        "specific_125000_raw_difference_cause_proven": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--bridge-source", type=Path, required=True)
    parser.add_argument("--identity-sidecar", type=Path, required=True)
    parser.add_argument("--day11-v3", type=Path, required=True)
    parser.add_argument("--day21-v3", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--output", type=Path)
    mode.add_argument("--check-sidecar", type=Path)
    args = parser.parse_args()
    result = project(args)
    if args.check_sidecar:
        require(json.loads(args.check_sidecar.read_text(encoding="utf-8")) == result,
                "dual-type source sidecar changed")
        print(json.dumps({"ok": True, "sidecar_sha256": sha256(args.check_sidecar)}))
    else:
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        print(json.dumps({"output": str(args.output), "sha256": sha256(args.output)}))


if __name__ == "__main__":
    main()
