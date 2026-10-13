"""Four new resolved-gift follow-up branches; no gift lifecycle replay."""

from copy import deepcopy
from pathlib import Path
from threading import RLock

import pytest

from xar_autoplayer.faction_gift_outcome_v1 import (
    COLD_RECOVERY_STEP, QUERY_PLAYER_FACTION_ALERTS_V1_STEP,
    RECEIPT_STEP, SUBMIT_STEP, query_resolved_faction_gift_outcome_v1,
)


@pytest.mark.parametrize("world", ["still_member", "recipient_left", "faction_known_absent", "unavailable"])
def test_resolved_gift_current_material_four_branches(tmp_path: Path, world: str) -> None:
    snapshot = {"snapshot_id": "native:9", "revision": 9, "native_revision": 12,
                "date_raw": 53290200, "episode_run_id": "native-29829-original",
                "paused": True, "map_ready": True,
                "played_character": {"character_id": 29829, "alive": True}}
    pending = {"request_id": "gift-original", "episode_run_id": snapshot["episode_run_id"],
               "pre_player_character_id": 29829, "source_faction_id": 50331692,
               "recipient_character_id": 33435, "pre_date_raw": 53290176,
               "gold_cost_raw": 15000000, "opinion_delta": 37,
               "pre_recipient_opinion_of_player": -25,
               "pre_source_faction_power_raw": 11000000,
               "pre_source_faction_discontent_raw": 5000000}
    receipt = {"schema_version": 1, "request_id": "gift-original", "status": "mitigated",
               "postcondition_verified": True, "mitigation_applied": True,
               "player_character_id": 29829, "source_faction_id": 50331692,
               "recipient_character_id": 33435, "post_observed_date_raw": 53290176,
               "post_gift_opinion_present": True, "post_gift_opinion_modifier_value": 37,
               "threat_resolved": False}
    history = [{"command": SUBMIT_STEP, "ok": True,
                "result": {"pending_ledger": {"pending": pending}}},
               {"command": RECEIPT_STEP, "ok": True, "result": {"receipt": receipt}}]
    ledger = tmp_path / "faction-gift-pending-v1.json"
    ledger.write_text('{"pending":null,"resolved_request_outcomes":{"gift-original":"applied"}}', encoding="utf-8")
    ledger_before = ledger.read_bytes()
    present = world != "faction_known_absent"
    members = [33435, 35637] if world == "still_member" else [35637]
    observation = {
        "available": world != "unavailable", "paused": True,
        "snapshot_revision": 12, "native_snapshot_revision": 12,
        "observed_date_raw": snapshot["date_raw"], "player_character_id": 29829,
        "source_faction_requery_complete": True, "queried_source_faction_id": 50331692,
        "source_faction_present": present, "source_faction_targeting_player": present,
        "source_faction_leader_character_id": members[0] if present else None,
        "source_faction_member_character_ids": members if present else [],
        "source_faction_metrics_available": present,
        "source_faction_power_raw": 9000000 if present else 0,
        "source_faction_discontent_raw": 4000000 if present else 0,
        "source_faction_metric_scale": 100000 if present else 0,
        "recipient_identity_resolved": True, "recipient_character_id": 33435,
        "recipient_opinion_query_complete": True, "recipient_opinion_of_player": 10,
        "gift_opinion_present": True, "gift_opinion_modifier_value": 37,
    }
    alert_row = {"faction_id": 50331692, "target_character_id": 29829,
                 "leader_character_id": members[0], "character_member_ids": members,
                 "power": {"raw": 9000000, "scale": 100000},
                 "power_threshold": {"raw": 8000000, "scale": 100000},
                 "discontent": {"raw": 4000000, "scale": 100000},
                 "discontent_per_month": {"raw": -100000, "scale": 100000},
                 "months_until_max_discontent": 0, "dangerous_by_stock_rule": False,
                 "faction_at_war": False}

    class Driver:
        _history_lock = RLock()

        def __init__(self):
            self._command_history = deepcopy(history)
            self.sent = []
            self.alert_calls = []
            self.endpoint = self
            self.state = self

        def take_internal_semantic_snapshot(self):
            return deepcopy(snapshot)

        def send(self, payload):
            self.sent.append(payload)

        def wait_for_command_result(self, request_id, timeout_seconds):
            return {"type": "command_result", "protocol_version": 1,
                    "request_id": request_id, "ok": True, "result": {
                        "step": COLD_RECOVERY_STEP, "accepted": True,
                        "status": "independent_read_complete", "native": {
                            "failure_flags": 0, "observation": deepcopy(observation)}}}

        def execute_step(self, step, *, expected_revision):
            self.alert_calls.append((step, expected_revision))
            return {"player_faction_alerts": {
                "status": "available", "snapshot_revision": 12,
                "date_raw": snapshot["date_raw"], "player_character_id": 29829,
                "readiness": {"same_frame_ready": True, "targeting_rows_ready": True,
                              "stock_dangerous_predicate_ready": True},
                "targeting_factions": [deepcopy(alert_row)] if present else []}}

        def _record_command(self, step, *, ok, result):
            self._command_history.append({"command": step, "ok": ok, "result": result})

    driver = Driver()
    result = query_resolved_faction_gift_outcome_v1(driver, request_id="gift-original", expected_revision=9)
    assert len(driver.sent) == 1
    assert driver.sent[0]["step"] == COLD_RECOVERY_STEP
    assert driver.sent[0]["source_faction_id"] == 50331692
    assert driver.sent[0]["recipient_character_id"] == 33435
    assert ledger.read_bytes() == ledger_before
    assert driver._command_history[:2] == history
    assert result["original"]["receipt"] == receipt
    assert result["attributed_to_gift"] is False
    if world == "unavailable":
        assert result["status"] == "unavailable"
        assert "faction_outcome" not in result
        assert driver.alert_calls == []
        assert len(driver._command_history) == 2
    else:
        assert result["status"] == "observed"
        assert result["faction_outcome"] == world
        assert result["current_observation"] == observation
        assert result["followup_date_advanced"] is True
        assert result["gift_submit_performed"] is False
        assert result["pending_resolution_performed"] is False
        assert driver.alert_calls == [(QUERY_PLAYER_FACTION_ALERTS_V1_STEP, 9)]
        if present:
            assert result["current_alert"]["row"] == alert_row
            assert result["current_alert"]["row"]["discontent_per_month"]["raw"] == -100000
        else:
            assert result["current_alert"]["status"] == "not_in_current_targeting_vector"
            assert result["current_alert"]["row"] is None
