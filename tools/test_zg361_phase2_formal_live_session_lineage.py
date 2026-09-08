#!/usr/bin/env python3
"""Regression tests for the complete formal-live managed PID lineage."""

from __future__ import annotations

import sys
import tempfile
import threading
from pathlib import Path
import unittest


TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_zhongguo_acceptance as runner  # noqa: E402


def _lifecycle(previous_pid: int, pid: int, generation: int) -> dict[str, object]:
    return {
        "lifecycle_intent": "restore",
        "request_id": f"restore-{pid}",
        "previous_pid": previous_pid,
        "pid": pid,
        "previous_connection_generation": generation,
        "connection_generation": generation + 1,
    }


def _restore_record(
    previous_pid: int, pid: int, generation: int
) -> dict[str, object]:
    lifecycle = _lifecycle(previous_pid, pid, generation)
    return {
        "before": {
            "bridge_pid": previous_pid,
            "connection_generation": generation,
        },
        "after": {
            "bridge_pid": pid,
            "connection_generation": generation + 1,
        },
        "lifecycle": lifecycle,
    }


def _scenario() -> dict[str, object]:
    workforce_records = [
        _restore_record(previous, current, generation)
        for previous, current, generation in zip(
            (40, 50, 60, 70, 80),
            (50, 60, 70, 80, 90),
            (4, 5, 6, 7, 8),
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
                    **_lifecycle(10, 20, 1),
                    "request_id": "base-restore",
                },
            },
            "checks": {"final_capabilities_bind_second_pid": True},
        },
        "scoreboard_gameplay_action_cell": {
            "surface_matrix": {
                "managed-capable": {
                    "preparation": {"lifecycle": _lifecycle(20, 30, 2)}
                },
                "received-only": {
                    "preparation": {"lifecycle": _lifecycle(30, 40, 3)}
                },
            }
        },
        "workforce_collective_gameplay_action_cell": {
            "session_lineage": {
                "pid_lineage": [40, 50, 60, 70, 80, 90],
                "connection_generation_lineage": [4, 5, 6, 7, 8, 9],
                "restore_records": workforce_records,
            }
        },
        "promotion_source_checkpoint_restore": {
            "restore_receipt": {"lifecycle": _lifecycle(90, 100, 9)}
        },
    }


def _paused_snapshot(pid: int, generation: int) -> dict[str, object]:
    return {
        "snapshot_id": "formal-live-final",
        "revision": 50,
        "native_revision": 60,
        "date_raw": 777,
        "paused": True,
        "map_ready": True,
        "played_character": {"character_id": 9001},
        "active_event": None,
        "diagnostics": {
            "bridge_pid": pid,
            "connection_generation": generation,
        },
    }


def _shutdown(pid: int) -> dict[str, object]:
    return {
        "ck3_pid": pid,
        "ok": True,
        "cleanup_proven": True,
        "tree_gone": True,
        "job_active_processes_final": 0,
        "final_ck3_inventory": {"processes": []},
        "watchdog_state_after": "absent",
        "control_files_absent": {"pid": True, "ready": True},
        "contract_errors": [],
    }


class FormalLiveSessionLineageTests(unittest.TestCase):
    def test_projection_orders_scoreboard_workforce_and_promotion_restores(self) -> None:
        projection = runner._phase2_expected_session_lineage(_scenario())

        self.assertEqual(
            projection["recorded_segments"],
            ["base", "scoreboard", "workforce", "promotion"],
        )
        self.assertEqual(
            projection["pid_lineage"],
            [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
        )
        self.assertEqual(
            projection["connection_generation_lineage"],
            list(range(1, 11)),
        )
        self.assertEqual(len(projection["additional_restore_records"]), 8)
        self.assertTrue(projection["all_recorded_lineage_joins_match"])
        self.assertTrue(
            projection["additional_restore_records_match_full_lineage"]
        )

    def test_liveness_binds_promotion_restore_as_the_final_session(self) -> None:
        class Service:
            @staticmethod
            def capabilities() -> dict[str, object]:
                return {
                    "diagnostics": {
                        "connected": True,
                        "bridge_pid": 100,
                        "connection_generation": 10,
                    }
                }

            @staticmethod
            def snapshot() -> dict[str, object]:
                return _paused_snapshot(100, 10)

        stop = threading.Event()
        thread = threading.Thread(target=stop.wait)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as temporary:
                evidence = runner.phase2_native_session_liveness_gate(
                    Service(),  # type: ignore[arg-type]
                    {
                        "session_done": threading.Event(),
                        "session_thread": thread,
                    },
                    Path(temporary),
                    scenario_evidence=_scenario(),
                )
            self.assertEqual(evidence["result"], "GREEN")
            self.assertEqual(evidence["expected_pid"], 100)
            self.assertEqual(evidence["expected_connection_generation"], 10)
            self.assertTrue(
                evidence["checks"][
                    "additional_restore_records_match_full_lineage"
                ]
            )
        finally:
            stop.set()
            thread.join(timeout=2)

    def test_cleanup_proves_all_ten_pids_including_promotion_final(self) -> None:
        report = {
            "kind": "ck3_native_headless_session",
            "mode": "native-headless",
            "pipe": "test-pipe",
            "pid": 100,
            "exit_reason": "stop",
            "process_exit_code": None,
            "shutdown": _shutdown(100),
            "restart_count": 9,
            "restart_shutdowns": [
                _shutdown(pid)
                for pid in (10, 20, 30, 40, 50, 60, 70, 80, 90)
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
                scenario_evidence=_scenario(),
                final_capabilities={
                    "diagnostics": {
                        "connected": True,
                        "bridge_pid": 100,
                        "connection_generation": 10,
                    }
                },
                supervisor_stopped=True,
            )

        self.assertEqual(evidence["result"], "GREEN")
        self.assertEqual(evidence["expected_final_pid"], 100)
        self.assertEqual(evidence["expected_final_generation"], 10)
        self.assertTrue(
            evidence["checks"]["additional_restore_lifecycle_chain_exact"]
        )
        self.assertTrue(
            evidence["checks"]["retired_pid_9_shutdown_cleanup_proven"]
        )


if __name__ == "__main__":
    unittest.main()
