"""Actual AUTO50 unchanged, production AST loader/check_after/full_loop/persist."""
import ast
import asyncio
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import types

PACK = Path(__file__).resolve().parent
N = PACK.parent
R = N / "native21-cold-generation03"
setup_path = N / "p34-hot-sdk-prep01/test_classifier_startup_baseline.py"
setup_text = setup_path.read_text().replace("p33", "p34").replace("P33", "P34")
prefix = []
for node in ast.parse(setup_text).body:
    if isinstance(node, ast.With):
        break
    prefix.append(node)
setup = {"__file__": str(setup_path), "__name__": "offline_formal_p34_queue"}
exec(compile(ast.Module(body=prefix, type_ignores=[]), str(setup_path), "exec"), setup)
env = setup["env"]
from xar_autoplayer.bridge.succession_transition_contract import normalize_succession_lifecycle_binding_v1

def body_at(sequence):
    p = R / f"p34-responses/{sequence:04d}-1-result.json"
    row = json.loads(p.read_bytes())
    assert row["result"]["is_error"] is False
    return row["result"]["structured_content"]

body, metrics_before, sem_start, sem_end = (body_at(i) for i in (50, 49, 1, 51))
assert body["result"]["active_event"] == sem_end["active_event"]
current = env["frame"](metrics_before)
startup = env["frame"](sem_start, semantic=True,
    expected_lifecycle=normalize_succession_lifecycle_binding_v1(sem_start["succession_lifecycle"]))
assert len(startup) == 6 and startup["date_raw"] < current["date_raw"]
source = body["planning_source_frame"]
assert all(current[key] == source[key] for key in current)
# This is an explicitly synthetic METRICS projection of actual SEM51. Root
# obtains the real paired METRICS after reconsume; no fixture is published.
metrics_after = {key: sem_end[key] for key in ("snapshot_id", "revision", "native_revision",
    "date_raw", "paused", "map_ready", "episode_run_id")}
metrics_after.update(actor_character_id=sem_end["played_character"]["character_id"],
    actor_alive=sem_end["played_character"]["alive"],
    connection_generation=sem_end["diagnostics"]["connection_generation"])
candidate = PACK / "root_p34_route_exactday_popup_result_classifier.py"
negative_checks = []
with tempfile.TemporaryDirectory(dir=PACK, prefix="formal-popup-") as temporary:
    root = Path(temporary)
    qdir, outbox, inbox = [root / name for name in ("q", "responses", "requests")]
    for path in (qdir, outbox, inbox):
        path.mkdir()
    env.update(N=root, Q=qdir, OUTBOX=outbox, INBOX=inbox)
    env["atomic"](root / "ROOT-ACTUAL-DRIVER-MODE-P34.json", {
        "episode_projection": "one_life", "before_submit_observation": True})
    canonical = root / "canonical.py"
    def loaded(path):
        canonical.write_bytes(path.read_bytes())
        env["atomic"](root / "ROOT-P34-CLASSIFIER-PIN.json", {
            "source": str(canonical), "sha256": hashlib.sha256(canonical.read_bytes()).hexdigest()
        }, replace=True, limit=16384)
        return env["load_cold_result_classifier"]()
    old = loaded(R / "root_p34_canonical_result_classifier.py")
    try:
        old(body, initial_frame=startup, game_pid=6068)
    except ValueError as error:
        assert str(error) == "route-contact exact day rejected: exact one-day composite"
    else:
        raise AssertionError("original rejection not reproduced")
    classifier = loaded(candidate)
    credit = classifier(copy.deepcopy(body), initial_frame=startup, game_pid=6068)[0]
    assert credit["actual_date_delta_raw"] == 24 and credit["actual_elapsed_days"] == 1
    assert credit["date_advance_observed"] is True
    for key in ("primitive_accepted", "material_verified", "ui_action_credit", "action_credit",
                "business_success_inferred", "replay_allowed"):
        assert credit[key] is False
    map_body = copy.deepcopy(body)
    map_body["result"].update(active_event=None, pending_character_interaction=None,
                              final_screen="map_hud", event_resolution="none")
    assert classifier(map_body, initial_frame=startup, game_pid=6068)[0] == old(
        map_body, initial_frame=startup, game_pid=6068)[0] == credit
    interaction_body = copy.deepcopy(map_body)
    interaction_body["result"].update(pending_character_interaction={"source": "synthetic_native_popup"},
                                       final_screen=None)
    assert classifier(interaction_body, initial_frame=startup, game_pid=6068)[0] == credit
    mutations = {
        "unpaused": lambda b: b["result"].update(paused=False),
        "event_bool_id": lambda b: b["result"]["active_event"].update(instance_id=True),
        "event_zero_options": lambda b: b["result"]["active_event"].update(option_count=0),
        "popup_with_map_screen": lambda b: b["result"].update(final_screen="map_hud"),
        "event_already_selected": lambda b: b["result"].update(event_resolution="selected"),
        "hidden_event_resolution_none": lambda b: b["result"].update(event_resolution="none"),
        "empty_interaction": lambda b: b["result"].update(pending_character_interaction={}),
        "UI_action_appended": lambda b: b["result"]["actions"].append({"step": "select-event-option-1", "result": {"accepted": True}}),
        "ordinary_event_consumed": lambda b: b["result"].update(ordinary_events=[{"selected": True}]),
        "elapsed_two_days": lambda b: b["result"].update(elapsed_days=2),
        "clock_overshoot": lambda b: b["result"]["exact_day_native_clock"]["stopped"].update(overshoot_days=1),
        "clock_extra_tick": lambda b: b["result"]["exact_day_native_clock"]["stopped"].update(completed_daily_ticks=2),
        "cached_speed_wrong_frame": lambda b: b["result"]["actions"][0]["result"].update(source_native_revision=1),
        "incomplete_hostile_scope": lambda b: b["plan"]["route_audit"]["contact_horizon"].update(hostile_army_ids=[]),
        "source_native_public_swap": lambda b: b["planning_source_frame"].update(native_revision=16),
        "wrong_Game": lambda b: b["planning_source_frame"].update(bridge_pid=1),
    }
    for name, mutate in mutations.items():
        bad = copy.deepcopy(body)
        mutate(bad)
        try:
            classifier(bad, initial_frame=startup, game_pid=6068)
        except ValueError:
            negative_checks.append(name)
        else:
            raise AssertionError(name)
    queue = env["FormalQueue"]()
    queue.launch, queue.initial_frame = {"pid": 6068}, startup
    queue.result_classifier = classifier
    queue.result_classifier_pin = {"source": str(canonical), "sha256": hashlib.sha256(canonical.read_bytes()).hexdigest()}
    queue.governance_result_state, queue.lifestyle_pending_focus = {}, None
    counters = ("submitted_pending_turns", "lifestyle_material_verified_turns", "existing_focus_verified_turns",
        "primitive_accepted_turns", "council_material_verified_turns", "construction_material_verified_turns",
        "construction_start_verified_turns", "construction_completion_verified_turns", "crown_material_verified_turns",
        "crown_receipt_nonmaterial_turns", "existing_typed_material_verified_turns", "typed_nonmaterial_observation_turns",
        "date_advanced_turns", "checkpoint_saved", "checkpoint_deferred")
    queue.full_loop_state = {"schema": "g2.queue.cumulative-loop/v1", "completed_cycles": 1,
        "start_date_raw": startup["date_raw"], "before": current, "before_metrics_response": "actual49.json",
        "pending_cycle": None, "pending_checkpoint": None, "terminal": None,
        "counts": {key: 0 for key in counters}}
    queue.halted, queue.initial_save = None, {"status": "saved"}
    queue.checkpoint_bootstrap_verified = True
    queue.loop_count, queue.next_sequence = 0, 1
    queue.guard = lambda: None
    queue.require_camera_pixel_admission = lambda: None
    calls = []
    async def generated(self, session, tool, arguments=None):
        assert tool in (env["AUTO"], env["METRICS"])
        calls.append(tool)
        value = copy.deepcopy(body if tool == env["AUTO"] else metrics_after)
        path = outbox / f"{self.next_sequence:04d}-1-result.json"
        self.next_sequence += 1
        env["atomic"](path, {"result": {"is_error": False, "structured_content": value}})
        self.check_after(tool, arguments or {}, value)
        return value, path
    queue.generated = types.MethodType(generated, queue)
    outcome = asyncio.run(queue.full_loop(None, {"sequence": 1, "command": "full_loop",
        "arguments": {"max_turns": 1}}, inbox / "0001-1-result.json"))
    assert calls == [env["AUTO"], env["METRICS"]] and outcome["cumulative_cycles"] == 2
    settled = env["read"](qdir / "ROOT-CUMULATIVE-LOOP-STATE.json", 65536)
    event = env["read"](qdir / "CUMULATIVE-TURN-000002.json", 16384)
    assert settled["pending_cycle"] is None and event["date_delta_raw"] == 24
    assert settled["counts"]["date_advanced_turns"] == 1
    assert all(value == 0 for key, value in settled["counts"].items() if key != "date_advanced_turns")
    assert classifier(json.loads((outbox / "0002-1-result.json").read_bytes())["result"]["structured_content"],
                      initial_frame=startup, game_pid=6068)[0] == credit
    sizes = {"canonical": canonical.stat().st_size,
        "TURN": (qdir / "CUMULATIVE-TURN-000002.json").stat().st_size,
        "state": (qdir / "ROOT-CUMULATIVE-LOOP-STATE.json").stat().st_size}

receipt = {"status": "ACTUAL50_POPUP_EXACT_DAY_FORMAL_QUEUE_REPLAY_GREEN_NOT_LIVE",
    "at_utc": datetime.now(timezone.utc).isoformat(), "canonical_sha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
    "original_rejection_reproduced": True, "actual_AUTO50_unchanged": True,
    "actual_SEM1_six_field_startup_baseline": startup, "actual_METRICS49_before_frame": current,
    "after_metrics_fixture": "explicit synthetic projection of actual SEM51; real paired METRICS still required",
    "full_AST_loader_check_after_full_loop_persist_atomic_JSON_roundtrip": True,
    "date_credit_once_raw": 24, "UI_business_credit": 0,
    "legacy_no_popup_credit_unchanged": True, "synthetic_pending_interaction_readback": True,
    "negative_checks": negative_checks, "sizes": sizes,
    "temporary_fixture_reclaimed": True, "MCP_or_process_calls": 0,
    "loaded_source_Driver_ledger_writes": 0}
with (PACK / "FORMAL-QUEUE-TESTS.json").open("x", encoding="utf-8", newline="\n") as stream:
    json.dump(receipt, stream, indent=2)
    stream.write("\n")
print(json.dumps(receipt))
