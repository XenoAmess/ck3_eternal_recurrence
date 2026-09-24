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
EPISODE01_OUTGOING_FILE = "ck3_1_19_0_6_episode01_messina_main_outgoing_conditional_parity.json"
EPISODE01_OUTGOING_SHA256 = "E31C81A6C7A65A65704C942DFC1C470C6C30EA41FB8CD769334E8D79CCF41727"
EPISODE01_OUTGOING_V2_FILE = "ck3_1_19_0_6_episode01_messina_main_outgoing_conditional_parity_v2.json"
EPISODE01_OUTGOING_V2_SHA256 = "967FD94030A39A7408C33D281E814E01C0F1E412B7797F61449F90FAA58F8F00"
EPISODE01_PAIRED_COUNTER_FILE = "ck3_1_19_0_6_episode01_messina_paired_counter_r14_parity.json"
EPISODE01_PAIRED_COUNTER_SHA256 = "18B9BC086BAFB4423262EF01BE00B71D19CBA461A4483795E514C710992E7358"
EPISODE01_PREJOIN_COUNTER_V2_FILE = "ck3_1_19_0_6_episode01_messina_prejoin_counter_r14_parity_v2.json"
EPISODE01_PREJOIN_COUNTER_V2_SHA256 = "6C32F7DED9CFDB29D103A242B3C9DC8E71DF69C1A08A9980A1EB917A6BAAE113"
EPISODE01_PAIRED_ADVANTAGE_FILE = "ck3_1_19_0_6_episode01_messina_paired_advantage_parity.json"
EPISODE01_PAIRED_ADVANTAGE_SHA256 = "1B8548CDE3AEA3844CD00B52AB4B0AF4C9CFEBD4C95424E2D6767D4B8996314A"
EPISODE01_TRACE_FAILURE_FILE = "ck3_1_19_0_6_episode01_messina_paired_trace_failure_boundaries.json"
EPISODE01_TRACE_FAILURE_SHA256 = "3E82A6A59ED2648F37D31BC8A4A6CEB32D79516F9E9F6DD2F2E5A0B7A4554953"
EPISODE01_TRACE_DAY26_FILE = "ck3_1_19_0_6_episode01_messina_paired_trace_day26_identity.json"
EPISODE01_TRACE_DAY26_SHA256 = "32715AE1731CF19ABFEFB4D2668D47F6EFA8188AEADC187F298E739825019065"
EPISODE01_KILL_REPLAY_FILE = "ck3_1_19_0_6_episode01_messina_phase_event_kill_replay_feedback.json"
EPISODE01_KILL_REPLAY_SHA256 = "2E68CB2196B1546E610CED211F81251AEE6DD09294FD6EF529EFF132C0134EDC"
EPISODE01_KILL_TRACE_RECOVERY_FILE = "ck3_1_19_0_6_episode01_messina_phase_event_kill_trace_recovery.json"
EPISODE01_KILL_TRACE_RECOVERY_SHA256 = "B7F940916285F5E057B972EBBF12873BF6466D2396A13EF76905A95F04EA2C05"
EPISODE01_KILL_TRACE_RELEASE_FILE = "ck3_1_19_0_6_episode01_messina_phase_event_kill_trace_release.json"
EPISODE01_KILL_TRACE_RELEASE_SHA256 = "906900875DF185CD3157874293E440865ECD7BDDDD758E7FB9EC6163FFFD19BE"
EPISODE01_CONDITIONAL_KILL_EFFECT_FILE = "ck3_1_19_0_6_episode01_messina_conditional_kill_effect_audit.json"
EPISODE01_CONDITIONAL_KILL_EFFECT_SHA256 = "CFB7E59263D09FBF9F92CBB2426C1227ABD706994393F142AC163A2BD4CE2F16"
EPISODE01_SELECTED_EVENT_ROW_FILE = "ck3_1_19_0_6_episode01_messina_selected_phase_event_row.json"
EPISODE01_SELECTED_EVENT_ROW_SHA256 = "BEA95DDF36C0B8F1E5D4B6E01364BF8E35C3C3A7F676B10B038880A94CB5321D"
EPISODE01_PHASE_FIRE_DRAWS_FILE = "ck3_1_19_0_6_episode01_messina_phase_fire_draw_projection.json"
EPISODE01_PHASE_FIRE_DRAWS_SHA256 = "5EC7EE43064603B913305EEEF7403D8315C0BB7EC67BFD0AE7BAD01EB3BFC5AD"
EPISODE01_KILL_REWARD_FILE = "ck3_1_19_0_6_episode01_knight_kill_reward_scaling.json"
EPISODE01_KILL_REWARD_SHA256 = "3FCB1FFB509251CA471E33FAACC768FD7E7FC04243413EDCD9EDCFD0CAD99E92"


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


def _validate_main_outgoing_conditional_parity(report: dict[str, Any]) -> None:
    if (report.get("schema") != "ck3-native-main-outgoing-conditional-parity-v1"
            or report.get("case_sha256") != EPISODE01_CASE_SHA256
            or report.get("join_evidence_sha256") != EPISODE01_JOIN_DAY_SHA256
            or report.get("game_version") != "1.19.0.6"
            or report.get("combat_id") != 16777218
            or report.get("trajectory") != "independent-replay-from-original-contact-checkpoint"
            or report.get("native_outgoing_values_compared") != 46
            or report.get("exact_outgoing_values") != 46):
        raise NativeBattleCaseError("conditional outgoing parity identity or count mismatch")
    if any(report.get(key) is not True for key in (
        "conditioned_on_native_post_counter_attack", "conditioned_on_native_advantage",
        "conditioned_on_observed_joined_roster_and_width",
    )) or any(report.get(key) is not False for key in (
        "post_counter_attack_reconstructed", "advantage_reconstructed",
        "join_policy_reconstructed", "width_refresh_reconstructed",
        "whole_battle_win_probability_available", "planner_usable",
    )):
        raise NativeBattleCaseError("conditional outgoing parity forecast gate mismatch")
    rows = report.get("source_days")
    if not isinstance(rows, list) or [row.get("source_day") for row in rows] != list(range(4, 27)):
        raise NativeBattleCaseError("conditional outgoing day sequence mismatch")
    for row in rows:
        sides = row.get("sides")
        if (not isinstance(sides, list)
                or [side.get("side_index") for side in sides] != [0, 1]
                or row.get("advantage_record_index") != 1
                or row.get("advantage_record_capture_failure_flags") != 0
                or row.get("both_sides_exact") is not True
                or any(side.get("agent_minus_native_raw") != 0
                       or side.get("agent_outgoing_damage_raw") != side.get("native_outgoing_damage_raw")
                       for side in sides)):
            raise NativeBattleCaseError("conditional outgoing day residual or boundary mismatch")
        source_day = row["source_day"]
        if source_day in (11, 21):
            if (row.get("width_source") != "arrival_day_control_after_join"
                    or row.get("observed_joined_fighting_men_raw") !=
                    (256000000 if source_day == 11 else 105800000)):
                raise NativeBattleCaseError("conditional outgoing join input mismatch")
        elif (row.get("width_source") != "source_day_control"
              or row.get("observed_joined_fighting_men_raw") != 0):
            raise NativeBattleCaseError("unexpected join input on stable day")


def load_episode01_main_outgoing_conditional_parity() -> dict[str, Any]:
    """Return 46 exact conditional damage-scaling checks, not forecasts."""
    path = Path(__file__).with_name("data") / EPISODE01_OUTGOING_FILE
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest().upper() != EPISODE01_OUTGOING_SHA256:
        raise NativeBattleCaseError("bundled outgoing parity bytes changed without review")
    report = json.loads(data)
    if not isinstance(report, dict):
        raise NativeBattleCaseError("outgoing parity must be a JSON object")
    _validate_main_outgoing_conditional_parity(report)
    return report


def _validate_main_outgoing_conditional_parity_v2(report: dict[str, Any]) -> None:
    if (report.get("schema") != "ck3-native-main-outgoing-conditional-parity-v2"
            or report.get("case_sha256") != EPISODE01_CASE_SHA256
            or report.get("join_evidence_sha256") != EPISODE01_JOIN_DAY_SHA256
            or report.get("game_version") != "1.19.0.6"
            or report.get("combat_id") != 16777218
            or report.get("trajectory") != "independent-replay-from-original-contact-checkpoint"
            or report.get("battle_province_id") != 2633
            or report.get("battle_terrain_key") != "forest"
            or report.get("terrain_width_multiplier_raw") != 90000
            or report.get("province_terrain_source_sha256") !=
            "922A5B8BA73007B18E95F1CCFCDBE075A03F5DE61CBF8FF8F66698BEDBB3BE3C"
            or report.get("terrain_types_source_sha256") !=
            "39D79AD120BF85B49D6EE8D96FE4D94EDBBABC190A41662DBA8ECA8DE0ACE64E"
            or report.get("native_outgoing_values_compared") != 46
            or report.get("exact_outgoing_values") != 46):
        raise NativeBattleCaseError("width-reconstructed outgoing identity or count mismatch")
    if any(report.get(key) is not True for key in (
        "conditioned_on_native_post_counter_attack", "conditioned_on_native_advantage",
        "conditioned_on_observed_joined_roster", "conditioned_on_stock_terrain_width",
        "width_formula_reconstructed_from_observed_join_timing",
    )) or any(report.get(key) is not False for key in (
        "post_counter_attack_reconstructed", "advantage_reconstructed",
        "join_policy_reconstructed", "width_update_timing_reconstructed",
        "whole_battle_win_probability_available", "planner_usable",
    )):
        raise NativeBattleCaseError("width-reconstructed outgoing forecast gate mismatch")
    rows = report.get("source_days")
    if not isinstance(rows, list) or [row.get("source_day") for row in rows] != list(range(4, 27)):
        raise NativeBattleCaseError("width-reconstructed outgoing day sequence mismatch")
    for row in rows:
        sides = row.get("sides")
        if (not isinstance(sides, list)
                or [side.get("side_index") for side in sides] != [0, 1]
                or row.get("advantage_record_index") != 1
                or row.get("advantage_record_capture_failure_flags") != 0
                or row.get("combat_width_exact") is not True
                or row.get("computed_base_combat_width") != row.get("native_base_combat_width")
                or row.get("computed_final_combat_width") != row.get("native_final_combat_width")
                or row.get("both_sides_exact") is not True
                or any(side.get("agent_minus_native_raw") != 0
                       or side.get("agent_outgoing_damage_raw") != side.get("native_outgoing_damage_raw")
                       for side in sides)):
            raise NativeBattleCaseError("width-reconstructed outgoing row mismatch")
        expected_join = {11: 256000000, 21: 105800000}.get(row["source_day"], 0)
        if row.get("observed_joined_fighting_men_raw") != expected_join:
            raise NativeBattleCaseError("width-reconstructed outgoing join strength mismatch")
    if (rows[0]["computed_base_combat_width"], rows[0]["computed_final_combat_width"]) != (1645, 1480):
        raise NativeBattleCaseError("initial width mismatch")
    if (rows[7]["computed_base_combat_width"], rows[7]["computed_final_combat_width"]) != (2467, 2220):
        raise NativeBattleCaseError("joined width mismatch")


def load_episode01_main_outgoing_conditional_parity_v2() -> dict[str, Any]:
    """Return observed-join width and outgoing parity, never a full forecast."""
    path = Path(__file__).with_name("data") / EPISODE01_OUTGOING_V2_FILE
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest().upper() != EPISODE01_OUTGOING_V2_SHA256:
        raise NativeBattleCaseError("bundled outgoing width parity bytes changed without review")
    report = json.loads(data)
    if not isinstance(report, dict):
        raise NativeBattleCaseError("outgoing width parity must be a JSON object")
    _validate_main_outgoing_conditional_parity_v2(report)
    return report


def load_episode01_paired_counter_r14_parity() -> dict[str, Any]:
    """Load only the same-run conditional R14 proof; never promote a forecast."""
    path = Path(__file__).with_name("data") / EPISODE01_PAIRED_COUNTER_FILE
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest().upper() != EPISODE01_PAIRED_COUNTER_SHA256:
        raise NativeBattleCaseError("bundled paired counter R14 bytes changed without review")
    report = json.loads(data)
    if (not isinstance(report, dict)
            or report.get("schema") != "xar.ck3.episode01.paired-counter-r14-parity/v1"
            or report.get("game_build") != "CK3 1.19.0.6"
            or report.get("forecast_ready") is not False
            or report.get("planner_usable") is not False
            or report.get("conditional_on") != [
                "native_current_fighting_raw", "native_effective_damage_raw", "native_pre_fire_roster"
            ]):
        raise NativeBattleCaseError("paired counter R14 scope or readiness drifted")
    days = report.get("days")
    if (not isinstance(days, list)
            or [row.get("day") for row in days] != list(range(4, 27))
            or report.get("observed_days") != 23):
        raise NativeBattleCaseError("paired counter R14 daily sequence is incomplete")
    exact_days = [row["day"] for row in days if all(
        value == "exact" for value in row["side_comparison"].values()
    )]
    unresolved_days = [row["day"] for row in days if row["day"] not in exact_days]
    exact_sides = sum(
        value == "exact" for row in days for value in row["side_comparison"].values()
    )
    if (report.get("conditional_exact_days") != exact_days
            or report.get("unresolved_days") != unresolved_days
            or report.get("conditional_exact_side_comparisons") != exact_sides
            or report.get("conditional_comparable_side_count") != 46
            or unresolved_days != [11, 21]):
        raise NativeBattleCaseError("paired counter R14 summary disagrees with day rows")
    return report


def load_episode01_prejoin_counter_r14_parity_v2() -> dict[str, Any]:
    """Load the two same-date hypothetical join probes with their RED gates."""
    path = Path(__file__).with_name("data") / EPISODE01_PREJOIN_COUNTER_V2_FILE
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest().upper() != EPISODE01_PREJOIN_COUNTER_V2_SHA256:
        raise NativeBattleCaseError("bundled prejoin counter R14 bytes changed without review")
    report = json.loads(data)
    if (not isinstance(report, dict)
            or report.get("schema") != "xar.ck3.episode01.prejoin-counter-r14-parity/v2"
            or report.get("game_build") != "CK3 1.19.0.6"
            or report.get("source_paired_report_sha256") != EPISODE01_PAIRED_COUNTER_SHA256
            or report.get("same_date_hypothetical_prejoin_query_available") is not True
            or report.get("native_r14_side_comparisons") != 46
            or report.get("conditional_exact_r14_side_comparisons") != 46
            or [row.get("source_day") for row in report.get("join_day_repairs", [])] != [11, 21]
            or any(any(delta != 0 for delta in row.get("delta_raw", {}).values())
                   for row in report["join_day_repairs"])
            or report.get("join_policy_reconstructed") is not False
            or report.get("phase_effect_transition_complete") is not False
            or report.get("advantage_reconstructed") is not False
            or report.get("whole_battle_win_probability_available") is not False
            or report.get("planner_usable") is not False):
        raise NativeBattleCaseError("prejoin counter R14 contract or readiness drifted")
    return report


def load_episode01_paired_advantage_parity() -> dict[str, Any]:
    """Load conditional observed-roll advantage parity, never a forecast."""
    path = Path(__file__).with_name("data") / EPISODE01_PAIRED_ADVANTAGE_FILE
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest().upper() != EPISODE01_PAIRED_ADVANTAGE_SHA256:
        raise NativeBattleCaseError("bundled paired advantage bytes changed without review")
    report = json.loads(data)
    if (not isinstance(report, dict)
            or report.get("schema") != "xar.ck3.episode01.paired-advantage-parity/v1"
            or report.get("game_build") != "CK3 1.19.0.6"
            or report.get("source_paired_report_sha256") != EPISODE01_PAIRED_COUNTER_SHA256
            or report.get("observed_main_days") != 23
            or report.get("conditional_exact_advantage_days") != 23
            or [row.get("day") for row in report.get("days", [])] != list(range(4, 27))
            or any(row.get("delta_raw") != 0 for row in report["days"])
            or report.get("zero_roll_context_reconstructed_independently") is not False
            or report.get("future_rolls_predicted") is not False
            or report.get("phase_effect_transition_complete") is not False
            or report.get("join_policy_reconstructed") is not False
            or report.get("whole_battle_win_probability_available") is not False
            or report.get("planner_usable") is not False):
        raise NativeBattleCaseError("paired advantage contract or readiness drifted")
    return report


def load_episode01_paired_trace_failure_boundaries() -> dict[str, Any]:
    """Identify locally valid boundaries while preserving whole-trace RED."""
    path = Path(__file__).with_name("data") / EPISODE01_TRACE_FAILURE_FILE
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest().upper() != EPISODE01_TRACE_FAILURE_SHA256:
        raise NativeBattleCaseError("bundled trace failure bytes changed without review")
    report = json.loads(data)
    if (not isinstance(report, dict)
            or report.get("schema") != "xar.ck3.episode01.paired-trace-failure-boundaries/v1"
            or report.get("game_build") != "CK3 1.19.0.6"
            or report.get("source_paired_report_sha256") != EPISODE01_PAIRED_COUNTER_SHA256
            or report.get("observed_main_days") != 23
            or report.get("whole_trace_green_days") != 20
            or report.get("whole_trace_red_days") != 3
            or [row.get("day") for row in report.get("red_days", [])] != [11, 21, 26]
            or [row.get("first_failing_boundary_index") for row in report["red_days"]] != [2, 2, 6]
            or any(row.get("full_trace_available") is not False for row in report["red_days"])
            or report.get("join_day_capture_repaired") is not False
            or report.get("final_identity_failure_repaired") is not False
            or report.get("phase_effect_transition_complete") is not False
            or report.get("whole_battle_win_probability_available") is not False
            or report.get("planner_usable") is not False):
        raise NativeBattleCaseError("paired trace failure boundary or readiness drifted")
    return report


def load_episode01_paired_trace_day26_identity() -> dict[str, Any]:
    """Read the narrow final-query failure diagnosis without promoting RED."""
    path = Path(__file__).with_name("data") / EPISODE01_TRACE_DAY26_FILE
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest().upper() != EPISODE01_TRACE_DAY26_SHA256:
        raise NativeBattleCaseError("bundled day-26 identity diagnosis bytes changed without review")
    report = json.loads(data)
    if (not isinstance(report, dict)
            or report.get("schema") != "xar.ck3.episode01.paired-trace-day26-identity/v1"
            or report.get("source_failure_report_sha256") != EPISODE01_TRACE_FAILURE_SHA256
            or report.get("day") != 26
            or report.get("first_failing_boundary_index") != 6
            or report.get("final_side1_scheduled_regiment_id") != 62
            or report.get("inferred_first_failing_read") !=
               "ReadSide(side1).scheduled_knights.regiment_identity_guard"
            or report.get("same_day_post_event_save_available") is not False
            or report.get("event_effect_write_set_complete") is not False
            or report.get("full_trace_available") is not False
            or report.get("whole_battle_win_probability_available") is not False
            or report.get("planner_usable") is not False):
        raise NativeBattleCaseError("day-26 identity diagnosis or readiness drifted")
    return report


def load_episode01_phase_event_kill_replay_feedback() -> dict[str, Any]:
    """Read an independent same-date kill/save observation for agent and film."""
    path = Path(__file__).with_name("data") / EPISODE01_KILL_REPLAY_FILE
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest().upper() != EPISODE01_KILL_REPLAY_SHA256:
        raise NativeBattleCaseError("bundled kill replay feedback bytes changed without review")
    report = json.loads(data)
    target = report.get("target_before_and_after", []) if isinstance(report, dict) else []
    if (not isinstance(report, dict)
            or not isinstance(target, list) or len(target) != 2
            or not all(isinstance(row, dict) for row in target)
            or report.get("schema") != "xar.ck3.episode01.phase-event-kill-replay-feedback/v1"
            or report.get("restored_source_paired_report_sha256") != EPISODE01_PAIRED_COUNTER_SHA256
            or report.get("appended_event", {}).get("stable_key") != "knight_killed_by_enemy"
            or report.get("appended_event", {}).get("left_character_id") != 33437
            or report.get("target_regiment_id_before") != 65
            or report.get("stale_scheduled_regiment_id_at_final_query") != 65
            or target[0].get("alive_data_present") is not True
            or target[1].get("dead_data_present") is not True
            or target[1].get("killer_character_id") != 34120
            or report.get("opponent_prestige_currency_delta") != "150.0000"
            or report.get("opponent_base_prowess_delta") != 0
            or report.get("full_event_write_set_proven") is not False
            or report.get("only_possible_cause_proven") is not False
            or report.get("full_phase_trace_available") is not False
            or report.get("whole_battle_win_probability_available") is not False
            or report.get("planner_usable") is not False):
        raise NativeBattleCaseError("kill replay feedback or readiness drifted")
    return report


def load_episode01_phase_event_kill_trace_recovery() -> dict[str, Any]:
    """Read a recovered seven-boundary capture without promoting effect fidelity."""
    path = Path(__file__).with_name("data") / EPISODE01_KILL_TRACE_RECOVERY_FILE
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest().upper() != EPISODE01_KILL_TRACE_RECOVERY_SHA256:
        raise NativeBattleCaseError("kill trace recovery bytes changed without review")
    report = json.loads(data)
    before = report.get("target_core_before_final_query", {}) if isinstance(report, dict) else {}
    after = report.get("target_core_at_final_query", {}) if isinstance(report, dict) else {}
    if (not isinstance(report, dict)
            or report.get("schema") != "xar.ck3.episode01.phase-event-kill-trace-recovery/v1"
            or report.get("restored_source_paired_report_sha256") != EPISODE01_PAIRED_COUNTER_SHA256
            or report.get("appended_event", {}).get("stable_key") != "knight_killed_by_enemy"
            or report.get("appended_event", {}).get("left_character_id") != 33437
            or report.get("boundary_count") != 7
            or report.get("boundary_capture_failure_flags") != [0] * 7
            or report.get("trace_failure_flags") != 0
            or before.get("death_marker_present") is not False
            or after.get("death_marker_present") is not True
            or before.get("current_regiment_id") != 65
            or after.get("current_regiment_id") != 0
            or report.get("scheduled_knight_at_final_query", {}).get("current_character_id") != -1
            or report.get("killer_prestige_currency_delta") != "150.0000"
            or report.get("seven_boundary_capture_available") is not True
            or any(report.get(key) is not False for key in (
                "full_mutable_transition_bundle_complete", "full_event_write_set_proven",
                "only_possible_cause_proven", "whole_battle_win_probability_available",
                "planner_usable",
            ))):
        raise NativeBattleCaseError("kill trace recovery or readiness drifted")
    return report


def load_episode01_phase_event_kill_trace_release() -> dict[str, Any]:
    """Read Release-build v3 admission and same-day kill capture, still nonplanner."""
    path = Path(__file__).with_name("data") / EPISODE01_KILL_TRACE_RELEASE_FILE
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest().upper() != EPISODE01_KILL_TRACE_RELEASE_SHA256:
        raise NativeBattleCaseError("Release kill trace bytes changed without review")
    report = json.loads(data)
    if (not isinstance(report, dict)
            or report.get("schema") != "xar.ck3.episode01.phase-event-kill-trace-recovery/v1"
            or report.get("restored_source_paired_report_sha256") != EPISODE01_PAIRED_COUNTER_SHA256
            or report.get("boundary_capture_failure_flags") != [0] * 7
            or report.get("appended_event", {}).get("left_character_id") != 33437
            or report.get("target_core_at_final_query", {}).get("death_marker_present") is not True
            or report.get("scheduled_knight_at_final_query", {}).get("current_character_id") != -1
            or report.get("v3_phase_event_input_status") != "available"
            or report.get("v3_phase_event_input_unavailable_reason") is not None
            or not isinstance(report.get("release_build_cache_sha256"), str)
            or len(report["release_build_cache_sha256"]) != 64
            or not isinstance(report.get("release_bridge_dll_sha256"), str)
            or len(report["release_bridge_dll_sha256"]) != 64
            or any(report.get(key) is not False for key in (
                "full_mutable_transition_bundle_complete", "full_event_write_set_proven",
                "only_possible_cause_proven", "whole_battle_win_probability_available",
                "planner_usable",
            ))):
        raise NativeBattleCaseError("Release kill trace or readiness drifted")
    return report


def load_episode01_conditional_kill_effect_audit() -> dict[str, Any]:
    """Read a reachable modeled kill path and its native mismatch, never a forecast."""
    path = Path(__file__).with_name("data") / EPISODE01_CONDITIONAL_KILL_EFFECT_FILE
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest().upper() != EPISODE01_CONDITIONAL_KILL_EFFECT_SHA256:
        raise NativeBattleCaseError("conditional kill effect audit bytes changed without review")
    report = json.loads(data)
    if (not isinstance(report, dict)
            or report.get("schema") != "xar.ck3.episode01.conditional-kill-effect-audit/v1"
            or report.get("source_native_report_sha256") != EPISODE01_KILL_TRACE_RELEASE_SHA256
            or report.get("root_character_id") != 33437
            or report.get("observed_killer_character_id") != 34120
            or report.get("draw_provenance") != "synthetic_reachability_witness_not_native_rng"
            or report.get("native_draw_trace_available") is not False
            or report.get("modeled_root_prowess_raw_after") != 400000
            or report.get("native_derived_root_prowess_raw_after") != 200000
            or any(report.get(key) is not True for key in (
                "conditional_death_reason_matches_native",
                "conditional_killer_matches_native",
                "conditional_participant_detach_matches_native",
            ))
            or any(report.get(key) is not False for key in (
                "effective_character_stat_refresh_matches_native",
                "reward_transition_modeled_by_effect_kernel",
                "full_effect_write_set_proven", "same_day_effect_order_proven",
                "whole_battle_win_probability_available", "planner_usable",
            ))):
        raise NativeBattleCaseError("conditional kill effect or fidelity boundary drifted")
    return report


def load_episode01_selected_phase_event_row() -> dict[str, Any]:
    """Read exact native row identity; this does not expose its hidden draws."""
    path = Path(__file__).with_name("data") / EPISODE01_SELECTED_EVENT_ROW_FILE
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest().upper() != EPISODE01_SELECTED_EVENT_ROW_SHA256:
        raise NativeBattleCaseError("selected event row bytes changed without review")
    report = json.loads(data)
    if (not isinstance(report, dict)
            or report.get("schema") != "xar.ck3.episode01.selected-phase-event-row/v1"
            or report.get("game_build") != "CK3 1.19.0.6"
            or report.get("restored_source_save_sha256") !=
            "C1276153435766A875B0984F1A3AD426CB3AFCFB6EC33061CEE6650538CFFD2B"
            or report.get("trace_response_sha256") !=
            "5744C62F395179F69234CAF15E9AE40913A14161D333D1D5D4E9D2A188E8B50B"
            or report.get("target_character_id") != 33437
            or report.get("target_regiment_id") != 65
            or report.get("native_event_global_load_index") != 11
            or report.get("native_event_key") != "knight_killed"
            or report.get("native_selected_row_observed") is not True
            or report.get("mapped_boundaries") != [1, 2, 3, 4, 5, 6]
            or report.get("appended_battle_event", {}).get("stable_key") != "knight_killed_by_enemy"
            or report.get("event_appended_between_boundaries") != [4, 5]
            or report.get("death_and_detachment_observed_at_boundary") != 6
            or report.get("target_derived_prowess_before_and_after") != [4, 2]
            or any(report.get(key) is not False for key in (
                "native_effect_internal_draws_observed", "full_event_write_set_proven",
                "whole_battle_win_probability_available", "planner_usable",
            ))):
        raise NativeBattleCaseError("selected event row or readiness drifted")
    return report


def load_episode01_phase_fire_draw_projection() -> dict[str, Any]:
    """Read observed RNG boundaries and exact-build draw/seed projection."""
    path = Path(__file__).with_name("data") / EPISODE01_PHASE_FIRE_DRAWS_FILE
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest().upper() != EPISODE01_PHASE_FIRE_DRAWS_SHA256:
        raise NativeBattleCaseError("phase-fire draw projection bytes changed without review")
    report = json.loads(data)
    fires = report.get("phase_fire_draws", []) if isinstance(report, dict) else []
    if (not isinstance(report, dict)
            or report.get("schema") != "xar.ck3.episode01.phase-fire-draw-projection/v1"
            or report.get("selected_event_row_report_sha256") != EPISODE01_SELECTED_EVENT_ROW_SHA256
            or report.get("trace_response_sha256") !=
            "5744C62F395179F69234CAF15E9AE40913A14161D333D1D5D4E9D2A188E8B50B"
            or report.get("native_state_counter_salt_observed") is not True
            or report.get("global_draw_and_effect_seed_provenance") !=
            "derived_from_native_state_with_exact_build_static_algorithm"
            or not isinstance(fires, list) or len(fires) != 2
            or [row.get("side_index") for row in fires] != [0, 1]
            or [row.get("derived_global_draw31") for row in fires] != [753992024, 816083018]
            or fires[1].get("scheduled_knight_event_load_indices") != [11]
            or fires[1].get("derived_knight_effect_seeds") != [1111439774]
            or report.get("target_effect_seed") != 1111439774
            or any(report.get(key) is not False for key in (
                "effect_local_draws_directly_observed", "effect_local_seed_to_draw_state_validated",
                "full_effect_write_set_proven", "whole_battle_win_probability_available",
                "planner_usable",
            ))):
        raise NativeBattleCaseError("phase-fire draw projection or readiness drifted")
    return report


def load_episode01_knight_kill_reward_scaling() -> dict[str, Any]:
    """Read conditional stock reward parity without event-effect promotion."""
    path = Path(__file__).with_name("data") / EPISODE01_KILL_REWARD_FILE
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest().upper() != EPISODE01_KILL_REWARD_SHA256:
        raise NativeBattleCaseError("bundled kill reward scaling bytes changed without review")
    report = json.loads(data)
    if (not isinstance(report, dict)
            or report.get("schema") != "xar.ck3.episode01.knight-kill-reward-scaling/v1"
            or report.get("source_old_feedback_sha256") != EPISODE01_PHASE_EVENT_SAVE_SHA256
            or report.get("source_new_feedback_sha256") != EPISODE01_KILL_REPLAY_SHA256
            or report.get("conditional_exact_cases") != 2
            or [row.get("target_character_id") for row in report.get("cases", [])] != [36673, 33437]
            or [row.get("native_prestige_delta_raw_q100000") for row in report["cases"]]
               != [30_000_000, 15_000_000]
            or any(row.get("delta_raw_q100000") != 0 for row in report["cases"])
            or report.get("title_rank_and_lowborn_conditions_proven_for_all_future_events") is not False
            or report.get("reward_only_possible_cause_proven") is not False
            or report.get("full_event_write_set_proven") is not False
            or report.get("whole_battle_win_probability_available") is not False
            or report.get("planner_usable") is not False):
        raise NativeBattleCaseError("conditional kill reward scaling or readiness drifted")
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
    "EPISODE01_OUTGOING_FILE",
    "EPISODE01_OUTGOING_SHA256",
    "EPISODE01_OUTGOING_V2_FILE",
    "EPISODE01_OUTGOING_V2_SHA256",
    "EPISODE01_PAIRED_COUNTER_FILE",
    "EPISODE01_PAIRED_COUNTER_SHA256",
    "EPISODE01_PREJOIN_COUNTER_V2_FILE",
    "EPISODE01_PREJOIN_COUNTER_V2_SHA256",
    "EPISODE01_PAIRED_ADVANTAGE_FILE",
    "EPISODE01_PAIRED_ADVANTAGE_SHA256",
    "EPISODE01_TRACE_FAILURE_FILE",
    "EPISODE01_TRACE_FAILURE_SHA256",
    "EPISODE01_TRACE_DAY26_FILE",
    "EPISODE01_TRACE_DAY26_SHA256",
    "EPISODE01_KILL_REPLAY_FILE",
    "EPISODE01_KILL_REPLAY_SHA256",
    "EPISODE01_KILL_TRACE_RECOVERY_FILE",
    "EPISODE01_KILL_TRACE_RECOVERY_SHA256",
    "EPISODE01_KILL_TRACE_RELEASE_FILE",
    "EPISODE01_KILL_TRACE_RELEASE_SHA256",
    "EPISODE01_CONDITIONAL_KILL_EFFECT_FILE",
    "EPISODE01_CONDITIONAL_KILL_EFFECT_SHA256",
    "EPISODE01_KILL_REWARD_FILE",
    "EPISODE01_KILL_REWARD_SHA256",
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
    "load_episode01_main_outgoing_conditional_parity",
    "load_episode01_main_outgoing_conditional_parity_v2",
    "load_episode01_paired_counter_r14_parity",
    "load_episode01_prejoin_counter_r14_parity_v2",
    "load_episode01_paired_advantage_parity",
    "load_episode01_paired_trace_failure_boundaries",
    "load_episode01_paired_trace_day26_identity",
    "load_episode01_phase_event_kill_replay_feedback",
    "load_episode01_phase_event_kill_trace_recovery",
    "load_episode01_phase_event_kill_trace_release",
    "load_episode01_conditional_kill_effect_audit",
    "load_episode01_knight_kill_reward_scaling",
    "original_daily_timeline",
]
