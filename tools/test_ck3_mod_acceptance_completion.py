"""Portable completion regressions; compile only the actual pure source boundaries."""
from __future__ import annotations

import argparse
import ast
import copy
from datetime import datetime
from pathlib import Path
import threading
from types import SimpleNamespace
import unittest


REPO = Path(__file__).resolve().parents[1]


class SharedCompletionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.host = REPO / "ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py"
        host_tree = ast.parse(cls.host.read_text(encoding="utf-8-sig"))
        run = next(node for node in host_tree.body
                   if isinstance(node, ast.AsyncFunctionDef) and node.name == "run")
        cls.write_node = next(node for node in run.body
                              if isinstance(node, ast.FunctionDef) and node.name == "write")
        client_path = REPO / "tools/ck3_mod_acceptance_client.py"
        client_tree = ast.parse(client_path.read_text(encoding="utf-8-sig"))
        cls.proof_node = next(node for parent in client_tree.body if isinstance(parent, ast.ClassDef)
                              for node in parent.body
                              if isinstance(node, ast.FunctionDef) and node.name == "native_zero_proof")

    def setUp(self):
        self.done = threading.Event()
        self.published = []
        pid = 2468
        pipe = r"\\.\pipe\synthetic-completion-only"
        self.report = {
            "fixture_only": False, "error": None, "pipe": pipe, "phase": "hold",
            "session": {"error": None, "report": {
                "kind": "ck3_native_headless_session", "mode": "native-headless",
                "format_version": 1, "ok": True, "error": None,
                "exit_reason": "process_exit", "process_exit_code": 0, "pid": pid, "pipe": pipe,
                "started_at": "2026-10-08T10:00:00+00:00", "finished_at": "2026-10-08T10:00:10+00:00",
                "shutdown": {
                    "ok": True, "cleanup_proven": True, "tree_gone": True,
                    "ck3_pid": pid, "ck3_exit_code": 0, "job_active_processes_final": 0,
                    "contract_errors": [], "watchdog_state_after": "absent",
                    "nonce": "a" * 32, "ck3_creation_date": "synthetic-creation-date",
                    "control_files_absent": {"ck3.json": True, "watchdog.json": True},
                    "final_ck3_inventory": {
                        "tasklist_returncode": 0, "tasklist_pids": [], "wmi_pids": [],
                        "native_pids": [], "processes": [],
                    },
                },
            }},
        }
        namespace = {
            "done": self.done, "report": self.report,
            "args": argparse.Namespace(output=Path("synthetic-only-unused-report.json")),
            "write_atomic_report": lambda _path, value: self.published.append(copy.deepcopy(value)),
            "datetime": datetime,
        }
        module = ast.fix_missing_locations(ast.Module(
            body=[self.write_node, self.proof_node], type_ignores=[]))
        exec(compile(module, str(self.host), "exec"), namespace)
        self.write = namespace["write"]
        self.client = SimpleNamespace(
            selection=SimpleNamespace(manifest_path_key=lambda _row: self.host),
            manifest={"host": {}}, _process={"pid": pid})
        self.proof = lambda report: namespace["native_zero_proof"](self.client, report)

    def test_real_completion_event_is_observable_before_host_finally(self):
        # A returned native DTO alone must not stand in for the supervisor Event.
        self.write()
        self.assertIs(self.published[-1]["managed_session_done"], False)
        self.assertIsNone(self.proof(self.published[-1]))
        self.done.set()
        self.write()
        published = self.published[-1]
        self.assertIs(published["managed_session_done"], True)
        self.assertNotIn("managed_session_thread_finished", published)
        proof = self.proof(published)
        self.assertIsNotNone(proof)
        self.assertIs(proof["alive_or_business_credit"], False)
        self.assertIs(proof["managed_session_done"], True)

    def test_completion_and_original_native_zero_safeguards_are_required(self):
        self.done.set()
        self.write()
        valid = self.published[-1]
        legacy = copy.deepcopy(valid)
        legacy.pop("managed_session_done")
        legacy["managed_session_thread_finished"] = True
        self.assertIsNone(self.proof(legacy))
        for value in (None, False, 0, 1, "true"):
            with self.subTest(completion=value):
                candidate = copy.deepcopy(valid)
                candidate["managed_session_done"] = value
                self.assertIsNone(self.proof(candidate))
        changes = [
            ("native exit1", ("session", "report", "process_exit_code"), 1),
            ("boolean exit0", ("session", "report", "process_exit_code"), False),
            ("cleanup unproven", ("session", "report", "shutdown", "cleanup_proven"), False),
            ("PID drift", ("session", "report", "pid"), 2469),
            ("nonce absent", ("session", "report", "shutdown", "nonce"), None),
            ("job still active", ("session", "report", "shutdown", "job_active_processes_final"), 1),
            ("watchdog present", ("session", "report", "shutdown", "watchdog_state_after"), "present"),
            ("original outer failure", ("error",), "original business failure"),
            ("original supervisor failure", ("session", "error"), "original supervisor failure"),
        ]
        for name, path, value in changes:
            with self.subTest(safeguard=name):
                candidate = copy.deepcopy(valid)
                target = candidate
                for part in path[:-1]:
                    target = target[part]
                target[path[-1]] = value
                self.assertIsNone(self.proof(candidate))

    def test_publication_tracks_actual_event_instead_of_latching_report_state(self):
        self.report["managed_session_done"] = True
        self.report["managed_session_thread_finished"] = True
        self.write()
        self.assertIs(self.published[-1]["managed_session_done"], False)
        self.assertIsNone(self.proof(self.published[-1]))


if __name__ == "__main__":
    unittest.main()
