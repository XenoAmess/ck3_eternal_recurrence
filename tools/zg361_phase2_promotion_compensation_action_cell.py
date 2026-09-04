#!/usr/bin/env python3
"""Independent Phase2 promotion/compensation gameplay action cell.

The cell starts on the exact ``zg361pp.147`` source event, submits the
canonical first option, and delegates only the passage to the result event to
an injected driver.  The driver and the command ACK are transport evidence;
GREEN is emitted only after the existing native-headless
``zhongguo_promotion_compensation_postcondition_v1`` provider observes the
promotion choice and the posted compensation receipt from one immutable case.

The formal Phase2 promo runner owns this cell only after restoring a qualified
real-CK3 ``zg361pp.147`` checkpoint.  Its default readiness remains
``live-pending`` until the provider is advertised by the exact-build adapter
and a paused CK3 artifact exercises the source/result path.
"""

from __future__ import annotations

import copy
from collections.abc import Callable, Mapping
from typing import Final, Protocol

from xar_autoplayer.bridge.event_window_context_contract import (
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY,
)
from xar_autoplayer.bridge.zhongguo_promotion_compensation_postcondition_contract import (
    QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_CAPABILITY,
    bind_promotion_compensation_event_snapshots_v1,
)
from zhongguo_phase2_business_postconditions import (
    PROMOTION_HANDLER,
    verify_phase2_business_postcondition,
)


ACTION_CELL_ID: Final = "zg361.phase2.promotion-compensation.action.v1"
SOURCE_EVENT_DEFINITION_KEY: Final = "zg361pp.147"
RESULT_EVENT_DEFINITION_KEY: Final = "zg361comp.1"
SOURCE_OPTION_NUMBER: Final = 1
SELECT_EVENT_OPTION_CAPABILITY: Final = "game.command.select-event-option-N"
IMPLEMENTATION_READINESS: Final = "live-pending"

_SOURCE_OWNER_SCOPE: Final = "zg361_pp_prompt_owner"
_SOURCE_SUBJECT_SCOPE: Final = "zg361_pp_prompt_subject"
_SOURCE_SCALAR_SCOPES: Final = frozenset(
    {
        "zg361_pp_prompt_cycle",
        "zg361_pp_prompt_case",
        "zg361_pp_prompt_state",
        "zg361_pp_prompt_mechanism",
    }
)


class PromotionCompensationActionService(Protocol):
    """Narrow facade already implemented by ``GameplayBridgeService``."""

    def capabilities(self) -> dict[str, object]: ...

    def snapshot(self) -> dict[str, object]: ...

    def query_current_event_window_context_v1(
        self, event_instance_id: int, *, expected_revision: int
    ) -> dict[str, object]: ...

    def select_event_option(
        self,
        option_number: int,
        *,
        event_instance_id: int,
        expected_revision: int,
    ) -> dict[str, object]: ...

    def query_zhongguo_promotion_compensation_postcondition_v1(
        self, request_nonce: str, *, expected_revision: int
    ) -> dict[str, object]: ...


AdvanceToResult = Callable[
    [PromotionCompensationActionService, Mapping[str, object], Mapping[str, object]],
    Mapping[str, object],
]


class PromotionCompensationActionCellError(RuntimeError):
    """Fail-closed result carrying the incomplete evidence sidecar."""

    def __init__(self, reason_code: str, evidence: Mapping[str, object]) -> None:
        self.reason_code = reason_code
        self.evidence = {
            **copy.deepcopy(dict(evidence)),
            "result": "RED",
            "reason_code": reason_code,
        }
        super().__init__(
            f"promotion/compensation action cell RED [{reason_code}]"
        )


def _integer(
    value: object, label: str, *, minimum: int, maximum: int
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not minimum <= value <= maximum
    ):
        raise ValueError(f"{label} is not an integer in range")
    return value


def _positive(value: object, label: str) -> int:
    return _integer(value, label, minimum=1, maximum=2**63 - 1)


def _snapshot_binding(snapshot: object, *, expected_event: bool) -> dict[str, object]:
    if not isinstance(snapshot, dict):
        raise ValueError("snapshot is not an object")
    if snapshot.get("paused") is not True or snapshot.get("map_ready") is not True:
        raise ValueError("action cell requires a paused, map-ready snapshot")
    played = snapshot.get("played_character")
    player = _integer(
        played.get("character_id") if isinstance(played, Mapping) else None,
        "snapshot.played_character.character_id",
        minimum=1,
        maximum=2**31 - 1,
    )
    diagnostics = snapshot.get("diagnostics")
    generation = _positive(
        diagnostics.get("connection_generation")
        if isinstance(diagnostics, Mapping)
        else None,
        "snapshot.connection_generation",
    )
    active_event = snapshot.get("active_event")
    event_instance_id: int | None = None
    event_option_count: int | None = None
    if isinstance(active_event, Mapping):
        event_instance_id = _integer(
            active_event.get("instance_id"),
            "snapshot.active_event.instance_id",
            minimum=1,
            maximum=2**31 - 1,
        )
        event_option_count = _integer(
            active_event.get("option_count"),
            "snapshot.active_event.option_count",
            minimum=0,
            maximum=64,
        )
    elif expected_event:
        raise ValueError("action cell requires one active event")
    snapshot_id = snapshot.get("snapshot_id")
    if not isinstance(snapshot_id, str) or not snapshot_id:
        raise ValueError("snapshot.snapshot_id is absent")
    return {
        "snapshot_id": snapshot_id,
        "revision": _integer(
            snapshot.get("revision"),
            "snapshot.revision",
            minimum=0,
            maximum=2**64 - 1,
        ),
        "native_revision": _positive(
            snapshot.get("native_revision"), "snapshot.native_revision"
        ),
        "date_raw": _integer(
            snapshot.get("date_raw"),
            "snapshot.date_raw",
            minimum=-(2**31),
            maximum=2**31 - 1,
        ),
        "paused": True,
        "map_ready": True,
        "player_character_id": player,
        "connection_generation": generation,
        "event_instance_id": event_instance_id,
        "event_option_count": event_option_count,
    }


def _character_scope_id(scope: object, label: str) -> int:
    if not isinstance(scope, Mapping):
        raise ValueError(f"{label} is not an event scope")
    identity = scope.get("typed_identity")
    if not (
        isinstance(identity, Mapping)
        and identity.get("status") == "available"
        and identity.get("kind") == "character"
    ):
        raise ValueError(f"{label} is not an available character scope")
    return _integer(
        identity.get("character_id"),
        f"{label}.character_id",
        minimum=1,
        maximum=2**31 - 1,
    )


def _event_context(
    response: object,
    *,
    binding: Mapping[str, object],
    expected_definition_key: str,
    require_source_scopes: bool,
) -> tuple[dict[str, object], int | None]:
    if not isinstance(response, dict) or response.get("status") != "available":
        raise ValueError("current-event-window provider is unavailable")
    response_binding = response.get("binding")
    if not isinstance(response_binding, Mapping):
        raise ValueError("current-event-window response lacks its binding")
    expected_binding = {
        "snapshot_id": binding["snapshot_id"],
        "revision": binding["revision"],
        "native_revision": binding["native_revision"],
        "date_raw": binding["date_raw"],
        "event_instance_id": binding["event_instance_id"],
    }
    if any(response_binding.get(key) != value for key, value in expected_binding.items()):
        raise ValueError("current-event-window response crossed its paused frame")
    context = response.get("current_event_window_context")
    if not isinstance(context, dict):
        raise ValueError("current-event-window response lacks its typed context")
    readiness = context.get("readiness")
    if not (
        context.get("status") == "available"
        and context.get("event_definition_key") == expected_definition_key
        and context.get("current_event_instance_id") == binding["event_instance_id"]
        and context.get("snapshot_revision") == binding["native_revision"]
        and context.get("date_raw") == binding["date_raw"]
        and isinstance(readiness, Mapping)
        and readiness.get("event_definition_identity_ready") is True
        and readiness.get("root_scope_ready") is True
        and readiness.get("saved_scopes_ready") is True
        and readiness.get("option_presentation_ready") is True
    ):
        raise ValueError("current event semantic identity is not ready")
    root = _character_scope_id(context.get("root_scope"), "event.root_scope")
    if root != binding["player_character_id"]:
        raise ValueError("current event root is not the played owner")

    subject: int | None = None
    if require_source_scopes:
        raw_scopes = context.get("saved_scopes")
        if not isinstance(raw_scopes, list):
            raise ValueError("source event saved scopes are unavailable")
        scopes: dict[str, object] = {}
        for row in raw_scopes:
            if not isinstance(row, Mapping) or not isinstance(row.get("name"), str):
                raise ValueError("source event contains a malformed saved scope")
            name = str(row["name"])
            if name in scopes:
                raise ValueError("source event contains duplicate saved scopes")
            scopes[name] = row.get("scope")
        required = {
            _SOURCE_OWNER_SCOPE,
            _SOURCE_SUBJECT_SCOPE,
            *_SOURCE_SCALAR_SCOPES,
        }
        missing = required - set(scopes)
        if missing:
            raise ValueError(
                "source event lacks frozen scopes: " + ", ".join(sorted(missing))
            )
        owner = _character_scope_id(scopes[_SOURCE_OWNER_SCOPE], "source.owner")
        subject = _character_scope_id(
            scopes[_SOURCE_SUBJECT_SCOPE], "source.subject"
        )
        if owner != binding["player_character_id"]:
            raise ValueError("source owner scope is not the played owner")
        options = context.get("options")
        if not isinstance(options, list) or len(options) != 3:
            raise ValueError("zg361pp.147 must expose exactly three options")
        selected = options[SOURCE_OPTION_NUMBER - 1]
        if not (
            isinstance(selected, Mapping)
            and selected.get("rendered_index") == SOURCE_OPTION_NUMBER - 1
            and selected.get("native_option_index") == SOURCE_OPTION_NUMBER - 1
            and selected.get("shown") is True
            and selected.get("enabled") is True
        ):
            raise ValueError("canonical promotion option is not selectable")
        if binding["event_option_count"] != len(options):
            raise ValueError("snapshot/event-context option counts disagree")
    return copy.deepcopy(response), subject


def _typed(group: object, key: str, kind: type, label: str) -> object:
    if not isinstance(group, Mapping):
        raise ValueError(f"{label} group is absent")
    field = group.get(key)
    if not (
        isinstance(field, Mapping)
        and set(field) == {"status", "value", "unavailable_reason"}
        and field.get("status") == "available"
        and field.get("unavailable_reason") is None
    ):
        raise ValueError(f"{label}.{key} is unavailable")
    value = field.get("value")
    if kind is bool:
        if not isinstance(value, bool):
            raise ValueError(f"{label}.{key} is not boolean")
    elif isinstance(value, bool) or not isinstance(value, kind):
        raise ValueError(f"{label}.{key} has the wrong type")
    return value


def _identity(group: object, label: str) -> tuple[dict[str, int], int]:
    identity = {
        key: _positive(_typed(group, key, int, label), f"{label}.{key}")
        for key in (
            "owner_character_id",
            "subject_character_id",
            "cycle_serial",
            "case_serial",
        )
    }
    revision = _positive(_typed(group, "revision", int, label), f"{label}.revision")
    return identity, revision


def _event_with_generation(
    event_query: Mapping[str, object], generation: int
) -> dict[str, object]:
    result = copy.deepcopy(dict(event_query))
    binding = result.get("binding")
    if not isinstance(binding, dict):
        raise ValueError("event query lacks mutable binding projection")
    binding["connection_generation"] = generation
    return result


def _provider_proof(
    provider: object,
    *,
    request: Mapping[str, object],
    source_event: Mapping[str, object],
    result_event: Mapping[str, object],
) -> tuple[dict[str, object], dict[str, object], dict[str, bool]]:
    if not isinstance(provider, dict):
        raise ValueError("promotion/compensation provider returned a non-object")
    readiness = provider.get("readiness")
    if not (
        provider.get("schema_version") == 1
        and provider.get("status") == "available"
        and provider.get("unavailable_reason") is None
        and provider.get("capability")
        == QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_CAPABILITY
        and provider.get("source_backend_id") == "native-headless"
        and provider.get("request_nonce") == request["request_nonce"]
        and isinstance(readiness, Mapping)
        and readiness.get("ready") is True
    ):
        raise ValueError("promotion/compensation provider is not ready")
    bound = bind_promotion_compensation_event_snapshots_v1(
        provider, source_event, result_event
    )
    binding = bound.get("binding")
    payload = bound.get("promotion_compensation")
    if not isinstance(binding, Mapping) or not isinstance(payload, Mapping):
        raise ValueError("provider business projection is incomplete")

    source_identity, source_identity_revision = _identity(
        payload.get("source_identity"), "source_identity"
    )
    result_identity, result_identity_revision = _identity(
        payload.get("result_identity"), "result_identity"
    )
    frozen = payload.get("frozen_case")
    choice = payload.get("promotion_choice")
    compensation = payload.get("compensation_receipt")
    if not isinstance(frozen, Mapping) or frozen.get("frozen") is not True:
        raise ValueError("provider did not publish one frozen case")
    frozen_identity, frozen_revision = _identity(
        frozen.get("identity"), "frozen_case.identity"
    )
    if not isinstance(choice, Mapping) or not isinstance(compensation, Mapping):
        raise ValueError("provider choice/compensation groups are absent")
    choice_identity, choice_revision = _identity(
        choice.get("identity"), "promotion_choice.identity"
    )
    compensation_identity, compensation_revision = _identity(
        compensation.get("identity"), "compensation_receipt.identity"
    )
    identities = (
        source_identity,
        result_identity,
        frozen_identity,
        choice_identity,
        compensation_identity,
    )
    promotion_option = _positive(
        _typed(choice, "option_number", int, "promotion_choice"),
        "promotion_choice.option_number",
    )
    promotion_receipt = _positive(
        _typed(choice, "receipt_serial", int, "promotion_choice"),
        "promotion_choice.receipt_serial",
    )
    compensation_receipt = _positive(
        _typed(compensation, "receipt_serial", int, "compensation_receipt"),
        "compensation_receipt.receipt_serial",
    )
    compensation_operation = _positive(
        _typed(compensation, "operation_id", int, "compensation_receipt"),
        "compensation_receipt.operation_id",
    )
    checks = {
        "provider_observed": True,
        "action_ack_not_business_postcondition": True,
        "event_frames_bound": all(
            binding.get(key) == request[key]
            for key in (
                "connection_generation",
                "source_snapshot_id",
                "source_revision",
                "source_native_revision",
                "result_snapshot_id",
                "result_revision",
                "result_native_revision",
            )
        )
        and binding.get("player_character_id") == request["owner_character_id"],
        "provider_owner_subject_match_request": binding.get("owner_character_id")
        == request["owner_character_id"]
        and binding.get("player_character_id") == request["owner_character_id"]
        and binding.get("subject_character_id") == request["subject_character_id"],
        "same_immutable_case": all(identity == identities[0] for identity in identities),
        "case_matches_action_request": source_identity["owner_character_id"]
        == request["owner_character_id"]
        and source_identity["subject_character_id"]
        == request["subject_character_id"],
        "promotion_choice_matches_action_request": promotion_option
        == request["option_number"],
        "promotion_choice_consumed": _typed(
            choice, "active", bool, "promotion_choice"
        )
        is True
        and _typed(choice, "consumed", bool, "promotion_choice") is True,
        "compensation_receipt_posted": _typed(
            compensation, "active", bool, "compensation_receipt"
        )
        is True
        and _typed(compensation, "consumed", bool, "compensation_receipt")
        is True
        and _typed(compensation, "posted", bool, "compensation_receipt") is True,
        "receipt_serial_joined": promotion_receipt == compensation_receipt
        and promotion_receipt == source_identity["case_serial"],
        "revision_lineage_ready": choice_revision == source_identity_revision
        and result_identity_revision > source_identity_revision
        and frozen_revision == result_identity_revision
        and compensation_revision == result_identity_revision,
    }

    packet = {
        "schema_version": 1,
        "handler": PROMOTION_HANDLER,
        "observation": {
            "provider_observed": True,
            "action_ack_only": False,
            **{
                key: binding[key]
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
        },
        "source_event": {
            "definition_key": SOURCE_EVENT_DEFINITION_KEY,
            "visible": True,
            "identity_ready": True,
            "snapshot_revision": binding["source_native_revision"],
            "identity": source_identity,
        },
        "result_event": {
            "definition_key": RESULT_EVENT_DEFINITION_KEY,
            "visible": True,
            "identity_ready": True,
            "snapshot_revision": binding["result_native_revision"],
            "identity": result_identity,
        },
        "frozen_case": {"identity": frozen_identity, "frozen": True},
        "promotion_choice": {
            "identity": choice_identity,
            "option_number": promotion_option,
            "receipt_serial": promotion_receipt,
            "provider_observed": True,
        },
        "compensation_receipt": {
            "identity": compensation_identity,
            "receipt_serial": compensation_receipt,
            "posted": True,
            "provider_observed": True,
        },
    }
    business_proof = verify_phase2_business_postcondition(
        PROMOTION_HANDLER, packet
    )
    checks["shared_business_postcondition_green"] = (
        business_proof.get("result") == "GREEN"
        and business_proof.get("provider_observed") is True
        and business_proof.get("postcondition_green") is True
    )
    checks["compensation_operation_observed"] = compensation_operation > 0
    failed = [key for key, passed in checks.items() if passed is not True]
    if failed:
        raise ValueError("provider/action lineage failed: " + ", ".join(failed))
    return bound, business_proof, checks


def run_promotion_compensation_gameplay_action_cell(
    service: PromotionCompensationActionService,
    *,
    advance_to_result: AdvanceToResult,
    request_nonce: str = "zg361.phase2.promo.comp.v1",
) -> dict[str, object]:
    """Select the canonical promotion route and prove its compensation result."""

    if not isinstance(request_nonce, str) or not request_nonce:
        raise ValueError("request_nonce must be non-empty")
    evidence: dict[str, object] = {
        "schema_version": 1,
        "cell_id": ACTION_CELL_ID,
        "span": "promotion-compensation",
        "result": "RED",
        "reason_code": None,
        "implementation_readiness": IMPLEMENTATION_READINESS,
        "production_live": False,
        "fixture_evidence_is_live": False,
        "mcp_only": True,
        "ocr_used": False,
        "coordinates_used": False,
        "action_ack_is_business_postcondition": False,
        "action_request": None,
        "selection_ack": None,
        "transition_driver": None,
        "source_event_query": None,
        "result_event_query": None,
        "provider_postcondition": None,
        "business_postcondition": None,
        "checks": {},
    }

    def fail(reason: str) -> None:
        raise PromotionCompensationActionCellError(reason, evidence)

    try:
        capabilities = service.capabilities()
        bridge = (
            capabilities.get("bridge_capabilities")
            if isinstance(capabilities, Mapping)
            else None
        )
        if not (
            isinstance(bridge, list)
            and {
                QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY,
                QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_CAPABILITY,
                SELECT_EVENT_OPTION_CAPABILITY,
            }.issubset(set(bridge))
        ):
            fail("mcp_capability_profile_incomplete")

        source_binding = _snapshot_binding(service.snapshot(), expected_event=True)
        source_instance = int(source_binding["event_instance_id"])
        source_query, subject = _event_context(
            service.query_current_event_window_context_v1(
                source_instance,
                expected_revision=int(source_binding["revision"]),
            ),
            binding=source_binding,
            expected_definition_key=SOURCE_EVENT_DEFINITION_KEY,
            require_source_scopes=True,
        )
        if subject is None:
            fail("source_subject_identity_unavailable")
        evidence["source_event_query"] = source_query
        action_request = {
            "request_nonce": request_nonce,
            "source_event_definition_key": SOURCE_EVENT_DEFINITION_KEY,
            "result_event_definition_key": RESULT_EVENT_DEFINITION_KEY,
            "source_event_instance_id": source_instance,
            "option_number": SOURCE_OPTION_NUMBER,
            "owner_character_id": source_binding["player_character_id"],
            "subject_character_id": subject,
            "connection_generation": source_binding["connection_generation"],
            "source_snapshot_id": source_binding["snapshot_id"],
            "source_revision": source_binding["revision"],
            "source_native_revision": source_binding["native_revision"],
            "result_snapshot_id": None,
            "result_revision": None,
            "result_native_revision": None,
        }
        evidence["action_request"] = action_request

        # Freeze once more immediately before the mutation so the request is
        # tied to the exact event instance and source revision.
        if _snapshot_binding(service.snapshot(), expected_event=True) != source_binding:
            fail("source_checkpoint_changed_before_submission")
        ack = service.select_event_option(
            SOURCE_OPTION_NUMBER,
            event_instance_id=source_instance,
            expected_revision=int(source_binding["revision"]),
        )
        evidence["selection_ack"] = copy.deepcopy(ack)
        if not (
            isinstance(ack, Mapping)
            and ack.get("accepted") is True
            and ack.get("status") == "submitted"
            and ack.get("event_instance_id") == source_instance
            and ack.get("option_number") == SOURCE_OPTION_NUMBER
        ):
            fail("bound_selection_ack_rejected")

        transition = advance_to_result(service, action_request, ack)
        evidence["transition_driver"] = copy.deepcopy(transition)
        if not (
            isinstance(transition, Mapping)
            and transition.get("result") == "GREEN"
            and transition.get("result_event_definition_key")
            == RESULT_EVENT_DEFINITION_KEY
            and transition.get("action_ack_is_business_postcondition") is False
        ):
            fail("transition_driver_did_not_reach_result_event")

        result_binding = _snapshot_binding(service.snapshot(), expected_event=True)
        if not (
            result_binding["connection_generation"]
            == source_binding["connection_generation"]
            and result_binding["player_character_id"]
            == source_binding["player_character_id"]
            and result_binding["snapshot_id"] != source_binding["snapshot_id"]
            and result_binding["revision"] > source_binding["revision"]
            and result_binding["native_revision"]
            > source_binding["native_revision"]
        ):
            fail("source_result_snapshot_lineage_drifted")
        result_instance = int(result_binding["event_instance_id"])
        result_query, _ = _event_context(
            service.query_current_event_window_context_v1(
                result_instance,
                expected_revision=int(result_binding["revision"]),
            ),
            binding=result_binding,
            expected_definition_key=RESULT_EVENT_DEFINITION_KEY,
            require_source_scopes=False,
        )
        evidence["result_event_query"] = result_query
        action_request.update(
            {
                "result_snapshot_id": result_binding["snapshot_id"],
                "result_revision": result_binding["revision"],
                "result_native_revision": result_binding["native_revision"],
            }
        )

        provider = service.query_zhongguo_promotion_compensation_postcondition_v1(
            request_nonce,
            expected_revision=int(result_binding["revision"]),
        )
        source_bound = _event_with_generation(
            source_query, int(source_binding["connection_generation"])
        )
        result_bound = _event_with_generation(
            result_query, int(result_binding["connection_generation"])
        )
        provider_bound, business_proof, checks = _provider_proof(
            provider,
            request=action_request,
            source_event=source_bound,
            result_event=result_bound,
        )
        evidence["provider_postcondition"] = provider_bound
        evidence["business_postcondition"] = business_proof
        evidence["checks"] = checks
        evidence["result"] = "GREEN"
        evidence["reason_code"] = None
        return evidence
    except PromotionCompensationActionCellError:
        raise
    except Exception as error:
        fail(f"{type(error).__name__}: {error}")
    raise AssertionError("unreachable")


__all__ = [
    "ACTION_CELL_ID",
    "IMPLEMENTATION_READINESS",
    "RESULT_EVENT_DEFINITION_KEY",
    "SOURCE_EVENT_DEFINITION_KEY",
    "SOURCE_OPTION_NUMBER",
    "PromotionCompensationActionCellError",
    "PromotionCompensationActionService",
    "run_promotion_compensation_gameplay_action_cell",
]
