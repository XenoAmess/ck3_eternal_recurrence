"""Consume the new synthetic native fixture through the actual registered MCP.

Authored only in the migration lane. Run once by the coordinator after its native
whole fixture succeeds; this program never discovers or starts a game process.
"""
from __future__ import annotations

import argparse
import asyncio
import copy
import json
from pathlib import Path
import sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--native-fixture", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    sys.path.insert(0, str(args.source_root / "ck3_autonomous_player/src"))
    from xar_autoplayer.bridge.mcp_server import create_server
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from mcp import Client

    native = json.loads(args.native_fixture.read_text(encoding="utf-8"))
    if native["status"] != "GREEN" or native["synthetic"] is not True:
        raise ValueError("requires the successful synthetic native whole fixture")
    if native["build"]["version"] != "1.20.0.4" or native["build"]["exe_sha256"] != (
        "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"
    ):
        raise ValueError("native fixture has a different exact-build identity")
    query_step = "query-current-timeline-blocker-context-v1"
    close_step = "continue-death-succession-modal-v1"

    class Endpoint:
        pipe_name = r"\\.\pipe\xar_death_succession_12004_synthetic"

        def __init__(self) -> None:
            self.on_frame = None
            self.requests: list[dict] = []
            self.mode = "no_modal"
            self.query_sequence = 0
            self.observation_revision = 200

        def start(self, on_frame, on_disconnect) -> None:
            self.on_frame = on_frame

        def publish(self, packet: dict) -> None:
            self.on_frame(copy.deepcopy(packet))

        def send(self, request: dict) -> None:
            if request.get("type") == "ping":
                return
            assert request["type"] == "execute_step"
            assert request["expected_revision"] == native["snapshot_revision"]
            self.requests.append(copy.deepcopy(request))
            self.observation_revision += 1
            if request["step"] == query_step:
                self.query_sequence += 1
                value = native[self.mode]
                result = {
                    "step": query_step,
                    "accepted": True,
                    "status": value["status"],
                    "query_sequence": self.query_sequence,
                    "observation_revision": self.observation_revision,
                    "snapshot_revision": native["snapshot_revision"],
                    "current_timeline_blocker_context": value,
                    "private_build": True,
                    "read_only": True,
                    "advertised": False,
                    "backend_id": "native-headless",
                }
            else:
                assert request["step"] == close_step
                assert request["expected_date_raw"] == native["date_raw"]
                assert request["expected_played_character_id"] == native["played_character_id"]
                result = {
                    **native["close_receipt"],
                    "step": close_step,
                    "accepted": True,
                    "action_observation_revision": self.observation_revision,
                    "private_build": True,
                    "advertised": False,
                    "backend_id": "native-headless",
                }
                # Keep the actual fixture's independent after-ACK modal result.
                # The transport must retain the ACK and avoid material credit.
                self.mode = "after_ack"
            self.publish({
                "type": "command_result", "protocol_version": 1,
                "request_id": request["request_id"], "ok": True, "result": result,
            })

        def close(self) -> None:
            pass

        def transport_error(self):
            return None

    async def exercise() -> dict:
        endpoint = Endpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=0.1,
            allow_private_current_timeline_blocker_query=True,
            allow_private_death_succession_modal_continue=True,
        )
        try:
            endpoint.publish({
                "type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
                "pid": 7878, "session_generation": 0,
                "game_version": native["build"]["version"],
                "expected_ck3_version": native["build"]["version"],
                "executable_sha256": native["build"]["exe_sha256"],
                "capabilities": ["game.state.snapshot"],
            })
            endpoint.publish({
                "type": "state_snapshot", "protocol_version": 1,
                "snapshot_id": "native:77", "revision": native["snapshot_revision"],
                "state": {
                    "phase": "map_hud", "date": "synthetic:12004", "date_raw": native["date_raw"],
                    "speed": 1, "paused": True, "map_ready": True,
                    "history": [], "active_event": None, "pending_character_interaction": None,
                    "played_character": {"character_id": native["played_character_id"], "alive": True},
                    "one_life_settlement": None, "active_wars": [], "player_armies": [],
                },
            })
            query_name = "ck3_query_current_timeline_blocker_context_v1"
            close_name = "ck3_continue_death_succession_modal_v1"
            async with Client(create_server(driver)) as client:
                names = {tool.name for tool in (await client.list_tools()).tools}
                assert query_name in names and close_name in names
                snapshot = driver.take_snapshot()
                response = await client.call_tool(query_name, {"expected_revision": snapshot["revision"]})
                assert not response.is_error
                observed = response.structured_content
                assert observed["current_timeline_blocker_context"] == native["no_modal"]
                assert observed["current_timeline_blocker_context"]["can_continue"]["value"] is None
                assert observed["queried_native_revision"] == native["snapshot_revision"]
                assert observed["advertised"] is False and observed["read_only"] is True
                binding = {
                    "expected_revision": snapshot["revision"],
                    "expected_played_character_id": snapshot["played_character"]["character_id"],
                    "expected_episode_run_id": snapshot["episode_run_id"],
                }
                rejected = await client.call_tool(close_name, binding)
                assert rejected.is_error
                assert all(row["step"] == query_step for row in endpoint.requests)

                endpoint.mode = "modal"
                pending_response = await client.call_tool(close_name, binding)
                assert not pending_response.is_error
                pending = pending_response.structured_content
                assert pending["status"] == "submitted_unconfirmed"
                assert pending["material_result_verified"] is False
                assert pending["submission_ack"]["close_invocations"] == 1
                assert pending["life_advance_result"] is None
                assert sum(row["step"] == close_step for row in endpoint.requests) == 1
                assert driver.take_snapshot()["date_raw"] == native["date_raw"]
                return {"living_query": observed, "pending_close": pending, "requests": endpoint.requests}
        finally:
            driver.close()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": "xar.death-succession-12004.registered-mcp-fixture.v1",
        "status": "RED", "synthetic": True, "live_queries": 0, "game_actions": 0,
        "build": native["build"], "native_fixture": str(args.native_fixture),
    }
    try:
        observed = asyncio.run(exercise())
        (args.output_dir / "observed.json").write_text(
            json.dumps(observed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        report.update(status="GREEN", source_root=str(args.source_root))
    finally:
        (args.output_dir / "RESULT.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
