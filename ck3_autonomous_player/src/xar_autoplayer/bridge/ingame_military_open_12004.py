"""Fixed stock Military opening through the existing semantic execute-step route."""
from __future__ import annotations
import hashlib
import json
import os
import time
import uuid
from .driver import BridgeUnavailableError,PreSubmissionRevisionMismatchError,UnsupportedStepError
from .ingame_decisions_open_contract import opening_binding,normalize_open_result
from .version_identity import CK3_12004,require_exact_native_build

STEP="activate-ingame-military-v1"
CAPABILITY="game.command."+STEP
GUI_SHA256="77d0beedefe23eee22b24c1c0b160ae5ee8ec938868d3f4b7ae76296347a6ac6"


def _binding(snapshot):
    binding=opening_binding(snapshot)
    hello=snapshot["diagnostics"]["hello"]
    if require_exact_native_build(hello.get("expected_ck3_version"),hello.get("expected_ck3_sha256"))!=CK3_12004:
        raise ValueError("Military opener requires exact .4")
    if not isinstance(binding["episode_run_id"],str) or not binding["episode_run_id"]:
        raise ValueError("Military opener requires an actual episode identity")
    return binding


def _normalize_ack(raw,binding):
    if (not isinstance(raw,dict) or raw.get("schema")!="ck3-ingame-military-open-12004-v1" or raw.get("step")!=STEP
            or raw.get("source_gui_sha256")!=GUI_SHA256
            or raw.get("business_model_available") is not False
            or raw.get("military_refill_action_available") is not False
            or require_exact_native_build(raw.get("game_version"),raw.get("executable_sha256"))!=CK3_12004):
        raise ValueError("Military opener lacks exact source/profile result")
    # Reuse the production fixed-opener proof validator, then restore this
    # action's native identity. No model/window name is inferred by projection.
    normalize_open_result({**raw,"schema":"ck3-ingame-decisions-open-v1","step":"activate-ingame-decisions-v1"},binding)
    if type(raw.get("dispatch_attempted")) is not bool or (
        raw["dispatch_invoked"] and not raw["dispatch_attempted"]
    ) or (raw["before_visible"] and raw["dispatch_attempted"]):
        raise ValueError("Military opener once-dispatch proof is inconsistent")
    return dict(raw)


def _visible(tree):
    if (not isinstance(tree,dict) or tree.get("scope_root_name")!="military_view"
            or tree.get("truncated") is not False):
        raise ValueError("Military later census is incomplete or mismatched")
    if tree.get("root_available") is not True:return False
    rows=tree.get("widgets")
    if not isinstance(rows,list):raise ValueError("Military later census lacks rows")
    roots=[row for row in rows if isinstance(row,dict) and row.get("child_path")==""]
    if len(roots)!=1 or roots[0].get("runtime_name")!="military_view":
        raise ValueError("Military actual root is not source-bound")
    return roots[0].get("effective_visible") is True


def open_fixed_military_window_12004(driver,*,expected_revision=None):
    from .native_driver import _same_paused_native_frame,_validate_revision
    from .ingame_decision_outcome_contract import reject_unresolved_claims,preserve_verified_claim
    starting=driver.take_snapshot()
    try:binding=_binding(starting)
    except ValueError as error:raise BridgeUnavailableError(str(error)) from error
    revision=starting["revision"]
    if expected_revision is not None:
        _validate_revision(expected_revision,"expected_revision")
        if expected_revision!=revision:raise PreSubmissionRevisionMismatchError("Military opener public revision changed")
    if CAPABILITY not in set(driver.capabilities().get("bridge_capabilities",[])):
        raise UnsupportedStepError("native DLL lacks the exact .4 fixed Military opener")
    directory=driver._native_driver_state_path().parent/"ingame-military-opener-actions"
    directory.mkdir(parents=True,exist_ok=True)
    identity={"game_pid":binding["game_pid"],"actor_id":binding["played_character_id"],
              "episode_run_id":binding["episode_run_id"],"decision_key":"","action":"open","public_revision":revision}
    try:reject_unresolved_claims(directory,identity)
    except ValueError as error:raise BridgeUnavailableError(str(error)) from error
    key=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()
    claim=directory/(key+".claim.json");request_id="military-"+uuid.uuid4().hex
    try:
        with claim.open("x",encoding="utf-8",newline="\n") as stream:
            json.dump({"schema":"ck3-ingame-military-once-claim-v1","request_id":request_id,"binding":binding,
                       "action_identity":identity,"status":"claimed_result_unknown_no_retry"},stream,ensure_ascii=False,indent=2)
            stream.write("\n");stream.flush();os.fsync(stream.fileno())
    except FileExistsError as error:raise BridgeUnavailableError("Military opener already claimed; no action retry") from error
    raw=None
    try:
        raw=driver._execute_primitive_step(STEP,expected_revision=revision,required_capability=CAPABILITY,
            protocol_request_id=request_id,request_fields={"expected_player_character_id":binding["played_character_id"],
                "expected_game_pid":binding["game_pid"],"expected_connection_generation":binding["connection_generation"]})
        with claim.with_suffix(".result.json").open("x",encoding="utf-8",newline="\n") as stream:
            json.dump({"request_id":request_id,"raw":raw},stream,ensure_ascii=False,indent=2)
            stream.write("\n");stream.flush();os.fsync(stream.fileno())
        result=_normalize_ack(raw,binding)
        deadline=time.monotonic()+5.0
        while True:
            current=driver.take_snapshot()
            if _binding(current)!=binding or not _same_paused_native_frame(starting,current):
                raise BridgeUnavailableError("Military later observation crossed episode/frame")
            later=driver.inspect_gui_window_tree_v1("military")
            ending=driver.take_snapshot()
            if _binding(ending)!=binding or not _same_paused_native_frame(starting,ending):
                raise BridgeUnavailableError("Military tree observation crossed episode/frame")
            if _visible(later):break
            remaining=deadline-time.monotonic()
            if remaining<=0:raise BridgeUnavailableError("Military ACK lacks later visible root; no retry")
            time.sleep(min(0.1,remaining))
        result.update({"postcondition_verified":True,"verification_pending":False,"status":"verified_visible",
                       "later_military_tree":later,"native_ack":dict(raw),"action_request_id":request_id,
                       "action_claim_path":str(claim),"episode_run_id":binding["episode_run_id"],
                       "queried_revision":revision,"uses_mouse":False,"uses_keyboard":False,"uses_ocr":False})
        preserve_verified_claim(claim,request_id,result)
        return result
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
