#!/usr/bin/env python3
"""Verify the stock on-action loader directory and literal candidate set.

This narrows stock direct parser inputs only. It does not inspect a loaded root
or prove that any runtime child came from a particular source line/VFS mount.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

import pefile


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
ON_ACTION_SHA256 = "B35D696F472E801BB332D7204AA46008349E8AFBFDB38985C781EB099BBFB233"
COMBAT_EVENTS_SHA256 = "CF4E7F43786477DF43319638138232086CFD477FEE0F2951B34DD41BE265CADD"
ON_ACTION_TREE_SHA256 = "7A94B27129485C068333303CFF0872C23788F0B6A6E0B7006A4ACF19888C3ED7"
STRING_OPERANDS = {
    "extension": (0x2506B7C, 0x4080A4C, 4),
    "directory": (0x2506B95, 0x4081118, 16),
    "separator": (0x2506C2B, 0x4084340, 1),
}
ANCHORS = {
    0x2506B88: "c744247804000000",   # .txt length 4
    0x2506BA0: "c7458810000000",     # common/on_action length 16
    0x2506BBD: "488d5590",           # enumeration output buffer
    0x2506C3C: "488b5590",           # enumerated entry
    0x2506C40: "4803d7",             # current entry index
    0x2506C99: "488d542450",         # joined path view
    0x2506C9E: "488d8e78ffffff",     # same database primary base
}
CALLS = {0x2506BC5: 0x3B55190, 0x2506C37: 0x81B220,
         0x2506C56: 0x81B220, 0x2506CA5: 0x33F75C0}


def checked(path: Path, expected: str) -> bytes:
    data = path.read_bytes()
    actual = hashlib.sha256(data).hexdigest().upper()
    if actual != expected:
        raise ValueError(f"{path}: SHA changed: {actual}")
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--game-root", required=True, type=Path)
    args = parser.parse_args()
    data = checked(args.exe, EXE_SHA256)
    pe = pefile.PE(data=data, fast_load=True)
    result = {}
    for key, (site, target, length) in STRING_OPERANDS.items():
        operand = pe.get_data(site, 7)
        if operand[:3] not in (b"\x48\x8d\x05", b"\x48\x8d\x15"):
            raise ValueError(f"unexpected RIP-relative lea at {site:#x}")
        actual_target = site + 7 + int.from_bytes(operand[3:7], "little", signed=True)
        if actual_target != target:
            raise ValueError(f"operand target changed at {site:#x}")
        raw = pe.get_data(target, length)
        result[key] = {"site_rva": f"0x{site:X}", "target_rva": f"0x{target:X}",
                       "raw_hex": raw.hex(), "text": raw.decode("utf-8")}
    if {key: value["text"] for key, value in result.items()} != {
        "extension": ".txt", "directory": "common/on_action", "separator": "/"
    }:
        raise ValueError("on-action loader path operands changed")
    for site, hex_bytes in ANCHORS.items():
        expected = bytes.fromhex(hex_bytes)
        if pe.get_data(site, len(expected)) != expected:
            raise ValueError(f"loader instruction changed at {site:#x}")
    for site, target in CALLS.items():
        instruction = pe.get_data(site, 5)
        if instruction[0] != 0xE8 or site + 5 + struct.unpack_from("<i", instruction, 1)[0] != target:
            raise ValueError(f"loader call target changed at {site:#x}")
    on_action_path = args.game_root / "common/on_action/combat_on_actions.txt"
    event_path = args.game_root / "events/war_events/combat_events.txt"
    on_action = checked(on_action_path, ON_ACTION_SHA256).decode("utf-8-sig").splitlines()
    event = checked(event_path, COMBAT_EVENTS_SHA256).decode("utf-8-sig").splitlines()
    literal = "combat = { warscore_value >= 15 }"
    if on_action[518].strip() != "on_combat_end_loser = {" or on_action[562].strip() != literal:
        raise ValueError("stock loser on-action line changed")
    if event[2172].strip() != "combat_event.3000 = {" or event[2237].strip() != literal:
        raise ValueError("stock event control line changed")
    files = sorted((args.game_root / "common/on_action").rglob("*.txt"))
    tree_digest = hashlib.sha256()
    matches = []
    labels = []
    for path in files:
        relative = path.relative_to(args.game_root).as_posix()
        file_bytes = path.read_bytes()
        tree_digest.update(relative.encode("utf-8") + b"\0")
        tree_digest.update(hashlib.sha256(file_bytes).digest())
        lines = file_bytes.decode("utf-8-sig").splitlines()
        for line_number, line in enumerate(lines, 1):
            if line.strip() == literal:
                matches.append([relative, line_number])
            if line.strip() == "on_combat_end_loser = {":
                labels.append([relative, line_number])
    expected_label = ["common/on_action/combat_on_actions.txt", 519]
    expected_literal = ["common/on_action/combat_on_actions.txt", 563]
    if len(files) != 165 or tree_digest.hexdigest().upper() != ON_ACTION_TREE_SHA256:
        raise ValueError("stock on-action directory bytes changed")
    if labels != [expected_label] or matches != [expected_literal]:
        raise ValueError("stock on-action label/literal candidate set changed")
    print(json.dumps({
        "exe_sha256": EXE_SHA256,
        "on_action_sha256": ON_ACTION_SHA256,
        "combat_events_sha256": COMBAT_EVENTS_SHA256,
        "loader_strings": result,
        "checked_instruction_anchors": len(ANCHORS),
        "checked_relative_calls": len(CALLS),
        "stock_on_action_txt_files_scanned": len(files),
        "stock_on_action_tree_sha256": ON_ACTION_TREE_SHA256,
        "stock_on_action_root_label_matches": labels,
        "stock_on_action_literal_matches": matches,
        "outside_loader_directory_same_literal": ["events/war_events/combat_events.txt", 2238],
        "outside_loader_directory_event_id": "combat_event.3000",
        "actual_vfs_path_and_bytes_verified": False,
        "loaded_child_to_source_line_563_unique": False,
    }, indent=2))


if __name__ == "__main__":
    main()
