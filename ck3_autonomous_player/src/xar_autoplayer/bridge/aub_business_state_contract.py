"""Actual four character flags and AUB-only Confirm; no variable or UI-value projection."""
from copy import deepcopy
from .aub_policy_options_contract import POLICY_KEYS, policy_binding, validate_policy_key
from .ingame_decision_item_action_contract import actual_selected_detail
from .ingame_decisions_open_contract import EXE_SHA256
QUERY_STEP="query-aub-business-state-v1"
QUERY_CAPABILITY="game.command.query-aub-business-state-v1"
CONFIRM_STEP="confirm-aub-policy-v1"
CONFIRM_CAPABILITY="game.command.confirm-aub-policy-v1"
FLAG_KEYS=("enable_auto_build","aub_funding_treasury_only","aub_funding_personal_only","aub_pause_when_over_domain_limit")
def normalize_state(raw: object,binding: dict[str,object]) -> dict[str,object]:
    fields={"schema","step","read_only","game_version","executable_sha256","native_revision","connection_generation","game_pid","played_character_id","date_raw",
            "available","owner_thread_verified","frame_verified","source_abi_pins_verified","gui_owner_binding_verified","stable_two_pass_verified",
            "detail_census_verified","detail_root_available","detail_tree_complete","detail_effectively_visible","flags","unavailable_reason",
            "rendered_text_available","rendered_down_available","product_acceptance_proven"}
    if not isinstance(raw,dict) or set(raw) not in (fields,fields|{"backend_id"}):raise ValueError("malformed AUB fixed flag DTO")
    if (raw["schema"]!="ck3-aub-business-state-v1" or raw["step"]!=QUERY_STEP or raw["read_only"] is not True or raw["game_version"]!="1.20.0.3"
            or str(raw["executable_sha256"]).lower()!=EXE_SHA256 or raw.get("backend_id","native-headless")!="native-headless" or raw["unavailable_reason"]):
        raise ValueError("actual AUB state unavailable or changed")
    for key in ("native_revision","connection_generation","game_pid","played_character_id","date_raw"):
        if type(raw[key]) is not int or raw[key]!=binding[key]:raise ValueError("AUB state stamp changed "+key)
    for key in ("available","owner_thread_verified","frame_verified","source_abi_pins_verified","gui_owner_binding_verified","stable_two_pass_verified","detail_census_verified","detail_tree_complete"):
        if raw[key] is not True:raise ValueError("actual AUB state proof missing "+key)
    for key in ("detail_root_available","detail_effectively_visible"):
        if type(raw[key]) is not bool:raise ValueError("actual AUB census bool missing "+key)
    if not raw["detail_root_available"] and raw["detail_effectively_visible"]:raise ValueError("absent AUB detail cannot be visible")
    for key in ("rendered_text_available","rendered_down_available","product_acceptance_proven"):
        if raw[key] is not False:raise ValueError("AUB native flags cannot grant "+key)
    if not isinstance(raw["flags"],list) or len(raw["flags"])!=4:raise ValueError("AUB flag set incomplete")
    for key,f in zip(FLAG_KEYS,raw["flags"],strict=True):
        if (not isinstance(f,dict) or set(f)!={"key","available","atom_registered","present","unavailable_reason"} or f["key"]!=key
                or f["available"] is not True or type(f["atom_registered"]) is not bool or type(f["present"]) is not bool or f["unavailable_reason"]
                or (f["present"] and not f["atom_registered"])):raise ValueError("actual AUB flag missing/type/name changed")
    return deepcopy(raw)
def flags_match_selected(key: object,state: dict[str,object]) -> bool:
    choice=POLICY_KEYS.index(validate_policy_key(key))
    return tuple(f["present"] for f in state["flags"])==(True,choice<2,2<=choice<4,choice%2==0)
def actual_confirmed_state(raw: object,binding: dict[str,object],key: str) -> dict[str,object]:
    state=normalize_state(raw,binding)
    if state["detail_effectively_visible"] or not flags_match_selected(key,state):raise ValueError("AUB actual flags or complete detail closure not proven")
    return state
def normalize_confirm(raw: object,binding: dict[str,object],key: str) -> dict[str,object]:
    validate_policy_key(key)
    fields={"schema","step","read_only","game_version","executable_sha256","selected_key","target_child_path","receiver_qualified","selected_policy_revalidated",
            "dispatch_attempted","dispatch_invoked","native_handled","postcondition_verified","verification_pending","before_actual_model","state_before","state_after",
            "actual_policy_before","unavailable_reason","product_acceptance_proven"}
    if not isinstance(raw,dict) or set(raw) not in (fields,fields|{"backend_id"}):raise ValueError("malformed fixed AUB Confirm DTO")
    if (raw["schema"]!="ck3-aub-confirm-v1" or raw["step"]!=CONFIRM_STEP or raw["read_only"] is not False or raw["game_version"]!="1.20.0.3"
            or str(raw["executable_sha256"]).lower()!=EXE_SHA256 or raw.get("backend_id","native-headless")!="native-headless"
            or raw["unavailable_reason"] or raw["selected_key"]!=key or raw["product_acceptance_proven"] is not False):
        raise ValueError("actual AUB Confirm unavailable/result unknown; no retry")
    if not actual_selected_detail(raw["before_actual_model"],binding,"enable_auto_build"):raise ValueError("AUB actual Confirm detail/actor not bound")
    for name in ("receiver_qualified","selected_policy_revalidated","dispatch_attempted","dispatch_invoked"):
        if raw[name] is not True:raise ValueError("AUB Confirm proof missing "+name+"; no retry")
    if (type(raw["native_handled"]) is not bool or type(raw["postcondition_verified"]) is not bool or type(raw["verification_pending"]) is not bool
            or raw["verification_pending"]==raw["postcondition_verified"] or type(raw["target_child_path"]) is not str or not raw["target_child_path"]):
        raise ValueError("AUB receiver/ACK metadata malformed")
    before=normalize_state(raw["state_before"],binding)
    if before["flags"][0]["present"] or not before["detail_effectively_visible"]:raise ValueError("AUB already enabled or before detail hidden")
    after=normalize_state(raw["state_after"],binding)
    actual_post=not after["detail_effectively_visible"] and flags_match_selected(key,after)
    if raw["postcondition_verified"]!=actual_post:raise ValueError("AUB native after-state and native postcondition disagree")
    p=raw["actual_policy_before"]
    if not isinstance(p,dict) or set(p)!={"ready","selected_key","entries"} or p["ready"] is not True or p["selected_key"]!=key:
        raise ValueError("AUB actual selected policy before Confirm missing")
    rows=p["entries"]
    if not isinstance(rows,list) or len(rows)!=6:raise ValueError("AUB actual six entries before Confirm missing")
    keys=[];selected=[]
    for entry in rows:
        if not isinstance(entry,dict) or set(entry)!={"value_key","selected"} or type(entry["selected"]) is not bool:raise ValueError("malformed actual AUB Entry")
        keys.append(validate_policy_key(entry["value_key"]))
        if entry["selected"]:selected.append(entry["value_key"])
    if len(set(keys))!=6 or set(keys)!=set(POLICY_KEYS) or selected!=[key]:raise ValueError("AUB actual selected Entry ambiguous")
    return deepcopy(raw)
