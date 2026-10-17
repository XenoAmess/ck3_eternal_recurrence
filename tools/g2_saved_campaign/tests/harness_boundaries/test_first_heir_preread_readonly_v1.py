from copy import deepcopy
import json
from pathlib import Path
import unittest
from tools.g2_saved_campaign.first_heir_preread_readonly_v1 import classify_first_heir_preread_readonly_v1 as qualify

PACK = Path(__file__).resolve().parent
ROW = json.loads((PACK / "actual196-projection.json").read_bytes())


class FirstHeirPreRead(unittest.TestCase):
    def test_other_named_native_pre_read_guards_only(self):
        text = ROW["result"]["content"][0]["text"]
        prefix = text.split("pre_read_guard=")[0] + "pre_read_guard="
        cached = text.split("; cached=", 1)[1].split("; observed=", 1)[0]
        cases = [("previous_snapshot_missing", False, "unknown", "unknown"),
                 ("snapshot_read_failed", False, cached, "unknown")]
        for guard, field in (("not_paused", "paused"), ("map_not_ready", "map_ready"),
                             ("played_character_missing", "has_played_character"),
                             ("played_character_not_alive", "played_character_alive")):
            changed = ",".join(field + ":0" if part.startswith(field + ":") else part
                               for part in cached.split(","))
            cases.append((guard, True, changed, changed))
        for guard, completed, old, fresh in cases:
            with self.subTest(guard=guard):
                row = deepcopy(ROW)
                row["result"]["content"][0]["text"] = (prefix + guard
                    + "; snapshot_read_completed=" + str(completed).lower()
                    + "; cached=" + old + "; observed=" + fresh
                    + "; complex_field_values=presence_or_count_only")
                value = qualify(row)
                self.assertEqual(value["pre_read_guard"], guard)
                self.assertFalse(value["relationship_query_executor_started"])
                row["result"]["content"][0]["text"] = row["result"]["content"][0]["text"].replace(
                    "snapshot_read_completed=" + str(completed).lower(),
                    "snapshot_read_completed=" + str(not completed).lower())
                self.assertIsNone(qualify(row))

    def test_actual196_and_scalar_or_complex_difference_labels(self):
        self.assertEqual(qualify(ROW)["differing_fields"], ["played_character_prestige"])
        text = ROW["result"]["content"][0]["text"]
        for name in ("played_character_gold", "played_character_piety", "played_character_spouse_ids",
                     "played_character_event_trait_membership", "active_wars", "player_armies"):
            with self.subTest(name=name):
                row = deepcopy(ROW)
                row["result"]["content"][0]["text"] = text.replace("differing_fields=played_character_prestige", "differing_fields=" + name)
                self.assertTrue(qualify(row)["read_only_precondition"])
                self.assertFalse(qualify(row)["business_submission"])

    def test_unknown_or_during_read_timeout_business_and_malformed_reject(self):
        text = ROW["result"]["content"][0]["text"]
        mutations = [
            text.replace("frame changed; pre_read_guard=", "frame changed during read; pre_read_guard="),
            text.replace("pre_read_guard=snapshot_not_equal", "pre_read_guard=unknown"),
            text.replace("snapshot_read_completed=true", "snapshot_read_completed=false"),
            text.replace("differing_fields=played_character_prestige", "differing_fields=unknown"),
            text.replace("differing_fields=played_character_prestige", "differing_fields=played_character_prestige,played_character_prestige"),
            text.replace("cached=date_raw:", "cached=bad:"),
            text.replace("observed=date_raw:", "observed=bad:"),
            text.replace("complex_field_values=presence_or_count_only", "complex_field_values=raw"),
            text.replace("current heir relationship query RED", "submit marriage RED"),
            text.replace("played_character_prestige_raw:199035710", "played_character_prestige_raw:null"),
            text.replace("; observed=", "; wrong="),
            "Error executing tool ck3_auto_turn: current heir relationship query timed out",
        ]
        for changed in mutations:
            with self.subTest(text=changed[:110]):
                row = deepcopy(ROW);row["result"]["content"][0]["text"] = changed
                self.assertIsNone(qualify(row))
        for key, value in (("client_error", "timeout"), ("request", {"tool":"ck3_execute_step","arguments":{},"sequence":196})):
            row=deepcopy(ROW);row[key]=value;self.assertIsNone(qualify(row))


if __name__ == "__main__": unittest.main()
