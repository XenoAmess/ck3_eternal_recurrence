"""Pure leaf replay of a real government primitive, with fixture ordinary intent.

The hello/state/government files are frozen production packets. The ordinary
binding and goal below are synthetic fixtures, not evidence of an ordinary
campaign live loop. The third case additionally supplies a synthetic native
spec-only profile matching the current 1.20.0.2 Japanese feudal definition.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.native_driver import NativeProtocolState
from xar_autoplayer.bridge.succession_transition_contract import (
    ORDINARY_CAMPAIGN_SUCCESSION,
    bind_succession_lifecycle_from_environment_v1,
)
from xar_autoplayer.ordinary_campaign_government_context_v1 import (
    build_ordinary_campaign_government_context_v1,
)
from xar_autoplayer.strategy import new_ordinary_campaign_goal_v1


FIXTURES = PROJECT_ROOT / "tests" / "fixtures" / "ck3_12002_government_protocol_live_fix"
CAMPAIGN_ID = "fixture-ordinary-government-context"


def _wire(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8-sig"))


def _ordinary_fixture_inputs() -> tuple[dict[str, object], dict[str, object]]:
    protocol = NativeProtocolState("offline-government-context-leaf")
    protocol.ingest(_wire("hello.json"))
    protocol.ingest(_wire("initial-state.json"))
    snapshot = protocol.semantic_snapshot()
    actor = snapshot["played_character"]["character_id"]
    # This binding expresses only the offline fixture's intent. The original
    # game packet is preserved and is not relabeled as an ordinary live run.
    snapshot["succession_lifecycle"] = bind_succession_lifecycle_from_environment_v1(
        {
            "environment_sha256": "a" * 64,
            "rules": {"profile": [{"rule": "xar_enabled", "setting": "xar_off"}]},
        },
        lifecycle=ORDINARY_CAMPAIGN_SUCCESSION,
        ordinary_campaign_no_pact=True,
    )
    snapshot["campaign_goal"] = new_ordinary_campaign_goal_v1(CAMPAIGN_ID, actor)
    # The original outer RED packet is deliberately not ingested. Its nested
    # observation is the real government primitive already validated by the
    # existing protocol-fix fixture; this leaf tests only its new consumer.
    government = _wire("government-response-red.json")["result"]["government_runtime_adapter"]
    return snapshot, government


class OrdinaryCampaignGovernmentContextLeafTests(unittest.TestCase):
    def test_real_core_identity_and_44_features_reach_ordinary_context(self) -> None:
        snapshot, government = _ordinary_fixture_inputs()

        context = build_ordinary_campaign_government_context_v1(
            snapshot, government_observation=government, query_permitted=True,
        )

        self.assertEqual(context["status"], "available")
        self.assertEqual(context["campaign_id"], CAMPAIGN_ID)
        self.assertEqual(context["current_character_id"], 29829)
        self.assertEqual(context["snapshot_revision"], 3)
        self.assertEqual(context["date_raw"], 53169072)
        self.assertEqual(context["government_key"], "feudal_government")
        self.assertEqual(context["adapter_family"], "core_landed")
        self.assertEqual(context["adapter_status"], "core_supported")
        self.assertTrue(context["identity_observation_ready"])
        self.assertTrue(context["core_adapter_ready"])
        self.assertTrue(context["ordinary_goal_context_ready"])
        self.assertIsNone(context["unavailable_reason"])
        observed = context["government_runtime_adapter"]
        self.assertEqual(observed, government)
        features = observed["effective_feature_flags"]
        self.assertEqual(features["native_count"], 44)
        self.assertEqual(len(features["items"]), 44)
        self.assertEqual(features["items"][43]["key"], "by_god_alone")
        self.assertNotIn("barter_troops", [item["key"] for item in features["items"]])

    def test_default_off_does_not_publish_a_government_from_available_input(self) -> None:
        snapshot, government = _ordinary_fixture_inputs()

        context = build_ordinary_campaign_government_context_v1(
            snapshot, government_observation=government,
        )

        self.assertEqual(context["status"], "not_queried")
        self.assertFalse(context["query_permitted"])
        self.assertEqual(context["unavailable_reason"], "government_query_not_permitted")
        self.assertFalse(context["identity_observation_ready"])
        self.assertFalse(context["core_adapter_ready"])
        self.assertFalse(context["ordinary_goal_context_ready"])
        self.assertIsNone(context["government_key"])
        self.assertIsNone(context["adapter_family"])
        self.assertIsNone(context["adapter_status"])
        self.assertIsNone(context["government_runtime_adapter"])

    def test_synthetic_spec_only_identity_keeps_core_goal_readiness_false(self) -> None:
        snapshot, actual_government = _ordinary_fixture_inputs()
        government = copy.deepcopy(actual_government)
        # Synthetic status case derived from the production observer's current
        # kGovernmentDefinitions12002 Japan row and kJapanFeudalProfile. This
        # is not an observed Japanese ruler or another live capability claim.
        government["government"]["key"] = "japan_feudal_government"
        government["government"]["flags"] = [
            "may_elevate_co_monarch",
            "government_is_japan_feudal",
            "government_has_county_tier_noble_families",
            "has_special_house_aspirations",
            "government_is_settled",
            "government_uses_domicile_but_not_adventurer",
            "has_unique_government_perks",
            "government_uses_japanese_family_aspirations",
            "government_has_house_blocs",
            "government_uses_japanese_bureaucracy",
        ]
        government["adapter"].update(
            status="adapter_spec_ready_not_implemented",
            family="tgp_japan_feudal",
            requirements_met=True,
            required_effective_features=[],
            capability_profile_features=[
                copy.deepcopy(item)
                for item in government["effective_feature_flags"]["items"]
                if item["key"] in {"all_under_heaven", "advanced_aspirations"}
            ],
        )
        government["readiness"]["core_adapter_ready"] = False

        context = build_ordinary_campaign_government_context_v1(
            snapshot, government_observation=government, query_permitted=True,
        )

        self.assertEqual(context["status"], "available")
        self.assertTrue(context["identity_observation_ready"])
        self.assertFalse(context["core_adapter_ready"])
        self.assertFalse(context["ordinary_goal_context_ready"])
        self.assertEqual(context["government_key"], "japan_feudal_government")
        self.assertEqual(context["adapter_family"], "tgp_japan_feudal")
        self.assertEqual(context["adapter_status"], "adapter_spec_ready_not_implemented")
        self.assertEqual(context["unavailable_reason"], "adapter_spec_ready_not_implemented")
        self.assertEqual(context["government_runtime_adapter"]["adapter"], government["adapter"])


if __name__ == "__main__":
    unittest.main()
