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
from xar_autoplayer.vanilla_events.portable_evidence import (  # noqa: E402
    query_vanilla_event_evidence_index_v1,
)
from xar_autoplayer.vanilla_events.records_yearly import (  # noqa: E402
    VANILLA_YEARLY_ANALYSIS,
    VANILLA_YEARLY_OBSERVATIONS,
    VANILLA_YEARLY_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.registry import (  # noqa: E402
    PLAYER_SENTINEL,
    query_vanilla_event_knowledge_v1,
)
from xar_autoplayer.vanilla_events.source_index import (  # noqa: E402
    query_vanilla_event_source_provenance_v1,
)


EVENT_KEY = "yearly.1030"
SHA256_PATTERN = re.compile(r"^[0-9A-F]{64}$")


def _scope(
    name: str,
    type_key: str,
    *,
    character_id: int | None = None,
) -> dict[str, object]:
    if character_id is None:
        identity: dict[str, object] = {
            "status": "unavailable",
            "reason": "generic_scope_payload_identity_not_closed",
        }
    else:
        identity = {
            "status": "available",
            "kind": "character",
            "character_id": character_id,
        }
    return {
        "name": name,
        "scope": {
            "status": "available",
            "type_key": type_key,
            "typed_identity": identity,
        },
    }


def _context() -> dict[str, object]:
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "window_match_count": 1,
        "event_definition_key": EVENT_KEY,
        "current_event_instance_id": 1096,
        "date_raw": 53943096,
        "root_scope": _scope(
            "root", "character", character_id=32904
        )["scope"],
        "saved_scopes": [
            _scope("secret_character", "character", character_id=50407232),
            _scope("secret", "secret"),
            _scope("hooked", "character", character_id=88187),
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


class YearlyHookForSecretEventRecordTests(unittest.TestCase):
    def test_contract_binds_exact_scope_shape_and_peaceful_exchange(self) -> None:
        contract = VANILLA_YEARLY_TIMELINE_CONTRACTS[EVENT_KEY]

        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)
        self.assertEqual(contract["saved_scope_name_sets"], (
            ("secret_character", "secret", "hooked"),
        ))
        self.assertEqual(contract["scope_types"], {
            "secret_character": "character",
            "secret": "secret",
            "hooked": "character",
        })
        self.assertEqual(contract["saved_scope_count"], 3)
        self.assertEqual(contract["native_option_indices"], (0, 1, 2))
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

    def test_exact_source_review_bounds_trade_and_coercion(self) -> None:
        analysis = VANILLA_YEARLY_ANALYSIS[EVENT_KEY]

        self.assertEqual(analysis["definition_lines"], "2927-3277")
        self.assertIn("two thousand", analysis["frequency_boundary"])
        self.assertIn("thirty-three-percent wound roll", analysis["option_semantics"][1])
        self.assertIn("surrendering the existing hook", analysis["safe_option_rationale"])
        self.assertIsNone(analysis["follow_up_event"])
        for digest in analysis["source_sha256"].values():
            self.assertRegex(digest, SHA256_PATTERN)

    def test_r418_red_and_hot_recovery_green_remain_observation_only(self) -> None:
        red, green = VANILLA_YEARLY_OBSERVATIONS[EVENT_KEY]["exemplars"]
        contract_repr = repr(VANILLA_YEARLY_TIMELINE_CONTRACTS[EVENT_KEY])

        self.assertEqual(red["run"], "R418-retry-03")
        self.assertEqual(red["snapshot_id"], "native:456")
        self.assertEqual(red["saved_character_ids"], {
            "secret_character": 50407232,
            "hooked": 88187,
        })
        self.assertEqual(red["saved_scope_raw_types"], {
            "secret_character": 4,
            "secret": 7,
            "hooked": 4,
        })
        self.assertEqual(red["rendered_native_option_indices"], [0, 1, 2])
        self.assertFalse(red["selection_attempted"])
        self.assertRegex(red["artifact_sha256"], SHA256_PATTERN)
        self.assertEqual(green["run"], "R418-attempt-04")
        self.assertEqual(green["selected_option_number"], 1)
        self.assertEqual(green["selected_native_option_index"], 0)
        self.assertEqual(green["starting_snapshot_id"], "native:457")
        self.assertEqual(green["ending_snapshot_id"], "native:458")
        self.assertTrue(green["postcondition_verified"])
        self.assertRegex(green["artifact_sha256"], SHA256_PATTERN)
        for observation_only in (53943096, 1096, 32904, 50407232, 88187, 204536):
            self.assertNotIn(str(observation_only), contract_repr)

    def test_live_shape_resolves_and_passes_production_checks(self) -> None:
        base = production._manager_recovery_contract(
            production.KNOWN_TIMELINE_INTERRUPTS[EVENT_KEY],
            player=32904,
            event_key=EVENT_KEY,
        )
        contract = production._timeline_contract_for_window(
            base,
            starting_date=53915424,
            absolute_end_date=54150240,
        )
        context = _context()
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53943096,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 1096},
            context=context,
            event_key=EVENT_KEY,
            contract=contract,
        )
        self.assertTrue(all(checks.values()), checks)
        resolved = production._interrupt_contract_for_context(context, contract)
        self.assertEqual(resolved["saved_scope_count"], 3)
        self.assertEqual(resolved["selected_native_option_index"], 0)

    def test_registry_source_and_portable_evidence_share_record(self) -> None:
        self.assertIs(
            DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS[EVENT_KEY],
            VANILLA_YEARLY_TIMELINE_CONTRACTS[EVENT_KEY],
        )
        self.assertIs(
            DEFAULT_VANILLA_EVENT_ANALYSIS[EVENT_KEY],
            VANILLA_YEARLY_ANALYSIS[EVENT_KEY],
        )
        self.assertIs(
            DEFAULT_VANILLA_EVENT_OBSERVATIONS[EVENT_KEY],
            VANILLA_YEARLY_OBSERVATIONS[EVENT_KEY],
        )
        response = query_vanilla_event_knowledge_v1(EVENT_KEY)
        self.assertEqual(response["status"], "available")
        self.assertEqual(response["analysis"]["definition_lines"], "2927-3277")
        source = query_vanilla_event_source_provenance_v1(EVENT_KEY)
        self.assertEqual(source["status"], "available")
        self.assertEqual(source["definition"]["line"], 2927)
        portable = query_vanilla_event_evidence_index_v1(EVENT_KEY)
        self.assertEqual(portable["status"], "available")
        self.assertEqual(
            {row["kind"] for row in portable["evidence"]},
            {"source_definition", "observation_artifact"},
        )
        json.dumps(response, allow_nan=False)


if __name__ == "__main__":
    unittest.main()
