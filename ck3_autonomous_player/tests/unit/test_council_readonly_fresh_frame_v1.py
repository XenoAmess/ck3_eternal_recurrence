"""Synthetic replay of the actual38b Chancellor-read/Steward-stale ordering.

The native stale error comes from the closed actual attempt. Positive terminal
DTOs reuse the existing serializer fixture shape with explicitly synthetic
role/build/frame substitutions. The subsequent native11/public3 snapshot is a
deterministic fixture, not a claimed actual captured frame. No pipe or CK3 opens.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from test_chancellor_council_query_v1 import _MailboxDriver, _terminal
from xar_autoplayer.bridge.council_composition_candidates_contract import (
    CHANCELLOR_POSITION_KEY, STEWARD_POSITION_KEY,
)
from xar_autoplayer.bridge.council_private_transport_v1 import PRIVATE_GATES_STEP, PRIVATE_STATUS_STEP
from xar_autoplayer.bridge.current_first_heir_relationship_private_transport import _same_frame_campaign_root_result
from xar_autoplayer.private_council_formal_consumer_v1 import (
    LEDGER_FILENAME, ROOT_QUERY_STEP, plan_council_private,
)

ACTUAL_STALE_ERROR = "nonwar private snapshot revision is stale or malformed"


def _bound_terminal(role: str, native_revision: int) -> dict[str, object]:
    result = _terminal(role, PRIVATE_GATES_STEP)
    result["snapshot_revision"] = native_revision
    frame = result["council_final_gates"]["council_composition_candidates"]["snapshot"]
    frame.update(snapshot_id=f"native:{native_revision}", public_revision=native_revision,
                 native_revision=native_revision)
    return result


class _RoleReadDriver(_MailboxDriver):
    allow_private_council_action = True

    def __init__(self):
        super().__init__([])
        self.snapshot.update(snapshot_id="native:10", revision=2, native_revision=10,
                             episode_run_id="synthetic-readonly-refresh")
        self.publish_new_frame = False
        self.rejected_frames = []
        self.root_calls = []
        self.chancellor = _bound_terminal(CHANCELLOR_POSITION_KEY, 10)
        self.steward = _bound_terminal(STEWARD_POSITION_KEY, 11)

    def take_internal_semantic_snapshot(self) -> dict[str, object]:
        if self.publish_new_frame:
            self.publish_new_frame = False
            # NativeState updates public revision when this state_snapshot arrives.
            self.snapshot.update(snapshot_id="native:11", revision=3, native_revision=11)
        return copy.deepcopy(self.snapshot)

    def _response(self, request_id: str, timeout: float) -> dict[str, object]:
        packet = self.sent[-1]
        frame = {"type": "command_result", "protocol_version": 1,
                 "request_id": request_id, "ok": True}
        if packet["step"] == PRIVATE_STATUS_STEP:
            return {**frame, "result": copy.deepcopy(self.chancellor)}
        assert packet["step"] == PRIVATE_GATES_STEP
        if packet["position_key"] == CHANCELLOR_POSITION_KEY:
            return {**frame, "result": {"private_council_transport": True,
                    "advertised": False, "step": PRIVATE_GATES_STEP, "status": "pending"}}
        assert packet["position_key"] == STEWARD_POSITION_KEY
        if packet["expected_revision"] == 10:
            self.publish_new_frame = True
            rejected = {**frame, "ok": False, "error": ACTUAL_STALE_ERROR}
            self.rejected_frames.append(rejected)
            return rejected
        assert packet["expected_revision"] == 11
        return {**frame, "result": copy.deepcopy(self.steward)}

    def root_result(self, snapshot: dict[str, object]) -> dict[str, object]:
        incumbent = self.chancellor["council_final_gates"]["council_composition_candidates"]["position"]["incumbent_character_id"]
        return {"status": "available", "query_sequence": 1,
                "queried_snapshot_id": snapshot["snapshot_id"],
                "queried_revision": snapshot["revision"],
                "queried_native_revision": snapshot["native_revision"],
                "campaign_root_context": {"status": "available",
                    "snapshot_revision": snapshot["native_revision"],
                    "date_raw": snapshot["date_raw"],
                    "player_character_id": snapshot["played_character"]["character_id"],
                    "council": {"positions": [{"position_key": CHANCELLOR_POSITION_KEY,
                        "incumbent_character_id": incumbent}]}}}

    def execute_step(self, step: str, *, expected_revision: int) -> dict[str, object]:
        assert step == ROOT_QUERY_STEP
        assert expected_revision == self.snapshot["revision"]
        self.root_calls.append((step, expected_revision))
        return self.root_result(self.snapshot)


def test_second_role_read_rebinds_after_native_stale_rejection(tmp_path: Path) -> None:
    driver = _RoleReadDriver()
    before = driver.take_internal_semantic_snapshot()
    cached_root = driver.root_result(before)
    assert _same_frame_campaign_root_result(cached_root, before) is cached_root
    chancellor_payload = driver.chancellor["council_final_gates"]["council_composition_candidates"]
    ledger = {"schema": "xar.ck3.private-council-formal/v1", "pending": None,
              "applied": {"episode_run_id": before["episode_run_id"],
                  "candidate_character_id": chancellor_payload["position"]["incumbent_character_id"],
                  "source_query": {"council_composition_candidates": chancellor_payload},
                  "receipt": {"council_assign_councillor_receipt": {"post_snapshot_id": "native:9"}}}}
    (tmp_path / LEDGER_FILENAME).write_text(json.dumps(ledger), encoding="utf-8")

    planned = plan_council_private(
        driver, {"revision": 2, "snapshot_id": "native:10", "plan": {"selected_step": None}},
        before, [], set(), state_dir=tmp_path, campaign_root_result=cached_root,
    )

    requests = [(packet["position_key"], packet["expected_revision"])
                for packet in driver.sent if packet["step"] == PRIVATE_GATES_STEP]
    assert requests == [(CHANCELLOR_POSITION_KEY, 10), (STEWARD_POSITION_KEY, 10),
                        (STEWARD_POSITION_KEY, 11)]
    assert driver.sent[1]["step"] == PRIVATE_STATUS_STEP
    assert driver.rejected_frames[0]["error"] == ACTUAL_STALE_ERROR
    assert len(driver.rejected_frames) == 1
    query = planned["plan"]["council_private_query"]
    assert query["status"] == "available"
    assert query["queried_snapshot_id"] == "native:11"
    assert query["queried_revision"] == 3
    assert query["queried_native_revision"] == 11
    assert query["source_frame"] == {"snapshot_id": "native:11", "revision": 3,
            "native_revision": 11, "date_raw": before["date_raw"],
            "player_character_id": before["played_character"]["character_id"], "paused": True}
    payload = query["council_composition_candidates"]
    assert payload["snapshot"]["snapshot_id"] == "native:11"
    assert payload["snapshot"]["public_revision"] == 11  # Native DTO quote; frontend revision is3.
    assert payload["position"]["position_key"] == STEWARD_POSITION_KEY
    assert planned["revision"] == 3 and planned["snapshot_id"] == "native:11"
    assert _same_frame_campaign_root_result(cached_root, driver.snapshot) is None
    assert driver.root_calls == [(ROOT_QUERY_STEP, 3)]
    consumed = planned["plan"]["council_receipt_consumed"]
    assert consumed["next_turn_consumed"] is True
    assert consumed["next_turn_native_revision"] == 11
    assert consumed["next_turn_snapshot_id"] == "native:11"
    assert json.loads((tmp_path / LEDGER_FILENAME).read_text(encoding="utf-8"))["pending"] is None
    assert all(packet["step"] in {PRIVATE_GATES_STEP, PRIVATE_STATUS_STEP} for packet in driver.sent)
