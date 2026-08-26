from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.battle_control_contract import (
    QUERY_BATTLE_CONTROL_SNAPSHOT_V1_CAPABILITY,
    normalize_battle_control_snapshot_v1,
    parse_query_battle_control_snapshot_v1_step,
    query_battle_control_snapshot_v1_step,
)
from xar_autoplayer.bridge.driver import (
    BridgeUnavailableError,
    UnsupportedStepError,
)
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import (
    NativeHeadlessGameplayDriver,
    _action_steps,
)
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.strategy import choose_one_life_turn


SUBJECT = 83_886_341
NATIVE_SUBJECT = 101
NATIVE_REVISION = 5
DATE_RAW = 53_178_264
STEP = f"query-battle-control-snapshot-v1-{SUBJECT}"
TRANSIENT_QUERY_ERROR = "CK3 battle-control state changed during query"


def _army_identity(
    native_id: int,
    public_id: int,
    owner_id: int,
) -> dict[str, int]:
    return {
        "native_carmy_id": native_id,
        "public_cunit_id": public_id,
        "owner_character_id": owner_id,
        "combat_backlink_id": 335_544_325,
    }


def _entry(
    *,
    bucket: str,
    bucket_index: int,
    regiment_id: int,
    native_carmy_id: int,
    public_cunit_id: int,
    owner_character_id: int,
    starting_raw: int,
    current_fighting_raw: int,
    soft_casualties_raw: int,
    fights_in_main_phase: bool,
    entry_strength_raw: int,
) -> dict[str, object]:
    if fights_in_main_phase:
        hard_status = "available"
        hard_raw = (
            starting_raw - current_fighting_raw - soft_casualties_raw
        )
        hard_source = "derived_starting_minus_current_minus_soft"
        hard_reason = None
    else:
        hard_status = "unavailable"
        hard_raw = None
        hard_source = None
        hard_reason = "non_main_reserve_not_distinguishable_from_hard"
    return {
        "bucket": bucket,
        "bucket_index": bucket_index,
        "regiment_id": regiment_id,
        "native_carmy_id": native_carmy_id,
        "public_cunit_id": public_cunit_id,
        "owner_character_id": owner_character_id,
        "starting_raw": starting_raw,
        "current_fighting_raw": current_fighting_raw,
        "soft_casualties_raw": soft_casualties_raw,
        "fights_in_main_phase": fights_in_main_phase,
        "hard_casualties_status": hard_status,
        "hard_casualties_raw": hard_raw,
        "hard_casualties_source": hard_source,
        "hard_casualties_unavailable_reason": hard_reason,
        "effective_max_size": 100,
        "effective_siege_raw": 100_000,
        "effective_damage_raw": 2_000_000_000,
        "effective_toughness_raw": 3_000_000_000,
        "effective_pursuit_raw": 400_000,
        "effective_screen_raw": 500_000,
        "entry_strength_raw": entry_strength_raw,
    }


def _side(
    *,
    side_index: int,
    role: str,
    primary: int,
    commander: int | None,
    roll: int,
    armies: list[dict[str, int]],
    levy_entries: list[dict[str, object]],
    men_at_arms_entries: list[dict[str, object]],
    participant_rows: list[dict[str, int]],
    side_strength_raw: int,
) -> dict[str, object]:
    entries = levy_entries + men_at_arms_entries
    derived_current = sum(
        int(row["current_fighting_raw"]) for row in entries
    )
    derived_levy_current = sum(
        int(row["current_fighting_raw"]) for row in levy_entries
    )
    main_entries = [
        row for row in entries if row["fights_in_main_phase"] is True
    ]
    non_main_entries = [
        row for row in entries if row["fights_in_main_phase"] is False
    ]
    return {
        "side_index": side_index,
        "role": role,
        "primary_participant_character_id": primary,
        "selected_commander_character_id": commander,
        "current_roll_points": roll,
        "ordered_armies": armies,
        "levy_entries": levy_entries,
        "men_at_arms_entries": men_at_arms_entries,
        "stored_current_fighting_raw": derived_current,
        "stored_levy_current_fighting_raw": derived_levy_current,
        "stored_current_matches_derived": True,
        "stored_levy_current_matches_derived": True,
        "derived_current_fighting_raw": derived_current,
        "derived_soft_casualties_raw": sum(
            int(row["soft_casualties_raw"]) for row in entries
        ),
        "derived_main_fighting_entry_hard_casualties_raw": sum(
            int(row["hard_casualties_raw"]) for row in main_entries
        ),
        "non_main_start_minus_current_minus_soft_raw": sum(
            int(row["starting_raw"])
            - int(row["current_fighting_raw"])
            - int(row["soft_casualties_raw"])
            for row in non_main_entries
        ),
        "participant_hard_ledger": participant_rows,
        "participant_hard_total_raw": sum(
            row["hard_casualties_raw"] for row in participant_rows
        ),
        "side_strength_raw": side_strength_raw,
        "side_strength_scale": 100000,
    }


def _battle_frame() -> dict[str, object]:
    attacker_levy = _entry(
        bucket="levy",
        bucket_index=0,
        regiment_id=501,
        native_carmy_id=NATIVE_SUBJECT,
        public_cunit_id=SUBJECT,
        owner_character_id=29_829,
        starting_raw=5_000_000_000,
        current_fighting_raw=4_000_000_000,
        soft_casualties_raw=500_000_000,
        fights_in_main_phase=True,
        entry_strength_raw=81_000,
    )
    attacker_reserve = _entry(
        bucket="men_at_arms",
        bucket_index=0,
        regiment_id=502,
        native_carmy_id=NATIVE_SUBJECT,
        public_cunit_id=SUBJECT,
        owner_character_id=29_829,
        starting_raw=3_000_000_000,
        current_fighting_raw=0,
        soft_casualties_raw=0,
        fights_in_main_phase=False,
        entry_strength_raw=0,
    )
    defender_levy = _entry(
        bucket="levy",
        bucket_index=0,
        regiment_id=601,
        native_carmy_id=202,
        public_cunit_id=357,
        owner_character_id=36_108,
        starting_raw=2_000_000_000,
        current_fighting_raw=1_500_000_000,
        soft_casualties_raw=200_000_000,
        fights_in_main_phase=True,
        entry_strength_raw=42_000,
    )
    defender_maa = _entry(
        bucket="men_at_arms",
        bucket_index=0,
        regiment_id=602,
        native_carmy_id=303,
        public_cunit_id=33_554_657,
        owner_character_id=36_109,
        starting_raw=1_000_000_000,
        current_fighting_raw=800_000_000,
        soft_casualties_raw=100_000_000,
        fights_in_main_phase=True,
        entry_strength_raw=23_000,
    )
    return {
        "schema_version": 1,
        "contract_stage": "production_exact_ongoing_combat",
        "status": "available",
        "battle_control_ready": True,
        "snapshot_revision": NATIVE_REVISION,
        "observed_date_raw": DATE_RAW,
        "subject_public_cunit_id": SUBJECT,
        "subject_native_carmy_id": NATIVE_SUBJECT,
        "combat_id": 335_544_325,
        "province_id": 2586,
        "selected_public_cunit_id": SUBJECT,
        "selected_native_carmy_id": NATIVE_SUBJECT,
        "selected_owner_character_id": 29_829,
        "combat_province_id": 2586,
        "side_index": 0,
        "side_scope": "full_side",
        "affected_public_cunit_ids_in_stored_order": [SUBJECT],
        "unaffected_same_side_public_cunit_ids_in_stored_order": [],
        "side_flags": {
            "disallow_retreat": False,
            "allow_early_retreat": True,
            "skip_pursuit": False,
        },
        "legality": {
            "status": "available",
            "native_boolean": True,
            "phase_raw": 1,
            "phase": "main",
            "retreat_elapsed_baseline_date_raw": DATE_RAW,
            "elapsed_whole_days": 0,
            "minimum_elapsed_whole_days_exclusive": 14,
            "landless_gate_allows_retreat": True,
            "legal_now": True,
            "reason_codes_in_native_order": [],
            "native_reason_keys_in_native_order": [],
            "earliest_day_gate_date_raw": DATE_RAW + 15 * 24,
        },
        "phase": "main",
        "phase_raw": 1,
        "phase_day": 4,
        "winner_side": "none",
        "winner_raw": -1,
        "forced_winner_side": "none",
        "forced_winner_raw": -1,
        "finalized": False,
        "battle_result_id": None,
        "base_combat_width": 6200,
        "final_combat_width": 5800,
        "roll_cadence_counter": 2,
        "base_advantage_raw": -5_000_000_000,
        "resolved_advantage_raw": 6_000_000_000,
        "attacker": _side(
            side_index=0,
            role="attacker",
            primary=29_829,
            commander=29_829,
            roll=7,
            armies=[_army_identity(NATIVE_SUBJECT, SUBJECT, 29_829)],
            levy_entries=[attacker_levy],
            men_at_arms_entries=[attacker_reserve],
            participant_rows=[
                {
                    "row_index": 0,
                    "participant_character_id": 29_829,
                    "hard_casualties_raw": 700_000_000,
                }
            ],
            side_strength_raw=129_975,
        ),
        "defender": _side(
            side_index=1,
            role="defender",
            primary=36_108,
            commander=None,
            roll=-2,
            armies=[
                _army_identity(202, 357, 36_108),
                _army_identity(303, 33_554_657, 36_109),
            ],
            levy_entries=[defender_levy],
            men_at_arms_entries=[defender_maa],
            participant_rows=[
                {
                    "row_index": 0,
                    "participant_character_id": 36_108,
                    "hard_casualties_raw": 200_000_000,
                },
                {
                    "row_index": 1,
                    "participant_character_id": 36_109,
                    "hard_casualties_raw": 200_000_000,
                },
            ],
            side_strength_raw=65_172,
        ),
    }


def _native_result() -> dict[str, object]:
    return {
        "step": STEP,
        "accepted": True,
        "status": "available",
        "query_sequence": 41,
        "snapshot_revision": NATIVE_REVISION,
        "battle_control_snapshot": _battle_frame(),
    }


def _service_result() -> dict[str, object]:
    result = {**_native_result(), "backend_id": "battle-control-fixture"}
    frame = result["battle_control_snapshot"]
    assert isinstance(frame, dict)
    for key in (
        "selected_public_cunit_id",
        "selected_native_carmy_id",
        "selected_owner_character_id",
        "combat_province_id",
        "side_index",
        "side_scope",
        "affected_public_cunit_ids_in_stored_order",
        "unaffected_same_side_public_cunit_ids_in_stored_order",
        "side_flags",
        "legality",
    ):
        result[key] = copy.deepcopy(frame[key])
    return result


def _semantic_snapshot(revision: int = NATIVE_REVISION) -> dict[str, object]:
    player_army = {
        "army_id": SUBJECT,
        "owner_character_id": 29_829,
        "soldiers": 40_000,
        "current_province_id": 2586,
        "move_target_province_id": None,
        "controllable": True,
        "in_combat": True,
        "army_state": "combat",
        "army_state_code": 2,
    }
    return {
        "type": "state_snapshot",
        "protocol_version": 1,
        "snapshot_id": f"native:{revision}",
        "revision": revision,
        "state": {
            "phase": "map_hud",
            "date": "1066.9.27",
            "date_raw": DATE_RAW,
            "speed": 1,
            "paused": True,
            "map_ready": True,
            "history": [],
            "active_event": None,
            "pending_character_interaction": None,
            "played_character": {"character_id": 29_829, "alive": True},
            "one_life_settlement": None,
            "active_wars": [],
            "player_armies": [player_army],
        },
    }
    return {
        "type": "state_snapshot",
        "protocol_version": 1,
        "snapshot_id": f"native:{revision}",
        "revision": revision,
        "state": {
            "phase": "map_hud",
            "date": "1066.9.27",
            "date_raw": DATE_RAW,
            "speed": 1,
            "paused": True,
            "map_ready": True,
            "history": [],
            "active_event": None,
            "pending_character_interaction": None,
            "played_character": {"character_id": 29_829, "alive": True},
            "one_life_settlement": None,
            "active_wars": [],
            "player_armies": [player_army],
        },
    }


def _battle_query_row(
    index: int,
    frame: dict[str, object],
    *,
    public_revision: int | None = None,
) -> dict[str, object]:
    subject = int(frame["subject_public_cunit_id"])
    native_revision = int(frame["snapshot_revision"])
    revision = (
        native_revision if public_revision is None else public_revision
    )
    step = query_battle_control_snapshot_v1_step(subject)
    return {
        "index": index,
        "command": step,
        "ok": True,
        "result": {
            "step": step,
            "accepted": True,
            "status": "available",
            "query_sequence": index,
            "snapshot_revision": native_revision,
            "battle_control_snapshot": copy.deepcopy(frame),
            "backend_id": "native-headless",
            "queried_snapshot_id": f"native:{revision}",
            "queried_revision": revision,
            "queried_native_revision": native_revision,
        },
    }


def _battle_advance_row(index: int) -> dict[str, object]:
    return {
        "index": index,
        "command": "life-advance",
        "ok": True,
        "result": {
            "step": "life-advance",
            "starting_date_raw": DATE_RAW,
            "ending_date_raw": DATE_RAW + 24,
            "elapsed_days": 1,
            "paused": True,
        },
    }


def _planner_battle_snapshot(
    *,
    frame: dict[str, object] | None,
    army_state: str = "combat",
    alive: bool = True,
) -> dict[str, object]:
    native_revision = (
        int(frame["snapshot_revision"])
        if isinstance(frame, dict)
        else NATIVE_REVISION
    )
    date_raw = (
        int(frame["observed_date_raw"])
        if isinstance(frame, dict)
        else DATE_RAW
    )
    state_code = {"combat": 2, "retreating": 6}.get(army_state, 0)
    player_army = {
        "army_id": SUBJECT,
        "owner_character_id": 29_829,
        "soldiers": 40_000,
        "current_province_id": 2586,
        "move_target_province_id": None,
        "controllable": True,
        "in_combat": army_state == "combat",
        "retreating": army_state == "retreating",
        "army_state": army_state,
        "army_state_code": state_code,
    }
    enemy_army = {
        "army_id": 357,
        "owner_character_id": 36_108,
        "soldiers": 20_000,
        "current_province_id": 2586,
        "move_target_province_id": None,
        "controllable": False,
        "army_state": "combat",
        "army_state_code": 2,
    }
    snapshot: dict[str, object] = {
        "format_version": 1,
        "snapshot_id": f"native:{native_revision}",
        "revision": native_revision,
        "native_revision": native_revision,
        "source": "native-headless",
        "date_raw": date_raw,
        "paused": True,
        "phase": "map_hud",
        "history": [],
        "played_character": {
            "character_id": 29_829,
            "alive": alive,
        },
        "active_wars": [
            {
                "war_id": 88,
                "player_side": "attacker",
                "primary_opponent_character_id": 36_108,
                "player_is_primary_war_leader": True,
                "player_relative_war_score": 17,
                "war_duration_days": 20,
                "allied_armies": [player_army],
                "enemy_armies": [enemy_army],
                "war_objective_province_ids": [],
                "objective_province_states": [],
                "targeted_title_ids": [],
            }
        ],
        "player_armies": [player_army],
        "army_routes_supported": False,
        "move_route_preview_supported": False,
        "route_contact_horizon_supported": False,
    }
    if isinstance(frame, dict):
        snapshot.update(
            {
                "battle_control_snapshot_v1": copy.deepcopy(frame),
                "battle_control_snapshot_v1_status": "available",
                "battle_control_snapshot_v1_query_sequence": 41,
                "battle_control_snapshot_v1_subject_army_id": SUBJECT,
                "battle_control_snapshot_v1_queried_snapshot_id": (
                    f"native:{native_revision}"
                ),
                "battle_control_snapshot_v1_queried_revision": (
                    native_revision
                ),
            }
        )
    return snapshot


def _next_battle_frame() -> dict[str, object]:
    frame = _battle_frame()
    frame["snapshot_revision"] = NATIVE_REVISION + 1
    frame["observed_date_raw"] = DATE_RAW + 24
    frame["phase_day"] = int(frame["phase_day"]) + 1
    frame["legality"]["elapsed_whole_days"] = 1
    return frame


class BattleControlStrategyTests(unittest.TestCase):
    def plan(
        self,
        history: list[dict[str, object]],
        *,
        frame: dict[str, object] | None,
        army_state: str = "combat",
        steps: tuple[str, ...] = (STEP, "life-advance"),
    ) -> dict[str, object]:
        return choose_one_life_turn(
            history,
            snapshot=_planner_battle_snapshot(
                frame=frame,
                army_state=army_state,
            ),
            action_steps=steps,
        )

    def test_combat_queries_current_paused_subject_before_advancing(self) -> None:
        query = self.plan([], frame=None)
        self.assertEqual(query["phase"], "native_war_battle_control_query")
        self.assertEqual(query["selected_step"], STEP)

        unsupported = self.plan(
            [], frame=None, steps=("life-advance",)
        )
        self.assertEqual(
            unsupported["phase"],
            "native_war_battle_control_query_unsupported",
        )
        self.assertIsNone(unsupported["selected_step"])
        self.assertEqual(unsupported["required_step"], STEP)

    def test_current_revision_available_frame_unlocks_one_bounded_advance(
        self,
    ) -> None:
        frame = _battle_frame()
        plan = self.plan([_battle_query_row(1, frame)], frame=frame)

        self.assertEqual(
            plan["phase"], "native_war_global_battle_control_progress"
        )
        self.assertEqual(plan["selected_step"], "life-advance")
        self.assertEqual(
            plan["battle_control_frames"][0]["combat_id"],
            frame["combat_id"],
        )

    def test_mismatched_current_binding_requires_a_fresh_query(self) -> None:
        frame = _battle_frame()
        snapshot = _planner_battle_snapshot(frame=frame)
        snapshot["battle_control_snapshot_v1_queried_revision"] = (
            int(snapshot["revision"]) - 1
        )

        plan = choose_one_life_turn(
            [], snapshot=snapshot, action_steps=(STEP, "life-advance")
        )

        self.assertEqual(plan["selected_step"], STEP)
        self.assertNotEqual(plan["selected_step"], "life-advance")

    def test_continuing_combat_requeries_immediately_after_advance(self) -> None:
        before = _battle_frame()
        history = [
            _battle_query_row(1, before),
            _battle_advance_row(2),
        ]
        snapshot = _planner_battle_snapshot(frame=None)
        snapshot.update(
            {
                "snapshot_id": f"native:{NATIVE_REVISION + 1}",
                "revision": NATIVE_REVISION + 1,
                "native_revision": NATIVE_REVISION + 1,
                "date_raw": DATE_RAW + 24,
            }
        )

        plan = choose_one_life_turn(
            history,
            snapshot=snapshot,
            action_steps=(STEP, "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_battle_control_query")
        self.assertEqual(plan["selected_step"], STEP)

    def test_post_advance_same_combat_phase_day_transition_unlocks_next_slice(
        self,
    ) -> None:
        before = _battle_frame()
        after = _next_battle_frame()
        history = [
            _battle_query_row(1, before),
            _battle_advance_row(2),
            _battle_query_row(3, after),
        ]

        plan = self.plan(history, frame=after)

        self.assertEqual(plan["selected_step"], "life-advance")
        self.assertEqual(
            plan["battle_transitions"][0]["status"],
            "same_combat_advanced",
        )
        self.assertTrue(
            plan["battle_transitions"][0]["phase_day_changed"]
        )

    def test_same_phase_day_exact_ledger_delta_unlocks_next_slice(self) -> None:
        before = _battle_frame()
        after = _next_battle_frame()
        after["phase_day"] = before["phase_day"]
        attacker = after["attacker"]
        levy = attacker["levy_entries"][0]
        levy["current_fighting_raw"] -= 10_000_000
        levy["soft_casualties_raw"] += 6_000_000
        levy["hard_casualties_raw"] += 4_000_000
        attacker["derived_current_fighting_raw"] -= 10_000_000
        attacker["derived_soft_casualties_raw"] += 6_000_000
        attacker[
            "derived_main_fighting_entry_hard_casualties_raw"
        ] += 4_000_000
        attacker["participant_hard_ledger"][0][
            "hard_casualties_raw"
        ] += 4_000_000
        attacker["participant_hard_total_raw"] += 4_000_000
        attacker["stored_current_matches_derived"] = False
        attacker["stored_levy_current_matches_derived"] = False
        history = [
            _battle_query_row(1, before),
            _battle_advance_row(2),
            _battle_query_row(3, after),
        ]

        plan = self.plan(history, frame=after)

        self.assertEqual(plan["selected_step"], "life-advance")
        self.assertFalse(
            plan["battle_transitions"][0]["phase_day_changed"]
        )
        self.assertTrue(plan["battle_transitions"][0]["ledger_changed"])

    def test_ack_date_and_revision_without_battle_transition_stays_blocked(
        self,
    ) -> None:
        before = _battle_frame()
        after = copy.deepcopy(before)
        after["snapshot_revision"] = NATIVE_REVISION + 1
        after["observed_date_raw"] = DATE_RAW + 24
        after["legality"]["elapsed_whole_days"] = 1
        history = [
            _battle_query_row(1, before),
            _battle_advance_row(2),
            _battle_query_row(3, after),
        ]

        plan = self.plan(history, frame=after)

        self.assertEqual(plan["phase"], "native_war_battle_transition_invalid")
        self.assertIsNone(plan["selected_step"])
        self.assertIn("ACK/date/revision", plan["battle_transition"]["reason"])

    def test_illegal_phase_regression_stays_blocked(self) -> None:
        before = _battle_frame()
        after = _next_battle_frame()
        after["phase"] = "maneuver"
        after["phase_raw"] = 0
        after["phase_day"] = 1
        after["legality"]["phase"] = "maneuver"
        after["legality"]["phase_raw"] = 0
        history = [
            _battle_query_row(1, before),
            _battle_advance_row(2),
            _battle_query_row(3, after),
        ]

        plan = self.plan(history, frame=after)

        self.assertEqual(plan["phase"], "native_war_battle_transition_invalid")
        self.assertIsNone(plan["selected_step"])

    def test_same_combat_pursuit_join_reopens_main_and_resets_winner(self) -> None:
        before = _battle_frame()
        before["phase"] = "pursuit"
        before["phase_raw"] = 2
        before["phase_day"] = 2
        before["winner_side"] = "attacker"
        before["winner_raw"] = 0
        before["legality"].update(
            {
                "native_boolean": False,
                "phase": "pursuit",
                "phase_raw": 2,
                "legal_now": False,
                "reason_codes_in_native_order": ["pursuit_or_done"],
                "native_reason_keys_in_native_order": [
                    "COMBAT_NO_RETREAT_PURSUIT"
                ],
            }
        )
        after = _next_battle_frame()
        after["phase"] = "main"
        after["phase_raw"] = 1
        after["phase_day"] = 2
        after["winner_side"] = "none"
        after["winner_raw"] = -1
        history = [
            _battle_query_row(1, before),
            _battle_advance_row(2),
            _battle_query_row(3, after),
        ]

        plan = self.plan(history, frame=after)

        self.assertEqual(plan["selected_step"], "life-advance")
        self.assertEqual(
            plan["battle_transitions"][0]["status"],
            "same_combat_reopened",
        )

    def test_nonfinal_battle_result_id_remains_ongoing(self) -> None:
        frame = _battle_frame()
        frame["battle_result_id"] = 553_648_135

        plan = self.plan([_battle_query_row(1, frame)], frame=frame)

        self.assertEqual(plan["selected_step"], "life-advance")
        self.assertNotEqual(plan["phase"], "native_war_battle_terminal_observed")

    def test_finalized_or_done_frame_uses_bounded_terminal_cleanup(self) -> None:
        finalized = _battle_frame()
        finalized["finalized"] = True
        done = _battle_frame()
        done["phase"] = "done"
        done["phase_raw"] = 3
        done["phase_day"] = 0
        done["winner_side"] = "attacker"
        done["winner_raw"] = 0
        done["legality"].update(
            {
                "native_boolean": False,
                "phase": "done",
                "phase_raw": 3,
                "legal_now": False,
                "reason_codes_in_native_order": ["pursuit_or_done"],
                "native_reason_keys_in_native_order": [
                    "COMBAT_NO_RETREAT_PURSUIT"
                ],
            }
        )
        for label, frame in (("finalized", finalized), ("done", done)):
            with self.subTest(label=label):
                plan = self.plan(
                    [_battle_query_row(1, frame)], frame=frame
                )
                self.assertEqual(
                    plan["phase"], "native_war_battle_terminal_cleanup"
                )
                self.assertEqual(plan["selected_step"], "life-advance")
                self.assertEqual(
                    plan["battle_transition"]["status"],
                    "terminal_observed",
                )
                self.assertIsNone(plan["battle_transition"]["outcome"])

        unsupported = self.plan(
            [_battle_query_row(1, finalized)],
            frame=finalized,
            steps=(STEP,),
        )
        self.assertEqual(
            unsupported["phase"],
            "native_war_battle_terminal_cleanup_unsupported",
        )
        self.assertIsNone(unsupported["selected_step"])
        self.assertEqual(unsupported["required_step"], "life-advance")

    def test_post_advance_retreat_is_explicit_left_combat_not_a_win_claim(
        self,
    ) -> None:
        before = _battle_frame()
        history = [
            _battle_query_row(1, before),
            _battle_advance_row(2),
        ]

        plan = self.plan(history, frame=None, army_state="retreating")

        self.assertEqual(plan["selected_step"], "life-advance")
        self.assertEqual(plan["battle_transitions"][0]["status"], "left_combat")
        self.assertEqual(
            plan["battle_transitions"][0]["observed_army_state"],
            "retreating",
        )
        self.assertNotIn("winner", plan["battle_transitions"][0])

    def test_changed_combat_id_is_recognized_before_new_battle_hold(self) -> None:
        before = _battle_frame()
        after = _next_battle_frame()
        after["combat_id"] = 335_544_326
        for role in ("attacker", "defender"):
            for army in after[role]["ordered_armies"]:
                army["combat_backlink_id"] = after["combat_id"]
        history = [
            _battle_query_row(1, before),
            _battle_advance_row(2),
            _battle_query_row(3, after),
        ]

        plan = self.plan(history, frame=after)

        self.assertEqual(plan["selected_step"], "life-advance")
        self.assertEqual(
            plan["battle_transitions"][0]["status"], "combat_replaced"
        )
class BattleControlSnapshotV1ContractTests(unittest.TestCase):
    def normalize(self, value: object) -> dict[str, object]:
        return normalize_battle_control_snapshot_v1(
            value,
            expected_subject_public_cunit_id=SUBJECT,
            expected_observed_date_raw=DATE_RAW,
            expected_snapshot_revision=NATIVE_REVISION,
        )

    def test_step_is_canonical_and_positive_full_cunit_bound(self) -> None:
        self.assertEqual(query_battle_control_snapshot_v1_step(SUBJECT), STEP)
        self.assertEqual(
            parse_query_battle_control_snapshot_v1_step(STEP), SUBJECT
        )
        for malformed in (
            "query-battle-control-snapshot-v1-0",
            "query-battle-control-snapshot-v1-01",
            "query-battle-control-snapshot-v1--1",
            "query-battle-control-snapshot-v1-2147483648",
            "query-battle-control-snapshot-v1-1-extra",
        ):
            self.assertIsNone(
                parse_query_battle_control_snapshot_v1_step(malformed)
            )

    def test_strict_frame_preserves_native_order_and_int64_raw_values(self) -> None:
        frame = _battle_frame()
        self.assertEqual(self.normalize(frame), frame)
        normalized = self.normalize(frame)
        self.assertEqual(normalized["base_advantage_raw"], -5_000_000_000)
        self.assertEqual(normalized["resolved_advantage_raw"], 6_000_000_000)
        self.assertEqual(
            [
                row["public_cunit_id"]
                for row in normalized["defender"]["ordered_armies"]
            ],
            [357, 33_554_657],
        )

    def test_available_legality_closes_all_four_gates_in_native_order(
        self,
    ) -> None:
        frame = _battle_frame()
        frame["side_flags"].update(
            {
                "disallow_retreat": True,
                "allow_early_retreat": False,
            }
        )
        frame["phase"] = "pursuit"
        frame["phase_raw"] = 2
        frame["legality"].update(
            {
                "native_boolean": False,
                "phase_raw": 2,
                "phase": "pursuit",
                "retreat_elapsed_baseline_date_raw": DATE_RAW - 14 * 24,
                "elapsed_whole_days": 14,
                "landless_gate_allows_retreat": False,
                "legal_now": False,
                "reason_codes_in_native_order": [
                    "disallowed",
                    "too_early",
                    "pursuit_or_done",
                    "landless",
                ],
                "native_reason_keys_in_native_order": [
                    "COMBAT_NO_RETREAT_DISALLOWED",
                    "COMBAT_NO_RETREAT_TOO_EARLY",
                    "COMBAT_NO_RETREAT_PURSUIT",
                    "COMBAT_NO_RETREAT_LANDLESS",
                ],
                "earliest_day_gate_date_raw": DATE_RAW + 24,
            }
        )

        normalized = self.normalize(frame)

        self.assertEqual(
            normalized["legality"]["reason_codes_in_native_order"],
            ["disallowed", "too_early", "pursuit_or_done", "landless"],
        )
        reordered = copy.deepcopy(frame)
        reordered["legality"]["reason_codes_in_native_order"][0:2] = [
            "too_early",
            "disallowed",
        ]
        with self.assertRaisesRegex(ValueError, "native gate order"):
            self.normalize(reordered)

    def test_available_and_unavailable_legality_are_not_conflated(self) -> None:
        available = self.normalize(_battle_frame())
        self.assertEqual(available["legality"]["status"], "available")
        self.assertTrue(available["legality"]["legal_now"])

        unavailable = _battle_frame()
        unavailable["legality"]["status"] = "unavailable"
        with self.assertRaisesRegex(ValueError, "legality is unavailable"):
            self.normalize(unavailable)

    def test_elapsed_and_earliest_day_gate_are_derived_from_raw_dates(
        self,
    ) -> None:
        normalized = self.normalize(_battle_frame())
        self.assertEqual(normalized["legality"]["elapsed_whole_days"], 0)
        self.assertEqual(
            normalized["legality"]["earliest_day_gate_date_raw"],
            DATE_RAW + 15 * 24,
        )

        forged_elapsed = _battle_frame()
        forged_elapsed["legality"]["elapsed_whole_days"] = 1
        with self.assertRaisesRegex(ValueError, "disagrees with raw dates"):
            self.normalize(forged_elapsed)

        forged_earliest = _battle_frame()
        forged_earliest["legality"]["earliest_day_gate_date_raw"] += 24
        with self.assertRaisesRegex(ValueError, "earliest_day_gate_date_raw"):
            self.normalize(forged_earliest)

    def test_full_side_and_owner_subset_preserve_owner_scan_stored_order(
        self,
    ) -> None:
        full_side = _battle_frame()
        full_side["attacker"]["ordered_armies"].append(
            _army_identity(404, 83_886_342, 29_829)
        )
        full_side["affected_public_cunit_ids_in_stored_order"] = [
            SUBJECT,
            83_886_342,
        ]
        normalized_full = self.normalize(full_side)
        self.assertEqual(normalized_full["side_scope"], "full_side")
        self.assertEqual(
            normalized_full["affected_public_cunit_ids_in_stored_order"],
            [SUBJECT, 83_886_342],
        )

        owner_subset = _battle_frame()
        owner_subset["attacker"]["ordered_armies"].extend(
            [
                _army_identity(405, 83_886_343, 41_001),
                _army_identity(406, 83_886_344, 29_829),
                _army_identity(407, 83_886_345, 41_002),
            ]
        )
        owner_subset["side_scope"] = "owner_subset"
        owner_subset["affected_public_cunit_ids_in_stored_order"] = [
            SUBJECT,
            83_886_344,
        ]
        owner_subset[
            "unaffected_same_side_public_cunit_ids_in_stored_order"
        ] = [83_886_343, 83_886_345]
        normalized_subset = self.normalize(owner_subset)
        self.assertEqual(normalized_subset["side_scope"], "owner_subset")
        self.assertEqual(
            normalized_subset[
                "unaffected_same_side_public_cunit_ids_in_stored_order"
            ],
            [83_886_343, 83_886_345],
        )

        reordered = copy.deepcopy(owner_subset)
        reordered[
            "unaffected_same_side_public_cunit_ids_in_stored_order"
        ].reverse()
        with self.assertRaisesRegex(ValueError, "stored-order scope"):
            self.normalize(reordered)

    def test_conditional_entry_hard_and_owner_history_remain_separate(self) -> None:
        normalized = self.normalize(_battle_frame())
        attacker = normalized["attacker"]
        main = attacker["levy_entries"][0]
        reserve = attacker["men_at_arms_entries"][0]
        self.assertEqual(main["hard_casualties_raw"], 500_000_000)
        self.assertEqual(reserve["hard_casualties_status"], "unavailable")
        self.assertIsNone(reserve["hard_casualties_raw"])
        self.assertEqual(
            attacker["derived_main_fighting_entry_hard_casualties_raw"],
            500_000_000,
        )
        self.assertEqual(attacker["participant_hard_total_raw"], 700_000_000)

        forged = _battle_frame()
        forged["attacker"]["men_at_arms_entries"][0][
            "hard_casualties_raw"
        ] = 3_000_000_000
        with self.assertRaisesRegex(ValueError, "non-main hard ledger"):
            self.normalize(forged)

    def test_accepts_truthfully_marked_tick_start_side_caches(self) -> None:
        frame = _battle_frame()
        attacker = frame["attacker"]
        attacker["stored_current_fighting_raw"] += 250_000_000
        attacker["stored_levy_current_fighting_raw"] += 250_000_000
        attacker["stored_current_matches_derived"] = False
        attacker["stored_levy_current_matches_derived"] = False

        normalized = self.normalize(frame)

        self.assertEqual(
            normalized["attacker"]["stored_current_fighting_raw"],
            4_250_000_000,
        )
        self.assertEqual(
            normalized["attacker"]["derived_current_fighting_raw"],
            4_000_000_000,
        )
        self.assertFalse(
            normalized["attacker"]["stored_current_matches_derived"]
        )

    def test_rejects_false_stored_cache_freshness_claim(self) -> None:
        frame = _battle_frame()
        frame["attacker"]["stored_current_fighting_raw"] += 1

        with self.assertRaisesRegex(ValueError, "freshness flags disagree"):
            self.normalize(frame)

    def test_rejects_schema_drift_mapping_drift_and_int64_overflow(self) -> None:
        extra = _battle_frame()
        extra["future_field"] = 1
        with self.assertRaisesRegex(ValueError, "malformed schema"):
            self.normalize(extra)

        mapping = _battle_frame()
        mapping["winner_side"] = "attacker"
        with self.assertRaisesRegex(ValueError, "winner mapping"):
            self.normalize(mapping)

        overflow = _battle_frame()
        entry = overflow["attacker"]["levy_entries"][0]
        entry["starting_raw"] = 2**63 - 1
        entry["current_fighting_raw"] = -1
        entry["soft_casualties_raw"] = 0
        entry["hard_casualties_raw"] = 2**63
        with self.assertRaisesRegex(ValueError, "signed int64"):
            self.normalize(overflow)

    def test_action_literal_is_advertised_only_for_paused_active_combat(self) -> None:
        armies = [
            {"army_id": SUBJECT, "controllable": True, "in_combat": True},
            {"army_id": 82, "controllable": True, "retreating": True},
            {"army_id": 83, "controllable": False, "in_combat": True},
        ]
        self.assertEqual(
            _action_steps(
                [QUERY_BATTLE_CONTROL_SNAPSHOT_V1_CAPABILITY],
                player_armies=armies,
                paused=True,
            ),
            [STEP],
        )
        self.assertEqual(
            _action_steps(
                [QUERY_BATTLE_CONTROL_SNAPSHOT_V1_CAPABILITY],
                player_armies=armies,
                paused=False,
            ),
            [],
        )


class _FakeEndpoint:
    def __init__(self) -> None:
        self.pipe_name = r"\\.\pipe\xar_battle_control_v1_fixture"
        self.frames: list[dict[str, object]] = []
        self.on_frame = None
        self.on_disconnect = None
        self.send_hook = None

    def start(self, on_frame, on_disconnect) -> None:
        self.on_frame = on_frame
        self.on_disconnect = on_disconnect

    def publish(self, frame: dict[str, object]) -> None:
        assert self.on_frame is not None
        self.on_frame(frame)

    def send(self, frame: dict[str, object]) -> None:
        self.frames.append(frame)
        if self.send_hook is not None:
            self.send_hook(frame)

    def close(self) -> None:
        return None

    def transport_error(self) -> str | None:
        return None


def _native_driver() -> tuple[NativeHeadlessGameplayDriver, _FakeEndpoint]:
    endpoint = _FakeEndpoint()
    driver = NativeHeadlessGameplayDriver(
        endpoint.pipe_name,
        endpoint=endpoint,
        command_timeout_seconds=0.1,
    )
    endpoint.publish(
        {
            "type": "hello",
            "protocol_version": 1,
            "bridge_version": "0.1.0",
            "pid": 4545,
            "session_generation": 0,
            "game_version": "1.19.0.6",
            "executable_sha256": "a" * 64,
            "capabilities": [
                "game.state.snapshot",
                QUERY_BATTLE_CONTROL_SNAPSHOT_V1_CAPABILITY,
            ],
        }
    )
    endpoint.publish(_semantic_snapshot())
    return driver, endpoint


def _answer_with(endpoint: _FakeEndpoint, result_factory) -> None:
    def answer(frame: dict[str, object]) -> None:
        if frame.get("type") != "execute_step":
            return
        endpoint.publish(
            {
                "type": "command_result",
                "protocol_version": 1,
                "request_id": frame["request_id"],
                "ok": True,
                "result": result_factory(),
            }
        )

    endpoint.send_hook = answer


class BattleControlSnapshotV1NativeDriverTests(unittest.TestCase):
    def test_atomic_query_is_normalized_and_cached_on_only_the_same_frame(
        self,
    ) -> None:
        driver, endpoint = _native_driver()
        capabilities = driver.capabilities()
        self.assertTrue(
            capabilities["battle_control_snapshot_v1_query_supported"]
        )
        self.assertIn(STEP, capabilities["action_steps"])
        self.assertNotIn(
            QUERY_BATTLE_CONTROL_SNAPSHOT_V1_CAPABILITY,
            capabilities["action_steps"],
        )
        _answer_with(endpoint, _native_result)
        revision = int(driver.take_snapshot()["revision"])

        result = driver.execute_step(STEP, expected_revision=revision)

        self.assertEqual(result["status"], "available")
        self.assertEqual(
            result["battle_control_snapshot"]["combat_id"], 335_544_325
        )
        self.assertEqual(result["selected_public_cunit_id"], SUBJECT)
        self.assertEqual(result["side_scope"], "full_side")
        self.assertEqual(
            result["legality"],
            result["battle_control_snapshot"]["legality"],
        )
        cached = driver.take_snapshot()
        self.assertEqual(
            cached["battle_control_snapshot_v1_status"], "available"
        )
        self.assertEqual(
            cached["battle_control_snapshot_v1"]["subject_public_cunit_id"],
            SUBJECT,
        )

        frozen = copy.deepcopy(driver._battle_control_snapshot_v1_query)
        assert isinstance(frozen, dict)
        tampered = copy.deepcopy(frozen)
        tampered["cache_binding"]["date_raw"] += 1
        driver._battle_control_snapshot_v1_query = tampered
        self.assertIsNone(driver.take_snapshot()["battle_control_snapshot_v1"])

        driver._battle_control_snapshot_v1_query = frozen
        endpoint.publish(_semantic_snapshot(NATIVE_REVISION + 1))
        self.assertIsNone(driver.take_snapshot()["battle_control_snapshot_v1"])

    def test_malformed_payload_and_same_frame_drift_are_rejected(self) -> None:
        driver, endpoint = _native_driver()

        def malformed() -> dict[str, object]:
            result = _native_result()
            del result["battle_control_snapshot"]["attacker"][
                "participant_hard_total_raw"
            ]
            return result

        _answer_with(endpoint, malformed)
        with self.assertRaisesRegex(BridgeUnavailableError, "malformed frame"):
            driver.execute_step(
                STEP, expected_revision=int(driver.take_snapshot()["revision"])
            )

        driver, endpoint = _native_driver()

        def drift_after_answer() -> dict[str, object]:
            result = _native_result()
            endpoint.publish(_semantic_snapshot(NATIVE_REVISION + 1))
            return result

        _answer_with(endpoint, drift_after_answer)
        with self.assertRaisesRegex(BridgeUnavailableError, "crossed"):
            driver.execute_step(
                STEP, expected_revision=int(driver.take_snapshot()["revision"])
            )

    def test_transient_native_query_error_retries_same_frame_once(self) -> None:
        driver, endpoint = _native_driver()
        attempts = 0

        def answer(frame: dict[str, object]) -> None:
            nonlocal attempts
            if frame.get("type") != "execute_step":
                return
            attempts += 1
            if attempts == 1:
                endpoint.publish(
                    {
                        "type": "command_result",
                        "protocol_version": 1,
                        "request_id": frame["request_id"],
                        "ok": False,
                        "error": TRANSIENT_QUERY_ERROR,
                    }
                )
                return
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": _native_result(),
                }
            )

        endpoint.send_hook = answer
        revision = int(driver.take_snapshot()["revision"])

        result = driver.execute_step(STEP, expected_revision=revision)

        self.assertEqual(attempts, 2)
        self.assertEqual(result["status"], "available")
        self.assertEqual(result["query_sequence"], 41)

    def test_persistent_transient_query_error_stops_after_three_attempts(
        self,
    ) -> None:
        driver, endpoint = _native_driver()
        attempts = 0

        def answer(frame: dict[str, object]) -> None:
            nonlocal attempts
            if frame.get("type") != "execute_step":
                return
            attempts += 1
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": False,
                    "error": TRANSIENT_QUERY_ERROR,
                }
            )

        endpoint.send_hook = answer
        with self.assertRaisesRegex(
            BridgeUnavailableError, TRANSIENT_QUERY_ERROR
        ) as rejected:
            driver.execute_step(
                STEP, expected_revision=int(driver.take_snapshot()["revision"])
            )

        self.assertEqual(attempts, 3)
        self.assertEqual(
            getattr(rejected.exception, "native_error", None),
            TRANSIENT_QUERY_ERROR,
        )

    def test_transient_query_error_does_not_retry_after_snapshot_drift(
        self,
    ) -> None:
        driver, endpoint = _native_driver()
        attempts = 0

        def answer(frame: dict[str, object]) -> None:
            nonlocal attempts
            if frame.get("type") != "execute_step":
                return
            attempts += 1
            endpoint.publish(_semantic_snapshot(NATIVE_REVISION + 1))
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": False,
                    "error": TRANSIENT_QUERY_ERROR,
                }
            )

        endpoint.send_hook = answer
        with self.assertRaisesRegex(
            BridgeUnavailableError, TRANSIENT_QUERY_ERROR
        ) as rejected:
            driver.execute_step(
                STEP, expected_revision=int(driver.take_snapshot()["revision"])
            )

        self.assertEqual(attempts, 1)
        self.assertEqual(
            getattr(rejected.exception, "native_error", None),
            TRANSIENT_QUERY_ERROR,
        )

    def test_unrelated_native_query_error_is_not_retried(self) -> None:
        driver, endpoint = _native_driver()
        attempts = 0
        native_error = "CK3 unrelated battle-control failure"

        def answer(frame: dict[str, object]) -> None:
            nonlocal attempts
            if frame.get("type") != "execute_step":
                return
            attempts += 1
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": False,
                    "error": native_error,
                }
            )

        endpoint.send_hook = answer
        with self.assertRaisesRegex(
            BridgeUnavailableError, native_error
        ) as rejected:
            driver.execute_step(
                STEP, expected_revision=int(driver.take_snapshot()["revision"])
            )

        self.assertEqual(attempts, 1)
        self.assertEqual(
            getattr(rejected.exception, "native_error", None), native_error
        )


class _ServiceDriver:
    def __init__(
        self,
        *,
        advertise: bool = True,
        drift: bool = False,
        mirror_drift: bool = False,
    ) -> None:
        self.advertise = advertise
        self.drift = drift
        self.mirror_drift = mirror_drift
        self.calls = 0

    def capabilities(self) -> dict[str, object]:
        return {
            "format_version": 1,
            "backend_id": "battle-control-fixture",
            "source": "named-pipe",
            "snapshot": True,
            "wait_for_change": False,
            "action_steps": [STEP] if self.advertise else [],
            "bridge_capabilities": (
                [QUERY_BATTLE_CONTROL_SNAPSHOT_V1_CAPABILITY]
                if self.advertise
                else []
            ),
        }

    def take_snapshot(self) -> dict[str, object]:
        self.calls += 1
        revision = 4 + (1 if self.drift and self.calls > 1 else 0)
        return {
            "format_version": 1,
            "snapshot_id": f"battle-control-fixture:{revision}",
            "revision": revision,
            "native_revision": NATIVE_REVISION,
            "source": "named-pipe",
            "backend_id": "battle-control-fixture",
            "date_raw": DATE_RAW,
            "paused": True,
            "episode_run_id": "native-29829-fixture",
            "diagnostics": {
                "hello": {
                    "game_version": "1.19.0.6",
                    "executable_sha256": "a" * 64,
                }
            },
        }

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        if step != STEP or expected_revision != 4:
            raise AssertionError("service changed the battle query binding")
        result = _service_result()
        if self.mirror_drift:
            result["side_scope"] = "owner_subset"
        return result

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        raise AssertionError("battle-control observation must not advance time")


class BattleControlSnapshotV1ServiceTests(unittest.TestCase):
    def test_service_requires_capability_revision_and_same_paused_frame(self) -> None:
        with self.assertRaises(UnsupportedStepError):
            GameplayBridgeService(
                _ServiceDriver(advertise=False)
            ).query_battle_control_snapshot_v1(
                SUBJECT,
                expected_revision=4,
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "revision mismatch"):
            GameplayBridgeService(
                _ServiceDriver()
            ).query_battle_control_snapshot_v1(
                SUBJECT,
                expected_revision=3,
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "crossed"):
            GameplayBridgeService(
                _ServiceDriver(drift=True)
            ).query_battle_control_snapshot_v1(
                SUBJECT,
                expected_revision=4,
            )

    def test_service_returns_typed_frame_without_win_probability(self) -> None:
        result = GameplayBridgeService(
            _ServiceDriver()
        ).query_battle_control_snapshot_v1(
            SUBJECT,
            expected_revision=4,
        )
        self.assertEqual(result["status"], "available")
        self.assertTrue(result["battle_control_ready"])
        self.assertEqual(result["subject_army_id"], SUBJECT)
        self.assertEqual(result["selected_public_cunit_id"], SUBJECT)
        self.assertEqual(
            result["side_scope"],
            result["battle_control_snapshot"]["side_scope"],
        )
        self.assertEqual(
            result["affected_public_cunit_ids_in_stored_order"],
            result["battle_control_snapshot"][
                "affected_public_cunit_ids_in_stored_order"
            ],
        )
        self.assertEqual(
            result["side_flags"],
            result["battle_control_snapshot"]["side_flags"],
        )
        self.assertEqual(
            result["legality"],
            result["battle_control_snapshot"]["legality"],
        )
        self.assertEqual(
            result["battle_control_snapshot"]["phase"], "main"
        )
        self.assertNotIn("win_probability", result)

        with self.assertRaisesRegex(
            BridgeUnavailableError, "active-retreat mirror disagrees"
        ):
            GameplayBridgeService(
                _ServiceDriver(mirror_drift=True)
            ).query_battle_control_snapshot_v1(
                SUBJECT,
                expected_revision=4,
            )


@unittest.skipIf(
    importlib.util.find_spec("mcp") is None,
    "optional MCP SDK not installed",
)
class BattleControlSnapshotV1McpTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_client_lists_and_calls_battle_control_tool(self) -> None:
        from mcp import Client

        server = create_server(_ServiceDriver())
        async with Client(server) as client:
            listed = await client.list_tools()
            names = {tool.name for tool in listed.tools}
            self.assertIn("ck3_query_battle_control_snapshot_v1", names)
            result = await client.call_tool(
                "ck3_query_battle_control_snapshot_v1",
                {
                    "subject_army_id": SUBJECT,
                    "expected_revision": 4,
                },
            )

        self.assertFalse(result.is_error)
        payload = result.structured_content
        self.assertTrue(payload["battle_control_ready"])
        self.assertEqual(payload["selected_public_cunit_id"], SUBJECT)
        self.assertEqual(
            payload["legality"],
            payload["battle_control_snapshot"]["legality"],
        )
        self.assertEqual(
            payload["battle_control_snapshot"]["combat_id"], 335_544_325
        )


if __name__ == "__main__":
    unittest.main()
