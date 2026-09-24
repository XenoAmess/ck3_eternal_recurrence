"""Cross-check two original knight-kill rewards against the exact stock value.

The title/lowborn inputs remain an explicit condition. This report does not
turn the larger phase-event effect tree into a planner-ready model.
"""

from __future__ import annotations

import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "ck3_autonomous_player/src"))
sys.path.insert(0, str(REPO / "ck3_autonomous_player/tools"))
from xar_autoplayer.simulation.native_battle_case import (  # noqa: E402
    EPISODE01_KILL_REPLAY_SHA256,
    EPISODE01_PHASE_EVENT_SAVE_SHA256,
    load_episode01_phase_event_kill_replay_feedback,
    load_episode01_phase_event_save_feedback,
)
from xar_autoplayer.simulation.native_phase_event_rewards import (  # noqa: E402
    knight_kill_inverse_prestige_raw,
)
from project_native_phase_event_save_feedback import digest  # noqa: E402


def _held_titles_and_house(text: str, character_id: int) -> tuple[list[str], int]:
    lines = text.splitlines()
    holder = f"\t\t\tholder={character_id}"
    titles: list[str] = []
    for index, line in enumerate(lines):
        if line != holder:
            continue
        key = next((candidate.strip().split('"')[1]
                    for candidate in reversed(lines[max(0, index - 25):index])
                    if candidate.startswith("\t\t\tkey=\"")), None)
        if key is None or not re.fullmatch(r"[bcdke]_[a-z0-9_]+", key):
            raise ValueError(f"character {character_id}: title holder context ambiguous")
        titles.append(key)
    body = re.findall(rf"^\t{character_id}=\{{\n(.*?)^\t\}}", text, re.M | re.S)
    if len(body) != 1:
        raise ValueError(f"character {character_id}: nonunique save block")
    house = re.findall(r"^\t\tdynasty_house=(\d+)$", body[0], re.M)
    if len(house) != 1:
        raise ValueError(f"character {character_id}: dynasty house not observed")
    return sorted(titles), int(house[0])


def _row(
    *, source: str, target_id: int, opponent_id: int, observed: str,
    raw_save: Path, melted_save: Path, expected_raw_sha: str,
    expected_melted_sha: str, expected_titles: list[str],
    expected_house: int, title_tier: int | None,
) -> dict:
    if digest(raw_save) != expected_raw_sha or digest(melted_save) != expected_melted_sha:
        raise ValueError(f"{source}: native or melted save bytes changed")
    titles, house = _held_titles_and_house(melted_save.read_text(encoding="utf-8-sig"), target_id)
    if titles != expected_titles or house != expected_house:
        raise ValueError(f"{source}: held title/house evidence changed")
    expected = knight_kill_inverse_prestige_raw(
        victim_primary_title_tier=title_tier, victim_is_lowborn=False)
    native_raw = int(Decimal(observed) * 100_000)
    if expected != native_raw:
        raise ValueError(f"{source}: conditional stock value does not match original prestige delta")
    return {
        "source": source,
        "target_character_id": target_id,
        "opponent_character_id": opponent_id,
        "target_held_title_keys": titles,
        "target_dynasty_house_id": house,
        "conditional_primary_title_tier": title_tier,
        "conditional_lowborn": False,
        "native_lowborn_trigger_readback_available": False,
        "native_prestige_delta_raw_q100000": native_raw,
        "agent_stock_value_raw_q100000": expected,
        "delta_raw_q100000": expected - native_raw,
        "source_native_save_sha256": expected_raw_sha,
        "source_melted_save_sha256": expected_melted_sha,
    }


def project(old_trace: Path, old_melted: Path, new_run: Path, stock_root: Path) -> dict:
    old = load_episode01_phase_event_save_feedback()
    new = load_episode01_phase_event_kill_replay_feedback()
    old_event = next(row for row in old["event_save_pairs"] if row["event_source_day"] == 15)
    if (old_event["event_key"] != "knight_killed_by_enemy"
            or old_event["target_character_id"] != 36673
            or old_event["opponent_character_id"] != 32716
            or Decimal(old_event["opponent_prestige_currency_delta"]) != 300
            or new["appended_event"]["left_character_id"] != 33437
            or new["appended_event"]["right_character_id"] != 34120
            or Decimal(new["opponent_prestige_currency_delta"]) != 150):
        raise ValueError("native kill event identities or observed rewards changed")
    basic = stock_root / "common/script_values/00_basic_values.txt"
    phase = stock_root / "common/combat_phase_events/00_knight_phase_events.txt"
    basic_text = basic.read_text(encoding="utf-8-sig")
    phase_text = phase.read_text(encoding="utf-8-sig")
    if (digest(phase) != "E8F8E4978BB1AF130D74AA6ED72EE41F014B09C9F324608EBFB0E87D56A5EDB1"
            or "medium_prestige_value = 150" not in basic_text
            or not re.search(r"knight_prestige_gain_on_kill_inverse\s*=\s*\{\s*value\s*=\s*medium_prestige_gain\s*if\s*=\s*\{\s*limit\s*=\s*\{\s*exists\s*=\s*root.primary_title\s*root.primary_title.tier\s*>\s*0\s*\}\s*multiply\s*=\s*root.primary_title.tier", basic_text)
            or not re.search(r"root\s*=\s*\{\s*is_lowborn\s*=\s*yes\s*\}\s*\}\s*divide\s*=\s*2", basic_text)
            or "add_prestige = knight_prestige_gain_on_kill_inverse" not in phase_text):
        raise ValueError("exact-build stock kill reward formula changed")
    prior = old_event["saves"][0]
    rows = [
        _row(
            source="attempt-004-original-day15-kill",
            target_id=36673, opponent_id=32716,
            observed=old_event["opponent_prestige_currency_delta"],
            raw_save=old_trace / "trace-d15-immutable.ck3",
            melted_save=old_melted / "trace-d15-melted.ck3",
            expected_raw_sha=prior["native_save_sha256"],
            expected_melted_sha=prior["melted_save_sha256"],
            expected_titles=["b_baja_medjerda", "c_medjerda"],
            expected_house=10393, title_tier=2,
        ),
        _row(
            source="attempt-013-independent-restored-day26-kill",
            target_id=33437, opponent_id=34120,
            observed=new["opponent_prestige_currency_delta"],
            raw_save=new_run / "d26-restored-before-immutable.ck3",
            melted_save=new_run / "d26-restored-before-melted.ck3",
            expected_raw_sha=new["before_native_save_sha256"],
            expected_melted_sha=new["before_melted_save_sha256"],
            expected_titles=[], expected_house=1105, title_tier=None,
        ),
    ]
    return {
        "schema": "xar.ck3.episode01.knight-kill-reward-scaling/v1",
        "game_build": "CK3 1.19.0.6",
        "source_old_feedback_sha256": EPISODE01_PHASE_EVENT_SAVE_SHA256,
        "source_new_feedback_sha256": EPISODE01_KILL_REPLAY_SHA256,
        "source_script_values_sha256": digest(basic),
        "source_phase_events_sha256": digest(phase),
        "script_value_key": "knight_prestige_gain_on_kill_inverse",
        "base_prestige_raw_q100000": 15_000_000,
        "conditional_formula": "base * positive_root_primary_title_tier_if_present / 2_if_root_is_lowborn",
        "conditional_exact_cases": len(rows),
        "cases": rows,
        "title_rank_and_lowborn_conditions_proven_for_all_future_events": False,
        "reward_only_possible_cause_proven": False,
        "full_event_write_set_proven": False,
        "whole_battle_win_probability_available": False,
        "planner_usable": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-trace", type=Path, required=True)
    parser.add_argument("--old-melted", type=Path, required=True)
    parser.add_argument("--new-run", type=Path, required=True)
    parser.add_argument("--stock-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = project(args.old_trace, args.old_melted, args.new_run, args.stock_root)
    with args.output.open("x", encoding="utf-8", newline="\n") as out:
        json.dump(report, out, ensure_ascii=False, indent=2)
        out.write("\n")
    print(json.dumps({"output": str(args.output), "sha256": digest(args.output)}))


if __name__ == "__main__":
    main()
