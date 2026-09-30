#!/usr/bin/env python3
"""Prepare external marriage seed files or verify already captured native frames.

This utility never starts CK3, injects a DLL, connects to a pipe, or writes a
game profile. The coordinator places seed inbox bytes into a disposable seed
profile, then executes the existing production native bridge itself.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(PACKAGE_ROOT))
from xar_autoplayer.bridge.marriage_contract import (  # noqa: E402
    arrange_marriage_step,
    normalize_arrange_marriage_choices,
    observed_marriage_status,
)

EXE_SHA256 = "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"
COST_ORDER = [
    "gold", "prestige", "piety", "renown", "influence", "herd", "treasury",
    "treasury_or_gold", "merit", "barter_goods",
]
GUARD = "xar_migration_12002_marriage_seed_consumed"
CANDIDATE_VARIABLE = "xar_migration_12002_marriage_candidate"


def seed_source(case: str) -> str:
    age = 25 if case == "adult" else 12
    # Stock 1.20 create_character accepts age ranges and faith/rite identities.
    # Divorce is confined to the disposable seed save. The candidate is never
    # married or betrothed by script; that is exclusively the tested command.
    def create(gender: str) -> str:
        return (
            "\t\tcreate_character = {\n"
            f"\t\t\tage = {{ {age} {age} }}\n"
            f"\t\t\tgender = {gender}\n"
            "\t\t\tdynasty = none\n"
            "\t\t\trandom_traits = no\n"
            "\t\t\tculture = root.culture\n"
            "\t\t\tfaith = root.faith\n"
            "\t\t\trite = root.rite\n"
            "\t\t\tlocation = root.capital_province\n"
            "\t\t\temployer = root\n"
            "\t\t\tsave_scope_as = xar_migration_12002_candidate\n"
            "\t\t}\n"
        )
    return (
        "# Disposable 1.20.0.2 seed profile only. Console run root is GetPlayer.\n"
        "if = {\n"
        "\tlimit = {\n"
        "\t\tis_ai = no\n"
        "\t\tis_adult = yes\n"
        "\t\tis_ruler = yes\n"
        "\t\texists = capital_province\n"
        f"\t\tNOT = {{ global_var:{GUARD} = 1 }}\n"
        "\t}\n"
        f"\tset_global_variable = {{ name = {GUARD} value = 1 }}\n"
        "\tif = {\n"
        "\t\tlimit = { exists = betrothed }\n"
        "\t\tbreak_betrothal = betrothed\n"
        "\t}\n"
        "\tevery_spouse = { root = { divorce = prev } }\n"
        "\tif = {\n"
        "\t\tlimit = { is_female = no }\n"
        + create("female") +
        "\t}\n"
        "\telse = {\n"
        + create("male") +
        "\t}\n"
        "\tset_global_variable = {\n"
        f"\t\tname = {CANDIDATE_VARIABLE}\n"
        "\t\tvalue = scope:xar_migration_12002_candidate\n"
        "\t}\n"
        f'\tdebug_log = "XAR_FIXTURE:MARRIAGE_12002_SEED|case={case}|age={age}'
        f"|player_id=[GetPlayer.GetID]|candidate_id=[GetGlobalVariable('{CANDIDATE_VARIABLE}').Char.GetID]" + '"\n'
        "}\n"
    )


def materialize(output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    files = []
    for case in ("adult", "child"):
        path = output / f"seed-{case}.txt"
        path.write_text(seed_source(case), encoding="utf-8-sig", newline="\n")
        files.append({
            "case": case,
            "path": str(path.resolve()),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper(),
            "expected_relationship": "accepted_marriage" if case == "adult" else "accepted_betrothal",
            "candidate_age": 25 if case == "adult" else 12,
        })
    noop = output / "seed-noop.txt"
    noop.write_text("# Marriage fixture seed inbox: no effects.\n", encoding="utf-8-sig")
    reset = output / "reset-seed-guard.txt"
    reset.write_text(
        "# Disposable fixture only: permits the next adult/child seed.\n"
        "if = {\n"
        f"\tlimit = {{ is_ai = no exists = global_var:{GUARD} }}\n"
        f"\tremove_global_variable = {GUARD}\n"
        '\tdebug_log = "XAR_FIXTURE:MARRIAGE_12002_GUARD_RESET"\n'
        "}\n", encoding="utf-8-sig", newline="\n",
    )
    result = {
        "schema": 1,
        "kind": "ck3_12002_marriage_fixture_files",
        "status": "prepared_not_live",
        "game_version": "1.20.0.2",
        "executable_sha256": EXE_SHA256,
        "files": files,
        "seed_inbox_relative_path": "run/xar_mcp_inbox.txt",
        "query_step": "query-arrange-marriage-choices",
        "submit_step_template": "arrange-marriage-{played_character_id}-{candidate_character_id}",
        "native_probe_entry": "xar::ck3_12002::CollectMarriageProbe12002",
        "cost_order": COST_ORDER,
        "observations": ["before.json", "choices.json", "submission.json", "after.json"],
        "optional_observations": ["native-probe-before.json", "native-probe-after.json", "cold-after.json"],
        "sequential_seed_reset": str(reset.resolve()),
        "payment_scope": "native on-send cost; same-court same-identity seed normally evaluates all ten costs to zero",
    }
    (output / "fixture-manifest.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8-sig",
    )
    return result


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _state(frame: dict[str, Any]) -> dict[str, Any]:
    value = frame.get("state", frame)
    if not isinstance(value, dict):
        raise ValueError("snapshot state must be an object")
    return value


def _result(frame: dict[str, Any]) -> dict[str, Any]:
    value = frame.get("result", frame)
    if not isinstance(value, dict):
        raise ValueError("command result must be an object")
    return value


def _integer(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    return value


def verify_capture(
    before: dict[str, Any], query: dict[str, Any], submission: dict[str, Any],
    after: dict[str, Any], *, player: int, candidate: int,
    expected: str, probe: dict[str, Any] | None = None,
    cold_after: dict[str, Any] | None = None,
) -> dict[str, Any]:
    before_state, after_state = _state(before), _state(after)
    for label, state in (("before", before_state), ("after", after_state)):
        if state.get("paused") is not True or state.get("map_ready") is not True:
            raise ValueError(f"{label} snapshot must be paused and map-ready")
        character = state.get("played_character")
        if not isinstance(character, dict) or character.get("character_id") != player:
            raise ValueError(f"{label} snapshot belongs to another player")
    if observed_marriage_status(before_state["played_character"], played_character_id=player,
                                candidate_character_id=candidate) is not None:
        raise ValueError("candidate already has the expected relationship before submission")
    query_result = _result(query)
    if query_result.get("accepted") is not True or query_result.get("status") != "available":
        raise ValueError("candidate query was not available")
    choices = normalize_arrange_marriage_choices(query_result.get("arrange_marriage_choices"))
    selected_id = f"{player}-{candidate}"
    if not any(row["choice_id"] == selected_id for row in choices):
        raise ValueError("seed candidate is absent from native legal choices")
    command = _result(submission)
    if command.get("accepted") is not True or command.get("status") != "submitted":
        raise ValueError("native queue did not report proposal submitted")
    if command.get("step") != arrange_marriage_step(selected_id):
        raise ValueError("submitted command does not identify the seed candidate")
    observed = observed_marriage_status(after_state["played_character"], played_character_id=player,
                                       candidate_character_id=candidate)
    if observed != expected:
        raise ValueError(f"expected {expected}, observed {observed!r}; an ACK is not the postcondition")
    if expected == "accepted_marriage" and before_state["played_character"].get("spouse_ids") == []:
        if after_state["played_character"].get("primary_spouse_id") != candidate:
            raise ValueError("first marriage did not populate primary_spouse_id")
    if expected == "accepted_betrothal" and candidate in after_state["played_character"].get("spouse_ids", []):
        raise ValueError("child betrothal candidate unexpectedly appears in spouse_ids")
    if cold_after is not None:
        cold_state = _state(cold_after)
        cold_observed = observed_marriage_status(cold_state.get("played_character"),
            played_character_id=player, candidate_character_id=candidate)
        if cold_observed != expected:
            raise ValueError("marriage relationship did not survive the coordinator's cold load")
        if cold_state.get("paused") is not True or cold_state.get("map_ready") is not True:
            raise ValueError("cold restored snapshot must be paused and map-ready")
        if cold_state.get("date_raw") != after_state.get("date_raw"):
            raise ValueError("cold restored date differs from the paused saved relationship frame")
        if expected == "accepted_marriage" and before_state["played_character"].get("spouse_ids") == []:
            if cold_state["played_character"].get("primary_spouse_id") != candidate:
                raise ValueError("first primary spouse did not survive cold restore")
        if expected == "accepted_betrothal" and candidate in cold_state["played_character"].get("spouse_ids", []):
            raise ValueError("cold child betrothal candidate unexpectedly appears in spouse_ids")
    costs: list[int] | None = None
    native_row: dict[str, Any] | None = None
    if probe is not None:
        # Accept the diagnostic body or the captured private command envelope.
        probe = _result(probe)
        nested_probe = probe.get("marriage_native_diagnostic")
        if isinstance(nested_probe, dict):
            probe = nested_probe
        if probe.get("executable_sha256") != EXE_SHA256 or probe.get("query_status") != "available":
            raise ValueError("private native probe is not bound to the available new-build query")
        if probe.get("played_character_id") != player or probe.get("paused") is not True:
            raise ValueError("private probe is not the selected paused player")
        if probe.get("date_raw") != before_state.get("date_raw"):
            raise ValueError("private pre-submit probe date differs from the public before snapshot")
        if probe.get("cost_order") != COST_ORDER:
            raise ValueError("private probe cost ordinals differ from the exact-build evaluator")
        rows = probe.get("marriage_candidate_evaluations")
        if not isinstance(rows, list):
            raise ValueError("private probe is missing evaluations")
        native_row = next((row for row in rows if isinstance(row, dict) and
            row.get("played_character_id") == player and row.get("candidate_character_id") == candidate), None)
        if native_row is None or native_row.get("native_legal") is not True:
            raise ValueError("private probe did not evaluate the native legal seed candidate")
        if not isinstance(native_row.get("native_auto_accept"), bool):
            raise ValueError("native auto-accept result is unobserved")
        for name in ("recipient_acceptance_score_raw", "intermediary_acceptance_score_raw"):
            _integer(native_row.get(name), name)
        if native_row.get("raw_scale") != 100_000:
            raise ValueError("native score/cost scale differs from the exact-build contract")
        costs = native_row.get("send_costs_raw")
        if not isinstance(costs, list) or len(costs) != 10:
            raise ValueError("private probe must observe all ten native send costs")
        for index, cost in enumerate(costs):
            _integer(cost, f"send_costs_raw[{index}]")
    return {
        "schema": 1, "kind": "ck3_12002_marriage_capture_verification",
        "status": "PASS", "played_character_id": player, "candidate_character_id": candidate,
        "choice_id": selected_id, "relationship_result": observed,
        "before_date_raw": before_state.get("date_raw"), "after_date_raw": after_state.get("date_raw"),
        "cold_load_result_observed": cold_after is not None,
        "native_evaluations_observed": probe is not None,
        "native_evaluation": native_row,
        "send_costs_raw": costs,
        "payment_result": "not_measured_by_relationship_frames",
        "payment_note": "on-send costs are evaluated; relationship and net prestige changes alone cannot prove a resource debit",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    prepare = sub.add_parser("materialize")
    prepare.add_argument("--output", type=Path, required=True)
    verify = sub.add_parser("verify")
    for name in ("before", "choices", "submission", "after"):
        verify.add_argument(f"--{name}", type=Path, required=True)
    verify.add_argument("--player", type=int, required=True)
    verify.add_argument("--candidate", type=int, required=True)
    verify.add_argument("--expected", choices=("accepted_marriage", "accepted_betrothal"), required=True)
    verify.add_argument("--probe", type=Path)
    verify.add_argument("--cold-after", type=Path)
    verify.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.operation == "materialize":
        result = materialize(args.output)
    else:
        try:
            result = verify_capture(_read(args.before), _read(args.choices), _read(args.submission),
                _read(args.after), player=args.player, candidate=args.candidate, expected=args.expected,
                probe=_read(args.probe) if args.probe else None,
                cold_after=_read(args.cold_after) if args.cold_after else None)
        except (ValueError, KeyError) as error:
            result = {"schema": 1, "kind": "ck3_12002_marriage_capture_verification", "status": "FAIL", "reason": str(error)}
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8-sig")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
