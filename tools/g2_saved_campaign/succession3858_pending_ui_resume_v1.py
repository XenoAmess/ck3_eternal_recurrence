"""Finite C7 UI-tail continuation; original successful prefix is never dispatched."""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path

MACHINE = "xenoamess-full-tower-eb9d2c1186"
KIND = "succession3858_pending_ui_AUTO_tail"
FROZEN = Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/p51-fresh1066-v20261019-prepare01/c7-succession3858-ui-failure78")
FROZEN_SHA = "987e1e0d2f6f37ab49c15840fa42dab9a09d6a671f45ea6f624b1bb264c1eb7b"
OLD = FROZEN.parent / "c7-succession3851-failure77"
SOURCE_SHA = "af114b3088ca847fdd14affe40f1c942f191fc0c2cac81e45d431eda64e070e1"
UI_SHA = "ff6bc8e4403e6e26c48d1c3d81226aac90d4fdd935a410a0135a3b2d9a2cf0e8"
PREFIX = (3851, 3853, 3854, 3855, 3856, 3857)


def require(ok, message):
    if not ok:
        raise ValueError("source-bound succession3858 resume denied: " + message)


def checked(path, digest):
    raw = Path(path).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == digest, "source pin differs: " + str(path))
    return raw


def original_namespace(source, ui_source):
    require(hashlib.sha256(source).hexdigest() == SOURCE_SHA, "original handoff differs")
    require(hashlib.sha256(ui_source).hexdigest() == UI_SHA, "reviewed UI AUTO contract differs")
    old = source.decode("utf-8-sig")
    edits = [
        ("from root_p37_overlay_relay import relay_compact, error_projection",
         "from root_p37c6_overlay_relay import relay_compact, error_projection", 2),
        ('audit_path = env["Q"] / f"AUTOMATIC-SUCCESSION-HANDOFF-{key:06d}.json"',
         'audit_path = env["Q"] / f"AUTOMATIC-SUCCESSION-HANDOFF-{key:06d}-RESUME3859.json"', 1),
        ("from p51_resident_successor_adoption_v1 import observe_app_ui_v1",
         "observe_app_ui_v1 = _source_bound_observe_app_ui_v1", 1),
    ]
    source_text = old
    for before, after, count in edits:
        require(source_text.count(before) == count, "original source seam differs")
        source_text = source_text.replace(before, after)
    restored = source_text
    for before, after, count in reversed(edits):
        restored = restored.replace(after, before)
    require(ast.dump(ast.parse(restored)) == ast.dump(ast.parse(old)), "original business tail AST changed")
    ns = {"__name__": "_isolated_succession3858_original"}
    exec(compile(source_text, "<exact-af114b-resume3859>", "exec"), ns)
    tree = ast.parse(ui_source.decode("utf-8-sig"))
    names = {"require", "_same_frame", "_app_proof", "observe_app_ui_v1"}
    nodes = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in names]
    require({node.name for node in nodes} == names, "UI contract functions missing")
    ui_ns = {"UI": "ck3_resume_successor_ui_v1"}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "<reviewed-UI-AUTO-ff6bc8>", "exec"), ui_ns)
    ns["_source_bound_observe_app_ui_v1"] = ui_ns["observe_app_ui_v1"]
    return ns


def validate(queue, request, path, env):
    require(request == {"sequence": 3859, "command": "recover_partial_life_advance",
        "arguments": {"recovery_kind": "ordinary_campaign_succession", "repair_kind": KIND}},
        "exact unused control3859 required")
    require(Path(path) == env["INBOX"] / "3859-1-result.json" and queue.next_sequence == 3859
            and getattr(queue, "held_control", None) in (None, Path(path).name), "outer-control boundary differs")
    manifest = json.loads(checked(FROZEN / "FROZEN.json", FROZEN_SHA))
    require(manifest["machine_id"] == MACHINE, "source machine differs")
    refs = {Path(p["path"]).relative_to(FROZEN).as_posix(): p for p in manifest["sources"] if "path" in p}
    def read_original(rel):
        pin = refs[rel]
        raw = checked(pin["path"], pin["sha256"])
        require(checked(pin["original_source"], pin["sha256"]) == raw, "retained source changed")
        return json.loads(raw), pin
    state, sp = read_original("p37-queue/ROOT-CUMULATIVE-LOOP-STATE.json")
    audit, ap = read_original("p37-queue/AUTOMATIC-SUCCESSION-HANDOFF-001839-RESUME3852.json")
    error, ep = read_original("p37-responses/3858-1-result.json")
    halt, hp = read_original("ROOT-CURRENT-HALT-P37.json")
    for rel in ("root_p37c7_mcp_entry.py", "root_p37c6_compact_decision_feed.py"):
        pin = refs[rel]
        checked(pin["path"], pin["sha256"])
        checked(pin["original_source"], pin["sha256"])
    require(queue.full_loop_state == state and state["completed_cycles"] == 1839
            and state["start_date_raw"] == 53144328 and state["before"]["date_raw"] == 53186856
            and all(state.get(k) is None for k in ("pending_cycle", "pending_checkpoint", "terminal", "pending_unsafe_route_halt"))
            and (state.get("pending_natural_succession") or {}).get("global_turn") == 1839,
            "uncommitted original handoff state differs")
    require(audit["status"] == "failed_retained" and [p["sequence"] for p in audit["calls"]] == [*PREFIX, 3858]
            and audit["logical_continue"] == {"source": str(env["OUTBOX"] / "3853-1-result.json"), "already_applied": False}
            and audit["same_game"] == {"pid": 153556, "creation_filetime": 134368602545256920},
            "exact applied Continue and failed UI prefix required")
    require(queue.launch["pid"] == 153556 and queue.job["game_creation_filetime"] == 134368602545256920,
            "physical Game differs")
    require(error["request"]["tool"] == "ck3_continue_death_succession_modal_v1"
            and error.get("client_error") is None and error["result"].get("is_error") is True
            and "pre-submit publication lacks the current held auto-turn request" in json.dumps(error["result"])
            and queue.halted == {"request": error["request"], "row": error, "response": ep["original_source"]}
            and halt["original_request"] == error["request"] and halt["original_response"] == ep["original_source"],
            "only the exact pre-submit direct-Close rejection is admitted")
    rows, pins = [], []
    for seq in PREFIX:
        if seq == 3851:
            pin = {"path": str(OLD / "p37-responses/3851-1-result.json"), "original_source": str(env["OUTBOX"] / "3851-1-result.json"),
                   "sha256": "34d51307b4d8de7707bed4e0ad6991a692eed9f5c044d943dd5b9ec6d6fefda3"}
            raw = checked(pin["path"], pin["sha256"])
            checked(pin["original_source"], pin["sha256"])
            row = json.loads(raw)
        else:
            row, pin = read_original(f"p37-responses/{seq}-1-result.json")
            read_original(f"p37-queue/{seq}-after-result.json")
        require(row.get("client_error") is None and row["result"].get("is_error") is False,
                "prefix contains unknown/failed result")
        rows.append(row); pins.append(pin)
    require(env["decoded"](rows[4]).get("status") == "close_required"
            and env["decoded"](rows[4]).get("pending") is True,
            "original App pending UI proof differs")
    checked(env["N"] / "root_p37c7_sdk_queue.py", "fd579859a384ba94a059a38701719918ef763a15d7df21f86c5b347dc6ff0a30")
    source = checked(OLD / "root_p37_automatic_natural_succession_handoff.py", SOURCE_SHA)
    ui_source = checked(env["N"] / "root_p37_succession3858_ui_contract.py", UI_SHA)
    require(not (env["Q"] / "SUCCESSION3858-RESUME-INTENT.json").exists()
            and not (env["Q"] / "AUTOMATIC-SUCCESSION-HANDOFF-001839-RESUME3859.json").exists(), "finite tail already attempted")
    require(not env["pending_request_paths"](env["INBOX"], env["OUTBOX"], 3859, held_control=Path(path).name),
            "another request pending")
    return queue.full_loop_state, audit, rows, pins, source, ui_source, {"state": sp, "failed_audit": ap, "failed3858": ep, "halt": hp}


async def recover(queue, session, request, path, env, *, birth_reader):
    # The actual partial-recovery method passes a deliberately small env. Use
    # only its source-pinned original function globals to supply the original
    # handoff's display/pending-request bindings; do not mutate that namespace.
    method = queue.recover_partial_life_advance.__func__
    expected_source = Path(env["OUTBOX"]).parent / "root_p37c7_sdk_queue.py"
    require(Path(method.__code__.co_filename).resolve() == expected_source.resolve(), "original partial-control source differs")
    scope = method.__globals__
    require(all(scope[name] == env[name] for name in ("Q", "INBOX", "OUTBOX", "SEMANTIC")), "partial-control globals differ")
    env = {**scope, **env}
    state, old_audit, rows, pins, source, ui_source, refs = validate(queue, request, path, env)
    require(birth_reader(153556) == 134368602545256920, "Game kernel birth differs")
    ns = original_namespace(source, ui_source)
    factory = ns["_resident_make_call"]
    consumed = 0
    fresh_started = False
    def make_call(q, sess, call_env, audit, audit_path, read_birth, pid, birth):
        original_call = factory(q, sess, call_env, audit, audit_path, read_birth, pid, birth)
        async def call(tool, arguments):
            nonlocal consumed, fresh_started
            if consumed < len(rows):
                row, pin = rows[consumed], pins[consumed]
                require(tool == row["request"]["tool"] and arguments == row["request"]["arguments"], "prefix call order/arguments differs")
                q.guard(); require(read_birth(pid) == birth, "Game birth changed")
                consumed += 1
                # Prior results/display acknowledgments remain original. Never
                # replay their RPC, callback, display or CURRENT-REQUEST write.
                response = Path(pin["original_source"])
                q.current_attempt = {"request": copy.deepcopy(row["request"]), "row": copy.deepcopy(row), "response": str(response)}
                audit["calls"].append({"sequence": row["request"]["sequence"], "tool": tool, "response": str(response),
                                       "status": "received_prior_prefix_once", "new_RPC_calls": 0, "source_pin": pin})
                env["atomic"](audit_path, audit, replace=True, limit=65536)
                return copy.deepcopy(env["decoded"](row)), response
            if not fresh_started:
                require(tool == "ck3_auto_turn" and arguments == {}, "first new call must be current App UI AUTO")
                fresh_started = True
            require(tool != "ck3_continue_death_succession_modal_v1", "direct Close cannot be replayed")
            return await original_call(tool, arguments)
        return call
    ns["_resident_make_call"] = make_call
    env["atomic"](env["Q"] / "SUCCESSION3858-RESUME-INTENT.json", {
        "machine_id": MACHINE, "at_utc": env["now"]().isoformat(), "request": request, "sources": refs,
        "prefix": pins, "original3853_Continue_replayed": False, "original3858_directClose_replayed": False}, limit=16384)
    queue.consume_sequence(request)
    queue.held_control = Path(path).name
    queue.halted = queue.halt_cause = None
    result = await ns["automatic_handoff"](queue, session, state, original_before=old_audit["original_before"],
         event={"auto_response": old_audit["original_cycle"]}, env=env, birth_reader=birth_reader)
    require(consumed == len(PREFIX) and fresh_started and result is queue.full_loop_state
            and result["completed_cycles"] == 1839 and result.get("pending_natural_succession") is None,
            "original SAVE/reconciliation tail did not commit")
    receipt = {"machine_id": MACHINE, "at_utc": env["now"]().isoformat(),
       "status": "source_bound_pending_UI_AUTO_and_original_tail_finished", "completed_cycles": 1839,
       "ordinary_cycle_credit_added": 0, "prefix_RPC_replayed": False, "original3858_directClose_replayed": False,
       "failed3858_preserved": refs["failed3858"], "final_frame": result["before"],
       "final_semantic_response": result["before_metrics_response"],
       "original_failed_audit": refs["failed_audit"], "sources": refs,
       "pending_natural_succession_cleared": result.get("pending_natural_succession") is None,
       "audit": str(env["Q"] / "AUTOMATIC-SUCCESSION-HANDOFF-001839-RESUME3859.json")}
    env["atomic"](env["Q"] / "SUCCESSION3858-RESUME-SETTLED.json", receipt, limit=16384)
    env["atomic"](env["N"] / "ROOT-CURRENT-HALT-P37.json", receipt, replace=True, limit=16384)
    env["atomic"](env["OUTBOX"] / Path(path).name, {"request": request,
        "result": {"is_error": False, "structured_content": receipt}}, limit=16384)
    queue.current_attempt = queue.held_control = None


def transform_unused_succession(source):
    require(hashlib.sha256(source).hexdigest() == "a100c22d2e8c3d30b22feca269a63592aa912e3ce829fa269cdf51155ffe6415", "unused succession module differs")
    return source + b'''
_before_UI3858_recover_succession = recover_succession
async def recover_succession(queue, session, request, path, env, **kwargs):
    if request.get("arguments", {}).get("repair_kind") == "succession3858_pending_ui_AUTO_tail":
        from root_p37_succession3858_resume import recover
        return await recover(queue, session, request, path, env, **kwargs)
    return await _before_UI3858_recover_succession(queue, session, request, path, env, **kwargs)
'''
