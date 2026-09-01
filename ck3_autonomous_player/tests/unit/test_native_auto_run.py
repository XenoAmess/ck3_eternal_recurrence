from __future__ import annotations

import contextlib
import copy
import hashlib
import io
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock


PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer import cli  # noqa: E402
from xar_autoplayer.bridge.driver import (  # noqa: E402
    BridgeUnavailableError,
    PreSubmissionRevisionMismatchError,
    StepPostconditionError,
)
from xar_autoplayer.environment import EnvironmentSpec  # noqa: E402
from xar_autoplayer.errors import AgentError  # noqa: E402
from xar_autoplayer.runtime import NativeBridgeLaunchConfig  # noqa: E402
import xar_autoplayer.native_auto_run as native_auto_run_module  # noqa: E402


_CHECKPOINT_PAYLOAD = b"native-auto-run periodic checkpoint fixture"
_SIGNED_PENDING_ID = -2_130_706_360
_NEXT_SIGNED_PENDING_ID = -2_130_706_359


def _white_peace_war() -> dict[str, object]:
    return {
        "war_id": 16_777_290,
        "player_side": "attacker",
        "player_is_primary_war_leader": True,
        "player_relative_war_score": 37,
        "war_duration_days": 436,
        "targeted_title_ids": [2_388],
        "allied_armies": [],
        "enemy_armies": [],
    }


def _session_report(pipe_name: str) -> dict[str, object]:
    return {
        "kind": "ck3_native_session",
        "mode": "native-headless",
        "pipe": pipe_name,
        "pid": 4242,
        "started_at": "2026-08-26T00:00:00Z",
        "finished_at": "2026-08-26T00:00:01Z",
        "elapsed_seconds": 1.0,
        "exit_reason": "stop",
        "process_exit_code": 0,
        "restart_count": 0,
        "ok": True,
        "shutdown": {
            "ok": True,
            "tree_gone": True,
            "cleanup_proven": True,
        },
    }


class _NativeAutoRunHarness:
    def __init__(
        self,
        spec: EnvironmentSpec,
        actions: list[str],
        *,
        initial_unready_snapshot: bool = True,
        cold_start: bool = False,
        session_exits_immediately: bool = False,
        fail_save_checkpoint: bool = False,
        persistent_unavailable: bool = False,
    ) -> None:
        self.spec = spec
        self.actions = list(actions)
        self.initial_unready_snapshot = initial_unready_snapshot
        self.cold_start = cold_start
        self.session_exits_immediately = session_exits_immediately
        self.fail_save_checkpoint = fail_save_checkpoint
        self.persistent_unavailable = persistent_unavailable
        self.events: list[str] = []
        self.date_raw = 53_171_400
        self.native_revision = 1
        self.public_revision = 101
        self.heartbeat_date_raw = self.date_raw
        self.heartbeat_lag_capability_reads = 0
        self.terminal = False
        self.episode_character_id = 707
        self.episode_run_id = "native-707-test-run"
        self.bridge_pid = 4242
        self.connection_generation = 1
        self.driver_state_restored = cold_start
        self.driver_state_restore_kind = (
            "cold_checkpoint" if cold_start else "new_episode"
        )
        self.episode_binding_state = (
            "active_resumed" if cold_start else "active_new"
        )
        self.settlement: dict[str, object] | None = None
        self.active_event_id = (
            900
            if self.actions
            and self.actions[0] in {"event", "event_no_delta"}
            else None
        )
        self.pending_character_interaction = (
            {
                "instance_id": _SIGNED_PENDING_ID,
                "sender_character_id": 501,
                "auto_accept_notification": False,
                "source": "native",
            }
            if any(action.startswith("reply_") for action in self.actions)
            else None
        )
        self.active_wars = (
            [_white_peace_war()]
            if any(action.startswith("white_peace_") for action in actions)
            else []
        )
        self.history: list[dict[str, object]] = []
        self.ready_snapshot_observed = False
        self.driver: _FakeNativeDriver | None = None

    def make_driver(
        self,
        pipe_name: str,
        *,
        state_dir: Path,
        save_dir: Path,
        route_contact_timeline_speed: int,
        allow_route_contact_high_speed_ab: bool,
        allow_stationary_objective_hold_sentinel_canary: bool,
    ) -> "_FakeNativeDriver":
        self.events.append("driver_init")
        self.route_contact_timeline_speed = route_contact_timeline_speed
        self.allow_route_contact_high_speed_ab = (
            allow_route_contact_high_speed_ab
        )
        self.allow_stationary_objective_hold_sentinel_canary = (
            allow_stationary_objective_hold_sentinel_canary
        )
        self.driver = _FakeNativeDriver(
            self,
            pipe_name=pipe_name,
            state_dir=state_dir,
            save_dir=save_dir,
        )
        return self.driver

    def make_service(self, driver: "_FakeNativeDriver") -> "_FakeGameplayService":
        if driver is not self.driver:
            raise AssertionError("service did not receive the pipe-owning driver")
        self.events.append("service_init")
        return _FakeGameplayService(self, driver)

    def run_session(self, spec: EnvironmentSpec, **kwargs: object) -> dict[str, object]:
        if self.driver is None:
            raise AssertionError("native session started before pipe driver construction")
        if spec is not self.spec:
            raise AssertionError("native session received a different environment")
        stop_event = kwargs.get("stop_event")
        config = kwargs.get("native_bridge")
        if not isinstance(stop_event, threading.Event):
            raise AssertionError("native session lacks the shared stop event")
        if not isinstance(config, NativeBridgeLaunchConfig):
            raise AssertionError("native session lacks the validated launch config")
        self.events.append("session_start")
        if self.session_exits_immediately:
            self.events.append("session_return")
            return _session_report(config.pipe_name)
        if not stop_event.wait(timeout=2.0):
            raise AssertionError("native auto-run did not stop its managed session")
        self.events.append("session_stop")
        report = _session_report(config.pipe_name)
        self.events.append("session_return")
        return report

    def capabilities(self) -> dict[str, object]:
        diagnostics = self._diagnostics()
        if self.heartbeat_lag_capability_reads > 0:
            self.heartbeat_lag_capability_reads -= 1
            if self.heartbeat_lag_capability_reads == 0:
                self.heartbeat_date_raw = self.date_raw
        return {
            "format_version": 1,
            "backend_id": "native-headless",
            "mode": "native-headless",
            "visual_fallback": False,
            "transport_ready": True,
            "snapshot": True,
            "wait_for_change": True,
            "diagnostics": diagnostics,
            "native_session_control": {
                "configured": True,
                "driver_state_restored": self.driver_state_restored,
                "driver_state_error": None,
                "driver_state_restore_kind": self.driver_state_restore_kind,
                "episode_binding_state": self.episode_binding_state,
                "cold_candidate_rejection": None,
            },
            "checkpoint_materialization": {
                "configured": True,
                "save_dir": str(self.spec.profile_dir / "save games"),
                "filename": "xar_checkpoint.ck3",
            },
        }

    def snapshot(self) -> dict[str, object]:
        if self.persistent_unavailable:
            self.events.append("snapshot_unavailable")
            raise BridgeUnavailableError(
                "native game state is not available yet; fixture persistent"
            )
        map_ready = True
        if self.initial_unready_snapshot:
            self.initial_unready_snapshot = False
            map_ready = False
            self.events.append("snapshot_unready")
        elif not self.ready_snapshot_observed:
            self.ready_snapshot_observed = True
            self.events.append("snapshot_ready")
        return {
            "format_version": 1,
            "backend_id": "native-headless",
            "source": "fake-native-pipe",
            "snapshot_id": f"native:{self.native_revision}",
            "revision": self.public_revision,
            "native_revision": self.native_revision,
            "date": "1066.9.15",
            "date_raw": self.date_raw,
            "phase": "map_hud",
            "map_ready": map_ready,
            "paused": True,
            "played_character": {
                "character_id": self.episode_character_id,
                "alive": not self.terminal,
            },
            "episode_character_id": self.episode_character_id,
            "episode_run_id": self.episode_run_id,
            "episode_identity_pending": False,
            "one_life_terminal": self.terminal,
            "one_life_terminal_reason": (
                "played_character_dead" if self.terminal else None
            ),
            "one_life_settlement_status": (
                "ready" if self.settlement is not None else "pending"
            ),
            "one_life_settlement": copy.deepcopy(self.settlement),
            "active_event": (
                {
                    "instance_id": self.active_event_id,
                    "option_count": 2,
                }
                if self.active_event_id is not None
                else None
            ),
            "pending_character_interaction": copy.deepcopy(
                self.pending_character_interaction
            ),
            "active_wars": copy.deepcopy(self.active_wars),
            "player_armies": [],
            "native_command_history": copy.deepcopy(self.history),
            "diagnostics": self._diagnostics(),
        }

    def execute_auto_turn(self) -> dict[str, object]:
        if not self.ready_snapshot_observed:
            raise AssertionError("auto_turn executed before initial readiness")
        if not self.actions:
            raise AssertionError("fake planner action list is exhausted")
        action = self.actions.pop(0)
        self.events.append(f"auto_turn:{action}")
        if action == "blocked":
            return {
                "status": "blocked",
                "plan": {
                    "phase": "blocked",
                    "reason": "fixture_has_no_executable_step",
                },
                "snapshot_id": f"native:{self.native_revision}",
                "revision": self.public_revision,
            }
        if action == "preexisting_terminal":
            return {
                "status": "terminal",
                "plan": {
                    "phase": "terminal_complete",
                    "selected_step": None,
                    "reason": "fixture already had a terminal result",
                },
                "snapshot_id": f"native:{self.native_revision}",
                "revision": self.public_revision,
            }
        if action == "opaque_checkpoint_failure":
            self.save_checkpoint(expected_revision=self.public_revision)
            raise OSError("fixture opaque checkpoint execution failed")
        if action == "opaque_known_noncheckpoint_bridge_failure":
            failure = BridgeUnavailableError("fixture native query rejected")
            failure.plan = {
                "phase": "native_war_route_contact_horizon",
                "selected_step": (
                    "query-route-contact-horizon-v1-101-to-3610-h-1-31"
                ),
            }
            failure.selected_step = (
                "query-route-contact-horizon-v1-101-to-3610-h-1-31"
            )
            raise failure
        if action == "opaque_pre_submission_revision_mismatch":
            self.actions.insert(0, action)
            failure = PreSubmissionRevisionMismatchError(
                "native gameplay revision mismatch: expected 517, current 518"
            )
            failure.plan = {
                "phase": "native_war_entry_assessment",
                "selected_step": "query-war-entry-assessments-v1-1-29097",
            }
            failure.selected_step = (
                "query-war-entry-assessments-v1-1-29097"
            )
            failure.replan_count = 1
            raise failure
        if action == "revision_race_then_query":
            self.native_revision += 1
            self.public_revision += 1
            self.actions.insert(0, "query")
            failure = PreSubmissionRevisionMismatchError(
                "native gameplay revision mismatch: expected 101, current 102"
            )
            failure.plan = {
                "phase": "native_war_entry_assessment",
                "selected_step": "query-war-entry-assessments-v1-1-29097",
            }
            failure.selected_step = (
                "query-war-entry-assessments-v1-1-29097"
            )
            raise failure
        if action == "opaque_postcondition_failure":
            step = "advance-route-contact-horizon-v1-101-to-3610-h-1-31"
            starting_date_raw = self.date_raw
            self.date_raw += 24
            self.native_revision += 2
            self.public_revision += 2
            self.heartbeat_date_raw = self.date_raw
            result = {
                "step": step,
                "source": "native-composite",
                "progress_status": "postcondition",
                "starting_date_raw": starting_date_raw,
                "ending_date": {"date_raw": self.date_raw},
                "ending_date_raw": self.date_raw,
                "elapsed_days": 1,
                "requested_horizon_days": 1,
                "timeline_speed": 1,
                "timeline_policy": "exact_one_day_contact",
                "war_progress_after": {
                    "date_raw": self.date_raw,
                    "wars": [{"war_id": 88, "player_relative_war_score": 7}],
                },
                "actions": [
                    {
                        "step": "pause-map",
                        "result": {
                            "step": "pause-map",
                            "accepted": True,
                            "status": "already_paused",
                        },
                    }
                ],
                "paused": True,
                "final_screen": "map_hud",
                "snapshot_id": f"native:{self.native_revision}",
                "revision": self.public_revision,
                "native_revision": self.native_revision,
                "contact_refresh": {
                    "status": "fresh_snapshot_observed",
                    "ack_status": "already_paused",
                    "starting_native_revision": self.native_revision - 1,
                    "ending_native_revision": self.native_revision,
                },
            }
            failure = StepPostconditionError(
                "fixture contact postcondition failed",
                step_result=result,
                selected_step=step,
            )
            failure.plan = {
                "phase": "native_war_unavoidable_contact_transition",
                "selected_step": step,
                "reason": "fixture unavoidable contact day",
            }
            raise failure

        if action in {"query", "query_change"}:
            step = "query-declarable-wars"
            if action == "query_change":
                self.date_raw += 1
                self.native_revision += 1
                self.public_revision += 1
            result = {
                "step": step,
                "accepted": True,
                "status": "queried",
            }
        elif action in {
            "advance",
            "lagged_advance",
            "slow_advance",
            "terminal_advance",
            "advance_to_event",
            "no_delta_advance",
            "identity_change",
        }:
            step = "life-advance"
            starting_date_raw = self.date_raw
            if action in {
                "advance",
                "lagged_advance",
                "slow_advance",
                "terminal_advance",
                "advance_to_event",
                "identity_change",
            }:
                if action == "slow_advance":
                    time.sleep(0.02)
                self.date_raw += 1
                self.native_revision += 1
                self.public_revision += 1
                if action == "lagged_advance":
                    self.heartbeat_lag_capability_reads = 3
                else:
                    self.heartbeat_date_raw = self.date_raw
                if action == "terminal_advance":
                    self.terminal = True
                if action == "advance_to_event":
                    self.active_event_id = 900
                if action == "identity_change":
                    self.episode_character_id = 708
            result = {
                "step": step,
                "accepted": True,
                "status": "completed",
                "progress_status": "postcondition",
                "starting_date_raw": starting_date_raw,
                "ending_date_raw": self.date_raw,
                "elapsed_days": self.date_raw - starting_date_raw,
            }
        elif action in {"event", "event_no_delta"}:
            step = "select-event-option-1"
            old_event_id = self.active_event_id
            if old_event_id is None:
                raise AssertionError("event action lacks an active event")
            if action == "event":
                self.active_event_id = None
                self.native_revision += 1
                self.public_revision += 1
            result = {
                "step": step,
                "accepted": True,
                "status": "submitted",
                "progress_status": "postcondition",
                "event_selection": {
                    "status": "event_instance_advanced",
                    "postcondition_verified": True,
                    "old_event_instance_id": old_event_id,
                    "new_event_instance_id": self.active_event_id,
                    "selected_option_number": 1,
                    "selected_native_option_index": 0,
                },
            }
        elif action in {
            "reply_reject",
            "reply_reject_next",
            "reply_missing_typed_postcondition",
        }:
            step = "reject-pending-character-interaction"
            old_pending = copy.deepcopy(self.pending_character_interaction)
            if not isinstance(old_pending, dict):
                raise AssertionError("reply action lacks a pending interaction")
            self.pending_character_interaction = (
                {
                    "instance_id": _NEXT_SIGNED_PENDING_ID,
                    "sender_character_id": 502,
                    "auto_accept_notification": False,
                    "source": "native",
                }
                if action == "reply_reject_next"
                else None
            )
            self.native_revision += 1
            self.public_revision += 1
            result = {
                "step": step,
                "accepted": True,
                "status": "submitted",
            }
            if action != "reply_missing_typed_postcondition":
                result.update(
                    {
                        "paused": True,
                        "interaction_result": {
                            "status": "rejected",
                            "instance_id": old_pending["instance_id"],
                            "sender_character_id": old_pending[
                                "sender_character_id"
                            ],
                            "ignored_unbounded_field": "not copied",
                        },
                        "remaining_pending_character_interaction": (
                            copy.deepcopy(self.pending_character_interaction)
                        ),
                    }
                )
        elif action in {
            "white_peace_applied",
            "white_peace_pending",
            "white_peace_ack_only",
        }:
            step = "offer-white-peace-16777290"
            starting_snapshot_id = f"native:{self.native_revision}"
            starting_date_raw = self.date_raw
            old_war = copy.deepcopy(self.active_wars[0])
            if action in {"white_peace_applied", "white_peace_ack_only"}:
                self.active_wars = []
            self.native_revision += 1
            self.public_revision += 1
            result = {
                "step": step,
                "accepted": True,
                "status": "submitted",
                "backend_id": "native-headless",
            }
            if action != "white_peace_ack_only":
                remaining = (
                    copy.deepcopy(old_war)
                    if action == "white_peace_pending"
                    else None
                )
                result["war_termination_result"] = {
                    "status": (
                        "submitted_pending"
                        if action == "white_peace_pending"
                        else "applied"
                    ),
                    "war_id": 16_777_290,
                    "outcome": "white_peace",
                    "submitted_date_raw": starting_date_raw,
                    "observed_date_raw": self.date_raw,
                    "episode_run_id": self.episode_run_id,
                    "starting_snapshot_id": starting_snapshot_id,
                    "observed_snapshot_id": f"native:{self.native_revision}",
                    "command_acknowledged": True,
                    "war_id_absent_after_ack": remaining is None,
                    "recipient_decision_status_raw": 0,
                    "recipient_would_accept_now": True,
                    "casus_belli": {
                        "database_index": 0,
                        "canonical_key": "claim_cb",
                    },
                    "claimant_character_id": 707,
                    "target_title_ids": [2_388],
                    "remaining_active_war": remaining,
                }
        elif action == "start_next_episode":
            if not self.terminal or self.settlement is None:
                raise AssertionError(
                    "start-next-episode action lacks a completed terminal"
                )
            step = "start-next-episode"
            source_run_id = self.episode_run_id
            previous_pid = self.bridge_pid
            previous_generation = self.connection_generation
            seed = {
                "format_version": 1,
                "name": "xar_episode_seed.ck3",
                "path": str(
                    self.spec.profile_dir
                    / "save games"
                    / "xar_episode_seed.ck3"
                ),
                "size": 1024,
                "sha256": "a" * 64,
                "date_raw": 53_168_784,
                "character_id": 707,
                "source_run_id": source_run_id,
                "source_checkpoint_name": "xar_checkpoint.ck3",
                "immutable": True,
            }
            self.terminal = False
            self.settlement = None
            self.date_raw = int(seed["date_raw"])
            self.heartbeat_date_raw = self.date_raw
            self.episode_character_id = int(seed["character_id"])
            self.episode_run_id = "native-707-next-test-run"
            self.bridge_pid = 4343
            self.connection_generation += 1
            self.driver_state_restored = False
            self.driver_state_restore_kind = "new_episode_seed"
            self.episode_binding_state = "active_new"
            self.native_revision += 1
            self.public_revision += 1
            self.history = []
            lifecycle_seed = {
                "name": seed["name"],
                "load_save_name": "xar_episode_seed",
                "path": seed["path"],
                "size": seed["size"],
                "sha256": seed["sha256"],
                "date_raw": seed["date_raw"],
                "character_id": seed["character_id"],
                "source_run_id": seed["source_run_id"],
                "immutable": True,
            }
            result = {
                "step": step,
                "accepted": True,
                "status": "started",
                "backend_id": "native-headless",
                "source": "native-session-lifecycle-queue",
                "lifecycle_intent": "new_episode",
                "source_run_id": source_run_id,
                "episode_run_id": self.episode_run_id,
                "episode_character_id": self.episode_character_id,
                "same_character_id": True,
                "episode_seed": seed,
                "cross_run_plan_used": {
                    "policy": "one-life-visible-outcomes-v1",
                    "continue_as_heir_after_death": False,
                },
                "lifecycle": {
                    "status": "relaunched",
                    "previous_pid": previous_pid,
                    "pid": self.bridge_pid,
                    "mode": "native-headless",
                    "pipe": r"\\.\pipe\native-auto-run-test",
                    "continue_last_save": False,
                    "load_save_name": "xar_episode_seed",
                    "lifecycle_intent": "new_episode",
                    "episode_seed": lifecycle_seed,
                    "request_id": "next-episode-fixture",
                    "previous_connection_generation": previous_generation,
                    "connection_generation": self.connection_generation,
                },
                "map_ready": True,
                "paused": True,
                "snapshot_id": f"native:{self.native_revision}",
                "revision": self.public_revision,
            }
        elif action in {
            "death_terminal",
            "death_terminal_source_mismatch",
            "death_terminal_score_mismatch",
            "death_terminal_unavailable",
        }:
            if not self.terminal:
                raise AssertionError("death-terminal action lacks terminal state")
            step = "death-terminal"
            source_character_id = (
                999
                if action == "death_terminal_source_mismatch"
                else 707
            )
            self.settlement = {
                "ready": True,
                "commit_serial": 1,
                "source_character_id": source_character_id,
                "final_score": 125,
                "score_before_reject": 125,
                "record_candidate": 125,
                "old_record": 125,
                "record_delta": 0,
                "blessing_count": 2,
                "refusal_count": 1,
                "contract_progress": 3,
                "record_written": False,
            }
            settlement_status = (
                "settlement_unavailable"
                if action == "death_terminal_unavailable"
                else "complete"
            )
            score = 126 if action == "death_terminal_score_mismatch" else 125
            result = {
                "step": step,
                "accepted": True,
                "terminal": True,
                "terminal_kind": "native_played_character_dead",
                "terminal_reason": "played_character_dead",
                "episode_character_id": self.episode_character_id,
                "settlement_status": settlement_status,
                "settlement_unavailable": (
                    settlement_status == "settlement_unavailable"
                ),
                "score": score,
                "continue_as_heir_after_death": False,
                "heir_gameplay_actions": 0,
                "one_life_settlement": copy.deepcopy(self.settlement),
                "record_persistence": {
                    "status": "not_required_no_new_record",
                    "required": False,
                    "record_candidate": 125,
                },
                "cross_run_strategy": {
                    "recorded_episode": {
                        "run_id": self.episode_run_id,
                        "score": score,
                        "continue_as_heir_after_death": False,
                        "heir_gameplay_actions": 0,
                        "successful_steps": ["life-advance", "death-terminal"],
                    }
                },
            }
        else:
            raise AssertionError(f"unsupported fake action {action!r}")

        self._append_history(step, result)
        plan: dict[str, object] = {
            "phase": "fixture",
            "selected_step": step,
        }
        if step.startswith("select-event-option-"):
            plan["event_decision"] = {
                "policy": "shown-enabled-death-cancel-native-order-v1",
                "selected_native_option_index": 0,
            }
        if step in {
            "accept-pending-character-interaction",
            "reject-pending-character-interaction",
            "acknowledge-pending-character-interaction",
        }:
            plan["pending_character_interaction"] = {
                "instance_id": _SIGNED_PENDING_ID,
                "interaction_key": "fixture_nonreligious_interaction",
                "roles": {
                    "actor_character_id": 501,
                    "recipient_character_id": 707,
                },
            }
            plan["decision"] = {
                "rule_id": "ordinary-reject-unique-accept-v1",
                "selected_action": "reject",
            }
        if step.startswith("offer-white-peace-"):
            plan["war_id"] = 16_777_290
            plan["decision"] = {
                "rule_id": "native_ai_claim_cb_minimal_white_peace_v1",
                "selected_action": "offer_white_peace",
                "native_ai_equivalent": False,
            }
        return {
            "status": "executed",
            "selected_step": step,
            "plan": plan,
            "result": copy.deepcopy(result),
        }

    def save_checkpoint(self, *, expected_revision: int) -> dict[str, object]:
        if expected_revision != self.public_revision:
            raise AssertionError(
                "checkpoint was not bound to the current public revision"
            )
        self.events.append("save_checkpoint")
        if self.fail_save_checkpoint:
            raise OSError("fixture checkpoint failed")
        path = self.spec.profile_dir / "save games" / "xar_checkpoint.ck3"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(_CHECKPOINT_PAYLOAD)
        digest = hashlib.sha256(_CHECKPOINT_PAYLOAD).hexdigest()
        history_index = len(self.history) + 1
        checkpoint = {
            "status": "saved",
            "path": str(path.resolve()),
            "name": path.name,
            "size": len(_CHECKPOINT_PAYLOAD),
            "sha256": digest,
            "date_raw": self.date_raw,
            "overwrite_confirmed": False,
            "strategy": "native-autosave-command-v1",
            "history_index": history_index,
            "episode_character_id": self.episode_character_id,
            "episode_run_id": self.episode_run_id,
        }
        result = {
            "step": "save-checkpoint",
            "accepted": True,
            "status": "submitted",
            "checkpoint": checkpoint,
            "materialization": {
                "available": True,
                "save_dir": str(path.parent.resolve()),
                "mtime_ns": path.stat().st_mtime_ns,
            },
        }
        self._append_history("save-checkpoint", result)
        return copy.deepcopy(result)

    def _append_history(self, command: str, result: dict[str, object]) -> None:
        self.history.append(
            {
                "index": len(self.history) + 1,
                "command": command,
                "ok": True,
                "result": copy.deepcopy(result),
            }
        )

    def _diagnostics(self) -> dict[str, object]:
        if self.persistent_unavailable:
            mailbox = {
                "installed": False,
                "stop": False,
                "failure": 0,
                "ready": False,
                "executor_submission_enabled": False,
                "date_raw": 0,
                "paused": False,
                "executed_requests": 0,
                "pump_epochs": 0,
                "consecutive_verified": 0,
            }
            semantic_state_available = False
            rejected_state_snapshot_count = 7
            snapshot_publish_diagnostic_count = 11
        else:
            mailbox = {
                "installed": True,
                "stop": False,
                "failure": 0,
                "ready": True,
                "executor_submission_enabled": True,
                "date_raw": self.heartbeat_date_raw,
                "paused": True,
                "executed_requests": len(self.history),
            }
            semantic_state_available = True
            rejected_state_snapshot_count = 0
            snapshot_publish_diagnostic_count = 0
        return {
            "protocol_version": 1,
            "pipe_name": r"\\.\pipe\native-auto-run-test",
            "connected": True,
            "connection_generation": self.connection_generation,
            "bridge_pid": self.bridge_pid,
            "semantic_state_available": semantic_state_available,
            "rejected_state_snapshot_count": rejected_state_snapshot_count,
            "snapshot_publish_diagnostic_count": snapshot_publish_diagnostic_count,
            "transport_fatal_error": None,
            "hello": {
                "type": "hello",
                "protocol_version": 1,
                "pid": self.bridge_pid,
                "bridge_version": "0.1.0-test",
                "game_adapter_id": "ck3-1.19.0.6-msvc-x64",
                "game_adapter_status": "ready",
                "ck3_build_match": True,
                "executable_sha256": "2" * 64,
            },
            "last_heartbeat": {
                "type": "heartbeat",
                "protocol_version": 1,
                "sequence": self.native_revision,
                "startup_failure_containment_enabled": False,
                "startup_particle2_stage_recorder_enabled": False,
                "main_thread_query_mailbox_v1": mailbox,
            },
        }


class _FakeNativeDriver:
    def __init__(
        self,
        harness: _NativeAutoRunHarness,
        *,
        pipe_name: str,
        state_dir: Path,
        save_dir: Path,
    ) -> None:
        self.harness = harness
        self.pipe_name = pipe_name
        self.state_dir = state_dir
        self.save_dir = save_dir

    def capabilities(self) -> dict[str, object]:
        return self.harness.capabilities()

    def take_snapshot(self) -> dict[str, object]:
        return self.harness.snapshot()

    def close(self) -> None:
        self.harness.events.append("driver_close")


class _FakeGameplayService:
    def __init__(
        self,
        harness: _NativeAutoRunHarness,
        driver: _FakeNativeDriver,
    ) -> None:
        self.harness = harness
        self.driver = driver

    def auto_turn(self) -> dict[str, object]:
        return self.harness.execute_auto_turn()

    def snapshot(self) -> dict[str, object]:
        return self.driver.take_snapshot()

    def save_checkpoint(self, *, expected_revision: int) -> dict[str, object]:
        return self.harness.save_checkpoint(expected_revision=expected_revision)


class NativeAutoRunTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="xar-native-auto-run-")
        root = Path(self.temporary.name)
        self.spec = EnvironmentSpec(root / "state", root / "game")
        self.dll_path = root / "xar_ck3_bridge.dll"
        self.injector_path = root / "xar_ck3_bridge_injector.exe"
        self.dll_path.write_bytes(b"fake bridge dll")
        self.injector_path.write_bytes(b"fake bridge injector")
        self.config = NativeBridgeLaunchConfig(
            mode="native-headless",
            pipe_name=r"\\.\pipe\native-auto-run-test",
            dll_path=self.dll_path,
            injector_path=self.injector_path,
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _run(
        self,
        actions: list[str],
        *,
        initial_unready_snapshot: bool = True,
        timeout_seconds: float = 2.0,
        completion_contract: str = "bounded",
        checkpoint_every_eligible_advances: int = 3,
        session_exits_immediately: bool = False,
        fail_save_checkpoint: bool = False,
        persistent_unavailable: bool = False,
        allow_stationary_objective_hold_sentinel_canary: bool = False,
    ) -> tuple[dict[str, object], _NativeAutoRunHarness]:
        harness = _NativeAutoRunHarness(
            self.spec,
            actions,
            initial_unready_snapshot=initial_unready_snapshot,
            cold_start=completion_contract
            in {"one_generation", "next_episode"},
            session_exits_immediately=session_exits_immediately,
            fail_save_checkpoint=fail_save_checkpoint,
            persistent_unavailable=persistent_unavailable,
        )
        with mock.patch.object(
            native_auto_run_module,
            "NativeHeadlessGameplayDriver",
            side_effect=harness.make_driver,
        ), mock.patch.object(
            native_auto_run_module,
            "GameplayBridgeService",
            side_effect=harness.make_service,
        ), mock.patch.object(
            native_auto_run_module,
            "native_session",
            side_effect=harness.run_session,
        ), mock.patch.object(
            native_auto_run_module,
            "validate_cold_start_checkpoint_for_pipe",
            return_value={
                "name": "xar_checkpoint.ck3",
                "load_save_name": "xar_checkpoint",
                "path": str(
                    self.spec.profile_dir / "save games" / "xar_checkpoint.ck3"
                ),
                "size": len(_CHECKPOINT_PAYLOAD),
                "sha256": hashlib.sha256(_CHECKPOINT_PAYLOAD).hexdigest(),
                "saved_date_raw": harness.date_raw,
                "history_index": 1,
            },
        ):
            report = native_auto_run_module.native_auto_run(
                self.spec,
                turn_count=len(actions),
                timeout_seconds=timeout_seconds,
                readiness_timeout_seconds=0.25,
                native_bridge=self.config,
                readiness_stable_seconds=0.0,
                poll_interval_seconds=0.001,
                checkpoint_every_eligible_advances=(
                    checkpoint_every_eligible_advances
                ),
                cold_start_checkpoint=(
                    completion_contract
                    in {"one_generation", "next_episode"}
                ),
                completion_contract=completion_contract,
                allow_stationary_objective_hold_sentinel_canary=(
                    allow_stationary_objective_hold_sentinel_canary
                ),
            )
        return report, harness

    def test_parser_exposes_bounded_native_auto_run(self) -> None:
        args = cli.parser().parse_args(
            [
                "--bridge-mode",
                "native-headless",
                "native-auto-run",
                "--turns",
                "7",
                "--timeout",
                "19",
                "--readiness-timeout",
                "3",
                "--cold-start-checkpoint",
            ]
        )

        self.assertEqual(args.command, "native-auto-run")
        self.assertEqual(args.bridge_mode, "native-headless")
        self.assertEqual(args.turns, 7)
        self.assertEqual(args.timeout, 19)
        self.assertEqual(args.readiness_timeout, 3)
        self.assertTrue(args.cold_start_checkpoint)
        self.assertEqual(args.route_contact_speed, 3)
        self.assertFalse(args.allow_route_contact_high_speed_ab)
        self.assertFalse(
            args.allow_stationary_objective_hold_sentinel_canary
        )

    def test_parser_exposes_strict_one_generation_runner(self) -> None:
        args = cli.parser().parse_args(
            [
                "--bridge-mode",
                "native-headless",
                "native-one-generation",
                "--max-turns",
                "50000",
                "--timeout",
                "7200",
                "--checkpoint-every-advances",
                "180",
                "--route-contact-speed",
                "5",
                "--allow-route-contact-high-speed-ab",
                "--allow-stationary-objective-hold-sentinel-canary",
            ]
        )

        self.assertEqual(args.command, "native-one-generation")
        self.assertEqual(args.max_turns, 50000)
        self.assertEqual(args.timeout, 7200)
        self.assertEqual(args.checkpoint_every_advances, 180)
        self.assertEqual(args.route_contact_speed, 5)
        self.assertTrue(args.allow_route_contact_high_speed_ab)
        self.assertTrue(
            args.allow_stationary_objective_hold_sentinel_canary
        )

    def test_parser_exposes_strict_next_episode_runner(self) -> None:
        args = cli.parser().parse_args(
            [
                "--bridge-mode",
                "native-headless",
                "native-next-episode",
                "--max-turns",
                "30",
                "--timeout",
                "1800",
                "--readiness-timeout",
                "300",
            ]
        )

        self.assertEqual(args.command, "native-next-episode")
        self.assertEqual(args.max_turns, 30)
        self.assertEqual(args.timeout, 1800)
        self.assertEqual(args.readiness_timeout, 300)
        self.assertEqual(args.checkpoint_every_advances, 1)
        self.assertEqual(args.route_contact_speed, 3)
        self.assertFalse(args.allow_route_contact_high_speed_ab)

    def test_high_speed_route_contact_arm_requires_explicit_ab_admission(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            AgentError, "targeted A/B arm"
        ):
            native_auto_run_module.native_auto_run(
                self.spec,
                turn_count=1,
                timeout_seconds=1,
                readiness_timeout_seconds=1,
                native_bridge=self.config,
                route_contact_timeline_speed=4,
            )

    def test_compact_success_keeps_route_speed_ab_evidence(self) -> None:
        compact = native_auto_run_module._compact_step_result(
            {
                "step": "advance-route-contact-horizon-v1-101-to-20-h-1-31",
                "starting_date_raw": 53_220_360,
                "ending_date_raw": 53_220_384,
                "elapsed_days": 1,
                "requested_horizon_days": 1,
                "timeline_speed": 3,
                "timeline_policy": "exact_one_day_contact_free_speed_3",
                "paused": True,
            }
        )

        self.assertIsNotNone(compact)
        self.assertEqual(compact["requested_horizon_days"], 1)
        self.assertEqual(compact["timeline_speed"], 3)
        self.assertEqual(
            compact["timeline_policy"],
            "exact_one_day_contact_free_speed_3",
        )

    def test_compact_success_keeps_native_battle_sentinel_evidence(self) -> None:
        sentinel = {
            "state": "triggered",
            "generation": 7,
            "starting_date_raw": 53_220_360,
            "target_date_raw": 53_221_440,
            "last_observed_date_raw": 53_220_480,
            "trigger_date_raw": 53_220_480,
            "speed": 3,
            "mode": "decision_epoch",
            "army_count": 2,
            "combat_count": 1,
            "completed_daily_ticks": 5,
            "intermediate_pause_count": 0,
            "trigger_flags": 64,
            "trigger_reasons": ["combat_phase_changed"],
            "signed_date_delta_from_target_raw": -960,
            "overshoot_days": 0,
            "pause_wrapper_called": True,
            "pause_observed": True,
            "terminal_observed": False,
            "abnormal": False,
        }
        compact = native_auto_run_module._compact_step_result(
            {
                "step": "battle-decision-epoch-advance",
                "starting_date_raw": 53_220_360,
                "target_date_raw": 53_221_440,
                "ending_date_raw": 53_220_480,
                "elapsed_days": 5,
                "timeline_speed": 3,
                "sentinel_mode": "decision_epoch",
                "watch_army_ids": [101, 202],
                "stop_kind": "decision_epoch",
                "completed_daily_ticks": 5,
                "intermediate_pause_count": 0,
                "overshoot_days": 0,
                "zero_intermediate_pause": True,
                "tactical_daily_sentinel": sentinel,
                "external_pause_count": 0,
                "external_rich_query_count": 0,
                "managed_failure_cleanup": False,
                "paused": True,
            }
        )

        self.assertIsNotNone(compact)
        self.assertEqual(compact["target_date_raw"], 53_221_440)
        self.assertEqual(compact["watch_army_ids"], [101, 202])
        self.assertEqual(compact["tactical_daily_sentinel"], sentinel)
        self.assertTrue(compact["zero_intermediate_pause"])

    def test_compact_success_keeps_terminal_journal_cursor_binding(self) -> None:
        transition = {
            "status": "observed",
            "query_sequence": 19,
            "event_sequence": 20,
            "combat_id": 8801,
            "subject_army_id": 101,
            "event_kind": "normal_terminal",
            "terminal_date_raw": 53_220_480,
            "winner_side_raw": 1,
        }
        compact = native_auto_run_module._compact_step_result(
            {
                "step": "query-battle-terminal-transition-v1-8801-101-19",
                "status": "accepted",
                "accepted": True,
                "query_sequence": 19,
                "snapshot_revision": 402,
                "queried_snapshot_id": "snap-402",
                "queried_revision": 402,
                "queried_native_revision": 990,
                "battle_terminal_transition": transition,
            }
        )

        self.assertIsNotNone(compact)
        self.assertEqual(compact["query_sequence"], 19)
        self.assertEqual(compact["snapshot_revision"], 402)
        self.assertEqual(compact["queried_snapshot_id"], "snap-402")
        self.assertEqual(compact["queried_revision"], 402)
        self.assertEqual(compact["queried_native_revision"], 990)
        self.assertEqual(compact["battle_terminal_transition"], transition)

    def test_compact_failure_keeps_bounded_war_query_mismatch(self) -> None:
        mismatch = {
            "stage": "starting_snapshot",
            "requested_war_id": 83_886_203,
            "snapshot_binding": {
                "snapshot_id": "native:25",
                "revision": 26,
                "native_revision": 25,
                "connection_generation": 1,
                "episode_run_id": "episode-29829",
            },
            "identity_diff": {
                "player_relative_war_score": {
                    "query": -34,
                    "active_war": -35,
                }
            },
        }
        compact = native_auto_run_module._compact_step_result(
            {
                "step": "query-war-termination-options-83886203",
                "status": "postcondition_failed",
                "accepted": True,
                "query_sequence": 7,
                "war_termination_query_mismatch": mismatch,
                "war_termination_options": {"intentionally": "omitted"},
            }
        )

        self.assertIsNotNone(compact)
        self.assertEqual(compact["war_termination_query_mismatch"], mismatch)
        self.assertNotIn("war_termination_options", compact)

    def test_non_native_cli_is_rejected_before_configuration_or_run(self) -> None:
        stderr = io.StringIO()
        with mock.patch.object(
            cli, "make_spec", return_value=self.spec
        ), mock.patch.object(
            cli, "configure_native_bridge_launch_environment"
        ) as configure_mock, mock.patch.object(
            native_auto_run_module, "native_auto_run"
        ) as run_mock, contextlib.redirect_stderr(stderr):
            code = cli.main(
                [
                    "--bridge-mode",
                    "hybrid-fallback",
                    "native-auto-run",
                    "--turns",
                    "1",
                ]
            )

        self.assertEqual(code, 1)
        self.assertIn("requires --bridge-mode native-headless", stderr.getvalue())
        configure_mock.assert_not_called()
        run_mock.assert_not_called()

    def test_ready_loop_counts_only_visible_advances_and_checkpoints_third(
        self,
    ) -> None:
        report, harness = self._run(
            ["query", "advance", "advance", "lagged_advance"]
        )

        self.assertTrue(report["ok"], report.get("error"))
        self.assertEqual(report["status"], "turn_limit")
        self.assertEqual(report["outcome"], "qualified")
        self.assertEqual(report["bounds"]["route_contact_timeline_speed"], 3)
        self.assertFalse(
            report["bounds"]["allow_route_contact_high_speed_ab"]
        )
        self.assertFalse(
            report["bounds"][
                "allow_stationary_objective_hold_sentinel_canary"
            ]
        )
        self.assertEqual(harness.route_contact_timeline_speed, 3)
        self.assertFalse(
            harness.allow_stationary_objective_hold_sentinel_canary
        )
        auto_run = report["auto_run"]
        self.assertEqual(auto_run["visible_gameplay_turns"], 3)
        self.assertEqual(
            auto_run["counts"],
            {
                "query": 1,
                "gameplay": 3,
                "checkpoint": 1,
                "recovery": 0,
                "terminal": 0,
            },
        )
        turns = auto_run["turns"]
        self.assertEqual(turns[0]["class"], "query")
        self.assertEqual(turns[0]["evidence"], ["same_frame_query"])
        for turn in turns[1:]:
            self.assertEqual(turn["selected_step"], "life-advance")
            self.assertEqual(turn["result"]["progress_status"], "postcondition")
            self.assertIn("date_advanced", turn["evidence"])

        self.assertEqual(len(report["checkpoints"]), 1)
        checkpoint = report["checkpoints"][0]
        self.assertEqual(checkpoint["phase"], "periodic_checkpoint")
        self.assertEqual(checkpoint["turn_index"], 4)
        self.assertEqual(checkpoint["eligible_advance_ordinal"], 3)
        path = Path(checkpoint["path"])
        self.assertEqual(path.read_bytes(), _CHECKPOINT_PAYLOAD)
        self.assertEqual(checkpoint["size"], len(_CHECKPOINT_PAYLOAD))
        self.assertEqual(
            checkpoint["sha256"],
            hashlib.sha256(_CHECKPOINT_PAYLOAD).hexdigest(),
        )
        history_index = checkpoint["history_index"]
        anchor = harness.history[history_index - 1]
        self.assertEqual(anchor["index"], history_index)
        self.assertEqual(anchor["command"], "save-checkpoint")
        self.assertTrue(anchor["ok"])
        self.assertEqual(
            anchor["result"]["checkpoint"]["sha256"],
            checkpoint["sha256"],
        )

        events = harness.events
        self.assertLess(events.index("driver_init"), events.index("session_start"))
        self.assertLess(events.index("snapshot_unready"), events.index("snapshot_ready"))
        self.assertLess(events.index("snapshot_ready"), events.index("auto_turn:query"))
        self.assertEqual(
            [event for event in events if event.startswith("auto_turn:")],
            [
                "auto_turn:query",
                "auto_turn:advance",
                "auto_turn:advance",
                "auto_turn:lagged_advance",
            ],
        )
        self.assertGreater(
            events.index("save_checkpoint"),
            max(
                index
                for index, event in enumerate(events)
                if event in {"auto_turn:advance", "auto_turn:lagged_advance"}
            ),
        )
        self.assertLess(events.index("session_stop"), events.index("session_return"))
        self.assertLess(events.index("session_return"), events.index("driver_close"))
        self.assertTrue(report["cleanup"]["ok"])

    def test_explicit_objective_hold_canary_flag_reaches_driver_and_report(
        self,
    ) -> None:
        report, harness = self._run(
            ["advance"],
            allow_stationary_objective_hold_sentinel_canary=True,
        )

        self.assertTrue(
            report["bounds"][
                "allow_stationary_objective_hold_sentinel_canary"
            ]
        )
        self.assertTrue(
            harness.allow_stationary_objective_hold_sentinel_canary
        )

    def test_blocked_planner_returns_failed_report(self) -> None:
        report, _harness = self._run(["blocked"])

        self.assertFalse(report["ok"])
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["outcome"], "failed")
        self.assertIn("fixture_has_no_executable_step", report["error"])
        self.assertTrue(report["cleanup"]["ok"])

    def test_postcondition_ack_without_visible_delta_is_not_qualified(self) -> None:
        report, _harness = self._run(["no_delta_advance"])

        self.assertFalse(report["ok"])
        self.assertEqual(report["status"], "turn_limit")
        self.assertEqual(report["outcome"], "not_qualified")
        self.assertIsNone(report["error"])
        self.assertEqual(report["auto_run"]["visible_gameplay_turns"], 0)
        self.assertEqual(
            report["auto_run"]["eligible_advances_since_checkpoint"], 0
        )
        self.assertEqual(report["checkpoints"], [])
        self.assertEqual(
            report["auto_run"]["turns"][0]["evidence"],
            ["no_semantic_delta"],
        )

    def test_event_turn_requires_and_records_full_instance_progress(self) -> None:
        report, _harness = self._run(["event"])

        self.assertTrue(report["ok"], report.get("error"))
        turn = report["auto_run"]["turns"][0]
        self.assertEqual(turn["selected_step"], "select-event-option-1")
        self.assertIn("event_changed", turn["evidence"])
        self.assertEqual(
            turn["plan"]["event_decision"]["policy"],
            "shown-enabled-death-cancel-native-order-v1",
        )
        self.assertEqual(
            turn["result"]["event_selection"]["status"],
            "event_instance_advanced",
        )
        self.assertEqual(
            turn["result"]["event_selection"]["old_event_instance_id"],
            900,
        )
        self.assertIsNone(
            turn["result"]["event_selection"]["new_event_instance_id"]
        )

    def test_event_ack_without_full_instance_progress_stops_the_run(self) -> None:
        report, _harness = self._run(["event_no_delta"])

        self.assertFalse(report["ok"])
        self.assertEqual(report["status"], "stopped_on_error")
        self.assertIn(
            "old-instance lifecycle postcondition", str(report["error"])
        )
        blocker = report["first_blocker"]
        self.assertEqual(blocker["turn_index"], 1)
        self.assertEqual(blocker["stage"], "postcondition")
        self.assertEqual(
            blocker["kind"], "event_lifecycle_postcondition_failed"
        )
        self.assertEqual(
            blocker["before"]["active_context"]["active_event"][
                "instance_id"
            ],
            900,
        )
        self.assertEqual(blocker["plan"]["selected_step"], "select-event-option-1")
        self.assertEqual(blocker["selected_step"], "select-event-option-1")
        self.assertEqual(
            blocker["result"]["event_selection"]["old_event_instance_id"],
            900,
        )
        self.assertEqual(
            blocker["result"]["event_selection"]["new_event_instance_id"],
            900,
        )
        self.assertEqual(
            blocker["after"]["active_context"]["active_event"][
                "instance_id"
            ],
            900,
        )
        self.assertEqual(report["auto_run"]["attempted_turns"], 1)
        self.assertEqual(report["auto_run"]["turns"], [])

    def test_pending_reply_records_lifecycle_evidence_and_tail_checkpoint(
        self,
    ) -> None:
        report, harness = self._run(["reply_reject"])

        self.assertTrue(report["ok"], report.get("error"))
        self.assertEqual(report["status"], "turn_limit")
        self.assertEqual(report["auto_run"]["visible_gameplay_turns"], 1)
        self.assertEqual(report["auto_run"]["counts"]["gameplay"], 1)
        turn = report["auto_run"]["turns"][0]
        self.assertEqual(
            turn["selected_step"], "reject-pending-character-interaction"
        )
        self.assertIn("pending_interaction_changed", turn["evidence"])
        self.assertEqual(
            turn["plan"]["decision"]["rule_id"],
            "ordinary-reject-unique-accept-v1",
        )
        self.assertEqual(
            turn["before"]["active_context"]["pending_character_interaction"][
                "instance_id"
            ],
            _SIGNED_PENDING_ID,
        )
        self.assertIsNone(
            turn["after"]["active_context"]["pending_character_interaction"]
        )
        self.assertEqual(
            turn["result"]["interaction_result"],
            {
                "status": "rejected",
                "instance_id": _SIGNED_PENDING_ID,
                "sender_character_id": 501,
            },
        )
        self.assertIsNone(
            turn["result"]["remaining_pending_character_interaction"]
        )
        self.assertEqual(report["auto_run"]["counts"]["checkpoint"], 1)
        self.assertEqual(len(report["checkpoints"]), 1)
        self.assertEqual(
            report["checkpoints"][0]["phase"], "final_checkpoint"
        )
        self.assertEqual(harness.events.count("save_checkpoint"), 1)

    def test_pending_reply_compacts_the_next_pending_identity(self) -> None:
        report, _harness = self._run(["reply_reject_next"])

        self.assertFalse(report["ok"])
        self.assertEqual(
            report["status"], "turn_limit_player_decision_pending"
        )
        self.assertTrue(
            report["auto_run"]["checkpoint_deferred_for_player_decision"]
        )
        result = report["auto_run"]["turns"][0]["result"]
        self.assertEqual(
            result["remaining_pending_character_interaction"],
            {
                "instance_id": _NEXT_SIGNED_PENDING_ID,
                "sender_character_id": 502,
                "auto_accept_notification": False,
                "source": "native",
            },
        )

    def test_pending_reply_without_typed_postcondition_stops_the_run(self) -> None:
        report, _harness = self._run(
            ["reply_missing_typed_postcondition"]
        )

        self.assertFalse(report["ok"])
        self.assertEqual(report["status"], "stopped_on_error")
        self.assertIn("old-instance lifecycle", str(report["error"]))
        blocker = report["first_blocker"]
        self.assertEqual(blocker["turn_index"], 1)
        self.assertEqual(blocker["stage"], "postcondition")
        self.assertEqual(
            blocker["kind"],
            "pending_interaction_lifecycle_postcondition_failed",
        )
        self.assertEqual(
            blocker["before"]["active_context"][
                "pending_character_interaction"
            ]["instance_id"],
            _SIGNED_PENDING_ID,
        )
        self.assertIsNone(
            blocker["after"]["active_context"][
                "pending_character_interaction"
            ]
        )
        self.assertEqual(
            blocker["result"]["step"],
            "reject-pending-character-interaction",
        )
        self.assertNotIn("interaction_result", blocker["result"])
        self.assertEqual(report["auto_run"]["turns"], [])

    def test_raiktor_pending_accept_requires_bound_war_id_to_disappear(
        self,
    ) -> None:
        war_id = 33_554_527
        before = {
            "_semantic": {
                "pending_character_interaction": {
                    "instance_id": _SIGNED_PENDING_ID,
                    "sender_character_id": 36_769,
                    "auto_accept_notification": False,
                },
                "active_wars": [{"war_id": war_id}],
            }
        }
        result = {
            "interaction_result": {
                "status": "accepted",
                "instance_id": _SIGNED_PENDING_ID,
                "sender_character_id": 36_769,
            },
            "remaining_pending_character_interaction": None,
            "paused": True,
        }
        plan = {
            "decision": {
                "rule_id": "raiktor-inbound-white-peace-v1",
                "selected_action": "accept",
                "raiktor_inbound_white_peace": {
                    "status": "ready",
                    "war_id": war_id,
                },
            }
        }
        evidence = ["pending_interaction_changed", "war_changed"]

        self.assertTrue(
            native_auto_run_module._pending_interaction_lifecycle_verified(
                "accept-pending-character-interaction",
                result,
                before=before,
                after_snapshot={
                    "pending_character_interaction": None,
                    "active_wars": [],
                    "paused": True,
                },
                evidence=evidence,
                plan=plan,
            )
        )
        self.assertFalse(
            native_auto_run_module._pending_interaction_lifecycle_verified(
                "accept-pending-character-interaction",
                result,
                before=before,
                after_snapshot={
                    "pending_character_interaction": None,
                    "active_wars": [{"war_id": war_id}],
                    "paused": True,
                },
                evidence=["pending_interaction_changed"],
                plan=plan,
            )
        )

    def test_call_ally_busy_reject_requires_no_new_active_war_id(self) -> None:
        existing_war = _white_peace_war()
        expected_signature = (
            native_auto_run_module.war_termination_active_war_signature(
                [existing_war]
            )
        )
        self.assertIsNotNone(expected_signature)
        before = {
            "_semantic": {
                "pending_character_interaction": {
                    "instance_id": _SIGNED_PENDING_ID,
                    "sender_character_id": 30_287,
                    "auto_accept_notification": False,
                },
                "active_wars": [existing_war],
            }
        }
        result = {
            "interaction_result": {
                "status": "rejected",
                "instance_id": _SIGNED_PENDING_ID,
                "sender_character_id": 30_287,
            },
            "remaining_pending_character_interaction": None,
            "paused": True,
        }
        plan = {
            "decision": {
                "rule_id": "call-ally-busy-reject-v1",
                "selected_action": "reject",
                "native_ai_equivalent": False,
                "semantic_optimal": False,
                "interaction_semantic_decision_ready": False,
                "call_ally_busy_reject": {
                    "status": "ready",
                    "evidence": {
                        "active_war_signature_before_reply": (
                            expected_signature
                        ),
                        "target_raw_token_consumed": False,
                        "target_war_id_resolved": False,
                    },
                },
            }
        }
        after = {
            "pending_character_interaction": None,
            "active_wars": [copy.deepcopy(existing_war)],
            "paused": True,
        }
        lifecycle_evidence = ["pending_interaction_changed"]

        self.assertTrue(
            native_auto_run_module._pending_interaction_lifecycle_verified(
                "reject-pending-character-interaction",
                result,
                before=before,
                after_snapshot=after,
                evidence=lifecycle_evidence,
                plan=plan,
            )
        )
        self.assertIn(
            "call_ally_active_war_signature_not_increased",
            lifecycle_evidence,
        )

        added_war = copy.deepcopy(existing_war)
        added_war["war_id"] = 67_108_946
        after_with_target = {
            **after,
            "active_wars": [copy.deepcopy(existing_war), added_war],
        }
        self.assertFalse(
            native_auto_run_module._pending_interaction_lifecycle_verified(
                "reject-pending-character-interaction",
                result,
                before=before,
                after_snapshot=after_with_target,
                evidence=["pending_interaction_changed", "war_changed"],
                plan=plan,
            )
        )

    def test_call_ally_busy_reject_binds_planned_active_war_signature(
        self,
    ) -> None:
        existing_war = _white_peace_war()
        stale_war = copy.deepcopy(existing_war)
        stale_war["player_relative_war_score"] = 36
        stale_signature = (
            native_auto_run_module.war_termination_active_war_signature(
                [stale_war]
            )
        )
        before = {
            "_semantic": {
                "pending_character_interaction": {
                    "instance_id": _SIGNED_PENDING_ID,
                    "sender_character_id": 30_287,
                    "auto_accept_notification": False,
                },
                "active_wars": [existing_war],
            }
        }
        result = {
            "interaction_result": {
                "status": "rejected",
                "instance_id": _SIGNED_PENDING_ID,
                "sender_character_id": 30_287,
            },
            "remaining_pending_character_interaction": None,
            "paused": True,
        }
        plan = {
            "decision": {
                "rule_id": "call-ally-busy-reject-v1",
                "selected_action": "reject",
                "call_ally_busy_reject": {
                    "status": "ready",
                    "evidence": {
                        "active_war_signature_before_reply": stale_signature,
                    },
                },
            }
        }

        self.assertFalse(
            native_auto_run_module._pending_interaction_lifecycle_verified(
                "reject-pending-character-interaction",
                result,
                before=before,
                after_snapshot={
                    "pending_character_interaction": None,
                    "active_wars": [copy.deepcopy(existing_war)],
                    "paused": True,
                },
                evidence=["pending_interaction_changed"],
                plan=plan,
            )
        )

    def test_white_peace_applied_preserves_bounded_semantic_evidence(
        self,
    ) -> None:
        report, _harness = self._run(["white_peace_applied"])

        self.assertTrue(report["ok"], report.get("error"))
        self.assertEqual(report["auto_run"]["visible_gameplay_turns"], 1)
        turn = report["auto_run"]["turns"][0]
        self.assertEqual(turn["selected_step"], "offer-white-peace-16777290")
        self.assertIn("war_changed", turn["evidence"])
        self.assertEqual(
            turn["plan"]["decision"]["selected_action"],
            "offer_white_peace",
        )
        termination = turn["result"]["war_termination_result"]
        self.assertEqual(termination["status"], "applied")
        self.assertTrue(termination["command_acknowledged"])
        self.assertTrue(termination["war_id_absent_after_ack"])
        self.assertIsNone(termination["remaining_active_war"])

    def test_white_peace_pending_is_recorded_but_not_visible_completion(
        self,
    ) -> None:
        report, _harness = self._run(["white_peace_pending"])

        self.assertFalse(report["ok"])
        self.assertEqual(report["outcome"], "not_qualified")
        self.assertEqual(
            report["first_blocker"]["kind"], "run_bound_exhausted"
        )
        self.assertEqual(report["auto_run"]["visible_gameplay_turns"], 0)
        turn = report["auto_run"]["turns"][0]
        self.assertEqual(turn["evidence"], ["no_semantic_delta"])
        termination = turn["result"]["war_termination_result"]
        self.assertEqual(termination["status"], "submitted_pending")
        self.assertFalse(termination["war_id_absent_after_ack"])
        self.assertEqual(
            termination["remaining_active_war"]["war_id"],
            16_777_290,
        )

    def test_white_peace_ack_without_typed_end_state_stops_the_run(self) -> None:
        report, _harness = self._run(["white_peace_ack_only"])

        self.assertFalse(report["ok"])
        self.assertEqual(report["status"], "stopped_on_error")
        self.assertEqual(
            report["first_blocker"]["kind"],
            "white_peace_lifecycle_postcondition_failed",
        )
        self.assertEqual(report["auto_run"]["turns"], [])

    def test_white_peace_lifecycle_rejects_contradictory_identity_fields(
        self,
    ) -> None:
        before = {
            "snapshot_id": "native:1",
            "date_raw": 53_171_400,
            "episode_run_id": "native-707-test-run",
            "_semantic": {
                "played_character": {"character_id": 707},
                "active_wars": [_white_peace_war()],
            },
        }
        after = {
            "snapshot_id": "native:2",
            "date_raw": 53_171_400,
            "episode_run_id": "native-707-test-run",
            "active_wars": [],
        }
        action = {
            "status": "applied",
            "war_id": 16_777_290,
            "outcome": "white_peace",
            "submitted_date_raw": 53_171_400,
            "observed_date_raw": 53_171_400,
            "episode_run_id": "native-707-test-run",
            "starting_snapshot_id": "native:1",
            "observed_snapshot_id": "native:2",
            "command_acknowledged": True,
            "war_id_absent_after_ack": True,
            "recipient_decision_status_raw": 0,
            "recipient_would_accept_now": True,
            "casus_belli": {
                "database_index": 0,
                "canonical_key": "claim_cb",
            },
            "claimant_character_id": 707,
            "target_title_ids": [2_388],
            "remaining_active_war": None,
        }
        result = {"war_termination_result": action}
        self.assertTrue(
            native_auto_run_module._white_peace_lifecycle_verified(
                "offer-white-peace-16777290",
                result,
                before=before,
                after_snapshot=after,
                evidence=["war_changed"],
            )
        )
        contradictions = {
            "submitted_date_raw": 53_171_399,
            "observed_date_raw": 53_171_401,
            "episode_run_id": "other-run",
            "recipient_decision_status_raw": 2,
            "claimant_character_id": 708,
            "target_title_ids": [9_999],
        }
        for field, value in contradictions.items():
            with self.subTest(field=field):
                malformed = copy.deepcopy(result)
                malformed["war_termination_result"][field] = value
                self.assertFalse(
                    native_auto_run_module._white_peace_lifecycle_verified(
                        "offer-white-peace-16777290",
                        malformed,
                        before=before,
                        after_snapshot=after,
                        evidence=["war_changed"],
                    )
                )
        malformed = copy.deepcopy(result)
        malformed["war_termination_result"]["casus_belli"][
            "canonical_key"
        ] = "holy_war_cb"
        self.assertFalse(
            native_auto_run_module._white_peace_lifecycle_verified(
                "offer-white-peace-16777290",
                malformed,
                before=before,
                after_snapshot=after,
                evidence=["war_changed"],
            )
        )
        malformed = copy.deepcopy(result)
        malformed["war_termination_result"]["casus_belli"][
            "database_index"
        ] = -1
        self.assertFalse(
            native_auto_run_module._white_peace_lifecycle_verified(
                "offer-white-peace-16777290",
                malformed,
                before=before,
                after_snapshot=after,
                evidence=["war_changed"],
            )
        )

        pending = copy.deepcopy(result)
        pending_action = pending["war_termination_result"]
        pending_action["status"] = "submitted_pending"
        pending_action["war_id_absent_after_ack"] = False
        pending_action["remaining_active_war"] = _white_peace_war()
        changed_after = copy.deepcopy(after)
        changed_war = _white_peace_war()
        changed_war["player_relative_war_score"] = 38
        changed_after["active_wars"] = [changed_war]
        self.assertFalse(
            native_auto_run_module._white_peace_lifecycle_verified(
                "offer-white-peace-16777290",
                pending,
                before=before,
                after_snapshot=changed_after,
                evidence=["war_changed"],
            )
        )

    def test_session_exit_during_readiness_is_classified_as_session_exit(self) -> None:
        report, _harness = self._run(
            ["advance"], session_exits_immediately=True
        )

        self.assertFalse(report["ok"])
        self.assertEqual(report["status"], "session_exit")
        self.assertEqual(report["first_blocker"]["stage"], "session")
        self.assertEqual(report["first_blocker"]["kind"], "session_exit")
        self.assertIn(
            "managed native-session exited before auto-run stop",
            report["first_blocker"]["message"],
        )

    def test_persistent_readiness_unavailable_preserves_diagnostics(self) -> None:
        report, harness = self._run(
            ["advance"],
            initial_unready_snapshot=False,
            persistent_unavailable=True,
            timeout_seconds=0.4,
        )

        self.assertFalse(report["ok"])
        self.assertEqual(report["status"], "stopped_on_error")
        self.assertEqual(report["outcome"], "failed")
        self.assertIsNone(report["readiness"])
        self.assertEqual(report["first_blocker"]["stage"], "readiness")
        self.assertEqual(report["first_blocker"]["kind"], "readiness_failed")
        self.assertEqual(
            report["first_blocker"]["status"], report["status"]
        )
        self.assertEqual(report["auto_run"]["attempted_turns"], 0)
        self.assertNotIn("auto_turn:advance", harness.events)
        self.assertTrue(report["cleanup"]["ok"])

        diagnostics = report["readiness_diagnostics"]
        self.assertIsInstance(diagnostics, dict)
        self.assertEqual(diagnostics["transport_ready"], True)
        self.assertEqual(diagnostics["snapshot"], True)
        self.assertEqual(diagnostics["diagnostics"]["connected"], True)
        self.assertEqual(
            diagnostics["diagnostics"]["connection_generation"], 1
        )
        self.assertEqual(
            diagnostics["diagnostics"]["semantic_state_available"], False
        )
        self.assertEqual(
            diagnostics["diagnostics"]["rejected_state_snapshot_count"], 7
        )
        self.assertEqual(
            diagnostics["diagnostics"]["snapshot_publish_diagnostic_count"],
            11,
        )
        self.assertEqual(
            diagnostics["diagnostics"]["last_heartbeat"]["sequence"], 1
        )
        self.assertEqual(
            diagnostics["diagnostics"]["last_heartbeat"][
                "main_thread_query_mailbox_v1"
            ]["installed"],
            False,
        )
        self.assertEqual(
            report["first_blocker"]["readiness_diagnostics"], diagnostics
        )

    def test_periodic_checkpoint_failure_names_checkpoint_attempt(self) -> None:
        report, _harness = self._run(
            ["advance", "advance", "advance"],
            completion_contract="one_generation",
            fail_save_checkpoint=True,
        )

        self.assertFalse(report["ok"])
        self.assertEqual(report["status"], "stopped_on_error")
        blocker = report["first_blocker"]
        self.assertEqual(blocker["stage"], "checkpoint")
        self.assertEqual(blocker["kind"], "checkpoint_failed")
        self.assertEqual(blocker["turn_index"], 3)
        self.assertEqual(blocker["plan"], {"phase": "periodic_checkpoint"})
        self.assertEqual(blocker["selected_step"], "save-checkpoint")
        self.assertIsNone(blocker["result"])
        self.assertIn("fixture checkpoint failed", blocker["message"])
        self.assertTrue(blocker["checkpoint_recovery_invalidated"])
        self.assertFalse(blocker["recoverable_from_checkpoint"])
        self.assertIsNone(blocker["last_durable_checkpoint"])

    def test_checkpoint_preflight_failure_keeps_previous_recovery(self) -> None:
        with mock.patch.object(
            native_auto_run_module,
            "_materialize_checkpoint",
            side_effect=AgentError("fixture checkpoint preflight failed"),
        ):
            report, _harness = self._run(
                ["advance", "advance", "advance"],
                completion_contract="one_generation",
            )

        self.assertFalse(report["ok"])
        blocker = report["first_blocker"]
        self.assertEqual(blocker["stage"], "checkpoint_preflight")
        self.assertEqual(blocker["kind"], "checkpoint_preflight_failed")
        self.assertFalse(blocker["checkpoint_recovery_invalidated"])
        self.assertTrue(blocker["recoverable_from_checkpoint"])
        self.assertEqual(
            blocker["last_durable_checkpoint"], report["fixed_seed"]
        )

    def test_opaque_auto_turn_failure_invalidates_live_checkpoint_path(self) -> None:
        report, _harness = self._run(
            ["opaque_checkpoint_failure"],
            completion_contract="one_generation",
        )

        self.assertFalse(report["ok"])
        blocker = report["first_blocker"]
        self.assertEqual(blocker["stage"], "opaque_auto_turn")
        self.assertEqual(blocker["kind"], "opaque_auto_turn_failed")
        self.assertTrue(blocker["checkpoint_recovery_invalidated"])
        self.assertEqual(
            blocker["checkpoint_recovery_invalidation_reason"],
            "opaque_auto_turn_may_have_submitted_checkpoint",
        )
        self.assertFalse(blocker["recoverable_from_checkpoint"])
        self.assertIsNone(blocker["last_durable_checkpoint"])

    def test_pre_submission_revision_race_keeps_latest_durable_checkpoint(
        self,
    ) -> None:
        report, _harness = self._run(
            [
                "query",
                "advance",
                "advance",
                "advance",
                "opaque_pre_submission_revision_mismatch",
            ],
            completion_contract="one_generation",
        )

        self.assertFalse(report["ok"])
        self.assertEqual(len(report["checkpoints"]), 1)
        blocker = report["first_blocker"]
        self.assertEqual(blocker["stage"], "opaque_auto_turn")
        self.assertEqual(
            blocker["selected_step"],
            "query-war-entry-assessments-v1-1-29097",
        )
        self.assertEqual(
            blocker["error_type"], "PreSubmissionRevisionMismatchError"
        )
        self.assertFalse(blocker["checkpoint_recovery_invalidated"])
        self.assertTrue(blocker["recoverable_from_checkpoint"])
        self.assertEqual(
            blocker["last_durable_checkpoint"], report["checkpoints"][-1]
        )

    def test_known_noncheckpoint_bridge_failure_keeps_latest_checkpoint(
        self,
    ) -> None:
        report, _harness = self._run(
            [
                "query",
                "advance",
                "advance",
                "advance",
                "opaque_known_noncheckpoint_bridge_failure",
            ],
            completion_contract="one_generation",
        )

        self.assertFalse(report["ok"])
        self.assertEqual(len(report["checkpoints"]), 1)
        blocker = report["first_blocker"]
        self.assertEqual(
            blocker["selected_step"],
            "query-route-contact-horizon-v1-101-to-3610-h-1-31",
        )
        self.assertEqual(blocker["error_type"], "BridgeUnavailableError")
        self.assertFalse(blocker["checkpoint_recovery_invalidated"])
        self.assertTrue(blocker["recoverable_from_checkpoint"])
        self.assertEqual(
            blocker["last_durable_checkpoint"], report["checkpoints"][-1]
        )

    def test_pre_submission_revision_race_refreshes_before_and_replans(self) -> None:
        report, harness = self._run(["revision_race_then_query"])

        self.assertEqual(report["status"], "turn_limit")
        self.assertIsNone(report["error"])
        self.assertEqual(report["auto_run"]["successful_turns"], 1)
        turn = report["auto_run"]["turns"][0]
        self.assertEqual(turn["class"], "query")
        self.assertEqual(turn["pre_submission_revision_replans"], 1)
        self.assertEqual(turn["selected_step"], "query-declarable-wars")
        self.assertEqual(turn["evidence"], ["same_frame_query"])
        self.assertEqual(turn["before"]["revision"], 102)
        self.assertEqual(turn["after"]["revision"], 102)
        self.assertEqual(
            [event for event in harness.events if event.startswith("auto_turn:")],
            ["auto_turn:revision_race_then_query", "auto_turn:query"],
        )

    def test_opaque_postcondition_failure_preserves_partial_step_result(
        self,
    ) -> None:
        report, _harness = self._run(
            ["opaque_postcondition_failure"],
            completion_contract="one_generation",
        )

        self.assertFalse(report["ok"])
        self.assertEqual(report["status"], "stopped_on_error")
        self.assertEqual(report["auto_run"]["attempted_turns"], 1)
        blocker = report["first_blocker"]
        self.assertEqual(blocker["stage"], "opaque_auto_turn")
        self.assertEqual(blocker["kind"], "opaque_auto_turn_failed")
        self.assertEqual(
            blocker["plan"]["phase"],
            "native_war_unavoidable_contact_transition",
        )
        self.assertEqual(
            blocker["selected_step"],
            "advance-route-contact-horizon-v1-101-to-3610-h-1-31",
        )
        result = blocker["result"]
        self.assertEqual(result["ending_date"], {"date_raw": 53_171_424})
        self.assertEqual(result["ending_date_raw"], 53_171_424)
        self.assertEqual(result["snapshot_id"], "native:3")
        self.assertEqual(result["revision"], 103)
        self.assertEqual(result["native_revision"], 3)
        self.assertEqual(result["war_progress_after"]["date_raw"], 53_171_424)
        self.assertEqual(
            result["actions"][-1]["result"]["status"], "already_paused"
        )
        self.assertEqual(
            result["contact_refresh"]["status"], "fresh_snapshot_observed"
        )
        self.assertFalse(blocker["checkpoint_recovery_invalidated"])
        self.assertTrue(blocker["recoverable_from_checkpoint"])
        self.assertEqual(
            blocker["last_durable_checkpoint"], report["fixed_seed"]
        )

    def test_compact_failure_context_preserves_pending_interaction_identity(self) -> None:
        context = native_auto_run_module._active_context_summary(
            {
                "pending_character_interaction": {
                    "instance_id": 72,
                    "kind": "marriage_offer",
                    "deadline_date_raw": 53_171_430,
                    "response_ready": True,
                }
            }
        )
        self.assertEqual(
            context["pending_character_interaction"],
            {
                "instance_id": 72,
                "kind": "marriage_offer",
                "deadline_date_raw": 53_171_430,
                "response_ready": True,
            },
        )
        self.assertEqual(
            native_auto_run_module._compact_plan(
                {
                    "phase": "pending_character_interaction_query",
                    "pending_character_interaction": {
                        "instance_id": 72,
                        "kind": "marriage_offer",
                    },
                }
            )["pending_character_interaction"]["instance_id"],
            72,
        )

    def test_compact_plan_preserves_no_declare_evidence(self) -> None:
        plan = {
            "phase": "native_war_entry_no_declare",
            "selected_step": "life-advance",
            "decision": {"outcome": "NO_DECLARE"},
            "required_capabilities": ["forecast"],
            "declaration": {"declaration_id": "29097-11-0"},
            "war_entry_assessment": {"target_character_id": 29_097},
            "war_entry_expected_utility": {
                "eu_lower_raw": None,
                "automatic_declaration_enabled": False,
            },
        }

        compact = native_auto_run_module._compact_plan(plan)

        self.assertEqual(compact, plan)

    def test_turn_limit_materializes_visible_tail_checkpoint(self) -> None:
        report, harness = self._run(["advance"])

        self.assertTrue(report["ok"], report.get("error"))
        self.assertEqual(report["status"], "turn_limit")
        self.assertEqual(report["auto_run"]["visible_gameplay_turns"], 1)
        self.assertEqual(report["auto_run"]["counts"]["checkpoint"], 1)
        self.assertEqual(len(report["checkpoints"]), 1)
        self.assertEqual(
            report["checkpoints"][0]["phase"], "final_checkpoint"
        )
        self.assertEqual(harness.events.count("save_checkpoint"), 1)
        self.assertFalse(
            report["auto_run"]["dirty_gameplay_since_checkpoint"]
        )

    def test_read_only_query_must_remain_on_same_paused_frame(self) -> None:
        report, _harness = self._run(["query_change"])

        self.assertFalse(report["ok"])
        self.assertEqual(report["outcome"], "failed")
        self.assertIn("read-only native query changed", report["error"])
        self.assertEqual(report["auto_run"]["counts"]["query"], 1)
        self.assertIn(
            "date_advanced", report["auto_run"]["turns"][0]["evidence"]
        )

    def test_checkpoint_must_bind_current_date_and_latest_history_row(self) -> None:
        for stale_kind in ("date", "history"):
            with self.subTest(stale_kind=stale_kind):
                harness = _NativeAutoRunHarness(
                    self.spec,
                    [],
                    initial_unready_snapshot=False,
                )
                result = harness.save_checkpoint(
                    expected_revision=harness.public_revision
                )
                if stale_kind == "date":
                    harness.date_raw += 1
                else:
                    harness._append_history(
                        "query-declarable-wars",
                        {"step": "query-declarable-wars", "accepted": True},
                    )
                snapshot = harness.snapshot()

                with self.assertRaisesRegex(
                    AgentError,
                    "materialization metadata is incomplete|history anchor",
                ):
                    native_auto_run_module._verify_checkpoint_result(
                        result,
                        snapshot=snapshot,
                        expected_save_dir=self.spec.profile_dir / "save games",
                    )

    def test_third_advance_skips_checkpoint_if_it_enters_terminal(self) -> None:
        report, harness = self._run(
            ["advance", "advance", "terminal_advance"]
        )

        self.assertFalse(report["ok"])
        self.assertEqual(report["status"], "turn_limit_terminal_pending")
        self.assertEqual(report["outcome"], "not_qualified")
        self.assertEqual(report["checkpoints"], [])
        self.assertNotIn("save_checkpoint", harness.events)
        self.assertEqual(
            report["auto_run"]["eligible_advances_since_checkpoint"], 3
        )

    def test_modal_third_advance_defers_checkpoint_until_event_reply(self) -> None:
        report, harness = self._run(
            ["advance", "advance", "advance_to_event", "event"]
        )

        self.assertTrue(report["ok"], report.get("error"))
        self.assertEqual(report["status"], "turn_limit")
        self.assertEqual(len(report["checkpoints"]), 1)
        self.assertEqual(report["checkpoints"][0]["phase"], "periodic_checkpoint")
        self.assertGreater(
            harness.events.index("save_checkpoint"),
            harness.events.index("auto_turn:event"),
        )
        self.assertFalse(
            report["auto_run"]["checkpoint_deferred_for_player_decision"]
        )

    def test_turn_limit_on_modal_keeps_previous_durable_anchor(self) -> None:
        report, harness = self._run(
            ["advance", "advance", "advance_to_event"],
            completion_contract="one_generation",
        )

        self.assertFalse(report["ok"])
        self.assertEqual(
            report["status"], "turn_limit_player_decision_pending"
        )
        self.assertEqual(report["checkpoints"], [])
        self.assertNotIn("save_checkpoint", harness.events)
        self.assertTrue(
            report["auto_run"]["checkpoint_deferred_for_player_decision"]
        )
        blocker = report["first_blocker"]
        self.assertEqual(blocker["kind"], "player_decision_checkpoint_deferred")
        self.assertTrue(blocker["recoverable_from_checkpoint"])
        self.assertEqual(blocker["last_durable_checkpoint"], report["fixed_seed"])

    def test_one_generation_requires_matching_scored_death_terminal(self) -> None:
        report, harness = self._run(
            ["advance", "terminal_advance", "death_terminal"],
            completion_contract="one_generation",
            checkpoint_every_eligible_advances=365,
        )

        self.assertTrue(report["ok"], report.get("error"))
        self.assertEqual(report["status"], "episode_complete")
        self.assertEqual(report["outcome"], "qualified")
        self.assertEqual(report["completion_contract"], "one_generation")
        self.assertEqual(report["terminal"]["status"], "verified")
        self.assertEqual(report["terminal"]["episode_character_id"], 707)
        self.assertEqual(report["terminal"]["score"], 125)
        self.assertTrue(all(report["qualification_gates"].values()))
        self.assertIsNone(report["first_blocker"])
        self.assertEqual(
            [row["selected_step"] for row in report["auto_run"]["turns"]],
            ["life-advance", "life-advance", "death-terminal"],
        )
        self.assertNotIn("start-next-episode", harness.events)

    def test_next_episode_requires_seed_reload_gameplay_and_checkpoint(self) -> None:
        report, harness = self._run(
            [
                "terminal_advance",
                "death_terminal",
                "start_next_episode",
                "advance",
            ],
            completion_contract="next_episode",
            checkpoint_every_eligible_advances=1,
        )

        self.assertTrue(report["ok"], report.get("error"))
        self.assertEqual(report["status"], "next_episode_checkpointed")
        self.assertEqual(report["outcome"], "qualified")
        self.assertEqual(report["completion_contract"], "next_episode")
        self.assertEqual(report["terminal"]["status"], "verified")
        next_episode = report["next_episode"]
        transition = next_episode["transition"]
        self.assertEqual(transition["status"], "verified")
        self.assertEqual(
            transition["source_run_id"], "native-707-test-run"
        )
        self.assertEqual(
            transition["episode_run_id"], "native-707-next-test-run"
        )
        self.assertTrue(transition["new_run_identity"])
        self.assertTrue(transition["seed_reloaded"])
        self.assertEqual(next_episode["visible_gameplay_turns"], 1)
        self.assertEqual(
            next_episode["checkpoint"]["episode_run_id"],
            "native-707-next-test-run",
        )
        self.assertEqual(
            next_episode["checkpoint"]["date_raw"], 53_168_785
        )
        self.assertTrue(all(report["qualification_gates"].values()))
        self.assertEqual(harness.events.count("save_checkpoint"), 1)
        self.assertEqual(
            [row["selected_step"] for row in report["auto_run"]["turns"]],
            [
                "life-advance",
                "death-terminal",
                "start-next-episode",
                "life-advance",
            ],
        )

    def test_one_generation_bound_is_incomplete_and_checkpointed(self) -> None:
        report, _harness = self._run(
            ["advance"],
            completion_contract="one_generation",
            checkpoint_every_eligible_advances=365,
        )

        self.assertFalse(report["ok"])
        self.assertEqual(report["status"], "turn_limit")
        self.assertEqual(report["outcome"], "bounded_incomplete")
        self.assertEqual(report["checkpoints"][-1]["phase"], "final_checkpoint")
        self.assertEqual(
            report["first_blocker"]["kind"], "run_bound_exhausted"
        )
        self.assertTrue(report["first_blocker"]["recoverable_from_checkpoint"])

    def test_one_generation_rejects_invalid_settlement_proofs(self) -> None:
        cases = {
            "death_terminal_source_mismatch": "score/source",
            "death_terminal_score_mismatch": "score/source",
            "death_terminal_unavailable": "no-heir settlement",
        }
        for terminal_action, marker in cases.items():
            with self.subTest(terminal_action=terminal_action):
                report, _harness = self._run(
                    ["advance", "terminal_advance", terminal_action],
                    completion_contract="one_generation",
                    checkpoint_every_eligible_advances=365,
                )

                self.assertFalse(report["ok"])
                self.assertEqual(report["status"], "stopped_on_error")
                self.assertIn(marker, str(report["error"]))
                self.assertEqual(
                    report["first_blocker"]["kind"], "settlement_invalid"
                )
                self.assertTrue(
                    report["first_blocker"]["recoverable_from_checkpoint"]
                )
                self.assertEqual(
                    report["first_blocker"]["last_durable_checkpoint"],
                    report["fixed_seed"],
                )
                self.assertEqual(
                    report["auto_run"]["turns"][-1]["selected_step"],
                    "death-terminal",
                )

    def test_one_generation_rejects_episode_identity_change(self) -> None:
        report, _harness = self._run(
            ["identity_change"],
            completion_contract="one_generation",
            checkpoint_every_eligible_advances=365,
        )

        self.assertFalse(report["ok"])
        self.assertEqual(report["status"], "stopped_on_error")
        self.assertFalse(report["qualification_gates"]["same_episode_binding"])
        self.assertEqual(report["first_blocker"]["kind"], "identity_violation")
        self.assertEqual(report["first_blocker"]["turn_index"], 1)

    def test_one_generation_rejects_bare_preexisting_terminal_status(self) -> None:
        report, _harness = self._run(
            ["preexisting_terminal"],
            completion_contract="one_generation",
        )

        self.assertFalse(report["ok"])
        self.assertEqual(report["status"], "terminal_preexisting")
        self.assertEqual(report["first_blocker"]["kind"], "preexisting_terminal")

    def test_action_finishing_after_deadline_cannot_qualify(self) -> None:
        report, harness = self._run(
            ["slow_advance"], timeout_seconds=0.01
        )

        self.assertFalse(report["ok"])
        self.assertEqual(report["status"], "timeout")
        self.assertEqual(report["outcome"], "failed")
        self.assertIn("expired during auto-turn", report["error"])
        self.assertNotIn("save_checkpoint", harness.events)

    def test_cli_returns_nonzero_for_blocked_or_unqualified_report(self) -> None:
        failures = (
            {"ok": False, "status": "blocked", "outcome": "failed"},
            {
                "ok": False,
                "status": "turn_limit",
                "outcome": "not_qualified",
            },
        )
        for failure in failures:
            with self.subTest(status=failure["status"]):
                stdout = io.StringIO()
                with mock.patch.object(
                    cli, "make_spec", return_value=self.spec
                ), mock.patch.object(
                    cli,
                    "configure_native_bridge_launch_environment",
                    return_value=self.config,
                ), mock.patch.object(
                    native_auto_run_module,
                    "native_auto_run",
                    return_value=failure,
                ) as run_mock, contextlib.redirect_stdout(stdout):
                    code = cli.main(
                        [
                            "--bridge-mode",
                            "native-headless",
                            "--bridge-dll",
                            str(self.dll_path),
                            "--bridge-injector",
                            str(self.injector_path),
                            "native-auto-run",
                            "--turns",
                            "1",
                        ]
                    )

                self.assertEqual(code, 1)
                self.assertIn('"ok": false', stdout.getvalue())
                run_mock.assert_called_once_with(
                    self.spec,
                    turn_count=1,
                    timeout_seconds=21600,
                    readiness_timeout_seconds=300,
                    cold_start_checkpoint=False,
                    route_contact_timeline_speed=3,
                    allow_route_contact_high_speed_ab=False,
                    allow_stationary_objective_hold_sentinel_canary=False,
                )


if __name__ == "__main__":
    unittest.main()
