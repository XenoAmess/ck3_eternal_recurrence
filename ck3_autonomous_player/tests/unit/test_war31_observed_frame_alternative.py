"""Guard the exact War 31 defender frame against an inferred surrender."""

from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))

from xar_autoplayer.strategy import (  # noqa: E402
    _de_jure_no_safe_route_exit_plan,
    _de_jure_no_safe_route_surrender_candidate,
    _de_jure_no_safe_route_white_peace_candidate,
)


BOARD = ROOT / "docs" / "autonomous-agent-progress" / "coordination" / "war-requests"
REQUEST = BOARD / "requests" / "WAR-INPUT-R0221-WAR31-20260927.json"
EVIDENCE = BOARD / "evidence"


def _hashed_json(path: Path, expected_sha: str) -> dict:
    data = path.read_bytes()
    assert hashlib.sha256(data).hexdigest().upper() == expected_sha, path
    value = json.loads(data)
    assert isinstance(value, dict), path
    return value


class War31ObservedFrameAlternativeTests(unittest.TestCase):
    def test_native_positive_defender_surrender_does_not_enter_attacker_emergency_exit(
        self,
    ) -> None:
        request = json.loads(REQUEST.read_text(encoding="utf-8"))
        evidence = request["evidence"]
        freeze = _hashed_json(
            EVIDENCE / "WAR-INPUT-R0221-WAR31-20260927.r0221-raw-freeze.json",
            evidence["git_r0221_readonly_freeze_sha256"],
        )
        result = _hashed_json(
            EVIDENCE / "WAR-INPUT-R0221-WAR31-20260927.termination-options.json",
            evidence["git_r0221_termination_result_sha256"],
        )
        source = request["reproduction"]
        assert freeze["same_native_frame"] is True
        assert freeze["gameplay_actions"] == freeze["date_advanced"] == 0
        assert freeze["typed_termination_authorized"] is False
        assert source["war_id"] == freeze["war_id"] == result["war_id"] == 16777231
        assert result["queried_snapshot_id"] == source["snapshot_id"]
        assert result["queried_revision"] == source["snapshot_revision"]
        assert result["queried_native_revision"] == source["native_revision"]
        assert result["queried_episode_run_id"] == source["episode_run_id"]
        assert result["termination_query_context"]["queried_date_raw"] == source["paused_date_raw"]
        assert result["termination_query_context"]["active_war_signature"] == [{
            "war_id": source["war_id"],
            "player_side": source["player_side"],
            "player_is_primary_war_leader": True,
            "primary_opponent_character_id": source["primary_opponent_character_id"],
            "player_relative_war_score": source["player_relative_war_score"],
            "targeted_title_ids": source["targeted_title_ids"],
        }]

        options = result["war_termination_options"]
        surrender = options["options"]["surrender"]
        assert options["player_side"] == "defender"
        assert options["active_casus_belli_identity"] == {
            "database_index": 17, "canonical_key": "individual_county_de_jure_cb"
        }
        assert surrender["available"] is True
        assert surrender["native_validator_passed"] is True
        assert surrender["recipient_response"]["would_accept_now"] is True
        assert surrender["terms_observable"] is False
        assert surrender["terms"] == {
            "status": "unavailable", "reason": "cb_specific_terms_not_observable"
        }
        assert options["options"]["white_peace"]["available"] is False
        assert options["options"]["victory"]["available"] is False

        war = {
            "war_id": source["war_id"],
            "player_side": source["player_side"],
            "player_is_primary_war_leader": True,
            "player_relative_war_score": source["player_relative_war_score"],
            "targeted_title_ids": source["targeted_title_ids"],
        }
        self.assertFalse(_de_jure_no_safe_route_surrender_candidate(war, options))
        self.assertFalse(_de_jure_no_safe_route_white_peace_candidate(war, options))
        self.assertIsNone(_de_jure_no_safe_route_exit_plan(
            {"paused": True, "snapshot_id": source["snapshot_id"],
             "revision": source["snapshot_revision"],
             "native_revision": source["native_revision"],
             "date_raw": source["paused_date_raw"],
             "episode_run_id": source["episode_run_id"],
             "diagnostics": {"connection_generation": result["queried_connection_generation"]}},
            active_wars=[war],
            termination_by_war_id={source["war_id"]: options},
            available_steps={f"surrender-war-{source['war_id']}"},
            active_war_summary=[war],
            route_rejections=[{"reason": "no_safe_exact_route"}],
        ))
        assert request["later_formal_high_water"]["qualified_turns"] == 12
        assert request["later_formal_high_water"]["war_31_still_active"] is True
        assert request["later_formal_high_water"]["termination_action_submitted"] is False


if __name__ == "__main__":
    unittest.main()
