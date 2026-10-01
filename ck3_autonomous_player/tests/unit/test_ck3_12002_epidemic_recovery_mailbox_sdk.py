"""Actual recovery caller packets through the production cache/query and SDK."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest

from xar_autoplayer.bridge.mcp_server import create_server, parser
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState
from xar_autoplayer.epidemic_recovery_formal_observer import (
    capture_epidemic_recovery_before_option, observe_epidemic_recovery_after_option,
)


FIXTURES = Path(__file__).resolve().parents[2] / "native_bridge/research/fixtures/ck3_12002_epidemic_recovery_mailbox"


def load_fixture(name: str) -> dict[str, object]:
    data = (FIXTURES / name).read_bytes()
    provenance = json.loads((FIXTURES / "provenance.json").read_bytes())
    expected = next(item["sha256"] for item in provenance["wire"] if item["name"] == name)
    if hashlib.sha256(data).hexdigest() != expected.lower():
        raise AssertionError(f"actual native packet bytes changed: {name}")
    return json.loads(data)


class ProtocolRecoverySdkDriver:
    """Fixture context with native actor/date/revision; no game or pipe endpoint."""

    allow_private_epidemic_recovery_query = False
    command_timeout_seconds = 30.0
    query_player_epidemic_recovery_private_v1 = NativeHeadlessGameplayDriver.query_player_epidemic_recovery_private_v1

    def __init__(self, packet: dict[str, object]) -> None:
        self.packet = deepcopy(packet)
        self.state = NativeProtocolState("offline-ce1-recovery-mailbox-replay")
        self.endpoint = self
        self.sent: list[dict[str, object]] = []
        provenance = json.loads((FIXTURES / "provenance.json").read_bytes())
        self.event_instance = provenance["same_day_near_pair"]["pre_event_instance"]
        self.state.ingest({
            "type": "hello", "protocol_version": 1, "pid": 1,
            "capabilities": ["game.state.snapshot"],
            "expected_ck3_version": provenance["exact_build"],
            "expected_ck3_sha256": provenance["exe_sha256"],
        })
        self.advance_context(packet)

    def advance_context(self, packet: dict[str, object]) -> None:
        self.packet = deepcopy(packet)
        native = packet["result"]["player_epidemic_recovery"]
        # The response is actual. Hello and published snapshot/event are explicit
        # synthetic scaffolding; revision/date/actor use the native payload.
        self.last_snapshot_ingest = self.state.ingest({
            "type": "state_snapshot", "protocol_version": 1,
            "snapshot_id": f"native:{native['snapshot_revision']}",
            "revision": native["snapshot_revision"],
            "state": {
                "date_raw": native["date_raw"], "speed": 1,
                "paused": True, "map_ready": True,
                "played_character": {"character_id": native["played_character_id"], "alive": True},
                "active_event": {"instance_id": self.event_instance} if native["requested_title_id"] == 0 else None,
                "pending_character_interaction": None, "one_life_settlement": None,
                "active_wars": [], "player_armies": [], "history": [],
            },
        })

    def take_snapshot(self) -> dict[str, object]:
        return self.state.semantic_snapshot()

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(deepcopy(request))
        packet = deepcopy(self.packet)
        packet["request_id"] = request["request_id"]
        self.last_ingest = self.state.ingest(packet)


class ParsedSdkRecoveryReadbacks:
    """Replay SDK-qualified material to the observer without another query/action."""

    def __init__(self, outputs: dict[str, dict[str, object]], snapshots: dict[str, dict[str, object]]) -> None:
        self.outputs = outputs
        self.snapshots = snapshots
        self.after = False
        self.requested_titles: list[int] = []

    def snapshot(self) -> dict[str, object]:
        return deepcopy(self.snapshots["post89-county-a.json" if self.after else "pre88-two-counties.json"])

    def query_player_epidemic_recovery_private_v1(self, *, expected_revision: int, requested_title_id: int = 0, expected_event_instance_id: int | None = None) -> dict[str, object]:
        if requested_title_id:
            name = next(name for name in ("post89-county-a.json", "post89-county-b.json")
                        if self.outputs[name]["player_epidemic_recovery"]["requested_title_id"] == requested_title_id)
        else:
            name = "pre88-two-counties.json"
        result = self.outputs[name]
        assert result["queried_revision"] == expected_revision
        assert result["queried_event_instance_id"] == expected_event_instance_id
        self.requested_titles.append(requested_title_id)
        return deepcopy(result)

    def query_campaign_root_context_v1(self, *, expected_revision: int) -> dict[str, object]:
        frame = self.snapshot()
        return {
            "queried_snapshot_id": frame["snapshot_id"], "queried_revision": expected_revision,
            "queried_native_revision": frame["native_revision"],
            "campaign_root_context": {
                "player_character_id": frame["played_character"]["character_id"],
                "player_legitimacy_v1": {"status": "unavailable", "unavailable_reason": "not_in_mailbox_fixture"},
            },
        }


class EpidemicRecovery12002MailboxSdkTest(unittest.IsolatedAsyncioTestCase):
    async def test_actual_same_day_titles_empty_list_and_unavailable_packets_reach_sdk(self) -> None:
        from mcp import Client

        name = "ck3_query_player_epidemic_recovery_private_v1"
        self.assertFalse(parser().parse_args([]).private_player_epidemic_recovery_query)
        self.assertTrue(parser().parse_args(["--private-player-epidemic-recovery-query"]).private_player_epidemic_recovery_query)
        driver = ProtocolRecoverySdkDriver(load_fixture("pre88-two-counties.json"))
        self.assertEqual(driver.last_snapshot_ingest, "state_snapshot")
        async with Client(create_server(driver)) as client:
            self.assertNotIn(name, {tool.name for tool in (await client.list_tools()).tools})
        self.assertEqual(driver.sent, [])

        driver.allow_private_epidemic_recovery_query = True
        outputs = {}
        snapshots = {}
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            self.assertTrue(tools[name].annotations.read_only_hint)
            for packet_name in ("pre88-two-counties.json", "post89-county-a.json", "post89-county-b.json", "empty-list.json", "list-unavailable.json"):
                with self.subTest(actual_native_packet=packet_name):
                    packet = load_fixture(packet_name)
                    driver.advance_context(packet)
                    snapshot = driver.take_snapshot()
                    native_result = packet["result"]
                    native = native_result["player_epidemic_recovery"]
                    title = native["requested_title_id"]
                    response = await client.call_tool(name, {
                        "expected_revision": snapshot["revision"],
                        "requested_title_id": title,
                        "expected_event_instance_id": driver.event_instance if title == 0 else None,
                    })
                    self.assertFalse(response.is_error, response.content)
                    actual = response.structured_content
                    self.assertEqual(driver.last_ingest, "command_result")
                    self.assertEqual({key: actual[key] for key in native_result}, native_result)
                    self.assertEqual(actual["queried_revision"], snapshot["revision"])
                    self.assertEqual(actual["queried_native_revision"], native["snapshot_revision"])
                    self.assertEqual(actual["queried_event_instance_id"], driver.event_instance if title == 0 else None)
                    self.assertEqual(driver.sent[-1]["step"], native_result["step"])
                    self.assertEqual(driver.sent[-1]["expected_revision"], native["snapshot_revision"])
                    outputs[packet_name] = actual
                    snapshots[packet_name] = snapshot
        before = outputs["pre88-two-counties.json"]["player_epidemic_recovery"]
        post = [outputs[name]["player_epidemic_recovery"] for name in ("post89-county-a.json", "post89-county-b.json")]
        self.assertEqual(before["snapshot_revision"], 88)
        self.assertEqual([value["snapshot_revision"] for value in post], [89, 89])
        self.assertEqual({value["date_raw"] for value in [before, *post]}, {53175816})
        self.assertEqual({value["played_character_id"] for value in [before, *post]}, {50331652})
        # These rows are actual native data. No synthesized county identities.
        for old, after, expected_change in zip(before["counties"], post, ("minor", "tiny"), strict=True):
            current = after["counties"][0]
            self.assertEqual(current["landed_title_id"], old["landed_title_id"])
            self.assertGreater(current["landed_title_id"], 0x00FFFFFF)
            self.assertIs(old[f"{expected_change}_present"], False)
            self.assertIs(current[f"{expected_change}_present"], True)
        self.assertEqual(outputs["empty-list.json"]["player_epidemic_recovery"]["counties"], [])
        self.assertIsNone(outputs["list-unavailable.json"]["player_epidemic_recovery"]["counties"])
        self.assertEqual(len(driver.sent), 5)
        self.assertEqual([outputs[name]["query_sequence"] for name in outputs], [1, 2, 3, 4, 5])
        self.assertEqual([outputs[name]["observation_revision"] for name in outputs], [4, 5, 6, 7, 8])

        service = ParsedSdkRecoveryReadbacks(outputs, snapshots)
        frame = service.snapshot()
        # Synthetic selection context only: no option is executed by this test.
        candidate = {
            "snapshot_id": frame["snapshot_id"], "revision": frame["revision"],
            "selected_step": "select-event-option-3",
            "plan": {"phase": "active_event_registry_choice",
                     "active_event": {"instance_id": driver.event_instance},
                     "event_decision": {"status": "recommended", "event_definition_key": "epidemic_events.0110",
                                        "selected_native_option_index": 2, "selected_option_number": 3}},
        }
        captured = capture_epidemic_recovery_before_option(service, candidate)
        self.assertEqual(captured["before_counties"], before["counties"])
        service.after = True
        observed = observe_epidemic_recovery_after_option(service, captured, service.snapshot())
        self.assertEqual(observed["status"], "verified_new_modifier_presence")
        self.assertEqual(observed["before_frame"]["native_revision"], 88)
        self.assertEqual(observed["after_frame"]["native_revision"], 89)
        self.assertEqual([row["newly_present"] for row in observed["counties"]], [["minor"], ["tiny"]])
        self.assertEqual([row["after"] for row in observed["counties"]], [value["counties"][0] for value in post])
        self.assertIsNone(observed["legitimacy"]["delta_raw"])
        self.assertEqual(observed["remaining_days"], {"status": "unavailable", "value": None})
        self.assertFalse(observed["date_advanced"])
        self.assertEqual(service.requested_titles, [0, *[row["landed_title_id"] for row in before["counties"]]])


if __name__ == "__main__":
    unittest.main()
