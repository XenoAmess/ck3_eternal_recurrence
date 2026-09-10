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
)
from xar_autoplayer.vanilla_events.portable_evidence import (  # noqa: E402
    query_vanilla_event_evidence_index_v1,
)
from xar_autoplayer.vanilla_events.records_health import (  # noqa: E402
    VANILLA_HEALTH_ANALYSIS,
    VANILLA_HEALTH_OBSERVATIONS,
)
from xar_autoplayer.vanilla_events.records_manager_a import (  # noqa: E402
    MANAGER_HEALTH_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.registry import (  # noqa: E402
    PLAYER_SENTINEL,
    materialize_vanilla_timeline_contract,
    query_vanilla_event_knowledge_v1,
)
from xar_autoplayer.vanilla_events.source_index import (  # noqa: E402
    query_vanilla_event_source_provenance_v1,
)


EVENT_KEY = "health.3001"
SHA256_PATTERN = re.compile(r"^[0-9A-F]{64}$")


def _scope(
    name: str,
    type_key: str,
    *,
    character_id: int | None = None,
) -> dict[str, object]:
    value: dict[str, object] = {
        "status": "available",
        "type_key": type_key,
    }
    if character_id is not None:
        value["typed_identity"] = {
            "status": "available",
            "kind": "character",
            "character_id": character_id,
        }
    return {"name": name, "scope": value}


def _context(*, inherited_diagnosis_scopes: bool) -> dict[str, object]:
    scopes = []
    if inherited_diagnosis_scopes:
        scopes.extend((
            _scope("epidemic", "epidemic"),
            _scope("disease_type", "flag"),
        ))
    scopes.append(_scope("sick_character", "character", character_id=32904))
    if inherited_diagnosis_scopes:
        scopes.append(_scope("new_memory", "character_memory"))
    scopes.extend((
        _scope("high_skill_option", "character", character_id=33648496),
        _scope("low_skill_option", "character", character_id=16889335),
    ))
    if not inherited_diagnosis_scopes:
        scopes.insert(1, _scope("disease_type", "flag"))
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "window_match_count": 1,
        "event_definition_key": EVENT_KEY,
        "current_event_instance_id": 1085,
        "date_raw": 53864784,
        "root_scope": _scope(
            "root", "character", character_id=32904
        )["scope"],
        "saved_scopes": scopes,
        "options": [
            {
                "rendered_index": rendered,
                "native_option_index": native,
                "shown": True,
                "enabled": True,
                "fallback": False,
                "cancel": False,
            }
            for rendered, native in enumerate((1, 2, 4))
        ],
    }


class HealthPhysicianSearchEventRecordTests(unittest.TestCase):
    def test_contract_admits_base_and_inherited_scope_shapes(self) -> None:
        contract = MANAGER_HEALTH_TIMELINE_CONTRACTS[EVENT_KEY]

        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)
        self.assertEqual(contract["character_scopes"], {
            "sick_character": PLAYER_SENTINEL,
        })
        self.assertEqual(contract["native_option_indices"], (1, 2, 4))
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)
        self.assertEqual(contract["saved_scope_count"], 4)
        inherited = contract["scope_variants"][0]
        self.assertEqual(inherited["saved_scope_count"], 6)
        self.assertEqual(inherited["saved_scope_names"], (
            "epidemic",
            "disease_type",
            "sick_character",
            "new_memory",
            "high_skill_option",
            "low_skill_option",
        ))

        materialized = materialize_vanilla_timeline_contract(contract, 32904)
        self.assertEqual(materialized["character_scopes"], {
            "sick_character": 32904,
        })

    def test_exact_source_review_covers_candidate_search_and_hiring(self) -> None:
        analysis = VANILLA_HEALTH_ANALYSIS[EVENT_KEY]

        self.assertEqual(analysis["definition_lines"], "6667-7276")
        self.assertIn("high- and low-skill", analysis["immediate_effect"])
        self.assertIn("court physician", analysis["option_semantics"][1])
        self.assertIn("health.3101", analysis["follow_up_event"])
        self.assertIn("epidemic and new_memory", analysis["scope_boundary"])
        for digest in analysis["source_sha256"].values():
            self.assertRegex(digest, SHA256_PATTERN)

    def test_r197_and_r416_observations_remain_outside_contract(self) -> None:
        r197, r416 = VANILLA_HEALTH_OBSERVATIONS[EVENT_KEY]["exemplars"]
        contract_repr = repr(MANAGER_HEALTH_TIMELINE_CONTRACTS[EVENT_KEY])

        self.assertEqual(r197["rendered_native_option_indices"], [1, 2, 4])
        self.assertEqual(r197["selected_native_option_index"], 1)
        self.assertEqual(r416["event_instance_id"], 1085)
        self.assertEqual(r416["saved_character_ids"], {
            "sick_character": 32904,
            "high_skill_option": 33648496,
            "low_skill_option": 16889335,
        })
        self.assertEqual(r416["rendered_native_option_indices"], [1, 2, 4])
        self.assertFalse(r416["selection_attempted"])
        self.assertRegex(r416["artifact_sha256"], SHA256_PATTERN)
        for observation_only in (
            53176968,
            53864784,
            1085,
            49718,
            36369,
            33648496,
            16889335,
            174656,
        ):
            self.assertNotIn(str(observation_only), contract_repr)

    def test_both_source_shapes_pass_production_checks(self) -> None:
        base = production._manager_recovery_contract(
            production.KNOWN_TIMELINE_INTERRUPTS[EVENT_KEY],
            player=32904,
            event_key=EVENT_KEY,
        )
        contract = production._timeline_contract_for_window(
            base,
            starting_date=53783472,
            absolute_end_date=53958720,
        )
        for inherited in (False, True):
            with self.subTest(inherited_diagnosis_scopes=inherited):
                context = _context(inherited_diagnosis_scopes=inherited)
                checks = production._known_interrupt_checks(
                    snapshot={
                        "date_raw": 53864784,
                        "active_event": {"option_count": 5},
                    },
                    event={"event_instance_id": 1085},
                    context=context,
                    event_key=EVENT_KEY,
                    contract=contract,
                )
                self.assertTrue(all(checks.values()), checks)
                resolved = production._interrupt_contract_for_context(
                    context, contract
                )
                self.assertEqual(resolved["saved_scope_count"], 6 if inherited else 4)
                self.assertEqual(resolved["selected_option_number"], 2)
                self.assertEqual(resolved["selected_native_option_index"], 1)

    def test_registry_runtime_source_and_evidence_share_reviewed_record(self) -> None:
        self.assertIs(DEFAULT_VANILLA_EVENT_ANALYSIS[EVENT_KEY], (
            VANILLA_HEALTH_ANALYSIS[EVENT_KEY]
        ))
        self.assertIs(DEFAULT_VANILLA_EVENT_OBSERVATIONS[EVENT_KEY], (
            VANILLA_HEALTH_OBSERVATIONS[EVENT_KEY]
        ))
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS[EVENT_KEY],
            MANAGER_HEALTH_TIMELINE_CONTRACTS[EVENT_KEY],
        )

        response = query_vanilla_event_knowledge_v1(EVENT_KEY)
        self.assertEqual(response["status"], "available")
        self.assertEqual(response["contract"]["native_option_indices"], [1, 2, 4])
        source = query_vanilla_event_source_provenance_v1(EVENT_KEY)
        self.assertEqual(source["status"], "available")
        self.assertEqual(source["definition"]["line"], 6667)
        portable = query_vanilla_event_evidence_index_v1(EVENT_KEY)
        self.assertEqual(portable["status"], "available")
        self.assertEqual(
            {row["kind"] for row in portable["evidence"]},
            {"source_definition", "observation_artifact"},
        )
        json.dumps(response, allow_nan=False)


if __name__ == "__main__":
    unittest.main()
