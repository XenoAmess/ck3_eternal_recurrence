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
from xar_autoplayer.vanilla_events.records_bp1_yearly import (  # noqa: E402
    PLAYER_SENTINEL,
    VANILLA_BP1_YEARLY_ANALYSIS,
    VANILLA_BP1_YEARLY_OBSERVATIONS,
    VANILLA_BP1_YEARLY_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.registry import (  # noqa: E402
    materialize_vanilla_timeline_contract,
    query_vanilla_event_knowledge_v1,
)
from xar_autoplayer.vanilla_events.source_index import (  # noqa: E402
    query_vanilla_event_source_provenance_v1,
)


EVENT_KEY = "bp1_yearly.1040"
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


class Bp1YearlyEventRecordTests(unittest.TestCase):
    def test_contract_binds_sparse_projection_and_terminal_refusal(self) -> None:
        contract = VANILLA_BP1_YEARLY_TIMELINE_CONTRACTS[EVENT_KEY]

        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)
        self.assertNotIn("date_raw", contract)
        self.assertEqual(contract["unique_character_scope_excludes"], {
            "new_friend": (PLAYER_SENTINEL,),
        })
        self.assertEqual(contract["saved_scope_name_sets"], (("new_friend",),))
        self.assertEqual(contract["saved_scope_count"], 1)
        self.assertEqual(contract["option_count"], 2)
        self.assertEqual(contract["snapshot_option_count"], 3)
        self.assertEqual(contract["native_option_indices"], (0, 2))
        self.assertEqual(contract["selected_option_number"], 3)
        self.assertEqual(contract["selected_native_option_index"], 2)

        materialized = materialize_vanilla_timeline_contract(contract, 32904)
        self.assertEqual(materialized["root_character_id"], 32904)
        self.assertEqual(
            materialized["unique_character_scope_excludes"],
            {"new_friend": (32904,)},
        )

    def test_analysis_freezes_source_route_and_cleanup(self) -> None:
        analysis = VANILLA_BP1_YEARLY_ANALYSIS[EVENT_KEY]

        self.assertEqual(analysis["definition_lines"], "2467-2845")
        self.assertEqual(analysis["on_yearly_pool_entry_line"], "3354")
        self.assertIn("twenty-year cooldown", analysis["frequency_boundary"])
        self.assertIn("seduce scheme", analysis["option_semantics"][1])
        self.assertIn("minus-thirty", analysis["option_semantics"][2])
        self.assertIn("is_naked", analysis["after_effect"])
        self.assertIsNone(analysis["follow_up_event"])
        for digest in analysis["source_sha256"].values():
            self.assertRegex(digest, SHA256_PATTERN)

    def test_r416_values_remain_observation_only(self) -> None:
        exemplar = VANILLA_BP1_YEARLY_OBSERVATIONS[EVENT_KEY]["exemplars"][0]
        contract_repr = repr(VANILLA_BP1_YEARLY_TIMELINE_CONTRACTS[EVENT_KEY])

        self.assertEqual(exemplar["run"], "R416")
        self.assertEqual(exemplar["red_classification"], "harness-route-red")
        self.assertFalse(exemplar["product_failure_proven"])
        self.assertEqual(exemplar["saved_scope_raw_types"], {"new_friend": 4})
        self.assertEqual(exemplar["rendered_native_option_indices"], [0, 2])
        self.assertFalse(exemplar["selection_attempted"])
        self.assertRegex(exemplar["artifact_sha256"], SHA256_PATTERN)
        for observation_only in (53804184, 1078, 32904, 50387675, 174656):
            self.assertNotIn(str(observation_only), contract_repr)

    def test_default_registry_runtime_and_evidence_share_record(self) -> None:
        self.assertIs(
            DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS[EVENT_KEY],
            VANILLA_BP1_YEARLY_TIMELINE_CONTRACTS[EVENT_KEY],
        )
        self.assertIs(
            DEFAULT_VANILLA_EVENT_ANALYSIS[EVENT_KEY],
            VANILLA_BP1_YEARLY_ANALYSIS[EVENT_KEY],
        )
        self.assertIs(
            DEFAULT_VANILLA_EVENT_OBSERVATIONS[EVENT_KEY],
            VANILLA_BP1_YEARLY_OBSERVATIONS[EVENT_KEY],
        )
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS[EVENT_KEY],
            VANILLA_BP1_YEARLY_TIMELINE_CONTRACTS[EVENT_KEY],
        )

        response = query_vanilla_event_knowledge_v1(EVENT_KEY)
        self.assertEqual(response["status"], "available")
        self.assertEqual(response["contract"]["native_option_indices"], [0, 2])
        source = query_vanilla_event_source_provenance_v1(EVENT_KEY)
        self.assertEqual(source["status"], "available")
        self.assertEqual(source["definition"]["line"], 2467)
        portable = query_vanilla_event_evidence_index_v1(EVENT_KEY)
        self.assertEqual(portable["status"], "available")
        self.assertEqual(
            {row["kind"] for row in portable["evidence"]},
            {"source_definition", "observation_artifact"},
        )
        json.dumps(response, allow_nan=False)

    def test_canonical_runtime_reload_rebinds_shared_record(self) -> None:
        script = (
            "import importlib,sys;"
            f"sys.path[:0]=[{str(ROOT / 'ck3_autonomous_player' / 'src')!r},"
            f"{str(ROOT / 'tools')!r}];"
            "import zg361_phase2_promotion_source_production_entry as entry;"
            "entry=importlib.reload(entry);"
            f"contract=entry.KNOWN_TIMELINE_INTERRUPTS[{EVENT_KEY!r}];"
            "assert contract['native_option_indices']==(0,2);"
            "assert contract['selected_option_number']==3;"
            "assert contract['selected_native_option_index']==2"
        )
        completed = subprocess.run(
            [sys.executable, "-c", script],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_r416_live_shape_passes_production_recovery_checks(self) -> None:
        contract = production._manager_recovery_contract(
            production.KNOWN_TIMELINE_INTERRUPTS[EVENT_KEY],
            player=32904,
            event_key=EVENT_KEY,
        )
        contract = production._timeline_contract_for_window(
            contract,
            starting_date=53783472,
            absolute_end_date=53958720,
        )
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": EVENT_KEY,
            "current_event_instance_id": 1078,
            "date_raw": 53804184,
            "root_scope": _character_scope("root", 32904)["scope"],
            "saved_scopes": [_character_scope("new_friend", 50387675)],
            "options": [
                {
                    "rendered_index": rendered,
                    "native_option_index": native,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for rendered, native in ((0, 0), (1, 2))
            ],
        }
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53804184,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 1078},
            context=context,
            event_key=EVENT_KEY,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)


if __name__ == "__main__":
    unittest.main()
