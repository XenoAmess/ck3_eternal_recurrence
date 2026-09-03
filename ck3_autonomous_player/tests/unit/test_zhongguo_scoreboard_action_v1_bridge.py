from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_zhongguo_scoreboard_action_contract import (  # noqa: E402
    CONNECTION_GENERATION,
    ENTRY,
    NATIVE_REVISION,
    PLAYER,
    PUBLIC_REVISION,
    _frame,
    _post,
    _request,
)
from test_zhongguo_scoreboard_state_v1_bridge import (  # noqa: E402
    SNAPSHOT_ID,
    _FakeEndpoint,
    _ServiceDriver as _StateServiceDriver,
    _native_result as _scoreboard_state_result,
    _semantic_snapshot,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError  # noqa: E402
from xar_autoplayer.bridge.mcp_server import (  # noqa: E402
    _ck3_activate_zhongguo_scoreboard_v1,
    create_server,
)
from xar_autoplayer.bridge.native_driver import (  # noqa: E402
    NativeHeadlessGameplayDriver,
)
from xar_autoplayer.bridge.service import GameplayBridgeService  # noqa: E402
from xar_autoplayer.bridge.zhongguo_scoreboard_action_cell import (  # noqa: E402
    run_zhongguo_scoreboard_action_cell,
)
from xar_autoplayer.bridge.zhongguo_scoreboard_action_contract import (  # noqa: E402
    ACTIVATE_ZHONGGUO_SCOREBOARD_V1_CAPABILITY,
    ACTIVATE_ZHONGGUO_SCOREBOARD_V1_STEP,
    ZHONGGUO_SCOREBOARD_ACTION_V1_TRANSPORT_CAPABILITY,
    ZhongguoScoreboardActionRequestV1,
    acknowledged_zhongguo_scoreboard_action_v1,
    normalize_native_zhongguo_scoreboard_action_v1_result,
    plan_zhongguo_scoreboard_action_v1,
)
from xar_autoplayer.bridge.zhongguo_scoreboard_state_contract import (  # noqa: E402
    QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_CAPABILITY,
    ZHONGGUO_SCOREBOARD_STATE_V1_BRIDGE_VERSION,
    ZHONGGUO_SCOREBOARD_STATE_V1_EXECUTABLE_SHA256,
    ZHONGGUO_SCOREBOARD_STATE_V1_GAME_ADAPTER_ID,
    ZHONGGUO_SCOREBOARD_STATE_V1_GAME_VERSION,
    parse_query_zhongguo_scoreboard_state_v1_step,
)


def _unavailable_result(
    request: ZhongguoScoreboardActionRequestV1,
) -> dict[str, object]:
    return {
        "step": ACTIVATE_ZHONGGUO_SCOREBOARD_V1_STEP,
        "accepted": False,
        "status": "unavailable",
        "request_nonce": request.request_nonce,
        "action": request.action,
        "action_sequence": 4,
        "snapshot_revision": NATIVE_REVISION,
        "rejection_reason": "action_dispatch_unavailable",
        "action_ack": None,
        "production_capability_advertised": False,
        "backend_id": "native-headless",
    }


class _ActionServiceDriver(_StateServiceDriver):
    def __init__(
        self, *, forged_ack: bool = False, valid_ack: bool = False
    ) -> None:
        super().__init__()
        self.forged_ack = forged_ack
        self.valid_ack = valid_ack
        self.action_applied = False
        self.request: ZhongguoScoreboardActionRequestV1 | None = None

    def capabilities(self) -> dict[str, object]:
        result = super().capabilities()
        result["bridge_capabilities"] = [
            *result["bridge_capabilities"],
            ZHONGGUO_SCOREBOARD_ACTION_V1_TRANSPORT_CAPABILITY,
        ]
        result["zhongguo_scoreboard_action_v1_transport_wired"] = True
        result["zhongguo_scoreboard_action_v1_supported"] = False
        return result

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        query = parse_query_zhongguo_scoreboard_state_v1_step(step)
        if query is None or expected_revision != PUBLIC_REVISION:
            raise AssertionError("service changed the typed scoreboard query")
        source = _frame(open_tab=None)
        frame = (
            _post(source, active_tab="received")
            if self.action_applied
            else source
        )
        frame["request_nonce"] = query.request_nonce
        return {
            **_scoreboard_state_result(frame),
            "backend_id": "native-headless",
            "queried_snapshot_id": SNAPSHOT_ID,
            "queried_revision": PUBLIC_REVISION,
            "queried_native_revision": NATIVE_REVISION,
            "queried_connection_generation": CONNECTION_GENERATION,
        }

    def activate_zhongguo_scoreboard_v1(
        self,
        request: ZhongguoScoreboardActionRequestV1,
        *,
        expected_revision: int,
    ) -> dict[str, object]:
        self.request = request
        if expected_revision != PUBLIC_REVISION:
            raise AssertionError("service changed the public revision")
        result = _unavailable_result(request)
        if self.valid_ack:
            source = _frame(open_tab=None)
            plan = plan_zhongguo_scoreboard_action_v1(
                request,
                source_state=source,
                observed_revision=PUBLIC_REVISION,
                observed_connection_generation=CONNECTION_GENERATION,
            )
            result.update(
                {
                    "accepted": True,
                    "status": "acknowledged_verification_pending",
                    "rejection_reason": None,
                    "action_ack": acknowledged_zhongguo_scoreboard_action_v1(
                        plan
                    ),
                }
            )
            self.action_applied = True
        elif self.forged_ack:
            result.update(
                {
                    "accepted": True,
                    "status": "acknowledged_verification_pending",
                    "rejection_reason": None,
                    # Deliberately no valid ACK and no production capability.
                    "action_ack": {},
                }
            )
        return {
            **result,
            "queried_snapshot_id": SNAPSHOT_ID,
            "queried_revision": PUBLIC_REVISION,
            "queried_native_revision": NATIVE_REVISION,
            "queried_connection_generation": CONNECTION_GENERATION,
        }


def _action_arguments() -> dict[str, object]:
    source = _frame(open_tab=None)
    request = _request(
        source, action="open", target_identity=ENTRY["received"]
    )
    return {
        "request_nonce": request.request_nonce,
        "action": request.action,
        "expected_revision": request.expected_revision,
        "expected_native_revision": request.expected_native_revision,
        "expected_connection_generation": (
            request.expected_connection_generation
        ),
        "expected_player_character_id": request.expected_player_character_id,
        "expected_provider_session_id": request.expected_provider_session_id,
        "expected_observation_sequence": request.expected_observation_sequence,
        "expected_observed_state_revision": (
            request.expected_observed_state_revision
        ),
        "expected_tree_fingerprint_v1": request.expected_tree_fingerprint_v1,
        "expected_semantic_fingerprint_v1": (
            request.expected_semantic_fingerprint_v1
        ),
        "expected_window_instance_pointer": (
            request.expected_window_instance_pointer
        ),
        "expected_target_instance_pointer": (
            request.expected_target_instance_pointer
        ),
        "expected_target_vtable_pointer": (
            request.expected_target_vtable_pointer
        ),
    }


class ZhongguoScoreboardActionV1ServiceTests(unittest.TestCase):
    def test_native_driver_keeps_public_revision_in_a_separate_wire_field(self) -> None:
        endpoint = _FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=0.1,
        )
        endpoint.publish(
            {
                "type": "hello",
                "protocol_version": 1,
                "bridge_version": ZHONGGUO_SCOREBOARD_STATE_V1_BRIDGE_VERSION,
                "pid": 6868,
                "session_generation": 0,
                "game_version": ZHONGGUO_SCOREBOARD_STATE_V1_GAME_VERSION,
                "expected_ck3_version": (
                    ZHONGGUO_SCOREBOARD_STATE_V1_GAME_VERSION
                ),
                "executable_sha256": (
                    ZHONGGUO_SCOREBOARD_STATE_V1_EXECUTABLE_SHA256
                ),
                "expected_ck3_sha256": (
                    ZHONGGUO_SCOREBOARD_STATE_V1_EXECUTABLE_SHA256
                ),
                "game_adapter_id": (
                    ZHONGGUO_SCOREBOARD_STATE_V1_GAME_ADAPTER_ID
                ),
                "capabilities": [
                    "game.state.snapshot",
                    QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_CAPABILITY,
                    ZHONGGUO_SCOREBOARD_ACTION_V1_TRANSPORT_CAPABILITY,
                ],
            }
        )
        endpoint.publish(_semantic_snapshot())
        snapshot = driver.take_snapshot()
        diagnostics = snapshot["diagnostics"]
        request = ZhongguoScoreboardActionRequestV1(
            request_nonce="scoreboard.native.transport",
            action="open",
            expected_revision=int(snapshot["revision"]),
            expected_native_revision=int(snapshot["native_revision"]),
            expected_connection_generation=int(
                diagnostics["connection_generation"]
            ),
            expected_player_character_id=PLAYER,
            expected_provider_session_id=(
                "0123456789ABCDEF0123456789ABCDEF"
            ),
            expected_observation_sequence=7,
            expected_observed_state_revision=3,
            expected_tree_fingerprint_v1="A" * 64,
            expected_semantic_fingerprint_v1="B" * 64,
            expected_window_instance_pointer="0x14000200",
            expected_target_instance_pointer="0x14000600",
            expected_target_vtable_pointer="0x14506020",
        )

        def answer(wire: dict[str, object]) -> None:
            raw = _unavailable_result(request)
            raw["snapshot_revision"] = snapshot["native_revision"]
            endpoint.publish(
                {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": wire["request_id"],
                    "ok": True,
                    "result": raw,
                }
            )

        endpoint.send_hook = answer
        result = driver.activate_zhongguo_scoreboard_v1(
            request, expected_revision=int(snapshot["revision"])
        )
        sent = endpoint.frames[-1]
        self.assertEqual(
            set(sent),
            {
                "type",
                "protocol_version",
                "request_id",
                "step",
                "expected_revision",
                "request_nonce",
                "action",
                "expected_public_revision",
                "expected_native_revision",
                "expected_connection_generation",
                "expected_player_character_id",
                "expected_provider_session_id",
                "expected_observation_sequence",
                "expected_observed_state_revision",
                "expected_tree_fingerprint_v1",
                "expected_semantic_fingerprint_v1",
                "expected_window_instance_pointer",
                "expected_target_instance_pointer",
                "expected_target_vtable_pointer",
            },
        )
        self.assertEqual(
            sent["expected_revision"], snapshot["native_revision"]
        )
        self.assertEqual(
            sent["expected_public_revision"], snapshot["revision"]
        )
        self.assertFalse(result["accepted"])
        capabilities = driver.capabilities()
        self.assertTrue(
            capabilities["zhongguo_scoreboard_action_v1_transport_wired"]
        )
        self.assertFalse(
            capabilities["zhongguo_scoreboard_action_v1_supported"]
        )
        self.assertNotIn(
            ACTIVATE_ZHONGGUO_SCOREBOARD_V1_STEP,
            capabilities["action_steps"],
        )

    def test_service_and_helper_publish_typed_unavailable_not_capability(self) -> None:
        driver = _ActionServiceDriver()
        result = _ck3_activate_zhongguo_scoreboard_v1(
            GameplayBridgeService(driver), **_action_arguments()
        )
        self.assertFalse(result["accepted"])
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(
            result["rejection_reason"], "action_dispatch_unavailable"
        )
        self.assertIsNone(result["action_ack"])
        self.assertFalse(result["production_capability_advertised"])
        self.assertIsNotNone(driver.request)
        self.assertEqual(driver.request.expected_revision, PUBLIC_REVISION)
        self.assertEqual(
            driver.request.expected_native_revision, NATIVE_REVISION
        )
        capabilities = GameplayBridgeService(driver).capabilities()
        self.assertTrue(
            capabilities["zhongguo_scoreboard_action_v1_transport_wired"]
        )
        self.assertFalse(
            capabilities["zhongguo_scoreboard_action_v1_supported"]
        )
        self.assertNotIn(
            ACTIVATE_ZHONGGUO_SCOREBOARD_V1_CAPABILITY,
            capabilities["bridge_capabilities"],
        )

    def test_malformed_transport_ack_is_rejected_before_service_returns_it(self) -> None:
        with self.assertRaisesRegex(
            BridgeUnavailableError, "scoreboard action ACK has unexpected fields"
        ):
            _ck3_activate_zhongguo_scoreboard_v1(
                GameplayBridgeService(_ActionServiceDriver(forged_ack=True)),
                **_action_arguments(),
            )

    def test_reusable_cell_preserves_source_action_later_query_as_red(self) -> None:
        evidence = run_zhongguo_scoreboard_action_cell(
            GameplayBridgeService(_ActionServiceDriver())
        )
        self.assertEqual(evidence["result"], "RED")
        self.assertFalse(evidence["verified_pass"])
        self.assertFalse(evidence["production_capability_advertised"])
        self.assertIsInstance(evidence["source_query"], dict)
        self.assertIsInstance(evidence["action_result"], dict)
        self.assertIsInstance(evidence["later_query"], dict)
        self.assertIsNone(evidence["verified_postcondition"])
        self.assertEqual(
            evidence["failure_reason"], "action_dispatch_unavailable"
        )

    def test_exact_ack_without_production_advertisement_remains_red(self) -> None:
        evidence = run_zhongguo_scoreboard_action_cell(
            GameplayBridgeService(_ActionServiceDriver(valid_ack=True))
        )
        self.assertEqual(evidence["result"], "RED")
        self.assertIsInstance(evidence["action_result"]["action_ack"], dict)
        self.assertIsInstance(evidence["later_query"], dict)
        self.assertFalse(evidence["production_capability_advertised"])
        self.assertEqual(
            evidence["failure_reason"],
            "production_capability_not_advertised",
        )
        self.assertIsInstance(evidence["verified_postcondition"], dict)
        self.assertTrue(evidence["verified_pass"])

    def test_native_result_normalizer_rejects_false_production_mirror(self) -> None:
        request = _request(
            _frame(open_tab=None),
            action="open",
            target_identity=ENTRY["received"],
        )
        normalized = normalize_native_zhongguo_scoreboard_action_v1_result(
            _unavailable_result(request), expected_request=request
        )
        self.assertFalse(normalized["accepted"])
        forged = copy.deepcopy(_unavailable_result(request))
        forged["production_capability_advertised"] = True
        with self.assertRaises(ValueError):
            normalize_native_zhongguo_scoreboard_action_v1_result(
                forged, expected_request=request
            )


@unittest.skipIf(
    importlib.util.find_spec("mcp") is None,
    "optional MCP SDK not installed",
)
class ZhongguoScoreboardActionV1McpTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_tool_returns_red_and_rejects_unknown_fields(self) -> None:
        from mcp import Client

        async with Client(create_server(_ActionServiceDriver())) as client:
            listed = await client.list_tools()
            self.assertIn(
                "ck3_activate_zhongguo_scoreboard_v1",
                {tool.name for tool in listed.tools},
            )
            accepted = await client.call_tool(
                "ck3_activate_zhongguo_scoreboard_v1", _action_arguments()
            )
            rejected = await client.call_tool(
                "ck3_activate_zhongguo_scoreboard_v1",
                {**_action_arguments(), "widget_name": "arbitrary"},
            )

        self.assertFalse(accepted.is_error)
        self.assertEqual(accepted.structured_content["status"], "unavailable")
        self.assertFalse(
            accepted.structured_content["production_capability_advertised"]
        )
        self.assertTrue(rejected.is_error)


if __name__ == "__main__":
    unittest.main()
