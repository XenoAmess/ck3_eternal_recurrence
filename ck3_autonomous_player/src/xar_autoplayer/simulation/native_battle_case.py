"""Shared, source-bound original battle case for film and agent calibration.

This module exposes observations, not a victory forecast.  The independent
phase-trace replay diverges numerically from the original on day 6, so callers
must not splice its event effects into the original battle's daily trajectory.
"""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from pathlib import Path
from typing import Any


EPISODE01_CASE_FILE = "ck3_1_19_0_6_episode01_messina_original_case.json"
EPISODE01_CASE_SHA256 = "62C70CED2E4E1E355A986C9220F05F59441EE26F14C0EE412D537383413DBF9F"
EPISODE01_PARITY_FILE = "ck3_1_19_0_6_episode01_messina_main_tick_parity.json"
EPISODE01_PARITY_SHA256 = "CE1B40AB72126C905D4B73411FBFB44141A1AA251D6A108575CDA32B019E7497"
EPISODE01_REPEATABILITY_FILE = "ck3_1_19_0_6_episode01_messina_repeatability.json"
EPISODE01_REPEATABILITY_SHA256 = "5E2D4B1AEE3BD6D64AC48111CD7ED1D8F48B8827D9FEBAB3F04505F3F2C1EF9C"
EPISODE01_PHASE_EVENT_FILE = "ck3_1_19_0_6_episode01_messina_phase_event_observations.json"
EPISODE01_PHASE_EVENT_SHA256 = "94831B16AE56BC050833D7BEE9064170D118F77700DE672A0977E68F47C98AAE"
EPISODE01_PHASE_EVENT_SAVE_FILE = "ck3_1_19_0_6_episode01_messina_phase_event_save_feedback.json"
EPISODE01_PHASE_EVENT_SAVE_SHA256 = "42C495789167F27F330D40FE657CEE359C02AF5FF217DFCB16E9A2971ECAC130"
EPISODE01_JOIN_DAY_FILE = "ck3_1_19_0_6_episode01_messina_join_day_casualties.json"
EPISODE01_JOIN_DAY_SHA256 = "C51A17070A66729C00B1BB1ADB40821CB61CAC1F7DF11155CE25FE0C5152EA72"
EPISODE01_JOIN_KERNEL_FILE = "ck3_1_19_0_6_episode01_messina_join_day_kernel_parity.json"
EPISODE01_JOIN_KERNEL_SHA256 = "CCD25D31E068658A78603F772BCA57B6B657A5F3C72DD404808BE48BE5B648E0"
EPISODE01_JOIN_KERNEL_V2_FILE = "ck3_1_19_0_6_episode01_messina_join_day_kernel_parity_v2.json"
EPISODE01_JOIN_KERNEL_V2_SHA256 = "B3660C52B27FD6D2186E0AB7590CE64C24720262A1BCCB3DCA8F2FB622DA5571"
EPISODE01_EVENT_REGIMENT_FILE = "ck3_1_19_0_6_episode01_messina_phase_event_regiment_feedback.json"
EPISODE01_EVENT_REGIMENT_SHA256 = "C32350EF7AE635A3E554761077100210A2F402BEB354218E640E7EA5B74D1A55"


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


def _validate_repeatability(report: dict[str, Any]) -> None:
    if report.get("schema") != "ck3-native-battle-repeatability-evidence-v1":
        raise NativeBattleCaseError("battle repeatability schema mismatch")
    if (report.get("game_version") != "1.19.0.6"
            or report.get("combat_id") != 16777218
            or report.get("player_cunit_id") != 18
            or report.get("player_combat_side_raw") != 1):
        raise NativeBattleCaseError("battle repeatability identity mismatch")
    if any(report.get(key) is not False for key in (
        "independent_random_draws_proven", "calibrated_win_probability_available",
        "planner_usable",
    )):
        raise NativeBattleCaseError("three replays cannot authorize a win percentage")
    trials = report.get("trials")
    if not isinstance(trials, list) or [row.get("trial") for row in trials] != [1, 2, 3]:
        raise NativeBattleCaseError("repeatability trials are missing")
    for number, trial in enumerate(trials, 1):
        if trial.get("mode") != (
            "live_continuation_after_contact_save" if number == 1 else "checkpoint_restore"
        ):
            raise NativeBattleCaseError("repeatability trial mode mismatch")
        if (trial.get("first_date_raw") != 53146248
                or trial.get("terminal_date_raw") != 53146992
                or trial.get("winner_side_raw") != 0
                or trial.get("player_won") is not False):
            raise NativeBattleCaseError("repeatability terminal outcome mismatch")
        days = trial.get("daily")
        if not isinstance(days, list) or [row.get("day") for row in days] != list(range(1, 32)):
            raise NativeBattleCaseError("repeatability daily sequence has a gap")
        if [row.get("date_raw") for row in days] != [53146248 + 24 * index for index in range(31)]:
            raise NativeBattleCaseError("repeatability daily dates have a gap")
    pairs = report.get("pairwise_divergence")
    if not isinstance(pairs, list) or [
        (row.get("left_trial"), row.get("right_trial"),
         row.get("first_regiment_current_divergence_day"))
        for row in pairs
    ] != [(1, 2, 6), (1, 3, 6), (2, 3, 6)]:
        raise NativeBattleCaseError("repeatability trajectory divergence mismatch")


def load_episode01_native_battle_repeatability() -> dict[str, Any]:
    """Return three observed trajectories, never a calibrated probability."""
    path = Path(__file__).with_name("data") / EPISODE01_REPEATABILITY_FILE
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest().upper() != EPISODE01_REPEATABILITY_SHA256:
        raise NativeBattleCaseError("bundled repeatability bytes changed without review")
    report = json.loads(data)
    if not isinstance(report, dict):
        raise NativeBattleCaseError("repeatability report must be a JSON object")
    _validate_repeatability(report)
    return report


def _validate_phase_event_observations(report: dict[str, Any]) -> None:
    if (report.get("schema") != "ck3-native-phase-event-observations-v2"
            or report.get("game_version") != "1.19.0.6"
            or report.get("combat_id") != 16777218
            or report.get("phase_trace_trajectory") !=
            "independent-replay-from-original-contact-checkpoint"):
        raise NativeBattleCaseError("phase-event observation identity mismatch")
    if (report.get("complete_effect_feedback_proven") is not False
            or report.get("planner_usable") is not False):
        raise NativeBattleCaseError("phase-event ledger cannot authorize effect parity")
    rows = report.get("event_fire_pairs")
    if (not isinstance(rows, list)
            or [row.get("source_day") for row in rows] != [5, 7, 9, 15, 16, 19]
            or report.get("battle_event_row_count") != 6):
        raise NativeBattleCaseError("phase-event observation sequence mismatch")
    for row in rows:
        if (len(row.get("appended_battle_events", [])) != 1
                or row.get("full_mutable_transition_bundle_complete") is not False
                or row.get("battle_event_append_observed") is not True
                or row.get("complete_effect_feedback_proven") is not False
                or row.get("observed_character_core_deltas_within_fire") != []
                or row.get("observed_accolade_deltas_within_fire") != []):
            raise NativeBattleCaseError("phase-event fire evidence was promoted")


def load_episode01_phase_event_observations() -> dict[str, Any]:
    """Return observed ledger appends and bounded core snapshots, not effects."""
    path = Path(__file__).with_name("data") / EPISODE01_PHASE_EVENT_FILE
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest().upper() != EPISODE01_PHASE_EVENT_SHA256:
        raise NativeBattleCaseError("bundled phase-event bytes changed without review")
    report = json.loads(data)
    if not isinstance(report, dict):
        raise NativeBattleCaseError("phase-event observations must be a JSON object")
    _validate_phase_event_observations(report)
    return report


def _validate_phase_event_save_feedback(report: dict[str, Any]) -> None:
    if (report.get("schema") != "ck3-native-phase-event-save-feedback-v2"
            or report.get("game_version") != "1.19.0.6"
            or report.get("combat_id") != 16777218
            or report.get("rakaly_version") != "0.8.19"
            or report.get("rakaly_exe_sha256") !=
            "E154AF990AAED2C2F44284946772188C9749AD3F6B641B41F6C23456A6F1633D"):
        raise NativeBattleCaseError("phase-event save evidence identity mismatch")
    if any(report.get(key) is not False for key in (
        "full_effect_write_set_proven", "calibrated_win_probability_available", "planner_usable",
    )):
        raise NativeBattleCaseError("save state changes do not authorize effect parity")
    rows = report.get("event_save_pairs")
    if not isinstance(rows, list) or [row.get("event_source_day") for row in rows] != [5, 7, 9, 15, 16, 19]:
        raise NativeBattleCaseError("phase-event save pairs missing")
    by_day = {row["event_source_day"]: row for row in rows}
    wound, killed = by_day[5], by_day[15]
    for row in rows:
        saves = row.get("saves")
        if (not isinstance(saves, list)
                or [save.get("source_day") for save in saves] !=
                [row["event_source_day"], row["event_source_day"] + 1]
                or saves[1].get("date_raw") != row.get("event_native_date_raw")
                or row.get("full_effect_write_set_proven") is not False
                or row.get("effect_was_only_possible_cause_proven") is not False):
            raise NativeBattleCaseError("phase-event save date or gate mismatch")
    if (wound["target_core_observations"]["same_fire_after"]["prowess"] != 8
            or wound["target_core_observations"]["next_source_day_record0"]["prowess"] != 8
            or wound["target_core_observations"]["next_source_day_record2"]["prowess"] != 6):
        raise NativeBattleCaseError("cached prowess observation mismatch")
    for day, target_id, opponent_id, event_key, prestige_gain, prowess_gain in (
        (5, 36303, 34867, "knight_wounded_by_enemy", Decimal("75"), 1),
        (7, 43706, 54140, "knight_wounded_by_enemy", Decimal("37.5"), 1),
        (9, 54144, 34867, "knight_wounded_by_enemy", Decimal("37.5"), 0),
        (15, 36673, 32716, "knight_killed_by_enemy", Decimal("300"), 1),
        (16, 33437, 54144, "knight_wounded_by_enemy", Decimal("75"), 1),
        (19, 30784, 35124, "knight_wounded_by_enemy", Decimal("75"), 0),
    ):
        row = by_day[day]
        target_before, target_after = (save["character"] for save in row["saves"])
        before, after = (save["opponent_character"] for save in row["saves"])
        if (row.get("target_character_id") != target_id
                or row.get("event_key") != event_key
                or target_before.get("character_id") != target_id
                or target_after.get("character_id") != target_id
                or row.get("opponent_character_id") != opponent_id
                or before.get("character_id") != opponent_id
                or after.get("character_id") != opponent_id
                or after.get("base_skill_values", [None])[-1]
                - before.get("base_skill_values", [None])[-1] != prowess_gain
                or Decimal(after["prestige_currency"]) - Decimal(before["prestige_currency"]) != prestige_gain
                or Decimal(row.get("opponent_prestige_currency_delta", "0")) != prestige_gain
                or row.get("opponent_base_prowess_delta") != prowess_gain):
            raise NativeBattleCaseError("opponent prestige or base prowess save observation mismatch")
        accumulated_available = (before["prestige_accumulated"] is not None
                                 and after["prestige_accumulated"] is not None)
        if accumulated_available != (day != 16):
            raise NativeBattleCaseError("opponent accumulated prestige availability mismatch")
        if (accumulated_available
                and Decimal(after["prestige_accumulated"])
                - Decimal(before["prestige_accumulated"]) != prestige_gain):
            raise NativeBattleCaseError("opponent accumulated prestige save observation mismatch")
        if event_key == "knight_wounded_by_enemy":
            if (target_before["wounded_rank"] != 0
                    or target_after["wounded_rank"] != 1
                    or target_before["alive_data_present"] is not True
                    or target_after["alive_data_present"] is not True):
                raise NativeBattleCaseError("wound save observation mismatch")
        elif (target_before["alive_data_present"] is not True
              or target_after["dead_data_present"] is not True
              or target_after["death_reason"] != "death_battle"
              or target_after["killer_character_id"] != opponent_id):
            raise NativeBattleCaseError("death save observation mismatch")


def load_episode01_phase_event_save_feedback() -> dict[str, Any]:
    """Return same-date original save state changes without full effect parity."""
    path = Path(__file__).with_name("data") / EPISODE01_PHASE_EVENT_SAVE_FILE
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest().upper() != EPISODE01_PHASE_EVENT_SAVE_SHA256:
        raise NativeBattleCaseError("bundled phase-event save bytes changed without review")
    report = json.loads(data)
    if not isinstance(report, dict):
        raise NativeBattleCaseError("phase-event save evidence must be an object")
    _validate_phase_event_save_feedback(report)
    return report


def _validate_join_day_casualties(report: dict[str, Any]) -> None:
    if (report.get("schema") != "ck3-native-join-day-casualty-observation-v1"
            or report.get("game_version") != "1.19.0.6"
            or report.get("combat_id") != 16777218
            or report.get("rakaly_exe_sha256") !=
            "E154AF990AAED2C2F44284946772188C9749AD3F6B641B41F6C23456A6F1633D"
            or report.get("same_day_reinforcement_damage_observed") is not True
            or report.get("global_manager_order_proven") is not False
            or report.get("planner_usable") is not False):
        raise NativeBattleCaseError("join-day evidence identity or boundary mismatch")
    rows = report.get("join_observations")
    if not isinstance(rows, list) or len(rows) != 2:
        raise NativeBattleCaseError("join-day pair count mismatch")
    for row, source_day, arrival_day, army_id, date_raw, fighting_count in zip(
        rows,
        (11, 21), (12, 22), (22, 28), (53146512, 53146752), (12, 5),
        strict=True,
    ):
        if (row.get("source_day") != source_day
                or row.get("arrival_day") != arrival_day
                or row.get("army_id") != army_id
                or row.get("combat_id") != 16777218
                or row.get("arrival_phase_date_raw") != date_raw
                or row.get("arrival_day_casualties_observed") is not True
                or row.get("source_day_whole_trace_available") is not False
                or row.get("global_manager_order_proven") is not False):
            raise NativeBattleCaseError("join-day row identity or gate mismatch")
        snapshots = row.get("snapshots")
        if (not isinstance(snapshots, list) or len(snapshots) != 2
                or snapshots[0].get("phase") != "before"
                or snapshots[1].get("phase") != "after"
                or snapshots[0].get("in_combat") is not False
                or snapshots[1].get("in_combat") is not True
                or snapshots[1].get("date_raw") != date_raw):
            raise NativeBattleCaseError("join-day arrival snapshot mismatch")
        regiments = row.get("regiments")
        if (not isinstance(regiments, list)
                or len(regiments) != (13 if source_day == 11 else 5)
                or sum(regiment.get("fights_in_main_phase") is True for regiment in regiments)
                != fighting_count
                or row.get("fighting_regiment_count") != fighting_count):
            raise NativeBattleCaseError("join-day regiment roster mismatch")
        for regiment in regiments:
            if regiment.get("prejoin_saved_current_raw") != regiment.get("arrival_day_starting_raw"):
                raise NativeBattleCaseError("join-day starting strength mismatch")
            if regiment.get("fights_in_main_phase") is True:
                soft = regiment.get("arrival_day_soft_casualties_raw")
                hard = regiment.get("arrival_day_hard_casualties_raw")
                if (not isinstance(soft, int) or not isinstance(hard, int)
                        or soft + hard <= 0
                        or soft + hard != regiment["prejoin_saved_current_raw"]
                        - regiment["arrival_day_current_fighting_raw"]):
                    raise NativeBattleCaseError("join-day casualty arithmetic mismatch")


def load_episode01_join_day_casualties() -> dict[str, Any]:
    """Return two observed same-date arrival/damage pairs, not universal order."""
    path = Path(__file__).with_name("data") / EPISODE01_JOIN_DAY_FILE
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest().upper() != EPISODE01_JOIN_DAY_SHA256:
        raise NativeBattleCaseError("bundled join-day evidence bytes changed without review")
    report = json.loads(data)
    if not isinstance(report, dict):
        raise NativeBattleCaseError("join-day evidence must be a JSON object")
    _validate_join_day_casualties(report)
    return report


def _validate_join_day_kernel_parity(report: dict[str, Any]) -> None:
    if (report.get("schema") != "ck3-native-join-day-conditional-casualty-parity-v1"
            or report.get("case_sha256") != EPISODE01_CASE_SHA256
            or report.get("join_evidence_sha256") != EPISODE01_JOIN_DAY_SHA256
            or report.get("game_version") != "1.19.0.6"
            or report.get("combat_id") != 16777218
            or report.get("trajectory") != "independent-replay-from-original-contact-checkpoint"
            or report.get("conditioned_on_native_outgoing_damage") is not True
            or report.get("conditioned_on_observed_joined_roster") is not True):
        raise NativeBattleCaseError("join-day kernel parity identity or conditioning mismatch")
    if any(report.get(key) is not False for key in (
        "outgoing_damage_reconstructed", "join_policy_reconstructed",
        "whole_battle_win_probability_available", "planner_usable",
    )):
        raise NativeBattleCaseError("conditional join-day parity cannot authorize a forecast")
    rows = report.get("source_days")
    if not isinstance(rows, list) or len(rows) != 2:
        raise NativeBattleCaseError("join-day kernel parity pair count mismatch")
    for row, source_day, arrival_day, army_id, old_count, joined_count in zip(
        rows, (11, 21), (12, 22), (22, 28), (26, 37), (12, 5), strict=True,
    ):
        if (row.get("source_day") != source_day
                or row.get("arrival_day") != arrival_day
                or row.get("army_id") != army_id
                or row.get("old_fighting_regiment_count") != old_count
                or row.get("joined_fighting_regiment_count") != joined_count
                or row.get("joined_regiment_current_exact_count") != joined_count
                or row.get("all_joined_regiments_current_exact") is not True
                or row.get("source_day_whole_trace_available") is not False):
            raise NativeBattleCaseError("join-day kernel parity row mismatch")
        residuals = row.get("residuals")
        if (residuals != ([{"regiment_id": 220, "newly_joined": False,
                            "predicted_minus_native_raw": 214}] if source_day == 11 else [])
                or row.get("whole_side_current_exact") is not (source_day == 21)):
            raise NativeBattleCaseError("join-day residual was hidden or changed")


def load_episode01_join_day_kernel_parity() -> dict[str, Any]:
    """Return conditional joined-roster casualty parity, never a battle forecast."""
    path = Path(__file__).with_name("data") / EPISODE01_JOIN_KERNEL_FILE
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest().upper() != EPISODE01_JOIN_KERNEL_SHA256:
        raise NativeBattleCaseError("bundled join-day parity bytes changed without review")
    report = json.loads(data)
    if not isinstance(report, dict):
        raise NativeBattleCaseError("join-day parity must be a JSON object")
    _validate_join_day_kernel_parity(report)
    return report


def _validate_join_day_kernel_parity_v2(report: dict[str, Any]) -> None:
    if (report.get("schema") != "ck3-native-join-day-conditional-casualty-parity-v2"
            or report.get("case_sha256") != EPISODE01_CASE_SHA256
            or report.get("join_evidence_sha256") != EPISODE01_JOIN_DAY_SHA256
            or report.get("game_version") != "1.19.0.6"
            or report.get("combat_id") != 16777218
            or report.get("trajectory") != "independent-replay-from-original-contact-checkpoint"):
        raise NativeBattleCaseError("join-day refreshed parity identity mismatch")
    if any(report.get(key) is not True for key in (
        "conditioned_on_native_outgoing_damage", "conditioned_on_observed_joined_roster",
        "conditioned_on_native_pre_schedule_effective_toughness",
    )) or any(report.get(key) is not False for key in (
        "outgoing_damage_reconstructed", "join_policy_reconstructed",
        "effective_toughness_refresh_reconstructed", "whole_battle_win_probability_available",
        "planner_usable",
    )):
        raise NativeBattleCaseError("refreshed parity conditioning or forecast gate mismatch")
    rows = report.get("source_days")
    if not isinstance(rows, list) or len(rows) != 2:
        raise NativeBattleCaseError("refreshed parity pair count mismatch")
    for row, source_day, arrival_day, army_id, old_count, joined_count in zip(
        rows, (11, 21), (12, 22), (22, 28), (26, 37), (12, 5), strict=True,
    ):
        if (row.get("source_day") != source_day
                or row.get("arrival_day") != arrival_day
                or row.get("army_id") != army_id
                or row.get("old_fighting_regiment_count") != old_count
                or row.get("joined_fighting_regiment_count") != joined_count
                or row.get("joined_regiment_current_exact_count") != joined_count
                or row.get("all_joined_regiments_current_exact") is not True
                or row.get("whole_side_current_exact") is not True
                or row.get("residuals") != []
                or row.get("source_day_whole_trace_available") is not False
                or row.get("pre_schedule_boundary") !=
                "native_capture_before_side0_schedule_call_0x27FB58F"
                or row.get("pre_schedule_capture_failure_flags") != 0):
            raise NativeBattleCaseError("refreshed parity row or pre-schedule boundary mismatch")
        changes = ([{"regiment_id": 220, "control_toughness_raw": 7400000,
                     "pre_schedule_toughness_raw": 3700000}]
                   if source_day == 11 else [])
        if row.get("old_regiment_effective_toughness_changes") != changes:
            raise NativeBattleCaseError("pre-schedule toughness change mismatch")


def load_episode01_join_day_kernel_parity_v2() -> dict[str, Any]:
    """Return native pre-schedule toughness-conditioned parity for two joins."""
    path = Path(__file__).with_name("data") / EPISODE01_JOIN_KERNEL_V2_FILE
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest().upper() != EPISODE01_JOIN_KERNEL_V2_SHA256:
        raise NativeBattleCaseError("bundled refreshed parity bytes changed without review")
    report = json.loads(data)
    if not isinstance(report, dict):
        raise NativeBattleCaseError("refreshed parity must be a JSON object")
    _validate_join_day_kernel_parity_v2(report)
    return report


def _validate_phase_event_regiment_feedback(report: dict[str, Any]) -> None:
    if (report.get("schema") != "ck3-native-phase-event-regiment-feedback-v1"
            or report.get("game_version") != "1.19.0.6"
            or report.get("combat_id") != 16777218
            or report.get("trajectory") != "independent-replay-from-original-contact-checkpoint"
            or report.get("case_sha256") != EPISODE01_CASE_SHA256
            or report.get("phase_event_sha256") != EPISODE01_PHASE_EVENT_SHA256
            or report.get("phase_event_save_sha256") != EPISODE01_PHASE_EVENT_SAVE_SHA256
            or report.get("join_kernel_initial_sha256") != EPISODE01_JOIN_KERNEL_SHA256
            or report.get("join_kernel_refreshed_sha256") != EPISODE01_JOIN_KERNEL_V2_SHA256
            or report.get("wound_event_source_day") != 9
            or report.get("wound_character_id") != 54144
            or report.get("wound_regiment_id") != 220
            or report.get("same_date_later_save_wounded_rank") != 1):
        raise NativeBattleCaseError("phase-event regiment feedback identity mismatch")
    if any(report.get(key) is not False for key in (
        "event_unique_cause_proven", "full_effect_write_set_proven",
        "source_day_11_whole_trace_available", "effective_stat_refresh_reconstructed",
        "planner_usable",
    )):
        raise NativeBattleCaseError("event-regiment observation cannot authorize a model")
    stages = report.get("stages")
    if (not isinstance(stages, list) or len(stages) != 4
            or [(row.get("source_day"), row.get("record_index")) for row in stages]
            != [(9, 2), (10, 0), (10, 2), (11, 0)]
            or [(row.get("prowess"), row.get("effective_toughness_raw")) for row in stages]
            != [(4, 7400000), (4, 7400000), (2, 7400000), (2, 3700000)]
            or [row.get("effective_damage_raw") for row in stages]
            != [37000000, 37000000, 37000000, 18500000]
            or any(row.get("character_id") != 54144 or row.get("regiment_id") != 220
                   or row.get("capture_failure_flags") != 0 for row in stages)):
        raise NativeBattleCaseError("event-regiment stage sequence mismatch")
    if (report.get("day_11_initial_conditional_residual_raw") != 214
            or report.get("day_11_refreshed_conditional_residual_raw") != 0):
        raise NativeBattleCaseError("event-regiment residual was hidden or changed")


def load_episode01_phase_event_regiment_feedback() -> dict[str, Any]:
    """Return one observed wound/prowess/entry-stat sequence, not unique cause."""
    path = Path(__file__).with_name("data") / EPISODE01_EVENT_REGIMENT_FILE
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest().upper() != EPISODE01_EVENT_REGIMENT_SHA256:
        raise NativeBattleCaseError("bundled event-regiment feedback bytes changed without review")
    report = json.loads(data)
    if not isinstance(report, dict):
        raise NativeBattleCaseError("event-regiment feedback must be a JSON object")
    _validate_phase_event_regiment_feedback(report)
    return report


__all__ = [
    "EPISODE01_CASE_FILE",
    "EPISODE01_CASE_SHA256",
    "EPISODE01_PARITY_FILE",
    "EPISODE01_PARITY_SHA256",
    "EPISODE01_REPEATABILITY_FILE",
    "EPISODE01_REPEATABILITY_SHA256",
    "EPISODE01_PHASE_EVENT_FILE",
    "EPISODE01_PHASE_EVENT_SHA256",
    "EPISODE01_PHASE_EVENT_SAVE_FILE",
    "EPISODE01_PHASE_EVENT_SAVE_SHA256",
    "EPISODE01_JOIN_DAY_FILE",
    "EPISODE01_JOIN_DAY_SHA256",
    "EPISODE01_JOIN_KERNEL_FILE",
    "EPISODE01_JOIN_KERNEL_SHA256",
    "EPISODE01_JOIN_KERNEL_V2_FILE",
    "EPISODE01_JOIN_KERNEL_V2_SHA256",
    "EPISODE01_EVENT_REGIMENT_FILE",
    "EPISODE01_EVENT_REGIMENT_SHA256",
    "NativeBattleCaseError",
    "load_episode01_native_battle_case",
    "load_episode01_main_tick_parity",
    "load_episode01_native_battle_repeatability",
    "load_episode01_phase_event_observations",
    "load_episode01_phase_event_save_feedback",
    "load_episode01_join_day_casualties",
    "load_episode01_join_day_kernel_parity",
    "load_episode01_join_day_kernel_parity_v2",
    "load_episode01_phase_event_regiment_feedback",
    "original_daily_timeline",
]
