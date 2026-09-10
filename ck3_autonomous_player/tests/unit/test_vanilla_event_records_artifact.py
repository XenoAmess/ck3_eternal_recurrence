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
from xar_autoplayer.vanilla_events.records_artifact import (  # noqa: E402
    PLAYER_SENTINEL,
    VANILLA_ARTIFACT_ANALYSIS,
    VANILLA_ARTIFACT_OBSERVATIONS,
    VANILLA_ARTIFACT_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.registry import (  # noqa: E402
    materialize_vanilla_timeline_contract,
    query_vanilla_event_knowledge_v1,
)
from xar_autoplayer.vanilla_events.source_index import (  # noqa: E402
    query_vanilla_event_source_provenance_v1,
)


EVENT_KEY = "artifact.4040"
SHA256_PATTERN = re.compile(r"^[0-9A-F]{64}$")


def _scope(
    name: str,
    type_key: str,
    *,
    character_id: int | None = None,
) -> dict[str, object]:
    typed_identity: dict[str, object] = {
        "status": "unavailable",
        "reason": "generic_scope_payload_identity_not_closed",
    }
    if character_id is not None:
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


class ArtifactEventRecordTests(unittest.TestCase):
    def test_contract_binds_observed_scopes_and_accepts_upgrade(self) -> None:
        contract = VANILLA_ARTIFACT_TIMELINE_CONTRACTS[EVENT_KEY]

        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)
        self.assertNotIn("date_raw", contract)
        self.assertEqual(
            contract["unique_character_scope_excludes"],
            {"helpful": (PLAYER_SENTINEL,)},
        )
        self.assertEqual(contract["scope_types"], {
            "this_artifact": "artifact",
            "helpful": "character",
        })
        self.assertEqual(
            contract["saved_scope_name_sets"],
            (("this_artifact", "helpful"),),
        )
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

        materialized = materialize_vanilla_timeline_contract(contract, 32904)
        self.assertEqual(materialized["root_character_id"], 32904)
        self.assertEqual(
            materialized["unique_character_scope_excludes"],
            {"helpful": (32904,)},
        )

    def test_analysis_freezes_source_cost_and_upgrade(self) -> None:
        analysis = VANILLA_ARTIFACT_ANALYSIS[EVENT_KEY]

        self.assertEqual(analysis["definition_lines"], "3066-3292")
        self.assertEqual(analysis["on_yearly_pool_entry_line"], "3275")
        self.assertIn("thirty-year cooldown", analysis["frequency_boundary"])
        self.assertIn("favor hook", analysis["option_semantics"][0])
        self.assertIn("always gains", analysis["option_semantics"][0])
        self.assertEqual(
            analysis["option_semantics"][1],
            "refuses the offer and has no authored effect",
        )
        self.assertIsNone(analysis["after_effect"])
        self.assertIsNone(analysis["follow_up_event"])
        for digest in analysis["source_sha256"].values():
            self.assertRegex(digest, SHA256_PATTERN)

    def test_r416_values_remain_observation_only(self) -> None:
        exemplar = VANILLA_ARTIFACT_OBSERVATIONS[EVENT_KEY]["exemplars"][0]
        contract_repr = repr(VANILLA_ARTIFACT_TIMELINE_CONTRACTS[EVENT_KEY])

        self.assertEqual(exemplar["artifact_sha256"], (
            "CFD57E5C381D35EE6E1DE166D9FF656A1E6D6F4FC7D3194BCC74393EB3B4EE6A"
        ))
        self.assertEqual(exemplar["saved_character_ids"], {"helpful": 79104})
        self.assertEqual(exemplar["saved_scope_raw_types"], {
            "this_artifact": 31,
            "helpful": 4,
        })
        self.assertEqual(exemplar["rendered_native_option_indices"], [0, 1])
        self.assertFalse(exemplar["selection_attempted"])
        for observation_only in (53832072, 1081, 32904, 79104, 174656):
            self.assertNotIn(str(observation_only), contract_repr)

    def test_registry_runtime_source_and_evidence_share_record(self) -> None:
        self.assertIs(
            DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS[EVENT_KEY],
            VANILLA_ARTIFACT_TIMELINE_CONTRACTS[EVENT_KEY],
        )
        self.assertIs(
            DEFAULT_VANILLA_EVENT_ANALYSIS[EVENT_KEY],
            VANILLA_ARTIFACT_ANALYSIS[EVENT_KEY],
        )
        self.assertIs(
            DEFAULT_VANILLA_EVENT_OBSERVATIONS[EVENT_KEY],
            VANILLA_ARTIFACT_OBSERVATIONS[EVENT_KEY],
        )
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS[EVENT_KEY],
            VANILLA_ARTIFACT_TIMELINE_CONTRACTS[EVENT_KEY],
        )

        response = query_vanilla_event_knowledge_v1(EVENT_KEY)
        self.assertEqual(response["status"], "available")
        self.assertEqual(response["contract"]["selected_native_option_index"], 0)
        source = query_vanilla_event_source_provenance_v1(EVENT_KEY)
        self.assertEqual(source["status"], "available")
        self.assertEqual(source["definition"]["line"], 3066)
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
            "assert contract['native_option_indices']==(0,1);"
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
            "current_event_instance_id": 1081,
            "date_raw": 53832072,
            "root_scope": _scope("root", "character", character_id=32904)["scope"],
            "saved_scopes": [
                _scope("this_artifact", "artifact"),
                _scope("helpful", "character", character_id=79104),
            ],
            "options": [
                {
                    "rendered_index": native,
                    "native_option_index": native,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for native in (0, 1)
            ],
        }
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53832072,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 1081},
            context=context,
            event_key=EVENT_KEY,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)


if __name__ == "__main__":
    unittest.main()
