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
from xar_autoplayer.vanilla_events.records_manager_b import (  # noqa: E402
    MANAGER_TGP_MINISTRY_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.records_tgp_treasury import (  # noqa: E402
    PLAYER_SENTINEL,
    VANILLA_TGP_TREASURY_ANALYSIS,
    VANILLA_TGP_TREASURY_OBSERVATIONS,
    VANILLA_TGP_TREASURY_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.registry import (  # noqa: E402
    materialize_vanilla_timeline_contract,
    query_vanilla_event_knowledge_v1,
)


EVENT_KEY = "tgp_china_ministry.0100"
SHA256_PATTERN = re.compile(r"^[0-9A-F]{64}$")
PREFERENCE_SCOPES = {
    "salary_budget",
    "ministry_budget",
    "military_budget",
    "hegemon_budget",
    "meritocratic_salary_budget",
    "meritocratic_military_budget",
}


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


def _context(
    *,
    scopes: list[dict[str, object]],
    native_option_indices: tuple[int, ...],
) -> dict[str, object]:
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "window_match_count": 1,
        "event_definition_key": EVENT_KEY,
        "current_event_instance_id": 700,
        "date_raw": 53610000,
        "root_scope": _character_scope("root", 32904)["scope"],
        "saved_scopes": scopes,
        "options": [
            {
                "rendered_index": rendered_index,
                "native_option_index": native_index,
                "shown": True,
                "enabled": True,
                "fallback": False,
                "cancel": False,
            }
            for rendered_index, native_index in enumerate(native_option_indices)
        ],
    }


class TgpTreasuryEventRecordTests(unittest.TestCase):
    def test_contract_is_campaign_neutral_and_covers_only_source_shapes(self) -> None:
        contract = VANILLA_TGP_TREASURY_TIMELINE_CONTRACTS[EVENT_KEY]

        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)
        self.assertNotIn("date_raw", contract)
        self.assertEqual(
            contract["character_scopes"],
            {"treasury_ruler": PLAYER_SENTINEL},
        )
        self.assertEqual(
            set(contract["optional_character_scopes"]),
            PREFERENCE_SCOPES,
        )
        self.assertEqual(
            contract["optional_unique_character_scope_excludes"],
            {"steward": (PLAYER_SENTINEL,)},
        )
        self.assertEqual(contract["saved_scope_counts"], (1, 2, 3))
        self.assertEqual(len(contract["saved_scope_name_sets"]), 8)
        for names in contract["saved_scope_name_sets"]:
            self.assertEqual(names[0], "treasury_ruler")
            self.assertTrue(set(names).issubset(
                {"treasury_ruler", "steward", *PREFERENCE_SCOPES}
            ))

    def test_contract_selects_terminal_current_allocation_route(self) -> None:
        contract = VANILLA_TGP_TREASURY_TIMELINE_CONTRACTS[EVENT_KEY]

        self.assertEqual(contract["native_option_indices"], (0, 1, 2))
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)
        self.assertEqual(contract["option_variants"], ({
            "option_count": 2,
            "snapshot_option_count": 3,
            "native_option_indices": (0, 1),
            "selected_option_number": 2,
            "selected_native_option_index": 1,
        },))
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )

    def test_materializer_binds_all_player_aliases_without_mutation(self) -> None:
        contract = VANILLA_TGP_TREASURY_TIMELINE_CONTRACTS[EVENT_KEY]
        materialized = materialize_vanilla_timeline_contract(contract, 32904)

        self.assertEqual(materialized["root_character_id"], 32904)
        self.assertEqual(materialized["character_scopes"], {
            "treasury_ruler": 32904,
        })
        self.assertEqual(
            set(materialized["optional_character_scopes"].values()),
            {32904},
        )
        self.assertEqual(
            materialized["optional_unique_character_scope_excludes"],
            {"steward": (32904,)},
        )
        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)

    def test_exact_source_analysis_freezes_frequency_and_choice_boundary(self) -> None:
        analysis = VANILLA_TGP_TREASURY_ANALYSIS[EVENT_KEY]

        self.assertEqual(analysis["definition_lines"], "509-830")
        self.assertIn("once per year, not daily", analysis["frequency_boundary"])
        self.assertIn("ninety-six months", analysis["frequency_boundary"])
        self.assertIn("additional picker", analysis["safe_option_rationale"])
        self.assertIn("allocation-law changes", analysis["safe_option_rationale"])
        self.assertIsNone(analysis["after_effect"])
        self.assertEqual(len(analysis["source_sha256"]), 5)
        for digest in analysis["source_sha256"].values():
            self.assertRegex(digest, SHA256_PATTERN)

    def test_r374_observation_is_identity_only_and_does_not_invent_context(self) -> None:
        exemplar = VANILLA_TGP_TREASURY_OBSERVATIONS[EVENT_KEY]["exemplars"][0]
        contract_repr = repr(VANILLA_TGP_TREASURY_TIMELINE_CONTRACTS[EVENT_KEY])

        self.assertEqual(exemplar["kind"], "foreground-ui-identity-red")
        self.assertEqual(exemplar["visible_title_text"], "宋国库")
        self.assertEqual(exemplar["rendered_option_count"], 3)
        self.assertEqual(exemplar["current_event_context_status"], "unavailable")
        self.assertNotIn("event_instance_id", exemplar)
        self.assertNotIn("date_raw", exemplar)
        self.assertNotIn("root_character_id", exemplar)
        self.assertNotIn("saved_scope_raw_types", exemplar)
        self.assertFalse(exemplar["selection_attempted"])
        self.assertRegex(exemplar["artifact_sha256"], SHA256_PATTERN)
        for campaign_only in (53163168, 29037):
            self.assertNotIn(str(campaign_only), contract_repr)

    def test_r375_production_live_observation_is_mcp_only_and_portable(self) -> None:
        live = VANILLA_TGP_TREASURY_OBSERVATIONS[EVENT_KEY]["exemplars"][1]
        contract_repr = repr(VANILLA_TGP_TREASURY_TIMELINE_CONTRACTS[EVENT_KEY])

        self.assertEqual(live["kind"], "production-live-primitive")
        self.assertEqual(live["production_live_ordinal"], 14)
        self.assertTrue(live["artifact"].endswith(
            "r375-live-014-tgp-china-ministry-0100-green.json"
        ))
        self.assertEqual(
            live["artifact_sha256"],
            "6C1407AF00D2E767FA201DA2411619D5724C86951BB5CEFF006DAB50ABC6C779",
        )
        self.assertEqual(live["event_instance_id"], 1057)
        self.assertEqual(live["context_query_driver_command_index"], 291)
        self.assertEqual(live["selection_driver_command_index"], 292)
        self.assertEqual(live["selected_option_number"], 2)
        self.assertEqual(live["selected_native_option_index"], 1)
        self.assertTrue(live["postcondition_verified"])
        self.assertEqual(live["ending_snapshot_id"], "native:357")
        self.assertTrue(live["mcp_only"])
        for forbidden_mode in (
            "fixture_used",
            "ocr_used",
            "coordinates_used",
            "console_used",
        ):
            self.assertFalse(live[forbidden_mode])
        self.assertRegex(live["artifact_sha256"], SHA256_PATTERN)

        for observation_only in (
            53609928,
            1057,
            32904,
            38076,
            180544,
            "native:356",
            "native:357",
        ):
            self.assertNotIn(str(observation_only), contract_repr)

    def test_default_registry_mcp_and_compatibility_export_use_new_record(self) -> None:
        self.assertIs(
            MANAGER_TGP_MINISTRY_TIMELINE_CONTRACTS,
            VANILLA_TGP_TREASURY_TIMELINE_CONTRACTS,
        )
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS[EVENT_KEY],
            VANILLA_TGP_TREASURY_TIMELINE_CONTRACTS[EVENT_KEY],
        )
        self.assertIs(
            DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS[EVENT_KEY],
            VANILLA_TGP_TREASURY_TIMELINE_CONTRACTS[EVENT_KEY],
        )
        self.assertIs(
            DEFAULT_VANILLA_EVENT_ANALYSIS[EVENT_KEY],
            VANILLA_TGP_TREASURY_ANALYSIS[EVENT_KEY],
        )
        self.assertIs(
            DEFAULT_VANILLA_EVENT_OBSERVATIONS[EVENT_KEY],
            VANILLA_TGP_TREASURY_OBSERVATIONS[EVENT_KEY],
        )

        response = query_vanilla_event_knowledge_v1(EVENT_KEY)
        self.assertEqual(response["status"], "available")
        self.assertEqual(response["contract"]["root_character_id"], "$player")
        self.assertEqual(response["contract"]["selected_option_number"], 2)
        self.assertEqual(response["analysis"]["definition_lines"], "509-830")
        self.assertEqual(
            response["observations"]["exemplars"][0]["kind"],
            "foreground-ui-identity-red",
        )
        self.assertEqual(
            response["observations"]["exemplars"][1]["kind"],
            "production-live-primitive",
        )
        json.dumps(response, allow_nan=False)

    def test_source_reviewed_steward_and_no_steward_shapes_pass_runtime_checks(self) -> None:
        contract = production._manager_recovery_contract(
            production.KNOWN_TIMELINE_INTERRUPTS[EVENT_KEY],
            player=32904,
            event_key=EVENT_KEY,
        )
        contract = production._timeline_contract_for_window(
            contract,
            starting_date=53600000,
        )

        for scopes, native_indices in (
            ([
                _character_scope("treasury_ruler", 32904),
                _character_scope("steward", 44001),
                _character_scope("military_budget", 32904),
            ], (0, 1, 2)),
            ([_character_scope("treasury_ruler", 32904)], (0, 1)),
        ):
            with self.subTest(native_indices=native_indices):
                context = _context(
                    scopes=scopes,
                    native_option_indices=native_indices,
                )
                checks = production._known_interrupt_checks(
                    snapshot={
                        "date_raw": 53610000,
                        "active_event": {"option_count": 3},
                    },
                    event={"event_instance_id": 700},
                    context=context,
                    event_key=EVENT_KEY,
                    contract=contract,
                )
                self.assertTrue(all(checks.values()), checks)


if __name__ == "__main__":
    unittest.main()
