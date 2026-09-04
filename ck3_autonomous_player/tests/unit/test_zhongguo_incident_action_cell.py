from __future__ import annotations

import copy
import unittest

from xar_autoplayer.bridge.event_window_context_contract import (
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY,
)
from xar_autoplayer.bridge.zhongguo_incident_action_cell import (
    INCIDENT_ACTION_CELL_ID,
    INCIDENT_PROFILES,
    SELECT_EVENT_OPTION_CAPABILITY,
    IncidentActionCellError,
    run_incident_xyz_gameplay_action_cell,
)
from xar_autoplayer.bridge.zhongguo_incident_snapshot_contract import (
    QUERY_ZHONGGUO_INCIDENT_SNAPSHOT_V1_CAPABILITY,
    ZHONGGUO_INCIDENT_KIND_V1,
)


PLAYER = 32_904
OWNER = 8_052
DATE_RAW = 53_147_016


def available(value: int) -> dict[str, object]:
    return {"status": "available", "value": value, "unavailable_reason": None}


def unavailable(reason: str) -> dict[str, object]:
    return {"status": "unavailable", "value": None, "unavailable_reason": reason}


def typed_character_scope(character_id: int) -> dict[str, object]:
    return {
        "status": "available",
        "raw_type_index": 4,
        "type_key": "character",
        "subtype": 0,
        "typed_identity": {
            "status": "available",
            "kind": "character",
            "character_id": character_id,
        },
    }


PROBE_KEYS = (
    "owner_character_id",
    "subject_character_id",
    "cycle_serial",
    "probe_serial",
    "result",
    "source_kind",
    "consequence_kind",
)
RESOURCE_KEYS = (
    "subject_personal_gold_q100000",
    "manager_treasury_q100000",
    "capital_control_q100000",
)
NA_KEYS = (
    "owner_character_id",
    "subject_character_id",
    "cycle_serial",
    "reason",
    "probe_serial",
    "receipt_serial",
    "applicable",
    "kpi_staged",
)
INCIDENT_KEYS = (
    "owner_character_id",
    "subject_character_id",
    "cycle_serial",
    "case_serial",
    "state",
    "revision",
    "incident_serial",
    "source_kind",
    "consequence_kind",
    "final_score",
    "applicable",
    "kpi_staged",
)


def unavailable_incident(profile: str, owner: int) -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "unavailable",
        "case_kind": ZHONGGUO_INCIDENT_KIND_V1,
        "profile": profile,
        "subject_character_id": PLAYER,
        "requested_owner_character_id": owner,
        "probe": {key: unavailable("snapshot_unavailable") for key in PROBE_KEYS},
        "resources": {
            key: unavailable("snapshot_unavailable") for key in RESOURCE_KEYS
        },
        "terminal": {"kind": "unavailable", "na": None, "incident": None},
        "kpi": {"disposition": "unavailable"},
        "readiness": {"ready": False},
        "unavailable_reason": "incident_not_found",
    }


def acl_incident(profile: str, owner: int) -> dict[str, object]:
    result = unavailable_incident(profile, owner)
    result["unavailable_reason"] = "owner_filter_mismatch"
    return result


def terminal_incident(
    profile: str,
    owner: int,
    *,
    kind: str,
) -> dict[str, object]:
    incident = kind == "incident"
    cycle = {"x": 7, "y": 6, "z": 7}[profile]
    probe_serial = {"x": 19, "y": 18, "z": 19}[profile]
    probe_values = {
        "owner_character_id": OWNER,
        "subject_character_id": PLAYER,
        "cycle_serial": cycle,
        "probe_serial": probe_serial,
        "result": 1 if incident else 0,
        "source_kind": 5 if incident else 0,
        "consequence_kind": 3 if incident else 0,
    }
    resources = {
        "subject_personal_gold_q100000": {
            "x": 4_200_000,
            "y": 5_200_000,
            "z": 4_200_000,
        }[profile],
        "manager_treasury_q100000": {
            "x": 8_800_000,
            "y": 9_800_000,
            "z": 8_800_000,
        }[profile],
        "capital_control_q100000": {
            "x": 4_000_000,
            "y": 7_000_000,
            "z": 4_000_000,
        }[profile],
    }
    if incident:
        state = 8 if profile == "x" else 6
        terminal_values = {
            "owner_character_id": OWNER,
            "subject_character_id": PLAYER,
            "cycle_serial": cycle,
            "case_serial": {"x": 31, "y": 32, "z": 33}[profile],
            "state": state,
            "revision": 4,
            "incident_serial": 9,
            "source_kind": 5,
            "consequence_kind": 3,
            "final_score": 2,
            "applicable": 1,
            "kpi_staged": 1,
        }
        terminal = {
            "kind": "incident",
            "na": None,
            "incident": {
                key: available(value) for key, value in terminal_values.items()
            },
        }
        kpi = {
            "disposition": "pending",
            "pending": available(1),
            "consumed": available(0),
        }
    else:
        terminal_values = {
            "owner_character_id": OWNER,
            "subject_character_id": PLAYER,
            "cycle_serial": cycle,
            "reason": 1,
            "probe_serial": probe_serial,
            "receipt_serial": {"x": 31, "y": 32, "z": 33}[profile],
            "applicable": 0,
            "kpi_staged": 0,
        }
        terminal = {
            "kind": "na",
            "na": {key: available(value) for key, value in terminal_values.items()},
            "incident": None,
        }
        kpi = {"disposition": "not_staged"}
    return {
        "schema_version": 1,
        "status": "available",
        "case_kind": ZHONGGUO_INCIDENT_KIND_V1,
        "profile": profile,
        "subject_character_id": PLAYER,
        "requested_owner_character_id": owner,
        "probe": {key: available(probe_values[key]) for key in PROBE_KEYS},
        "resources": {key: available(resources[key]) for key in RESOURCE_KEYS},
        "terminal": terminal,
        "kpi": kpi,
        "readiness": {"ready": True},
        "unavailable_reason": None,
    }


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0
        self.on_sleep = None

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds
        if self.on_sleep is not None:
            self.on_sleep()


class FakeIncidentService:
    def __init__(
        self,
        *,
        initial_event: str | None = "zg361.50",
        terminal_kinds: dict[str, str] | None = None,
    ) -> None:
        self.event_key = initial_event
        self.event_instance_id = 100 if initial_event is not None else None
        self.paused = True
        self.speed = 1
        self.revision = 10
        self.native_revision = 100
        self.date_raw = DATE_RAW
        self.terminal_kinds = terminal_kinds or {
            "x": "incident",
            "y": "na",
            "z": "incident",
        }
        self.terminal_ready = False
        self.entry_selected = False
        self.result_selected = False
        self.selection_ack_stuck = False
        self.wrong_notice_owner = False
        self.acl_leak = False
        self.profile_receipt_binding_drift = False
        self.invalid_kpi = False
        self.unexpected_after_entry: str | None = None
        self.entry_event_after_ticks: int | None = None
        self.timeline_ticks = 0
        self.selections: list[tuple[str, int]] = []
        self.steps: list[str] = []
        self.remove_capability: str | None = None
        self.bad_native_option_index = False

    def capabilities(self) -> dict[str, object]:
        bridge = [
            QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY,
            QUERY_ZHONGGUO_INCIDENT_SNAPSHOT_V1_CAPABILITY,
            SELECT_EVENT_OPTION_CAPABILITY,
        ]
        steps = [
            "pause-map",
            "resume-map",
            "set-speed-1",
        ]
        if self.remove_capability in bridge:
            bridge.remove(self.remove_capability)
        if self.remove_capability in steps:
            steps.remove(self.remove_capability)
        return {"bridge_capabilities": bridge, "action_steps": steps}

    def snapshot(self) -> dict[str, object]:
        option_count = 3
        active_event = (
            {
                "instance_id": self.event_instance_id,
                "option_count": option_count,
                "options": [
                    {"option_number": index + 1, "enabled": True}
                    for index in range(option_count)
                ],
            }
            if self.event_key is not None
            else None
        )
        return {
            "snapshot_id": f"snapshot-{self.revision}",
            "revision": self.revision,
            "native_revision": self.native_revision,
            "date_raw": self.date_raw,
            "paused": self.paused,
            "speed": self.speed,
            "map_ready": True,
            "played_character": {"character_id": PLAYER, "alive": True},
            "active_event": active_event,
        }

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        if expected_revision != self.revision:
            raise AssertionError("revision binding changed")
        self.steps.append(step)
        if step == "pause-map":
            self.paused = True
        elif step == "resume-map":
            self.paused = False
        elif step == "set-speed-1":
            self.speed = 1
        else:
            raise AssertionError(f"unexpected step {step}")
        self.revision += 1
        self.native_revision += 1
        return {"accepted": True, "status": "submitted", "step": step}

    def query_current_event_window_context_v1(
        self, event_instance_id: int, *, expected_revision: int
    ) -> dict[str, object]:
        if (
            expected_revision != self.revision
            or event_instance_id != self.event_instance_id
            or self.event_key is None
            or not self.paused
        ):
            raise AssertionError("event context binding changed")
        options = []
        for index in range(3):
            options.append(
                {
                    "rendered_index": index,
                    "native_option_index": (
                        9 if self.bad_native_option_index and index == 0 else index
                    ),
                    "shown": True,
                    "enabled": True,
                    "resolved_name": f"option-{index + 1}",
                }
            )
        saved_scopes = []
        if self.event_key == "zg361.50":
            saved_scopes.append(
                {
                    "name": "zg361_notice_prompt_owner",
                    "name_identifier": 91,
                    "scope": typed_character_scope(
                        OWNER + 1 if self.wrong_notice_owner else OWNER
                    ),
                }
            )
        context = {
            "status": "available",
            "event_definition_key": self.event_key,
            "root_scope": typed_character_scope(PLAYER),
            "saved_scopes": saved_scopes,
            "options": options,
            "readiness": {
                "event_definition_identity_ready": True,
                "root_scope_ready": True,
                "saved_scopes_ready": True,
                "option_presentation_ready": True,
            },
        }
        return {
            "status": "available",
            "current_event_window_context": context,
        }

    def select_event_option(
        self,
        option_number: int,
        *,
        event_instance_id: int | None = None,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        if (
            self.event_key is None
            or event_instance_id != self.event_instance_id
            or expected_revision != self.revision
        ):
            raise AssertionError("selection binding changed")
        self.selections.append((self.event_key, option_number))
        if self.selection_ack_stuck:
            return {"accepted": True, "status": "submitted"}
        selected = self.event_key
        self.event_key = None
        self.event_instance_id = None
        self.paused = True
        self.revision += 1
        self.native_revision += 1
        if selected == "zg361.50":
            self.entry_selected = True
        elif selected == "zg361.4":
            self.result_selected = True
        return {"accepted": True, "status": "submitted"}

    def query_zhongguo_incident_snapshot_v1(
        self,
        request_nonce: str,
        *,
        expected_revision: int,
        owner_character_id: int,
        profile: str,
    ) -> dict[str, object]:
        if expected_revision != self.revision or not self.paused:
            raise AssertionError("provider query binding changed")
        if profile not in INCIDENT_PROFILES:
            raise AssertionError("profile allowlist changed")
        if owner_character_id != OWNER:
            if self.acl_leak:
                return terminal_incident(
                    profile, owner_character_id, kind=self.terminal_kinds[profile]
                )
            return acl_incident(profile, owner_character_id)
        if not self.terminal_ready:
            return unavailable_incident(profile, owner_character_id)
        response = terminal_incident(
            profile, owner_character_id, kind=self.terminal_kinds[profile]
        )
        if self.profile_receipt_binding_drift and profile == "z":
            response["probe"]["owner_character_id"] = available(OWNER + 1)
        if self.invalid_kpi and profile == "x":
            response["kpi"]["disposition"] = "consumed"
        return response

    def advance(self) -> None:
        if self.paused or self.event_key is not None:
            return
        self.timeline_ticks += 1
        self.date_raw += 1
        self.revision += 1
        self.native_revision += 1
        if not self.entry_selected:
            if (
                self.entry_event_after_ticks is not None
                and self.timeline_ticks >= self.entry_event_after_ticks
            ):
                self.event_key = "zg361.50"
                self.event_instance_id = 100
                self.paused = True
            return
        if not self.result_selected:
            self.event_key = self.unexpected_after_entry or "zg361.4"
            self.event_instance_id = 101
            self.paused = True
            return
        self.terminal_ready = True


def run_cell(service: FakeIncidentService, *, timeout: float = 3.0):
    clock = FakeClock()
    clock.on_sleep = service.advance
    return run_incident_xyz_gameplay_action_cell(
        service,
        owner_character_id=OWNER,
        timeout_seconds=timeout,
        poll_interval_seconds=0.1,
        monotonic=clock.monotonic,
        sleep=clock.sleep,
    )


class IncidentActionCellTests(unittest.TestCase):
    def test_incident_route_selects_fixed_options_and_proves_postcondition(self) -> None:
        service = FakeIncidentService()
        result = run_cell(service)
        self.assertEqual(result["result"], "GREEN")
        self.assertEqual(result["cell_id"], INCIDENT_ACTION_CELL_ID)
        self.assertEqual(
            service.selections, [("zg361.50", 1), ("zg361.4", 1)]
        )
        self.assertEqual(
            {row["kind"] for row in result["terminal_profiles"].values()},
            {"na", "incident"},
        )
        self.assertEqual(
            result["terminal_profiles"]["y"]["kpi_disposition"],
            "not_staged",
        )
        self.assertTrue(result["checks"]["ack_not_used_as_result"])
        self.assertTrue(
            result["checks"]["xyz_profile_probe_receipts_frozen"]
        )
        self.assertTrue(result["checks"]["xyz_mixed_na_incident_matrix"])
        self.assertTrue(result["checks"]["wrong_owner_acl_typed_red"])
        self.assertGreaterEqual(len(result["selection_materializations"]), 2)

    def test_single_kind_matrix_cannot_claim_mixed_terminal_coverage(self) -> None:
        service = FakeIncidentService(
            terminal_kinds={profile: "na" for profile in INCIDENT_PROFILES}
        )
        with self.assertRaises(IncidentActionCellError) as caught:
            run_cell(service)
        self.assertIn("must contain exact N/A and incident", caught.exception.reason)

    def test_event_free_seed_waits_for_exact_trigger(self) -> None:
        service = FakeIncidentService(initial_event=None)
        service.entry_event_after_ticks = 2
        result = run_cell(service)
        self.assertEqual(result["result"], "GREEN")
        self.assertEqual(service.selections[0], ("zg361.50", 1))

    def test_unexpected_entry_event_fails_before_selection(self) -> None:
        service = FakeIncidentService(initial_event="vanilla.999")
        with self.assertRaises(IncidentActionCellError) as caught:
            run_cell(service)
        self.assertIn("unexpected event definition", caught.exception.reason)
        self.assertEqual(service.selections, [])
        self.assertEqual(caught.exception.evidence["result"], "RED")

    def test_valid_route_event_identity_is_preserved_before_entry_order_red(self) -> None:
        service = FakeIncidentService(initial_event="zg361.4")
        with self.assertRaises(IncidentActionCellError) as caught:
            run_cell(service)
        self.assertIn("did not start", caught.exception.reason)
        self.assertEqual(service.selections, [])
        observations = caught.exception.evidence["event_observations"]
        self.assertEqual(observations[-1]["event_definition_key"], "zg361.4")

    def test_wrong_notice_owner_fails_before_selection(self) -> None:
        service = FakeIncidentService()
        service.wrong_notice_owner = True
        with self.assertRaises(IncidentActionCellError) as caught:
            run_cell(service)
        self.assertIn("notice owner does not match", caught.exception.reason)
        self.assertEqual(service.selections, [])

    def test_authored_option_identity_mismatch_fails_before_selection(self) -> None:
        service = FakeIncidentService()
        service.bad_native_option_index = True
        with self.assertRaises(IncidentActionCellError) as caught:
            run_cell(service)
        self.assertIn("not uniquely materialized", caught.exception.reason)
        self.assertEqual(service.selections, [])

    def test_selection_ack_without_event_transition_is_red(self) -> None:
        service = FakeIncidentService()
        service.selection_ack_stuck = True
        with self.assertRaises(IncidentActionCellError) as caught:
            run_cell(service, timeout=1.0)
        self.assertIn("ACK did not materialize", caught.exception.reason)
        self.assertEqual(service.selections, [("zg361.50", 1)])
        self.assertIsNone(caught.exception.evidence["terminal_profiles"])

    def test_unexpected_mid_route_event_is_not_auto_resolved(self) -> None:
        service = FakeIncidentService()
        service.unexpected_after_entry = "vanilla.123"
        with self.assertRaises(IncidentActionCellError) as caught:
            run_cell(service)
        self.assertIn("unexpected event definition", caught.exception.reason)
        self.assertEqual(service.selections, [("zg361.50", 1)])

    def test_invalid_kpi_postcondition_rejects_a_successful_action_ack(self) -> None:
        service = FakeIncidentService()
        service.invalid_kpi = True
        with self.assertRaises(IncidentActionCellError) as caught:
            run_cell(service)
        self.assertIn("fresh pending KPI", caught.exception.reason)
        self.assertEqual(
            service.selections, [("zg361.50", 1), ("zg361.4", 1)]
        )

    def test_profile_receipt_owner_binding_drift_is_red(self) -> None:
        service = FakeIncidentService()
        service.profile_receipt_binding_drift = True
        with self.assertRaises(IncidentActionCellError) as caught:
            run_cell(service)
        self.assertIn("changed owner/subject binding", caught.exception.reason)

    def test_wrong_owner_acl_must_be_typed_red(self) -> None:
        service = FakeIncidentService()
        service.acl_leak = True
        with self.assertRaises(IncidentActionCellError) as caught:
            run_cell(service)
        self.assertIn("wrong-owner ACL leaked state", caught.exception.reason)
        self.assertEqual(
            set(caught.exception.evidence["terminal_profiles"]),
            {"x", "y", "z"},
        )

    def test_missing_capability_is_red_before_gameplay_action(self) -> None:
        service = FakeIncidentService()
        service.remove_capability = QUERY_ZHONGGUO_INCIDENT_SNAPSHOT_V1_CAPABILITY
        with self.assertRaises(IncidentActionCellError) as caught:
            run_cell(service)
        self.assertIn("capability profile is incomplete", caught.exception.reason)
        self.assertEqual(service.selections, [])

    def test_timeout_without_trigger_never_claims_provider_observation_as_action(self) -> None:
        service = FakeIncidentService(initial_event=None)
        with self.assertRaises(IncidentActionCellError) as caught:
            run_cell(service, timeout=0.8)
        self.assertIn("timed out", caught.exception.reason)
        self.assertEqual(service.selections, [])
        self.assertIsNone(caught.exception.evidence["terminal_profiles"])


if __name__ == "__main__":
    unittest.main()
