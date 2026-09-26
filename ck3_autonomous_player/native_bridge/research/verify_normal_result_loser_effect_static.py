#!/usr/bin/env python3
"""Fail closed on exact-build normal-result loser-effect source anchors.

This is a read-only source verifier. It checks file identities, instruction bytes,
and the stock script declarations; it cannot prove that a live battle executed an
effect or that CK3 compiled a script literal to a particular comparison operand.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import pefile


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
ON_ACTION_SHA256 = "B35D696F472E801BB332D7204AA46008349E8AFBFDB38985C781EB099BBFB233"
VALUES_SHA256 = "13E43166356B5DD99358F435330B03CB9BE95AB5913280318B01681186E23A2E"

# Exact bytes are deliberately narrower than the whole functions. The pinned
# EXE SHA guards against interpreting these bytes under another game build.
ANCHORS = {
    0x230A654: "4584c9",  # suppress-normal-result flag
    0x230A657: "0f8560030000",  # true bypass to common cleanup
    0x230A7C6: "e8d5fdf1ff",  # CWar battle-row writer call
    0x230A7DA: "e8d1efffff",  # UI/reward builder call
    0x230A9A3: "e868050000",  # result-effect dispatcher call
    0x222A693: "488b4140",  # load new row +0x40
    0x222A697: "49894040",  # store result +0x40
    0x230AF7F: "48638ee0060000",  # winner side CCombat+0x6E0
    0x230AFF4: "488b9858020000",  # winner database +0x258
    0x230B035: "e816d30e01",  # winner effect dispatch
    0x230B0AD: "488b9860020000",  # loser database +0x260
    0x230B0EE: "e85dd20e01",  # loser effect dispatch
    0x284C7FC: "448b8008070000",  # warscore trigger: CCombat+0x708
    0x284C830: "488b4040",  # warscore trigger: ResultData+0x40
}


def checked_bytes(path: Path, expected_sha: str) -> bytes:
    data = path.read_bytes()
    actual_sha = hashlib.sha256(data).hexdigest().upper()
    if actual_sha != expected_sha:
        raise ValueError(f"{path}: expected SHA-256 {expected_sha}, got {actual_sha}")
    return data


def script_block(text: str, name: str) -> str:
    start = text.index(f"{name} = {{")
    opening = text.index("{", start)
    depth = 0
    for index in range(opening, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    raise ValueError(f"unclosed script block: {name}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--on-action", required=True, type=Path)
    parser.add_argument("--legitimacy-values", required=True, type=Path)
    args = parser.parse_args()

    exe = checked_bytes(args.exe, EXE_SHA256)
    image = pefile.PE(data=exe, fast_load=True)
    for rva, expected_hex in ANCHORS.items():
        expected = bytes.fromhex(expected_hex)
        offset = image.get_offset_from_rva(rva)
        actual = exe[offset : offset + len(expected)]
        if actual != expected:
            raise ValueError(f"RVA 0x{rva:X}: expected {expected.hex()}, got {actual.hex()}")

    on_action = checked_bytes(args.on_action, ON_ACTION_SHA256).decode("utf-8-sig")
    values = checked_bytes(args.legitimacy_values, VALUES_SHA256).decode("utf-8-sig")
    loser = script_block(on_action, "on_combat_end_loser")
    fragments = (
        "combat = { warscore_value >= 15 }",
        "is_valid_for_legitimacy_change = yes",
        "add_legitimacy = minor_legitimacy_loss",
        "defender_war_score <= -25",
        "attacker_war_score <= -25",
        "trigger_event = ach_yearly_events.1003",
    )
    for fragment in fragments:
        if fragment not in loser:
            raise ValueError(f"missing loser on-action declaration: {fragment}")
    if not (loser.index(fragments[0]) < loser.index(fragments[1]) < loser.index(fragments[2])):
        raise ValueError("unexpected loser score / legitimacy declaration order")
    if not re.search(r"(?m)^minor_legitimacy_gain\s*=\s*50\s*$", values):
        raise ValueError("minor_legitimacy_gain is not 50")
    if not re.search(
        r"(?ms)^minor_legitimacy_loss\s*=\s*\{\s*value\s*=\s*0\s*subtract\s*=\s*minor_legitimacy_gain\s*\}",
        values,
    ):
        raise ValueError("minor_legitimacy_loss no longer subtracts minor gain from zero")

    print(
        json.dumps(
            {
                "status": "static_source_verified",
                "exe_sha256": EXE_SHA256,
                "on_action_sha256": ON_ACTION_SHA256,
                "legitimacy_values_sha256": VALUES_SHA256,
                "verified_rvas": [f"0x{rva:X}" for rva in ANCHORS],
                "single_battle_magnitude_scale": 100000,
                "script_threshold_nominal": 15,
                "script_threshold_projected_raw": 1500000,
                "script_literal_comparator_verified": False,
                "declared_legitimacy_delta": -50,
                "live_effect_writeback_verified": False,
                "war48_request_verified": False,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
