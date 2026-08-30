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
from xar_autoplayer.bridge.battle_terminal_transition_contract import (
    QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY,
    query_battle_terminal_transition_v1_step,
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
from xar_autoplayer.bridge.war_contract import (
    battle_decision_epoch_advance_step,
    committed_route_sentinel_advance_step,
    war_objective_hold_sentinel_advance_step,
)
from xar_autoplayer.strategy import (
    _battle_sentinel_advance_validation,
    choose_one_life_turn,
)


SUBJECT = 83_886_341
NATIVE_SUBJECT = 101
NATIVE_REVISION = 5
DATE_RAW = 53_178_264
STEP = f"query-battle-control-snapshot-v1-{SUBJECT}"
TRANSIENT_QUERY_ERROR = "CK3 battle-control state changed during query"
IDENTITY_PENDING_DIAGNOSTIC = (
    "active_combat_identity_subject_combat_id_invalid"
)
IDENTITY_PENDING_QUERY_ERROR = (
    f"{TRANSIENT_QUERY_ERROR} ({IDENTITY_PENDING_DIAGNOSTIC})"
)


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


def _with_combat_id(
    frame: dict[str, object], combat_id: int
) -> dict[str, object]:
    result = copy.deepcopy(frame)
    result["combat_id"] = combat_id
    for side_name in ("attacker", "defender"):
        side = result[side_name]
        assert isinstance(side, dict)
        armies = side["ordered_armies"]
        assert isinstance(armies, list)
        for army in armies:
            assert isinstance(army, dict)
            army["combat_backlink_id"] = combat_id
    return result


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


def _battle_advance_row(
    index: int,
    *,
    ending_date_raw: int = DATE_RAW + 24,
    elapsed_days: int = 1,
) -> dict[str, object]:
    return {
        "index": index,
        "command": "life-advance",
        "ok": True,
        "result": {
            "step": "life-advance",
            "starting_date_raw": DATE_RAW,
            "ending_date_raw": ending_date_raw,
            "elapsed_days": elapsed_days,
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
        "map_ready": True,
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


def _next_battle_frame(*, elapsed_days: int = 1) -> dict[str, object]:
    frame = _battle_frame()
    frame["snapshot_revision"] = NATIVE_REVISION + elapsed_days
    frame["observed_date_raw"] = DATE_RAW + 24 * elapsed_days
    frame["phase_day"] = int(frame["phase_day"]) + elapsed_days
    frame["legality"]["elapsed_whole_days"] = elapsed_days
    return frame


class BattleControlStrategyTests(unittest.TestCase):
    def plan(
        self,
        history: list[dict[str, object]],
        *,
        frame: dict[str, object] | None,
        army_state: str = "combat",
        steps: tuple[str, ...] = (STEP, "life-advance"),
        snapshot_overrides: dict[str, object] | None = None,
    ) -> dict[str, object]:
        snapshot = _planner_battle_snapshot(
            frame=frame,
            army_state=army_state,
        )
        if isinstance(snapshot_overrides, dict):
            snapshot.update(copy.deepcopy(snapshot_overrides))
        return choose_one_life_turn(
            history,
            snapshot=snapshot,
            action_steps=steps,
        )

    def test_identity_pending_allows_one_explicit_materialization_day(
        self,
    ) -> None:
        pending = {
            "battle_control_snapshot_v1": None,
            "battle_control_snapshot_v1_status": "identity_pending",
            "battle_control_snapshot_v1_query_sequence": None,
            "battle_control_snapshot_v1_query_attempts": 3,
            "battle_control_snapshot_v1_diagnostic_reason": (
                IDENTITY_PENDING_DIAGNOSTIC
            ),
            "battle_control_snapshot_v1_native_query_status": "state_changed",
            "battle_control_snapshot_v1_subject_army_id": SUBJECT,
            "battle_control_snapshot_v1_queried_snapshot_id": (
                f"native:{NATIVE_REVISION}"
            ),
            "battle_control_snapshot_v1_queried_revision": NATIVE_REVISION,
            "battle_control_snapshot_v1_queried_native_revision": (
                NATIVE_REVISION
            ),
        }

        plan = self.plan([], frame=None, snapshot_overrides=pending)

        self.assertEqual(
            plan["phase"], "native_war_battle_identity_materialization"
        )
        self.assertEqual(plan["selected_step"], "life-advance")
        self.assertEqual(
            plan["next_revision_requirement"], "full_combat_id"
        )

    def test_identity_pending_after_materialization_stays_blocked(
        self,
    ) -> None:
        pending = {
            "battle_control_snapshot_v1": None,
            "battle_control_snapshot_v1_status": "identity_pending",
            "battle_control_snapshot_v1_query_sequence": None,
            "battle_control_snapshot_v1_query_attempts": 3,
            "battle_control_snapshot_v1_diagnostic_reason": (
                IDENTITY_PENDING_DIAGNOSTIC
            ),
            "battle_control_snapshot_v1_native_query_status": "state_changed",
            "battle_control_snapshot_v1_subject_army_id": SUBJECT,
            "battle_control_snapshot_v1_queried_snapshot_id": (
                f"native:{NATIVE_REVISION}"
            ),
            "battle_control_snapshot_v1_queried_revision": NATIVE_REVISION,
            "battle_control_snapshot_v1_queried_native_revision": (
                NATIVE_REVISION
            ),
        }
        materialization = {
            "index": 1,
            "command": "life-advance",
            "ok": True,
            "result": {
                "step": "life-advance",
                "starting_date_raw": DATE_RAW - 24,
                "ending_date_raw": DATE_RAW,
                "elapsed_days": 1,
                "timeline_speed": 1,
                "timeline_policy": (
                    "exact_one_day_battle_identity_materialization"
                ),
                "paused": True,
                "battle_identity_materialization": {
                    "schema_version": 1,
                    "status": "one_day_advanced",
                    "proof_kind": "battle_identity_materialization",
                    "diagnostic_reason": IDENTITY_PENDING_DIAGNOSTIC,
                    "subject_public_cunit_id": SUBJECT,
                    "starting_snapshot_id": (
                        f"native:{NATIVE_REVISION - 1}"
                    ),
                    "starting_revision": NATIVE_REVISION - 1,
                    "starting_native_revision": NATIVE_REVISION - 1,
                    "starting_date_raw": DATE_RAW - 24,
                    "ending_snapshot_id": f"native:{NATIVE_REVISION}",
                    "ending_revision": NATIVE_REVISION,
                    "ending_native_revision": NATIVE_REVISION,
                    "ending_date_raw": DATE_RAW,
                    "elapsed_days": 1,
                    "next_revision_requirement": "full_combat_id",
                },
            },
        }

        plan = self.plan(
            [materialization],
            frame=None,
            snapshot_overrides=pending,
        )

        self.assertEqual(
            plan["phase"],
            "native_war_battle_identity_materialization_failed",
        )
        self.assertIsNone(plan["selected_step"])
        self.assertEqual(
            plan["required_observation"],
            "full-current-revision-CombatID",
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

    def test_correlated_two_day_pause_overshoot_unlocks_next_slice(
        self,
    ) -> None:
        before = _battle_frame()
        after = _next_battle_frame(elapsed_days=2)
        history = [
            _battle_query_row(1, before),
            _battle_advance_row(
                2,
                ending_date_raw=DATE_RAW + 48,
                elapsed_days=2,
            ),
            _battle_query_row(3, after),
        ]

        plan = self.plan(history, frame=after)

        self.assertEqual(plan["selected_step"], "life-advance")
        transition = plan["battle_transitions"][0]
        self.assertEqual(transition["status"], "same_combat_advanced")
        self.assertEqual(transition["observed_date_delta_raw"], 48)
        self.assertEqual(transition["advance_elapsed_days"], 2)
        self.assertEqual(transition["actual_elapsed_days"], 2)

    def test_two_day_overshoot_cannot_skip_three_phase_days(self) -> None:
        before = _battle_frame()
        after = _next_battle_frame(elapsed_days=2)
        after["phase_day"] = int(before["phase_day"]) + 3
        history = [
            _battle_query_row(1, before),
            _battle_advance_row(
                2,
                ending_date_raw=DATE_RAW + 48,
                elapsed_days=2,
            ),
            _battle_query_row(3, after),
        ]

        plan = self.plan(history, frame=after)

        self.assertEqual(plan["phase"], "native_war_battle_transition_invalid")
        self.assertIsNone(plan["selected_step"])
        self.assertIn("skipped", plan["battle_transition"]["reason"])

    def test_two_day_frame_rejects_one_day_action_report(self) -> None:
        before = _battle_frame()
        after = _next_battle_frame(elapsed_days=2)
        history = [
            _battle_query_row(1, before),
            _battle_advance_row(2),
            _battle_query_row(3, after),
        ]

        plan = self.plan(history, frame=after)

        self.assertEqual(plan["phase"], "native_war_battle_transition_invalid")
        self.assertIsNone(plan["selected_step"])
        self.assertIn(
            "does not match the observed battle dates",
            plan["battle_transition"]["reason"],
        )

    def test_three_day_pause_overshoot_stays_blocked(self) -> None:
        before = _battle_frame()
        after = _next_battle_frame(elapsed_days=3)
        history = [
            _battle_query_row(1, before),
            _battle_advance_row(
                2,
                ending_date_raw=DATE_RAW + 72,
                elapsed_days=3,
            ),
            _battle_query_row(3, after),
        ]

        plan = self.plan(history, frame=after)

        self.assertEqual(plan["phase"], "native_war_battle_transition_invalid")
        self.assertIsNone(plan["selected_step"])
        self.assertIn(
            "two-day pause-settle envelope",
            plan["battle_transition"]["reason"],
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


DECISION_SENTINEL_STEP = "battle-decision-epoch-advance"
TERMINAL_SENTINEL_STEP = "battle-terminal-cruise"
_ALL_BATTLE_SPEED_GATES = {
    "decision_sentinel_live_ready": True,
    "terminal_sentinel_live_ready": True,
    "overwhelming_matrix_live_ready": True,
}
_TERMINAL_ONLY_BATTLE_SPEED_GATES = {
    "decision_sentinel_live_ready": False,
    "terminal_sentinel_live_ready": True,
    "overwhelming_matrix_live_ready": False,
}
_BATTLE_SPEED_GATES_WITHOUT_OVERWHELMING = {
    "decision_sentinel_live_ready": True,
    "terminal_sentinel_live_ready": True,
    "overwhelming_matrix_live_ready": False,
}


def _crushing_battle_frame() -> dict[str, object]:
    frame = _battle_frame()
    attacker = frame["attacker"]
    levy = attacker["levy_entries"][0]
    levy.update(
        {
            "starting_raw": 12_000_000_000,
            "current_fighting_raw": 10_000_000_000,
            "soft_casualties_raw": 500_000_000,
            "hard_casualties_raw": 1_500_000_000,
            "entry_strength_raw": 300_000,
        }
    )
    attacker.update(
        {
            "stored_current_fighting_raw": 10_000_000_000,
            "stored_levy_current_fighting_raw": 10_000_000_000,
            "derived_current_fighting_raw": 10_000_000_000,
            "derived_soft_casualties_raw": 500_000_000,
            "derived_main_fighting_entry_hard_casualties_raw": (
                1_500_000_000
            ),
            "participant_hard_total_raw": 1_500_000_000,
            "side_strength_raw": 300_000,
        }
    )
    attacker["participant_hard_ledger"][0][
        "hard_casualties_raw"
    ] = 1_500_000_000
    return frame


def _pursuit_battle_frame() -> dict[str, object]:
    frame = _battle_frame()
    frame.update(
        {
            "phase": "pursuit",
            "phase_raw": 2,
            "phase_day": 0,
            "winner_side": "attacker",
            "winner_raw": 0,
        }
    )
    frame["legality"].update(
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
    return frame


def _rebind_battle_frame(
    frame: dict[str, object],
    *,
    subject: int,
    native_subject: int,
    combat_id: int,
    province_id: int,
) -> dict[str, object]:
    rebound = copy.deepcopy(frame)
    rebound.update(
        {
            "subject_public_cunit_id": subject,
            "subject_native_carmy_id": native_subject,
            "combat_id": combat_id,
            "province_id": province_id,
            "selected_public_cunit_id": subject,
            "selected_native_carmy_id": native_subject,
            "combat_province_id": province_id,
            "affected_public_cunit_ids_in_stored_order": [subject],
        }
    )
    attacker = rebound["attacker"]
    attacker_army = attacker["ordered_armies"][0]
    attacker_army.update(
        {
            "native_carmy_id": native_subject,
            "public_cunit_id": subject,
            "combat_backlink_id": combat_id,
        }
    )
    for entry in [
        *attacker["levy_entries"],
        *attacker["men_at_arms_entries"],
    ]:
        entry["native_carmy_id"] = native_subject
        entry["public_cunit_id"] = subject
    for defender_army in rebound["defender"]["ordered_armies"]:
        defender_army["combat_backlink_id"] = combat_id
    return rebound


def _multi_battle_snapshot(
    frames: list[dict[str, object]],
    *,
    extra_idle_army_id: int | None = None,
) -> dict[str, object]:
    snapshot = _planner_battle_snapshot(frame=frames[0])
    player_armies = [
        {
            "army_id": int(frame["subject_public_cunit_id"]),
            "owner_character_id": 29_829,
            "soldiers": 40_000,
            "current_province_id": int(frame["province_id"]),
            "move_target_province_id": None,
            "controllable": True,
            "in_combat": True,
            "army_state": "combat",
            "army_state_code": 2,
        }
        for frame in frames
    ]
    if extra_idle_army_id is not None:
        player_armies.append(
            {
                "army_id": extra_idle_army_id,
                "owner_character_id": 29_829,
                "soldiers": 1_000,
                "current_province_id": 9999,
                "move_target_province_id": None,
                "controllable": True,
                "in_combat": False,
                "army_state": "regular",
                "army_state_code": 0,
            }
        )
    snapshot["player_armies"] = player_armies
    snapshot["active_wars"][0]["allied_armies"] = player_armies
    return snapshot


def _active_terminal_transition_frame(
    battle: dict[str, object],
    *,
    latest_sequence: int = 40,
) -> dict[str, object]:
    combat_id = int(battle["combat_id"])
    subject = int(battle["subject_public_cunit_id"])
    attacker_ids = [
        int(row["public_cunit_id"])
        for row in battle["attacker"]["ordered_armies"]
    ]
    defender_ids = [
        int(row["public_cunit_id"])
        for row in battle["defender"]["ordered_armies"]
    ]
    return {
        "schema_version": 1,
        "contract_stage": "production_exact_battle_terminal_transition",
        "status": "available",
        "unavailable_reason": None,
        "battle_terminal_transition_ready": True,
        "snapshot_revision": battle["snapshot_revision"],
        "observed_date_raw": battle["observed_date_raw"],
        "prior_combat_id": combat_id,
        "subject_public_cunit_id": subject,
        "terminal_journal": {
            "requested_after_sequence": None,
            "oldest_available_sequence": 1,
            "latest_sequence": latest_sequence,
            "event_sequence": None,
            "event_status": "not_observed",
        },
        "prior": {
            "combat_id": combat_id,
            "terminal_kind": "active_not_terminal",
            "terminal_date_raw": None,
            "suppress_normal_result_envelopes": None,
            "phase_raw": battle["phase_raw"],
            "phase_day": battle["phase_day"],
            "winner_raw": battle["winner_raw"],
            "finalized_before": False,
            "daily_guard_raw": 0,
            "province_id": battle["province_id"],
            "battle_result_id": battle["battle_result_id"],
            "wipe_raw": None,
            "attacker_primary_participant_character_id": battle[
                "attacker"
            ]["primary_participant_character_id"],
            "defender_primary_participant_character_id": battle[
                "defender"
            ]["primary_participant_character_id"],
            "attacker_public_cunit_ids_in_stored_order": attacker_ids,
            "defender_public_cunit_ids_in_stored_order": defender_ids,
            "battle_warscore": {
                "status": "unavailable",
                "war_id": None,
                "war_battle_row_index": None,
                "value_raw_q100000": None,
                "winner_is_war_attacker": None,
                "combat_side0_is_war_attacker": None,
                "attacker_relative_delta_raw_q100000": None,
            },
        },
        "removal": {
            "prior_combat_strictly_resolves": True,
            "prior_province_strictly_resolves": True,
            "prior_province_contains_prior_combat_id": True,
            "result_strictly_resolves": None,
            "result_relevant_player_count": None,
        },
        "subject": {
            "exists": True,
            "current_province_id": battle["province_id"],
            "native_carmy_id": battle["subject_native_carmy_id"],
            "combat_backlink_id": combat_id,
            "active_combat_id": combat_id,
            "movement_or_retreat_state_raw": 0,
            "move_target_province_id": None,
            "route_province_ids_in_stored_order": [],
            "ai_membership_status": "none",
            "coordinator_id": None,
            "unit_stack_stored_index": None,
            "subunit_stored_index": None,
            "blocked_by_active_combat": True,
        },
        "successor": {
            "state": "unavailable",
            "matching_combat_ids_in_native_order": [],
            "selected_successor_combat_id": None,
            "participant_overlap_public_cunit_ids_in_prior_order": [],
        },
    }


def _terminal_cursor_query_row(
    index: int,
    battle: dict[str, object],
    *,
    latest_sequence: int = 40,
) -> dict[str, object]:
    combat_id = int(battle["combat_id"])
    subject = int(battle["subject_public_cunit_id"])
    step = query_battle_terminal_transition_v1_step(combat_id, subject)
    frame = _active_terminal_transition_frame(
        battle, latest_sequence=latest_sequence
    )
    return {
        "index": index,
        "command": step,
        "ok": True,
        "result": {
            "step": step,
            "accepted": True,
            "status": "available",
            "query_sequence": index,
            "snapshot_revision": battle["snapshot_revision"],
            "battle_terminal_transition": frame,
            "queried_snapshot_id": f"native:{battle['snapshot_revision']}",
            "queried_revision": battle["snapshot_revision"],
            "queried_native_revision": battle["snapshot_revision"],
        },
    }


def _observed_terminal_transition_frame(
    battle: dict[str, object],
    *,
    cursor: int,
    observed_date_raw: int,
    snapshot_revision: int,
) -> dict[str, object]:
    frame = _active_terminal_transition_frame(
        battle, latest_sequence=cursor
    )
    frame.update(
        {
            "snapshot_revision": snapshot_revision,
            "observed_date_raw": observed_date_raw,
        }
    )
    frame["terminal_journal"] = {
        "requested_after_sequence": cursor,
        "oldest_available_sequence": 1,
        "latest_sequence": cursor + 1,
        "event_sequence": cursor + 1,
        "event_status": "observed",
    }
    frame["prior"].update(
        {
            "terminal_kind": "normal_result",
            "terminal_date_raw": observed_date_raw,
            "suppress_normal_result_envelopes": False,
            "phase_raw": 3,
            "phase_day": 0,
            "winner_raw": 0,
            "battle_warscore": {
                "status": "not_recorded_by_native",
                "war_id": None,
                "war_battle_row_index": None,
                "value_raw_q100000": None,
                "winner_is_war_attacker": None,
                "combat_side0_is_war_attacker": None,
                "attacker_relative_delta_raw_q100000": None,
            },
        }
    )
    frame["removal"] = {
        "prior_combat_strictly_resolves": False,
        "prior_province_strictly_resolves": True,
        "prior_province_contains_prior_combat_id": False,
        "result_strictly_resolves": None,
        "result_relevant_player_count": None,
    }
    frame["subject"].update(
        {
            "combat_backlink_id": None,
            "active_combat_id": None,
            "movement_or_retreat_state_raw": 0,
            "ai_membership_status": "none",
            "coordinator_id": None,
            "unit_stack_stored_index": None,
            "subunit_stored_index": None,
            "blocked_by_active_combat": False,
        }
    )
    frame["successor"] = {
        "state": "no_successor",
        "matching_combat_ids_in_native_order": [],
        "selected_successor_combat_id": None,
        "participant_overlap_public_cunit_ids_in_prior_order": [],
    }
    return frame


def _observed_terminal_query_row(
    index: int,
    battle: dict[str, object],
    *,
    cursor: int,
    observed_date_raw: int,
    snapshot_revision: int,
) -> dict[str, object]:
    combat_id = int(battle["combat_id"])
    subject = int(battle["subject_public_cunit_id"])
    step = query_battle_terminal_transition_v1_step(
        combat_id, subject, cursor
    )
    frame = _observed_terminal_transition_frame(
        battle,
        cursor=cursor,
        observed_date_raw=observed_date_raw,
        snapshot_revision=snapshot_revision,
    )
    return {
        "index": index,
        "command": step,
        "ok": True,
        "result": {
            "step": step,
            "accepted": True,
            "status": "available",
            "query_sequence": index,
            "snapshot_revision": snapshot_revision,
            "battle_terminal_transition": frame,
            "queried_snapshot_id": f"native:{snapshot_revision}",
            "queried_revision": snapshot_revision,
            "queried_native_revision": snapshot_revision,
        },
    }


def _sentinel_advance_row(
    index: int,
    *,
    step: str = DECISION_SENTINEL_STEP,
    elapsed_days: int = 5,
    watch_army_ids: list[int] | None = None,
    terminal: bool = False,
    native_pause: bool = False,
    target_date_raw: int | None = None,
) -> dict[str, object]:
    speed = 5 if step == TERMINAL_SENTINEL_STEP else 3
    mode = (
        "terminal_or_sentinel"
        if step == TERMINAL_SENTINEL_STEP
        else "decision_epoch"
    )
    target = target_date_raw or DATE_RAW + 45 * 24
    ending = DATE_RAW + elapsed_days * 24
    watched = list(watch_army_ids or [SUBJECT])
    reasons = [
        "combat_terminal"
        if terminal
        else "native_pause"
        if native_pause
        else "combat_phase_changed"
    ]
    armed = {
        "state": "armed",
        "generation": 7,
        "starting_date_raw": DATE_RAW,
        "target_date_raw": target,
        "last_observed_date_raw": DATE_RAW,
        "trigger_date_raw": 0,
        "speed": speed,
        "mode": mode,
        "army_count": len(watched),
        "combat_count": 1,
        "completed_daily_ticks": 0,
        "intermediate_pause_count": 0,
        "trigger_flags": 0,
        "trigger_reasons": [],
        "signed_date_delta_from_target_raw": 0,
        "overshoot_days": -1,
        "pause_wrapper_called": False,
        "pause_observed": False,
        "terminal_observed": False,
        "abnormal": False,
    }
    return {
        "index": index,
        "command": step,
        "ok": True,
        "result": {
            "step": step,
            "starting_date_raw": DATE_RAW,
            "target_date_raw": target,
            "ending_date_raw": ending,
            "elapsed_days": elapsed_days,
            "requested_horizon_days": (target - DATE_RAW) // 24,
            "timeline_speed": speed,
            "timeline_policy": mode,
            "sentinel_scope": "active_battle",
            "progress_status": "postcondition",
            "sentinel_mode": mode,
            "watch_army_ids": watched,
            "stop_kind": "terminal" if terminal else "decision_epoch",
            "terminal_reached": terminal,
            "trigger_reasons": reasons,
            "sentinel_generation": 7,
            "completed_daily_ticks": elapsed_days,
            "intermediate_pause_count": 1 if native_pause else 0,
            "overshoot_days": 0,
            "zero_intermediate_pause": not native_pause,
            "external_pause_count": 0,
            "external_rich_query_count": 0,
            "managed_failure_cleanup": {
                "attempted": False,
                "error": None,
            },
            "paused": True,
            "armed_tactical_daily_sentinel": armed,
            "tactical_daily_sentinel": {
                "state": "triggered",
                "generation": 7,
                "starting_date_raw": DATE_RAW,
                "target_date_raw": target,
                "last_observed_date_raw": ending,
                "trigger_date_raw": ending,
                "speed": speed,
                "mode": mode,
                "army_count": len(watched),
                "combat_count": 1,
                "completed_daily_ticks": elapsed_days,
                "intermediate_pause_count": 1 if native_pause else 0,
                "trigger_flags": (
                    256 if terminal else 1 << 13 if native_pause else 64
                ),
                "trigger_reasons": reasons,
                "signed_date_delta_from_target_raw": ending - target,
                "overshoot_days": 0,
                "pause_wrapper_called": not native_pause,
                "pause_observed": True,
                "terminal_observed": terminal,
                "abnormal": False,
            },
        },
    }


class BattleSentinelStrategyTests(unittest.TestCase):
    def test_objective_hold_result_reconciles_typed_scope_and_fresh_post_stop(
        self,
    ) -> None:
        target = DATE_RAW + 7 * 24
        step = war_objective_hold_sentinel_advance_step(
            61, SUBJECT, 2_635, target
        )
        row = _sentinel_advance_row(
            1, step=step, elapsed_days=7, target_date_raw=target
        )
        result = row["result"]
        assert isinstance(result, dict)
        result["sentinel_scope"] = "stationary_objective_hold"
        armed = result["armed_tactical_daily_sentinel"]
        sentinel = result["tactical_daily_sentinel"]
        assert isinstance(armed, dict)
        assert isinstance(sentinel, dict)
        armed["combat_count"] = 0
        sentinel["combat_count"] = 0
        result["trigger_reasons"] = ["date_deadline"]
        sentinel["trigger_flags"] = 1
        sentinel["trigger_reasons"] = ["date_deadline"]
        binding = {
            "status": "matched",
            "reason": None,
            "sentinel_scope": "stationary_objective_hold",
            "war_id": 61,
            "subject_army_id": SUBJECT,
            "objective_province_id": 2_635,
            "watch_army_ids": [SUBJECT],
            "exact_war_terminal_watch": False,
            "exact_active_war_set_watch": False,
        }
        result["war_objective_hold_request"] = {
            "sentinel_scope": "stationary_objective_hold",
            "war_id": 61,
            "subject_army_id": SUBJECT,
            "objective_province_id": 2_635,
            "target_date_raw": target,
        }
        result["war_objective_hold_admission"] = dict(binding)
        result["war_objective_hold_post_stop"] = dict(binding)
        result["exact_war_terminal_watch"] = False
        result["exact_active_war_set_watch"] = False
        result["maximum_omitted_state_detection_lag_days"] = 7

        valid = _battle_sentinel_advance_validation(result)
        self.assertIsInstance(valid, dict)
        assert isinstance(valid, dict)
        self.assertTrue(valid["valid"], valid["errors"])
        self.assertEqual(valid["sentinel_scope"], "stationary_objective_hold")

        mismatched = copy.deepcopy(result)
        mismatched["war_objective_hold_post_stop"]["war_id"] = 62
        invalid = _battle_sentinel_advance_validation(mismatched)
        self.assertIsInstance(invalid, dict)
        assert isinstance(invalid, dict)
        self.assertFalse(invalid["valid"])
        self.assertIn(
            "objective_hold_post_stop_binding_failed", invalid["errors"]
        )

    def test_route_result_scope_must_match_typed_route_request(self) -> None:
        route_step = committed_route_sentinel_advance_step(
            SUBJECT, 2635, DATE_RAW + 45 * 24
        )
        row = _sentinel_advance_row(1, step=route_step)
        result = row["result"]
        assert isinstance(result, dict)
        result["sentinel_scope"] = "committed_route"
        armed = result["armed_tactical_daily_sentinel"]
        sentinel = result["tactical_daily_sentinel"]
        assert isinstance(armed, dict)
        assert isinstance(sentinel, dict)
        armed["combat_count"] = 0
        sentinel["combat_count"] = 0
        result["trigger_reasons"] = ["route_target_changed"]
        sentinel["trigger_flags"] = 1 << 2
        sentinel["trigger_reasons"] = ["route_target_changed"]

        valid = _battle_sentinel_advance_validation(result)
        self.assertIsInstance(valid, dict)
        assert isinstance(valid, dict)
        self.assertTrue(valid["valid"])
        self.assertEqual(valid["sentinel_scope"], "committed_route")

        mismatched = copy.deepcopy(result)
        mismatched["sentinel_scope"] = "active_battle"
        invalid = _battle_sentinel_advance_validation(mismatched)
        self.assertIsInstance(invalid, dict)
        assert isinstance(invalid, dict)
        self.assertFalse(invalid["valid"])
        self.assertIn("sentinel_completion_invalid", invalid["errors"])

    def test_route_result_speed_must_match_typed_speed_five_binding(self) -> None:
        route_step = committed_route_sentinel_advance_step(
            SUBJECT,
            2635,
            DATE_RAW + 45 * 24,
            timeline_speed=5,
        )
        row = _sentinel_advance_row(1, step=route_step)
        result = row["result"]
        assert isinstance(result, dict)
        result["sentinel_scope"] = "committed_route"
        result["timeline_speed"] = 5
        armed = result["armed_tactical_daily_sentinel"]
        sentinel = result["tactical_daily_sentinel"]
        assert isinstance(armed, dict)
        assert isinstance(sentinel, dict)
        armed["speed"] = 5
        armed["combat_count"] = 0
        sentinel["speed"] = 5
        sentinel["combat_count"] = 0
        result["trigger_reasons"] = ["route_target_changed"]
        sentinel["trigger_flags"] = 1 << 2
        sentinel["trigger_reasons"] = ["route_target_changed"]

        valid = _battle_sentinel_advance_validation(result)
        self.assertIsInstance(valid, dict)
        assert isinstance(valid, dict)
        self.assertTrue(valid["valid"], valid["errors"])

        mismatched = copy.deepcopy(result)
        mismatched["timeline_speed"] = 3
        invalid = _battle_sentinel_advance_validation(mismatched)
        self.assertIsInstance(invalid, dict)
        assert isinstance(invalid, dict)
        self.assertFalse(invalid["valid"])
        self.assertIn("sentinel_completion_invalid", invalid["errors"])

    def _plan(
        self,
        history: list[dict[str, object]],
        frame: dict[str, object],
        *,
        steps: tuple[str, ...],
        readiness: dict[str, object] | None,
    ) -> dict[str, object]:
        return choose_one_life_turn(
            history,
            snapshot=_planner_battle_snapshot(frame=frame),
            action_steps=steps,
            bridge_capabilities=(
                QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY,
            ),
            battle_speed_readiness=readiness,
        )

    def test_missing_composite_or_live_gate_falls_back_to_speed_one(self) -> None:
        frame = _battle_frame()
        history = [_battle_query_row(1, frame)]
        for label, steps, readiness in (
            (
                "missing-composite",
                (STEP, "life-advance"),
                _ALL_BATTLE_SPEED_GATES,
            ),
            (
                "missing-live-gate",
                (STEP, "life-advance", DECISION_SENTINEL_STEP),
                None,
            ),
        ):
            with self.subTest(label=label):
                plan = self._plan(
                    history, frame, steps=steps, readiness=readiness
                )
                self.assertEqual(plan["selected_step"], "life-advance")
                self.assertEqual(
                    plan["phase"], "native_war_global_battle_control_progress"
                )

    def test_live_decision_epoch_defaults_active_combat_to_speed_three(self) -> None:
        frame = _battle_frame()
        plan = self._plan(
            [_battle_query_row(1, frame)],
            frame,
            steps=(STEP, "life-advance", DECISION_SENTINEL_STEP),
            readiness={"decision_sentinel_live_ready": True},
        )

        self.assertEqual(
            plan["selected_step"],
            battle_decision_epoch_advance_step(DATE_RAW + 45 * 24),
        )
        self.assertEqual(plan["timeline_speed"], 3)
        self.assertEqual(plan["sentinel_mode"], "decision_epoch")
        self.assertEqual(plan["absolute_target_date_raw"], DATE_RAW + 45 * 24)
        self.assertEqual(plan["watch_army_ids"], [SUBJECT])
        self.assertIn("hold-invalidation", plan["reason"])
        self.assertNotIn("phase", plan["reason"])
        self.assertNotIn("winner", plan["reason"])

    def test_active_assault_disables_ordinary_battle_decision_sentinel(self) -> None:
        frame = _battle_frame()
        snapshot = _planner_battle_snapshot(frame=frame)
        assaulting = {
            "army_id": 117_440_751,
            "owner_character_id": 29_829,
            "soldiers": 650,
            "current_province_id": 2600,
            "move_target_province_id": None,
            "controllable": True,
            "in_combat": False,
            "retreating": False,
            "army_state": "sieging",
            "army_state_code": 3,
            "route_province_ids": [],
        }
        snapshot["player_armies"].append(assaulting)
        snapshot["active_wars"][0]["allied_armies"].append(assaulting)
        snapshot["active_wars"][0]["war_objective_province_ids"] = [2600]
        snapshot["active_wars"][0]["objective_province_states"] = [
            {
                "province_id": 2600,
                "occupation_observable": True,
                "is_occupied": False,
                "occupying_character_id": None,
                "fort_level": 2,
                "garrison_size": 500,
                "besieging_strength": 650,
                "siege_observable": True,
                "active_siege": {
                    "siege_id": 901,
                    "besieging_army_id": 117_440_751,
                    "player_army_besieging": True,
                    "progress_fraction": {"raw": 25_000, "scale": 100_000},
                    "current_work": {"raw": 2_500_000, "scale": 100_000},
                    "total_work": {"raw": 10_000_000, "scale": 100_000},
                    "remaining_work": {"raw": 7_500_000, "scale": 100_000},
                    "days_left": 12,
                    "assault_observable": True,
                    "breach_level": 1,
                    "assault_in_progress": True,
                    "can_start_assault": False,
                    "can_stop_assault": True,
                    "assault_daily_progress": {
                        "raw": 340_000,
                        "scale": 100_000,
                    },
                    "assault_daily_casualties": 16,
                },
            }
        ]
        snapshot["war_objective_garrison_supported"] = True
        snapshot["war_objective_siege_progress_supported"] = True
        snapshot["war_objective_assault_supported"] = True
        sentinel_step = battle_decision_epoch_advance_step(
            DATE_RAW + 45 * 24
        )

        plan = choose_one_life_turn(
            [_battle_query_row(1, frame)],
            snapshot=snapshot,
            action_steps=(STEP, "life-advance", DECISION_SENTINEL_STEP),
            bridge_capabilities=(
                QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY,
            ),
            battle_speed_readiness={
                "decision_sentinel_live_ready": True
            },
        )

        self.assertEqual(plan["selected_step"], "life-advance")
        self.assertNotEqual(plan["selected_step"], sentinel_step)
        self.assertEqual(
            plan["phase"], "native_war_global_battle_control_progress"
        )

    def test_decision_epoch_targets_earliest_exact_retreat_gate(self) -> None:
        first = _battle_frame()
        first["side_flags"]["allow_early_retreat"] = False
        first["legality"].update(
            {
                "native_boolean": False,
                "legal_now": False,
                "reason_codes_in_native_order": ["too_early"],
                "native_reason_keys_in_native_order": [
                    "COMBAT_NO_RETREAT_TOO_EARLY"
                ],
            }
        )
        second = _rebind_battle_frame(
            _battle_frame(),
            subject=117_440_751,
            native_subject=404,
            combat_id=335_544_326,
            province_id=2587,
        )
        second["side_flags"]["allow_early_retreat"] = False
        second["legality"].update(
            {
                "native_boolean": False,
                "retreat_elapsed_baseline_date_raw": DATE_RAW - 5 * 24,
                "elapsed_whole_days": 5,
                "legal_now": False,
                "reason_codes_in_native_order": ["too_early"],
                "native_reason_keys_in_native_order": [
                    "COMBAT_NO_RETREAT_TOO_EARLY"
                ],
                "earliest_day_gate_date_raw": DATE_RAW + 10 * 24,
            }
        )
        snapshot = _multi_battle_snapshot([first, second])
        plan = choose_one_life_turn(
            [_battle_query_row(1, first), _battle_query_row(2, second)],
            snapshot=snapshot,
            action_steps=(
                STEP,
                query_battle_control_snapshot_v1_step(117_440_751),
                "life-advance",
                DECISION_SENTINEL_STEP,
            ),
            battle_speed_readiness={
                "decision_sentinel_live_ready": True
            },
        )

        expected_target = DATE_RAW + 10 * 24
        self.assertEqual(
            plan["selected_step"],
            battle_decision_epoch_advance_step(expected_target),
        )
        self.assertEqual(plan["absolute_target_date_raw"], expected_target)

    def test_terminal_cruise_never_clamps_to_retreat_gate(self) -> None:
        frame = _crushing_battle_frame()
        frame["side_flags"]["allow_early_retreat"] = False
        frame["legality"].update(
            {
                "native_boolean": False,
                "legal_now": False,
                "reason_codes_in_native_order": ["too_early"],
                "native_reason_keys_in_native_order": [
                    "COMBAT_NO_RETREAT_TOO_EARLY"
                ],
            }
        )
        plan = self._plan(
            [
                _battle_query_row(1, frame),
                _terminal_cursor_query_row(2, frame),
            ],
            frame,
            steps=(
                STEP,
                "life-advance",
                DECISION_SENTINEL_STEP,
                TERMINAL_SENTINEL_STEP,
            ),
            readiness=_ALL_BATTLE_SPEED_GATES,
        )

        self.assertEqual(plan["selected_step"], TERMINAL_SENTINEL_STEP)
        self.assertEqual(
            plan["absolute_target_date_raw"], DATE_RAW + 45 * 24
        )

    def test_double_four_x_and_player_won_pursuit_select_speed_five(
        self,
    ) -> None:
        for label, frame, readiness in (
            (
                "double-four-x",
                _crushing_battle_frame(),
                _ALL_BATTLE_SPEED_GATES,
            ),
            (
                "player-won-pursuit",
                _pursuit_battle_frame(),
                _TERMINAL_ONLY_BATTLE_SPEED_GATES,
            ),
        ):
            with self.subTest(label=label):
                history = [
                    _battle_query_row(1, frame),
                    _terminal_cursor_query_row(2, frame),
                ]
                plan = self._plan(
                    history,
                    frame,
                    steps=(
                        STEP,
                        "life-advance",
                        DECISION_SENTINEL_STEP,
                        TERMINAL_SENTINEL_STEP,
                    ),
                    readiness=readiness,
                )
                self.assertEqual(plan["selected_step"], TERMINAL_SENTINEL_STEP)
                self.assertEqual(plan["timeline_speed"], 5)
                self.assertEqual(plan["sentinel_mode"], "terminal_or_sentinel")
                self.assertEqual(
                    plan["terminal_journal_cursors"][0][
                        "after_terminal_sequence"
                    ],
                    40,
                )

    def test_terminal_only_gate_does_not_admit_dominance_or_bad_pursuit(
        self,
    ) -> None:
        losing_pursuit = _pursuit_battle_frame()
        losing_pursuit.update(
            {"winner_side": "defender", "winner_raw": 1}
        )
        undecided_pursuit = _pursuit_battle_frame()
        undecided_pursuit.update(
            {"winner_side": "none", "winner_raw": -1}
        )
        for label, frame in (
            ("double-four-x", _crushing_battle_frame()),
            ("player-lost-pursuit", losing_pursuit),
            ("undecided-pursuit", undecided_pursuit),
        ):
            with self.subTest(label=label):
                plan = self._plan(
                    [
                        _battle_query_row(1, frame),
                        _terminal_cursor_query_row(2, frame),
                    ],
                    frame,
                    steps=(
                        STEP,
                        "life-advance",
                        DECISION_SENTINEL_STEP,
                        TERMINAL_SENTINEL_STEP,
                    ),
                    readiness=_BATTLE_SPEED_GATES_WITHOUT_OVERWHELMING,
                )

                self.assertEqual(
                    plan["selected_step"],
                    battle_decision_epoch_advance_step(
                        DATE_RAW + 45 * 24
                    ),
                )
                self.assertEqual(plan["timeline_speed"], 3)

    def test_terminal_cruise_first_freezes_cursor(self) -> None:
        frame = _pursuit_battle_frame()
        plan = self._plan(
            [_battle_query_row(1, frame)],
            frame,
            steps=(
                STEP,
                "life-advance",
                DECISION_SENTINEL_STEP,
                TERMINAL_SENTINEL_STEP,
            ),
            readiness=_TERMINAL_ONLY_BATTLE_SPEED_GATES,
        )

        self.assertEqual(
            plan["phase"], "native_war_battle_terminal_cursor_query"
        )
        self.assertEqual(
            plan["selected_step"],
            query_battle_terminal_transition_v1_step(
                int(frame["combat_id"]), SUBJECT
            ),
        )

    def test_multiple_combats_are_all_of_and_watch_every_controllable_army(
        self,
    ) -> None:
        first = _crushing_battle_frame()
        second = _rebind_battle_frame(
            _battle_frame(),
            subject=117_440_751,
            native_subject=404,
            combat_id=335_544_326,
            province_id=2587,
        )
        snapshot = _multi_battle_snapshot(
            [first, second], extra_idle_army_id=444
        )
        steps = (
            STEP,
            query_battle_control_snapshot_v1_step(117_440_751),
            "life-advance",
            DECISION_SENTINEL_STEP,
            TERMINAL_SENTINEL_STEP,
        )
        history = [
            _battle_query_row(1, first),
            _terminal_cursor_query_row(2, first),
            _battle_query_row(3, second),
            _terminal_cursor_query_row(4, second),
        ]
        mixed = choose_one_life_turn(
            history,
            snapshot=snapshot,
            action_steps=steps,
            bridge_capabilities=(
                QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY,
            ),
            battle_speed_readiness=_ALL_BATTLE_SPEED_GATES,
        )
        self.assertEqual(
            mixed["selected_step"],
            battle_decision_epoch_advance_step(DATE_RAW + 45 * 24),
        )
        self.assertEqual(mixed["watch_army_ids"], [444, SUBJECT, 117_440_751])

        second_crush = _rebind_battle_frame(
            _crushing_battle_frame(),
            subject=117_440_751,
            native_subject=404,
            combat_id=335_544_326,
            province_id=2587,
        )
        snapshot = _multi_battle_snapshot(
            [first, second_crush], extra_idle_army_id=444
        )
        all_crush = choose_one_life_turn(
            [
                _battle_query_row(1, first),
                _terminal_cursor_query_row(2, first),
                _battle_query_row(3, second_crush),
                _terminal_cursor_query_row(4, second_crush),
            ],
            snapshot=snapshot,
            action_steps=steps,
            bridge_capabilities=(
                QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY,
            ),
            battle_speed_readiness=_ALL_BATTLE_SPEED_GATES,
        )
        self.assertEqual(all_crush["selected_step"], TERMINAL_SENTINEL_STEP)
        self.assertEqual(
            all_crush["watch_army_ids"], [444, SUBJECT, 117_440_751]
        )
        self.assertEqual(len(all_crush["terminal_journal_cursors"]), 2)

    def test_terminal_only_won_pursuits_keep_all_of_full_watch_and_cursors(
        self,
    ) -> None:
        first = _pursuit_battle_frame()
        second = _rebind_battle_frame(
            _pursuit_battle_frame(),
            subject=117_440_751,
            native_subject=404,
            combat_id=335_544_326,
            province_id=2587,
        )
        snapshot = _multi_battle_snapshot(
            [first, second], extra_idle_army_id=444
        )
        plan = choose_one_life_turn(
            [
                _battle_query_row(1, first),
                _terminal_cursor_query_row(2, first),
                _battle_query_row(3, second),
                _terminal_cursor_query_row(4, second),
            ],
            snapshot=snapshot,
            action_steps=(
                STEP,
                query_battle_control_snapshot_v1_step(117_440_751),
                "life-advance",
                DECISION_SENTINEL_STEP,
                TERMINAL_SENTINEL_STEP,
            ),
            bridge_capabilities=(
                QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY,
            ),
            battle_speed_readiness=_TERMINAL_ONLY_BATTLE_SPEED_GATES,
        )

        self.assertEqual(plan["selected_step"], TERMINAL_SENTINEL_STEP)
        self.assertEqual(plan["watch_army_ids"], [444, SUBJECT, 117_440_751])
        self.assertEqual(len(plan["terminal_journal_cursors"]), 2)

    def test_valid_multiday_sentinel_unlocks_but_wrong_status_is_rejected(
        self,
    ) -> None:
        before = _battle_frame()
        after = _next_battle_frame(elapsed_days=5)
        good = _sentinel_advance_row(2)
        history = [
            _battle_query_row(1, before),
            good,
            _battle_query_row(3, after),
        ]
        plan = self._plan(
            history,
            after,
            steps=(STEP, "life-advance", DECISION_SENTINEL_STEP),
            readiness={"decision_sentinel_live_ready": True},
        )
        self.assertEqual(
            plan["selected_step"],
            battle_decision_epoch_advance_step(
                DATE_RAW + 5 * 24 + 45 * 24
            ),
        )
        self.assertEqual(
            plan["battle_transitions"][0]["actual_elapsed_days"], 5
        )

        bad = copy.deepcopy(good)
        bad["result"]["tactical_daily_sentinel"]["state"] = "armed"
        rejected = self._plan(
            [
                _battle_query_row(1, before),
                bad,
                _battle_query_row(3, after),
            ],
            after,
            steps=(STEP, "life-advance", DECISION_SENTINEL_STEP),
            readiness={"decision_sentinel_live_ready": True},
        )
        self.assertEqual(
            rejected["phase"], "native_war_battle_transition_invalid"
        )
        self.assertIsNone(rejected["selected_step"])
        self.assertIn(
            "sentinel_completion_invalid",
            rejected["battle_transition"]["sentinel_validation"]["errors"],
        )

    def test_native_pause_stop_is_a_valid_decision_epoch(self) -> None:
        before = _battle_frame()
        after = _next_battle_frame(elapsed_days=1)
        plan = self._plan(
            [
                _battle_query_row(1, before),
                _sentinel_advance_row(2, elapsed_days=1, native_pause=True),
                _battle_query_row(3, after),
            ],
            after,
            steps=(STEP, "life-advance", DECISION_SENTINEL_STEP),
            readiness={"decision_sentinel_live_ready": True},
        )

        self.assertEqual(
            plan["selected_step"],
            battle_decision_epoch_advance_step(
                DATE_RAW + 24 + 45 * 24
            ),
        )

    def test_parameterized_decision_target_reconciles_result_dates(self) -> None:
        before = _battle_frame()
        after = _next_battle_frame(elapsed_days=5)
        target = DATE_RAW + 15 * 24
        dynamic_step = battle_decision_epoch_advance_step(target)
        plan = self._plan(
            [
                _battle_query_row(1, before),
                _sentinel_advance_row(
                    2,
                    step=dynamic_step,
                    elapsed_days=5,
                    target_date_raw=target,
                ),
                _battle_query_row(3, after),
            ],
            after,
            steps=(STEP, "life-advance", DECISION_SENTINEL_STEP),
            readiness={"decision_sentinel_live_ready": True},
        )

        self.assertEqual(
            plan["selected_step"],
            battle_decision_epoch_advance_step(
                DATE_RAW + 5 * 24 + 45 * 24
            ),
        )

    def test_terminal_stop_requires_cursor_bound_same_combat_outcome(self) -> None:
        before = _crushing_battle_frame()
        ending = DATE_RAW + 5 * 24
        after_revision = NATIVE_REVISION + 5
        after = _planner_battle_snapshot(
            frame=None, army_state="regular"
        )
        after.update(
            {
                "snapshot_id": f"native:{after_revision}",
                "revision": after_revision,
                "native_revision": after_revision,
                "date_raw": ending,
            }
        )
        terminal_advance = _sentinel_advance_row(
            3,
            step=TERMINAL_SENTINEL_STEP,
            terminal=True,
        )
        history = [
            _battle_query_row(1, before),
            _terminal_cursor_query_row(2, before),
            terminal_advance,
        ]
        query = choose_one_life_turn(
            history,
            snapshot=after,
            action_steps=(
                STEP,
                "life-advance",
                DECISION_SENTINEL_STEP,
                TERMINAL_SENTINEL_STEP,
            ),
            bridge_capabilities=(
                QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY,
            ),
            battle_speed_readiness=_ALL_BATTLE_SPEED_GATES,
        )
        expected_query = query_battle_terminal_transition_v1_step(
            int(before["combat_id"]), SUBJECT, 40
        )
        self.assertEqual(
            query["phase"], "native_war_battle_terminal_journal_query"
        )
        self.assertEqual(query["selected_step"], expected_query)

        accepted = choose_one_life_turn(
            [
                *history,
                _observed_terminal_query_row(
                    4,
                    before,
                    cursor=40,
                    observed_date_raw=ending,
                    snapshot_revision=after_revision,
                ),
            ],
            snapshot=after,
            action_steps=(
                STEP,
                "life-advance",
                DECISION_SENTINEL_STEP,
                TERMINAL_SENTINEL_STEP,
            ),
            bridge_capabilities=(
                QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY,
            ),
            battle_speed_readiness=_ALL_BATTLE_SPEED_GATES,
        )
        terminal = next(
            transition
            for transition in accepted["battle_transitions"]
            if transition.get("status") == "terminal_journal_observed"
        )
        self.assertEqual(terminal["before_combat_id"], before["combat_id"])
        self.assertEqual(terminal["after_terminal_sequence"], 40)
        self.assertEqual(terminal["terminal_journal_sequence"], 41)
        self.assertEqual(terminal["outcome"]["winner_side"], "attacker")

    def test_finalized_terminal_cruise_records_journal_outcome_before_cleanup(
        self,
    ) -> None:
        before = _crushing_battle_frame()
        after = _next_battle_frame(elapsed_days=5)
        after["finalized"] = True
        ending = int(after["observed_date_raw"])
        after_revision = int(after["snapshot_revision"])
        history = [
            _battle_query_row(1, before),
            _terminal_cursor_query_row(2, before),
            _sentinel_advance_row(
                3,
                step=TERMINAL_SENTINEL_STEP,
                terminal=True,
            ),
            _battle_query_row(4, after),
            _observed_terminal_query_row(
                5,
                before,
                cursor=40,
                observed_date_raw=ending,
                snapshot_revision=after_revision,
            ),
        ]

        plan = self._plan(
            history,
            after,
            steps=(
                STEP,
                "life-advance",
                DECISION_SENTINEL_STEP,
                TERMINAL_SENTINEL_STEP,
            ),
            readiness=_ALL_BATTLE_SPEED_GATES,
        )

        self.assertEqual(plan["phase"], "native_war_battle_terminal_cleanup")
        self.assertEqual(plan["selected_step"], "life-advance")
        self.assertEqual(
            plan["battle_transition"]["status"],
            "terminal_journal_observed",
        )
        self.assertEqual(
            plan["battle_transition"]["outcome"]["winner_side"],
            "attacker",
        )

    def test_one_cursor_proves_each_controlled_subject_in_same_combat(
        self,
    ) -> None:
        first = _crushing_battle_frame()
        second_subject = 117_440_751
        second = _rebind_battle_frame(
            _crushing_battle_frame(),
            subject=second_subject,
            native_subject=404,
            combat_id=int(first["combat_id"]),
            province_id=int(first["province_id"]),
        )
        ending = DATE_RAW + 5 * 24
        after_revision = NATIVE_REVISION + 5
        after = _planner_battle_snapshot(frame=None, army_state="regular")
        after.update(
            {
                "snapshot_id": f"native:{after_revision}",
                "revision": after_revision,
                "native_revision": after_revision,
                "date_raw": ending,
            }
        )
        history = [
            _battle_query_row(1, first),
            _terminal_cursor_query_row(2, first),
            _battle_query_row(3, second),
            _sentinel_advance_row(
                4,
                step=TERMINAL_SENTINEL_STEP,
                terminal=True,
                watch_army_ids=[SUBJECT, second_subject],
            ),
            _observed_terminal_query_row(
                5,
                first,
                cursor=40,
                observed_date_raw=ending,
                snapshot_revision=after_revision,
            ),
        ]

        plan = choose_one_life_turn(
            history,
            snapshot=after,
            action_steps=(
                STEP,
                query_battle_control_snapshot_v1_step(second_subject),
                "life-advance",
                DECISION_SENTINEL_STEP,
                TERMINAL_SENTINEL_STEP,
            ),
            bridge_capabilities=(
                QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY,
            ),
            battle_speed_readiness=_ALL_BATTLE_SPEED_GATES,
        )

        terminal = [
            transition
            for transition in plan["battle_transitions"]
            if transition.get("status") == "terminal_journal_observed"
        ]
        self.assertEqual(
            {row["subject_army_id"] for row in terminal},
            {SUBJECT, second_subject},
        )
        self.assertEqual(
            {row["journal_subject_army_id"] for row in terminal},
            {SUBJECT},
        )
        self.assertEqual(
            {row["before_combat_id"] for row in terminal},
            {first["combat_id"]},
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

    def test_signed_generation_combat_id_is_not_missing(self) -> None:
        combat_id = -2_130_706_429
        frame = _with_combat_id(_battle_frame(), combat_id)

        normalized = self.normalize(frame)

        self.assertEqual(normalized["combat_id"], combat_id)
        for side_name in ("attacker", "defender"):
            self.assertTrue(
                all(
                    army["combat_backlink_id"] == combat_id
                    for army in normalized[side_name]["ordered_armies"]
                )
            )

        missing = _with_combat_id(_battle_frame(), -1)
        with self.assertRaisesRegex(ValueError, "missing-ID sentinel"):
            self.normalize(missing)

    def test_signed_generation_battle_result_id_is_not_missing(self) -> None:
        frame = _battle_frame()
        frame["battle_result_id"] = -2_130_706_431

        normalized = self.normalize(frame)

        self.assertEqual(normalized["battle_result_id"], -2_130_706_431)
        frame["battle_result_id"] = -1
        with self.assertRaisesRegex(ValueError, "missing-ID sentinel"):
            self.normalize(frame)

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
                        "error": (
                            TRANSIENT_QUERY_ERROR
                            + " (retreat_projection_failed)"
                        ),
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

    def test_persistent_identity_gap_becomes_same_frame_typed_pending(
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
                    "error": IDENTITY_PENDING_QUERY_ERROR,
                }
            )

        endpoint.send_hook = answer
        revision = int(driver.take_snapshot()["revision"])

        result = driver.execute_step(STEP, expected_revision=revision)

        self.assertEqual(attempts, 3)
        self.assertEqual(result["status"], "identity_pending")
        self.assertEqual(result["native_query_status"], "state_changed")
        self.assertEqual(result["diagnostic_reason"], IDENTITY_PENDING_DIAGNOSTIC)
        self.assertEqual(result["query_attempts"], 3)
        self.assertEqual(result["subject_public_cunit_id"], SUBJECT)
        cached = driver.take_snapshot()
        self.assertEqual(
            cached["battle_control_snapshot_v1_status"], "identity_pending"
        )
        self.assertIsNone(cached["battle_control_snapshot_v1"])
        self.assertEqual(
            cached["battle_control_snapshot_v1_diagnostic_reason"],
            IDENTITY_PENDING_DIAGNOSTIC,
        )
        self.assertEqual(
            cached["battle_control_snapshot_v1_queried_native_revision"],
            NATIVE_REVISION,
        )

        endpoint.publish(_semantic_snapshot(NATIVE_REVISION + 1))
        advanced = driver.take_snapshot()
        self.assertIsNone(advanced["battle_control_snapshot_v1_status"])
        self.assertIsNone(advanced["battle_control_snapshot_v1"])

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
