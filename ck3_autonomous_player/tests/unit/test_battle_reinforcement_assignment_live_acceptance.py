from __future__ import annotations

import argparse
import copy
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest import mock


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "native_bridge"
    / "research"
    / "run_battle_reinforcement_assignment_live_acceptance.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_battle_reinforcement_assignment_live_acceptance", SCRIPT
)
assert SPEC is not None and SPEC.loader is not None
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)


SUBJECT = 83_886_341
SIBLING = 83_886_342
NATIVE_ARMY = 100_663_397
COORDINATOR = 117_440_519
TARGET = 2_579
CURRENT = 2_578
COMBAT = 335_544_325
DATE_RAW = 53_178_264
NATIVE_REVISION = 5
PUBLIC_REVISION = 4


def _mailbox(executed_requests: int) -> dict[str, object]:
    return {
        "query_scope": HARNESS.EXPECTED_QUERY_SCOPE,
        "installed": True,
        "stop": False,
        "failure": 0,
        "pump_epochs": 21,
        "consecutive_verified": 7,
        "owner_tid": 9191,
        "current_tid": 9191,
        "tls_global": 1,
        "tls_context": 0x7FF600001000,
        "tls_marker": 1,
        "jomini_state": 0x7FF600002000,
        "game_state": 0x7FF600003000,
        "date_raw": DATE_RAW,
        "paused": True,
        "stamp_read_success": True,
        "executed_requests": executed_requests,
        "executor_submission_enabled": True,
        "ready": True,
    }


def _capabilities(executed_requests: int = 10) -> dict[str, object]:
    native_capabilities = [
        HARNESS.QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1_CAPABILITY,
        HARNESS.QUERY_BATTLE_TRANSITION_V1_CAPABILITY,
    ]
    return {
        "mode": "native-headless",
        "backend_id": "native-headless",
        "bridge_capabilities": native_capabilities,
        "battle_reinforcement_assignment_v1_query_supported": True,
        "diagnostics": {
            "connected": True,
            "semantic_state_available": True,
            "bridge_pid": 80196,
            "connection_generation": 3,
            "hello": {
                "pid": 80196,
                "expected_ck3_version": HARNESS.EXPECTED_GAME_VERSION,
                "expected_ck3_sha256": (
                    HARNESS.EXPECTED_EXECUTABLE_SHA256
                ),
                "game_adapter_id": HARNESS.EXPECTED_ADAPTER_ID,
                "game_adapter_status": "ready",
                "ck3_build_match": True,
                "capabilities": native_capabilities,
            },
            "last_heartbeat": {
                "sequence": 100 + executed_requests,
                "main_thread_query_mailbox_v1": _mailbox(
                    executed_requests
                ),
            },
        },
    }


def _army(*, in_combat: bool = False) -> dict[str, object]:
    return {
        "army_id": SUBJECT,
        "owner_character_id": 29_829,
        "soldiers": None,
        "current_province_id": CURRENT,
        "move_target_province_id": TARGET,
        "move_target_observable": True,
        "route_province_ids": [TARGET],
        "controllable": False,
        "in_combat": in_combat,
        "retreating": False,
        "army_state": "combat" if in_combat else "moving",
        "army_state_code": 2 if in_combat else 7,
        "source": "native",
    }


def _snapshot(*, in_combat: bool = False) -> dict[str, object]:
    subject = _army(in_combat=in_combat)
    return {
        "snapshot_id": f"native:{NATIVE_REVISION}",
        "revision": PUBLIC_REVISION,
        "native_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "map_ready": True,
        "paused": True,
        "episode_character_id": 29_829,
        "episode_run_id": "native-29829-reinforcement",
        "player_armies": [],
        "active_wars": [
            {
                "war_id": 16_777_290,
                "allied_armies": [],
                "enemy_armies": [subject],
            }
        ],
    }


def _frame(
    *,
    active_combat_id: int | None = None,
    contact_combat_id: int | None = COMBAT,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "contract_stage": "production_exact_ai_reinforcement_assignment",
        "status": "available",
        "unavailable_reason": None,
        "battle_reinforcement_assignment_ready": True,
        "snapshot_revision": NATIVE_REVISION,
        "observed_date_raw": DATE_RAW,
        "selected_public_cunit_id": SUBJECT,
        "selected_native_carmy_id": NATIVE_ARMY,
        "coordinator_id": COORDINATOR,
        "unit_stack_stored_index": 2,
        "subunit_stored_index": 0,
        "signal": {
            "asking_for_help": False,
            "assigned_to_help": True,
            "asking_changed_last_evaluation": True,
            "request_power_basis_raw": None,
            "cross_coordinator_request_valid_raw": 1,
            "cross_coordinator_request_power_raw": 2_300_000,
            "first_route_edge_remaining_duration_q100000": 150_000,
        },
        "assignment": {
            "assignment_target_province_id": TARGET,
            "target_provenance": "native_help_override",
            "combat_binding_status": (
                "already_in_active_combat"
                if active_combat_id is not None
                else "unbound_until_contact"
            ),
            "active_combat_id": active_combat_id,
        },
        "route": {
            "current_province_id": CURRENT,
            "move_target_province_id": TARGET,
            "route_province_ids": [TARGET],
            "route_alignment": "aligned_to_assignment",
            "arrival_date_raws": [DATE_RAW + 24],
            "assignment_eta_date_raw": DATE_RAW + 24,
        },
        "native_order": {
            "support_search_province_ids_in_stored_order": [
                TARGET,
                TARGET,
            ],
            "parent_subunits_in_stored_order": [
                {
                    "public_cunit_ids_in_stored_order": [SUBJECT],
                    "asking_for_help": False,
                    "assigned_to_help": True,
                    "assignment_target_province_id": TARGET,
                },
                {
                    "public_cunit_ids_in_stored_order": [SIBLING],
                    "asking_for_help": True,
                    "assigned_to_help": False,
                    "assignment_target_province_id": None,
                },
            ],
        },
        "contact_projection": {
            "status": "available",
            "temporal_semantics": (
                "present_time_only_not_future_binding"
            ),
            "current_target_compatible_combat_ids_in_stored_order": (
                [contact_combat_id]
                if contact_combat_id is not None
                else []
            ),
            "contact_if_now_selected_combat_id": contact_combat_id,
        },
    }


def _query_result(sequence: int, frame: dict[str, object]) -> dict[str, object]:
    return {
        "status": "available",
        "query_sequence": sequence,
        "snapshot_revision": NATIVE_REVISION,
        "queried_snapshot_id": f"native:{NATIVE_REVISION}",
        "queried_revision": PUBLIC_REVISION,
        "queried_native_revision": NATIVE_REVISION,
        "battle_reinforcement_assignment": copy.deepcopy(frame),
    }


def _pair(frame: dict[str, object] | None = None) -> dict[str, object]:
    value = frame if frame is not None else _frame()
    return {
        "first": _query_result(40, value),
        "second": _query_result(41, value),
        "frame_sha256": "A" * 64,
        "immediate_frame_equal": True,
        "query_sequence_increased": True,
        "binding_equal": True,
        "ok": True,
    }


def _transition(
    *, province_id: int, include_subject: bool
) -> dict[str, object]:
    return {
        "status": "available",
        "battle_transition_ready": True,
        "combat_id": COMBAT,
        "province_id": province_id,
        "phase": "main",
        "attacker_public_cunit_ids_in_stored_order": (
            [SUBJECT] if include_subject else [16_777_301]
        ),
        "defender_public_cunit_ids_in_stored_order": [16_777_302],
    }


class BattleReinforcementLiveAcceptanceTests(unittest.TestCase):
    def test_exact_build_and_capability_are_both_strict(self) -> None:
        capabilities = _capabilities()
        self.assertTrue(
            HARNESS._exact_build_proof(
                capabilities, HARNESS.EXPECTED_EXECUTABLE_SHA256
            )["ok"]
        )
        self.assertTrue(HARNESS._capability_proof(capabilities)["ok"])

        bad_sha = copy.deepcopy(capabilities)
        bad_sha["diagnostics"]["hello"]["expected_ck3_sha256"] = "0" * 64
        self.assertFalse(
            HARNESS._exact_build_proof(
                bad_sha, HARNESS.EXPECTED_EXECUTABLE_SHA256
            )["ok"]
        )
        missing = copy.deepcopy(capabilities)
        missing["bridge_capabilities"].remove(
            HARNESS.QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1_CAPABILITY
        )
        self.assertFalse(HARNESS._capability_proof(missing)["ok"])

    def test_main_thread_generation_binds_owner_tls_and_execution_delta(
        self,
    ) -> None:
        proof = HARNESS._main_thread_generation_proof(
            _capabilities(10),
            _capabilities(13),
            _snapshot(),
            _pair(),
            expected_executions=3,
        )
        self.assertTrue(proof["ok"])
        self.assertEqual(proof["observed_execution_delta"], 3)

        changed = _capabilities(13)
        changed["diagnostics"]["connection_generation"] = 4
        self.assertFalse(
            HARNESS._main_thread_generation_proof(
                _capabilities(10),
                changed,
                _snapshot(),
                _pair(),
                expected_executions=3,
            )["ok"]
        )
        stale = _capabilities(12)
        self.assertFalse(
            HARNESS._main_thread_generation_proof(
                _capabilities(10),
                stale,
                _snapshot(),
                _pair(),
                expected_executions=3,
            )["ok"]
        )

    def test_assigned_route_and_contact_battle_are_consistent(self) -> None:
        frame = _frame()
        probes = [
            {
                "kind": "contact_if_now",
                "combat_id": COMBAT,
                "result": _transition(
                    province_id=TARGET, include_subject=False
                ),
            }
        ]
        proof = HARNESS._consistency_proof(
            _snapshot(),
            SUBJECT,
            frame,
            probes,
            require_assigned=True,
            expected_target_province_id=TARGET,
        )
        self.assertTrue(proof["ok"])
        self.assertTrue(proof["assignment_observed"])
        self.assertTrue(proof["aligned_assignment_eta_ready"])

    def test_current_battle_requires_subject_membership_and_province(self) -> None:
        frame = _frame(active_combat_id=COMBAT, contact_combat_id=None)
        good = [
            {
                "kind": "active_combat",
                "combat_id": COMBAT,
                "result": _transition(
                    province_id=CURRENT, include_subject=True
                ),
            }
        ]
        self.assertTrue(
            HARNESS._consistency_proof(
                _snapshot(in_combat=True),
                SUBJECT,
                frame,
                good,
                require_assigned=True,
                expected_target_province_id=TARGET,
            )["ok"]
        )
        missing = copy.deepcopy(good)
        missing[0]["result"] = _transition(
            province_id=CURRENT, include_subject=False
        )
        self.assertFalse(
            HARNESS._consistency_proof(
                _snapshot(in_combat=True),
                SUBJECT,
                frame,
                missing,
                require_assigned=True,
                expected_target_province_id=TARGET,
            )["ok"]
        )

    def test_army_route_and_stored_membership_mismatches_are_red(self) -> None:
        snapshot = _snapshot()
        snapshot["active_wars"][0]["enemy_armies"][0][
            "route_province_ids"
        ] = [2_580]
        self.assertFalse(
            HARNESS._consistency_proof(
                snapshot,
                SUBJECT,
                _frame(),
                [],
                require_assigned=True,
                expected_target_province_id=TARGET,
            )["checks"]["route_matches_semantic_army"]
        )
        frame = _frame()
        frame["native_order"]["parent_subunits_in_stored_order"][0][
            "public_cunit_ids_in_stored_order"
        ] = [SIBLING]
        self.assertFalse(
            HARNESS._consistency_proof(
                _snapshot(),
                SUBJECT,
                frame,
                [],
                require_assigned=True,
                expected_target_province_id=TARGET,
            )["checks"]["native_selected_subunit_membership"]
        )

    def test_active_combat_raw_native_target_may_differ_from_route_endpoint(
        self,
    ) -> None:
        frame = _frame(active_combat_id=COMBAT, contact_combat_id=None)
        frame["signal"]["assigned_to_help"] = False
        frame["assignment"] = {
            "assignment_target_province_id": None,
            "target_provenance": "none",
            "combat_binding_status": "already_in_active_combat",
            "active_combat_id": COMBAT,
        }
        frame["route"]["move_target_province_id"] = 2_581
        frame["route"]["route_alignment"] = "no_assignment"
        frame["route"]["assignment_eta_date_raw"] = None
        frame["native_order"]["parent_subunits_in_stored_order"][0][
            "assigned_to_help"
        ] = False
        frame["native_order"]["parent_subunits_in_stored_order"][0][
            "assignment_target_province_id"
        ] = None
        proof = HARNESS._consistency_proof(
            _snapshot(in_combat=True),
            SUBJECT,
            frame,
            [
                {
                    "kind": "active_combat",
                    "combat_id": COMBAT,
                    "result": _transition(
                        province_id=CURRENT, include_subject=True
                    ),
                }
            ],
            require_assigned=False,
            expected_target_province_id=None,
        )
        self.assertTrue(proof["ok"])
        self.assertFalse(
            proof["route_semantics"][
                "native_slot_matches_semantic_route_endpoint"
            ]
        )

    def test_duplicate_semantic_observations_must_agree(self) -> None:
        snapshot = _snapshot()
        snapshot["player_armies"] = [_army()]
        self.assertTrue(
            HARNESS._consistency_proof(
                snapshot,
                SUBJECT,
                _frame(contact_combat_id=None),
                [],
                require_assigned=True,
                expected_target_province_id=TARGET,
            )["checks"]["semantic_subject_observations_agree"]
        )
        snapshot["player_armies"][0]["current_province_id"] = 2_580
        self.assertFalse(
            HARNESS._consistency_proof(
                snapshot,
                SUBJECT,
                _frame(contact_combat_id=None),
                [],
                require_assigned=True,
                expected_target_province_id=TARGET,
            )["checks"]["semantic_subject_observations_agree"]
        )

    def test_query_pair_requires_equal_frame_and_increasing_sequence(self) -> None:
        class Service:
            def __init__(self) -> None:
                self.sequence = 20

            def query_battle_reinforcement_assignment_v1(
                self, subject: int, *, expected_revision: int
            ) -> dict[str, object]:
                self.sequence += 1
                self.assertions = (subject, expected_revision)
                return _query_result(self.sequence, _frame())

        service = Service()
        result = HARNESS._query_pair(service, SUBJECT, _snapshot())
        self.assertTrue(result["ok"])
        self.assertEqual(service.assertions, (SUBJECT, PUBLIC_REVISION))

    def test_runner_source_is_explicitly_read_only(self) -> None:
        proof = HARNESS._read_only_runner_proof()
        self.assertTrue(proof["ok"])
        self.assertEqual(proof["mutation_commands_executed"], [])
        self.assertEqual(
            proof["forbidden_native_calls"], ["0x2208320", "0x27FB7C0"]
        )
        self.assertEqual(proof["forbidden_native_calls_invoked"], [])

    def test_managed_run_queries_twice_and_proves_cleanup_without_ck3(
        self,
    ) -> None:
        events: list[str] = []
        snapshot = _snapshot()
        frame = _frame(contact_combat_id=None)

        class Driver:
            def __init__(self, *args: object, **kwargs: object) -> None:
                self.executed = 0

            def capabilities(self) -> dict[str, object]:
                return _capabilities(self.executed)

            def take_snapshot(self) -> dict[str, object]:
                return copy.deepcopy(snapshot)

            def close(self) -> None:
                events.append("driver_close")

        class Service:
            def __init__(self, driver: Driver) -> None:
                self.driver = driver

            def snapshot(self) -> dict[str, object]:
                return self.driver.take_snapshot()

            def query_battle_reinforcement_assignment_v1(
                self, subject: int, *, expected_revision: int
            ) -> dict[str, object]:
                self.driver.executed += 1
                events.append("query_reinforcement")
                return _query_result(self.driver.executed, frame)

            def query_battle_transition_v1(
                self, combat_id: int, *, expected_revision: int
            ) -> dict[str, object]:
                raise AssertionError("fixture has no battle probe")

        def session(
            spec: object,
            *,
            stop_event: object,
            **kwargs: object,
        ) -> dict[str, object]:
            events.append("session_start")
            self.assertTrue(stop_event.wait(2.0))
            events.append("session_stop")
            return {"ok": True, "pid": 80196, "shutdown": {"ok": True}}

        def cleanup(
            report: object,
            *,
            session_error: object,
            driver_closed: bool,
            elapsed_seconds: float,
        ) -> dict[str, object]:
            return {
                "ok": bool(
                    isinstance(report, dict)
                    and report.get("ok") is True
                    and session_error is None
                    and driver_closed
                )
            }

        args = argparse.Namespace(
            state_dir=Path("state"),
            game_dir=Path("game"),
            bridge_pipe="reinforcement-offline-test",
            bridge_dll=Path("bridge.dll"),
            bridge_injector=Path("injector.exe"),
            output=Path("artifact.json"),
            subject_public_cunit_id=SUBJECT,
            expected_target_province_id=TARGET,
            require_assigned=True,
            timeout=10.0,
            readiness_timeout=2.0,
            mailbox_observation_timeout=1.0,
            cold_start_checkpoint=True,
        )
        spec = SimpleNamespace(
            state_dir=Path("state"),
            profile_dir=Path("state/profile"),
            game_exe=Path("game/binaries/ck3.exe"),
        )
        with (
            mock.patch.object(HARNESS, "make_spec", return_value=spec),
            mock.patch.object(
                HARNESS, "NativeHeadlessGameplayDriver", Driver
            ),
            mock.patch.object(HARNESS, "GameplayBridgeService", Service),
            mock.patch.object(HARNESS, "native_session", side_effect=session),
            mock.patch.object(
                HARNESS,
                "_wait_for_readiness",
                return_value={"paused": True, "map_ready": True},
            ),
            mock.patch.object(
                HARNESS, "_cleanup_report", side_effect=cleanup
            ),
            mock.patch.object(
                HARNESS,
                "_sha256_file",
                return_value=HARNESS.EXPECTED_EXECUTABLE_SHA256,
            ),
        ):
            payload, exit_code = HARNESS._run(args)

        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(events.count("query_reinforcement"), 2)
        self.assertIn("session_stop", events)
        self.assertEqual(events[-1], "driver_close")
        self.assertTrue(payload["cleanup"]["ok"])
        self.assertEqual(
            payload["read_only_proof"]["mutation_commands_executed"], []
        )

    def test_main_materializes_the_json_artifact(self) -> None:
        payload = {
            "ok": True,
            "query_pair": {"frame_sha256": "B" * 64},
            "readiness_gates": {"managed_cleanup": True},
            "cleanup": {"ok": True},
            "error": None,
        }
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "logs" / "reinforcement-live.json"
            argv = [
                str(SCRIPT),
                "--state-dir",
                str(Path(temporary) / "state"),
                "--game-dir",
                str(Path(temporary) / "game"),
                "--bridge-pipe",
                "artifact-offline-test",
                "--bridge-dll",
                str(Path(temporary) / "bridge.dll"),
                "--bridge-injector",
                str(Path(temporary) / "injector.exe"),
                "--output",
                str(output),
                "--subject-public-cunit-id",
                str(SUBJECT),
            ]
            with (
                mock.patch.object(HARNESS.sys, "argv", argv),
                mock.patch.object(HARNESS, "_run", return_value=(payload, 0)),
                mock.patch("builtins.print"),
            ):
                self.assertEqual(HARNESS.main(), 0)
            self.assertEqual(
                HARNESS.json.loads(output.read_text(encoding="utf-8")),
                payload,
            )


if __name__ == "__main__":
    unittest.main()
