from __future__ import annotations

import json
import re
import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from xar_autoplayer.vanilla_events import (  # noqa: E402
    DEFAULT_VANILLA_EVENT_ANALYSIS,
    DEFAULT_VANILLA_EVENT_OBSERVATIONS,
    DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.records_pay_homage import (  # noqa: E402
    PLAYER_SENTINEL,
    VANILLA_PAY_HOMAGE_ANALYSIS,
    VANILLA_PAY_HOMAGE_OBSERVATIONS,
    VANILLA_PAY_HOMAGE_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.registry import (  # noqa: E402
    materialize_vanilla_timeline_contract,
    query_vanilla_event_knowledge_v1,
)
from xar_autoplayer.vanilla_events.portable_evidence import (  # noqa: E402
    query_vanilla_event_evidence_index_v1,
)
from xar_autoplayer.vanilla_events.source_index import (  # noqa: E402
    query_vanilla_event_source_provenance_v1,
)
import zg361_phase2_promotion_source_production_entry as production  # noqa: E402


EVENT_KEY = "pay_homage.0101"
SHA256_PATTERN = re.compile(r"^[0-9A-F]{64}$")


def _scope(name: str, type_key: str, character_id: int | None = None) -> dict:
    identity = (
        {
            "status": "available",
            "kind": "character",
            "character_id": character_id,
        }
        if character_id is not None
        else {
            "status": "unavailable",
            "reason": "generic_scope_payload_identity_not_closed",
        }
    )
    return {
        "name": name,
        "scope": {
            "status": "available",
            "type_key": type_key,
            "typed_identity": identity,
        },
    }


class PayHomageEventRecordTests(unittest.TestCase):
    def test_contract_is_portable_and_exact_for_observed_smooth_shape(self) -> None:
        contract = VANILLA_PAY_HOMAGE_TIMELINE_CONTRACTS[EVENT_KEY]

        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)
        self.assertNotIn("date_raw", contract)
        self.assertEqual(contract["character_scopes"], {
            "homage_liege": PLAYER_SENTINEL,
        })
        self.assertEqual(contract["unique_character_scope_excludes"], {
            "homage_vassal": (PLAYER_SENTINEL,),
        })
        self.assertEqual(contract["saved_scope_count"], 7)
        self.assertEqual(contract["option_count"], 1)
        self.assertEqual(contract["snapshot_option_count"], 3)
        self.assertEqual(contract["native_option_indices"], (0,))
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)
        self.assertNotIn("option_variants", contract)

    def test_materialization_binds_every_player_sentinel(self) -> None:
        source = VANILLA_PAY_HOMAGE_TIMELINE_CONTRACTS[EVENT_KEY]
        materialized = materialize_vanilla_timeline_contract(source, 32904)

        self.assertEqual(materialized["root_character_id"], 32904)
        self.assertEqual(materialized["character_scopes"], {
            "homage_liege": 32904,
        })
        self.assertEqual(materialized["unique_character_scope_excludes"], {
            "homage_vassal": (32904,),
        })
        self.assertEqual(source["root_character_id"], PLAYER_SENTINEL)

    def test_analysis_freezes_sources_and_safe_option_boundary(self) -> None:
        analysis = VANILLA_PAY_HOMAGE_ANALYSIS[EVENT_KEY]

        self.assertEqual(analysis["definition_lines"], "686-1052")
        self.assertEqual(analysis["decision_definition_lines"], "2-390")
        self.assertIn("travel plan", analysis["caller_semantics"])
        self.assertIn("two-year", analysis["frequency_boundary"])
        self.assertIn("sole legal option", analysis["safe_option_rationale"])
        self.assertEqual(analysis["safe_option_policy"], {
            "no_faux_pas": 0,
            "faux_pas": 1,
            "default_forbidden": 2,
        })
        for digest in analysis["source_sha256"].values():
            self.assertRegex(digest, SHA256_PATTERN)

    def test_r384_values_and_red_evidence_remain_observation_only(self) -> None:
        exemplar, = VANILLA_PAY_HOMAGE_OBSERVATIONS[EVENT_KEY]["exemplars"]
        contract_repr = repr(VANILLA_PAY_HOMAGE_TIMELINE_CONTRACTS[EVENT_KEY])

        self.assertEqual(exemplar["event_instance_id"], 1046)
        self.assertEqual(exemplar["date_raw"], 53590944)
        self.assertEqual(exemplar["saved_character_ids"], {
            "homage_liege": 32904,
            "homage_vassal": 50338971,
        })
        self.assertEqual(exemplar["snapshot_option_count"], 3)
        self.assertEqual(exemplar["rendered_native_option_indices"], [0])
        self.assertFalse(exemplar["selection_attempted"])
        self.assertFalse(exemplar["process_restart_required"])
        for field in (
            "artifact_sha256",
            "park_artifact_sha256",
            "driver_state_artifact_sha256",
        ):
            self.assertRegex(exemplar[field], SHA256_PATTERN)
        for observation_only in (1046, 53590944, 32904, 50338971, 38864, 125):
            self.assertNotIn(str(observation_only), contract_repr)

    def test_default_registry_mcp_and_runtime_share_canonical_record(self) -> None:
        self.assertEqual(len(DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS), 170)
        self.assertEqual(len(DEFAULT_VANILLA_EVENT_ANALYSIS), 170)
        self.assertIs(
            DEFAULT_VANILLA_EVENT_OBSERVATIONS[EVENT_KEY],
            VANILLA_PAY_HOMAGE_OBSERVATIONS[EVENT_KEY],
        )
        self.assertEqual(len(production.KNOWN_TIMELINE_INTERRUPTS), 310)
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS[EVENT_KEY],
            VANILLA_PAY_HOMAGE_TIMELINE_CONTRACTS[EVENT_KEY],
        )

        response = query_vanilla_event_knowledge_v1(EVENT_KEY)
        self.assertEqual(response["status"], "available")
        self.assertEqual(response["contract"]["root_character_id"], "$player")
        self.assertEqual(response["contract"]["native_option_indices"], [0])
        self.assertEqual(response["analysis"]["definition_lines"], "686-1052")
        self.assertEqual(
            response["observations"]["exemplars"][0]["event_instance_id"],
            1046,
        )
        source = query_vanilla_event_source_provenance_v1(EVENT_KEY)
        self.assertEqual(source["status"], "available")
        self.assertEqual(source["definition"]["line"], 686)
        portable = query_vanilla_event_evidence_index_v1(EVENT_KEY)
        self.assertEqual(portable["status"], "available")
        self.assertEqual(len(portable["evidence"]), 8)
        self.assertEqual(
            {row["kind"] for row in portable["evidence"]},
            {"source_definition", "observation_artifact"},
        )
        json.dumps(response, allow_nan=False)

    def test_r384_live_shape_passes_production_recovery_checks(self) -> None:
        contract = production._manager_recovery_contract(
            production.KNOWN_TIMELINE_INTERRUPTS[EVENT_KEY],
            player=32904,
            event_key=EVENT_KEY,
        )
        contract = production._timeline_contract_for_window(
            contract,
            starting_date=53584920,
        )
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": EVENT_KEY,
            "current_event_instance_id": 1046,
            "date_raw": 53590944,
            "root_scope": _scope("root", "character", 32904)["scope"],
            "saved_scopes": [
                _scope("pay_homage_submission", "boolean"),
                _scope("pay_homage_hook", "boolean"),
                _scope("pay_homage_contract", "boolean"),
                _scope("pay_homage_gold", "boolean"),
                _scope("homage_vassal", "character", 50338971),
                _scope("homage_liege", "character", 32904),
                _scope("opinion_of_petitioner", "value"),
            ],
            "options": [{
                "rendered_index": 0,
                "native_option_index": 0,
                "shown": True,
                "enabled": True,
                "fallback": False,
                "cancel": False,
            }],
        }
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53590944,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 1046},
            context=context,
            event_key=EVENT_KEY,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertTrue(checks["snapshot_option_count"])
        self.assertTrue(checks["scope:homage_liege"])
        self.assertTrue(checks["scope:homage_vassal:unique_third_party"])
        self.assertTrue(checks["saved_scope_names_exact"])
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)


if __name__ == "__main__":
    unittest.main()
