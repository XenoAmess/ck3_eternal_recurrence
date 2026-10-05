from __future__ import annotations

import json
from pathlib import Path
import runpy
import unittest

from xar_autoplayer.vanilla_events.registry import query_vanilla_event_knowledge_v1


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
FIXTURE = Path(__file__).parent / "fixtures" / "rite_growth_event29_nine_scope_12003.json"


class RiteGrowthObservedScopeVariant12003Tests(unittest.TestCase):
    def test_actual_event29_nine_scope_replay_keeps_native0_and_opaque_payloads(self) -> None:
        frozen = FIXTURE.read_bytes()
        bundle = json.loads(frozen)
        context = bundle["context"]
        scopes = {row["name"]: row["scope"] for row in context["saved_scopes"]}
        self.assertEqual(context["current_event_instance_id"], 29)
        self.assertEqual(context["snapshot_revision"], 18)
        self.assertEqual(context["date_raw"], 53265288)
        self.assertEqual(len(scopes), 9)
        self.assertEqual(scopes["founder"]["typed_identity"]["character_id"], 38699)
        self.assertEqual(scopes["convert_ruler"]["typed_identity"]["character_id"], 34092)
        self.assertEqual(scopes["founder_clerical_title"]["typed_identity"]["title_id"], 18382)
        for name in ("origin_faith", "source_rite", "new_rite", "differing_tenet", "rite_growth_target_share"):
            self.assertEqual(scopes[name]["typed_identity"], {
                "status": "unavailable", "reason": "generic_scope_payload_identity_not_closed",
            })
        self.assertFalse(context["readiness"]["semantic_decision_ready"])
        self.assertNotIn("snapshot", bundle)
        self.assertEqual(bundle["frozen_sources"]["authored_option_count"]["native_revision"], 17)
        self.assertFalse(bundle["frozen_sources"]["same_query_binding"])

        # Existing offline tool invokes the production policy and registry.
        # No bridge, gameplay driver or command consumer is instantiated.
        replay = runpy.run_path(str(REPOSITORY_ROOT / "tools" / "replay_vanilla_event_research.py"))
        report = replay["replay_bytes"](frozen)
        self.assertEqual(report["policy"]["status"], "recommended")
        self.assertEqual(report["policy"]["selected_native_option_index"], 0)
        self.assertEqual(report["policy"]["selected_option_number"], 1)
        self.assertEqual(report["policy"]["failed_checks"], [])
        self.assertFalse(report["game_started"])
        self.assertEqual(report["gameplay_commands_submitted"], 0)
        self.assertFalse(report["new_live_evidence"])
        self.assertEqual(report["material_plan"]["reason"], "snapshot_not_supplied")

        # The original observed seven-scope contract remains the base;
        # this check does not rerun its previously qualified replay.
        contract = query_vanilla_event_knowledge_v1("rite_growth.0010", "1.20.0.3")["contract"]
        self.assertEqual(contract["saved_scope_count"], 7)
        self.assertEqual(contract["scope_types"]["differing_doctrine"], "doctrine")
        self.assertEqual(len(contract["scope_variants"]), 1)
        self.assertEqual(contract["scope_variants"][0]["saved_scope_count"], 9)
