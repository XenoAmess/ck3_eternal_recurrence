#!/usr/bin/env python3
"""Exact-build live seam for the cross-cycle endgame action cell.

This module supplies the two deliberately missing callbacks of
``zg361_phase2_cross_cycle_endgame_action_cell``.  It advances only the real
owner-facing product path (356 option A, bounded M357-M359 time, 360 route C,
then 361), saves the visible 361 frame, reloads that exact save with one
acceptance-only typed event fixture, and changes to the product-bound subject.

There is no public arbitrary character-rebind or variable-query operation.
The target is derived by the fixture from ``zg361_p2c_m360_source_subject``;
GREEN still comes only from the existing received-self Workforce provider.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from pathlib import Path
import time
from typing import Callable, Final, Mapping, Protocol

from zg361_phase2_cross_cycle_endgame_action_cell import (
    CrossCycleEndgameCellError,
    EndgameResultBinding,
    EndgameSubjectProofSession,
    EndgameVisibleBinding,
    RESULT_EVENT,
    run_cross_cycle_endgame_action_cell,
)
from zhongguo_phase2_workforce_action import (
    M360_EVENT_DEFINITION_KEY,
    WorkforceActionCellError,
    select_typed_fixture_player_transition,
    submit_m360_route_action,
)


EXACT_GAME_VERSION: Final = "1.19.0.6"
EXACT_EXE_SHA256: Final = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
TRANSITION_FIXTURE_ID: Final = "zg361_phase2_cross_cycle_endgame_rebind"
TRANSITION_EVENT: Final = "zga_phase2_endgame_rebind.1"
TRANSITION_OWNER_SCOPE: Final = "zga_phase2_endgame_owner"
TRANSITION_SUBJECT_SCOPE: Final = "zga_phase2_endgame_subject"
M361_OPTION_NUMBER: Final = 1
DATE_RAW_HOURS_PER_DAY: Final = 24
DEFAULT_PROGRESS_MAX_DAYS: Final = 730


class CrossCycleEndgameLiveSeamError(RuntimeError):
    """Typed RED produced before the provider-backed action cell can GREEN."""

    def __init__(self, reason_code: str, evidence: Mapping[str, object]) -> None:
        self.reason_code = reason_code
        self.evidence = {
            **dict(evidence),
            "result": "RED",
            "reason_code": reason_code,
        }
        super().__init__(f"cross-cycle endgame live seam RED [{reason_code}]")


def _fail(reason_code: str, **evidence: object) -> None:
    raise CrossCycleEndgameLiveSeamError(reason_code, evidence)


class EndgameLiveService(Protocol):
    def capabilities(self) -> dict[str, object]: ...

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

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]: ...

    def save_checkpoint(
        self, *, expected_revision: int | None = None
    ) -> dict[str, object]: ...

    def query_zhongguo_workforce_collective_snapshot_v1(
        self,
        request_nonce: str,
        *,
        expected_revision: int,
        owner_character_id: int,
    ) -> dict[str, object]: ...


@dataclass(frozen=True, slots=True)
class ActivatedResultSession:
    """Service returned after fixture installation and exact-save reload."""

    service: EndgameLiveService
    restore_receipt: Mapping[str, object]


ResultSessionActivator = Callable[
    [EndgameResultBinding], ActivatedResultSession
]


def _positive_int(value: object, label: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 1 <= value <= 2**31 - 1
    ):
        _fail("integer_binding_invalid", label=label, observed=value)
    return value


def _snapshot_binding(
    service: EndgameLiveService,
    *,
    expected_player: int,
    require_paused: bool,
) -> tuple[dict[str, object], dict[str, object]]:
    snapshot = service.snapshot()
    if not isinstance(snapshot, Mapping):
        _fail("snapshot_not_an_object", snapshot=snapshot)
    played = snapshot.get("played_character")
    player = played.get("character_id") if isinstance(played, Mapping) else None
    binding = {
        "snapshot_id": snapshot.get("snapshot_id"),
        "revision": snapshot.get("revision"),
        "native_revision": snapshot.get("native_revision"),
        "date_raw": snapshot.get("date_raw"),
        "player_character_id": player,
        "paused": snapshot.get("paused"),
        "speed": snapshot.get("speed"),
    }
    if not (
        snapshot.get("map_ready") is True
        and (not require_paused or snapshot.get("paused") is True)
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
        and player == expected_player
    ):
        _fail(
            "owner_timeline_binding_invalid",
            expected_player_character_id=expected_player,
            binding=binding,
        )
    return dict(snapshot), binding


def _event_definition(
    service: EndgameLiveService,
    snapshot: Mapping[str, object],
    *,
    expected_definition: str,
) -> dict[str, object]:
    active = snapshot.get("active_event")
    event_id = active.get("instance_id") if isinstance(active, Mapping) else None
    revision = snapshot.get("revision")
    if not isinstance(event_id, int) or isinstance(event_id, bool) or event_id <= 0:
        _fail("expected_event_not_visible", expected_event=expected_definition)
    if not isinstance(revision, int) or isinstance(revision, bool):
        _fail("event_revision_invalid", revision=revision)
    response = service.query_current_event_window_context_v1(
        event_id, expected_revision=revision
    )
    context = (
        response.get("current_event_window_context")
        if isinstance(response, Mapping)
        else None
    )
    readiness = context.get("readiness") if isinstance(context, Mapping) else None
    observed = context.get("event_definition_key") if isinstance(context, Mapping) else None
    if observed != expected_definition:
        _fail(
            "unexpected_owner_event",
            expected_event=expected_definition,
            observed_event=observed,
            response=response,
        )
    if not (
        isinstance(response, Mapping)
        and response.get("status") == "available"
        and isinstance(context, Mapping)
        and context.get("current_event_instance_id") == event_id
        and isinstance(readiness, Mapping)
        and readiness.get("event_definition_identity_ready") is True
        and readiness.get("root_scope_ready") is True
        and readiness.get("saved_scopes_ready") is True
        and readiness.get("option_presentation_ready") is True
    ):
        _fail(
            "owner_event_not_identity_ready",
            expected_event=expected_definition,
            response=response,
        )
    return dict(context)


def _accepted_step(value: object, step: str) -> dict[str, object]:
    receipt = dict(value) if isinstance(value, Mapping) else {}
    if not (receipt.get("accepted") is True and receipt.get("status") == "submitted"):
        _fail("timeline_step_not_submitted", step=step, receipt=receipt)
    return receipt


def _wait_for_exact_owner_event(
    service: EndgameLiveService,
    *,
    expected_definition: str,
    expected_owner: int,
    starting_date_raw: int,
    max_game_days: int,
    allow_timeline_input: bool,
    timeout_s: float,
    poll_interval_s: float,
) -> dict[str, object]:
    if max_game_days < 0 or timeout_s <= 0 or poll_interval_s < 0:
        raise ValueError("endgame event wait bounds are invalid")
    deadline = time.monotonic() + timeout_s
    observations: list[dict[str, object]] = []
    submissions: list[dict[str, object]] = []
    while time.monotonic() < deadline:
        snapshot, binding = _snapshot_binding(
            service, expected_player=expected_owner, require_paused=False
        )
        date_raw = int(binding["date_raw"])
        if not (
            starting_date_raw
            <= date_raw
            <= starting_date_raw + max_game_days * DATE_RAW_HOURS_PER_DAY
        ):
            _fail(
                "bounded_progression_date_escaped",
                expected_event=expected_definition,
                starting_date_raw=starting_date_raw,
                max_game_days=max_game_days,
                observed_date_raw=date_raw,
            )
        active = snapshot.get("active_event")
        observations.append(
            {
                **binding,
                "active_event_instance_id": (
                    active.get("instance_id") if isinstance(active, Mapping) else None
                ),
            }
        )
        if isinstance(active, Mapping):
            if snapshot.get("paused") is not True:
                submissions.append(
                    _accepted_step(
                        service.execute_step(
                            "pause-map", expected_revision=int(binding["revision"])
                        ),
                        "pause-map",
                    )
                )
                if poll_interval_s:
                    time.sleep(poll_interval_s)
                continue
            context = _event_definition(
                service, snapshot, expected_definition=expected_definition
            )
            return {
                "result": "GREEN",
                "provider_observed": True,
                "action_ack_only": False,
                "expected_event_definition_key": expected_definition,
                "binding": binding,
                "event_context": context,
                "observations": observations,
                "timeline_submissions": submissions,
            }
        if not allow_timeline_input:
            if poll_interval_s:
                time.sleep(poll_interval_s)
            continue
        if snapshot.get("speed") != 1:
            step = "set-speed-1"
        elif snapshot.get("paused") is True:
            step = "resume-map"
        else:
            step = ""
        if step:
            submissions.append(
                _accepted_step(
                    service.execute_step(
                        step, expected_revision=int(binding["revision"])
                    ),
                    step,
                )
            )
        if poll_interval_s:
            time.sleep(poll_interval_s)
    _fail(
        "bounded_progression_timed_out",
        expected_event=expected_definition,
        max_game_days=max_game_days,
        observations=observations,
        timeline_submissions=submissions,
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _save_result_checkpoint(
    service: EndgameLiveService,
    *,
    owner: int,
    subject: int,
    save_lineage_id: str,
) -> dict[str, object]:
    snapshot, before = _snapshot_binding(
        service, expected_player=owner, require_paused=True
    )
    context = _event_definition(service, snapshot, expected_definition=RESULT_EVENT)
    result = service.save_checkpoint(expected_revision=int(before["revision"]))
    checkpoint = result.get("checkpoint") if isinstance(result, Mapping) else None
    checkpoint = dict(checkpoint) if isinstance(checkpoint, Mapping) else {}
    raw_path = checkpoint.get("path")
    size = checkpoint.get("size")
    sha = str(checkpoint.get("sha256", "")).upper()
    path = Path(raw_path) if isinstance(raw_path, str) else Path()
    valid = (
        isinstance(result, Mapping)
        and result.get("accepted") is True
        and checkpoint.get("status") == "saved"
        and path.is_absolute()
        and path.is_file()
        and isinstance(size, int)
        and not isinstance(size, bool)
        and size > 0
        and path.stat().st_size == size
        and _sha256_file(path) == sha
        and len(sha) == 64
    )
    if not valid:
        _fail("result_checkpoint_not_materialized", result=result, checkpoint=checkpoint)
    after_snapshot, after = _snapshot_binding(
        service, expected_player=owner, require_paused=True
    )
    _event_definition(service, after_snapshot, expected_definition=RESULT_EVENT)
    if before["date_raw"] != after["date_raw"]:
        _fail("result_checkpoint_date_drifted", before=before, after=after)
    return {
        "path": str(path.resolve()),
        "bytes": size,
        "sha256": sha,
        "save_lineage_id": save_lineage_id,
        "event_definition_key": RESULT_EVENT,
        "owner_character_id": owner,
        "subject_character_id": subject,
        "player_character_id": owner,
        "date_raw": int(after["date_raw"]),
        "event_context": context,
    }


def _validate_exact_build(build_identity: Mapping[str, object]) -> None:
    observed_version = build_identity.get("game_version")
    observed_sha = str(build_identity.get("game_exe_sha256", "")).upper()
    if observed_version != EXACT_GAME_VERSION or observed_sha != EXACT_EXE_SHA256:
        _fail(
            "exact_build_mismatch",
            expected_game_version=EXACT_GAME_VERSION,
            expected_game_exe_sha256=EXACT_EXE_SHA256,
            observed_build=dict(build_identity),
        )


def _validated_activation(
    activation: ActivatedResultSession,
    *,
    result: EndgameResultBinding,
) -> EndgameLiveService:
    if not isinstance(activation, ActivatedResultSession):
        _fail("result_session_activation_invalid", observed_type=type(activation).__name__)
    receipt = dict(activation.restore_receipt)
    if receipt.get("generic_character_rebind_used") is not False:
        _fail("generic_character_rebind_forbidden", restore_receipt=receipt)
    if receipt.get("owner_character_id") != result.owner_character_id:
        _fail(
            "result_restore_owner_mismatch",
            expected_owner_character_id=result.owner_character_id,
            restore_receipt=receipt,
        )
    valid = (
        receipt.get("result") == "GREEN"
        and receipt.get("provider_observed") is True
        and receipt.get("action_ack_only") is False
        and receipt.get("transition_fixture_id") == TRANSITION_FIXTURE_ID
        and receipt.get("typed_event_fixture_used") is True
        and receipt.get("business_state_fixture_used") is False
        and receipt.get("console_used") is False
        and str(receipt.get("checkpoint_sha256", "")).upper()
        == result.result_checkpoint_sha256
        and receipt.get("save_lineage_id") == result.save_lineage_id
        and receipt.get("event_definition_key") == RESULT_EVENT
        and receipt.get("player_character_id") == result.owner_character_id
        and receipt.get("subject_character_id") == result.subject_character_id
        and receipt.get("date_raw") == result.result_date_raw
        and receipt.get("game_version") == EXACT_GAME_VERSION
        and str(receipt.get("game_exe_sha256", "")).upper()
        == EXACT_EXE_SHA256
    )
    if not valid:
        _fail(
            "result_checkpoint_restore_not_green",
            result_binding=asdict(result),
            restore_receipt=receipt,
        )
    snapshot, _ = _snapshot_binding(
        activation.service,
        expected_player=result.owner_character_id,
        require_paused=True,
    )
    _event_definition(
        activation.service, snapshot, expected_definition=RESULT_EVENT
    )
    return activation.service


def run_exact_build_cross_cycle_endgame_seam(
    owner_service: EndgameLiveService,
    *,
    source_checkpoint_restore: Mapping[str, object],
    build_identity: Mapping[str, object],
    activate_result_session: ResultSessionActivator,
    request_nonce: str = "zg361.phase2.endgame.exact",
    progression_max_days: int = DEFAULT_PROGRESS_MAX_DAYS,
    timeout_s: float = 60.0,
    poll_interval_s: float = 0.05,
    evidence_directory: Path | None = None,
) -> dict[str, object]:
    """Run the fixed 356 -> 360C -> 361 -> subject-provider seam.

    ``activate_result_session`` is lifecycle plumbing only: it installs the
    named fixture and reloads the exact result save.  This function then
    re-queries 361, selects its first product option, queries the sole typed
    fixture event, performs the fixed transition, and lets the action cell
    query the Workforce provider.  A callback ACK can never make the cell
    GREEN.
    """

    if not callable(activate_result_session):
        raise ValueError("activate_result_session must be callable")
    _validate_exact_build(build_identity)
    if not isinstance(source_checkpoint_restore, Mapping):
        _fail(
            "source_checkpoint_restore_invalid",
            observed_type=type(source_checkpoint_restore).__name__,
        )
    checkpoint_value = source_checkpoint_restore.get("checkpoint")
    checkpoint = checkpoint_value if isinstance(checkpoint_value, Mapping) else {}
    lineage = checkpoint.get("save_lineage_id")
    if not isinstance(lineage, str) or not lineage:
        _fail("source_save_lineage_missing", checkpoint=checkpoint)

    def complete(
        service: EndgameLiveService, binding: EndgameVisibleBinding
    ) -> Mapping[str, object]:
        m360 = _wait_for_exact_owner_event(
            service,
            expected_definition=M360_EVENT_DEFINITION_KEY,
            expected_owner=binding.owner_character_id,
            starting_date_raw=binding.source_date_raw,
            max_game_days=progression_max_days,
            allow_timeline_input=True,
            timeout_s=timeout_s,
            poll_interval_s=poll_interval_s,
        )
        action_path = (
            evidence_directory / "m360_route_c_action.json"
            if evidence_directory is not None
            else None
        )
        try:
            route = submit_m360_route_action(
                service,
                route="C",
                evidence_path=action_path,
                settle_polls=max(1, int(timeout_s / max(poll_interval_s, 0.05))),
                poll_interval_s=poll_interval_s,
            )
        except WorkforceActionCellError as error:
            _fail("m360_route_c_action_red", error=f"{type(error).__name__}: {error}")
        route_binding = route.get("binding")
        if not (
            isinstance(route_binding, Mapping)
            and route_binding.get("owner_character_id") == binding.owner_character_id
            and route_binding.get("subject_character_id") == binding.subject_character_id
            and route_binding.get("route") == "C"
            and route_binding.get("option_number") == 3
        ):
            _fail("m360_owner_subject_binding_drifted", route_evidence=route)
        result_wait = _wait_for_exact_owner_event(
            service,
            expected_definition=RESULT_EVENT,
            expected_owner=binding.owner_character_id,
            starting_date_raw=int(m360["binding"]["date_raw"]),
            max_game_days=1,
            allow_timeline_input=False,
            timeout_s=timeout_s,
            poll_interval_s=poll_interval_s,
        )
        saved = _save_result_checkpoint(
            service,
            owner=binding.owner_character_id,
            subject=binding.subject_character_id,
            save_lineage_id=lineage,
        )
        return {
            "result": "GREEN",
            "m360_route": "C",
            "action_ack_only": False,
            "fixture_used": False,
            "console_used": False,
            "m357_m359_bounded_real_progression": m360,
            "m360_route_c_action": route,
            "owner_visible_result": result_wait,
            "result_checkpoint": saved,
        }

    def subject_session(result: EndgameResultBinding) -> EndgameSubjectProofSession:
        service = _validated_activation(
            activate_result_session(result), result=result
        )
        owner_snapshot, owner_binding = _snapshot_binding(
            service, expected_player=result.owner_character_id, require_paused=True
        )
        result_context = _event_definition(
            service, owner_snapshot, expected_definition=RESULT_EVENT
        )
        options = result_context.get("options")
        if not (
            isinstance(options, list)
            and len(options) == 3
            and [
                row.get("native_option_index")
                for row in options
                if isinstance(row, Mapping)
                and row.get("shown") is True
                and row.get("enabled") is True
            ]
            == [0, 1, 2]
        ):
            _fail("result_event_options_not_actionable", context=result_context)
        ack = service.select_event_option(
            M361_OPTION_NUMBER,
            event_instance_id=int(
                owner_snapshot["active_event"]["instance_id"]
            ),
            expected_revision=int(owner_binding["revision"]),
        )
        if not (
            isinstance(ack, Mapping)
            and ack.get("accepted") is True
            and ack.get("status") == "submitted"
        ):
            _fail("result_event_action_not_submitted", action_ack=ack)
        fixture = _wait_for_exact_owner_event(
            service,
            expected_definition=TRANSITION_EVENT,
            expected_owner=result.owner_character_id,
            starting_date_raw=result.result_date_raw,
            max_game_days=0,
            allow_timeline_input=False,
            timeout_s=timeout_s,
            poll_interval_s=poll_interval_s,
        )
        transition_path = (
            evidence_directory / "typed_owner_subject_transition.json"
            if evidence_directory is not None
            else None
        )
        try:
            typed = select_typed_fixture_player_transition(
                service,
                expected_event_definition_key=TRANSITION_EVENT,
                expected_player_before=result.owner_character_id,
                expected_player_after=result.subject_character_id,
                owner_character_id=result.owner_character_id,
                subject_character_id=result.subject_character_id,
                owner_scope_name=TRANSITION_OWNER_SCOPE,
                subject_scope_name=TRANSITION_SUBJECT_SCOPE,
                evidence_path=transition_path,
                settle_polls=max(1, int(timeout_s / max(poll_interval_s, 0.05))),
                poll_interval_s=poll_interval_s,
            )
        except WorkforceActionCellError as error:
            _fail(
                "typed_owner_subject_transition_red",
                error=f"{type(error).__name__}: {error}",
                fixture_event=fixture,
            )
        native_post = typed.get("native_played_character_postcondition")
        date_raw = native_post.get("date_raw") if isinstance(native_post, Mapping) else None
        return EndgameSubjectProofSession(
            service=service,
            transition_receipt={
                "result": "GREEN",
                "provider_observed": True,
                "action_ack_only": False,
                "from_player_character_id": result.owner_character_id,
                "to_player_character_id": result.subject_character_id,
                "date_raw": date_raw,
                "restored_checkpoint_sha256": result.result_checkpoint_sha256,
                "save_lineage_id": result.save_lineage_id,
                "typed_event_fixture_used": True,
                "business_state_fixture_used": False,
                "console_used": False,
                "generic_character_rebind_used": False,
                "result_event_action_ack": dict(ack),
                "fixture_event": fixture,
                "typed_transition": typed,
            },
        )

    try:
        return run_cross_cycle_endgame_action_cell(
            owner_service,
            source_checkpoint_restore=source_checkpoint_restore,
            completion_executor=complete,
            subject_session_factory=subject_session,
            request_nonce=request_nonce,
        )
    except CrossCycleEndgameCellError:
        raise


__all__ = [
    "ActivatedResultSession",
    "CrossCycleEndgameLiveSeamError",
    "DEFAULT_PROGRESS_MAX_DAYS",
    "EXACT_EXE_SHA256",
    "EXACT_GAME_VERSION",
    "EndgameLiveService",
    "ResultSessionActivator",
    "TRANSITION_EVENT",
    "TRANSITION_FIXTURE_ID",
    "TRANSITION_OWNER_SCOPE",
    "TRANSITION_SUBJECT_SCOPE",
    "run_exact_build_cross_cycle_endgame_seam",
]
