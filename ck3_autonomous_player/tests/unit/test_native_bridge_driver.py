from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock
import uuid


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.driver import (
    BridgeUnavailableError,
    CallbackGameplayDriver,
    UnsupportedStepError,
)
from xar_autoplayer.bridge.native_driver import (
    ConfiguredHybridFallbackDriver,
    MinimizedRejectingVisualDriver,
    NativeHeadlessGameplayDriver,
    _fresh_route_contact_advance_steps,
    _is_deferred_read_only_history_step,
    _life_advance_horizon_days,
    _native_unobservable_started_assaults,
    _unavoidable_contact_transition_postcondition,
)
from xar_autoplayer.bridge.settlement_contract import (
    ONE_LIFE_SETTLEMENT_CAPABILITY,
)
from xar_autoplayer.bridge.war_contract import (
    advance_route_contact_horizon_step,
    is_native_war_step,
    merge_armies_step,
    parse_merge_armies_step,
    parse_start_assault_step,
    parse_stop_assault_step,
    parse_split_army_half_step,
    query_route_contact_horizon_step,
    split_army_half_step,
    start_assault_step,
    stop_assault_step,
)
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.environment import write_bytes_atomic, write_json_atomic


_SIGNED_PENDING_ID = -2_130_706_341
_SIGNED_NOTIFICATION_ID = -2_130_706_340
_SIGNED_SERVICE_NOTIFICATION_ID = -2_130_706_339


class FakeEndpoint:
    def __init__(self, pipe_name: str = r"\\.\pipe\xar_fixture") -> None:
        self.pipe_name = pipe_name
        self.frames: list[dict[str, object]] = []
        self.on_frame = None
        self.on_disconnect = None
        self.send_hook = None
        self.closed = False
        self.error: str | None = None

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
        self.closed = True

    def transport_error(self) -> str | None:
        return self.error


def _hello(*capabilities: str) -> dict[str, object]:
    return {
        "type": "hello",
        "protocol_version": 1,
        "bridge_version": "0.1.0",
        "pid": 4242,
        "session_generation": 0,
        "capabilities": list(capabilities),
    }


def _snapshot(
    revision: int = 1,
    *,
    active_event: dict[str, object] | None = None,
    date_raw: int = 53_171_400,
    speed: int = 1,
    paused: bool = True,
    map_ready: bool = True,
    pending_character_interaction: dict[str, object] | None = None,
    played_character: dict[str, object] | None = None,
    one_life_settlement: dict[str, object] | None = None,
    active_wars: list[dict[str, object]] | None = None,
    player_armies: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "type": "state_snapshot",
        "protocol_version": 1,
        "snapshot_id": f"native:{revision}",
        "revision": revision,
        "state": {
            "phase": "map_hud",
            "date": "1066.9.15",
            "date_raw": date_raw,
            "speed": speed,
            "paused": paused,
            "map_ready": map_ready,
            "history": [],
            "active_event": active_event,
            "pending_character_interaction": pending_character_interaction,
            "played_character": played_character,
            "one_life_settlement": one_life_settlement,
            "active_wars": active_wars,
            "player_armies": player_armies,
        },
    }


def _one_life_settlement(**overrides: object) -> dict[str, object]:
    result: dict[str, object] = {
        "ready": True,
        "commit_serial": 1,
        "source_character_id": 707,
        "final_score": {"raw": 40_525_000, "scale": 100_000},
        "score_before_reject": {"raw": 41_000_000, "scale": 100_000},
        "record_candidate": 405,
        "old_record": 405,
        "record_delta": 0,
        "blessing_count": 3,
        "refusal_count": 1,
        "contract_progress": 7,
        "record_written": False,
    }
    result.update(overrides)
    return result


def _write_driver_state_checkpoint_fixture(
    state_dir: Path,
    pipe_name: str,
    *,
    bridge_pid: int = 1111,
    character_id: int = 707,
    run_id: str = "native-707-existing",
    date_raw: int = 53_168_784,
    format_version: int = 2,
    include_v2_anchor: bool = True,
) -> tuple[Path, dict[str, object]]:
    save_dir = state_dir / "profile" / "save games"
    save_dir.mkdir(parents=True)
    checkpoint_path = save_dir / "xar_checkpoint.ck3"
    payload = b"cold-checkpoint-fixture"
    checkpoint_path.write_bytes(payload)
    checkpoint: dict[str, object] = {
        "status": "saved",
        "path": str(checkpoint_path.resolve()),
        "name": checkpoint_path.name,
        "size": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "date_raw": date_raw,
        "strategy": "native-autosave-command-v1",
    }
    if include_v2_anchor:
        checkpoint.update(
            {
                "history_index": 8,
                "episode_character_id": character_id,
                "episode_run_id": run_id,
            }
        )
    history: list[dict[str, object]] = [
        {
            "index": index,
            "command": "life-advance",
            "ok": True,
            "result": {"step": "life-advance", "ending_date_raw": date_raw},
        }
        for index in range(1, 8)
    ]
    history.append(
        {
            "index": 8,
            "command": "save-checkpoint",
            "ok": True,
            "result": {
                "step": "save-checkpoint",
                "checkpoint": dict(checkpoint),
            },
        }
    )
    history.extend(
        [
            {
                "index": 9,
                "command": "life-advance",
                "ok": True,
                "result": {"step": "life-advance"},
            },
            {
                "index": 10,
                "command": "life-advance",
                "ok": True,
                "result": {"step": "life-advance"},
            },
            {
                "index": 11,
                "command": "move-army-1-to-2",
                "ok": True,
                "result": {"step": "move-army-1-to-2"},
            },
        ]
    )
    write_json_atomic(
        state_dir / "native-session" / "driver-state.json",
        {
            "format_version": format_version,
            "pipe_name": pipe_name,
            "bridge_pid": bridge_pid,
            "episode_character_id": character_id,
            "episode_run_id": run_id,
            "last_checkpoint": checkpoint,
            "command_history": history,
        },
    )
    return checkpoint_path, checkpoint


def _rollback_failure(
    checkpoint: dict[str, object],
    *,
    target: int,
    route: list[int],
    run_id: str,
    war_id: int = 61,
    army_id: int = 1,
    origin: int = 2598,
) -> dict[str, object]:
    return {
        "status": "rolled_back_active_route",
        "source": "checkpoint_discarded_branch",
        "episode_run_id": run_id,
        "checkpoint_sha256": checkpoint["sha256"],
        "checkpoint_date_raw": checkpoint["date_raw"],
        "war_id": war_id,
        "army_id": army_id,
        "restored_origin_province_id": origin,
        "target_province_id": target,
        "route_origin_province_id": origin,
        "route_province_ids": list(route),
        "previewed_date_raw": checkpoint["date_raw"],
        "terminal_failure_target_province_id": target,
        "terminal_failure_route_origin_province_id": origin,
        "terminal_failure_route_province_ids": list(route),
        "restored_date_raw": checkpoint["date_raw"],
    }


def _army(
    army_id: int,
    *,
    soldiers: int | None = 1_000,
    province_id: int | None = 10,
    move_target_province_id: int | None = None,
    observe_move_target: bool = True,
    controllable: bool = True,
    **state: object,
) -> dict[str, object]:
    result = {
        "army_id": army_id,
        "owner_character_id": 707 if controllable else 808,
        "soldiers": soldiers,
        "current_province_id": province_id,
        "move_target_province_id": move_target_province_id,
        "controllable": controllable,
        **state,
    }
    if not observe_move_target:
        result.pop("move_target_province_id")
    return result


def _active_siege(
    *,
    siege_id: int = 901,
    army_id: int | None = 101,
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
    fort_level: int | None = 2,
    garrison_size: int | None = 500,
    besieging_strength: int | None = 650,
    siege_observable: bool = True,
    active_siege: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "province_id": province_id,
        "occupation_observable": True,
        "is_occupied": occupant is not None,
        "occupying_character_id": occupant,
        "fort_level": fort_level,
        "garrison_size": garrison_size,
        "besieging_strength": besieging_strength,
        "siege_observable": siege_observable,
        "active_siege": active_siege if siege_observable else None,
    }


def _war(
    war_id: int = 61,
    *,
    allied_armies: list[dict[str, object]] | None = None,
    enemy_armies: list[dict[str, object]] | None = None,
    score: int = 12,
    player_is_primary_war_leader: bool = True,
    enemy_primary_default_raise_province_id: int | None = None,
    war_objective_province_ids: list[int] | None = None,
    objective_province_states: list[dict[str, object]] | None = None,
    targeted_title_ids: list[int] | None = None,
) -> dict[str, object]:
    return {
        "war_id": war_id,
        "player_side": "attacker",
        "primary_opponent_character_id": 808,
        "player_is_primary_war_leader": player_is_primary_war_leader,
        "enemy_primary_default_raise_province_id": (
            enemy_primary_default_raise_province_id
        ),
        "player_relative_war_score": score,
        "allied_armies": allied_armies or [],
        "enemy_armies": enemy_armies or [],
        "war_objective_province_ids": war_objective_province_ids or [],
        "objective_province_states": objective_province_states or [],
        "targeted_title_ids": targeted_title_ids or [],
    }


def _termination_options(
    war_id: int,
    *,
    score: int = 41,
    surrender_available: bool = True,
    white_peace_available: bool = True,
    white_peace_acceptance_raw: int = -2_900_000,
    casus_belli_database_index: int = 17,
    casus_belli_key: str = "county_conquest_cb",
    war_duration_days: int = 203,
    white_peace_decision_status_raw: int = 0,
) -> dict[str, object]:
    def option(
        outcome: str,
        available: bool,
        *,
        acceptance_raw: int = -2_900_000,
        decision_status_raw: int = 0,
    ) -> dict[str, object]:
        return {
            "outcome": outcome,
            "hostage_variant": "none",
            "context_constructed": True,
            "native_validator_passed": True if available else False,
            "available": available,
            "terms_observable": False,
            "terms": {
                "status": "unavailable",
                "reason": "cb_specific_terms_not_observable",
            },
            "ai_acceptance_observable": True,
            "ai_acceptance": {"raw": acceptance_raw, "scale": 100_000},
            "auto_accept_observable": True,
            "auto_accept": outcome == "attacker_defeat",
            "recipient_response": (
                {
                    "status": "available",
                    "decision_status_raw": decision_status_raw,
                    "would_accept_now": decision_status_raw != 2,
                }
                if available
                else {
                    "status": "unavailable",
                    "decision_status_raw": None,
                    "would_accept_now": None,
                }
            ),
        }

    return {
        "war_id": war_id,
        "player_side": "attacker",
        "player_is_primary_war_leader": True,
        "player_relative_war_score": score,
        "war_duration_days": war_duration_days,
        "active_casus_belli_present": True,
        "active_casus_belli_identity": {
            "database_index": casus_belli_database_index,
            "canonical_key": casus_belli_key,
        },
        "cb_allows_white_peace": True,
        "absolute_war_scores_observable": True,
        "attacker_war_score": score,
        "defender_war_score": -score,
        "war_score_breakdown": {
            "imprisonment": 0,
            "battles": -4,
            "occupation": 45,
            "ticking": 0,
        },
        "options": {
            "surrender": option("attacker_defeat", surrender_available),
            "white_peace": option(
                "white_peace",
                white_peace_available,
                acceptance_raw=white_peace_acceptance_raw,
                decision_status_raw=white_peace_decision_status_raw,
            ),
            "victory": option("attacker_victory", True),
        },
    }


def _termination_terms(
    war_id: int,
    *,
    status: str = "available",
    claimant_character_id: int = 29_829,
    target_title_ids: list[int] | None = None,
    strong: bool = True,
) -> dict[str, object]:
    common: dict[str, object] = {
        "schema_version": 1,
        "status": status,
        "war_id": war_id,
        "casus_belli": {
            "database_index": 0 if status == "available" else 4,
            "canonical_key": (
                "claim_cb" if status == "available" else "county_conquest_cb"
            ),
        },
        "supported_slice": "claim_cb_claim_disposition",
        "provenance": {
            "game_version": "1.19.0.6",
            "executable_sha256": (
                "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
            ),
            "native_reader": "CWar+0x270/+0x290;0x28B1AA0",
            "present_claim_lifecycle": (
                "present_only_vtable_slot_0_delete_flags_0"
            ),
            "claim_script_sha256": (
                "D9AA37BDC45F81B4F6185B2697A3EBD09404084EA0D3CF77BBE3C1D2C962E8B1"
            ),
        },
    }
    if status == "unsupported":
        return {
            **common,
            "reason": "casus_belli_not_claim_cb",
            "readiness": {"ready": False},
        }
    targets = target_title_ids or [2_388]
    return {
        **common,
        "claimant_character_id": claimant_character_id,
        "target_title_ids": targets,
        "claims": [
            {
                "title_id": title_id,
                "present": True,
                "strong": strong,
                "implicit": False,
                "state": (
                    "strong_explicit" if strong else "weak_explicit"
                ),
            }
            for title_id in targets
        ],
        "outcomes": {
            "attacker_victory": {
                "declared_title_disposition": (
                    "transfer_to_claimant_via_conquest_claim"
                ),
                "claim_disposition": "resolve_with_add_claim_on_loss",
            },
            "white_peace": {
                "declared_title_disposition": "unchanged",
                "claim_disposition": "retain_and_strengthen_weak",
            },
            "attacker_defeat": {
                "declared_title_disposition": "unchanged",
                "claim_disposition": "remove_declared_target_claims",
            },
        },
        "readiness": {
            "identity_ready": True,
            "targets_ready": True,
            "claim_rows_ready": True,
            "claim_disposition_ready": True,
            "ready": True,
        },
    }


def _termination_exit_terms_v2() -> dict[str, object]:
    fixture = (
        ROOT
        / "tests"
        / "fixtures"
        / "war_termination_exit_terms_v2_synthetic.json"
    )
    return json.loads(fixture.read_text(encoding="utf-8"))


def _army_strength(
    army_id: int,
    role: str,
    war_ids: list[int],
    *,
    status: str = "available",
    current: int = 1_200,
    maximum: int = 1_500,
    regiment_count: int = 3,
    base_power_raw: int = 180_000_000,
) -> dict[str, object]:
    available = status == "available"
    return {
        "status": status,
        "army_id": army_id,
        "native_carmy_id": army_id + 1_000,
        "scope_role": role,
        "war_ids": war_ids,
        "regiment_count": regiment_count if available else None,
        "current_soldiers": current if available else None,
        "maximum_soldiers": maximum if available else None,
        "ai_base_power_raw": base_power_raw if available else None,
        "ai_base_power_scale": 100_000,
        "unavailable_reason": (
            None if available else "regiment_generation_mismatch"
        ),
    }


class NativeHeadlessGameplayDriverTests(unittest.TestCase):
    def _run_life_advance_speed_fixture(
        self,
        *,
        active_wars: list[dict[str, object]],
        player_armies: list[dict[str, object]],
        extra_capabilities: tuple[str, ...] = (),
        policy_capabilities: tuple[str, ...] = (
            "game.state.army-routes",
            "game.state.war-objective-assault",
        ),
        expected_speed: int,
        horizon_days: int,
        actual_elapsed_days: int | None = None,
    ) -> tuple[dict[str, object], list[str]]:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            life_advance_timeout_seconds=0.1,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                *policy_capabilities,
                "game.command.pause-map",
                "game.command.resume-map",
                "game.command.set-speed-1",
                "game.command.set-speed-3",
                "game.command.set-speed-5",
                *extra_capabilities,
            )
        )
        start_date = 53_175_216
        elapsed_days = (
            horizon_days
            if actual_elapsed_days is None
            else actual_elapsed_days
        )

        def publish(
            revision: int, *, date_raw: int, speed: int, paused: bool
        ) -> None:
            endpoint.publish(
                _snapshot(
                    revision,
                    date_raw=date_raw,
                    speed=speed,
                    paused=paused,
                    active_wars=active_wars,
                    player_armies=player_armies,
                )
            )

        publish(1, date_raw=start_date, speed=3, paused=True)

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            step = str(frame["step"])
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {"step": step, "accepted": True},
                }
            )
            if step == f"set-speed-{expected_speed}":
                publish(
                    2,
                    date_raw=start_date,
                    speed=expected_speed,
                    paused=True,
                )
            elif step == "resume-map":
                publish(
                    3,
                    date_raw=start_date,
                    speed=expected_speed,
                    paused=False,
                )
                publish(
                    4,
                    date_raw=start_date + elapsed_days * 24,
                    speed=expected_speed,
                    paused=False,
                )
            elif step == "pause-map":
                publish(
                    5,
                    date_raw=start_date + elapsed_days * 24,
                    speed=expected_speed,
                    paused=True,
                )

        endpoint.send_hook = answer
        result = driver.execute_step("life-advance")
        steps = [
            str(frame["step"])
            for frame in endpoint.frames
            if frame.get("type") == "execute_step"
        ]
        return result, steps

    def test_current_dll_only_exposes_connection_diagnostics(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )

        disconnected = driver.capabilities()
        self.assertEqual(disconnected["mode"], "native-headless")
        self.assertTrue(disconnected["headless"])
        self.assertTrue(disconnected["minimized_operation"])
        self.assertFalse(disconnected["visual_fallback"])
        self.assertFalse(disconnected["fallback_enabled"])
        self.assertFalse(disconnected["snapshot"])
        self.assertEqual(disconnected["action_steps"], [])

    def test_rejected_state_snapshot_records_delivery_diagnostics_and_recovers(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(_hello("game.state.snapshot"))
        endpoint.publish(_snapshot(1, date_raw=53_211_480, paused=False))
        endpoint.publish(
            {
                "type": "snapshot_publish_diagnostic",
                "protocol_version": 1,
                "request_id": "pause-fixture",
                "phase": "begin",
                "status": "begin",
                "revision": 1,
                "payload_bytes": 0,
            }
        )
        malformed = _snapshot(2, date_raw=53_211_504, paused=True)
        malformed["state"]["active_wars"] = {}  # type: ignore[index]
        endpoint.publish(malformed)
        endpoint.publish(
            {
                "type": "snapshot_publish_diagnostic",
                "protocol_version": 1,
                "request_id": "pause-fixture",
                "phase": "end",
                "status": "written",
                "revision": 2,
                "payload_bytes": 42_000,
            }
        )

        stale = driver.take_internal_semantic_snapshot()
        diagnostics = stale["diagnostics"]
        self.assertEqual(stale["native_revision"], 1)
        self.assertEqual(diagnostics["rejected_state_snapshot_count"], 1)
        self.assertEqual(
            diagnostics["last_rejected_state_snapshot"],
            {
                "snapshot_id": "native:2",
                "revision": 2,
                "date_raw": 53_211_504,
                "speed": 1,
                "paused": True,
                "map_ready": True,
                "error_type": "ValueError",
                "error": "native active_wars must be an array",
            },
        )
        self.assertEqual(diagnostics["snapshot_publish_diagnostic_count"], 2)
        self.assertEqual(
            diagnostics["last_snapshot_publish_diagnostic"]["status"],
            "written",
        )

        endpoint.publish(_snapshot(3, date_raw=53_211_504, paused=True))
        recovered = driver.take_internal_semantic_snapshot()
        self.assertEqual(recovered["native_revision"], 3)
        self.assertTrue(recovered["paused"])
        self.assertEqual(
            recovered["diagnostics"]["rejected_state_snapshot_count"], 1
        )

    def test_split_army_half_step_parser_is_exact(self) -> None:
        self.assertEqual(split_army_half_step(1), "split-army-half-1")
        self.assertEqual(
            split_army_half_step(2**31 - 1),
            "split-army-half-2147483647",
        )
        self.assertEqual(parse_split_army_half_step("split-army-half-1"), 1)
        self.assertTrue(is_native_war_step("split-army-half-1"))

        malformed_steps: tuple[object, ...] = (
            None,
            True,
            "",
            "split-army-half-",
            "split-army-half-0",
            "split-army-half--1",
            "split-army-half-+1",
            "split-army-half-1 ",
            "split-army-half-1-extra",
            "split-army-half-2147483648",
            "split-army-half-１",
        )
        for malformed in malformed_steps:
            with self.subTest(step=malformed):
                self.assertIsNone(parse_split_army_half_step(malformed))
                self.assertFalse(is_native_war_step(malformed))
        for malformed_id in (0, -1, 2**31, True):
            with self.subTest(army_id=malformed_id):
                with self.assertRaises(ValueError):
                    split_army_half_step(malformed_id)

    def test_partial_hello_does_not_advertise_split_army_literals(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.command.disband-army-N",
                "game.command.split-army-half-X",
            )
        )
        endpoint.publish(
            _snapshot(2, player_armies=[_army(101), _army(202)])
        )

        capabilities = driver.capabilities()
        self.assertNotIn(
            "game.command.split-army-half-N",
            capabilities["bridge_capabilities"],
        )
        self.assertFalse(
            any(
                step.startswith("split-army-half-")
                for step in capabilities["action_steps"]
            )
        )

    def test_merge_armies_step_parser_is_exact(self) -> None:
        self.assertEqual(
            merge_armies_step(1, 2), "merge-armies-1-with-2"
        )
        self.assertEqual(
            merge_armies_step(2**31 - 1, 1),
            "merge-armies-2147483647-with-1",
        )
        self.assertEqual(
            parse_merge_armies_step("merge-armies-1-with-2"), (1, 2)
        )
        self.assertTrue(is_native_war_step("merge-armies-1-with-2"))

        malformed_steps: tuple[object, ...] = (
            None,
            True,
            "",
            "merge-armies-",
            "merge-armies-1",
            "merge-armies-0-with-2",
            "merge-armies-1-with-0",
            "merge-armies--1-with-2",
            "merge-armies-+1-with-2",
            "merge-armies-1-with--2",
            "merge-armies-1-with-+2",
            "merge-armies-1 -with-2",
            "merge-armies-1-with-2 ",
            "merge-armies-1-with-2-extra",
            "merge-armies-1-with-2-with-3",
            "merge-armies-2147483648-with-2",
            "merge-armies-1-with-2147483648",
            "merge-armies-1-with-1",
            "merge-armies-１-with-2",
            "merge-armies-1-with-２",
        )
        for malformed in malformed_steps:
            with self.subTest(step=malformed):
                self.assertIsNone(parse_merge_armies_step(malformed))
                self.assertFalse(is_native_war_step(malformed))
        for destination, source in (
            (0, 1),
            (-1, 1),
            (2**31, 1),
            (True, 1),
            (1, 0),
            (1, -1),
            (1, 2**31),
            (1, True),
            (7, 7),
        ):
            with self.subTest(destination=destination, source=source):
                with self.assertRaises(ValueError):
                    merge_armies_step(destination, source)

    def test_partial_hello_does_not_advertise_merge_army_literals(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.command.merge-armies-N-with-X",
                "game.command.merge-armies-101-with-202",
            )
        )
        endpoint.publish(
            _snapshot(
                2,
                player_armies=[
                    _army(101, province_id=11),
                    _army(202, province_id=11),
                ],
            )
        )

        capabilities = driver.capabilities()
        self.assertNotIn(
            "game.command.merge-armies-N-with-N",
            capabilities["bridge_capabilities"],
        )
        self.assertFalse(
            any(
                step.startswith("merge-armies-")
                for step in capabilities["action_steps"]
            )
        )

    def test_assault_step_parsers_are_exact(self) -> None:
        self.assertEqual(start_assault_step(1), "start-assault-1")
        self.assertEqual(
            stop_assault_step(2**31 - 1),
            "stop-assault-2147483647",
        )
        self.assertEqual(parse_start_assault_step("start-assault-901"), 901)
        self.assertEqual(parse_stop_assault_step("stop-assault-901"), 901)
        self.assertTrue(is_native_war_step("start-assault-901"))
        self.assertTrue(is_native_war_step("stop-assault-901"))

        malformed_steps: tuple[object, ...] = (
            None,
            True,
            "",
            "start-assault-",
            "start-assault-0",
            "start-assault--1",
            "start-assault-+1",
            "start-assault-1 ",
            "start-assault-1-extra",
            "start-assault-2147483648",
            "start-assault-１",
            "stop-assault-",
            "stop-assault-0",
            "stop-assault--1",
            "stop-assault-+1",
            "stop-assault-1 ",
            "stop-assault-1-extra",
            "stop-assault-2147483648",
            "stop-assault-１",
        )
        for malformed in malformed_steps:
            with self.subTest(step=malformed):
                self.assertIsNone(parse_start_assault_step(malformed))
                self.assertIsNone(parse_stop_assault_step(malformed))
                self.assertFalse(is_native_war_step(malformed))
        for malformed_id in (0, -1, 2**31, True):
            with self.subTest(siege_id=malformed_id):
                with self.assertRaises(ValueError):
                    start_assault_step(malformed_id)
                with self.assertRaises(ValueError):
                    stop_assault_step(malformed_id)

    def test_assault_literals_require_exact_state_and_command_capabilities(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.war-objective-assault",
                "game.command.start-assault-X",
                "game.command.stop-assault-901",
            )
        )
        siege = _active_siege(
            assault_observable=True,
            breach_level=1,
            assault_in_progress=False,
            can_start_assault=True,
            can_stop_assault=False,
            assault_daily_progress_raw=340_000,
            assault_daily_casualties=16,
        )
        endpoint.publish(
            _snapshot(
                2,
                active_wars=[
                    _war(
                        war_objective_province_ids=[2585],
                        objective_province_states=[
                            _objective_state(2585, active_siege=siege)
                        ],
                    )
                ],
            )
        )

        capabilities = driver.capabilities()
        self.assertTrue(capabilities["war_objective_assault_supported"])
        self.assertFalse(
            any(
                step.startswith(("start-assault-", "stop-assault-"))
                for step in capabilities["action_steps"]
            )
        )

    def test_assault_start_requires_complete_stop_recovery_bundle(self) -> None:
        cases = (
            {
                "name": "start_without_stop",
                "commands": ("game.command.start-assault-N",),
                "active": False,
                "expected": (),
            },
            {
                "name": "stop_recovery_only",
                "commands": ("game.command.stop-assault-N",),
                "active": True,
                "expected": ("stop-assault-901",),
            },
            {
                "name": "complete_bundle",
                "commands": (
                    "game.command.start-assault-N",
                    "game.command.stop-assault-N",
                ),
                "active": False,
                "expected": ("start-assault-901",),
            },
        )
        for case in cases:
            with self.subTest(case=case["name"]):
                endpoint = FakeEndpoint()
                driver = NativeHeadlessGameplayDriver(
                    endpoint.pipe_name,
                    endpoint=endpoint,
                )
                endpoint.publish(
                    _hello(
                        "game.state.snapshot",
                        "game.state.war-objective-assault",
                        *case["commands"],
                    )
                )
                active = bool(case["active"])
                endpoint.publish(
                    _snapshot(
                        2,
                        active_wars=[
                            _war(
                                war_objective_province_ids=[2585],
                                objective_province_states=[
                                    _objective_state(
                                        2585,
                                        active_siege=_active_siege(
                                            assault_observable=True,
                                            breach_level=1,
                                            assault_in_progress=active,
                                            can_start_assault=not active,
                                            can_stop_assault=active,
                                            assault_daily_progress_raw=340_000,
                                            assault_daily_casualties=16,
                                        ),
                                    )
                                ],
                            )
                        ],
                    )
                )

                assault_steps = tuple(
                    step
                    for step in driver.capabilities()["action_steps"]
                    if step.startswith(("start-assault-", "stop-assault-"))
                )
                self.assertEqual(assault_steps, case["expected"])

    def test_start_and_stop_assault_wait_for_same_paused_siege_flag(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.war-objective-assault",
                "game.command.start-assault-N",
                "game.command.stop-assault-N",
            )
        )

        def frame(revision: int, active: bool) -> dict[str, object]:
            siege = _active_siege(
                assault_observable=True,
                breach_level=1,
                assault_in_progress=active,
                can_start_assault=not active,
                can_stop_assault=active,
                assault_daily_progress_raw=340_000,
                assault_daily_casualties=16,
            )
            return _snapshot(
                revision,
                paused=True,
                active_wars=[
                    _war(
                        war_id=61,
                        war_objective_province_ids=[2585],
                        objective_province_states=[
                            _objective_state(2585, active_siege=siege)
                        ],
                    )
                ],
            )

        endpoint.publish(frame(2, False))
        self.assertIn("start-assault-901", driver.capabilities()["action_steps"])

        def answer_start(request: dict[str, object]) -> None:
            if request.get("type") != "execute_step":
                return
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": request["request_id"],
                    "ok": True,
                    "result": {
                        "step": request["step"],
                        "accepted": True,
                        "status": "start_submitted",
                    },
                }
            )
            endpoint.publish(frame(3, True))

        endpoint.send_hook = answer_start
        started = driver.execute_step("start-assault-901")
        self.assertEqual(started["assault_action"]["status"], "assault_started")
        self.assertTrue(started["active_siege"]["assault_in_progress"])
        self.assertEqual(started["assault_action"]["province_id"], 2585)
        self.assertIn("stop-assault-901", driver.capabilities()["action_steps"])

        def answer_stop(request: dict[str, object]) -> None:
            if request.get("type") != "execute_step":
                return
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": request["request_id"],
                    "ok": True,
                    "result": {
                        "step": request["step"],
                        "accepted": True,
                        "status": "stop_submitted",
                    },
                }
            )
            endpoint.publish(frame(4, False))

        endpoint.send_hook = answer_stop
        stopped = driver.execute_step("stop-assault-901")
        self.assertEqual(stopped["assault_action"]["status"], "assault_stopped")
        self.assertFalse(stopped["active_siege"]["assault_in_progress"])

    def test_assault_ack_without_flag_postcondition_is_not_applied(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=0.01,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.war-objective-assault",
                "game.command.start-assault-N",
                "game.command.stop-assault-N",
            )
        )
        endpoint.publish(
            _snapshot(
                2,
                active_wars=[
                    _war(
                        war_objective_province_ids=[2585],
                        objective_province_states=[
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
                    )
                ],
            )
        )

        def ack_only(request: dict[str, object]) -> None:
            if request.get("type") == "execute_step":
                endpoint.publish(
                    {
                        "type": "command_result",
                        "protocol_version": 1,
                        "request_id": request["request_id"],
                        "ok": True,
                        "result": {
                            "step": request["step"],
                            "accepted": True,
                            "status": "start_submitted",
                        },
                    }
                )

        endpoint.send_hook = ack_only
        with self.assertRaisesRegex(
            BridgeUnavailableError, "same-SiegeID paused postcondition"
        ):
            driver.execute_step("start-assault-901")

    def test_direct_life_advance_blocks_open_unobservable_assault_before_resume(
        self,
    ) -> None:
        start_history = {
            "index": 1,
            "command": "start-assault-901",
            "ok": True,
            "result": {
                "assault_action": {
                    "status": "assault_started",
                    "siege_id": 901,
                    "war_id": 61,
                    "province_id": 2585,
                }
            },
        }
        for paused in (True, False):
            with self.subTest(paused=paused):
                endpoint = FakeEndpoint()
                driver = NativeHeadlessGameplayDriver(
                    endpoint.pipe_name,
                    endpoint=endpoint,
                )
                endpoint.publish(
                    _hello(
                        "game.state.snapshot",
                        "game.state.war-objective-assault",
                        "game.command.pause-map",
                        "game.command.resume-map",
                        "game.command.set-speed-1",
                        "game.command.set-speed-3",
                        "game.command.set-speed-5",
                    )
                )
                endpoint.publish(
                    _snapshot(
                        2,
                        paused=paused,
                        active_wars=[
                            _war(
                                war_id=61,
                                war_objective_province_ids=[2585],
                                objective_province_states=[],
                            )
                        ],
                    )
                )
                driver._command_history = [dict(start_history)]

                with self.assertRaisesRegex(
                    BridgeUnavailableError,
                    "assault_started|paused rich snapshot",
                ):
                    driver.execute_step("life-advance")

                self.assertFalse(
                    any(
                        frame.get("type") == "execute_step"
                        for frame in endpoint.frames
                    )
                )

    def test_direct_life_advance_blocks_latest_failed_active_assault_slice(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.war-objective-assault",
                "game.command.pause-map",
                "game.command.resume-map",
                "game.command.set-speed-1",
                "game.command.set-speed-3",
                "game.command.set-speed-5",
            )
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
        endpoint.publish(
            _snapshot(
                2,
                active_wars=[
                    _war(
                        war_id=61,
                        war_objective_province_ids=[2585],
                        objective_province_states=[
                            _objective_state(
                                2585, active_siege=active_siege
                            )
                        ],
                    )
                ],
            )
        )
        driver._command_history = [
            {
                "index": 1,
                "command": "start-assault-901",
                "ok": True,
                "result": {
                    "assault_action": {
                        "status": "assault_started",
                        "siege_id": 901,
                        "war_id": 61,
                        "province_id": 2585,
                    }
                },
            },
            {
                "index": 2,
                "command": "life-advance",
                "ok": False,
                "error": "fixture partial composite failure",
            },
        ]

        with self.assertRaisesRegex(
            BridgeUnavailableError, "unresolved assault_started"
        ):
            driver.execute_step("life-advance")
        self.assertFalse(
            any(
                frame.get("type") == "execute_step"
                for frame in endpoint.frames
            )
        )

    def test_failed_assault_slice_does_not_block_exact_no_siege_completion(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            life_advance_timeout_seconds=0.1,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.war-objective-assault",
                "game.command.pause-map",
                "game.command.resume-map",
                "game.command.set-speed-1",
                "game.command.set-speed-3",
                "game.command.set-speed-5",
            )
        )
        player = _army(101, province_id=2585, army_state="regular")

        def frame(
            revision: int, *, paused: bool, speed: int, score: int
        ) -> dict[str, object]:
            return _snapshot(
                revision,
                paused=paused,
                speed=speed,
                active_wars=[
                    _war(
                        war_id=61,
                        allied_armies=[player],
                        score=score,
                        war_objective_province_ids=[2585],
                        objective_province_states=[
                            _objective_state(2585, active_siege=None)
                        ],
                    )
                ],
                player_armies=[player],
            )

        endpoint.publish(frame(1, paused=True, speed=1, score=12))
        driver._command_history = [
            {
                "index": 1,
                "command": "start-assault-901",
                "ok": True,
                "result": {
                    "assault_action": {
                        "status": "assault_started",
                        "siege_id": 901,
                        "war_id": 61,
                        "province_id": 2585,
                    }
                },
            },
            {
                "index": 2,
                "command": "life-advance",
                "ok": False,
                "error": "fixture partial composite failure",
            },
        ]
        self.assertEqual(
            _native_unobservable_started_assaults(
                driver.take_snapshot(), driver._history_snapshot()
            ),
            [],
        )

        def answer(request: dict[str, object]) -> None:
            if request.get("type") != "execute_step":
                return
            step = str(request["step"])
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": request["request_id"],
                    "ok": True,
                    "result": {"step": step, "accepted": True},
                }
            )
            if step == "set-speed-5":
                endpoint.publish(frame(2, paused=True, speed=5, score=12))
            elif step == "resume-map":
                endpoint.publish(frame(3, paused=False, speed=5, score=13))
            elif step == "pause-map":
                endpoint.publish(frame(4, paused=True, speed=5, score=13))

        endpoint.send_hook = answer
        driver.execute_step("life-advance")
        wire_steps = [
            frame["step"]
            for frame in endpoint.frames
            if frame.get("type") == "execute_step"
        ]
        self.assertEqual(
            wire_steps, ["set-speed-5", "resume-map", "pause-map"]
        )

    def test_active_assault_life_advance_horizon_is_one_day(self) -> None:
        siege = _active_siege(
            assault_observable=True,
            breach_level=1,
            assault_in_progress=True,
            can_start_assault=False,
            can_stop_assault=True,
            assault_daily_progress_raw=340_000,
            assault_daily_casualties=16,
        )
        snapshot = {
            "paused": True,
            "war_objective_siege_progress_supported": True,
            "war_objective_assault_supported": True,
            "active_wars": [
                _war(
                    war_objective_province_ids=[2585],
                    objective_province_states=[
                        _objective_state(2585, active_siege=siege)
                    ],
                )
            ],
        }

        self.assertEqual(_life_advance_horizon_days(snapshot), 1)
        siege["assault_in_progress"] = False
        self.assertEqual(_life_advance_horizon_days(snapshot), 7)

    def test_active_route_one_day_slice_uses_speed_one(self) -> None:
        player = _army(
            101,
            province_id=2598,
            move_target_province_id=2596,
            route_province_ids=[2596],
            army_state="moving",
        )
        result, steps = self._run_life_advance_speed_fixture(
            active_wars=[_war(allied_armies=[player])],
            player_armies=[player],
            expected_speed=1,
            horizon_days=1,
        )

        self.assertEqual(
            steps, ["set-speed-1", "resume-map", "pause-map"]
        )
        self.assertEqual(result["elapsed_days"], 1)
        self.assertEqual(result["requested_horizon_days"], 1)
        self.assertEqual(result["timeline_speed"], 1)
        self.assertEqual(result["timeline_policy"], "player_tactical")

    def test_active_assault_one_day_slice_uses_speed_one(self) -> None:
        player = _army(
            101,
            province_id=2585,
            army_state="sieging",
            route_province_ids=[],
        )
        siege = _active_siege(
            assault_observable=True,
            breach_level=1,
            assault_in_progress=True,
            can_start_assault=False,
            can_stop_assault=True,
            assault_daily_progress_raw=340_000,
            assault_daily_casualties=16,
        )
        result, steps = self._run_life_advance_speed_fixture(
            active_wars=[
                _war(
                    allied_armies=[player],
                    war_objective_province_ids=[2585],
                    objective_province_states=[
                        _objective_state(2585, active_siege=siege)
                    ],
                )
            ],
            player_armies=[player],
            extra_capabilities=("game.state.war-objective-assault",),
            expected_speed=1,
            horizon_days=1,
        )

        self.assertEqual(
            steps, ["set-speed-1", "resume-map", "pause-map"]
        )
        self.assertEqual(result["elapsed_days"], 1)
        self.assertEqual(result["timeline_policy"], "player_assault")

    def test_ordinary_siege_seven_day_slice_keeps_speed_five(self) -> None:
        player = _army(101, province_id=2585, army_state="sieging")
        siege = _active_siege(
            assault_observable=False,
        )
        result, steps = self._run_life_advance_speed_fixture(
            active_wars=[
                _war(
                    allied_armies=[player],
                    war_objective_province_ids=[2585],
                    objective_province_states=[
                        _objective_state(2585, active_siege=siege)
                    ],
                )
            ],
            player_armies=[player],
            extra_capabilities=(
                "game.state.war-objective-siege-progress",
            ),
            expected_speed=5,
            horizon_days=7,
        )

        self.assertEqual(
            steps, ["set-speed-5", "resume-map", "pause-map"]
        )
        self.assertEqual(result["elapsed_days"], 7)
        self.assertEqual(result["timeline_policy"], "bounded_non_tactical")

    def test_life_advance_requires_all_timeline_speed_primitives(self) -> None:
        for omitted in ("set-speed-1", "set-speed-3", "set-speed-5"):
            with self.subTest(omitted=omitted):
                endpoint = FakeEndpoint()
                driver = NativeHeadlessGameplayDriver(
                    endpoint.pipe_name,
                    endpoint=endpoint,
                )
                commands = {
                    "set-speed-1",
                    "set-speed-3",
                    "set-speed-5",
                }
                commands.remove(omitted)
                endpoint.publish(
                    _hello(
                        "game.state.snapshot",
                        "game.state.army-routes",
                        "game.state.war-objective-assault",
                        "game.command.pause-map",
                        "game.command.resume-map",
                        *(f"game.command.{step}" for step in sorted(commands)),
                    )
                )
                endpoint.publish(_snapshot(1, speed=5))

                self.assertNotIn(
                    "life-advance", driver.capabilities()["action_steps"]
                )
                with self.assertRaisesRegex(
                    UnsupportedStepError, "does not implement.*life-advance"
                ):
                    driver.execute_step("life-advance")
                self.assertFalse(
                    any(
                        frame.get("type") == "execute_step"
                        for frame in endpoint.frames
                    )
                )

    def test_active_route_life_advance_horizon_is_one_day_until_arrival(
        self,
    ) -> None:
        player = _army(
            101,
            province_id=2597,
            move_target_province_id=2596,
            route_province_ids=[2596],
            army_state="moving",
        )
        snapshot = {
            "paused": True,
            "war_objective_siege_progress_supported": False,
            "player_armies": [player],
            "active_wars": [_war(allied_armies=[player])],
        }

        self.assertEqual(_life_advance_horizon_days(snapshot), 1)
        player["move_target_province_id"] = None
        player["route_province_ids"] = []
        player["army_state"] = "regular"
        self.assertEqual(_life_advance_horizon_days(snapshot), 7)

    def test_route_target_alone_enforces_one_day_horizon(self) -> None:
        player = _army(
            101,
            province_id=2597,
            move_target_province_id=2596,
            army_state="moving",
        )
        snapshot = {
            "paused": True,
            "war_objective_siege_progress_supported": True,
            "player_armies": [player],
            "active_wars": [],
        }

        self.assertEqual(_life_advance_horizon_days(snapshot), 1)

    def test_any_controllable_combat_or_retreat_enforces_one_day_horizon(
        self,
    ) -> None:
        safe = _army(
            101,
            province_id=20,
            route_province_ids=[],
            army_state="regular",
        )
        for tactical in (
            {"army_state": "combat", "army_state_code": 2},
            {"army_state": "retreating", "army_state_code": 6},
            {"in_combat": True},
            {"retreating": True},
        ):
            with self.subTest(tactical=tactical):
                army = _army(202, province_id=31, **tactical)
                snapshot = {
                    "paused": True,
                    "player_armies": [safe, army],
                    "active_wars": [_war(allied_armies=[safe, army])],
                }
                self.assertEqual(_life_advance_horizon_days(snapshot), 1)
                result, steps = self._run_life_advance_speed_fixture(
                    active_wars=[_war(allied_armies=[safe, army])],
                    player_armies=[safe, army],
                    expected_speed=1,
                    horizon_days=1,
                )
                self.assertEqual(
                    steps, ["set-speed-1", "resume-map", "pause-map"]
                )
                self.assertEqual(
                    result["timeline_policy"], "player_tactical"
                )

    def test_combat_stays_speed_one_and_remote_enemy_route_uses_three(
        self,
    ) -> None:
        combat = _army(
            101, province_id=20, army_state="combat", army_state_code=2
        )
        combat_result, combat_steps = self._run_life_advance_speed_fixture(
            active_wars=[_war(allied_armies=[combat])],
            player_armies=[combat],
            expected_speed=1,
            horizon_days=1,
        )
        self.assertEqual(
            combat_steps, ["set-speed-1", "resume-map", "pause-map"]
        )
        self.assertEqual(combat_result["elapsed_days"], 1)

        player = _army(
            101,
            province_id=2585,
            army_state="sieging",
            route_province_ids=[],
        )
        enemy = _army(
            202,
            province_id=2581,
            controllable=False,
            move_target_province_id=2596,
            route_province_ids=[2596],
            army_state="moving",
        )
        enemy_result, enemy_steps = self._run_life_advance_speed_fixture(
            active_wars=[
                _war(allied_armies=[player], enemy_armies=[enemy])
            ],
            player_armies=[player],
            expected_speed=3,
            horizon_days=1,
            actual_elapsed_days=3,
        )
        self.assertEqual(
            enemy_steps, ["set-speed-3", "resume-map", "pause-map"]
        )
        self.assertEqual(enemy_result["requested_horizon_days"], 1)
        self.assertEqual(enemy_result["elapsed_days"], 3)
        self.assertTrue(enemy_result["paused"])
        self.assertEqual(enemy_result["timeline_speed"], 3)
        self.assertEqual(
            enemy_result["timeline_policy"], "remote_enemy_route"
        )

    def test_enemy_route_intersecting_stationary_player_stays_speed_one(
        self,
    ) -> None:
        player = _army(
            101,
            province_id=2585,
            army_state="sieging",
            route_province_ids=[],
        )
        enemy = _army(
            202,
            province_id=2581,
            controllable=False,
            move_target_province_id=2585,
            route_province_ids=[2585],
            army_state="moving",
        )
        result, steps = self._run_life_advance_speed_fixture(
            active_wars=[
                _war(allied_armies=[player], enemy_armies=[enemy])
            ],
            player_armies=[player],
            expected_speed=1,
            horizon_days=1,
        )

        self.assertEqual(
            steps, ["set-speed-1", "resume-map", "pause-map"]
        )
        self.assertEqual(
            result["timeline_policy"], "enemy_route_imminent_or_unknown"
        )

    def test_deep_enemy_route_endpoint_at_player_stays_speed_one(
        self,
    ) -> None:
        player = _army(
            101,
            province_id=2585,
            army_state="sieging",
            route_province_ids=[],
        )
        enemy = _army(
            202,
            province_id=2581,
            controllable=False,
            move_target_province_id=2585,
            route_province_ids=[2596, 2595, 2585],
            army_state="moving",
        )
        result, steps = self._run_life_advance_speed_fixture(
            active_wars=[
                _war(allied_armies=[player], enemy_armies=[enemy])
            ],
            player_armies=[player],
            expected_speed=1,
            horizon_days=1,
        )

        self.assertEqual(
            steps, ["set-speed-1", "resume-map", "pause-map"]
        )
        self.assertEqual(
            result["timeline_policy"], "enemy_route_imminent_or_unknown"
        )

    def test_production_history_2575_route_to_player_stays_speed_one(
        self,
    ) -> None:
        player_armies = [
            _army(
                33554797,
                province_id=5598,
                army_state="sieging",
                army_state_code=3,
                route_province_ids=[],
            ),
            *(
                _army(
                    army_id,
                    province_id=2619,
                    army_state="regular",
                    army_state_code=1,
                    route_province_ids=[],
                )
                for army_id in (
                    33554818,
                    67109252,
                    83886358,
                    117440751,
                    218103933,
                )
            ),
        ]
        enemies = [
            _army(
                83886265,
                province_id=702,
                controllable=False,
                army_state="sieging",
                army_state_code=3,
                route_province_ids=[],
            ),
            _army(
                117440838,
                province_id=496,
                controllable=False,
                move_target_province_id=5598,
                army_state="moving",
                army_state_code=7,
                route_province_ids=[
                    5565,
                    5566,
                    5567,
                    5568,
                    5576,
                    5577,
                    753,
                    5684,
                    5683,
                    5596,
                    5597,
                    5598,
                ],
            ),
        ]

        result, steps = self._run_life_advance_speed_fixture(
            active_wars=[
                _war(
                    war_id=33554527,
                    allied_armies=player_armies,
                    enemy_armies=enemies,
                )
            ],
            player_armies=player_armies,
            expected_speed=1,
            horizon_days=1,
        )

        self.assertEqual(
            steps, ["set-speed-1", "resume-map", "pause-map"]
        )
        self.assertEqual(result["requested_horizon_days"], 1)
        self.assertEqual(result["timeline_speed"], 1)
        self.assertEqual(
            result["timeline_policy"], "enemy_route_imminent_or_unknown"
        )

    def test_production_history_2421_remote_route_uses_speed_three(
        self,
    ) -> None:
        player_armies = [
            _army(
                33554797,
                province_id=5598,
                army_state="sieging",
                army_state_code=3,
                route_province_ids=[],
            ),
            *(
                _army(
                    army_id,
                    province_id=2619,
                    army_state="regular",
                    army_state_code=1,
                    route_province_ids=[],
                )
                for army_id in (
                    33554818,
                    67109252,
                    83886358,
                    117440751,
                    218103933,
                )
            ),
        ]
        enemies = [
            _army(
                83886265,
                province_id=5740,
                controllable=False,
                move_target_province_id=701,
                army_state="moving",
                army_state_code=7,
                route_province_ids=[
                    5739,
                    5733,
                    5734,
                    5735,
                    5731,
                    5732,
                    701,
                ],
            ),
            _army(
                117440838,
                province_id=496,
                controllable=False,
                army_state="gathering",
                army_state_code=5,
                route_province_ids=[],
            ),
        ]

        result, steps = self._run_life_advance_speed_fixture(
            active_wars=[
                _war(
                    war_id=33554527,
                    allied_armies=player_armies,
                    enemy_armies=enemies,
                )
            ],
            player_armies=player_armies,
            expected_speed=3,
            horizon_days=1,
            actual_elapsed_days=2,
        )

        self.assertEqual(
            steps, ["set-speed-3", "resume-map", "pause-map"]
        )
        self.assertEqual(result["requested_horizon_days"], 1)
        self.assertEqual(result["elapsed_days"], 2)
        self.assertEqual(result["timeline_speed"], 3)
        self.assertEqual(result["timeline_policy"], "remote_enemy_route")
        self.assertTrue(result["paused"])

    def test_remote_route_requires_route_and_assault_observation(self) -> None:
        player = _army(
            101,
            province_id=2585,
            army_state="sieging",
            route_province_ids=[],
        )
        enemy = _army(
            202,
            province_id=2581,
            controllable=False,
            move_target_province_id=2596,
            route_province_ids=[2596],
            army_state="moving",
        )
        for policy_capabilities in (
            (),
            ("game.state.army-routes",),
            ("game.state.war-objective-assault",),
        ):
            with self.subTest(policy_capabilities=policy_capabilities):
                result, steps = self._run_life_advance_speed_fixture(
                    active_wars=[
                        _war(
                            allied_armies=[player],
                            enemy_armies=[enemy],
                        )
                    ],
                    player_armies=[player],
                    policy_capabilities=policy_capabilities,
                    expected_speed=1,
                    horizon_days=1,
                )
                self.assertEqual(
                    steps, ["set-speed-1", "resume-map", "pause-map"]
                )
                self.assertEqual(
                    result["timeline_policy"],
                    "enemy_route_imminent_or_unknown",
                )

    def test_remote_route_requires_valid_enemy_current_province(self) -> None:
        player = _army(
            101,
            province_id=2585,
            army_state="sieging",
            route_province_ids=[],
        )
        for province_id in (None, 0):
            with self.subTest(province_id=province_id):
                enemy = _army(
                    202,
                    province_id=province_id,
                    controllable=False,
                    move_target_province_id=2596,
                    route_province_ids=[2596],
                    army_state="moving",
                )
                result, steps = self._run_life_advance_speed_fixture(
                    active_wars=[
                        _war(
                            allied_armies=[player],
                            enemy_armies=[enemy],
                        )
                    ],
                    player_armies=[player],
                    expected_speed=1,
                    horizon_days=1,
                )
                self.assertEqual(
                    steps, ["set-speed-1", "resume-map", "pause-map"]
                )
                self.assertEqual(
                    result["timeline_policy"],
                    "enemy_route_imminent_or_unknown",
                )

    def test_enemy_route_intersecting_second_player_stays_speed_one(
        self,
    ) -> None:
        players = [
            _army(
                101,
                province_id=2585,
                army_state="sieging",
                route_province_ids=[],
            ),
            _army(
                303,
                province_id=2586,
                army_state="regular",
                route_province_ids=[],
            ),
        ]
        enemy = _army(
            202,
            province_id=2581,
            controllable=False,
            move_target_province_id=2596,
            route_province_ids=[2586, 2596],
            army_state="moving",
        )
        result, steps = self._run_life_advance_speed_fixture(
            active_wars=[
                _war(allied_armies=players, enemy_armies=[enemy])
            ],
            player_armies=players,
            expected_speed=1,
            horizon_days=1,
        )

        self.assertEqual(
            steps, ["set-speed-1", "resume-map", "pause-map"]
        )
        self.assertEqual(
            result["timeline_policy"], "enemy_route_imminent_or_unknown"
        )

    def test_incomplete_enemy_route_stays_speed_one(self) -> None:
        player = _army(
            101,
            province_id=2585,
            army_state="sieging",
            route_province_ids=[],
        )
        enemy = _army(
            202,
            province_id=2581,
            controllable=False,
            move_target_province_id=2596,
            route_province_ids=[],
            army_state="moving",
        )
        result, steps = self._run_life_advance_speed_fixture(
            active_wars=[
                _war(allied_armies=[player], enemy_armies=[enemy])
            ],
            player_armies=[player],
            expected_speed=1,
            horizon_days=1,
        )

        self.assertEqual(
            steps, ["set-speed-1", "resume-map", "pause-map"]
        )
        self.assertEqual(
            result["timeline_policy"], "enemy_route_imminent_or_unknown"
        )

    def test_remote_route_speed_three_fails_closed_on_player_state(self) -> None:
        enemy = _army(
            202,
            province_id=2581,
            controllable=False,
            move_target_province_id=2596,
            route_province_ids=[2596],
            army_state="moving",
        )
        for state in ("gathering", "unknown-native-state"):
            with self.subTest(state=state):
                player = _army(
                    101,
                    province_id=2585,
                    army_state=state,
                    route_province_ids=[],
                )
                result, steps = self._run_life_advance_speed_fixture(
                    active_wars=[
                        _war(
                            allied_armies=[player],
                            enemy_armies=[enemy],
                        )
                    ],
                    player_armies=[player],
                    expected_speed=1,
                    horizon_days=1,
                )

                self.assertEqual(
                    steps, ["set-speed-1", "resume-map", "pause-map"]
                )
                self.assertEqual(
                    result["timeline_policy"],
                    "enemy_route_imminent_or_unknown",
                )

    def test_remote_route_speed_three_requires_complete_player_projection(
        self,
    ) -> None:
        player = _army(
            101,
            province_id=2585,
            army_state="sieging",
            route_province_ids=[],
        )
        enemy = _army(
            202,
            province_id=2581,
            controllable=False,
            move_target_province_id=2596,
            route_province_ids=[2596],
            army_state="moving",
        )
        cases: list[tuple[str, dict[str, object], list[dict[str, object]]]] = []

        missing_allied = _war(
            allied_armies=[player], enemy_armies=[enemy]
        )
        missing_allied.pop("allied_armies")
        cases.append(("missing_allied", missing_allied, [player]))

        other_player = _army(
            303,
            province_id=2586,
            army_state="regular",
            route_province_ids=[],
        )
        cases.append(
            (
                "allied_set_mismatch",
                _war(allied_armies=[player], enemy_armies=[enemy]),
                [player, other_player],
            )
        )

        ally_at_wrong_province = dict(player)
        ally_at_wrong_province["current_province_id"] = 2586
        cases.append(
            (
                "allied_position_mismatch",
                _war(
                    allied_armies=[ally_at_wrong_province],
                    enemy_armies=[enemy],
                ),
                [player],
            )
        )

        ally_with_route = dict(player)
        ally_with_route["army_state"] = "moving"
        ally_with_route["move_target_province_id"] = 2587
        ally_with_route["route_province_ids"] = [2587]
        cases.append(
            (
                "allied_tactical_projection_mismatch",
                _war(
                    allied_armies=[ally_with_route],
                    enemy_armies=[enemy],
                ),
                [player],
            )
        )

        incomplete_player = _army(
            404,
            province_id=2585,
            army_state="sieging",
        )
        cases.append(
            (
                "missing_player_route_projection",
                _war(
                    allied_armies=[incomplete_player],
                    enemy_armies=[enemy],
                ),
                [incomplete_player],
            )
        )

        for name, war, players in cases:
            with self.subTest(name=name):
                result, steps = self._run_life_advance_speed_fixture(
                    active_wars=[war],
                    player_armies=players,
                    expected_speed=1,
                    horizon_days=1,
                )
                self.assertEqual(
                    steps, ["set-speed-1", "resume-map", "pause-map"]
                )
                self.assertEqual(
                    result["timeline_policy"],
                    "enemy_route_imminent_or_unknown",
                )

    def test_remote_route_rejects_duplicate_or_inconsistent_projections(
        self,
    ) -> None:
        player = _army(
            101,
            province_id=2585,
            army_state="sieging",
            route_province_ids=[],
        )
        enemy = _army(
            202,
            province_id=2581,
            controllable=False,
            move_target_province_id=2596,
            route_province_ids=[2596],
            army_state="moving",
        )
        inconsistent_enemy = dict(enemy)
        inconsistent_enemy["move_target_province_id"] = 2597
        inconsistent_enemy["route_province_ids"] = [2597]
        cases = (
            (
                "duplicate_allied_in_one_war",
                [
                    _war(
                        allied_armies=[player, dict(player)],
                        enemy_armies=[enemy],
                    )
                ],
            ),
            (
                "duplicate_enemy_in_one_war",
                [
                    _war(
                        allied_armies=[player],
                        enemy_armies=[enemy, dict(enemy)],
                    )
                ],
            ),
            (
                "inconsistent_enemy_across_wars",
                [
                    _war(
                        war_id=61,
                        allied_armies=[player],
                        enemy_armies=[enemy],
                    ),
                    _war(
                        war_id=62,
                        allied_armies=[dict(player)],
                        enemy_armies=[inconsistent_enemy],
                    ),
                ],
            ),
        )
        for name, wars in cases:
            with self.subTest(name=name):
                result, steps = self._run_life_advance_speed_fixture(
                    active_wars=wars,
                    player_armies=[player],
                    expected_speed=1,
                    horizon_days=1,
                )
                self.assertEqual(
                    steps, ["set-speed-1", "resume-map", "pause-map"]
                )
                self.assertEqual(
                    result["timeline_policy"],
                    "enemy_route_imminent_or_unknown",
                )

    def test_consistent_enemy_projection_across_wars_can_use_speed_three(
        self,
    ) -> None:
        player = _army(
            101,
            province_id=2585,
            army_state="sieging",
            route_province_ids=[],
        )
        enemy = _army(
            202,
            province_id=2581,
            controllable=False,
            move_target_province_id=2596,
            route_province_ids=[2596],
            army_state="moving",
        )
        result, steps = self._run_life_advance_speed_fixture(
            active_wars=[
                _war(
                    war_id=61,
                    allied_armies=[player],
                    enemy_armies=[enemy],
                ),
                _war(
                    war_id=62,
                    allied_armies=[dict(player)],
                    enemy_armies=[dict(enemy)],
                ),
            ],
            player_armies=[player],
            expected_speed=3,
            horizon_days=1,
            actual_elapsed_days=2,
        )

        self.assertEqual(
            steps, ["set-speed-3", "resume-map", "pause-map"]
        )
        self.assertEqual(result["requested_horizon_days"], 1)
        self.assertEqual(result["elapsed_days"], 2)
        self.assertEqual(result["timeline_policy"], "remote_enemy_route")
        self.assertTrue(result["paused"])

    def test_mixed_complete_and_incomplete_enemy_routes_stay_speed_one(
        self,
    ) -> None:
        player = _army(
            101,
            province_id=2585,
            army_state="sieging",
            route_province_ids=[],
        )
        complete = _army(
            202,
            province_id=2581,
            controllable=False,
            move_target_province_id=2596,
            route_province_ids=[2596],
            army_state="moving",
        )
        incomplete = _army(
            303,
            province_id=2582,
            controllable=False,
            move_target_province_id=2597,
            route_province_ids=[],
            army_state="moving",
        )
        result, steps = self._run_life_advance_speed_fixture(
            active_wars=[
                _war(
                    allied_armies=[player],
                    enemy_armies=[complete, incomplete],
                )
            ],
            player_armies=[player],
            expected_speed=1,
            horizon_days=1,
        )

        self.assertEqual(
            steps, ["set-speed-1", "resume-map", "pause-map"]
        )
        self.assertEqual(
            result["timeline_policy"], "enemy_route_imminent_or_unknown"
        )

    def test_moving_state_without_route_fields_enforces_one_day_horizon(
        self,
    ) -> None:
        for state in (
            {"army_state": "moving"},
            {"army_state_code": 7},
        ):
            with self.subTest(state=state):
                player = _army(
                    101,
                    province_id=2597,
                    observe_move_target=False,
                    **state,
                )
                snapshot = {
                    "paused": True,
                    "war_objective_siege_progress_supported": False,
                    "player_armies": [player],
                    "active_wars": [_war(allied_armies=[player])],
                }

                self.assertEqual(_life_advance_horizon_days(snapshot), 1)

    def test_active_assault_horizon_does_not_require_siege_progress_capability(
        self,
    ) -> None:
        snapshot = {
            "paused": True,
            "war_objective_siege_progress_supported": False,
            "war_objective_assault_supported": True,
            "active_wars": [
                _war(
                    objective_province_states=[
                        _objective_state(
                            2585,
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
                    ]
                )
            ],
        }

        self.assertEqual(_life_advance_horizon_days(snapshot), 1)

    def test_exact_objective_capabilities_and_state_are_projected(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.war-objective-occupation",
                "game.state.war-objective-fort-level",
                "game.state.war-objective-garrison",
                "game.state.war-objective-siege-progress",
            )
        )
        player = _army(101, province_id=2585, army_state="sieging")
        endpoint.publish(
            _snapshot(
                2,
                active_wars=[
                    _war(
                        allied_armies=[player],
                        war_objective_province_ids=[2585],
                        objective_province_states=[
                            _objective_state(
                                2585,
                                active_siege=_active_siege(),
                            )
                        ],
                    )
                ],
                player_armies=[player],
            )
        )

        projected = driver.take_snapshot()
        capabilities = driver.capabilities()

        for name in (
            "war_objective_occupation_supported",
            "war_objective_fort_level_supported",
            "war_objective_garrison_supported",
            "war_objective_siege_progress_supported",
        ):
            self.assertTrue(projected[name])
            self.assertTrue(capabilities[name])
        siege = projected["active_wars"][0]["objective_province_states"][0][
            "active_siege"
        ]
        self.assertEqual(
            siege["remaining_work"],
            {"raw": 7_500_000, "scale": 100_000},
        )

        endpoint.publish(
            _hello("bridge.identity", "bridge.heartbeat", "bridge.ping")
        )
        ping = endpoint.frames[-1]
        self.assertEqual(ping["type"], "ping")
        endpoint.publish(
            {
                "type": "heartbeat",
                "protocol_version": 1,
                "sequence": 7,
                "pid": 4242,
                "monotonic_ms": 500,
            }
        )
        endpoint.publish(
            {
                "type": "pong",
                "protocol_version": 1,
                "request_id": ping["request_id"],
                "pid": 4242,
            }
        )

        connected = driver.capabilities()
        diagnostics = connected["diagnostics"]
        self.assertTrue(diagnostics["connected"])
        self.assertEqual(diagnostics["bridge_pid"], 4242)
        self.assertEqual(diagnostics["last_heartbeat"]["sequence"], 7)
        self.assertEqual(
            diagnostics["last_pong"]["request_id"], ping["request_id"]
        )
        self.assertFalse(connected["snapshot"])
        self.assertEqual(connected["action_steps"], [])
        with self.assertRaisesRegex(UnsupportedStepError, "did not advertise"):
            driver.take_snapshot()
        with self.assertRaisesRegex(UnsupportedStepError, "does not implement"):
            driver.execute_step("life-advance")

    def test_protocol_extension_routes_snapshot_and_command_result(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello("game.state.snapshot", "game.command.life-advance")
        )
        endpoint.publish(_snapshot(19))

        capabilities = driver.capabilities()
        self.assertTrue(capabilities["snapshot"])
        self.assertEqual(capabilities["action_steps"], ["life-advance"])
        snapshot = driver.take_snapshot()
        self.assertEqual(snapshot["native_revision"], 19)
        self.assertEqual(snapshot["phase"], "map_hud")

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") == "execute_step":
                endpoint.publish(
                    {
                        "type": "command_result",
                        "protocol_version": 1,
                        "request_id": frame["request_id"],
                        "ok": True,
                        "result": {"step": frame["step"], "accepted": True},
                    }
                )

        endpoint.send_hook = answer
        result = driver.execute_step(
            "life-advance", expected_revision=int(snapshot["revision"])
        )
        command = next(
            frame for frame in reversed(endpoint.frames)
            if frame.get("type") == "execute_step"
        )
        self.assertEqual(command["expected_revision"], 19)
        self.assertTrue(result["accepted"])
        self.assertEqual(result["backend_id"], "native-headless")
        self.assertEqual(
            driver.take_snapshot()["native_command_history"],
            [
                {
                    "index": 1,
                    "command": "life-advance",
                    "ok": True,
                    "result": result,
                }
            ],
        )

    def test_daemon_restart_restores_episode_and_command_history(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            endpoint = FakeEndpoint()
            driver = NativeHeadlessGameplayDriver(
                endpoint.pipe_name,
                endpoint=endpoint,
                state_dir=state_dir,
            )
            endpoint.publish(
                _hello(
                    "game.state.snapshot",
                    "game.state.played-character",
                    "game.command.life-advance",
                )
            )
            endpoint.publish(
                _snapshot(
                    19,
                    played_character={"character_id": 707, "alive": True},
                )
            )
            first = driver.take_snapshot()

            def answer(frame: dict[str, object]) -> None:
                if frame.get("type") == "execute_step":
                    endpoint.publish(
                        {
                            "type": "command_result",
                            "protocol_version": 1,
                            "request_id": frame["request_id"],
                            "ok": True,
                            "result": {
                                "step": frame["step"],
                                "accepted": True,
                            },
                        }
                    )

            endpoint.send_hook = answer
            driver.execute_step(
                "life-advance", expected_revision=int(first["revision"])
            )
            state_path = state_dir / "native-session" / "driver-state.json"
            persisted = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(persisted["bridge_pid"], 4242)
            self.assertEqual(persisted["episode_run_id"], first["episode_run_id"])
            self.assertEqual(len(persisted["command_history"]), 1)

            replacement_endpoint = FakeEndpoint(endpoint.pipe_name)
            replacement = NativeHeadlessGameplayDriver(
                replacement_endpoint.pipe_name,
                endpoint=replacement_endpoint,
                state_dir=state_dir,
            )
            replacement_endpoint.publish(
                _hello(
                    "game.state.snapshot",
                    "game.state.played-character",
                    "game.command.life-advance",
                )
            )
            replacement_endpoint.publish(
                _snapshot(
                    20,
                    played_character={"character_id": 707, "alive": True},
                )
            )
            restored = replacement.take_snapshot()
            self.assertEqual(restored["episode_run_id"], first["episode_run_id"])
            self.assertEqual(len(restored["native_command_history"]), 1)
            self.assertTrue(
                replacement.capabilities()["native_session_control"][
                    "driver_state_restored"
                ]
            )

            # A process-level restore inside the same driver keeps this
            # one-life episode, and updates the PID used by the next daemon.
            replacement_endpoint.publish({**_hello("game.state.snapshot"), "pid": 5000})
            replacement_endpoint.publish(
                _snapshot(
                    21,
                    played_character={"character_id": 707, "alive": True},
                )
            )
            after_process_restore = replacement.take_snapshot()
            self.assertEqual(
                after_process_restore["episode_run_id"], first["episode_run_id"]
            )
            self.assertEqual(
                json.loads(state_path.read_text(encoding="utf-8"))["bridge_pid"],
                5000,
            )

            new_endpoint = FakeEndpoint(endpoint.pipe_name)
            new_driver = NativeHeadlessGameplayDriver(
                new_endpoint.pipe_name,
                endpoint=new_endpoint,
                state_dir=state_dir,
            )
            new_endpoint.publish({**_hello("game.state.snapshot"), "pid": 6000})
            new_endpoint.publish(
                _snapshot(
                    1,
                    played_character={"character_id": 909, "alive": True},
                )
            )
            new_episode = new_driver.take_snapshot()
            self.assertEqual(new_episode["episode_character_id"], 909)
            self.assertNotEqual(
                new_episode["episode_run_id"], first["episode_run_id"]
            )
            self.assertEqual(new_episode["native_command_history"], [])
            self.assertFalse(
                new_driver.capabilities()["native_session_control"][
                    "driver_state_restored"
                ]
            )

    def test_read_only_history_step_classifier_is_exact_for_previews(self) -> None:
        self.assertTrue(
            _is_deferred_read_only_history_step("query-fixture-v1")
        )
        self.assertTrue(
            _is_deferred_read_only_history_step(
                "preview-move-army-101-to-2585"
            )
        )
        self.assertTrue(
            _is_deferred_read_only_history_step(
                "preview-active-combat-retreat-v1-101-to-2585"
            )
        )
        self.assertFalse(
            _is_deferred_read_only_history_step(
                "preview-move-army-0-to-2585"
            )
        )
        self.assertFalse(
            _is_deferred_read_only_history_step(
                "preview-active-combat-retreat-v1-101-to-0"
            )
        )
        self.assertFalse(
            _is_deferred_read_only_history_step("move-army-101-to-2585")
        )

    def test_successful_read_only_history_batches_until_action_barrier(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            endpoint = FakeEndpoint()
            driver = NativeHeadlessGameplayDriver(
                endpoint.pipe_name,
                endpoint=endpoint,
                state_dir=state_dir,
            )
            endpoint.publish(
                _hello("game.state.snapshot", "game.state.played-character")
            )
            endpoint.publish(
                _snapshot(
                    1,
                    played_character={"character_id": 707, "alive": True},
                )
            )
            driver.take_snapshot()
            state_path = state_dir / "native-session" / "driver-state.json"
            baseline = state_path.read_bytes()
            read_only_steps = [
                "query-fixture-v1",
                "preview-move-army-101-to-2585",
                "preview-active-combat-retreat-v1-101-to-2585",
            ]

            for step in read_only_steps:
                driver._record_command(
                    step,
                    ok=True,
                    result={"step": step, "status": "available"},
                )
                self.assertEqual(state_path.read_bytes(), baseline)

            self.assertTrue(driver._driver_state_dirty)
            self.assertEqual(
                [
                    row["command"]
                    for row in driver.take_snapshot()[
                        "native_command_history"
                    ]
                ],
                read_only_steps,
            )

            driver._record_command(
                "life-advance",
                ok=True,
                result={"step": "life-advance", "elapsed_days": 1},
            )

            persisted = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(
                [row["command"] for row in persisted["command_history"]],
                [*read_only_steps, "life-advance"],
            )
            self.assertFalse(driver._driver_state_dirty)

    def test_driver_state_barrier_encodes_without_payload_history_clone(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            endpoint = FakeEndpoint()
            driver = NativeHeadlessGameplayDriver(
                endpoint.pipe_name,
                endpoint=endpoint,
                state_dir=state_dir,
            )
            endpoint.publish(
                _hello("game.state.snapshot", "game.state.played-character")
            )
            endpoint.publish(
                _snapshot(
                    1,
                    played_character={"character_id": 707, "alive": True},
                )
            )
            driver.take_snapshot()

            with mock.patch.object(
                driver,
                "_driver_state_payload_locked",
                side_effect=AssertionError("full payload clone is forbidden"),
            ):
                driver._record_command(
                    "life-advance",
                    ok=True,
                    result={"step": "life-advance", "elapsed_days": 1},
                )

            state_path = state_dir / "native-session" / "driver-state.json"
            encoded = state_path.read_bytes()
            persisted = json.loads(encoded.decode("utf-8"))
            self.assertTrue(encoded.endswith(b"\n"))
            self.assertNotIn(b'\n  "', encoded)
            self.assertEqual(persisted["format_version"], 2)
            self.assertEqual(
                persisted["command_history"][-1]["command"],
                "life-advance",
            )
            self.assertFalse(driver._driver_state_dirty)

    def test_failed_read_only_command_flushes_the_pending_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            endpoint = FakeEndpoint()
            driver = NativeHeadlessGameplayDriver(
                endpoint.pipe_name,
                endpoint=endpoint,
                state_dir=state_dir,
            )
            endpoint.publish(
                _hello("game.state.snapshot", "game.state.played-character")
            )
            endpoint.publish(
                _snapshot(
                    1,
                    played_character={"character_id": 707, "alive": True},
                )
            )
            driver.take_snapshot()
            state_path = state_dir / "native-session" / "driver-state.json"
            baseline = state_path.read_bytes()

            driver._record_command(
                "query-fixture-v1",
                ok=True,
                result={"step": "query-fixture-v1"},
            )
            self.assertEqual(state_path.read_bytes(), baseline)
            driver._record_command(
                "query-fixture-v2",
                ok=False,
                error="BridgeUnavailableError: fixture failure",
            )

            persisted = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(len(persisted["command_history"]), 2)
            self.assertTrue(persisted["command_history"][0]["ok"])
            self.assertFalse(persisted["command_history"][1]["ok"])
            self.assertFalse(driver._driver_state_dirty)

    def test_close_flushes_only_a_pending_read_only_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            endpoint = FakeEndpoint()
            driver = NativeHeadlessGameplayDriver(
                endpoint.pipe_name,
                endpoint=endpoint,
                state_dir=state_dir,
            )
            endpoint.publish(
                _hello("game.state.snapshot", "game.state.played-character")
            )
            endpoint.publish(
                _snapshot(
                    1,
                    played_character={"character_id": 707, "alive": True},
                )
            )
            driver.take_snapshot()
            state_path = state_dir / "native-session" / "driver-state.json"
            baseline = state_path.read_bytes()
            driver._record_command(
                "preview-move-army-101-to-2585",
                ok=True,
                result={"step": "preview-move-army-101-to-2585"},
            )
            self.assertEqual(state_path.read_bytes(), baseline)

            driver.close()

            persisted = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(
                persisted["command_history"][-1]["command"],
                "preview-move-army-101-to-2585",
            )
            self.assertFalse(driver._driver_state_dirty)
            self.assertTrue(endpoint.closed)

    def test_persistence_failure_keeps_dirty_state_for_close_retry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            endpoint = FakeEndpoint()
            driver = NativeHeadlessGameplayDriver(
                endpoint.pipe_name,
                endpoint=endpoint,
                state_dir=state_dir,
            )
            endpoint.publish(
                _hello("game.state.snapshot", "game.state.played-character")
            )
            endpoint.publish(
                _snapshot(
                    1,
                    played_character={"character_id": 707, "alive": True},
                )
            )
            driver.take_snapshot()

            with mock.patch(
                "xar_autoplayer.bridge.native_driver.write_bytes_atomic",
                side_effect=OSError("fixture write failure"),
            ):
                driver._record_command(
                    "life-advance",
                    ok=True,
                    result={"step": "life-advance"},
                )

            self.assertTrue(driver._driver_state_dirty)
            self.assertIn(
                "fixture write failure",
                str(driver._driver_state_error),
            )
            driver.close()
            persisted = json.loads(
                (
                    state_dir / "native-session" / "driver-state.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(
                persisted["command_history"][-1]["command"],
                "life-advance",
            )
            self.assertFalse(driver._driver_state_dirty)
            self.assertTrue(endpoint.closed)

    def test_query_appended_during_write_remains_dirty_for_close(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            endpoint = FakeEndpoint()
            driver = NativeHeadlessGameplayDriver(
                endpoint.pipe_name,
                endpoint=endpoint,
                state_dir=state_dir,
            )
            endpoint.publish(
                _hello("game.state.snapshot", "game.state.played-character")
            )
            endpoint.publish(
                _snapshot(
                    1,
                    played_character={"character_id": 707, "alive": True},
                )
            )
            driver.take_snapshot()
            state_path = state_dir / "native-session" / "driver-state.json"
            write_started = threading.Event()
            release_write = threading.Event()

            def blocked_write(path: Path, payload: bytes) -> None:
                write_started.set()
                self.assertTrue(release_write.wait(timeout=1.0))
                write_bytes_atomic(path, payload)

            worker = threading.Thread(
                target=lambda: driver._record_command(
                    "life-advance",
                    ok=True,
                    result={"step": "life-advance"},
                )
            )
            with mock.patch(
                "xar_autoplayer.bridge.native_driver.write_bytes_atomic",
                side_effect=blocked_write,
            ):
                worker.start()
                self.assertTrue(write_started.wait(timeout=1.0))
                driver._record_command(
                    "query-fixture-v1",
                    ok=True,
                    result={"step": "query-fixture-v1"},
                )
                self.assertTrue(driver._driver_state_dirty)
                release_write.set()
                worker.join(timeout=1.0)
                self.assertFalse(worker.is_alive())

            persisted_before_close = json.loads(
                state_path.read_text(encoding="utf-8")
            )
            self.assertEqual(
                [
                    row["command"]
                    for row in persisted_before_close["command_history"]
                ],
                ["life-advance"],
            )
            self.assertTrue(driver._driver_state_dirty)

            driver.close()

            persisted_after_close = json.loads(
                state_path.read_text(encoding="utf-8")
            )
            self.assertEqual(
                [
                    row["command"]
                    for row in persisted_after_close["command_history"]
                ],
                ["life-advance", "query-fixture-v1"],
            )
            self.assertFalse(driver._driver_state_dirty)
            self.assertTrue(endpoint.closed)

    def test_close_reflushes_query_appended_during_its_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            endpoint = FakeEndpoint()
            driver = NativeHeadlessGameplayDriver(
                endpoint.pipe_name,
                endpoint=endpoint,
                state_dir=state_dir,
            )
            endpoint.publish(
                _hello("game.state.snapshot", "game.state.played-character")
            )
            endpoint.publish(
                _snapshot(
                    1,
                    played_character={"character_id": 707, "alive": True},
                )
            )
            driver.take_snapshot()
            driver._record_command(
                "query-fixture-v1",
                ok=True,
                result={"step": "query-fixture-v1"},
            )
            state_path = state_dir / "native-session" / "driver-state.json"
            first_write_started = threading.Event()
            release_first_write = threading.Event()
            write_count = 0

            def block_first_write(path: Path, payload: bytes) -> None:
                nonlocal write_count
                write_count += 1
                if write_count == 1:
                    first_write_started.set()
                    self.assertTrue(release_first_write.wait(timeout=1.0))
                write_bytes_atomic(path, payload)

            worker = threading.Thread(target=driver.close)
            with mock.patch(
                "xar_autoplayer.bridge.native_driver.write_bytes_atomic",
                side_effect=block_first_write,
            ):
                worker.start()
                self.assertTrue(first_write_started.wait(timeout=1.0))
                driver._record_command(
                    "query-fixture-v2",
                    ok=True,
                    result={"step": "query-fixture-v2"},
                )
                release_first_write.set()
                worker.join(timeout=2.0)
                self.assertFalse(worker.is_alive())

            persisted = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(
                [row["command"] for row in persisted["command_history"]],
                ["query-fixture-v1", "query-fixture-v2"],
            )
            self.assertEqual(write_count, 2)
            self.assertFalse(driver._driver_state_dirty)
            self.assertTrue(endpoint.closed)

    def test_close_does_not_loop_without_driver_state_storage(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            state_dir=None,
        )
        endpoint.publish(
            _hello("game.state.snapshot", "game.state.played-character")
        )
        endpoint.publish(
            _snapshot(
                1,
                played_character={"character_id": 707, "alive": True},
            )
        )
        driver.take_snapshot()
        driver._record_command(
            "query-fixture-v1",
            ok=True,
            result={"step": "query-fixture-v1"},
        )

        driver.close()

        self.assertTrue(driver._driver_state_dirty)
        self.assertTrue(endpoint.closed)

    def test_v1_hot_migration_then_cold_checkpoint_resume_rolls_back_tail(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            pipe_name = r"\\.\pipe\xar_cold_migration"
            checkpoint_path, _checkpoint = _write_driver_state_checkpoint_fixture(
                state_dir,
                pipe_name,
                bridge_pid=140760,
                character_id=29829,
                run_id="native-29829-live-run",
                format_version=1,
                include_v2_anchor=False,
            )
            hot_endpoint = FakeEndpoint(pipe_name)
            hot_driver = NativeHeadlessGameplayDriver(
                pipe_name,
                endpoint=hot_endpoint,
                state_dir=state_dir,
                save_dir=checkpoint_path.parent,
            )
            hot_endpoint.publish({**_hello("game.state.snapshot"), "pid": 140760})

            hot_control = hot_driver.capabilities()["native_session_control"]
            self.assertTrue(hot_control["driver_state_restored"])
            self.assertEqual(hot_control["driver_state_restore_kind"], "same_pid_hot")
            migrated = json.loads(
                (
                    state_dir / "native-session" / "driver-state.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(migrated["format_version"], 2)
            self.assertEqual(migrated["last_checkpoint"]["history_index"], 8)
            self.assertEqual(
                migrated["last_checkpoint"]["episode_character_id"], 29829
            )
            self.assertEqual(
                migrated["last_checkpoint"]["episode_run_id"],
                "native-29829-live-run",
            )

            cold_endpoint = FakeEndpoint(pipe_name)
            cold_driver = NativeHeadlessGameplayDriver(
                pipe_name,
                endpoint=cold_endpoint,
                state_dir=state_dir,
                save_dir=checkpoint_path.parent,
            )
            cold_endpoint.publish({**_hello("game.state.snapshot"), "pid": 150000})
            pending = cold_driver.capabilities()["native_session_control"]
            self.assertEqual(
                pending["episode_binding_state"], "pending_cold_candidate"
            )
            self.assertFalse(pending["driver_state_restored"])

            cold_endpoint.publish(
                _snapshot(
                    1,
                    map_ready=False,
                    date_raw=53_168_784,
                    played_character={"character_id": 29829, "alive": True},
                )
            )
            not_ready = cold_driver.take_snapshot()
            self.assertTrue(not_ready["episode_identity_pending"])
            self.assertFalse(not_ready["one_life_terminal"])
            self.assertIsNone(not_ready["episode_character_id"])

            cold_endpoint.publish(
                _snapshot(
                    2,
                    date_raw=53_168_784,
                    played_character={"character_id": 29829, "alive": True},
                )
            )
            resumed = cold_driver.take_snapshot()
            self.assertEqual(resumed["episode_character_id"], 29829)
            self.assertEqual(resumed["episode_run_id"], "native-29829-live-run")
            self.assertFalse(resumed["one_life_terminal"])
            history = resumed["native_command_history"]
            self.assertEqual(len(history), 9)
            self.assertEqual(history[7]["command"], "save-checkpoint")
            self.assertEqual(history[8]["command"], "restore-checkpoint")
            self.assertEqual(
                history[8]["result"]["source"], "native-session-cold-start"
            )
            self.assertNotIn("move-army-1-to-2", [row["command"] for row in history])
            resumed_control = cold_driver.capabilities()["native_session_control"]
            self.assertTrue(resumed_control["driver_state_restored"])
            self.assertEqual(
                resumed_control["driver_state_restore_kind"], "cold_checkpoint"
            )
            persisted = json.loads(
                (
                    state_dir / "native-session" / "driver-state.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(persisted["bridge_pid"], 150000)
            self.assertEqual(len(persisted["command_history"]), 9)

    def test_restore_record_keeps_save_anchor_and_discards_factual_tail(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            endpoint = FakeEndpoint()
            driver = NativeHeadlessGameplayDriver(
                endpoint.pipe_name,
                endpoint=endpoint,
                state_dir=state_dir,
            )
            endpoint.publish(_hello("game.state.snapshot"))
            checkpoint = {
                "history_index": 2,
                "sha256": "a" * 64,
                "size": 123,
                "date_raw": 24_000,
            }
            driver._last_checkpoint = dict(checkpoint)
            driver._command_history = [
                {
                    "index": 1,
                    "command": "life-advance",
                    "ok": True,
                    "result": {},
                },
                {
                    "index": 2,
                    "command": "save-checkpoint",
                    "ok": True,
                    "result": {"checkpoint": dict(checkpoint)},
                },
                {
                    "index": 3,
                    "command": "move-army-1-to-2",
                    "ok": True,
                    "result": {},
                },
            ]

            driver._record_command(
                "restore-checkpoint",
                ok=True,
                result={"status": "restored"},
            )

            history = driver._history_snapshot()
            self.assertEqual(
                [row["command"] for row in history],
                ["life-advance", "save-checkpoint", "restore-checkpoint"],
            )
            self.assertEqual([row["index"] for row in history], [1, 2, 3])

    def test_cold_restore_uses_root_auto_turn_result_for_route_memory(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            pipe_name = r"\\.\pipe\xar_cold_route_memory"
            checkpoint_path, checkpoint = _write_driver_state_checkpoint_fixture(
                state_dir,
                pipe_name,
                bridge_pid=140760,
                character_id=707,
                run_id="native-707-route-memory",
            )
            state_path = state_dir / "native-session" / "driver-state.json"
            persisted = json.loads(state_path.read_text(encoding="utf-8"))
            persisted["command_history"][8] = {
                "index": 9,
                "command": "auto-turn",
                "ok": True,
                "result": {
                    "route_preview": {
                        "status": "available",
                        "army_id": 1,
                        "origin_province_id": 1,
                        "target_province_id": 2,
                        "route_province_ids": [3, 2],
                        "previewed_date_raw": 53_168_784,
                    },
                    "auto_turn": {
                        "selected_step": "preview-move-army-1-to-2",
                        "result": {
                            "route_preview": {
                                "status": "deferred",
                                "army_id": 1,
                                "target_province_id": 999,
                            }
                        },
                    },
                },
            }
            persisted["command_history"][9] = {
                "index": 10,
                "command": "auto-turn",
                "ok": True,
                "result": {
                    "war_action": {
                        "status": "moving",
                        "army_id": 1,
                        "target_province_id": 2,
                        "submitted_date_raw": 53_168_784,
                    },
                    "player_armies": [
                        _army(
                            1,
                            province_id=1,
                            move_target_province_id=2,
                            army_state="moving",
                            route_province_ids=[3, 2],
                        )
                    ],
                    "auto_turn": {
                        "selected_step": "move-army-1-to-2",
                        "result": {"war_action": {"status": "arrived"}},
                    },
                },
            }
            persisted["command_history"][10] = {
                "index": 11,
                "command": "life-advance",
                "ok": True,
                "result": {},
            }
            write_json_atomic(state_path, persisted)

            restored_player = _army(
                1,
                province_id=1,
                army_state="regular",
                route_province_ids=[],
            )
            endpoint = FakeEndpoint(pipe_name)
            driver = NativeHeadlessGameplayDriver(
                pipe_name,
                endpoint=endpoint,
                state_dir=state_dir,
                save_dir=checkpoint_path.parent,
            )
            endpoint.publish({**_hello("game.state.snapshot"), "pid": 150000})
            endpoint.publish(
                _snapshot(
                    1,
                    date_raw=int(checkpoint["date_raw"]),
                    played_character={"character_id": 707, "alive": True},
                    active_wars=[
                        _war(
                            61,
                            allied_armies=[restored_player],
                            war_objective_province_ids=[2, 4],
                        )
                    ],
                    player_armies=[restored_player],
                )
            )

            restored = driver.take_snapshot()
            self.assertEqual(
                [row["command"] for row in restored["native_command_history"]],
                ["life-advance"] * 7
                + ["save-checkpoint", "restore-checkpoint"],
            )
            failure = restored["native_rollback_war_failure"]
            self.assertEqual(failure["status"], "rolled_back_active_route")
            self.assertEqual(failure["war_id"], 61)
            self.assertEqual(failure["army_id"], 1)
            self.assertEqual(failure["restored_origin_province_id"], 1)
            self.assertEqual(failure["target_province_id"], 2)
            self.assertEqual(failure["route_province_ids"], [3, 2])
            self.assertEqual(restored["native_rollback_war_failures"], [failure])
            self.assertNotIn(
                "move-army-1-to-2",
                [row["command"] for row in restored["native_command_history"]],
            )
            on_disk = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(on_disk["rollback_war_failure"], failure)
            self.assertEqual(on_disk["rollback_war_failures"], [failure])

            resumed_endpoint = FakeEndpoint(pipe_name)
            resumed_driver = NativeHeadlessGameplayDriver(
                pipe_name,
                endpoint=resumed_endpoint,
                state_dir=state_dir,
                save_dir=checkpoint_path.parent,
            )
            resumed_endpoint.publish(
                {**_hello("game.state.snapshot"), "pid": 150000}
            )
            resumed_endpoint.publish(
                _snapshot(
                    2,
                    date_raw=int(checkpoint["date_raw"]),
                    played_character={"character_id": 707, "alive": True},
                    active_wars=[
                        _war(
                            61,
                            allied_armies=[restored_player],
                            war_objective_province_ids=[2, 4],
                        )
                    ],
                    player_armies=[restored_player],
                )
            )
            self.assertEqual(
                resumed_driver.take_snapshot()["native_rollback_war_failure"],
                failure,
            )
            self.assertEqual(
                resumed_driver.take_snapshot()["native_rollback_war_failures"],
                [failure],
            )

            next_endpoint = FakeEndpoint(pipe_name)
            next_driver = NativeHeadlessGameplayDriver(
                pipe_name,
                endpoint=next_endpoint,
                state_dir=state_dir,
                save_dir=checkpoint_path.parent,
            )
            next_endpoint.publish(
                {**_hello("game.state.snapshot"), "pid": 160000}
            )
            next_endpoint.publish(
                _snapshot(
                    1,
                    date_raw=int(checkpoint["date_raw"]),
                    played_character={"character_id": 909, "alive": True},
                    player_armies=[],
                    active_wars=[],
                )
            )
            new_episode = next_driver.take_snapshot()
            self.assertEqual(new_episode["episode_character_id"], 909)
            self.assertIsNone(new_episode["native_rollback_war_failure"])
            self.assertEqual(new_episode["native_rollback_war_failures"], [])

    def test_legacy_singular_seeds_two_entry_migration_and_round_trips(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            pipe_name = r"\\.\pipe\xar_two_rollback_memories"
            run_id = "native-707-two-rollback-memories"
            checkpoint_path, checkpoint = _write_driver_state_checkpoint_fixture(
                state_dir,
                pipe_name,
                bridge_pid=140760,
                character_id=707,
                run_id=run_id,
            )
            state_path = state_dir / "native-session" / "driver-state.json"
            persisted = json.loads(state_path.read_text(encoding="utf-8"))
            history = persisted["command_history"][:8]

            def append(command: str, result: dict[str, object]) -> None:
                history.append(
                    {
                        "index": len(history) + 1,
                        "command": command,
                        "ok": True,
                        "result": result,
                    }
                )

            def append_completed_epoch(target: int, route: list[int]) -> None:
                preview = {
                    "status": "available",
                    "army_id": 1,
                    "origin_province_id": 2598,
                    "target_province_id": target,
                    "route_province_ids": list(route),
                    "previewed_date_raw": checkpoint["date_raw"],
                }
                moving = _army(
                    1,
                    province_id=2598,
                    move_target_province_id=target,
                    army_state="moving",
                    route_province_ids=list(route),
                )
                append(
                    f"preview-move-army-1-to-{target}",
                    {"route_preview": preview},
                )
                append(
                    f"move-army-1-to-{target}",
                    {
                        "war_action": {
                            "status": "moving",
                            "army_id": 1,
                            "target_province_id": target,
                            "submitted_date_raw": checkpoint["date_raw"],
                        },
                        "player_armies": [moving],
                    },
                )
                append("life-advance", {"player_armies": [moving]})
                append("restore-checkpoint", {"status": "restored"})

            # The oldest completed epoch is beyond the compatibility scan.
            append_completed_epoch(2500, [2599, 2500])
            append_completed_epoch(2585, [2599, 2587, 2585])
            append_completed_epoch(
                2568, [2599, 2587, 2585, 2572, 2568]
            )
            persisted["command_history"] = history
            persisted["rollback_war_failure"] = _rollback_failure(
                checkpoint,
                target=2568,
                route=[2599, 2587, 2585, 2572, 2568],
                run_id=run_id,
            )
            persisted.pop("rollback_war_failures", None)
            write_json_atomic(state_path, persisted)

            restored_army = _army(
                1,
                province_id=2598,
                army_state="regular",
                route_province_ids=[],
            )
            endpoint = FakeEndpoint(pipe_name)
            driver = NativeHeadlessGameplayDriver(
                pipe_name,
                endpoint=endpoint,
                state_dir=state_dir,
                save_dir=checkpoint_path.parent,
            )
            endpoint.publish({**_hello("game.state.snapshot"), "pid": 150000})
            endpoint.publish(
                _snapshot(
                    1,
                    date_raw=int(checkpoint["date_raw"]),
                    played_character={"character_id": 707, "alive": True},
                    active_wars=[_war(61, allied_armies=[restored_army])],
                    player_armies=[restored_army],
                )
            )

            restored = driver.take_snapshot()
            failures = restored["native_rollback_war_failures"]
            self.assertEqual(
                [failure["target_province_id"] for failure in failures],
                [2568, 2585],
            )
            self.assertNotIn(
                2500,
                [failure["target_province_id"] for failure in failures],
            )
            self.assertEqual(restored["native_rollback_war_failure"], failures[0])
            on_disk = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(on_disk["rollback_war_failures"], failures)
            self.assertEqual(on_disk["rollback_war_failure"], failures[0])

            # Once factual history has been truncated, a separately
            # live-confirmed legacy route can still be seeded as an advisory
            # without inventing terminal diagnostics.  The reader preserves
            # it and evicts an overfull third entry.
            manually_seeded_older = {
                "status": "rolled_back_active_route",
                "source": "live-confirmed legacy reconstruction",
                "episode_run_id": run_id,
                "checkpoint_sha256": checkpoint["sha256"],
                "checkpoint_date_raw": checkpoint["date_raw"],
                "war_id": 61,
                "army_id": 1,
                "restored_origin_province_id": 2598,
                "target_province_id": 2585,
                "route_origin_province_id": 2598,
                "route_province_ids": [2599, 2587, 2585],
                "restored_date_raw": checkpoint["date_raw"],
            }
            on_disk["rollback_war_failures"] = [
                failures[0],
                manually_seeded_older,
                _rollback_failure(
                    checkpoint,
                    target=2500,
                    route=[2599, 2500],
                    run_id=run_id,
                ),
            ]
            write_json_atomic(state_path, on_disk)

            resumed_endpoint = FakeEndpoint(pipe_name)
            resumed = NativeHeadlessGameplayDriver(
                pipe_name,
                endpoint=resumed_endpoint,
                state_dir=state_dir,
                save_dir=checkpoint_path.parent,
            )
            resumed_endpoint.publish(
                {**_hello("game.state.snapshot"), "pid": 150000}
            )
            resumed_endpoint.publish(
                _snapshot(
                    2,
                    date_raw=int(checkpoint["date_raw"]),
                    played_character={"character_id": 707, "alive": True},
                    active_wars=[_war(61, allied_armies=[restored_army])],
                    player_armies=[restored_army],
                )
            )
            resumed_failures = resumed.take_snapshot()[
                "native_rollback_war_failures"
            ]
            self.assertEqual(
                resumed_failures, [failures[0], manually_seeded_older]
            )
            self.assertNotIn(
                "terminal_failure_target_province_id", resumed_failures[1]
            )

    def test_managed_restore_transaction_recovers_after_new_pid_daemon_crash(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            pipe_name = r"\\.\pipe\xar_managed_restore_transaction"
            checkpoint_path, checkpoint = _write_driver_state_checkpoint_fixture(
                state_dir,
                pipe_name,
                bridge_pid=140760,
                character_id=707,
                run_id="native-707-managed-restore",
            )
            state_path = state_dir / "native-session" / "driver-state.json"
            persisted = json.loads(state_path.read_text(encoding="utf-8"))
            persisted["command_history"][8] = {
                "index": 9,
                "command": "preview-move-army-1-to-2",
                "ok": True,
                "result": {
                    "route_preview": {
                        "status": "available",
                        "army_id": 1,
                        "origin_province_id": 1,
                        "target_province_id": 2,
                        "route_province_ids": [3, 2],
                        "previewed_date_raw": checkpoint["date_raw"],
                    }
                },
            }
            active_army = _army(
                1,
                province_id=1,
                move_target_province_id=2,
                army_state="moving",
                route_province_ids=[3, 2],
            )
            persisted["command_history"][9] = {
                "index": 10,
                "command": "move-army-1-to-2",
                "ok": True,
                "result": {
                    "war_action": {
                        "status": "moving",
                        "army_id": 1,
                        "target_province_id": 2,
                        "submitted_date_raw": checkpoint["date_raw"],
                    },
                    "player_armies": [active_army],
                },
            }
            persisted["command_history"][10] = {
                "index": 11,
                "command": "life-advance",
                "ok": True,
                "result": {"player_armies": [active_army]},
            }
            older_failure = _rollback_failure(
                checkpoint,
                target=4,
                route=[5, 4],
                run_id="native-707-managed-restore",
                origin=1,
            )
            persisted["rollback_war_failure"] = older_failure
            persisted["rollback_war_failures"] = [older_failure]
            write_json_atomic(state_path, persisted)

            endpoint = FakeEndpoint(pipe_name)
            driver = NativeHeadlessGameplayDriver(
                pipe_name,
                endpoint=endpoint,
                state_dir=state_dir,
                save_dir=checkpoint_path.parent,
            )
            endpoint.publish(
                {**_hello("game.state.snapshot"), "pid": 140760}
            )
            with driver._driver_state_lock:
                driver._managed_restore_transaction = {
                    "status": "awaiting_checkpoint_rebind",
                    "request_id": "restore-crash-window",
                    "source_bridge_pid": 140760,
                    "checkpoint_sha256": checkpoint["sha256"],
                    "checkpoint_size": checkpoint["size"],
                    "checkpoint_date_raw": checkpoint["date_raw"],
                    "history_index": checkpoint["history_index"],
                    "episode_character_id": 707,
                    "episode_run_id": "native-707-managed-restore",
                }
            driver._persist_driver_state()

            # The managed CK3 replacement says hello, but the daemon dies
            # before a playable snapshot can bind and before execute_step can
            # append its final restore row.
            endpoint.publish(
                {**_hello("game.state.snapshot"), "pid": 150000}
            )
            interrupted = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(interrupted["bridge_pid"], 150000)
            self.assertEqual(len(interrupted["command_history"]), 11)
            self.assertEqual(
                interrupted["managed_restore_transaction"][
                    "replacement_bridge_pid"
                ],
                150000,
            )

            replacement_endpoint = FakeEndpoint(pipe_name)
            replacement = NativeHeadlessGameplayDriver(
                pipe_name,
                endpoint=replacement_endpoint,
                state_dir=state_dir,
                save_dir=checkpoint_path.parent,
            )
            replacement_endpoint.publish(
                {**_hello("game.state.snapshot"), "pid": 150000}
            )
            self.assertEqual(
                replacement.capabilities()["native_session_control"][
                    "episode_binding_state"
                ],
                "pending_cold_candidate",
            )
            restored_army = _army(
                1,
                province_id=1,
                army_state="regular",
                route_province_ids=[],
            )
            replacement_endpoint.publish(
                _snapshot(
                    1,
                    date_raw=int(checkpoint["date_raw"]),
                    played_character={"character_id": 707, "alive": True},
                    active_wars=[
                        _war(
                            61,
                            allied_armies=[restored_army],
                            war_objective_province_ids=[2, 4],
                        )
                    ],
                    player_armies=[restored_army],
                )
            )

            recovered = replacement.take_snapshot()
            self.assertEqual(
                [
                    row["command"]
                    for row in recovered["native_command_history"]
                ],
                ["life-advance"] * 7
                + ["save-checkpoint", "restore-checkpoint"],
            )
            self.assertEqual(
                recovered["native_command_history"][-1]["result"]["source"],
                "native-session-cold-start",
            )
            failure = recovered["native_rollback_war_failure"]
            self.assertEqual(failure["target_province_id"], 2)
            self.assertEqual(failure["route_province_ids"], [3, 2])
            self.assertEqual(
                recovered["native_rollback_war_failures"],
                [failure, older_failure],
            )
            finalized = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertIsNone(finalized["managed_restore_transaction"])
            self.assertEqual(len(finalized["command_history"]), 9)
            self.assertEqual(
                finalized["rollback_war_failures"],
                [failure, older_failure],
            )

    def test_cold_v2_migration_scans_only_two_completed_restore_epochs(
        self,
    ) -> None:
        for second_epoch, expected_target in (
            ("restored_origin_entry", 2568),
            ("arrived", None),
            ("terminal_without_entry", None),
        ):
            with self.subTest(second_epoch=second_epoch):
                with tempfile.TemporaryDirectory() as temporary:
                    state_dir = Path(temporary)
                    pipe_name = (
                        r"\\.\pipe\xar_v2_completed_restore_epochs_"
                        + second_epoch
                    )
                    checkpoint_path, checkpoint = (
                        _write_driver_state_checkpoint_fixture(
                            state_dir,
                            pipe_name,
                            bridge_pid=140760,
                            character_id=707,
                            run_id="native-707-v2-epoch-migration",
                        )
                    )
                    state_path = (
                        state_dir / "native-session" / "driver-state.json"
                    )
                    persisted = json.loads(
                        state_path.read_text(encoding="utf-8")
                    )
                    history = persisted["command_history"][:8]

                    def append(
                        command: str, result: dict[str, object]
                    ) -> None:
                        history.append(
                            {
                                "index": len(history) + 1,
                                "command": command,
                                "ok": True,
                                "result": result,
                            }
                        )

                    def fill_before(index: int) -> None:
                        while len(history) < index - 1:
                            append("life-advance", {})

                    def append_active_route(
                        target: int,
                        *,
                        origin: int = 2598,
                        route: list[int] | None = None,
                        date_raw: int | None = None,
                    ) -> None:
                        selected_route = route or [target]
                        selected_date = (
                            int(checkpoint["date_raw"])
                            if date_raw is None
                            else date_raw
                        )
                        append(
                            f"preview-move-army-1-to-{target}",
                            {
                                "route_preview": {
                                    "status": "available",
                                    "army_id": 1,
                                    "origin_province_id": origin,
                                    "target_province_id": target,
                                    "route_province_ids": selected_route,
                                    "previewed_date_raw": selected_date,
                                }
                            },
                        )
                        moving = _army(
                            1,
                            province_id=origin,
                            move_target_province_id=target,
                            army_state="moving",
                            route_province_ids=selected_route,
                        )
                        append(
                            f"move-army-1-to-{target}",
                            {
                                "war_action": {
                                    "status": "moving",
                                    "army_id": 1,
                                    "target_province_id": target,
                                    "submitted_date_raw": selected_date,
                                },
                                "player_armies": [moving],
                            },
                        )
                        append("life-advance", {"player_armies": [moving]})

                    def append_arrived_route(target: int) -> None:
                        append_active_route(target)
                        append(
                            f"move-army-1-to-{target}",
                            {
                                "war_action": {
                                    "status": "arrived",
                                    "army_id": 1,
                                    "target_province_id": target,
                                },
                                "player_armies": [
                                    _army(
                                        1,
                                        province_id=target,
                                        army_state="regular",
                                        route_province_ids=[],
                                    )
                                ],
                            },
                        )

                    # Oldest completed epoch is deliberately a tempting
                    # failure.  The compatibility path must never reach it.
                    fill_before(39)
                    append_active_route(2500)
                    fill_before(42)
                    append("restore-checkpoint", {"status": "restored"})

                    if second_epoch == "restored_origin_entry":
                        entry_route = [2599, 2587, 2585, 2572, 2568]
                        terminal_route = [
                            8759,
                            2602,
                            2591,
                            2589,
                            2579,
                            2574,
                            2572,
                            2568,
                        ]
                        # Mirrors the real legacy epoch: row 44 is the first
                        # successful move from the restored province, while
                        # the unresolved terminal move was previewed later
                        # from a mid-branch province.
                        append_active_route(2568, route=entry_route)
                        append_active_route(
                            2568,
                            origin=2604,
                            route=terminal_route,
                            date_raw=int(checkpoint["date_raw"]) + 1_296,
                        )
                    elif second_epoch == "terminal_without_entry":
                        append_active_route(
                            2568,
                            origin=2604,
                            route=[8759, 2602, 2591, 2589, 2568],
                            date_raw=int(checkpoint["date_raw"]) + 1_296,
                        )
                    else:
                        append_arrived_route(2602)
                    fill_before(87)
                    append("restore-checkpoint", {"status": "restored"})

                    # The newest completed epoch ended safely, matching the
                    # real legacy state immediately before restore row 132.
                    append_arrived_route(2604)
                    fill_before(132)
                    append("restore-checkpoint", {"status": "restored"})
                    self.assertEqual(len(history), 132)
                    persisted["command_history"] = history
                    if second_epoch == "restored_origin_entry":
                        # The old extractor persisted the terminal preview as
                        # the blocking route even though it originated after
                        # leaving the restored province.  New code rejects
                        # that shape and uses the bounded v2 migration scan.
                        persisted["rollback_war_failure"] = {
                            "status": "rolled_back_active_route",
                            "episode_run_id": (
                                "native-707-v2-epoch-migration"
                            ),
                            "checkpoint_sha256": checkpoint["sha256"],
                            "war_id": 61,
                            "army_id": 1,
                            "restored_origin_province_id": 2598,
                            "target_province_id": 2568,
                            "route_origin_province_id": 2604,
                            "route_province_ids": terminal_route,
                        }
                    else:
                        persisted.pop("rollback_war_failure", None)
                    write_json_atomic(state_path, persisted)

                    endpoint = FakeEndpoint(pipe_name)
                    driver = NativeHeadlessGameplayDriver(
                        pipe_name,
                        endpoint=endpoint,
                        state_dir=state_dir,
                        save_dir=checkpoint_path.parent,
                    )
                    endpoint.publish(
                        {**_hello("game.state.snapshot"), "pid": 150000}
                    )
                    restored_army = _army(
                        1,
                        province_id=2598,
                        army_state="regular",
                        route_province_ids=[],
                    )
                    endpoint.publish(
                        _snapshot(
                            1,
                            date_raw=int(checkpoint["date_raw"]),
                            played_character={
                                "character_id": 707,
                                "alive": True,
                            },
                            active_wars=[
                                _war(61, allied_armies=[restored_army])
                            ],
                            player_armies=[restored_army],
                        )
                    )

                    restored = driver.take_snapshot()
                    failure = restored["native_rollback_war_failure"]
                    if expected_target is None:
                        self.assertIsNone(failure)
                    else:
                        self.assertEqual(
                            failure["target_province_id"], expected_target
                        )
                        self.assertEqual(
                            failure["route_origin_province_id"], 2598
                        )
                        self.assertEqual(
                            failure["route_province_ids"], entry_route
                        )
                        self.assertEqual(
                            failure[
                                "terminal_failure_target_province_id"
                            ],
                            2568,
                        )
                        self.assertEqual(
                            failure[
                                "terminal_failure_route_origin_province_id"
                            ],
                            2604,
                        )
                        self.assertEqual(
                            failure[
                                "terminal_failure_route_province_ids"
                            ],
                            terminal_route,
                        )
                    self.assertEqual(
                        len(restored["native_command_history"]), 9
                    )

    def test_managed_restore_failure_disarms_transaction_before_pid_change(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            pipe_name = r"\\.\pipe\xar_managed_restore_failure"
            checkpoint_path, checkpoint = _write_driver_state_checkpoint_fixture(
                state_dir,
                pipe_name,
                bridge_pid=4242,
                character_id=707,
                run_id="native-707-restore-failure",
            )
            endpoint = FakeEndpoint(pipe_name)
            driver = NativeHeadlessGameplayDriver(
                pipe_name,
                endpoint=endpoint,
                state_dir=state_dir,
                save_dir=checkpoint_path.parent,
            )
            endpoint.publish(_hello("game.state.snapshot"))
            endpoint.publish(
                _snapshot(
                    20,
                    date_raw=int(checkpoint["date_raw"]) + 96,
                    played_character={"character_id": 707, "alive": True},
                )
            )
            with mock.patch.object(
                driver,
                "_wait_for_restore_response",
                side_effect=BridgeUnavailableError("fixture restore rejected"),
            ):
                with self.assertRaisesRegex(
                    BridgeUnavailableError, "fixture restore rejected"
                ):
                    driver.execute_step("restore-checkpoint")

            state_path = state_dir / "native-session" / "driver-state.json"
            failed = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertIsNone(failed["managed_restore_transaction"])
            self.assertEqual(
                failed["command_history"][-1]["command"],
                "restore-checkpoint",
            )
            self.assertFalse(failed["command_history"][-1]["ok"])

            replacement_endpoint = FakeEndpoint(pipe_name)
            replacement = NativeHeadlessGameplayDriver(
                pipe_name,
                endpoint=replacement_endpoint,
                state_dir=state_dir,
                save_dir=checkpoint_path.parent,
            )
            replacement_endpoint.publish(_hello("game.state.snapshot"))
            replacement_endpoint.publish(
                _snapshot(
                    21,
                    date_raw=int(checkpoint["date_raw"]) + 96,
                    played_character={"character_id": 707, "alive": True},
                )
            )
            resumed = replacement.take_snapshot()
            self.assertFalse(resumed["episode_identity_pending"])
            self.assertEqual(
                resumed["native_command_history"][-1]["command"],
                "restore-checkpoint",
            )
            self.assertEqual(
                replacement.capabilities()["native_session_control"][
                    "driver_state_restore_kind"
                ],
                "same_pid_hot",
            )

    def test_same_pid_hot_restart_disarms_marker_without_queue_request(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            pipe_name = r"\\.\pipe\xar_orphan_restore_marker"
            checkpoint_path, checkpoint = _write_driver_state_checkpoint_fixture(
                state_dir,
                pipe_name,
                bridge_pid=4242,
                character_id=707,
                run_id="native-707-orphan-marker",
            )
            state_path = state_dir / "native-session" / "driver-state.json"
            persisted = json.loads(state_path.read_text(encoding="utf-8"))
            persisted["managed_restore_transaction"] = {
                "status": "awaiting_checkpoint_rebind",
                "request_id": "restore-never-enqueued",
                "source_bridge_pid": 4242,
                "checkpoint_sha256": checkpoint["sha256"],
                "checkpoint_size": checkpoint["size"],
                "checkpoint_date_raw": checkpoint["date_raw"],
                "history_index": checkpoint["history_index"],
                "episode_character_id": 707,
                "episode_run_id": "native-707-orphan-marker",
            }
            write_json_atomic(state_path, persisted)

            endpoint = FakeEndpoint(pipe_name)
            driver = NativeHeadlessGameplayDriver(
                pipe_name,
                endpoint=endpoint,
                state_dir=state_dir,
                save_dir=checkpoint_path.parent,
            )
            endpoint.publish(_hello("game.state.snapshot"))
            endpoint.publish(
                _snapshot(
                    1,
                    date_raw=int(checkpoint["date_raw"]) + 96,
                    played_character={"character_id": 707, "alive": True},
                )
            )

            resumed = driver.take_snapshot()
            self.assertFalse(resumed["episode_identity_pending"])
            self.assertEqual(
                driver.capabilities()["native_session_control"][
                    "driver_state_restore_kind"
                ],
                "same_pid_hot",
            )
            self.assertIsNone(
                json.loads(state_path.read_text(encoding="utf-8"))[
                    "managed_restore_transaction"
                ]
            )

    def test_cold_checkpoint_mismatch_starts_nonterminal_new_episode(self) -> None:
        cases = (
            ("played_character", 909, 53_168_784, False),
            ("date", 707, 53_168_785, False),
            ("sha256", 707, 53_168_784, True),
        )
        for name, character_id, date_raw, mutate_bytes in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                state_dir = Path(temporary)
                pipe_name = rf"\\.\pipe\xar_cold_mismatch_{name}"
                checkpoint_path, _checkpoint = (
                    _write_driver_state_checkpoint_fixture(state_dir, pipe_name)
                )
                if mutate_bytes:
                    checkpoint_path.write_bytes(b"cold-checkpoint-fixturf")
                endpoint = FakeEndpoint(pipe_name)
                driver = NativeHeadlessGameplayDriver(
                    pipe_name,
                    endpoint=endpoint,
                    state_dir=state_dir,
                    save_dir=checkpoint_path.parent,
                )
                endpoint.publish({**_hello("game.state.snapshot"), "pid": 2222})
                endpoint.publish(
                    _snapshot(
                        1,
                        date_raw=date_raw,
                        played_character={
                            "character_id": character_id,
                            "alive": True,
                        },
                    )
                )

                current = driver.take_snapshot()
                self.assertEqual(current["episode_character_id"], character_id)
                self.assertNotEqual(
                    current["episode_run_id"], "native-707-existing"
                )
                self.assertEqual(current["native_command_history"], [])
                self.assertFalse(current["one_life_terminal"])
                control = driver.capabilities()["native_session_control"]
                self.assertFalse(control["driver_state_restored"])
                self.assertEqual(control["driver_state_restore_kind"], "new_episode")
                self.assertEqual(control["episode_binding_state"], "active_new")

    def test_event_wildcard_expands_from_current_option_count(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.active-event",
                "game.command.select-event-option-N",
            )
        )
        endpoint.publish(
            _snapshot(23, active_event={"instance_id": 419, "option_count": 3})
        )

        capabilities = driver.capabilities()
        self.assertEqual(
            capabilities["action_steps"],
            [
                "select-event-option-1",
                "select-event-option-2",
                "select-event-option-3",
            ],
        )
        self.assertNotIn("select-event-option-N", capabilities["action_steps"])
        snapshot = driver.take_snapshot()
        self.assertEqual(snapshot["active_event"]["instance_id"], 419)
        self.assertEqual(snapshot["active_event"]["options"][2]["index"], 2)

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") == "execute_step":
                endpoint.publish(
                    {
                        "type": "command_result",
                        "protocol_version": 1,
                        "request_id": frame["request_id"],
                        "ok": True,
                        "result": {"accepted": True},
                    }
                )
                endpoint.publish(_snapshot(24))

        endpoint.send_hook = answer
        result = driver.execute_step(
            "select-event-option-3",
            expected_revision=int(snapshot["revision"]),
        )
        command = next(
            frame
            for frame in reversed(endpoint.frames)
            if frame.get("type") == "execute_step"
        )
        self.assertEqual(command["step"], "select-event-option-3")
        self.assertEqual(command["expected_revision"], 23)
        self.assertEqual(
            result["event_selection"]["status"], "event_instance_advanced"
        )
        self.assertEqual(
            result["event_selection"]["old_event_instance_id"], 419
        )
        self.assertIsNone(
            result["event_selection"]["new_event_instance_id"]
        )
        self.assertEqual(
            result["event_selection"]["selected_native_option_index"], 2
        )
        self.assertEqual(result["progress_status"], "postcondition")

    def test_event_selection_accepts_a_chained_new_full_instance(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=0.1,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.active-event",
                "game.command.select-event-option-N",
            )
        )
        endpoint.publish(
            _snapshot(31, active_event={"instance_id": 500, "option_count": 2})
        )
        starting = driver.take_snapshot()

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {"accepted": True},
                }
            )
            endpoint.publish(
                _snapshot(
                    32,
                    active_event={"instance_id": 501, "option_count": 1},
                )
            )

        endpoint.send_hook = answer
        result = driver.execute_step(
            "select-event-option-2",
            expected_revision=int(starting["revision"]),
        )

        self.assertEqual(
            result["event_selection"]["new_event_instance_id"], 501
        )
        self.assertEqual(result["active_event"]["instance_id"], 501)

    def test_event_selection_rejects_ack_without_instance_progress(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=0.02,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.active-event",
                "game.command.select-event-option-N",
            )
        )
        endpoint.publish(
            _snapshot(41, active_event={"instance_id": 600, "option_count": 2})
        )
        starting = driver.take_snapshot()

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") == "execute_step":
                endpoint.publish(
                    {
                        "type": "command_result",
                        "protocol_version": 1,
                        "request_id": frame["request_id"],
                        "ok": True,
                        "result": {"accepted": True},
                    }
                )

        endpoint.send_hook = answer
        with self.assertRaisesRegex(
            BridgeUnavailableError, "ACK did not advance"
        ):
            driver.execute_step(
                "select-event-option-1",
                expected_revision=int(starting["revision"]),
            )

    def test_event_selection_preflight_rejects_without_sending(self) -> None:
        for label, snapshot, step, stale_revision in (
            (
                "unpaused",
                _snapshot(
                    51,
                    paused=False,
                    active_event={"instance_id": 700, "option_count": 2},
                ),
                "select-event-option-1",
                False,
            ),
            ("no-event", _snapshot(52), "select-event-option-1", False),
            (
                "out-of-range",
                _snapshot(
                    53,
                    active_event={"instance_id": 701, "option_count": 1},
                ),
                "select-event-option-2",
                False,
            ),
            (
                "stale-revision",
                _snapshot(
                    54,
                    active_event={"instance_id": 702, "option_count": 1},
                ),
                "select-event-option-1",
                True,
            ),
        ):
            with self.subTest(label=label):
                endpoint = FakeEndpoint()
                driver = NativeHeadlessGameplayDriver(
                    endpoint.pipe_name,
                    endpoint=endpoint,
                    command_timeout_seconds=0.02,
                )
                endpoint.publish(
                    _hello(
                        "game.state.snapshot",
                        "game.state.active-event",
                        "game.command.select-event-option-N",
                    )
                )
                endpoint.publish(snapshot)
                current_revision = int(driver.take_snapshot()["revision"])
                with self.assertRaises(BridgeUnavailableError):
                    driver.execute_step(
                        step,
                        expected_revision=(
                            current_revision - 1
                            if stale_revision
                            else current_revision
                        ),
                    )
                self.assertFalse(
                    any(
                        frame.get("type") == "execute_step"
                        for frame in endpoint.frames
                    )
                )

    def test_pending_character_interaction_routes_native_reply(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.pending-character-interaction",
                "game.command.accept-pending-character-interaction",
                "game.command.reject-pending-character-interaction",
                "game.command.acknowledge-pending-character-interaction",
            )
        )
        endpoint.publish(
            _snapshot(
                27,
                pending_character_interaction={
                    "instance_id": _SIGNED_PENDING_ID,
                    "sender_character_id": 4_294_967,
                    "auto_accept_notification": False,
                },
            )
        )
        snapshot = driver.take_snapshot()
        self.assertEqual(
            snapshot["pending_character_interaction"]["instance_id"],
            _SIGNED_PENDING_ID,
        )
        self.assertEqual(
            driver.capabilities()["action_steps"],
            [
                "accept-pending-character-interaction",
                "reject-pending-character-interaction",
            ],
        )

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") == "execute_step":
                endpoint.publish(
                    {
                        "type": "command_result",
                        "protocol_version": 1,
                        "request_id": frame["request_id"],
                        "ok": True,
                        "result": {"step": frame["step"], "status": "submitted"},
                    }
                )
                endpoint.publish(_snapshot(28))

        endpoint.send_hook = answer
        result = driver.execute_step(
            "accept-pending-character-interaction",
            expected_revision=int(snapshot["revision"]),
        )
        self.assertEqual(result["status"], "submitted")
        command = next(
            frame
            for frame in reversed(endpoint.frames)
            if frame.get("type") == "execute_step"
        )
        self.assertEqual(
            command["step"], "accept-pending-character-interaction"
        )
        self.assertEqual(command["expected_revision"], 27)
        endpoint.publish(
            _snapshot(
                29,
                pending_character_interaction={
                    "instance_id": _SIGNED_NOTIFICATION_ID,
                    "sender_character_id": 4_294_968,
                    "auto_accept_notification": True,
                },
            )
        )
        notification_snapshot = driver.take_snapshot()
        self.assertEqual(
            driver.capabilities()["action_steps"],
            ["acknowledge-pending-character-interaction"],
        )

        def answer_ack(frame: dict[str, object]) -> None:
            if frame.get("type") == "execute_step":
                endpoint.publish(
                    {
                        "type": "command_result",
                        "protocol_version": 1,
                        "request_id": frame["request_id"],
                        "ok": True,
                        "result": {
                            "step": frame["step"],
                            "status": "submitted",
                        },
                    }
                )
                endpoint.publish(_snapshot(30))

        endpoint.send_hook = answer_ack
        acknowledged = driver.execute_step(
            "acknowledge-pending-character-interaction",
            expected_revision=int(notification_snapshot["revision"]),
        )
        self.assertEqual(
            acknowledged["interaction_result"]["status"], "acknowledged"
        )
        self.assertIsNone(
            acknowledged["remaining_pending_character_interaction"]
        )
        ack_command = next(
            frame
            for frame in reversed(endpoint.frames)
            if frame.get("type") == "execute_step"
        )
        self.assertEqual(
            ack_command["step"],
            "acknowledge-pending-character-interaction",
        )
        self.assertEqual(ack_command["expected_revision"], 29)
        self.assertEqual(
            ack_command["pending_interaction_id"], _SIGNED_NOTIFICATION_ID
        )

        endpoint.publish(
            _snapshot(
                31,
                pending_character_interaction={
                    "instance_id": _SIGNED_SERVICE_NOTIFICATION_ID,
                    "sender_character_id": 13,
                    "auto_accept_notification": True,
                },
            )
        )

        def answer_service_ack(frame: dict[str, object]) -> None:
            if frame.get("type") == "execute_step":
                endpoint.publish(
                    {
                        "type": "command_result",
                        "protocol_version": 1,
                        "request_id": frame["request_id"],
                        "ok": True,
                        "result": {
                            "step": frame["step"],
                            "status": "submitted",
                        },
                    }
                )
                endpoint.publish(_snapshot(32))

        endpoint.send_hook = answer_service_ack
        service = GameplayBridgeService(driver)
        service_ack = service.acknowledge_pending_character_interaction(
            interaction_instance_id=_SIGNED_SERVICE_NOTIFICATION_ID
        )
        self.assertTrue(service_ack["acknowledged"])
        self.assertEqual(
            service_ack["interaction_instance_id"],
            _SIGNED_SERVICE_NOTIFICATION_ID,
        )
        service_ack_command = next(
            frame
            for frame in reversed(endpoint.frames)
            if frame.get("type") == "execute_step"
        )
        self.assertEqual(
            service_ack_command["pending_interaction_id"],
            _SIGNED_SERVICE_NOTIFICATION_ID,
        )

    def test_pending_notification_queue_ack_is_not_postcondition(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=0.01,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.pending-character-interaction",
                "game.command.acknowledge-pending-character-interaction",
            )
        )
        endpoint.publish(
            _snapshot(
                33,
                pending_character_interaction={
                    "instance_id": 0x01000031,
                    "sender_character_id": 81,
                    "auto_accept_notification": True,
                },
            )
        )

        def answer_queue_only(frame: dict[str, object]) -> None:
            if frame.get("type") == "execute_step":
                endpoint.publish(
                    {
                        "type": "command_result",
                        "protocol_version": 1,
                        "request_id": frame["request_id"],
                        "ok": True,
                        "result": {
                            "step": frame["step"],
                            "status": "submitted",
                        },
                    }
                )

        endpoint.send_hook = answer_queue_only
        with self.assertRaisesRegex(
            BridgeUnavailableError,
            "did not advance the pending request",
        ):
            driver.execute_step("acknowledge-pending-character-interaction")

    def test_episode_identity_locks_on_first_ready_character_and_keeps_heir_info(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello("game.state.snapshot", "game.state.played-character")
        )
        endpoint.publish(
            _snapshot(
                28,
                map_ready=False,
                played_character={"character_id": 707, "alive": True},
            )
        )
        self.assertIsNone(driver.take_snapshot()["episode_character_id"])

        endpoint.publish(
            _snapshot(
                29,
                played_character={
                    "character_id": 707,
                    "alive": True,
                    "primary_heir_id": 808,
                    "has_heir": True,
                },
            )
        )
        first_ready = driver.take_snapshot()
        self.assertEqual(first_ready["episode_character_id"], 707)
        self.assertFalse(first_ready["one_life_terminal"])
        self.assertIsNone(first_ready["one_life_terminal_reason"])
        self.assertEqual(first_ready["played_character"]["primary_heir_id"], 808)
        self.assertTrue(first_ready["played_character"]["has_heir"])

        endpoint.publish(
            _snapshot(
                30,
                played_character={
                    "character_id": 707,
                    "alive": True,
                    "primary_heir_id": None,
                    "has_heir": False,
                },
            )
        )
        same_character = driver.take_snapshot()
        capabilities = driver.capabilities()
        self.assertEqual(same_character["episode_character_id"], 707)
        self.assertFalse(same_character["one_life_terminal"])
        self.assertEqual(capabilities["episode_character_id"], 707)
        self.assertFalse(capabilities["one_life_terminal"])
        self.assertNotIn("death-terminal", capabilities["action_steps"])

    def test_played_character_relationship_state_is_preserved(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello("game.state.snapshot", "game.state.played-character")
        )
        endpoint.publish(
            _snapshot(
                31,
                played_character={
                    "character_id": 707,
                    "alive": True,
                    "betrothed_id": None,
                    "primary_spouse_id": 808,
                    "spouse_ids": [808, 809],
                },
            )
        )

        played = driver.take_snapshot()["played_character"]
        self.assertIsNone(played["betrothed_id"])
        self.assertEqual(played["primary_spouse_id"], 808)
        self.assertEqual(played["spouse_ids"], [808, 809])

    def test_map_ready_without_played_character_does_not_invent_terminal(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello("game.state.snapshot", "game.state.played-character")
        )
        endpoint.publish(_snapshot(29, played_character=None))

        snapshot = driver.take_snapshot()
        capabilities = driver.capabilities()

        self.assertIsNone(snapshot["episode_character_id"])
        self.assertFalse(snapshot["one_life_terminal"])
        self.assertIsNone(snapshot["one_life_terminal_reason"])
        self.assertIsNone(capabilities["episode_character_id"])
        self.assertNotIn("death-terminal", capabilities["action_steps"])

    def test_dead_played_character_exposes_one_life_terminal(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello("game.state.snapshot", "game.state.played-character")
        )
        endpoint.publish(
            _snapshot(
                30,
                played_character={"character_id": 17_031, "alive": False},
            )
        )
        snapshot = driver.take_snapshot()

        self.assertIn("death-terminal", driver.capabilities()["action_steps"])
        result = driver.execute_step(
            "death-terminal", expected_revision=int(snapshot["revision"])
        )

        self.assertTrue(result["terminal"])
        self.assertEqual(result["terminal_kind"], "native_played_character_dead")
        self.assertEqual(result["terminal_reason"], "played_character_dead")
        self.assertEqual(result["episode_character_id"], 17_031)
        self.assertFalse(result["continue_as_heir_after_death"])
        self.assertEqual(result["heir_gameplay_actions"], 0)
        self.assertEqual(
            result["settlement_status"], "settlement_unavailable"
        )
        self.assertTrue(result["settlement_unavailable"])
        self.assertEqual(result["played_character"]["character_id"], 17_031)

    def test_terminal_waits_for_matching_native_settlement(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            settlement_timeout_seconds=0.5,
            settlement_poll_interval_seconds=0.01,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.played-character",
                ONE_LIFE_SETTLEMENT_CAPABILITY,
            )
        )
        endpoint.publish(
            _snapshot(
                30,
                played_character={"character_id": 707, "alive": False},
                one_life_settlement={"ready": False, "commit_serial": 0},
            )
        )
        starting = driver.take_snapshot()
        self.assertEqual(starting["one_life_settlement_status"], "pending")

        publisher = threading.Timer(
            0.02,
            lambda: endpoint.publish(
                _snapshot(
                    31,
                    played_character={"character_id": 707, "alive": False},
                    one_life_settlement=_one_life_settlement(),
                )
            ),
        )
        publisher.start()
        try:
            result = driver.execute_step(
                "death-terminal",
                expected_revision=int(starting["revision"]),
            )
        finally:
            publisher.join(timeout=1.0)

        self.assertEqual(result["settlement_status"], "complete")
        self.assertFalse(result["settlement_unavailable"])
        self.assertEqual(result["score"], 405.25)
        self.assertEqual(
            result["one_life_settlement"]["source_character_id"], 707
        )
        self.assertEqual(
            result["record_persistence"]["status"],
            "not_required_no_new_record",
        )
        self.assertFalse(result["continue_as_heir_after_death"])
        self.assertEqual(result["heir_gameplay_actions"], 0)

    def test_terminal_waits_for_new_record_tutorial_bit_to_stabilize(self) -> None:
        endpoint = FakeEndpoint()
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            profile_dir = state_dir / "profile"
            profile_dir.mkdir()
            tutorial_path = profile_dir / "tutorial.txt"
            tutorial_path.write_text(
                'last_lesson_chain="reactive_advice"\ncompleted_lessons={\n}\n',
                encoding="utf-8",
            )
            driver = NativeHeadlessGameplayDriver(
                endpoint.pipe_name,
                endpoint=endpoint,
                state_dir=state_dir,
                settlement_timeout_seconds=0.5,
                settlement_poll_interval_seconds=0.01,
            )
            endpoint.publish(
                _hello(
                    "game.state.snapshot",
                    "game.state.played-character",
                    ONE_LIFE_SETTLEMENT_CAPABILITY,
                )
            )
            endpoint.publish(
                _snapshot(
                    30,
                    played_character={"character_id": 707, "alive": False},
                    one_life_settlement=_one_life_settlement(
                        old_record=400,
                        record_delta=5,
                        record_written=True,
                    ),
                )
            )
            starting = driver.take_snapshot()
            writer = threading.Timer(
                0.02,
                lambda: tutorial_path.write_text(
                    'last_lesson_chain="reactive_advice"\n'
                    "completed_lessons={\n\txar_hs_ge_405\n}\n",
                    encoding="utf-8",
                ),
            )
            writer.start()
            try:
                result = driver.execute_step(
                    "death-terminal",
                    expected_revision=int(starting["revision"]),
                )
            finally:
                writer.join(timeout=1.0)

        persistence = result["record_persistence"]
        self.assertEqual(persistence["status"], "persisted")
        self.assertEqual(persistence["lesson_id"], "xar_hs_ge_405")
        self.assertGreaterEqual(persistence["stable_observations"], 2)
        self.assertEqual(
            result["cross_run_strategy"]["recorded_episode"]["score"],
            405.25,
        )

    def test_terminal_rejects_settlement_for_the_heir(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            settlement_timeout_seconds=0.03,
            settlement_poll_interval_seconds=0.005,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.played-character",
                ONE_LIFE_SETTLEMENT_CAPABILITY,
            )
        )
        endpoint.publish(
            _snapshot(
                31,
                played_character={"character_id": 707, "alive": True},
                one_life_settlement={"ready": False, "commit_serial": 0},
            )
        )
        self.assertEqual(driver.take_snapshot()["episode_character_id"], 707)
        endpoint.publish(
            _snapshot(
                32,
                played_character={"character_id": 808, "alive": True},
                one_life_settlement=_one_life_settlement(
                    source_character_id=808
                ),
            )
        )
        switched = driver.take_snapshot()
        self.assertEqual(
            switched["one_life_settlement_status"], "source_mismatch"
        )

        with self.assertRaisesRegex(
            BridgeUnavailableError, "CharacterID 707"
        ):
            driver.execute_step(
                "death-terminal",
                expected_revision=int(switched["revision"]),
            )

    def test_no_heir_missing_player_is_terminal_when_settlement_matches(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.played-character",
                ONE_LIFE_SETTLEMENT_CAPABILITY,
            )
        )
        endpoint.publish(
            _snapshot(
                31,
                played_character={"character_id": 707, "alive": True},
                one_life_settlement={"ready": False, "commit_serial": 0},
            )
        )
        self.assertEqual(driver.take_snapshot()["episode_character_id"], 707)
        endpoint.publish(
            _snapshot(
                32,
                played_character=None,
                one_life_settlement=_one_life_settlement(),
            )
        )

        terminal = driver.take_snapshot()
        result = driver.execute_step(
            "death-terminal", expected_revision=int(terminal["revision"])
        )

        self.assertEqual(
            terminal["one_life_terminal_reason"], "played_character_missing"
        )
        self.assertEqual(
            result["terminal_kind"], "native_played_character_missing"
        )
        self.assertEqual(result["score"], 405.25)
        self.assertEqual(result["heir_gameplay_actions"], 0)

    def test_native_death_terminal_records_cross_run_strategy(self) -> None:
        endpoint = FakeEndpoint()
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            driver = NativeHeadlessGameplayDriver(
                endpoint.pipe_name,
                endpoint=endpoint,
                state_dir=state_dir,
            )
            endpoint.publish(
                _hello(
                    "game.state.snapshot",
                    "game.state.played-character",
                    ONE_LIFE_SETTLEMENT_CAPABILITY,
                )
            )
            endpoint.publish(
                _snapshot(
                    30,
                    played_character={"character_id": 17_031, "alive": False},
                    one_life_settlement=_one_life_settlement(
                        source_character_id=17_031
                    ),
                )
            )
            snapshot = driver.take_snapshot()

            result = driver.execute_step(
                "death-terminal", expected_revision=int(snapshot["revision"])
            )

            history = result["cross_run_strategy"]
            episode = history["recorded_episode"]
            self.assertEqual(episode["run_id"], snapshot["episode_run_id"])
            self.assertEqual(episode["terminal_reason"], "played_character_dead")
            self.assertFalse(episode["continue_as_heir_after_death"])
            self.assertEqual(episode["heir_gameplay_actions"], 0)
            self.assertIn("death-terminal", episode["successful_steps"])
            persisted = json.loads(
                (state_dir / "strategy" / "one-life-history.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(len(persisted["episodes"]), 1)
            self.assertEqual(
                persisted["episodes"][0]["run_id"], snapshot["episode_run_id"]
            )

    def test_unavailable_terminal_retries_after_capability_appears(self) -> None:
        endpoint = FakeEndpoint()
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            driver = NativeHeadlessGameplayDriver(
                endpoint.pipe_name,
                endpoint=endpoint,
                state_dir=state_dir,
            )
            endpoint.publish(
                _hello("game.state.snapshot", "game.state.played-character")
            )
            endpoint.publish(
                _snapshot(
                    31,
                    played_character={"character_id": 707, "alive": True},
                )
            )
            driver.take_snapshot()
            endpoint.publish(
                _snapshot(
                    32,
                    played_character={"character_id": 808, "alive": True},
                )
            )
            service = GameplayBridgeService(driver)

            unavailable = service.auto_turn()
            blocked = service.auto_turn()

            self.assertEqual(
                unavailable["result"]["settlement_status"],
                "settlement_unavailable",
            )
            self.assertEqual(blocked["status"], "blocked")
            self.assertEqual(
                blocked["plan"]["phase"],
                "terminal_settlement_unavailable",
            )
            self.assertFalse(
                (state_dir / "strategy" / "one-life-history.json").exists()
            )

            endpoint.publish(
                _hello(
                    "game.state.snapshot",
                    "game.state.played-character",
                    ONE_LIFE_SETTLEMENT_CAPABILITY,
                )
            )
            endpoint.publish(
                _snapshot(
                    33,
                    played_character={"character_id": 808, "alive": True},
                    one_life_settlement=_one_life_settlement(),
                )
            )
            completed = service.auto_turn()

            self.assertEqual(completed["status"], "executed")
            self.assertEqual(completed["result"]["score"], 405.25)
            persisted = json.loads(
                (state_dir / "strategy" / "one-life-history.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(len(persisted["episodes"]), 1)
            self.assertEqual(persisted["episodes"][0]["score"], 405.25)

    def test_hybrid_uses_data_mod_settlement_without_visual_action(self) -> None:
        endpoint = FakeEndpoint()
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            native = NativeHeadlessGameplayDriver(
                endpoint.pipe_name,
                endpoint=endpoint,
                state_dir=state_dir,
            )
            endpoint.publish(
                _hello("game.state.snapshot", "game.state.played-character")
            )
            endpoint.publish(
                _snapshot(
                    31,
                    played_character={"character_id": 707, "alive": True},
                )
            )
            native.take_snapshot()
            endpoint.publish(
                _snapshot(
                    32,
                    played_character={"character_id": 808, "alive": True},
                )
            )
            native_terminal = native.take_snapshot()
            unavailable = native.execute_step(
                "death-terminal",
                expected_revision=int(native_terminal["revision"]),
            )
            self.assertEqual(
                unavailable["settlement_status"], "settlement_unavailable"
            )
            self.assertFalse(
                (state_dir / "strategy" / "one-life-history.json").exists()
            )

            data_mod = mock.Mock()
            data_mod.capabilities.return_value = {
                "snapshot": True,
                "wait_for_change": True,
                "action_steps": [],
                "bridge_capabilities": [
                    "game.state.snapshot",
                    ONE_LIFE_SETTLEMENT_CAPABILITY,
                ],
            }
            data_mod.take_snapshot.return_value = {
                "format_version": 1,
                "snapshot_id": "data-mod:33",
                "revision": 33,
                "backend_id": "data-mod",
                "history": [{"command": "settlement-projection", "ok": True}],
                "one_life_settlement": _one_life_settlement(),
            }
            visual = mock.Mock()
            visual.capabilities.return_value = {
                "snapshot": True,
                "wait_for_change": True,
                "action_steps": ["death-terminal"],
                "bridge_capabilities": [],
            }
            hybrid = ConfiguredHybridFallbackDriver(native, data_mod, visual)
            service = GameplayBridgeService(hybrid)

            projected = service.one_life_settlement()
            retry_plan = service.plan_turn()["plan"]
            completed_turn = service.auto_turn()
            completed = completed_turn["result"]
            stopped = service.auto_turn()

            self.assertEqual(projected["status"], "ready")
            self.assertEqual(retry_plan["phase"], "terminal_native")
            self.assertEqual(completed_turn["status"], "executed")
            self.assertEqual(completed["score"], 405.25)
            self.assertEqual(completed["backend_id"], "hybrid-fallback")
            self.assertEqual(
                completed["settlement_projection_backend"], "data-mod"
            )
            self.assertEqual(stopped["status"], "terminal")
            data_mod.execute_step.assert_not_called()
            visual.execute_step.assert_not_called()
            persisted = json.loads(
                (state_dir / "strategy" / "one-life-history.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(len(persisted["episodes"]), 1)
            self.assertEqual(persisted["episodes"][0]["score"], 405.25)

    def test_played_character_switch_ends_episode_before_heir_gameplay(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.played-character",
                ONE_LIFE_SETTLEMENT_CAPABILITY,
            )
        )
        endpoint.publish(
            _snapshot(
                31,
                played_character={
                    "character_id": 707,
                    "alive": True,
                    "primary_heir_id": 808,
                    "has_heir": True,
                },
                one_life_settlement={"ready": False, "commit_serial": 0},
            )
        )
        self.assertEqual(driver.take_snapshot()["episode_character_id"], 707)
        endpoint.publish(
            _snapshot(
                32,
                played_character={"character_id": 808, "alive": True},
                one_life_settlement=_one_life_settlement(),
            )
        )

        switched = driver.take_snapshot()
        capabilities = driver.capabilities()
        service = GameplayBridgeService(driver)
        plan = service.plan_turn()["plan"]
        result = service.auto_turn()

        self.assertEqual(switched["episode_character_id"], 707)
        self.assertTrue(switched["one_life_terminal"])
        self.assertEqual(
            switched["one_life_terminal_reason"], "played_character_changed"
        )
        self.assertIn("death-terminal", capabilities["action_steps"])
        self.assertEqual(plan["phase"], "terminal_native")
        self.assertEqual(plan["selected_step"], "death-terminal")
        self.assertEqual(plan["episode_character_id"], 707)
        self.assertEqual(plan["terminal_reason"], "played_character_changed")
        self.assertEqual(result["status"], "executed")
        self.assertEqual(
            result["result"]["terminal_kind"],
            "native_played_character_changed",
        )
        self.assertEqual(result["result"]["episode_character_id"], 707)
        self.assertFalse(result["result"]["continue_as_heir_after_death"])
        completed_plan = service.plan_turn()["plan"]
        completed_turn = service.auto_turn()
        self.assertEqual(completed_plan["phase"], "terminal_complete")
        self.assertIsNone(completed_plan["selected_step"])
        self.assertEqual(completed_plan["heir_gameplay_actions"], 0)
        self.assertEqual(completed_turn["status"], "terminal")

    def test_split_army_half_expands_and_returns_queue_only_receipt(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=0.01,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.command.split-army-half-N",
            )
        )
        source = _army(101, province_id=11)
        second = _army(303, province_id=12)
        foreign = _army(202, province_id=13, controllable=False)
        endpoint.publish(
            _snapshot(
                40,
                date_raw=53_171_400,
                player_armies=[source, foreign, second],
            )
        )
        service = GameplayBridgeService(driver)

        self.assertEqual(
            driver.capabilities()["action_steps"],
            ["split-army-half-101", "split-army-half-303"],
        )
        planned_step = service.plan_turn()["plan"].get("selected_step")
        self.assertFalse(
            isinstance(planned_step, str)
            and planned_step.startswith("split-army-half-")
        )

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {
                        "step": frame["step"],
                        "accepted": True,
                        "status": "split_submitted",
                    },
                }
            )

        endpoint.send_hook = answer
        result = service.execute_step(
            "split-army-half-101",
            expected_revision=int(driver.take_snapshot()["revision"]),
        )

        self.assertEqual(
            result["war_action"],
            {
                "status": "split_submitted",
                "source_army_id": 101,
                "submitted_date_raw": 53_171_400,
                "player_army_ids_before": [101, 303],
            },
        )
        self.assertNotIn("sibling_army_id", result["war_action"])
        self.assertNotIn("player_armies", result)
        self.assertEqual(
            [
                frame["step"]
                for frame in endpoint.frames
                if frame.get("type") == "execute_step"
            ],
            ["split-army-half-101"],
        )
        self.assertEqual(
            sorted(
                int(army["army_id"])
                for army in driver.take_snapshot()["player_armies"]
                if army.get("controllable") is True
            ),
            [101, 303],
        )

    def test_split_army_half_projects_one_immediate_sibling(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=0.01,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.command.split-army-half-N",
            )
        )
        source = _army(83886341, province_id=2585)
        endpoint.publish(
            _snapshot(40, date_raw=53_171_400, player_armies=[source])
        )

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {
                        "step": frame["step"],
                        "accepted": True,
                        "status": "split_submitted",
                    },
                }
            )
            sibling = _army(83886342, province_id=2585)
            endpoint.publish(
                _snapshot(
                    41,
                    date_raw=53_171_400,
                    player_armies=[source, sibling],
                )
            )

        endpoint.send_hook = answer
        result = GameplayBridgeService(driver).execute_step(
            "split-army-half-83886341"
        )

        self.assertEqual(
            result["war_action"],
            {
                "status": "split_applied",
                "source_army_id": 83886341,
                "submitted_date_raw": 53_171_400,
                "player_army_ids_before": [83886341],
                "sibling_army_id": 83886342,
            },
        )

    def test_split_army_half_does_not_guess_between_immediate_additions(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.command.split-army-half-N",
            )
        )
        source = _army(101, province_id=2585)
        endpoint.publish(
            _snapshot(40, date_raw=53_171_400, player_armies=[source])
        )

        def submit_without_identity_proof(
            _step: str, *, expected_revision: int | None
        ) -> dict[str, object]:
            self.assertEqual(expected_revision, 2)
            endpoint.publish(
                _snapshot(
                    41,
                    date_raw=53_171_400,
                    player_armies=[
                        source,
                        _army(102, province_id=2585),
                        _army(103, province_id=2585),
                    ],
                )
            )
            return {"status": "split_submitted"}

        with mock.patch.object(
            driver,
            "_execute_primitive_step",
            side_effect=submit_without_identity_proof,
        ):
            result = driver._execute_native_war_step(
                "split-army-half-101", expected_revision=None
            )

        self.assertEqual(result["war_action"]["status"], "split_submitted")
        self.assertNotIn("sibling_army_id", result["war_action"])

    def test_merge_armies_expands_ordered_pairs_and_returns_queue_receipt(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.command.merge-armies-N-with-N",
            )
        )
        destination = _army(
            101,
            province_id=11,
            army_state="moving",
            in_combat=False,
            retreating=False,
        )
        source = _army(303, province_id=11)
        endpoint.publish(
            _snapshot(
                40,
                date_raw=53_171_400,
                player_armies=[
                    destination,
                    source,
                    _army(404, province_id=11, in_combat=True),
                    _army(505, province_id=11, retreating=True),
                    _army(606, province_id=12),
                    _army(707, province_id=11, controllable=False),
                ],
            )
        )
        service = GameplayBridgeService(driver)

        self.assertEqual(
            driver.capabilities()["action_steps"],
            [
                "merge-armies-101-with-303",
                "merge-armies-303-with-101",
            ],
        )
        planned_step = service.plan_turn()["plan"].get("selected_step")
        self.assertFalse(
            isinstance(planned_step, str)
            and planned_step.startswith("merge-armies-")
        )

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {
                        "step": frame["step"],
                        "accepted": True,
                        "status": "merge_submitted",
                    },
                }
            )

        endpoint.send_hook = answer
        result = service.execute_step(
            "merge-armies-101-with-303",
            expected_revision=int(driver.take_snapshot()["revision"]),
        )

        self.assertEqual(
            result["war_action"],
            {
                "status": "merge_submitted",
                "destination_army_id": 101,
                "source_army_id": 303,
                "submitted_date_raw": 53_171_400,
                "player_army_ids_before": [101, 303, 404, 505, 606],
            },
        )
        self.assertEqual(
            [
                frame["step"]
                for frame in endpoint.frames
                if frame.get("type") == "execute_step"
            ],
            ["merge-armies-101-with-303"],
        )

    def test_merge_armies_projects_exact_immediate_removal(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.command.merge-armies-N-with-N",
            )
        )
        destination = _army(101, province_id=11)
        source = _army(303, province_id=11)
        unaffected = _army(404, province_id=12)
        endpoint.publish(
            _snapshot(
                40,
                date_raw=53_171_400,
                player_armies=[destination, source, unaffected],
            )
        )

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {
                        "step": frame["step"],
                        "accepted": True,
                        "status": "merge_submitted",
                    },
                }
            )
            endpoint.publish(
                _snapshot(
                    41,
                    date_raw=53_171_400,
                    player_armies=[destination, unaffected],
                )
            )

        endpoint.send_hook = answer
        result = GameplayBridgeService(driver).execute_step(
            "merge-armies-101-with-303"
        )

        self.assertEqual(result["war_action"]["status"], "merge_applied")
        self.assertEqual(
            result["war_action"]["player_army_ids_before"],
            [101, 303, 404],
        )

    def test_merge_armies_does_not_guess_from_partial_immediate_state(
        self,
    ) -> None:
        destination_before = _army(101, province_id=11)
        source_before = _army(303, province_id=11)
        unchanged = _army(404, province_id=12)
        changed_owner = _army(101, province_id=11)
        changed_owner["owner_character_id"] = 909
        cases = {
            "destination_moved": [
                _army(101, province_id=12),
                unchanged,
            ],
            "destination_owner_changed": [changed_owner, unchanged],
            "unexpected_new_army": [
                destination_before,
                unchanged,
                _army(505, province_id=12),
            ],
            "source_still_exists": [
                destination_before,
                _army(303, province_id=11, controllable=False),
                unchanged,
            ],
        }
        for name, immediate_armies in cases.items():
            with self.subTest(case=name):
                endpoint = FakeEndpoint()
                driver = NativeHeadlessGameplayDriver(
                    endpoint.pipe_name,
                    endpoint=endpoint,
                )
                endpoint.publish(
                    _hello(
                        "game.state.snapshot",
                        "game.command.merge-armies-N-with-N",
                    )
                )
                endpoint.publish(
                    _snapshot(
                        40,
                        date_raw=53_171_400,
                        player_armies=[
                            destination_before,
                            source_before,
                            unchanged,
                        ],
                    )
                )

                def submit_and_publish(
                    _step: str, *, expected_revision: int | None
                ) -> dict[str, object]:
                    endpoint.publish(
                        _snapshot(
                            41,
                            date_raw=53_171_400,
                            player_armies=immediate_armies,
                        )
                    )
                    return {"status": "merge_submitted"}

                with mock.patch.object(
                    driver,
                    "_execute_primitive_step",
                    side_effect=submit_and_publish,
                ):
                    result = driver._execute_native_war_step(
                        "merge-armies-101-with-303",
                        expected_revision=None,
                    )

                self.assertEqual(
                    result["war_action"]["status"], "merge_submitted"
                )

    def test_native_war_templates_expand_and_move_waits_for_target(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=0.2,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.active-wars",
                "game.state.war-primary-opponent",
                "game.command.move-army-N-to-N",
                "game.command.disband-army-N",
            )
        )
        player = _army(101, soldiers=1_500, province_id=11)
        enemy = _army(
            202,
            soldiers=2_400,
            province_id=33,
            controllable=False,
        )
        endpoint.publish(
            _snapshot(
                40,
                active_wars=[
                    _war(
                        allied_armies=[player],
                        enemy_armies=[enemy],
                        enemy_primary_default_raise_province_id=77,
                    )
                ],
                player_armies=[player],
            )
        )

        self.assertEqual(
            driver.capabilities()["action_steps"],
            [
                "disband-army-101",
                "move-army-101-to-33",
                "move-army-101-to-77",
            ],
        )
        before = driver.take_snapshot()
        self.assertEqual(before["active_wars"][0]["enemy_armies"][0]["soldiers"], 2_400)
        self.assertEqual(
            before["active_wars"][0]["primary_opponent_character_id"], 808
        )
        self.assertTrue(
            before["active_wars"][0]["player_is_primary_war_leader"]
        )
        self.assertEqual(
            before["active_wars"][0][
                "enemy_primary_default_raise_province_id"
            ],
            77,
        )

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {"status": "submitted"},
                }
            )
            moving = _army(
                101,
                soldiers=1_500,
                province_id=11,
                move_target_province_id=33,
            )
            endpoint.publish(
                _snapshot(
                    41,
                    active_wars=[
                        _war(
                            allied_armies=[moving],
                            enemy_armies=[enemy],
                            enemy_primary_default_raise_province_id=77,
                        )
                    ],
                    player_armies=[moving],
                )
            )

        endpoint.send_hook = answer
        result = driver.execute_step(
            "move-army-101-to-33",
            expected_revision=int(before["revision"]),
        )

        self.assertEqual(result["war_action"]["status"], "moving")
        self.assertEqual(result["war_action"]["target_province_id"], 33)
        command = next(
            frame for frame in reversed(endpoint.frames)
            if frame.get("type") == "execute_step"
        )
        self.assertEqual(command["step"], "move-army-101-to-33")
        self.assertEqual(command["expected_revision"], 40)
        self.assertNotIn(
            "move-army-101-to-33", driver.capabilities()["action_steps"]
        )
        self.assertIn(
            "move-army-101-to-77", driver.capabilities()["action_steps"]
        )

    def test_native_route_preview_expands_and_records_date_and_origin(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=0.2,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.war-objectives",
                "game.state.army-routes",
                "game.command.move-army-N-to-N",
                "game.command.preview-move-army-N-to-N",
            )
        )
        player = _army(101, province_id=11, route_province_ids=[])
        war = _war(
            allied_armies=[player],
            war_objective_province_ids=[2585],
        )
        endpoint.publish(
            _snapshot(
                40,
                date_raw=53_171_400,
                active_wars=[war],
                player_armies=[player],
            )
        )

        steps = driver.capabilities()["action_steps"]
        self.assertIn("move-army-101-to-2585", steps)
        self.assertIn("preview-move-army-101-to-2585", steps)
        projected = driver.take_snapshot()
        self.assertTrue(projected["army_routes_supported"])
        self.assertTrue(projected["move_route_preview_supported"])

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {
                        "step": frame["step"],
                        "accepted": True,
                        "status": "available",
                        "route_preview": {
                            "status": "available",
                            "army_id": 101,
                            "origin_province_id": 11,
                            "target_province_id": 2585,
                            "route_province_ids": [11, 31, 31, 2585],
                        },
                    },
                }
            )

        endpoint.send_hook = answer
        with mock.patch.object(
            driver,
            "take_snapshot",
            side_effect=AssertionError(
                "read-only route preview must not copy command history"
            ),
        ):
            result = driver.execute_step("preview-move-army-101-to-2585")

        self.assertEqual(result["route_preview"]["origin_province_id"], 11)
        self.assertEqual(
            result["route_preview"]["previewed_date_raw"], 53_171_400
        )
        self.assertEqual(
            result["route_preview"]["route_province_ids"],
            [11, 31, 31, 2585],
        )

    def test_routed_controllable_army_projects_same_province_route_clear(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=0.2,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.active-wars",
                "game.state.army-routes",
                "game.command.move-army-N-to-N",
                "game.command.preview-move-army-N-to-N",
            )
        )
        routed = _army(
            83_886_341,
            province_id=2596,
            move_target_province_id=2604,
            route_province_ids=[2595, 2603, 2604],
        )
        enemy = _army(
            357,
            province_id=2564,
            move_target_province_id=2596,
            route_province_ids=[2582, 2587, 2597, 2596],
            controllable=False,
        )
        endpoint.publish(
            _snapshot(
                40,
                active_wars=[
                    _war(allied_armies=[routed], enemy_armies=[enemy])
                ],
                player_armies=[routed],
            )
        )

        routed_steps = driver.capabilities()["action_steps"]
        self.assertIn(
            "preview-move-army-83886341-to-2596", routed_steps
        )
        self.assertIn("move-army-83886341-to-2596", routed_steps)
        self.assertNotIn("move-army-357-to-2564", routed_steps)

        cleared = _army(
            83_886_341,
            province_id=2596,
            move_target_province_id=None,
            route_province_ids=[],
        )
        endpoint.publish(
            _snapshot(
                41,
                active_wars=[
                    _war(allied_armies=[cleared], enemy_armies=[enemy])
                ],
                player_armies=[cleared],
            )
        )

        cleared_steps = driver.capabilities()["action_steps"]
        self.assertNotIn(
            "preview-move-army-83886341-to-2596", cleared_steps
        )
        self.assertNotIn("move-army-83886341-to-2596", cleared_steps)

    def test_actual_contact_scope_is_atomic_and_combat_v3_ready(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=0.2,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.command.query-actual-contact-scope-v1-N",
            )
        )
        player = _army(101, province_id=2585, route_province_ids=[])
        endpoint.publish(
            _snapshot(
                40,
                date_raw=53_176_176,
                player_armies=[player],
            )
        )
        step = "query-actual-contact-scope-v1-101-at-2585"
        self.assertIn(step, driver.capabilities()["action_steps"])
        self.assertTrue(
            driver.take_snapshot()["actual_contact_scope_query_supported"]
        )

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {
                        "step": frame["step"],
                        "accepted": True,
                        "status": "available",
                        "query_sequence": 1,
                        "snapshot_revision": 40,
                        "actual_contact_scope": {
                            "schema_version": 1,
                            "contract_stage": (
                                "production_exact_current_province"
                            ),
                            "status": "available",
                            "scope_kind": "pre_contact_prediction",
                            "snapshot_revision": 40,
                            "date_raw": 53_176_176,
                            "subject_army_id": 101,
                            "subject_native_carmy_id": 201,
                            "subject_owner_character_id": 7,
                            "target_province_id": 2585,
                            "province_unit_army_ids": [31, 41, 101],
                            "province_combat_ids": [],
                            "stored_order_policy": "numeric_full_id",
                            "transition_kind": "create_new",
                            "selected_combat_id": None,
                            "selected_combat_array_index": None,
                            "join_side": None,
                            "defender_seed_character_id": 19,
                            "initiator_is_defender": False,
                            "adjacency_kind_raw": 2,
                            "loser_excluded_native_carmy_ids": [],
                            "opponent_army_ids": [31, 41],
                            "attacker_army_ids": [101],
                            "defender_army_ids": [31, 41],
                            "actual_contact_scope_ready": True,
                            "combat_v3_participant_scope_ready": True,
                        },
                    },
                }
            )

        endpoint.send_hook = answer
        result = GameplayBridgeService(driver).query_actual_contact_scope(
            101, 2585
        )
        scope = result["actual_contact_scope"]
        self.assertEqual(scope["attacker_army_ids"], [101])
        self.assertEqual(scope["defender_army_ids"], [31, 41])
        self.assertTrue(scope["combat_v3_participant_scope_ready"])
        command = next(
            frame
            for frame in reversed(endpoint.frames)
            if frame.get("type") == "execute_step"
        )
        self.assertEqual(command["expected_revision"], 40)

    def test_actual_contact_scope_step_includes_combat_but_excludes_retreat(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.command.query-actual-contact-scope-v1-N",
            )
        )
        endpoint.publish(
            _snapshot(
                40,
                date_raw=53_176_176,
                player_armies=[
                    _army(101, province_id=2585),
                    _army(202, province_id=2585, in_combat=True),
                    _army(303, province_id=2585, retreating=True),
                ],
            )
        )

        self.assertEqual(
            driver.capabilities()["action_steps"],
            [
                "query-actual-contact-scope-v1-101-at-2585",
                "query-actual-contact-scope-v1-202-at-2585",
            ],
        )

    def test_route_contact_horizon_is_atomic_and_scope_complete(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=0.2,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.war-objectives",
                "game.state.army-routes",
                "game.command.query-route-contact-horizon-v1-N",
            )
        )
        player = _army(101, province_id=2603, route_province_ids=[])
        enemy = _army(
            31,
            province_id=2583,
            controllable=False,
            move_target_province_id=2604,
            army_state="moving",
            route_province_ids=[2594, 2599, 2604],
        )
        endpoint.publish(
            _snapshot(
                40,
                date_raw=53_176_176,
                active_wars=[
                    _war(
                        allied_armies=[player],
                        enemy_armies=[enemy],
                        war_objective_province_ids=[2585],
                    )
                ],
                player_armies=[player],
            )
        )
        step = "query-route-contact-horizon-v1-101-to-2585-h-1-31"
        self.assertIn(step, driver.capabilities()["action_steps"])
        self.assertTrue(
            driver.take_snapshot()["route_contact_horizon_supported"]
        )

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {
                        "step": frame["step"],
                        "accepted": True,
                        "status": "available",
                        "query_sequence": 1,
                        "snapshot_revision": 40,
                        "route_contact_horizon": {
                            "status": "available",
                            "date_raw": 53_176_176,
                            "snapshot_revision": 40,
                            "subject_army_id": 101,
                            "target_province_id": 2585,
                            "hostile_army_ids": [31],
                            "subject_route": {
                                "timeline_observable": True,
                                "army_id": 101,
                                "current_province_id": 2603,
                                "effective_origin_province_id": 2604,
                                "route_province_ids": [2604, 2595, 2585],
                                "arrival_date_raws": [
                                    53_176_200,
                                    53_176_248,
                                    53_176_296,
                                ],
                            },
                            "hostile_routes": [
                                {
                                    "timeline_observable": True,
                                    "army_id": 31,
                                    "current_province_id": 2583,
                                    "effective_origin_province_id": 2583,
                                    "route_province_ids": [2594, 2599, 2604],
                                    "arrival_date_raws": [
                                        53_176_224,
                                        53_176_272,
                                        53_176_320,
                                    ],
                                }
                            ],
                            "horizon_start_date_raw": 53_176_176,
                            "horizon_end_date_raw": 53_176_200,
                            "one_day_contact_free": True,
                            "conflicts": [],
                        },
                    },
                }
            )

        endpoint.send_hook = answer
        with mock.patch.object(
            driver,
            "take_snapshot",
            side_effect=AssertionError(
                "read-only contact query must not copy command history"
            ),
        ):
            result = driver.execute_step(step)
        self.assertTrue(
            result["route_contact_horizon"]["one_day_contact_free"]
        )
        self.assertEqual(result["queried_native_revision"], 40)
        command = next(
            frame
            for frame in reversed(endpoint.frames)
            if frame.get("type") == "execute_step"
        )
        self.assertEqual(command["expected_revision"], 40)

        with self.assertRaises(UnsupportedStepError):
            driver.execute_step(
                "query-route-contact-horizon-v1-101-to-2585-h-1-41"
            )

    def test_fresh_contact_proof_advertises_and_consumes_exact_day_once(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=0.2,
            life_advance_timeout_seconds=0.2,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.war-objectives",
                "game.state.army-routes",
                "game.command.query-route-contact-horizon-v1-N",
                "game.command.set-speed-1",
                "game.command.resume-map",
                "game.command.pause-map",
            )
        )
        start_date = 53_176_176
        player = _army(
            101,
            province_id=2603,
            move_target_province_id=2585,
            army_state="moving",
            route_province_ids=[2604, 2595, 2585],
        )
        enemy = _army(
            31,
            province_id=2583,
            controllable=False,
            move_target_province_id=2600,
            army_state="moving",
            route_province_ids=[2594, 2600],
        )
        war = _war(
            allied_armies=[player],
            enemy_armies=[enemy],
            war_objective_province_ids=[2585],
        )

        def publish_snapshot(
            revision: int, *, paused: bool, date_raw: int, speed: int
        ) -> None:
            endpoint.publish(
                _snapshot(
                    revision,
                    paused=paused,
                    date_raw=date_raw,
                    speed=speed,
                    active_wars=[war],
                    player_armies=[player],
                )
            )

        publish_snapshot(40, paused=True, date_raw=start_date, speed=5)
        query_step = (
            "query-route-contact-horizon-v1-101-to-2585-h-1-31"
        )
        advance_step = advance_route_contact_horizon_step(
            101, 2585, (31,)
        )

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            step = str(frame["step"])
            result: dict[str, object] = {"step": step, "accepted": True}
            if step == query_step:
                result.update(
                    {
                        "status": "available",
                        "query_sequence": 1,
                        "snapshot_revision": 40,
                        "route_contact_horizon": {
                            "status": "available",
                            "date_raw": start_date,
                            "snapshot_revision": 40,
                            "subject_army_id": 101,
                            "target_province_id": 2585,
                            "hostile_army_ids": [31],
                            "subject_route": {
                                "timeline_observable": True,
                                "army_id": 101,
                                "current_province_id": 2603,
                                "effective_origin_province_id": 2604,
                                "route_province_ids": [2604, 2595, 2585],
                                "arrival_date_raws": [
                                    start_date + 24,
                                    start_date + 48,
                                    start_date + 72,
                                ],
                            },
                            "hostile_routes": [
                                {
                                    "timeline_observable": True,
                                    "army_id": 31,
                                    "current_province_id": 2583,
                                    "effective_origin_province_id": 2594,
                                    "route_province_ids": [2594, 2600],
                                    "arrival_date_raws": [
                                        start_date + 24,
                                        start_date + 48,
                                    ],
                                }
                            ],
                            "horizon_start_date_raw": start_date,
                            "horizon_end_date_raw": start_date + 24,
                            "one_day_contact_free": True,
                            "conflicts": [],
                        },
                    }
                )
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": result,
                }
            )
            if step == "set-speed-1":
                publish_snapshot(
                    41, paused=True, date_raw=start_date, speed=1
                )
            elif step == "resume-map":
                publish_snapshot(
                    42,
                    paused=False,
                    date_raw=start_date + 24,
                    speed=1,
                )
            elif step == "pause-map":
                publish_snapshot(
                    43,
                    paused=True,
                    date_raw=start_date + 24,
                    speed=1,
                )

        endpoint.send_hook = answer
        driver.execute_step(query_step)
        self.assertIn(advance_step, driver.capabilities()["action_steps"])
        revision = int(driver.take_snapshot()["revision"])

        with mock.patch.object(
            driver,
            "_history_snapshot",
            side_effect=AssertionError(
                "contact proof validation must not copy command history"
            ),
        ):
            result = driver.execute_step(
                advance_step, expected_revision=revision
            )

        self.assertEqual(result["starting_date_raw"], start_date)
        self.assertEqual(result["ending_date_raw"], start_date + 24)
        self.assertEqual(result["elapsed_days"], 1)
        self.assertEqual(result["timeline_speed"], 1)
        self.assertEqual(result["timeline_policy"], "exact_one_day_contact")
        self.assertTrue(result["paused"])
        self.assertNotIn(advance_step, driver.capabilities()["action_steps"])

    def test_unavoidable_contact_proof_observes_combat_after_exact_day(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=0.2,
            life_advance_timeout_seconds=0.2,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.war-objectives",
                "game.state.army-routes",
                "game.command.query-route-contact-horizon-v1-N",
                "game.command.set-speed-1",
                "game.command.resume-map",
                "game.command.pause-map",
            )
        )
        start_date = 53_216_424
        player = _army(
            101,
            province_id=5692,
            move_target_province_id=3610,
            army_state="moving",
            route_province_ids=[8672, 3610],
        )
        enemy = _army(
            31,
            province_id=5693,
            controllable=False,
            move_target_province_id=5692,
            army_state="moving",
            route_province_ids=[5692],
        )
        war = _war(
            allied_armies=[player],
            enemy_armies=[enemy],
            war_objective_province_ids=[3610],
        )
        combat_player = {
            **player,
            "in_combat": True,
            "army_state": "combat",
            "army_state_code": 2,
            "move_target_province_id": None,
            "route_province_ids": [],
        }
        combat_enemy = {
            **enemy,
            "current_province_id": 5692,
            "in_combat": True,
            "army_state": "combat",
            "army_state_code": 2,
            "move_target_province_id": None,
            "route_province_ids": [],
        }
        combat_war = _war(
            allied_armies=[combat_player],
            enemy_armies=[combat_enemy],
            war_objective_province_ids=[3610],
        )

        def publish_snapshot(
            revision: int,
            *,
            paused: bool,
            date_raw: int,
            speed: int,
            combat: bool = False,
        ) -> None:
            endpoint.publish(
                _snapshot(
                    revision,
                    paused=paused,
                    date_raw=date_raw,
                    speed=speed,
                    active_wars=[combat_war if combat else war],
                    player_armies=[combat_player if combat else player],
                )
            )

        publish_snapshot(40, paused=True, date_raw=start_date, speed=5)
        query_step = query_route_contact_horizon_step(101, 3610, (31,))
        advance_step = advance_route_contact_horizon_step(101, 3610, (31,))

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            step = str(frame["step"])
            result: dict[str, object] = {"step": step, "accepted": True}
            if step == query_step:
                result.update(
                    {
                        "status": "available",
                        "query_sequence": 1,
                        "snapshot_revision": 40,
                        "route_contact_horizon": {
                            "status": "available",
                            "date_raw": start_date,
                            "snapshot_revision": 40,
                            "subject_army_id": 101,
                            "target_province_id": 3610,
                            "hostile_army_ids": [31],
                            "subject_route": {
                                "timeline_observable": True,
                                "army_id": 101,
                                "current_province_id": 5692,
                                "effective_origin_province_id": 8672,
                                "route_province_ids": [8672, 3610],
                                "arrival_date_raws": [
                                    start_date + 264,
                                    start_date + 504,
                                ],
                            },
                            "hostile_routes": [
                                {
                                    "timeline_observable": True,
                                    "army_id": 31,
                                    "current_province_id": 5693,
                                    "effective_origin_province_id": 5692,
                                    "route_province_ids": [5692],
                                    "arrival_date_raws": [start_date + 24],
                                }
                            ],
                            "horizon_start_date_raw": start_date,
                            "horizon_end_date_raw": start_date + 24,
                            "one_day_contact_free": False,
                            "conflicts": [
                                {
                                    "kind": "same_province",
                                    "hostile_army_id": 31,
                                    "province_id": 5692,
                                    "overlap_start_date_raw": start_date + 24,
                                    "overlap_end_date_raw": start_date + 24,
                                }
                            ],
                        },
                    }
                )
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": result,
                }
            )
            if step == "set-speed-1":
                publish_snapshot(41, paused=True, date_raw=start_date, speed=1)
            elif step == "resume-map":
                publish_snapshot(
                    42,
                    paused=False,
                    date_raw=start_date + 24,
                    speed=1,
                )
            elif step == "pause-map":
                publish_snapshot(
                    43,
                    paused=True,
                    date_raw=start_date + 24,
                    speed=1,
                    combat=True,
                )

        endpoint.send_hook = answer
        driver.execute_step(query_step)
        self.assertIn(advance_step, driver.capabilities()["action_steps"])
        revision = int(driver.take_snapshot()["revision"])
        result = driver.execute_step(advance_step, expected_revision=revision)

        self.assertEqual(result["ending_date_raw"], start_date + 24)
        self.assertEqual(result["timeline_speed"], 1)
        self.assertEqual(
            result["contact_transition"]["postcondition"],
            "active_combat_observed",
        )
        self.assertNotIn(advance_step, driver.capabilities()["action_steps"])

    def test_unavoidable_contact_observes_conflict_hostile_entering_province(
        self,
    ) -> None:
        start_date = 53_216_424
        contact_province_id = 5692
        player = _army(
            101,
            province_id=contact_province_id,
            move_target_province_id=3610,
            army_state="moving",
            route_province_ids=[8672, 3610],
        )
        conflict_enemy = _army(
            31,
            province_id=5693,
            controllable=False,
            move_target_province_id=contact_province_id,
            army_state="moving",
            route_province_ids=[contact_province_id],
        )
        remote_enemy = _army(
            41,
            province_id=1111,
            controllable=False,
            move_target_province_id=contact_province_id,
            army_state="moving",
            route_province_ids=[8665, contact_province_id],
        )

        def semantic_snapshot(
            *,
            date_raw: int,
            subject: dict[str, object] = player,
            local_enemy: dict[str, object] = conflict_enemy,
            other_enemy: dict[str, object] = remote_enemy,
        ) -> dict[str, object]:
            return {
                "paused": True,
                "date_raw": date_raw,
                "played_character_alive": True,
                "one_life_terminal": False,
                "active_wars": [
                    _war(
                        allied_armies=[subject],
                        enemy_armies=[local_enemy, other_enemy],
                        war_objective_province_ids=[3610],
                    )
                ],
                "player_armies": [subject],
            }

        proof = {
            "subject_army_id": 101,
            "hostile_army_ids": [31, 41],
            "contact_horizon": {
                "subject_route": {
                    "current_province_id": contact_province_id,
                },
                "conflicts": [
                    {
                        "kind": "same_province",
                        "hostile_army_id": 31,
                        "province_id": contact_province_id,
                    }
                ],
            },
        }
        starting = semantic_snapshot(date_raw=start_date)
        entered_enemy = {
            **conflict_enemy,
            "current_province_id": contact_province_id,
        }
        ending = semantic_snapshot(
            date_raw=start_date + 24,
            local_enemy=entered_enemy,
        )

        observed = _unavoidable_contact_transition_postcondition(
            starting,
            ending,
            proof=proof,
        )
        self.assertIsNotNone(observed)
        assert observed is not None
        self.assertEqual(
            observed["postcondition"],
            "hostile_entered_contact_province",
        )
        self.assertEqual(observed["contact_province_id"], contact_province_id)
        self.assertEqual(observed["changed_hostile_army_ids"], [31])

        already_present = semantic_snapshot(
            date_raw=start_date,
            local_enemy=entered_enemy,
        )
        with self.subTest("same hostile cannot satisfy entry twice"):
            self.assertIsNone(
                _unavoidable_contact_transition_postcondition(
                    already_present,
                    ending,
                    proof=proof,
                )
            )

        remote_entered = {
            **remote_enemy,
            "current_province_id": contact_province_id,
        }
        with self.subTest("non-conflict hostile cannot mask missing contact"):
            self.assertIsNone(
                _unavoidable_contact_transition_postcondition(
                    starting,
                    semantic_snapshot(
                        date_raw=start_date + 24,
                        other_enemy=remote_entered,
                    ),
                    proof=proof,
                )
            )

        remote_rerouted = {
            **remote_enemy,
            "move_target_province_id": 8665,
            "route_province_ids": [8665],
        }
        with self.subTest("remote hostile reroute cannot mask missing contact"):
            self.assertIsNone(
                _unavoidable_contact_transition_postcondition(
                    starting,
                    semantic_snapshot(
                        date_raw=start_date + 24,
                        other_enemy=remote_rerouted,
                    ),
                    proof=proof,
                )
            )

        conflict_rerouted = {
            **conflict_enemy,
            "move_target_province_id": 5693,
            "route_province_ids": [5693],
        }
        with self.subTest("conflict hostile reroute invalidates the proof"):
            changed = _unavoidable_contact_transition_postcondition(
                starting,
                semantic_snapshot(
                    date_raw=start_date + 24,
                    local_enemy=conflict_rerouted,
                ),
                proof=proof,
            )
            self.assertIsNotNone(changed)
            assert changed is not None
            self.assertEqual(changed["postcondition"], "hostile_intent_changed")
            self.assertEqual(changed["changed_hostile_army_ids"], [31])

        subject_left = {
            **player,
            "current_province_id": 8672,
        }
        with self.subTest("subject must remain in the proved contact province"):
            self.assertIsNone(
                _unavoidable_contact_transition_postcondition(
                    starting,
                    semantic_snapshot(
                        date_raw=start_date + 24,
                        subject=subject_left,
                        local_enemy=entered_enemy,
                    ),
                    proof=proof,
                )
            )

    def test_moving_contact_proof_covers_stationary_army_exact_day(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.war-objectives",
                "game.state.army-routes",
                "game.command.query-route-contact-horizon-v1-N",
                "game.command.set-speed-1",
                "game.command.resume-map",
                "game.command.pause-map",
            )
        )
        start_date = 53_212_728
        moving = _army(
            101,
            province_id=20,
            move_target_province_id=30,
            army_state="moving",
            route_province_ids=[25, 30],
        )
        stationary = _army(
            202,
            province_id=22,
            army_state="regular",
            route_province_ids=[],
        )
        enemy = _army(
            31,
            province_id=99,
            controllable=False,
            move_target_province_id=30,
            army_state="moving",
            route_province_ids=[23, 22, 25, 30],
        )
        war = _war(
            allied_armies=[moving, stationary],
            enemy_armies=[enemy],
            war_objective_province_ids=[30],
        )
        endpoint.publish(
            _snapshot(
                40,
                date_raw=start_date,
                active_wars=[war],
                player_armies=[moving, stationary],
            )
        )
        snapshot = driver.take_snapshot()
        hostiles = (31,)
        moving_query = query_route_contact_horizon_step(101, 30, hostiles)
        stationary_query = query_route_contact_horizon_step(202, 22, hostiles)
        advance_step = advance_route_contact_horizon_step(101, 30, hostiles)
        self.assertNotIn(
            stationary_query, driver.capabilities()["action_steps"]
        )

        def proof_row(
            index: int,
            *,
            step: str,
            subject_id: int,
            current: int,
            target: int,
            route: list[int],
            arrivals: list[int],
        ) -> dict[str, object]:
            return {
                "index": index,
                "command": step,
                "ok": True,
                "result": {
                    "step": step,
                    "accepted": True,
                    "status": "available",
                    "route_contact_horizon": {
                        "status": "available",
                        "date_raw": start_date,
                        "snapshot_revision": snapshot["native_revision"],
                        "subject_army_id": subject_id,
                        "target_province_id": target,
                        "hostile_army_ids": [31],
                        "subject_route": {
                            "timeline_observable": True,
                            "army_id": subject_id,
                            "current_province_id": current,
                            "effective_origin_province_id": (
                                route[0] if route else current
                            ),
                            "route_province_ids": route,
                            "arrival_date_raws": arrivals,
                        },
                        "hostile_routes": [
                            {
                                "timeline_observable": True,
                                "army_id": 31,
                                "current_province_id": 99,
                                "effective_origin_province_id": 23,
                                "route_province_ids": [23, 22, 25, 30],
                                "arrival_date_raws": [
                                    start_date + 24,
                                    start_date + 48,
                                    start_date + 72,
                                    start_date + 96,
                                ],
                            }
                        ],
                        "horizon_start_date_raw": start_date,
                        "horizon_end_date_raw": start_date + 24,
                        "one_day_contact_free": True,
                        "conflicts": [],
                    },
                    "queried_snapshot_id": snapshot["snapshot_id"],
                    "queried_revision": snapshot["revision"],
                    "queried_native_revision": snapshot["native_revision"],
                    "queried_connection_generation": snapshot[
                        "diagnostics"
                    ]["connection_generation"],
                    "queried_episode_run_id": snapshot["episode_run_id"],
                },
            }

        moving_proof = proof_row(
            1,
            step=moving_query,
            subject_id=101,
            current=20,
            target=30,
            route=[25, 30],
            arrivals=[start_date + 24, start_date + 48],
        )
        self.assertIn(
            advance_step,
            _fresh_route_contact_advance_steps(snapshot, [moving_proof]),
        )
        gathering_snapshot = copy.deepcopy(snapshot)
        next(
            army
            for army in gathering_snapshot["player_armies"]
            if army["army_id"] == 202
        )["army_state"] = "gathering"
        self.assertNotIn(
            advance_step,
            _fresh_route_contact_advance_steps(
                gathering_snapshot, [moving_proof]
            ),
        )
        malformed_route_snapshot = copy.deepcopy(snapshot)
        next(
            army
            for army in malformed_route_snapshot["player_armies"]
            if army["army_id"] == 202
        )["route_province_ids"] = [None]
        self.assertNotIn(
            advance_step,
            _fresh_route_contact_advance_steps(
                malformed_route_snapshot, [moving_proof]
            ),
        )
        blocked_proof = copy.deepcopy(moving_proof)
        hostile_route = blocked_proof["result"]["route_contact_horizon"][
            "hostile_routes"
        ][0]
        hostile_route["route_province_ids"] = [22, 25, 30]
        hostile_route["arrival_date_raws"] = [
            start_date + 24,
            start_date + 72,
            start_date + 96,
        ]
        hostile_route["effective_origin_province_id"] = 22
        self.assertNotIn(
            advance_step,
            _fresh_route_contact_advance_steps(snapshot, [blocked_proof]),
        )

    def test_existing_move_target_still_advertises_preview_not_duplicate_move(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.war-objectives",
                "game.command.move-army-N-to-N",
                "game.command.preview-move-army-N-to-N",
            )
        )
        player = _army(
            101,
            province_id=11,
            move_target_province_id=77,
            route_province_ids=[77],
            army_state="moving",
        )
        endpoint.publish(
            _snapshot(
                40,
                active_wars=[
                    _war(
                        allied_armies=[player],
                        war_objective_province_ids=[77],
                    )
                ],
                player_armies=[player],
            )
        )

        steps = driver.capabilities()["action_steps"]
        self.assertIn("preview-move-army-101-to-77", steps)
        self.assertNotIn("move-army-101-to-77", steps)

    def test_native_route_preview_preserves_a_later_origin_loop(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=0.2,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.war-objectives",
                "game.state.army-routes",
                "game.command.preview-move-army-N-to-N",
            )
        )
        player = _army(
            83886341,
            province_id=8759,
            move_target_province_id=2568,
            army_state="moving",
            route_province_ids=[
                2602,
                2591,
                2589,
                2579,
                2574,
                2572,
                2568,
            ],
        )
        endpoint.publish(
            _snapshot(
                163,
                date_raw=53_177_568,
                active_wars=[
                    _war(
                        allied_armies=[player],
                        war_objective_province_ids=[2604],
                    )
                ],
                player_armies=[player],
            )
        )

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {
                        "step": frame["step"],
                        "accepted": True,
                        "status": "available",
                        "route_preview": {
                            "status": "available",
                            "army_id": 83886341,
                            "origin_province_id": 8759,
                            "target_province_id": 2604,
                            "route_province_ids": [2602, 8759, 2604],
                        },
                    },
                }
            )

        endpoint.send_hook = answer
        result = driver.execute_step(
            "preview-move-army-83886341-to-2604"
        )

        self.assertEqual(
            result["route_preview"]["route_province_ids"],
            [2602, 8759, 2604],
        )
        self.assertEqual(
            result["route_preview"]["previewed_date_raw"], 53_177_568
        )

    def test_native_route_preview_rejects_unpaused_starting_snapshot(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.war-objectives",
                "game.command.preview-move-army-N-to-N",
            )
        )
        player = _army(101, province_id=11, route_province_ids=[])
        endpoint.publish(
            _snapshot(
                40,
                paused=False,
                active_wars=[
                    _war(
                        allied_armies=[player],
                        war_objective_province_ids=[2585],
                    )
                ],
                player_armies=[player],
            )
        )

        with self.assertRaisesRegex(BridgeUnavailableError, "paused map"):
            driver.execute_step("preview-move-army-101-to-2585")
        self.assertFalse(
            any(
                frame.get("type") == "execute_step"
                for frame in endpoint.frames
            )
        )

    def test_native_route_preview_accepts_empty_same_origin_route(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.command.preview-move-army-N-to-N",
            )
        )
        player = _army(101, province_id=11, route_province_ids=[])
        endpoint.publish(
            _snapshot(
                40,
                active_wars=[_war(allied_armies=[player])],
                player_armies=[player],
            )
        )

        primitive_result = {
            "step": "preview-move-army-101-to-11",
            "accepted": True,
            "status": "available",
            "route_preview": {
                "status": "available",
                "army_id": 101,
                "origin_province_id": 11,
                "target_province_id": 11,
                "route_province_ids": [],
            },
        }
        with mock.patch.object(
            driver,
            "_execute_primitive_step",
            return_value=primitive_result,
        ):
            result = driver._execute_native_war_step(
                "preview-move-army-101-to-11", expected_revision=None
            )

        self.assertEqual(result["route_preview"]["route_province_ids"], [])
        self.assertEqual(
            result["route_preview"]["previewed_date_raw"], 53_171_400
        )

    def test_native_route_preview_not_ready_is_structured_deferred(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.war-objectives",
                "game.command.preview-move-army-N-to-N",
            )
        )
        player = _army(101, province_id=11, route_province_ids=[])
        endpoint.publish(
            _snapshot(
                40,
                active_wars=[
                    _war(
                        allied_armies=[player],
                        war_objective_province_ids=[2585],
                    )
                ],
                player_armies=[player],
            )
        )

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": False,
                    "error": "CK3 army state rejects movement",
                }
            )

        endpoint.send_hook = answer
        result = driver.execute_step("preview-move-army-101-to-2585")

        self.assertFalse(result["accepted"])
        self.assertEqual(result["status"], "deferred")
        self.assertEqual(result["route_preview"]["status"], "deferred")
        self.assertEqual(
            result["route_preview"]["native_rejection_stage"],
            "army_state_rejected",
        )
        self.assertEqual(
            result["route_preview"]["native_error"],
            "CK3 army state rejects movement",
        )
        self.assertEqual(
            result["route_preview"]["previewed_date_raw"], 53_171_400
        )

    def test_native_move_with_routes_waits_for_auditable_route(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=0.2,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.active-wars",
                "game.state.army-routes",
                "game.command.move-army-N-to-N",
            )
        )
        player = _army(
            401,
            province_id=20,
            observe_move_target=False,
            route_province_ids=[],
        )
        enemy = _army(402, province_id=90, controllable=False)
        endpoint.publish(
            _snapshot(
                60,
                active_wars=[_war(allied_armies=[player], enemy_armies=[enemy])],
                player_armies=[player],
            )
        )
        timer: threading.Timer | None = None

        def publish_auditable_route() -> None:
            moving = _army(
                401,
                province_id=20,
                move_target_province_id=90,
                route_province_ids=[44, 90],
            )
            endpoint.publish(
                _snapshot(
                    62,
                    active_wars=[
                        _war(allied_armies=[moving], enemy_armies=[enemy])
                    ],
                    player_armies=[moving],
                )
            )

        def answer(frame: dict[str, object]) -> None:
            nonlocal timer
            if frame.get("type") != "execute_step":
                return
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {"status": "submitted"},
                }
            )
            waiting = _army(
                401,
                province_id=20,
                observe_move_target=False,
                route_province_ids=[],
            )
            endpoint.publish(
                _snapshot(
                    61,
                    active_wars=[
                        _war(allied_armies=[waiting], enemy_armies=[enemy])
                    ],
                    player_armies=[waiting],
                )
            )
            timer = threading.Timer(0.01, publish_auditable_route)
            timer.start()

        endpoint.send_hook = answer
        result = driver.execute_step("move-army-401-to-90")
        if timer is not None:
            timer.join(timeout=0.2)

        self.assertEqual(result["war_action"]["status"], "moving")
        self.assertEqual(
            result["war_action"]["submitted_date_raw"], 53_171_400
        )
        self.assertEqual(
            result["player_armies"][0]["route_province_ids"], [44, 90]
        )

    def test_exact_war_capability_expands_fallback_and_filters_enforce(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.war-primary-opponent",
                "game.state.war-objectives",
                "game.command.move-army-N-to-N",
                "game.command.enforce-demands-N",
            )
        )
        player = _army(101, province_id=11)
        allied_war = _war(
            war_id=404,
            allied_armies=[player],
            score=100,
            player_is_primary_war_leader=False,
            enemy_primary_default_raise_province_id=77,
            targeted_title_ids=[9001],
            war_objective_province_ids=[2585],
        )
        endpoint.publish(
            _snapshot(
                42,
                active_wars=[allied_war],
                player_armies=[player],
            )
        )

        action_steps = driver.capabilities()["action_steps"]

        self.assertIn("move-army-101-to-77", action_steps)
        self.assertIn("move-army-101-to-2585", action_steps)
        self.assertNotIn("enforce-demands-404", action_steps)
        snapshot = driver.take_snapshot()
        self.assertEqual(snapshot["active_wars"][0]["targeted_title_ids"], [9001])
        self.assertEqual(
            snapshot["active_wars"][0]["war_objective_province_ids"], [2585]
        )

        primary_war = {
            **allied_war,
            "player_is_primary_war_leader": True,
        }
        endpoint.publish(
            _snapshot(
                43,
                active_wars=[primary_war],
                player_armies=[player],
            )
        )
        self.assertIn(
            "enforce-demands-404", driver.capabilities()["action_steps"]
        )

    def test_legacy_war_adapter_keeps_previous_enforce_advertisement(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.command.enforce-demands-N",
            )
        )
        legacy_war = _war(war_id=405, score=12)
        legacy_war.pop("primary_opponent_character_id")
        legacy_war.pop("player_is_primary_war_leader")
        legacy_war.pop("enemy_primary_default_raise_province_id")
        endpoint.publish(_snapshot(44, active_wars=[legacy_war]))

        snapshot = driver.take_snapshot()

        self.assertIsNone(
            snapshot["active_wars"][0]["player_is_primary_war_leader"]
        )
        self.assertIn(
            "enforce-demands-405", driver.capabilities()["action_steps"]
        )

    def test_native_war_primary_fields_record_malformed_values(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(_hello("game.state.snapshot"))
        malformed_values = (
            ("primary_opponent_character_id", "808"),
            ("player_is_primary_war_leader", 1),
            ("enemy_primary_default_raise_province_id", -1),
        )
        for revision, (field, value) in enumerate(
            malformed_values, start=45
        ):
            with self.subTest(field=field):
                war = {**_war(), field: value}
                endpoint.publish(_snapshot(revision, active_wars=[war]))
                diagnostics = driver.diagnostics()
                self.assertEqual(
                    diagnostics["rejected_state_snapshot_count"],
                    revision - 44,
                )
                self.assertEqual(
                    diagnostics["last_rejected_state_snapshot"]["revision"],
                    revision,
                )
                self.assertIn(
                    field,
                    diagnostics["last_rejected_state_snapshot"]["error"],
                )

    def test_native_declaration_query_expands_and_starts_war(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=0.1,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.declarable-wars",
                "game.command.query-declarable-wars",
                "game.command.declare-war-N",
            )
        )
        endpoint.publish(
            _snapshot(
                40,
                played_character={"character_id": 707, "alive": True},
            )
        )
        declaration = {
            "declaration_id": "808-17-0",
            "target_character_id": 808,
            "casus_belli_index": 17,
            "casus_belli_key": "county_conquest_cb",
            "configuration_index": 0,
            "claimant_character_id": -1,
            "target_title_ids": [91],
        }

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            result: dict[str, object] = {
                "step": frame["step"],
                "accepted": True,
                "status": "submitted",
            }
            if frame["step"] == "query-declarable-wars":
                result.update(
                    {
                        "status": "available",
                        "query_sequence": 3,
                        "declarable_wars": [declaration],
                    }
                )
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": result,
                }
            )
            if frame["step"].startswith("declare-war-"):
                endpoint.publish(
                    _snapshot(
                        41,
                        played_character={"character_id": 707, "alive": True},
                        active_wars=[_war(73)],
                    )
                )

        endpoint.send_hook = answer
        starting = driver.take_snapshot()
        query = driver.execute_step(
            "query-declarable-wars",
            expected_revision=int(starting["revision"]),
        )
        self.assertEqual(query["declarable_wars"][0]["casus_belli_key"], "county_conquest_cb")
        self.assertEqual(
            driver.capabilities()["action_steps"],
            ["declare-war-808-17-0", "query-declarable-wars"],
        )
        queried = driver.take_snapshot()
        self.assertEqual(queried["declaration_query_sequence"], 3)

        declared = driver.execute_step(
            "declare-war-808-17-0",
            expected_revision=int(queried["revision"]),
        )
        self.assertEqual(declared["war_action"]["status"], "war_started")
        self.assertEqual(declared["war_action"]["target_character_id"], 808)
        self.assertEqual(driver.take_snapshot()["declarable_wars"], [])

    def test_army_strength_query_is_atomic_cached_and_mcp_subset_filtered(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=0.1,
        )
        war_id = 16_777_290
        player = _army(81, controllable=True)
        ally = _army(82, controllable=False)
        enemy = _army(91, controllable=False)
        war = _war(
            war_id=war_id,
            allied_armies=[player, ally],
            enemy_armies=[enemy],
        )
        full_rows = [
            _army_strength(81, "player", [war_id]),
            _army_strength(82, "active_war_ally", [war_id]),
            _army_strength(
                91,
                "active_war_enemy",
                [war_id],
                status="unavailable",
            ),
        ]
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.command.query-army-strengths-v1",
            )
        )
        endpoint.publish(
            _snapshot(
                40,
                played_character={"character_id": 707, "alive": True},
                active_wars=[war],
                player_armies=[player],
            )
        )
        self.assertEqual(
            driver.capabilities()["action_steps"],
            ["query-army-strengths-v1"],
        )

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {
                        "step": frame["step"],
                        "accepted": True,
                        "status": "partial",
                        "query_sequence": 7,
                        "army_strengths": full_rows,
                    },
                }
            )

        endpoint.send_hook = answer
        starting = driver.take_snapshot()
        queried = driver.execute_step(
            "query-army-strengths-v1",
            expected_revision=int(starting["revision"]),
        )
        self.assertEqual(queried["status"], "partial")
        self.assertEqual(queried["queried_snapshot_id"], "native:40")
        cached = driver.take_snapshot()
        self.assertEqual(cached["army_strengths_status"], "partial")
        self.assertEqual(cached["army_strengths_query_sequence"], 7)
        self.assertEqual(
            [row["army_id"] for row in cached["army_strengths"]],
            [81, 82, 91],
        )

        service = GameplayBridgeService(driver)
        subset = service.query_army_strengths(
            [91, 81], expected_revision=int(cached["revision"])
        )
        self.assertEqual(subset["status"], "partial")
        self.assertEqual(subset["scope_status"], "partial")
        self.assertEqual(subset["scope_army_ids"], [81, 82, 91])
        self.assertEqual(
            [row["army_id"] for row in subset["army_strengths"]],
            [91, 81],
        )
        available_subset = service.query_army_strengths(
            [81], expected_revision=int(cached["revision"])
        )
        self.assertEqual(available_subset["status"], "available")
        self.assertEqual(available_subset["scope_status"], "partial")
        self.assertEqual(
            [row["army_id"] for row in available_subset["army_strengths"]],
            [81],
        )

        endpoint.publish(
            _snapshot(
                41,
                played_character={"character_id": 707, "alive": True},
                active_wars=[war],
                player_armies=[player],
            )
        )
        changed = driver.take_snapshot()
        self.assertEqual(changed["army_strengths"], [])
        self.assertIsNone(changed["army_strengths_status"])
        endpoint.publish(
            _snapshot(
                42,
                paused=False,
                played_character={"character_id": 707, "alive": True},
                active_wars=[war],
                player_armies=[player],
            )
        )
        self.assertNotIn(
            "query-army-strengths-v1",
            driver.capabilities()["action_steps"],
        )

    def test_army_strength_service_rejects_empty_duplicate_and_out_of_scope(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        player = _army(81, controllable=True)
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.command.query-army-strengths-v1",
            )
        )
        endpoint.publish(_snapshot(1, player_armies=[player], active_wars=[]))
        service = GameplayBridgeService(driver)

        for army_ids, error_type in (
            ([], ValueError),
            ([81, 81], ValueError),
            ([91], BridgeUnavailableError),
        ):
            with self.subTest(army_ids=army_ids):
                with self.assertRaises(error_type):
                    service.query_army_strengths(army_ids)
        self.assertFalse(
            any(
                frame.get("type") == "execute_step"
                for frame in endpoint.frames
            )
        )

    def test_war_termination_query_caches_exact_frame_and_gates_actions(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=0.1,
        )
        war_id = 16_777_290
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.command.query-war-termination-options-N",
                "game.command.query-war-termination-terms-v1-N",
                "game.command.surrender-war-N",
                "game.command.offer-white-peace-N",
            )
        )
        endpoint.publish(
            _snapshot(
                40,
                played_character={"character_id": 707, "alive": True},
                active_wars=[_war(war_id=war_id, score=41)],
            )
        )
        self.assertEqual(
            driver.capabilities()["action_steps"],
            [
                "query-war-termination-options-16777290",
                "query-war-termination-terms-v1-16777290",
            ],
        )

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            is_terms = str(frame["step"]).startswith(
                "query-war-termination-terms-v1-"
            )
            result: dict[str, object] = {
                "step": frame["step"],
                "accepted": True,
                "status": "available",
                "query_sequence": 12 if is_terms else 9,
            }
            if is_terms:
                result["war_termination_terms"] = _termination_terms(war_id)
            else:
                result["war_termination_options"] = _termination_options(
                    war_id,
                    white_peace_acceptance_raw=1_100_000,
                    casus_belli_database_index=0,
                    casus_belli_key="claim_cb",
                )
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": result,
                }
            )

        endpoint.send_hook = answer
        selected_revision = int(driver.take_snapshot()["revision"])
        with mock.patch.object(
            driver,
            "_history_snapshot",
            wraps=driver._history_snapshot,
        ) as options_history_snapshot:
            queried = driver.execute_step(
                "query-war-termination-options-16777290",
                expected_revision=selected_revision,
            )
        self.assertEqual(options_history_snapshot.call_count, 0)
        self.assertEqual(
            driver.take_snapshot()["native_command_history"][-1]["command"],
            "query-war-termination-options-16777290",
        )
        self.assertEqual(queried["query_sequence"], 9)
        self.assertFalse(
            queried["war_termination_options"]["options"]["surrender"][
                "terms_observable"
            ]
        )
        self.assertEqual(
            queried["war_termination_options"]["options"]["surrender"][
                "ai_acceptance"
            ],
            {"raw": -2_900_000, "scale": 100_000},
        )
        self.assertEqual(
            driver.capabilities()["action_steps"],
            [
                "query-war-termination-options-16777290",
                "query-war-termination-terms-v1-16777290",
            ],
        )
        with mock.patch.object(
            driver,
            "_history_snapshot",
            wraps=driver._history_snapshot,
        ) as terms_history_snapshot:
            driver.execute_step(
                "query-war-termination-terms-v1-16777290"
            )
        self.assertEqual(terms_history_snapshot.call_count, 0)
        self.assertEqual(
            driver.take_snapshot()["native_command_history"][-1]["command"],
            "query-war-termination-terms-v1-16777290",
        )
        self.assertEqual(
            driver.capabilities()["action_steps"],
            [
                "query-war-termination-options-16777290",
                "query-war-termination-terms-v1-16777290",
            ],
        )
        self.assertFalse(
            any(
                step.startswith("offer-white-peace-")
                for step in driver.capabilities()["action_steps"]
            )
        )
        service = GameplayBridgeService(driver)
        with self.assertRaisesRegex(
            BridgeUnavailableError, "fresh same-frame claim_cb"
        ):
            service.execute_step("offer-white-peace-16777290")
        with self.assertRaisesRegex(
            BridgeUnavailableError, "structured_terms_v2"
        ):
            service.execute_step("surrender-war-16777290")
        self.assertFalse(
            any(
                frame.get("type") == "execute_step"
                and frame.get("step")
                in {
                    "offer-white-peace-16777290",
                    "surrender-war-16777290",
                }
                for frame in endpoint.frames
            )
        )
        cached = driver.take_snapshot()["war_termination_options"]
        self.assertEqual(cached[0]["war_id"], war_id)
        self.assertEqual(cached[0]["query_sequence"], 9)

        # A new generation can reuse the low object slot.  It must not inherit
        # the old full-generation WarID's context or validator result.
        replacement_war_id = war_id + (1 << 24)
        endpoint.publish(
            _snapshot(
                41,
                played_character={"character_id": 707, "alive": True},
                active_wars=[_war(war_id=replacement_war_id, score=41)],
            )
        )
        self.assertEqual(driver.take_snapshot()["war_termination_options"], [])
        self.assertEqual(driver.take_snapshot()["war_termination_terms"], [])
        self.assertEqual(
            driver.capabilities()["action_steps"],
            [
                f"query-war-termination-options-{replacement_war_id}",
                f"query-war-termination-terms-v1-{replacement_war_id}",
            ],
        )

    def test_partial_termination_capabilities_never_advertise_an_action(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.command.surrender-war-N",
                "game.command.offer-white-peace-N",
            )
        )
        endpoint.publish(
            _snapshot(40, active_wars=[_war(war_id=16_777_290, score=41)])
        )

        action_steps = driver.capabilities()["action_steps"]

        self.assertNotIn("surrender-war-N", action_steps)
        self.assertNotIn("offer-white-peace-N", action_steps)
        self.assertFalse(
            any(step.startswith("surrender-war-") for step in action_steps)
        )
        self.assertFalse(
            any(
                step.startswith("offer-white-peace-")
                for step in action_steps
            )
        )

    def test_minimal_claim_cb_white_peace_direct_result_tracks_war_identity(
        self,
    ) -> None:
        for remove_war in (False, True):
            with self.subTest(remove_war=remove_war):
                endpoint = FakeEndpoint()
                driver = NativeHeadlessGameplayDriver(
                    endpoint.pipe_name,
                    endpoint=endpoint,
                    command_timeout_seconds=0.1,
                )
                war_id = 16_777_290
                date_raw = 53_177_976
                active_war = _war(
                    war_id=war_id,
                    score=37,
                    targeted_title_ids=[2_388],
                )
                endpoint.publish(
                    _hello(
                        "game.state.snapshot",
                        "game.command.query-war-termination-options-N",
                        "game.command.query-war-termination-terms-v1-N",
                        "game.command.offer-white-peace-N",
                    )
                )
                endpoint.publish(
                    _snapshot(
                        40,
                        date_raw=date_raw,
                        played_character={
                            "character_id": 707,
                            "alive": True,
                        },
                        active_wars=[active_war],
                    )
                )

                def answer(frame: dict[str, object]) -> None:
                    if frame.get("type") != "execute_step":
                        return
                    step = str(frame["step"])
                    if step.startswith("query-war-termination-options-"):
                        result: dict[str, object] = {
                            "step": step,
                            "accepted": True,
                            "status": "available",
                            "query_sequence": 1,
                            "war_termination_options": _termination_options(
                                war_id,
                                score=37,
                                casus_belli_database_index=0,
                                casus_belli_key="claim_cb",
                                war_duration_days=436,
                                white_peace_acceptance_raw=1_279_120,
                            ),
                        }
                    elif step.startswith(
                        "query-war-termination-terms-v1-"
                    ):
                        result = {
                            "step": step,
                            "accepted": True,
                            "status": "available",
                            "query_sequence": 2,
                            "war_termination_terms": _termination_terms(
                                war_id,
                                claimant_character_id=707,
                                target_title_ids=[2_388],
                                strong=False,
                            ),
                        }
                    else:
                        self.assertEqual(
                            step, "offer-white-peace-16777290"
                        )
                        if remove_war:
                            endpoint.publish(
                                _snapshot(
                                    41,
                                    date_raw=date_raw,
                                    played_character={
                                        "character_id": 707,
                                        "alive": True,
                                    },
                                    active_wars=[],
                                )
                            )
                        result = {
                            "step": step,
                            "accepted": True,
                            "status": "submitted",
                        }
                    endpoint.publish(
                        {
                            "type": "command_result",
                            "protocol_version": 1,
                            "request_id": frame["request_id"],
                            "ok": True,
                            "result": result,
                        }
                    )

                endpoint.send_hook = answer
                driver.execute_step(
                    "query-war-termination-options-16777290"
                )
                driver.execute_step(
                    "query-war-termination-terms-v1-16777290"
                )
                self.assertIn(
                    "offer-white-peace-16777290",
                    driver.capabilities()["action_steps"],
                )

                submitted = driver.execute_step(
                    "offer-white-peace-16777290"
                )
                action = submitted["war_termination_result"]

                self.assertEqual(
                    action["status"],
                    "applied" if remove_war else "submitted_pending",
                )
                self.assertEqual(action["war_id"], war_id)
                self.assertEqual(action["outcome"], "white_peace")
                self.assertEqual(
                    action["war_id_absent_after_ack"], remove_war
                )
                self.assertEqual(
                    action["recipient_decision_status_raw"], 0
                )
                self.assertTrue(action["recipient_would_accept_now"])
                if not remove_war:
                    self.assertNotIn(
                        "offer-white-peace-16777290",
                        driver.capabilities()["action_steps"],
                    )

    def test_white_peace_direct_rejects_malformed_ack_and_stale_frame(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=0.1,
        )
        war_id = 16_777_290
        active_war = _war(
            war_id=war_id, score=37, targeted_title_ids=[2_388]
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.command.query-war-termination-options-N",
                "game.command.query-war-termination-terms-v1-N",
                "game.command.offer-white-peace-N",
            )
        )
        endpoint.publish(
            _snapshot(
                40,
                played_character={"character_id": 707, "alive": True},
                active_wars=[active_war],
            )
        )

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            step = str(frame["step"])
            if step.startswith("query-war-termination-options-"):
                result: dict[str, object] = {
                    "step": step,
                    "accepted": True,
                    "status": "available",
                    "query_sequence": 1,
                    "war_termination_options": _termination_options(
                        war_id,
                        score=37,
                        casus_belli_database_index=0,
                        casus_belli_key="claim_cb",
                        war_duration_days=436,
                    ),
                }
            elif step.startswith("query-war-termination-terms-v1-"):
                result = {
                    "step": step,
                    "accepted": True,
                    "status": "available",
                    "query_sequence": 2,
                    "war_termination_terms": _termination_terms(
                        war_id,
                        claimant_character_id=707,
                        target_title_ids=[2_388],
                    ),
                }
            else:
                result = {
                    "step": step,
                    "accepted": True,
                    "status": "available",
                }
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": result,
                }
            )

        endpoint.send_hook = answer
        driver.execute_step("query-war-termination-options-16777290")
        driver.execute_step("query-war-termination-terms-v1-16777290")
        with self.assertRaisesRegex(
            BridgeUnavailableError, "malformed ACK"
        ):
            driver.execute_step("offer-white-peace-16777290")
        self.assertFalse(
            any(
                isinstance(row.get("result"), dict)
                and "war_termination_result" in row["result"]
                for row in driver.take_snapshot()["native_command_history"]
            )
        )

        endpoint.publish(
            _snapshot(
                41,
                played_character={"character_id": 707, "alive": True},
                active_wars=[active_war],
            )
        )
        with self.assertRaisesRegex(
            BridgeUnavailableError, "fresh same-frame"
        ):
            driver.execute_step("offer-white-peace-16777290")

    def test_claim_terms_query_is_same_frame_cached_and_typed(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=0.1,
        )
        war_id = 16_777_290
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.command.query-war-termination-terms-v1-N",
            )
        )
        endpoint.publish(
            _snapshot(
                40,
                played_character={"character_id": 707, "alive": True},
                active_wars=[_war(war_id=war_id, targeted_title_ids=[2_388])],
            )
        )
        self.assertEqual(
            driver.capabilities()["action_steps"],
            ["query-war-termination-terms-v1-16777290"],
        )

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {
                        "step": frame["step"],
                        "accepted": True,
                        "status": "available",
                        "query_sequence": 12,
                        "war_termination_terms": _termination_terms(war_id),
                    },
                }
            )

        endpoint.send_hook = answer
        revision = int(driver.take_snapshot()["revision"])
        result = GameplayBridgeService(driver).query_war_termination_terms(
            war_id, expected_revision=revision
        )
        self.assertEqual(result["query_sequence"], 12)
        self.assertEqual(
            result["war_termination_terms"]["claims"][0]["state"],
            "strong_explicit",
        )
        cached = driver.take_snapshot()["war_termination_terms"]
        self.assertEqual(len(cached), 1)
        self.assertEqual(cached[0]["queried_revision"], revision)
        self.assertEqual(cached[0]["claimant_character_id"], 29_829)

        endpoint.publish(
            _snapshot(
                41,
                played_character={"character_id": 707, "alive": True},
                active_wars=[_war(war_id=war_id, targeted_title_ids=[2_388])],
            )
        )
        self.assertEqual(driver.take_snapshot()["war_termination_terms"], [])

        def answer_unsupported(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {
                        "step": frame["step"],
                        "accepted": True,
                        "status": "unsupported",
                        "query_sequence": 13,
                        "war_termination_terms": _termination_terms(
                            war_id, status="unsupported"
                        ),
                    },
                }
            )

        endpoint.send_hook = answer_unsupported
        unsupported = driver.execute_step(
            "query-war-termination-terms-v1-16777290"
        )
        self.assertEqual(unsupported["status"], "unsupported")
        self.assertNotIn(
            "claimant_character_id", unsupported["war_termination_terms"]
        )

    def test_unsupported_claim_terms_keep_termination_commands_frozen(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=0.1,
        )
        war_id = 16_777_290
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.command.query-war-termination-options-N",
                "game.command.query-war-termination-terms-v1-N",
                "game.command.surrender-war-N",
                "game.command.offer-white-peace-N",
            )
        )
        endpoint.publish(
            _snapshot(
                40,
                played_character={"character_id": 707, "alive": True},
                active_wars=[_war(war_id=war_id, score=41)],
            )
        )

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            is_terms = str(frame["step"]).startswith(
                "query-war-termination-terms-v1-"
            )
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {
                        "step": frame["step"],
                        "accepted": True,
                        "status": "unsupported" if is_terms else "available",
                        "query_sequence": 8 if is_terms else 7,
                        **(
                            {
                                "war_termination_terms": _termination_terms(
                                    war_id, status="unsupported"
                                )
                            }
                            if is_terms
                            else {
                                "war_termination_options": (
                                    _termination_options(
                                        war_id,
                                        casus_belli_database_index=0,
                                        casus_belli_key="claim_cb",
                                    )
                                )
                            }
                        ),
                    },
                }
            )

        endpoint.send_hook = answer
        driver.execute_step("query-war-termination-options-16777290")
        driver.execute_step("query-war-termination-terms-v1-16777290")
        action_steps = driver.capabilities()["action_steps"]
        self.assertFalse(
            any(
                step.startswith(("surrender-war-", "offer-white-peace-"))
                for step in action_steps
            )
        )
        with self.assertRaisesRegex(
            BridgeUnavailableError, "structured_terms_v2"
        ):
            driver.execute_step("surrender-war-16777290")
        self.assertFalse(
            any(
                frame.get("type") == "execute_step"
                and frame.get("step") == "surrender-war-16777290"
                for frame in endpoint.frames
            )
        )

    def test_exit_terms_v2_is_suppressed_even_if_stale_dll_advertises_it(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=0.1,
        )
        exit_terms = _termination_exit_terms_v2()
        war_id = int(exit_terms["war_id"])
        attacker_id = int(exit_terms["primary_attacker_character_id"])
        defender_id = int(exit_terms["primary_defender_character_id"])
        war = _war(
            war_id=war_id,
            targeted_title_ids=list(exit_terms["target_title_ids"]),
        )
        war["primary_opponent_character_id"] = defender_id
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.command.query-war-termination-exit-terms-v2-N",
            )
        )
        endpoint.publish(
            _snapshot(
                40,
                played_character={"character_id": attacker_id, "alive": True},
                active_wars=[war],
            )
        )
        query_step = "query-war-termination-exit-terms-v2-" + str(war_id)
        capabilities = driver.capabilities()
        self.assertFalse(
            capabilities["war_termination_exit_terms_query_supported"]
        )
        self.assertNotIn(query_step, capabilities["action_steps"])
        with self.assertRaisesRegex(
            UnsupportedStepError, "disabled.*RVA 0x334C668"
        ):
            driver.execute_step(query_step)
        with self.assertRaisesRegex(BridgeUnavailableError, "disabled"):
            GameplayBridgeService(driver).query_war_termination_exit_terms(
                war_id, expected_revision=40
            )
        self.assertFalse(
            any(frame.get("type") == "execute_step" for frame in endpoint.frames)
        )
        self.assertEqual(
            driver.take_snapshot()["war_termination_exit_terms"], []
        )

    def test_native_marriage_query_expands_and_submits_exact_choice(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=0.1,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.command.query-arrange-marriage-choices",
                "game.command.arrange-marriage-N",
            )
        )
        endpoint.publish(
            _snapshot(
                40,
                played_character={"character_id": 707, "alive": True},
            )
        )
        choice = {
            "choice_id": "707-808",
            "played_character_id": 707,
            "candidate_character_id": 808,
        }

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            result: dict[str, object] = {
                "step": frame["step"],
                "accepted": True,
                "status": "submitted",
            }
            if frame["step"] == "query-arrange-marriage-choices":
                result.update(
                    {
                        "status": "available",
                        "query_sequence": 4,
                        "arrange_marriage_choices": [choice],
                    }
                )
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": result,
                }
            )

        endpoint.send_hook = answer
        starting = driver.take_snapshot()
        query = driver.execute_step(
            "query-arrange-marriage-choices",
            expected_revision=int(starting["revision"]),
        )
        self.assertEqual(query["arrange_marriage_choices"], [{**choice, "source": "native"}])
        self.assertEqual(
            driver.capabilities()["action_steps"],
            ["arrange-marriage-707-808", "query-arrange-marriage-choices"],
        )

        queried = driver.take_snapshot()
        submitted = driver.execute_step(
            "arrange-marriage-707-808",
            expected_revision=int(queried["revision"]),
        )
        self.assertEqual(
            submitted["marriage_action"]["status"], "proposal_submitted"
        )
        self.assertEqual(
            submitted["marriage_action"]["candidate_character_id"], 808
        )
        self.assertEqual(
            submitted["marriage_action"]["submitted_date_raw"], 53_171_400
        )
        self.assertEqual(driver.take_snapshot()["arrange_marriage_choices"], [])

        endpoint.publish(
            _snapshot(
                41,
                played_character={
                    "character_id": 707,
                    "alive": True,
                    "betrothed_id": None,
                    "primary_spouse_id": 808,
                    "spouse_ids": [808],
                },
            )
        )
        observed = driver.take_snapshot()
        outcome = observed["native_command_history"][-1]["result"][
            "marriage_result"
        ]
        self.assertEqual(outcome["status"], "accepted_marriage")
        self.assertEqual(outcome["candidate_character_id"], 808)
        self.assertEqual(outcome["source"], "native_relationship_snapshot")

    def test_native_raise_and_postwar_disband_wait_for_army_state(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=0.2,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.active-wars",
                "game.command.raise-troops-default",
                "game.command.disband-army-N",
            )
        )
        enemy = _army(
            302,
            soldiers=None,
            province_id=44,
            controllable=False,
        )
        endpoint.publish(
            _snapshot(50, active_wars=[_war(enemy_armies=[enemy])])
        )
        self.assertEqual(
            driver.capabilities()["action_steps"],
            ["raise-troops-default"],
        )

        def answer_raise(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {"status": "submitted"},
                }
            )
            raised = _army(303, province_id=12)
            endpoint.publish(
                _snapshot(
                    51,
                    active_wars=[
                        _war(allied_armies=[raised], enemy_armies=[enemy])
                    ],
                    player_armies=[raised],
                )
            )

        endpoint.send_hook = answer_raise
        raised = driver.execute_step("raise-troops-default")
        self.assertEqual(raised["war_action"]["raised_army_ids"], [303])

        remaining = _army(303, province_id=12)
        endpoint.publish(_snapshot(52, active_wars=[], player_armies=[remaining]))
        self.assertEqual(
            driver.capabilities()["action_steps"], ["disband-army-303"]
        )

        def answer_disband(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {"status": "submitted"},
                }
            )
            endpoint.publish(_snapshot(53, active_wars=[], player_armies=[]))

        endpoint.send_hook = answer_disband
        disbanded = driver.execute_step("disband-army-303")
        self.assertEqual(disbanded["war_action"]["status"], "disbanded")
        self.assertEqual(disbanded["player_armies"], [])

    def test_native_enforce_demands_ends_war_before_more_army_orders(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=0.2,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.active-wars",
                "game.state.war-primary-opponent",
                "game.command.enforce-demands-N",
            )
        )
        won_war = _war(war_id=404)
        won_war["player_relative_war_score"] = 100
        endpoint.publish(_snapshot(60, active_wars=[won_war]))

        snapshot = driver.take_snapshot()
        self.assertIn(
            "enforce-demands-404", driver.capabilities()["action_steps"]
        )
        plan = GameplayBridgeService(driver).plan_turn()["plan"]
        self.assertEqual(plan["phase"], "native_war_enforce_demands")
        self.assertEqual(plan["selected_step"], "enforce-demands-404")

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {"status": "submitted"},
                }
            )
            endpoint.publish(_snapshot(61, active_wars=[]))

        endpoint.send_hook = answer
        result = driver.execute_step(
            "enforce-demands-404",
            expected_revision=int(snapshot["revision"]),
        )

        self.assertEqual(result["war_action"]["status"], "victory_enforced")
        self.assertEqual(result["war_victory"]["war_id"], 404)
        self.assertEqual(result["active_wars"], [])

    def test_native_move_without_target_observation_uses_submission_ack(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=0.01,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.command.move-army-N-to-N",
            )
        )
        player = _army(
            401,
            province_id=None,
            observe_move_target=False,
            route_province_ids=[],
        )
        enemy = _army(402, province_id=90, controllable=False)
        endpoint.publish(
            _snapshot(
                60,
                active_wars=[_war(allied_armies=[player], enemy_armies=[enemy])],
                player_armies=[player],
            )
        )
        projected = driver.take_snapshot()
        self.assertFalse(projected["army_routes_supported"])
        self.assertFalse(projected["move_route_preview_supported"])

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") == "execute_step":
                endpoint.publish(
                    {
                        "type": "command_result",
                        "protocol_version": 1,
                        "request_id": frame["request_id"],
                        "ok": True,
                        "result": {"status": "submitted"},
                    }
                )

        endpoint.send_hook = answer
        result = driver.execute_step("move-army-401-to-90")

        self.assertEqual(result["war_action"]["status"], "move_submitted")
        self.assertFalse(result["war_action"]["move_target_observable"])
        self.assertEqual(
            result["war_action"]["submitted_date_raw"], 53_171_400
        )

    def test_native_move_not_ready_is_a_deferred_war_action(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=0.01,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.command.move-army-N-to-N",
            )
        )
        player = _army(401, province_id=20, observe_move_target=False)
        enemy = _army(402, province_id=90, controllable=False)
        endpoint.publish(
            _snapshot(
                60,
                active_wars=[_war(allied_armies=[player], enemy_armies=[enemy])],
                player_armies=[player],
            )
        )

        native_error = "CK3 army state rejects movement"

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") == "execute_step":
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
        result = driver.execute_step("move-army-401-to-90")

        self.assertFalse(result["accepted"])
        self.assertEqual(result["status"], "deferred")
        self.assertEqual(result["war_action"]["status"], "move_deferred")
        self.assertEqual(
            result["war_action"]["reason"], "army_not_move_ready"
        )

    def test_save_checkpoint_waits_for_isolated_file_materialization(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            save_dir = Path(temporary) / "profile" / "save games"
            save_dir.mkdir(parents=True)
            checkpoint_path = save_dir / "xar_checkpoint.ck3"
            checkpoint_path.write_bytes(b"old checkpoint")
            old_mtime = checkpoint_path.stat().st_mtime_ns
            endpoint = FakeEndpoint()
            driver = NativeHeadlessGameplayDriver(
                endpoint.pipe_name,
                endpoint=endpoint,
                state_dir=Path(temporary) / "state",
                save_dir=save_dir,
                checkpoint_timeout_seconds=1.0,
                checkpoint_poll_interval_seconds=0.005,
            )
            endpoint.publish(
                _hello("game.state.snapshot", "game.command.save-checkpoint")
            )
            endpoint.publish(
                _snapshot(
                    31,
                    date_raw=53_171_424,
                    played_character={"character_id": 707, "alive": True},
                )
            )
            payload = b"materialized native checkpoint"
            timer: threading.Timer | None = None

            def answer(frame: dict[str, object]) -> None:
                nonlocal timer
                if frame.get("type") != "execute_step":
                    return
                endpoint.publish(
                    {
                        "type": "command_result",
                        "protocol_version": 1,
                        "request_id": frame["request_id"],
                        "ok": True,
                        "result": {
                            "step": "save-checkpoint",
                            "accepted": True,
                            "status": "submitted",
                            "submission": {
                                "sequence": 2,
                                "requested_save_name": "xar_checkpoint",
                                "date_raw": 53_171_424,
                            },
                        },
                    }
                )

                def materialize() -> None:
                    checkpoint_path.write_bytes(payload)
                    changed_mtime = old_mtime + 1_000_000_000
                    os.utime(
                        checkpoint_path,
                        ns=(changed_mtime, changed_mtime),
                    )

                timer = threading.Timer(0.02, materialize)
                timer.start()

            endpoint.send_hook = answer
            snapshot = driver.take_snapshot()
            with driver._driver_state_lock:
                driver._rollback_war_failures = [
                    _rollback_failure(
                        {
                            "sha256": "b" * 64,
                            "date_raw": 53_171_400,
                        },
                        target=20,
                        route=[20],
                        run_id=str(snapshot["episode_run_id"]),
                        origin=10,
                    )
                ]
            result = driver.execute_step(
                "save-checkpoint",
                expected_revision=int(snapshot["revision"]),
            )
            if timer is not None:
                timer.join(timeout=1.0)

            checkpoint = result["checkpoint"]
            self.assertEqual(checkpoint["status"], "saved")
            self.assertEqual(checkpoint["name"], "xar_checkpoint.ck3")
            self.assertEqual(checkpoint["path"], str(checkpoint_path.resolve()))
            self.assertEqual(checkpoint["size"], len(payload))
            self.assertEqual(
                checkpoint["sha256"], hashlib.sha256(payload).hexdigest()
            )
            self.assertEqual(checkpoint["date_raw"], 53_171_424)
            self.assertEqual(checkpoint["history_index"], 1)
            self.assertEqual(checkpoint["episode_character_id"], 707)
            self.assertEqual(
                checkpoint["episode_run_id"], snapshot["episode_run_id"]
            )
            self.assertTrue(checkpoint["overwrite_confirmed"])
            self.assertTrue(result["materialization"]["available"])
            self.assertEqual(
                driver.take_snapshot()["native_rollback_war_failures"], []
            )
            seed_path = save_dir / "xar_episode_seed.ck3"
            self.assertEqual(seed_path.read_bytes(), payload)
            self.assertEqual(result["episode_seed"]["name"], seed_path.name)
            self.assertTrue(result["episode_seed"]["immutable"])
            persisted = json.loads(
                (
                    Path(temporary)
                    / "state"
                    / "native-session"
                    / "driver-state.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(persisted["last_checkpoint"], checkpoint)
            self.assertEqual(
                persisted["command_history"][checkpoint["history_index"] - 1][
                    "command"
                ],
                "save-checkpoint",
            )
            self.assertFalse(driver._driver_state_dirty)
            plan = GameplayBridgeService(driver).plan_turn()["plan"]
            self.assertNotEqual(plan.get("selected_step"), "save-checkpoint")
            self.assertEqual(plan.get("required_step"), "dynasty-review")

    def test_later_recovery_checkpoint_does_not_replace_episode_seed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            save_dir = root / "profile" / "save games"
            save_dir.mkdir(parents=True)
            checkpoint_path = save_dir / "xar_checkpoint.ck3"
            checkpoint_path.write_bytes(b"old")
            endpoint = FakeEndpoint()
            driver = NativeHeadlessGameplayDriver(
                endpoint.pipe_name,
                endpoint=endpoint,
                state_dir=root,
                save_dir=save_dir,
                checkpoint_timeout_seconds=1.0,
                checkpoint_poll_interval_seconds=0.005,
            )
            endpoint.publish(
                _hello("game.state.snapshot", "game.command.save-checkpoint")
            )
            endpoint.publish(
                _snapshot(1, played_character={"character_id": 707, "alive": True})
            )
            payloads = iter((b"baseline-seed", b"later-recovery"))

            def answer(frame: dict[str, object]) -> None:
                if frame.get("type") != "execute_step":
                    return
                payload = next(payloads)
                endpoint.publish(
                    {
                        "type": "command_result",
                        "protocol_version": 1,
                        "request_id": frame["request_id"],
                        "ok": True,
                        "result": {
                            "accepted": True,
                            "submission": {"date_raw": 53_171_400},
                        },
                    }
                )
                previous = checkpoint_path.stat().st_mtime_ns
                checkpoint_path.write_bytes(payload)
                os.utime(checkpoint_path, ns=(previous + 1, previous + 1))

            endpoint.send_hook = answer
            driver.execute_step("save-checkpoint")
            first_seed = (save_dir / "xar_episode_seed.ck3").read_bytes()
            driver.execute_step("save-checkpoint")

            self.assertEqual(first_seed, b"baseline-seed")
            self.assertEqual(
                (save_dir / "xar_episode_seed.ck3").read_bytes(), first_seed
            )
            self.assertEqual(checkpoint_path.read_bytes(), b"later-recovery")

    def test_start_next_episode_rebinds_same_character_to_new_run(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            save_dir = state_dir / "profile" / "save games"
            save_dir.mkdir(parents=True)
            seed_payload = b"immutable episode seed"
            seed_path = save_dir / "xar_episode_seed.ck3"
            seed_path.write_bytes(seed_payload)
            seed = {
                "format_version": 1,
                "name": seed_path.name,
                "path": str(seed_path.resolve()),
                "size": len(seed_payload),
                "sha256": hashlib.sha256(seed_payload).hexdigest(),
                "date_raw": 53_168_784,
                "character_id": 707,
                "source_run_id": "native-707-seed-source",
                "immutable": True,
            }
            write_json_atomic(
                state_dir / "native-session" / "episode-seed.json", seed
            )
            endpoint = FakeEndpoint()
            driver = NativeHeadlessGameplayDriver(
                endpoint.pipe_name,
                endpoint=endpoint,
                state_dir=state_dir,
                save_dir=save_dir,
                restore_timeout_seconds=1.5,
                restore_poll_interval_seconds=0.005,
            )
            endpoint.publish(
                _hello(
                    "game.state.snapshot",
                    "game.state.played-character",
                    ONE_LIFE_SETTLEMENT_CAPABILITY,
                )
            )
            endpoint.publish(
                _snapshot(
                    30,
                    date_raw=53_171_400,
                    played_character={"character_id": 707, "alive": False},
                    one_life_settlement=_one_life_settlement(),
                )
            )
            terminal_snapshot = driver.take_snapshot()
            source_run_id = terminal_snapshot["episode_run_id"]
            driver.execute_step(
                "death-terminal",
                expected_revision=int(terminal_snapshot["revision"]),
            )
            self.assertIn(
                "start-next-episode", driver.capabilities()["action_steps"]
            )
            terminal_plan = GameplayBridgeService(driver).plan_turn()["plan"]
            self.assertEqual(
                terminal_plan["selected_step"], "start-next-episode"
            )
            errors: list[BaseException] = []

            def lifecycle() -> None:
                try:
                    inbox = state_dir / "native-session" / "bridge" / "inbox"
                    deadline = time.monotonic() + 1.0
                    paths: list[Path] = []
                    while time.monotonic() < deadline:
                        paths = list(inbox.glob("next-episode-*.json"))
                        if paths:
                            break
                        time.sleep(0.005)
                    self.assertEqual(len(paths), 1)
                    request = json.loads(paths[0].read_text(encoding="utf-8"))
                    assert endpoint.on_disconnect is not None
                    endpoint.on_disconnect()
                    write_json_atomic(
                        paths[0].parents[1] / "outbox" / paths[0].name,
                        {
                            "protocol_version": 1,
                            "request_id": paths[0].stem,
                            "ok": True,
                            "result": {
                                "status": "relaunched",
                                "previous_pid": 4242,
                                "pid": 5252,
                                "pipe": endpoint.pipe_name,
                                "load_save_name": "xar_episode_seed",
                                "lifecycle_intent": "new_episode",
                                "episode_seed": seed,
                            },
                            "error": None,
                        },
                    )
                    endpoint.publish(
                        {**_hello("game.state.snapshot"), "pid": 5252}
                    )
                    endpoint.publish(
                        _snapshot(
                            1,
                            date_raw=53_168_784,
                            played_character={"character_id": 707, "alive": True},
                        )
                    )
                    self.assertEqual(request["source_run_id"], source_run_id)
                except BaseException as error:
                    errors.append(error)

            worker = threading.Thread(target=lifecycle)
            worker.start()
            result = driver.execute_step(
                "start-next-episode",
                expected_revision=int(driver.take_snapshot()["revision"]),
            )
            worker.join(timeout=2.0)

            self.assertEqual(errors, [])
            self.assertEqual(result["lifecycle_intent"], "new_episode")
            self.assertEqual(result["source_run_id"], source_run_id)
            self.assertNotEqual(result["episode_run_id"], source_run_id)
            self.assertEqual(result["episode_character_id"], 707)
            self.assertTrue(result["same_character_id"])
            self.assertIsInstance(result["cross_run_plan_used"], dict)
            current = driver.take_snapshot()
            self.assertFalse(current["one_life_terminal"])
            self.assertEqual(
                current["native_command_history"][0]["command"],
                "start-next-episode",
            )

    def test_start_next_episode_rejects_terminal_without_complete_score(self) -> None:
        endpoint = FakeEndpoint()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            save_dir = root / "profile" / "save games"
            save_dir.mkdir(parents=True)
            seed_path = save_dir / "xar_episode_seed.ck3"
            seed_path.write_bytes(b"seed")
            write_json_atomic(
                root / "native-session" / "episode-seed.json",
                {
                    "format_version": 1,
                    "name": seed_path.name,
                    "size": 4,
                    "sha256": hashlib.sha256(b"seed").hexdigest(),
                    "date_raw": 53_168_784,
                    "character_id": 707,
                    "source_run_id": "seed-run",
                    "immutable": True,
                },
            )
            driver = NativeHeadlessGameplayDriver(
                endpoint.pipe_name,
                endpoint=endpoint,
                state_dir=root,
                save_dir=save_dir,
            )
            endpoint.publish(
                _hello("game.state.snapshot", "game.state.played-character")
            )
            endpoint.publish(
                _snapshot(
                    2,
                    played_character={"character_id": 707, "alive": False},
                )
            )
            terminal = driver.take_snapshot()
            unavailable = driver.execute_step(
                "death-terminal", expected_revision=int(terminal["revision"])
            )

            self.assertEqual(
                unavailable["settlement_status"], "settlement_unavailable"
            )
            self.assertNotIn(
                "start-next-episode", driver.capabilities()["action_steps"]
            )
            with self.assertRaises(UnsupportedStepError):
                driver.execute_step("start-next-episode")

    def test_save_checkpoint_without_directory_keeps_submission_explicit(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello("game.state.snapshot", "game.command.save-checkpoint")
        )
        endpoint.publish(_snapshot(8, date_raw=53_171_448))

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") == "execute_step":
                endpoint.publish(
                    {
                        "type": "command_result",
                        "protocol_version": 1,
                        "request_id": frame["request_id"],
                        "ok": True,
                        "result": {
                            "step": "save-checkpoint",
                            "accepted": True,
                            "status": "submitted",
                            "submission": {
                                "sequence": 1,
                                "requested_save_name": "xar_checkpoint",
                                "date_raw": 53_171_448,
                            },
                        },
                    }
                )

        endpoint.send_hook = answer
        result = driver.execute_step("save-checkpoint")

        self.assertTrue(result["accepted"])
        self.assertEqual(
            result["checkpoint"]["status"], "materialization_unavailable"
        )
        self.assertIsNone(result["checkpoint"]["path"])
        self.assertFalse(result["materialization"]["available"])
        self.assertEqual(
            result["materialization"]["reason"], "save_dir_not_configured"
        )

    def test_restore_checkpoint_relaunches_and_waits_for_new_map_generation(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            save_dir = state_dir / "profile" / "save games"
            save_dir.mkdir(parents=True)
            checkpoint_path = save_dir / "xar_checkpoint.ck3"
            checkpoint_payload = b"native restore checkpoint fixture"
            checkpoint_path.write_bytes(checkpoint_payload)
            endpoint = FakeEndpoint()
            driver = NativeHeadlessGameplayDriver(
                endpoint.pipe_name,
                endpoint=endpoint,
                state_dir=state_dir,
                save_dir=save_dir,
                restore_timeout_seconds=3.0,
                restore_poll_interval_seconds=0.005,
            )
            endpoint.publish(_hello("game.state.snapshot"))
            endpoint.publish(
                _snapshot(
                    40,
                    date_raw=53_171_520,
                    played_character={"character_id": 707, "alive": True},
                )
            )
            lifecycle_errors: list[BaseException] = []
            observed_request: dict[str, object] = {}

            def lifecycle() -> None:
                try:
                    inbox = (
                        state_dir
                        / "native-session"
                        / "bridge"
                        / "inbox"
                    )
                    deadline = time.monotonic() + 1.0
                    request_paths: list[Path] = []
                    while time.monotonic() < deadline:
                        request_paths = list(inbox.glob("restore-*.json"))
                        if request_paths:
                            break
                        time.sleep(0.005)
                    self.assertEqual(len(request_paths), 1)
                    request_path = request_paths[0]
                    observed_request.update(
                        json.loads(request_path.read_text(encoding="utf-8"))
                    )
                    assert endpoint.on_disconnect is not None
                    endpoint.on_disconnect()
                    outbox = request_path.parents[1] / "outbox"
                    write_json_atomic(
                        outbox / request_path.name,
                        {
                            "protocol_version": 1,
                            "request_id": request_path.stem,
                            "ok": True,
                            "result": {
                                "status": "relaunched",
                                "previous_pid": 4242,
                                "pid": 5252,
                                "pipe": endpoint.pipe_name,
                                "continue_last_save": False,
                                "load_save_name": "xar_checkpoint",
                                "checkpoint": {
                                    "name": "xar_checkpoint.ck3",
                                    "size": len(checkpoint_payload),
                                    "sha256": hashlib.sha256(
                                        checkpoint_payload
                                    ).hexdigest(),
                                    "saved_date_raw": None,
                                },
                            },
                            "error": None,
                        },
                    )
                    endpoint.publish(
                        {
                            **_hello("game.state.snapshot"),
                            "pid": 5252,
                            "session_generation": 1,
                        }
                    )
                    endpoint.publish(
                        _snapshot(
                            1,
                            date_raw=53_171_400,
                            map_ready=True,
                            played_character=None,
                        )
                    )
                    # CK3 can publish map_ready while the loaded save still has
                    # no playable character.  Keep this transient frame alive
                    # longer than the ordinary semantic stability window: it
                    # must never be accepted as the restored episode identity.
                    time.sleep(0.6)
                    endpoint.publish(
                        _snapshot(
                            2,
                            date_raw=53_171_424,
                            map_ready=True,
                            played_character={
                                "character_id": 707,
                                "alive": True,
                            },
                        )
                    )
                except BaseException as error:
                    lifecycle_errors.append(error)

            worker = threading.Thread(target=lifecycle)
            worker.start()
            snapshot = driver.take_snapshot()
            self.assertIn(
                "restore-checkpoint", driver.capabilities()["action_steps"]
            )
            result = driver.execute_step(
                "restore-checkpoint",
                expected_revision=int(snapshot["revision"]),
            )
            worker.join(timeout=1.0)

            self.assertFalse(worker.is_alive())
            self.assertEqual(lifecycle_errors, [])
            self.assertEqual(
                observed_request["command"], "restore-checkpoint"
            )
            self.assertEqual(observed_request["pipe"], endpoint.pipe_name)
            self.assertEqual(
                observed_request["checkpoint_name"], "xar_checkpoint.ck3"
            )
            self.assertEqual(
                observed_request["checkpoint_size"], len(checkpoint_payload)
            )
            self.assertEqual(
                observed_request["checkpoint_sha256"],
                hashlib.sha256(checkpoint_payload).hexdigest(),
            )
            self.assertEqual(result["status"], "restored")
            self.assertEqual(result["restored_date_raw"], 53_171_424)
            self.assertEqual(result["checkpoint"]["status"], "restored")
            self.assertEqual(
                result["checkpoint"]["sha256"],
                hashlib.sha256(checkpoint_payload).hexdigest(),
            )
            self.assertEqual(
                result["lifecycle"]["previous_connection_generation"], 1
            )
            self.assertEqual(result["lifecycle"]["connection_generation"], 2)
            self.assertEqual(result["lifecycle"]["previous_pid"], 4242)
            self.assertEqual(result["lifecycle"]["pid"], 5252)
            self.assertTrue(result["map_ready"])
            restored_snapshot = driver.take_snapshot()
            self.assertEqual(restored_snapshot["episode_character_id"], 707)
            self.assertFalse(restored_snapshot["one_life_terminal"])
            self.assertIsNone(restored_snapshot["one_life_terminal_reason"])

    def test_composite_life_advance_resolves_native_event_and_stays_paused(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            life_advance_timeout_seconds=1.0,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.active-event",
                "game.command.pause-map",
                "game.command.resume-map",
                "game.command.set-speed-1",
                "game.command.set-speed-3",
                "game.command.set-speed-5",
                "game.command.select-event-option-N",
            )
        )
        endpoint.publish(_snapshot(1, map_ready=False))
        timers: list[threading.Timer] = []

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            step = str(frame["step"])
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {"step": step, "accepted": True},
                }
            )
            if step == "set-speed-5":
                endpoint.publish(_snapshot(3, speed=5))
            elif step == "resume-map":
                endpoint.publish(_snapshot(4, speed=5, paused=False))
                timer = threading.Timer(
                    0.01,
                    lambda: endpoint.publish(
                        _snapshot(
                            5,
                            date_raw=53_171_424,
                            speed=5,
                            paused=False,
                            active_event={"instance_id": 77, "option_count": 2},
                        )
                    ),
                )
                timers.append(timer)
                timer.start()
            elif step == "pause-map":
                endpoint.publish(
                    _snapshot(
                        6,
                        date_raw=53_171_424,
                        speed=5,
                        active_event={"instance_id": 77, "option_count": 2},
                    )
                )
            elif step == "select-event-option-1":
                endpoint.publish(
                    _snapshot(7, date_raw=53_171_424, speed=5, paused=True)
                )

        endpoint.send_hook = answer
        capabilities = driver.capabilities()
        self.assertIn("life-advance", capabilities["action_steps"])
        self.assertEqual(capabilities["composite_action_steps"], ["life-advance"])
        starting_revision = int(driver.take_snapshot()["revision"])
        ready_timer = threading.Timer(
            0.1, lambda: endpoint.publish(_snapshot(2, map_ready=True))
        )
        timers.append(ready_timer)
        ready_timer.start()

        result = driver.execute_step(
            "life-advance", expected_revision=starting_revision
        )
        for timer in timers:
            timer.join(timeout=1.0)

        commands = [
            frame["step"]
            for frame in endpoint.frames
            if frame.get("type") == "execute_step"
        ]
        self.assertEqual(
            commands,
            [
                "set-speed-5",
                "resume-map",
                "pause-map",
                "select-event-option-1",
            ],
        )
        self.assertEqual(result["starting_date_raw"], 53_171_400)
        self.assertEqual(result["ending_date_raw"], 53_171_424)
        self.assertEqual(result["elapsed_days"], 1)
        self.assertTrue(result["paused"])
        self.assertEqual(result["event_resolution"], "selected")
        self.assertEqual(
            result["ordinary_events"][0]["selected_option_number"], 1
        )
        self.assertIsNone(result["active_event"])

    def test_composite_life_advance_can_stop_after_date_without_event(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            life_advance_timeout_seconds=0.1,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.army-routes",
                "game.state.war-objective-assault",
                "game.command.pause-map",
                "game.command.resume-map",
                "game.command.set-speed-1",
                "game.command.set-speed-3",
                "game.command.set-speed-5",
            )
        )
        endpoint.publish(_snapshot(1))
        driver.take_snapshot()
        endpoint.publish(_snapshot(2, date_raw=53_171_424))
        starting_revision = int(driver.take_snapshot()["revision"])

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            step = str(frame["step"])
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {"step": step, "accepted": True},
                }
            )
            if step == "set-speed-5":
                endpoint.publish(
                    _snapshot(3, date_raw=53_171_424, speed=5)
                )
            elif step == "resume-map":
                endpoint.publish(
                    _snapshot(
                        4,
                        date_raw=53_171_448,
                        speed=5,
                        paused=False,
                    )
                )
            elif step == "pause-map":
                endpoint.publish(
                    _snapshot(5, date_raw=53_171_448, speed=5, paused=True)
                )

        endpoint.send_hook = answer
        result = driver.execute_step(
            "life-advance", expected_revision=starting_revision
        )

        self.assertEqual(result["ordinary_events"], [])
        self.assertEqual(result["event_resolution"], "none")
        self.assertEqual(result["starting_date_raw"], 53_171_424)
        self.assertEqual(result["ending_date_raw"], 53_171_448)
        self.assertEqual(result["elapsed_days"], 1)
        self.assertTrue(result["paused"])

    def test_life_advance_bounds_full_history_copies_with_large_transcript(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            life_advance_timeout_seconds=0.1,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.command.pause-map",
                "game.command.resume-map",
                "game.command.set-speed-1",
                "game.command.set-speed-3",
                "game.command.set-speed-5",
            )
        )
        route_army = _army(
            501,
            province_id=10,
            move_target_province_id=20,
            army_state="moving",
            army_state_code=7,
            route_province_ids=[20],
        )
        endpoint.publish(_snapshot(1, player_armies=[route_army]))
        with driver._history_lock:
            driver._command_history = [
                {
                    "index": index,
                    "command": f"query-frozen-history-{index}",
                    "ok": True,
                    "result": {
                        "values": list(range(256)),
                        "label": f"frozen-history-{index}",
                    },
                }
                for index in range(1, 4097)
            ]
        internal = driver.take_internal_semantic_snapshot()
        public = driver.take_snapshot()
        self.assertNotIn("native_command_history", internal)
        self.assertEqual(len(public["native_command_history"]), 4096)
        with mock.patch.object(
            driver, "_with_internal_planning_view", None
        ):
            public_plan = GameplayBridgeService(driver).plan_turn()
        with mock.patch.object(
            driver,
            "_history_snapshot",
            wraps=driver._history_snapshot,
        ) as planning_history_snapshot:
            planned = GameplayBridgeService(driver).plan_turn()
        self.assertEqual(planned, public_plan)
        self.assertEqual(planning_history_snapshot.call_count, 0)

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            step = str(frame["step"])
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {"step": step, "accepted": True},
                }
            )
            if step == "set-speed-1":
                endpoint.publish(
                    _snapshot(2, speed=1, player_armies=[route_army])
                )
            elif step == "resume-map":
                endpoint.publish(
                    _snapshot(
                        3,
                        date_raw=53_171_424,
                        speed=1,
                        paused=False,
                        player_armies=[route_army],
                    )
                )
            elif step == "pause-map":
                endpoint.publish(
                    _snapshot(
                        4,
                        date_raw=53_171_424,
                        speed=1,
                        player_armies=[route_army],
                    )
                )

        endpoint.send_hook = answer
        with mock.patch.object(
            driver,
            "_history_snapshot",
            wraps=driver._history_snapshot,
        ) as history_snapshot:
            result = driver.execute_step("life-advance")

        self.assertTrue(result["paused"])
        self.assertEqual(result["timeline_speed"], 1)
        self.assertEqual(history_snapshot.call_count, 0)

    def test_paused_life_advance_rejects_stale_revision_before_resume(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            life_advance_timeout_seconds=0.1,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.command.pause-map",
                "game.command.resume-map",
                "game.command.set-speed-1",
                "game.command.set-speed-3",
                "game.command.set-speed-5",
            )
        )
        endpoint.publish(_snapshot(1))
        stale_revision = int(driver.take_snapshot()["revision"])
        endpoint.publish(_snapshot(2, date_raw=53_171_424))

        with self.assertRaisesRegex(
            BridgeUnavailableError, "life-advance revision mismatch"
        ):
            driver.execute_step(
                "life-advance", expected_revision=stale_revision
            )

        self.assertFalse(
            any(
                frame.get("type") == "execute_step"
                for frame in endpoint.frames
            )
        )

    def test_active_war_life_advance_ignores_day_tick_and_enemy_motion(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            life_advance_timeout_seconds=0.2,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.command.pause-map",
                "game.command.resume-map",
                "game.command.set-speed-1",
                "game.command.set-speed-3",
                "game.command.set-speed-5",
            )
        )
        start_date = 53_171_400
        player = _army(501, province_id=20)
        enemy = _army(502, province_id=90, controllable=False)
        starting_war = _war(
            allied_armies=[player],
            enemy_armies=[enemy],
            war_objective_province_ids=[2585],
            enemy_primary_default_raise_province_id=2543,
        )
        endpoint.publish(
            _snapshot(
                70,
                date_raw=start_date,
                active_wars=[starting_war],
                player_armies=[player],
            )
        )
        timers: list[threading.Timer] = []

        def publish_running(
            revision: int,
            *,
            date_raw: int,
            score: int,
            enemy_province_id: int,
        ) -> None:
            moved_enemy = _army(
                502,
                province_id=enemy_province_id,
                controllable=False,
            )
            endpoint.publish(
                _snapshot(
                    revision,
                    date_raw=date_raw,
                    speed=5,
                    paused=False,
                    active_wars=[
                        _war(
                            allied_armies=[player],
                            enemy_armies=[moved_enemy],
                            score=score,
                            war_objective_province_ids=[2585],
                            enemy_primary_default_raise_province_id=2543,
                        )
                    ],
                    player_armies=[player],
                )
            )

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            step = str(frame["step"])
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {"step": step, "accepted": True},
                }
            )
            if step == "set-speed-5":
                endpoint.publish(
                    _snapshot(
                        71,
                        date_raw=start_date,
                        speed=5,
                        active_wars=[starting_war],
                        player_armies=[player],
                    )
                )
            elif step == "resume-map":
                publish_running(
                    72,
                    date_raw=start_date,
                    score=12,
                    enemy_province_id=90,
                )
                day_tick = threading.Timer(
                    0.01,
                    lambda: publish_running(
                        73,
                        date_raw=start_date + 24,
                        score=12,
                        enemy_province_id=91,
                    ),
                )
                score_tick = threading.Timer(
                    0.03,
                    lambda: publish_running(
                        74,
                        date_raw=start_date + 48,
                        score=13,
                        enemy_province_id=92,
                    ),
                )
                timers.extend((day_tick, score_tick))
                day_tick.start()
                score_tick.start()
            elif step == "pause-map":
                endpoint.publish(
                    _snapshot(
                        75,
                        date_raw=start_date + 48,
                        speed=5,
                        paused=True,
                        active_wars=[
                            _war(
                                allied_armies=[player],
                                enemy_armies=[enemy],
                                score=13,
                                war_objective_province_ids=[2585],
                                enemy_primary_default_raise_province_id=2543,
                            )
                        ],
                        player_armies=[player],
                    )
                )

        endpoint.send_hook = answer
        result = driver.execute_step("life-advance")
        for timer in timers:
            timer.join(timeout=1.0)

        self.assertEqual(result["elapsed_days"], 2)
        self.assertEqual(result["progress_status"], "postcondition")
        self.assertTrue(result["paused"])
        self.assertEqual(result["war_progress_before"]["date_raw"], start_date)
        self.assertEqual(
            result["war_progress_before"]["wars"][0][
                "player_relative_war_score"
            ],
            12,
        )
        self.assertEqual(
            result["war_progress_before"]["wars"][0][
                "war_objective_province_ids"
            ],
            [2585],
        )
        self.assertEqual(
            result["war_progress_before"]["wars"][0][
                "enemy_primary_default_raise_province_id"
            ],
            2543,
        )
        self.assertEqual(
            result["war_progress_before"]["wars"][0]["player_armies"][0],
            {
                "army_id": 501,
                "current_province_id": 20,
                "soldiers": 1_000,
                "move_target_province_id": None,
            },
        )
        self.assertEqual(result["war_progress_after"]["date_raw"], start_date + 48)
        self.assertEqual(
            result["war_progress_after"]["wars"][0][
                "player_relative_war_score"
            ],
            13,
        )

    def test_active_war_life_advance_stops_on_stationary_army_threat(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            life_advance_timeout_seconds=0.2,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.army-routes",
                "game.state.war-objective-assault",
                "game.command.pause-map",
                "game.command.resume-map",
                "game.command.set-speed-1",
                "game.command.set-speed-3",
                "game.command.set-speed-5",
            )
        )
        start_date = 53_171_400
        player = _army(
            501,
            province_id=2585,
            army_state="sieging",
            route_province_ids=[],
        )
        starting_enemy = _army(
            502,
            province_id=2600,
            controllable=False,
            move_target_province_id=2596,
            army_state="moving",
            route_province_ids=[2596],
        )
        ordinary_enemy = _army(
            502,
            province_id=2599,
            controllable=False,
            move_target_province_id=2596,
            army_state="moving",
            route_province_ids=[],
        )
        threatening_enemy = _army(
            502,
            province_id=2599,
            controllable=False,
            move_target_province_id=2585,
            army_state="moving",
            route_province_ids=[2585],
        )

        def war(enemy: dict[str, object]) -> dict[str, object]:
            return _war(
                allied_armies=[player],
                enemy_armies=[enemy],
                war_objective_province_ids=[2585, 2510],
            )

        starting_war = war(starting_enemy)
        endpoint.publish(
            _snapshot(
                80,
                date_raw=start_date,
                active_wars=[starting_war],
                player_armies=[player],
            )
        )
        threat_published = threading.Event()
        pause_before_threat: list[bool] = []
        timers: list[threading.Timer] = []

        def publish_running(
            revision: int,
            date_raw: int,
            enemy: dict[str, object],
        ) -> None:
            endpoint.publish(
                _snapshot(
                    revision,
                    date_raw=date_raw,
                    speed=3,
                    paused=False,
                    active_wars=[war(enemy)],
                    player_armies=[player],
                )
            )

        def publish_threat() -> None:
            threat_published.set()
            publish_running(84, start_date + 48, threatening_enemy)

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            step = str(frame["step"])
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {"step": step, "accepted": True},
                }
            )
            if step == "set-speed-3":
                endpoint.publish(
                    _snapshot(
                        81,
                        date_raw=start_date,
                        speed=3,
                        active_wars=[starting_war],
                        player_armies=[player],
                    )
                )
            elif step == "resume-map":
                publish_running(82, start_date, starting_enemy)
                ordinary = threading.Timer(
                    0.01,
                    lambda: publish_running(
                        83, start_date + 24, ordinary_enemy
                    ),
                )
                threat = threading.Timer(0.03, publish_threat)
                timers.extend((ordinary, threat))
                ordinary.start()
                threat.start()
            elif step == "pause-map":
                pause_before_threat.append(not threat_published.is_set())
                endpoint.publish(
                    _snapshot(
                        85,
                        date_raw=start_date + 24,
                        speed=3,
                        paused=True,
                        active_wars=[war(threatening_enemy)],
                        player_armies=[player],
                    )
                )

        endpoint.send_hook = answer
        result = driver.execute_step("life-advance")
        for timer in timers:
            timer.join(timeout=1.0)

        self.assertEqual(pause_before_threat, [True])
        self.assertEqual(result["elapsed_days"], 1)
        self.assertEqual(result["requested_horizon_days"], 1)
        self.assertEqual(result["progress_status"], "postcondition")
        self.assertEqual(result["timeline_policy"], "remote_enemy_route")
        self.assertTrue(result["paused"])
        self.assertEqual(
            result["war_progress_after"]["wars"][0]["enemy_armies"][0][
                "route_province_ids"
            ],
            [2585],
        )
        submitted_steps = [
            frame.get("step")
            for frame in endpoint.frames
            if frame.get("type") == "execute_step"
        ]
        self.assertEqual(
            submitted_steps, ["set-speed-3", "resume-map", "pause-map"]
        )

    def test_active_war_life_advance_wall_timeout_keeps_date_progress(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            life_advance_timeout_seconds=0.05,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.command.pause-map",
                "game.command.resume-map",
                "game.command.set-speed-1",
                "game.command.set-speed-3",
                "game.command.set-speed-5",
            )
        )
        start_date = 53_171_400
        player = _army(501, province_id=20)
        war = _war(allied_armies=[player])
        endpoint.publish(
            _snapshot(
                80,
                date_raw=start_date,
                active_wars=[war],
                player_armies=[player],
            )
        )
        timer: threading.Timer | None = None

        def answer(frame: dict[str, object]) -> None:
            nonlocal timer
            if frame.get("type") != "execute_step":
                return
            step = str(frame["step"])
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {"step": step, "accepted": True},
                }
            )
            if step == "set-speed-5":
                endpoint.publish(
                    _snapshot(
                        81,
                        date_raw=start_date,
                        speed=5,
                        active_wars=[war],
                        player_armies=[player],
                    )
                )
            elif step == "resume-map":
                endpoint.publish(
                    _snapshot(
                        82,
                        date_raw=start_date,
                        speed=5,
                        paused=False,
                        active_wars=[war],
                        player_armies=[player],
                    )
                )
                timer = threading.Timer(
                    0.01,
                    lambda: endpoint.publish(
                        _snapshot(
                            83,
                            date_raw=start_date + 24,
                            speed=5,
                            paused=False,
                            active_wars=[war],
                            player_armies=[player],
                        )
                    ),
                )
                timer.start()
            elif step == "pause-map":
                endpoint.publish(
                    _snapshot(
                        84,
                        date_raw=start_date + 24,
                        speed=5,
                        paused=True,
                        active_wars=[war],
                        player_armies=[player],
                    )
                )

        endpoint.send_hook = answer
        result = driver.execute_step("life-advance")
        if timer is not None:
            timer.join(timeout=1.0)

        self.assertEqual(result["elapsed_days"], 1)
        self.assertEqual(
            result["progress_status"], "wall_timeout_with_date_progress"
        )
        self.assertTrue(result["paused"])

    def test_active_war_life_advance_stops_at_thirty_day_horizon(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            life_advance_timeout_seconds=0.1,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.command.pause-map",
                "game.command.resume-map",
                "game.command.set-speed-1",
                "game.command.set-speed-3",
                "game.command.set-speed-5",
            )
        )
        start_date = 53_171_400
        player = _army(501, province_id=20)
        war = _war(allied_armies=[player])
        endpoint.publish(
            _snapshot(
                90,
                date_raw=start_date,
                active_wars=[war],
                player_armies=[player],
            )
        )

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            step = str(frame["step"])
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {"step": step, "accepted": True},
                }
            )
            if step == "set-speed-5":
                endpoint.publish(
                    _snapshot(
                        91,
                        date_raw=start_date,
                        speed=5,
                        active_wars=[war],
                        player_armies=[player],
                    )
                )
            elif step == "resume-map":
                endpoint.publish(
                    _snapshot(
                        92,
                        date_raw=start_date + 30 * 24,
                        speed=5,
                        paused=False,
                        active_wars=[war],
                        player_armies=[player],
                    )
                )
            elif step == "pause-map":
                endpoint.publish(
                    _snapshot(
                        93,
                        date_raw=start_date + 30 * 24,
                        speed=5,
                        paused=True,
                        active_wars=[war],
                        player_armies=[player],
                    )
                )

        endpoint.send_hook = answer
        result = driver.execute_step("life-advance")

        self.assertEqual(result["elapsed_days"], 30)
        self.assertEqual(result["progress_status"], "postcondition")
        self.assertTrue(result["paused"])

    def test_active_route_composite_stops_after_one_game_day(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            life_advance_timeout_seconds=0.1,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.army-routes",
                "game.command.pause-map",
                "game.command.resume-map",
                "game.command.set-speed-1",
                "game.command.set-speed-3",
                "game.command.set-speed-5",
            )
        )
        start_date = 53_176_368
        player = _army(
            501,
            province_id=2597,
            move_target_province_id=2596,
            route_province_ids=[2596],
            army_state="moving",
        )
        war = _war(allied_armies=[player])
        endpoint.publish(
            _snapshot(
                90,
                date_raw=start_date,
                active_wars=[war],
                player_armies=[player],
            )
        )
        paused_dates: list[int] = []

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            step = str(frame["step"])
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {"step": step, "accepted": True},
                }
            )
            if step == "set-speed-1":
                endpoint.publish(
                    _snapshot(
                        91,
                        date_raw=start_date,
                        speed=1,
                        active_wars=[war],
                        player_armies=[player],
                    )
                )
            elif step == "resume-map":
                endpoint.publish(
                    _snapshot(
                        92,
                        date_raw=start_date + 24,
                        speed=1,
                        paused=False,
                        active_wars=[war],
                        player_armies=[player],
                    )
                )
            elif step == "pause-map":
                paused_dates.append(start_date + 24)
                endpoint.publish(
                    _snapshot(
                        93,
                        date_raw=start_date + 24,
                        speed=1,
                        paused=True,
                        active_wars=[war],
                        player_armies=[player],
                    )
                )

        endpoint.send_hook = answer
        result = driver.execute_step("life-advance")

        self.assertEqual(paused_dates, [start_date + 24])
        self.assertEqual(result["elapsed_days"], 1)
        self.assertEqual(result["progress_status"], "postcondition")
        self.assertTrue(result["paused"])

    def test_player_siege_uses_seven_day_horizon_and_ignores_running_gap(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            life_advance_timeout_seconds=0.2,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.state.war-objective-occupation",
                "game.state.war-objective-fort-level",
                "game.state.war-objective-garrison",
                "game.state.war-objective-siege-progress",
                "game.command.pause-map",
                "game.command.resume-map",
                "game.command.set-speed-1",
                "game.command.set-speed-3",
                "game.command.set-speed-5",
            )
        )
        start_date = 53_171_400
        player = _army(
            101,
            province_id=2585,
            army_state="sieging",
            army_state_code=3,
        )

        def war(*, paused_rich: bool, progressed: bool = False):
            return _war(
                allied_armies=[player],
                war_objective_province_ids=[2585],
                objective_province_states=[
                    _objective_state(
                        2585,
                        siege_observable=paused_rich,
                        active_siege=(
                            _active_siege(
                                progress_raw=(32_000 if progressed else 25_000),
                                current_work_raw=(
                                    3_200_000 if progressed else 2_500_000
                                ),
                            )
                            if paused_rich
                            else None
                        ),
                    )
                ],
            )

        starting_war = war(paused_rich=True)
        endpoint.publish(
            _snapshot(
                100,
                date_raw=start_date,
                active_wars=[starting_war],
                player_armies=[player],
            )
        )
        timers: list[threading.Timer] = []
        last_running_date = start_date
        pause_dates: list[int] = []

        def publish_running(revision: int, date_raw: int) -> None:
            nonlocal last_running_date
            last_running_date = date_raw
            endpoint.publish(
                _snapshot(
                    revision,
                    date_raw=date_raw,
                    speed=5,
                    paused=False,
                    active_wars=[war(paused_rich=False)],
                    player_armies=[player],
                )
            )

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            step = str(frame["step"])
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {"step": step, "accepted": True},
                }
            )
            if step == "set-speed-5":
                endpoint.publish(
                    _snapshot(
                        101,
                        date_raw=start_date,
                        speed=5,
                        active_wars=[starting_war],
                        player_armies=[player],
                    )
                )
            elif step == "resume-map":
                publish_running(102, start_date + 24)
                timer = threading.Timer(
                    0.01,
                    lambda: publish_running(103, start_date + 7 * 24),
                )
                timers.append(timer)
                timer.start()
            elif step == "pause-map":
                pause_dates.append(last_running_date)
                endpoint.publish(
                    _snapshot(
                        104,
                        date_raw=last_running_date,
                        speed=5,
                        paused=True,
                        active_wars=[
                            war(paused_rich=True, progressed=True)
                        ],
                        player_armies=[player],
                    )
                )

        endpoint.send_hook = answer
        result = driver.execute_step("life-advance")
        for timer in timers:
            timer.join(timeout=1.0)

        self.assertEqual(pause_dates, [start_date + 7 * 24])
        self.assertEqual(result["elapsed_days"], 7)
        before_state = result["war_progress_before"]["wars"][0][
            "objective_province_states"
        ][0]
        after_state = result["war_progress_after"]["wars"][0][
            "objective_province_states"
        ][0]
        self.assertEqual(
            before_state["active_siege"]["current_work"]["raw"],
            2_500_000,
        )
        self.assertEqual(
            after_state["active_siege"]["current_work"]["raw"],
            3_200_000,
        )

    def test_composite_life_advance_retries_one_natural_revision_race(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            life_advance_timeout_seconds=0.1,
        )
        endpoint.publish(
            _hello(
                "game.state.snapshot",
                "game.command.pause-map",
                "game.command.resume-map",
                "game.command.set-speed-1",
                "game.command.set-speed-3",
                "game.command.set-speed-5",
            )
        )
        endpoint.publish(_snapshot(1))
        original_take_snapshot = (
            driver.take_internal_semantic_snapshot
        )
        calls = 0

        def racing_snapshot() -> dict[str, object]:
            nonlocal calls
            calls += 1
            if calls == 2:
                endpoint.publish(_snapshot(2, date_raw=53_171_424))
            return original_take_snapshot()

        driver.take_internal_semantic_snapshot = (  # type: ignore[method-assign]
            racing_snapshot
        )

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            step = str(frame["step"])
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {"step": step, "accepted": True},
                }
            )
            if step == "set-speed-5":
                endpoint.publish(
                    _snapshot(3, date_raw=53_171_424, speed=5)
                )
            elif step == "resume-map":
                endpoint.publish(
                    _snapshot(
                        4,
                        date_raw=53_171_448,
                        speed=5,
                        paused=False,
                    )
                )
            elif step == "pause-map":
                endpoint.publish(
                    _snapshot(5, date_raw=53_171_448, speed=5, paused=True)
                )

        endpoint.send_hook = answer
        result = driver.execute_step("life-advance")

        wire_steps = [
            frame["step"]
            for frame in endpoint.frames
            if frame.get("type") == "execute_step"
        ]
        self.assertEqual(wire_steps, ["set-speed-5", "resume-map", "pause-map"])
        self.assertEqual(result["starting_date_raw"], 53_171_400)
        self.assertEqual(result["ending_date_raw"], 53_171_448)
        self.assertTrue(result["paused"])

    def test_resume_life_advance_retries_once_after_ack_without_running(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=2.5,
        )
        endpoint.publish(
            _hello("game.state.snapshot", "game.command.resume-map")
        )
        endpoint.publish(_snapshot(1, speed=1, paused=True))
        observed = driver.take_snapshot()
        submissions = 0

        def answer(frame: dict[str, object]) -> None:
            nonlocal submissions
            if frame.get("type") != "execute_step":
                return
            submissions += 1
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {
                        "step": "resume-map",
                        "accepted": True,
                        "status": (
                            "submitted"
                            if submissions == 1
                            else "already_running"
                        ),
                    },
                }
            )
            if submissions == 2:
                endpoint.publish(_snapshot(2, speed=1, paused=False))

        endpoint.send_hook = answer
        actions: list[dict[str, object]] = []
        paused = driver.take_internal_semantic_snapshot()
        waits = 0

        def wait_then_observe_running(
            snapshot: dict[str, object],
            predicate: object,
            *,
            timeout_seconds: float,
        ) -> dict[str, object]:
            nonlocal waits
            waits += 1
            if waits == 1:
                return paused
            return driver.take_internal_semantic_snapshot()

        with mock.patch.object(
            driver,
            "_wait_for_life_advance_snapshot",
            side_effect=wait_then_observe_running,
        ):
            running = driver._resume_life_advance(observed, actions)

        self.assertFalse(running["paused"])
        self.assertEqual(
            [action["result"]["status"] for action in actions],
            ["submitted", "already_running"],
        )
        resume_frames = [
            frame
            for frame in endpoint.frames
            if frame.get("type") == "execute_step"
            and frame.get("step") == "resume-map"
        ]
        self.assertEqual(len(resume_frames), 2)
        self.assertEqual(
            [frame.get("expected_revision") for frame in resume_frames],
            [1, 1],
        )

    def test_resume_life_advance_retries_at_most_once_within_deadline(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=2.5,
        )
        endpoint.publish(
            _hello("game.state.snapshot", "game.command.resume-map")
        )
        endpoint.publish(_snapshot(1, speed=1, paused=True))
        observed = driver.take_snapshot()
        current_time = 100.0

        def monotonic() -> float:
            return current_time

        def wait_without_running(
            snapshot: dict[str, object],
            predicate: object,
            *,
            timeout_seconds: float,
        ) -> dict[str, object]:
            nonlocal current_time
            current_time += timeout_seconds
            return snapshot

        with (
            mock.patch(
                "xar_autoplayer.bridge.native_driver.time.monotonic",
                side_effect=monotonic,
            ),
            mock.patch.object(
                driver,
                "_execute_primitive_step",
                return_value={
                    "step": "resume-map",
                    "accepted": True,
                    "status": "submitted",
                },
            ) as execute,
            mock.patch.object(
                driver,
                "_wait_for_life_advance_snapshot",
                side_effect=wait_without_running,
            ) as wait,
        ):
            with self.assertRaisesRegex(
                BridgeUnavailableError,
                "resume_attempts=2",
            ):
                driver._resume_life_advance(observed, [])

        self.assertEqual(execute.call_count, 2)
        self.assertEqual(wait.call_count, 2)
        self.assertEqual(
            [call.kwargs["timeout_seconds"] for call in wait.call_args_list],
            [1.0, 1.5],
        )

    def test_resume_life_advance_does_not_retry_after_owner_change(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello("game.state.snapshot", "game.command.resume-map")
        )
        endpoint.publish(_snapshot(1, speed=1, paused=True))
        observed = driver.take_snapshot()
        changed = copy.deepcopy(observed)
        changed["diagnostics"]["connection_generation"] += 1

        with (
            mock.patch.object(
                driver,
                "_execute_primitive_step",
                return_value={
                    "step": "resume-map",
                    "accepted": True,
                    "status": "submitted",
                },
            ) as execute,
            mock.patch.object(
                driver,
                "_wait_for_life_advance_snapshot",
                return_value=changed,
            ),
        ):
            with self.assertRaisesRegex(
                BridgeUnavailableError,
                "retry_suppressed=owner_changed",
            ):
                driver._resume_life_advance(observed, [])

        execute.assert_called_once()

    def test_resume_life_advance_preserves_first_ack_when_retry_fails(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello("game.state.snapshot", "game.command.resume-map")
        )
        endpoint.publish(_snapshot(1, speed=1, paused=True))
        observed = driver.take_snapshot()
        with (
            mock.patch.object(
                driver,
                "_execute_primitive_step",
                side_effect=(
                    {
                        "step": "resume-map",
                        "accepted": True,
                        "status": "submitted",
                    },
                    BridgeUnavailableError("second ACK timed out"),
                ),
            ),
            mock.patch.object(
                driver,
                "_wait_for_life_advance_snapshot",
                return_value=observed,
            ),
        ):
            with self.assertRaisesRegex(
                BridgeUnavailableError,
                "resume_ack_statuses=\\['submitted'\\].*second ACK timed out",
            ):
                driver._resume_life_advance(observed, [])

    def test_pause_life_advance_adopts_fresh_auto_paused_frame(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello("game.state.snapshot", "game.command.pause-map")
        )
        endpoint.publish(
            _snapshot(1, date_raw=53_171_400, speed=5, paused=False)
        )
        observed = driver.take_snapshot()
        original_take_snapshot = (
            driver.take_internal_semantic_snapshot
        )
        calls = 0

        def auto_pausing_snapshot() -> dict[str, object]:
            nonlocal calls
            calls += 1
            if calls == 1:
                endpoint.publish(
                    _snapshot(
                        2,
                        active_event={"instance_id": 2, "option_count": 1},
                        date_raw=53_171_424,
                        speed=5,
                        paused=True,
                    )
                )
            return original_take_snapshot()

        driver.take_internal_semantic_snapshot = (  # type: ignore[method-assign]
            auto_pausing_snapshot
        )
        actions: list[dict[str, object]] = []
        paused = driver._pause_life_advance(observed, actions)

        self.assertTrue(paused["paused"])
        self.assertEqual(paused["date_raw"], 53_171_424)
        self.assertEqual(paused["active_event"]["instance_id"], 2)
        self.assertEqual(actions, [])
        self.assertFalse(
            any(
                frame.get("type") == "execute_step"
                and frame.get("step") == "pause-map"
                for frame in endpoint.frames
            )
        )

    def test_pause_life_advance_submits_after_running_date_change(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello("game.state.snapshot", "game.command.pause-map")
        )
        endpoint.publish(
            _snapshot(1, date_raw=53_171_400, speed=5, paused=False)
        )
        observed = driver.take_snapshot()
        original_take_snapshot = (
            driver.take_internal_semantic_snapshot
        )
        calls = 0

        def racing_snapshot() -> dict[str, object]:
            nonlocal calls
            calls += 1
            if calls == 1:
                endpoint.publish(
                    _snapshot(
                        2,
                        date_raw=53_171_424,
                        speed=5,
                        paused=False,
                    )
                )
            return original_take_snapshot()

        driver.take_internal_semantic_snapshot = (  # type: ignore[method-assign]
            racing_snapshot
        )

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {
                        "step": "pause-map",
                        "accepted": True,
                        "status": "submitted",
                    },
                }
            )
            endpoint.publish(
                _snapshot(
                    3,
                    date_raw=53_171_424,
                    speed=5,
                    paused=True,
                )
            )

        endpoint.send_hook = answer
        actions: list[dict[str, object]] = []
        paused = driver._pause_life_advance(observed, actions)
        pause_frames = [
            frame
            for frame in endpoint.frames
            if frame.get("type") == "execute_step"
            and frame.get("step") == "pause-map"
        ]

        self.assertTrue(paused["paused"])
        self.assertEqual(len(pause_frames), 1)
        self.assertEqual(pause_frames[0]["expected_revision"], 2)
        self.assertEqual([action["step"] for action in actions], ["pause-map"])

    def test_pause_life_advance_submits_across_running_control_drift(self) -> None:
        for drift in ("event", "speed"):
            with self.subTest(drift=drift):
                endpoint = FakeEndpoint()
                driver = NativeHeadlessGameplayDriver(
                    endpoint.pipe_name,
                    endpoint=endpoint,
                )
                endpoint.publish(
                    _hello("game.state.snapshot", "game.command.pause-map")
                )
                endpoint.publish(
                    _snapshot(
                        1,
                        date_raw=53_171_400,
                        speed=5,
                        paused=False,
                    )
                )
                observed = driver.take_snapshot()
                original_take_snapshot = (
                    driver.take_internal_semantic_snapshot
                )
                calls = 0

                def drifting_snapshot() -> dict[str, object]:
                    nonlocal calls
                    calls += 1
                    if calls == 1:
                        endpoint.publish(
                            _snapshot(
                                2,
                                active_event=(
                                    {"instance_id": 2, "option_count": 1}
                                    if drift == "event"
                                    else None
                                ),
                                date_raw=53_171_424,
                                speed=4 if drift == "speed" else 5,
                                paused=False,
                            )
                        )
                    return original_take_snapshot()

                driver.take_internal_semantic_snapshot = (  # type: ignore[method-assign]
                    drifting_snapshot
                )

                def answer(frame: dict[str, object]) -> None:
                    if frame.get("type") != "execute_step":
                        return
                    endpoint.publish(
                        {
                            "type": "command_result",
                            "protocol_version": 1,
                            "request_id": frame["request_id"],
                            "ok": True,
                            "result": {"step": "pause-map", "accepted": True},
                        }
                    )
                    endpoint.publish(
                        _snapshot(
                            3,
                            active_event=(
                                {"instance_id": 2, "option_count": 1}
                                if drift == "event"
                                else None
                            ),
                            date_raw=53_171_424,
                            speed=4 if drift == "speed" else 5,
                            paused=True,
                        )
                    )

                endpoint.send_hook = answer
                actions: list[dict[str, object]] = []
                paused = driver._pause_life_advance(observed, actions)
                pause_frames = [
                    frame
                    for frame in endpoint.frames
                    if frame.get("type") == "execute_step"
                    and frame.get("step") == "pause-map"
                ]

                self.assertTrue(paused["paused"])
                self.assertEqual(len(pause_frames), 1)
                self.assertEqual(pause_frames[0]["expected_revision"], 2)
                if drift == "event":
                    self.assertEqual(paused["active_event"]["instance_id"], 2)
                else:
                    self.assertIsNone(paused.get("active_event"))
                self.assertEqual(
                    [action["step"] for action in actions], ["pause-map"]
                )

    def test_pause_life_advance_submits_once_across_continuous_revisions(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello("game.state.snapshot", "game.command.pause-map")
        )
        endpoint.publish(
            _snapshot(1, date_raw=53_171_400, speed=5, paused=False)
        )
        observed = driver.take_snapshot()
        original_take_snapshot = (
            driver.take_internal_semantic_snapshot
        )
        calls = 0

        def repeatedly_racing_snapshot() -> dict[str, object]:
            nonlocal calls
            calls += 1
            if calls in (1, 2):
                revision = calls + 1
                endpoint.publish(
                    _snapshot(
                        revision,
                        date_raw=53_171_400 + (revision - 1) * 24,
                        speed=5,
                        paused=False,
                    )
                )
            return original_take_snapshot()

        driver.take_internal_semantic_snapshot = (  # type: ignore[method-assign]
            repeatedly_racing_snapshot
        )

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {"step": "pause-map", "accepted": True},
                }
            )
            endpoint.publish(
                _snapshot(
                    4,
                    date_raw=53_171_448,
                    speed=5,
                    paused=True,
                )
            )

        endpoint.send_hook = answer
        actions: list[dict[str, object]] = []
        paused = driver._pause_life_advance(observed, actions)
        pause_frames = [
            frame
            for frame in endpoint.frames
            if frame.get("type") == "execute_step"
            and frame.get("step") == "pause-map"
        ]

        self.assertTrue(paused["paused"])
        self.assertEqual(len(pause_frames), 1)
        self.assertEqual(pause_frames[0]["expected_revision"], 3)
        self.assertEqual([action["step"] for action in actions], ["pause-map"])

    def test_pause_life_advance_bounds_pre_submission_by_deadline(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=0.5,
        )
        endpoint.publish(
            _hello("game.state.snapshot", "game.command.pause-map")
        )
        endpoint.publish(
            _snapshot(1, date_raw=53_171_400, speed=5, paused=False)
        )
        observed = driver.take_snapshot()
        with mock.patch(
            "xar_autoplayer.bridge.native_driver.time.monotonic",
            side_effect=(100.0, 101.0),
        ):
            with self.assertRaisesRegex(
                BridgeUnavailableError,
                "pause-map submission timed out",
            ):
                driver._pause_life_advance(observed, [])
        self.assertFalse(
            any(
                frame.get("type") == "execute_step"
                for frame in endpoint.frames
            )
        )

    def test_pause_life_advance_does_not_retry_non_revision_error(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello("game.state.snapshot", "game.command.pause-map")
        )
        endpoint.publish(_snapshot(1, speed=5, paused=False))
        observed = driver.take_snapshot()

        with mock.patch.object(
            driver,
            "_execute_primitive_step",
            side_effect=BridgeUnavailableError("native pause command unavailable"),
        ) as execute:
            with self.assertRaisesRegex(
                BridgeUnavailableError,
                "native pause command unavailable",
            ):
                driver._pause_life_advance(observed, [])

        execute.assert_called_once()

    def test_pause_life_advance_retries_once_after_ack_without_pause(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=2.5,
        )
        endpoint.publish(
            _hello("game.state.snapshot", "game.command.pause-map")
        )
        endpoint.publish(_snapshot(1, speed=5, paused=False))
        observed = driver.take_snapshot()
        submissions = 0

        def answer(frame: dict[str, object]) -> None:
            nonlocal submissions
            if frame.get("type") != "execute_step":
                return
            submissions += 1
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {
                        "step": "pause-map",
                        "accepted": True,
                        "status": (
                            "submitted"
                            if submissions == 1
                            else "already_paused"
                        ),
                    },
                }
            )
            if submissions == 2:
                endpoint.publish(_snapshot(2, speed=5, paused=True))

        endpoint.send_hook = answer
        actions: list[dict[str, object]] = []
        running = driver.take_internal_semantic_snapshot()
        waits = 0

        def wait_then_observe_pause(
            snapshot: dict[str, object],
            predicate: object,
            *,
            timeout_seconds: float,
        ) -> dict[str, object]:
            nonlocal waits
            waits += 1
            if waits == 1:
                return running
            return driver.take_internal_semantic_snapshot()

        with mock.patch.object(
            driver,
            "_wait_for_life_advance_snapshot",
            side_effect=wait_then_observe_pause,
        ):
            paused = driver._pause_life_advance(observed, actions)
        pause_frames = [
            frame
            for frame in endpoint.frames
            if frame.get("type") == "execute_step"
            and frame.get("step") == "pause-map"
        ]

        self.assertTrue(paused["paused"])
        self.assertEqual(len(pause_frames), 2)
        self.assertEqual(
            [action["step"] for action in actions],
            ["pause-map", "pause-map"],
        )
        self.assertEqual(
            [action["result"]["status"] for action in actions],
            ["submitted", "already_paused"],
        )

    def test_pause_life_advance_retries_at_most_once_within_deadline(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=2.5,
        )
        endpoint.publish(
            _hello("game.state.snapshot", "game.command.pause-map")
        )
        endpoint.publish(_snapshot(1, speed=5, paused=False))
        observed = driver.take_snapshot()
        current_time = 100.0

        def monotonic() -> float:
            return current_time

        def wait_without_pause(
            snapshot: dict[str, object],
            predicate: object,
            *,
            timeout_seconds: float,
        ) -> dict[str, object]:
            nonlocal current_time
            current_time += timeout_seconds
            return snapshot

        with (
            mock.patch(
                "xar_autoplayer.bridge.native_driver.time.monotonic",
                side_effect=monotonic,
            ),
            mock.patch.object(
                driver,
                "_execute_primitive_step",
                return_value={
                    "step": "pause-map",
                    "accepted": True,
                    "status": "submitted",
                },
            ) as execute,
            mock.patch.object(
                driver,
                "_wait_for_life_advance_snapshot",
                side_effect=wait_without_pause,
            ) as wait,
        ):
            actions: list[dict[str, object]] = []
            with self.assertRaisesRegex(
                BridgeUnavailableError,
                "pause_attempts=2",
            ):
                driver._pause_life_advance(observed, actions)

        self.assertEqual(execute.call_count, 2)
        self.assertEqual(wait.call_count, 2)
        self.assertEqual(
            [call.kwargs["timeout_seconds"] for call in wait.call_args_list],
            [1.0, 1.5],
        )
        self.assertEqual(len(actions), 2)

    def test_pause_life_advance_does_not_retry_after_owner_change(self) -> None:
        cases = (
            (
                "connection_generation",
                lambda snapshot: snapshot["diagnostics"].__setitem__(
                    "connection_generation",
                    int(snapshot["diagnostics"]["connection_generation"]) + 1,
                ),
            ),
            (
                "bridge_pid",
                lambda snapshot: snapshot["diagnostics"].__setitem__(
                    "bridge_pid",
                    int(snapshot["diagnostics"]["bridge_pid"]) + 1,
                ),
            ),
            (
                "episode_character_id",
                lambda snapshot: snapshot.__setitem__(
                    "episode_character_id",
                    int(snapshot.get("episode_character_id") or 0) + 1,
                ),
            ),
            (
                "episode_run_id",
                lambda snapshot: snapshot.__setitem__(
                    "episode_run_id", "different-run"
                ),
            ),
            (
                "map_ready",
                lambda snapshot: snapshot.__setitem__("map_ready", False),
            ),
            (
                "speed",
                lambda snapshot: snapshot.__setitem__("speed", 4),
            ),
            (
                "active_event",
                lambda snapshot: snapshot.__setitem__(
                    "active_event", {"instance_id": 99}
                ),
            ),
            (
                "terminal",
                lambda snapshot: snapshot.__setitem__(
                    "one_life_terminal_reason", "death"
                ),
            ),
        )
        for name, mutate in cases:
            with self.subTest(owner_change=name):
                endpoint = FakeEndpoint()
                driver = NativeHeadlessGameplayDriver(
                    endpoint.pipe_name,
                    endpoint=endpoint,
                )
                endpoint.publish(
                    _hello("game.state.snapshot", "game.command.pause-map")
                )
                endpoint.publish(_snapshot(1, speed=5, paused=False))
                observed = driver.take_snapshot()
                changed = copy.deepcopy(observed)
                mutate(changed)

                with (
                    mock.patch.object(
                        driver,
                        "_execute_primitive_step",
                        return_value={
                            "step": "pause-map",
                            "accepted": True,
                            "status": "submitted",
                        },
                    ) as execute,
                    mock.patch.object(
                        driver,
                        "_wait_for_life_advance_snapshot",
                        return_value=changed,
                    ),
                ):
                    with self.assertRaisesRegex(
                        BridgeUnavailableError,
                        "retry_suppressed=owner_changed",
                    ):
                        driver._pause_life_advance(observed, [])

                execute.assert_called_once()

    def test_pause_life_advance_preserves_first_ack_when_retry_fails(
        self,
    ) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello("game.state.snapshot", "game.command.pause-map")
        )
        endpoint.publish(_snapshot(1, speed=5, paused=False))
        observed = driver.take_snapshot()
        with (
            mock.patch.object(
                driver,
                "_execute_primitive_step",
                side_effect=(
                    {
                        "step": "pause-map",
                        "accepted": True,
                        "status": "submitted",
                    },
                    BridgeUnavailableError("second ACK timed out"),
                ),
            ),
            mock.patch.object(
                driver,
                "_wait_for_life_advance_snapshot",
                return_value=observed,
            ),
        ):
            with self.assertRaisesRegex(
                BridgeUnavailableError,
                "pause_ack_statuses=\\['submitted'\\].*second ACK timed out",
            ):
                driver._pause_life_advance(observed, [])

    def test_pause_life_advance_records_real_already_paused_request(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello("game.state.snapshot", "game.command.pause-map")
        )
        endpoint.publish(_snapshot(1, speed=5, paused=False))
        observed = driver.take_snapshot()
        original_take_snapshot = (
            driver.take_internal_semantic_snapshot
        )
        calls = 0

        def auto_pause_during_sender_refresh() -> dict[str, object]:
            nonlocal calls
            calls += 1
            if calls == 2:
                endpoint.publish(_snapshot(2, speed=5, paused=True))
            return original_take_snapshot()

        driver.take_internal_semantic_snapshot = (  # type: ignore[method-assign]
            auto_pause_during_sender_refresh
        )

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": frame["request_id"],
                    "ok": True,
                    "result": {
                        "step": "pause-map",
                        "accepted": True,
                        "status": "already_paused",
                    },
                }
            )

        endpoint.send_hook = answer
        actions: list[dict[str, object]] = []
        paused = driver._pause_life_advance(observed, actions)
        pause_frames = [
            frame
            for frame in endpoint.frames
            if frame.get("type") == "execute_step"
            and frame.get("step") == "pause-map"
        ]

        self.assertTrue(paused["paused"])
        self.assertEqual(len(pause_frames), 1)
        self.assertEqual(actions[0]["result"]["status"], "already_paused")

    def test_direct_pause_primitive_keeps_public_revision_gate(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello("game.state.snapshot", "game.command.pause-map")
        )
        endpoint.publish(_snapshot(1, speed=5, paused=False))
        endpoint.publish(_snapshot(2, speed=5, paused=False))
        current = driver.take_snapshot()

        with self.assertRaisesRegex(
            BridgeUnavailableError,
            "native gameplay revision mismatch",
        ):
            driver.execute_step(
                "pause-map", expected_revision=int(current["revision"]) - 1
            )
        self.assertFalse(
            any(
                frame.get("type") == "execute_step"
                for frame in endpoint.frames
            )
        )

    def test_pause_life_advance_keeps_initial_paused_frame(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello("game.state.snapshot", "game.command.pause-map")
        )
        endpoint.publish(_snapshot(1, paused=True))
        observed = driver.take_snapshot()

        with mock.patch.object(
            driver,
            "take_snapshot",
            side_effect=AssertionError("paused frame should need no refresh"),
        ):
            actions: list[dict[str, object]] = []
            paused = driver._pause_life_advance(observed, actions)

        self.assertEqual(paused, observed)
        self.assertEqual(actions, [])
        self.assertFalse(
            any(
                frame.get("type") == "execute_step"
                for frame in endpoint.frames
            )
        )

    def test_command_result_does_not_forge_a_semantic_change(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello("game.state.snapshot", "game.command.life-advance")
        )
        endpoint.publish(_snapshot(19))
        before = driver.take_snapshot()

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") == "execute_step":
                endpoint.publish(
                    {
                        "type": "command_result",
                        "protocol_version": 1,
                        "request_id": frame["request_id"],
                        "ok": True,
                        "result": {"step": frame["step"], "accepted": True},
                    }
                )

        endpoint.send_hook = answer
        driver.execute_step(
            "life-advance", expected_revision=int(before["revision"])
        )
        after = driver.wait_for_change(
            int(before["revision"]), timeout_seconds=0.001
        )

        self.assertEqual(after["revision"], before["revision"])
        self.assertEqual(after["native_revision"], before["native_revision"])
        self.assertEqual(after["snapshot_id"], before["snapshot_id"])

    def test_error_frame_is_diagnostic_not_a_semantic_change(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(_hello("game.state.snapshot"))
        endpoint.publish(_snapshot(4))
        before = driver.take_snapshot()

        endpoint.publish(
            {
                "type": "error",
                "protocol_version": 1,
                "error": "fixture diagnostic",
            }
        )
        after = driver.wait_for_change(
            int(before["revision"]), timeout_seconds=0.001
        )

        self.assertEqual(after["revision"], before["revision"])
        self.assertEqual(
            driver.diagnostics()["last_error"]["error"],
            "fixture diagnostic",
        )

    def test_disconnect_removes_semantic_state(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(_hello("game.state.snapshot"))
        endpoint.publish(_snapshot())
        endpoint.on_disconnect()

        self.assertFalse(driver.capabilities()["snapshot"])
        with self.assertRaises(BridgeUnavailableError):
            driver.take_snapshot()

    def test_repeated_native_snapshot_does_not_forge_a_public_change(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(_hello("game.state.snapshot"))
        frame = _snapshot(7)
        endpoint.publish(frame)
        first = driver.take_snapshot()

        endpoint.publish(dict(frame))
        second = driver.take_snapshot()

        self.assertEqual(second["revision"], first["revision"])
        self.assertEqual(second["native_revision"], 7)

    def test_fatal_transport_error_is_visible_and_blocks_snapshot(self) -> None:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.error = "fixture CreateNamedPipeW failure"

        capabilities = driver.capabilities()
        self.assertFalse(capabilities["transport_ready"])
        self.assertEqual(
            capabilities["diagnostics"]["transport_fatal_error"],
            endpoint.error,
        )
        with self.assertRaisesRegex(BridgeUnavailableError, "CreateNamedPipeW"):
            driver.take_snapshot()


class NativeFallbackModeTests(unittest.TestCase):
    def test_minimized_visual_fallback_is_refused_without_execution(self) -> None:
        calls: list[str] = []
        visual = CallbackGameplayDriver(
            backend_id="vision-session",
            snapshot=lambda: {
                "snapshot_id": "vision:1",
                "revision": 1,
                "history": [],
            },
            execute=lambda step, _revision: calls.append(step) or {},
            action_steps=("marriage-review",),
        )
        guarded = MinimizedRejectingVisualDriver(
            visual,
            window_minimized=lambda: True,
        )

        with self.assertRaisesRegex(BridgeUnavailableError, "minimized"):
            guarded.execute_step("marriage-review")
        self.assertEqual(calls, [])
        self.assertFalse(guarded.capabilities()["visual_fallback_when_minimized"])

    def test_unknown_window_state_also_refuses_visual_fallback(self) -> None:
        calls: list[str] = []
        guarded = MinimizedRejectingVisualDriver(
            CallbackGameplayDriver(
                backend_id="vision-session",
                snapshot=lambda: {"snapshot_id": "vision:1", "revision": 1},
                execute=lambda step, _revision: calls.append(step) or {},
                action_steps=("life-advance",),
            ),
            window_minimized=lambda: None,
        )

        with self.assertRaisesRegex(BridgeUnavailableError, "visibility is unknown"):
            guarded.execute_step("life-advance")
        self.assertEqual(calls, [])

    def test_hybrid_fallback_order_is_explicit_and_guarded(self) -> None:
        endpoint = FakeEndpoint()
        native = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        endpoint.publish(
            _hello("bridge.identity", "bridge.heartbeat", "bridge.ping")
        )
        data_mod = CallbackGameplayDriver(
            backend_id="data-mod",
            snapshot=lambda: {
                "snapshot_id": "mod:1",
                "revision": 1,
                "history": [],
                "date": "1066.9.15",
            },
            execute=lambda _step, _revision: {},
            action_steps=(),
        )
        calls: list[str] = []
        visual = MinimizedRejectingVisualDriver(
            CallbackGameplayDriver(
                backend_id="vision-session",
                snapshot=lambda: {
                    "snapshot_id": "vision:2",
                    "revision": 2,
                    "history": [],
                },
                execute=lambda step, _revision: calls.append(step) or {},
                action_steps=("marriage-review",),
            ),
            window_minimized=lambda: True,
        )
        driver = ConfiguredHybridFallbackDriver(native, data_mod, visual)

        capabilities = driver.capabilities()
        self.assertEqual(
            capabilities["fallback_order"],
            ["native-headless", "data-mod", "vision-session-guarded"],
        )
        self.assertTrue(capabilities["fallback_enabled"])
        self.assertFalse(capabilities["visual_fallback_when_minimized"])
        self.assertEqual(driver.take_snapshot()["date"], "1066.9.15")
        with self.assertRaisesRegex(BridgeUnavailableError, "minimized"):
            driver.execute_step("marriage-review")
        self.assertEqual(calls, [])

    def test_restore_checkpoint_never_uses_hybrid_visual_fallback(self) -> None:
        endpoint = FakeEndpoint()
        native = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        visual_calls: list[str] = []
        driver = ConfiguredHybridFallbackDriver(
            native,
            CallbackGameplayDriver(
                backend_id="data-mod",
                snapshot=lambda: {
                    "snapshot_id": "mod:1",
                    "revision": 1,
                },
                execute=lambda _step, _revision: {},
                action_steps=(),
            ),
            MinimizedRejectingVisualDriver(
                CallbackGameplayDriver(
                    backend_id="vision-session",
                    snapshot=lambda: {
                        "snapshot_id": "vision:1",
                        "revision": 1,
                    },
                    execute=lambda step, _revision: visual_calls.append(step) or {},
                    action_steps=("restore-checkpoint", "start-next-episode"),
                ),
                window_minimized=lambda: False,
            ),
        )

        self.assertNotIn(
            "restore-checkpoint", driver.capabilities()["action_steps"]
        )
        with self.assertRaisesRegex(UnsupportedStepError, "pure native"):
            driver.execute_step("restore-checkpoint")
        self.assertNotIn(
            "start-next-episode", driver.capabilities()["action_steps"]
        )
        with self.assertRaisesRegex(UnsupportedStepError, "pure native"):
            driver.execute_step("start-next-episode")
        self.assertEqual(visual_calls, [])

    def test_native_war_command_never_uses_hybrid_visual_fallback(self) -> None:
        endpoint = FakeEndpoint()
        native = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
        )
        visual_calls: list[str] = []
        driver = ConfiguredHybridFallbackDriver(
            native,
            CallbackGameplayDriver(
                backend_id="data-mod",
                snapshot=lambda: {"snapshot_id": "mod:1", "revision": 1},
                execute=lambda _step, _revision: {},
                action_steps=(),
            ),
            MinimizedRejectingVisualDriver(
                CallbackGameplayDriver(
                    backend_id="vision-session",
                    snapshot=lambda: {
                        "snapshot_id": "vision:1",
                        "revision": 1,
                    },
                    execute=lambda step, _revision: visual_calls.append(step) or {},
                    action_steps=(
                        "move-army-7-to-9",
                        "split-army-half-7",
                        "merge-armies-7-with-8",
                        "query-declarable-wars",
                        "declare-war-808-17-0",
                        "query-arrange-marriage-choices",
                        "arrange-marriage-707-809",
                    ),
                ),
                window_minimized=lambda: False,
            ),
        )

        self.assertNotIn(
            "move-army-7-to-9", driver.capabilities()["action_steps"]
        )
        with self.assertRaisesRegex(UnsupportedStepError, "pure native"):
            driver.execute_step("move-army-7-to-9")
        self.assertNotIn(
            "split-army-half-7", driver.capabilities()["action_steps"]
        )
        with self.assertRaisesRegex(UnsupportedStepError, "pure native"):
            driver.execute_step("split-army-half-7")
        self.assertNotIn(
            "merge-armies-7-with-8", driver.capabilities()["action_steps"]
        )
        with self.assertRaisesRegex(UnsupportedStepError, "pure native"):
            driver.execute_step("merge-armies-7-with-8")
        self.assertNotIn(
            "declare-war-808-17-0", driver.capabilities()["action_steps"]
        )
        with self.assertRaisesRegex(UnsupportedStepError, "pure native"):
            driver.execute_step("declare-war-808-17-0")
        self.assertNotIn(
            "arrange-marriage-707-809", driver.capabilities()["action_steps"]
        )
        with self.assertRaisesRegex(UnsupportedStepError, "pure native"):
            driver.execute_step("arrange-marriage-707-809")
        self.assertEqual(visual_calls, [])


@unittest.skipUnless(os.name == "nt", "Windows named-pipe integration")
class NativeNamedPipeIntegrationTests(unittest.TestCase):
    def test_real_pipe_receives_dll_frames_and_returns_ping(self) -> None:
        try:
            import pywintypes
            import win32file
            import win32pipe
        except ImportError:
            self.skipTest("pywin32 unavailable")
        pipe_name = rf"\\.\pipe\xar_python_test_{uuid.uuid4().hex}"
        driver = NativeHeadlessGameplayDriver(pipe_name)
        client = None
        try:
            deadline = time.monotonic() + 3.0
            while client is None:
                try:
                    client = win32file.CreateFile(
                        pipe_name,
                        win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                        0,
                        None,
                        win32file.OPEN_EXISTING,
                        0,
                        None,
                    )
                except pywintypes.error as error:
                    if time.monotonic() >= deadline:
                        raise
                    if error.winerror not in (2, 231):
                        raise
                    time.sleep(0.01)
            win32pipe.SetNamedPipeHandleState(
                client, win32pipe.PIPE_READMODE_BYTE, None, None
            )
            _client_write_frame(win32file, client, _hello("bridge.ping"))
            ping = _client_read_frame(win32file, client)
            self.assertEqual(ping["type"], "ping")
            _client_write_frame(
                win32file,
                client,
                {
                    "type": "heartbeat",
                    "protocol_version": 1,
                    "sequence": 11,
                    "pid": 4242,
                    "monotonic_ms": 750,
                },
            )
            _client_write_frame(
                win32file,
                client,
                {
                    "type": "pong",
                    "protocol_version": 1,
                    "request_id": ping["request_id"],
                    "pid": 4242,
                },
            )
            deadline = time.monotonic() + 2.0
            while driver.diagnostics()["last_pong"] is None:
                if time.monotonic() >= deadline:
                    self.fail("native pipe server did not ingest pong")
                time.sleep(0.01)
            self.assertEqual(
                driver.diagnostics()["last_heartbeat"]["sequence"], 11
            )
        finally:
            if client is not None:
                win32file.CloseHandle(client)
            driver.close()


def _client_write_frame(win32file, client, frame: dict[str, object]) -> None:
    payload = json.dumps(frame, separators=(",", ":")).encode("utf-8")
    win32file.WriteFile(client, struct.pack("<I", len(payload)) + payload)


def _client_read_frame(win32file, client) -> dict[str, object]:
    _status, header = win32file.ReadFile(client, 4)
    size = struct.unpack("<I", header)[0]
    _status, payload = win32file.ReadFile(client, size)
    result = json.loads(payload.decode("utf-8"))
    assert isinstance(result, dict)
    return result


if __name__ == "__main__":
    unittest.main()
