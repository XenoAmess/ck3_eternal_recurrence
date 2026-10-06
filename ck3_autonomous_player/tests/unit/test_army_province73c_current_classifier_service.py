"""One FIRST compound for five compiled, nonempty current-classifier wires.

Source delivery is NOT RUN. The native fixture constructs the world and emits
the production collector / Army serializer result. This consumer retains those
whole results and rebinds request_id only. Session frames and the endpoint are
synthetic; Driver protocol ingest/wait, strict normalization, Service and its
pure admission projection are production code. No CK3, SDK server or pipe runs.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12003
from xar_autoplayer.simulation.army_daily_assault_roster_admission_12003 import (
    daily_assault_roster_admission_requests_12003,
)


LEAF = "current_daily_assault_roster_admission_v1"
STEP = "query-army-strengths-v1"
CASES = (("case-0", 0), ("case-1", 1), ("case-2", 2),
         ("case-unbound", None), ("case-not-demanded", None))
FIELDS = ("native_2c099f0_character_identity", "native_2c099f0_province_identity",
          "native_2c099f0_third_argument_is_null", "native_2c099f0_returned",
          "native_2c099f0_classification_raw_i32")
QUALIFICATION = (
    "Five whole compiled production Army collector/serializer result packets; "
    "synthetic native world, session frames and in-memory endpoint; unmodified "
    "NativeHeadlessGameplayDriver protocol ingest/wait, strict Army contract, "
    "GameplayBridgeService and pure current admission derivation; request_id "
    "rebound only. No CK3, named pipe, MCP/SDK server, actual next callback, "
    "future table placement, daily/monthly loop or gameplay action."
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


class _CompiledResultEndpoint:
    """Fixture session plumbing into the real driver's protocol receiver."""

    def __init__(self, case: str, packet: dict) -> None:
        self.pipe_name = rf"\\.\pipe\xar_province73c_first_{case}"
        self.packet = deepcopy(packet)
        self.on_frame = None
        self.sent = []
        self.replies = []

    def start(self, on_frame, on_disconnect) -> None:
        self.on_frame = on_frame

    def publish(self, frame: dict) -> None:
        require(self.on_frame is not None, "fixture endpoint was not started")
        self.on_frame(json.loads(json.dumps(frame)))

    def send(self, request: dict) -> None:
        self.sent.append(deepcopy(request))
        if request.get("type") == "execute_step":
            require(request.get("step") == STEP, "unexpected production command")
            require(self.packet["result"]["step"] == STEP, "compiled packet step differs")
            reply = deepcopy(self.packet)
            reply["request_id"] = request["request_id"]
            self.replies.append(deepcopy(reply))
            self.publish(reply)

    def transport_error(self):
        return None

    def close(self) -> None:
        return None


def _synthetic_session(army: dict) -> tuple[dict, dict]:
    hello = {
        "type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
        "pid": 4242, "session_generation": 0,
        "game_version": CK3_12003.game_version,
        "executable_sha256": CK3_12003.executable_sha256,
        "capabilities": ["game.state.snapshot", "game.command.query-army-strengths-v1"],
    }
    snapshot = {
        "type": "state_snapshot", "protocol_version": 1,
        "snapshot_id": "native:7", "revision": 7,
        "state": {
            "phase": "map_hud", "date": "1066.9.15", "date_raw": 53288232,
            "speed": 1, "paused": True, "map_ready": True, "history": [],
            "active_event": None, "pending_character_interaction": None,
            "played_character": {"character_id": 29829, "alive": True},
            "played_character_gold": None, "played_character_prestige": None,
            "played_character_piety": None, "one_life_settlement": None,
            "active_wars": [], "player_armies": [{
                "army_id": army["army_id"], "owner_character_id": 29829,
                "soldiers": army["current_soldiers"], "current_province_id": 2619,
                "move_target_province_id": None, "controllable": True,
            }],
        },
    }
    return hello, snapshot


def run_compound(wire_dir: Path, receipt: Path | None = None) -> dict:
    """Consume exactly five new native whole packets through complete Service."""
    started = datetime.now(timezone.utc).isoformat()
    outputs = {}
    for case, expected_classification in CASES:
        packet = json.loads((wire_dir / f"{case}.json").read_text(encoding="utf-8-sig"))
        original_packet = deepcopy(packet)
        require(packet["type"] == "command_result" and packet["ok"] is True,
                "native fixture must emit a successful whole command result")
        require(packet["result"]["step"] == STEP, "wrong native query result")
        native_rows = packet["result"]["army_strengths"]
        require(len(native_rows) == 1, "FIRST must preserve one nonempty scoped Army row")
        native_army = native_rows[0]
        native_leaf = native_army[LEAF]
        require(native_leaf["original_roster"]["count_raw_i32"] > 0,
                "FIRST admission input must retain a nonempty original roster")
        require(len(native_leaf["occurrences"]) == native_leaf["original_roster"]["count_raw_i32"],
                "compiled admission roster coverage differs")
        gate = native_leaf["occurrences"][0]["gate"]
        require(all(field in gate for field in FIELDS), "compiled classifier extension is incomplete")
        require(type(gate["native_2c099f0_returned"]) is bool, "native return readiness is malformed")
        if case == "case-not-demanded":
            require(gate["native_2c099f0_returned"] is False, "unused classifier was called")
            require(all(gate[name] is None for name in FIELDS if name != "native_2c099f0_returned"),
                    "early false guard fabricated classifier operands")
        else:
            require(gate["province_character_id_73c_raw_u32"] == 0xFFFFFFFF,
                    "FIRST does not reach the genuine Province73C sentinel branch")
            require(gate["native_2c099f0_character_identity"] ==
                    gate["associated_character_resolution"]["object_identity"],
                    "classifier did not retain selected associated Character")
            require(gate["native_2c099f0_province_identity"] == gate["original_unit_province_identity"],
                    "classifier did not retain original Unit20 Province")
            require(gate["native_2c099f0_third_argument_is_null"] is True,
                    "classifier third argument differs from native null War selector")
            raw_classification = gate["native_2c099f0_classification_raw_i32"]
            if expected_classification is None:
                require(gate["native_2c099f0_returned"] is False and raw_classification is None,
                        "unbound classifier invented a native return")
                require(gate["unavailable_reason"] == "province_73c_2c099f0_getter_unbound",
                        "unbound callback lost its precise reason")
            else:
                require(gate["native_2c099f0_returned"] is True,
                        "native classifier success lacks returned evidence")
                require(type(raw_classification) is int and raw_classification == expected_classification,
                        "native signed classification was changed or converted to bool")
                require(gate["verdict"] is (expected_classification == 0),
                        "native admission must compare EAX directly with zero")

        endpoint = _CompiledResultEndpoint(case, packet)
        driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
                                              episode_projection="native_campaign")
        try:
            hello, semantic = _synthetic_session(native_army)
            endpoint.publish(hello)
            endpoint.publish(semantic)
            before = driver.take_snapshot()
            service = GameplayBridgeService(driver)
            returned = service.query_army_strengths([native_army["army_id"]],
                                                   expected_revision=before["revision"])
            observed = returned["army_strengths"][0][LEAF]
            projection = returned["current_daily_assault_roster_admission_inputs_v1"][0]["projection"]
            require(observed == native_leaf, "production strict normalization changed native classifier DTO")
            require(returned["status"] == packet["result"]["status"], "service changed current Army status")
            require(returned["queried_native_revision"] == semantic["revision"],
                    "driver lost the current native snapshot binding")
            require(projection["native_calls_executed"] == 0 and projection["native_writes_executed"] == 0,
                    "pure admission projection claimed a native call or write")
            for flag in ("actual_next_callback_ready", "actual_tomorrow_roster_ready",
                         "full_future_table_placement_ready", "full_daily_assault_ready", "full_monthly"):
                require(projection[flag] is False, f"current classifier falsely completed {flag}")
            if case == "case-unbound":
                require(projection["conditional_admission_ready"] is False,
                        "unbound classifier completed conditional admission")
                require(projection["occurrences"][0]["gate"]["unavailable_reason"] ==
                        "province_73c_2c099f0_getter_unbound", "pure gate lost unbound provenance")
                require(not projection["request_prefix"], "unbound classifier fabricated an append request")
            else:
                require(projection["conditional_admission_ready"] is True,
                        "observed classifier / early guard did not close current admission")
                requests = daily_assault_roster_admission_requests_12003(projection)
                if case == "case-0":
                    require(len(requests) > 0, "classification zero did not yield a nonempty append request")
                    require(projection["occurrences"][0]["gate"]["verdict"] is True,
                            "classification zero did not admit current gate")
                else:
                    require(not requests and projection["occurrences"][0]["gate"]["verdict"] is False,
                            "nonzero classifier / early false guard incorrectly admitted an append")
            commands = [frame for frame in endpoint.sent if frame.get("type") == "execute_step"]
            require(len(commands) == 1 and commands[0]["step"] == STEP,
                    "complete Service must send exactly one current Army query per case")
            require(endpoint.replies[0]["result"] == original_packet["result"],
                    "fixture endpoint replaced native result fields")
            require(driver.state.wait_for_command_result(commands[0]["request_id"], 0) is None,
                    "production wait did not consume the correlated command result")
            require(packet == original_packet, "FIRST consumer modified compiled input packet")
            outputs[case] = {"native_classifier": {field: gate[field] for field in FIELDS},
                             "service": returned, "production_query_count": len(commands)}
        finally:
            driver.close()

    result = {"status": "GREEN", "qualification": QUALIFICATION,
              "started_at_utc": started, "ended_at_utc": datetime.now(timezone.utc).isoformat(),
              "wire_directory": str(wire_dir.resolve()), "cases": outputs,
              "new_compound_count": 1, "native_whole_result_count": 5,
              "production_query_count": 5, "synthetic_fixture": True, "live": False,
              "game_launched": False, "sdk_server_started": False, "named_pipe_used": False}
    if receipt is not None:
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


class ArmyProvince73CCurrentClassifierServiceTests(unittest.TestCase):
    def test_five_compiled_whole_results_through_driver_service_current_gate(self) -> None:
        directory = os.environ.get("XAR_PROVINCE73C_CURRENT_CLASSIFIER_FIRST_WIRE_DIR")
        if not directory:
            self.skipTest("FIRST NOT RUN: ROOT must provide the newly compiled native wholewire directory")
        receipt = os.environ.get("XAR_PROVINCE73C_CURRENT_CLASSIFIER_FIRST_RECEIPT")
        run_compound(Path(directory), Path(receipt) if receipt else None)


if __name__ == "__main__":
    unittest.main()
