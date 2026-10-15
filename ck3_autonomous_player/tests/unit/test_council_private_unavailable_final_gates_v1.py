"""An empty native final-gates read cannot become an assignment candidate."""

import json
from pathlib import Path

import pytest

from xar_autoplayer.bridge import council_private_transport_v1 as transport
from xar_autoplayer.private_council_formal_consumer_v1 import select_council_candidate_v1


FIXTURES = Path(__file__).parents[1] / "fixtures/native_12002/governance"


def _empty_gates(status="available"):
    return {
        "schema": "xar.ck3.council-application-main/v1",
        "step": transport.PRIVATE_GATES_STEP,
        "accepted": True, "backend_id": "native-headless",
        "query_sequence": 917, "snapshot_revision": 34, "status": status,
        "private": True, "advertised": False, "native_helper_invocations_delta": 0,
        "council_final_gates": {
            "schema": "xar.ck3.private.council-final-gates/v1",
            "status": "unavailable", "unavailable_reason": "no_native_final_gate_rows",
            "candidate_count": 0, "rows": [],
        },
    }


def _parse(raw):
    return transport.normalize_council_private_query_result_v1(
        raw, expected_request={"public_revision": 34},
        query_step=transport.PRIVATE_GATES_STEP)


@pytest.mark.parametrize("native_status", ["available", "unavailable"])
def test_empty_final_gates_are_readonly_unavailable(native_status):
    raw = _empty_gates(native_status)
    result = _parse(raw)
    assert result["native_envelope_status"] == native_status
    assert result["status"] == "unavailable"
    assert result["read_only"] is True
    assert result["native_helper_invocations_delta"] == 0
    assert result["query_sequence"] == 917
    assert result["council_final_gates"]["rows"] == []
    assert "council_composition_candidates" not in result
    decision = select_council_candidate_v1(result)
    assert decision["outcome"] == "QUERY_UNAVAILABLE"
    assert "selected_candidate" not in decision
    assert raw["status"] == native_status


def test_available_candidates_keep_the_full_contract():
    raw = json.loads((FIXTURES / "council-gates.json").read_text(encoding="utf-8"))["result"]
    request = {"public_revision": 8, "expected_snapshot_id": "native:council12002",
               "native_revision": 7, "date_raw": 53178264,
               "owner_character_id": 16777217, "position_key": "councillor_steward"}
    result = transport.normalize_council_private_query_result_v1(
        raw, expected_request=request, query_step=transport.PRIVATE_GATES_STEP)
    assert result["status"] == "available"
    assert result["council_final_gates"]["candidate_count"] == 2
    assert len(result["council_composition_candidates"]["candidates"]) == 2


def test_same_frame_private_transport_sends_only_the_read():
    class Driver:
        command_timeout_seconds = 2.0

        def __init__(self):
            self.sent = []
            self.endpoint = self
            self.state = self

        def take_internal_semantic_snapshot(self):
            return {"snapshot_id": "native:34", "revision": 33,
                    "native_revision": 34, "date_raw": 53235120,
                    "paused": True, "map_ready": True,
                    "played_character": {"character_id": 31254, "alive": True}}

        def send(self, frame):
            self.sent.append(frame)

        def wait_for_command_result(self, request_id, remaining):
            return {"type": "command_result", "protocol_version": 1,
                    "request_id": request_id, "ok": True,
                    "result": _empty_gates()}

    driver = Driver()
    result = transport.query_council_private_v1(
        driver, expected_revision=33, query_step=transport.PRIVATE_GATES_STEP)
    assert result["status"] == "unavailable"
    assert result["queried_snapshot_id"] == "native:34"
    assert result["queried_native_revision"] == 34
    assert result["source_frame"]["date_raw"] == 53235120
    assert [frame["step"] for frame in driver.sent] == [transport.PRIVATE_GATES_STEP]


@pytest.mark.parametrize("change", [
    lambda w: w.__setitem__("accepted", False),
    lambda w: w.__setitem__("step", "assign-councillor-v1"),
    lambda w: w.__setitem__("snapshot_revision", 33),
    lambda w: w.__setitem__("status", "pending"),
    lambda w: w.__setitem__("private", False),
    lambda w: w.__setitem__("native_helper_invocations_delta", 1),
    lambda w: w["council_final_gates"].__setitem__("status", "available"),
    lambda w: w["council_final_gates"].__setitem__("candidate_count", 1),
    lambda w: w["council_final_gates"].__setitem__("rows", [{}]),
    lambda w: w["council_final_gates"].__setitem__("council_composition_candidates", {}),
    lambda w: w.__setitem__("council_composition_candidates", {}),
])
def test_bad_envelope_or_candidate_claim_is_rejected(change):
    raw = _empty_gates()
    change(raw)
    with pytest.raises(ValueError):
        _parse(raw)
