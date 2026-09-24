"""Shared, source-bound original battle case for film and agent calibration.

This module exposes observations, not a victory forecast.  The independent
phase-trace replay diverges numerically from the original on day 6, so callers
must not splice its event effects into the original battle's daily trajectory.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


EPISODE01_CASE_FILE = "ck3_1_19_0_6_episode01_messina_original_case.json"
EPISODE01_CASE_SHA256 = "62C70CED2E4E1E355A986C9220F05F59441EE26F14C0EE412D537383413DBF9F"
EPISODE01_PARITY_FILE = "ck3_1_19_0_6_episode01_messina_main_tick_parity.json"
EPISODE01_PARITY_SHA256 = "CE1B40AB72126C905D4B73411FBFB44141A1AA251D6A108575CDA32B019E7497"


class NativeBattleCaseError(ValueError):
    """A bundled original battle observation violates its evidence contract."""


def _validate(case: dict[str, Any]) -> None:
    if case.get("schema") != "ck3-native-battle-evidence-v1":
        raise NativeBattleCaseError("native battle case schema mismatch")
    if case.get("game_version") != "1.19.0.6" or case.get("combat_id") != 16777218:
        raise NativeBattleCaseError("native battle case identity mismatch")
    if case.get("same_random_trajectory_proven") is not False:
        raise NativeBattleCaseError("replay trajectory must remain unproven")
    if case.get("phase_trace_may_bind_to_original_daily_transition") is not False:
        raise NativeBattleCaseError("replay trace cannot bind to original daily transition")
    if case.get("planner_usable") is not False or case.get("calibrated_win_probability_available") is not False:
        raise NativeBattleCaseError("single original case cannot authorize a win probability")
    days = case.get("daily")
    traces = case.get("phase_traces")
    if not isinstance(days, list) or [row.get("day") for row in days] != list(range(1, 32)):
        raise NativeBattleCaseError("original daily sequence is incomplete")
    if not isinstance(traces, list) or [row.get("source_day") for row in traces] != list(range(4, 28)):
        raise NativeBattleCaseError("phase replay sequence is incomplete")
    first_date = case["first_date_raw"]
    if [row.get("date_raw") for row in days] != [first_date + 24 * i for i in range(31)]:
        raise NativeBattleCaseError("original daily date sequence has a gap")
    if case.get("terminal_date_raw") != first_date + 31 * 24:
        raise NativeBattleCaseError("terminal date is not the next day")
    divergence = next(
        (row["source_day"] for row in traces if row.get("replay_matches_original_day") is False),
        None,
    )
    if case.get("first_numeric_divergence_source_day") != divergence:
        raise NativeBattleCaseError("replay divergence marker disagrees with daily evidence")
    if any(row.get("readiness", {}).get("original_trace_ready") is not False for row in traces):
        raise NativeBattleCaseError("bounded traces cannot be promoted to original-trace ready")


def load_episode01_native_battle_case() -> dict[str, Any]:
    """Return one portable exact-build case used by both research consumers."""
    path = Path(__file__).with_name("data") / EPISODE01_CASE_FILE
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest().upper() != EPISODE01_CASE_SHA256:
        raise NativeBattleCaseError("bundled native case bytes changed without review")
    case = json.loads(data)
    if not isinstance(case, dict):
        raise NativeBattleCaseError("native case must be a JSON object")
    _validate(case)
    return case


def original_daily_timeline() -> tuple[dict[str, Any], ...]:
    """Return the original 31 daily observations for plots and residual checks."""
    case = load_episode01_native_battle_case()
    return tuple(case["daily"])


def load_episode01_main_tick_parity() -> dict[str, Any]:
    """Return the conditional casualty check, never an independent forecast."""
    path = Path(__file__).with_name("data") / EPISODE01_PARITY_FILE
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest().upper() != EPISODE01_PARITY_SHA256:
        raise NativeBattleCaseError("bundled main-tick parity bytes changed without review")
    report = json.loads(data)
    if not isinstance(report, dict) or report.get("schema") != "ck3-native-main-tick-conditional-parity-v1":
        raise NativeBattleCaseError("main-tick parity schema mismatch")
    if report.get("case_sha256") != EPISODE01_CASE_SHA256:
        raise NativeBattleCaseError("main-tick parity references another native case")
    if report.get("conditioned_on_native_outgoing_damage") is not True:
        raise NativeBattleCaseError("main-tick parity must declare native outgoing conditioning")
    if any(report.get(key) is not False for key in (
        "outgoing_damage_reconstructed", "phase_effects_reconstructed",
        "join_and_terminal_reconstructed", "win_probability_available",
    )):
        raise NativeBattleCaseError("conditional parity cannot advertise missing fidelity")
    rows = report.get("source_days")
    if not isinstance(rows, list) or [row.get("source_day") for row in rows] != list(range(4, 27)):
        raise NativeBattleCaseError("main-tick parity day sequence is incomplete")
    if report.get("stable_bounded_exact_days") != sum(
        row["stable_bounded_current_raw_exact"] for row in rows
    ):
        raise NativeBattleCaseError("main-tick exact-day summary disagrees with rows")
    return report


__all__ = [
    "EPISODE01_CASE_FILE",
    "EPISODE01_CASE_SHA256",
    "EPISODE01_PARITY_FILE",
    "EPISODE01_PARITY_SHA256",
    "NativeBattleCaseError",
    "load_episode01_native_battle_case",
    "load_episode01_main_tick_parity",
    "original_daily_timeline",
]
