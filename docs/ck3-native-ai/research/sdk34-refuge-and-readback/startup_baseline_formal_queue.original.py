"""Actual queue AST loader/methods with real six-key startup frame contract."""
import ast
import asyncio
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import types
import uuid

PACK = Path(__file__).resolve().parent
N = PACK.parent
R3 = N / "native21-cold-generation03"
sys.path[:0] = [str(R3), str(N / "sdk-p33-candidate/src")]
from root_p33_checkpoint_cadence import checkpoint_after_settled_cycle, checkpoint_context_from_auto
from root_p33_halt_pending_watch import pending_marker_from_credit

queue_path = R3 / "root_p33_sdk_queue.py"
qt = ast.parse(queue_path.read_text(encoding="utf-8"))
env = dict(globals())
for node in qt.body:
    if isinstance(node, ast.Assign) and all(isinstance(t, ast.Name) for t in node.targets):
        try:
            value = ast.literal_eval(node.value)
        except (ValueError, TypeError):
            continue
        for target in node.targets:
            env[target.id] = value
env["REPLY_RESERVE"] = 512 * 1024**2 + 65536
nodes = [node for node in qt.body if isinstance(node, ast.FunctionDef) and
         (node.name in {"now", "read", "atomic", "frame", "load_cold_result_classifier"}
          or node.name.startswith("classify_"))]
original = next(node for node in qt.body if isinstance(node, ast.ClassDef) and node.name == "FreshQueue")
methods = [node for node in original.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
           and node.name in {"check_after", "persist_loop_state", "full_loop", "consume_sequence"}]
nodes.append(ast.ClassDef(name="FormalQueue", bases=[], keywords=[], body=methods, decorator_list=[]))
exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), str(queue_path), "exec"), env)
evidence = N / "p32-war-results-first-failure-candidate01/CONNECTED-READONLY-FAILURE.json"
body = json.loads(evidence.read_bytes())["outcome"]
source = body["planning_source_frame"]
metrics = dict(source, paused=True, map_ready=True, actor_alive=True)
current = env["frame"](metrics)
startup = env["frame"](dict(metrics, snapshot_id="native:39", revision=1, native_revision=39,
                           date_raw=metrics["date_raw"] - 24))
assert set(startup) == {"snapshot_id", "revision", "native_revision", "date_raw", "actor_character_id", "episode_run_id"}
assert startup["date_raw"] < current["date_raw"] and startup["revision"] != current["revision"]

with tempfile.TemporaryDirectory(dir=PACK, prefix="baseline-formal-") as tmp:
    root = Path(tmp)
    qdir, outbox, inbox = (root / name for name in ("q", "responses", "requests"))
    for path in (qdir, outbox, inbox):
        path.mkdir()
    env.update(N=root, Q=qdir, OUTBOX=outbox, INBOX=inbox)
    env["atomic"](root / "ROOT-ACTUAL-DRIVER-MODE-P33.json", {"episode_projection": "one_life", "before_submit_observation": True})
    candidate = root / "canonical.py"
    pin_path = root / "ROOT-P33-CLASSIFIER-PIN.json"
    def loaded(path):
        candidate.write_bytes(path.read_bytes())
        env["atomic"](pin_path, {"source": str(candidate), "sha256": hashlib.sha256(candidate.read_bytes()).hexdigest()}, replace=True, limit=16384)
        return env["load_cold_result_classifier"]()
    old = loaded(PACK / "ROOT-CLASSIFIER-BEFORE-INITIAL-BASELINE-CORRECTION.py")
    try:
        old(body, initial_frame=startup, game_pid=source["bridge_pid"])
    except ValueError as error:
        assert str(error) == "war results readonly failure source Game/frame differs"
    else:
        raise AssertionError("original shape mismatch not reproduced")
    classifier = loaded(PACK / "root_p34_canonical_result_classifier.py")
    state, focus = {"retained": True}, {"focus": True}
    credit, returned, returned_focus = classifier(json.loads(json.dumps(body)), state=state,
        pending_focus=focus, initial_frame=startup, game_pid=source["bridge_pid"])
    assert returned is state and returned_focus is focus
    assert credit["typed_nonmaterial_observation"] is True
    for key in ("primitive_accepted", "submitted_pending", "ui_action_credit", "date_advance_observed",
                "business_success_inferred", "war_results_window_closed_verified", "replay_allowed"):
        assert credit[key] is False
    rejected = []
    mutations = {
        "wire_public_not_native": lambda b: b["result"]["native_error_evidence"]["native_request"].update(expected_revision=2),
        "raw_request_id": lambda b: b["result"]["native_error_evidence"]["native_command_result"].update(request_id="other"),
        "current_source_public_native_swap": lambda b: b["result"]["source_frame"].update(revision=40),
        "current_query_lease": lambda b: b["result"]["failed_attempt"].update(queried_revision=3),
        "wrong_Game": lambda b: b["result"]["source_frame"].update(bridge_pid=1),
        "false_acceptance": lambda b: b["result"].update(accepted=True),
        "false_window_close": lambda b: b["result"].update(close_dispatched=True),
    }
    for name, mutate in mutations.items():
        bad = copy.deepcopy(body)
        mutate(bad)
        try:
            classifier(bad, initial_frame=startup, game_pid=source["bridge_pid"])
        except ValueError:
            rejected.append(name)
        else:
            raise AssertionError(name)
    for key, value in (("actor_character_id", startup["actor_character_id"] + 1),
                       ("episode_run_id", "other-episode"), ("date_raw", current["date_raw"] + 24)):
        bad_initial = dict(startup, **{key: value})
        try:
            classifier(body, initial_frame=bad_initial, game_pid=source["bridge_pid"])
        except ValueError:
            rejected.append("initial_" + key)
        else:
            raise AssertionError("initial_" + key)
    queue = env["FormalQueue"]()
    queue.launch = {"pid": source["bridge_pid"]}
    queue.initial_frame = startup
    queue.result_classifier = classifier
    queue.result_classifier_pin = {"source": str(candidate), "sha256": hashlib.sha256(candidate.read_bytes()).hexdigest()}
    queue.governance_result_state, queue.lifestyle_pending_focus = state, focus
    counters = ("submitted_pending_turns", "lifestyle_material_verified_turns", "existing_focus_verified_turns",
        "primitive_accepted_turns", "council_material_verified_turns", "construction_material_verified_turns",
        "construction_start_verified_turns", "construction_completion_verified_turns", "crown_material_verified_turns",
        "crown_receipt_nonmaterial_turns", "existing_typed_material_verified_turns", "typed_nonmaterial_observation_turns",
        "date_advanced_turns", "checkpoint_saved", "checkpoint_deferred")
    queue.full_loop_state = {"schema": "g2.queue.cumulative-loop/v1", "completed_cycles": 1,
        "start_date_raw": startup["date_raw"], "before": current, "before_metrics_response": "current-before.json",
        "pending_cycle": None, "pending_checkpoint": None, "terminal": None, "counts": {key: 0 for key in counters}}
    queue.halted = None
    queue.initial_save = {"status": "saved"}
    queue.checkpoint_bootstrap_verified = True
    queue.loop_count, queue.next_sequence = 0, 1
    queue.guard = lambda: None
    queue.require_camera_pixel_admission = lambda: None
    calls = []
    async def generated(self, session, tool, arguments=None):
        assert tool in (env["AUTO"], env["METRICS"])
        calls.append(tool)
        value = copy.deepcopy(body if tool == env["AUTO"] else metrics)
        path = outbox / f"{self.next_sequence:04d}-1-result.json"
        self.next_sequence += 1
        env["atomic"](path, {"result": {"is_error": False, "structured_content": value}})
        self.check_after(tool, arguments or {}, value)
        return value, path
    queue.generated = types.MethodType(generated, queue)
    outcome = asyncio.run(queue.full_loop(None, {"sequence": 1, "command": "full_loop", "arguments": {"max_turns": 1}}, inbox / "0001-1-result.json"))
    assert calls == [env["AUTO"], env["METRICS"]]
    assert outcome["cumulative_cycles"] == 2
    settled = env["read"](qdir / "ROOT-CUMULATIVE-LOOP-STATE.json", 65536)
    event = env["read"](qdir / "CUMULATIVE-TURN-000002.json", 16384)
    assert settled["pending_cycle"] is None
    assert settled["counts"]["typed_nonmaterial_observation_turns"] == 1
    assert all(value == 0 for key, value in settled["counts"].items() if key != "typed_nonmaterial_observation_turns")
    assert event["date_delta_raw"] == 0
    assert classifier(json.loads((outbox / "0002-1-result.json").read_bytes())["result"]["structured_content"],
                      initial_frame=startup, game_pid=source["bridge_pid"])[0] == credit
    sizes = {"canonical": candidate.stat().st_size, "TURN": (qdir / "CUMULATIVE-TURN-000002.json").stat().st_size,
             "state": (qdir / "ROOT-CUMULATIVE-LOOP-STATE.json").stat().st_size}

natural = R3 / "root_p33_automatic_natural_succession_handoff.py"
natural_source = natural.read_text(encoding="utf-8")
assert "queue.semantic, queue.initial_frame, queue.initial_save = final_body, compact, copy.deepcopy(saved)" in natural_source
receipt = {"status": "CLASSIFIER_REAL_QUEUE_STARTUP_BASELINE_CORRECTION_GREEN_NOT_LIVE",
    "at_utc": datetime.now(timezone.utc).isoformat(), "canonical": str(PACK / "root_p34_canonical_result_classifier.py"),
    "sha256": hashlib.sha256((PACK / "root_p34_canonical_result_classifier.py").read_bytes()).hexdigest(),
    "original_036ea2_failure_reproduced": True, "startup_frame_producer": "actual queue.frame(metrics) six fields",
    "startup_public_native_date": [1, 39, startup["date_raw"]], "current_public_native_date": [2, 40, current["date_raw"]],
    "actual_AST_loader_check_after_full_loop_persist_atomic_roundtrip": True,
    "negative_checks": rejected, "identity_state_focus_preserved": True,
    "zero_date_business_close_credit": True, "settled_nonmaterial_observation_once": True, "sizes": sizes,
    "natural_handoff_updates_initial_frame": {"path": str(natural), "sha256": hashlib.sha256(natural.read_bytes()).hexdigest(), "assignment_line": 574},
    "original_review_correction": "old formal fixture supplied eight current fields; old evidence retained and corrected here",
    "limits": ["Native state_changed is synthetic; actual Service DTO retained", "process/UI admission and actual Game branch not exercised"],
    "temporary_fixture_reclaimed": True, "SDK33_or_live_writes": 0, "ledger_writes": 0}
output = PACK / "CLASSIFIER-BASELINE-FORMAL-QUEUE-REVIEW.json"
with output.open("x", encoding="utf-8") as stream:
    json.dump(receipt, stream, indent=2)
    stream.write("\n")
print(json.dumps({"status": receipt["status"], "review": str(output), "sha256": hashlib.sha256(output.read_bytes()).hexdigest(), "sizes": sizes}))
