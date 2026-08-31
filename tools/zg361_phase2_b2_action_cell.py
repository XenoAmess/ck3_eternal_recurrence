#!/usr/bin/env python3
"""MCP-first gameplay action cell for the ZhongGuo B2 PIP prompt.

The cell deliberately composes existing production primitives:

* the paused current-event-window context query;
* the bound ``select-event-option-N`` action; and
* the paused received-self B2 PIP snapshot query.

An accepted option-command ACK is never treated as a gameplay postcondition.
GREEN requires the same real owner/subject/cycle/case tuple to publish the
action-specific response and state transition through the B2 provider.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
import time
import unicodedata
from typing import Callable, Mapping, Protocol


B2_PIP_EVENT_DEFINITION_KEY = "zg361b2.40"
B2_PIP_CASE_KIND = "zhongguo.b2.pip"

_NONCE_PREFIX_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,47}\Z")
_CHARACTER_SCOPE_NAMES = {
    "owner": "zg361_b2_pip_prompt_owner",
    "subject": "zg361_b2_pip_prompt_subject",
}
_SCALAR_SCOPE_NAMES = frozenset(
    {
        "zg361_b2_pip_prompt_cycle",
        "zg361_b2_pip_prompt_case",
        "zg361_b2_pip_prompt_state",
    }
)


class B2PipActionService(Protocol):
    """Narrow interface already implemented by ``GameplayBridgeService``."""

    def snapshot(self) -> dict[str, object]: ...

    def query_current_event_window_context_v1(
        self, event_instance_id: int, *, expected_revision: int
    ) -> dict[str, object]: ...

    def query_zhongguo_b2_pip_snapshot_v1(
        self,
        request_nonce: str,
        *,
        expected_revision: int,
        owner_character_id: int,
    ) -> dict[str, object]: ...

    def select_event_option(
        self,
        option_number: int,
        *,
        event_instance_id: int,
        expected_revision: int,
    ) -> dict[str, object]: ...


@dataclass(frozen=True)
class B2PipIdentity:
    owner_character_id: int
    subject_character_id: int
    cycle_serial: int
    case_serial: int
    state: int

    @property
    def immutable_case(self) -> tuple[int, int, int, int]:
        return (
            self.owner_character_id,
            self.subject_character_id,
            self.cycle_serial,
            self.case_serial,
        )


@dataclass(frozen=True)
class _ActionSpec:
    option_number: int
    response_code: int
    resulting_state: int
    goal_revision_used: bool
    refusal_receipt: bool
    resolved_names: tuple[str, ...]


_ACTION_SPECS: Mapping[str, _ActionSpec] = {
    "accept": _ActionSpec(
        option_number=1,
        response_code=1,
        resulting_state=2,
        goal_revision_used=False,
        refusal_receipt=False,
        resolved_names=(
            "Accept the plan and its support.",
            "接受计划及配套支持。",
        ),
    ),
    "negotiate": _ActionSpec(
        option_number=2,
        response_code=2,
        resulting_state=2,
        goal_revision_used=True,
        refusal_receipt=False,
        resolved_names=(
            "Revise the goal once, then begin.",
            "修改一次目标，然后开始执行。",
        ),
    ),
    "refuse": _ActionSpec(
        option_number=3,
        response_code=3,
        resulting_state=5,
        goal_revision_used=False,
        refusal_receipt=True,
        resolved_names=(
            "Refuse, and let only the next cycle judge it.",
            "拒绝，并只让下一轮评价此事。",
        ),
    ),
}


class B2PipActionCellError(RuntimeError):
    """Fail-closed result carrying the incomplete evidence sidecar."""

    def __init__(self, message: str, evidence: dict[str, object]) -> None:
        super().__init__(message)
        self.evidence = evidence


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


def _positive_int32(value: object, label: str) -> int:
    return _integer(value, label, minimum=1, maximum=2**31 - 1)


def _typed_value(
    group: object, field_name: str, label: str
) -> object:
    if not isinstance(group, dict):
        raise ValueError(f"{label} group is absent")
    field = group.get(field_name)
    if not isinstance(field, dict) or set(field) != {
        "status",
        "value",
        "unavailable_reason",
    }:
        raise ValueError(f"{label}.{field_name} is not a typed field")
    if field.get("status") != "available" or field.get(
        "unavailable_reason"
    ) is not None:
        raise ValueError(f"{label}.{field_name} is unavailable")
    return field.get("value")


def _typed_unavailable(
    group: object, field_name: str, label: str, *, reason: str
) -> bool:
    if not isinstance(group, dict):
        return False
    field = group.get(field_name)
    return (
        isinstance(field, dict)
        and set(field) == {"status", "value", "unavailable_reason"}
        and field.get("status") == "unavailable"
        and field.get("value") is None
        and field.get("unavailable_reason") == reason
    )


def _normalize_semantic_text(value: object) -> str:
    if not isinstance(value, str):
        return ""
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return "".join(character for character in normalized if character.isalnum())


def _character_scope_id(scope: object, label: str) -> int:
    if not isinstance(scope, dict):
        raise ValueError(f"{label} is not an event scope")
    identity = scope.get("typed_identity")
    if not isinstance(identity, dict):
        raise ValueError(f"{label} lacks typed identity")
    if identity.get("status") != "available" or identity.get("kind") != "character":
        raise ValueError(f"{label} is not a typed character scope")
    return _positive_int32(identity.get("character_id"), f"{label}.character_id")


def _snapshot_binding(
    snapshot: object, *, require_event: bool
) -> dict[str, object]:
    if not isinstance(snapshot, dict):
        raise ValueError("gameplay snapshot is not an object")
    if snapshot.get("paused") is not True:
        raise ValueError("B2 action cell requires a paused snapshot")
    revision = _integer(
        snapshot.get("revision"),
        "snapshot.revision",
        minimum=0,
        maximum=2**64 - 1,
    )
    native_revision = _integer(
        snapshot.get("native_revision"),
        "snapshot.native_revision",
        minimum=1,
        maximum=2**64 - 1,
    )
    date_raw = _integer(
        snapshot.get("date_raw"),
        "snapshot.date_raw",
        minimum=-(2**31),
        maximum=2**31 - 1,
    )
    snapshot_id = snapshot.get("snapshot_id")
    if not isinstance(snapshot_id, str) or not snapshot_id:
        raise ValueError("snapshot.snapshot_id is absent")
    played_character = snapshot.get("played_character")
    player_character_id = _positive_int32(
        played_character.get("character_id")
        if isinstance(played_character, dict)
        else None,
        "snapshot.played_character.character_id",
    )
    diagnostics = snapshot.get("diagnostics")
    connection_generation = _integer(
        diagnostics.get("connection_generation")
        if isinstance(diagnostics, dict)
        else None,
        "snapshot.diagnostics.connection_generation",
        minimum=1,
        maximum=2**64 - 1,
    )
    active_event = snapshot.get("active_event")
    event_instance_id: int | None = None
    event_option_count: int | None = None
    if isinstance(active_event, dict):
        event_instance_id = _positive_int32(
            active_event.get("instance_id"), "active_event.instance_id"
        )
        event_option_count = _integer(
            active_event.get("option_count"),
            "active_event.option_count",
            minimum=0,
            maximum=64,
        )
    elif require_event:
        raise ValueError("B2 action cell lacks an active event")
    return {
        "snapshot_id": snapshot_id,
        "revision": revision,
        "native_revision": native_revision,
        "date_raw": date_raw,
        "paused": True,
        "player_character_id": player_character_id,
        "connection_generation": connection_generation,
        "event_instance_id": event_instance_id,
        "event_option_count": event_option_count,
    }


def _require_query_binding(
    response: dict[str, object], binding: dict[str, object], *, owner: int
) -> None:
    query_binding = response.get("binding")
    if not isinstance(query_binding, dict):
        raise ValueError("B2 provider response lacks its paused binding")
    expected = {
        "snapshot_id": binding["snapshot_id"],
        "revision": binding["revision"],
        "native_revision": binding["native_revision"],
        "connection_generation": binding["connection_generation"],
        "date_raw": binding["date_raw"],
        "paused": True,
        "player_character_id": binding["player_character_id"],
        "subject_character_id": binding["player_character_id"],
        "owner_character_id": owner,
        "expected_revision": binding["revision"],
    }
    for key, value in expected.items():
        if query_binding.get(key) != value:
            raise ValueError(f"B2 provider binding changed at {key}")


def _extract_b2_identity(
    response: object,
    *,
    binding: dict[str, object],
    owner_character_id: int,
) -> B2PipIdentity:
    if not isinstance(response, dict):
        raise ValueError("B2 provider response is not an object")
    if (
        response.get("status") != "available"
        or response.get("case_kind") != B2_PIP_CASE_KIND
        or response.get("unavailable_reason") is not None
    ):
        raise ValueError("B2 provider did not publish an available PIP case")
    if response.get("paused") is not True:
        raise ValueError("B2 provider response is not paused")
    if response.get("date_raw") != binding["date_raw"]:
        raise ValueError("B2 provider response crossed the paused date")
    if response.get("player_character_id") != binding["player_character_id"]:
        raise ValueError("B2 provider response changed the played character")
    if response.get("subject_character_id") != binding["player_character_id"]:
        raise ValueError("B2 provider response is not received-self")
    if response.get("requested_owner_character_id") != owner_character_id:
        raise ValueError("B2 provider response changed the owner filter")
    _require_query_binding(response, binding, owner=owner_character_id)

    readiness = response.get("readiness")
    if not (
        isinstance(readiness, dict)
        and readiness.get("player_subject_binding_ready") is True
        and readiness.get("owner_binding_ready") is True
        and readiness.get("gate_ready") is True
        and readiness.get("pip_identity_ready") is True
        and readiness.get("response_ready") is True
        and readiness.get("same_frame_ready") is True
        and readiness.get("ready") is True
    ):
        raise ValueError("B2 provider identity/response readiness is RED")

    gate = response.get("gate")
    pip = response.get("pip")
    gate_identity = (
        _positive_int32(
            _typed_value(gate, "owner_character_id", "gate"), "gate.owner"
        ),
        _positive_int32(
            _typed_value(gate, "subject_character_id", "gate"),
            "gate.subject",
        ),
        _integer(
            _typed_value(gate, "cycle_serial", "gate"),
            "gate.cycle",
            minimum=1,
            maximum=2**63 - 1,
        ),
        _integer(
            _typed_value(gate, "case_serial", "gate"),
            "gate.case",
            minimum=1,
            maximum=999_999,
        ),
    )
    pip_identity = (
        _positive_int32(
            _typed_value(pip, "owner_character_id", "pip"), "pip.owner"
        ),
        _positive_int32(
            _typed_value(pip, "subject_character_id", "pip"), "pip.subject"
        ),
        _integer(
            _typed_value(pip, "cycle_serial", "pip"),
            "pip.cycle",
            minimum=1,
            maximum=2**63 - 1,
        ),
        _integer(
            _typed_value(pip, "case_serial", "pip"),
            "pip.case",
            minimum=1,
            maximum=999_999,
        ),
    )
    if gate_identity != pip_identity:
        raise ValueError("B2 gate and PIP immutable identities disagree")
    if pip_identity[0] != owner_character_id:
        raise ValueError("B2 PIP owner differs from the requested owner")
    if pip_identity[1] != binding["player_character_id"]:
        raise ValueError("B2 PIP subject differs from the played character")
    state = _integer(
        _typed_value(pip, "state", "pip"),
        "pip.state",
        minimum=1,
        maximum=5,
    )
    return B2PipIdentity(*pip_identity, state)


def _response_projection(response: dict[str, object]) -> dict[str, object]:
    group = response.get("response")
    fields = (
        "subject_response",
        "response_case_serial",
        "response_author_character_id",
        "acknowledgement_receipt_serial",
        "goal_revision_used",
        "refusal_receipt_serial",
    )
    return {
        key: group.get(key) if isinstance(group, dict) else None for key in fields
    }


def _require_pending_response(
    response: dict[str, object], identity: B2PipIdentity
) -> None:
    if identity.state != 1:
        raise ValueError("B2 PIP prompt is not in ACK_PENDING state")
    gate = response.get("gate")
    if _typed_value(gate, "status", "gate") != 1:
        raise ValueError("B2 PIP evidence gate is not qualified")
    subject_response = response.get("response")
    if (
        _typed_value(subject_response, "subject_response", "response") != 0
        or _typed_value(subject_response, "response_case_serial", "response")
        != 0
        or not _typed_unavailable(
            subject_response,
            "response_author_character_id",
            "response",
            reason="variable_absent",
        )
        or _typed_value(
            subject_response, "acknowledgement_receipt_serial", "response"
        )
        != identity.case_serial
        or _typed_value(subject_response, "goal_revision_used", "response")
        is not False
        or _typed_value(subject_response, "refusal_receipt_serial", "response")
        != 0
    ):
        raise ValueError("B2 PIP prompt lacks its unique pending response tuple")


def _require_post_response(
    response: dict[str, object], identity: B2PipIdentity, spec: _ActionSpec
) -> None:
    group = response.get("response")
    expected_refusal_receipt = (
        identity.case_serial if spec.refusal_receipt else 0
    )
    if (
        identity.state != spec.resulting_state
        or _typed_value(group, "subject_response", "response")
        != spec.response_code
        or _typed_value(group, "response_case_serial", "response")
        != identity.case_serial
        or _typed_value(group, "response_author_character_id", "response")
        != identity.subject_character_id
        or _typed_value(group, "acknowledgement_receipt_serial", "response")
        != identity.case_serial
        or _typed_value(group, "goal_revision_used", "response")
        is not spec.goal_revision_used
        or _typed_value(group, "refusal_receipt_serial", "response")
        != expected_refusal_receipt
    ):
        raise ValueError("B2 provider did not publish the selected response receipt")


def _validate_event_context(
    response: object,
    *,
    binding: dict[str, object],
    owner_character_id: int,
) -> list[dict[str, object]]:
    if not isinstance(response, dict):
        raise ValueError("current-event-window response is not an object")
    context = response.get("current_event_window_context")
    if not isinstance(context, dict):
        raise ValueError("current-event-window response lacks its typed context")
    if response.get("status") != "available" or context.get("status") != "available":
        raise ValueError("current-event-window context is unavailable")
    if context.get("event_definition_key") != B2_PIP_EVENT_DEFINITION_KEY:
        raise ValueError(
            "wrong active event: expected "
            f"{B2_PIP_EVENT_DEFINITION_KEY}, observed "
            f"{context.get('event_definition_key')}"
        )
    if (
        context.get("current_event_instance_id") != binding["event_instance_id"]
        or context.get("snapshot_revision") != binding["native_revision"]
        or context.get("date_raw") != binding["date_raw"]
    ):
        raise ValueError("current-event-window context crossed its paused frame")
    readiness = context.get("readiness")
    if not (
        isinstance(readiness, dict)
        and readiness.get("event_definition_identity_ready") is True
        and readiness.get("root_scope_ready") is True
        and readiness.get("saved_scopes_ready") is True
        and readiness.get("option_presentation_ready") is True
    ):
        raise ValueError("current-event-window semantic identity is not ready")
    root_character_id = _character_scope_id(
        context.get("root_scope"), "current event root_scope"
    )
    if root_character_id != binding["player_character_id"]:
        raise ValueError("PIP event root is not the played subject")

    raw_saved_scopes = context.get("saved_scopes")
    if not isinstance(raw_saved_scopes, list):
        raise ValueError("PIP event saved scopes are unavailable")
    saved_scopes: dict[str, object] = {}
    for row in raw_saved_scopes:
        if not isinstance(row, dict) or not isinstance(row.get("name"), str):
            raise ValueError("PIP event contains a malformed saved scope")
        name = str(row["name"])
        if name in saved_scopes:
            raise ValueError("PIP event contains duplicate saved scopes")
        saved_scopes[name] = row.get("scope")
    missing = (
        set(_CHARACTER_SCOPE_NAMES.values()) | set(_SCALAR_SCOPE_NAMES)
    ) - set(saved_scopes)
    if missing:
        raise ValueError(
            "PIP event lacks required frozen scopes: " + ", ".join(sorted(missing))
        )
    if (
        _character_scope_id(
            saved_scopes[_CHARACTER_SCOPE_NAMES["owner"]],
            "PIP prompt owner scope",
        )
        != owner_character_id
    ):
        raise ValueError("PIP event owner scope differs from the requested owner")
    if (
        _character_scope_id(
            saved_scopes[_CHARACTER_SCOPE_NAMES["subject"]],
            "PIP prompt subject scope",
        )
        != binding["player_character_id"]
    ):
        raise ValueError("PIP event subject scope differs from the played subject")

    raw_options = context.get("options")
    if not isinstance(raw_options, list) or len(raw_options) != 3:
        raise ValueError("zg361b2.40 does not expose exactly three options")
    option_rows: list[dict[str, object]] = []
    observed_indices: set[int] = set()
    for rendered_index, raw_option in enumerate(raw_options):
        if not isinstance(raw_option, dict):
            raise ValueError("PIP event option is not an object")
        native_index = _integer(
            raw_option.get("native_option_index"),
            "PIP option native index",
            minimum=0,
            maximum=2,
        )
        if native_index in observed_indices:
            raise ValueError("PIP event option indices are duplicated")
        observed_indices.add(native_index)
        if (
            raw_option.get("rendered_index") != rendered_index
            or native_index != rendered_index
            or raw_option.get("shown") is not True
            or raw_option.get("enabled") is not True
        ):
            raise ValueError("PIP event option order/availability changed")
        action_name = tuple(_ACTION_SPECS)[native_index]
        spec = _ACTION_SPECS[action_name]
        normalized_name = _normalize_semantic_text(raw_option.get("resolved_name"))
        allowed = {
            _normalize_semantic_text(candidate) for candidate in spec.resolved_names
        }
        if not normalized_name or normalized_name not in allowed:
            raise ValueError(
                f"PIP option {native_index + 1} semantic text changed"
            )
        option_rows.append(
            {
                "action": action_name,
                "option_number": native_index + 1,
                "native_option_index": native_index,
                "resolved_name": raw_option.get("resolved_name"),
                "semantic_text_valid": True,
            }
        )
    if binding["event_option_count"] != 3 or observed_indices != {0, 1, 2}:
        raise ValueError("snapshot and typed PIP option counts disagree")
    return option_rows


def _query_b2(
    service: B2PipActionService,
    *,
    nonce: str,
    binding: dict[str, object],
    owner_character_id: int,
) -> dict[str, object]:
    response = service.query_zhongguo_b2_pip_snapshot_v1(
        nonce,
        expected_revision=int(binding["revision"]),
        owner_character_id=owner_character_id,
    )
    if not isinstance(response, dict):
        raise ValueError("B2 provider returned a non-object")
    if response.get("request_nonce") != nonce:
        raise ValueError("B2 provider request nonce changed")
    return response


def run_b2_pip_gameplay_action_cell(
    service: B2PipActionService,
    *,
    owner_character_id: int,
    action: str = "accept",
    request_nonce_prefix: str = "zg361.phase2.b2.action",
    timeout_s: float = 5.0,
    poll_interval_s: float = 0.05,
    clock: Callable[[], float] = time.monotonic,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, object]:
    """Execute and prove one received-self B2 PIP response.

    The caller owns save/restore bracketing.  This helper intentionally does
    not advance the game date: all three response effects are immediate and a
    same-paused-date provider transition is the strongest postcondition.
    """

    owner_character_id = _positive_int32(
        owner_character_id, "owner_character_id"
    )
    if action not in _ACTION_SPECS:
        raise ValueError("action must be accept, negotiate, or refuse")
    if (
        not isinstance(request_nonce_prefix, str)
        or _NONCE_PREFIX_RE.fullmatch(request_nonce_prefix) is None
    ):
        raise ValueError("request_nonce_prefix must be a 1-48 character token")
    if timeout_s < 0 or poll_interval_s <= 0:
        raise ValueError("timeout_s must be non-negative and poll_interval_s positive")
    spec = _ACTION_SPECS[action]
    evidence: dict[str, object] = {
        "schema_version": 1,
        "result": "RED",
        "cell": "zg361.phase2.b2.pip-response-action",
        "action": action,
        "mcp_only": True,
        "ocr_used": False,
        "coordinates_used": False,
        "event_definition_key": B2_PIP_EVENT_DEFINITION_KEY,
        "option_number": spec.option_number,
        "precondition": None,
        "selection_submission": None,
        "postcondition_observations": [],
        "postcondition": None,
        "ack_is_postcondition": False,
        "postcondition_query_green": False,
        "failure_reason": None,
    }

    def fail(reason: str) -> None:
        evidence["failure_reason"] = reason
        raise B2PipActionCellError(reason, evidence)

    try:
        pre_snapshot = service.snapshot()
        pre_binding = _snapshot_binding(pre_snapshot, require_event=True)
        event_instance_id = int(pre_binding["event_instance_id"])
        event_response = service.query_current_event_window_context_v1(
            event_instance_id,
            expected_revision=int(pre_binding["revision"]),
        )
        option_rows = _validate_event_context(
            event_response,
            binding=pre_binding,
            owner_character_id=owner_character_id,
        )
        pre_response = _query_b2(
            service,
            nonce=f"{request_nonce_prefix}.pre",
            binding=pre_binding,
            owner_character_id=owner_character_id,
        )
        pre_identity = _extract_b2_identity(
            pre_response,
            binding=pre_binding,
            owner_character_id=owner_character_id,
        )
        _require_pending_response(pre_response, pre_identity)
        evidence["precondition"] = {
            "binding": pre_binding,
            "event_definition_key": B2_PIP_EVENT_DEFINITION_KEY,
            "required_event_scopes": sorted(
                set(_CHARACTER_SCOPE_NAMES.values()) | set(_SCALAR_SCOPE_NAMES)
            ),
            "options": option_rows,
            "identity": asdict(pre_identity),
            "response": _response_projection(pre_response),
        }

        selection_snapshot = service.snapshot()
        selection_binding = _snapshot_binding(
            selection_snapshot, require_event=True
        )
        if selection_binding != pre_binding:
            fail("paused B2 event changed between precondition and submission")
        submission = service.select_event_option(
            spec.option_number,
            event_instance_id=event_instance_id,
            expected_revision=int(selection_binding["revision"]),
        )
        evidence["selection_submission"] = submission
        if not (
            isinstance(submission, dict)
            and submission.get("accepted") is True
            and submission.get("status") == "submitted"
            and submission.get("event_instance_id") == event_instance_id
            and submission.get("option_number") == spec.option_number
        ):
            fail("bound select-event-option ACK was not accepted")

        deadline = clock() + timeout_s
        query_attempt = 0
        while True:
            post_snapshot = service.snapshot()
            post_binding = _snapshot_binding(post_snapshot, require_event=False)
            observations = evidence["postcondition_observations"]
            assert isinstance(observations, list)
            observations.append(post_binding)
            if (
                post_binding["date_raw"] != pre_binding["date_raw"]
                or post_binding["player_character_id"]
                != pre_binding["player_character_id"]
                or post_binding["connection_generation"]
                != pre_binding["connection_generation"]
            ):
                fail("B2 action crossed its paused date/player/connection binding")

            if post_binding["event_instance_id"] != event_instance_id:
                query_attempt += 1
                post_response = _query_b2(
                    service,
                    nonce=f"{request_nonce_prefix}.post{query_attempt}",
                    binding=post_binding,
                    owner_character_id=owner_character_id,
                )
                post_identity = _extract_b2_identity(
                    post_response,
                    binding=post_binding,
                    owner_character_id=owner_character_id,
                )
                if post_identity.immutable_case != pre_identity.immutable_case:
                    fail("B2 action postcondition changed the immutable case identity")
                if post_identity.state == 1:
                    _require_pending_response(post_response, post_identity)
                else:
                    _require_post_response(post_response, post_identity, spec)
                    evidence["postcondition"] = {
                        "binding": post_binding,
                        "identity": asdict(post_identity),
                        "response": _response_projection(post_response),
                        "same_immutable_case": True,
                        "expected_state_transition": [
                            pre_identity.state,
                            spec.resulting_state,
                        ],
                    }
                    evidence["postcondition_query_green"] = True
                    evidence["result"] = "GREEN"
                    evidence["failure_reason"] = None
                    return evidence

            now = clock()
            if now >= deadline:
                fail(
                    "timed out before the B2 provider published the selected "
                    "response postcondition"
                )
            sleeper(min(poll_interval_s, max(0.0, deadline - now)))
    except B2PipActionCellError:
        raise
    except Exception as error:
        fail(f"{type(error).__name__}: {error}")
    raise AssertionError("unreachable")


__all__ = [
    "B2_PIP_EVENT_DEFINITION_KEY",
    "B2PipActionCellError",
    "B2PipIdentity",
    "run_b2_pip_gameplay_action_cell",
]
