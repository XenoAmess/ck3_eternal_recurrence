"""Consume one preserved native whole through the registered ArmyStrength MCP.

AUTHOR_NOT_RUN. Set CK3_BATTLE_CASUALTY_PHYSICAL_DEBIT_12004_MCP_WIRE_DIR
to Root's fresh producer directory. The endpoint supplies only paused scope
and request correlation; the original whole business result is preserved.
"""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import threading
import traceback
import unittest


ENV = "CK3_BATTLE_CASUALTY_PHYSICAL_DEBIT_12004_MCP_WIRE_DIR"
BASENAME = "battle-casualty-physical-debit-12004-whole.json"
FAMILY = "battle_casualty_observations_v1"
WRITER_FAMILY = "actual_loss_writer_observations_v1"
ROUTE = "ck3_query_army_strengths"


def _assert_native_values(case: unittest.TestCase, original: object,
                          observed: object, path: str) -> None:
    if isinstance(original, dict):
        case.assertIsInstance(observed, dict, path)
        for key, value in original.items():
            case.assertIn(key, observed, path)
            _assert_native_values(case, value, observed[key], path + "." + key)
    elif isinstance(original, list):
        case.assertIsInstance(observed, list, path)
        case.assertEqual(len(observed), len(original), path)
        for index, value in enumerate(original):
            _assert_native_values(case, value, observed[index], f"{path}[{index}]")
    else:
        case.assertIs(type(observed), type(original), path)
        case.assertEqual(observed, original, path)


class _PreservedWholeEndpoint:
    def __init__(self, whole: dict[str, object]) -> None:
        self.pipe_name = "\\\\.\\pipe\\xar_ck3_battle_casualty_physical_debit_fixture"
        self.whole = whole
        self.requests: list[dict[str, object]] = []
        self.delivered: list[dict[str, object]] = []
        self.on_frame = None
        self.on_disconnect = None

    def start(self, on_frame, on_disconnect) -> None:
        self.on_frame = on_frame
        self.on_disconnect = on_disconnect

    def publish(self, frame: dict[str, object]) -> None:
        if self.on_frame is None:
            raise AssertionError("production driver did not start its endpoint")
        self.on_frame(deepcopy(frame))

    def send(self, frame: dict[str, object]) -> None:
        self.requests.append(deepcopy(frame))
        if frame.get("type") == "ping":
            self.publish({"type": "pong", "protocol_version": 1,
                          "request_id": frame["request_id"]})
            return
        if (frame.get("type"), frame.get("step")) != (
                "execute_step", "query-army-strengths-v1"):
            raise AssertionError("unexpected transport request: " + str(frame))
        delivered = deepcopy(self.whole)
        delivered["request_id"] = frame["request_id"]
        self.delivered.append(deepcopy(delivered))
        self.publish(delivered)

    def close(self) -> None:
        if self.on_disconnect is not None:
            self.on_disconnect()


class BattleCasualtyPhysicalDebitRegisteredMcp12004Tests(
        unittest.IsolatedAsyncioTestCase):
    async def test_battle_casualty_whole_through_registered_army_query(self) -> None:
        wire_directory = os.environ.get(ENV)
        if not wire_directory:
            self.skipTest(f"Root must provide the sole new whole via {ENV}")
        project = Path(__file__).resolve().parents[2]
        repository = project.parent
        sys.path[0:0] = [str(repository / "tools"),
                         str(repository / "ck3_workshop_mcp/src"),
                         str(project / "src")]
        from xar_autoplayer.bridge import war_contract
        from xar_autoplayer.bridge import battle_casualty_observation_contract
        from xar_autoplayer.bridge.mcp_server import create_server
        from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
        from xar_autoplayer.bridge.service import GameplayBridgeService
        from xar_autoplayer.bridge.version_identity import CK3_12004

        self.assertEqual(Path(war_contract.__file__).resolve(),
                         project / "src/xar_autoplayer/bridge/war_contract.py")
        self.assertEqual(Path(battle_casualty_observation_contract.__file__).resolve(),
                         project / "src/xar_autoplayer/bridge/battle_casualty_observation_contract.py")
        wire_dir = Path(wire_directory).resolve()
        native_path = wire_dir / BASENAME
        output_dir = wire_dir / "registered-consumer"
        output_dir.mkdir(parents=True, exist_ok=True)
        packet = json.loads(native_path.read_text(encoding="utf-8"))
        self.assertEqual(set(packet), {"schema_version", "fixture_receipt", "whole"})
        self.assertIs(type(packet["schema_version"]), int)
        self.assertEqual(packet["schema_version"], 1)
        fixture = packet["fixture_receipt"]
        self.assertEqual(fixture["original_target_kind"], "typed_fixture_callback")
        self.assertIs(fixture["native_EXE_invoked"], False)
        for field in ("application_invocations", "application_original_invocations",
                      "writer_original_invocations"):
            self.assertEqual(fixture[field], 1)
        for field in ("original_exactly_once_per_wrapper",
                      "actual_return_pointer_preserved",
                      "entry_writer_full_id_association_proven",
                      "full_id_membership_proven",
                      "physical_entry_request_cache_distinct",
                      "owner_unit_generation_fallback_observed",
                      "owned_capture_survives_source_mutation"):
            self.assertIs(fixture[field], True)
        whole = packet["whole"]
        self.assertEqual(whole["type"], "command_result")
        self.assertIs(whole["ok"], True)
        native = whole["result"]
        self.assertEqual(native["step"], "query-army-strengths-v1")
        self.assertIs(native["accepted"], True)
        self.assertEqual(native["status"], "available")
        self._assert_observations(native["army_strengths"], fixture)

        receipt: dict[str, object] = {
            "date": "2026-10-10", "iso_week": "2026-W41", "status": "RED",
            "source_root": str(repository), "native_wire": str(native_path),
            "registered_tool": ROUTE, "native_producer_reexecution": 0,
            "native_body_rewrites": 0, "calls": [],
            "synthetic_boundary": "hello/paused scope/request_id correlation only",
            "native_fixture_receipt": fixture,
        }
        watched = {
            ("mcp_server.py", ROUTE), ("service.py", "query_army_strengths"),
            ("native_driver.py", "execute_step"),
            ("native_driver.py", "_execute_army_strength_query"),
            ("war_contract.py", "_normalize_army_strength_row"),
            ("battle_casualty_observation_contract.py",
             "normalize_battle_casualty_observations_v1"),
        }
        endpoint = _PreservedWholeEndpoint(whole)
        driver = None
        previous_profile = sys.getprofile()
        previous_thread_profile = threading.getprofile()

        def observe(frame, event, value):
            key = (Path(frame.f_code.co_filename).name, frame.f_code.co_name)
            if key not in watched:
                return
            if event == "call":
                receipt["calls"].append({"source": frame.f_code.co_filename,
                                         "function": key[1]})
                if key == ("service.py", "query_army_strengths"):
                    self.assertIs(type(frame.f_locals["self"]), GameplayBridgeService)
                    self.assertIs(frame.f_locals["self"].driver, driver)
            elif event == "return" and key == ("native_driver.py", "execute_step"):
                receipt["driver_result"] = deepcopy(value)
            elif event == "return" and key == ("service.py", "query_army_strengths"):
                receipt["service_result"] = deepcopy(value)

        try:
            sys.setprofile(observe)
            threading.setprofile(observe)
            driver = NativeHeadlessGameplayDriver(
                endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=1.0,
                state_dir=output_dir / "driver-state", episode_projection="native_campaign")
            server = create_server(driver)
            self.assertIn(ROUTE, server._tool_manager._tools)
            endpoint.publish({
                "type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
                "pid": 4242, "connection_generation": 1,
                "game_version": CK3_12004.game_version,
                "executable_sha256": CK3_12004.executable_sha256,
                "expected_ck3_version": CK3_12004.game_version,
                "expected_ck3_sha256": CK3_12004.executable_sha256,
                "capabilities": ["game.state.snapshot", war_contract.QUERY_ARMY_STRENGTHS_CAPABILITY],
            })
            endpoint.publish({
                "type": "state_snapshot", "protocol_version": 1,
                "snapshot_id": "native:1", "revision": 1,
                "state": {
                    "phase": "map_hud", "date": "synthetic-current-not-live",
                    "date_raw": fixture["observed_date_raw"], "speed": 1,
                    "paused": True, "map_ready": True, "history": [], "active_event": None,
                    "pending_character_interaction": None,
                    "played_character": {"character_id": fixture["owner_character_id"],
                                         "alive": True},
                    "player_armies": [
                        {"army_id": army_id, "controllable": True,
                         "owner_character_id": fixture["owner_character_id"],
                         "current_province_id": 100}
                        for army_id in (11, 12)
                    ],
                    "active_wars": [],
                },
            })
            before = driver.take_snapshot()
            self.assertEqual(before["snapshot_id"], "native:1")
            self.assertEqual(before["native_revision"], 1)
            result = await server.call_tool(ROUTE, {
                "army_ids": [11, 12], "expected_revision": before["revision"],
            })
            self.assertIs(result.is_error, False)
            registered = result.structured_content
            self.assertIsInstance(registered, dict)
            self.assertEqual(registered, receipt["service_result"])
            _assert_native_values(self, native, receipt["driver_result"], "driver")
            _assert_native_values(self, native, registered, "registered")
            self._assert_observations(registered["army_strengths"], fixture)
            for field in ("snapshot_id", "revision", "native_revision", "date_raw"):
                self.assertEqual(registered["source"][field], before[field])
            executed = {(Path(item["source"]).name, item["function"])
                        for item in receipt["calls"]}
            self.assertTrue(watched <= executed, executed)
            commands = [item for item in endpoint.requests if item["type"] == "execute_step"]
            self.assertEqual(len(commands), 1)
            self.assertEqual(commands[0]["expected_revision"], before["native_revision"])
            self.assertEqual(len(endpoint.delivered), 1)
            delivered = endpoint.delivered[0]
            self.assertEqual(delivered["result"], native)
            for key in whole:
                if key != "request_id":
                    self.assertEqual(delivered[key], whole[key])
            receipt["transport_requests"] = deepcopy(endpoint.requests)
            receipt["registered_result"] = result.model_dump(mode="json", by_alias=True)
            receipt["status"] = "GREEN"
        except BaseException:
            receipt["error"] = traceback.format_exc()
            raise
        finally:
            sys.setprofile(previous_profile)
            threading.setprofile(previous_thread_profile)
            if driver is not None:
                driver.close()
            (output_dir / "COMPOUND-RECEIPT.json").write_text(
                json.dumps(receipt, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8", newline="\n")

    def _assert_observations(self, rows, fixture) -> None:
        self.assertEqual([row["army_id"] for row in rows], [11, 12])
        matched, other_generation = rows
        full_id = fixture["current_full_regiment_id"]
        wrong_id = fixture["same_index_other_generation_id"]
        self.assertNotEqual(full_id, wrong_id)
        self.assertEqual(full_id & 0xFFFFFF, wrong_id & 0xFFFFFF)
        self.assertEqual(matched["regiment_strengths"][0]["army_regiment_id"], full_id)
        self.assertEqual(other_generation["regiment_strengths"][0]["army_regiment_id"], wrong_id)
        for row in rows:
            observations = row[FAMILY]
            self.assertEqual(observations["status"], "available")
            self.assertEqual(observations["source"], "native_battle_casualty_application_entry_return")
            self.assertEqual(observations["membership_basis"], "membership_at_query")
            self.assertIs(observations["observer_installed"], False)
            self.assertEqual(observations["oldest_available_sequence"], 1)
            self.assertEqual(observations["latest_sequence"], 1)
            self.assertEqual(observations["overwritten_events"], 0)
            self.assertEqual(row[WRITER_FAMILY]["latest_sequence"], 1)
        self.assertEqual(other_generation[FAMILY]["event_count"], 0)
        self.assertEqual(other_generation[FAMILY]["events"], [])
        self.assertEqual(other_generation[WRITER_FAMILY]["event_count"], 0)
        self.assertEqual(other_generation[WRITER_FAMILY]["events"], [])
        self.assertEqual(matched[FAMILY]["event_count"], 1)
        self.assertEqual(matched[WRITER_FAMILY]["event_count"], 1)
        event = matched[FAMILY]["events"][0]
        writer = matched[WRITER_FAMILY]["events"][0]
        self.assertEqual(event["sequence"], 1)
        self.assertEqual(event["entry_identity"], fixture["entry_identity"])
        self.assertEqual(event["entry_army_regiment_id"], full_id)
        self.assertEqual(event["soft_request_raw"], 250000)
        self.assertEqual(event["hard_request_raw"], 750000)
        self.assertEqual(event["raw_scale"], 100000)
        self.assertEqual(event["soldiers_scale"], 1)
        self.assertEqual(event["observed_date_raw"], fixture["observed_date_raw"])
        self.assertEqual(event["before_fighting_raw"], 10000000)
        self.assertEqual(event["before_soft_raw"], 500000)
        self.assertEqual(event["after_fighting_raw"], 9000000)
        self.assertEqual(event["after_soft_raw"], 750000)
        self.assertIs(event["same_entry_after"], True)
        self.assertEqual(event["nested_writer_event_count"], 1)
        self.assertEqual(event["writer_sequence"], writer["sequence"])
        self.assertEqual(event["writer_sequence"], 1)
        self.assertEqual(event["writer_army_regiment_id"], writer["army_regiment_id"])
        self.assertEqual(event["writer_army_regiment_id"], full_id)
        self.assertEqual(event["writer_request_raw"], writer["request_raw"])
        self.assertEqual(event["writer_request_raw"], 750000)
        self.assertIs(event["entry_writer_association_proven"], True)
        self.assertIs(event["physical_capture_complete"], True)
        self.assertEqual(event["actual_physical_soldier_debit"], 7)
        self.assertEqual(event["actual_physical_soldier_debit"], writer["actual_physical_soldier_debit"])
        self.assertEqual(writer["cached_current_delta"], -5)
        self.assertEqual(writer["before_current_soldiers"], 100)
        self.assertEqual(writer["after_current_soldiers"], 95)
        self.assertEqual(writer["physical_slots"][0]["before"]["current_soldiers"], 100)
        self.assertEqual(writer["physical_slots"][0]["after"]["current_soldiers"], 93)
        self.assertEqual(event["owner_army"], {
            "reference_demanded": True,
            "requested_full_id": fixture["owner_army_id"],
            "resolved_full_id": fixture["owner_army_id"],
            "used_fallback": False, "read_complete": True,
        })
        requested = fixture["requested_unit_id"]
        generation_mismatch = fixture["wrong_unit_generation_id"]
        self.assertNotEqual(requested, generation_mismatch)
        self.assertEqual(requested & 0xFFFFFF, generation_mismatch & 0xFFFFFF)
        self.assertEqual(event["owner_unit"], {
            "reference_demanded": True, "requested_full_id": requested,
            "resolved_full_id": fixture["fallback_unit_id"],
            "used_fallback": True, "read_complete": True,
        })
        self.assertEqual(event["owner_character_id"], fixture["owner_character_id"])
        self.assertEqual(event["original_return_identity"], fixture["original_return_identity"])
        self.assertEqual(event["owner_hard_ledger_after_raw"], 1250000)
        self.assertNotIn("person_died", event)


if __name__ == "__main__":
    unittest.main(verbosity=2)
