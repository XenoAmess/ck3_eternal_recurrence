"""Project one immutable same-run CK3 v3 + phase-trace R14 comparison.

This is a conditional combat-kernel check. Native fighting-men and effective
damage values are read from the phase boundary; the projector never promotes
that observation to a forecast producer or battle-win probability.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "ck3_autonomous_player" / "src"))
from xar_autoplayer.simulation.combat_input import freeze_combat_simulation_input


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def load_body(path: Path) -> dict:
    row = json.loads(path.read_text(encoding="utf-8"))
    if row.get("result") != "CALL_COMPLETED":
        raise ValueError(f"not a completed native call: {path}")
    return row["body"]


def project(run: Path) -> dict:
    journal = run / "paired-v3-r14.jsonl"
    rows = [json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines()]
    if not rows or [row["day"] for row in rows] != list(range(4, 4 + len(rows))):
        raise ValueError("paired days must be a nonempty contiguous sequence from day 4")
    projected = []
    for row in rows:
        day = row["day"]
        tag = f"d{day:02d}"
        checkpoint = run / f"{tag}-immutable.ck3"
        if sha256(checkpoint) != row["checkpoint_sha256"].upper():
            raise ValueError(f"checkpoint hash drift on day {day}")
        v3_path = run / "ck3-output" / "interactive-requests-responses" / f"{tag}-v3.json"
        trace_path = run / "ck3-output" / "interactive-requests-responses" / f"{tag}-finish.json"
        if sha256(v3_path) != row["v3_response_sha256"]:
            raise ValueError(f"v3 response hash drift on day {day}")
        if sha256(trace_path) != row["trace_response_sha256"]:
            raise ValueError(f"trace response hash drift on day {day}")
        v3 = load_body(v3_path)
        finish = load_body(trace_path)
        if v3["status"] != "available" or finish["status"] != row["trace_status"]:
            raise ValueError(f"native statuses drifted on day {day}")
        model = freeze_combat_simulation_input(v3["combat_simulation_inputs"]["base_inputs"])
        trace = finish["managed_trace"]["trace"]
        native_r14 = trace["post_counter_attack"]
        if native_r14 != row["native_r14"]:
            raise ValueError(f"R14 capture drifted on day {day}")
        predicted = None
        boundary_index = row["boundary_index"]
        if boundary_index is not None:
            boundary = trace["records"][boundary_index]
            if boundary["capture_failure_flags"] or [s["side_index"] for s in boundary["sides"]] != [0, 1]:
                raise ValueError(f"claimed boundary is invalid on day {day}")
            observed = {
                "enemy": {r["regiment_id"]: r for r in boundary["sides"][0]["regiments"]},
                "player_or_allied": {r["regiment_id"]: r for r in boundary["sides"][1]["regiments"]},
            }
            entries = {}
            for side in observed:
                original = model.initial_entries_for_side(side)
                if {entry.regiment_id for entry in original} != set(observed[side]):
                    raise ValueError(f"claimed regiment census drifted on day {day}: {side}")
                entries[side] = tuple(
                    replace(entry,
                            current_raw=observed[side][entry.regiment_id]["current_fighting_raw"],
                            toughness_raw=observed[side][entry.regiment_id]["effective_toughness_raw"])
                    for entry in original
                )
            predicted = {}
            for side in observed:
                other = "enemy" if side == "player_or_allied" else "player_or_allied"
                damage = {
                    regiment.regiment_id: observed[side][regiment.regiment_id]["effective_damage_raw"]
                    for army in model.armies_for_side(side) for regiment in army.regiments
                    if regiment.fights_in_main_phase
                }
                predicted[side] = model.post_counter_attack_from_fighting_entries_raw(
                    side, entries[side], entries[other], damage
                )
            if predicted != row["predicted_r14"]:
                raise ValueError(f"projected R14 drifted on day {day}")
        side_comparison = {
            "enemy": ("unavailable" if predicted is None else
                      "exact" if predicted["enemy"] == native_r14["side0_raw"] else "mismatch"),
            "player_or_allied": ("unavailable" if predicted is None else
                                 "exact" if predicted["player_or_allied"] == native_r14["side1_raw"] else "mismatch"),
        }
        exact = all(value == "exact" for value in side_comparison.values())
        projected.append({
            "day": day, "date_raw": row["date_raw"],
            "attacker_army_ids": row["v3_attacker_ids"],
            "defender_army_ids": row["v3_defender_ids"],
            "trace_status": row["trace_status"],
            "trace_failure_flags": row["trace_failure_flags"],
            "boundary_index": boundary_index,
            "native_enemy_r14_raw": native_r14["side0_raw"],
            "native_player_r14_raw": native_r14["side1_raw"],
            "derived_enemy_r14_raw": None if predicted is None else predicted["enemy"],
            "derived_player_r14_raw": None if predicted is None else predicted["player_or_allied"],
            "side_comparison": side_comparison,
            "classification": (
                "conditional_exact_native_fighting_and_stats" if exact
                else "join_or_boundary_not_reconstructed" if predicted is not None
                else "pre_fire_regiment_boundary_unavailable"
            ),
            "checkpoint_sha256": row["checkpoint_sha256"].upper(),
            "v3_response_sha256": row["v3_response_sha256"],
            "trace_response_sha256": row["trace_response_sha256"],
        })
    exact_days = [row["day"] for row in projected if row["classification"] == "conditional_exact_native_fighting_and_stats"]
    unresolved_days = [row["day"] for row in projected if row["classification"] != "conditional_exact_native_fighting_and_stats"]
    exact_sides = sum(value == "exact" for row in projected for value in row["side_comparison"].values())
    comparable_sides = sum(value != "unavailable" for row in projected for value in row["side_comparison"].values())
    return {
        "schema": "xar.ck3.episode01.paired-counter-r14-parity/v1",
        "game_build": "CK3 1.19.0.6",
        "capture_run": str(run.resolve()),
        "source_journal_sha256": sha256(journal),
        "scope": "single-independent-replay; same-day native v3 input plus native phase trace",
        "conditional_on": ["native_current_fighting_raw", "native_effective_damage_raw", "native_pre_fire_roster"],
        "forecast_ready": False,
        "planner_usable": False,
        "observed_days": len(projected),
        "conditional_exact_days": exact_days,
        "conditional_exact_side_comparisons": exact_sides,
        "conditional_comparable_side_count": comparable_sides,
        "unresolved_days": unresolved_days,
        "days": projected,
    }


def make_regression_fixture(run: Path, day: int) -> dict:
    """Keep the v3 combat base and one complete pre-fire boundary, not 5 MB effects."""
    tag = f"d{day:02d}"
    responses = run / "ck3-output" / "interactive-requests-responses"
    v3_path = responses / f"{tag}-v3.json"
    trace_path = responses / f"{tag}-finish.json"
    v3 = load_body(v3_path)
    finish = load_body(trace_path)
    trace = finish["managed_trace"]["trace"]
    for boundary_index in (1, 0):
        boundary = trace["records"][boundary_index]
        if boundary["capture_failure_flags"] == 0 and [s["side_index"] for s in boundary["sides"]] == [0, 1]:
            break
    else:
        raise ValueError(f"no complete pre-fire boundary on day {day}")
    return {
        "schema": "xar.ck3.native-r14-regression-fixture/v1",
        "game_build": "CK3 1.19.0.6",
        "source_capture_run": str(run.resolve()),
        "source_day": day,
        "v3_response_sha256": sha256(v3_path),
        "trace_response_sha256": sha256(trace_path),
        "basis": "same-run v3 classes/context plus native pre-fire fighting Q100000 and refreshed damage",
        "base_inputs": v3["combat_simulation_inputs"]["base_inputs"],
        "pre_fire_regiments": {
            "enemy": [
                {key: regiment[key] for key in (
                    "regiment_id", "current_fighting_raw", "effective_damage_raw", "effective_toughness_raw"
                )} for regiment in boundary["sides"][0]["regiments"]
            ],
            "player_or_allied": [
                {key: regiment[key] for key in (
                    "regiment_id", "current_fighting_raw", "effective_damage_raw", "effective_toughness_raw"
                )} for regiment in boundary["sides"][1]["regiments"]
            ],
        },
        "native_r14_raw": {
            "enemy": trace["post_counter_attack"]["side0_raw"],
            "player_or_allied": trace["post_counter_attack"]["side1_raw"],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fixture-day", type=int)
    parser.add_argument("--fixture-output", type=Path)
    args = parser.parse_args()
    if (args.fixture_day is None) != (args.fixture_output is None):
        parser.error("--fixture-day and --fixture-output must be supplied together")
    report = project(args.run)
    with args.output.open("x", encoding="utf-8", newline="\n") as out:
        json.dump(report, out, ensure_ascii=False, indent=2)
        out.write("\n")
    fixture_sha = None
    if args.fixture_day is not None:
        fixture = make_regression_fixture(args.run, args.fixture_day)
        with args.fixture_output.open("x", encoding="utf-8", newline="\n") as out:
            json.dump(fixture, out, ensure_ascii=False, indent=2)
            out.write("\n")
        fixture_sha = sha256(args.fixture_output)
    print(json.dumps({
        "days": report["observed_days"],
        "exact_side_comparisons": report["conditional_exact_side_comparisons"],
        "unresolved_days": report["unresolved_days"],
        "sha256": sha256(args.output),
        "fixture_sha256": fixture_sha,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
