#!/usr/bin/env python3
"""MCP-first Workforce #360 action and received-self postcondition helper.

The product deliberately exposes two different player bindings:

* ``zg361we.360`` is selected by the player who owns the AL case; and
* the Workforce snapshot v1 provider reads the played character as the case
  subject and equality-filters the owner supplied by the caller.

Consequently an option ACK is never treated as a business receipt.  The
owner-side action and the subject-side proof are separate public functions.
The runner may bridge them with a real save/character/session transition, but
this module will not invent such a transition or use OCR/coordinates.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import time
from typing import Callable, Literal, Protocol


M360_EVENT_DEFINITION_KEY = "zg361we.360"
M361_EVENT_DEFINITION_KEY = "zg361we.361"
WORKFORCE_CASE_KIND = "zhongguo.workforce-collective"

Route = Literal["A", "B", "C"]
ROUTE_NUMBER: dict[Route, int] = {"A": 1, "B": 2, "C": 3}
ROUTE_PHASE: dict[Route, str] = {
    "A": "route_a_exception",
    "B": "route_b_forced",
    "C": "route_c_debt",
}


class WorkforceActionCellError(RuntimeError):
    """The MCP action cell observed a malformed or contradictory product fact."""


class WorkforceActionCellBlocked(WorkforceActionCellError):
    """The product/runner has not supplied a required reachable transition."""


class _WorkforceNotMature(WorkforceActionCellBlocked):
    """A coherent product lifecycle has not reached the requested fact yet."""


class WorkforceService(Protocol):
    """Narrow duck-typed surface supplied by ``GameplayBridgeService``."""

    def snapshot(self) -> dict[str, object]: ...

    def query_current_event_window_context_v1(
        self, event_instance_id: int, *, expected_revision: int
    ) -> dict[str, object]: ...

    def select_event_option(
        self,
        option_number: int,
        *,
        event_instance_id: int | None = None,
        expected_revision: int | None = None,
    ) -> dict[str, object]: ...

    def query_zhongguo_workforce_collective_snapshot_v1(
        self,
        request_nonce: str,
        *,
        expected_revision: int,
        owner_character_id: int,
    ) -> dict[str, object]: ...

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]: ...


@dataclass(frozen=True)
class M360ActionBinding:
    route: Route
    owner_character_id: int
    subject_character_id: int
    event_instance_id: int
    option_number: int
    date_raw: int
    pre_action_revision: int


def _positive_int(value: object, label: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 1 <= value <= 2**31 - 1
    ):
        raise WorkforceActionCellError(f"{label} is not a positive CharacterID")
    return value


def _integer(value: object, label: str, *, minimum: int = -(2**63)) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise WorkforceActionCellError(f"{label} is not a valid integer")
    return value


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise WorkforceActionCellError(message)


def _write_json(path: Path | None, payload: dict[str, object]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _snapshot_binding(
    service: WorkforceService, *, label: str
) -> tuple[dict[str, object], int, int, int]:
    snapshot = service.snapshot()
    if not isinstance(snapshot, dict):
        raise WorkforceActionCellError(f"{label} snapshot is not an object")
    _require(snapshot.get("paused") is True, f"{label} is not paused")
    _require(snapshot.get("map_ready") is True, f"{label} is not map-ready")
    revision = _integer(snapshot.get("revision"), f"{label}.revision", minimum=0)
    date_raw = _integer(snapshot.get("date_raw"), f"{label}.date_raw")
    played = snapshot.get("played_character")
    _require(isinstance(played, dict), f"{label} lacks played_character")
    assert isinstance(played, dict)
    player = _positive_int(
        played.get("character_id"), f"{label}.played_character.character_id"
    )
    return snapshot, revision, date_raw, player


def _active_event_id(snapshot: dict[str, object]) -> int | None:
    active = snapshot.get("active_event")
    if active is None:
        return None
    if not isinstance(active, dict):
        raise WorkforceActionCellError("active_event is not an object")
    return _positive_int(active.get("instance_id"), "active_event.instance_id")


def _event_context(
    service: WorkforceService,
    snapshot: dict[str, object],
    *,
    expected_definition: str,
) -> dict[str, object]:
    event_id = _active_event_id(snapshot)
    if event_id is None:
        raise WorkforceActionCellBlocked(
            f"current paused frame has no {expected_definition} event"
        )
    revision = _integer(snapshot.get("revision"), "event snapshot revision", minimum=0)
    response = service.query_current_event_window_context_v1(
        event_id, expected_revision=revision
    )
    if not isinstance(response, dict):
        raise WorkforceActionCellError("event-window query returned a non-object")
    context = response.get("current_event_window_context")
    readiness = context.get("readiness") if isinstance(context, dict) else None
    _require(
        response.get("status") == "available"
        and isinstance(context, dict)
        and isinstance(readiness, dict)
        and readiness.get("event_definition_identity_ready") is True
        and readiness.get("root_scope_ready") is True
        and readiness.get("saved_scopes_ready") is True
        and readiness.get("option_presentation_ready") is True,
        "event-window query is not identity/presentation ready",
    )
    assert isinstance(context, dict)
    _require(
        context.get("event_definition_key") == expected_definition,
        "unexpected event definition: expected "
        f"{expected_definition}, observed {context.get('event_definition_key')}",
    )
    return context


def _event_context_allowlist(
    service: WorkforceService,
    snapshot: dict[str, object],
    *,
    expected_definitions: tuple[str, ...],
) -> dict[str, object]:
    """Resolve one event while preserving an explicit definition allowlist.

    The product default remains the single ``zg361we.361`` successor.  A
    dedicated acceptance fixture may instead put its typed switch-back card
    immediately behind #360.  Callers must opt into that exact key; an empty,
    duplicate or malformed allowlist is rejected before querying CK3.
    """

    if (
        not expected_definitions
        or any(
            not isinstance(value, str) or not value
            for value in expected_definitions
        )
        or len(set(expected_definitions)) != len(expected_definitions)
    ):
        raise ValueError("post-ACK event definition allowlist is invalid")
    event_id = _active_event_id(snapshot)
    if event_id is None:
        raise WorkforceActionCellBlocked(
            "current paused frame has no allowlisted post-ACK event"
        )
    revision = _integer(
        snapshot.get("revision"), "event snapshot revision", minimum=0
    )
    response = service.query_current_event_window_context_v1(
        event_id, expected_revision=revision
    )
    if not isinstance(response, dict):
        raise WorkforceActionCellError("event-window query returned a non-object")
    context = response.get("current_event_window_context")
    readiness = context.get("readiness") if isinstance(context, dict) else None
    _require(
        response.get("status") == "available"
        and isinstance(context, dict)
        and isinstance(readiness, dict)
        and readiness.get("event_definition_identity_ready") is True
        and readiness.get("root_scope_ready") is True
        and readiness.get("saved_scopes_ready") is True
        and readiness.get("option_presentation_ready") is True,
        "event-window query is not identity/presentation ready",
    )
    assert isinstance(context, dict)
    observed = context.get("event_definition_key")
    _require(
        observed in expected_definitions,
        "unexpected post-ACK event definition: expected one of "
        f"{list(expected_definitions)}, observed {observed}",
    )
    return context


def _scope_character_id(scope: object, label: str) -> int:
    _require(isinstance(scope, dict), f"{label} is not a scope object")
    assert isinstance(scope, dict)
    identity = scope.get("typed_identity")
    _require(isinstance(identity, dict), f"{label} lacks typed_identity")
    assert isinstance(identity, dict)
    _require(
        identity.get("status") == "available"
        and identity.get("kind") == "character",
        f"{label} is not a typed character scope",
    )
    return _positive_int(identity.get("character_id"), f"{label}.character_id")


def _saved_character_id(context: dict[str, object], name: str) -> int:
    saved = context.get("saved_scopes")
    _require(isinstance(saved, list), "event context saved_scopes is not a list")
    matches = [
        row
        for row in saved
        if isinstance(row, dict) and row.get("name") == name
    ]
    _require(
        len(matches) == 1,
        f"event context does not contain exactly one saved scope {name}",
    )
    return _scope_character_id(matches[0].get("scope"), f"saved scope {name}")


def select_typed_fixture_player_transition(
    service: WorkforceService,
    *,
    expected_event_definition_key: str,
    expected_player_before: int,
    expected_player_after: int,
    owner_character_id: int,
    subject_character_id: int,
    owner_scope_name: str,
    subject_scope_name: str,
    evidence_path: Path | None = None,
    settle_polls: int = 40,
    poll_interval_s: float = 0.05,
) -> dict[str, object]:
    """Select one typed acceptance-fixture card and prove the native rebind.

    The option ACK proves only submission.  Success requires a later paused
    semantic snapshot whose played ``CharacterID`` equals the requested target
    while the date remains frozen.  The event root and its two named saved
    scopes independently bind the exact owner/subject pair, so this helper
    cannot become a caller-reported ``set_player_character`` shortcut.
    """

    if not isinstance(expected_event_definition_key, str) or not (
        expected_event_definition_key
    ):
        raise ValueError("fixture transition event definition is invalid")
    before_player = _positive_int(
        expected_player_before, "expected_player_before"
    )
    after_player = _positive_int(
        expected_player_after, "expected_player_after"
    )
    owner = _positive_int(owner_character_id, "owner_character_id")
    subject = _positive_int(subject_character_id, "subject_character_id")
    if owner == subject or before_player == after_player:
        raise ValueError("fixture transition requires two distinct characters")
    if {before_player, after_player} != {owner, subject}:
        raise ValueError("fixture transition endpoints must be owner/subject")
    if (
        not isinstance(owner_scope_name, str)
        or not owner_scope_name
        or not isinstance(subject_scope_name, str)
        or not subject_scope_name
        or owner_scope_name == subject_scope_name
    ):
        raise ValueError("fixture transition saved-scope names are invalid")
    if settle_polls < 0 or poll_interval_s < 0:
        raise ValueError("fixture transition settle timing is invalid")

    evidence: dict[str, object] = {
        "schema_version": 1,
        "result": "RED",
        "stage": "typed_fixture_player_transition",
        "mcp_only": True,
        "ocr_used": False,
        "coordinates_used": False,
        "console_used": False,
        "test_decision_used": False,
        "expected_event_definition_key": expected_event_definition_key,
        "owner_character_id": owner,
        "subject_character_id": subject,
        "expected_player_before": before_player,
        "expected_player_after": after_player,
        "selection_expected_revision": None,
        "event_context": None,
        "selection_submission": None,
        "post_submission_snapshots": [],
        "native_played_character_postcondition": None,
        "ack_used_as_identity_postcondition": False,
        "failure_reason": None,
    }
    _write_json(evidence_path, evidence)
    try:
        snapshot, revision, date_raw, played = _snapshot_binding(
            service, label="fixture transition precondition"
        )
        _require(
            played == before_player,
            "fixture transition started from the wrong played CharacterID",
        )
        event_id = _active_event_id(snapshot)
        if event_id is None:
            raise WorkforceActionCellBlocked(
                "fixture transition has no active typed event"
            )
        context = _event_context(
            service,
            snapshot,
            expected_definition=expected_event_definition_key,
        )
        evidence["event_context"] = context
        root = _scope_character_id(
            context.get("root_scope"), "fixture transition root scope"
        )
        observed_owner = _saved_character_id(context, owner_scope_name)
        observed_subject = _saved_character_id(context, subject_scope_name)
        _require(
            root == before_player,
            "fixture transition root does not equal the played character",
        )
        _require(
            observed_owner == owner and observed_subject == subject,
            "fixture transition saved owner/subject scopes drifted",
        )
        options = context.get("options")
        _require(
            isinstance(options, list)
            and len(options) == 1
            and isinstance(options[0], dict)
            and options[0].get("shown") is True
            and options[0].get("enabled") is True
            and options[0].get("native_option_index") == 0,
            "fixture transition must expose exactly one enabled native option",
        )
        submission = service.select_event_option(
            1,
            event_instance_id=event_id,
            expected_revision=revision,
        )
        evidence["selection_expected_revision"] = revision
        evidence["selection_submission"] = submission
        _require(
            isinstance(submission, dict)
            and submission.get("accepted") is True
            and submission.get("status") == "submitted",
            "fixture transition option was not acknowledged",
        )

        observations = evidence["post_submission_snapshots"]
        assert isinstance(observations, list)
        for poll in range(settle_polls + 1):
            after, after_revision, after_date, after_played = _snapshot_binding(
                service, label="fixture transition post-submission"
            )
            row = {
                "poll": poll,
                "revision": after_revision,
                "date_raw": after_date,
                "played_character_id": after_played,
                "active_event_instance_id": _active_event_id(after),
            }
            observations.append(row)
            _require(
                after_date == date_raw,
                "fixture transition advanced the frozen game date",
            )
            if after_played == after_player:
                _require(
                    after_revision > revision,
                    "fixture transition changed played CharacterID without "
                    "advancing the revision bound to its option submission",
                )
                evidence["native_played_character_postcondition"] = row
                evidence["result"] = "GREEN"
                _write_json(evidence_path, evidence)
                return evidence
            _require(
                after_played == before_player,
                "fixture transition reached an unexpected played CharacterID",
            )
            if poll_interval_s:
                time.sleep(poll_interval_s)
        raise WorkforceActionCellBlocked(
            "fixture transition ACK did not produce the expected native "
            f"played CharacterID {after_player}"
        )
    except BaseException as error:
        evidence["failure_reason"] = f"{type(error).__name__}: {error}"
        _write_json(evidence_path, evidence)
        raise


def submit_m360_route_action(
    service: WorkforceService,
    *,
    route: Route,
    evidence_path: Path | None = None,
    settle_polls: int = 20,
    poll_interval_s: float = 0.05,
    post_ack_event_definition_allowlist: tuple[str, ...] = (
        M361_EVENT_DEFINITION_KEY,
    ),
) -> dict[str, object]:
    """Submit exactly one #360 option and return ACK evidence only.

    A successful return proves the native option submission was acknowledged.
    It does *not* claim that the M360 operation receipt or route object exists.
    Those facts are proved separately by :func:`prove_m360_postcondition`.
    """

    if route not in ROUTE_NUMBER:
        raise ValueError("route must be A, B or C")
    if settle_polls < 0 or poll_interval_s < 0:
        raise ValueError("settle timing must be non-negative")
    if (
        not post_ack_event_definition_allowlist
        or any(
            not isinstance(value, str) or not value
            for value in post_ack_event_definition_allowlist
        )
        or len(set(post_ack_event_definition_allowlist))
        != len(post_ack_event_definition_allowlist)
    ):
        raise ValueError("post-ACK event definition allowlist is invalid")
    evidence: dict[str, object] = {
        "schema_version": 1,
        "result": "RED",
        "stage": "owner_side_m360_option_ack",
        "route": route,
        "mcp_only": True,
        "ocr_used": False,
        "coordinates_used": False,
        "business_receipt_claimed": False,
        "binding": None,
        "event_context": None,
        "action_ack": None,
        "post_ack_event": None,
        "post_ack_event_definition_allowlist": list(
            post_ack_event_definition_allowlist
        ),
        "failure_reason": None,
    }
    _write_json(evidence_path, evidence)
    try:
        snapshot, revision, date_raw, player = _snapshot_binding(
            service, label="M360 action frame"
        )
        event_id = _active_event_id(snapshot)
        if event_id is None:
            raise WorkforceActionCellBlocked(
                "M360 action frame has no active product event"
            )
        context = _event_context(
            service, snapshot, expected_definition=M360_EVENT_DEFINITION_KEY
        )
        evidence["event_context"] = context
        root = _scope_character_id(context.get("root_scope"), "M360 root scope")
        owner = _saved_character_id(context, "zg361_we_al_owner")
        subject = _saved_character_id(context, "zg361_we_al_subject")
        _require(root == player == owner, "M360 root/player/owner binding disagrees")
        _require(subject != owner, "M360 owner and subject must be distinct")

        options = context.get("options")
        _require(isinstance(options, list), "M360 options are not a list")
        assert isinstance(options, list)
        _require(len(options) == 3, "M360 must expose exactly A/B/C")
        native_indices = [
            row.get("native_option_index")
            for row in options
            if isinstance(row, dict)
            and row.get("shown") is True
            and row.get("enabled") is True
        ]
        _require(
            native_indices == [0, 1, 2],
            "M360 A/B/C native option order/readiness changed",
        )
        option_number = ROUTE_NUMBER[route]
        binding = M360ActionBinding(
            route=route,
            owner_character_id=owner,
            subject_character_id=subject,
            event_instance_id=event_id,
            option_number=option_number,
            date_raw=date_raw,
            pre_action_revision=revision,
        )
        evidence["binding"] = binding.__dict__
        ack = service.select_event_option(
            option_number,
            event_instance_id=event_id,
            expected_revision=revision,
        )
        evidence["action_ack"] = ack
        _require(
            isinstance(ack, dict)
            and ack.get("accepted") is True
            and ack.get("status") == "submitted",
            "M360 option command was not acknowledged",
        )

        # The immediate #361 event is useful orchestration evidence, but it is
        # intentionally not a substitute for the subject-side M360 receipt.
        observations: list[dict[str, object]] = []
        for poll in range(settle_polls + 1):
            after, _, after_date, after_player = _snapshot_binding(
                service, label="M360 post-ACK frame"
            )
            _require(after_date == date_raw, "game date advanced during M360 ACK")
            _require(after_player == owner, "played owner changed during M360 ACK")
            active_id = _active_event_id(after)
            row: dict[str, object] = {
                "poll": poll,
                "revision": after.get("revision"),
                "date_raw": after_date,
                "active_event_instance_id": active_id,
                "event_definition_key": None,
            }
            if active_id is not None and active_id != event_id:
                next_context = _event_context_allowlist(
                    service,
                    after,
                    expected_definitions=(
                        post_ack_event_definition_allowlist
                    ),
                )
                row["event_definition_key"] = next_context.get(
                    "event_definition_key"
                )
                observations.append(row)
                break
            observations.append(row)
            if poll_interval_s:
                time.sleep(poll_interval_s)
        evidence["post_ack_event"] = {
            "expected_definition": (
                post_ack_event_definition_allowlist[0]
                if len(post_ack_event_definition_allowlist) == 1
                else None
            ),
            "expected_definitions": list(
                post_ack_event_definition_allowlist
            ),
            "observed": bool(
                observations
                and observations[-1].get("event_definition_key")
                in post_ack_event_definition_allowlist
            ),
            "m361_observed": bool(
                observations
                and observations[-1].get("event_definition_key")
                == M361_EVENT_DEFINITION_KEY
            ),
            "observations": observations,
            "business_receipt_claimed": False,
        }
        evidence["result"] = "ACKED"
        _write_json(evidence_path, evidence)
        return evidence
    except BaseException as error:
        evidence["failure_reason"] = f"{type(error).__name__}: {error}"
        _write_json(evidence_path, evidence)
        raise


def _typed_value(group: object, key: str, label: str) -> object:
    _require(isinstance(group, dict), f"{label} is not an object")
    assert isinstance(group, dict)
    field = group.get(key)
    _require(isinstance(field, dict), f"{label}.{key} is not typed")
    assert isinstance(field, dict)
    _require(
        field.get("status") == "available"
        and field.get("unavailable_reason") is None,
        f"{label}.{key} is unavailable",
    )
    return field.get("value")


def _typed_unavailable(group: object, key: str, reason: str, label: str) -> bool:
    if not isinstance(group, dict):
        return False
    field = group.get(key)
    return (
        isinstance(field, dict)
        and field.get("status") == "unavailable"
        and field.get("value") is None
        and field.get("unavailable_reason") == reason
    )


def _assert_identity_group(
    group: object,
    *,
    owner: int,
    subject: int,
    cycle: int,
    case: int,
    state: int,
    label: str,
) -> None:
    _require(_typed_value(group, "owner_character_id", label) == owner, f"{label} owner drifted")
    _require(_typed_value(group, "subject_character_id", label) == subject, f"{label} subject drifted")
    _require(_typed_value(group, "cycle_serial", label) == cycle, f"{label} cycle drifted")
    _require(_typed_value(group, "case_serial", label) == case, f"{label} case drifted")
    _require(_typed_value(group, "state", label) == state, f"{label} state drifted")


def _assert_m360_product(
    response: dict[str, object],
    *,
    route: Route,
    owner: int,
    subject: int,
) -> dict[str, object]:
    if response.get("status") != "available":
        raise _WorkforceNotMature(
            "Workforce case is not available yet: "
            f"{response.get('unavailable_reason') or response.get('status')}"
        )
    _require(response.get("case_kind") == WORKFORCE_CASE_KIND, "Workforce case kind drifted")
    _require(response.get("player_character_id") == subject, "provider is not bound to played subject")
    _require(response.get("subject_character_id") == subject, "provider subject drifted")
    _require(response.get("requested_owner_character_id") == owner, "provider owner filter drifted")

    al_case = response.get("al_case")
    cycle = _integer(_typed_value(al_case, "cycle_serial", "al_case"), "al_case.cycle", minimum=1)
    case = _positive_int(_typed_value(al_case, "case_serial", "al_case"), "al_case.case")
    _assert_identity_group(
        al_case,
        owner=owner,
        subject=subject,
        cycle=cycle,
        case=case,
        state=5,
        label="al_case",
    )
    collective = response.get("collective")
    _require(isinstance(collective, dict), "collective is not an object")
    assert isinstance(collective, dict)
    if collective.get("phase") == "not_reached":
        raise _WorkforceNotMature("M360 business receipt has not been recorded yet")

    receipt = response.get("m360_receipt")
    _assert_identity_group(
        receipt,
        owner=owner,
        subject=subject,
        cycle=cycle,
        case=case,
        state=4,
        label="m360_receipt",
    )
    _require(
        _typed_value(receipt, "choice", "m360_receipt") == ROUTE_NUMBER[route],
        "M360 business receipt choice disagrees with the acknowledged route",
    )

    _require(collective.get("phase") == ROUTE_PHASE[route], "M360 route phase drifted")
    cohorts = response.get("cohorts")
    _require(isinstance(cohorts, list) and len(cohorts) == 3, "M360 must publish three cohort slots")
    assert isinstance(cohorts, list)
    if route in {"A", "B"}:
        _assert_identity_group(
            collective,
            owner=owner,
            subject=subject,
            cycle=cycle,
            case=case,
            state=4,
            label="collective",
        )
        _require(_typed_value(collective, "route", "collective") == ROUTE_NUMBER[route], "collective route drifted")
        for key, expected in (
            ("submission_active", False),
            ("submission_sealed", True),
            ("submission_consumed", True),
            ("settled", True),
            ("cohort_count", 3),
        ):
            _require(_typed_value(collective, key, "collective") == expected, f"collective {key} drifted")
        cohort_ids: list[int] = []
        managers: list[int] = []
        totals = {key: 0 for key in ("member_count", "quota", "forced_count", "exception_count", "manager_cost")}
        for index, cohort in enumerate(cohorts):
            label = f"cohorts[{index}]"
            cohort_ids.append(_positive_int(_typed_value(cohort, "cohort_id", label), f"{label}.cohort_id"))
            managers.append(_positive_int(_typed_value(cohort, "manager_character_id", label), f"{label}.manager"))
            quota = _integer(_typed_value(cohort, "quota", label), f"{label}.quota", minimum=0)
            member_count = _integer(_typed_value(cohort, "member_count", label), f"{label}.members", minimum=0)
            _require(member_count >= quota, f"{label} quota exceeds members")
            _require(_typed_value(cohort, "partition_verified", label) is True, f"{label} partition is not verified")
            expected_values = (
                (0, quota, quota, True)
                if route == "A"
                else (quota, 0, 0, False)
            )
            observed_values = (
                _typed_value(cohort, "forced_count", label),
                _typed_value(cohort, "exception_count", label),
                _typed_value(cohort, "manager_cost", label),
                _typed_value(cohort, "approval_verified", label),
            )
            _require(observed_values == expected_values, f"{label} route conservation drifted")
            for key in totals:
                totals[key] += _integer(_typed_value(cohort, key, label), f"{label}.{key}", minimum=0)
        _require(len(set(cohort_ids)) == 3 and len(set(managers)) == 3, "cohort/manager identities are not distinct")
        aggregate_fields = {
            "member_count": "total_members",
            "quota": "total_quota",
            "forced_count": "forced_count",
            "exception_count": "exception_count",
            "manager_cost": "manager_cost_total",
        }
        for cohort_key, collective_key in aggregate_fields.items():
            _require(
                _typed_value(collective, collective_key, "collective")
                == totals[cohort_key],
                f"collective {collective_key} does not conserve cohort totals",
            )
        _require(1 <= totals["quota"] <= 6, "collective quota is outside 1..6")
    else:
        for key in (
            "submission_active", "submission_sealed", "submission_consumed",
            "owner_character_id", "subject_character_id", "cycle_serial",
            "case_serial", "state", "collective_case_serial",
            "submitted_cycle_serial", "cohort_count", "settlement_id",
            "settlement_hash", "settled", "route", "total_members",
            "total_quota", "forced_count", "exception_count",
            "manager_cost_total",
        ):
            _require(_typed_unavailable(collective, key, "not_applicable", "collective"), f"route C materialized collective.{key}")
        for index, cohort in enumerate(cohorts):
            _require(
                isinstance(cohort, dict)
                and all(
                    isinstance(field, dict)
                    and field.get("status") == "unavailable"
                    and field.get("unavailable_reason") == "not_applicable"
                    for field in cohort.values()
                ),
                f"route C materialized cohorts[{index}]",
            )
        debt = response.get("route_c_debt")
        _assert_identity_group(
            debt,
            owner=owner,
            subject=subject,
            cycle=cycle,
            case=case,
            state=4,
            label="route_c_debt",
        )
        open_value = _typed_value(debt, "open", "route_c_debt")
        consumed_value = _typed_value(debt, "consumed", "route_c_debt")
        _require(
            (open_value, consumed_value) in {(True, False), (False, True)},
            "route C debt lifecycle is contradictory",
        )
        _require(
            _typed_value(debt, "due_cycle_serial", "route_c_debt") == cycle + 1,
            "route C debt is not due next cycle",
        )

    history = response.get("history")
    _require(isinstance(history, dict), "history is not an object")
    assert isinstance(history, dict)
    if history.get("status") in {"empty", "partial"}:
        raise _WorkforceNotMature(
            "rolling Workforce history has not matured to three cycles"
        )
    _require(
        history.get("status") == "three_cycle"
        and history.get("effective_count") == 3
        and _typed_value(history, "count", "history") == 3,
        "M360 receipt is not backed by a mature three-cycle ledger",
    )
    slots = history.get("slots")
    _require(isinstance(slots, list) and len(slots) == 3, "history does not expose three slots")
    assert isinstance(slots, list)
    slot_cycles: list[int] = []
    for index, slot in enumerate(slots):
        label = f"history.slots[{index}]"
        _require(_typed_value(slot, "owner_character_id", label) == owner, f"{label} owner drifted")
        slot_cycles.append(_integer(_typed_value(slot, "cycle_serial", label), f"{label}.cycle", minimum=1))
        ids = [
            _positive_int(_typed_value(slot, f"m{number}_receipt_id", label), f"{label}.m{number}_id")
            for number in (357, 358, 359)
        ]
        hashes = [
            _positive_int(_typed_value(slot, f"m{number}_receipt_hash", label), f"{label}.m{number}_hash")
            for number in (357, 358, 359)
        ]
        _require(len(set(ids)) == 3 and len(set(hashes)) == 3, f"{label} receipt identities collide")
    _require(slot_cycles[0] < slot_cycles[1] < slot_cycles[2] == cycle, "history cycles are not ordered through the current case")

    charter = response.get("charter_gate")
    _require(isinstance(charter, dict), "charter_gate is not an object")
    assert isinstance(charter, dict)
    if charter.get("status") in {"not_eligible", "awaiting_gate"}:
        raise _WorkforceNotMature("#361 charter gate has not matured to ready")
    _require(charter.get("status") == "ready", "#361 charter gate is not ready after M360")
    _assert_identity_group(
        charter,
        owner=owner,
        subject=subject,
        cycle=cycle,
        case=case,
        state=5,
        label="charter_gate",
    )
    for key, expected in (
        ("evidence_count", 3),
        ("evidence_ready", True),
        ("evidence_consumed", False),
        ("adopted_cycle_serial", cycle),
        ("effective_cycle_serial", cycle + 1),
    ):
        _require(_typed_value(charter, key, "charter_gate") == expected, f"charter_gate {key} drifted")
    _positive_int(_typed_value(charter, "prepared_report_id", "charter_gate"), "charter_gate report")
    _positive_int(_typed_value(charter, "prepared_charter_id", "charter_gate"), "charter_gate charter")

    readiness = response.get("readiness")
    _require(isinstance(readiness, dict), "Workforce readiness is not an object")
    assert isinstance(readiness, dict)
    for key in (
        "m360_receipt_projection_ready", "collective_lifecycle_ready",
        "cohort_conservation_ready", "route_conservation_ready",
        "history_ledger_ready", "history_order_ready", "three_cycle_ready",
        "charter_gate_lifecycle_ready", "same_frame_ready", "ready",
    ):
        _require(readiness.get(key) is True, f"Workforce readiness {key} is false")
    return {
        "owner_character_id": owner,
        "subject_character_id": subject,
        "cycle_serial": cycle,
        "case_serial": case,
        "route": route,
        "route_phase": ROUTE_PHASE[route],
        "history_cycles": slot_cycles,
        "charter_status": "ready",
        "charter_effective_cycle": cycle + 1,
    }


def _bounded_timeline_step(
    service: WorkforceService,
    *,
    timeout_s: float,
    poll_interval_s: float,
) -> dict[str, object]:
    """Advance until one date change, then force a paused observation frame."""

    if timeout_s <= 0 or poll_interval_s < 0:
        raise ValueError("timeline timing is invalid")
    before, revision, date_raw, player = _snapshot_binding(
        service, label="bounded timeline pre-step"
    )
    if _active_event_id(before) is not None:
        raise WorkforceActionCellBlocked(
            "bounded Workforce maturation is blocked by an active event; "
            "the helper will not select an unrelated option"
        )
    submissions: list[dict[str, object]] = []
    if before.get("speed") != 1:
        submissions.append(
            {
                "step": "set-speed-1",
                "result": service.execute_step(
                    "set-speed-1", expected_revision=revision
                ),
            }
        )
        before, revision, _, observed_player = _snapshot_binding(
            service, label="bounded timeline speed-one frame"
        )
        _require(observed_player == player, "played character changed while arming speed one")
    submissions.append(
        {
            "step": "resume-map",
            "result": service.execute_step(
                "resume-map", expected_revision=revision
            ),
        }
    )
    deadline = time.monotonic() + timeout_s
    observations: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    while time.monotonic() < deadline:
        candidate = service.snapshot()
        if not isinstance(candidate, dict):
            raise WorkforceActionCellError("timeline snapshot is not an object")
        observations.append(
            {
                "revision": candidate.get("revision"),
                "date_raw": candidate.get("date_raw"),
                "paused": candidate.get("paused"),
                "active_event_instance_id": _active_event_id(candidate),
            }
        )
        candidate_date = candidate.get("date_raw")
        if isinstance(candidate_date, int) and not isinstance(candidate_date, bool) and candidate_date != date_raw:
            current = candidate
            break
        if poll_interval_s:
            time.sleep(poll_interval_s)
    if current is None:
        raise WorkforceActionCellBlocked("bounded timeline step did not advance the date")
    if current.get("paused") is not True:
        current_revision = _integer(current.get("revision"), "timeline current revision", minimum=0)
        submissions.append(
            {
                "step": "pause-map",
                "result": service.execute_step(
                    "pause-map", expected_revision=current_revision
                ),
            }
        )
    paused, _, paused_date, paused_player = _snapshot_binding(
        service, label="bounded timeline post-step"
    )
    _require(paused_player == player, "played character changed during bounded timeline step")
    _require(paused_date != date_raw, "bounded timeline post-step did not advance")
    return {
        "starting_date_raw": date_raw,
        "paused_date_raw": paused_date,
        "submissions": submissions,
        "observations": observations,
        "post_snapshot": paused,
    }


def prove_m360_postcondition(
    service: WorkforceService,
    *,
    route: Route,
    owner_character_id: int,
    subject_character_id: int,
    evidence_path: Path | None = None,
    settle_polls: int = 8,
    max_timeline_steps: int = 0,
    timeline_timeout_s: float = 10.0,
    poll_interval_s: float = 0.05,
) -> dict[str, object]:
    """Prove receipt + route object + three cycles + ready #361 gate.

    Every provider request is issued from a paused frame.  Optional timeline
    progress is bounded one observed date transition at a time; an unrelated
    active event is a blocker, never something this helper auto-clicks.
    """

    if route not in ROUTE_NUMBER:
        raise ValueError("route must be A, B or C")
    owner = _positive_int(owner_character_id, "owner_character_id")
    subject = _positive_int(subject_character_id, "subject_character_id")
    if owner == subject:
        raise ValueError("owner and subject must differ")
    if settle_polls < 0 or max_timeline_steps < 0 or poll_interval_s < 0:
        raise ValueError("postcondition wait bounds must be non-negative")
    evidence: dict[str, object] = {
        "schema_version": 1,
        "result": "RED",
        "stage": "subject_side_m360_business_postcondition",
        "route": route,
        "mcp_only": True,
        "ocr_used": False,
        "coordinates_used": False,
        "owner_character_id": owner,
        "subject_character_id": subject,
        "action_ack_used_as_receipt": False,
        "paused_queries": [],
        "timeline_steps": [],
        "business_receipt": None,
        "postcondition": None,
        "failure_reason": None,
    }
    _write_json(evidence_path, evidence)
    last_error = "no Workforce query was issued"
    try:
        for timeline_index in range(max_timeline_steps + 1):
            for settle_index in range(settle_polls + 1):
                snapshot, revision, date_raw, player = _snapshot_binding(
                    service, label="Workforce postcondition query frame"
                )
                if player != subject:
                    raise WorkforceActionCellBlocked(
                        "Workforce snapshot v1 is received-self: the postcondition "
                        f"must run while subject {subject} is played, observed {player}"
                    )
                nonce = f"zg361.p2.wf.m360.{route.lower()}.{timeline_index}.{settle_index}"
                response = service.query_zhongguo_workforce_collective_snapshot_v1(
                    nonce,
                    expected_revision=revision,
                    owner_character_id=owner,
                )
                row = {
                    "timeline_step": timeline_index,
                    "settle_poll": settle_index,
                    "revision": revision,
                    "date_raw": date_raw,
                    "paused": True,
                    "request_nonce": nonce,
                    "response": response,
                }
                queries = evidence["paused_queries"]
                assert isinstance(queries, list)
                queries.append(row)
                _write_json(evidence_path, evidence)
                try:
                    _require(isinstance(response, dict), "Workforce query returned a non-object")
                    assert isinstance(response, dict)
                    projection = _assert_m360_product(
                        response, route=route, owner=owner, subject=subject
                    )
                except _WorkforceNotMature as error:
                    last_error = str(error)
                    if settle_index < settle_polls:
                        if poll_interval_s:
                            time.sleep(poll_interval_s)
                        continue
                    break
                receipt = response.get("m360_receipt")
                evidence["business_receipt"] = receipt
                evidence["postcondition"] = projection
                evidence["result"] = "GREEN"
                _write_json(evidence_path, evidence)
                return evidence
            if timeline_index == max_timeline_steps:
                break
            timeline_step = _bounded_timeline_step(
                service,
                timeout_s=timeline_timeout_s,
                poll_interval_s=poll_interval_s,
            )
            timeline_steps = evidence["timeline_steps"]
            assert isinstance(timeline_steps, list)
            timeline_steps.append(timeline_step)
            _write_json(evidence_path, evidence)
        raise WorkforceActionCellBlocked(
            "M360 product postcondition did not mature within the configured "
            f"paused-query/timeline bound: {last_error}"
        )
    except BaseException as error:
        evidence["failure_reason"] = f"{type(error).__name__}: {error}"
        _write_json(evidence_path, evidence)
        raise


def run_m360_action_and_postcondition(
    owner_service: WorkforceService,
    *,
    route: Route,
    subject_service_factory: Callable[[M360ActionBinding], WorkforceService]
    | None,
    evidence_directory: Path,
    max_timeline_steps: int = 0,
    post_ack_event_definition_allowlist: tuple[str, ...] = (
        M361_EVENT_DEFINITION_KEY,
    ),
) -> dict[str, object]:
    """Join the two phases only through an explicit subject-session seam."""

    evidence_directory.mkdir(parents=True, exist_ok=True)
    matrix_path = evidence_directory / f"workforce_m360_route_{route.lower()}_gate.json"
    matrix: dict[str, object] = {
        "schema_version": 1,
        "result": "RED",
        "route": route,
        "mcp_only": True,
        "owner_action": None,
        "subject_postcondition": None,
        "identity_transition": None,
        "failure_reason": None,
    }
    _write_json(matrix_path, matrix)
    try:
        action = submit_m360_route_action(
            owner_service,
            route=route,
            evidence_path=evidence_directory
            / f"workforce_m360_route_{route.lower()}_action_ack.json",
            post_ack_event_definition_allowlist=(
                post_ack_event_definition_allowlist
            ),
        )
        matrix["owner_action"] = action
        binding_value = action.get("binding")
        _require(isinstance(binding_value, dict), "M360 ACK lacks its owner/subject binding")
        assert isinstance(binding_value, dict)
        binding = M360ActionBinding(
            route=route,
            owner_character_id=_positive_int(binding_value.get("owner_character_id"), "ACK owner"),
            subject_character_id=_positive_int(binding_value.get("subject_character_id"), "ACK subject"),
            event_instance_id=_positive_int(binding_value.get("event_instance_id"), "ACK event"),
            option_number=_integer(binding_value.get("option_number"), "ACK option", minimum=1),
            date_raw=_integer(binding_value.get("date_raw"), "ACK date"),
            pre_action_revision=_integer(binding_value.get("pre_action_revision"), "ACK revision", minimum=0),
        )
        if subject_service_factory is None:
            matrix["identity_transition"] = {
                "result": "BLOCKED",
                "reason": "received_self_provider_requires_subject_player_rebind",
                "owner_character_id": binding.owner_character_id,
                "subject_character_id": binding.subject_character_id,
                "required_runner_seam": (
                    "rebind a managed MCP session to the exact saved-scope "
                    "subject, then query Workforce snapshot v1"
                ),
            }
            raise WorkforceActionCellBlocked(
                "M360 option was ACKed, but Workforce snapshot v1 can prove the "
                "receipt only after an explicit owner-to-subject player rebind"
            )
        subject_service = subject_service_factory(binding)
        matrix["identity_transition"] = {
            "result": "SUPPLIED_BY_RUNNER",
            "owner_character_id": binding.owner_character_id,
            "subject_character_id": binding.subject_character_id,
        }
        postcondition = prove_m360_postcondition(
            subject_service,
            route=route,
            owner_character_id=binding.owner_character_id,
            subject_character_id=binding.subject_character_id,
            evidence_path=evidence_directory
            / f"workforce_m360_route_{route.lower()}_postcondition.json",
            max_timeline_steps=max_timeline_steps,
        )
        matrix["subject_postcondition"] = postcondition
        matrix["result"] = "GREEN"
        _write_json(matrix_path, matrix)
        return matrix
    except BaseException as error:
        matrix["failure_reason"] = f"{type(error).__name__}: {error}"
        _write_json(matrix_path, matrix)
        raise


__all__ = [
    "M360ActionBinding",
    "M360_EVENT_DEFINITION_KEY",
    "M361_EVENT_DEFINITION_KEY",
    "ROUTE_NUMBER",
    "ROUTE_PHASE",
    "WorkforceActionCellBlocked",
    "WorkforceActionCellError",
    "prove_m360_postcondition",
    "run_m360_action_and_postcondition",
    "select_typed_fixture_player_transition",
    "submit_m360_route_action",
]
