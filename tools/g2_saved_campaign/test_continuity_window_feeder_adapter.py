"""Portable replay of original feeder functions with synthetic full inputs.

The fixture retains production function source, not an executable deployment.
Readiness markers, camera, seed, errors and loop outcomes are synthetic. These
tests never connect to a game, SDK, recorder, desktop or machine-specific root.
"""
import ast
import hashlib
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

from continuity_window_feeder_adapter import adapt
from root_continuity_window import WindowLedger, TARGET_RAW


FRAME = {"date_raw": 53328720, "actor_character_id": 40526,
    "episode_run_id": "synthetic-natural-episode", "snapshot_id": "native:144",
    "native_revision": 144, "revision": 2}
GAME = {"pid": 1234, "creation_date": "20260101000000.000001+000"}


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


def fixture(root):
    recorded = read(Path(__file__).parent / "fixtures/continuity_original_feeder_functions.json")
    header = '''from datetime import datetime, timezone
import hashlib, json, os, uuid
from pathlib import Path
N = Path(__file__).resolve().parent
Q = N / "queue"
INBOX = N / "requests"
OUTBOX = N / "responses"
BATCHES = N / "batches"
STATUS = N / "status.json"
STOP = N / "STOP"
SEED = N / "ROOT-P08-CUMULATIVE-SEED.json"
MARKER = Q / "ROOT-COLD-CAMPAIGN-VERIFIED.json"
NEXT = N / "NEXT.json"
BASELINE_CYCLES = None
BASELINE_DATE_RAW = None
START_RAW = 53144328
TARGET_DAYS = 30 * 365.25
'''
    # Preserve the original footer's error-reporting span in a non-executed
    # function so the adapter checks and rewrites every old-goal reference.
    footer = '''
def fixture_outer_failure(error):
    try:
        raise error
    except Exception as error:
        status("feeder_error_review_required", error=str(error))
        raise
'''
    original = header + "\n\n".join(recorded["functions"].values()) + footer
    adapted = adapt(original)
    tree = ast.parse(adapted)
    if any(isinstance(node, ast.Name) and node.id in ("START_RAW", "TARGET_DAYS") for node in ast.walk(tree)):
        raise AssertionError("obsolete campaign age reference survived")
    module = types.ModuleType("portable_continuity_feeder")
    module.__file__ = str(root / "synthetic_feeder.py")
    exec(compile(adapted, module.__file__, "exec"), module.__dict__)
    for folder in (module.Q, module.INBOX, module.OUTBOX, module.BATCHES):
        folder.mkdir()
    seed = {"completed_cycles": 6143, "before": FRAME, "pending_cycle": None,
        "pending_checkpoint": None, "terminal": None,
        "cold_resume_source": {"original_action_replayed": False}}
    write(module.SEED, seed)
    governance = root / "governance.json"
    write(governance, {"schema": "synthetic-governance", "state": {}})
    camera = root / "camera.json"
    write(camera, {"synthetic": "already executed original camera; no invocation"})
    pixels = root / "pixels.json"
    write(pixels, {"status": "GREEN", "reviewer": "/root", "game_pid": GAME["pid"],
        "game_creation_date": GAME["creation_date"], "visible_played_realm_map_reviewed": True,
        "camera_response": str(camera)})
    def pin(path):
        return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    write(root / "ROOT-ACTUAL-GAME-LAUNCH.json", GAME)
    write(root / "ROOT-COLD-INPUTS.json", {"checkpoint": {"sha256": "a" * 64}})
    write(root / "ROOT-P08-GOVERNANCE-BOOTSTRAP-ADMITTED.json", {
        "status": "ADMITTED_SAME_GAME_REUSE_VERIFIED_CAMERA", "same_Game_pid": GAME["pid"],
        "same_Game_creation_date": GAME["creation_date"], "old_actual_pair_exits_verified": True,
        "settled_global_turn": 6143, "last_saved_checkpoint_cycle": 6140,
        "seed": pin(module.SEED), "governance": pin(governance),
        "camera_response": pin(camera), "camera_pixels": pin(pixels)})
    write(module.MARKER, {
        "status": "COLD_OR_HOT_READINESS_CAMPAIGN_VERIFIED", "driver_state_restore_kind": "same_pid_hot",
        "original_action_replayed": False, "Game_restarted": False,
        "historical_counts_source": str(module.SEED), "actual_baseline_frame": FRAME,
        "cold_restore_generation": {"game_pid": GAME["pid"], "game_creation_date": GAME["creation_date"],
            "saved_checkpoint_cycle": 6140, "historical_completed_cycles": 6143,
            "original_action_replayed": False, "checkpoint_sha256": "a" * 64}})
    WindowLedger(module.CONTINUITY_WINDOW).apply("repair_required", {
        "evidence_id": "synthetic-readonly-error", "source": {"fixture": "synthetic full error context"},
        "machine_id": "synthetic-machine", "game": GAME, "frame": FRAME,
        "completed_cycles": 6143, "reason": "blocked strategy required manual source repair"})
    module.incident_index = lambda: set()
    module.collect_incidents = lambda index: []
    return module, seed


class FeederContinuityTests(unittest.TestCase):
    def run_one_batch(self, *, delta, continuation=True):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            module, seed = fixture(root)
            self.assertEqual(module.admitted()["actual_baseline_frame"]["date_raw"], FRAME["date_raw"])
            module.status("prepared_test")
            self.assertEqual(read(module.STATUS)["continuity_window"]["status"], "prepared")
            request = {"sequence": 4, "command": "full_loop", "arguments": {"max_turns": 1},
                "source": "explicit synthetic Root control"}
            write(module.INBOX / "0004-1-result.json", request)
            result = {"status": "bounded_loop_finished", "actual_turns": 1,
                "cumulative_cycles": seed["completed_cycles"] + 1,
                "actual_end_date_raw": FRAME["date_raw"] + delta, "next_sequence": 7,
                "same_SDK_continuation_available": continuation,
                "reason": "synthetic terminal needs repair" if not continuation else None}
            write(module.OUTBOX / "0004-1-result.json", {"request": request,
                "result": {"is_error": False, "structured_content": result}})
            write(module.Q / "ROOT-CUMULATIVE-LOOP-STATE.json", {
                "completed_cycles": result["cumulative_cycles"],
                "before": {**FRAME, "date_raw": result["actual_end_date_raw"]}})
            published = []
            def follow(sequence):
                published.append(sequence)
                module.STOP.touch()
                return "synthetic_follow_no_RPC"
            with patch.object(module, "publish_or_follow", side_effect=follow):
                module.main(4)
            return WindowLedger(module.CONTINUITY_WINDOW).load(), published, read(module.STATUS)

    def test_status_admitted_main_old_campaign_goal_does_not_stop(self):
        state, published, status = self.run_one_batch(delta=53144328 + TARGET_RAW - FRAME["date_raw"])
        self.assertEqual(state["status"], "running")
        self.assertEqual(published, [7])
        self.assertEqual(state["start_date_raw"], FRAME["date_raw"])
        self.assertEqual(status["status"], "operator_stopped")

    def test_exact_new_stability_target_stops_without_publishing_more(self):
        state, published, status = self.run_one_batch(delta=TARGET_RAW)
        self.assertEqual(state["status"], "complete")
        self.assertEqual(published, [])
        self.assertEqual(status["status"], "thirty_year_stability_window_completed")

    def test_terminal_intervention_on_target_day_cannot_claim_stability(self):
        state, published, status = self.run_one_batch(delta=TARGET_RAW, continuation=False)
        self.assertEqual(state["status"], "repair_required")
        self.assertEqual(published, [])
        self.assertEqual(status["status"], "campaign_terminal_review_required")


if __name__ == "__main__":
    unittest.main(verbosity=2)
