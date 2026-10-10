"""One new same-query serializer/56strict/copied-fact consumer join; no native replay."""
from copy import deepcopy
import json
from pathlib import Path
import sys

wire_path, own_src, contract_src, caller_src, support_src, retained_journal = map(Path, sys.argv[1:7])
sys.path.insert(0, str(support_src))
import xar_autoplayer.bridge as bridge_package
import xar_autoplayer.simulation as simulation_package
for path in (caller_src, contract_src, own_src):
    bridge_package.__path__.insert(0, str(path / "xar_autoplayer/bridge"))
simulation_package.__path__.insert(0, str(contract_src / "xar_autoplayer/simulation"))
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.current_first_heir_reproductive_inputs_v1 import validate_current_first_heir_reproductive_inputs_v1

wire_rows = [json.loads(line) for line in wire_path.read_text(encoding="utf-8").splitlines()]
wires = {v["request_id"]:v["result"]["current_first_heir_reproductive_inputs_v1"] for v in wire_rows}
assert len(wires)==3
def validate(value):
    return validate_current_first_heir_reproductive_inputs_v1(value, actor=1,heir=38822,
        native_revision=7,date_raw=123,relation={"status":"available",
        "primary_spouse_character_id":38718,"spouse_character_ids":[38718],"betrothed_character_id":None})
def pair(value): return value["conception_pair_inputs"]["pairs"][0]
legacy=wires["legacy_natural_absent"]
assert validate(legacy)==legacy
assert "natural_conception_observation" not in pair(validate(legacy))
owned=wires["owned_retained_native_orientation"]
assert pair(owned)["natural_conception_observations_v1"]==json.loads(retained_journal.read_text(encoding="utf-8"))
normalized=validate(owned)
p=pair(normalized);raw=p["natural_conception_observations_v1"];summary=p["natural_conception_observation"]
assert raw==pair(owned)["natural_conception_observations_v1"]
assert raw["events"][0]["first_before"]["full_id"]==38718
assert raw["events"][0]["second_before"]["full_id"]==38822
assert raw["observer_installed"] is False and raw["current_session_guard"] is False
assert raw["events"][1]["provider"] is None and raw["events"][1]["sample"] is None
assert summary["status"]=="unknown_current_observation"
assert summary["pregnancy_or_birth_status"]=="unknown"
assert summary["monthly_or_stage_role"]=="unknown"
assert p["conditional_pair_provider"]["first_output_raw"] is None
assert "natural_conception_observation" not in pair(owned)
empty=pair(validate(wires["owned_journal_unavailable"]))
assert empty["natural_conception_observations_v1"] is None
assert empty["natural_conception_observation"]["status"]=="unavailable"
mutations=[(("source_pin",),"incorrect_pin"),(("events",0,"first_before","full_id"),9),
           (("event_count",),True),(("events",0,"original_al"),256),
           (("current_session_guard",),1)]
for path,replacement in mutations:
    value=deepcopy(owned);target=pair(value)["natural_conception_observations_v1"]
    for key in path[:-1]:target=target[key]
    target[path[-1]]=replacement
    try:validate(value)
    except BridgeUnavailableError:pass
    else:raise AssertionError("malformed retained natural journal accepted: "+str(path))
print(json.dumps({"new_whole_query_wire_cases":3,"retained_native_events":2,
    "strict_rejections":len(mutations),"native_orientation_retained":True,
    "false_guards_not_upgraded":True,"old_native_fixture_replays":0,"Game_queries":0}))
