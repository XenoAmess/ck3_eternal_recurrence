from __future__ import annotations

import json
import unittest

from xar_autoplayer.vanilla_events.registry import (
    query_vanilla_event_knowledge_v1,
)


class VanillaTgpTravelEventRecordTests(unittest.TestCase):
    def test_selected_stress_effect_profile_is_queryable_and_json_safe(
        self,
    ) -> None:
        response = query_vanilla_event_knowledge_v1("tgp_travel_events.0030")
        profile = response["analysis"]["selected_choice_effect_profile"]

        json.dumps(profile, allow_nan=False)
        self.assertEqual(profile["selected_native_option_index"], 1)
        stress_effect = profile["selected_option_effects"][0]
        self.assertEqual(stress_effect["authored_value_key"], "medium_stress_impact_loss")
        self.assertEqual(stress_effect["authored_base_points"], -30)
        self.assertFalse(stress_effect["runtime_delta_exact"])
        self.assertEqual(
            profile["observable_postcondition"]["expected_relation"],
            "non_increasing",
        )


if __name__ == "__main__":
    unittest.main()
