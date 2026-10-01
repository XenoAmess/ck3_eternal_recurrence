"""Consume JSON emitted by the 1.20.0.2 production serializers offline.

These files come from native provider fixtures, not paused game captures.
No test opens a pipe, resolves a real process or sends desktop input.
"""

from __future__ import annotations

import asyncio
import copy
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.player_faction_alerts_contract import (
    QUERY_PLAYER_FACTION_ALERTS_V1_CAPABILITY,
    QUERY_PLAYER_FACTION_ALERTS_V1_STEP,
    normalize_player_faction_alerts_v1,
)
from xar_autoplayer.bridge.council_composition_candidates_contract import (
    build_council_composition_candidates_request_v1,
)
from xar_autoplayer.bridge.council_assign_councillor_action_contract import (
    build_assign_councillor_request_v1,
    normalize_assign_councillor_ack_v1,
    normalize_assign_councillor_receipt_v1,
)
from xar_autoplayer.bridge.council_private_transport_v1 import (
    PRIVATE_GATES_STEP,
    PRIVATE_ASSIGN_STEP,
    PRIVATE_QUERY_STEP,
    PRIVATE_RECEIPT_STEP,
    PRIVATE_STATUS_STEP,
    normalize_council_private_query_result_v1,
    query_council_assign_receipt_private_v1,
    query_council_private_v1,
    submit_council_assign_private_v1,
)
from xar_autoplayer.bridge import council_private_transport_v1 as council_transport
from xar_autoplayer.bridge import faction_gift_formal_route_v1 as gift_formal_route
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.faction_gift_private_transport_v1 import (
    query_faction_gift_private_candidate_v1,
)
from xar_autoplayer.faction_gift_cold_recovery_contract_v1 import (
    evaluate_faction_gift_cold_recovery_v1,
)
from xar_autoplayer.faction_gift_pending_v1 import (
    begin_faction_gift_submission_v1,
    complete_faction_gift_after_independent_receipt_v1,
    mark_faction_gift_ack_pending_v1,
)
from xar_autoplayer.bridge.version_identity import CK3_12002


FIXTURES = PROJECT_ROOT / "tests/fixtures/native_12002/governance"


def _wire(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_native_faction_wire_preserves_percent_points_and_leaderless_members() -> None:
    raw = _wire("faction-alerts.json")
    normalized = normalize_player_faction_alerts_v1(
        raw,
        expected_date_raw=raw["date_raw"],
        expected_snapshot_revision=raw["snapshot_revision"],
        expected_game_version=CK3_12002.game_version,
        expected_executable_sha256=CK3_12002.executable_sha256,
    )
    assert normalized == raw
    assert normalized["readiness"]["alert_ready"] is True
    assert normalized["targeting_faction_count"] == 3
    liberty, populist, peasant = normalized["targeting_factions"]
    assert liberty["power"] == {"raw": 11_000_000, "scale": 100_000}
    assert liberty["discontent"] == {"raw": 2_500_000, "scale": 100_000}
    assert populist["leader_character_id"] is None
    assert populist["character_member_ids"] == []
    assert populist["county_member_title_ids"] == [50_331_649]
    assert peasant["months_until_max_discontent"] == 0
    assert peasant["dangerous_by_stock_rule"] is True
    assert normalized["planner_projection"]["dangerous_faction_ids"] == [
        33_554_433, 33_554_434, 33_554_435,
    ]
    assert normalized["county_exposures"][0]["target_character_id"] != (
        normalized["player_character_id"]
    )


class _FactionSdkDriver(NativeHeadlessGameplayDriver):
    """Feed the actual native DTO into the production driver and service path."""

    def __init__(self) -> None:
        self.frame = _wire("faction-alerts.json")
        self.calls = 0

    def take_snapshot(self) -> dict[str, object]:
        return {
            "format_version": 1, "snapshot_id": "native:41", "revision": 17,
            "native_revision": self.frame["snapshot_revision"],
            "date_raw": self.frame["date_raw"], "paused": True,
            "backend_id": "native-headless", "source": "named-pipe",
            "episode_run_id": "native-16777217-fixture", "active_wars": [],
            "diagnostics": {"hello": {
                "expected_ck3_version": CK3_12002.game_version,
                "expected_ck3_sha256": CK3_12002.executable_sha256,
            }},
        }

    def capabilities(self) -> dict[str, object]:
        return {
            "format_version": 1, "backend_id": "native-headless", "source": "named-pipe",
            "snapshot": True, "wait_for_change": False,
            "action_steps": [QUERY_PLAYER_FACTION_ALERTS_V1_STEP],
            "bridge_capabilities": [QUERY_PLAYER_FACTION_ALERTS_V1_CAPABILITY],
        }

    def execute_step(self, step: str, *, expected_revision: int | None = None) -> dict[str, object]:
        assert step == QUERY_PLAYER_FACTION_ALERTS_V1_STEP
        return self._execute_player_faction_alerts_v1_query(expected_revision=expected_revision)

    def _execute_primitive_step(
        self, step: str, *, expected_revision: int, required_capability: str,
    ) -> dict[str, object]:
        assert step == QUERY_PLAYER_FACTION_ALERTS_V1_STEP
        assert expected_revision == 17
        assert required_capability == QUERY_PLAYER_FACTION_ALERTS_V1_CAPABILITY
        self.calls += 1
        return {
            "step": step, "accepted": True, "status": self.frame["status"],
            "query_sequence": 1, "snapshot_revision": self.frame["snapshot_revision"],
            "player_faction_alerts": self.frame,
            "player_faction_alerts_ready": self.frame["readiness"]["alert_ready"],
            "backend_id": "native-headless",
        }


def test_actual_faction_wire_runs_through_driver_service_and_official_mcp_sdk() -> None:
    from mcp import Client

    driver = _FactionSdkDriver()
    async def exercise():
        async with Client(create_server(driver)) as client:
            return await client.call_tool(
                "ck3_query_player_faction_alerts_v1", {"expected_revision": 17},
            )

    response = asyncio.run(exercise())
    assert response.is_error is False
    payload = response.structured_content
    assert payload["status"] == "available"
    assert payload["build"]["version"] == CK3_12002.game_version
    assert payload["player_faction_alerts_ready"] is True
    assert payload["player_faction_alerts"] == driver.frame
    assert driver.calls == 1


def _council_request(payload: dict[str, object]) -> dict[str, object]:
    snapshot = payload["snapshot"]
    return build_council_composition_candidates_request_v1(
        expected_snapshot_id=snapshot["snapshot_id"],
        public_revision=snapshot["public_revision"],
        native_revision=snapshot["native_revision"],
        date_raw=snapshot["date_raw"],
        owner_character_id=payload["owner_character_id"],
    )


def test_native_council_source_query_ack_and_independent_incumbent_receipt() -> None:
    result = _wire("council-query.json")["result"]
    query = normalize_council_private_query_result_v1(
        result,
        expected_request=_council_request(result["council_composition_candidates"]),
    )
    candidates = query["council_composition_candidates"]
    assert [row["main_skill"]["value"] for row in candidates["candidates"]] == [22, 17]
    native_ack = _wire("council-ack.json")["result"]["council_assign_councillor_ack"]
    request = build_assign_councillor_request_v1(
        candidates,
        candidate_character_id=native_ack["candidate_character_id"],
        request_id=native_ack["action_request_id"],
    )
    ack = normalize_assign_councillor_ack_v1(native_ack, expected_request=request)
    assert ack["verification_pending"] is True
    native_receipt = _wire("council-receipt.json")["result"]["council_assign_councillor_receipt"]
    receipt = normalize_assign_councillor_receipt_v1(native_receipt, expected_ack=ack)
    assert receipt["status"] == "applied"
    assert receipt["incumbent_character_id"] == request.candidate_character_id


def test_native_council_four_final_gates_keep_native_candidate_identity() -> None:
    result = _wire("council-gates.json")["result"]
    payload = result["council_final_gates"]["council_composition_candidates"]
    normalized = normalize_council_private_query_result_v1(
        result, expected_request=_council_request(payload),
        query_step=PRIVATE_GATES_STEP,
    )
    gates = normalized["council_final_gates"]
    assert gates["candidate_count"] == 2
    assert all(row["final_gate_available"] is True for row in gates["rows"])
    assert all(row["incumbent_can_be_fired"] is True for row in gates["rows"])


class _CouncilMailboxDriver:
    """Only protocol request IDs change when replaying actual native wires."""

    def __init__(self, names: list[str]) -> None:
        payload = _wire("council-private-query-available.json")["result"]["council_composition_candidates"]
        snapshot = payload["snapshot"]
        self.snapshot = {
            "snapshot_id": snapshot["snapshot_id"], "revision": 31,
            "native_revision": snapshot["native_revision"], "date_raw": snapshot["date_raw"],
            "paused": True, "map_ready": True,
            "played_character": {"character_id": payload["owner_character_id"], "alive": True},
        }
        self.frames = [_wire(name) for name in names]
        self.sent = []
        self.endpoint = SimpleNamespace(send=self.sent.append)
        self.state = SimpleNamespace(wait_for_command_result=self._response)
        self.command_timeout_seconds = 1.0

    def take_internal_semantic_snapshot(self) -> dict[str, object]:
        return dict(self.snapshot)

    def _response(self, request_id: str, timeout: float) -> dict[str, object]:
        return {**self.frames.pop(0), "request_id": request_id}


def test_native_private_council_query_polls_same_ticket_before_returning_ready(monkeypatch) -> None:
    monkeypatch.setattr(council_transport.time, "sleep", lambda _: None)
    driver = _CouncilMailboxDriver([
        "council-private-query-pending.json", "council-private-status-pending.json",
        "council-private-query-available.json",
    ])
    result = query_council_private_v1(driver, expected_revision=31)
    assert result["status"] == "available"
    assert result["council_composition_candidates"]["readiness"]["ready"] is True
    assert result["queried_revision"] == 31
    assert result["queried_native_revision"] == 13
    assert result["council_composition_candidates"]["snapshot"]["public_revision"] == 13
    assert [request["step"] for request in driver.sent] == [
        PRIVATE_QUERY_STEP, PRIVATE_STATUS_STEP, PRIVATE_STATUS_STEP,
    ]
    assert driver.sent[0]["expected_revision"] == 13
    assert all("expected_revision" not in request for request in driver.sent[1:])


def test_native_consumed_private_council_result_does_not_turn_idle_into_ready(monkeypatch) -> None:
    monkeypatch.setattr(council_transport.time, "sleep", lambda _: None)
    driver = _CouncilMailboxDriver([
        "council-private-query-pending.json", "council-private-status-idle.json",
    ])
    with pytest.raises(BridgeUnavailableError, match="no completed operation"):
        query_council_private_v1(driver, expected_revision=31)


def test_actual_private_council_sdk_query_assign_and_later_incumbent_receipt(monkeypatch) -> None:
    monkeypatch.setattr(council_transport.time, "sleep", lambda _: None)
    driver = _CouncilMailboxDriver([
        "council-private-query-pending.json", "council-private-status-pending.json",
        "council-private-query-available.json", "council-private-assign-pending.json",
        "council-private-assign-status-pending.json", "council-private-ack.json",
        "council-private-receipt-pending.json", "council-private-receipt-status-pending.json",
        "council-private-receipt.json",
    ])
    query = query_council_private_v1(driver, expected_revision=31)
    actual_ack = _wire("council-private-ack.json")["result"]["council_assign_councillor_ack"]
    pending = submit_council_assign_private_v1(
        driver, query=query, candidate_character_id=actual_ack["candidate_character_id"],
        expected_revision=31, action_request_id=actual_ack["action_request_id"],
    )
    assert pending["status"] == "native_helper_invoked_verification_pending"
    assert pending["council_assign_councillor_ack"]["verification_pending"] is True
    post = _wire("council-private-receipt.json")["result"]["council_assign_councillor_receipt"]
    driver.snapshot.update({
        "snapshot_id": post["post_snapshot_id"], "revision": 32,
        "native_revision": post["post_native_revision"], "date_raw": post["post_date_raw"],
    })
    receipt = query_council_assign_receipt_private_v1(
        driver, pending=pending, expected_revision=32,
    )
    assert receipt["status"] == "applied"
    assert receipt["council_assign_councillor_receipt"]["incumbent_character_id"] == actual_ack["candidate_character_id"]
    assert [request["step"] for request in driver.sent] == [
        PRIVATE_QUERY_STEP, PRIVATE_STATUS_STEP, PRIVATE_STATUS_STEP,
        PRIVATE_ASSIGN_STEP, PRIVATE_STATUS_STEP, PRIVATE_STATUS_STEP,
        PRIVATE_RECEIPT_STEP, PRIVATE_STATUS_STEP, PRIVATE_STATUS_STEP,
    ]
    assert driver.sent[3]["request_id"] == actual_ack["action_request_id"]
    assert driver.sent[3]["expected_revision"] == 13
    assert driver.sent[6]["expected_revision"] == 14
    assert driver.frames == []


class _CouncilSdkDriver(_CouncilMailboxDriver):
    """Use real native driver wrappers without initializing a native session."""

    allow_private_council_query = True
    allow_private_council_action = True
    query_council_composition_candidates_private_v1 = NativeHeadlessGameplayDriver.query_council_composition_candidates_private_v1
    query_council_final_gates_private_v1 = NativeHeadlessGameplayDriver.query_council_final_gates_private_v1
    submit_council_assign_private_v1 = NativeHeadlessGameplayDriver.submit_council_assign_private_v1
    query_council_assign_receipt_private_v1 = NativeHeadlessGameplayDriver.query_council_assign_receipt_private_v1

    def take_snapshot(self) -> dict[str, object]:
        return {**self.snapshot, "diagnostics": {"hello": {
            "expected_ck3_version": CK3_12002.game_version,
            "expected_ck3_sha256": CK3_12002.executable_sha256,
        }}}

    def capabilities(self) -> dict[str, object]:
        return {"format_version": 1, "backend_id": "native-headless",
                "source": "named-pipe", "snapshot": True, "wait_for_change": False,
                "action_steps": [], "bridge_capabilities": []}


def test_actual_private_council_query_assign_and_receipt_reach_official_mcp_sdk(monkeypatch) -> None:
    from mcp import Client

    monkeypatch.setattr(council_transport.time, "sleep", lambda _: None)
    driver = _CouncilSdkDriver([
        "council-private-query-pending.json", "council-private-status-pending.json",
        "council-private-query-available.json", "council-private-assign-pending.json",
        "council-private-assign-status-pending.json", "council-private-ack.json",
        "council-private-receipt-pending.json", "council-private-receipt-status-pending.json",
        "council-private-receipt.json",
    ])
    actual_ack = _wire("council-private-ack.json")["result"]["council_assign_councillor_ack"]

    async def exercise():
        async with Client(create_server(driver)) as client:
            quote = await client.call_tool("ck3_query_council_composition_candidates_private_v1", {
                "expected_revision": 31,
            })
            assert quote.is_error is False
            assert quote.structured_content["queried_native_revision"] == 13
            submitted = await client.call_tool("ck3_assign_councillor_private_v1", {
                "query": quote.structured_content,
                "candidate_character_id": actual_ack["candidate_character_id"],
                "expected_revision": 31, "action_request_id": actual_ack["action_request_id"],
            })
            assert submitted.is_error is False
            pending = submitted.structured_content
            assert pending["council_assign_councillor_ack"]["verification_pending"] is True
            post = _wire("council-private-receipt.json")["result"]["council_assign_councillor_receipt"]
            driver.snapshot.update({
                "snapshot_id": post["post_snapshot_id"], "revision": 32,
                "native_revision": post["post_native_revision"], "date_raw": post["post_date_raw"],
            })
            received = await client.call_tool("ck3_query_council_assign_receipt_private_v1", {
                "pending": pending, "expected_revision": 32,
            })
            assert received.is_error is False
            assert received.structured_content["status"] == "applied"
            assert received.structured_content["council_assign_councillor_receipt"]["incumbent_character_id"] == actual_ack["candidate_character_id"]

    asyncio.run(exercise())
    assert len(driver.sent) == 9
    assert driver.frames == []


class _GiftQueryDriver:
    """A fake endpoint returning the actual C++ query serializer output."""

    def __init__(self, name: str) -> None:
        self.frame = _wire(name)
        native = self.frame["result"]["native"]
        observation = native["observation"]
        self.snapshot = {
            "snapshot_id": f"native:{observation['snapshot_revision']}",
            "revision": observation["snapshot_revision"],
            "native_revision": observation["native_snapshot_revision"],
            "date_raw": observation["observed_date_raw"],
            "paused": True, "map_ready": True,
            "played_character": {"character_id": observation["player_character_id"], "alive": True},
            "active_event": None, "pending_character_interaction": None,
        }
        rows = native["direct_targeting_rows"]
        self.root = {
            "snapshot_revision": observation["snapshot_revision"],
            "date_raw": observation["observed_date_raw"],
            "player_character_id": observation["player_character_id"],
            "government": {"key": "feudal_government"},
            "player_targeting_faction_count": rows["faction_count"],
            "direct_landed_vassal_character_ids": [observation["recipient_character_id"]],
        }
        self.sent = []
        self.endpoint = SimpleNamespace(send=self.sent.append)
        self.state = SimpleNamespace(wait_for_command_result=self._response)

    def take_internal_semantic_snapshot(self) -> dict[str, object]:
        return dict(self.snapshot)

    def diagnostics(self) -> dict[str, object]:
        return {"last_heartbeat": {"g2_faction_gift_mitigation_async_glue_v1": {"private_build": True}}}

    def _response(self, request_id: str, timeout: float) -> dict[str, object]:
        return {**self.frame, "request_id": request_id}


@pytest.mark.parametrize(
    ("fixture", "expected_status"),
    [("gift-query.json", "selected"), ("gift-query-denied.json", "no_legal_candidate")],
)
def test_native_gift_query_reaches_existing_private_reader(fixture: str, expected_status: str) -> None:
    driver = _GiftQueryDriver(fixture)
    candidate = query_faction_gift_private_candidate_v1(
        driver, snapshot=driver.snapshot, same_frame_root=driver.root,
        minimum_gold_reserve_raw=5_000_000,
    )
    assert candidate["status"] == expected_status
    assert len(driver.sent) == 1
    assert driver.sent[0]["expected_revision"] == driver.snapshot["native_revision"]
    if expected_status == "selected":
        assert candidate["choice"]["gold_cost_raw"] == 7_500_000
        assert candidate["observation"]["source_faction_power_raw"] == 11_000_000


class _GiftSdkDriver(_GiftQueryDriver):
    """Run real query/action wrappers with fixture process identity only."""

    allow_private_faction_gift_query = True
    allow_private_faction_gift_action = True
    allow_private_faction_gift_formal_trial = False
    query_faction_gift_private_candidate_v1 = NativeHeadlessGameplayDriver.query_faction_gift_private_candidate_v1
    submit_faction_gift_private_v1 = NativeHeadlessGameplayDriver.submit_faction_gift_private_v1
    query_faction_gift_receipt_private_v1 = NativeHeadlessGameplayDriver.query_faction_gift_receipt_private_v1
    query_faction_gift_cold_recovery_private_v1 = NativeHeadlessGameplayDriver.query_faction_gift_cold_recovery_private_v1

    def __init__(self, state_dir: Path) -> None:
        super().__init__("gift-query.json")
        self.snapshot["episode_run_id"] = "native-50331649-fixture"
        self.state_dir = state_dir
        self.private_faction_round_id = "R0001"
        self.identity = (101, "fixture-before")
        self.action_id = None
        self.records = []

    def capabilities(self) -> dict[str, object]:
        return {"format_version": 1, "backend_id": "native-headless",
                "source": "named-pipe", "snapshot": True, "wait_for_change": False,
                "action_steps": [], "bridge_capabilities": []}

    def take_snapshot(self) -> dict[str, object]:
        return dict(self.snapshot)

    def load_wire(self, name: str) -> None:
        self.frame = _wire(name)
        observation = self.frame["result"]["native"]["observation"]
        self.snapshot.update({
            "snapshot_id": f"native:{observation['snapshot_revision']}",
            "revision": observation["snapshot_revision"],
            "native_revision": observation["native_snapshot_revision"],
            "date_raw": observation["observed_date_raw"],
        })

    def _response(self, request_id: str, timeout: float) -> dict[str, object]:
        frame = copy.deepcopy(self.frame)
        frame["request_id"] = request_id
        result = frame["result"]
        if result["step"] == gift_formal_route.SUBMIT_STEP:
            self.action_id = request_id
            result["native"]["ack"]["request_id"] = request_id
        elif result["step"] == gift_formal_route.RECEIPT_STEP:
            result["receipt"]["request_id"] = self.action_id
        return frame

    def _record_command(self, step: str, *, ok: bool, result: dict[str, object], error=None) -> None:
        self.records.append((step, ok, result, error))


async def _gift_sdk_submit(client, driver: _GiftSdkDriver) -> dict[str, object]:
    queried = await client.call_tool("ck3_query_faction_gift_candidate_private_v1", {
        "expected_revision": driver.snapshot["revision"],
        "same_frame_root": driver.root, "minimum_gold_reserve_raw": 5_000_000,
    })
    assert queried.is_error is False
    candidate = queried.structured_content
    assert candidate["status"] == "selected"
    assert candidate["choice"]["gold_cost_raw"] == 7_500_000
    driver.load_wire("gift-ack.json")
    submitted = await client.call_tool("ck3_send_faction_gift_private_v1", {
        "candidate": candidate,
        "checkpoint": {"sha256": "a" * 64,
                       "date_raw": driver.snapshot["date_raw"],
                       "episode_run_id": driver.snapshot["episode_run_id"]},
        "expected_revision": driver.snapshot["revision"],
    })
    assert submitted.is_error is False
    result = submitted.structured_content
    assert result["status"] == "submitted_verification_pending"
    assert result["native"]["ack"]["verification_pending"] is True
    pending = result["pending_ledger"]["pending"]
    assert pending["minimum_gold_reserve_raw"] == candidate["choice"]["minimum_gold_reserve_raw"]
    return pending


def test_actual_gift_query_submit_and_material_receipt_reach_official_mcp_sdk(monkeypatch, tmp_path: Path) -> None:
    from mcp import Client

    monkeypatch.setattr(gift_formal_route, "_runtime_identity", lambda driver: driver.identity)
    driver = _GiftSdkDriver(tmp_path)

    async def exercise():
        async with Client(create_server(driver)) as client:
            pending = await _gift_sdk_submit(client, driver)
            driver.load_wire("gift-receipt.json")
            received = await client.call_tool("ck3_query_faction_gift_receipt_private_v1", {
                "pending": pending, "expected_revision": driver.snapshot["revision"],
            })
            assert received.is_error is False
            result = received.structured_content
            assert result["status"] == "applied"
            assert result["pending_ledger"]["pending"] is None
            assert result["receipt"]["post_player_gold_raw"] == 12_500_000
            assert result["receipt"]["threat_resolved"] is False

    asyncio.run(exercise())
    assert len(driver.sent) == 3
    assert len(driver.records) == 2
    assert driver.allow_private_faction_gift_formal_trial is False


@pytest.mark.parametrize(
    ("fixture", "expected_threat_resolved"),
    [("gift-cold-present.json", False), ("gift-cold-absent.json", True)],
)
def test_actual_gift_cold_entity_query_reaches_official_mcp_sdk(
    monkeypatch, tmp_path: Path, fixture: str, expected_threat_resolved: bool,
) -> None:
    from mcp import Client

    monkeypatch.setattr(gift_formal_route, "_runtime_identity", lambda driver: driver.identity)
    driver = _GiftSdkDriver(tmp_path)

    async def exercise():
        async with Client(create_server(driver)) as client:
            pending = await _gift_sdk_submit(client, driver)
            driver.identity = (102, "fixture-after")
            driver.private_faction_round_id = "R0002"
            driver.load_wire(fixture)
            recovered = await client.call_tool("ck3_query_faction_gift_cold_recovery_private_v1", {
                "pending": pending, "expected_revision": driver.snapshot["revision"],
            })
            assert recovered.is_error is False
            classification = recovered.structured_content["cold_recovery_classification"]
            assert classification["status"] == "applied"
            assert classification["threat_resolved"] is expected_threat_resolved

    asyncio.run(exercise())
    assert len(driver.sent) == 3


@pytest.mark.parametrize("kind", ["council", "gift"])
def test_private_governance_tools_are_absent_from_default_off_discovery(kind: str, tmp_path: Path) -> None:
    from mcp import Client

    if kind == "council":
        driver = _CouncilSdkDriver([])
        driver.allow_private_council_query = False
        driver.allow_private_council_action = False
        names = {"ck3_query_council_composition_candidates_private_v1",
                 "ck3_query_council_final_gates_private_v1",
                 "ck3_assign_councillor_private_v1",
                 "ck3_query_council_assign_receipt_private_v1"}
    else:
        driver = _GiftSdkDriver(tmp_path)
        driver.allow_private_faction_gift_query = False
        driver.allow_private_faction_gift_action = False
        names = {"ck3_query_faction_gift_candidate_private_v1",
                 "ck3_send_faction_gift_private_v1",
                 "ck3_query_faction_gift_receipt_private_v1",
                 "ck3_query_faction_gift_cold_recovery_private_v1"}

    async def exercise():
        async with Client(create_server(driver)) as client:
            tools = await client.list_tools()
            assert names.isdisjoint({tool.name for tool in tools.tools})

    asyncio.run(exercise())
    assert driver.sent == []


def _gift_pending(state_dir: Path) -> dict[str, object]:
    observation = _wire("gift-query.json")["result"]["native"]["observation"]
    ack = _wire("gift-ack.json")["result"]["native"]["ack"]
    begin_faction_gift_submission_v1(
        state_dir, request_id=ack["request_id"],
        episode_run_id="native-50331649-fixture",
        source_round_id="R0001", source_bridge_pid=101,
        source_bridge_creation_date="fixture-before",
        observation=observation, minimum_gold_reserve_raw=5_000_000,
        checkpoint_sha256_before_submit="a" * 64,
    )
    ledger = mark_faction_gift_ack_pending_v1(
        state_dir, request_id=ack["request_id"], ack=ack,
    )
    assert ledger["pending"]["status"] == "submitted_verification_pending"
    return ledger["pending"]


def test_native_gift_ack_waits_for_material_independent_receipt(tmp_path: Path) -> None:
    pending = _gift_pending(tmp_path)
    unchanged = _wire("gift-receipt-unchanged.json")["result"]["receipt"]
    with pytest.raises(ValueError, match="independent post-state"):
        complete_faction_gift_after_independent_receipt_v1(
            tmp_path, request_id=pending["request_id"], receipt=unchanged,
        )
    receipt = _wire("gift-receipt.json")["result"]["receipt"]
    completed = complete_faction_gift_after_independent_receipt_v1(
        tmp_path, request_id=pending["request_id"], receipt=receipt,
    )
    assert completed["pending"] is None
    assert receipt["post_player_gold_raw"] == 12_500_000
    assert receipt["post_gift_opinion_modifier_value"] == 35
    assert receipt["threat_resolved"] is False


@pytest.mark.parametrize(
    ("fixture", "expected_threat_resolved"),
    [("gift-cold-present.json", False), ("gift-cold-absent.json", True)],
)
def test_native_gift_persisted_entity_recovery_keeps_absence_distinct(
    tmp_path: Path, fixture: str, expected_threat_resolved: bool,
) -> None:
    pending = _gift_pending(tmp_path)
    result = _wire(fixture)["result"]
    native = result["native"]
    recovery = {
        "schema_version": 1, "status": result["status"],
        "private_build": result["private_build"], "advertised": result["advertised"],
        "new_process_confirmed": True, "new_round_id": "R0002",
        "new_bridge_pid": 102, "new_bridge_creation_date": "fixture-after",
        "episode_run_id": pending["episode_run_id"], "paused": True, "map_ready": True,
        "independent_faction_storage_lookup_complete": native["failure_flags"] == 0,
        "independent_recipient_lookup_complete": native["observation"]["recipient_identity_resolved"],
        "selected_from_current_targeting_vector": False,
        "post_observation": native["observation"],
    }
    classified = evaluate_faction_gift_cold_recovery_v1(pending, recovery)
    assert classified["status"] == "applied"
    assert classified["threat_resolved"] is expected_threat_resolved
