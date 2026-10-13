"""Optional rule reads must not hide already observed campaign components."""

from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "tests" / "unit"))

from test_campaign_root_context_v1_bridge import (
    DATE_RAW,
    NATIVE_REVISION,
    PLAYER_CHARACTER_ID,
    PUBLIC_REVISION,
    STEP,
    _ServiceDriver,
    _driver_result,
)
from xar_autoplayer.bridge.campaign_root_context_contract import (
    _PROVENANCE_BY_BUILD,
    _READINESS_KEYS,
    normalize_campaign_root_context_v1,
)
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.turn_bundle_contract import build_turn_bundle_v1
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.strategy import (
    _complete_player_held_county_capital_province_ids,
    _same_frame_campaign_root_context,
)


class _OptionalRuleDriver(_ServiceDriver):
    """Synthetic actual4 wire using the real Service query and planner."""

    def __init__(self):
        super().__init__()
        self.history = [{"index": 1, "command": "save-checkpoint", "ok": True}]
        self.sent_steps = []

    def capabilities(self):
        result = super().capabilities()
        result["action_steps"] += ["life-advance", "query-war-entry-assessments-v1-1-45678"]
        return result

    def take_snapshot(self):
        snapshot = super().take_snapshot()
        snapshot.update(map_ready=True, player_armies=[], history=copy.deepcopy(self.history))
        snapshot["diagnostics"]["hello"].update(
            game_version=CK3_12004.game_version,
            expected_ck3_version=CK3_12004.game_version,
            expected_ck3_sha256=CK3_12004.executable_sha256,
        )
        snapshot["declarable_wars"] = [{
            "declaration_id": "45678-17-0",
            "target_character_id": 45678,
            "casus_belli_index": 17,
            "casus_belli_key": "claim_cb",
            "configuration_index": -1,
            "claimant_character_id": PLAYER_CHARACTER_ID,
            "target_title_ids": [145678],
            "source": "native",
        }]
        return snapshot

    def execute_step(self, step, *, expected_revision=None):
        if step != STEP or expected_revision != PUBLIC_REVISION:
            raise AssertionError("planning sent an unexpected command")
        self.sent_steps.append(step)
        result = _driver_result()
        root = result["campaign_root_context"]
        root["provenance"] = copy.deepcopy(_PROVENANCE_BY_BUILD[CK3_12004.game_version])
        root["selected_game_rule_tokens"] = []
        root["native_selected_game_rule_token_count"] = 0
        root["readiness"]["selected_game_rule_tokens_ready"] = False
        root["readiness"]["ready"] = False
        root["player_targeting_faction_count"] = 0
        root = normalize_campaign_root_context_v1(
            root, expected_date_raw=DATE_RAW, expected_snapshot_revision=NATIVE_REVISION)
        result["campaign_root_context"] = root
        for key in tuple(result):
            if key in root:
                result[key] = copy.deepcopy(root[key])
        result["campaign_root_context_ready"] = False
        self.history.append({"index": len(self.history) + 1, "command": step,
                             "ok": True, "result": copy.deepcopy(result)})
        return result


class CampaignRootOptionalRulesServiceTests(unittest.TestCase):
    def test_available_components_continue_ordinary_service_planning(self):
        driver = _OptionalRuleDriver()
        service = GameplayBridgeService(driver)
        # The existing ordinary planner requests its missing root once.
        before = service.plan_turn()
        self.assertEqual(before["plan"]["selected_step"], STEP)
        self.assertEqual(driver.sent_steps, [])

        query = service.query_campaign_root_context_v1(expected_revision=PUBLIC_REVISION)
        root = query["campaign_root_context"]
        self.assertEqual(query["build"]["version"], CK3_12004.game_version)
        self.assertFalse(query["campaign_root_context_ready"])
        self.assertFalse(root["readiness"]["selected_game_rule_tokens_ready"])
        self.assertEqual(root["selected_game_rule_tokens"], [])
        snapshot = service.snapshot()
        recovered = _same_frame_campaign_root_context(driver.history, snapshot)
        self.assertEqual(recovered, root)
        self.assertEqual(recovered["capital_province_id"], 42)
        self.assertEqual(_complete_player_held_county_capital_province_ids(recovered), [43])
        after = service.plan_turn()
        self.assertEqual(after["plan"]["phase"], "native_player_claim_power_assessment")
        self.assertEqual(after["plan"]["selected_step"], "query-war-entry-assessments-v1-1-45678")
        # Neither planning nor accepting a partial root sends a declaration.
        self.assertEqual(driver.sent_steps, [STEP])

        # A missing required component cannot use the optional-rule fallback.
        required = set(_READINESS_KEYS) - {
            "ready", "selected_game_rule_tokens_ready", "council_ready",
        }
        for key in required:
            with self.subTest(required_component=key):
                incomplete = copy.deepcopy(root)
                incomplete["readiness"][key] = False
                view = {**snapshot, "campaign_root_context": incomplete}
                self.assertIsNone(_same_frame_campaign_root_context([], view))

        for field in ("player_character_id", "snapshot_revision", "date_raw"):
            for through_history in (False, True):
                with self.subTest(stale_field=field, through_history=through_history):
                    stale = copy.deepcopy(root)
                    stale[field] += 1
                    view = {**snapshot, "campaign_root_context": stale}
                    rows = []
                    if through_history:
                        view.pop("campaign_root_context")
                        rows = [{"command": STEP, "ok": True,
                                 "result": {"campaign_root_context": stale}}]
                    self.assertIsNone(_same_frame_campaign_root_context(rows, view))

        # Existing complete historical rows retain the former accepted branch.
        historical = copy.deepcopy(root)
        historical["readiness"] = {"ready": True}
        self.assertIs(_same_frame_campaign_root_context([], {
            **snapshot, "campaign_root_context": historical}), historical)

        # A legitimate landless/no-capital observation remains observed absence.
        absent = copy.deepcopy(root)
        absent.update(primary_title=None, capital_province_id=None, government=None,
                      primary_title_succession_character_ids=[], held_title_partition=[])
        absent["council"] = {
            "status": "unavailable", "coverage_key": "standard_landed_non_nomadic_core_v1",
            "owner_character_id": PLAYER_CHARACTER_ID, "positions": [],
            "auxiliary_vacancies_complete": False,
            "unavailable_reason": "outside_standard_landed_non_nomadic_core_scope",
        }
        absent["readiness"]["council_ready"] = False
        absent = normalize_campaign_root_context_v1(
            absent, expected_date_raw=DATE_RAW, expected_snapshot_revision=NATIVE_REVISION)
        recovered_absent = _same_frame_campaign_root_context([], {
            **snapshot, "campaign_root_context": absent})
        self.assertIs(recovered_absent, absent)
        absent_query = {**query, "campaign_root_context": absent}
        bundle = build_turn_bundle_v1(snapshot, absent_query)
        state = bundle["ruler_state"]["value"]
        self.assertEqual(state["primary_title"]["status"], "not_applicable")
        self.assertEqual(state["capital_province_id"]["status"], "not_applicable")


if __name__ == "__main__":
    unittest.main()
