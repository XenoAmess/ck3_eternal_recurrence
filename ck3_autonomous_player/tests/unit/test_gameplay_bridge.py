from __future__ import annotations

import json
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.driver import (
    BridgeGameplayStepExecutor,
    CallbackGameplayDriver,
    DevelopmentReportDriver,
    HybridGameplayDriver,
    UnsupportedStepError,
)
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.settlement_contract import (
    ONE_LIFE_SETTLEMENT_CAPABILITY,
)
from xar_autoplayer.bridge.war_contract import (
    normalize_active_wars,
    war_objective_province_ids,
)
from xar_autoplayer.strategy import _audit_war_route, record_one_life_episode


def _snapshot(revision: int = 0, history: list[dict[str, object]] | None = None):
    return {
        "format_version": 1,
        "snapshot_id": f"session:{revision}",
        "revision": revision,
        "source": "fixture",
        "history": history or [],
        "phase": "map_hud",
    }


def _army(
    army_id: int,
    *,
    soldiers: int | None,
    province_id: int,
    controllable: bool,
    move_target_province_id: int | None = None,
    **state: object,
) -> dict[str, object]:
    return {
        "army_id": army_id,
        "owner_character_id": 707 if controllable else 808,
        "soldiers": soldiers,
        "current_province_id": province_id,
        "move_target_province_id": move_target_province_id,
        "controllable": controllable,
        **state,
    }


def _active_siege(
    *,
    siege_id: int = 901,
    army_id: int | None = 11,
    player: bool = True,
    progress_raw: int = 25_000,
    current_work_raw: int = 2_500_000,
    total_work_raw: int = 10_000_000,
    days_left: int | None = 12,
    assault_observable: bool = False,
    breach_level: int | None = None,
    assault_in_progress: bool | None = None,
    can_start_assault: bool | None = None,
    can_stop_assault: bool | None = None,
    assault_daily_progress_raw: int | None = None,
    assault_daily_casualties: int | None = None,
) -> dict[str, object]:
    return {
        "siege_id": siege_id,
        "besieging_army_id": army_id,
        "player_army_besieging": player,
        "progress_fraction": {"raw": progress_raw, "scale": 100_000},
        "current_work": {"raw": current_work_raw, "scale": 100_000},
        "total_work": {"raw": total_work_raw, "scale": 100_000},
        "days_left": days_left,
        "assault_observable": assault_observable,
        "breach_level": breach_level,
        "assault_in_progress": assault_in_progress,
        "can_start_assault": can_start_assault,
        "can_stop_assault": can_stop_assault,
        "assault_daily_progress": (
            {
                "raw": assault_daily_progress_raw,
                "scale": 100_000,
            }
            if assault_daily_progress_raw is not None
            else None
        ),
        "assault_daily_casualties": assault_daily_casualties,
    }


def _objective_state(
    province_id: int,
    *,
    occupant: int | None = None,
    occupation_observable: bool = True,
    fort_level: int | None = 2,
    garrison_size: int | None = 500,
    besieging_strength: int | None = 650,
    siege_observable: bool = True,
    active_siege: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "province_id": province_id,
        "occupation_observable": occupation_observable,
        "is_occupied": (
            occupant is not None if occupation_observable else None
        ),
        "occupying_character_id": (
            occupant if occupation_observable else None
        ),
        "fort_level": fort_level,
        "garrison_size": garrison_size,
        "besieging_strength": besieging_strength,
        "siege_observable": siege_observable,
        "active_siege": active_siege if siege_observable else None,
    }


def _war(
    *,
    war_id: int = 88,
    allied_armies: list[dict[str, object]],
    enemy_armies: list[dict[str, object]],
    score: int = 17,
    player_side: str = "attacker",
    player_is_primary_war_leader: bool = True,
    enemy_primary_default_raise_province_id: int | None = None,
    war_objective_province_ids: list[int] | None = None,
    objective_province_states: list[dict[str, object]] | None = None,
    targeted_title_ids: list[int] | None = None,
) -> dict[str, object]:
    return {
        "war_id": war_id,
        "player_side": player_side,
        "primary_opponent_character_id": 808,
        "player_is_primary_war_leader": player_is_primary_war_leader,
        "enemy_primary_default_raise_province_id": (
            enemy_primary_default_raise_province_id
        ),
        "player_relative_war_score": score,
        "allied_armies": allied_armies,
        "enemy_armies": enemy_armies,
        "war_objective_province_ids": war_objective_province_ids or [],
        "objective_province_states": objective_province_states or [],
        "targeted_title_ids": targeted_title_ids or [],
    }


def _war_progress(
    date_raw: int,
    *,
    player: dict[str, object],
    enemies: list[dict[str, object]],
    score: int,
    war_id: int = 88,
    objectives: list[int] | None = None,
    objective_states: list[dict[str, object]] | None = None,
    fallback: int | None = None,
) -> dict[str, object]:
    keys = (
        "army_id",
        "current_province_id",
        "soldiers",
        "move_target_province_id",
        "army_state",
        "army_state_code",
        "in_combat",
        "retreating",
    )

    def compact(army: dict[str, object]) -> dict[str, object]:
        return {key: army.get(key) for key in keys if key in army}

    return {
        "date_raw": date_raw,
        "wars": [
            {
                "war_id": war_id,
                "player_relative_war_score": score,
                "war_objective_province_ids": objectives or [],
                "objective_province_states": objective_states or [],
                "enemy_primary_default_raise_province_id": fallback,
                "player_armies": [compact(player)],
                "enemy_armies": [compact(enemy) for enemy in enemies],
            }
        ],
    }


def _advance_row(
    index: int,
    before: dict[str, object],
    after: dict[str, object],
) -> dict[str, object]:
    return {
        "index": index,
        "command": "life-advance",
        "ok": True,
        "result": {
            "elapsed_days": (
                int(after["date_raw"]) - int(before["date_raw"])
            )
            // 24,
            "war_progress_before": before,
            "war_progress_after": after,
        },
    }


def _assault_action_row(
    index: int,
    *,
    status: str,
    siege_id: int = 901,
    war_id: int = 88,
    province_id: int = 2585,
    decorated: bool = False,
) -> dict[str, object]:
    step = (
        f"start-assault-{siege_id}"
        if status == "assault_started"
        else f"stop-assault-{siege_id}"
    )
    action = {
        "status": status,
        "siege_id": siege_id,
        "war_id": war_id,
        "province_id": province_id,
    }
    result: dict[str, object] = {
        "assault_action": dict(action),
        "war_action": dict(action),
    }
    command = step
    if decorated:
        command = "auto-turn"
        result.update(
            {
                "requested_step": "auto-turn",
                "auto_turn": {"selected_step": step},
            }
        )
    return {
        "index": index,
        "command": command,
        "ok": True,
        "result": result,
    }


def _failed_life_advance_row(
    index: int, *, decorated: bool = False
) -> dict[str, object]:
    result: dict[str, object] = {}
    command = "life-advance"
    if decorated:
        command = "auto-turn"
        result = {"auto_turn": {"selected_step": "life-advance"}}
    return {
        "index": index,
        "command": command,
        "ok": False,
        "result": result,
        "error": "fixture composite postcondition failed",
    }


def _preview_row(
    index: int,
    *,
    army_id: int = 11,
    origin: int,
    target: int,
    date_raw: int,
    route: list[int],
) -> dict[str, object]:
    return {
        "index": index,
        "command": f"preview-move-army-{army_id}-to-{target}",
        "ok": True,
        "result": {
            "accepted": True,
            "status": "available",
            "route_preview": {
                "status": "available",
                "army_id": army_id,
                "origin_province_id": origin,
                "target_province_id": target,
                "route_province_ids": list(route),
                "previewed_date_raw": date_raw,
            },
        },
    }


def _native_war_plan(
    *,
    player: dict[str, object],
    enemies: list[dict[str, object]],
    score: int,
    date_raw: int,
    history: list[dict[str, object]] | None = None,
    objective: int | None = None,
    objectives: list[int] | None = None,
    fallback: int | None = None,
    steps: tuple[str, ...] = (),
    paused: bool = True,
    army_routes_supported: bool | None = None,
    move_route_preview_supported: bool | None = None,
    objective_states: list[dict[str, object]] | None = None,
    occupation_supported: bool = False,
    fort_level_supported: bool = False,
    garrison_supported: bool = False,
    siege_progress_supported: bool = False,
    assault_supported: bool = False,
    rollback_war_failure: dict[str, object] | None = None,
) -> dict[str, object]:
    route_field_present = "route_province_ids" in player
    driver = CallbackGameplayDriver(
        backend_id="native-headless",
        snapshot=lambda: {
            **_snapshot(90),
            "paused": paused,
            "army_routes_supported": (
                route_field_present
                if army_routes_supported is None
                else army_routes_supported
            ),
            "move_route_preview_supported": (
                route_field_present
                if move_route_preview_supported is None
                else move_route_preview_supported
            ),
            "war_objective_occupation_supported": occupation_supported,
            "war_objective_fort_level_supported": fort_level_supported,
            "war_objective_garrison_supported": garrison_supported,
            "war_objective_siege_progress_supported": (
                siege_progress_supported
            ),
            "war_objective_assault_supported": assault_supported,
            "date_raw": date_raw,
            "native_command_history": history or [],
            "native_rollback_war_failure": rollback_war_failure,
            "active_wars": [
                _war(
                    allied_armies=[player],
                    enemy_armies=enemies,
                    score=score,
                    enemy_primary_default_raise_province_id=fallback,
                    war_objective_province_ids=(
                        list(objectives)
                        if objectives is not None
                        else [objective]
                        if objective is not None
                        else []
                    ),
                    objective_province_states=objective_states,
                )
            ],
            "player_armies": [player],
        },
        execute=lambda _step, _revision: {},
        action_steps=steps,
    )
    return GameplayBridgeService(driver).plan_turn()["plan"]


class GameplayBridgeTests(unittest.TestCase):
    def test_war_contract_preserves_adapter_objective_order(self) -> None:
        normalized = normalize_active_wars(
            [
                _war(
                    allied_armies=[],
                    enemy_armies=[],
                    targeted_title_ids=[2388, 2200, 2388],
                    war_objective_province_ids=[2585, 2510, 2548, 2585],
                )
            ]
        )

        self.assertEqual(normalized[0]["targeted_title_ids"], [2388, 2200])
        self.assertEqual(
            normalized[0]["war_objective_province_ids"],
            [2585, 2510, 2548],
        )
        self.assertEqual(
            war_objective_province_ids(normalized),
            [2585, 2510, 2548],
        )

    def test_war_contract_normalizes_exact_objective_state(self) -> None:
        state = _objective_state(
            2585,
            active_siege=_active_siege(
                current_work_raw=2_500_001,
                total_work_raw=10_000_000,
            ),
        )
        normalized = normalize_active_wars(
            [
                _war(
                    allied_armies=[],
                    enemy_armies=[],
                    war_objective_province_ids=[2585],
                    objective_province_states=[state],
                )
            ]
        )[0]["objective_province_states"]

        self.assertEqual(len(normalized), 1)
        siege = normalized[0]["active_siege"]
        self.assertEqual(
            siege["remaining_work"],
            {"raw": 7_499_999, "scale": 100_000},
        )
        self.assertEqual(normalized[0]["garrison_size"], 500)

    def test_war_contract_normalizes_assault_subdomain_all_or_none(self) -> None:
        active = _active_siege(
            assault_observable=True,
            breach_level=2,
            assault_in_progress=False,
            can_start_assault=True,
            can_stop_assault=False,
            assault_daily_progress_raw=340_000,
            assault_daily_casualties=16,
        )
        normalized = normalize_active_wars(
            [
                _war(
                    allied_armies=[],
                    enemy_armies=[],
                    war_objective_province_ids=[2585],
                    objective_province_states=[
                        _objective_state(2585, active_siege=active)
                    ],
                )
            ]
        )[0]["objective_province_states"][0]["active_siege"]

        self.assertTrue(normalized["assault_observable"])
        self.assertEqual(normalized["breach_level"], 2)
        self.assertTrue(normalized["walls_breached"])
        self.assertEqual(
            normalized["assault_daily_progress"],
            {"raw": 340_000, "scale": 100_000},
        )
        self.assertEqual(normalized["assault_daily_casualties"], 16)

        partial = _active_siege()
        partial["breach_level"] = 1
        with self.assertRaisesRegex(ValueError, "unobservable assault"):
            normalize_active_wars(
                [
                    _war(
                        allied_armies=[],
                        enemy_armies=[],
                        war_objective_province_ids=[2585],
                        objective_province_states=[
                            _objective_state(2585, active_siege=partial)
                        ],
                    )
                ]
            )

        malformed = dict(active)
        malformed["breach_level"] = 3
        with self.assertRaisesRegex(ValueError, "range 0..2"):
            normalize_active_wars(
                [
                    _war(
                        allied_armies=[],
                        enemy_armies=[],
                        war_objective_province_ids=[2585],
                        objective_province_states=[
                            _objective_state(2585, active_siege=malformed)
                        ],
                    )
                ]
            )

    def test_war_contract_distinguishes_unknown_from_zero(self) -> None:
        unknown = _objective_state(
            2585,
            occupation_observable=False,
            fort_level=None,
            garrison_size=None,
            besieging_strength=None,
            siege_observable=False,
        )
        zero = _objective_state(
            2510,
            fort_level=0,
            garrison_size=0,
            besieging_strength=0,
            active_siege=None,
        )
        states = normalize_active_wars(
            [
                _war(
                    allied_armies=[],
                    enemy_armies=[],
                    war_objective_province_ids=[2585, 2510],
                    objective_province_states=[unknown, zero],
                )
            ]
        )[0]["objective_province_states"]

        self.assertIsNone(states[0]["is_occupied"])
        self.assertIsNone(states[0]["garrison_size"])
        self.assertFalse(states[0]["siege_observable"])
        self.assertFalse(states[1]["is_occupied"])
        self.assertEqual(states[1]["garrison_size"], 0)
        self.assertTrue(states[1]["siege_observable"])
        self.assertIsNone(states[1]["active_siege"])

    def test_war_contract_rejects_partial_or_malformed_objective_state(self) -> None:
        with self.assertRaisesRegex(ValueError, "completely match"):
            normalize_active_wars(
                [
                    _war(
                        allied_armies=[],
                        enemy_armies=[],
                        war_objective_province_ids=[2585, 2510],
                        objective_province_states=[_objective_state(2585)],
                    )
                ]
            )

        malformed = _objective_state(
            2585, active_siege=_active_siege()
        )
        malformed["active_siege"]["progress_fraction"]["scale"] = 1_000
        with self.assertRaisesRegex(ValueError, "fixed value is malformed"):
            normalize_active_wars(
                [
                    _war(
                        allied_armies=[],
                        enemy_armies=[],
                        war_objective_province_ids=[2585],
                        objective_province_states=[malformed],
                    )
                ]
            )

        contradictory = _objective_state(2585)
        contradictory["occupation_observable"] = False
        with self.assertRaisesRegex(ValueError, "unobservable occupation"):
            normalize_active_wars(
                [
                    _war(
                        allied_armies=[],
                        enemy_armies=[],
                        war_objective_province_ids=[2585],
                        objective_province_states=[contradictory],
                    )
                ]
            )

    def test_war_contract_preserves_route_order_and_repetition(self) -> None:
        normalized = normalize_active_wars(
            [
                _war(
                    allied_armies=[
                        _army(
                            11,
                            soldiers=900,
                            province_id=20,
                            controllable=True,
                            route_province_ids=[20, 31, 31, 2585],
                        )
                    ],
                    enemy_armies=[],
                )
            ]
        )

        self.assertEqual(
            normalized[0]["allied_armies"][0]["route_province_ids"],
            [20, 31, 31, 2585],
        )

    def test_exact_route_previews_first_then_moves_with_fresh_safe_route(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            army_state="regular",
            route_province_ids=[],
        )
        steps = (
            "preview-move-army-11-to-2585",
            "move-army-11-to-2585",
            "life-advance",
        )

        preview = _native_war_plan(
            player=player,
            enemies=[],
            score=0,
            date_raw=24_000,
            objective=2585,
            steps=steps,
        )
        self.assertEqual(preview["phase"], "native_war_route_preview")
        self.assertEqual(
            preview["selected_step"], "preview-move-army-11-to-2585"
        )

        move = _native_war_plan(
            player=player,
            enemies=[],
            score=0,
            date_raw=24_000,
            history=[
                _preview_row(
                    1,
                    origin=20,
                    target=2585,
                    date_raw=24_000,
                    route=[20, 31, 31, 2585],
                )
            ],
            objective=2585,
            steps=steps,
        )
        self.assertEqual(move["selected_step"], "move-army-11-to-2585")
        self.assertEqual(
            move["pursuit"]["route_audit"]["route_province_ids"],
            [31, 31, 2585],
        )

    def test_route_audit_preserves_a_later_return_to_physical_origin(
        self,
    ) -> None:
        enemy = _army(
            21,
            soldiers=800,
            province_id=90,
            controllable=False,
            move_target_province_id=99,
            army_state="moving",
            route_province_ids=[52, 8759, 99],
        )

        audit = _audit_war_route(
            [2602, 8759, 2604],
            origin_province_id=8759,
            target_province_id=2604,
            enemies=[enemy],
        )

        self.assertEqual(audit["status"], "unsafe")
        self.assertEqual(
            audit["route_province_ids"], [2602, 8759, 2604]
        )
        self.assertIn(
            {
                "kind": "enemy_route_intersection",
                "enemy_army_id": 21,
                "province_id": 8759,
                "player_hop": 2,
                "enemy_hop": 2,
            },
            audit["conflicts"],
        )

    def test_route_audit_strips_only_the_enemy_leading_current_province(
        self,
    ) -> None:
        enemy = _army(
            21,
            soldiers=800,
            province_id=90,
            controllable=False,
            move_target_province_id=99,
            army_state="moving",
            route_province_ids=[90, 52, 90, 99],
        )

        audit = _audit_war_route(
            [31, 90],
            origin_province_id=20,
            target_province_id=90,
            enemies=[enemy],
            allow_enemy_at_destination=True,
        )

        self.assertEqual(audit["status"], "unsafe")
        self.assertIn(
            {
                "kind": "enemy_route_intersection",
                "enemy_army_id": 21,
                "province_id": 90,
                "player_hop": 2,
                "enemy_hop": 2,
            },
            audit["conflicts"],
        )

    def test_decorated_auto_turn_preview_is_fresh_from_root_result(self) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            army_state="regular",
            route_province_ids=[],
        )
        direct = _preview_row(
            1,
            origin=20,
            target=2585,
            date_raw=24_000,
            route=[31, 2585],
        )
        decorated = {
            **direct,
            "command": "auto-turn",
            "result": {
                **direct["result"],
                "requested_step": "auto-turn",
                "auto_turn": {
                    "selected_step": "preview-move-army-11-to-2585"
                },
            },
        }

        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=0,
            date_raw=24_000,
            history=[decorated],
            objective=2585,
            steps=(
                "preview-move-army-11-to-2585",
                "move-army-11-to-2585",
            ),
        )

        self.assertEqual(plan["selected_step"], "move-army-11-to-2585")

    def test_exact_route_rejects_only_observable_convergence_kinds(self) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            army_state="regular",
            route_province_ids=[],
        )
        cases = {
            "enemy_current_on_route": _army(
                21, soldiers=800, province_id=31, controllable=False
            ),
            "enemy_target_on_route": _army(
                21,
                soldiers=800,
                province_id=90,
                controllable=False,
                move_target_province_id=31,
                army_state="moving",
            ),
            "shared_next_hop": _army(
                21,
                soldiers=800,
                province_id=90,
                controllable=False,
                move_target_province_id=99,
                army_state="moving",
                route_province_ids=[31, 99],
            ),
            "enemy_route_intersection": _army(
                21,
                soldiers=800,
                province_id=90,
                controllable=False,
                move_target_province_id=99,
                army_state="moving",
                route_province_ids=[52, 31, 99],
            ),
        }
        for conflict_kind, enemy in cases.items():
            with self.subTest(conflict_kind=conflict_kind):
                plan = _native_war_plan(
                    player=player,
                    enemies=[enemy],
                    score=0,
                    date_raw=24_000,
                    history=[
                        _preview_row(
                            1,
                            origin=20,
                            target=2585,
                            date_raw=24_000,
                            route=[20, 31, 2585],
                        )
                    ],
                    objectives=[2585, 2510],
                    steps=(
                        "move-army-11-to-2585",
                        "preview-move-army-11-to-2510",
                        "move-army-11-to-2510",
                        "life-advance",
                    ),
                )
                self.assertEqual(
                    plan["selected_step"],
                    "preview-move-army-11-to-2510",
                )
                self.assertEqual(
                    plan["route_rejections"][0]["conflicts"][0]["kind"],
                    conflict_kind,
                )

    def test_exact_route_rejects_opposite_enemy_edge(self) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            army_state="regular",
            route_province_ids=[],
        )
        enemy = _army(
            21,
            soldiers=800,
            province_id=90,
            controllable=False,
            move_target_province_id=99,
            army_state="moving",
            route_province_ids=[52, 31, 99],
        )
        plan = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=0,
            date_raw=24_000,
            history=[
                _preview_row(
                    1,
                    origin=20,
                    target=2585,
                    date_raw=24_000,
                    route=[20, 31, 52, 2585],
                )
            ],
            objectives=[2585, 2510],
            steps=("preview-move-army-11-to-2510", "life-advance"),
        )

        kinds = {
            conflict["kind"]
            for conflict in plan["route_rejections"][0]["conflicts"]
        }
        self.assertIn("enemy_route_intersection", kinds)
        self.assertIn("opposite_edge_intersection", kinds)

    def test_exact_route_ignores_retreating_enemy(self) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            army_state="regular",
            route_province_ids=[],
        )
        retreating = _army(
            21,
            soldiers=800,
            province_id=31,
            controllable=False,
            move_target_province_id=2585,
            army_state="retreating",
            route_province_ids=[31, 2585],
        )
        plan = _native_war_plan(
            player=player,
            enemies=[retreating],
            score=0,
            date_raw=24_000,
            history=[
                _preview_row(
                    1,
                    origin=20,
                    target=2585,
                    date_raw=24_000,
                    route=[20, 31, 2585],
                )
            ],
            objective=2585,
            steps=(
                "preview-move-army-11-to-2585",
                "move-army-11-to-2585",
                "life-advance",
            ),
        )

        self.assertEqual(plan["selected_step"], "move-army-11-to-2585")

    def test_passive_route_allows_only_the_pursued_enemy_at_destination(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            move_target_province_id=31,
            army_state="moving",
            route_province_ids=[20, 52, 31],
        )
        target_enemy = _army(
            21, soldiers=800, province_id=31, controllable=False
        )
        safe = _native_war_plan(
            player=player,
            enemies=[target_enemy],
            score=0,
            date_raw=24_000,
            steps=("life-advance",),
        )
        self.assertEqual(safe["phase"], "native_war_route_progress")
        self.assertEqual(safe["selected_step"], "life-advance")

        intermediate_enemy = _army(
            22, soldiers=700, province_id=52, controllable=False
        )
        blocked = _native_war_plan(
            player=player,
            enemies=[target_enemy, intermediate_enemy],
            score=0,
            date_raw=24_000,
            steps=("life-advance",),
        )
        self.assertEqual(blocked["phase"], "native_war_no_safe_exact_route")
        self.assertIsNone(blocked["selected_step"])

    def test_all_exact_routes_unsafe_never_uses_fallback_or_advances(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            army_state="regular",
            route_province_ids=[],
        )
        enemies = [
            _army(21, soldiers=800, province_id=31, controllable=False),
            _army(22, soldiers=700, province_id=52, controllable=False),
        ]
        plan = _native_war_plan(
            player=player,
            enemies=enemies,
            score=0,
            date_raw=24_000,
            history=[
                _preview_row(
                    1,
                    origin=20,
                    target=2585,
                    date_raw=24_000,
                    route=[31, 2585],
                ),
                _preview_row(
                    2,
                    origin=20,
                    target=2510,
                    date_raw=24_000,
                    route=[52, 2510],
                ),
            ],
            objectives=[2585, 2510],
            fallback=2543,
            steps=(
                "move-army-11-to-2585",
                "move-army-11-to-2510",
                "move-army-11-to-2543",
                "life-advance",
            ),
        )

        self.assertEqual(plan["phase"], "native_war_no_safe_exact_route")
        self.assertIsNone(plan["selected_step"])
        self.assertEqual(plan["required_step"], "safe-exact-war-route")

    def test_route_preview_freshness_uses_date_origin_and_latest_restore(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            army_state="regular",
            route_province_ids=[],
        )
        fresh = _preview_row(
            1,
            origin=20,
            target=2585,
            date_raw=24_000,
            route=[31, 2585],
        )
        histories = {
            "stale_date": [
                _preview_row(
                    1,
                    origin=20,
                    target=2585,
                    date_raw=23_976,
                    route=[31, 2585],
                )
            ],
            "stale_origin": [
                _preview_row(
                    1,
                    origin=19,
                    target=2585,
                    date_raw=24_000,
                    route=[31, 2585],
                )
            ],
            "pre_restore": [
                fresh,
                {
                    "index": 2,
                    "command": "restore-checkpoint",
                    "ok": True,
                    "result": {"status": "restored"},
                },
            ],
        }
        for stale_kind, history in histories.items():
            with self.subTest(stale_kind=stale_kind):
                plan = _native_war_plan(
                    player=player,
                    enemies=[],
                    score=0,
                    date_raw=24_000,
                    history=history,
                    objective=2585,
                    steps=(
                        "preview-move-army-11-to-2585",
                        "move-army-11-to-2585",
                    ),
                )
                self.assertEqual(
                    plan["selected_step"],
                    "preview-move-army-11-to-2585",
                )

    def test_gathering_or_same_date_deferred_preview_advances_once(self) -> None:
        gathering = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            army_state="gathering",
            route_province_ids=[],
        )
        gathering_plan = _native_war_plan(
            player=gathering,
            enemies=[],
            score=0,
            date_raw=24_000,
            objective=2585,
            steps=("preview-move-army-11-to-2585", "life-advance"),
        )
        self.assertEqual(
            gathering_plan["phase"], "native_war_gathering_progress"
        )
        self.assertEqual(gathering_plan["selected_step"], "life-advance")

        regular = {**gathering, "army_state": "regular"}
        deferred = {
            "index": 1,
            "command": "preview-move-army-11-to-2585",
            "ok": True,
            "result": {
                "accepted": False,
                "status": "deferred",
                "route_preview": {
                    "status": "deferred",
                    "reason": "army_not_move_ready",
                    "army_id": 11,
                    "origin_province_id": 20,
                    "target_province_id": 2585,
                    "route_province_ids": [],
                    "previewed_date_raw": 24_000,
                },
            },
        }
        same_date = _native_war_plan(
            player=regular,
            enemies=[],
            score=0,
            date_raw=24_000,
            history=[deferred],
            objective=2585,
            steps=("preview-move-army-11-to-2585", "life-advance"),
        )
        self.assertEqual(
            same_date["phase"], "native_war_route_preview_deferred"
        )
        self.assertEqual(same_date["selected_step"], "life-advance")

        next_date = _native_war_plan(
            player=regular,
            enemies=[],
            score=0,
            date_raw=24_024,
            history=[deferred],
            objective=2585,
            steps=("preview-move-army-11-to-2585", "life-advance"),
        )
        self.assertEqual(
            next_date["selected_step"],
            "preview-move-army-11-to-2585",
        )

    def test_passive_route_is_reaudited_before_every_advance(self) -> None:
        safe_player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            move_target_province_id=2585,
            army_state="moving",
            route_province_ids=[20, 31, 2585],
        )
        safe = _native_war_plan(
            player=safe_player,
            enemies=[],
            score=0,
            date_raw=24_000,
            objectives=[2585, 2510],
            steps=("life-advance",),
        )
        self.assertEqual(safe["phase"], "native_war_route_progress")
        self.assertEqual(safe["selected_step"], "life-advance")

        enemy = _army(21, soldiers=800, province_id=31, controllable=False)
        reroute = _native_war_plan(
            player=safe_player,
            enemies=[enemy],
            score=0,
            date_raw=24_000,
            objectives=[2585, 2510],
            steps=(
                "preview-move-army-11-to-2510",
                "move-army-11-to-2510",
                "life-advance",
            ),
        )
        self.assertEqual(
            reroute["selected_step"], "preview-move-army-11-to-2510"
        )
        self.assertNotEqual(reroute["selected_step"], "life-advance")

    def test_sieging_army_with_unsafe_active_route_reroutes_first(self) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            move_target_province_id=2585,
            army_state="sieging",
            route_province_ids=[20, 31, 2585],
        )
        enemy = _army(21, soldiers=800, province_id=31, controllable=False)

        plan = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=24,
            date_raw=24_000,
            objectives=[2585, 2510],
            steps=("preview-move-army-11-to-2510", "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_route_preview")
        self.assertEqual(
            plan["selected_step"], "preview-move-army-11-to-2510"
        )

    def test_stationary_siege_threat_previews_next_exact_before_advance(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=2585,
            controllable=True,
            army_state="sieging",
            route_province_ids=[],
        )
        approaching_enemy = _army(
            21,
            soldiers=800,
            province_id=2600,
            controllable=False,
            move_target_province_id=2596,
            army_state="moving",
            route_province_ids=[2596, 2585],
        )

        reroute = _native_war_plan(
            player=player,
            enemies=[approaching_enemy],
            score=24,
            date_raw=24_000,
            objectives=[2585, 2510],
            steps=("preview-move-army-11-to-2510", "life-advance"),
        )

        self.assertEqual(reroute["phase"], "native_war_route_preview")
        self.assertEqual(
            reroute["selected_step"], "preview-move-army-11-to-2510"
        )
        self.assertNotEqual(reroute["selected_step"], "life-advance")

        blocked = _native_war_plan(
            player=player,
            enemies=[approaching_enemy],
            score=24,
            date_raw=24_000,
            objective=2585,
            steps=("life-advance",),
            move_route_preview_supported=False,
        )
        self.assertEqual(blocked["phase"], "native_war_no_safe_exact_route")
        self.assertIsNone(blocked["selected_step"])

        deferred = _native_war_plan(
            player=player,
            enemies=[approaching_enemy],
            score=24,
            date_raw=24_000,
            history=[
                {
                    "index": 1,
                    "command": "preview-move-army-11-to-2510",
                    "ok": True,
                    "result": {
                        "route_preview": {
                            "status": "deferred",
                            "army_id": 11,
                            "origin_province_id": 2585,
                            "target_province_id": 2510,
                            "previewed_date_raw": 24_000,
                        }
                    },
                }
            ],
            objectives=[2585, 2510],
            steps=("life-advance",),
        )
        self.assertEqual(
            deferred["phase"], "native_war_no_safe_exact_route"
        )
        self.assertIsNone(deferred["selected_step"])

    def test_threatened_exact_siege_collects_all_previews_then_uses_shortest(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=2585,
            controllable=True,
            army_state="sieging",
            route_province_ids=[],
        )
        approaching_enemy = _army(
            21,
            soldiers=800,
            province_id=2600,
            controllable=False,
            move_target_province_id=2585,
            army_state="moving",
            route_province_ids=[2596, 2585],
        )
        first_preview = _preview_row(
            1,
            origin=2585,
            target=2510,
            date_raw=24_000,
            route=[2587, 2599, 2604, 2510],
        )
        steps = (
            "preview-move-army-11-to-2510",
            "preview-move-army-11-to-2548",
            "move-army-11-to-2510",
            "move-army-11-to-2548",
            "life-advance",
        )

        collect = _native_war_plan(
            player=player,
            enemies=[approaching_enemy],
            score=24,
            date_raw=24_000,
            history=[first_preview],
            objectives=[2585, 2510, 2548],
            steps=steps,
        )
        self.assertEqual(collect["phase"], "native_war_route_preview")
        self.assertEqual(
            collect["selected_step"], "preview-move-army-11-to-2548"
        )

        shortest = _native_war_plan(
            player=player,
            enemies=[approaching_enemy],
            score=24,
            date_raw=24_000,
            history=[
                first_preview,
                _preview_row(
                    2,
                    origin=2585,
                    target=2548,
                    date_raw=24_000,
                    route=[2587, 2548],
                ),
            ],
            objectives=[2585, 2510, 2548],
            steps=steps,
        )
        self.assertEqual(shortest["selected_step"], "move-army-11-to-2548")
        self.assertEqual(
            shortest["pursuit"]["route_audit"]["selection"],
            {
                "policy": "shortest_safe_route_then_objective_rank",
                "route_hops": 2,
                "objective_rank": 2,
            },
        )

        tied = _native_war_plan(
            player=player,
            enemies=[approaching_enemy],
            score=24,
            date_raw=24_000,
            history=[
                _preview_row(
                    1,
                    origin=2585,
                    target=2510,
                    date_raw=24_000,
                    route=[2587, 2510],
                ),
                _preview_row(
                    2,
                    origin=2585,
                    target=2548,
                    date_raw=24_000,
                    route=[2599, 2548],
                ),
            ],
            objectives=[2585, 2510, 2548],
            steps=steps,
        )
        self.assertEqual(tied["selected_step"], "move-army-11-to-2510")

    def test_ordinary_exact_routing_keeps_first_safe_rank_without_full_scan(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            army_state="regular",
            route_province_ids=[],
        )
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_000,
            history=[
                _preview_row(
                    1,
                    origin=20,
                    target=2510,
                    date_raw=24_000,
                    route=[31, 52, 2510],
                )
            ],
            objectives=[2510, 2548],
            steps=(
                "move-army-11-to-2510",
                "preview-move-army-11-to-2548",
                "move-army-11-to-2548",
                "life-advance",
            ),
        )

        self.assertEqual(plan["selected_step"], "move-army-11-to-2510")

    def test_restore_failure_memory_rejects_same_target_outside_fact_history(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=2598,
            controllable=True,
            army_state="sieging",
            route_province_ids=[],
        )
        enemy = _army(
            21,
            soldiers=800,
            province_id=2600,
            controllable=False,
            move_target_province_id=2598,
            army_state="moving",
            route_province_ids=[2596, 2598],
        )
        failure = {
            "status": "rolled_back_active_route",
            "episode_run_id": "native-707-test",
            "war_id": 88,
            "army_id": 11,
            "restored_origin_province_id": 2598,
            "target_province_id": 2568,
            "route_origin_province_id": 2598,
            "route_province_ids": [2599, 2587, 2585, 2572, 2568],
            "terminal_failure_target_province_id": 2568,
            "terminal_failure_route_origin_province_id": 2604,
            "terminal_failure_route_province_ids": [
                8759,
                2602,
                2591,
                2589,
                2579,
                2574,
                2572,
                2568,
            ],
        }
        plan = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=24,
            date_raw=24_000,
            history=[
                _preview_row(
                    1,
                    origin=2598,
                    target=2568,
                    date_raw=24_000,
                    route=[2599, 2587, 2585, 2572, 2568],
                ),
                _preview_row(
                    2,
                    origin=2598,
                    target=2548,
                    date_raw=24_000,
                    route=[2599, 2587, 2585, 2572, 2548],
                ),
            ],
            objectives=[2598, 2568, 2548],
            steps=(
                "move-army-11-to-2568",
                "move-army-11-to-2548",
                "life-advance",
            ),
            rollback_war_failure=failure,
        )

        self.assertEqual(plan["selected_step"], "move-army-11-to-2548")
        without_memory = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=24,
            date_raw=24_000,
            history=[
                _preview_row(
                    1,
                    origin=2598,
                    target=2568,
                    date_raw=24_000,
                    route=[2599, 2587, 2585, 2572, 2568],
                ),
                _preview_row(
                    2,
                    origin=2598,
                    target=2548,
                    date_raw=24_000,
                    route=[2599, 2587, 2585, 2572, 2548],
                ),
            ],
            objectives=[2598, 2568, 2548],
            steps=(
                "move-army-11-to-2568",
                "move-army-11-to-2548",
                "life-advance",
            ),
        )
        self.assertEqual(
            without_memory["selected_step"], "move-army-11-to-2568"
        )
        changed_route = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=24,
            date_raw=24_000,
            history=[
                _preview_row(
                    1,
                    origin=2598,
                    target=2568,
                    date_raw=24_000,
                    route=[2587, 2585, 2572, 2568],
                ),
                _preview_row(
                    2,
                    origin=2598,
                    target=2548,
                    date_raw=24_000,
                    route=[2599, 2587, 2585, 2572, 2548],
                ),
            ],
            objectives=[2598, 2568, 2548],
            steps=(
                "move-army-11-to-2568",
                "move-army-11-to-2548",
                "life-advance",
            ),
            rollback_war_failure=failure,
        )
        self.assertEqual(changed_route["selected_step"], "move-army-11-to-2568")

    def test_stationary_threat_blocks_nonobjective_recovery_advance(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=2598,
            controllable=True,
            army_state="regular",
        )
        approaching_enemy = _army(
            21,
            soldiers=800,
            province_id=2585,
            controllable=False,
            move_target_province_id=2598,
            army_state="moving",
        )

        plan = _native_war_plan(
            player=player,
            enemies=[approaching_enemy],
            score=24,
            date_raw=24_000,
            objective=2585,
            steps=("life-advance",),
        )

        self.assertEqual(plan["phase"], "native_war_no_safe_target")
        self.assertIsNone(plan["selected_step"])
        self.assertEqual(
            plan["route_rejections"][0]["kind"],
            "enemy_targeting_stationary_province",
        )

    def test_stationary_army_chooses_route_without_enemy_route_overlap(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=2604,
            controllable=True,
            army_state="regular",
            route_province_ids=[],
        )
        enemy = _army(
            21,
            soldiers=800,
            province_id=2597,
            controllable=False,
            move_target_province_id=2604,
            army_state="moving",
            route_province_ids=[2596, 2595, 2603, 2604],
        )
        history = [
            _preview_row(
                1,
                origin=2604,
                target=2585,
                date_raw=24_000,
                route=[2603, 2595, 2598, 2599, 2587, 2585],
            ),
            _preview_row(
                2,
                origin=2604,
                target=2568,
                date_raw=24_000,
                route=[8759, 2602, 2591, 2589, 2579, 2574, 2572, 2568],
            ),
        ]

        plan = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=38,
            date_raw=24_000,
            history=history,
            objectives=[2585, 2568],
            steps=(
                "move-army-11-to-2585",
                "move-army-11-to-2568",
                "life-advance",
            ),
        )

        self.assertEqual(plan["selected_step"], "move-army-11-to-2568")

    def test_preview_without_passive_routes_is_explicitly_unsupported(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            army_state="regular",
            route_province_ids=[],
        )

        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=0,
            date_raw=24_000,
            objective=2585,
            steps=("preview-move-army-11-to-2585", "life-advance"),
            army_routes_supported=False,
            move_route_preview_supported=True,
        )

        self.assertEqual(
            plan["phase"], "native_war_route_monitoring_unsupported"
        )
        self.assertIsNone(plan["selected_step"])
        self.assertEqual(plan["required_step"], "game.state.army-routes")

    def test_unsafe_route_never_advances_for_deferred_or_current_reroute(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            move_target_province_id=2585,
            army_state="moving",
            route_province_ids=[20, 31, 2585],
        )
        enemy = _army(21, soldiers=800, province_id=31, controllable=False)
        deferred = {
            "index": 2,
            "command": "move-army-11-to-2510",
            "ok": True,
            "result": {
                "accepted": False,
                "war_action": {
                    "status": "move_deferred",
                    "army_id": 11,
                    "target_province_id": 2510,
                    "submitted_date_raw": 24_000,
                },
            },
        }
        blocked = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=24,
            date_raw=24_000,
            history=[
                _preview_row(
                    1,
                    origin=20,
                    target=2510,
                    date_raw=24_000,
                    route=[52, 2510],
                ),
                deferred,
            ],
            objectives=[2585, 2510],
            steps=("move-army-11-to-2510", "life-advance"),
        )
        self.assertEqual(blocked["phase"], "native_war_unsafe_route_blocked")
        self.assertIsNone(blocked["selected_step"])

        current_only = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=24,
            date_raw=24_000,
            objectives=[2585, 20],
            steps=("move-army-11-to-20", "life-advance"),
        )
        self.assertEqual(current_only["phase"], "native_war_no_safe_exact_route")
        self.assertIsNone(current_only["selected_step"])

    def test_all_controllable_routes_and_all_wars_are_audited(self) -> None:
        strong = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            move_target_province_id=2585,
            army_state="moving",
            route_province_ids=[20, 52, 2585],
        )
        weak = _army(
            12,
            soldiers=500,
            province_id=20,
            controllable=True,
            move_target_province_id=2585,
            army_state="moving",
            route_province_ids=[20, 31, 2585],
        )
        selected_war_enemy = _army(
            21, soldiers=700, province_id=90, controllable=False
        )
        other_war_enemy = _army(
            22, soldiers=600, province_id=31, controllable=False
        )
        snapshot = {
            **_snapshot(90),
            "paused": True,
            "army_routes_supported": True,
            "move_route_preview_supported": True,
            "date_raw": 24_000,
            "native_command_history": [],
            "active_wars": [
                _war(
                    war_id=88,
                    allied_armies=[strong, weak],
                    enemy_armies=[selected_war_enemy],
                    score=24,
                    war_objective_province_ids=[2585, 2510],
                ),
                _war(
                    war_id=99,
                    allied_armies=[strong, weak],
                    enemy_armies=[other_war_enemy],
                    score=10,
                    war_objective_province_ids=[2600],
                ),
            ],
            "player_armies": [strong, weak],
        }
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: snapshot,
            execute=lambda _step, _revision: {},
            action_steps=("preview-move-army-12-to-2510", "life-advance"),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "native_war_route_preview")
        self.assertEqual(
            plan["selected_step"], "preview-move-army-12-to-2510"
        )
        self.assertNotEqual(plan["selected_step"], "life-advance")

    def test_unpaused_active_route_is_paused_before_route_audit(self) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            move_target_province_id=2585,
            army_state="moving",
            route_province_ids=[],
        )
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=0,
            date_raw=24_000,
            objective=2585,
            steps=("pause-map", "preview-move-army-11-to-2585"),
            paused=False,
        )

        self.assertEqual(
            plan["phase"], "native_war_route_wait_for_pause"
        )
        self.assertEqual(plan["selected_step"], "pause-map")

    def test_assault_only_capability_requires_pause_before_rich_state(self) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=2585,
            controllable=True,
            army_state="sieging",
        )
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=0,
            date_raw=24_000,
            objective=2585,
            steps=("pause-map", "life-advance"),
            paused=False,
            assault_supported=True,
        )

        self.assertEqual(plan["phase"], "native_war_route_wait_for_pause")
        self.assertEqual(plan["selected_step"], "pause-map")

    def test_route_field_without_capabilities_keeps_legacy_direct_move(self) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            army_state="regular",
            route_province_ids=[],
        )
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=0,
            date_raw=24_000,
            objective=2585,
            fallback=2543,
            steps=("move-army-11-to-2585", "life-advance"),
            army_routes_supported=False,
            move_route_preview_supported=False,
        )

        self.assertEqual(plan["selected_step"], "move-army-11-to-2585")

    def test_cross_run_plan_changes_native_opening_order_and_is_exposed(self) -> None:
        plans = {
            "war": [
                {"priority": 100, "action": "reassess_first_low_cost_expansion"},
                {"priority": 80, "action": "seek_current_life_marriage_alliance"},
            ],
            "marriage": [
                {"priority": 100, "action": "seek_current_life_marriage_alliance"},
                {"priority": 80, "action": "reassess_first_low_cost_expansion"},
            ],
        }
        selected: dict[str, str | None] = {}
        for label, priorities in plans.items():
            with tempfile.TemporaryDirectory() as temporary:
                state_dir = Path(temporary)
                strategy_path = state_dir / "strategy" / "one-life-history.json"
                strategy_path.parent.mkdir(parents=True)
                strategy_path.write_text(
                    json.dumps(
                        {
                            "format_version": 1,
                            "mode": "one_life_roguelike",
                            "continue_as_heir_after_death": False,
                            "episodes": [{"run_id": "previous"}],
                            "next_run_plan": {
                                "policy": "fixture",
                                "continue_as_heir_after_death": False,
                                "priorities": priorities,
                            },
                        }
                    ),
                    encoding="utf-8",
                )
                driver = CallbackGameplayDriver(
                    backend_id="native-headless",
                    snapshot=lambda: {
                        **_snapshot(7),
                        "played_character": {
                            "character_id": 707,
                            "alive": True,
                            "betrothed_id": None,
                            "primary_spouse_id": None,
                            "spouse_ids": [],
                        },
                        "native_command_history": [
                            {"index": 1, "command": "save-checkpoint", "ok": True}
                        ],
                    },
                    execute=lambda step, revision: {"step": step},
                    action_steps=(
                        "query-arrange-marriage-choices",
                        "query-declarable-wars",
                        "life-advance",
                    ),
                )
                driver.state_dir = state_dir
                plan = GameplayBridgeService(driver).plan_turn()["plan"]
                selected[label] = plan["selected_step"]
                self.assertEqual(
                    plan["cross_run_plan_used"]["priorities"], priorities
                )

        self.assertEqual(selected["war"], "query-declarable-wars")
        self.assertEqual(selected["marriage"], "query-arrange-marriage-choices")

    def test_hybrid_propagates_semantic_settlement_without_visual_action(
        self,
    ) -> None:
        fast = mock.Mock()
        fast.capabilities.return_value = {
            "snapshot": True,
            "wait_for_change": True,
            "action_steps": ["death-terminal"],
            "bridge_capabilities": ["game.state.snapshot"],
        }
        fast.take_snapshot.return_value = {
            **_snapshot(4, history=[{"command": "life-advance", "ok": True}]),
            "backend_id": "native-headless",
            "episode_character_id": 707,
            "one_life_terminal": True,
            "one_life_terminal_reason": "played_character_changed",
            "one_life_settlement": None,
        }
        baseline = mock.Mock()
        baseline.capabilities.return_value = {
            "snapshot": True,
            "wait_for_change": True,
            "action_steps": [],
            "bridge_capabilities": [
                "game.state.snapshot",
                ONE_LIFE_SETTLEMENT_CAPABILITY,
            ],
        }
        baseline.take_snapshot.return_value = {
            **_snapshot(7),
            "backend_id": "data-mod",
            "one_life_settlement": {
                "ready": True,
                "source_character_id": 707,
            },
        }
        hybrid = HybridGameplayDriver(fast, baseline)

        capabilities = hybrid.capabilities()
        snapshot = hybrid.take_snapshot()

        self.assertIn(
            ONE_LIFE_SETTLEMENT_CAPABILITY,
            capabilities["bridge_capabilities"],
        )
        self.assertEqual(
            snapshot["one_life_settlement"]["source_character_id"], 707
        )
        self.assertEqual(
            snapshot["one_life_settlement_backend"], "data-mod"
        )
        self.assertEqual(snapshot["one_life_settlement_status"], "ready")
        baseline.execute_step.assert_not_called()

    def test_hybrid_routes_supported_steps_to_fast_backend(self) -> None:
        calls: list[tuple[str, str]] = []
        fast = CallbackGameplayDriver(
            backend_id="native",
            snapshot=lambda: _snapshot(3),
            execute=lambda step, revision: calls.append(("fast", step))
            or {"step": step, "expected_revision": revision},
            action_steps=("life-advance",),
            source="injected-dll",
            latency="realtime",
        )
        vision = CallbackGameplayDriver(
            backend_id="vision",
            snapshot=lambda: _snapshot(3),
            execute=lambda step, revision: calls.append(("vision", step))
            or {"step": step, "expected_revision": revision},
            action_steps=("life-advance", "marriage-review"),
            source="ocr-keyboard-mouse",
        )
        hybrid = HybridGameplayDriver(fast, vision)
        revision = int(hybrid.take_snapshot()["revision"])

        self.assertEqual(
            hybrid.execute_step(
                "life-advance", expected_revision=revision
            )["backend_id"],
            "native",
        )
        self.assertEqual(
            hybrid.execute_step(
                "marriage-review", expected_revision=revision
            )["backend_id"],
            "vision",
        )
        self.assertEqual(calls, [("fast", "life-advance"), ("vision", "marriage-review")])

    def test_hybrid_does_not_replay_a_failed_supported_fast_action(self) -> None:
        vision_calls: list[str] = []

        def fail(_step: str, _revision: int | None):
            raise RuntimeError("native action failed after dispatch")

        fast = CallbackGameplayDriver(
            backend_id="native",
            snapshot=lambda: _snapshot(),
            execute=fail,
            action_steps=("life-advance",),
        )
        vision = CallbackGameplayDriver(
            backend_id="vision",
            snapshot=lambda: _snapshot(),
            execute=lambda step, _revision: vision_calls.append(step) or {},
            action_steps=("life-advance",),
        )

        with self.assertRaisesRegex(RuntimeError, "after dispatch"):
            HybridGameplayDriver(fast, vision).execute_step("life-advance")
        self.assertEqual(vision_calls, [])

    def test_hybrid_merges_fast_state_with_baseline_history_and_revisions(self) -> None:
        calls: list[tuple[str, int | None]] = []
        history = [
            {
                "command": "save-checkpoint",
                "ok": True,
                "result": {"final_screen": "map_hud"},
            }
        ]
        fast = CallbackGameplayDriver(
            backend_id="data-mod",
            snapshot=lambda: {
                **_snapshot(7, []),
                "phase": None,
                "total_days": 389_742,
            },
            execute=lambda step, revision: calls.append((step, revision)) or {},
            action_steps=(),
        )
        vision = CallbackGameplayDriver(
            backend_id="vision-session",
            snapshot=lambda: _snapshot(3, history),
            execute=lambda step, revision: calls.append((step, revision))
            or {"step": step},
            action_steps=("dynasty-review",),
        )
        hybrid = HybridGameplayDriver(fast, vision)

        snapshot = hybrid.take_snapshot()
        self.assertEqual(snapshot["backend_id"], "hybrid")
        self.assertEqual(snapshot["total_days"], 389_742)
        self.assertEqual(snapshot["history"], history)
        self.assertEqual(snapshot["phase"], "map_hud")
        self.assertEqual(snapshot["backend_revisions"], {"fast": 7, "baseline": 3})

        result = hybrid.execute_step(
            "dynasty-review", expected_revision=int(snapshot["revision"])
        )
        self.assertEqual(result["backend_id"], "vision-session")
        self.assertEqual(calls, [("dynasty-review", 3)])

    def test_service_reuses_existing_one_life_planner(self) -> None:
        driver = CallbackGameplayDriver(
            backend_id="fixture",
            snapshot=lambda: _snapshot(),
            execute=lambda _step, _revision: {},
            action_steps=(),
        )
        plan = GameplayBridgeService(driver).plan_turn()
        self.assertIsNone(plan["plan"]["selected_step"])
        self.assertEqual(plan["plan"]["required_step"], "save-checkpoint")
        self.assertEqual(plan["snapshot_id"], "session:0")

    def test_partial_native_backend_keeps_advancing_at_capability_gap(self) -> None:
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: _snapshot(
                4,
                [
                    {
                        "command": "save-checkpoint",
                        "ok": True,
                        "result": {"checkpoint": {"status": "saved"}},
                    }
                ],
            ),
            execute=lambda _step, _revision: {},
            action_steps=("save-checkpoint", "life-advance"),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["selected_step"], "life-advance")
        self.assertEqual(plan["required_step"], "dynasty-review")
        self.assertEqual(plan["deferred_phase"], "current_life_family")

    def test_planner_prioritizes_pending_native_character_interaction(self) -> None:
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(6),
                "pending_character_interaction": {
                    "instance_id": 72,
                    "sender_character_id": 501,
                    "auto_accept_notification": False,
                },
            },
            execute=lambda _step, _revision: {},
            action_steps=("accept-pending-character-interaction",),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(
            plan["selected_step"], "accept-pending-character-interaction"
        )
        self.assertEqual(plan["pending_character_interaction"]["instance_id"], 72)

    def test_native_war_planner_raises_when_no_player_army_exists(self) -> None:
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(7),
                "active_wars": [_war(allied_armies=[], enemy_armies=[])],
                "player_armies": [],
            },
            execute=lambda _step, _revision: {},
            action_steps=("raise-troops-default",),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "native_war_raise")
        self.assertEqual(plan["selected_step"], "raise-troops-default")

    def test_native_war_planner_chases_largest_visible_enemy(self) -> None:
        player = _army(
            11, soldiers=1_700, province_id=20, controllable=True
        )
        smaller = _army(
            21, soldiers=800, province_id=31, controllable=False
        )
        larger = _army(
            22, soldiers=2_400, province_id=32, controllable=False
        )
        step = "move-army-11-to-32"
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(8),
                "active_wars": [
                    _war(
                        allied_armies=[player],
                        enemy_armies=[smaller, larger],
                    )
                ],
                "player_armies": [player],
            },
            execute=lambda _step, _revision: {},
            action_steps=(step,),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "native_war_pursuit")
        self.assertEqual(plan["selected_step"], step)
        self.assertEqual(plan["pursuit"]["target_army_id"], 22)
        self.assertEqual(plan["pursuit"]["target_province_id"], 32)

    def test_native_war_planner_uses_stable_enemy_when_soldiers_unknown(self) -> None:
        player = _army(11, soldiers=900, province_id=20, controllable=True)
        enemy_22 = _army(
            22, soldiers=None, province_id=42, controllable=False
        )
        enemy_21 = _army(
            21, soldiers=None, province_id=41, controllable=False
        )
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(9),
                "active_wars": [
                    _war(
                        allied_armies=[player],
                        enemy_armies=[enemy_22, enemy_21],
                    )
                ],
                "player_armies": [player],
            },
            execute=lambda _step, _revision: {},
            action_steps=("move-army-11-to-41",),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["selected_step"], "move-army-11-to-41")
        self.assertEqual(plan["pursuit"]["target_army_id"], 21)

    def test_zero_score_attacker_still_chases_visible_enemy(self) -> None:
        player = _army(11, soldiers=900, province_id=20, controllable=True)
        enemy = _army(21, soldiers=1_100, province_id=41, controllable=False)
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(9),
                "active_wars": [
                    _war(
                        allied_armies=[player],
                        enemy_armies=[enemy],
                        score=0,
                        enemy_primary_default_raise_province_id=77,
                    )
                ],
                "player_armies": [player],
            },
            execute=lambda _step, _revision: {},
            action_steps=(
                "move-army-11-to-41",
                "move-army-11-to-77",
            ),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["selected_step"], "move-army-11-to-41")
        self.assertEqual(plan["pursuit"]["objective_kind"], "pursuit")
        self.assertEqual(plan["pursuit"]["target_army_id"], 21)

    def test_zero_score_attacker_uses_exact_objective_before_enemy(self) -> None:
        player = _army(11, soldiers=900, province_id=20, controllable=True)
        enemy = _army(21, soldiers=1_100, province_id=41, controllable=False)
        plan = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=0,
            date_raw=24_000,
            objective=2585,
            fallback=2543,
            steps=(
                "move-army-11-to-41",
                "move-army-11-to-2585",
                "move-army-11-to-2543",
            ),
        )

        self.assertEqual(plan["selected_step"], "move-army-11-to-2585")
        self.assertEqual(plan["pursuit"]["objective_kind"], "siege")
        self.assertEqual(plan["pursuit"]["target_source"], "war_objective_province")

    def test_positive_score_attacker_advances_same_province_battle(self) -> None:
        player = _army(11, soldiers=900, province_id=41, controllable=True)
        enemy = _army(21, soldiers=1_100, province_id=41, controllable=False)
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(9),
                "active_wars": [
                    _war(
                        allied_armies=[player],
                        enemy_armies=[enemy],
                        score=24,
                        enemy_primary_default_raise_province_id=77,
                    )
                ],
                "player_armies": [player],
            },
            execute=lambda _step, _revision: {},
            action_steps=("move-army-11-to-77", "life-advance"),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["selected_step"], "life-advance")
        self.assertEqual(plan["pursuit"]["objective_kind"], "pursuit")
        self.assertEqual(plan["pursuit"]["target_army_id"], 21)
        self.assertEqual(plan["pursuit"]["target_province_id"], 41)

    def test_positive_score_attacker_switches_to_siege_objective(self) -> None:
        player = _army(11, soldiers=900, province_id=20, controllable=True)
        enemy = _army(21, soldiers=1_100, province_id=41, controllable=False)
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(9),
                "active_wars": [
                    _war(
                        allied_armies=[player],
                        enemy_armies=[enemy],
                        score=24,
                        enemy_primary_default_raise_province_id=77,
                    )
                ],
                "player_armies": [player],
            },
            execute=lambda _step, _revision: {},
            action_steps=(
                "move-army-11-to-41",
                "move-army-11-to-77",
            ),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["selected_step"], "move-army-11-to-77")
        self.assertEqual(plan["pursuit"]["objective_kind"], "siege")
        self.assertIsNone(plan["pursuit"]["target_army_id"])
        self.assertEqual(plan["pursuit"]["target_province_id"], 77)

    def test_attacker_at_siege_objective_advances_without_retargeting(self) -> None:
        player = _army(11, soldiers=900, province_id=77, controllable=True)
        enemy = _army(21, soldiers=1_100, province_id=42, controllable=False)
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(10),
                "active_wars": [
                    _war(
                        allied_armies=[player],
                        enemy_armies=[enemy],
                        score=24,
                        enemy_primary_default_raise_province_id=77,
                    )
                ],
                "player_armies": [player],
            },
            execute=lambda _step, _revision: {},
            action_steps=("move-army-11-to-42", "life-advance"),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["selected_step"], "life-advance")
        self.assertEqual(plan["pursuit"]["objective_kind"], "siege")
        self.assertEqual(plan["pursuit"]["target_province_id"], 77)

    def test_exact_war_objective_precedes_legacy_rally_fallback(self) -> None:
        player = _army(11, soldiers=900, province_id=20, controllable=True)
        enemy = _army(21, soldiers=800, province_id=41, controllable=False)

        plan = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=24,
            date_raw=24_000,
            objective=2585,
            fallback=2543,
            steps=("move-army-11-to-2585", "move-army-11-to-2543"),
        )

        self.assertEqual(plan["selected_step"], "move-army-11-to-2585")
        self.assertEqual(plan["pursuit"]["target_source"], "war_objective_province")

    def test_exact_war_objectives_preserve_native_dfs_order(self) -> None:
        player = _army(11, soldiers=900, province_id=20, controllable=True)
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_000,
            objectives=[2585, 2510, 2548, 2585],
            fallback=2543,
            steps=(
                "move-army-11-to-2585",
                "move-army-11-to-2510",
                "move-army-11-to-2548",
            ),
        )

        self.assertEqual(plan["selected_step"], "move-army-11-to-2585")
        self.assertEqual(plan["pursuit"]["target_province_id"], 2585)

    def test_completed_exact_objective_rotates_to_legacy_fallback(self) -> None:
        sieging = _army(
            11, soldiers=900, province_id=2585, controllable=True,
            army_state="sieging",
        )
        idle = _army(11, soldiers=900, province_id=2585, controllable=True)
        enemy = _army(21, soldiers=800, province_id=41, controllable=False)
        before = _war_progress(
            24_000, player=sieging, enemies=[enemy], score=24,
            objectives=[2585], fallback=2543,
        )
        after = _war_progress(
            24_168, player=idle, enemies=[enemy], score=30,
            objectives=[2585], fallback=2543,
        )

        plan = _native_war_plan(
            player=idle, enemies=[enemy], score=30, date_raw=24_168,
            history=[_advance_row(1, before, after)],
            objective=2585, fallback=2543,
            steps=("move-army-11-to-2585", "move-army-11-to-2543"),
        )

        self.assertEqual(plan["selected_step"], "move-army-11-to-2543")
        self.assertEqual(
            plan["pursuit"]["target_source"],
            "enemy_primary_default_raise_province",
        )

    def test_completed_exact_and_fallback_objectives_rotate_to_enemy(self) -> None:
        enemy = _army(21, soldiers=800, province_id=41, controllable=False)
        exact_siege = _army(
            11, soldiers=900, province_id=2585, controllable=True,
            army_state="sieging",
        )
        exact_done = _army(11, soldiers=900, province_id=2585, controllable=True)
        fallback_siege = _army(
            11, soldiers=900, province_id=2543, controllable=True,
            army_state="sieging",
        )
        fallback_done = _army(11, soldiers=900, province_id=2543, controllable=True)
        history = [
            _advance_row(
                1,
                _war_progress(
                    24_000, player=exact_siege, enemies=[enemy], score=24,
                    objectives=[2585], fallback=2543,
                ),
                _war_progress(
                    24_168, player=exact_done, enemies=[enemy], score=30,
                    objectives=[2585], fallback=2543,
                ),
            ),
            _advance_row(
                2,
                _war_progress(
                    24_168, player=fallback_siege, enemies=[enemy], score=30,
                    objectives=[2585], fallback=2543,
                ),
                _war_progress(
                    24_336, player=fallback_done, enemies=[enemy], score=36,
                    objectives=[2585], fallback=2543,
                ),
            ),
        ]

        plan = _native_war_plan(
            player=fallback_done, enemies=[enemy], score=36, date_raw=24_336,
            history=history, objective=2585, fallback=2543,
            steps=("move-army-11-to-41", "life-advance"),
        )

        self.assertEqual(plan["selected_step"], "move-army-11-to-41")
        self.assertEqual(plan["pursuit"]["target_source"], "enemy_army")

        waiting = _native_war_plan(
            player=fallback_done,
            enemies=[],
            score=36,
            date_raw=24_336,
            history=history,
            objective=2585,
            fallback=2543,
            steps=("life-advance",),
        )
        self.assertEqual(waiting["phase"], "native_war_reconnaissance")
        self.assertEqual(waiting["selected_step"], "life-advance")

    def test_exact_siege_state_keeps_advancing_current_objective(self) -> None:
        player = _army(
            11, soldiers=900, province_id=2585, controllable=True,
            army_state="sieging",
        )
        plan = _native_war_plan(
            player=player, enemies=[], score=24, date_raw=24_000,
            objective=2585, fallback=2543,
            steps=("move-army-11-to-2543", "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_siege_progress")
        self.assertEqual(plan["selected_step"], "life-advance")

    def test_exact_player_siege_uses_authoritative_progress_state(self) -> None:
        player = _army(
            11, soldiers=None, province_id=2585, controllable=True,
            army_state="sieging",
        )
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_000,
            objective=2585,
            objective_states=[
                _objective_state(
                    2585,
                    garrison_size=650,
                    besieging_strength=650,
                    active_siege=_active_siege(),
                )
            ],
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            steps=("life-advance",),
        )

        self.assertEqual(plan["phase"], "native_war_siege_progress")
        self.assertEqual(plan["selected_step"], "life-advance")
        self.assertEqual(plan["siege_state"]["status"], "progressing")

    def test_breached_safe_exact_siege_starts_assault(self) -> None:
        player = _army(
            11,
            soldiers=650,
            province_id=2585,
            controllable=True,
            army_state="sieging",
        )
        active_siege = _active_siege(
            assault_observable=True,
            breach_level=1,
            assault_in_progress=False,
            can_start_assault=True,
            can_stop_assault=False,
            assault_daily_progress_raw=340_000,
            assault_daily_casualties=16,
        )
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_000,
            objective=2585,
            objective_states=[
                _objective_state(
                    2585,
                    garrison_size=500,
                    besieging_strength=650,
                    active_siege=active_siege,
                )
            ],
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            assault_supported=True,
            steps=("start-assault-901", "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_assault_start")
        self.assertEqual(plan["selected_step"], "start-assault-901")
        self.assertTrue(plan["assault_state"]["one_day_safe"])
        self.assertEqual(
            plan["assault_state"]["projection_horizon_days"], 1
        )
        self.assertNotIn("eta", str(plan).casefold())

    def test_assault_start_is_blocked_by_unsafe_active_siege_route(self) -> None:
        player = _army(
            11,
            soldiers=650,
            province_id=2585,
            controllable=True,
            move_target_province_id=2600,
            army_state="sieging",
            route_province_ids=[2590, 2600],
        )
        enemy = _army(
            21,
            soldiers=700,
            province_id=2590,
            controllable=False,
            army_state="regular",
        )
        plan = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=24,
            date_raw=24_000,
            objective=2585,
            objective_states=[
                _objective_state(
                    2585,
                    garrison_size=500,
                    besieging_strength=650,
                    active_siege=_active_siege(
                        assault_observable=True,
                        breach_level=1,
                        assault_in_progress=False,
                        can_start_assault=True,
                        can_stop_assault=False,
                        assault_daily_progress_raw=340_000,
                        assault_daily_casualties=16,
                    ),
                )
            ],
            army_routes_supported=True,
            move_route_preview_supported=False,
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            assault_supported=True,
            steps=(
                "start-assault-901",
                "move-army-11-to-2590",
                "life-advance",
            ),
        )

        self.assertNotEqual(plan["phase"], "native_war_assault_start")
        self.assertNotEqual(plan["selected_step"], "start-assault-901")

    def test_moving_army_without_route_target_blocks_assault_and_time(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=650,
            province_id=2585,
            controllable=True,
            army_state="moving",
            route_province_ids=[],
        )
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_000,
            objective=2585,
            objective_states=[
                _objective_state(
                    2585,
                    active_siege=_active_siege(
                        assault_observable=True,
                        breach_level=1,
                        assault_in_progress=False,
                        can_start_assault=True,
                        can_stop_assault=False,
                        assault_daily_progress_raw=340_000,
                        assault_daily_casualties=16,
                    ),
                )
            ],
            army_routes_supported=True,
            move_route_preview_supported=False,
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            assault_supported=True,
            steps=("start-assault-901", "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_route_audit_pending")
        self.assertIsNone(plan["selected_step"])

    def test_moving_state_code_without_route_target_blocks_assault_and_time(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=650,
            province_id=2585,
            controllable=True,
            army_state_code=7,
            route_province_ids=[],
        )
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_000,
            objective=2585,
            objective_states=[
                _objective_state(
                    2585,
                    active_siege=_active_siege(
                        assault_observable=True,
                        breach_level=1,
                        assault_in_progress=False,
                        can_start_assault=True,
                        can_stop_assault=False,
                        assault_daily_progress_raw=340_000,
                        assault_daily_casualties=16,
                    ),
                )
            ],
            army_routes_supported=True,
            move_route_preview_supported=False,
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            assault_supported=True,
            steps=("start-assault-901", "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_route_audit_pending")
        self.assertIsNone(plan["selected_step"])

    def test_started_assault_lifecycle_blocks_missing_rich_row_direct_and_decorated(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=650,
            province_id=2585,
            controllable=True,
            army_state="sieging",
        )
        for decorated in (False, True):
            with self.subTest(decorated=decorated):
                plan = _native_war_plan(
                    player=player,
                    enemies=[],
                    score=24,
                    date_raw=24_000,
                    history=[
                        _assault_action_row(
                            1,
                            status="assault_started",
                            decorated=decorated,
                        )
                    ],
                    objective=2585,
                    objective_states=[],
                    occupation_supported=True,
                    garrison_supported=True,
                    siege_progress_supported=True,
                    assault_supported=True,
                    steps=("life-advance",),
                )

                self.assertEqual(
                    plan["phase"], "native_war_assault_lifecycle_blocked"
                )
                self.assertIsNone(plan["selected_step"])
                self.assertEqual(
                    plan["assault_lifecycles"][0]["reason"],
                    "objective_row_unavailable_after_start",
                )

    def test_started_assault_lifecycle_closes_on_exact_no_siege_stop_or_restore(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=650,
            province_id=2585,
            controllable=True,
            army_state="sieging",
        )
        cases = {
            "exact_no_siege": {
                "history": [
                    _assault_action_row(1, status="assault_started")
                ],
                "states": [_objective_state(2585, active_siege=None)],
            },
            "stopped": {
                "history": [
                    _assault_action_row(1, status="assault_started"),
                    _assault_action_row(2, status="assault_stopped"),
                ],
                "states": [],
            },
            "restored": {
                "history": [
                    _assault_action_row(1, status="assault_started"),
                    {
                        "index": 2,
                        "command": "restore-checkpoint",
                        "ok": True,
                        "result": {"status": "restored"},
                    },
                ],
                "states": [],
            },
        }
        for name, case in cases.items():
            with self.subTest(case=name):
                plan = _native_war_plan(
                    player=player,
                    enemies=[],
                    score=24,
                    date_raw=24_000,
                    history=case["history"],
                    objective=2585,
                    objective_states=case["states"],
                    occupation_supported=True,
                    garrison_supported=True,
                    siege_progress_supported=True,
                    assault_supported=True,
                    steps=("life-advance",),
                )

                self.assertNotEqual(
                    plan["phase"], "native_war_assault_lifecycle_blocked"
                )

    def test_failed_assault_slice_stops_direct_and_decorated_history(self) -> None:
        player = _army(
            11,
            soldiers=None,
            province_id=2585,
            controllable=True,
            army_state="sieging",
        )
        active_state = _objective_state(
            2585,
            garrison_size=500,
            besieging_strength=634,
            active_siege=_active_siege(
                assault_observable=True,
                breach_level=1,
                assault_in_progress=True,
                can_start_assault=False,
                can_stop_assault=True,
                assault_daily_progress_raw=330_000,
                assault_daily_casualties=16,
            ),
        )
        for decorated in (False, True):
            with self.subTest(decorated=decorated):
                plan = _native_war_plan(
                    player=player,
                    enemies=[],
                    score=24,
                    date_raw=24_024,
                    history=[
                        _assault_action_row(
                            1,
                            status="assault_started",
                            decorated=decorated,
                        ),
                        _failed_life_advance_row(
                            2, decorated=decorated
                        ),
                    ],
                    objective=2585,
                    objective_states=[active_state],
                    occupation_supported=True,
                    garrison_supported=True,
                    siege_progress_supported=True,
                    assault_supported=True,
                    steps=("stop-assault-901", "life-advance"),
                )

                self.assertEqual(plan["selected_step"], "stop-assault-901")
                self.assertIn(
                    "previous_assault_slice_failed_unknown",
                    plan["assault_state"]["one_day_rejection_reasons"],
                )

    def test_assault_start_requires_breach_native_gate_and_one_day_budget(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=650,
            province_id=2585,
            controllable=True,
            army_state="sieging",
        )
        cases = (
            {
                "name": "intact",
                "breach_level": 0,
                "can_start": True,
                "casualties": 16,
            },
            {
                "name": "validator",
                "breach_level": 1,
                "can_start": False,
                "casualties": 16,
            },
            {
                "name": "casualties",
                "breach_level": 1,
                "can_start": True,
                "casualties": 151,
            },
        )
        for case in cases:
            with self.subTest(case=case["name"]):
                active_siege = _active_siege(
                    assault_observable=True,
                    breach_level=int(case["breach_level"]),
                    assault_in_progress=False,
                    can_start_assault=bool(case["can_start"]),
                    can_stop_assault=False,
                    assault_daily_progress_raw=340_000,
                    assault_daily_casualties=int(case["casualties"]),
                )
                plan = _native_war_plan(
                    player=player,
                    enemies=[],
                    score=24,
                    date_raw=24_000,
                    objective=2585,
                    objective_states=[
                        _objective_state(
                            2585,
                            garrison_size=500,
                            besieging_strength=650,
                            active_siege=active_siege,
                        )
                    ],
                    occupation_supported=True,
                    garrison_supported=True,
                    siege_progress_supported=True,
                    assault_supported=True,
                    steps=("start-assault-901", "life-advance"),
                )

                self.assertNotEqual(
                    plan["selected_step"], "start-assault-901"
                )

    def test_active_assault_advances_one_day_then_stops_when_unsafe(self) -> None:
        player = _army(
            11,
            soldiers=650,
            province_id=2585,
            controllable=True,
            army_state="sieging",
        )

        def assault(casualties: int) -> dict[str, object]:
            return _active_siege(
                assault_observable=True,
                breach_level=1,
                assault_in_progress=True,
                can_start_assault=False,
                can_stop_assault=True,
                assault_daily_progress_raw=340_000,
                assault_daily_casualties=casualties,
            )

        safe = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_000,
            objective=2585,
            objective_states=[
                _objective_state(
                    2585,
                    garrison_size=500,
                    besieging_strength=650,
                    active_siege=assault(16),
                )
            ],
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            assault_supported=True,
            steps=("stop-assault-901", "life-advance"),
        )
        self.assertEqual(safe["phase"], "native_war_assault_daily_progress")
        self.assertEqual(safe["selected_step"], "life-advance")
        self.assertEqual(safe["assault_state"]["projection_horizon_days"], 1)

        unsafe = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_024,
            objective=2585,
            objective_states=[
                _objective_state(
                    2585,
                    garrison_size=500,
                    besieging_strength=650,
                    active_siege=assault(151),
                )
            ],
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            assault_supported=True,
            steps=("stop-assault-901", "life-advance"),
        )
        self.assertEqual(unsafe["phase"], "native_war_assault_stop")
        self.assertEqual(unsafe["selected_step"], "stop-assault-901")
        self.assertIn(
            "projected_strength_below_garrison",
            unsafe["assault_state"]["one_day_rejection_reasons"],
        )

    def test_active_assault_stops_before_observed_enemy_convergence(self) -> None:
        player = _army(
            11,
            soldiers=650,
            province_id=2585,
            controllable=True,
            army_state="sieging",
        )
        enemy = _army(
            21,
            soldiers=900,
            province_id=2600,
            controllable=False,
            move_target_province_id=2585,
            route_province_ids=[2590, 2585],
            army_state="moving",
        )
        plan = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=24,
            date_raw=24_000,
            objective=2585,
            objective_states=[
                _objective_state(
                    2585,
                    garrison_size=500,
                    besieging_strength=650,
                    active_siege=_active_siege(
                        assault_observable=True,
                        breach_level=1,
                        assault_in_progress=True,
                        can_start_assault=False,
                        can_stop_assault=True,
                        assault_daily_progress_raw=340_000,
                        assault_daily_casualties=16,
                    ),
                )
            ],
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            assault_supported=True,
            steps=("stop-assault-901", "life-advance"),
        )

        self.assertEqual(plan["selected_step"], "stop-assault-901")
        self.assertIn(
            "enemy_convergence_observed",
            plan["assault_state"]["one_day_rejection_reasons"],
        )

    def test_active_assault_rechecks_realized_daily_progress_and_losses(
        self,
    ) -> None:
        before_player = _army(
            11,
            soldiers=650,
            province_id=2585,
            controllable=True,
            army_state="sieging",
        )
        after_player = _army(
            11,
            soldiers=634,
            province_id=2585,
            controllable=True,
            army_state="sieging",
        )
        active_siege = _active_siege(
            assault_observable=True,
            breach_level=1,
            assault_in_progress=True,
            can_start_assault=False,
            can_stop_assault=True,
            assault_daily_progress_raw=340_000,
            assault_daily_casualties=16,
        )
        state = _objective_state(
            2585,
            garrison_size=500,
            besieging_strength=634,
            active_siege=active_siege,
        )
        history = [
            _advance_row(
                1,
                _war_progress(
                    24_000,
                    player=before_player,
                    enemies=[],
                    score=24,
                    objectives=[2585],
                    objective_states=[state],
                ),
                _war_progress(
                    24_024,
                    player=after_player,
                    enemies=[],
                    score=24,
                    objectives=[2585],
                    objective_states=[state],
                ),
            )
        ]
        plan = _native_war_plan(
            player=after_player,
            enemies=[],
            score=24,
            date_raw=24_024,
            history=history,
            objective=2585,
            objective_states=[state],
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            assault_supported=True,
            steps=("stop-assault-901", "life-advance"),
        )

        self.assertEqual(plan["selected_step"], "stop-assault-901")
        self.assertEqual(
            plan["assault_state"]["previous_assault_day"]["soldier_loss"],
            16,
        )
        self.assertEqual(
            plan["assault_state"]["previous_assault_day"]["strength_loss"],
            0,
        )
        self.assertIn(
            "previous_assault_day_no_work_progress",
            plan["assault_state"]["one_day_rejection_reasons"],
        )

    def test_active_assault_continues_from_realized_strength_with_null_soldiers(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=None,
            province_id=2585,
            controllable=True,
            army_state="sieging",
        )
        before_state = _objective_state(
            2585,
            garrison_size=500,
            besieging_strength=650,
            active_siege=_active_siege(
                current_work_raw=2_500_000,
                assault_observable=True,
                breach_level=1,
                assault_in_progress=True,
                can_start_assault=False,
                can_stop_assault=True,
                assault_daily_progress_raw=340_000,
                assault_daily_casualties=16,
            ),
        )
        after_state = _objective_state(
            2585,
            garrison_size=500,
            besieging_strength=634,
            active_siege=_active_siege(
                current_work_raw=2_840_000,
                assault_observable=True,
                breach_level=1,
                assault_in_progress=True,
                can_start_assault=False,
                can_stop_assault=True,
                assault_daily_progress_raw=330_000,
                assault_daily_casualties=16,
            ),
        )
        history = [
            _advance_row(
                1,
                _war_progress(
                    24_000,
                    player=player,
                    enemies=[],
                    score=24,
                    objectives=[2585],
                    objective_states=[before_state],
                ),
                _war_progress(
                    24_024,
                    player=player,
                    enemies=[],
                    score=24,
                    objectives=[2585],
                    objective_states=[after_state],
                ),
            )
        ]

        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_024,
            history=history,
            objective=2585,
            objective_states=[after_state],
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            assault_supported=True,
            steps=("stop-assault-901", "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_assault_daily_progress")
        self.assertEqual(plan["selected_step"], "life-advance")
        previous_day = plan["assault_state"]["previous_assault_day"]
        self.assertEqual(previous_day["strength_loss"], 16)
        self.assertIsNone(previous_day["soldier_loss"])
        self.assertTrue(plan["assault_state"]["one_day_safe"])

    def test_active_assault_stops_when_realized_strength_is_unavailable(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=None,
            province_id=2585,
            controllable=True,
            army_state="sieging",
        )
        before_state = _objective_state(
            2585,
            garrison_size=500,
            besieging_strength=None,
            active_siege=_active_siege(
                current_work_raw=2_500_000,
                assault_observable=True,
                breach_level=1,
                assault_in_progress=True,
                can_start_assault=False,
                can_stop_assault=True,
                assault_daily_progress_raw=340_000,
                assault_daily_casualties=16,
            ),
        )
        after_state = _objective_state(
            2585,
            garrison_size=500,
            besieging_strength=634,
            active_siege=_active_siege(
                current_work_raw=2_840_000,
                assault_observable=True,
                breach_level=1,
                assault_in_progress=True,
                can_start_assault=False,
                can_stop_assault=True,
                assault_daily_progress_raw=330_000,
                assault_daily_casualties=16,
            ),
        )
        history = [
            _advance_row(
                1,
                _war_progress(
                    24_000,
                    player=player,
                    enemies=[],
                    score=24,
                    objectives=[2585],
                    objective_states=[before_state],
                ),
                _war_progress(
                    24_024,
                    player=player,
                    enemies=[],
                    score=24,
                    objectives=[2585],
                    objective_states=[after_state],
                ),
            )
        ]

        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_024,
            history=history,
            objective=2585,
            objective_states=[after_state],
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            assault_supported=True,
            steps=("stop-assault-901", "life-advance"),
        )

        self.assertEqual(plan["selected_step"], "stop-assault-901")
        self.assertIn(
            "previous_assault_day_strength_change_unavailable",
            plan["assault_state"]["one_day_rejection_reasons"],
        )

    def test_active_assault_stops_after_strength_falls_below_garrison(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=None,
            province_id=2585,
            controllable=True,
            army_state="sieging",
        )
        before_state = _objective_state(
            2585,
            garrison_size=500,
            besieging_strength=650,
            active_siege=_active_siege(
                current_work_raw=2_500_000,
                assault_observable=True,
                breach_level=1,
                assault_in_progress=True,
                can_start_assault=False,
                can_stop_assault=True,
                assault_daily_progress_raw=340_000,
                assault_daily_casualties=16,
            ),
        )
        after_state = _objective_state(
            2585,
            garrison_size=500,
            besieging_strength=499,
            active_siege=_active_siege(
                current_work_raw=2_840_000,
                assault_observable=True,
                breach_level=1,
                assault_in_progress=True,
                can_start_assault=False,
                can_stop_assault=True,
                assault_daily_progress_raw=330_000,
                assault_daily_casualties=4,
            ),
        )
        history = [
            _advance_row(
                1,
                _war_progress(
                    24_000,
                    player=player,
                    enemies=[],
                    score=24,
                    objectives=[2585],
                    objective_states=[before_state],
                ),
                _war_progress(
                    24_024,
                    player=player,
                    enemies=[],
                    score=24,
                    objectives=[2585],
                    objective_states=[after_state],
                ),
            )
        ]

        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_024,
            history=history,
            objective=2585,
            objective_states=[after_state],
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            assault_supported=True,
            steps=("stop-assault-901", "life-advance"),
        )

        self.assertEqual(plan["selected_step"], "stop-assault-901")
        self.assertEqual(
            plan["assault_state"]["previous_assault_day"]["strength_loss"],
            151,
        )
        self.assertIn(
            "projected_strength_below_garrison",
            plan["assault_state"]["one_day_rejection_reasons"],
        )

    def test_advertised_but_unobservable_assault_state_blocks_time(self) -> None:
        player = _army(
            11,
            soldiers=650,
            province_id=2585,
            controllable=True,
            army_state="sieging",
        )
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_000,
            objective=2585,
            objective_states=[
                _objective_state(
                    2585,
                    active_siege=_active_siege(
                        assault_observable=False
                    ),
                )
            ],
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            assault_supported=True,
            steps=("life-advance",),
        )

        self.assertEqual(
            plan["phase"], "native_war_assault_observation_blocked"
        )
        self.assertIsNone(plan["selected_step"])

    def test_occupation_only_capability_keeps_legacy_siege_stickiness(
        self,
    ) -> None:
        player = _army(
            11, soldiers=None, province_id=2585, controllable=True,
            army_state="sieging",
        )
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_000,
            objectives=[2585, 2510],
            objective_states=[
                _objective_state(2585, fort_level=3),
                _objective_state(2510, fort_level=1),
            ],
            occupation_supported=True,
            fort_level_supported=True,
            siege_progress_supported=False,
            steps=("move-army-11-to-2510", "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_siege_progress")
        self.assertEqual(plan["selected_step"], "life-advance")

    def test_insufficient_exact_siege_strength_moves_to_next_objective(
        self,
    ) -> None:
        player = _army(
            11, soldiers=None, province_id=2585, controllable=True,
            army_state="sieging",
        )
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_000,
            objectives=[2585, 2510],
            objective_states=[
                _objective_state(
                    2585,
                    garrison_size=500,
                    besieging_strength=499,
                    active_siege=_active_siege(),
                ),
                _objective_state(
                    2510,
                    garrison_size=300,
                    besieging_strength=0,
                ),
            ],
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            steps=("move-army-11-to-2510", "life-advance"),
        )

        self.assertEqual(plan["selected_step"], "move-army-11-to-2510")
        self.assertEqual(plan["pursuit"]["target_province_id"], 2510)

    def test_rejected_exact_siege_does_not_advance_deferred_preview(
        self,
    ) -> None:
        player = _army(
            11, soldiers=None, province_id=2585, controllable=True,
            army_state="sieging", route_province_ids=[],
        )
        states = [
            _objective_state(
                2585,
                garrison_size=500,
                besieging_strength=499,
                active_siege=_active_siege(),
            ),
            _objective_state(2510, besieging_strength=0),
        ]
        deferred_preview = {
            "index": 1,
            "command": "preview-move-army-11-to-2510",
            "ok": True,
            "result": {
                "accepted": True,
                "route_preview": {
                    "status": "deferred",
                    "army_id": 11,
                    "origin_province_id": 2585,
                    "target_province_id": 2510,
                    "previewed_date_raw": 24_000,
                },
            },
        }
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_000,
            history=[deferred_preview],
            objectives=[2585, 2510],
            objective_states=states,
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            steps=("preview-move-army-11-to-2510", "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_no_safe_exact_route")
        self.assertIsNone(plan["selected_step"])
        self.assertEqual(
            plan["route_rejections"][-1]["status"],
            "deferred_while_exact_siege_rejected",
        )

    def test_rejected_exact_siege_does_not_advance_move_backoff(
        self,
    ) -> None:
        player = _army(
            11, soldiers=None, province_id=2585, controllable=True,
            army_state="sieging",
        )
        deferred_move = {
            "index": 1,
            "command": "move-army-11-to-2510",
            "ok": True,
            "result": {
                "accepted": False,
                "war_action": {
                    "status": "move_deferred",
                    "army_id": 11,
                    "target_province_id": 2510,
                    "submitted_date_raw": 24_000,
                },
            },
        }
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_000,
            history=[deferred_move],
            objectives=[2585, 2510],
            objective_states=[
                _objective_state(
                    2585,
                    garrison_size=500,
                    besieging_strength=499,
                    active_siege=_active_siege(),
                ),
                _objective_state(2510, besieging_strength=0),
            ],
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            steps=("move-army-11-to-2510", "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_siege_exit_blocked")
        self.assertIsNone(plan["selected_step"])
        self.assertFalse(plan["move_backoff"]["retry_due"])

    def test_seven_day_exact_siege_stall_moves_to_next_objective(self) -> None:
        player = _army(
            11, soldiers=None, province_id=2585, controllable=True,
            army_state="sieging",
        )
        active = _objective_state(
            2585,
            active_siege=_active_siege(),
        )
        other = _objective_state(2510, besieging_strength=0)
        before = _war_progress(
            24_000,
            player=player,
            enemies=[],
            score=24,
            objectives=[2585, 2510],
            objective_states=[active, other],
        )
        after = _war_progress(
            24_168,
            player=player,
            enemies=[],
            score=24,
            objectives=[2585, 2510],
            objective_states=[active, other],
        )
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_168,
            history=[_advance_row(1, before, after)],
            objectives=[2585, 2510],
            objective_states=[active, other],
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            steps=("move-army-11-to-2510", "life-advance"),
        )

        self.assertEqual(plan["selected_step"], "move-army-11-to-2510")
        self.assertEqual(plan["pursuit"]["target_province_id"], 2510)

    def test_exact_siege_work_progress_resets_stall(self) -> None:
        player = _army(
            11, soldiers=None, province_id=2585, controllable=True,
            army_state="sieging",
        )
        before_state = _objective_state(
            2585,
            active_siege=_active_siege(),
        )
        after_state = _objective_state(
            2585,
            active_siege=_active_siege(
                progress_raw=32_000,
                current_work_raw=3_200_000,
            ),
        )
        history = [
            _advance_row(
                1,
                _war_progress(
                    24_000,
                    player=player,
                    enemies=[],
                    score=24,
                    objectives=[2585],
                    objective_states=[before_state],
                ),
                _war_progress(
                    24_168,
                    player=player,
                    enemies=[],
                    score=24,
                    objectives=[2585],
                    objective_states=[after_state],
                ),
            )
        ]
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_168,
            history=history,
            objective=2585,
            objective_states=[after_state],
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            steps=("life-advance",),
        )

        self.assertEqual(plan["selected_step"], "life-advance")
        self.assertEqual(plan["siege_state"]["stall_days"], 0)

    def test_exact_siege_stall_requires_uninterrupted_player_control(
        self,
    ) -> None:
        player = _army(
            11, soldiers=None, province_id=2585, controllable=True,
            army_state="sieging",
        )
        player_state = _objective_state(
            2585, active_siege=_active_siege()
        )
        ally_state = _objective_state(
            2585,
            active_siege=_active_siege(army_id=12, player=False),
        )

        def progress(
            date_raw: int,
            states: list[dict[str, object]],
        ) -> dict[str, object]:
            return _war_progress(
                date_raw,
                player=player,
                enemies=[],
                score=24,
                objectives=[2585, 2510],
                objective_states=states,
            )

        history = [
            _advance_row(1, progress(24_000, [player_state]),
                         progress(24_096, [player_state])),
            _advance_row(2, progress(24_096, []), progress(24_120, [])),
            _advance_row(3, progress(24_120, [ally_state]),
                         progress(24_216, [ally_state])),
            _advance_row(4, progress(24_216, [player_state]),
                         progress(24_312, [player_state])),
        ]
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_312,
            history=history,
            objectives=[2585, 2510],
            objective_states=[player_state, _objective_state(2510)],
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            steps=("move-army-11-to-2510", "life-advance"),
        )

        self.assertEqual(plan["selected_step"], "life-advance")
        self.assertEqual(plan["siege_state"]["stall_days"], 4)

    def test_player_occupied_exact_objective_is_skipped(self) -> None:
        player = _army(
            11, soldiers=None, province_id=2585, controllable=True,
            army_state="regular",
        )
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=30,
            date_raw=24_000,
            objectives=[2585, 2510],
            objective_states=[
                _objective_state(2585, occupant=707),
                _objective_state(2510),
            ],
            occupation_supported=True,
            siege_progress_supported=True,
            steps=("move-army-11-to-2510", "life-advance"),
        )

        self.assertEqual(plan["selected_step"], "move-army-11-to-2510")
        self.assertEqual(plan["pursuit"]["target_province_id"], 2510)

    def test_mixed_exact_occupation_overrides_legacy_per_province(
        self,
    ) -> None:
        enemy = _army(21, soldiers=800, province_id=41, controllable=False)
        siege_2585 = _army(
            11, soldiers=900, province_id=2585, controllable=True,
            army_state="sieging",
        )
        siege_2510 = _army(
            11, soldiers=900, province_id=2510, controllable=True,
            army_state="sieging",
        )
        idle_2585 = _army(
            11, soldiers=900, province_id=2585, controllable=True
        )
        idle_2510 = _army(
            11, soldiers=900, province_id=2510, controllable=True
        )
        current = _army(
            11, soldiers=900, province_id=2600, controllable=True,
            army_state="regular",
        )
        history = [
            _advance_row(
                1,
                _war_progress(24_000, player=siege_2585, enemies=[enemy],
                              score=24, objectives=[2585, 2510]),
                _war_progress(24_168, player=idle_2585, enemies=[enemy],
                              score=30, objectives=[2585, 2510]),
            ),
            _advance_row(
                2,
                _war_progress(24_168, player=siege_2510, enemies=[enemy],
                              score=30, objectives=[2585, 2510]),
                _war_progress(24_336, player=idle_2510, enemies=[enemy],
                              score=36, objectives=[2585, 2510]),
            ),
        ]
        unknown = _objective_state(
            2585,
            occupation_observable=False,
            fort_level=None,
            garrison_size=None,
            besieging_strength=None,
            siege_observable=False,
        )
        lost = _objective_state(
            2510,
            fort_level=None,
            garrison_size=None,
            besieging_strength=None,
            siege_observable=False,
        )

        plan = _native_war_plan(
            player=current,
            enemies=[enemy],
            score=36,
            date_raw=24_336,
            history=history,
            objectives=[2585, 2510],
            objective_states=[unknown, lost],
            occupation_supported=True,
            steps=("move-army-11-to-2585", "move-army-11-to-2510"),
        )

        self.assertEqual(plan["selected_step"], "move-army-11-to-2510")
        self.assertEqual(plan["pursuit"]["target_province_id"], 2510)

    def test_all_exact_objectives_occupied_does_not_use_rally_fallback(
        self,
    ) -> None:
        player = _army(
            11, soldiers=None, province_id=2585, controllable=True,
            army_state="regular",
        )
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=30,
            date_raw=24_000,
            objective=2585,
            fallback=2543,
            objective_states=[_objective_state(2585, occupant=707)],
            occupation_supported=True,
            siege_progress_supported=True,
            steps=("move-army-11-to-2543", "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_reconnaissance")
        self.assertEqual(plan["selected_step"], "life-advance")

    def test_completed_exact_objective_ignores_stale_siege_state(self) -> None:
        player = _army(
            11, soldiers=None, province_id=2585, controllable=True,
            army_state="sieging",
        )
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=30,
            date_raw=24_000,
            objective=2585,
            fallback=2543,
            objective_states=[
                _objective_state(2585, occupant=707, active_siege=None)
            ],
            occupation_supported=True,
            siege_progress_supported=True,
            steps=("move-army-11-to-2543", "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_reconnaissance")
        self.assertEqual(plan["selected_step"], "life-advance")

    def test_exact_siege_state_leaves_unrelated_province_for_objective(self) -> None:
        player = _army(
            11, soldiers=900, province_id=2598, controllable=True,
            army_state="sieging",
        )
        retreating_enemy = _army(
            21, soldiers=800, province_id=2598, controllable=False,
            army_state="retreating", army_state_code=6,
        )
        plan = _native_war_plan(
            player=player, enemies=[retreating_enemy], score=41, date_raw=24_000,
            objective=2585, fallback=2543,
            steps=("move-army-11-to-2585", "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_pursuit")
        self.assertEqual(plan["selected_step"], "move-army-11-to-2585")
        self.assertEqual(plan["pursuit"]["target_source"], "war_objective_province")

    def test_exact_siege_retargets_when_enemy_marches_to_objective(self) -> None:
        player = _army(
            11, soldiers=900, province_id=2585, controllable=True,
            army_state="sieging", army_state_code=3,
        )
        approaching_enemy = _army(
            21, soldiers=800, province_id=2572, controllable=False,
            move_target_province_id=2585,
            army_state="moving", army_state_code=7,
        )
        plan = _native_war_plan(
            player=player, enemies=[approaching_enemy], score=41, date_raw=24_000,
            objective=2585, fallback=2543,
            steps=("move-army-11-to-2543", "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_pursuit")
        self.assertEqual(plan["selected_step"], "move-army-11-to-2543")
        self.assertEqual(
            plan["pursuit"]["target_source"],
            "enemy_primary_default_raise_province",
        )

    def test_safe_observed_fallback_route_finishes_before_retargeting(self) -> None:
        moving = _army(
            11, soldiers=900, province_id=2564, controllable=True,
            move_target_province_id=2543,
            army_state="moving", army_state_code=7,
        )
        history = [
            {
                "index": 1,
                "command": "move-army-11-to-2543",
                "ok": True,
                "result": {
                    "accepted": True,
                    "war_action": {
                        "status": "move_submitted",
                        "army_id": 11,
                        "target_province_id": 2543,
                        "submitted_date_raw": 24_000,
                    },
                },
            }
        ]
        plan = _native_war_plan(
            player=moving, enemies=[], score=41, date_raw=24_240,
            history=history, objective=2585, fallback=2543,
            steps=("move-army-11-to-2585", "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_pursuit_progress")
        self.assertEqual(plan["selected_step"], "life-advance")
        self.assertEqual(plan["move_intent"]["target_province_id"], 2543)

    def test_observable_cleared_route_releases_old_move_intent(self) -> None:
        idle = _army(
            11, soldiers=900, province_id=2564, controllable=True,
            move_target_province_id=None,
            move_target_observable=False,
            army_state="regular", army_state_code=1,
        )
        history = [
            {
                "index": 1,
                "command": "move-army-11-to-2543",
                "ok": True,
                "result": {
                    "accepted": True,
                    "war_action": {
                        "status": "move_submitted",
                        "army_id": 11,
                        "target_province_id": 2543,
                        "submitted_date_raw": 24_000,
                    },
                },
            }
        ]
        plan = _native_war_plan(
            player=idle, enemies=[], score=41, date_raw=24_240,
            history=history, objective=2585, fallback=2543,
            steps=("move-army-11-to-2585", "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_pursuit")
        self.assertEqual(plan["selected_step"], "move-army-11-to-2585")

    def test_siege_exit_without_score_gain_does_not_complete_objective(self) -> None:
        sieging = _army(
            11, soldiers=900, province_id=2585, controllable=True,
            army_state="sieging",
        )
        idle = _army(11, soldiers=900, province_id=20, controllable=True)
        before = _war_progress(
            24_000, player=sieging, enemies=[], score=24,
            objectives=[2585], fallback=2543,
        )
        after = _war_progress(
            24_168, player=idle, enemies=[], score=24,
            objectives=[2585], fallback=2543,
        )

        plan = _native_war_plan(
            player=idle, enemies=[], score=24, date_raw=24_168,
            history=[_advance_row(1, before, after)],
            objective=2585, fallback=2543,
            steps=("move-army-11-to-2585", "move-army-11-to-2543"),
        )

        self.assertEqual(plan["selected_step"], "move-army-11-to-2585")

    def test_multiwar_planner_keeps_enemy_objective_and_progress_on_one_war(self) -> None:
        player = _army(11, soldiers=900, province_id=20, controllable=True)
        old_collision = _army(11, soldiers=900, province_id=2585, controllable=True)
        enemy_a = _army(21, soldiers=2_000, province_id=2585, controllable=False)
        enemy_b = _army(22, soldiers=800, province_id=42, controllable=False)
        war_a = _war(
            war_id=10,
            allied_armies=[player],
            enemy_armies=[enemy_a],
            score=15,
            player_side="defender",
        )
        war_b = _war(
            war_id=20,
            allied_armies=[player],
            enemy_armies=[enemy_b],
            score=24,
            war_objective_province_ids=[2585],
        )
        before = {
            "date_raw": 24_000,
            "wars": [
                _war_progress(
                    24_000,
                    player=old_collision,
                    enemies=[enemy_a],
                    score=41,
                    war_id=10,
                )["wars"][0],
                _war_progress(
                    24_000,
                    player=player,
                    enemies=[enemy_b],
                    score=24,
                    war_id=20,
                )["wars"][0],
            ],
        }
        after = {
            "date_raw": 24_432,
            "wars": [
                _war_progress(
                    24_432,
                    player=old_collision,
                    enemies=[enemy_a],
                    score=15,
                    war_id=10,
                )["wars"][0],
                _war_progress(
                    24_432,
                    player=player,
                    enemies=[enemy_b],
                    score=24,
                    war_id=20,
                )["wars"][0],
            ],
        }
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(91),
                "date_raw": 24_432,
                "native_command_history": [_advance_row(1, before, after)],
                "active_wars": [war_a, war_b],
                "player_armies": [player],
            },
            execute=lambda _step, _revision: {},
            action_steps=(
                "move-army-11-to-2585",
                "move-army-11-to-42",
                "life-advance",
            ),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["selected_step"], "move-army-11-to-2585")
        self.assertEqual(plan["pursuit"]["war_id"], 20)
        self.assertIsNone(plan["pursuit"]["target_army_id"])

    def test_restore_discards_pre_restore_collision_and_move_backoff(self) -> None:
        player = _army(11, soldiers=800, province_id=20, controllable=True)
        collision = _army(11, soldiers=900, province_id=77, controllable=True)
        enemy = _army(21, soldiers=800, province_id=77, controllable=False)
        history = [
            _advance_row(
                1,
                _war_progress(24_000, player=collision, enemies=[enemy], score=41),
                _war_progress(24_432, player=collision, enemies=[enemy], score=15),
            ),
            {
                "index": 2,
                "command": "move-army-11-to-77",
                "ok": True,
                "result": {
                    "accepted": False,
                    "war_action": {
                        "status": "move_deferred",
                        "submitted_date_raw": 24_432,
                    },
                },
            },
            {
                "index": 3,
                "command": "restore-checkpoint",
                "ok": True,
                "result": {"status": "restored"},
            },
        ]

        plan = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=15,
            date_raw=24_456,
            history=history,
            objective=77,
            steps=("move-army-11-to-77", "life-advance"),
        )

        self.assertEqual(plan["selected_step"], "move-army-11-to-77")

    def test_same_province_contact_stales_then_escapes_to_safe_objective(self) -> None:
        player = _army(11, soldiers=900, province_id=41, controllable=True)
        enemy = _army(21, soldiers=800, province_id=41, controllable=False)
        before = _war_progress(24_000, player=player, enemies=[enemy], score=24)
        after = _war_progress(24_432, player=player, enemies=[enemy], score=24)

        plan = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=24,
            date_raw=24_432,
            history=[_advance_row(1, before, after)],
            objective=77,
            steps=("life-advance", "move-army-11-to-77"),
        )

        self.assertEqual(plan["selected_step"], "move-army-11-to-77")
        self.assertEqual(plan["pursuit"]["objective_kind"], "siege")

    def test_large_war_score_defeat_blacklists_collision_for_ninety_days(self) -> None:
        player = _army(11, soldiers=900, province_id=41, controllable=True)
        enemy = _army(21, soldiers=800, province_id=41, controllable=False)
        before = _war_progress(24_000, player=player, enemies=[enemy], score=41)
        after = _war_progress(24_432, player=player, enemies=[enemy], score=15)

        plan = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=15,
            date_raw=24_432,
            history=[_advance_row(1, before, after)],
            objective=41,
            steps=("life-advance",),
        )

        self.assertEqual(plan["phase"], "native_war_recovery_wait")
        self.assertEqual(plan["selected_step"], "life-advance")
        self.assertIn(21, plan["tactical_state"]["blocked_enemy_ids"])
        self.assertIn(41, plan["tactical_state"]["blocked_province_ids"])

    def test_ninety_day_move_then_deferred_marks_target_as_retreat_collision(self) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            army_state="retreating",
            army_state_code=6,
        )
        enemy = _army(21, soldiers=800, province_id=41, controllable=False)
        history = [
            {
                "index": 1,
                "command": "move-army-11-to-41",
                "ok": True,
                "result": {
                    "accepted": True,
                    "war_action": {
                        "status": "move_submitted",
                        "army_id": 11,
                        "target_province_id": 41,
                        "submitted_date_raw": 24_000,
                    },
                },
            },
            _advance_row(
                2,
                _war_progress(24_000, player=player, enemies=[enemy], score=0),
                _war_progress(26_184, player=player, enemies=[enemy], score=0),
            ),
            {
                "index": 3,
                "command": "move-army-11-to-41",
                "ok": True,
                "result": {
                    "accepted": False,
                    "war_action": {
                        "status": "move_deferred",
                        "army_id": 11,
                        "target_province_id": 41,
                        "submitted_date_raw": 26_184,
                    },
                },
            },
        ]

        plan = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=0,
            date_raw=26_184,
            history=history,
            steps=("move-army-11-to-41", "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_recovery_wait")
        self.assertEqual(plan["selected_step"], "life-advance")

    def test_forced_retreat_after_deferred_move_submits_safe_objective_once(self) -> None:
        at_collision = _army(11, soldiers=900, province_id=41, controllable=True)
        retreated = _army(11, soldiers=850, province_id=42, controllable=True)
        enemy = _army(21, soldiers=800, province_id=41, controllable=False)
        history: list[dict[str, object]] = [
            {
                "index": 1,
                "command": "move-army-11-to-41",
                "ok": True,
                "result": {
                    "accepted": False,
                    "war_action": {
                        "status": "move_deferred",
                        "army_id": 11,
                        "target_province_id": 41,
                        "submitted_date_raw": 24_000,
                    },
                },
            },
            _advance_row(
                2,
                _war_progress(24_000, player=at_collision, enemies=[enemy], score=24),
                _war_progress(24_168, player=retreated, enemies=[enemy], score=24),
            ),
        ]
        plan = _native_war_plan(
            player=retreated,
            enemies=[enemy],
            score=24,
            date_raw=24_168,
            history=history,
            objective=77,
            steps=("move-army-11-to-77", "life-advance"),
        )
        self.assertEqual(plan["selected_step"], "move-army-11-to-77")

        history.append(
            {
                "index": 3,
                "command": "move-army-11-to-77",
                "ok": True,
                "result": {
                    "accepted": True,
                    "war_action": {
                        "status": "move_submitted",
                        "army_id": 11,
                        "target_province_id": 77,
                        "submitted_date_raw": 24_168,
                    },
                },
            }
        )
        accepted = _native_war_plan(
            player=retreated,
            enemies=[enemy],
            score=24,
            date_raw=24_192,
            history=history,
            objective=77,
            steps=("move-army-11-to-77", "life-advance"),
        )
        self.assertEqual(accepted["selected_step"], "life-advance")
        self.assertEqual(accepted["move_intent"]["target_province_id"], 77)

    def test_deferred_move_retries_use_seven_fourteen_thirty_day_backoff(self) -> None:
        player = _army(11, soldiers=900, province_id=20, controllable=True)
        history: list[dict[str, object]] = []
        dates = (24_000, 24_168, 24_504)
        for index, submitted in enumerate(dates, start=1):
            history.append(
                {
                    "index": index,
                    "command": "move-army-11-to-77",
                    "ok": True,
                    "result": {
                        "accepted": False,
                        "war_action": {
                            "status": "move_deferred",
                            "army_id": 11,
                            "target_province_id": 77,
                            "submitted_date_raw": submitted,
                        },
                    },
                }
            )
            required = (7, 14, 30)[index - 1]
            waiting = _native_war_plan(
                player=player,
                enemies=[],
                score=24,
                date_raw=submitted + (required - 1) * 24,
                history=history,
                objective=77,
                steps=("move-army-11-to-77", "life-advance"),
            )
            self.assertEqual(waiting["selected_step"], "life-advance")
            self.assertEqual(waiting["move_backoff"]["required_days"], required)
            due = _native_war_plan(
                player=player,
                enemies=[],
                score=24,
                date_raw=submitted + required * 24,
                history=history,
                objective=77,
                steps=("move-army-11-to-77", "life-advance"),
            )
            self.assertEqual(due["selected_step"], "move-army-11-to-77")

    def test_occupied_blacklisted_objective_has_no_safe_target(self) -> None:
        collision = _army(11, soldiers=900, province_id=77, controllable=True)
        retreated = _army(11, soldiers=800, province_id=42, controllable=True)
        enemy = _army(21, soldiers=800, province_id=77, controllable=False)
        history = [
            _advance_row(
                1,
                _war_progress(24_000, player=collision, enemies=[enemy], score=41),
                _war_progress(24_432, player=retreated, enemies=[enemy], score=15),
            )
        ]

        plan = _native_war_plan(
            player=retreated,
            enemies=[enemy],
            score=15,
            date_raw=24_432,
            history=history,
            objective=77,
            steps=("move-army-11-to-77", "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_recovery_wait")
        self.assertEqual(plan["selected_step"], "life-advance")

    def test_score_gain_and_enemy_disappearance_clear_stale_contact(self) -> None:
        player = _army(11, soldiers=900, province_id=41, controllable=True)
        enemy = _army(21, soldiers=800, province_id=41, controllable=False)
        first = _advance_row(
            1,
            _war_progress(24_000, player=player, enemies=[enemy], score=24),
            _war_progress(24_168, player=player, enemies=[enemy], score=24),
        )
        improved = _advance_row(
            2,
            _war_progress(24_168, player=player, enemies=[enemy], score=24),
            _war_progress(24_336, player=player, enemies=[enemy], score=25),
        )
        plan = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=25,
            date_raw=24_336,
            history=[first, improved],
            objective=77,
            steps=("life-advance", "move-army-11-to-77"),
        )
        self.assertEqual(plan["selected_step"], "life-advance")

        stale = _advance_row(
            2,
            _war_progress(24_168, player=player, enemies=[enemy], score=24),
            _war_progress(24_504, player=player, enemies=[enemy], score=24),
        )
        disappeared = _advance_row(
            3,
            _war_progress(24_504, player=player, enemies=[enemy], score=24),
            _war_progress(24_528, player=player, enemies=[], score=24),
        )
        cleared = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_528,
            history=[first, stale, disappeared],
            objective=77,
            steps=("life-advance", "move-army-11-to-77"),
        )
        self.assertEqual(cleared["selected_step"], "move-army-11-to-77")

    def test_exact_army_states_override_heuristics_but_combat_has_deadline(self) -> None:
        combat = _army(
            11,
            soldiers=900,
            province_id=41,
            controllable=True,
            army_state="combat",
            army_state_code=2,
        )
        enemy = _army(21, soldiers=800, province_id=41, controllable=False)
        first = _native_war_plan(
            player=combat,
            enemies=[enemy],
            score=15,
            date_raw=24_000,
            objective=41,
            steps=("life-advance",),
        )
        self.assertEqual(first["selected_step"], "life-advance")

        bounded = _native_war_plan(
            player=combat,
            enemies=[enemy],
            score=15,
            date_raw=24_360,
            history=[
                _advance_row(
                    1,
                    _war_progress(24_000, player=combat, enemies=[enemy], score=15),
                    _war_progress(24_360, player=combat, enemies=[enemy], score=15),
                )
            ],
            objective=77,
            steps=("life-advance", "move-army-11-to-77"),
        )
        self.assertEqual(bounded["phase"], "native_war_combat_progress")
        self.assertEqual(bounded["selected_step"], "life-advance")

        unsupported = _native_war_plan(
            player=combat,
            enemies=[enemy],
            score=15,
            date_raw=24_360,
            history=[
                _advance_row(
                    1,
                    _war_progress(24_000, player=combat, enemies=[enemy], score=15),
                    _war_progress(24_360, player=combat, enemies=[enemy], score=15),
                )
            ],
            objective=77,
            steps=("move-army-11-to-77",),
        )
        self.assertEqual(
            unsupported["phase"], "native_war_combat_progress_unsupported"
        )
        self.assertIsNone(unsupported["selected_step"])
        self.assertEqual(unsupported["required_step"], "life-advance")

        retreating = {**combat, "army_state": "retreating", "army_state_code": 6}
        retreat = _native_war_plan(
            player=retreating,
            enemies=[enemy],
            score=15,
            date_raw=24_000,
            objective=77,
            steps=("life-advance",),
        )
        self.assertEqual(retreat["phase"], "native_war_retreat_progress")

        sieging = {**combat, "army_state": "sieging", "army_state_code": 3}
        siege = _native_war_plan(
            player=sieging,
            enemies=[],
            score=15,
            date_raw=24_000,
            objective=41,
            steps=("life-advance",),
        )
        self.assertEqual(siege["phase"], "native_war_siege_progress")

    def test_defender_keeps_chasing_visible_enemy(self) -> None:
        player = _army(11, soldiers=900, province_id=20, controllable=True)
        enemy = _army(21, soldiers=1_100, province_id=41, controllable=False)
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(11),
                "active_wars": [
                    _war(
                        allied_armies=[player],
                        enemy_armies=[enemy],
                        score=24,
                        player_side="defender",
                        enemy_primary_default_raise_province_id=77,
                    )
                ],
                "player_armies": [player],
            },
            execute=lambda _step, _revision: {},
            action_steps=(
                "move-army-11-to-41",
                "move-army-11-to-77",
            ),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["selected_step"], "move-army-11-to-41")
        self.assertEqual(plan["pursuit"]["objective_kind"], "pursuit")
        self.assertEqual(plan["pursuit"]["target_army_id"], 21)

    def test_native_war_planner_uses_primary_opponent_fallback(self) -> None:
        player = _army(11, soldiers=900, province_id=20, controllable=True)
        step = "move-army-11-to-77"
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(9),
                "active_wars": [
                    _war(
                        allied_armies=[player],
                        enemy_armies=[],
                        enemy_primary_default_raise_province_id=77,
                    )
                ],
                "player_armies": [player],
            },
            execute=lambda _step, _revision: {},
            action_steps=(step,),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "native_war_pursuit")
        self.assertEqual(plan["selected_step"], step)
        self.assertEqual(
            plan["pursuit"]["target_source"],
            "enemy_primary_default_raise_province",
        )
        self.assertIsNone(plan["pursuit"]["target_army_id"])

    def test_non_primary_war_participant_does_not_enforce_at_100(self) -> None:
        player = _army(11, soldiers=900, province_id=20, controllable=True)
        enemy = _army(21, soldiers=1_100, province_id=41, controllable=False)
        move_step = "move-army-11-to-41"
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(9),
                "active_wars": [
                    _war(
                        allied_armies=[player],
                        enemy_armies=[enemy],
                        score=100,
                        player_is_primary_war_leader=False,
                    )
                ],
                "player_armies": [player],
            },
            execute=lambda _step, _revision: {},
            action_steps=(
                "enforce-demands-88",
                move_step,
                "life-advance",
            ),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "native_war_pursuit")
        self.assertEqual(plan["selected_step"], move_step)

    def test_native_war_planner_advances_after_unobservable_move_ack(self) -> None:
        player = _army(11, soldiers=900, province_id=20, controllable=True)
        enemy = _army(21, soldiers=1_100, province_id=41, controllable=False)
        history = [
            {
                "index": 1,
                "command": "move-army-11-to-41",
                "ok": True,
                "result": {
                    "accepted": True,
                    "war_action": {
                        "status": "move_submitted",
                        "army_id": 11,
                        "target_province_id": 41,
                        "submitted_date_raw": 24_000,
                    },
                },
            },
            {
                "index": 2,
                "command": "life-advance",
                "ok": True,
                "result": {"elapsed_days": 5},
            },
            {
                "index": 3,
                "command": "life-advance",
                "ok": True,
                "result": {"elapsed_days": 5},
            },
        ]
        state = {
            **_snapshot(9),
            "date_raw": 24_240,
            "native_command_history": history,
            "active_wars": [
                _war(allied_armies=[player], enemy_armies=[enemy])
            ],
            "player_armies": [player],
        }
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: dict(state),
            execute=lambda _step, _revision: {},
            action_steps=("move-army-11-to-41", "life-advance"),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "native_war_pursuit_progress")
        self.assertEqual(plan["selected_step"], "life-advance")
        self.assertEqual(plan["move_intent"]["elapsed_days"], 10)

        state["date_raw"] = 26_160
        expired = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(expired["phase"], "native_war_pursuit")
        self.assertEqual(expired["selected_step"], "move-army-11-to-41")

    def test_native_move_intent_ends_when_enemy_target_changes(self) -> None:
        player = _army(11, soldiers=900, province_id=20, controllable=True)
        enemy = _army(21, soldiers=1_100, province_id=42, controllable=False)
        history = [
            {
                "index": 1,
                "command": "move-army-11-to-41",
                "ok": True,
                "result": {
                    "accepted": True,
                    "war_action": {
                        "status": "move_submitted",
                        "army_id": 11,
                        "target_province_id": 41,
                        "submitted_date_raw": 24_000,
                    },
                },
            }
        ]
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(10),
                "date_raw": 24_024,
                "native_command_history": history,
                "active_wars": [
                    _war(allied_armies=[player], enemy_armies=[enemy])
                ],
                "player_armies": [player],
            },
            execute=lambda _step, _revision: {},
            action_steps=("move-army-11-to-42", "life-advance"),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "native_war_pursuit")
        self.assertEqual(plan["selected_step"], "move-army-11-to-42")

    def test_native_move_intent_does_not_cross_checkpoint_restore(self) -> None:
        player = _army(11, soldiers=900, province_id=20, controllable=True)
        enemy = _army(21, soldiers=1_100, province_id=41, controllable=False)
        history = [
            {
                "index": 1,
                "command": "move-army-11-to-41",
                "ok": True,
                "result": {
                    "accepted": True,
                    "war_action": {
                        "status": "move_submitted",
                        "army_id": 11,
                        "target_province_id": 41,
                        "submitted_date_raw": 24_000,
                    },
                },
            },
            {
                "index": 2,
                "command": "restore-checkpoint",
                "ok": True,
                "result": {"status": "restored"},
            },
        ]
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(11),
                "date_raw": 23_976,
                "native_command_history": history,
                "active_wars": [
                    _war(allied_armies=[player], enemy_armies=[enemy])
                ],
                "player_armies": [player],
            },
            execute=lambda _step, _revision: {},
            action_steps=("move-army-11-to-41", "life-advance"),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "native_war_pursuit")
        self.assertEqual(plan["selected_step"], "move-army-11-to-41")

    def test_native_war_planner_retries_date_less_legacy_deferred_move(self) -> None:
        player = _army(11, soldiers=900, province_id=20, controllable=True)
        enemy = _army(21, soldiers=1_100, province_id=41, controllable=False)
        history = [
            {
                "index": 1,
                "command": "move-army-11-to-41",
                "ok": True,
                "result": {
                    "war_action": {"status": "move_deferred"}
                },
            }
        ]
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(9, history),
                "active_wars": [
                    _war(allied_armies=[player], enemy_armies=[enemy])
                ],
                "player_armies": [player],
            },
            execute=lambda _step, _revision: {},
            action_steps=("move-army-11-to-41", "life-advance"),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "native_war_pursuit")
        self.assertEqual(plan["selected_step"], "move-army-11-to-41")

    def test_native_war_planner_disbands_residual_postwar_army(self) -> None:
        player = _army(
            71, soldiers=1_100, province_id=50, controllable=True
        )
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(10),
                "active_wars": [],
                "player_armies": [player],
            },
            execute=lambda _step, _revision: {},
            action_steps=("disband-army-71",),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "native_postwar_disband")
        self.assertEqual(plan["selected_step"], "disband-army-71")

    def test_typed_war_service_routes_exact_native_commands(self) -> None:
        player = _army(
            81, soldiers=1_300, province_id=50, controllable=True
        )
        enemy = _army(
            91, soldiers=1_900, province_id=60, controllable=False
        )
        calls: list[tuple[str, int | None]] = []
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(14),
                "active_wars": [
                    _war(allied_armies=[player], enemy_armies=[enemy])
                ],
                "player_armies": [player],
            },
            execute=lambda step, revision: calls.append((step, revision))
            or {"status": "submitted"},
            action_steps=(
                "raise-troops-default",
                "move-army-81-to-60",
                "disband-army-81",
                "enforce-demands-88",
            ),
        )
        service = GameplayBridgeService(driver)

        state = service.war_state()
        self.assertEqual(state["status"], "active")
        self.assertEqual(state["active_wars"][0]["war_id"], 88)
        service.raise_troops_default(expected_revision=14)
        service.move_army(81, 60, expected_revision=14)
        service.disband_army(81, expected_revision=14)
        service.enforce_demands(88, expected_revision=14)

        self.assertEqual(
            calls,
            [
                ("raise-troops-default", 14),
                ("move-army-81-to-60", 14),
                ("disband-army-81", 14),
                ("enforce-demands-88", 14),
            ],
        )

    def test_service_auto_turn_plans_and_executes_one_supported_step(self) -> None:
        calls: list[tuple[str, int | None]] = []
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: _snapshot(11),
            execute=lambda step, revision: calls.append((step, revision))
            or {"step": step},
            action_steps=("save-checkpoint",),
        )

        result = GameplayBridgeService(driver).auto_turn()

        self.assertEqual(result["status"], "executed")
        self.assertEqual(result["selected_step"], "save-checkpoint")
        self.assertEqual(calls, [("save-checkpoint", 11)])

    def test_service_auto_turn_ends_native_one_life_on_player_death(self) -> None:
        calls: list[tuple[str, int | None]] = []
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(12),
                "played_character": {"character_id": 707, "alive": False},
            },
            execute=lambda step, revision: calls.append((step, revision))
            or {"terminal": True, "continue_as_heir_after_death": False},
            action_steps=("death-terminal",),
        )

        result = GameplayBridgeService(driver).auto_turn()

        self.assertEqual(result["selected_step"], "death-terminal")
        self.assertTrue(result["result"]["terminal"])
        self.assertEqual(calls, [("death-terminal", 12)])

    def test_service_exposes_and_finalizes_matching_one_life_settlement(
        self,
    ) -> None:
        settlement = {
            "ready": True,
            "commit_serial": 1,
            "source_character_id": 707,
            "final_score": 405.25,
            "score_before_reject": 410,
            "record_candidate": 405,
            "old_record": 405,
            "record_delta": 0,
            "blessing_count": 3,
            "refusal_count": 1,
            "contract_progress": 7,
            "record_written": False,
        }
        snapshot = {
            **_snapshot(12),
            "played_character": {"character_id": 808, "alive": True},
            "episode_character_id": 707,
            "one_life_terminal": True,
            "one_life_terminal_reason": "played_character_changed",
            "one_life_settlement": settlement,
        }
        driver = mock.Mock()
        driver.take_snapshot.return_value = snapshot
        driver.capabilities.return_value = {
            "action_steps": ["death-terminal"],
            "bridge_capabilities": [ONE_LIFE_SETTLEMENT_CAPABILITY],
        }
        driver.execute_step.return_value = {
            "terminal": True,
            "settlement_status": "complete",
            "continue_as_heir_after_death": False,
            "heir_gameplay_actions": 0,
            "score": 405.25,
        }
        service = GameplayBridgeService(driver)

        projected = service.one_life_settlement()
        finalized = service.settle_one_life(expected_revision=12)

        self.assertEqual(projected["status"], "ready")
        self.assertEqual(projected["episode_character_id"], 707)
        self.assertEqual(finalized["score"], 405.25)
        self.assertFalse(finalized["continue_as_heir_after_death"])
        self.assertEqual(finalized["heir_gameplay_actions"], 0)
        driver.execute_step.assert_called_once_with(
            "death-terminal", expected_revision=12
        )

    def test_cross_run_achievements_accept_native_war_prefixes_only(self) -> None:
        commands = [
            {
                "command": "enforce-demands-88",
                "ok": True,
                "result": {
                    "war_victory": {
                        "status": "victory_enforced",
                        "war_id": 88,
                    }
                },
            },
            {
                "command": "disband-army-81",
                "ok": True,
                "result": {
                    "war_action": {"status": "disbanded", "army_id": 81}
                },
            },
            {
                "command": "arrange-marriage-707-809",
                "ok": True,
                "result": {
                    "marriage_action": {
                        "status": "proposal_submitted",
                        "candidate_character_id": 809,
                    }
                },
            },
        ]
        terminal = {
            "terminal": True,
            "terminal_reason": "played_character_dead",
            "continue_as_heir_after_death": False,
            "heir_gameplay_actions": 0,
            "score": 405.25,
        }
        with tempfile.TemporaryDirectory() as temporary:
            recorded = record_one_life_episode(
                Path(temporary),
                run_id="native-707-settlement",
                commands=commands,
                terminal=terminal,
            )

        achievements = recorded["recorded_episode"]["achievements"]
        self.assertTrue(achievements["palermo_holy_war_won"])
        self.assertTrue(achievements["armies_disbanded"])
        self.assertFalse(achievements["danish_betrothal_accepted"])

    def test_cross_run_marriage_requires_native_relationship_confirmation(self) -> None:
        commands = [
            {
                "command": "arrange-marriage-707-809",
                "ok": True,
                "result": {
                    "marriage_action": {
                        "status": "proposal_submitted",
                        "played_character_id": 707,
                        "candidate_character_id": 809,
                    },
                    "marriage_result": {
                        "status": "accepted_betrothal",
                        "played_character_id": 707,
                        "candidate_character_id": 809,
                        "source": "native_relationship_snapshot",
                    },
                },
            }
        ]
        terminal = {
            "terminal": True,
            "terminal_reason": "played_character_dead",
            "continue_as_heir_after_death": False,
            "heir_gameplay_actions": 0,
            "score": 405.25,
        }
        with tempfile.TemporaryDirectory() as temporary:
            recorded = record_one_life_episode(
                Path(temporary),
                run_id="native-707-married",
                commands=commands,
                terminal=terminal,
            )

        self.assertTrue(
            recorded["recorded_episode"]["achievements"][
                "danish_betrothal_accepted"
            ]
        )

    def test_bridge_driver_adapts_to_backend_neutral_runner(self) -> None:
        calls: list[tuple[str, int | None]] = []
        driver = CallbackGameplayDriver(
            backend_id="mcp",
            snapshot=lambda: _snapshot(12),
            execute=lambda step, revision: calls.append((step, revision))
            or {"step": step},
            action_steps=("life-advance",),
        )
        executor = BridgeGameplayStepExecutor(driver, expected_revision=lambda: 12)
        self.assertEqual(executor.execute_step("life-advance")["backend_id"], "mcp")
        self.assertEqual(calls, [("life-advance", 12)])

    def test_development_report_driver_reads_without_starting_ck3(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state = Path(temporary)
            run = state / "runs" / "20260823T000000Z-dev-session-fixture"
            run.mkdir(parents=True)
            (run / "report.json").write_text(
                json.dumps(
                    {
                        "run_id": run.name,
                        "process": {"pid": 123},
                        "finalized": False,
                        "commands": [
                            {
                                "command": "life-advance",
                                "ok": True,
                                "result": {"final_screen": "map_hud"},
                            },
                            {
                                "command": "auto-run 2",
                                "ok": True,
                                "result": {
                                    "final_screen": "unchanged",
                                    "turns": [
                                        {
                                            "command": "auto-turn",
                                            "ok": True,
                                            "result": {"final_screen": "map_running"},
                                        },
                                        {
                                            "command": "auto-turn",
                                            "ok": False,
                                            "error": "fixture stop",
                                        },
                                    ],
                                },
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            driver = DevelopmentReportDriver(state)

            snapshot = driver.take_snapshot()
            self.assertEqual(snapshot["revision"], 2)
            self.assertEqual(snapshot["phase"], "map_running")
            self.assertEqual(snapshot["backend_id"], "vision-report")
            with self.assertRaises(UnsupportedStepError):
                driver.execute_step("life-advance")

    def test_native_mcp_driver_receives_isolated_profile_save_dir(self) -> None:
        from xar_autoplayer.bridge.mcp_server import load_driver

        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            with mock.patch(
                "xar_autoplayer.bridge.mcp_server.NativeHeadlessGameplayDriver"
            ) as factory:
                driver = load_driver(
                    "native-headless",
                    state_dir=state_dir,
                    pipe_name=r"\\.\pipe\xar_save_fixture",
                )

        self.assertIs(driver, factory.return_value)
        factory.assert_called_once_with(
            r"\\.\pipe\xar_save_fixture",
            state_dir=state_dir,
            save_dir=state_dir / "profile" / "save games",
        )

@unittest.skipIf(importlib.util.find_spec("mcp") is None, "optional MCP SDK not installed")
class GameplayMcpServerTests(unittest.IsolatedAsyncioTestCase):
    async def test_mcp_settle_one_life_returns_final_score(self) -> None:
        from mcp import Client
        from xar_autoplayer.bridge.mcp_server import create_server

        driver = CallbackGameplayDriver(
            backend_id="terminal-fixture",
            snapshot=lambda: {
                **_snapshot(14),
                "played_character": {"character_id": 707, "alive": False},
                "one_life_terminal": True,
                "one_life_terminal_reason": "played_character_dead",
            },
            execute=lambda step, revision: {
                "step": step,
                "terminal": True,
                "settlement_status": "complete",
                "continue_as_heir_after_death": False,
                "heir_gameplay_actions": 0,
                "score": 405.25,
                "expected_revision": revision,
            },
            action_steps=("death-terminal",),
        )
        server = create_server(driver)

        async with Client(server) as client:
            settled = await client.call_tool(
                "ck3_settle_one_life", {"expected_revision": 14}
            )

        self.assertFalse(settled.is_error)
        self.assertEqual(settled.structured_content["score"], 405.25)
        self.assertFalse(
            settled.structured_content["continue_as_heir_after_death"]
        )
        self.assertEqual(settled.structured_content["heir_gameplay_actions"], 0)

    async def test_official_mcp_client_lists_and_calls_ck3_tools(self) -> None:
        from mcp import Client
        from xar_autoplayer.bridge.mcp_server import create_server

        driver = CallbackGameplayDriver(
            backend_id="native-fixture",
            snapshot=lambda: {
                **_snapshot(4),
                "active_event": {"instance_id": 44, "option_count": 2},
                "pending_character_interaction": {
                    "instance_id": 52,
                    "sender_character_id": 901,
                    "auto_accept_notification": False,
                },
                "active_wars": [
                    _war(
                        allied_armies=[
                            _army(
                                81,
                                soldiers=1_300,
                                province_id=50,
                                controllable=True,
                            )
                        ],
                        enemy_armies=[
                            _army(
                                91,
                                soldiers=1_900,
                                province_id=60,
                                controllable=False,
                            )
                        ],
                    )
                ],
                "player_armies": [
                    _army(
                        81,
                        soldiers=1_300,
                        province_id=50,
                        controllable=True,
                    )
                ],
                "declarable_wars": [
                    {
                        "declaration_id": "808-17-0",
                        "target_character_id": 808,
                        "casus_belli_index": 17,
                        "casus_belli_key": "county_conquest_cb",
                        "configuration_index": 0,
                        "claimant_character_id": -1,
                        "target_title_ids": [91],
                    }
                ],
                "arrange_marriage_choices": [
                    {
                        "choice_id": "707-809",
                        "played_character_id": 707,
                        "candidate_character_id": 809,
                    }
                ],
            },
            execute=lambda step, revision: {
                "step": step,
                "expected_revision": revision,
                **(
                    {
                        "arrange_marriage_choices": [
                            {
                                "choice_id": "707-809",
                                "played_character_id": 707,
                                "candidate_character_id": 809,
                            }
                        ],
                        "query_sequence": 2,
                    }
                    if step == "query-arrange-marriage-choices"
                    else (
                    {
                        "declarable_wars": [
                            {
                                "declaration_id": "808-17-0",
                                "target_character_id": 808,
                                "casus_belli_index": 17,
                                "casus_belli_key": "county_conquest_cb",
                                "configuration_index": 0,
                                "claimant_character_id": -1,
                                "target_title_ids": [91],
                            }
                        ],
                        "query_sequence": 1,
                    }
                    if step == "query-declarable-wars"
                    else (
                    {
                        "checkpoint": {
                            "status": "saved",
                            "name": "xar_checkpoint.ck3",
                            "path": "C:/fixture/xar_checkpoint.ck3",
                            "size": 123,
                            "sha256": "a" * 64,
                            "date_raw": 53_171_424,
                        }
                    }
                    if step == "save-checkpoint"
                    else (
                        {
                            "checkpoint": {
                                "status": "restored",
                                "name": "xar_checkpoint.ck3",
                                "path": "C:/fixture/xar_checkpoint.ck3",
                                "size": 123,
                                "sha256": "a" * 64,
                                "date_raw": 53_171_424,
                            },
                            "restored_date": {"date_raw": 53_171_424},
                        }
                        if step == "restore-checkpoint"
                        else {}
                    )
                    )
                    )
                ),
            },
            action_steps=(
                "life-advance",
                "save-checkpoint",
                "restore-checkpoint",
                "accept-pending-character-interaction",
                "reject-pending-character-interaction",
                "raise-troops-default",
                "move-army-81-to-60",
                "merge-armies-81-with-82",
                "start-assault-901",
                "stop-assault-901",
                "disband-army-81",
                "enforce-demands-88",
                "query-declarable-wars",
                "declare-war-808-17-0",
                "query-arrange-marriage-choices",
                "arrange-marriage-707-809",
                "select-event-option-1",
                "select-event-option-2",
            ),
            source="named-pipe",
            latency="realtime",
        )
        server = create_server(driver)
        async with Client(server) as client:
            listed = await client.list_tools()
            self.assertEqual(
                {tool.name for tool in listed.tools},
                {
                    "ck3_get_capabilities",
                    "ck3_get_bridge_diagnostics",
                    "ck3_take_snapshot",
                    "ck3_get_one_life_settlement",
                    "ck3_settle_one_life",
                    "ck3_plan_turn",
                    "ck3_auto_turn",
                    "ck3_execute_step",
                    "ck3_save_checkpoint",
                    "ck3_restore_checkpoint",
                    "ck3_start_next_episode",
                    "ck3_reply_pending_character_interaction",
                    "ck3_get_war_state",
                    "ck3_query_arrange_marriage_choices",
                    "ck3_arrange_marriage",
                    "ck3_query_declarable_wars",
                    "ck3_declare_war",
                    "ck3_raise_troops_default",
                    "ck3_move_army",
                    "ck3_start_assault",
                    "ck3_stop_assault",
                    "ck3_disband_army",
                    "ck3_enforce_demands",
                    "ck3_select_event_option",
                    "ck3_resolve_active_event",
                    "ck3_wait_for_change",
                },
            )
            snapshot = await client.call_tool("ck3_take_snapshot", {})
            self.assertFalse(snapshot.is_error)
            self.assertEqual(snapshot.structured_content["revision"], 4)
            settlement = await client.call_tool(
                "ck3_get_one_life_settlement", {}
            )
            self.assertFalse(settlement.is_error)
            self.assertEqual(
                settlement.structured_content["status"], "not_terminal"
            )
            action = await client.call_tool(
                "ck3_execute_step",
                {"step": "life-advance", "expected_revision": 4},
            )
            self.assertFalse(action.is_error)
            self.assertEqual(action.structured_content["backend_id"], "native-fixture")
            self.assertEqual(action.structured_content["expected_revision"], 4)
            merged = await client.call_tool(
                "ck3_execute_step",
                {
                    "step": "merge-armies-81-with-82",
                    "expected_revision": 4,
                },
            )
            self.assertFalse(merged.is_error)
            self.assertEqual(
                merged.structured_content["step"],
                "merge-armies-81-with-82",
            )
            automatic = await client.call_tool("ck3_auto_turn", {})
            self.assertFalse(automatic.is_error)
            self.assertEqual(
                automatic.structured_content["selected_step"],
                "select-event-option-1",
            )
            checkpoint = await client.call_tool(
                "ck3_save_checkpoint",
                {"expected_revision": 4},
            )
            self.assertFalse(checkpoint.is_error)
            self.assertEqual(
                checkpoint.structured_content["checkpoint"]["name"],
                "xar_checkpoint.ck3",
            )
            self.assertEqual(
                checkpoint.structured_content["checkpoint"]["date_raw"],
                53_171_424,
            )
            restored = await client.call_tool(
                "ck3_restore_checkpoint",
                {"expected_revision": 4},
            )
            self.assertFalse(restored.is_error)
            self.assertEqual(
                restored.structured_content["checkpoint"]["status"],
                "restored",
            )
            self.assertEqual(
                restored.structured_content["restored_date"]["date_raw"],
                53_171_424,
            )
            interaction = await client.call_tool(
                "ck3_reply_pending_character_interaction",
                {
                    "accept": True,
                    "interaction_instance_id": 52,
                    "expected_revision": 4,
                },
            )
            self.assertFalse(interaction.is_error)
            self.assertTrue(interaction.structured_content["accepted"])
            self.assertEqual(
                interaction.structured_content["sender_character_id"], 901
            )
            war_state = await client.call_tool("ck3_get_war_state", {})
            self.assertFalse(war_state.is_error)
            self.assertEqual(war_state.structured_content["status"], "active")
            marriage_choices = await client.call_tool(
                "ck3_query_arrange_marriage_choices",
                {"expected_revision": 4},
            )
            self.assertFalse(marriage_choices.is_error)
            self.assertEqual(
                marriage_choices.structured_content[
                    "arrange_marriage_choices"
                ][0]["candidate_character_id"],
                809,
            )
            marriage = await client.call_tool(
                "ck3_arrange_marriage",
                {"choice_id": "707-809", "expected_revision": 4},
            )
            self.assertFalse(marriage.is_error)
            declarations = await client.call_tool(
                "ck3_query_declarable_wars", {"expected_revision": 4}
            )
            self.assertFalse(declarations.is_error)
            self.assertEqual(
                declarations.structured_content["declarable_wars"][0][
                    "casus_belli_key"
                ],
                "county_conquest_cb",
            )
            declared = await client.call_tool(
                "ck3_declare_war",
                {"declaration_id": "808-17-0", "expected_revision": 4},
            )
            self.assertFalse(declared.is_error)
            raised = await client.call_tool(
                "ck3_raise_troops_default", {"expected_revision": 4}
            )
            self.assertFalse(raised.is_error)
            moved = await client.call_tool(
                "ck3_move_army",
                {
                    "army_id": 81,
                    "target_province_id": 60,
                    "expected_revision": 4,
                },
            )
            self.assertFalse(moved.is_error)
            self.assertEqual(moved.structured_content["army_id"], 81)
            started_assault = await client.call_tool(
                "ck3_start_assault",
                {"siege_id": 901, "expected_revision": 4},
            )
            self.assertFalse(started_assault.is_error)
            self.assertEqual(started_assault.structured_content["siege_id"], 901)
            stopped_assault = await client.call_tool(
                "ck3_stop_assault",
                {"siege_id": 901, "expected_revision": 4},
            )
            self.assertFalse(stopped_assault.is_error)
            self.assertEqual(stopped_assault.structured_content["siege_id"], 901)
            disbanded = await client.call_tool(
                "ck3_disband_army",
                {"army_id": 81, "expected_revision": 4},
            )
            self.assertFalse(disbanded.is_error)
            enforced = await client.call_tool(
                "ck3_enforce_demands",
                {"war_id": 88, "expected_revision": 4},
            )
            self.assertFalse(enforced.is_error)
            self.assertEqual(enforced.structured_content["war_id"], 88)
            event_action = await client.call_tool(
                "ck3_select_event_option",
                {
                    "option_number": 2,
                    "event_instance_id": 44,
                    "expected_revision": 4,
                },
            )
            self.assertFalse(event_action.is_error)
            self.assertEqual(event_action.structured_content["option_number"], 2)
            self.assertEqual(event_action.structured_content["option_index"], 1)


if __name__ == "__main__":
    unittest.main()
