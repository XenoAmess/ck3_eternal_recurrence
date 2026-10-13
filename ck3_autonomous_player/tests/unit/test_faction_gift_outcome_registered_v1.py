"""One new MCP -> Service -> real native Driver wrapper -> follow-up case."""

import asyncio
from copy import deepcopy
from pathlib import Path
from threading import RLock

from xar_autoplayer.bridge import mcp_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.faction_gift_outcome_v1 import (
    COLD_RECOVERY_STEP, QUERY_PLAYER_FACTION_ALERTS_V1_STEP,
    RECEIPT_STEP, STEP, SUBMIT_STEP,
)


def test_registered_resolved_gift_reads_original_material_without_resubmit(tmp_path: Path) -> None:
    from mcp import Client

    current = {"snapshot_id": "native:9", "revision": 9, "native_revision": 12,
               "date_raw": 53290200, "episode_run_id": "native-29829-original",
               "paused": True, "map_ready": True,
               "played_character": {"character_id": 29829, "alive": True}}
    pending = {"request_id": "gift-original", "episode_run_id": current["episode_run_id"],
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
    observation = {"available": True, "paused": True, "snapshot_revision": 12,
                   "native_snapshot_revision": 12, "observed_date_raw": current["date_raw"],
                   "player_character_id": 29829, "source_faction_requery_complete": True,
                   "queried_source_faction_id": 50331692, "source_faction_present": True,
                   "source_faction_targeting_player": True,
                   "source_faction_leader_character_id": 35637,
                   "source_faction_member_character_ids": [35637],
                   "source_faction_metrics_available": True,
                   "source_faction_power_raw": 9000000,
                   "source_faction_discontent_raw": 4000000,
                   "source_faction_metric_scale": 100000,
                   "recipient_identity_resolved": True, "recipient_character_id": 33435,
                   "recipient_opinion_query_complete": True, "recipient_opinion_of_player": 10,
                   "gift_opinion_present": True, "gift_opinion_modifier_value": 37}
    row = {"faction_id": 50331692, "target_character_id": 29829,
           "leader_character_id": 35637, "character_member_ids": [35637],
           "dangerous_by_stock_rule": False, "faction_at_war": False,
           "discontent_per_month": {"raw": -100000, "scale": 100000}}
    history = [{"command": SUBMIT_STEP, "ok": True,
                "result": {"pending_ledger": {"pending": pending}}},
               {"command": RECEIPT_STEP, "ok": True, "result": {"receipt": receipt}}]
    ledger = tmp_path / "faction-gift-pending-v1.json"
    ledger.write_text('{"pending":null,"resolved_request_outcomes":{"gift-original":"applied"}}', encoding="utf-8")
    original_bytes = ledger.read_bytes()

    class FixtureNativeDriver(NativeHeadlessGameplayDriver):
        # Only the existing wrapper is inherited. No native endpoint/process is
        # constructed; all history and returned observations are synthetic.
        def __init__(self):
            self.allow_private_faction_gift_query = True
            self._history_lock = RLock()
            self._command_history = deepcopy(history)
            self.endpoint = self
            self.state = self
            self.sent = []
            self.alert_calls = []

        def take_internal_semantic_snapshot(self):
            return deepcopy(current)

        def send(self, payload):
            assert payload["step"] == COLD_RECOVERY_STEP
            self.sent.append(payload)

        def wait_for_command_result(self, request_id, timeout_seconds):
            return {"type": "command_result", "protocol_version": 1,
                    "request_id": request_id, "ok": True, "result": {
                        "step": COLD_RECOVERY_STEP, "accepted": True,
                        "status": "independent_read_complete", "native": {
                            "failure_flags": 0, "observation": deepcopy(observation)}}}

        def execute_step(self, step, *, expected_revision):
            assert step == QUERY_PLAYER_FACTION_ALERTS_V1_STEP
            self.alert_calls.append((step, expected_revision))
            return {"player_faction_alerts": {"status": "available",
                    "snapshot_revision": 12, "date_raw": current["date_raw"],
                    "player_character_id": 29829, "readiness": {
                        "same_frame_ready": True, "targeting_rows_ready": True,
                        "stock_dangerous_predicate_ready": True},
                    "targeting_factions": [deepcopy(row)]}}

        def _record_command(self, step, *, ok, result):
            assert step == STEP
            self._command_history.append({"command": step, "ok": ok, "result": result})

    driver = FixtureNativeDriver()
    assert type(driver).query_resolved_faction_gift_outcome_v1 is NativeHeadlessGameplayDriver.query_resolved_faction_gift_outcome_v1

    async def call_registered():
        async with Client(mcp_server.create_server(driver)) as client:
            return await client.call_tool("ck3_query_resolved_faction_gift_outcome_v1", {
                "request_id": "gift-original", "expected_revision": 9})

    result = asyncio.run(call_registered())
    assert not result.is_error, result.content
    outcome = result.structured_content
    assert outcome["status"] == "observed"
    assert outcome["faction_outcome"] == "recipient_left"
    assert outcome["original"]["receipt"] == receipt
    assert outcome["current_observation"] == observation
    assert outcome["current_alert"]["row"] == row
    assert outcome["attributed_to_gift"] is False
    assert outcome["gift_submit_performed"] is False
    assert outcome["pending_resolution_performed"] is False
    assert len(driver.sent) == 1
    assert driver.sent[0]["source_faction_id"] == 50331692
    assert driver.sent[0]["recipient_character_id"] == 33435
    assert driver.alert_calls == [(QUERY_PLAYER_FACTION_ALERTS_V1_STEP, 9)]
    assert driver._command_history[:2] == history
    assert len(driver._command_history) == 3
    assert ledger.read_bytes() == original_bytes
