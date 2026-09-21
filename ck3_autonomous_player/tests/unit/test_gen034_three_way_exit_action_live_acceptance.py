"""Focused offline tests for the bounded GEN-034-D action runner."""

from __future__ import annotations

import asyncio
from copy import deepcopy
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
TEST_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(TEST_ROOT))
SCRIPT = (
    ROOT
    / "native_bridge"
    / "research"
    / "run_gen034_three_way_exit_action_live_acceptance.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_gen034_three_way_exit_action_live_acceptance", SCRIPT
)
if SPEC is None or SPEC.loader is None:  # pragma: no cover
    raise RuntimeError(f"cannot load harness: {SCRIPT}")
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)

from test_raiktor_three_way_exit_postcondition import (  # noqa: E402
    _action_result,
    _authorized,
    _checkpoint_restore,
    _post,
)
from test_raiktor_three_way_exit_postwar_evidence import (  # noqa: E402
    SOURCE_CAPTURE_SHA256,
    _active,
    _cleanup_wire,
    _source_capture,
    _truce_wire,
)


PREFIX = [{"command": "restore-checkpoint", "ok": True}]


def _record(value: dict[str, object]) -> dict[str, object]:
    return {
        "result_type": "fixture",
        "is_error": False,
        "structured_content": deepcopy(value),
        "content": [],
    }


def _read_phase(gate: dict[str, object]) -> dict[str, object]:
    frame = gate["authorization"]["frame"]
    before = {
        "snapshot_id": frame["snapshot_id"],
        "revision": frame["snapshot_revision"],
        "native_revision": frame["native_revision"],
        "date_raw": frame["date_raw"],
        "paused": True,
        "active_event": None,
        "episode_run_id": frame["episode_id"],
        "diagnostics": {
            "bridge_pid": frame["ck3_pid"],
            "connection_generation": 12,
        },
        "played_character": {
            "character_id": frame["primary_attacker_character_id"]
        },
        "active_wars": [
            {
                "war_id": frame["war_id"],
                "primary_opponent_character_id": frame[
                    "primary_defender_character_id"
                ],
            }
        ],
        "native_command_history": deepcopy(PREFIX),
    }
    active = _active(gate)
    terms = {
        "raiktor_surrender_aggregate_session": {
            "aggregate": {
                "domains": {
                    "generic_war_bound_current": {
                        "available": True,
                        "payload": active,
                    }
                }
            }
        }
    }
    opponent = frame["primary_defender_character_id"]
    commands = [
        HARNESS.recommendation.query_war_termination_options_step(
            frame["war_id"]
        ),
        HARNESS.recommendation.query_war_termination_terms_step(
            frame["war_id"]
        ),
        HARNESS.recommendation.query_war_entry_assessments_step([opponent]),
        HARNESS.recommendation.query_war_entry_assessments_step([opponent]),
    ]
    return {
        "ok": True,
        "allowed_gameplay_commands": commands,
        "before_snapshot": _record(before),
        "terms_query": _record(terms),
        "action_gate": deepcopy(gate),
    }


def _with_history(
    snapshot: dict[str, object], commands: list[str]
) -> dict[str, object]:
    result = deepcopy(snapshot)
    result["native_command_history"] = [
        *deepcopy(PREFIX),
        *({"command": command, "ok": True} for command in commands),
    ]
    return result


class _FakeClient:
    def __init__(self, responses: list[dict[str, object]]) -> None:
        self.responses = [deepcopy(value) for value in responses]
        self.calls: list[tuple[str, dict[str, object]]] = []

    async def call_tool(self, name: str, arguments: dict[str, object]):
        self.calls.append((name, deepcopy(arguments)))
        if not self.responses:
            raise AssertionError(f"unexpected MCP call: {name}")
        return SimpleNamespace(
            structured_content=self.responses.pop(0),
            is_error=False,
            content=[],
        )


class Gen034ActionRunnerCheckpointRebindTests(unittest.TestCase):
    def test_parser_requires_frozen_profile_inputs(self) -> None:
        actions = {
            option
            for action in HARNESS._parser()._actions
            if action.required
            for option in action.option_strings
        }
        self.assertTrue(
            {
                "--profile-settings-template",
                "--expected-profile-settings-sha256",
                "--expected-shadercache-tree-sha256",
            }.issubset(actions)
        )

    def test_profile_hook_reuses_adapter_copy_and_binding(self) -> None:
        spec = SimpleNamespace(profile_dir=Path("isolated-profile"))
        receipt = {"status": "GREEN", "profile_ready": True}
        binding = {
            "status": "verified",
            "settings_sha256": "A" * 64,
            "shadercache_tree_sha256": "B" * 64,
        }
        with mock.patch.object(
            HARNESS.live_adapter,
            "prepare_startup_profile_assets",
            return_value=receipt,
        ) as prepare, mock.patch.object(
            HARNESS.live_adapter,
            "_prepared_profile_binding",
            return_value=binding,
        ) as bind:
            result = HARNESS._prepare_action_runner_profile(
                spec,
                profile_settings_template=Path("template/pdx_settings.txt"),
                expected_profile_settings_sha256="A" * 64,
                expected_shadercache_tree_sha256="B" * 64,
            )

        prepare.assert_called_once_with(
            spec.profile_dir,
            Path("template/pdx_settings.txt"),
        )
        bind.assert_called_once_with(
            receipt,
            expected_settings_sha256="A" * 64,
            expected_shadercache_tree_sha256="B" * 64,
        )
        self.assertEqual(result["frozen_binding"], binding)

    def test_action_runner_wires_typed_rogue_checkpoint_rebinder(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn(
            "from xar_autoplayer.rogue_checkpoint_rebinder import",
            source,
        )
        self.assertIn(
            "checkpoint_rebinder=rebind_rogue_checkpoint_v1",
            source,
        )
        self.assertIn("after_prepare_profile=after_prepare_profile", source)


def _termination_fixture(
    *, cleanup_status: str = "destroyed"
) -> tuple[dict[str, object], _FakeClient]:
    gate = _authorized("white_peace")
    read = _read_phase(gate)
    before = deepcopy(read["before_snapshot"]["structured_content"])
    post = _post(gate, route="white_peace")
    read_commands = read["allowed_gameplay_commands"]
    action_step = gate["authorization"]["action"]["literal"]
    cleanup_step = (
        HARNESS.QUERY_RAIKTOR_WAR_BOUND_LOSS_CLEANUP_V1_STEP_PREFIX
        + str(gate["authorization"]["frame"]["war_id"])
    )
    opponent = gate["authorization"]["frame"][
        "primary_defender_character_id"
    ]
    truce_step = (
        HARNESS.QUERY_RAIKTOR_ACTUAL_TRUCE_EXPIRY_V1_STEP_PREFIX
        + str(opponent)
    )
    post_commands = [*read_commands, action_step]
    post = _with_history(post, post_commands)
    action = _action_result(gate, post)
    cleanup = _cleanup_wire(
        gate,
        _active(gate),
        post,
        status=cleanup_status,
    )
    first = _truce_wire(gate, post, 10)
    second = _truce_wire(gate, post, 11)
    for value in (first, second):
        value["actual_truce_expiry_proof"] = deepcopy(
            value["raiktor_actual_truce_expiry"]
        )
    between = _with_history(post, [*post_commands, cleanup_step, truce_step])
    after_truce = _with_history(
        post,
        [*post_commands, cleanup_step, truce_step, truce_step],
    )
    checkpoint = _checkpoint_restore(gate, post)
    save = checkpoint["save_result"]
    after_save = _with_history(
        post,
        [
            *post_commands,
            cleanup_step,
            truce_step,
            truce_step,
            "save-checkpoint",
        ],
    )
    after_save.update(
        {
            "snapshot_id": "fixture-native:93",
            "revision": post["revision"] + 1,
            "native_revision": post["native_revision"] + 1,
        }
    )
    post_restore_turn = {
        "status": "executed",
        "selected_step": "advance-time",
        "plan": {"phase": "fixture", "selected_step": "advance-time"},
    }
    post_restore_snapshot = deepcopy(checkpoint["restored_snapshot"])
    post_restore_snapshot["active_wars"] = []
    post_restore_snapshot["revision"] += 1
    post_restore_snapshot["native_revision"] += 1
    client = _FakeClient(
        [
            before,
            action,
            post,
            cleanup,
            first,
            between,
            second,
            after_truce,
            save,
            after_save,
            checkpoint["restore_result"],
            checkpoint["restored_snapshot"],
            post_restore_turn,
            post_restore_snapshot,
        ]
    )
    return read, client


class Gen034ThreeWayExitActionLiveAcceptanceTests(unittest.TestCase):
    def test_recomputed_terminal_selection_must_match_frozen_authorization(self) -> None:
        gate = _authorized("white_peace")
        read = _read_phase(gate)
        action = gate["authorization"]["action"]
        frame = gate["authorization"]["frame"]
        frozen = HARNESS.terminal_authorization_v1(
            selected_step=action["literal"],
            recommended_outcome=action["semantic_action"],
            war_id=action["war_id"],
            opponent_character_id=frame["primary_defender_character_id"],
            source_capture_sha256=SOURCE_CAPTURE_SHA256,
        )

        admitted = HARNESS._require_recomputed_terminal_selection(
            read,
            source_capture_sha256=SOURCE_CAPTURE_SHA256,
            expected_terminal_step=action["literal"],
            expected_terminal_outcome=action["semantic_action"],
            expected_terminal_authorization_sha256=frozen["sha256"],
        )
        self.assertEqual(admitted, frozen)

        with self.assertRaisesRegex(
            HARNESS.Gen034ActionRunnerError,
            "terminal selection authorization mismatch",
        ):
            HARNESS._require_recomputed_terminal_selection(
                read,
                source_capture_sha256=SOURCE_CAPTURE_SHA256,
                expected_terminal_step=action["literal"],
                expected_terminal_outcome="surrender",
                expected_terminal_authorization_sha256=frozen["sha256"],
            )

    def test_white_peace_executes_once_then_closes_all_six_checks(self) -> None:
        read, client = _termination_fixture()
        result = asyncio.run(
            HARNESS._execute_action_tail(
                client,
                read_phase=read,
                source_capture=_source_capture(),
                source_capture_sha256=SOURCE_CAPTURE_SHA256,
            )
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "verified")
        self.assertTrue(result["gen034_closed"])
        action_step = result["exit_action_commands"][0]
        self.assertEqual(result["issued_commands"].count(action_step), 1)
        self.assertEqual(
            [name for name, _arguments in client.calls],
            [
                "ck3_take_snapshot",
                "ck3_execute_step",
                "ck3_take_snapshot",
                "ck3_execute_step",
                "ck3_execute_step",
                "ck3_take_snapshot",
                "ck3_execute_step",
                "ck3_take_snapshot",
                "ck3_save_checkpoint",
                "ck3_take_snapshot",
                "ck3_restore_checkpoint",
                "ck3_take_snapshot",
                "ck3_auto_turn",
                "ck3_take_snapshot",
            ],
        )
        self.assertTrue(result["checks"]["post_restore_production_turn_consumed"])
        self.assertTrue(result["checks"]["terminal_action_not_replayed"])

    def test_pending_white_peace_checkpoint_stops_at_event_without_reoffer(self) -> None:
        gate = _authorized("white_peace")
        read = _read_phase(gate)
        before = read["before_snapshot"]["structured_content"]
        action_step = gate["authorization"]["action"]["literal"]
        pending = _with_history(
            before, [*read["allowed_gameplay_commands"], action_step]
        )
        pending_save = {
            "step": "save-checkpoint",
            "accepted": True,
            "status": "submitted",
            "checkpoint": {"status": "saved", "sha256": "D" * 64},
        }
        pending_saved = _with_history(
            pending,
            [*read["allowed_gameplay_commands"], action_step, "save-checkpoint"],
        )
        pending_saved["revision"] += 1
        pending_saved["native_revision"] += 1
        interrupted = _with_history(
            pending_saved,
            [
                *read["allowed_gameplay_commands"],
                action_step,
                "save-checkpoint",
                "resume-map",
            ],
        )
        interrupted["date_raw"] += 24
        interrupted["revision"] += 1
        interrupted["native_revision"] += 1
        interrupted["active_event"] = {"instance_id": 7}
        action_result = _action_result(gate, pending, nested=False)
        action_result["war_termination_result"] = {
            "status": "submitted_pending",
            "war_id": gate["authorization"]["frame"]["war_id"],
            "outcome": "white_peace",
            "episode_run_id": gate["authorization"]["frame"]["episode_id"],
            "starting_snapshot_id": gate["authorization"]["frame"]["snapshot_id"],
            "observed_snapshot_id": pending["snapshot_id"],
            "command_acknowledged": True,
            "war_id_absent_after_ack": False,
        }
        client = _FakeClient(
            [
                before,
                action_result,
                pending,
                pending_save,
                pending_saved,
                {"step": "resume-map", "accepted": True, "status": "submitted"},
                interrupted,
            ]
        )

        result = asyncio.run(
            HARNESS._execute_action_tail(
                client,
                read_phase=read,
                source_capture=_source_capture(),
                source_capture_sha256=SOURCE_CAPTURE_SHA256,
            )
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["pending_action"]["status"], "submitted_pending")
        self.assertEqual(
            result["pending_action"]["stop_reason"],
            "event_interrupt_while_offer_pending",
        )
        self.assertEqual(result["issued_commands"].count(action_step), 1)
        self.assertEqual(
            result["issued_commands"],
            [action_step, "save-checkpoint", "resume-map"],
        )
        self.assertNotIn(
            "ck3_restore_checkpoint", [name for name, _arguments in client.calls]
        )

    def test_async_reply_observes_war_disappearance_then_pauses(self) -> None:
        gate = _authorized("white_peace")
        frame = gate["authorization"]["frame"]
        pending = _read_phase(gate)["before_snapshot"]["structured_content"]
        running = deepcopy(pending)
        running["paused"] = False
        running["date_raw"] += 9 * 24
        running["revision"] += 2
        running["native_revision"] += 2
        applied_running = deepcopy(running)
        applied_running["date_raw"] += 24
        applied_running["revision"] += 1
        applied_running["native_revision"] += 1
        applied_running["active_wars"] = []
        applied_paused = deepcopy(applied_running)
        applied_paused["paused"] = True
        applied_paused["revision"] += 1
        applied_paused["native_revision"] += 1
        client = _FakeClient(
            [
                {"step": "resume-map", "accepted": True, "status": "submitted"},
                running,
                applied_running,
                {"step": "pause-map", "accepted": True, "status": "submitted"},
                applied_paused,
            ]
        )

        result = asyncio.run(
            HARNESS._await_white_peace_reply(
                client, initial=pending, war_id=frame["war_id"]
            )
        )
        self.assertTrue(result["completed"])
        self.assertEqual(result["reason"], "war_disappeared")
        self.assertEqual(result["issued_commands"], ["resume-map", "pause-map"])
        self.assertEqual(result["snapshot"]["date_raw"], frame["date_raw"] + 240)
        self.assertNotIn(
            "offer-white-peace", " ".join(name for name, _arguments in client.calls)
        )

    def test_continue_executes_once_without_claiming_gen034_closure(self) -> None:
        gate = _authorized("continue")
        read = _read_phase(gate)
        # The immutable-checkpoint replay mode needs only the two exit reads;
        # the direct same-frame mode retains its two additional power reads.
        read["allowed_gameplay_commands"] = read[
            "allowed_gameplay_commands"
        ][:2]
        before = read["before_snapshot"]["structured_content"]
        post = _post(gate, route="continue")
        action_step = gate["authorization"]["action"]["literal"]
        post = _with_history(
            post, [*read["allowed_gameplay_commands"], action_step]
        )
        client = _FakeClient([before, _action_result(gate, post), post])

        result = asyncio.run(
            HARNESS._execute_action_tail(
                client,
                read_phase=read,
                source_capture={},
                source_capture_sha256=SOURCE_CAPTURE_SHA256,
            )
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "verified_continue")
        self.assertFalse(result["gen034_closed"])
        self.assertIsNone(result["checkpoint_restore"])
        self.assertEqual(len(client.calls), 3)

    def test_continue_waits_for_a_real_successor_without_resubmitting(self) -> None:
        gate = _authorized("continue")
        read = _read_phase(gate)
        read["allowed_gameplay_commands"] = []
        read["checkpoint_replay_recommendation"] = True
        before = read["before_snapshot"]["structured_content"]
        stalled = deepcopy(before)
        stalled = _with_history(
            stalled,
            [*read["allowed_gameplay_commands"], "resume-map"],
        )
        successor = _post(gate, route="continue")
        successor = _with_history(
            successor,
            [*read["allowed_gameplay_commands"], "resume-map"],
        )
        action_result = _action_result(gate, successor)
        client = _FakeClient([before, action_result, stalled, successor])

        result = asyncio.run(
            HARNESS._execute_action_tail(
                client,
                read_phase=read,
                source_capture={},
                source_capture_sha256=SOURCE_CAPTURE_SHA256,
            )
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["continue_observation_attempts"], 2)
        self.assertEqual(result["issued_commands"], ["resume-map"])

    def test_observed_cleanup_red_stops_before_checkpoint(self) -> None:
        read, client = _termination_fixture(cleanup_status="still_alive")

        result = asyncio.run(
            HARNESS._execute_action_tail(
                client,
                read_phase=read,
                source_capture=_source_capture(),
                source_capture_sha256=SOURCE_CAPTURE_SHA256,
            )
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "red")
        self.assertIn(
            "source_specific_cleanup_destroyed",
            result["postwar_evidence"]["blockers"],
        )
        self.assertNotIn(
            "ck3_save_checkpoint", [name for name, _arguments in client.calls]
        )
        self.assertNotIn(
            "ck3_restore_checkpoint", [name for name, _arguments in client.calls]
        )

    def test_frame_drift_is_rejected_before_action(self) -> None:
        gate = _authorized("white_peace")
        read = _read_phase(gate)
        stale = deepcopy(read["before_snapshot"]["structured_content"])
        stale["revision"] += 1
        client = _FakeClient([stale])

        with self.assertRaisesRegex(
            HARNESS.Gen034ActionRunnerError,
            "changed before submission",
        ):
            asyncio.run(
                HARNESS._execute_action_tail(
                    client,
                    read_phase=read,
                    source_capture=_source_capture(),
                    source_capture_sha256=SOURCE_CAPTURE_SHA256,
                )
            )
        self.assertEqual(
            [name for name, _arguments in client.calls],
            ["ck3_take_snapshot"],
        )

    def test_source_generation_drift_is_rejected_before_action(self) -> None:
        gate = _authorized("white_peace")
        read = _read_phase(gate)
        read["terms_query"]["structured_content"][
            "raiktor_surrender_aggregate_session"
        ]["aggregate"]["domains"]["generic_war_bound_current"]["payload"][
            "regiments"
        ][0]["persistent_regiment_id"] += 1_000
        before = read["before_snapshot"]["structured_content"]
        client = _FakeClient([before])

        with self.assertRaisesRegex(
            HARNESS.Gen034ActionRunnerError,
            "pre-action source binding failed",
        ):
            asyncio.run(
                HARNESS._execute_action_tail(
                    client,
                    read_phase=read,
                    source_capture=_source_capture(),
                    source_capture_sha256=SOURCE_CAPTURE_SHA256,
                )
            )
        self.assertEqual(
            [name for name, _arguments in client.calls],
            ["ck3_take_snapshot"],
        )

    def test_exact_build_requires_postwar_and_checkpoint_surfaces(self) -> None:
        terms_capability = HARNESS.recommendation.base.QUERY_WAR_TERMINATION_TERMS_CAPABILITY
        options_capability = HARNESS.recommendation.exit_read.QUERY_WAR_TERMINATION_OPTIONS_CAPABILITY
        power_capability = HARNESS.recommendation.power.QUERY_WAR_ENTRY_ASSESSMENTS_CAPABILITY
        private = {
            HARNESS.QUERY_RAIKTOR_WAR_BOUND_LOSS_CLEANUP_V1_CAPABILITY,
            HARNESS.QUERY_RAIKTOR_ACTUAL_TRUCE_EXPIRY_V1_CAPABILITY,
        }
        bridge_capabilities = [
            terms_capability,
            options_capability,
            power_capability,
            *sorted(private),
        ]
        war_id = 50_331_699
        opponent = 17_116
        capabilities = {
            "bridge_capabilities": bridge_capabilities,
            "diagnostics": {
                "hello": {
                    "expected_ck3_version": HARNESS.base.EXPECTED_GAME_VERSION,
                    "game_adapter_id": HARNESS.base.EXPECTED_ADAPTER_ID,
                    "game_adapter_status": "ready",
                    "ck3_build_match": True,
                    "expected_ck3_sha256": HARNESS.base.EXPECTED_EXECUTABLE_SHA256,
                    "capabilities": deepcopy(bridge_capabilities),
                }
            },
            "action_steps": [
                HARNESS.recommendation.query_war_termination_terms_step(war_id),
                HARNESS.recommendation.query_war_termination_options_step(war_id),
                HARNESS.recommendation.query_war_entry_assessments_step([opponent]),
                "save-checkpoint",
            ],
            "composite_action_steps": ["restore-checkpoint"],
        }

        proof = HARNESS._exact_build_proof(
            capabilities,
            managed_executable_sha256=HARNESS.base.EXPECTED_EXECUTABLE_SHA256,
            war_id=war_id,
            opponent_character_id=opponent,
        )
        self.assertTrue(proof["ok"])

        capabilities["composite_action_steps"] = []
        rejected = HARNESS._exact_build_proof(
            capabilities,
            managed_executable_sha256=HARNESS.base.EXPECTED_EXECUTABLE_SHA256,
            war_id=war_id,
            opponent_character_id=opponent,
        )
        self.assertFalse(rejected["ok"])
        self.assertFalse(rejected["checks"]["checkpoint_cold_restore_step"])

    def test_source_contains_no_unbounded_or_broad_action(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn('"life-advance"', source)
        self.assertNotIn("query-war-termination-exit-terms-v2", source)
        self.assertEqual(HARNESS.CONTINUE_SUCCESSOR_TIMEOUT_SECONDS, 5.0)
        self.assertEqual(HARNESS.CONTINUE_SUCCESSOR_POLL_SECONDS, 0.1)
        self.assertEqual(HARNESS.WHITE_PEACE_REPLY_MAX_DAYS, 12)
        self.assertEqual(HARNESS.WHITE_PEACE_REPLY_TIMEOUT_SECONDS, 45.0)


if __name__ == "__main__":
    unittest.main()
