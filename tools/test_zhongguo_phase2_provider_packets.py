#!/usr/bin/env python3

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest


TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from zhongguo_phase2_business_postconditions import (  # noqa: E402
    ENDGAME_HANDLER,
    PROJECTS_HANDLER,
    PROMOTION_HANDLER,
    SCOREBOARD_HANDLER,
)
from zhongguo_phase2_provider_packets import (  # noqa: E402
    PROJECTS_METRICS_QUERY_CAPABILITY,
    PROMOTION_COMPENSATION_QUERY_CAPABILITY,
    build_cross_cycle_endgame_provider_packet,
    build_projects_metrics_provider_packet,
    build_promotion_compensation_provider_packet,
    build_scoreboard_calibration_provider_packet,
)


CASES = json.loads(
    (TOOLS / "fixtures" / "phase2_business_postconditions_v1.json").read_text(
        encoding="utf-8"
    )
)["cases"]


def _typed(value: object) -> dict[str, object]:
    return {"status": "available", "value": value, "unavailable_reason": None}


def _event_query(
    key: str,
    identity: dict[str, object],
    *,
    snapshot_id: str,
    revision: int,
    native_revision: int,
) -> dict[str, object]:
    owner = identity["owner_character_id"]
    subject = identity["subject_character_id"]
    return {
        "status": "available",
        "binding": {
            "snapshot_id": snapshot_id,
            "revision": revision,
            "native_revision": native_revision,
        },
        "current_event_window_context": {
            "event_definition_key": key,
            "current_event_instance_id": native_revision + 1000,
            "snapshot_revision": native_revision,
            "root_scope": {
                "typed_identity": {"status": "available", "character_id": owner}
            },
            "saved_scopes": [
                {
                    "name": "subject",
                    "scope": {
                        "typed_identity": {
                            "status": "available",
                            "character_id": subject,
                        }
                    },
                }
            ],
            "readiness": {
                "event_definition_identity_ready": True,
                "root_scope_ready": True,
                "saved_scopes_ready": True,
            },
        },
    }


def _scoreboard_state(
    *,
    snapshot_id: str,
    revision: int,
    native_revision: int,
    observed: int,
    fingerprint: str,
    visible: bool,
) -> dict[str, object]:
    return {
        "status": "available",
        "binding": {
            "snapshot_id": snapshot_id,
            "revision": revision,
            "native_revision": native_revision,
            "player_character_id": 29037,
        },
        "source": {"connection_generation": 4},
        "observed_state_revision": observed,
        "semantic_fingerprint_v1": fingerprint,
        "widgets": [
            {
                "stable_identity": "zg361_scoreboard_modal",
                "effective_visible": _typed(visible),
            }
        ],
    }


def _scoreboard_action_cell() -> dict[str, object]:
    source = _scoreboard_state(
        snapshot_id="scoreboard-frame",
        revision=70,
        native_revision=700,
        observed=21,
        fingerprint="A" * 64,
        visible=False,
    )
    later = _scoreboard_state(
        snapshot_id="scoreboard-frame",
        revision=70,
        native_revision=700,
        observed=22,
        fingerprint="B" * 64,
        visible=True,
    )
    return {
        "result": "GREEN",
        "verified_pass": True,
        "production_capability_advertised": True,
        "verified_postcondition": {"postcondition_verified": True},
        "action_request": {"action": "open"},
        "source_query": source,
        "later_query": later,
    }


def _workforce(
    identity: dict[str, object],
    *,
    snapshot_id: str,
    revision: int,
    native_revision: int,
    result: bool,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "status": "available",
        "readiness": {"ready": True},
        "binding": {
            "snapshot_id": snapshot_id,
            "revision": revision,
            "native_revision": native_revision,
            "player_character_id": identity["owner_character_id"],
        },
        "source": {"connection_generation": 4},
        "al_case": {key: _typed(value) for key, value in identity.items()},
    }
    if result:
        payload["route_c_debt"] = {
            **{key: _typed(value) for key, value in identity.items()},
            "due_cycle_serial": _typed(int(identity["cycle_serial"]) + 1),
        }
        payload["charter_gate"] = {
            **{key: _typed(value) for key, value in identity.items()},
            "prepared_charter_id": _typed(36101),
            "adopted_cycle_serial": _typed(identity["cycle_serial"]),
            "effective_cycle_serial": _typed(int(identity["cycle_serial"]) + 1),
        }
    else:
        payload["route_c_debt"] = {}
        payload["charter_gate"] = {}
    return payload


def _future_query(handler: str) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    fixture = CASES[handler]
    source_event = fixture["source_event"]
    result_event = fixture["result_event"]
    observation = fixture["observation"]
    source_query = _event_query(
        source_event["definition_key"],
        source_event["identity"],
        snapshot_id=observation["source_snapshot_id"],
        revision=observation["source_revision"],
        native_revision=observation["source_native_revision"],
    )
    result_query = _event_query(
        result_event["definition_key"],
        result_event["identity"],
        snapshot_id=observation["result_snapshot_id"],
        revision=observation["result_revision"],
        native_revision=observation["result_native_revision"],
    )
    if handler == PROMOTION_HANDLER:
        capability = PROMOTION_COMPENSATION_QUERY_CAPABILITY
        payload_key = "promotion_compensation"
        payload = {
            key: deepcopy(fixture[key])
            for key in (
                "frozen_case",
                "promotion_choice",
                "compensation_receipt",
            )
        }
    else:
        capability = PROJECTS_METRICS_QUERY_CAPABILITY
        payload_key = "projects_metrics"
        payload = {
            key: deepcopy(fixture[key])
            for key in ("contribution", "metrics_result")
        }
    payload["source_identity"] = deepcopy(source_event["identity"])
    payload["result_identity"] = deepcopy(result_event["identity"])
    business = {
        "schema_version": 1,
        "status": "available",
        "capability": capability,
        "source_backend_id": "native-headless",
        "readiness": {"ready": True},
        "binding": {
            key: observation[key]
            for key in (
                "connection_generation",
                "player_character_id",
                "source_snapshot_id",
                "result_snapshot_id",
                "source_revision",
                "result_revision",
                "source_native_revision",
                "result_native_revision",
            )
        },
        payload_key: payload,
    }
    return source_query, result_query, business


class Phase2ProviderPacketTests(unittest.TestCase):
    def test_scoreboard_builds_from_verified_action_and_current_event(self) -> None:
        identity = {
            "owner_character_id": 29037,
            "subject_character_id": 29038,
            "cycle_serial": 14,
            "case_serial": 14007,
        }
        event = _event_query(
            "zg361.1",
            identity,
            snapshot_id="scoreboard-frame",
            revision=70,
            native_revision=700,
        )
        result = build_scoreboard_calibration_provider_packet(
            _scoreboard_action_cell(), event
        )
        self.assertEqual(result["result"], "GREEN")
        self.assertEqual(result["handler"], SCOREBOARD_HANDLER)
        self.assertEqual(result["postcondition"]["result"], "GREEN")

    def test_scoreboard_fails_closed_without_verified_action_or_event(self) -> None:
        action = _scoreboard_action_cell()
        action["verified_pass"] = False
        self.assertEqual(
            build_scoreboard_calibration_provider_packet(action, None)["reason_code"],
            "scoreboard_action_cell_not_verified",
        )
        self.assertEqual(
            build_scoreboard_calibration_provider_packet(
                _scoreboard_action_cell(), None
            )["reason_code"],
            "scoreboard_or_calibration_provider_binding_missing",
        )

    def test_promotion_and_projects_name_missing_native_queries(self) -> None:
        for handler, builder, capability in (
            (
                PROMOTION_HANDLER,
                build_promotion_compensation_provider_packet,
                PROMOTION_COMPENSATION_QUERY_CAPABILITY,
            ),
            (
                PROJECTS_HANDLER,
                build_projects_metrics_provider_packet,
                PROJECTS_METRICS_QUERY_CAPABILITY,
            ),
        ):
            source, result, _business = _future_query(handler)
            with self.subTest(handler=handler):
                built = builder(source, result)
                self.assertEqual(built["result"], "RED")
                self.assertEqual(
                    built["reason_code"], "required_business_provider_unavailable"
                )
                self.assertEqual(built["missing_provider_fields"], [capability])

    def test_future_native_query_shape_can_build_but_wrong_backend_cannot(self) -> None:
        for handler, builder in (
            (PROMOTION_HANDLER, build_promotion_compensation_provider_packet),
            (PROJECTS_HANDLER, build_projects_metrics_provider_packet),
        ):
            source, result, business = _future_query(handler)
            with self.subTest(handler=handler):
                built = builder(source, result, business)
                self.assertEqual(built["result"], "GREEN")
                wrong = deepcopy(business)
                wrong["source_backend_id"] = "fixture"
                blocked = builder(source, result, wrong)
                self.assertEqual(blocked["result"], "RED")
                self.assertEqual(
                    blocked["reason_code"], "required_business_provider_unavailable"
                )

    def test_future_query_rejects_cross_frame_business_binding(self) -> None:
        source, result, business = _future_query(PROMOTION_HANDLER)
        business["binding"]["result_native_revision"] += 1
        built = build_promotion_compensation_provider_packet(
            source, result, business
        )
        self.assertEqual(built["result"], "RED")
        self.assertEqual(built["reason_code"], "business_provider_event_binding_drift")

    def test_endgame_builds_from_existing_workforce_debt_and_charter(self) -> None:
        fixture = CASES[ENDGAME_HANDLER]
        identity = fixture["source_event"]["identity"]
        observation = fixture["observation"]
        source_event = _event_query(
            "zg361we.356",
            identity,
            snapshot_id=observation["source_snapshot_id"],
            revision=observation["source_revision"],
            native_revision=observation["source_native_revision"],
        )
        result_event = _event_query(
            "zg361we.361",
            identity,
            snapshot_id=observation["result_snapshot_id"],
            revision=observation["result_revision"],
            native_revision=observation["result_native_revision"],
        )
        source_workforce = _workforce(
            identity,
            snapshot_id=observation["source_snapshot_id"],
            revision=observation["source_revision"],
            native_revision=observation["source_native_revision"],
            result=False,
        )
        result_workforce = _workforce(
            identity,
            snapshot_id=observation["result_snapshot_id"],
            revision=observation["result_revision"],
            native_revision=observation["result_native_revision"],
            result=True,
        )
        built = build_cross_cycle_endgame_provider_packet(
            source_event, result_event, source_workforce, result_workforce
        )
        self.assertEqual(built["result"], "GREEN")
        self.assertEqual(built["postcondition"]["result"], "GREEN")

    def test_endgame_fails_closed_if_workforce_debt_is_unavailable(self) -> None:
        fixture = CASES[ENDGAME_HANDLER]
        identity = fixture["source_event"]["identity"]
        observation = fixture["observation"]
        source_event = _event_query(
            "zg361we.356",
            identity,
            snapshot_id=observation["source_snapshot_id"],
            revision=observation["source_revision"],
            native_revision=observation["source_native_revision"],
        )
        result_event = _event_query(
            "zg361we.361",
            identity,
            snapshot_id=observation["result_snapshot_id"],
            revision=observation["result_revision"],
            native_revision=observation["result_native_revision"],
        )
        before = _workforce(
            identity,
            snapshot_id=observation["source_snapshot_id"],
            revision=observation["source_revision"],
            native_revision=observation["source_native_revision"],
            result=False,
        )
        after = _workforce(
            identity,
            snapshot_id=observation["result_snapshot_id"],
            revision=observation["result_revision"],
            native_revision=observation["result_native_revision"],
            result=True,
        )
        after["route_c_debt"]["due_cycle_serial"] = {
            "status": "unavailable",
            "value": None,
            "unavailable_reason": "not_applicable",
        }
        built = build_cross_cycle_endgame_provider_packet(
            source_event, result_event, before, after
        )
        self.assertEqual(built["result"], "RED")
        self.assertEqual(built["reason_code"], "business_postcondition_not_green")


if __name__ == "__main__":
    unittest.main()
