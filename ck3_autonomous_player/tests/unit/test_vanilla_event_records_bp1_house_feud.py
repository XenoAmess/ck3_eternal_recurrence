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
from xar_autoplayer.vanilla_events.records_bp1_house_feud import (  # noqa: E402
    PLAYER_SENTINEL,
    VANILLA_BP1_HOUSE_FEUD_ANALYSIS,
    VANILLA_BP1_HOUSE_FEUD_OBSERVATIONS,
    VANILLA_BP1_HOUSE_FEUD_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.registry import (  # noqa: E402
    materialize_vanilla_timeline_contract,
    query_vanilla_event_knowledge_v1,
)
from xar_autoplayer.vanilla_events.source_index import (  # noqa: E402
    query_vanilla_event_source_provenance_v1,
)


EVENT_KEY = "bp1_house_feud.0014"
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


ALIASES = {
    "mother": 81924,
    "father": 33606629,
    "real_father": 16850404,
    "spouse": 33606629,
    "adultery_spouse": 33606629,
    "assumed_father": 33606629,
    "secret_exposer": 33606629,
    "sex_partner": 16850404,
    "adulterer_check": 81924,
    "house_feud_spouse": 81924,
    "house_feud_rival": 16850404,
    "house_feud_attacker": 16850404,
    "house_feud_victim": 33606629,
}


class Bp1HouseFeudEventRecordTests(unittest.TestCase):
    def test_contract_is_campaign_neutral_and_selects_forgiveness(self) -> None:
        contract = VANILLA_BP1_HOUSE_FEUD_TIMELINE_CONTRACTS[EVENT_KEY]

        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)
        self.assertNotIn("date_raw", contract)
        self.assertEqual(contract["saved_scope_count"], 15)
        relation_variant, = contract["scope_variants"]
        self.assertEqual(relation_variant["saved_scope_count"], 16)
        self.assertEqual(relation_variant["scope_types"]["relation"], "house_relation")
        self.assertEqual(
            contract["boolean_scopes"],
            ("is_child_of_concubine", "matrilineal"),
        )
        self.assertEqual(contract["option_count"], 3)
        self.assertEqual(contract["snapshot_option_count"], 3)
        self.assertEqual(contract["selected_option_number"], 3)
        self.assertEqual(contract["selected_native_option_index"], 2)

    def test_materialization_binds_player_without_campaign_ids(self) -> None:
        source = VANILLA_BP1_HOUSE_FEUD_TIMELINE_CONTRACTS[EVENT_KEY]
        materialized = materialize_vanilla_timeline_contract(source, 32904)

        self.assertEqual(materialized["root_character_id"], 32904)
        self.assertEqual(
            materialized["unique_character_scope_excludes"],
            {
                "mother": (32904,),
                "father": (32904,),
                "real_father": (32904,),
            },
        )
        self.assertEqual(source["root_character_id"], PLAYER_SENTINEL)

    def test_analysis_freezes_native_weights_and_bounded_cost(self) -> None:
        analysis = VANILLA_BP1_HOUSE_FEUD_ANALYSIS[EVENT_KEY]

        self.assertEqual(analysis["definition_lines"], "2310-2433")
        self.assertIn("seventy-five-percent", analysis["caller_semantics"])
        self.assertIn("five-year cooldown", analysis["frequency_boundary"])
        self.assertIn("minus-fifteen", analysis["safe_option_rationale"])
        self.assertIn("base 25", analysis["native_ai_weights"][2])
        self.assertIsNone(analysis["follow_up_event"])
        for digest in analysis["source_sha256"].values():
            self.assertRegex(digest, SHA256_PATTERN)

    def test_r414_ids_and_harness_red_remain_observation_only(self) -> None:
        r414, r416 = VANILLA_BP1_HOUSE_FEUD_OBSERVATIONS[EVENT_KEY]["exemplars"]
        contract_repr = repr(VANILLA_BP1_HOUSE_FEUD_TIMELINE_CONTRACTS[EVENT_KEY])

        self.assertEqual(r414["run"], "R414")
        self.assertEqual(r416["run"], "R416")
        self.assertEqual(r416["saved_scope_raw_types"]["relation"], 22)
        for exemplar in (r414, r416):
            self.assertEqual(exemplar["red_classification"], "harness-route-red")
            self.assertFalse(exemplar["product_failure_proven"])
            self.assertEqual(exemplar["rendered_native_option_indices"], [0, 1, 2])
            self.assertFalse(exemplar["selection_attempted"])
            self.assertRegex(exemplar["artifact_sha256"], SHA256_PATTERN)
        for observation_only in (53671224, 1066, 53785920, 1076, 32904, 81924, 33606629, 16850404):
            self.assertNotIn(str(observation_only), contract_repr)

    def test_default_registry_runtime_and_evidence_share_record(self) -> None:
        self.assertIs(
            DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS[EVENT_KEY],
            VANILLA_BP1_HOUSE_FEUD_TIMELINE_CONTRACTS[EVENT_KEY],
        )
        self.assertIs(
            DEFAULT_VANILLA_EVENT_ANALYSIS[EVENT_KEY],
            VANILLA_BP1_HOUSE_FEUD_ANALYSIS[EVENT_KEY],
        )
        self.assertIs(
            DEFAULT_VANILLA_EVENT_OBSERVATIONS[EVENT_KEY],
            VANILLA_BP1_HOUSE_FEUD_OBSERVATIONS[EVENT_KEY],
        )
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS[EVENT_KEY],
            VANILLA_BP1_HOUSE_FEUD_TIMELINE_CONTRACTS[EVENT_KEY],
        )

        response = query_vanilla_event_knowledge_v1(EVENT_KEY)
        self.assertEqual(response["status"], "available")
        self.assertEqual(response["contract"]["selected_native_option_index"], 2)
        source = query_vanilla_event_source_provenance_v1(EVENT_KEY)
        self.assertEqual(source["status"], "available")
        self.assertEqual(source["definition"]["line"], 2310)
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
        scopes = [
            _scope(name, "character", character_id)
            for name, character_id in ALIASES.items()
        ] + [
            _scope("is_child_of_concubine", "boolean"),
            _scope("matrilineal", "boolean"),
        ]
        order = VANILLA_BP1_HOUSE_FEUD_TIMELINE_CONTRACTS[EVENT_KEY][
            "saved_scope_name_sets"
        ][0]
        by_name = {scope["name"]: scope for scope in scopes}
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": EVENT_KEY,
            "current_event_instance_id": 1066,
            "date_raw": 53671224,
            "root_scope": _scope("root", "character", 32904)["scope"],
            "saved_scopes": [by_name[name] for name in order],
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
                "date_raw": 53671224,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 1066},
            context=context,
            event_key=EVENT_KEY,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)

    def test_r416_live_relation_shape_passes_production_recovery_checks(self) -> None:
        source = VANILLA_BP1_HOUSE_FEUD_TIMELINE_CONTRACTS[EVENT_KEY]
        contract = production._manager_recovery_contract(
            source,
            player=32904,
            event_key=EVENT_KEY,
        )
        contract = production._timeline_contract_for_window(
            contract,
            starting_date=53783472,
            absolute_end_date=53958720,
        )
        scopes = [
            _scope(name, "character", character_id)
            for name, character_id in ALIASES.items()
        ] + [
            _scope("is_child_of_concubine", "boolean"),
            _scope("matrilineal", "boolean"),
            _scope("relation", "house_relation"),
        ]
        order = source["scope_variants"][0]["saved_scope_names"]
        by_name = {scope["name"]: scope for scope in scopes}
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": EVENT_KEY,
            "current_event_instance_id": 1076,
            "date_raw": 53785920,
            "root_scope": _scope("root", "character", 32904)["scope"],
            "saved_scopes": [by_name[name] for name in order],
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
        resolved = production._interrupt_contract_for_context(context, contract)
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53785920,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 1076},
            context=context,
            event_key=EVENT_KEY,
            contract=resolved,
        )

        self.assertEqual(resolved["saved_scope_count"], 16)
        self.assertTrue(all(checks.values()), checks)


if __name__ == "__main__":
    unittest.main()
