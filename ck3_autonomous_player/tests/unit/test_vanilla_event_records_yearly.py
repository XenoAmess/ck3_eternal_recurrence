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
from xar_autoplayer.vanilla_events.records_yearly import (  # noqa: E402
    PLAYER_SENTINEL,
    VANILLA_YEARLY_ANALYSIS,
    VANILLA_YEARLY_OBSERVATIONS,
    VANILLA_YEARLY_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.registry import (  # noqa: E402
    materialize_vanilla_timeline_contract,
    query_vanilla_event_knowledge_v1,
)
from xar_autoplayer.vanilla_events.source_index import (  # noqa: E402
    query_vanilla_event_source_provenance_v1,
)


EVENT_KEY = "yearly.0003"
SHA256_PATTERN = re.compile(r"^[0-9A-F]{64}$")


def _scope(name: str, type_key: str, character_id: int | None = None) -> dict:
    identity = (
        {"status": "available", "kind": "character", "character_id": character_id}
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


class YearlyEventRecordTests(unittest.TestCase):
    def test_contract_is_campaign_neutral_and_selects_protective_route(self) -> None:
        contract = VANILLA_YEARLY_TIMELINE_CONTRACTS[EVENT_KEY]

        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)
        self.assertNotIn("date_raw", contract)
        self.assertEqual(
            contract["saved_scope_name_sets"],
            (("child", "relative", "secret"),),
        )
        self.assertEqual(contract["option_count"], 3)
        self.assertEqual(contract["snapshot_option_count"], 4)
        self.assertEqual(contract["native_option_indices"], (0, 1, 2))
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

    def test_materialization_binds_only_player_constraints(self) -> None:
        source = VANILLA_YEARLY_TIMELINE_CONTRACTS[EVENT_KEY]
        materialized = materialize_vanilla_timeline_contract(source, 32904)

        self.assertEqual(materialized["root_character_id"], 32904)
        self.assertEqual(
            materialized["unique_character_scope_excludes"],
            {"child": (32904,), "relative": (32904,)},
        )
        self.assertEqual(source["root_character_id"], PLAYER_SENTINEL)

    def test_analysis_freezes_source_route_and_bounded_downside(self) -> None:
        analysis = VANILLA_YEARLY_ANALYSIS[EVENT_KEY]

        self.assertEqual(analysis["definition_lines"], "766-1103")
        self.assertIn("once per playable", analysis["caller_semantics"])
        self.assertIn("no daily poll", analysis["frequency_boundary"])
        self.assertIn("no explicit ai_chance", analysis["native_ai_boundary"])
        self.assertIn("minor stress", analysis["safe_option_rationale"])
        self.assertIsNone(analysis["follow_up_event"])
        for digest in analysis["source_sha256"].values():
            self.assertRegex(digest, SHA256_PATTERN)

    def test_r414_ids_and_harness_red_remain_observation_only(self) -> None:
        exemplar, = VANILLA_YEARLY_OBSERVATIONS[EVENT_KEY]["exemplars"]
        contract_repr = repr(VANILLA_YEARLY_TIMELINE_CONTRACTS[EVENT_KEY])

        self.assertEqual(exemplar["run"], "R414")
        self.assertEqual(exemplar["red_classification"], "harness-route-red")
        self.assertFalse(exemplar["product_failure_proven"])
        self.assertEqual(exemplar["rendered_native_option_indices"], [0, 1, 2])
        self.assertFalse(exemplar["selection_attempted"])
        self.assertTrue(exemplar["retained_red"])
        self.assertRegex(exemplar["artifact_sha256"], SHA256_PATTERN)
        for observation_only in (53639352, 1064, 32904, 37804, 33606148):
            self.assertNotIn(str(observation_only), contract_repr)

    def test_default_registry_mcp_runtime_and_evidence_share_record(self) -> None:
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
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS[EVENT_KEY],
            VANILLA_YEARLY_TIMELINE_CONTRACTS[EVENT_KEY],
        )

        response = query_vanilla_event_knowledge_v1(EVENT_KEY)
        self.assertEqual(response["status"], "available")
        self.assertEqual(response["contract"]["root_character_id"], "$player")
        self.assertEqual(response["contract"]["native_option_indices"], [0, 1, 2])
        self.assertEqual(response["analysis"]["definition_lines"], "766-1103")
        self.assertEqual(response["observations"]["exemplars"][0]["run"], "R414")
        source = query_vanilla_event_source_provenance_v1(EVENT_KEY)
        self.assertEqual(source["status"], "available")
        self.assertEqual(source["definition"]["line"], 766)
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

    def test_r414_live_shape_passes_production_recovery_checks(self) -> None:
        contract = production._manager_recovery_contract(
            production.KNOWN_TIMELINE_INTERRUPTS[EVENT_KEY],
            player=32904,
            event_key=EVENT_KEY,
        )
        contract = production._timeline_contract_for_window(
            contract,
            starting_date=53628720,
            absolute_end_date=53782080,
        )
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": EVENT_KEY,
            "current_event_instance_id": 1064,
            "date_raw": 53639352,
            "root_scope": _scope("root", "character", 32904)["scope"],
            "saved_scopes": [
                _scope("child", "character", 37804),
                _scope("relative", "character", 33606148),
                _scope("secret", "secret"),
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
                "date_raw": 53639352,
                "active_event": {"option_count": 4},
            },
            event={"event_instance_id": 1064},
            context=context,
            event_key=EVENT_KEY,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)


if __name__ == "__main__":
    unittest.main()
