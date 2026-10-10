"""New guarded-observer wire source regression; no CK3 call or old fixture replay."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

wire_path, candidate_parser, old_parser, support_root = map(Path, sys.argv[1:5])
sys.path.insert(0, str(support_root))
from xar_autoplayer.bridge.driver import BridgeUnavailableError

def load(path, suffix):
    name = "xar_autoplayer.bridge._guarded_source_regression_" + suffix
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

fixed, before = load(candidate_parser, "fixed"), load(old_parser, "before")
wire = json.loads(wire_path.read_text(encoding="utf-8").strip())
value = wire["result"]["current_first_heir_reproductive_inputs_v1"]
pair = value["conception_pair_inputs"]["pairs"][0]
assert pair["conditional_short_circuit"]["source"] == "guarded_current_actual4_pair_provider_shortcircuit"
assert pair["conditional_short_circuit"]["first_output_raw"] == 0
assert pair["conditional_short_circuit"]["short_circuits_to_zero"] is True
assert pair["conditional_short_circuit"]["second_evaluated"] is False

def validate(module, raw):
    return module.validate_current_first_heir_reproductive_inputs_v1(raw,
        actor=1, heir=2, native_revision=7, date_raw=123,
        relation={"status":"available", "primary_spouse_character_id":3,
                  "spouse_character_ids":[3], "betrothed_character_id":None})

try: validate(before, value)
except BridgeUnavailableError as error:
    assert str(error) == "native conception observation is malformed"
else: raise AssertionError("old current parser did not reproduce guarded source rejection")
assert validate(fixed, value) == value
legacy = deepcopy(value)
legacy["conception_pair_inputs"]["pairs"][0]["conditional_short_circuit"]["source"] = "conditional_actual4_pair_provider_shortcircuit"
assert validate(fixed, legacy) == legacy
mutations = [("source", "unknown_guarded_source"), ("first_output_raw", True),
             ("status", "complete"), ("unavailable_reason", "unexpected_reason")]
for key, replacement in mutations:
    raw = deepcopy(value)
    raw["conception_pair_inputs"]["pairs"][0]["conditional_short_circuit"][key] = replacement
    try: validate(fixed, raw)
    except BridgeUnavailableError: pass
    else: raise AssertionError("strict guarded observation mutation accepted: " + key)
raw = deepcopy(value)
raw["rows"][0]["native_conception_extended_gate"]["source"] = "guarded_current_actual4_pair_provider_shortcircuit"
try: validate(fixed, raw)
except BridgeUnavailableError: pass
else: raise AssertionError("other leaf source validation was widened")
assert value["conception_pair_inputs"]["pairs"][0]["conditional_pair_provider"]["first_output_raw"] is None
print(json.dumps({"new_actual_observer_serializer_wire_cells":1,
    "old_parser_rejection_reproduced":True, "new_parser_preserves_guarded_source":True,
    "legacy_source_preserved":True,"strict_rejection_mutations":5,
    "old_fixture_replays":0,"Game_queries":0,"natural_probability_or_pregnancy_credit":False}))
