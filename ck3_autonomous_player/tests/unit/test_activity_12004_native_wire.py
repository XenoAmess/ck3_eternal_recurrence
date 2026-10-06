"""Current-4 metadata through real Activity consumers using archived DTO wire.

The hello is a fixture for CK3 1.20.0.4. The unmodified payload files retain
their historical 1.20.0.2/3 names and C++ provenance. This is a Python consumer
compatibility case, not a current-4 native reader, serializer or live result.
No game process, SDK, pipe, desktop, or old test module is used.
"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
FIXTURES = ROOT / "native_bridge" / "research" / "fixtures"

from xar_autoplayer.bridge.activity_feast_stage5_start_private_transport import (
    INPUT_STEP, POST_STEP, RESOURCE_KEYS, START_STEP,
    query_activity_feast_hosted_post_private_v1,
    query_activity_feast_stage5_start_inputs_private_v1,
    submit_activity_feast_stage5_start_private_v1,
)
from xar_autoplayer.bridge.activity_feast_terminal_outcome_v1 import (
    normalize_activity_feast_terminal_outcome_v1,
)
from xar_autoplayer.bridge.activity_stage5_feast_full_cost_private_transport import (
    STEP as COST_STEP, query_activity_stage5_feast_full_cost_private_v1,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.version_identity import (
    CK3_12002, CK3_12003, CK3_12004, NativeBuildIdentity,
)

CURRENT_VERSION = "1.20.0.4"
CURRENT_SHA256 = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"


def archived_wire(name: str) -> object:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class ActivityFixtureDriver:
    """In-memory endpoint; payload bytes come from the archived stable wire."""

    allow_private_activity_stage5_feast_full_cost_query = True
    allow_private_activity_feast_stage5_start_query = True
    allow_private_activity_feast_stage5_start_action = True

    def __init__(
        self, payload: dict[str, object], *, build: NativeBuildIdentity = CK3_12004,
    ) -> None:
        self.payload = payload
        self.endpoint = self
        self.state = self
        self.requests: list[dict[str, object]] = []
        self.snapshot = {
            "snapshot_id": "activity-current-build-fixture:" + str(payload["snapshot_revision"]),
            "revision": 5,
            "native_revision": payload["snapshot_revision"],
            "date_raw": payload["date_raw"],
            "paused": True,
            "map_ready": True,
            "played_character": {
                "character_id": payload["actor_character_id"], "alive": True,
            },
            "diagnostics": {"hello": {
                "expected_ck3_version": build.game_version,
                "expected_ck3_sha256": build.executable_sha256,
                "actual_sha256": build.executable_sha256,
            }},
        }

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(self.snapshot)

    def send(self, request: dict[str, object]) -> None:
        self.requests.append(request)

    def wait_for_command_result(self, request_id: str, _: float) -> dict[str, object]:
        step = self.requests[-1]["step"]
        key = {
            COST_STEP: "activity_stage5_feast_full_cost",
            INPUT_STEP: "activity_feast_stage5_start_inputs",
            POST_STEP: "activity_feast_hosted_post",
            START_STEP: "activity_feast_stage5_start",
        }[step]
        pending = step == START_STEP
        payload = {
            "schema": "activity-feast-stage5-start-private-action-v1",
            "submitted": True,
            "native_status": "submitted_pending",
            "precondition": deepcopy(self.payload),
        } if pending else self.payload
        return {
            "type": "command_result", "protocol_version": 1,
            "request_id": request_id, "ok": True,
            "result": {
                "step": step, "accepted": True,
                "status": "pending" if pending else "available",
                "private_build": True, "read_only": not pending,
                "advertised": False, "backend_id": "native-headless",
                key: payload,
            },
        }


class Activity12004NativeWireTests(unittest.TestCase):
    def test_current_build_consumes_cost_guest_start_and_hosted_terminal_wire(self) -> None:
        self.assertEqual(CK3_12004.game_version, CURRENT_VERSION)
        self.assertEqual(CK3_12004.executable_sha256, CURRENT_SHA256)

        cost_wire = archived_wire("ck3_12002_feast_fullcost_wire.json")
        cost_driver = ActivityFixtureDriver(cost_wire)
        cost = query_activity_stage5_feast_full_cost_private_v1(
            cost_driver, expected_revision=5,
        )
        self.assertEqual(cost["exact_ck3_build"], CURRENT_VERSION)
        self.assertEqual(cost["exe_sha256"], CURRENT_SHA256)
        self.assertEqual(cost["resources"], cost_wire["resources"])
        self.assertEqual(cost["actor_gold_raw"], 134000000)
        self.assertEqual(cost["resources"]["piety"]["configured_cost_raw"], -100000)
        self.assertEqual(cost["resources"]["barter_goods"]["resource_index"], 8)
        self.assertIs(cost["final_can_start"], False)
        self.assertEqual(cost["final_can_start_failure_display"],
                         cost_wire["final_can_start_failure_display"])
        self.assertEqual([item["step"] for item in cost_driver.requests], [COST_STEP])

        # The shared exact-build resolver also retains the old pairs. These
        # reads use the same stable payload, rather than rerunning old tests.
        for build in (CK3_12002, CK3_12003):
            historical = query_activity_stage5_feast_full_cost_private_v1(
                ActivityFixtureDriver(cost_wire, build=build), expected_revision=5,
            )
            self.assertEqual(historical["exact_ck3_build"], build.game_version)
            self.assertEqual(historical["exe_sha256"], build.executable_sha256)

        start_wires = archived_wire("ck3_12003_feast_ordinary_start_wire.json")
        reserve = {key: 0 for key in RESOURCE_KEYS}
        qualified_driver = ActivityFixtureDriver(start_wires[0])
        qualified = query_activity_feast_stage5_start_inputs_private_v1(
            qualified_driver, expected_revision=5,
        )
        self.assertEqual(qualified["exact_ck3_build"], CURRENT_VERSION)
        self.assertEqual(qualified["exe_sha256"], CURRENT_SHA256)
        self.assertEqual(qualified["ordinary_guest_route"],
                         start_wires[0]["ordinary_guest_route"])
        self.assertEqual(qualified["ordinary_guest_route"]["candidate"]["character_id"], 37502)
        self.assertIs(qualified["native_guest_route_qualified"], True)
        self.assertEqual([item["step"] for item in qualified_driver.requests], [INPUT_STEP])
        pending = submit_activity_feast_stage5_start_private_v1(
            qualified_driver, inputs=qualified, reserve_raw=reserve,
        )
        self.assertEqual(pending["exact_ck3_build"], CURRENT_VERSION)
        self.assertEqual(pending["exe_sha256"], CURRENT_SHA256)
        self.assertEqual(pending["native_status"], "submitted_pending")
        self.assertNotIn("success", pending)
        self.assertEqual([item["step"] for item in qualified_driver.requests],
                         [INPUT_STEP, START_STEP])

        unqualified_driver = ActivityFixtureDriver(start_wires[1])
        unqualified = query_activity_feast_stage5_start_inputs_private_v1(
            unqualified_driver, expected_revision=5,
        )
        self.assertIs(unqualified["native_guest_route_qualified"], False)
        self.assertIs(unqualified["ordinary_guest_route"]["candidate_membership"], False)
        with self.assertRaisesRegex(BridgeUnavailableError, "lacks qualified inputs"):
            submit_activity_feast_stage5_start_private_v1(
                unqualified_driver, inputs=unqualified, reserve_raw=reserve,
            )
        self.assertEqual([item["step"] for item in unqualified_driver.requests], [INPUT_STEP])

        hosted_wires = archived_wire("ck3_12002_feast_hosted_post_wire.json")
        for wire, status in zip(hosted_wires, ("ongoing", "completed", "invalidated"), strict=True):
            hosted_driver = ActivityFixtureDriver(wire)
            post = query_activity_feast_hosted_post_private_v1(
                hosted_driver, expected_revision=5,
            )
            self.assertEqual(post["balances"], wire["balances"])
            self.assertEqual(post["hosted_activities"], wire["hosted_activities"])
            terminal = normalize_activity_feast_terminal_outcome_v1(
                post, activity_id=16777234, actor_character_id=29829,
            )
            self.assertEqual(terminal["exact_ck3_build"], CURRENT_VERSION)
            self.assertEqual(terminal["exe_sha256"], CURRENT_SHA256)
            self.assertEqual(terminal["status"], status)
            self.assertIs(terminal["native_completed"], status == "completed")
            self.assertIs(terminal["native_invalidated"], status == "invalidated")
            self.assertEqual([item["step"] for item in hosted_driver.requests], [POST_STEP])


if __name__ == "__main__":
    unittest.main()
