"""Unchanged AUTO22 through actual P35 loader/reconsume/full_loop/persistence."""
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
R = N / "native22-cold-generation04"
setup_path = N / "p34-hot-sdk-prep01/test_classifier_startup_baseline.py"
setup_text = setup_path.read_text().replace("p33", "p35").replace("P33", "P35").replace("native21-cold-generation03", "native22-cold-generation04")
setup_text = setup_text.replace('"full_loop", "consume_sequence"}', '"full_loop", "consume_sequence", "reconsume_original_response"}')
setup_text = setup_text.replace('{"now", "read", "atomic", "frame",', '{"now", "read", "atomic", "frame", "decoded",')
nodes = []
for node in ast.parse(setup_text).body:
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "evidence" for t in node.targets):
        break
    nodes.append(node)
ns = {"__file__": str(setup_path), "__name__": "offline_actual22_p35_queue"}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(setup_path), "exec"), ns)
env = ns["env"]
from xar_autoplayer.bridge.succession_transition_contract import normalize_succession_lifecycle_binding_v1


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def row_at(seq):
    path = R / f"p35-responses/{seq:04d}-1-result.json"
    row = json.loads(path.read_bytes())
    assert row["result"]["is_error"] is False
    return row, row["result"]["structured_content"], path


original, body, original_path = row_at(22)
original_sha = sha(original_path)
_, sem_start, _ = row_at(1)
_, metrics_before, _ = row_at(20)
_, sem_end, _ = row_at(23)
_, metrics_after, metrics_after_path = row_at(24)
startup = env["frame"](sem_start, semantic=True,
    expected_lifecycle=normalize_succession_lifecycle_binding_v1(sem_start["succession_lifecycle"]))
current, after = env["frame"](metrics_before), env["frame"](metrics_after)
assert len(startup) == 6 and current["date_raw"] + 24 == after["date_raw"]
assert all(current[k] == body["planning_source_frame"][k] for k in current)
state = json.loads((R / "p35-queue/ROOT-CUMULATIVE-LOOP-STATE.json").read_bytes())
assert state["pending_cycle"]["auto_sequence"] == 22 and state["pending_cycle"]["stage"] == "auto_unsettled"
candidate = PACK / "root_p35_stationary_result_classifier.py"
negative = []
with tempfile.TemporaryDirectory(dir=PACK, prefix="actual22-") as temp:
    root = Path(temp)
    qdir, outbox, inbox = [root / x for x in ("q", "responses", "requests")]
    for p in (qdir, outbox, inbox):
        p.mkdir()
    env.update(N=root, Q=qdir, OUTBOX=outbox, INBOX=inbox)
    env["atomic"](root / "ROOT-ACTUAL-DRIVER-MODE-P35.json", {"episode_projection": "one_life", "before_submit_observation": True})
    canonical = root / "canonical.py"
    def loaded(source):
        canonical.write_bytes(source.read_bytes())
        env["atomic"](root / "ROOT-P35-CLASSIFIER-PIN.json", {"source": str(canonical), "sha256": sha(canonical)}, replace=True, limit=16384)
        return env["load_cold_result_classifier"]()
    old = loaded(R / "root_p35_modal_result_classifier.py")
    try:
        old(body, initial_frame=startup, game_pid=263980)
    except ValueError as error:
        assert str(error) == "route-contact exact day rejected: exact one-day composite"
    else:
        raise AssertionError("original failure not reproduced")
    (root / "root_route_contact_exact_day_classifier_v2.py").write_bytes((PACK / "root_route_contact_exact_day_classifier_v2.py").read_bytes())
    (root / "root_battle_route_modal_classifier_v1.py").write_bytes((R / "root_battle_route_modal_classifier_v1.py").read_bytes())
    classifier = loaded(candidate)
    credit = classifier(copy.deepcopy(body), initial_frame=startup, game_pid=263980)[0]
    assert credit["actual_date_delta_raw"] == 24 and credit["actual_elapsed_days"] == 1 and credit["date_advance_observed"] is True
    assert all(credit[k] is False for k in ("primitive_accepted", "ui_action_credit", "action_credit", "material_verified", "business_success_inferred", "replay_allowed"))
    def horizon(b):return b["plan"]["route_audit"]["contact_horizon"]
    def subject(b):return b["result"]["war_progress_before"]["wars"][0]["player_armies"][0]
    mutations = {
        "wrong_phase": lambda b:b["plan"].update(phase="native_war_stationary_contact_horizon_progress_unsupported"),
        "wrong_audit_status": lambda b:b["plan"]["route_audit"].update(status="safe_route"),
        "unknown_timeline": lambda b:horizon(b)["subject_route"].update(timeline_observable=False),
        "nonempty_stationary_route": lambda b:horizon(b)["subject_route"].update(route_province_ids=[2604],arrival_date_raws=[53483040]),
        "wrong_origin": lambda b:horizon(b)["subject_route"].update(effective_origin_province_id=2605),
        "wrong_current": lambda b:horizon(b)["subject_route"].update(current_province_id=2605),
        "moving_subject": lambda b:subject(b).update(army_state="moving",army_state_code=7),
        "subject_in_combat": lambda b:subject(b).update(in_combat=True),
        "subject_retreating": lambda b:subject(b).update(retreating=True),
        "subject_pending_target": lambda b:subject(b).update(move_target_province_id=2605),
        "subject_route_nonempty": lambda b:subject(b).update(route_province_ids=[2605]),
        "subject_wrong_province": lambda b:subject(b).update(current_province_id=2605),
        "missing_hostile": lambda b:horizon(b).update(hostile_army_ids=[]),
        "missing_hostile_timeline": lambda b:horizon(b).update(hostile_routes=[]),
        "unobservable_hostile": lambda b:horizon(b)["hostile_routes"][0].update(timeline_observable=False),
        "unwatched_enemy": lambda b:b["result"]["war_progress_before"]["wars"][0]["enemy_armies"].append({"army_id":123,"retreating":False}),
        "false_contact_free": lambda b:horizon(b).update(one_day_contact_free=False),
        "wrong_native_revision": lambda b:horizon(b).update(snapshot_revision=2),
        "wrong_Game": lambda b:b["planning_source_frame"].update(bridge_pid=1),
        "wrong_episode": lambda b:b["planning_source_frame"].update(episode_run_id="other"),
        "unpaused": lambda b:b["result"].update(paused=False),
        "two_days": lambda b:b["result"].update(elapsed_days=2),
        "clock_overshoot": lambda b:b["result"]["exact_day_native_clock"]["stopped"].update(overshoot_days=1),
        "cached_speed_other_source": lambda b:b["result"]["actions"][0]["result"].update(source_snapshot_id="native:9"),
        "UI_submit_extra": lambda b:b["result"]["actions"].append({"step":"select-event-option-1","result":{"accepted":True}}),
    }
    for name, mutate in mutations.items():
        bad = copy.deepcopy(body)
        mutate(bad)
        try:classifier(bad, initial_frame=startup, game_pid=263980)
        except ValueError:negative.append(name)
        else:raise AssertionError(name)
    # Existing popup contract applies equally after a stationary exact clock.
    modal = copy.deepcopy(body)
    modal["result"].update(active_event={"instance_id":111,"option_count":3}, final_screen=None,event_resolution="typed_query_required")
    assert classifier(modal,initial_frame=startup,game_pid=263980)[0] == credit
    queue = env["FormalQueue"]()
    queue.launch, queue.initial_frame = {"pid":263980}, startup
    queue.result_classifier, queue.result_classifier_pin = classifier, {"source":str(canonical),"sha256":sha(canonical)}
    queue.governance_result_state, queue.lifestyle_pending_focus = {}, None
    queue.full_loop_state = copy.deepcopy(state)
    queue.halted = {"request":original["request"],"row":original,"response":str(original_path)}
    queue.initial_save, queue.checkpoint_bootstrap_verified = {"status":"restored"}, True
    queue.loop_count, queue.next_sequence = 0, 25
    queue.guard = lambda:None
    queue.require_camera_pixel_admission = lambda:None
    queue.semantic = sem_end
    counts_before = copy.deepcopy(state["counts"])
    asyncio.run(queue.reconsume_original_response(None,{"sequence":25,"command":"reconsume_original_response","arguments":{}},inbox/"0025-1-result.json"))
    assert queue.halted is None and queue.full_loop_state["pending_cycle"]["stage"] == "auto_verified"
    calls = []
    async def generated(self,session,tool,arguments=None):
        assert tool == env["METRICS"], "original AUTO must never be replayed"
        calls.append(tool)
        path = outbox/f"{self.next_sequence:04d}-1-result.json"
        self.next_sequence += 1
        env["atomic"](path,{"result":{"is_error":False,"structured_content":metrics_after}})
        self.check_after(tool,arguments or {},metrics_after)
        return metrics_after,path
    queue.generated = types.MethodType(generated,queue)
    result = asyncio.run(queue.full_loop(None,{"sequence":26,"command":"full_loop","arguments":{"max_turns":1}},inbox/"0026-1-result.json"))
    settled = env["read"](qdir/"ROOT-CUMULATIVE-LOOP-STATE.json",65536)
    turn = env["read"](qdir/f"CUMULATIVE-TURN-{state['completed_cycles']+1:06d}.json",16384)
    assert calls == [env["METRICS"]] and sha(original_path) == original_sha
    assert settled["completed_cycles"] == state["completed_cycles"]+1 and settled["pending_cycle"] is None
    assert settled["before"] == after and turn["date_delta_raw"] == 24
    assert settled["counts"]["date_advanced_turns"] == counts_before["date_advanced_turns"]+1
    for key in ("primitive_accepted_turns","submitted_pending_turns","existing_typed_material_verified_turns","typed_nonmaterial_observation_turns"):
        assert settled["counts"][key] == counts_before[key]
    assert classifier(json.loads(original_path.read_bytes())["result"]["structured_content"],initial_frame=startup,game_pid=263980)[0] == credit
    sizes = {"canonical":canonical.stat().st_size,"TURN":(qdir/f"CUMULATIVE-TURN-{state['completed_cycles']+1:06d}.json").stat().st_size}
receipt = {"status":"ACTUAL22_STATIONARY_FORMAL_QUEUE_RECONSUME_SETTLE_GREEN_NOT_RUNTIME",
    "at_utc":datetime.now(timezone.utc).isoformat(),"original_AUTO22_sha256":original_sha,
    "actual_SEM1_six_field_startup":startup,"actual_METRICS20_before":current,"actual_METRICS24_after":after,
    "old_failure_reproduced":True,"unchanged_original_AUTO22":True,"negative_cases":negative,
    "same_original_response_reconsume_then_only_METRICS":True,"date_credit_once_raw":24,"UI_business_or_replay_credit":0,
    "actual_P35_loader_check_after_reconsume_full_loop_persist_JSON":True,"stationary_popup_contract_retained":True,
    "sizes":sizes,"new_MCP_Game_Native_or_Driver_calls":0,"live_source_or_ledger_writes":0}
with (PACK/"ACTUAL22-QUEUE-TESTS.json").open("x",encoding="utf-8")as stream:json.dump(receipt,stream,indent=2)
print(json.dumps({"status":receipt["status"],"sha256":sha(PACK/"ACTUAL22-QUEUE-TESTS.json"),"negative_cases":len(negative),"sizes":sizes}))
