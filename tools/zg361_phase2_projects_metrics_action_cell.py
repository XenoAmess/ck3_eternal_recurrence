#!/usr/bin/env python3
"""Independent projects-metrics query/action/postcondition cell.

The live checkpoint for this cell is deliberately narrower than the visual
promo capture: the played character is the project subject, a distinct AI
character is the owner, and the CP #026 contribution has been prepared before
P3 copies it into its provider projection.  The pre-query therefore reports
``project_source_not_found``.  (P3 initialization and its authorized AI #229
route run in one effect call, so a source-ready/result-pending paused frame is
not generally observable.)  The only mutation is a bounded ``life-advance``.
Its acknowledgement is retained as transport evidence but can never satisfy
the business gate.  GREEN is emitted only after the existing native provider
observes a complete CP #026 receipt consumed by a committed P3 #229 result on
a later paused frame.

No CK3 process is started here.  The production service is injected by a live
caller; unit tests inject a deterministic fixture service.
"""

from __future__ import annotations

import copy
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Protocol

from xar_autoplayer.bridge.event_contract import action_step_set
from xar_autoplayer.bridge.zhongguo_projects_metrics_postcondition_contract import (
    QUERY_ZHONGGUO_PROJECTS_METRICS_V1_CAPABILITY,
    query_zhongguo_projects_metrics_v1_step,
)


READINESS = "static-ready-live-pending"
CASE_KIND = "zhongguo.projects-metrics.project-correlation"
MAX_ADVANCE_STEPS = 100
MAX_ELAPSED_DAYS = 370
RAW_HOURS_PER_DAY = 24


class ProjectsMetricsActionService(Protocol):
    def capabilities(self) -> dict[str, object]: ...

    def snapshot(self) -> dict[str, object]: ...

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]: ...

    def query_zhongguo_projects_metrics_postcondition_v1(
        self,
        request_nonce: str,
        *,
        expected_revision: int,
        owner_character_id: int,
    ) -> dict[str, object]: ...


@dataclass(frozen=True)
class ProjectsMetricsSourceCheckpoint:
    owner_character_id: int
    subject_character_id: int
    cycle_serial: int
    case_serial: int
    contribution_receipt_id: int
    contribution_receipt_revision: int
    contribution_value: int

    @property
    def identity(self) -> tuple[int, int, int, int]:
        return (
            self.owner_character_id,
            self.subject_character_id,
            self.cycle_serial,
            self.case_serial,
        )


class ProjectsMetricsActionCellError(RuntimeError):
    """Fail-closed cell result with structured evidence."""

    def __init__(self, reason_code: str, evidence: Mapping[str, object]) -> None:
        self.reason_code = reason_code
        self.evidence = {
            **copy.deepcopy(dict(evidence)),
            "result": "RED",
            "reason_code": reason_code,
        }
        super().__init__(f"projects-metrics action cell RED [{reason_code}]")


def _integer(
    value: object, label: str, *, minimum: int, maximum: int
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not minimum <= value <= maximum
    ):
        raise ValueError(f"{label} must be an integer in range")
    return value


def _positive_character_id(value: object, label: str) -> int:
    return _integer(value, label, minimum=1, maximum=2**31 - 1)


def _positive_bound(value: object, label: str, maximum: int) -> int:
    return _integer(value, label, minimum=1, maximum=maximum)


def _nonce(prefix: str, suffix: str, owner_character_id: int) -> str:
    if not isinstance(prefix, str) or not prefix:
        raise ValueError("request_nonce_prefix must be non-empty")
    value = f"{prefix}.{suffix}"
    # Reuse the provider's canonical nonce validator rather than maintaining a
    # second grammar in this cell.
    query_zhongguo_projects_metrics_v1_step(owner_character_id, value)
    return value


def _snapshot_binding(snapshot: object) -> tuple[dict[str, object] | None, str | None]:
    if not isinstance(snapshot, dict):
        return None, "snapshot_not_an_object"
    revision = snapshot.get("revision")
    native_revision = snapshot.get("native_revision")
    date_raw = snapshot.get("date_raw")
    snapshot_id = snapshot.get("snapshot_id")
    played = snapshot.get("played_character")
    player_character_id = (
        played.get("character_id") if isinstance(played, dict) else None
    )
    diagnostics = snapshot.get("diagnostics")
    connection_generation = (
        diagnostics.get("connection_generation")
        if isinstance(diagnostics, dict)
        else None
    )
    if snapshot.get("paused") is not True:
        return None, "snapshot_not_paused"
    if snapshot.get("map_ready") is not True:
        return None, "map_not_ready"
    if (
        isinstance(revision, bool)
        or not isinstance(revision, int)
        or not 0 <= revision <= 2**64 - 1
    ):
        return None, "public_revision_unavailable"
    if (
        isinstance(native_revision, bool)
        or not isinstance(native_revision, int)
        or not 1 <= native_revision <= 2**64 - 1
    ):
        return None, "native_revision_unavailable"
    if (
        isinstance(date_raw, bool)
        or not isinstance(date_raw, int)
        or not -(2**31) <= date_raw <= 2**31 - 1
    ):
        return None, "date_raw_unavailable"
    if not isinstance(snapshot_id, str) or not snapshot_id:
        return None, "snapshot_id_unavailable"
    if (
        isinstance(player_character_id, bool)
        or not isinstance(player_character_id, int)
        or not 1 <= player_character_id <= 2**31 - 1
    ):
        return None, "played_character_unavailable"
    if (
        isinstance(connection_generation, bool)
        or not isinstance(connection_generation, int)
        or not 1 <= connection_generation <= 2**64 - 1
    ):
        return None, "connection_generation_unavailable"
    active_event = snapshot.get("active_event")
    active_event_instance_id = None
    if isinstance(active_event, dict):
        candidate = active_event.get("instance_id")
        if not isinstance(candidate, bool) and isinstance(candidate, int):
            active_event_instance_id = candidate
        else:
            active_event_instance_id = "unknown"
    return {
        "snapshot_id": snapshot_id,
        "revision": revision,
        "native_revision": native_revision,
        "date_raw": date_raw,
        "paused": True,
        "map_ready": True,
        "player_character_id": player_character_id,
        "connection_generation": connection_generation,
        "active_event_instance_id": active_event_instance_id,
    }, None


def _typed_integer(group: object, key: str, label: str) -> int:
    if not isinstance(group, Mapping):
        raise ValueError(f"{label} is absent")
    field = group.get(key)
    if not isinstance(field, Mapping) or set(field) != {
        "status",
        "value",
        "unavailable_reason",
    }:
        raise ValueError(f"{label}.{key} is not a typed field")
    value = field.get("value")
    if (
        field.get("status") != "available"
        or field.get("unavailable_reason") is not None
        or isinstance(value, bool)
        or not isinstance(value, int)
    ):
        raise ValueError(f"{label}.{key} is unavailable")
    return value


def _typed_string(group: object, key: str, label: str) -> str:
    if not isinstance(group, Mapping):
        raise ValueError(f"{label} is absent")
    field = group.get(key)
    if not isinstance(field, Mapping) or set(field) != {
        "status",
        "value",
        "unavailable_reason",
    }:
        raise ValueError(f"{label}.{key} is not a typed field")
    value = field.get("value")
    if (
        field.get("status") != "available"
        or field.get("unavailable_reason") is not None
        or not isinstance(value, str)
        or not value
    ):
        raise ValueError(f"{label}.{key} is unavailable")
    return value


def _identity(group: object, label: str) -> tuple[int, int, int, int]:
    return (
        _positive_character_id(
            _typed_integer(group, "owner_character_id", label),
            f"{label}.owner_character_id",
        ),
        _positive_character_id(
            _typed_integer(group, "subject_character_id", label),
            f"{label}.subject_character_id",
        ),
        _integer(
            _typed_integer(group, "cycle_serial", label),
            f"{label}.cycle_serial",
            minimum=1,
            maximum=2**63 - 1,
        ),
        _integer(
            _typed_integer(group, "case_serial", label),
            f"{label}.case_serial",
            minimum=1,
            maximum=2**63 - 1,
        ),
    )


def _require_provider_binding(
    response: Mapping[str, object],
    binding: Mapping[str, object],
    *,
    owner_character_id: int,
) -> None:
    query_binding = response.get("binding")
    if not isinstance(query_binding, Mapping):
        raise ValueError("provider response lacks its paused binding")
    expected = {
        "snapshot_id": binding["snapshot_id"],
        "revision": binding["revision"],
        "native_revision": binding["native_revision"],
        "connection_generation": binding["connection_generation"],
        "date_raw": binding["date_raw"],
        "paused": True,
        "player_character_id": binding["player_character_id"],
        "subject_character_id": binding["player_character_id"],
        "owner_character_id": owner_character_id,
        "expected_revision": binding["revision"],
    }
    for key, expected_value in expected.items():
        if query_binding.get(key) != expected_value:
            raise ValueError(f"provider binding changed at {key}")


def _source_checkpoint(
    response: object,
    *,
    binding: Mapping[str, object],
    owner_character_id: int,
) -> ProjectsMetricsSourceCheckpoint:
    if not isinstance(response, Mapping):
        raise ValueError("provider response is not an object")
    if (
        response.get("schema_version") != 1
        or response.get("status") != "available"
        or response.get("capability")
        != QUERY_ZHONGGUO_PROJECTS_METRICS_V1_CAPABILITY
        or response.get("case_kind") != CASE_KIND
        or response.get("source_backend_id") != "native-headless"
        or response.get("unavailable_reason") is not None
    ):
        raise ValueError(
            "provider did not expose an available projects source "
            f"(status={response.get('status')}, "
            f"reason={response.get('unavailable_reason')})"
        )
    _require_provider_binding(
        response, binding, owner_character_id=owner_character_id
    )
    readiness = response.get("readiness")
    if not isinstance(readiness, Mapping) or not all(
        readiness.get(key) is True
        for key in (
            "player_subject_binding_ready",
            "owner_binding_ready",
            "source_identity_ready",
            "contribution_ready",
            "same_frame_ready",
        )
    ):
        raise ValueError("provider source/contribution checkpoint is not ready")
    payload = response.get("projects_metrics")
    if not isinstance(payload, Mapping):
        raise ValueError("provider projects_metrics payload is absent")
    source_identity = _identity(response.get("source_identity"), "source_identity")
    payload_source_identity = _identity(
        payload.get("source_identity"), "projects_metrics.source_identity"
    )
    contribution = payload.get("contribution")
    contribution_identity = _identity(
        contribution.get("identity") if isinstance(contribution, Mapping) else None,
        "contribution.identity",
    )
    if not (
        source_identity == payload_source_identity == contribution_identity
        and source_identity[0] == owner_character_id
        and source_identity[1] == binding["player_character_id"]
        and isinstance(contribution, Mapping)
        and contribution.get("provider_observed") is True
    ):
        raise ValueError("provider source identity is not the requested AI-owner/player-subject case")
    receipt_id = _integer(
        _typed_integer(contribution, "receipt_id", "contribution"),
        "contribution.receipt_id",
        minimum=1,
        maximum=2**63 - 1,
    )
    receipt_revision = _integer(
        _typed_integer(contribution, "receipt_revision", "contribution"),
        "contribution.receipt_revision",
        minimum=1,
        maximum=2**63 - 1,
    )
    value = _integer(
        _typed_integer(contribution, "value", "contribution"),
        "contribution.value",
        minimum=-(2**63),
        maximum=2**63 - 1,
    )
    return ProjectsMetricsSourceCheckpoint(
        *source_identity,
        contribution_receipt_id=receipt_id,
        contribution_receipt_revision=receipt_revision,
        contribution_value=value,
    )


def _pre_result_is_absent(response: Mapping[str, object]) -> bool:
    readiness = response.get("readiness")
    return bool(
        isinstance(readiness, Mapping)
        and readiness.get("ready") is False
        and readiness.get("result_identity_ready") is False
        and readiness.get("metrics_ready") is False
        and readiness.get("same_project_case_identity") is False
        and readiness.get("receipt_lineage_ready") is False
        and readiness.get("result_operation_committed") is False
    )


def _provider_source_is_absent(
    response: object,
    *,
    binding: Mapping[str, object],
    owner_character_id: int,
) -> bool:
    if not isinstance(response, Mapping):
        return False
    if not (
        response.get("schema_version") == 1
        and response.get("status") == "unavailable"
        and response.get("capability")
        == QUERY_ZHONGGUO_PROJECTS_METRICS_V1_CAPABILITY
        and response.get("case_kind") == CASE_KIND
        and response.get("source_backend_id") == "native-headless"
        and response.get("unavailable_reason") == "project_source_not_found"
    ):
        return False
    try:
        _require_provider_binding(
            response, binding, owner_character_id=owner_character_id
        )
    except ValueError:
        return False
    return True


def _require_committed_postcondition(
    response: object,
    *,
    binding: Mapping[str, object],
    owner_character_id: int,
    baseline: ProjectsMetricsSourceCheckpoint | None,
) -> dict[str, object]:
    current_source = _source_checkpoint(
        response,
        binding=binding,
        owner_character_id=owner_character_id,
    )
    if baseline is not None and current_source != baseline:
        raise ValueError("source contribution identity or receipt drifted")
    if not isinstance(response, Mapping):  # narrowed by _source_checkpoint
        raise ValueError("provider response is not an object")
    readiness = response.get("readiness")
    required_readiness = (
        "player_subject_binding_ready",
        "owner_binding_ready",
        "source_identity_ready",
        "result_identity_ready",
        "contribution_ready",
        "metrics_ready",
        "same_project_case_identity",
        "receipt_lineage_ready",
        "result_operation_committed",
        "same_frame_ready",
        "ready",
    )
    if not isinstance(readiness, Mapping) or not all(
        readiness.get(key) is True for key in required_readiness
    ):
        raise ValueError("projects/metrics provider has not committed the postcondition")
    payload = response.get("projects_metrics")
    if not isinstance(payload, Mapping):
        raise ValueError("projects_metrics payload is absent")
    identities = (
        _identity(response.get("source_identity"), "source_identity"),
        _identity(response.get("result_identity"), "result_identity"),
        _identity(payload.get("source_identity"), "payload.source_identity"),
        _identity(payload.get("result_identity"), "payload.result_identity"),
    )
    contribution = payload.get("contribution")
    metrics = payload.get("metrics_result")
    identities += (
        _identity(
            contribution.get("identity")
            if isinstance(contribution, Mapping)
            else None,
            "contribution.identity",
        ),
        _identity(
            metrics.get("identity") if isinstance(metrics, Mapping) else None,
            "metrics_result.identity",
        ),
    )
    if any(identity != current_source.identity for identity in identities):
        raise ValueError("source/result/contribution/metrics identities disagree")
    if not (
        isinstance(metrics, Mapping)
        and metrics.get("provider_observed") is True
    ):
        raise ValueError("metrics result is not provider observed")
    source_receipt_id = _typed_integer(
        metrics, "source_contribution_receipt_id", "metrics_result"
    )
    source_receipt_revision = _typed_integer(
        metrics, "source_contribution_receipt_revision", "metrics_result"
    )
    metrics_revision = _integer(
        _typed_integer(metrics, "metrics_revision", "metrics_result"),
        "metrics_result.metrics_revision",
        minimum=1,
        maximum=2**63 - 1,
    )
    dictionary_key = _typed_string(
        metrics, "dictionary_key", "metrics_result"
    )
    if (
        source_receipt_id != current_source.contribution_receipt_id
        or source_receipt_revision
        != current_source.contribution_receipt_revision
    ):
        raise ValueError("metrics result consumed a different contribution receipt")
    if dictionary_key not in {
        "metric_dictionary_subject_v1",
        "metric_dictionary_manager_v1",
    }:
        raise ValueError("metrics dictionary key is outside the v1 allowlist")
    return {
        "identity": list(current_source.identity),
        "contribution_receipt_id": current_source.contribution_receipt_id,
        "contribution_receipt_revision": current_source.contribution_receipt_revision,
        "contribution_value": current_source.contribution_value,
        "metrics_revision": metrics_revision,
        "dictionary_key": dictionary_key,
    }


def preflight_projects_metrics_gameplay_action_cell(
    service: ProjectsMetricsActionService,
    *,
    owner_character_id: int,
    request_nonce_prefix: str = "zg361.projects.metrics",
) -> dict[str, object]:
    """Read and classify the exact non-mutating live checkpoint."""

    owner = _positive_character_id(owner_character_id, "owner_character_id")
    nonce = _nonce(request_nonce_prefix, "pre", owner)
    report: dict[str, object] = {
        "schema_version": 1,
        "kind": "zg361_projects_metrics_gameplay_action_preflight",
        "readiness": READINESS,
        "result": "RED",
        "ready_to_run": False,
        "reason_code": None,
        "owner_character_id": owner,
        "binding": None,
        "source_checkpoint": None,
        "provider_response": None,
        "gameplay_action_executed": False,
        "action_ack_is_business_postcondition": False,
    }

    def red(reason_code: str) -> dict[str, object]:
        report["reason_code"] = reason_code
        return report

    capabilities = service.capabilities()
    bridge_capabilities = (
        capabilities.get("bridge_capabilities")
        if isinstance(capabilities, Mapping)
        else None
    )
    if not (
        isinstance(bridge_capabilities, list)
        and QUERY_ZHONGGUO_PROJECTS_METRICS_V1_CAPABILITY
        in bridge_capabilities
    ):
        return red("projects_metrics_provider_not_advertised")
    if "life-advance" not in action_step_set(capabilities):
        return red("life_advance_not_advertised")
    binding, binding_error = _snapshot_binding(service.snapshot())
    report["binding"] = copy.deepcopy(binding)
    if binding is None:
        report["binding_error"] = binding_error
        return red("paused_binding_unavailable")
    if binding["active_event_instance_id"] is not None:
        return red("player_visible_event_pending")
    if binding["player_character_id"] == owner:
        return red("owner_must_be_distinct_bounded_ai")
    try:
        response = service.query_zhongguo_projects_metrics_postcondition_v1(
            nonce,
            expected_revision=int(binding["revision"]),
            owner_character_id=owner,
        )
        report["provider_response"] = copy.deepcopy(response)
    except Exception as error:
        report["query_error_type"] = type(error).__name__
        report["query_error"] = str(error)
        return red("source_checkpoint_unavailable")
    if _provider_source_is_absent(
        response, binding=binding, owner_character_id=owner
    ):
        report["checkpoint_mode"] = "provider_source_absent"
    else:
        try:
            source = _source_checkpoint(
                response,
                binding=binding,
                owner_character_id=owner,
            )
        except ValueError as error:
            report["query_error_type"] = type(error).__name__
            report["query_error"] = str(error)
            return red("source_checkpoint_unavailable")
        report["source_checkpoint"] = asdict(source)
        if not isinstance(response, Mapping) or not _pre_result_is_absent(response):
            return red("checkpoint_is_not_pre_result")
        report["checkpoint_mode"] = "source_ready_result_pending"
    report["result"] = "READY"
    report["ready_to_run"] = True
    report["reason_code"] = None
    return report


def run_projects_metrics_gameplay_action_cell(
    service: ProjectsMetricsActionService,
    *,
    owner_character_id: int,
    request_nonce_prefix: str = "zg361.projects.metrics",
    max_advance_steps: int = 30,
    max_elapsed_days: int = 120,
) -> dict[str, object]:
    """Advance from CP #026 source-ready to a provider-observed P3 #229 result."""

    owner = _positive_character_id(owner_character_id, "owner_character_id")
    steps_bound = _positive_bound(
        max_advance_steps, "max_advance_steps", MAX_ADVANCE_STEPS
    )
    days_bound = _positive_bound(
        max_elapsed_days, "max_elapsed_days", MAX_ELAPSED_DAYS
    )
    # Validate the largest generated nonce before any action is attempted.
    _nonce(request_nonce_prefix, f"d{steps_bound}", owner)
    preflight = preflight_projects_metrics_gameplay_action_cell(
        service,
        owner_character_id=owner,
        request_nonce_prefix=request_nonce_prefix,
    )
    report: dict[str, object] = {
        "schema_version": 1,
        "kind": "zg361_projects_metrics_gameplay_action_cell",
        "span_id": "phase2_projects_metrics",
        "producer_key": "projects-metrics",
        "readiness": READINESS,
        "result": "RED",
        "mcp_only": True,
        "ocr_used": False,
        "coordinates_used": False,
        "test_ui_used": False,
        "gameplay_action_executed": False,
        "gameplay_action_complete": False,
        "business_postcondition_complete": False,
        "action_ack_is_business_postcondition": False,
        "postcondition_source": QUERY_ZHONGGUO_PROJECTS_METRICS_V1_CAPABILITY,
        "owner_character_id": owner,
        "preflight": copy.deepcopy(preflight),
        "timeline_actions": [],
        "provider_observations": [],
        "terminal_condition": None,
    }
    if preflight.get("ready_to_run") is not True:
        raise ProjectsMetricsActionCellError(
            str(preflight.get("reason_code") or "preflight_not_ready"), report
        )
    binding = preflight.get("binding")
    source_raw = preflight.get("source_checkpoint")
    if not isinstance(binding, Mapping):
        raise ProjectsMetricsActionCellError("preflight_projection_missing", report)
    baseline: ProjectsMetricsSourceCheckpoint | None = None
    if isinstance(source_raw, Mapping):
        baseline = ProjectsMetricsSourceCheckpoint(
            owner_character_id=_positive_character_id(
                source_raw.get("owner_character_id"), "source.owner"
            ),
            subject_character_id=_positive_character_id(
                source_raw.get("subject_character_id"), "source.subject"
            ),
            cycle_serial=_integer(
                source_raw.get("cycle_serial"), "source.cycle", minimum=1,
                maximum=2**63 - 1,
            ),
            case_serial=_integer(
                source_raw.get("case_serial"), "source.case", minimum=1,
                maximum=2**63 - 1,
            ),
            contribution_receipt_id=_integer(
                source_raw.get("contribution_receipt_id"), "source.receipt_id",
                minimum=1, maximum=2**63 - 1,
            ),
            contribution_receipt_revision=_integer(
                source_raw.get("contribution_receipt_revision"),
                "source.receipt_revision", minimum=1, maximum=2**63 - 1,
            ),
            contribution_value=_integer(
                source_raw.get("contribution_value"), "source.value",
                minimum=-(2**63), maximum=2**63 - 1,
            ),
        )
    initial_date = int(binding["date_raw"])
    current_binding = dict(binding)

    for ordinal in range(1, steps_bound + 1):
        expected_revision = int(current_binding["revision"])
        try:
            acknowledgement = service.execute_step(
                "life-advance", expected_revision=expected_revision
            )
        except Exception as error:
            report["action_error_type"] = type(error).__name__
            report["action_error"] = str(error)
            raise ProjectsMetricsActionCellError(
                "timeline_submission_failed", report
            ) from error
        report["gameplay_action_executed"] = True
        action_row: dict[str, object] = {
            "ordinal": ordinal,
            "step": "life-advance",
            "expected_revision": expected_revision,
            "acknowledgement": copy.deepcopy(acknowledgement),
            "ack_is_business_postcondition": False,
            "post_snapshot": None,
        }
        actions = report["timeline_actions"]
        if isinstance(actions, list):
            actions.append(action_row)
        if not (
            isinstance(acknowledgement, Mapping)
            and acknowledgement.get("step") == "life-advance"
        ):
            raise ProjectsMetricsActionCellError(
                "timeline_acknowledgement_malformed", report
            )

        post_binding, binding_error = _snapshot_binding(service.snapshot())
        action_row["post_snapshot"] = copy.deepcopy(post_binding)
        action_row["post_snapshot_error"] = binding_error
        if post_binding is None:
            raise ProjectsMetricsActionCellError(
                "timeline_postcondition_unavailable", report
            )
        if (
            post_binding["player_character_id"]
            != binding["player_character_id"]
            or post_binding["connection_generation"]
            != binding["connection_generation"]
        ):
            raise ProjectsMetricsActionCellError(
                "player_or_connection_binding_drifted", report
            )
        if post_binding["active_event_instance_id"] is not None:
            raise ProjectsMetricsActionCellError(
                "player_visible_event_interrupted", report
            )
        if (
            int(post_binding["date_raw"]) <= int(current_binding["date_raw"])
            or int(post_binding["native_revision"])
            <= int(current_binding["native_revision"])
            or post_binding["snapshot_id"] == current_binding["snapshot_id"]
        ):
            raise ProjectsMetricsActionCellError(
                "timeline_did_not_produce_a_later_paused_frame", report
            )
        elapsed_hours = int(post_binding["date_raw"]) - initial_date
        action_row["elapsed_days"] = elapsed_hours / RAW_HOURS_PER_DAY

        try:
            response = service.query_zhongguo_projects_metrics_postcondition_v1(
                _nonce(request_nonce_prefix, f"d{ordinal}", owner),
                expected_revision=int(post_binding["revision"]),
                owner_character_id=owner,
            )
        except Exception as error:
            report["query_error_type"] = type(error).__name__
            report["query_error"] = str(error)
            raise ProjectsMetricsActionCellError(
                "postcondition_query_failed", report
            ) from error
        observation: dict[str, object] = {
            "phase": f"after_{ordinal}",
            "binding": copy.deepcopy(post_binding),
            "response": copy.deepcopy(response),
            "classification": "pending",
            "reason": "metrics_result_not_committed",
        }
        observations = report["provider_observations"]
        if isinstance(observations, list):
            observations.append(observation)
        if _provider_source_is_absent(
            response, binding=post_binding, owner_character_id=owner
        ):
            current_binding = post_binding
            if elapsed_hours >= days_bound * RAW_HOURS_PER_DAY:
                break
            continue
        try:
            current_source = _source_checkpoint(
                response,
                binding=post_binding,
                owner_character_id=owner,
            )
        except ValueError as error:
            observation["classification"] = "blocked"
            observation["reason"] = str(error)
            raise ProjectsMetricsActionCellError(
                "source_checkpoint_regressed", report
            ) from error
        if baseline is not None and current_source != baseline:
            observation["classification"] = "blocked"
            observation["reason"] = "source contribution identity or receipt drifted"
            raise ProjectsMetricsActionCellError(
                "source_checkpoint_drifted", report
            )
        if baseline is None:
            baseline = current_source
            observation["source_checkpoint_first_observed"] = asdict(baseline)
        readiness = response.get("readiness") if isinstance(response, Mapping) else None
        if isinstance(readiness, Mapping) and readiness.get("ready") is True:
            try:
                business = _require_committed_postcondition(
                    response,
                    binding=post_binding,
                    owner_character_id=owner,
                    baseline=baseline,
                )
            except ValueError as error:
                observation["classification"] = "blocked"
                observation["reason"] = str(error)
                raise ProjectsMetricsActionCellError(
                    "provider_postcondition_invalid", report
                ) from error
            observation["classification"] = "postcondition"
            observation["reason"] = None
            observation["business_postcondition"] = business
            action_row["provider_observed_business_postcondition"] = True
            report["result"] = "GREEN"
            report["gameplay_action_complete"] = True
            report["business_postcondition_complete"] = True
            report["terminal_condition"] = (
                "same_cp26_receipt_consumed_by_committed_p3m229_result"
            )
            report["postcondition"] = business
            return report
        current_binding = post_binding
        if elapsed_hours >= days_bound * RAW_HOURS_PER_DAY:
            break

    report["terminal_condition"] = "projects_metrics_postcondition_unobserved"
    raise ProjectsMetricsActionCellError(
        "projects_metrics_postcondition_unobserved", report
    )


__all__ = [
    "ProjectsMetricsActionCellError",
    "ProjectsMetricsActionService",
    "ProjectsMetricsSourceCheckpoint",
    "READINESS",
    "preflight_projects_metrics_gameplay_action_cell",
    "run_projects_metrics_gameplay_action_cell",
]
