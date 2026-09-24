"""Bind exact CK3 saves to two observed phase-event state changes.

Rakaly is used only to decode immutable CK3 saves into external plaintext
artifacts.  This projector verifies the native saves, melter, melted bytes,
character identities, trait lookup, and battle-event evidence before emitting
a portable narrow observation.  It does not establish a complete effect model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from xar_autoplayer.simulation.native_battle_case import (  # noqa: E402
    load_episode01_native_battle_case,
    load_episode01_phase_event_observations,
)


RAKALY_VERSION = "0.8.19"
RAKALY_EXE_SHA256 = "E154AF990AAED2C2F44284946772188C9749AD3F6B641B41F6C23456A6F1633D"
MELTED_SHA256_BY_DAY = {
    5: "AC71F3BFC148F475318CB98339470D52B30188957DD091C9552CA8DA5B4476C1",
    6: "54665950498039F44E92EC57F1E9D5E8951DE5EB4DAD2C525B7A7C34FECD2945",
    15: "D3DADB33E2638EE078FFED90D6BCB40A131638BCEBCD83D8B29F6F43DD4B025D",
    16: "2A2C2A8B8CAD579843613B3A5DEF2496D34433F541134CC388A49E267253D374",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _field(body: str, key: str) -> str | None:
    values = re.findall(rf"^\t+{re.escape(key)}=([^\n]+)", body, re.M)
    return values[0].strip() if values else None


def _character_snapshot(text: str, character_id: int) -> dict:
    lookup = re.findall(r"^traits_lookup=\{\s*\n\t([^\n]+)\n\}", text, re.M)
    if len(lookup) != 1:
        raise ValueError("melted save has no unique trait lookup")
    trait_keys = lookup[0].split()
    matches = re.findall(rf"^\t{character_id}=\{{\n(.*?)^\t\}}", text, re.M | re.S)
    if len(matches) != 1:
        raise ValueError(f"melted save has no unique character {character_id}")
    body = matches[0]
    trait_lists = re.findall(r"^\t\ttraits=\{\s*\n\t\t\t([^\n]+)\n\t\t\}", body, re.M)
    if len(trait_lists) != 1:
        raise ValueError(f"character {character_id} has no unique trait list")
    indices = [int(value) for value in trait_lists[0].split()]
    if len(indices) != len(set(indices)) or any(index >= len(trait_keys) or index < 0 for index in indices):
        raise ValueError(f"character {character_id} trait indices invalid")
    alive = re.search(r"^\t\talive_data=\{", body, re.M) is not None
    dead = re.search(r"^\t\tdead_data=\{", body, re.M) is not None
    if alive == dead:
        raise ValueError(f"character {character_id} life status ambiguous")
    return {
        "character_id": character_id,
        "trait_lookup_sha256": hashlib.sha256(lookup[0].encode("utf-8")).hexdigest().upper(),
        "trait_indices": indices,
        "trait_keys": [trait_keys[index] for index in indices],
        "wounded_rank": next((rank for rank in (1, 2, 3) if f"wounded_{rank}" in
                              [trait_keys[index] for index in indices]), 0),
        "alive_data_present": alive,
        "dead_data_present": dead,
        "death_date": _field(body, "date") if dead else None,
        "death_reason": _field(body, "reason").strip('"') if dead and _field(body, "reason") else None,
        "killer_character_id": int(_field(body, "killer")) if dead and _field(body, "killer") else None,
        "regiment_id": int(_field(body, "regiment")) if alive and _field(body, "regiment") else None,
        "character_block_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest().upper(),
    }


def project(trace_root: Path, melted_dir: Path, rakaly_exe: Path) -> dict:
    trace_root, melted_dir = trace_root.resolve(), melted_dir.resolve()
    if digest(rakaly_exe) != RAKALY_EXE_SHA256:
        raise ValueError("Rakaly executable bytes changed")
    case = load_episode01_native_battle_case()
    observations = load_episode01_phase_event_observations()
    if case["case_id"] != observations["case_id"]:
        raise ValueError("native case and event observation identities differ")
    source_by_day = {row["source_day"]: row for row in case["phase_traces"]}
    event_by_day = {row["source_day"]: row for row in observations["event_fire_pairs"]}
    rows = []
    for event_day, character_id, key in (
        (5, 36303, "knight_wounded_by_enemy"),
        (15, 36673, "knight_killed_by_enemy"),
    ):
        event = event_by_day[event_day]
        ledger = event["appended_battle_events"]
        if (len(ledger) != 1 or ledger[0]["stable_key"] != key
                or ledger[0]["left_character_id"] != character_id
                or ledger[0]["target_right"] is not False):
            raise ValueError(f"day {event_day}: ledger target mismatch")
        saves = []
        for source_day in (event_day, event_day + 1):
            raw = trace_root / f"trace-d{source_day:02d}-immutable.ck3"
            raw_sha = digest(raw)
            if raw_sha != source_by_day[source_day]["checkpoint_sha256"]:
                raise ValueError(f"day {source_day}: original CK3 save changed")
            melted = melted_dir / f"trace-d{source_day:02d}-melted.ck3"
            melted_sha = digest(melted)
            if melted_sha != MELTED_SHA256_BY_DAY[source_day]:
                raise ValueError(f"day {source_day}: melted save changed")
            snapshot = _character_snapshot(melted.read_text(encoding="utf-8-sig"), character_id)
            saves.append({
                "source_day": source_day,
                "date_raw": case["daily"][source_day - 1]["date_raw"],
                "native_save_sha256": raw_sha,
                "melted_save_sha256": melted_sha,
                "character": snapshot,
            })
        if (event_day == 5 and not (
                saves[0]["character"]["wounded_rank"] == 0
                and saves[1]["character"]["wounded_rank"] == 1
                and saves[0]["character"]["alive_data_present"]
                and saves[1]["character"]["alive_data_present"])
                or event_day == 15 and not (
                    saves[0]["character"]["alive_data_present"]
                    and saves[1]["character"]["dead_data_present"]
                    and saves[1]["character"]["death_reason"] == "death_battle"
                    and saves[1]["character"]["killer_character_id"] ==
                    ledger[0]["right_character_id"]
                )):
            raise ValueError(f"day {event_day}: expected narrow state transition absent")
        if event["native_date_raw"] != saves[1]["date_raw"]:
            raise ValueError(f"day {event_day}: event and later save date differ")
        rows.append({
            "event_source_day": event_day,
            "event_native_date_raw": event["native_date_raw"],
            "event_key": key,
            "target_character_id": character_id,
            "event_receipt_sha256": event["source_receipt_sha256"],
            "saves": saves,
            "same_fire_character_core_deltas": event["observed_character_core_deltas_within_fire"],
            "target_core_observations": event["target_character_observations"][0],
            "full_effect_write_set_proven": False,
            "effect_was_only_possible_cause_proven": False,
        })
    return {
        "schema": "ck3-native-phase-event-save-feedback-v1",
        "case_id": case["case_id"],
        "game_version": case["game_version"],
        "combat_id": case["combat_id"],
        "phase_trace_trajectory": case["phase_trace_trajectory"],
        "rakaly_version": RAKALY_VERSION,
        "rakaly_exe_sha256": RAKALY_EXE_SHA256,
        "rakaly_command": "melt <immutable.ck3> --unknown-key stringify --format ck3 --out <melted.ck3>",
        "event_save_pairs": rows,
        "full_effect_write_set_proven": False,
        "calibrated_win_probability_available": False,
        "planner_usable": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace-root", type=Path, required=True)
    parser.add_argument("--melted-dir", type=Path, required=True)
    parser.add_argument("--rakaly-exe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f"refusing to overwrite output: {args.output}")
    report = project(args.trace_root, args.melted_dir, args.rakaly_exe)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "sha256": digest(args.output),
                      "pairs": len(report["event_save_pairs"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
