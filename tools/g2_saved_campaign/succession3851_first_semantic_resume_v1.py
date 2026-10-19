"""One source-bound continuation of the received C7 handoff SEM3851.

The original handoff algorithm runs in an isolated namespace. Only its display
imports and new audit basename change; the business tail is retained verbatim.
Runtime's existing, previously unused known-owner control delegates here.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path

MACHINE = "xenoamess-full-tower-eb9d2c1186"
KIND = "natural_succession3851_first_semantic_resume"
FROZEN = Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/p51-fresh1066-v20261019-prepare01/c7-succession3851-failure77")
FROZEN_SHA = "098d9a0c539b23eecc63e09d028b6c9d41194dd20d045a0db08280f410c0c2d9"
SOURCE_SHA = "af114b3088ca847fdd14affe40f1c942f191fc0c2cac81e45d431eda64e070e1"
ROW_SHA = "34d51307b4d8de7707bed4e0ad6991a692eed9f5c044d943dd5b9ec6d6fefda3"
QUEUE_SHA = "fd579859a384ba94a059a38701719918ef763a15d7df21f86c5b347dc6ff0a30"


def require(value, message):
    if not value:
        raise ValueError("source-bound succession3851 resume denied: " + message)


def checked(path, digest):
    raw = Path(path).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == digest, "source pin differs: " + str(path))
    return raw


def prepare_original_namespace(source):
    """Exactly two provider imports and one independent audit filename change."""
    require(hashlib.sha256(source).hexdigest() == SOURCE_SHA, "handoff source differs")
    old = source.decode("utf-8-sig")
    provider = "from root_p37_overlay_relay import relay_compact, error_projection"
    require(old.count(provider) == 2, "two original display imports required")
    audit = 'audit_path = env["Q"] / f"AUTOMATIC-SUCCESSION-HANDOFF-{key:06d}.json"'
    require(old.count(audit) == 1, "single original audit path required")
    new = old.replace(provider, "from root_p37c6_overlay_relay import relay_compact, error_projection")
    new = new.replace(audit, 'audit_path = env["Q"] / f"AUTOMATIC-SUCCESSION-HANDOFF-{key:06d}-RESUME3852.json"')
    # Reverse the three literal substitutions before comparing the full AST.
    restored = new.replace("from root_p37c6_overlay_relay import relay_compact, error_projection", provider)
    restored = restored.replace('audit_path = env["Q"] / f"AUTOMATIC-SUCCESSION-HANDOFF-{key:06d}-RESUME3852.json"', audit)
    require(ast.dump(ast.parse(restored)) == ast.dump(ast.parse(old)), "business AST changed")
    namespace = {"__name__": "_source_bound_succession3851_original"}
    exec(compile(new, "<source-bound-af114b-succession3851>", "exec"), namespace)
    return namespace


def validate(queue, request, path, env, *, frozen=FROZEN):
    require(request == {"sequence": 3852, "command": "recover_known_owner_1024",
                        "arguments": {"repair_kind": KIND}}, "exact unused local3852 control required")
    require(Path(path) == env["INBOX"] / "3852-1-result.json"
            and queue.next_sequence == 3852
            and getattr(queue, "held_control", None) in (None, Path(path).name),
            "current outer-control boundary differs")
    package = json.loads(checked(frozen / "FROZEN.json", FROZEN_SHA))
    require(package.get("machine_id") == MACHINE, "source machine differs")
    sources = {Path(row["path"]).relative_to(frozen).as_posix(): row
               for row in package["sources"] if "path" in row}
    def original(relative):
        pin = sources[relative]
        data = checked(pin["path"], pin["sha256"])
        require(checked(pin["original_source"], pin["sha256"]) == data,
                "live retained source changed")
        return json.loads(data), pin
    state, state_pin = original("p37-queue/ROOT-CUMULATIVE-LOOP-STATE.json")
    audit, audit_pin = original("p37-queue/AUTOMATIC-SUCCESSION-HANDOFF-001839.json")
    row, row_pin = original("p37-responses/3851-1-result.json")
    halt, halt_pin = original("ROOT-CURRENT-HALT-P37.json")
    source = checked(frozen / "root_p37_automatic_natural_succession_handoff.py", SOURCE_SHA)
    checked(env["N"] / "root_p37_automatic_natural_succession_handoff.py", SOURCE_SHA)
    checked(env["N"] / "root_p37c7_sdk_queue.py", QUEUE_SHA)
    require(queue.full_loop_state == state and state["completed_cycles"] == 1839
            and state["start_date_raw"] == 53144328
            and state["before"]["date_raw"] == 53186856
            and all(state.get(k) is None for k in ("pending_cycle", "pending_checkpoint", "terminal", "pending_unsafe_route_halt")),
            "original settled state differs")
    pending = state.get("pending_natural_succession")
    require(isinstance(pending, dict) and pending["global_turn"] == 1839
            and pending["original_before"] == audit["original_before"]
            and pending["auto_response"] == audit["original_cycle"]
            and audit.get("status") == "failed_retained"
            and audit.get("error") == "Foreign cached decision provider"
            and audit.get("same_game") == {"pid": 153556, "creation_filetime": 134368602545256920}
            and audit.get("calls") == [{"sequence": 3851, "tool": env["SEMANTIC"],
                  "response": row_pin["original_source"], "status": "received"}],
            "only the first received handoff SEM may resume")
    require(queue.launch["pid"] == 153556 and queue.job["game_creation_filetime"] == 134368602545256920,
            "physical Game identity differs")
    require(halt.get("message") == "Foreign cached decision provider"
            and halt.get("next_sequence") == 3852
            and halt.get("original_request") == row["request"]
            and halt.get("original_response") == row_pin["original_source"]
            and queue.halted.get("request") == row["request"]
            and queue.halted.get("row") == row
            and queue.halted.get("response") == row_pin["original_source"], "original halt differs")
    require(row_pin["sha256"] == ROW_SHA and row.get("client_error") is None
            and row["request"]["sequence"] == 3851
            and row["result"].get("is_error") is False, "closed SEM unsuccessful")
    body = env["decoded"](row)
    require(body.get("one_life_terminal") is True
            and body.get("date_raw") == state["before"]["date_raw"]
            and (body.get("played_character") or {}).get("character_id") == 40526
            and body.get("campaign_goal") == state["campaign_goal_anchor"], "original terminal SEM differs")
    require(not (env["Q"] / "3851-after-result.json").exists(), "original display unexpectedly settled")
    require(not (env["Q"] / "SUCCESSION3851-CONSUME-INTENT.json").exists()
            and not (env["Q"] / "AUTOMATIC-SUCCESSION-HANDOFF-001839-RESUME3852.json").exists(),
            "finite resume already attempted")
    require(not env["pending_request_paths"](env["INBOX"], env["OUTBOX"], 3852, held_control=Path(path).name),
            "another request pending")
    return queue.full_loop_state, audit, row, body, source, {"state": state_pin, "failed_audit": audit_pin,
                                          "original_semantic": row_pin, "original_halt": halt_pin}


async def recover(queue, session, request, path, env, *, birth_reader=None):
    state, old_audit, row, body, source, pins = validate(queue, request, path, env)
    if birth_reader is None:
        from root_p37_known_pause_recovery_control import process_birth_filetime
        birth_reader = process_birth_filetime
    require(birth_reader(153556) == 134368602545256920, "Game kernel birth differs")
    namespace = prepare_original_namespace(source)
    original_factory = namespace["_resident_make_call"]
    original_path = Path(pins["original_semantic"]["original_source"])
    consumed = False

    def make_call(q, sess, original_env, audit, audit_path, read_birth, pid, birth):
        original_call = original_factory(q, sess, original_env, audit, audit_path, read_birth, pid, birth)
        async def call(tool, arguments):
            nonlocal consumed
            if not consumed:
                require(tool == env["SEMANTIC"] and arguments == {}, "first original call differs")
                q.guard()
                require(read_birth(pid) == birth, "Game birth changed before original SEM consumption")
                from root_p37c6_overlay_relay import relay_compact
                # The actual C6 publisher must acknowledge these exact original bytes.
                projected = env["display_projection"](row, body)
                relay_compact(original_path, projected)
                consumed = True
                q.current_attempt = {"request": copy.deepcopy(row["request"]), "row": copy.deepcopy(row),
                                     "response": str(original_path)}
                audit["calls"].append({"sequence": 3851, "tool": tool, "response": str(original_path),
                                       "status": "received_original_once", "new_RPC_calls": 0})
                audit["original_first_semantic_source"] = pins["original_semantic"]
                env["atomic"](audit_path, audit, replace=True, limit=65536)
                return copy.deepcopy(body), original_path
            return await original_call(tool, arguments)
        return call

    namespace["_resident_make_call"] = make_call
    intent = {"schema": "xar.succession3851-original-semantic-once/v1", "machine_id": MACHINE,
              "at_utc": env["now"]().isoformat(), "control": request, "sources": pins,
              "original3851_RPC_replayed": False, "original_cycle_credit_added": 0}
    env["atomic"](env["Q"] / "SUCCESSION3851-CONSUME-INTENT.json", intent, limit=16384)
    queue.consume_sequence(request)
    queue.held_control = Path(path).name
    queue.halted = None
    queue.halt_cause = None
    # All original frame/expectation/Continue/CAP/UI/SAVE checks remain in this body.
    result = await namespace["automatic_handoff"](
        queue, session, state, original_before=old_audit["original_before"],
        event={"auto_response": old_audit["original_cycle"]}, env=env, birth_reader=birth_reader)
    require(consumed and result is queue.full_loop_state
            and result["completed_cycles"] == 1839
            and result.get("pending_natural_succession") is None, "original handoff did not commit")
    receipt = {"machine_id": MACHINE, "at_utc": env["now"]().isoformat(),
               "status": "source_bound_original_succession_tail_finished",
               "original3851_RPC_replayed": False, "original3849_AUTO_replayed": False,
               "original_first_semantic_source": pins["original_semantic"],
               "original_failed_audit_preserved": pins["failed_audit"],
               "completed_cycles": 1839, "final_frame": result["before"],
               "final_semantic_response": result["before_metrics_response"],
               "ordinary_cycle_credit_added": 0,
               "audit": str(env["Q"] / "AUTOMATIC-SUCCESSION-HANDOFF-001839-RESUME3852.json")}
    env["atomic"](env["Q"] / "SUCCESSION3851-RESUME-SETTLED.json", receipt, limit=16384)
    env["atomic"](env["N"] / "ROOT-CURRENT-HALT-P37.json", receipt, replace=True, limit=16384)
    env["atomic"](env["OUTBOX"] / Path(path).name,
                  {"request": request, "result": {"is_error": False, "structured_content": receipt}}, limit=16384)
    queue.current_attempt = None
    queue.held_control = None


def transform_unused_known_owner(source):
    """Append a finite branch; retain the entire old module and its delegate."""
    require(hashlib.sha256(source).hexdigest() == "47274e0d53f0b4383d11ec8cb40a5fed731fa0b5ba76bb738b71f33f9e77a74b",
            "unused known-owner module differs")
    suffix = '''
_before_succession3851_recover = recover
async def recover(queue, session, request, path, env, *, birth_reader=None, lifecycle_executor=None):
    if request.get("arguments", {}).get("repair_kind") == "natural_succession3851_first_semantic_resume":
        from root_p37_succession3851_resume import recover as resume3851
        return await resume3851(queue, session, request, path, env, birth_reader=birth_reader)
    return await _before_succession3851_recover(queue, session, request, path, env,
        birth_reader=birth_reader, lifecycle_executor=lifecycle_executor)
'''
    return source + suffix.encode("utf-8")
