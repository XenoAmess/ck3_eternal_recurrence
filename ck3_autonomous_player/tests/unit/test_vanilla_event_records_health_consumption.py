from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
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


EVENT_KEY = "health.1006"
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


def _context(*, physician_id: int | None) -> dict[str, object]:
    scopes = [
        _scope("epidemic", "epidemic"),
        _scope("disease_type", "flag"),
    ]
    if physician_id is not None:
        scopes.append(_scope("physician", "character", character_id=physician_id))
    scopes.extend((
        _scope("sick_character", "character", character_id=32904),
        _scope("new_memory", "character_memory"),
    ))
    native_indices = (0, 6) if physician_id is None else (3, 4, 6)
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "window_match_count": 1,
        "event_definition_key": EVENT_KEY,
        "current_event_instance_id": 1084,
        "date_raw": 53864592,
        "root_scope": _scope("root", "character", character_id=32904)["scope"],
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
            for rendered, native in enumerate(native_indices)
        ],
    }


class HealthConsumptionEventRecordTests(unittest.TestCase):
    def test_contract_admits_two_coupled_source_projections(self) -> None:
        contract = MANAGER_HEALTH_TIMELINE_CONTRACTS[EVENT_KEY]

        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)
        self.assertNotIn("date_raw", contract)
        self.assertEqual(contract["native_option_indices"], (0, 6))
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)
        self.assertEqual(contract["saved_scope_count"], 4)
        self.assertEqual(contract["option_variants"][0]["native_option_indices"], (
            3, 4, 6,
        ))
        self.assertEqual(
            contract["option_variants"][0]["selected_native_option_index"], 3
        )
        self.assertEqual(contract["scope_variants"][0]["saved_scope_count"], 5)
        self.assertEqual(
            contract["scope_variants"][0]["saved_scope_names"],
            ("epidemic", "disease_type", "physician", "sick_character", "new_memory"),
        )

        materialized = materialize_vanilla_timeline_contract(contract, 32904)
        self.assertEqual(materialized["character_scopes"], {
            "sick_character": 32904,
        })
        self.assertEqual(
            materialized["scope_variants"][0]["unique_character_scope_excludes"],
            {"physician": (32904,)},
        )

    def test_analysis_freezes_disease_and_treatment_order(self) -> None:
        analysis = VANILLA_HEALTH_ANALYSIS[EVENT_KEY]

        self.assertEqual(analysis["definition_lines"], "2135-2334")
        self.assertIn("before presenting", analysis["immediate_effect"])
        self.assertIn("schedules health.3001", analysis["option_semantics"][0])
        self.assertIn("without treatment", analysis["option_semantics"][6])
        self.assertIn("twenty-seven days", analysis["safe_option_rationale"])
        self.assertIsNone(analysis["after_effect"])
        for digest in analysis["source_sha256"].values():
            self.assertRegex(digest, SHA256_PATTERN)

    def test_r416_shape_green_and_r97_outcome_remain_observations(self) -> None:
        r97, r416, r416_green = VANILLA_HEALTH_OBSERVATIONS[EVENT_KEY][
            "exemplars"
        ]
        contract_repr = repr(MANAGER_HEALTH_TIMELINE_CONTRACTS[EVENT_KEY])

        self.assertEqual(r97["rendered_native_option_indices"], [3, 4, 6])
        self.assertEqual(r97["selected_native_option_index"], 6)
        self.assertEqual(r97["downstream_played_owner_death_after_rough_days"], 27)
        self.assertEqual(r416["saved_character_ids"], {"sick_character": 32904})
        self.assertEqual(r416["rendered_native_option_indices"], [0, 6])
        self.assertFalse(r416["selection_attempted"])
        self.assertRegex(r416["artifact_sha256"], SHA256_PATTERN)
        self.assertEqual(r416_green["event_instance_id"], 1084)
        self.assertEqual(r416_green["selected_native_option_index"], 0)
        self.assertEqual(r416_green["starting_snapshot_id"], "native:1026")
        self.assertEqual(r416_green["ending_snapshot_id"], "native:1027")
        self.assertTrue(r416_green["postcondition_verified"])
        self.assertRegex(r416_green["artifact_sha256"], SHA256_PATTERN)
        for observation_only in (53168904, 53864592, 1084, 56656, 174656):
            self.assertNotIn(str(observation_only), contract_repr)

    def test_both_observed_shapes_pass_production_checks(self) -> None:
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
        for physician_id in (None, 79104):
            with self.subTest(physician_id=physician_id):
                context = _context(physician_id=physician_id)
                checks = production._known_interrupt_checks(
                    snapshot={
                        "date_raw": 53864592,
                        "active_event": {"option_count": 7},
                    },
                    event={"event_instance_id": 1084},
                    context=context,
                    event_key=EVENT_KEY,
                    contract=contract,
                )
                self.assertTrue(all(checks.values()), checks)
                resolved = production._interrupt_contract_for_context(
                    context, contract
                )
                expected_native = 0 if physician_id is None else 3
                self.assertEqual(
                    resolved["selected_native_option_index"], expected_native
                )

    def test_registry_runtime_source_and_evidence_share_reviewed_record(self) -> None:
        self.assertIs(
            DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS[EVENT_KEY],
            MANAGER_HEALTH_TIMELINE_CONTRACTS[EVENT_KEY],
        )
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
        self.assertEqual(response["contract"]["native_option_indices"], [0, 6])
        source = query_vanilla_event_source_provenance_v1(EVENT_KEY)
        self.assertEqual(source["status"], "available")
        self.assertEqual(source["definition"]["line"], 2135)
        portable = query_vanilla_event_evidence_index_v1(EVENT_KEY)
        self.assertEqual(portable["status"], "available")
        self.assertEqual(
            {row["kind"] for row in portable["evidence"]},
            {"source_definition", "observation_artifact"},
        )
        json.dumps(response, allow_nan=False)

    def test_canonical_runtime_reload_uses_no_physician_route(self) -> None:
        script = (
            "import importlib,sys;"
            f"sys.path[:0]=[{str(ROOT / 'ck3_autonomous_player' / 'src')!r},"
            f"{str(ROOT / 'tools')!r}];"
            "import zg361_phase2_promotion_source_production_entry as entry;"
            "entry=importlib.reload(entry);"
            f"contract=entry.KNOWN_TIMELINE_INTERRUPTS[{EVENT_KEY!r}];"
            "assert contract['native_option_indices']==(0,6);"
            "assert contract['selected_option_number']==1;"
            "assert contract['selected_native_option_index']==0"
        )
        completed = subprocess.run(
            [sys.executable, "-c", script],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
