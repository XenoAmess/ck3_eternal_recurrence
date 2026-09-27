#!/usr/bin/env python3
"""Bind WAR31's persisted truce_0/1 slot to its exact-build owner direction.

This is a read-only save and executable projection.  It does not make a native
same-frame query or claim that the six-day save delta records every write.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

import pefile

from project_war31_save_material import project_melted


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
MATERIAL_REPORT_SHA256 = "84154554437CE96FB751DC6DB23E65847CA974CD92917A2FCB32B12C3FC11634"
BEFORE_MELTED_SHA256 = "FC39B744D666C649C4E54B1198F7C7C5B39847B8AB8E98BC97F16919D9603C79"
AFTER_MELTED_SHA256 = "2BE7B6485653A6E328CAE3829AF3E19F23AA27F32E96CD71C6578BEC12638ABA"
BEFORE_SAVE_SHA256 = "1AF4055F978AF60267FB3A0D8658224047CD6BFDA884C66886A13B74EE34A90A"
AFTER_SAVE_SHA256 = "A29A41B2434B2A91BE1D3DC254F8C71455D4ACA528F1DCC9FF32369608F2EDB5"

# Each opcode pins one link in the chain: serialized token to slot, parsed
# token to slot, native owner to slot, and stock add-truce owner to slot.
_OPCODES = {
    0x23655ED: "488D4F28",      # serialize relation+0x28
    0x236561B: "BA522B0000",    # token 0x2B52 = truce_0
    0x236564B: "488D4F58",      # serialize relation+0x58
    0x2365672: "BA532B0000",    # token 0x2B53 = truce_1
    0x236508C: "4181F8522B0000",  # parse token 0x2B52
    0x2365093: "B828000000",    # truce_0 -> +0x28
    0x2365098: "BA58000000",    # otherwise +0x58
    0x236509D: "0F45C2",        # choose by token equality
    0x2663272: "8B4F18",        # native getter owner ID
    0x2663275: "448B4B08",      # relation first ID
    0x2663279: "413BC9",        # compare owner with first
    0x2663284: "488D5328",      # first owner -> +0x28
    0x2663290: "3B4B0C",       # compare owner with second
    0x266329B: "4C8D4358",      # second owner -> +0x58
    0x2EDB1A9: "418B4618",     # stock add-truce owner ID
    0x2EDB1AD: "413B442408",   # compare owner with first
    0x2EDB1B4: "B828000000",   # first owner -> +0x28
    0x2EDB1BB: "413B44240C",   # compare owner with second
    0x2EDB1C2: "B858000000",   # second owner -> +0x58
    0x2EDB1EA: "488903",       # write resulting date
}


def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest().upper()


def verify_exact_build(exe: Path) -> dict[str, object]:
    data = exe.read_bytes()
    if hashlib.sha256(data).hexdigest().upper() != EXE_SHA256:
        raise ValueError("exact CK3 executable SHA-256 mismatch")
    image = pefile.PE(data=data, fast_load=True)
    if image.OPTIONAL_HEADER.ImageBase != 0x140000000:
        raise ValueError("exact CK3 image base mismatch")
    observed = {}
    for rva, expected_hex in _OPCODES.items():
        expected = bytes.fromhex(expected_hex)
        if image.get_data(rva, len(expected)) != expected:
            raise ValueError(f"truce slot opcode changed at RVA 0x{rva:X}")
        observed[f"0x{rva:X}"] = expected_hex
    token_rows = []
    for token_id, name, name_rva, entry_rva in (
        (0x2B52, b"truce_0\x00", 0x429A390, 0x42BF8D0),
        (0x2B53, b"truce_1\x00", 0x429A400, 0x42BF8E0),
    ):
        if image.get_data(name_rva, len(name)) != name:
            raise ValueError("truce slot token string changed")
        entry = struct.pack("<Q", token_id) + struct.pack(
            "<Q", image.OPTIONAL_HEADER.ImageBase + name_rva
        )
        if image.get_data(entry_rva, len(entry)) != entry:
            raise ValueError("truce slot token-ID mapping changed")
        token_rows.append({"name": name[:-1].decode("ascii"),
                           "token_id": token_id,
                           "name_rva": f"0x{name_rva:X}",
                           "entry_rva": f"0x{entry_rva:X}"})
    return {"exe_sha256": EXE_SHA256, "opcode_bytes": observed,
            "token_rows": token_rows,
            "slot_mapping": {
                "truce_0": {"owner": "first", "relation_offset": "0x28"},
                "truce_1": {"owner": "second", "relation_offset": "0x58"},
            }}


def project_direction(relation: dict[str, object]) -> list[dict[str, object]]:
    if relation.get("status") != "observed_pair_truce_slots":
        raise ValueError("exact saved character pair has no truce slot")
    first = relation.get("first_character_id")
    second = relation.get("second_character_id")
    if (not isinstance(first, int) or isinstance(first, bool) or first <= 0
            or not isinstance(second, int) or isinstance(second, bool)
            or second <= 0 or first == second):
        raise ValueError("saved character pair identity invalid")
    slots = relation.get("raw_slots")
    if not isinstance(slots, dict) or not slots:
        raise ValueError("saved truce slots absent")
    projected = []
    for slot, raw in sorted(slots.items()):
        if slot not in {"truce_0", "truce_1"} or not isinstance(raw, dict):
            raise ValueError("unexpected saved truce slot")
        if not isinstance(raw.get("date"), str) or not raw["date"]:
            raise ValueError("saved truce slot lacks expiry")
        projected.append({
            "slot": slot,
            "owner_character_id": first if slot == "truce_0" else second,
            "toward_character_id": second if slot == "truce_0" else first,
            "expiry_date": raw["date"],
            "result": raw.get("result"),
            "source_line": raw.get("line_start"),
        })
    return projected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--material-report", type=Path, required=True)
    parser.add_argument("--before-melted", type=Path, required=True)
    parser.add_argument("--after-melted", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build = verify_exact_build(args.exe)
    if digest(args.material_report) != MATERIAL_REPORT_SHA256:
        raise ValueError("WAR31 exact save-material report SHA-256 mismatch")
    if (digest(args.before_melted) != BEFORE_MELTED_SHA256
            or digest(args.after_melted) != AFTER_MELTED_SHA256):
        raise ValueError("WAR31 melted text SHA-256 mismatch")
    material = json.loads(args.material_report.read_text(encoding="utf-8"))
    if (material.get("schema") != "xar.ck3.war31.save-material.v1"
            or material["sources"]["before"]["save_sha256"] != BEFORE_SAVE_SHA256
            or material["sources"]["after"]["save_sha256"] != AFTER_SAVE_SHA256):
        raise ValueError("WAR31 material report source identity mismatch")
    before = project_melted(args.before_melted)
    after = project_melted(args.after_melted)
    if before != material["before"] or after != material["after"]:
        raise ValueError("fresh save projection differs from frozen material report")
    if before["persisted_truce"]["raw_slots"]:
        raise ValueError("WAR31 before save already has a truce slot")
    relation = after["persisted_truce"]
    if (relation["first_character_id"] != 29829
            or relation["second_character_id"] != 30097
            or relation["active_war_id"] is not None):
        raise ValueError("WAR31 after relation identity mismatch")
    direction = project_direction(relation)
    report = {
        "schema": "xar.ck3.war31.truce-slot-direction.v1",
        "status": "exact_build_serialized_slot_direction_observed",
        "source_sha256": {
            "exe": EXE_SHA256,
            "material_report": MATERIAL_REPORT_SHA256,
            "before_melted": BEFORE_MELTED_SHA256,
            "after_melted": AFTER_MELTED_SHA256,
        },
        "build_mapping": build,
        "save_date": after["save_date"],
        "war_id": 16777231,
        "relation_first_character_id": 29829,
        "relation_second_character_id": 30097,
        "observed_directional_slots": direction,
        "same_native_frame_binding": False,
        "causal_attribution": "not_proven_for_every_intervening_save_write",
    }
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output), "sha256": digest(args.output),
                      "directions": direction}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
