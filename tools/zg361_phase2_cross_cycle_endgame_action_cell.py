#!/usr/bin/env python3
"""Independent Phase 2 cross-cycle endgame action/postcondition cell.

The visible ``zg361we.356`` and ``zg361we.361`` events are owner-facing, while
the existing Workforce provider is deliberately received-self and therefore
must be queried while the case subject is played.  This cell joins those two
surfaces through one hash-identical result checkpoint.  It never upgrades the
``#356`` option ACK, a transition callback, or a character-switch ACK into the
business postcondition: GREEN requires the subject-side provider to expose the
route-C debt and the prepared/consumed #361 charter for the same case.

The module does not launch CK3, register a promo handler, create checkpoints,
or perform character switching.  Those live operations remain explicit runner
seams and the contract stays live-pending until a real checkpoint and typed
transition receipt are supplied.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Callable, Final, Mapping, Protocol


SPAN_ID: Final = "phase2_cross_cycle_endgame"
HANDLER: Final = "capture_cross_cycle_endgame"
PRODUCER_KEY: Final = "cross-cycle-endgame"
SOURCE_EVENT: Final = "zg361we.356"
RESULT_EVENT: Final = "zg361we.361"
SOURCE_OPTION_NUMBER: Final = 1
M360_REQUIRED_ROUTE: Final = "C"

QUERY_EVENT_CAPABILITY: Final = (
    "game.command.query-current-event-window-context-v1"
)
SELECT_EVENT_OPTION_CAPABILITY: Final = "game.command.select-event-option-N"
WORKFORCE_QUERY_CAPABILITY: Final = (
    "game.command.query-zhongguo-workforce-collective-snapshot-v1"
)

_OWNER_SCOPE: Final = "zg361_we_al_owner"
_SUBJECT_SCOPE: Final = "zg361_we_al_subject"
_SCALAR_SCOPES: Final = frozenset(
    {"zg361_we_al_cycle", "zg361_we_al_case"}
)
_SHA256_RE: Final = re.compile(r"[0-9A-F]{64}\Z")


class EndgameOwnerService(Protocol):
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


class EndgameSubjectService(Protocol):
    def snapshot(self) -> dict[str, object]: ...

    def query_zhongguo_workforce_collective_snapshot_v1(
        self,
        request_nonce: str,
        *,
        expected_revision: int,
        owner_character_id: int,
    ) -> dict[str, object]: ...


@dataclass(frozen=True, slots=True)
class EndgameVisibleBinding:
    owner_character_id: int
    subject_character_id: int
    source_event_instance_id: int
    source_revision: int
    source_native_revision: int
    source_date_raw: int


@dataclass(frozen=True, slots=True)
class EndgameResultBinding:
    owner_character_id: int
    subject_character_id: int
    result_event_instance_id: int
    result_revision: int
    result_native_revision: int
    result_date_raw: int
    result_checkpoint_sha256: str
    save_lineage_id: str


@dataclass(frozen=True, slots=True)
class EndgameSubjectProofSession:
    service: EndgameSubjectService
    transition_receipt: Mapping[str, object]


CompletionExecutor = Callable[
    [EndgameOwnerService, EndgameVisibleBinding], Mapping[str, object]
]
SubjectSessionFactory = Callable[
    [EndgameResultBinding], EndgameSubjectProofSession
]


class CrossCycleEndgameCellError(RuntimeError):
    """Typed RED with evidence that is safe to persist as a sidecar."""

    def __init__(self, reason_code: str, evidence: Mapping[str, object]) -> None:
        self.reason_code = reason_code
        self.evidence = {
            **dict(evidence),
            "result": "RED",
            "reason_code": reason_code,
        }
        super().__init__(f"cross-cycle endgame cell RED [{reason_code}]")


def _fail(reason_code: str, **evidence: object) -> None:
    raise CrossCycleEndgameCellError(reason_code, evidence)


def _integer(
    value: object, label: str, *, minimum: int, maximum: int
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not minimum <= value <= maximum
    ):
        _fail("integer_binding_invalid", label=label, observed=value)
    return value


def _positive_int32(value: object, label: str) -> int:
    return _integer(value, label, minimum=1, maximum=2**31 - 1)


def _paused_binding(
    snapshot: object, *, expected_player: int | None, require_event: bool
) -> dict[str, object]:
    if not isinstance(snapshot, Mapping):
        _fail("snapshot_not_an_object", snapshot=snapshot)
    played = snapshot.get("played_character")
    active = snapshot.get("active_event")
    player = (
        played.get("character_id") if isinstance(played, Mapping) else None
    )
    binding = {
        "snapshot_id": snapshot.get("snapshot_id"),
        "revision": snapshot.get("revision"),
        "native_revision": snapshot.get("native_revision"),
        "date_raw": snapshot.get("date_raw"),
        "player_character_id": player,
        "event_instance_id": (
            active.get("instance_id") if isinstance(active, Mapping) else None
        ),
    }
    valid = (
        snapshot.get("paused") is True
        and snapshot.get("map_ready") is True
        and isinstance(binding["snapshot_id"], str)
        and bool(binding["snapshot_id"])
        and isinstance(binding["revision"], int)
        and not isinstance(binding["revision"], bool)
        and int(binding["revision"]) >= 0
        and isinstance(binding["native_revision"], int)
        and not isinstance(binding["native_revision"], bool)
        and int(binding["native_revision"]) > 0
        and isinstance(binding["date_raw"], int)
        and not isinstance(binding["date_raw"], bool)
        and isinstance(player, int)
        and not isinstance(player, bool)
        and 1 <= int(player) <= 2**31 - 1
        and (
            not require_event
            or (
                isinstance(binding["event_instance_id"], int)
                and not isinstance(binding["event_instance_id"], bool)
                and int(binding["event_instance_id"]) > 0
            )
        )
    )
    if not valid:
        _fail("paused_binding_unavailable", binding=binding)
    if expected_player is not None and player != expected_player:
        _fail(
            "played_character_drifted",
            expected_player_character_id=expected_player,
            observed_player_character_id=player,
        )
    return binding


def _character_scope_id(scope: object, label: str) -> int:
    if not isinstance(scope, Mapping):
        _fail("event_character_scope_missing", label=label, scope=scope)
    identity = scope.get("typed_identity")
    if not (
        isinstance(identity, Mapping)
        and identity.get("status") == "available"
        and identity.get("kind") == "character"
    ):
        _fail("event_character_scope_unready", label=label, scope=scope)
    return _positive_int32(identity.get("character_id"), f"{label}.character_id")


def _event_surface(
    service: EndgameOwnerService,
    binding: Mapping[str, object],
    *,
    expected_event: str,
    expected_owner: int | None,
    expected_subject: int | None,
) -> tuple[dict[str, object], int, int]:
    response = service.query_current_event_window_context_v1(
        int(binding["event_instance_id"]),
        expected_revision=int(binding["revision"]),
    )
    context = (
        response.get("current_event_window_context")
        if isinstance(response, Mapping)
        else None
    )
    readiness = context.get("readiness") if isinstance(context, Mapping) else None
    if not (
        isinstance(response, Mapping)
        and response.get("status") == "available"
        and isinstance(context, Mapping)
        and context.get("status") == "available"
        and context.get("event_definition_key") == expected_event
        and context.get("current_event_instance_id")
        == binding["event_instance_id"]
        and context.get("snapshot_revision") == binding["native_revision"]
        and context.get("date_raw") == binding["date_raw"]
        and isinstance(readiness, Mapping)
        and readiness.get("event_definition_identity_ready") is True
        and readiness.get("root_scope_ready") is True
        and readiness.get("saved_scopes_ready") is True
        and readiness.get("option_presentation_ready") is True
    ):
        _fail(
            "event_surface_not_identity_ready",
            expected_event=expected_event,
            binding=dict(binding),
            response=response,
        )
    assert isinstance(context, Mapping)
    root = _character_scope_id(context.get("root_scope"), "root_scope")
    if root != binding["player_character_id"]:
        _fail("event_root_is_not_played_owner", root=root, binding=dict(binding))

    saved_rows = context.get("saved_scopes")
    if not isinstance(saved_rows, list):
        _fail("event_saved_scopes_missing", event_definition_key=expected_event)
    saved: dict[str, object] = {}
    for row in saved_rows:
        if not isinstance(row, Mapping) or not isinstance(row.get("name"), str):
            _fail("event_saved_scope_malformed", row=row)
        name = str(row["name"])
        if name in saved:
            _fail("event_saved_scope_duplicated", name=name)
        saved[name] = row.get("scope")
    missing = {_OWNER_SCOPE, _SUBJECT_SCOPE, *_SCALAR_SCOPES} - set(saved)
    if missing:
        _fail("event_case_scopes_missing", missing_scopes=sorted(missing))
    owner = _character_scope_id(saved[_OWNER_SCOPE], _OWNER_SCOPE)
    subject = _character_scope_id(saved[_SUBJECT_SCOPE], _SUBJECT_SCOPE)
    if owner != root or subject == owner:
        _fail(
            "event_owner_subject_binding_invalid",
            owner_character_id=owner,
            subject_character_id=subject,
            root_character_id=root,
        )
    if expected_owner is not None and owner != expected_owner:
        _fail("event_owner_drifted", expected=expected_owner, observed=owner)
    if expected_subject is not None and subject != expected_subject:
        _fail("event_subject_drifted", expected=expected_subject, observed=subject)

    options = context.get("options")
    if not isinstance(options, list) or len(options) != 3:
        _fail("event_option_surface_invalid", expected_event=expected_event)
    observed_indices = [
        row.get("native_option_index")
        for row in options
        if isinstance(row, Mapping)
        and row.get("shown") is True
        and row.get("enabled") is True
    ]
    if observed_indices != [0, 1, 2]:
        _fail(
            "event_option_surface_invalid",
            expected_event=expected_event,
            native_indices=observed_indices,
        )
    return dict(context), owner, subject


def _checkpoint_sha(value: object, *, label: str) -> str:
    sha = str(value or "").upper()
    if _SHA256_RE.fullmatch(sha) is None:
        _fail("checkpoint_binding_invalid", label=label, sha256=value)
    return sha


def _validate_source_restore(
    value: object, *, binding: Mapping[str, object]
) -> dict[str, object]:
    restore = dict(value) if isinstance(value, Mapping) else {}
    checkpoint = restore.get("checkpoint")
    expected = restore.get("expected")
    receipt = restore.get("restore_receipt")
    checkpoint = dict(checkpoint) if isinstance(checkpoint, Mapping) else {}
    expected = dict(expected) if isinstance(expected, Mapping) else {}
    receipt = dict(receipt) if isinstance(receipt, Mapping) else {}
    sha = _checkpoint_sha(checkpoint.get("sha256"), label="source checkpoint")
    valid = (
        restore.get("result") == "GREEN"
        and restore.get("span_id") == SPAN_ID
        and restore.get("handler") == HANDLER
        and expected.get("event_definition_key") == SOURCE_EVENT
        and expected.get("owner_character_id") == binding["player_character_id"]
        and expected.get("player_character_id") == binding["player_character_id"]
        and expected.get("date_raw") == binding["date_raw"]
        and isinstance(checkpoint.get("bytes"), int)
        and not isinstance(checkpoint.get("bytes"), bool)
        and int(checkpoint["bytes"]) > 0
        and isinstance(checkpoint.get("save_lineage_id"), str)
        and bool(checkpoint.get("save_lineage_id"))
        and receipt.get("result") == "GREEN"
        and receipt.get("provider_observed") is True
        and str(receipt.get("checkpoint_sha256", "")).upper() == sha
        and receipt.get("save_lineage_id") == checkpoint.get("save_lineage_id")
        and receipt.get("event_definition_key") == SOURCE_EVENT
        and receipt.get("owner_character_id") == binding["player_character_id"]
        and receipt.get("player_character_id") == binding["player_character_id"]
        and receipt.get("date_raw") == binding["date_raw"]
        and receipt.get("fixture_used") is False
        and receipt.get("console_used") is False
        and receipt.get("generic_character_rebind_used") is False
    )
    if not valid:
        _fail(
            "source_checkpoint_restore_not_green",
            restore=restore,
            source_binding=dict(binding),
        )
    return restore


def _validate_completion(
    value: object,
    *,
    owner: int,
    subject: int,
    result_binding: Mapping[str, object],
) -> tuple[dict[str, object], str, str]:
    completion = dict(value) if isinstance(value, Mapping) else {}
    checkpoint = completion.get("result_checkpoint")
    checkpoint = dict(checkpoint) if isinstance(checkpoint, Mapping) else {}
    sha = _checkpoint_sha(checkpoint.get("sha256"), label="result checkpoint")
    lineage = checkpoint.get("save_lineage_id")
    valid = (
        completion.get("result") == "GREEN"
        and completion.get("m360_route") == M360_REQUIRED_ROUTE
        and completion.get("action_ack_only") is False
        and completion.get("fixture_used") is False
        and completion.get("console_used") is False
        and checkpoint.get("event_definition_key") == RESULT_EVENT
        and checkpoint.get("owner_character_id") == owner
        and checkpoint.get("player_character_id") == owner
        and checkpoint.get("subject_character_id") == subject
        and checkpoint.get("date_raw") == result_binding["date_raw"]
        and isinstance(checkpoint.get("bytes"), int)
        and not isinstance(checkpoint.get("bytes"), bool)
        and int(checkpoint["bytes"]) > 0
        and isinstance(lineage, str)
        and bool(lineage)
    )
    if not valid:
        _fail(
            "completion_transition_not_green",
            completion=completion,
            result_binding=dict(result_binding),
        )
    assert isinstance(lineage, str)
    return completion, sha, lineage


def _typed(group: object, key: str, label: str) -> object:
    if not isinstance(group, Mapping):
        _fail("provider_group_missing", label=label)
    field = group.get(key)
    if not (
        isinstance(field, Mapping)
        and field.get("status") == "available"
        and field.get("unavailable_reason") is None
    ):
        _fail("provider_field_unavailable", label=f"{label}.{key}", field=field)
    return field.get("value")


def _identity(
    group: object, *, label: str, state: int | None = None
) -> tuple[int, int, int, int]:
    owner = _positive_int32(_typed(group, "owner_character_id", label), f"{label}.owner")
    subject = _positive_int32(
        _typed(group, "subject_character_id", label), f"{label}.subject"
    )
    cycle = _integer(
        _typed(group, "cycle_serial", label),
        f"{label}.cycle",
        minimum=1,
        maximum=2**63 - 1,
    )
    case = _positive_int32(_typed(group, "case_serial", label), f"{label}.case")
    if state is not None and _typed(group, "state", label) != state:
        _fail(
            "provider_state_drifted",
            label=label,
            expected_state=state,
            observed_state=_typed(group, "state", label),
        )
    return owner, subject, cycle, case


def _validate_subject_transition(
    value: object,
    *,
    result: EndgameResultBinding,
) -> dict[str, object]:
    receipt = dict(value) if isinstance(value, Mapping) else {}
    valid = (
        receipt.get("result") == "GREEN"
        and receipt.get("provider_observed") is True
        and receipt.get("action_ack_only") is False
        and receipt.get("from_player_character_id") == result.owner_character_id
        and receipt.get("to_player_character_id") == result.subject_character_id
        and receipt.get("date_raw") == result.result_date_raw
        and str(receipt.get("restored_checkpoint_sha256", "")).upper()
        == result.result_checkpoint_sha256
        and receipt.get("save_lineage_id") == result.save_lineage_id
        and receipt.get("fixture_used") is False
        and receipt.get("console_used") is False
        and receipt.get("generic_character_rebind_used") is False
    )
    if not valid:
        _fail(
            "subject_proof_transition_not_green",
            transition_receipt=receipt,
            result_binding=asdict(result),
        )
    return receipt


def _validate_workforce_postcondition(
    response: object,
    *,
    subject_binding: Mapping[str, object],
    owner: int,
    subject: int,
) -> dict[str, object]:
    provider = dict(response) if isinstance(response, Mapping) else {}
    readiness = provider.get("readiness")
    binding = provider.get("binding")
    if not (
        provider.get("status") == "available"
        and isinstance(readiness, Mapping)
        and readiness.get("ready") is True
        and provider.get("player_character_id") == subject
        and provider.get("subject_character_id") == subject
        and provider.get("requested_owner_character_id") == owner
        and isinstance(binding, Mapping)
        and binding.get("snapshot_id") == subject_binding["snapshot_id"]
        and binding.get("revision") == subject_binding["revision"]
        and binding.get("native_revision") == subject_binding["native_revision"]
        and binding.get("date_raw") == subject_binding["date_raw"]
        and binding.get("player_character_id") == subject
        and binding.get("subject_character_id") == subject
        and binding.get("owner_character_id") == owner
    ):
        _fail(
            "workforce_provider_unavailable",
            subject_binding=dict(subject_binding),
            provider=provider,
        )

    case_identity = _identity(provider.get("al_case"), label="al_case")
    receipt_identity = _identity(
        provider.get("m360_receipt"), label="m360_receipt", state=4
    )
    debt_identity = _identity(
        provider.get("route_c_debt"), label="route_c_debt", state=4
    )
    charter_identity = _identity(
        provider.get("charter_gate"), label="charter_gate", state=5
    )
    expected_identity = (
        owner,
        subject,
        case_identity[2],
        case_identity[3],
    )
    if not (
        case_identity == expected_identity
        and receipt_identity == expected_identity
        and debt_identity == expected_identity
        and charter_identity == expected_identity
    ):
        _fail(
            "endgame_case_identity_drifted",
            case_identity=case_identity,
            receipt_identity=receipt_identity,
            debt_identity=debt_identity,
            charter_identity=charter_identity,
        )
    cycle = case_identity[2]
    debt = provider["route_c_debt"]
    charter = provider["charter_gate"]
    debt_open = _typed(debt, "open", "route_c_debt")
    debt_consumed = _typed(debt, "consumed", "route_c_debt")
    charter_status = charter.get("status") if isinstance(charter, Mapping) else None
    expected_ready = charter_status == "ready"
    expected_consumed = charter_status == "consumed"
    checks = {
        "m360_route_c_receipt": _typed(
            provider["m360_receipt"], "choice", "m360_receipt"
        )
        == 3,
        "debt_lifecycle_coherent": (debt_open, debt_consumed)
        in {(True, False), (False, True)},
        "debt_due_next_cycle": _typed(
            debt, "due_cycle_serial", "route_c_debt"
        )
        == cycle + 1,
        "charter_status_visible": charter_status in {"ready", "consumed"},
        "charter_evidence_count_three": _typed(
            charter, "evidence_count", "charter_gate"
        )
        == 3,
        "charter_evidence_lifecycle": _typed(
            charter, "evidence_ready", "charter_gate"
        )
        is expected_ready
        and _typed(charter, "evidence_consumed", "charter_gate")
        is expected_consumed,
        "charter_id_positive": isinstance(
            _typed(charter, "prepared_charter_id", "charter_gate"), int
        )
        and not isinstance(
            _typed(charter, "prepared_charter_id", "charter_gate"), bool
        )
        and int(_typed(charter, "prepared_charter_id", "charter_gate")) > 0,
        "charter_adopted_in_terminal_cycle": _typed(
            charter, "adopted_cycle_serial", "charter_gate"
        )
        == cycle,
        "charter_effective_next_cycle": _typed(
            charter, "effective_cycle_serial", "charter_gate"
        )
        == cycle + 1,
    }
    failed = [name for name, passed in checks.items() if passed is not True]
    if failed:
        _fail(
            "endgame_business_postcondition_not_green",
            failed_checks=failed,
            provider=provider,
        )
    return {
        "provider_observed": True,
        "action_ack_only": False,
        "owner_character_id": owner,
        "subject_character_id": subject,
        "terminal_cycle_serial": cycle,
        "terminal_case_serial": case_identity[3],
        "carried_debt": {
            "origin_cycle_serial": cycle,
            "carried_into_cycle_serial": cycle + 1,
            "open": debt_open,
            "consumed": debt_consumed,
        },
        "default_change": {
            "charter_id": _typed(
                charter, "prepared_charter_id", "charter_gate"
            ),
            "status": charter_status,
            "adopted_cycle_serial": cycle,
            "effective_cycle_serial": cycle + 1,
        },
        "checks": checks,
    }


def inspect_cross_cycle_endgame_source(
    owner_service: EndgameOwnerService,
    *,
    source_checkpoint_restore: Mapping[str, object],
) -> dict[str, object]:
    """Read-only proof that the restored #356 owner surface is actionable."""

    source_snapshot = owner_service.snapshot()
    source_binding = _paused_binding(
        source_snapshot, expected_player=None, require_event=True
    )
    restore = _validate_source_restore(
        source_checkpoint_restore, binding=source_binding
    )
    source_context, owner, subject = _event_surface(
        owner_service,
        source_binding,
        expected_event=SOURCE_EVENT,
        expected_owner=int(source_binding["player_character_id"]),
        expected_subject=None,
    )
    return {
        "result": "GREEN",
        "provider_observed": True,
        "action_executed": False,
        "source_checkpoint_restore": restore,
        "source_binding": source_binding,
        "source_event_context": source_context,
        "owner_character_id": owner,
        "subject_character_id": subject,
    }


def run_cross_cycle_endgame_action_cell(
    owner_service: EndgameOwnerService,
    *,
    source_checkpoint_restore: Mapping[str, object],
    completion_executor: CompletionExecutor,
    subject_session_factory: SubjectSessionFactory,
    request_nonce: str = "zg361.phase2.endgame.post",
) -> dict[str, object]:
    """Select #356 route A and prove #361 + route-C debt/default change.

    ``completion_executor`` owns the bounded product path from the accepted
    #356 option through the M357-M360 lifecycle and must deliberately choose
    M360 route C.  ``subject_session_factory`` restores/rebinds the exact
    result checkpoint for the received-self query.  Neither callback result is
    accepted as the business postcondition.
    """

    if not callable(completion_executor) or not callable(subject_session_factory):
        raise ValueError("endgame live transition seams must be callable")
    if not isinstance(request_nonce, str) or not request_nonce or len(request_nonce) > 64:
        raise ValueError("request_nonce must be 1..64 characters")

    source = inspect_cross_cycle_endgame_source(
        owner_service, source_checkpoint_restore=source_checkpoint_restore
    )
    source_binding = source["source_binding"]
    assert isinstance(source_binding, Mapping)
    restore = source["source_checkpoint_restore"]
    assert isinstance(restore, Mapping)
    source_context = source["source_event_context"]
    assert isinstance(source_context, Mapping)
    owner = int(source["owner_character_id"])
    subject = int(source["subject_character_id"])
    visible_binding = EndgameVisibleBinding(
        owner_character_id=owner,
        subject_character_id=subject,
        source_event_instance_id=int(source_binding["event_instance_id"]),
        source_revision=int(source_binding["revision"]),
        source_native_revision=int(source_binding["native_revision"]),
        source_date_raw=int(source_binding["date_raw"]),
    )
    ack = owner_service.select_event_option(
        SOURCE_OPTION_NUMBER,
        event_instance_id=visible_binding.source_event_instance_id,
        expected_revision=visible_binding.source_revision,
    )
    if not (
        isinstance(ack, Mapping)
        and ack.get("accepted") is True
        and ack.get("status") == "submitted"
    ):
        _fail("source_event_action_not_submitted", action_ack=ack)

    raw_completion = completion_executor(owner_service, visible_binding)
    result_snapshot = owner_service.snapshot()
    result_binding = _paused_binding(
        result_snapshot, expected_player=owner, require_event=True
    )
    if not (
        result_binding["snapshot_id"] != source_binding["snapshot_id"]
        and int(result_binding["revision"]) > int(source_binding["revision"])
        and int(result_binding["native_revision"])
        > int(source_binding["native_revision"])
    ):
        _fail(
            "result_frame_did_not_advance",
            source_binding=source_binding,
            result_binding=result_binding,
        )
    result_context, result_owner, result_subject = _event_surface(
        owner_service,
        result_binding,
        expected_event=RESULT_EVENT,
        expected_owner=owner,
        expected_subject=subject,
    )
    completion, result_sha, lineage = _validate_completion(
        raw_completion,
        owner=owner,
        subject=subject,
        result_binding=result_binding,
    )
    result = EndgameResultBinding(
        owner_character_id=result_owner,
        subject_character_id=result_subject,
        result_event_instance_id=int(result_binding["event_instance_id"]),
        result_revision=int(result_binding["revision"]),
        result_native_revision=int(result_binding["native_revision"]),
        result_date_raw=int(result_binding["date_raw"]),
        result_checkpoint_sha256=result_sha,
        save_lineage_id=lineage,
    )

    proof_session = subject_session_factory(result)
    if not isinstance(proof_session, EndgameSubjectProofSession):
        _fail("subject_proof_session_invalid", observed_type=type(proof_session).__name__)
    transition = _validate_subject_transition(
        proof_session.transition_receipt, result=result
    )
    subject_snapshot = proof_session.service.snapshot()
    subject_binding = _paused_binding(
        subject_snapshot, expected_player=subject, require_event=False
    )
    if subject_binding["date_raw"] != result.result_date_raw:
        _fail(
            "subject_proof_date_drifted",
            result_date_raw=result.result_date_raw,
            subject_date_raw=subject_binding["date_raw"],
        )
    provider = proof_session.service.query_zhongguo_workforce_collective_snapshot_v1(
        request_nonce,
        expected_revision=int(subject_binding["revision"]),
        owner_character_id=owner,
    )
    postcondition = _validate_workforce_postcondition(
        provider,
        subject_binding=subject_binding,
        owner=owner,
        subject=subject,
    )
    return {
        "schema_version": 1,
        "cell_id": "phase2_cross_cycle_endgame_query_action_postcondition",
        "span_id": SPAN_ID,
        "handler": HANDLER,
        "producer_key": PRODUCER_KEY,
        "result": "GREEN",
        "readiness": "static-ready-live-pending",
        "fixture_evidence_is_live": False,
        "action_ack_is_business_postcondition": False,
        "provider_observed_postcondition": True,
        "source_checkpoint_restore": dict(restore),
        "source_event_context": dict(source_context),
        "source_action_ack": dict(ack),
        "completion_transition": completion,
        "result_event_context": result_context,
        "result_event_visible": True,
        "subject_transition_receipt": transition,
        "subject_provider_response": provider,
        "postcondition": postcondition,
    }


__all__ = [
    "CompletionExecutor",
    "CrossCycleEndgameCellError",
    "EndgameOwnerService",
    "EndgameResultBinding",
    "EndgameSubjectProofSession",
    "EndgameSubjectService",
    "EndgameVisibleBinding",
    "HANDLER",
    "M360_REQUIRED_ROUTE",
    "PRODUCER_KEY",
    "QUERY_EVENT_CAPABILITY",
    "RESULT_EVENT",
    "SELECT_EVENT_OPTION_CAPABILITY",
    "SOURCE_EVENT",
    "SOURCE_OPTION_NUMBER",
    "SPAN_ID",
    "SubjectSessionFactory",
    "WORKFORCE_QUERY_CAPABILITY",
    "inspect_cross_cycle_endgame_source",
    "run_cross_cycle_endgame_action_cell",
]
