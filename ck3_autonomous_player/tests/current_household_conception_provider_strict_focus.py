"""One connected full-provider wire and strict-input compound; no CK3 call."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

source = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(source))
if len(sys.argv) > 2:
    sys.path.append(sys.argv.pop(2))
import xar_autoplayer.bridge as bridge_package
bridge_package.__path__.insert(0, str(source / "xar_autoplayer/bridge"))
from xar_autoplayer.bridge.current_first_heir_reproductive_inputs_v1 import validate_current_first_heir_reproductive_inputs_v1
from xar_autoplayer.bridge.driver import BridgeUnavailableError

wire_path = Path(sys.argv.pop(1))
wire_rows = [json.loads(line) for line in wire_path.read_text(encoding="utf-8").splitlines() if line.startswith("{")]
wires = {value["request_id"]: value["result"]["current_first_heir_reproductive_inputs_v1"] for value in wire_rows if "result" in value}

def validate(value):
    return validate_current_first_heir_reproductive_inputs_v1(value, actor=1, heir=2,
        native_revision=7, date_raw=123, relation={"status":"available", "primary_spouse_character_id":3,
        "spouse_character_ids":[3], "betrothed_character_id":None})

class CurrentProviderCompound(unittest.TestCase):
    def test_one_new_full_provider_wire_strict_compound(self):
        self.assertEqual(len(wires), 8)
        for name, value in wires.items():
            with self.subTest(wire=name): self.assertEqual(validate(value), value)
        def pair(name): return wires[name]["conception_pair_inputs"]["pairs"][0]
        normal = pair("normal_complete")
        self.assertEqual(normal["conditional_pair_provider"]["first_output_raw"], 35000)
        self.assertIs(normal["native_normal_close_family"]["normal_close_family"], False)
        self.assertIs(normal["native_reverse_close_or_extended"]["alternate_close_or_extended"], False)
        unused = pair("unused_scalar_missing")
        self.assertEqual(unused["conditional_pair_provider"]["first_output_raw"], 35000)
        self.assertIsNone(unused["independent_numeric_inputs"]["alternate_relation_multiplier"])
        alternate = pair("alternate_directed_true")
        self.assertEqual(alternate["conditional_pair_provider"]["first_output_raw"], 70000)
        self.assertEqual(alternate["native_second_title_state"]["second_1c0_raw_u64"], 2**63)
        self.assertEqual(alternate["native_normal_close_family"]["status"], "not_required")
        partial = pair("partial_membership")
        self.assertIsNone(partial["native_secondary_family_membership"]["second_family20_contains_first"])
        self.assertEqual(partial["native_secondary_family_membership"]["ordered_full_ids"], [0x01000002, 2])
        self.assertEqual(partial["conditional_pair_provider"]["unavailable_input"], "second_family20_contains_first")
        changed = pair("normal_identity_changed")
        self.assertIs(changed["native_normal_close_family"]["native_return_value"], True)
        self.assertIsNone(changed["native_normal_close_family"]["normal_close_family"])
        early = pair("known_early_zero")["conditional_pair_provider"]
        self.assertEqual(early["first_output_raw"], 0)
        self.assertIs(early["actual_caller_zero_rejection"], True)
        self.assertEqual(early["reached_stages_mask_u64"], 1)
        self.assertEqual(wires["changed_frame"]["status"], "available")
        self.assertNotIn("conception_pair_inputs", wires["legacy_absent"])
        mutations = [
            (("conditional_pair_provider","first_output_raw"), True),
            (("conditional_pair_provider","actual_caller_zero_rejection"), True),
            (("conditional_pair_provider","status"), "unavailable"),
            (("conditional_pair_provider","terminal_writer_rva"), 0),
            (("conditional_pair_provider","selected_count_role"), "outsider"),
            (("conditional_pair_provider","unavailable_input"), "invented"),
            (("conditional_pair_provider","stop_stage_raw_u8"), 21),
            (("conditional_pair_provider","reached_stages_mask_u64"), 2**21),
            (("conditional_pair_provider","reached_stages_mask_u64"), 1),
            (("independent_numeric_inputs","available_mask_u8"), True),
            (("independent_numeric_inputs","base_average_floor"), None),
            (("native_normal_close_family","normal_close_family"), True),
            (("native_normal_close_family","first_full_id_after"), 0x01000002),
            (("native_normal_close_family","status"), "not_required"),
            (("native_second_title_state","second_1c0_raw_u64"), -1),
            (("native_second_title_state","second_title_state_present"), True),
            (("native_secondary_family_membership","list_count_raw_i32"), -1),
            (("native_secondary_family_membership","first_match_index"), 0),
            (("native_reverse_close_or_extended","alternate_close_or_extended"), None),
        ]
        for path, replacement in mutations:
            value = deepcopy(wires["normal_complete"])
            target = value["conception_pair_inputs"]["pairs"][0]
            for key in path[:-1]: target = target[key]
            target[path[-1]] = replacement
            with self.subTest(path=path), self.assertRaises(BridgeUnavailableError): validate(value)
        legacy = deepcopy(wires["normal_complete"])
        for key in ("native_normal_close_family", "native_second_title_state", "native_secondary_family_membership",
                    "native_reverse_close_or_extended", "independent_numeric_inputs", "conditional_pair_provider"):
            del legacy["conception_pair_inputs"]["pairs"][0][key]
        self.assertEqual(validate(legacy), legacy)
        returned = validate(wires["normal_complete"])
        returned["conception_pair_inputs"]["pairs"][0]["conditional_pair_provider"]["first_output_raw"] = 999
        self.assertEqual(normal["conditional_pair_provider"]["first_output_raw"], 35000)
        print(json.dumps({"new_wire_cases":8,"strict_rejection_mutations":len(mutations),"legacy_new_fields_absent":True,
                          "conditional_only":True,"original_provider_calls":False,"native_rng_calls":False}))

if __name__ == "__main__": unittest.main(verbosity=2)
