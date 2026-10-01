"""Service GOV use with frozen actual payload and explicit synthetic ordinary intent.

The hello/state/GOV primitive are original production packets. Only the service
planning view has a synthetic ordinary goal/binding, nonwar view and a clearly
synthetic successor case. This does not claim an ordinary campaign live loop.
The original outer government RED packet is neither repaired nor ingested.
"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.native_driver import NativeProtocolState
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.succession_transition_contract import (
    ORDINARY_CAMPAIGN_SUCCESSION, bind_succession_lifecycle_from_environment_v1,
)
from xar_autoplayer.strategy import new_ordinary_campaign_goal_v1


FIXTURES = ROOT / "tests/fixtures/ck3_12002_government_protocol_live_fix"
CAMPAIGN_ID = "synthetic-ordinary-nonwar-service-government"


def wire(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8-sig"))


def ordinary_nonwar_fixture_snapshot() -> dict[str, object]:
    protocol = NativeProtocolState("offline-service-government-fixture")
    protocol.ingest(wire("hello.json"))
    protocol.ingest(wire("initial-state.json"))
    snapshot = protocol.semantic_snapshot()
    snapshot["succession_lifecycle"] = bind_succession_lifecycle_from_environment_v1(
        {"environment_sha256": "a" * 64,
         "rules": {"profile": [{"rule": "xar_enabled", "setting": "xar_off"}]}},
        lifecycle=ORDINARY_CAMPAIGN_SUCCESSION, ordinary_campaign_no_pact=True,
    )
    snapshot["campaign_goal"] = new_ordinary_campaign_goal_v1(
        CAMPAIGN_ID, snapshot["played_character"]["character_id"],
    )
    # These two overlays only select the nonwar service path in an offline
    # planning fixture. The original production state packet remains unchanged.
    snapshot["active_wars"] = []
    snapshot["player_armies"] = []
    return snapshot


class OrdinaryGovernmentFixtureDriver:
    """Record the service's query use; return the untouched actual primitive."""

    def __init__(self, *, enabled: bool = True, query_error: Exception | None = None) -> None:
        self.snapshot = ordinary_nonwar_fixture_snapshot()
        self.government = wire("government-response-red.json")["result"]["government_runtime_adapter"]
        self.allow_private_government_runtime_adapter_query = enabled
        self.query_error = query_error
        self.queries: list[dict[str, object]] = []

    def capabilities(self) -> dict[str, object]:
        return {"action_steps": ["life-advance"], "bridge_capabilities": []}

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(self.snapshot)

    def query_government_runtime_adapter_private_v1(self, *, expected_revision: int) -> dict[str, object]:
        self.queries.append({
            "expected_revision": expected_revision,
            "character_id": self.snapshot["played_character"]["character_id"],
            "date_raw": self.snapshot["date_raw"],
        })
        if self.query_error is not None:
            raise self.query_error
        return deepcopy(self.government)

    def select_synthetic_successor(self, character_id: int) -> None:
        self.snapshot["played_character"]["character_id"] = character_id
        self.snapshot["revision"] += 1
        self.snapshot["native_revision"] += 1
        self.snapshot["snapshot_id"] = f"synthetic-successor:{self.snapshot['native_revision']}"
        self.snapshot["campaign_goal"]["current_character_id"] = character_id
        # The actual GOV payload remains the observed predecessor primitive.


class G2NonwarServiceGovernmentTests(unittest.TestCase):
    def test_enabled_service_queries_every_turn_and_uses_only_current_actor_observation(self) -> None:
        driver = OrdinaryGovernmentFixtureDriver()
        service = GameplayBridgeService(driver)
        actual_government = deepcopy(driver.government)
        initial_revision = driver.snapshot["revision"]
        for _ in range(2):
            planned = service.plan_nonwar_turn()
            self.assertEqual(planned["plan"]["selected_step"], "life-advance")
            context = planned["plan"]["campaign_government_context_used"]
            self.assertEqual(context["government_runtime_adapter"], actual_government)
            self.assertEqual(context["current_character_id"], 29829)
            self.assertEqual(context["government_key"], "feudal_government")
            self.assertIs(context["ordinary_goal_context_ready"], True)
            self.assertEqual(context["government_runtime_adapter"]["effective_feature_flags"]["native_count"], 44)
        self.assertEqual(driver.queries, [
            {"expected_revision": initial_revision, "character_id": 29829, "date_raw": 53169072},
            {"expected_revision": initial_revision, "character_id": 29829, "date_raw": 53169072},
        ])
        driver.select_synthetic_successor(29830)
        planned = service.plan_nonwar_turn()
        self.assertEqual(planned["plan"]["selected_step"], "life-advance")
        context = planned["plan"]["campaign_government_context_used"]
        self.assertEqual(len(driver.queries), 3)
        self.assertEqual(driver.queries[-1]["character_id"], 29830)
        self.assertEqual(driver.queries[-1]["expected_revision"], driver.snapshot["revision"])
        self.assertEqual(context["current_character_id"], 29830)
        self.assertEqual(context["status"], "unavailable")
        self.assertIs(context["ordinary_goal_context_ready"], False)
        self.assertIsNone(context["government_key"])
        self.assertIsNone(context["government_runtime_adapter"])
        self.assertEqual(driver.government, actual_government)

    def test_off_service_keeps_base_nonwar_plan_without_any_government_query(self) -> None:
        driver = OrdinaryGovernmentFixtureDriver(enabled=False)
        planned = GameplayBridgeService(driver).plan_nonwar_turn()
        self.assertEqual(planned["plan"]["selected_step"], "life-advance")
        self.assertEqual(driver.queries, [])
        context = planned["plan"]["campaign_government_context_used"]
        self.assertEqual(context["status"], "not_queried")
        self.assertIs(context["query_permitted"], False)
        self.assertEqual(context["unavailable_reason"], "government_query_not_permitted")
        self.assertIsNone(context["government_runtime_adapter"])

    def test_typed_query_error_preserves_base_life_advance_and_error_metadata(self) -> None:
        error = BridgeUnavailableError("synthetic service query unavailable")
        driver = OrdinaryGovernmentFixtureDriver(query_error=error)
        planned = GameplayBridgeService(driver).plan_nonwar_turn()
        self.assertEqual(planned["plan"]["selected_step"], "life-advance")
        self.assertEqual(len(driver.queries), 1)
        context = planned["plan"]["campaign_government_context_used"]
        self.assertEqual(context["status"], "unavailable")
        self.assertIs(context["query_permitted"], True)
        self.assertIs(context["ordinary_goal_context_ready"], False)
        self.assertIsNone(context["government_runtime_adapter"])
        self.assertEqual(context["government_query_error"]["type"], "BridgeUnavailableError")
        self.assertEqual(context["government_query_error"]["message"], str(error))


if __name__ == "__main__":
    unittest.main()
