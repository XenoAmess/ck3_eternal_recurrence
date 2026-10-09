"""Synthetic registered replay of normal026's Crown readonly stale-frame RED.

All quotes and frames are explicitly source-shaped fixtures, including the
new native11/public3 frame. The real registered normal planner, Crown consumer,
NativeDriver wrapper and formal transport run. Only external native messages,
the ordinary baseline and the final executor are fixture seams. No CK3 opens.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
import json
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from xar_autoplayer.bridge import realm_law_formal_private_transport as formal
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12004


STALE = "nonwar private snapshot revision is stale or malformed"
OTHER_RED = "source-shaped unrelated Crown native failure"
BASELINE = {"policy": "normal-crown-stale-source-fixture",
            "phase": "life_advance", "selected_step": "life-advance"}


class _Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def monotonic(self) -> float:
        return self.now


class _CrownReadonlyDriver:
    query_realm_law_crown_action_private_v1 = (
        NativeHeadlessGameplayDriver.query_realm_law_crown_action_private_v1
    )
    allow_private_realm_law_action = True
    allow_private_realm_law_paused_query = False
    nonwar_only = False
    command_timeout_seconds = 30.0
    _session_bridge_pid = 881

    def __init__(self, state_dir: Path, responses: list[str], *, new_frame: bool) -> None:
        self.state_dir = state_dir
        self.responses = responses
        self.new_frame = new_frame
        self.clock = _Clock()
        self.endpoint = self
        self.state = self
        self.sent: list[dict[str, object]] = []
        self.received: list[dict[str, object]] = []
        self.waits: list[dict[str, object]] = []
        self.command_timeouts: list[float] = []
        self.semantic_reads = 0
        self.frame = {
            "snapshot_id": "native:10", "revision": 2, "native_revision": 10,
            "date_raw": 53169072, "paused": True, "map_ready": True,
            "phase": "map_hud", "episode_run_id": "normal026-crown-source-fixture",
            "active_event": None, "pending_character_interaction": None,
            "active_wars": [], "player_armies": [], "native_command_history": [],
            "played_character": {"character_id": 29829, "alive": True},
            "diagnostics": {"hello": {
                "expected_ck3_version": CK3_12004.game_version,
                "expected_ck3_sha256": CK3_12004.executable_sha256,
            }},
        }

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(self.frame)

    take_snapshot_without_native_command_history = take_snapshot

    def take_internal_semantic_snapshot(self) -> dict[str, object]:
        self.semantic_reads += 1
        return self.take_snapshot()

    def capabilities(self) -> dict[str, object]:
        return {"backend_id": "native-headless", "action_steps": ["life-advance"],
                "bridge_capabilities": []}

    def send(self, request: dict[str, object]) -> None:
        assert request["step"] == formal.QUERY_STEP
        assert request["expected_revision"] == self.frame["native_revision"]
        assert request["expected_date_raw"] == self.frame["date_raw"]
        assert request["expected_player_character_id"] == 29829
        assert len(self.sent) < len(self.responses), "unexpected additional Crown request"
        self.sent.append(deepcopy(request))

    def wait_for_command_result(self, request_id: str, timeout: float) -> dict[str, object]:
        assert request_id == self.sent[-1]["request_id"]
        assert 0 < timeout <= self.command_timeout_seconds
        self.command_timeouts.append(timeout)
        self.clock.now += 0.01
        response = self.responses[len(self.sent) - 1]
        packet = {"type": "command_result", "protocol_version": 1,
                  "request_id": request_id, "ok": response == "available"}
        if response != "available":
            packet["error"] = STALE if response == "stale" else OTHER_RED
        else:
            # This is a new source-shaped quote for the fixture's current frame,
            # not a relabelled held native quote or a future enactment result.
            observation = {
                "available": True, "paused": True,
                "snapshot_revision": self.frame["native_revision"],
                "native_snapshot_revision": self.frame["native_revision"],
                "proof_epoch": self.frame["native_revision"],
                "date_raw": self.frame["date_raw"], "player_character_id": 29829,
                "group_key": "crown_authority", "active_law_key": "crown_authority_0",
                "resources": [{"currency_key": key,
                    "amount_raw": 50000000 if key == "prestige" else 0}
                    for key in formal.CURRENCIES],
                "title_successors": {"primary_title_id": 16777217, "held_titles": [{
                    "title_id": 16777217, "primary": True,
                    "successor_character_ids": [29830]}]},
                "candidates": [{"law_key": f"crown_authority_{level}",
                    "is_active": level == 0, "engine_final_only": False,
                    "can_enact": False, "blocked_reason": "source_fixture_native_final_blocked",
                    "costs": [{"currency_key": "prestige", "cost_raw": 20000000}]
                        if level == 1 else []} for level in range(4)],
            }
            packet["result"] = {
                "step": formal.QUERY_STEP, "accepted": True, "private_build": True,
                "advertised": False, "backend_id": "native-headless", "read_only": True,
                "game_version": CK3_12004.game_version,
                "executable_sha256": CK3_12004.executable_sha256,
                "status": "available", "ack": None, "receipt": None,
                "observation": observation,
            }
        self.received.append(deepcopy(packet))
        return packet

    def wait_for_public_change(self, revision: int, timeout_seconds: float) -> dict[str, object]:
        assert revision == self.frame["revision"]
        assert 0 < timeout_seconds <= self.command_timeout_seconds
        self.waits.append({"revision": revision, "timeout_seconds": timeout_seconds})
        if self.new_frame:
            self.clock.now += 0.01
            self.frame.update(snapshot_id="native:11", revision=3, native_revision=11)
        else:
            # Deterministic deadline exhaustion, without real sleeping or a
            # duplicate request against the same stale native revision.
            self.clock.now += timeout_seconds + 0.001
        return self.take_internal_semantic_snapshot()


def test_registered_normal_crown_rebinds_only_stale_readonly_quote(tmp_path: Path) -> None:
    from mcp import Client

    records: list[dict[str, object]] = []
    executor_calls: list[dict[str, object]] = []

    def executor_seam(_service, planned, *, before_submit=None):
        executor_calls.append(deepcopy(planned))
        return {"status": "fixture_execution_reached", "plan": planned["plan"],
                "snapshot_id": planned["snapshot_id"], "revision": planned["revision"],
                "external_execution_fixture": True}

    async def call(driver: _CrownReadonlyDriver):
        # Replacing only this module's time binding avoids changing asyncio's
        # wall clock while making the original query deadline deterministic.
        with patch.object(formal, "time", SimpleNamespace(monotonic=driver.clock.monotonic)):
            async with Client(create_server(driver)) as client:
                return await client.call_tool("ck3_auto_turn", {})

    async def run() -> None:
        with patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value=BASELINE), \
                patch.object(GameplayBridgeService, "_execute_planned_turn", new=executor_seam), \
                patch.object(GameplayBridgeService, "plan_nonwar_turn",
                             side_effect=AssertionError("Crown must use the ordinary planner")):
            positive = _CrownReadonlyDriver(tmp_path / "positive", ["stale", "available"], new_frame=True)
            result = await call(positive)
            assert result.is_error is False, result.content
            observed = result.structured_content
            assert observed["status"] == "fixture_execution_reached"
            assert observed["revision"] == 3 and observed["snapshot_id"] == "native:11"
            assert observed["plan"]["selected_step"] == "life-advance"
            quote = observed["plan"]["crown_readback"]
            assert quote["queried_snapshot_id"] == "native:11"
            assert quote["queried_revision"] == 3 and quote["queried_native_revision"] == 11
            assert quote["snapshot_revision"] == quote["native_snapshot_revision"] == 11
            assert observed["plan"]["crown_decision"]["status"] == "native_blocked"
            assert [(row["step"], row["expected_revision"]) for row in positive.sent] == [
                (formal.QUERY_STEP, 10), (formal.QUERY_STEP, 11)]
            assert positive.received[0]["ok"] is False
            assert positive.received[0]["error"] == STALE
            assert positive.received[1]["ok"] is True
            assert len(positive.waits) == 1 and positive.waits[0]["revision"] == 2
            assert positive.command_timeouts[1] < positive.command_timeouts[0]
            assert positive.clock.now < positive.command_timeout_seconds
            assert len(executor_calls) == 1 and executor_calls[0]["revision"] == 3
            records.append({"scene": "stale-readonly-rebound-to-new-native-frame",
                "requests": positive.sent, "response_packets": positive.received,
                "frame_waits": positive.waits, "command_timeouts": positive.command_timeouts,
                "registered_output": observed, "executor_entered": True})

            for name, responses, new_frame, expected_count in (
                ("nonstale-native-red", ["other"], True, 1),
                ("twice-stale-native-red", ["stale", "stale"], True, 2),
                ("stale-with-no-new-native-frame", ["stale"], False, 1),
            ):
                driver = _CrownReadonlyDriver(tmp_path / name, responses, new_frame=new_frame)
                failed = await call(driver)
                assert failed.is_error is True, failed.content
                assert len(driver.sent) == expected_count
                assert len(executor_calls) == 1
                assert all(row["step"] == formal.QUERY_STEP for row in driver.sent)
                assert all(row["ok"] is False for row in driver.received)
                if name == "nonstale-native-red":
                    assert driver.received[0]["error"] == OTHER_RED
                    assert driver.waits == []
                else:
                    assert driver.received[0]["error"] == STALE
                    assert len(driver.waits) == 1
                    if new_frame:
                        assert [row["expected_revision"] for row in driver.sent] == [10, 11]
                    else:
                        assert driver.frame["native_revision"] == 10
                        assert driver.clock.now >= driver.command_timeout_seconds
                records.append({"scene": name, "requests": driver.sent,
                    "response_packets": driver.received, "frame_waits": driver.waits,
                    "command_timeouts": driver.command_timeouts, "executor_entered": False,
                    "registered_error": str(failed.content)})

    try:
        asyncio.run(run())
        assert len(records) == 4
    finally:
        evidence = {
            "schema": "xar.ck3.crown-readonly-fresh-frame-regression12004/v1",
            "fixture_source_shaped": True, "registered_auto_turn": True,
            "native_queries_only": True, "original_failed_packets_retained": True,
            "execution_fixture": "sole external _execute_planned_turn seam after real plan_turn",
            "scenes": records, "executor_calls": executor_calls,
            "pipe_operations": 0, "game_operations": 0, "native_actions": 0,
            "old_tests_replayed": 0, "live": False,
        }
        output = Path(os.environ.get("XAR_CROWN_READONLY_FRESH_FRAME_OUTPUT", str(
            tmp_path / "crown-readonly-fresh-frame-evidence.json")))
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
