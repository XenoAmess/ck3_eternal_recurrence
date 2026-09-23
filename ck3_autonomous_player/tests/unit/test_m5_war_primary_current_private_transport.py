from __future__ import annotations

import copy
import inspect
from types import SimpleNamespace
import unittest

from xar_autoplayer.bridge.driver import (
    BridgeUnavailableError,
    UnsupportedStepError,
)
from xar_autoplayer.bridge.m5_war_primary_current_private_transport import (
    PREWAR_PLAYER_CLAIM_STEP_PREFIX,
    STEP_PREFIX,
    query_m5_war_primary_current_private_v1,
    query_prewar_player_claim_current_private_v1,
)
from xar_autoplayer.bridge.mcp_server import (
    _ck3_query_m5_war_primary_current_private_v1,
)
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver


ACTOR = 29_829
TARGET = 31_549


def _declaration() -> dict[str, object]:
    return {
        "declaration_id": "31549-7-0",
        "target_character_id": TARGET,
        "casus_belli_index": 7,
        "casus_belli_key": "minor_religious_war",
        "configuration_index": 0,
        "claimant_character_id": ACTOR,
        "target_title_ids": [1234],
    }


def _snapshot(*, with_army: bool = False) -> dict[str, object]:
    armies: list[dict[str, object]] = []
    if with_army:
        armies.append(
            {
                "army_id": 83_886_341,
                "owner_character_id": ACTOR,
                "soldiers": 950,
                "current_province_id": 2610,
                "move_target_province_id": 2628,
                "move_target_observable": True,
                "route_province_ids": [2611, 2628],
                "controllable": True,
                "source": "native",
            }
        )
    return {
        "snapshot_id": "native:49",
        "revision": 14,
        "native_revision": 49,
        "date_raw": 53_144_328,
        "paused": True,
        "map_ready": True,
        "played_character": {"character_id": ACTOR, "alive": True},
        "played_character_gold": {"raw": 0, "scale": 100_000},
        "declarable_wars": [_declaration()],
        "active_wars": [{"war_id": 16_777_231}],
        "player_armies": armies,
    }


def _payload(*, with_army: bool = False) -> dict[str, object]:
    armies: list[dict[str, object]] = []
    supply: list[dict[str, object]] = []
    if with_army:
        armies.append(
            {
                "army_id": 83_886_341,
                "owner_character_id": ACTOR,
                "has_current_province": True,
                "current_province_id": 2610,
                "move_target_observable": True,
                "move_target_province_id": 2628,
                "route_province_ids": [2611, 2628],
            }
        )
        supply.append(
            {
                "army_id": 83_886_341,
                "native_carmy_id": 117_440_789,
                "owner_character_id": ACTOR,
                "current_supply_raw": 1_750_000,
                "current_supply_scale": 100_000,
            }
        )
    declaration = _declaration()
    declaration.pop("declaration_id")
    return {
        "status": "available_current_primary_slice",
        "native_revision": 49,
        "date_raw": 53_144_328,
        "actor_character_id": ACTOR,
        "declaration": declaration,
        "effective_target_character_id": TARGET,
        "native_power_ratio_raw": 251_000,
        "native_power_ratio_scale": 100_000,
        "current_treasury": {"raw": 0, "scale": 100_000},
        "active_war_ids": [16_777_231],
        "actor_current_raised_armies": armies,
        "actor_current_raised_supply": supply,
    }


class _Endpoint:
    def __init__(self) -> None:
        self.sent: list[dict[str, object]] = []

    def send(self, frame: dict[str, object]) -> None:
        self.sent.append(copy.deepcopy(frame))


class _State:
    def __init__(self, endpoint: _Endpoint, payload: dict[str, object]) -> None:
        self.endpoint = endpoint
        self.payload = payload

    def wait_for_command_result(
        self, request_id: str, timeout_seconds: float
    ) -> dict[str, object]:
        assert timeout_seconds > 0
        request = self.endpoint.sent[-1]
        assert request["request_id"] == request_id
        return {
            "type": "command_result",
            "protocol_version": 1,
            "request_id": request_id,
            "ok": True,
            "result": {
                "step": request["step"],
                "accepted": True,
                "status": "available",
                "m5_war_primary_current": copy.deepcopy(self.payload),
            },
        }


class _Driver:
    def __init__(
        self,
        payload: dict[str, object],
        *,
        with_army: bool = False,
        enabled: bool = True,
    ) -> None:
        self.allow_private_m5_war_primary_current_query = enabled
        self.endpoint = _Endpoint()
        self.state = _State(self.endpoint, payload)
        self.snapshot = _snapshot(with_army=with_army)

    def take_snapshot(self) -> dict[str, object]:
        return copy.deepcopy(self.snapshot)


class M5WarPrimaryCurrentPrivateTransportTest(unittest.TestCase):
    def test_zero_treasury_and_no_raised_army_are_positive_observations(self) -> None:
        driver = _Driver(_payload())
        result = query_m5_war_primary_current_private_v1(
            driver,
            target_character_id=TARGET,
            expected_revision=14,
            timeout_seconds=1,
        )
        self.assertEqual(driver.endpoint.sent[0]["step"], STEP_PREFIX + str(TARGET))
        self.assertEqual(driver.endpoint.sent[0]["expected_revision"], 49)
        current = result["m5_war_primary_current"]
        self.assertEqual(current["current_treasury"], {"raw": 0, "scale": 100_000})
        self.assertEqual(current["actor_current_raised_armies"], [])
        self.assertEqual(current["actor_current_raised_supply"], [])
        self.assertTrue(result["readiness"]["current_treasury_ready"])
        self.assertFalse(result["readiness"]["campaign_cost_ready"])
        self.assertFalse(result["readiness"]["minimum_gold_reserve_ready"])
        self.assertFalse(result["readiness"]["war_proposal_ready"])
        self.assertFalse(result["advertised"])


    def test_nonempty_army_and_supply_bind_to_same_public_frame(self) -> None:
        result = query_m5_war_primary_current_private_v1(
            _Driver(_payload(with_army=True), with_army=True),
            target_character_id=TARGET,
            expected_revision=14,
        )
        current = result["m5_war_primary_current"]
        self.assertEqual(
            current["actor_current_raised_armies"][0]["route_province_ids"],
            [2611, 2628],
        )
        self.assertEqual(
            current["actor_current_raised_supply"][0]["current_supply_raw"],
            1_750_000,
        )

    def test_disabled_and_malformed_resource_rows_are_red(self) -> None:
        with self.assertRaises(UnsupportedStepError):
            query_m5_war_primary_current_private_v1(
                _Driver(_payload(), enabled=False),
                target_character_id=TARGET,
                expected_revision=14,
            )
        malformed = _payload(with_army=True)
        malformed["current_treasury"]["scale"] = 1
        with self.assertRaisesRegex(BridgeUnavailableError, "treasury"):
            query_m5_war_primary_current_private_v1(
                _Driver(malformed, with_army=True),
                target_character_id=TARGET,
                expected_revision=14,
            )
        missing_supply = _payload(with_army=True)
        missing_supply["actor_current_raised_supply"] = []
        with self.assertRaisesRegex(BridgeUnavailableError, "does not cover"):
            query_m5_war_primary_current_private_v1(
                _Driver(missing_supply, with_army=True),
                target_character_id=TARGET,
                expected_revision=14,
            )

    def test_rejects_frame_drift(self) -> None:
        driver = _Driver(_payload())
        calls = 0

        def snapshot() -> dict[str, object]:
            nonlocal calls
            calls += 1
            value = _snapshot()
            if calls > 1:
                value["date_raw"] = 53_144_352
            return value

        driver.take_snapshot = snapshot  # type: ignore[method-assign]
        with self.assertRaisesRegex(BridgeUnavailableError, "crossed"):
            query_m5_war_primary_current_private_v1(
                driver,
                target_character_id=TARGET,
                expected_revision=14,
            )

    def test_driver_flag_defaults_off_and_mcp_seam_stays_private(self) -> None:
        parameter = inspect.signature(NativeHeadlessGameplayDriver.__init__).parameters[
            "allow_private_m5_war_primary_current_query"
        ]
        self.assertIs(parameter.default, False)
        calls: list[dict[str, int]] = []

        class Driver:
            def query_m5_war_primary_current_private_v1(
                self, *, target_character_id: int, expected_revision: int
            ) -> dict[str, object]:
                calls.append(
                    {"target": target_character_id, "revision": expected_revision}
                )
                return {"advertised": False, "read_only": True}

        result = _ck3_query_m5_war_primary_current_private_v1(
            SimpleNamespace(driver=Driver()), TARGET, 14
        )
        self.assertEqual(calls, [{"target": TARGET, "revision": 14}])
        self.assertFalse(result["advertised"])

def _claim_declaration() -> dict[str, object]:
    return {
        "declaration_id": "31549-8-0",
        "source": "native",
        "target_character_id": TARGET,
        "casus_belli_index": 8,
        "casus_belli_key": "claim_cb",
        "configuration_index": 0,
        "claimant_character_id": ACTOR,
        "target_title_ids": [1234],
    }


def _claim_driver() -> tuple[_Driver, dict[str, object], dict[str, object]]:
    selected = _claim_declaration()
    snapshot = _snapshot(with_army=True)
    snapshot["declarable_wars"] = [_declaration(), copy.deepcopy(selected)]
    snapshot["active_wars"] = []
    payload = _payload(with_army=True)
    payload["declaration"] = {
        key: value for key, value in selected.items()
        if key not in {"declaration_id", "source"}
    }
    payload["active_war_ids"] = []
    payload["prewar_player_claim"] = {
        "county_objective_province_id": 2610,
        "actor_default_raise_province_id": 2612,
        "effective_defender_default_raise_province_id": 2620,
        "primary_current_raised_armies": [
            {
                "army_id": 83_886_341, "native_carmy_id": 117_440_789,
                "owner_character_id": ACTOR, "side": "attacker",
                "current_province_id": 2610, "move_target_province_id": 2628,
                "route_province_ids": [2611, 2628],
            },
            {
                "army_id": 83_886_355, "native_carmy_id": 117_440_795,
                "owner_character_id": TARGET, "side": "defender",
                "current_province_id": 2614, "move_target_province_id": None,
                "route_province_ids": [],
            },
        ],
        "hypothetical_raised_roster_ready": False,
        "raise_legality_ready": False,
        "muster_time_ready": False,
        "complete_initial_participants_ready": False,
        "combat_forecast_ready": False,
    }
    root = {
        "status": "available", "snapshot_revision": 49,
        "date_raw": 53_144_328, "player_character_id": ACTOR,
        "readiness": {"ready": True},
        "government": {
            "key": "feudal_government", "flags": ["government_is_feudal"],
        },
    }
    driver = _Driver(payload, with_army=True)
    driver.snapshot = snapshot
    return driver, selected, root


class PrewarPlayerClaimPrivateTransportTest(unittest.TestCase):
    def _read(
        self, driver: _Driver, selected: dict[str, object], root: dict[str, object]
    ) -> dict[str, object]:
        return query_prewar_player_claim_current_private_v1(
            driver, selected_declaration=selected,
            campaign_root_context=root, expected_revision=14,
            timeout_seconds=1,
        )

    def test_binds_second_final_legal_claim_and_both_current_primary_armies(self) -> None:
        driver, selected, root = _claim_driver()
        result = self._read(driver, selected, root)
        self.assertEqual(
            driver.endpoint.sent[0]["step"],
            PREWAR_PLAYER_CLAIM_STEP_PREFIX + str(TARGET),
        )
        self.assertEqual(result["m5_war_primary_current"]["declaration"]["casus_belli_key"], "claim_cb")
        self.assertEqual(result["prewar_player_claim_current"]["county_objective_province_id"], 2610)
        self.assertEqual(result["prewar_player_claim_current"]["actor_default_raise_province_id"], 2612)
        self.assertEqual(result["prewar_player_claim_current"]["effective_defender_default_raise_province_id"], 2620)
        self.assertEqual(
            [row["side"] for row in result["prewar_player_claim_current"]["primary_current_raised_armies"]],
            ["attacker", "defender"],
        )
        self.assertFalse(result["advertised"])
        self.assertFalse(result["readiness"]["combat_forecast_ready"])
        self.assertFalse(result["readiness"]["hypothetical_raised_roster_ready"])
        self.assertFalse(result["readiness"]["raise_legality_ready"])
        self.assertFalse(result["readiness"]["muster_time_ready"])
        self.assertFalse(result["readiness"]["declaration_admission_ready"])

    def test_missing_default_muster_is_not_a_fabricated_army(self) -> None:
        driver, selected, root = _claim_driver()
        driver.state.payload["prewar_player_claim"]["actor_default_raise_province_id"] = None
        result = self._read(driver, selected, root)
        self.assertIsNone(result["prewar_player_claim_current"]["actor_default_raise_province_id"])
        self.assertFalse(result["readiness"]["actor_default_raise_province_ready"])
        self.assertEqual(len(result["prewar_player_claim_current"]["primary_current_raised_armies"]), 2)
        self.assertFalse(result["readiness"]["combat_forecast_ready"])

    def test_selected_identity_and_unique_target_are_required_before_command(self) -> None:
        driver, selected, root = _claim_driver()
        wrong = copy.deepcopy(selected)
        wrong["configuration_index"] = 1
        with self.assertRaisesRegex(BridgeUnavailableError, "unique same-target"):
            self._read(driver, wrong, root)
        driver.snapshot["declarable_wars"].append(copy.deepcopy(selected))
        with self.assertRaisesRegex(BridgeUnavailableError, "unique same-target"):
            self._read(driver, selected, root)
        self.assertEqual(driver.endpoint.sent, [])

    def test_feudal_frame_and_payload_fields_fail_closed(self) -> None:
        driver, selected, root = _claim_driver()
        root["snapshot_revision"] = 48
        with self.assertRaisesRegex(BridgeUnavailableError, "same-frame"):
            self._read(driver, selected, root)
        self.assertEqual(driver.endpoint.sent, [])
        root["snapshot_revision"] = 49
        driver.state.payload["prewar_player_claim"]["primary_current_raised_armies"][0]["army_id"] = 1
        with self.assertRaisesRegex(BridgeUnavailableError, "public snapshot"):
            self._read(driver, selected, root)

    def test_private_build_flag_defaults_off(self) -> None:
        parameter = inspect.signature(NativeHeadlessGameplayDriver.__init__).parameters[
            "allow_private_m5_war_primary_current_query"
        ]
        self.assertIs(parameter.default, False)
        self.assertTrue(hasattr(NativeHeadlessGameplayDriver, "query_prewar_player_claim_current_private_v1"))
        driver, selected, root = _claim_driver()
        driver.allow_private_m5_war_primary_current_query = False
        with self.assertRaises(UnsupportedStepError):
            self._read(driver, selected, root)


if __name__ == "__main__":
    unittest.main()
