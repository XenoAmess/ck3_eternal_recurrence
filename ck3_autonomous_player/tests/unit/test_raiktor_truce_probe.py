"""Contract tests for the narrow G2 Raiktor truce probe."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.raiktor_truce_probe import (  # noqa: E402
    EXPECTED_EXECUTABLE_SHA256,
    EXPECTED_GAME_VERSION,
    EXPECTED_TRUCE_OBSERVER,
    validate_pointer_contract,
    validate_truce_probe,
)


WAR_ID = 16_777_290
CHARACTER_ID = 29_829
DEFENDER_ID = 17_116
DATE_RAW = 53_175_816


def _snapshot(*, revision: int = 73) -> dict[str, object]:
    return {
        "snapshot_id": "native:4",
        "revision": revision,
        "native_revision": 4,
        "date_raw": DATE_RAW,
        "paused": True,
        "episode_run_id": "g2-truce-probe-fixture",
        "played_character": {"character_id": CHARACTER_ID, "alive": True},
        "active_wars": [
            {
                "war_id": WAR_ID,
                "player_side": "attacker",
                "player_is_primary_war_leader": True,
                "primary_opponent_character_id": DEFENDER_ID,
            }
        ],
    }


def _terms(*, days: int = 1_825) -> dict[str, object]:
    return {
        "war_termination_terms": {
            "status": "available",
            "war_id": WAR_ID,
            "claimant_character_id": CHARACTER_ID,
            "casus_belli": {
                "canonical_key": "raiktor_claim_cb",
                "database_index": 411,
            },
            "provenance": {
                "game_version": EXPECTED_GAME_VERSION,
                "executable_sha256": EXPECTED_EXECUTABLE_SHA256,
                "truce_observer": EXPECTED_TRUCE_OBSERVER,
            },
            "truce": {
                "direction": "primary_attacker_toward_primary_defender",
                "result": "defeat",
                "evaluated_days_observable": True,
                "evaluated_days": days,
                "actual_expiry_observable": False,
                "expiry_date_raw": None,
            },
            "readiness": {"truce_ready": True},
        }
    }


def _query(*, days: int = 1_825, sequence: int = 1) -> dict[str, object]:
    value = _terms(days=days)
    value["query_sequence"] = sequence
    value["queried_revision"] = 73
    value["queried_snapshot_id"] = "native:4"
    value["queried_native_revision"] = 4
    return value


def _pointer_checks() -> dict[str, bool]:
    path = (
        PROJECT_ROOT
        / "native_bridge"
        / "research"
        / "fixtures"
        / "raiktor_surrender_truce_v1_source_contract.json"
    )
    return validate_pointer_contract(json.loads(path.read_text(encoding="utf-8")))


class RaiktorTruceProbeTests(unittest.TestCase):
    def test_frozen_pointer_contract_covers_unique_caddtruce_and_live_gap(self) -> None:
        checks = _pointer_checks()
        self.assertTrue(checks["unique_caddtruce"])
        self.assertTrue(checks["double_nonnegative_read"])
        self.assertTrue(checks["expiry_not_claimed"])
        self.assertTrue(checks["ok"])

    def test_mcp_probe_accepts_two_same_frame_read_only_samples(self) -> None:
        first = _query()
        second = copy.deepcopy(first)
        second["query_sequence"] = 2
        checks = validate_truce_probe(
            before=_snapshot(),
            between=_snapshot(),
            after=_snapshot(),
            first=first,
            second=second,
            tool_names=[
                "ck3_get_capabilities",
                "ck3_take_snapshot",
                "ck3_query_war_termination_terms",
            ],
            allowed_gameplay_commands=[
                f"query-war-termination-terms-v1-{WAR_ID}",
                f"query-war-termination-terms-v1-{WAR_ID}",
            ],
            mutation_commands=[],
            expected_war_id=WAR_ID,
            expected_character_id=CHARACTER_ID,
            expected_date_raw=DATE_RAW,
            pointer_contract_checks=_pointer_checks(),
        )
        self.assertTrue(checks["same_paused_frame"])
        self.assertTrue(checks["war_id_and_roles"])
        self.assertTrue(checks["exact_provenance"])
        self.assertTrue(checks["pointer_only_contract_bound"])
        self.assertTrue(checks["raiktor_truce_shape"])
        self.assertTrue(checks["evaluated_days_equal"])
        self.assertTrue(checks["ok"])

    def test_mcp_probe_rejects_frame_drift_duration_drift_and_writes(self) -> None:
        first = _query()
        second = _query(days=1_826, sequence=2)
        checks = validate_truce_probe(
            before=_snapshot(),
            between=_snapshot(revision=74),
            after=_snapshot(),
            first=first,
            second=second,
            tool_names=list(
                (
                    "ck3_get_capabilities",
                    "ck3_take_snapshot",
                    "ck3_query_war_termination_terms",
                )
            ),
            allowed_gameplay_commands=[
                f"query-war-termination-terms-v1-{WAR_ID}",
                f"surrender-war-{WAR_ID}",
            ],
            mutation_commands=[f"offer-white-peace-{WAR_ID}"],
            expected_war_id=WAR_ID,
            expected_character_id=CHARACTER_ID,
            expected_date_raw=DATE_RAW,
            pointer_contract_checks=_pointer_checks(),
        )
        self.assertFalse(checks["same_paused_frame"])
        self.assertFalse(checks["evaluated_days_equal"])
        self.assertFalse(checks["read_only_tool_boundary"])
        self.assertFalse(checks["ok"])


if __name__ == "__main__":
    unittest.main()
