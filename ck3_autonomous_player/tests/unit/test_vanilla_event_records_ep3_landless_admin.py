from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import unittest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))
sys.path.insert(0, str(ROOT / "tools"))

import zg361_phase2_promotion_source_production_entry as production  # noqa: E402
from xar_autoplayer.vanilla_events import (  # noqa: E402
    DEFAULT_VANILLA_EVENT_ANALYSIS,
    DEFAULT_VANILLA_EVENT_OBSERVATIONS,
    DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.records_ep3_landless_admin import (  # noqa: E402
    PLAYER_SENTINEL,
    VANILLA_EP3_LANDLESS_ADMIN_ANALYSIS,
    VANILLA_EP3_LANDLESS_ADMIN_OBSERVATIONS,
    VANILLA_EP3_LANDLESS_ADMIN_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.registry import (  # noqa: E402
    materialize_vanilla_timeline_contract,
    query_vanilla_event_knowledge_v1,
)


EVENT_KEY = "ep3_landless_admin.1000"
SHA256_PATTERN = re.compile(r"^[0-9A-F]{64}$")


def _character_scope(name: str, character_id: int) -> dict[str, object]:
    return {
        "name": name,
        "scope": {
            "status": "available",
            "type_key": "character",
            "typed_identity": {
                "status": "available",
                "kind": "character",
                "character_id": character_id,
            },
        },
    }


class Ep3LandlessAdminEventRecordTests(unittest.TestCase):
    def test_contract_is_portable_and_accepts_only_observed_shape(self) -> None:
        contract = VANILLA_EP3_LANDLESS_ADMIN_TIMELINE_CONTRACTS[EVENT_KEY]

        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)
        self.assertNotIn("date_raw", contract)
        self.assertNotIn("max_occurrences", contract)
        self.assertEqual(contract["character_scopes"], {})
        self.assertEqual(
            contract["unique_character_scope_excludes"],
            {"proposed_councillor": (PLAYER_SENTINEL,)},
        )
        self.assertEqual(
            contract["scope_types"],
            {"proposed_councillor": "character"},
        )
        self.assertEqual(
            contract["saved_scope_name_sets"],
            (("proposed_councillor",),),
        )
        self.assertEqual(contract["saved_scope_count"], 1)
        self.assertEqual(contract["native_option_indices"], (0, 1, 2))
        self.assertEqual(contract["selected_option_number"], 3)
        self.assertEqual(contract["selected_native_option_index"], 2)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )

    def test_materializer_binds_player_exclusion_without_mutation(self) -> None:
        contract = VANILLA_EP3_LANDLESS_ADMIN_TIMELINE_CONTRACTS[EVENT_KEY]
        materialized = materialize_vanilla_timeline_contract(contract, 47001)

        self.assertEqual(materialized["root_character_id"], 47001)
        self.assertEqual(
            materialized["unique_character_scope_excludes"],
            {"proposed_councillor": (47001,)},
        )
        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)
        self.assertEqual(
            contract["unique_character_scope_excludes"],
            {"proposed_councillor": (PLAYER_SENTINEL,)},
        )

    def test_exact_analysis_freezes_source_chain_and_safe_boundary(self) -> None:
        analysis = VANILLA_EP3_LANDLESS_ADMIN_ANALYSIS[EVENT_KEY]

        self.assertEqual(analysis["definition_lines"], "17-212")
        self.assertEqual(analysis["trigger_lines"], "41-44")
        self.assertEqual(analysis["immediate_lines"], "59-88")
        self.assertEqual(analysis["option_lines"], "90-211")
        self.assertIn("never both", analysis["caller_semantics"])
        self.assertIn("five-year cooldown", analysis["frequency_boundary"])
        self.assertIn("exactly proposed_councillor", analysis["scope_boundary"])
        self.assertIn("non-religious", analysis["domain_boundary"])
        self.assertIn("stochastic duel", analysis["safe_option_rationale"])
        self.assertEqual(len(analysis["source_sha256"]), 5)
        for digest in analysis["source_sha256"].values():
            self.assertRegex(digest, SHA256_PATTERN)

    def test_r375_red_is_immutable_and_does_not_leak_into_contract(self) -> None:
        exemplar = VANILLA_EP3_LANDLESS_ADMIN_OBSERVATIONS[EVENT_KEY][
            "exemplars"
        ][0]
        contract_repr = repr(
            VANILLA_EP3_LANDLESS_ADMIN_TIMELINE_CONTRACTS[EVENT_KEY]
        )

        self.assertEqual(exemplar["run"], "R375")
        self.assertEqual(exemplar["kind"], "pre-selection-live-red")
        self.assertTrue(exemplar["artifact"].endswith("-red-freeze.json"))
        self.assertEqual(exemplar["event_instance_id"], 1062)
        self.assertEqual(exemplar["date_raw"], 53619912)
        self.assertEqual(
            exemplar["saved_scope_raw_types"],
            {"proposed_councillor": 4},
        )
        self.assertEqual(exemplar["rendered_native_option_indices"], [0, 1, 2])
        self.assertFalse(exemplar["selection_attempted"])
        self.assertFalse(exemplar["process_restart_required"])
        for field in ("artifact_sha256", "park_artifact_sha256"):
            self.assertRegex(exemplar[field], SHA256_PATTERN)
        for observation_only in (
            53619912,
            1062,
            32904,
            33643335,
            180544,
            "native:720",
        ):
            self.assertNotIn(str(observation_only), contract_repr)

    def test_registry_mcp_and_production_share_canonical_record(self) -> None:
        self.assertIs(
            DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS[EVENT_KEY],
            VANILLA_EP3_LANDLESS_ADMIN_TIMELINE_CONTRACTS[EVENT_KEY],
        )
        self.assertIs(
            DEFAULT_VANILLA_EVENT_ANALYSIS[EVENT_KEY],
            VANILLA_EP3_LANDLESS_ADMIN_ANALYSIS[EVENT_KEY],
        )
        self.assertIs(
            DEFAULT_VANILLA_EVENT_OBSERVATIONS[EVENT_KEY],
            VANILLA_EP3_LANDLESS_ADMIN_OBSERVATIONS[EVENT_KEY],
        )
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS[EVENT_KEY],
            VANILLA_EP3_LANDLESS_ADMIN_TIMELINE_CONTRACTS[EVENT_KEY],
        )

        response = query_vanilla_event_knowledge_v1(EVENT_KEY)
        self.assertEqual(response["status"], "available")
        self.assertEqual(response["contract"]["root_character_id"], "$player")
        self.assertEqual(response["contract"]["native_option_indices"], [0, 1, 2])
        self.assertEqual(response["analysis"]["definition_lines"], "17-212")
        self.assertEqual(
            response["observations"]["exemplars"][0]["artifact_sha256"],
            "F74447FE01DDB9BC890C757578DBA477373167EA0DA862BB987D26A61904DFA1",
        )
        json.dumps(response, allow_nan=False)

    def test_current_live_shape_passes_production_recovery_checks(self) -> None:
        contract = production._manager_recovery_contract(
            production.KNOWN_TIMELINE_INTERRUPTS[EVENT_KEY],
            player=32904,
            event_key=EVENT_KEY,
        )
        contract = production._timeline_contract_for_window(
            contract,
            starting_date=53600000,
        )
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": EVENT_KEY,
            "current_event_instance_id": 1062,
            "date_raw": 53619912,
            "root_scope": _character_scope("root", 32904)["scope"],
            "saved_scopes": [
                _character_scope("proposed_councillor", 33643335),
            ],
            "options": [
                {
                    "rendered_index": index,
                    "native_option_index": index,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for index in range(3)
            ],
        }
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53619912,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 1062},
            context=context,
            event_key=EVENT_KEY,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 3)
        self.assertEqual(contract["selected_native_option_index"], 2)


if __name__ == "__main__":
    unittest.main()
