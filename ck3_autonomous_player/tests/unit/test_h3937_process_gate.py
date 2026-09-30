"""Exercise the actual worker handoff and native-session closure without CK3."""
import ast
from contextlib import contextmanager, ExitStack
import inspect
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from xar_autoplayer import h3937_cold_observer_once_enable as entry
from xar_autoplayer import h3937_combined_paused_war_scope_run as outer


class ActualH3937ProcessGateTests(unittest.TestCase):
    def test_worker_passes_single_keeper_and_abort_to_actual_session_closure(self):
        class Keeper:
            def __init__(self):
                self.abort = threading.Event()
                self.starts = self.stops = self.gates = 0
            def start(self):
                self.starts += 1
            def stop(self):
                self.stops += 1
            def report(self):
                return {"failure": None, "thread_exited": True}
            @contextmanager
            def process_create_gate(self):
                self.gates += 1
                yield
        keeper = Keeper()
        calls = []
        production_source = inspect.getsource(outer.collect_h3937_combined_paused_war_scope_once)

        def session_spy(spec, **options):
            calls.append(options)
            with options["before_process_create"]():
                self.assertIs(options["stop_event"], keeper.abort)
            return {"fixture_only": True}

        def collect_spy(spec, **options):
            self.assertIs(options["before_process_create"].__self__, keeper)
            self.assertIs(options["managed_stop_event"], keeper.abort)
            # Execute the actual production nested supervisor function. No game,
            # bridge, desktop or other parts of the managed session are started.
            tree = ast.parse(production_source)
            closure = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "supervise")
            environment = {"spec": spec, "timeout": 1, "SESSION_TIMEOUT_GRACE_SECONDS": 1,
                           "config": options["native_bridge"], "poll_seconds": 0.1,
                           "stop_event": options["managed_stop_event"],
                           "before_process_create": options["before_process_create"],
                           "diagnostic_event": None, "session_state": {},
                           "session_done": threading.Event(), "native_session": session_spy}
            exec(compile(ast.fix_missing_locations(ast.Module(body=[closure], type_ignores=[])), "actual-h3937-session-closure", "exec"), environment)
            environment["supervise"]()
            self.assertIsNone(environment["session_state"].get("error"))
            return {"ok": False, "status": "fixture-only-no-semantic-read"}

        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            output = Path(directory)
            claim = {"schema": "xar.war.h3937-cold-observer-supervisor-claim.v1", "claim_nonce": "fixture",
                     "round": entry.ROUND, "live_run_id": entry.LIVE_RUN_ID,
                     "run_config_sha256": entry.RUN_CONFIG_SHA256,
                     "output_dir": str(output), "head": "fixture-head"}
            go = {"screen_task_last_sequence": 123, "operator_direct_review_evidence": {"review_receipt_path": str(output/"review.json"), "review_receipt_sha256": "A"*64}}
            for name in ("steam_original", "steam_frame_receipt", "screen_challenge", "screen_lease_receipt"):
                go[name+"_path"], go[name+"_sha256"] = str(output/(name+".json")), "A"*64
            replacements = {"OUTPUT": output, "_read_json": lambda path: claim,
                            "_git": lambda *args: "fixture-head", "_sha": lambda path: "A"*64,
                            "_require_exact_admission": lambda: {}, "_require_go": lambda identity: (go,"A"*64),
                            "_require_zero_live_inventory": lambda: {}, "_require_pipe_server_absent": lambda: None,
                            "_require_live_screen_lease": lambda *args: {}, "_require_no_launch_unchanged": lambda identity: None,
                            "_image_inventory": lambda image: {"returncode":0,"found":False},
                            "screen_keeper_for_runner": lambda runner,sequence: keeper}
            for name,value in replacements.items():
                stack.enter_context(patch.object(entry,name,value))
            stack.enter_context(patch.object(outer,"collect_h3937_combined_paused_war_scope_once",collect_spy))
            completion = entry.run_exact_once("fixture")
            self.assertEqual(completion["status"], "RED")
            self.assertIsNone(completion["error"])
        self.assertEqual((keeper.starts,keeper.stops,keeper.gates,len(calls)),(1,1,1,1))


if __name__ == "__main__":
    unittest.main(verbosity=2)
