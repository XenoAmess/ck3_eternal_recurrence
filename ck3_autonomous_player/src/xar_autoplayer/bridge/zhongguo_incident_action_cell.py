"""MCP-first gameplay cell for the ZhongGuo Incident X/Y/Z pipeline.

The cell deliberately starts from the received-self ``zg361.50`` notice.  Its
first authored option posts the real result-delivery receipt, which is the
product hook that wakes the central phase-two pipeline.  The later
``zg361.4`` presentation is also closed with its first authored option.  No
other event is guessed or auto-resolved.

An option command acknowledgement is never a result.  Each selection must
materialize as the old event instance disappearing, and the cell is GREEN only
after the received-self Incident provider publishes exact X, Y and Z terminal
tuples plus their KPI disposition on one paused snapshot.  The three profiles
own immutable probe receipts, so the matrix must contain both an exact N/A and
a positive incident instead of pretending one shared mutable probe can prove
both.  A wrong-owner query is then required to return the typed ACL denial.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import time
from typing import Callable, Final, Protocol

from .event_window_context_contract import (
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY,
)
from .zhongguo_incident_snapshot_contract import (
    QUERY_ZHONGGUO_INCIDENT_SNAPSHOT_V1_CAPABILITY,
    ZHONGGUO_INCIDENT_KIND_V1,
)


INCIDENT_ACTION_CELL_ID: Final = (
    "incident_xyz_gameplay_action_and_postcondition_matrix"
)
INCIDENT_PROFILES: Final = ("x", "y", "z")
INCIDENT_TRIGGER_EVENT_DEFINITION_KEY: Final = "zg361.50"
INCIDENT_TRIGGER_OPTION_NUMBER: Final = 1
INCIDENT_RESULT_EVENT_DEFINITION_KEY: Final = "zg361.4"
INCIDENT_RESULT_OPTION_NUMBER: Final = 1
NOTICE_OWNER_SCOPE_NAME: Final = "zg361_notice_prompt_owner"
SELECT_EVENT_OPTION_CAPABILITY: Final = "game.command.select-event-option-N"
_EVENT_ROUTE: Final = {
    INCIDENT_TRIGGER_EVENT_DEFINITION_KEY: INCIDENT_TRIGGER_OPTION_NUMBER,
    INCIDENT_RESULT_EVENT_DEFINITION_KEY: INCIDENT_RESULT_OPTION_NUMBER,
}
_PROFILE_TERMINAL_STATES: Final = {"x": 8, "y": 6, "z": 6}
_WAITABLE_PROVIDER_REASONS: Final = {"incident_not_found"}


class IncidentActionService(Protocol):
    """Narrow service surface used by the reusable action cell."""

    def capabilities(self) -> dict[str, object]: ...

    def snapshot(self) -> dict[str, object]: ...

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]: ...

    def select_event_option(
        self,
        option_number: int,
        *,
        event_instance_id: int | None = None,
        expected_revision: int | None = None,
    ) -> dict[str, object]: ...

    def query_current_event_window_context_v1(
        self, event_instance_id: int, *, expected_revision: int
    ) -> dict[str, object]: ...

    def query_zhongguo_incident_snapshot_v1(
        self,
        request_nonce: str,
        *,
        expected_revision: int,
        owner_character_id: int,
        profile: str,
    ) -> dict[str, object]: ...


@dataclass(frozen=True)
class _Binding:
    snapshot_id: str
    revision: int
    native_revision: int
    date_raw: int
    player_character_id: int


class IncidentActionCellError(RuntimeError):
    """Fail-closed cell error carrying the complete partial evidence."""

    def __init__(self, reason: str, evidence: dict[str, object]) -> None:
        super().__init__(reason)
        self.reason = reason
        self.evidence = deepcopy(evidence)


def _positive_int(value: object, label: str, *, maximum: int) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 1 <= value <= maximum
    ):
        raise ValueError(f"{label} must be a positive integer in range")
    return value


def _nonnegative_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")
    return value


def _snapshot_binding(snapshot: object, *, expected_player: int | None) -> _Binding:
    if not isinstance(snapshot, dict):
        raise ValueError("snapshot must be an object")
    snapshot_id = snapshot.get("snapshot_id")
    revision = _nonnegative_int(snapshot.get("revision"), "snapshot revision")
    native_revision = _positive_int(
        snapshot.get("native_revision"),
        "snapshot native revision",
        maximum=2**64 - 1,
    )
    date_raw = snapshot.get("date_raw")
    if (
        isinstance(date_raw, bool)
        or not isinstance(date_raw, int)
        or not -(2**31) <= date_raw <= 2**31 - 1
    ):
        raise ValueError("snapshot date_raw must be a signed int32")
    if not isinstance(snapshot_id, str) or not snapshot_id:
        raise ValueError("snapshot_id must be non-empty")
    played = snapshot.get("played_character")
    if not isinstance(played, dict) or played.get("alive") is not True:
        raise ValueError("played character must be present and alive")
    player = _positive_int(
        played.get("character_id"),
        "played character ID",
        maximum=2**31 - 1,
    )
    if expected_player is not None and player != expected_player:
        raise ValueError("played character changed during Incident action cell")
    return _Binding(snapshot_id, revision, native_revision, date_raw, player)


def _active_event(snapshot: dict[str, object]) -> tuple[int, int] | None:
    event = snapshot.get("active_event")
    if event is None:
        return None
    if not isinstance(event, dict):
        raise ValueError("active_event must be an object or null")
    instance = _positive_int(
        event.get("instance_id"), "active event instance", maximum=2**31 - 1
    )
    count = _positive_int(
        event.get("option_count"), "active event option count", maximum=256
    )
    return instance, count


def _typed_character_id(scope: object, label: str) -> int:
    if not isinstance(scope, dict) or scope.get("status") != "available":
        raise ValueError(f"{label} is not a typed available scope")
    if scope.get("type_key") != "character":
        raise ValueError(f"{label} is not a Character scope")
    identity = scope.get("typed_identity")
    if not (
        isinstance(identity, dict)
        and identity.get("status") == "available"
        and identity.get("kind") == "character"
    ):
        raise ValueError(f"{label} lacks a typed Character identity")
    return _positive_int(
        identity.get("character_id"), f"{label} character ID", maximum=2**31 - 1
    )


def _typed_value(field: object, label: str) -> int:
    if not (
        isinstance(field, dict)
        and set(field) == {"status", "value", "unavailable_reason"}
        and field.get("status") == "available"
        and field.get("unavailable_reason") is None
    ):
        raise ValueError(f"{label} is not typed available")
    value = field.get("value")
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} is not an integer")
    return value


def _event_identity(
    service: IncidentActionService,
    snapshot: dict[str, object],
    *,
    expected_player: int,
    expected_owner: int,
) -> dict[str, object]:
    binding = _snapshot_binding(snapshot, expected_player=expected_player)
    if snapshot.get("paused") is not True:
        raise ValueError("event identity requires a paused snapshot")
    active = _active_event(snapshot)
    if active is None:
        raise ValueError("event identity requires an active event")
    instance_id, option_count = active
    response = service.query_current_event_window_context_v1(
        instance_id, expected_revision=binding.revision
    )
    context = (
        response.get("current_event_window_context")
        if isinstance(response, dict)
        else None
    )
    if not isinstance(context, dict) or context.get("status") != "available":
        raise ValueError("current-event context is not typed available")
    readiness = context.get("readiness")
    required_readiness = (
        "event_definition_identity_ready",
        "root_scope_ready",
        "saved_scopes_ready",
        "option_presentation_ready",
    )
    if not isinstance(readiness, dict) or any(
        readiness.get(key) is not True for key in required_readiness
    ):
        raise ValueError("current-event context is not identity/action ready")
    event_key = context.get("event_definition_key")
    if event_key not in _EVENT_ROUTE:
        raise ValueError(f"unexpected event definition: {event_key!r}")
    root_id = _typed_character_id(context.get("root_scope"), "event root")
    if root_id != expected_player:
        raise ValueError("event root is not the played reviewed subject")

    saved_scopes = context.get("saved_scopes")
    if not isinstance(saved_scopes, list):
        raise ValueError("current-event saved scopes are unavailable")
    if event_key == INCIDENT_TRIGGER_EVENT_DEFINITION_KEY:
        owner_rows = [
            row
            for row in saved_scopes
            if isinstance(row, dict) and row.get("name") == NOTICE_OWNER_SCOPE_NAME
        ]
        if len(owner_rows) != 1:
            raise ValueError("zg361.50 lacks one exact notice owner scope")
        owner_id = _typed_character_id(
            owner_rows[0].get("scope"), "zg361.50 notice owner"
        )
        if owner_id != expected_owner:
            raise ValueError("zg361.50 notice owner does not match the action owner")

    expected_option_number = _EVENT_ROUTE[event_key]
    expected_native_index = expected_option_number - 1
    options = context.get("options")
    if not isinstance(options, list) or len(options) != option_count:
        raise ValueError("current-event option presentation is incomplete")
    matches = [
        row
        for row in options
        if isinstance(row, dict)
        and row.get("native_option_index") == expected_native_index
    ]
    if len(matches) != 1:
        raise ValueError("fixed authored event option is not uniquely materialized")
    option = matches[0]
    if option.get("shown") is not True or option.get("enabled") is not True:
        raise ValueError("fixed authored event option is not shown and enabled")
    return {
        "event_definition_key": event_key,
        "event_instance_id": instance_id,
        "option_count": option_count,
        "option_number": expected_option_number,
        "native_option_index": expected_native_index,
        "resolved_name": option.get("resolved_name"),
        "snapshot_binding": binding.__dict__,
        "context": response,
    }


def _wrong_owner(owner: int, player: int) -> int:
    for candidate in (owner + 1, owner - 1, player + 1, player - 1, 1):
        if 1 <= candidate <= 2**31 - 1 and candidate not in {owner, player}:
            return candidate
    raise ValueError("cannot derive a distinct wrong-owner ACL probe")


def _profile_projection(
    response: object,
    *,
    profile: str,
    owner: int,
    player: int,
) -> dict[str, object] | None:
    if not isinstance(response, dict):
        raise ValueError(f"Incident {profile} response is not an object")
    if response.get("status") == "unavailable":
        reason = response.get("unavailable_reason")
        if reason in _WAITABLE_PROVIDER_REASONS:
            return None
        raise ValueError(f"Incident {profile} provider is unavailable: {reason}")
    readiness = response.get("readiness")
    if not (
        response.get("status") == "available"
        and response.get("case_kind") == ZHONGGUO_INCIDENT_KIND_V1
        and response.get("profile") == profile
        and response.get("subject_character_id") == player
        and response.get("requested_owner_character_id") == owner
        and response.get("unavailable_reason") is None
        and isinstance(readiness, dict)
        and readiness.get("ready") is True
    ):
        raise ValueError(f"Incident {profile} terminal is not fully ready")
    probe = response.get("probe")
    resources = response.get("resources")
    terminal = response.get("terminal")
    kpi = response.get("kpi")
    if not all(isinstance(group, dict) for group in (probe, resources, terminal, kpi)):
        raise ValueError(f"Incident {profile} response has a partial group")
    assert isinstance(probe, dict)
    assert isinstance(resources, dict)
    assert isinstance(terminal, dict)
    assert isinstance(kpi, dict)
    probe_values = {
        key: _typed_value(value, f"Incident {profile}.probe.{key}")
        for key, value in probe.items()
    }
    resource_values = {
        key: _typed_value(value, f"Incident {profile}.resources.{key}")
        for key, value in resources.items()
    }
    kind = terminal.get("kind")
    if kind == "na":
        if probe_values.get("result") != 0 or kpi.get("disposition") != "not_staged":
            raise ValueError(f"Incident {profile} N/A lacks exact no-KPI semantics")
        arm = terminal.get("na")
        if terminal.get("incident") is not None or not isinstance(arm, dict):
            raise ValueError(f"Incident {profile} N/A union is malformed")
        terminal_values = {
            key: _typed_value(value, f"Incident {profile}.terminal.na.{key}")
            for key, value in arm.items()
        }
    elif kind == "incident":
        if probe_values.get("result") != 1 or kpi.get("disposition") != "pending":
            raise ValueError(
                f"Incident {profile} terminal lacks a fresh pending KPI tuple"
            )
        arm = terminal.get("incident")
        if terminal.get("na") is not None or not isinstance(arm, dict):
            raise ValueError(f"Incident {profile} incident union is malformed")
        terminal_values = {
            key: _typed_value(
                value, f"Incident {profile}.terminal.incident.{key}"
            )
            for key, value in arm.items()
        }
        if (
            terminal_values.get("state") != _PROFILE_TERMINAL_STATES[profile]
            or terminal_values.get("kpi_staged") != 1
        ):
            raise ValueError(f"Incident {profile} terminal identity changed")
        pending = _typed_value(kpi.get("pending"), f"Incident {profile}.kpi.pending")
        consumed = _typed_value(
            kpi.get("consumed"), f"Incident {profile}.kpi.consumed"
        )
        if (pending, consumed) != (1, 0):
            raise ValueError(f"Incident {profile} KPI pending bits are invalid")
    else:
        raise ValueError(f"Incident {profile} has an invalid terminal kind")
    return {
        "profile": profile,
        "kind": kind,
        "probe": probe_values,
        "resources": resource_values,
        "terminal": terminal_values,
        "kpi_disposition": kpi.get("disposition"),
        "response": response,
    }


def _query_terminal_matrix(
    service: IncidentActionService,
    snapshot: dict[str, object],
    *,
    owner: int,
    player: int,
    nonce_serial: int,
) -> tuple[dict[str, dict[str, object]], dict[str, object]] | None:
    binding = _snapshot_binding(snapshot, expected_player=player)
    if snapshot.get("paused") is not True:
        raise ValueError("Incident terminal query requires a paused snapshot")
    profiles: dict[str, dict[str, object]] = {}
    raw: dict[str, object] = {}
    for profile in INCIDENT_PROFILES:
        nonce = f"zg361.iac.{nonce_serial:04d}.{profile}"
        response = service.query_zhongguo_incident_snapshot_v1(
            nonce,
            expected_revision=binding.revision,
            owner_character_id=owner,
            profile=profile,
        )
        raw[profile] = response
        projection = _profile_projection(
            response, profile=profile, owner=owner, player=player
        )
        if projection is None:
            return None
        profiles[profile] = projection

    kinds = {str(row["kind"]) for row in profiles.values()}
    if kinds != {"na", "incident"}:
        raise ValueError(
            "Incident X/Y/Z matrix must contain exact N/A and incident receipts"
        )
    for profile, row in profiles.items():
        probe = row["probe"]
        assert isinstance(probe, dict)
        if (
            probe.get("owner_character_id") != owner
            or probe.get("subject_character_id") != player
        ):
            raise ValueError(
                f"Incident {profile} profile receipt changed owner/subject binding"
            )
    return profiles, raw


def _query_acl_matrix(
    service: IncidentActionService,
    snapshot: dict[str, object],
    *,
    owner: int,
    player: int,
    nonce_serial: int,
) -> dict[str, object]:
    binding = _snapshot_binding(snapshot, expected_player=player)
    wrong = _wrong_owner(owner, player)
    responses: dict[str, object] = {}
    for profile in INCIDENT_PROFILES:
        nonce = f"zg361.iac.{nonce_serial:04d}.{profile}.acl"
        response = service.query_zhongguo_incident_snapshot_v1(
            nonce,
            expected_revision=binding.revision,
            owner_character_id=wrong,
            profile=profile,
        )
        if not isinstance(response, dict):
            raise ValueError(f"Incident {profile} ACL response is not an object")
        terminal = response.get("terminal")
        readiness = response.get("readiness")
        if not (
            response.get("status") == "unavailable"
            and response.get("unavailable_reason") == "owner_filter_mismatch"
            and isinstance(terminal, dict)
            and terminal.get("kind") == "unavailable"
            and terminal.get("na") is None
            and terminal.get("incident") is None
            and isinstance(readiness, dict)
            and readiness.get("ready") is False
        ):
            raise ValueError(f"Incident {profile} wrong-owner ACL leaked state")
        responses[profile] = response
    return {"wrong_owner_character_id": wrong, "responses": responses}


def run_incident_xyz_gameplay_action_cell(
    service: IncidentActionService,
    *,
    owner_character_id: int,
    timeout_seconds: float = 240.0,
    poll_interval_seconds: float = 0.10,
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, object]:
    """Execute the fixed Incident trigger route and prove X/Y/Z terminals.

    The function raises :class:`IncidentActionCellError` on every RED path.
    The exception carries a JSON-serializable evidence object so a runner can
    preserve the failed attempt without reimplementing the state machine.
    """

    owner = _positive_int(
        owner_character_id, "owner_character_id", maximum=2**31 - 1
    )
    if timeout_seconds <= 0 or poll_interval_seconds <= 0:
        raise ValueError("timeouts must be positive")
    started = monotonic()
    deadline = started + timeout_seconds
    evidence: dict[str, object] = {
        "schema_version": 1,
        "cell_id": INCIDENT_ACTION_CELL_ID,
        "result": "RED",
        "mcp_only": True,
        "ocr_used": False,
        "coordinates_used": False,
        "expected_owner_character_id": owner,
        "entry_event_definition_key": INCIDENT_TRIGGER_EVENT_DEFINITION_KEY,
        "entry_option_number": INCIDENT_TRIGGER_OPTION_NUMBER,
        "fixed_profiles": list(INCIDENT_PROFILES),
        "event_observations": [],
        "selection_submissions": [],
        "selection_materializations": [],
        "provider_polls": [],
        "terminal_profiles": None,
        "acl_profiles": None,
        "checks": {},
        "failure_reason": None,
    }

    def fail(reason: str) -> None:
        evidence["failure_reason"] = reason
        evidence["duration_seconds"] = round(monotonic() - started, 6)
        raise IncidentActionCellError(reason, evidence)

    try:
        capabilities = service.capabilities()
        bridge_capabilities = (
            capabilities.get("bridge_capabilities")
            if isinstance(capabilities, dict)
            else None
        )
        action_steps = (
            capabilities.get("action_steps") if isinstance(capabilities, dict) else None
        )
        required_capabilities = {
            QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY,
            QUERY_ZHONGGUO_INCIDENT_SNAPSHOT_V1_CAPABILITY,
            SELECT_EVENT_OPTION_CAPABILITY,
        }
        required_steps = {
            "pause-map",
            "resume-map",
            "set-speed-1",
        }
        if not (
            isinstance(bridge_capabilities, list)
            and required_capabilities.issubset(set(bridge_capabilities))
            and isinstance(action_steps, list)
            and required_steps.issubset(set(action_steps))
        ):
            fail("Incident action cell MCP capability profile is incomplete")
        checks = evidence["checks"]
        assert isinstance(checks, dict)
        checks["mcp_capability_profile_ready"] = True

        first_snapshot = service.snapshot()
        initial = _snapshot_binding(first_snapshot, expected_player=None)
        if initial.player_character_id == owner:
            fail("received-self Incident owner must differ from the player subject")
        player = initial.player_character_id
        initial_date = initial.date_raw
        entry_selected = False
        result_selected = False
        provider_nonce_serial = 0

        while monotonic() < deadline:
            snapshot = service.snapshot()
            binding = _snapshot_binding(snapshot, expected_player=player)
            if binding.date_raw < initial_date:
                fail("game date moved backwards during Incident action cell")
            active = _active_event(snapshot)

            if active is not None:
                instance_id, _option_count = active
                if snapshot.get("paused") is not True:
                    submission = service.execute_step(
                        "pause-map", expected_revision=binding.revision
                    )
                    pause_deadline = min(deadline, monotonic() + 5.0)
                    while monotonic() < pause_deadline:
                        snapshot = service.snapshot()
                        rebound = _snapshot_binding(snapshot, expected_player=player)
                        rebound_active = _active_event(snapshot)
                        if rebound_active is None or rebound_active[0] != instance_id:
                            fail("active event changed while materializing pause-map")
                        if snapshot.get("paused") is True:
                            binding = rebound
                            break
                        sleep(poll_interval_seconds)
                    else:
                        fail("pause-map ACK did not materialize on the active event")
                    event_observations = evidence["event_observations"]
                    assert isinstance(event_observations, list)
                    event_observations.append(
                        {"pause_submission": submission, "materialized": True}
                    )

                try:
                    identity = _event_identity(
                        service,
                        snapshot,
                        expected_player=player,
                        expected_owner=owner,
                    )
                except ValueError as error:
                    fail(str(error))
                event_key = str(identity["event_definition_key"])
                observations = evidence["event_observations"]
                assert isinstance(observations, list)
                observations.append(identity)
                if not entry_selected and event_key != INCIDENT_TRIGGER_EVENT_DEFINITION_KEY:
                    fail("Incident action cell did not start on the exact zg361.50 event")
                if entry_selected and event_key == INCIDENT_TRIGGER_EVENT_DEFINITION_KEY:
                    fail("zg361.50 reappeared after its bound selection")
                if result_selected and event_key == INCIDENT_RESULT_EVENT_DEFINITION_KEY:
                    fail("zg361.4 reappeared after its bound selection")

                option_number = int(identity["option_number"])
                selected_revision = int(
                    identity["snapshot_binding"]["revision"]  # type: ignore[index]
                )
                submission = service.select_event_option(
                    option_number,
                    event_instance_id=instance_id,
                    expected_revision=selected_revision,
                )
                submissions = evidence["selection_submissions"]
                assert isinstance(submissions, list)
                submissions.append(
                    {
                        "event_definition_key": event_key,
                        "event_instance_id": instance_id,
                        "option_number": option_number,
                        "ack": submission,
                    }
                )

                transition_deadline = min(deadline, monotonic() + 5.0)
                materialized: dict[str, object] | None = None
                while monotonic() < transition_deadline:
                    after = service.snapshot()
                    after_binding = _snapshot_binding(after, expected_player=player)
                    after_active = _active_event(after)
                    if after_active is None or after_active[0] != instance_id:
                        materialized = {
                            "old_event_instance_id": instance_id,
                            "new_event_instance_id": (
                                after_active[0] if after_active is not None else None
                            ),
                            "revision_before": selected_revision,
                            "revision_after": after_binding.revision,
                            "date_raw_after": after_binding.date_raw,
                        }
                        break
                    sleep(poll_interval_seconds)
                if materialized is None:
                    fail(
                        f"{event_key} option ACK did not materialize as an event transition"
                    )
                transitions = evidence["selection_materializations"]
                assert isinstance(transitions, list)
                transitions.append(materialized)
                if event_key == INCIDENT_TRIGGER_EVENT_DEFINITION_KEY:
                    entry_selected = True
                elif event_key == INCIDENT_RESULT_EVENT_DEFINITION_KEY:
                    result_selected = True
                continue

            if not entry_selected:
                # The seed may be paused shortly before the D+1 notice.  Wait
                # only through an event-free map; the first surfaced event is
                # still required to be the exact zg361.50 definition above.
                if snapshot.get("speed") != 1:
                    service.execute_step(
                        "set-speed-1", expected_revision=binding.revision
                    )
                    speed_deadline = min(deadline, monotonic() + 5.0)
                    while monotonic() < speed_deadline:
                        snapshot = service.snapshot()
                        binding = _snapshot_binding(
                            snapshot, expected_player=player
                        )
                        if _active_event(snapshot) is not None:
                            break
                        if snapshot.get("speed") == 1:
                            break
                        sleep(poll_interval_seconds)
                    if _active_event(snapshot) is not None:
                        continue
                    if snapshot.get("speed") != 1:
                        fail("set-speed-1 ACK did not materialize before zg361.50")
                if snapshot.get("paused") is True:
                    service.execute_step(
                        "resume-map", expected_revision=binding.revision
                    )
                    resume_deadline = min(deadline, monotonic() + 5.0)
                    while monotonic() < resume_deadline:
                        snapshot = service.snapshot()
                        _snapshot_binding(snapshot, expected_player=player)
                        if _active_event(snapshot) is not None:
                            break
                        if snapshot.get("paused") is False:
                            break
                        sleep(poll_interval_seconds)
                    if (
                        _active_event(snapshot) is None
                        and snapshot.get("paused") is not False
                    ):
                        fail("resume-map ACK did not materialize before zg361.50")
                sleep(poll_interval_seconds)
                continue

            # Provider queries require a real paused snapshot.  Pause and then
            # verify state; the command ACK itself is not accepted as proof.
            if snapshot.get("paused") is not True:
                service.execute_step("pause-map", expected_revision=binding.revision)
                pause_deadline = min(deadline, monotonic() + 5.0)
                while monotonic() < pause_deadline:
                    snapshot = service.snapshot()
                    binding = _snapshot_binding(snapshot, expected_player=player)
                    active = _active_event(snapshot)
                    if active is not None:
                        break
                    if snapshot.get("paused") is True:
                        break
                    sleep(poll_interval_seconds)
                if active is not None:
                    continue
                if snapshot.get("paused") is not True:
                    fail("pause-map ACK did not materialize before Incident query")

            provider_nonce_serial += 1
            try:
                matrix = _query_terminal_matrix(
                    service,
                    snapshot,
                    owner=owner,
                    player=player,
                    nonce_serial=provider_nonce_serial,
                )
            except ValueError as error:
                fail(str(error))
            polls = evidence["provider_polls"]
            assert isinstance(polls, list)
            polls.append(
                {
                    "nonce_serial": provider_nonce_serial,
                    "revision": binding.revision,
                    "date_raw": binding.date_raw,
                    "terminal_ready": matrix is not None,
                }
            )
            if matrix is not None:
                profiles, _raw = matrix
                # Preserve the positive terminal proof even when the following
                # negative ACL probe exposes a leak and the cell stays RED.
                evidence["terminal_profiles"] = profiles
                try:
                    acl = _query_acl_matrix(
                        service,
                        snapshot,
                        owner=owner,
                        player=player,
                        nonce_serial=provider_nonce_serial,
                    )
                except ValueError as error:
                    fail(str(error))
                evidence["acl_profiles"] = acl
                checks["entry_event_identity_bound"] = True
                checks["entry_option_materialized"] = True
                checks["ack_not_used_as_result"] = True
                checks["xyz_terminal_same_frame_ready"] = True
                checks["xyz_profile_probe_receipts_frozen"] = True
                checks["xyz_mixed_na_incident_matrix"] = True
                checks["wrong_owner_acl_typed_red"] = True
                evidence["result"] = "GREEN"
                evidence["failure_reason"] = None
                evidence["duration_seconds"] = round(monotonic() - started, 6)
                return evidence

            # Keep the bounded carrier at speed one.  Verify both speed and
            # unpause materialization on subsequent snapshots.
            if snapshot.get("speed") != 1:
                service.execute_step("set-speed-1", expected_revision=binding.revision)
                speed_deadline = min(deadline, monotonic() + 5.0)
                while monotonic() < speed_deadline:
                    snapshot = service.snapshot()
                    binding = _snapshot_binding(snapshot, expected_player=player)
                    if _active_event(snapshot) is not None:
                        break
                    if snapshot.get("speed") == 1:
                        break
                    sleep(poll_interval_seconds)
                if _active_event(snapshot) is not None:
                    continue
                if snapshot.get("speed") != 1:
                    fail("set-speed-1 ACK did not materialize")
            if snapshot.get("paused") is True:
                service.execute_step("resume-map", expected_revision=binding.revision)
                resume_deadline = min(deadline, monotonic() + 5.0)
                while monotonic() < resume_deadline:
                    snapshot = service.snapshot()
                    rebound = _snapshot_binding(snapshot, expected_player=player)
                    if _active_event(snapshot) is not None:
                        break
                    if snapshot.get("paused") is False:
                        break
                    sleep(poll_interval_seconds)
                if _active_event(snapshot) is None and snapshot.get("paused") is not False:
                    fail("resume-map ACK did not materialize")
            sleep(poll_interval_seconds)

        fail("Incident X/Y/Z action cell timed out before terminal postconditions")
    except IncidentActionCellError:
        raise
    except Exception as error:
        fail(f"{type(error).__name__}: {error}")
    raise AssertionError("unreachable")
