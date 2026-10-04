"""Actual six-key AUB option-list observation/source selection; no Confirm."""
from copy import deepcopy
from .ingame_decisions_open_contract import EXE_SHA256, opening_binding
from .ingame_decision_item_action_contract import actual_selected_detail
SCHEMA="ck3-aub-policy-options-v1"
QUERY_STEP="query-aub-policy-options-v1"
QUERY_CAPABILITY="game.command.query-aub-policy-options-v1"
SELECT_STEP="select-aub-policy-option-v1"
SELECT_CAPABILITY="game.command.select-aub-policy-option-v1"
POLICY_KEYS=(
    "aub_policy_treasury_only_pause_choice", "aub_policy_treasury_only_continue_choice",
    "aub_policy_personal_only_pause_choice", "aub_policy_personal_only_continue_choice",
    "aub_policy_treasury_first_pause_choice", "aub_policy_treasury_first_continue_choice",
)
def validate_policy_key(key: object) -> str:
    if type(key) is not str or key not in POLICY_KEYS:
        raise ValueError("policy key is not an actual admitted AUB choice")
    return key
def policy_binding(snapshot: object) -> dict[str,object]:
    result=opening_binding(snapshot)
    if ("active_event" not in snapshot or snapshot["active_event"] is not None
            or "pending_character_interaction" not in snapshot or snapshot["pending_character_interaction"] is not None
            or type(result["episode_run_id"]) is not str or not result["episode_run_id"]):
        raise ValueError("AUB policy requires actual no-event/no-pending episode")
    for key,bound in (("native_revision",2**64),("connection_generation",2**64),("game_pid",2**32),("played_character_id",2**31)):
        if type(result[key]) is not int or not 0<result[key]<bound:
            raise ValueError("invalid native AUB episode stamp "+key)
    if type(result["date_raw"]) is not int or not -2**31<=result["date_raw"]<2**31:
        raise ValueError("invalid native AUB date")
    return result
def _policy(raw: object,binding: dict[str,object]) -> dict[str,object]:
    if not isinstance(raw,dict) or set(raw)!={"ready","unavailable_reason","played_character_id","decision_key","selected_key","selected_index","entries"}:
        raise ValueError("malformed actual AUB policy collection")
    if raw["ready"] is not True or raw["unavailable_reason"] or raw["decision_key"]!="enable_auto_build":
        raise ValueError("actual AUB collection unavailable or wrong decision")
    if type(raw["played_character_id"]) is not int or raw["played_character_id"]!=binding["played_character_id"]:
        raise ValueError("actual AUB collection changed player")
    rows=raw["entries"]
    if not isinstance(rows,list) or len(rows)!=6:
        raise ValueError("actual AUB collection is not six choices")
    keys=[];selected=[]
    for n,row in enumerate(rows):
        if not isinstance(row,dict) or set(row)!={"value_key","selected"} or type(row["selected"]) is not bool:
            raise ValueError("malformed actual AUB Entry")
        keys.append(validate_policy_key(row["value_key"]))
        if row["selected"]:selected.append(n)
    if len(set(keys))!=6 or set(keys)!=set(POLICY_KEYS) or len(selected)>1:
        raise ValueError("actual AUB keys/selection are ambiguous")
    index=selected[0] if selected else -1
    key=keys[index] if selected else ""
    if type(raw["selected_index"]) is not int or raw["selected_index"]!=index or raw["selected_key"]!=key:
        raise ValueError("actual AUB selected key/index/Entry disagree")
    return deepcopy(raw)
def normalize_policy_result(raw: object,binding: dict[str,object],*,action: bool=False,
                            expected_key: str|None=None,desired_key: str|None=None) -> dict[str,object]:
    common={"schema","step","read_only","game_version","executable_sha256","native_revision","connection_generation",
            "game_pid","played_character_id","date_raw","tooltip_available","enabled_available","rendered_down_available",
            "production_confirmed","before_actual_model","after_actual_model","unavailable_reason"}
    extra={"before_policy","after_policy","expected_selected_key","desired_key","already_selected","dispatch_invoked",
           "native_call_completed","postcondition_verified","verification_pending"} if action else {"policy"}
    if not isinstance(raw,dict) or set(raw) not in (common|extra,common|extra|{"backend_id"}):
        raise ValueError("malformed fixed AUB native DTO")
    if (raw["schema"]!=SCHEMA or raw["step"]!=(SELECT_STEP if action else QUERY_STEP) or raw["read_only"] is not (not action)
            or raw["game_version"]!="1.20.0.3" or str(raw["executable_sha256"]).lower()!=EXE_SHA256
            or raw.get("backend_id","native-headless")!="native-headless" or raw["unavailable_reason"]):
        raise ValueError("actual exact .3 AUB result unavailable or changed")
    for key in ("native_revision","connection_generation","game_pid","played_character_id","date_raw"):
        if type(raw[key]) is not int or raw[key]!=binding[key]:raise ValueError("AUB native stamp changed "+key)
    for key in ("tooltip_available","enabled_available","rendered_down_available","production_confirmed"):
        if raw[key] is not False:raise ValueError("AUB query/action cannot grant unsupported "+key)
    for key in ("before_actual_model","after_actual_model"):
        if not actual_selected_detail(raw[key],binding,"enable_auto_build"):
            raise ValueError("AUB actual selected detail/owner/frame unqualified")
    if action:
        validate_policy_key(expected_key);validate_policy_key(desired_key)
        if raw["expected_selected_key"]!=expected_key or raw["desired_key"]!=desired_key:raise ValueError("AUB action intent changed")
        before=_policy(raw["before_policy"],binding);after=_policy(raw["after_policy"],binding)
        if before["selected_key"]!=expected_key or after["selected_key"]!=desired_key:raise ValueError("AUB actual selection did not match intent")
        for name in ("already_selected","dispatch_invoked","native_call_completed","postcondition_verified","verification_pending"):
            if type(raw[name]) is not bool:raise ValueError("AUB action lacks actual bool "+name)
        same=expected_key==desired_key
        if (raw["already_selected"]!=same or raw["dispatch_invoked"]==same or raw["native_call_completed"]==same
                or raw["postcondition_verified"] is not True or raw["verification_pending"] is not False):
            raise ValueError("AUB source call/independent after proof inconsistent; no retry")
        if [r["value_key"] for r in before["entries"]]!=[r["value_key"] for r in after["entries"]]:
            raise ValueError("AUB actual row membership/order changed")
    else:_policy(raw["policy"],binding)
    return deepcopy(raw)
