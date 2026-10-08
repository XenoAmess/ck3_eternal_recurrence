"""AUTHORED_NOTRUN: one new current-task scalar registered-MCP compound.

Root supplies fresh whole-native mailbox envelopes through
CK3_COUNCIL_TASK_DOMAIN_TAX_NATIVE_WIRE_DIR and owns FIRST. The enclosing
paused snapshot is explicitly synthetic; no game or old fixture is used.
Only the outer command_result request_id changes for transport correlation.
"""

from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [
    str(ROOT / "src"),
    str(ROOT.parent / "tools"),
    str(ROOT.parent / "ck3_workshop_mcp" / "src"),
]

from xar_autoplayer.bridge.council_private_transport_v1 import PRIVATE_GATES_STEP
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12004


_TOOL = "ck3_query_council_final_gates_private_v1"
_POSITION_KEY = "councillor_steward"
_LEAF_KEY = "current_task_owner_domain_tax_mult_v1"
_SCENES = (
    ("positive-gates.json", 24_000, False),
    ("zero-gates.json", 0, False),
    ("negative-gates.json", -5_000, True),
    ("keyword-mismatch-gates.json", None, False),
)
_LEAF_FIELDS = {
    "status", "unavailable_reason", "active_task_id", "owner_character_id",
    "incumbent_character_id", "task_key", "frozen", "modifier_id", "keyword_id",
    "observed_keyword_key", "value",
}


class _WholeNativeCouncilEndpoint:
    """Replay one complete producer envelope through the real driver cache."""

    pipe_name = r"\\.\pipe\xar-council-task-domain-tax-12004-whole-fixture"

    def __init__(self, frame: dict[str, object]) -> None:
        self.frame = deepcopy(frame)
        self.requests: list[dict[str, object]] = []
        self.published: list[dict[str, object]] = []
        self.on_frame = None
        self.closed = False

    def start(self, on_frame, on_disconnect) -> None:
        self.on_frame = on_frame

    def send(self, request: dict[str, object]) -> None:
        if (
            request.get("type") != "execute_step"
            or request.get("protocol_version") != 1
            or request.get("step") != PRIVATE_GATES_STEP
            or request.get("expected_revision") != 7
            or request.get("position_key") != _POSITION_KEY
            or self.requests
        ):
            raise AssertionError("expected exactly one selected-Steward read")
        self.requests.append(deepcopy(request))
        packet = deepcopy(self.frame)
        packet["request_id"] = request["request_id"]
        self.published.append(deepcopy(packet))
        if self.on_frame is None:
            raise AssertionError("native endpoint was not started")
        self.on_frame(packet)

    def close(self) -> None:
        self.closed = True


def _synthetic_paused_snapshot() -> dict[str, object]:
    """Use the existing whole-driver fixture's minimal enclosing frame shape."""
    return {
        "snapshot_id": "synthetic:council-task-tax12004",
        "revision": 8,
        "native_revision": 7,
        "date_raw": 53_178_264,
        "paused": True,
        "map_ready": True,
        "backend_id": "native-headless",
        "episode_run_id": "offline-council-task-domain-tax12004",
        "played_character": {"character_id": 29_829, "alive": True},
        "active_wars": [],
        "player_armies": [],
        "diagnostics": {
            "connection_generation": 1,
            "hello": {
                "expected_ck3_version": CK3_12004.game_version,
                "expected_ck3_sha256": CK3_12004.executable_sha256,
                "game_version": CK3_12004.game_version,
                "executable_sha256": CK3_12004.executable_sha256,
            },
        },
    }


class CouncilCurrentTaskDomainTaxRegistered12004Tests(unittest.IsolatedAsyncioTestCase):
    async def test_new_whole_native_tax_leaf_reaches_registered_council_tool(self) -> None:
        from mcp import Client

        wire_dir = Path(os.environ["CK3_COUNCIL_TASK_DOMAIN_TAX_NATIVE_WIRE_DIR"])
        wires = {
            name: json.loads((wire_dir / name).read_text(encoding="utf-8-sig"))
            for name, _, _ in _SCENES
        }
        originals = deepcopy(wires)
        snapshot = _synthetic_paused_snapshot()
        observations = []

        for name, expected_raw, expected_frozen in _SCENES:
            with self.subTest(native_wire=name):
                frame = wires[name]
                self.assertEqual(
                    set(frame), {"type", "protocol_version", "request_id", "ok", "result"}
                )
                self.assertEqual(frame["type"], "command_result")
                self.assertEqual(frame["protocol_version"], 1)
                self.assertEqual(frame["request_id"], "fixture:council-task-tax12004")
                self.assertIs(frame["ok"], True)
                native_result = frame["result"]
                self.assertEqual(native_result["step"], PRIVATE_GATES_STEP)
                self.assertIs(native_result["accepted"], True)
                self.assertEqual(native_result["status"], "available")
                self.assertEqual(native_result["query_sequence"], 1)
                self.assertEqual(native_result["snapshot_revision"], 7)
                native_gates = native_result["council_final_gates"]
                native_candidates = native_gates["council_composition_candidates"]
                native_leaf = native_candidates["position"][_LEAF_KEY]
                self.assertEqual(native_candidates["snapshot"]["snapshot_id"], "native:7")
                self.assertEqual(native_candidates["snapshot"]["public_revision"], 7)
                self.assertEqual(native_candidates["snapshot"]["native_revision"], 7)
                self.assertEqual(native_candidates["snapshot"]["date_raw"], snapshot["date_raw"])
                self.assertEqual(native_candidates["owner_character_id"], 29_829)
                self.assertEqual(native_candidates["exact_build"], {
                    "game_version": CK3_12004.game_version,
                    "executable_sha256": CK3_12004.executable_sha256,
                })

                endpoint = _WholeNativeCouncilEndpoint(frame)
                with TemporaryDirectory(prefix="council-tax12004-consumer-") as state_dir:
                    driver = NativeHeadlessGameplayDriver(
                        endpoint.pipe_name, endpoint=endpoint, state_dir=state_dir,
                        command_timeout_seconds=1.0, episode_projection="native_campaign",
                    )
                    driver.allow_private_council_query = True
                    driver.allow_private_council_action = False
                    try:
                        with patch.object(
                            driver, "take_internal_semantic_snapshot",
                            side_effect=lambda: deepcopy(snapshot),
                        ):
                            async with Client(create_server(driver)) as client:
                                response = await client.call_tool(_TOOL, {
                                    "expected_revision": 8, "position_key": _POSITION_KEY,
                                })
                        self.assertFalse(response.is_error, response.content)
                        observed = response.structured_content
                        self.assertIsInstance(observed, dict)
                        self.assertEqual(observed["queried_revision"], 8)
                        self.assertEqual(observed["queried_native_revision"], 7)
                        self.assertEqual(observed["queried_snapshot_id"], snapshot["snapshot_id"])
                        self.assertEqual(observed["exact_build"], native_candidates["exact_build"])
                        self.assertIs(observed["read_only"], True)
                        self.assertIs(observed["private_build"], True)
                        self.assertIs(observed["advertised"], False)
                        candidates = observed["council_composition_candidates"]
                        gates = observed["council_final_gates"]
                        leaf = candidates["position"][_LEAF_KEY]
                        self.assertEqual(leaf, native_leaf)
                        self.assertEqual(set(leaf), _LEAF_FIELDS)
                        self.assertEqual(leaf["active_task_id"], 6_100)
                        self.assertEqual(leaf["owner_character_id"], 29_829)
                        self.assertEqual(leaf["incumbent_character_id"], 32_440)
                        self.assertEqual(leaf["task_key"], "collect_taxes")
                        self.assertIs(leaf["frozen"], expected_frozen)
                        # Unique captured descriptor row183: modifier162 / keyword11976.
                        self.assertEqual(leaf["modifier_id"], 162)
                        self.assertEqual(leaf["keyword_id"], 11_976)
                        if expected_raw is None:
                            self.assertEqual(leaf["status"], "unavailable")
                            self.assertEqual(
                                leaf["unavailable_reason"], "current_task_owner_tax_keyword_mismatch"
                            )
                            self.assertIsNone(leaf["value"])
                            self.assertNotEqual(leaf["observed_keyword_key"], "domain_tax_mult")
                        else:
                            self.assertEqual(leaf["status"], "available")
                            self.assertIsNone(leaf["unavailable_reason"])
                            self.assertEqual(leaf["observed_keyword_key"], "domain_tax_mult")
                            self.assertEqual(leaf["value"], {"raw": expected_raw, "scale": 100_000})

                        self.assertEqual(gates["council_composition_candidates"], candidates)
                        self.assertEqual(
                            {key: value for key, value in gates.items()
                             if key != "council_composition_candidates"},
                            {key: value for key, value in native_gates.items()
                             if key != "council_composition_candidates"},
                        )
                        self.assertEqual(gates["status"], "available")
                        self.assertEqual(candidates["candidates"], native_candidates["candidates"])
                        self.assertEqual(candidates["readiness"], native_candidates["readiness"])
                        position = candidates["position"]
                        self.assertEqual(position["position_key"], _POSITION_KEY)
                        self.assertEqual(position["incumbent_character_id"], 32_440)
                        self.assertEqual(position["incumbent_main_skill"]["value"], 11)
                        self.assertEqual([row["character_id"] for row in candidates["candidates"]], [32_716])
                        self.assertEqual(candidates["candidates"][0]["main_skill"]["value"], 22)
                        self.assertIs(candidates["candidates"][0]["eligible"], True)
                        self.assertEqual(len(endpoint.requests), 1)
                        self.assertEqual(endpoint.published[0]["result"], native_result)
                        self.assertEqual(
                            {key: value for key, value in endpoint.published[0].items()
                             if key != "request_id"},
                            {key: value for key, value in frame.items() if key != "request_id"},
                        )
                        self.assertEqual(endpoint.frame, frame)
                        self.assertIsNone(driver.state.wait_for_command_result(
                            endpoint.requests[0]["request_id"], 0
                        ))
                        observations.append({
                            "native_wire": str(wire_dir / name),
                            "request": endpoint.requests[0], "result": observed,
                        })
                    finally:
                        driver.close()
                self.assertTrue(endpoint.closed)

        self.assertEqual(wires, originals)
        output = os.environ.get("CK3_COUNCIL_TASK_DOMAIN_TAX_CONSUMER_OUTPUT")
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps({
                "qualification": "offline registered MCP consumer; synthetic enclosing snapshot; not live",
                "native_wire_directory": str(wire_dir), "compound_cases": 1,
                "whole_native_packets": 4, "registered_tool_calls": 4,
                "native_packet_changes": "outer request_id correlation only",
                "game_actions": 0, "observations": observations,
            }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
