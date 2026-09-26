"""Bind the observed knight-kill boundary to same-day native save writeback.

Requires two already melted CK3 saves from the same isolated attempt.  The
underlying saves, executable, decoded text, native trace and selection report
are all hash-bound.  A narrow target/killer delta is evidence; it is not the
complete compiled effect write set or proof of sole causation.
"""

from __future__ import annotations

import argparse
from decimal import Decimal
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player/tools"))
from project_native_phase_event_save_feedback import (  # noqa: E402
    RAKALY_EXE_SHA256,
    RAKALY_VERSION,
    _character_snapshot,
)

SELECTOR_REPORT = (
    ROOT / "ck3_autonomous_player/src/xar_autoplayer/simulation/data"
    / "ck3_1_19_0_6_episode01_messina_knight_selector_native_parity.json"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def response(attempt: Path, name: str) -> tuple[dict[str, object], str]:
    path = attempt / "ck3-output/interactive-requests-responses" / name
    value = json.loads(path.read_text(encoding="utf-8"))
    require(value["result"] == "CALL_COMPLETED" and value["body"]["accepted"] is True,
            f"{name} native response")
    return value["body"], digest(path)


def project(attempt: Path, rakaly_exe: Path) -> dict[str, object]:
    require(digest(rakaly_exe) == RAKALY_EXE_SHA256, "Rakaly executable SHA")
    selector = json.loads(SELECTOR_REPORT.read_text(encoding="utf-8"))
    before, before_sha = response(attempt, "002-before-save.json")
    after, after_sha = response(attempt, "008-after-save.json")
    finish, finish_sha = response(attempt, "007-finish.json")
    require(finish_sha == selector["trace_response_sha256"]
            and before["checkpoint"]["date_raw"] == 53146848
            and after["checkpoint"]["date_raw"] == 53146872,
            "same source day, native trace and next-date save")
    raw_before = attempt / "d26-episode-seed-immutable.ck3"
    raw_after = attempt / "d27-postevent-immutable.ck3"
    require(digest(raw_before) == before["episode_seed"]["sha256"].upper()
            == before["checkpoint"]["sha256"].upper()
            and digest(raw_after) == after["checkpoint"]["sha256"].upper(),
            "immutable raw save identities")
    melted_before = attempt / "d26-episode-seed-melted.ck3"
    melted_after = attempt / "d27-postevent-melted.ck3"
    texts = [path.read_text(encoding="utf-8-sig")
             for path in (melted_before, melted_after)]
    target_before, target_after = (_character_snapshot(text, 33437) for text in texts)
    killer_before, killer_after = (_character_snapshot(text, 34120) for text in texts)
    require(target_before["trait_lookup_sha256"] == target_after["trait_lookup_sha256"]
            == killer_before["trait_lookup_sha256"] == killer_after["trait_lookup_sha256"],
            "stock trait lookup stable across saves")
    trace = finish["managed_trace"]["trace"]
    require(finish["status"] == "bounded_trace_available"
            and trace["failure_flags"] == 0
            and len(trace["records"]) == 7,
            "complete bounded phase trace")
    at_fire = [row for row in trace["records"][5]["characters"]
               if row["character_id"] == 33437]
    at_final = [row for row in trace["records"][6]["characters"]
                if row["character_id"] == 33437]
    require(len(at_fire) == len(at_final) == 1
            and at_fire[0]["death_marker_present"] is False
            and at_fire[0]["prowess"] == 4
            and at_fire[0]["current_regiment_id"] == 65
            and at_final[0]["death_marker_present"] is True
            and at_final[0]["prowess"] == 2
            and at_final[0]["current_regiment_id"] == 0,
            "original fire-to-final target core transition")
    require(target_before["alive_data_present"] is True
            and target_before["regiment_id"] == 65
            and target_after["dead_data_present"] is True
            and target_after["death_reason"] == "death_battle"
            and target_after["killer_character_id"] == 34120
            and target_after["regiment_id"] is None,
            "native save death and regiment detach")
    require(target_before["base_skill_values"] == target_after["base_skill_values"]
            and target_before["base_skill_values"][-1] == 2,
            "root base prowess did not change on death")
    require(killer_before["base_skill_values"] == killer_after["base_skill_values"]
            and killer_before["alive_data_present"] is True
            and killer_after["alive_data_present"] is True,
            "killer base skills and life stable")
    prestige_currency = (Decimal(killer_after["prestige_currency"])
                         - Decimal(killer_before["prestige_currency"]))
    prestige_accumulated = (Decimal(killer_after["prestige_accumulated"])
                            - Decimal(killer_before["prestige_accumulated"]))
    require(prestige_currency == prestige_accumulated == Decimal("150"),
            "same-day killer prestige ledger")
    return {
        "schema": "ck3.native_knight_kill_writeback.v1",
        "game_build": "1.19.0.6",
        "combat_id": 16777218,
        "source_day": 26,
        "selector_report_sha256": digest(SELECTOR_REPORT),
        "rakaly_version": RAKALY_VERSION,
        "rakaly_exe_sha256": RAKALY_EXE_SHA256,
        "rakaly_command": "melt <immutable.ck3> --unknown-key stringify --format ck3 --out <melted.ck3>",
        "before_save_receipt_sha256": before_sha,
        "after_save_receipt_sha256": after_sha,
        "trace_response_sha256": finish_sha,
        "before_native_save_sha256": digest(raw_before),
        "after_native_save_sha256": digest(raw_after),
        "before_melted_save_sha256": digest(melted_before),
        "after_melted_save_sha256": digest(melted_after),
        "target_character_id": 33437,
        "killer_character_id": 34120,
        "target_at_fire_boundary": at_fire[0],
        "target_at_final_boundary": at_final[0],
        "target_before_save": target_before,
        "target_after_save": target_after,
        "killer_before_save": killer_before,
        "killer_after_save": killer_after,
        "target_base_prowess_change": 0,
        "target_effective_core_prowess_change": -2,
        "killer_base_prowess_change": 0,
        "killer_prestige_currency_delta": str(prestige_currency),
        "killer_prestige_accumulated_delta": str(prestige_accumulated),
        "full_effect_write_set_proven": False,
        "effect_only_cause_proven": False,
        "whole_battle_win_probability_available": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=Path, required=True)
    parser.add_argument("--rakaly-exe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = project(args.attempt, args.rakaly_exe)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output), "sha256": digest(args.output)}))


if __name__ == "__main__":
    main()
