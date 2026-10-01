"""Actual C++ payloads; explicitly synthetic transport/context scaffolding."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.epidemic_treatment_private_transport import (
    STEP as TREATMENT_STEP, query_player_epidemic_treatment_presence_private_v1,
)
from xar_autoplayer.bridge.epidemic_recovery_private_transport import (
    STEP as RECOVERY_STEP, TITLE_STEP_PREFIX,
    query_player_epidemic_recovery_private_v1,
)
from xar_autoplayer.epidemic_recovery_formal_observer import (
    capture_epidemic_recovery_before_option, observe_epidemic_recovery_after_option,
)


FIXTURES = ROOT / "native_bridge/research/fixtures/ck3_12002_epidemic_material"
EVENT_INSTANCE = 71  # Synthetic event context, not a native-emitted event.


def payload(domain: str, name: str) -> dict[str, object]:
    return json.loads((FIXTURES / domain / name).read_text(encoding="utf-8"))


def paused_context(value: dict[str, object], *, event: bool) -> dict[str, object]:
    revision = value["snapshot_revision"]
    return {
        "snapshot_id": f"native:{revision}", "revision": revision + 1,
        "native_revision": revision, "date_raw": value["date_raw"],
        "paused": True, "map_ready": True, "episode_run_id": "ce1-material-fixture",
        "played_character": {"character_id": value["played_character_id"], "alive": True},
        "active_event": {"instance_id": EVENT_INSTANCE} if event else None,
        "pending_character_interaction": None, "one_life_terminal_reason": None,
    }


class SyntheticCe1EnvelopeDriver:
    """Exercise the production query's inline validator, not a native caller."""

    allow_private_epidemic_treatment_presence_query = True
    allow_private_epidemic_recovery_query = True

    def __init__(self, value: dict[str, object], domain: str) -> None:
        self.value = deepcopy(value)
        self.domain = domain
        self.context = paused_context(value, event=domain == "recovery" and value["requested_title_id"] == 0)
        self.sent: list[dict[str, object]] = []
        self.endpoint = self
        self.state = self

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(self.context)

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(deepcopy(request))

    def wait_for_command_result(self, request_id: str, timeout_seconds: float) -> dict[str, object]:
        # Only self.value is actual native output. Every outer field below is
        # declared synthetic scaffolding, with no actual cache/SDK qualification.
        inner_key = ("player_epidemic_treatment_presence" if self.domain == "treatment"
                     else "player_epidemic_recovery")
        return {
            "type": "command_result", "protocol_version": 1, "request_id": request_id,
            "ok": True, "result": {
                "step": self.sent[-1]["step"], "accepted": True,
                "status": self.value["status"], "query_sequence": len(self.sent),
                "observation_revision": len(self.sent),
                "snapshot_revision": self.value["snapshot_revision"],
                inner_key: deepcopy(self.value),
                "private_build": True, "read_only": True, "advertised": False,
                "backend_id": "native-headless",
            },
        }


def treatment_query(driver: SyntheticCe1EnvelopeDriver) -> dict[str, object]:
    return query_player_epidemic_treatment_presence_private_v1(
        driver, expected_revision=driver.context["revision"],
    )


def recovery_query(driver: SyntheticCe1EnvelopeDriver) -> dict[str, object]:
    title = driver.value["requested_title_id"]
    return query_player_epidemic_recovery_private_v1(
        driver, expected_revision=driver.context["revision"], requested_title_id=title,
        expected_event_instance_id=EVENT_INSTANCE if title == 0 else None,
    )


class SyntheticNearPairService:
    """Actual county payloads, synthetic event/context, no action or legitimacy."""

    def __init__(self) -> None:
        self.driver = SyntheticCe1EnvelopeDriver(payload("recovery", "two-counties.json"), "recovery")
        self.after_titles = {
            row["requested_title_id"]: row for row in (
                payload("recovery", "explicit-title-after.json"),
                payload("recovery", "explicit-title-b-after.json"),
            )
        }

    def snapshot(self) -> dict[str, object]:
        return self.driver.take_snapshot()

    def query_player_epidemic_recovery_private_v1(self, **request: object) -> dict[str, object]:
        title = request.get("requested_title_id", 0)
        if title:
            self.driver.value = deepcopy(self.after_titles[title])
        return query_player_epidemic_recovery_private_v1(self.driver, **request)

    def query_campaign_root_context_v1(self, *, expected_revision: int) -> dict[str, object]:
        frame = self.snapshot()
        return {
            "queried_snapshot_id": frame["snapshot_id"], "queried_revision": expected_revision,
            "queried_native_revision": frame["native_revision"],
            "campaign_root_context": {
                "player_character_id": frame["played_character"]["character_id"],
                "player_legitimacy_v1": {"status": "unavailable",
                                         "unavailable_reason": "not_in_material_payload_fixture"},
            },
        }

    def advance_fixture_context(self) -> None:
        self.driver.context = paused_context(next(iter(self.after_titles.values())), event=False)


class Ce1Material12002PayloadConsumerTest(unittest.TestCase):
    def test_six_treatment_payloads_reach_the_existing_production_query_validator(self) -> None:
        for name in payload("treatment", "provenance.json")["payload_sha256"]:
            with self.subTest(payload=name):
                native = payload("treatment", name)
                driver = SyntheticCe1EnvelopeDriver(native, "treatment")
                actual = treatment_query(driver)
                self.assertEqual(actual["player_epidemic_treatment_presence"], native)
                self.assertEqual(actual["queried_native_revision"], native["snapshot_revision"])
                self.assertEqual(driver.sent[0]["step"], TREATMENT_STEP)
                self.assertEqual(driver.sent[0]["expected_revision"], native["snapshot_revision"])
        self.assertIs(payload("treatment", "present.json")["present"], True)
        self.assertIs(payload("treatment", "empty-extension.json")["present"], False)
        self.assertIsNone(payload("treatment", "rows-unavailable.json")["present"])

    def test_nine_recovery_payloads_preserve_full_titles_empty_lists_and_unavailability(self) -> None:
        for name in payload("recovery", "provenance.json")["payload_sha256"]:
            with self.subTest(payload=name):
                native = payload("recovery", name)
                driver = SyntheticCe1EnvelopeDriver(native, "recovery")
                actual = recovery_query(driver)
                self.assertEqual(actual["player_epidemic_recovery"], native)
                self.assertEqual(actual["queried_native_revision"], native["snapshot_revision"])
                title = native["requested_title_id"]
                expected_step = TITLE_STEP_PREFIX + str(title) if title else RECOVERY_STEP
                self.assertEqual(driver.sent[0]["step"], expected_step)
                self.assertEqual(driver.sent[0]["expected_revision"], native["snapshot_revision"])
        self.assertEqual(payload("recovery", "empty-list.json")["counties"], [])
        self.assertIsNone(payload("recovery", "list-unavailable.json")["counties"])
        self.assertTrue(all(row["landed_title_id"] > 0x00FFFFFF
                            for row in payload("recovery", "two-counties.json")["counties"]))

    def test_actual_same_day_88_to_89_county_payloads_reach_the_production_near_pair_observer(self) -> None:
        service = SyntheticNearPairService()
        frame = service.snapshot()
        candidate = {
            "snapshot_id": frame["snapshot_id"], "revision": frame["revision"],
            "selected_step": "select-event-option-3",
            "plan": {
                "phase": "active_event_registry_choice", "active_event": {"instance_id": EVENT_INSTANCE},
                "event_decision": {
                    "status": "recommended", "event_definition_key": "epidemic_events.0110",
                    "selected_native_option_index": 2, "selected_option_number": 3,
                },
            },
        }
        before = capture_epidemic_recovery_before_option(service, candidate)
        self.assertEqual(before["before_counties"], payload("recovery", "two-counties.json")["counties"])
        service.advance_fixture_context()
        actual = observe_epidemic_recovery_after_option(service, before, service.snapshot())
        self.assertEqual(actual["before_frame"]["native_revision"], 88)
        self.assertEqual(actual["after_frame"]["native_revision"], 89)
        self.assertEqual(actual["before_frame"]["date_raw"], actual["after_frame"]["date_raw"])
        self.assertEqual(actual["status"], "verified_new_modifier_presence")
        self.assertEqual([row["newly_present"] for row in actual["counties"]], [["minor"], ["tiny"]])
        for row in actual["counties"]:
            self.assertEqual(row["after"], service.after_titles[row["landed_title_id"]]["counties"][0])
        self.assertIsNone(actual["legitimacy"]["delta_raw"])
        self.assertEqual(actual["remaining_days"], {"status": "unavailable", "value": None})
        self.assertFalse(actual["date_advanced"])
        self.assertEqual(len(service.driver.sent), 3)


if __name__ == "__main__":
    unittest.main()
