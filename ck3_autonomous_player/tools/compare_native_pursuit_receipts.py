"""Compare three native pursuit days against the shared combat calculator.

The input is an immutable episode attempt containing terminal-replay-d28-d32
and the original term-d28..31 battle-control responses.  This tool never
starts CK3 or changes its input.  It reports conditional parity for that one
observed participant set, not a qualified whole-battle forecast.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from xar_autoplayer.simulation.combat_core import (  # noqa: E402
    CombatRegimentState,
    PursuitInitialPools,
    RegimentKind,
    apply_pursuit_day,
    apply_three_day_pursuit,
)


def _load_source(attempt: Path) -> tuple[list[tuple[dict[str, object], str]], str, dict[str, object], str]:
    index = attempt / "terminal-replay-d28-d32.jsonl"
    index_bytes = index.read_bytes()
    index_sha = hashlib.sha256(index_bytes).hexdigest().upper()
    index_rows = [json.loads(line) for line in index_bytes.decode("utf-8").splitlines()]
    require([row["day"] for row in index_rows] == [28, 29, 30, 31, 32], "index day sequence")
    result = []
    for row in index_rows[:4]:
        path = attempt / "ck3-output" / "interactive-requests-responses" / f"term-d{row['day']}-control.json"
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest().upper()
        require(digest == row["control_sha256"], f"day {row['day']} source SHA")
        response = json.loads(raw)
        require(response["result"] == "CALL_COMPLETED" and response["body"]["accepted"] is True,
                f"day {row['day']} native response")
        control = response["body"]["battle_control_snapshot"]
        require(control["combat_id"] == 16777218 and control["phase"] == "pursuit",
                f"day {row['day']} combat identity")
        require(control["observed_date_raw"] == row["date_raw"] and control["phase_day"] == row["phase_day"],
                f"day {row['day']} phase identity")
        require(control["winner_raw"] == 0 and control["attacker"]["ordered_armies"] and control["defender"]["ordered_armies"],
                f"day {row['day']} winner and participants")
        result.append((control, digest))
    require([control["phase_day"] for control, _ in result] == [0, 1, 2, 3], "three pursuit ticks")
    require([control["observed_date_raw"] for control, _ in result] == [53146896 + day * 24 for day in range(4)],
            "native one-day cadence")
    terminal_path = attempt / "ck3-output" / "interactive-requests-responses" / "term-d32-terminal.json"
    terminal_bytes = terminal_path.read_bytes()
    terminal_sha = hashlib.sha256(terminal_bytes).hexdigest().upper()
    require(terminal_sha == index_rows[4]["terminal_sha256"], "terminal source SHA")
    terminal_response = json.loads(terminal_bytes)
    require(terminal_response["result"] == "CALL_COMPLETED" and terminal_response["body"]["accepted"] is True,
            "terminal native response")
    terminal = terminal_response["body"]["battle_terminal_transition"]
    require(terminal["prior"]["terminal_kind"] == "normal_result"
            and terminal["prior"]["winner_raw"] == 0
            and terminal["observed_date_raw"] == index_rows[4]["date_raw"]
            and terminal["prior_combat_id"] == 16777218,
            "terminal identity and result")
    return result, index_sha, terminal, terminal_sha


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _entries(side: dict[str, object]) -> tuple[CombatRegimentState, ...]:
    result = []
    for key, kind in (("levy_entries", RegimentKind.LEVY),
                      ("men_at_arms_entries", RegimentKind.MEN_AT_ARMS)):
        for row in side[key]:
            require(row["bucket"] == ("levy" if kind is RegimentKind.LEVY else "men_at_arms"),
                    "entry kind")
            result.append(CombatRegimentState(
                regiment_id=row["regiment_id"], kind=kind,
                current_raw=row["current_fighting_raw"],
                soft_casualties_raw=row["soft_casualties_raw"],
                toughness_raw=row["effective_toughness_raw"],
                pursuit_raw=row["effective_pursuit_raw"],
                screen_raw=row["effective_screen_raw"],
            ))
    require(len({entry.regiment_id for entry in result}) == len(result), "unique regiment identity")
    return tuple(result)


def _modifier(control: dict[str, object], side_index: int, key: str) -> int:
    scope = control["pursuit_modifier_sides"]
    require(scope["status"] == "available" and scope["source_combat_id"] == 16777218,
            "pursuit modifier identity")
    rows = [row for row in scope["sides"] if row["side_index"] == side_index]
    require(len(rows) == 1 and type(rows[0][key]) is int, "pursuit modifier row")
    return rows[0][key]


def _native_rows(side: dict[str, object]) -> dict[int, dict[str, object]]:
    rows = side["levy_entries"] + side["men_at_arms_entries"]
    return {row["regiment_id"]: row for row in rows}


def _state_rows(entries: tuple[CombatRegimentState, ...]) -> list[dict[str, object]]:
    return [
        {
            "regiment_id": entry.regiment_id,
            "kind": entry.kind.value,
            "current_raw": entry.current_raw,
            "soft_casualties_raw": entry.soft_casualties_raw,
            "toughness_raw": entry.toughness_raw,
            "pursuit_raw": entry.pursuit_raw,
            "screen_raw": entry.screen_raw,
        }
        for entry in entries
    ]


def compare(attempt: Path) -> dict[str, object]:
    sources, index_sha, terminal, terminal_sha = _load_source(attempt)
    first_loser = _entries(sources[0][0]["defender"])
    initial_pools = PursuitInitialPools.from_entries(first_loser)
    first_pursuer = _entries(sources[0][0]["attacker"])
    chained = apply_three_day_pursuit(
        first_loser, first_pursuer, initial_pools=initial_pools,
        pursuer_efficiency_modifier_raw=_modifier(sources[0][0], 0, "pursuit_efficiency_raw"),
        retreater_loss_modifier_raw=_modifier(sources[0][0], 1, "retreat_losses_raw"),
    )
    days = []
    for index in range(3):
        before, before_sha = sources[index]
        after, after_sha = sources[index + 1]
        loser_before = _entries(before["defender"])
        loser_after = _entries(after["defender"])
        chained_after = chained.days[index].entries
        pursuer_before = _entries(before["attacker"])
        native_before = _native_rows(before["defender"])
        native_after = _native_rows(after["defender"])
        require([entry.regiment_id for entry in loser_before] == [entry.regiment_id for entry in loser_after],
                f"day {28 + index} stable loser roster")
        require(_modifier(before, 0, "pursuit_efficiency_raw") == _modifier(after, 0, "pursuit_efficiency_raw")
                and _modifier(before, 1, "retreat_losses_raw") == _modifier(after, 1, "retreat_losses_raw"),
                f"day {28 + index} stable pursuit modifiers")
        prediction = apply_pursuit_day(
            loser_before, pursuer_before, initial_pools=initial_pools,
            pursuer_efficiency_modifier_raw=_modifier(before, 0, "pursuit_efficiency_raw"),
            retreater_loss_modifier_raw=_modifier(before, 1, "retreat_losses_raw"),
        )
        rows = []
        for prior, model, observed, independent in zip(
            loser_before, prediction.entries, loser_after, chained_after, strict=True
        ):
            model_hard = prior.soft_casualties_raw - model.soft_casualties_raw
            native_hard = prior.soft_casualties_raw - observed.soft_casualties_raw
            before_hard = native_before[prior.regiment_id]["hard_casualties_raw"]
            after_hard = native_after[prior.regiment_id]["hard_casualties_raw"]
            native_hard_delta = after_hard - before_hard if type(before_hard) is int and type(after_hard) is int else None
            rows.append({
                "regiment_id": prior.regiment_id,
                "kind": prior.kind.value,
                "before_soft_raw": prior.soft_casualties_raw,
                "model_after_soft_raw": model.soft_casualties_raw,
                "native_after_soft_raw": observed.soft_casualties_raw,
                "model_pursuit_hard_raw": model_hard,
                "native_pursuit_hard_raw": native_hard,
                "native_hard_ledger_delta_raw": native_hard_delta,
                "native_hard_ledger_residual_raw": native_hard_delta - native_hard if native_hard_delta is not None else None,
                "soft_residual_raw": model.soft_casualties_raw - observed.soft_casualties_raw,
                "chained_after_soft_raw": independent.soft_casualties_raw,
                "chained_soft_residual_raw": independent.soft_casualties_raw - observed.soft_casualties_raw,
                "native_current_delta_raw": observed.current_raw - prior.current_raw,
            })
        native_owner_hard_delta = (
            after["defender"]["participant_hard_total_raw"]
            - before["defender"]["participant_hard_total_raw"]
        )
        days.append({
            "from_day": 28 + index, "to_day": 29 + index,
            "before_control_sha256": before_sha, "after_control_sha256": after_sha,
            "initial_pools": {
                "levy_soft_raw": initial_pools.levy_soft_raw,
                "men_at_arms_soft_raw": initial_pools.men_at_arms_soft_raw,
            },
            "model_intermediates_raw": {
                "toughness_soft": prediction.toughness_soft_raw,
                "pursuit_damage": prediction.pursuit_damage_raw,
                "screen": prediction.screen_raw,
                "base": prediction.base_raw,
                "minimum": prediction.minimum_raw,
                "extra": prediction.extra_raw,
                "floor_component": prediction.floor_component_raw,
            },
            "model_total_hard_raw": prediction.total_hard_raw,
            "native_total_soft_to_hard_raw": sum(row["native_pursuit_hard_raw"] for row in rows),
            "native_owner_hard_ledger_delta_raw": native_owner_hard_delta,
            "owner_hard_ledger_residual_raw": native_owner_hard_delta - prediction.total_hard_raw,
            "exact_rows": sum(row["soft_residual_raw"] == 0 for row in rows),
            "chained_exact_rows": sum(row["chained_soft_residual_raw"] == 0 for row in rows),
            "hard_ledger_rows": sum(row["native_hard_ledger_delta_raw"] is not None for row in rows),
            "exact_hard_ledger_rows": sum(row["native_hard_ledger_residual_raw"] == 0 for row in rows),
            "stable_current_rows": sum(row["native_current_delta_raw"] == 0 for row in rows),
            "row_count": len(rows),
            "rows": rows,
        })
    return {
        "schema": "ck3.native_pursuit_conditional_parity.v1",
        "game_build": "1.19.0.6",
        "combat_id": 16777218,
        "source_index_sha256": index_sha,
        "terminal_source_sha256": terminal_sha,
        "scope": "same-replay observed participants and effective stats; not independent battle prediction",
        "initial_state": {
            "retreater_entries": _state_rows(first_loser),
            "pursuer_entries": _state_rows(first_pursuer),
            "pursuer_efficiency_modifier_raw": _modifier(sources[0][0], 0, "pursuit_efficiency_raw"),
            "retreater_loss_modifier_raw": _modifier(sources[0][0], 1, "retreat_losses_raw"),
        },
        "day_count": len(days),
        "row_count": sum(day["row_count"] for day in days),
        "exact_rows": sum(day["exact_rows"] for day in days),
        "chained_exact_rows": sum(day["chained_exact_rows"] for day in days),
        "hard_ledger_rows": sum(day["hard_ledger_rows"] for day in days),
        "exact_hard_ledger_rows": sum(day["exact_hard_ledger_rows"] for day in days),
        "stable_current_rows": sum(day["stable_current_rows"] for day in days),
        "terminal": {
            "kind": terminal["prior"]["terminal_kind"],
            "winner_raw": terminal["prior"]["winner_raw"],
            "player_subject_state": terminal["successor"]["state"],
            "battle_warscore_attacker_relative_raw": terminal["prior"]["battle_warscore"]["attacker_relative_delta_raw_q100000"],
        },
        "days": days,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = compare(args.attempt)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        if args.output.exists():
            raise FileExistsError(args.output)
        args.output.write_text(rendered, encoding="utf-8")
    print(f"PURSUIT conditional parity {report['exact_rows']}/{report['row_count']}", file=sys.stderr)


if __name__ == "__main__":
    main()
