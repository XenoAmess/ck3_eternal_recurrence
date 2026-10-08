"""Root-only FIRST for actual normal chooser/Service/registered plan consumption.

Outer frames/options are explicitly synthetic. No native producer or live
outcome is qualified. The baseline chooser and end-condition leaf are real.
"""

import asyncio
import copy
import json
import os
from pathlib import Path
from unittest.mock import patch

from xar_autoplayer.bridge import mcp_server
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.bridge.war_contract import (
    RAISE_TROOPS_STEP,
    enforce_demands_step,
    normalize_war_termination_options,
    query_war_termination_options_step,
)


WAR_ID = 100663329


def _option(outcome, *, legal, auto_accept=False):
    return {
        "outcome": outcome,
        "hostage_variant": "none",
        "context_constructed": True,
        "native_validator_passed": legal,
        "available": legal,
        "terms_observable": False,
        "terms": {"status": "unavailable", "reason": "cb_specific_terms_not_observable"},
        "ai_acceptance_observable": True,
        "ai_acceptance": {"raw": 9000000, "scale": 100000},
        "auto_accept_observable": True,
        "auto_accept": auto_accept,
        "recipient_response": {
            "status": "unavailable",
            "decision_status_raw": None,
            "would_accept_now": None,
        },
    }


def _frame(*, score=0, duration=23, white_peace_legal=False, victory_legal=False):
    frame = {
        "paused": True,
        "map_ready": True,
        "snapshot_id": "source-war-end-frame34",
        "revision": 34,
        "native_revision": 234,
        "date_raw": 53288472,
        "episode_run_id": "source-fixture-native-war-end-input34",
        "diagnostics": {"connection_generation": 1, "hello": {
            "expected_ck3_version": CK3_12004.game_version,
            "expected_ck3_sha256": CK3_12004.executable_sha256,
        }},
        "played_character": {"character_id": 29829, "alive": True},
        "active_event": None,
        "pending_character_interaction": None,
        "player_armies": [],
        "history": [],
        "native_command_history": [],
        "active_wars": [{
            "war_id": WAR_ID,
            "player_side": "attacker",
            "player_is_primary_war_leader": True,
            "player_relative_war_score": score,
            "primary_opponent_character_id": 31050,
            "targeted_title_ids": [2132],
            "allied_armies": [],
            "enemy_armies": [],
        }],
    }
    options = normalize_war_termination_options({
        "war_id": WAR_ID,
        "player_side": "attacker",
        "player_is_primary_war_leader": True,
        "player_relative_war_score": score,
        "war_duration_days": duration,
        "absolute_war_scores_observable": True,
        "attacker_war_score": score,
        "defender_war_score": -score,
        "war_score_breakdown": {"imprisonment": 0, "battles": 0, "occupation": score, "ticking": 0},
        "active_casus_belli_present": True,
        "active_casus_belli_identity": {"database_index": 11, "canonical_key": "claim_cb"},
        "cb_allows_white_peace": True,
        "options": {
            "surrender": _option("attacker_defeat", legal=True, auto_accept=True),
            "white_peace": _option("white_peace", legal=white_peace_legal),
            "victory": _option("attacker_victory", legal=victory_legal),
        },
    }, expected_war_id=WAR_ID, source_build=CK3_12004)
    options.update(
        queried_snapshot_id=frame["snapshot_id"],
        queried_revision=frame["revision"],
        queried_native_revision=frame["native_revision"],
        queried_connection_generation=1,
        episode_run_id=frame["episode_run_id"],
    )
    frame["war_termination_options"] = [options]
    return frame


class OuterFixtureDriver:
    nonwar_only = False
    state_dir = None

    def __init__(self, frame):
        self.frame = frame

    def take_snapshot(self):
        return copy.deepcopy(self.frame)

    def capabilities(self):
        return {
            "backend_id": "native-headless",
            "action_steps": [RAISE_TROOPS_STEP, enforce_demands_step(WAR_ID), query_war_termination_options_step(WAR_ID)],
            "bridge_capabilities": [],
        }


def test_registered_current_native_war_end_conditions(tmp_path):
    from mcp import Client

    records = []

    async def run():
        for name, frame, expected_step, expected_input, expected_nonloss in (
            ("r76-end-inputs-synthetic-no-army", _frame(), RAISE_TROOPS_STEP, "continue_war", False),
            ("legal-white-peace-final-reply-missing", _frame(duration=365, white_peace_legal=True), RAISE_TROOPS_STEP, "review_existing_exit_policy", True),
            ("existing-native100-victory-priority", _frame(score=100, victory_legal=True), enforce_demands_step(WAR_ID), "existing_score_victory_policy", True),
        ):
            driver = OuterFixtureDriver(frame)
            # This fixture's outer lifecycle preparation is explicit. It
            # neither supplies nor qualifies succession/provider behavior.
            with patch.object(GameplayBridgeService, "_prepare_succession_transition_v1", return_value=frame):
                server = mcp_server.create_server(driver)
                async with Client(server) as client:
                    observed = await client.call_tool("ck3_plan_turn", {})
            assert not observed.is_error, observed.content
            plan = observed.structured_content["plan"]
            assert plan["selected_step"] == expected_step
            conditions = plan["active_wars"][0]["native_end_conditions"]
            assert conditions["status"] == "current_native_conditions_observed"
            assert conditions["ordinary_war_input"] == expected_input
            assert conditions["native_nonloss_exit_available"] is expected_nonloss
            assert conditions["native_options"]["surrender"]["available"] is True
            assert conditions["native_options"]["surrender"]["auto_accept"] is True
            assert conditions["native_options"]["white_peace"]["recipient_would_accept_now"] is None
            if name == "legal-white-peace-final-reply-missing":
                assert conditions["required_native_input"] == "current_white_peace_recipient_response"
                assert conditions["native_options"]["white_peace"]["ai_acceptance"]["raw"] > 0
            if expected_input == "continue_war":
                assert conditions["required_native_input"] is None
                assessment = plan["active_wars"][0]["war_exit_assessment"]
                assert assessment["automatic_termination_scope"] == "full_campaign_expected_utility"
            records.append({"scene": name, "selected_step": plan["selected_step"], "native_end_conditions": conditions})

    asyncio.run(run())
    output = Path(os.environ.get("WAR_END_CONSUMER_ROOT_REPORT_DIR", str(tmp_path)))
    output.mkdir(parents=True, exist_ok=True)
    (output / "SOLE-REGISTERED-CONSUMER-RESULT.json").write_text(json.dumps({
        "readiness": "offline fixture result only; synthetic outer frames",
        "registered_tool": "ck3_plan_turn",
        "baseline_chooser_mocked": False,
        "native_producer_qualified": False,
        "game_calls": 0,
        "cases": records,
    }, indent=2) + "\n", encoding="utf-8")
