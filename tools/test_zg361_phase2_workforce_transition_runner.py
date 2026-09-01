from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import threading
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))


def install_optional_desktop_import_stubs() -> None:
    attributes = {
        "pyautogui": (
            "FAILSAFE",
            "press",
            "hotkey",
            "moveTo",
            "click",
            "mouseDown",
            "mouseUp",
            "size",
        ),
        "numpy": (),
        "cv2": (),
        "win32api": ("GetKeyboardLayoutList",),
        "win32con": (),
        "win32gui": ("GetForegroundWindow", "GetWindowText"),
        "win32process": ("GetWindowThreadProcessId",),
    }
    for name, names in attributes.items():
        if importlib.util.find_spec(name) is None:
            module = types.ModuleType(name)
            for attribute in names:
                setattr(module, attribute, None)
            sys.modules[name] = module


install_optional_desktop_import_stubs()
import run_zhongguo_acceptance as runner


OWNER = 9200
SUBJECT = 9001


def paused_snapshot(
    *, pid: int, generation: int, revision: int, player: int = SUBJECT
) -> dict[str, object]:
    return {
        "snapshot_id": f"snapshot-{pid}-{revision}",
        "revision": revision,
        "native_revision": revision + 100,
        "date_raw": 777,
        "paused": True,
        "map_ready": True,
        "played_character": {"character_id": player},
        "diagnostics": {
            "bridge_pid": pid,
            "connection_generation": generation,
        },
        "active_event": None,
    }


def shutdown_proof(pid: int) -> dict[str, object]:
    return {
        "ck3_pid": pid,
        "ok": True,
        "cleanup_proven": True,
        "tree_gone": True,
        "job_active_processes_final": 0,
        "final_ck3_inventory": {"processes": []},
        "watchdog_state_after": "absent",
        "control_files_absent": {
            "pid": True,
            "ready": True,
            "watchdog_error": True,
            "unsafe": True,
        },
        "contract_errors": [],
    }


def restore_record(
    *, before_pid: int, after_pid: int, before_generation: int
) -> dict[str, object]:
    after_generation = before_generation + 1
    return {
        "label": f"restore-{after_generation}",
        "before": {
            "bridge_pid": before_pid,
            "connection_generation": before_generation,
            "player_character_id": SUBJECT,
            "date_raw": 777,
        },
        "after": {
            "bridge_pid": after_pid,
            "connection_generation": after_generation,
            "player_character_id": SUBJECT,
            "date_raw": 777,
        },
        "result": {
            "accepted": True,
            "status": "restored",
            "source": "native-session-lifecycle-queue",
        },
        "restored_checkpoint": {
            "status": "restored",
            "size": 1234,
            "sha256": "b" * 64,
        },
        "lifecycle": {
            "previous_pid": before_pid,
            "pid": after_pid,
            "previous_connection_generation": before_generation,
            "connection_generation": after_generation,
            "lifecycle_intent": "restore",
            "request_id": f"restore-{after_generation}",
        },
        "checks": {"typed": True},
    }


def seven_pid_scenario() -> dict[str, object]:
    records = [
        restore_record(
            before_pid=before_pid,
            after_pid=after_pid,
            before_generation=before_generation,
        )
        for before_pid, after_pid, before_generation in zip(
            (20, 30, 40, 50, 60),
            (30, 40, 50, 60, 70),
            (2, 3, 4, 5, 6),
        )
    ]
    return {
        "save_restore_lineage": {
            "result": "GREEN",
            "scope": "phase2_one_save_one_restore_two_pid_lineage",
            "first_pid": 10,
            "second_pid": 20,
            "pid_lineage": [10, 20],
            "first_connection_generation": 1,
            "second_connection_generation": 2,
            "connection_generation_lineage": [1, 2],
            "two_pid_lineage_proven": True,
            "save_result": {
                "accepted": True,
                "checkpoint": {
                    "status": "saved",
                    "size": 1234,
                    "sha256": "a" * 64,
                },
            },
            "restore_result": {
                "accepted": True,
                "status": "restored",
                "source": "native-session-lifecycle-queue",
                "lifecycle": {
                    "previous_pid": 10,
                    "pid": 20,
                    "lifecycle_intent": "restore",
                    "request_id": "base-restore",
                },
            },
            "checks": {"final_capabilities_bind_second_pid": True},
        },
        "workforce_collective_gameplay_action_cell": {
            "result": "GREEN",
            "session_lineage": {
                "scope": (
                    "phase2_workforce_activation_three_route_final_restore"
                ),
                "result": "GREEN",
                "baseline_restored": True,
                "restore_count": 5,
                "pid_lineage": [20, 30, 40, 50, 60, 70],
                "connection_generation_lineage": [2, 3, 4, 5, 6, 7],
                "restore_records": records,
                "final_binding": records[-1]["after"],
            },
        },
    }


class FixtureInstallTests(unittest.TestCase):
    def test_dynamic_fixture_appends_only_the_isolated_profile(self) -> None:
        seed_source = (
            runner.ROOT / "tools" / "fixtures" / "zg361_phase2_seed_bootstrap"
        )
        seed_before = runner.isolated.tree_snapshot(seed_source)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            userdir = root / "userdir"
            artifacts = root / "artifacts"
            userdir.mkdir()
            artifacts.mkdir()
            (userdir / "mod").mkdir()
            baseline = ["mod/product.mod", "mod/seed.mod"]
            (userdir / "dlc_load.json").write_text(
                json.dumps({"enabled_mods": baseline}), encoding="utf-8"
            )
            evidence = runner.install_phase2_workforce_action_fixture(
                userdir,
                {"enabled_mods": baseline},
                artifacts,
            )
            self.assertEqual(evidence["result"], "GREEN")
            self.assertTrue(evidence["acceptance_only"])
            self.assertFalse(evidence["release_included"])
            self.assertFalse(evidence["promo_included"])
            self.assertEqual(evidence["enabled_mods_before"], baseline)
            self.assertEqual(
                evidence["enabled_mods_after"],
                [
                    *baseline,
                    f"mod/{runner.PHASE2_WORKFORCE_ACTION_FIXTURE_OUTER}",
                ],
            )
            target = userdir / "mod-content" / "phase2_workforce_action_fixture"
            self.assertEqual(
                runner.isolated.tree_snapshot(target),
                runner.isolated.tree_snapshot(
                    runner.PHASE2_WORKFORCE_ACTION_FIXTURE_SOURCE
                ),
            )
            self.assertTrue(
                (userdir / "mod" / runner.PHASE2_WORKFORCE_ACTION_FIXTURE_OUTER)
                .is_file()
            )
        self.assertEqual(
            runner.isolated.tree_snapshot(seed_source), seed_before
        )


class MultiRestoreLineageTests(unittest.TestCase):
    def test_cleanup_proves_all_seven_pids(self) -> None:
        scenario = seven_pid_scenario()
        projection = runner._phase2_expected_session_lineage(scenario)
        self.assertEqual(projection["pid_lineage"], [10, 20, 30, 40, 50, 60, 70])
        self.assertEqual(
            projection["connection_generation_lineage"],
            [1, 2, 3, 4, 5, 6, 7],
        )
        report = {
            "kind": "ck3_native_headless_session",
            "mode": "native-headless",
            "pipe": "test-pipe",
            "pid": 70,
            "exit_reason": "stop",
            "process_exit_code": None,
            "shutdown": shutdown_proof(70),
            "restart_count": 6,
            "restart_shutdowns": [
                shutdown_proof(pid) for pid in (10, 20, 30, 40, 50, 60)
            ],
            "ok": True,
        }
        with tempfile.TemporaryDirectory() as temporary:
            evidence = runner.prove_phase2_native_session_cleanup(
                report,
                Path(temporary),
                initial_pid=10,
                initial_generation=1,
                expected_pipe="test-pipe",
                scenario_evidence=scenario,
                final_capabilities={
                    "diagnostics": {
                        "connected": True,
                        "bridge_pid": 70,
                        "connection_generation": 7,
                    }
                },
                supervisor_stopped=True,
            )
        self.assertEqual(evidence["result"], "GREEN")
        self.assertEqual(evidence["expected_final_pid"], 70)
        self.assertTrue(
            evidence["checks"]["restart_count_matches_full_lineage"]
        )
        self.assertTrue(
            evidence["checks"]["workforce_restore_lifecycle_chain_exact"]
        )
        self.assertTrue(
            evidence["checks"]["retired_pid_6_shutdown_cleanup_proven"]
        )
        self.assertTrue(evidence["checks"]["final_pid_shutdown_cleanup_proven"])

    def test_liveness_binds_the_seventh_pid(self) -> None:
        scenario = seven_pid_scenario()
        stop = threading.Event()
        thread = threading.Thread(target=stop.wait)
        thread.start()

        class Service:
            def capabilities(self) -> dict[str, object]:
                return {
                    "diagnostics": {
                        "connected": True,
                        "bridge_pid": 70,
                        "connection_generation": 7,
                    }
                }

            def snapshot(self) -> dict[str, object]:
                return paused_snapshot(pid=70, generation=7, revision=80)

        try:
            with tempfile.TemporaryDirectory() as temporary:
                evidence = runner.phase2_native_session_liveness_gate(
                    Service(),
                    {
                        "session_done": threading.Event(),
                        "session_thread": thread,
                    },
                    Path(temporary),
                    scenario_evidence=scenario,
                )
            self.assertEqual(evidence["result"], "GREEN")
            self.assertEqual(evidence["expected_pid"], 70)
            self.assertEqual(evidence["binding"]["bridge_pid"], 70)
        finally:
            stop.set()
            thread.join(timeout=2)


class WorkforceMatrixTests(unittest.TestCase):
    def test_matrix_restores_one_checkpoint_for_a_b_c_and_final(self) -> None:
        class Service:
            def __init__(self) -> None:
                self.snapshots = [
                    paused_snapshot(pid=20, generation=2, revision=20),
                    paused_snapshot(pid=30, generation=3, revision=30),
                ]

            def snapshot(self) -> dict[str, object]:
                return copy.deepcopy(self.snapshots.pop(0))

        service = Service()
        install = {
            "result": "GREEN",
            "acceptance_only": True,
            "release_included": False,
            "promo_included": False,
        }
        activation_checkpoint = {
            "status": "saved",
            "size": 1234,
            "sha256": "a" * 64,
            "date_raw": 777,
        }
        shared_checkpoint = {
            "status": "saved",
            "size": 1234,
            "sha256": "b" * 64,
            "date_raw": 777,
        }
        save_results = [
            {"checkpoint": activation_checkpoint},
            {"checkpoint": shared_checkpoint},
        ]
        restore_results: list[dict[str, object]] = []
        prior_pid = 20
        prior_generation = 2
        for index in range(5):
            after_pid = 30 + index * 10
            row = restore_record(
                before_pid=prior_pid,
                after_pid=after_pid,
                before_generation=prior_generation,
            )
            if index == 0:
                row["restored_checkpoint"] = {
                    "status": "restored",
                    "size": 1234,
                    "sha256": "a" * 64,
                }
            restore_results.append(row)
            prior_pid = after_pid
            prior_generation += 1
        transition_calls: list[dict[str, object]] = []
        matrix_calls: list[dict[str, object]] = []
        sequence: list[str] = []

        def fixture_install(*_args: object) -> dict[str, object]:
            sequence.append("install-fixture")
            return copy.deepcopy(install)

        def save(
            _service: object, *, label: str
        ) -> dict[str, object]:
            self.assertIs(_service, service)
            sequence.append(f"save:{label}")
            return copy.deepcopy(save_results.pop(0))

        def restore(
            _service: object, *, label: str, **_kwargs: object
        ) -> dict[str, object]:
            self.assertIs(_service, service)
            sequence.append(f"restore:{label}")
            return copy.deepcopy(restore_results.pop(0))

        def wait_event(
            _service: object,
            *,
            expected_definition_key: str,
            **_kwargs: object,
        ) -> dict[str, object]:
            self.assertIs(_service, service)
            sequence.append(f"wait:{expected_definition_key}")
            return {"binding": {}, "identity": {}}

        def transition(
            _service: object, **kwargs: object
        ) -> dict[str, object]:
            self.assertIs(_service, service)
            transition_calls.append(dict(kwargs))
            sequence.append(
                "transition:"
                f"{kwargs['expected_event_definition_key']}:"
                f"{kwargs['expected_player_before']}->"
                f"{kwargs['expected_player_after']}"
            )
            return {
                "result": "GREEN",
                "native_played_character_postcondition": {
                    "played_character_id": kwargs["expected_player_after"]
                },
            }

        def matrix(
            _service: object, **kwargs: object
        ) -> dict[str, object]:
            self.assertIs(_service, service)
            matrix_calls.append(dict(kwargs))
            sequence.append(f"matrix:{kwargs['route']}")
            binding = SimpleNamespace(
                owner_character_id=OWNER,
                subject_character_id=SUBJECT,
            )
            subject_service = kwargs["subject_service_factory"](binding)
            self.assertIs(subject_service, service)
            return {"result": "GREEN"}

        with tempfile.TemporaryDirectory() as temporary, (
            mock.patch.object(
                runner,
                "install_phase2_workforce_action_fixture",
                side_effect=fixture_install,
            )
        ), mock.patch.object(
            runner,
            "_save_phase2_workforce_checkpoint",
            side_effect=save,
        ) as save_call, mock.patch.object(
            runner,
            "_restore_phase2_workforce_checkpoint",
            side_effect=restore,
        ) as restore_call, mock.patch.object(
            runner,
            "wait_for_phase2_exact_event",
            side_effect=wait_event,
        ), mock.patch.object(
            runner,
            "select_typed_fixture_player_transition",
            side_effect=transition,
        ), mock.patch.object(
            runner,
            "run_m360_action_and_postcondition",
            side_effect=matrix,
        ):
            evidence = runner.run_phase2_workforce_m360_gameplay_action_cell(
                service,
                Path(temporary),
                userdir=Path(temporary) / "userdir",
                bootstrap={"enabled_mods": []},
                owner_character_id=OWNER,
                subject_character_id=SUBJECT,
                b2_owner_character_id=9300,
                prior_lineage={"pid_lineage": [10, 20]},
            )

        self.assertEqual(evidence["result"], "GREEN")
        self.assertEqual(save_call.call_count, 2)
        self.assertEqual(restore_call.call_count, 5)
        self.assertEqual(
            [call.kwargs["label"] for call in restore_call.call_args_list],
            [
                "Workforce fixture activation",
                "Workforce route A",
                "Workforce route B",
                "Workforce route C",
                "Workforce final frozen baseline",
            ],
        )
        self.assertEqual([row["route"] for row in matrix_calls], ["A", "B", "C"])
        self.assertTrue(
            all(
                row["post_ack_event_definition_allowlist"]
                == (runner.PHASE2_WORKFORCE_SWITCH_BACK_EVENT,)
                for row in matrix_calls
            )
        )
        self.assertEqual(len(transition_calls), 6)
        self.assertEqual(
            evidence["session_lineage"]["pid_lineage"],
            [20, 30, 40, 50, 60, 70],
        )
        self.assertTrue(evidence["checks"]["three_independent_route_restores"])
        self.assertTrue(evidence["checks"]["native_subject_restored"])
        expected_sequence = [
            "install-fixture",
            "save:Workforce fixture activation",
            "restore:Workforce fixture activation",
            f"wait:{runner.PHASE2_WORKFORCE_ACTION_FIXTURE_EVENT}",
            "save:shared pre-M360 A/B/C",
        ]
        for route in ("A", "B", "C"):
            expected_sequence.extend(
                [
                    f"restore:Workforce route {route}",
                    f"wait:{runner.PHASE2_WORKFORCE_ACTION_FIXTURE_EVENT}",
                    (
                        "transition:"
                        f"{runner.PHASE2_WORKFORCE_ACTION_FIXTURE_EVENT}:"
                        f"{SUBJECT}->{OWNER}"
                    ),
                    f"wait:{runner.M360_EVENT_DEFINITION_KEY}",
                    f"matrix:{route}",
                    (
                        "transition:"
                        f"{runner.PHASE2_WORKFORCE_SWITCH_BACK_EVENT}:"
                        f"{OWNER}->{SUBJECT}"
                    ),
                ]
            )
        expected_sequence.extend(
            [
                "restore:Workforce final frozen baseline",
                f"wait:{runner.PHASE2_WORKFORCE_ACTION_FIXTURE_EVENT}",
            ]
        )
        self.assertEqual(sequence, expected_sequence)


if __name__ == "__main__":
    unittest.main()
