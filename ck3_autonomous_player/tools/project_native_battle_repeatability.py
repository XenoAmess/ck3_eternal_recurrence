"""Project one bounded CK3 checkpoint-reload experiment for film and planner research.

Different native replays may diverge. This projection preserves every source
receipt identity but never converts a few trajectories into a win percentage.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def obj(path: Path) -> dict:
    row = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(row, dict):
        raise ValueError(f"expected JSON object: {path}")
    return row


def verified_response(identity: dict, root: Path) -> tuple[dict, str]:
    path = Path(identity["path"])
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"response escaped its run directory: {path}")
    sha = digest(path)
    if sha != identity["sha256"] or path.stat().st_size != identity["bytes"]:
        raise ValueError(f"response bytes changed: {path}")
    row = obj(path)
    if row.get("result") != "CALL_COMPLETED" or not isinstance(row.get("body"), dict):
        raise ValueError(f"source response is not completed: {path}")
    return row["body"], sha


def project(root: Path) -> dict:
    root = root.resolve()
    summary_path = root / "repeatability-summary.json"
    summary = obj(summary_path)
    if (summary.get("schema") != "ck3.native_battle_repeatability.v1"
            or summary.get("game_build") != "1.19.0.6"
            or summary.get("combat_id") != 16777218
            or summary.get("subject_public_cunit_id") != 18
            or summary.get("independence_established") is not False):
        raise ValueError("repeatability summary identity/gate mismatch")
    original = [json.loads(line) for line in (root / "repeatability-journal.jsonl").read_text(
        encoding="utf-8").splitlines()]
    continued = [json.loads(line) for line in (root / "repeatability-continuation-journal.jsonl").read_text(
        encoding="utf-8").splitlines()]
    entries = original + continued
    checkpoint = next(row["checkpoint"] for row in original if row["kind"] == "checkpoint")
    checkpoint_path = Path(checkpoint["path"])
    if (digest(checkpoint_path) != checkpoint["sha256"].upper()
            or summary["contact_checkpoint_sha256"].upper() != checkpoint["sha256"].upper()):
        raise ValueError("contact checkpoint changed")
    trials = []
    source_trials = summary.get("trials")
    if not isinstance(source_trials, list) or [t.get("trial") for t in source_trials] != [1, 2, 3]:
        raise ValueError("expected exactly three bounded trials")
    for number, source in enumerate(source_trials, 1):
        daily = [row for row in entries if row.get("trial") == number and row.get("kind") == "battle_day"]
        if [row.get("day") for row in daily] != list(range(1, 32)):
            raise ValueError(f"trial {number} has a daily gap")
        projected_days = []
        for day, row in enumerate(daily, 1):
            body, sha = verified_response(row["control"]["response"], root)
            control = body.get("battle_control_snapshot")
            if (not isinstance(control, dict) or control.get("combat_id") != 16777218
                    or control.get("observed_date_raw") != 53146248 + (day - 1) * 24):
                raise ValueError(f"trial {number} day {day}: battle identity/date mismatch")
            sides = [control.get("attacker"), control.get("defender")]
            if not all(isinstance(side, dict) for side in sides):
                raise ValueError(f"trial {number} day {day}: missing sides")
            for side in sides:
                derived = sum(
                    int(regiment["current_fighting_raw"])
                    for bucket in ("levy_entries", "men_at_arms_entries")
                    for regiment in side[bucket]
                )
                if derived != side["derived_current_fighting_raw"]:
                    raise ValueError(f"trial {number} day {day}: regiment sum mismatch")
            projected_days.append({
                "day": day, "date_raw": control["observed_date_raw"],
                "phase": control["phase"], "phase_raw": control["phase_raw"],
                "side_current_raw_from_regiments": [
                    sides[0]["derived_current_fighting_raw"],
                    sides[1]["derived_current_fighting_raw"],
                ],
                "side_stored_current_raw": [
                    sides[0]["stored_current_fighting_raw"],
                    sides[1]["stored_current_fighting_raw"],
                ],
                "stored_matches_derived": [
                    sides[0]["stored_current_matches_derived"],
                    sides[1]["stored_current_matches_derived"],
                ],
                "control_response_sha256": sha,
            })
        terminal, terminal_sha = verified_response(source["terminal"]["response"], root)
        transition = terminal.get("battle_terminal_transition")
        prior = transition.get("prior") if isinstance(transition, dict) else None
        if (not isinstance(prior, dict) or prior.get("combat_id") != 16777218
                or prior.get("winner_raw") != source["winner_raw"]
                or prior.get("terminal_date_raw") != 53146248 + 31 * 24
                or source.get("day") != 32):
            raise ValueError(f"trial {number}: terminal identity mismatch")
        trials.append({
            "trial": number,
            "mode": "live_continuation_after_contact_save" if number == 1 else "checkpoint_restore",
            "first_date_raw": 53146248,
            "terminal_date_raw": prior["terminal_date_raw"],
            "winner_side_raw": prior["winner_raw"],
            "player_won": prior["winner_raw"] == 1,
            "battle_warscore": prior.get("battle_warscore"),
            "terminal_response_sha256": terminal_sha,
            "daily": projected_days,
        })
    pairwise = []
    for left, right in ((1, 2), (1, 3), (2, 3)):
        a, b = trials[left - 1]["daily"], trials[right - 1]["daily"]
        first = next((day for day in range(1, 32)
                      if a[day - 1]["side_current_raw_from_regiments"] !=
                      b[day - 1]["side_current_raw_from_regiments"]), None)
        pairwise.append({"left_trial": left, "right_trial": right,
                         "first_regiment_current_divergence_day": first})
    return {
        "schema": "ck3-native-battle-repeatability-evidence-v1",
        "case_id": "episode01-sicily-messina-combat-16777218",
        "game_version": "1.19.0.6",
        "combat_id": 16777218,
        "player_cunit_id": 18,
        "player_combat_side_raw": 1,
        "source_run_dir": str(root),
        "source_summary_sha256": digest(summary_path),
        "source_journal_sha256": [
            digest(root / "repeatability-journal.jsonl"),
            digest(root / "repeatability-continuation-journal.jsonl"),
        ],
        "contact_checkpoint_sha256": checkpoint["sha256"].upper(),
        "trials": trials,
        "pairwise_divergence": pairwise,
        "independent_random_draws_proven": False,
        "calibrated_win_probability_available": False,
        "planner_usable": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f"refusing to overwrite existing projection: {args.output}")
    result = project(args.run_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "sha256": digest(args.output),
                      "trials": len(result["trials"]),
                      "pairwise": result["pairwise_divergence"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
