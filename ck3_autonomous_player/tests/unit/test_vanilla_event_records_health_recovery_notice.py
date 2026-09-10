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
    query_vanilla_event_knowledge_v1,
)
from xar_autoplayer.vanilla_events.source_index import (  # noqa: E402
    query_vanilla_event_source_provenance_v1,
)


EVENT_KEY = "health.2202"
SHA256_PATTERN = re.compile(r"^[0-9A-F]{64}$")


def _scope(
    name: str,
    type_key: str,
    *,
    character_id: int | None = None,
) -> dict[str, object]:
    if character_id is None:
        typed_identity: dict[str, object] = {
            "status": "unavailable",
            "reason": "generic_scope_payload_identity_not_closed",
        }
    else:
        typed_identity = {
            "status": "available",
            "kind": "character",
            "character_id": character_id,
        }
    return {
        "name": name,
        "scope": {
            "status": "available",
            "type_key": type_key,
            "typed_identity": typed_identity,
        },
    }


def _context() -> dict[str, object]:
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "window_match_count": 1,
        "event_definition_key": EVENT_KEY,
        "current_event_instance_id": 1091,
        "date_raw": 53905680,
        "root_scope": _scope("root", "character", character_id=32904)["scope"],
        "saved_scopes": [
            _scope("epidemic", "epidemic"),
            _scope("disease_type", "flag"),
            _scope("sick_character", "character", character_id=88187),
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


class HealthRecoveryNoticeEventRecordTests(unittest.TestCase):
    def test_contract_admits_exact_no_physician_variant(self) -> None:
        contract = MANAGER_HEALTH_TIMELINE_CONTRACTS[EVENT_KEY]
        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

        (variant,) = contract["scope_variants"]
        self.assertEqual(variant["scope_types"], {
            "epidemic": "epidemic",
            "disease_type": "flag",
            "sick_character": "character",
        })
        self.assertEqual(variant["saved_scope_count"], 3)
        self.assertEqual(variant["character_scope_differs_from"], {})
        self.assertEqual(
            variant["unique_character_scope_excludes"],
            {"sick_character": (PLAYER_SENTINEL,)},
        )

    def test_exact_source_review_confirms_sole_acknowledgement(self) -> None:
        analysis = VANILLA_HEALTH_ANALYSIS[EVENT_KEY]
        self.assertEqual(analysis["definition_lines"], "6333-6565")
        self.assertEqual(analysis["trigger_lines"], "6451-6453")
        self.assertEqual(analysis["recover_from_disease_effect_lines"], "694-887")
        self.assertIn("before removing", analysis["caller_semantics"])
        self.assertIn("sole shown and enabled", analysis["safe_option_rationale"])
        self.assertIsNone(analysis["after_effect"])
        self.assertIsNone(analysis["follow_up_event"])
        for digest in analysis["source_sha256"].values():
            self.assertRegex(digest, SHA256_PATTERN)

    def test_r416_red_and_legacy_binding_remain_observations(self) -> None:
        legacy, red = VANILLA_HEALTH_OBSERVATIONS[EVENT_KEY]["exemplars"]
        contract_repr = repr(MANAGER_HEALTH_TIMELINE_CONTRACTS[EVENT_KEY])

        self.assertEqual(legacy["run"], "legacy-migrated")
        self.assertEqual(red["run"], "R416-retry-11")
        self.assertEqual(red["snapshot_id"], "native:1545")
        self.assertEqual(red["saved_character_ids"], {"sick_character": 88187})
        self.assertEqual(red["saved_scope_raw_types"], {
            "epidemic": 50,
            "disease_type": 3,
            "sick_character": 4,
        })
        self.assertEqual(red["rendered_native_option_indices"], [0])
        self.assertFalse(red["selection_attempted"])
        self.assertRegex(red["artifact_sha256"], SHA256_PATTERN)
        for observation_only in (53905680, 1091, 32904, 88187, 174656):
            self.assertNotIn(str(observation_only), contract_repr)

    def test_live_shape_resolves_and_passes_production_checks(self) -> None:
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
        context = _context()
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53905680,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 1091},
            context=context,
            event_key=EVENT_KEY,
            contract=contract,
        )
        self.assertTrue(all(checks.values()), checks)
        resolved = production._interrupt_contract_for_context(context, contract)
        self.assertEqual(resolved["saved_scope_count"], 3)
        self.assertNotIn("physician", resolved["scope_types"])
        self.assertEqual(resolved["selected_native_option_index"], 0)

    def test_registry_source_and_portable_evidence_share_record(self) -> None:
        self.assertIs(
            DEFAULT_VANILLA_EVENT_ANALYSIS[EVENT_KEY],
            VANILLA_HEALTH_ANALYSIS[EVENT_KEY],
        )
        self.assertIs(
            DEFAULT_VANILLA_EVENT_OBSERVATIONS[EVENT_KEY],
            VANILLA_HEALTH_OBSERVATIONS[EVENT_KEY],
        )
        response = query_vanilla_event_knowledge_v1(EVENT_KEY)
        self.assertEqual(response["status"], "available")
        self.assertEqual(response["analysis"]["definition_lines"], "6333-6565")
        source = query_vanilla_event_source_provenance_v1(EVENT_KEY)
        self.assertEqual(source["status"], "available")
        self.assertEqual(source["definition"]["line"], 6333)
        portable = query_vanilla_event_evidence_index_v1(EVENT_KEY)
        self.assertEqual(portable["status"], "available")
        self.assertEqual(
            {row["kind"] for row in portable["evidence"]},
            {"source_definition", "observation_artifact"},
        )
        json.dumps(response, allow_nan=False)


if __name__ == "__main__":
    unittest.main()
