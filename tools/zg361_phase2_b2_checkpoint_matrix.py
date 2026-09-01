#!/usr/bin/env python3
"""Same-checkpoint A/B/C acceptance matrix for the ZhongGuo B2 PIP prompt.

This module owns orchestration only.  It composes the existing production
``save-checkpoint`` / ``restore-checkpoint`` service methods, the typed B2
pre-choice queries, and :func:`run_b2_pip_gameplay_action_cell`.  It never
uses OCR, coordinates, synthetic decisions, or an ACK as a postcondition.

The initial service session is transferred to this function.  A successful
run closes every managed CK3 PID after restoring and re-reading the frozen
baseline.  A RED run makes the same best-effort recovery and cleanup attempt
and retains all evidence acquired before the failure.
"""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import re
from typing import Callable, Mapping, Protocol

from zg361_phase2_b2_action_cell import (
    B2_PIP_EVENT_DEFINITION_KEY,
    B2PipActionCellError,
    B2PipActionService,
    _extract_b2_identity,
    _query_b2,
    _require_pending_response,
    _response_projection,
    _snapshot_binding,
    _validate_event_context,
    run_b2_pip_gameplay_action_cell,
)


MATRIX_ACTIONS = ("accept", "negotiate", "refuse")
_OPTION_NUMBER = {"accept": 1, "negotiate": 2, "refuse": 3}
_SHA256_RE = re.compile(r"[0-9A-Fa-f]{64}\Z")


class B2CheckpointMatrixService(B2PipActionService, Protocol):
    """Existing bridge/service primitives consumed by the matrix."""

    def save_checkpoint(
        self, *, expected_revision: int
    ) -> dict[str, object]: ...

    def restore_checkpoint(
        self, *, expected_revision: int
    ) -> dict[str, object]: ...


class B2ManagedProcessLifecycle(Protocol):
    """Small adapter around the runner's existing process owner.

    ``prove_pid_dead`` may poll for a bounded interval.  It must not merely
    echo a shutdown ACK; its returned ``dead`` field is the independently
    observed process-tree result.
    """

    def prove_pid_dead(
        self, pid: int, *, reason: str
    ) -> dict[str, object]: ...

    def stop_session(
        self, pid: int, *, reason: str
    ) -> dict[str, object]: ...


ActionExecutor = Callable[..., dict[str, object]]


class B2PrechoiceInspectionError(RuntimeError):
    """Typed pre-choice query failure retaining the raw provider payloads."""

    def __init__(self, message: str, evidence: dict[str, object]) -> None:
        super().__init__(message)
        self.evidence = evidence


class B2SameCheckpointMatrixError(RuntimeError):
    """Fail-closed matrix result with the final recovery/cleanup report."""

    def __init__(self, message: str, evidence: dict[str, object]) -> None:
        super().__init__(message)
        self.evidence = evidence


class _MatrixContractViolation(RuntimeError):
    pass


class _JsonArtifactStore:
    """Write-once JSON sidecars; existing attempts are never overwritten."""

    def __init__(self, root: Path) -> None:
        if not isinstance(root, Path):
            raise ValueError("artifacts_directory must be a pathlib.Path")
        root.mkdir(parents=True, exist_ok=True)
        if not root.is_dir():
            raise ValueError("artifacts_directory is not a directory")
        self.root = root

    def write(
        self, relative_name: str, payload: Mapping[str, object]
    ) -> dict[str, object]:
        if (
            not isinstance(relative_name, str)
            or not relative_name
            or Path(relative_name).name != relative_name
            or not relative_name.endswith(".json")
        ):
            raise ValueError("artifact name must be one local JSON filename")
        destination = self.root / relative_name
        encoded = (
            json.dumps(
                dict(payload),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
        with destination.open("xb") as stream:
            stream.write(encoded)
        return {
            "relative_path": relative_name,
            "absolute_path": str(destination.resolve()),
            "bytes": len(encoded),
            "sha256": hashlib.sha256(encoded).hexdigest().upper(),
        }


def _positive_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{label} must be a positive integer")
    return value


def _process_binding(
    snapshot: object, *, require_event: bool
) -> dict[str, object]:
    binding = _snapshot_binding(snapshot, require_event=require_event)
    if not isinstance(snapshot, dict):
        raise ValueError("managed snapshot is not an object")
    diagnostics = snapshot.get("diagnostics")
    if not isinstance(diagnostics, dict):
        raise ValueError("managed snapshot lacks diagnostics")
    if diagnostics.get("connected") is not True:
        raise ValueError("managed snapshot bridge is not connected")
    bridge_pid = _positive_int(
        diagnostics.get("bridge_pid"), "snapshot.diagnostics.bridge_pid"
    )
    episode_run_id = snapshot.get("episode_run_id")
    if episode_run_id is not None and (
        not isinstance(episode_run_id, str) or not episode_run_id
    ):
        raise ValueError("snapshot.episode_run_id is malformed")
    return {
        **binding,
        "bridge_pid": bridge_pid,
        "episode_run_id": episode_run_id,
    }


def inspect_b2_pip_prechoice(
    service: B2PipActionService,
    *,
    owner_character_id: int,
    request_nonce: str,
) -> dict[str, object]:
    """Read and validate one real pending ``zg361b2.40`` prompt.

    All raw payloads are retained so callers can persist a useful RED even
    when a later semantic check fails.
    """

    owner_character_id = _positive_int(
        owner_character_id, "owner_character_id"
    )
    if not isinstance(request_nonce, str) or not request_nonce:
        raise ValueError("request_nonce must be a non-empty string")
    evidence: dict[str, object] = {
        "schema_version": 1,
        "result": "RED",
        "query": "zg361.phase2.b2.prechoice",
        "mcp_only": True,
        "ocr_used": False,
        "coordinates_used": False,
        "test_decisions_used": False,
        "raw_snapshot": None,
        "binding": None,
        "raw_event_context": None,
        "raw_b2_snapshot": None,
        "event_definition_key": None,
        "options": None,
        "identity": None,
        "response": None,
        "failure_reason": None,
    }
    try:
        snapshot = service.snapshot()
        evidence["raw_snapshot"] = snapshot
        binding = _process_binding(snapshot, require_event=True)
        evidence["binding"] = binding
        event_instance_id = int(binding["event_instance_id"])
        event_response = service.query_current_event_window_context_v1(
            event_instance_id,
            expected_revision=int(binding["revision"]),
        )
        evidence["raw_event_context"] = event_response
        options = _validate_event_context(
            event_response,
            binding=binding,
            owner_character_id=owner_character_id,
        )
        b2_response = _query_b2(
            service,
            nonce=request_nonce,
            binding=binding,
            owner_character_id=owner_character_id,
        )
        evidence["raw_b2_snapshot"] = b2_response
        identity = _extract_b2_identity(
            b2_response,
            binding=binding,
            owner_character_id=owner_character_id,
        )
        _require_pending_response(b2_response, identity)
        evidence.update(
            {
                "result": "GREEN",
                "event_definition_key": B2_PIP_EVENT_DEFINITION_KEY,
                "options": options,
                "identity": asdict(identity),
                "response": _response_projection(b2_response),
                "failure_reason": None,
            }
        )
        return evidence
    except Exception as error:
        evidence["failure_reason"] = f"{type(error).__name__}: {error}"
        raise B2PrechoiceInspectionError(str(error), evidence) from error


def _semantic_anchor(observation: Mapping[str, object]) -> dict[str, object]:
    binding = observation.get("binding")
    identity = observation.get("identity")
    options = observation.get("options")
    if (
        observation.get("result") != "GREEN"
        or not isinstance(binding, dict)
        or not isinstance(identity, dict)
        or not isinstance(options, list)
    ):
        raise ValueError("pre-choice observation is not GREEN")
    return {
        "event_definition_key": observation.get("event_definition_key"),
        "owner_character_id": identity.get("owner_character_id"),
        "subject_character_id": identity.get("subject_character_id"),
        "cycle_serial": identity.get("cycle_serial"),
        "case_serial": identity.get("case_serial"),
        "state": identity.get("state"),
        "player_character_id": binding.get("player_character_id"),
        "date_raw": binding.get("date_raw"),
        "episode_run_id": binding.get("episode_run_id"),
        "typed_options": options,
    }


def _require_same_semantic_anchor(
    expected: Mapping[str, object],
    observation: Mapping[str, object],
    *,
    label: str,
) -> None:
    observed = _semantic_anchor(observation)
    mismatches = [
        key for key, value in expected.items() if observed.get(key) != value
    ]
    if mismatches:
        raise _MatrixContractViolation(
            f"{label} checkpoint semantic drift: " + ", ".join(mismatches)
        )


def _checkpoint_identity(
    result: object,
    *,
    status: str,
    expected_player_character_id: int,
    expected_date_raw: int,
) -> dict[str, object]:
    if not isinstance(result, dict) or result.get("accepted") is not True:
        raise ValueError("checkpoint command was not acknowledged")
    checkpoint = result.get("checkpoint")
    if not isinstance(checkpoint, dict) or checkpoint.get("status") != status:
        raise ValueError(f"checkpoint does not have {status} status")
    path = checkpoint.get("path")
    name = checkpoint.get("name")
    size = checkpoint.get("size")
    sha256 = checkpoint.get("sha256")
    date_raw = checkpoint.get("date_raw")
    if not isinstance(path, str) or not path:
        raise ValueError("checkpoint path is absent")
    if not isinstance(name, str) or not name:
        raise ValueError("checkpoint name is absent")
    if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
        raise ValueError("checkpoint size is invalid")
    if not isinstance(sha256, str) or _SHA256_RE.fullmatch(sha256) is None:
        raise ValueError("checkpoint SHA-256 is invalid")
    if date_raw != expected_date_raw:
        raise ValueError("checkpoint date differs from the frozen prompt")
    if status == "saved" and (
        checkpoint.get("episode_character_id")
        != expected_player_character_id
    ):
        raise ValueError("checkpoint episode character differs from the subject")
    return {
        "path": path,
        "name": name,
        "size": size,
        "sha256": sha256.lower(),
        "date_raw": date_raw,
    }


def _require_exact_restored_checkpoint(
    expected: Mapping[str, object], observed: Mapping[str, object]
) -> None:
    mismatches = [
        key for key in ("path", "name", "size", "sha256", "date_raw")
        if observed.get(key) != expected.get(key)
    ]
    if mismatches:
        raise _MatrixContractViolation(
            "restored checkpoint bytes/identity drifted: "
            + ", ".join(mismatches)
        )


def _binding_projection(binding: Mapping[str, object]) -> dict[str, object]:
    return {
        key: binding.get(key)
        for key in (
            "snapshot_id",
            "revision",
            "native_revision",
            "date_raw",
            "paused",
            "player_character_id",
            "connection_generation",
            "event_instance_id",
            "event_option_count",
            "bridge_pid",
            "episode_run_id",
        )
    }


class _SingleSubmitServiceProxy:
    """Pin the arm to its freshly observed instance and one submission."""

    def __init__(
        self,
        service: B2CheckpointMatrixService,
        *,
        expected_binding: Mapping[str, object],
        expected_option_number: int,
    ) -> None:
        self._service = service
        self._expected_binding = _binding_projection(expected_binding)
        self._expected_option_number = expected_option_number
        self._first_snapshot_checked = False
        self.submission_count = 0
        self.submissions: list[dict[str, object]] = []

    def snapshot(self) -> dict[str, object]:
        value = self._service.snapshot()
        if not self._first_snapshot_checked:
            observed = _process_binding(value, require_event=True)
            projected = _binding_projection(observed)
            mismatches = [
                key
                for key, expected in self._expected_binding.items()
                if projected.get(key) != expected
            ]
            if mismatches:
                raise _MatrixContractViolation(
                    "stale event instance or checkpoint frame before submit: "
                    + ", ".join(mismatches)
                )
            self._first_snapshot_checked = True
        return value

    def query_current_event_window_context_v1(
        self, event_instance_id: int, *, expected_revision: int
    ) -> dict[str, object]:
        return self._service.query_current_event_window_context_v1(
            event_instance_id, expected_revision=expected_revision
        )

    def query_zhongguo_b2_pip_snapshot_v1(
        self,
        request_nonce: str,
        *,
        expected_revision: int,
        owner_character_id: int,
    ) -> dict[str, object]:
        return self._service.query_zhongguo_b2_pip_snapshot_v1(
            request_nonce,
            expected_revision=expected_revision,
            owner_character_id=owner_character_id,
        )

    def select_event_option(
        self,
        option_number: int,
        *,
        event_instance_id: int,
        expected_revision: int,
    ) -> dict[str, object]:
        if self.submission_count != 0:
            raise _MatrixContractViolation(
                "duplicate option submission attempted in one B2 arm"
            )
        if option_number != self._expected_option_number:
            raise _MatrixContractViolation(
                "B2 arm attempted the wrong typed option"
            )
        if event_instance_id != self._expected_binding["event_instance_id"]:
            raise _MatrixContractViolation(
                "B2 arm attempted a stale event instance"
            )
        self.submission_count += 1
        submission = self._service.select_event_option(
            option_number,
            event_instance_id=event_instance_id,
            expected_revision=expected_revision,
        )
        self.submissions.append(
            {
                "option_number": option_number,
                "event_instance_id": event_instance_id,
                "expected_revision": expected_revision,
                "raw_ack": submission,
            }
        )
        return submission


def _restore_exact_checkpoint(
    service: B2CheckpointMatrixService,
    lifecycle: B2ManagedProcessLifecycle,
    *,
    checkpoint: Mapping[str, object],
    expected_anchor: Mapping[str, object],
    label: str,
) -> tuple[dict[str, object] | None, dict[str, object]]:
    evidence: dict[str, object] = {
        "schema_version": 1,
        "result": "RED",
        "label": label,
        "before_snapshot": None,
        "before_binding": None,
        "raw_restore_result": None,
        "after_snapshot": None,
        "after_binding": None,
        "previous_pid_cleanup": None,
        "checks": {},
        "failure_reason": None,
    }
    after_binding: dict[str, object] | None = None
    try:
        before_snapshot = service.snapshot()
        evidence["before_snapshot"] = before_snapshot
        before = _process_binding(before_snapshot, require_event=False)
        evidence["before_binding"] = before
        result = service.restore_checkpoint(
            expected_revision=int(before["revision"])
        )
        evidence["raw_restore_result"] = result
        after_snapshot = service.snapshot()
        evidence["after_snapshot"] = after_snapshot
        after_binding = _process_binding(after_snapshot, require_event=True)
        evidence["after_binding"] = after_binding
        # Discover the replacement PID and prove the old tree gone before
        # validating the restored checkpoint receipt.  A dishonest/malformed
        # receipt can still have restarted CK3, and that PID must remain in
        # the cleanup lineage of the resulting RED attempt.
        dead_proof = lifecycle.prove_pid_dead(
            int(before["bridge_pid"]), reason=f"{label}: replaced by restore"
        )
        evidence["previous_pid_cleanup"] = dead_proof
        restored = _checkpoint_identity(
            result,
            status="restored",
            expected_player_character_id=int(
                expected_anchor["player_character_id"]
            ),
            expected_date_raw=int(expected_anchor["date_raw"]),
        )
        _require_exact_restored_checkpoint(checkpoint, restored)
        lifecycle_payload = result.get("lifecycle")
        native_lifecycle = (
            lifecycle_payload if isinstance(lifecycle_payload, dict) else {}
        )
        checks = {
            "restore_status": result.get("status") == "restored",
            "new_pid": after_binding["bridge_pid"] != before["bridge_pid"],
            "generation_advanced_once": after_binding[
                "connection_generation"
            ]
            == int(before["connection_generation"]) + 1,
            "same_player": after_binding["player_character_id"]
            == expected_anchor["player_character_id"],
            "same_date": after_binding["date_raw"]
            == expected_anchor["date_raw"],
            "same_episode": after_binding["episode_run_id"]
            == expected_anchor["episode_run_id"],
            "paused": after_binding["paused"] is True,
            "typed_event_present": after_binding["event_instance_id"]
            is not None
            and after_binding["event_option_count"] == 3,
            "lifecycle_previous_pid": native_lifecycle.get("previous_pid")
            == before["bridge_pid"],
            "lifecycle_new_pid": native_lifecycle.get("pid")
            == after_binding["bridge_pid"],
            "lifecycle_intent": native_lifecycle.get("lifecycle_intent")
            == "restore",
            "lifecycle_previous_generation": native_lifecycle.get(
                "previous_connection_generation"
            )
            == before["connection_generation"],
            "lifecycle_new_generation": native_lifecycle.get(
                "connection_generation"
            )
            == after_binding["connection_generation"],
            "previous_pid_dead": isinstance(dead_proof, dict)
            and dead_proof.get("pid") == before["bridge_pid"]
            and dead_proof.get("dead") is True,
        }
        evidence["checks"] = checks
        failed = [name for name, passed in checks.items() if passed is not True]
        if failed:
            raise _MatrixContractViolation(
                f"{label} restore/cleanup contract RED: "
                + ", ".join(failed)
            )
        evidence["result"] = "GREEN"
        return after_binding, evidence
    except Exception as error:
        evidence["failure_reason"] = f"{type(error).__name__}: {error}"
        return after_binding, evidence


def _run_action_arm(
    service: B2CheckpointMatrixService,
    *,
    observation: Mapping[str, object],
    expected_anchor: Mapping[str, object],
    owner_character_id: int,
    action: str,
    action_executor: ActionExecutor,
) -> tuple[dict[str, object] | None, dict[str, object]]:
    binding = observation.get("binding")
    if not isinstance(binding, dict):
        raise ValueError("arm pre-choice observation lacks a binding")
    proxy = _SingleSubmitServiceProxy(
        service,
        expected_binding=binding,
        expected_option_number=_OPTION_NUMBER[action],
    )
    evidence: dict[str, object] = {
        "schema_version": 1,
        "result": "RED",
        "action": action,
        "mcp_only": True,
        "ocr_used": False,
        "coordinates_used": False,
        "test_decisions_used": False,
        "raw_action_cell": None,
        "raw_action_cell_error": None,
        "submit_count": 0,
        "submissions": [],
        "checks": {},
        "failure_reason": None,
    }
    action_result: dict[str, object] | None = None
    try:
        action_result = action_executor(
            proxy,
            owner_character_id=owner_character_id,
            action=action,
            request_nonce_prefix=f"zg361.phase2.b2.matrix.{action}",
        )
        evidence["raw_action_cell"] = action_result
    except B2PipActionCellError as error:
        evidence["raw_action_cell_error"] = error.evidence
        evidence["failure_reason"] = f"{type(error).__name__}: {error}"
    except Exception as error:
        nested = getattr(error, "evidence", None)
        if isinstance(nested, dict):
            evidence["raw_action_cell_error"] = nested
        evidence["failure_reason"] = f"{type(error).__name__}: {error}"
    evidence["submit_count"] = proxy.submission_count
    evidence["submissions"] = proxy.submissions
    if action_result is None:
        return None, evidence

    precondition = action_result.get("precondition")
    postcondition = action_result.get("postcondition")
    pre_identity = (
        precondition.get("identity")
        if isinstance(precondition, dict)
        else None
    )
    pre_binding = (
        precondition.get("binding")
        if isinstance(precondition, dict)
        else None
    )
    post_identity = (
        postcondition.get("identity")
        if isinstance(postcondition, dict)
        else None
    )
    immutable_keys = (
        "owner_character_id",
        "subject_character_id",
        "cycle_serial",
        "case_serial",
    )
    checks = {
        "action_cell_green": action_result.get("result") == "GREEN",
        "independent_postcondition": action_result.get(
            "postcondition_query_green"
        )
        is True
        and action_result.get("ack_is_postcondition") is False,
        "exactly_one_submit": proxy.submission_count == 1,
        "typed_option_number": action_result.get("option_number")
        == _OPTION_NUMBER[action],
        "pre_identity_matches_checkpoint": isinstance(pre_identity, dict)
        and all(
            pre_identity.get(key) == expected_anchor.get(key)
            for key in immutable_keys
        )
        and pre_identity.get("state") == 1,
        "post_identity_same_case": isinstance(post_identity, dict)
        and isinstance(pre_identity, dict)
        and all(
            post_identity.get(key) == pre_identity.get(key)
            for key in immutable_keys
        ),
        "fresh_event_instance_bound": isinstance(pre_binding, dict)
        and pre_binding.get("event_instance_id")
        == binding.get("event_instance_id"),
        "same_prechoice_frame": isinstance(pre_binding, dict)
        and all(
            pre_binding.get(key) == binding.get(key)
            for key in (
                "snapshot_id",
                "revision",
                "native_revision",
                "date_raw",
                "player_character_id",
                "connection_generation",
                "event_instance_id",
                "event_option_count",
            )
        ),
    }
    evidence["checks"] = checks
    failed = [name for name, passed in checks.items() if passed is not True]
    if failed:
        evidence["failure_reason"] = (
            f"{action} action contract RED: " + ", ".join(failed)
        )
        return action_result, evidence
    evidence["result"] = "GREEN"
    evidence["failure_reason"] = None
    return action_result, evidence


def _exception_evidence(error: Exception) -> dict[str, object]:
    nested = getattr(error, "evidence", None)
    return {
        "error_type": type(error).__name__,
        "message": str(error),
        "nested_evidence": nested if isinstance(nested, dict) else None,
    }


def run_b2_same_checkpoint_matrix(
    service: B2CheckpointMatrixService,
    lifecycle: B2ManagedProcessLifecycle,
    *,
    owner_character_id: int,
    artifacts_directory: Path,
    action_executor: ActionExecutor = run_b2_pip_gameplay_action_cell,
) -> dict[str, object]:
    """Run accept/negotiate/refuse from one frozen real PIP checkpoint.

    Every arm starts with a native restart from the same hashed checkpoint.
    Native event instance IDs are deliberately *not* reused across sessions:
    each arm queries its restored instance, pins it through a single-submit
    proxy, and then requires the B2 provider's independent postcondition.
    """

    owner_character_id = _positive_int(
        owner_character_id, "owner_character_id"
    )
    if not callable(action_executor):
        raise ValueError("action_executor must be callable")
    store = _JsonArtifactStore(artifacts_directory)
    report: dict[str, object] = {
        "schema_version": 1,
        "result": "RED",
        "matrix": "zg361.phase2.b2.same-checkpoint-abc",
        "readiness": "static-ready",
        "mcp_only": True,
        "ocr_used": False,
        "coordinates_used": False,
        "test_decisions_used": False,
        "actions": list(MATRIX_ACTIONS),
        "frozen_anchor": None,
        "checkpoint": None,
        "arms": {},
        "final_baseline": None,
        "pid_lineage": [],
        "connection_generation_lineage": [],
        "artifact_receipts": [],
        "recovery": None,
        "cleanup": None,
        "checks": {},
        "failure_reason": None,
    }
    contract_receipt = store.write(
        "00_matrix_contract.json",
        {
            "schema_version": 1,
            "actions": list(MATRIX_ACTIONS),
            "one_frozen_checkpoint": True,
            "restore_before_every_arm": True,
            "final_baseline_restore": True,
            "exactly_one_real_option_per_arm": True,
            "ack_is_postcondition": False,
            "mcp_only": True,
            "ocr_used": False,
            "coordinates_used": False,
            "test_decisions_used": False,
            "live_evidence_claimed": False,
        },
    )
    artifact_receipts = report["artifact_receipts"]
    if not isinstance(artifact_receipts, list):
        raise RuntimeError("matrix artifact receipt list is malformed")
    artifact_receipts.append(contract_receipt)

    checkpoint: dict[str, object] | None = None
    anchor: dict[str, object] | None = None
    current_binding: dict[str, object] | None = None
    tracked_pids: list[int] = []
    tracked_generations: list[int] = []
    final_baseline_restored = False
    final_session_stopped = False

    def remember(binding: Mapping[str, object]) -> None:
        pid = _positive_int(binding.get("bridge_pid"), "binding.bridge_pid")
        generation = _positive_int(
            binding.get("connection_generation"),
            "binding.connection_generation",
        )
        if pid not in tracked_pids:
            tracked_pids.append(pid)
            tracked_generations.append(generation)
        report["pid_lineage"] = list(tracked_pids)
        report["connection_generation_lineage"] = list(tracked_generations)

    def persist(name: str, payload: Mapping[str, object]) -> None:
        artifact_receipts.append(store.write(name, payload))

    try:
        try:
            initial = inspect_b2_pip_prechoice(
                service,
                owner_character_id=owner_character_id,
                request_nonce="zg361.phase2.b2.matrix.initial",
            )
        except B2PrechoiceInspectionError as error:
            persist("01_initial_prechoice_raw.json", error.evidence)
            raise
        persist("01_initial_prechoice_raw.json", initial)
        initial_binding = initial["binding"]
        if not isinstance(initial_binding, dict):
            raise _MatrixContractViolation("initial pre-choice binding is absent")
        remember(initial_binding)
        current_binding = dict(initial_binding)
        initial_anchor = _semantic_anchor(initial)

        save_result: dict[str, object] | None = None
        try:
            save_result = service.save_checkpoint(
                expected_revision=int(initial_binding["revision"])
            )
            checkpoint = _checkpoint_identity(
                save_result,
                status="saved",
                expected_player_character_id=int(
                    initial_anchor["player_character_id"]
                ),
                expected_date_raw=int(initial_anchor["date_raw"]),
            )
        except Exception as error:
            persist(
                "02_frozen_checkpoint_raw.json",
                {
                    "schema_version": 1,
                    "result": "RED",
                    "raw_save_result": save_result,
                    "checkpoint": checkpoint,
                    "post_save_prechoice": None,
                    "failure_reason": f"{type(error).__name__}: {error}",
                },
            )
            raise
        try:
            post_save = inspect_b2_pip_prechoice(
                service,
                owner_character_id=owner_character_id,
                request_nonce="zg361.phase2.b2.matrix.post-save",
            )
        except B2PrechoiceInspectionError as error:
            persist(
                "02_frozen_checkpoint_raw.json",
                {
                    "result": "RED",
                    "raw_save_result": save_result,
                    "checkpoint": checkpoint,
                    "post_save_prechoice": error.evidence,
                    "failure_reason": str(error),
                },
            )
            raise
        try:
            _require_same_semantic_anchor(
                initial_anchor, post_save, label="post-save"
            )
            anchor = _semantic_anchor(post_save)
            current_binding_value = post_save.get("binding")
            if not isinstance(current_binding_value, dict):
                raise _MatrixContractViolation(
                    "post-save binding is absent"
                )
            current_binding = dict(current_binding_value)
            save_frame_mismatches = [
                key
                for key in (
                    "bridge_pid",
                    "connection_generation",
                    "date_raw",
                    "player_character_id",
                    "episode_run_id",
                    "event_instance_id",
                    "event_option_count",
                )
                if current_binding.get(key) != initial_binding.get(key)
            ]
            if save_frame_mismatches:
                raise _MatrixContractViolation(
                    "save-checkpoint escaped its pending event frame: "
                    + ", ".join(save_frame_mismatches)
                )
        except Exception as error:
            persist(
                "02_frozen_checkpoint_raw.json",
                {
                    "schema_version": 1,
                    "result": "RED",
                    "raw_save_result": save_result,
                    "checkpoint": checkpoint,
                    "initial_prechoice_anchor": initial_anchor,
                    "post_save_prechoice": post_save,
                    "failure_reason": f"{type(error).__name__}: {error}",
                },
            )
            raise
        remember(current_binding)
        frozen_payload = {
            "schema_version": 1,
            "result": "GREEN",
            "raw_save_result": save_result,
            "checkpoint": checkpoint,
            "initial_prechoice_anchor": initial_anchor,
            "post_save_prechoice": post_save,
            "frozen_anchor": anchor,
        }
        persist("02_frozen_checkpoint_raw.json", frozen_payload)
        report["checkpoint"] = checkpoint
        report["frozen_anchor"] = anchor

        arms = report["arms"]
        if not isinstance(arms, dict):
            raise RuntimeError("matrix arm report is malformed")
        for ordinal, action in enumerate(MATRIX_ACTIONS, start=1):
            restore_binding, restore_evidence = _restore_exact_checkpoint(
                service,
                lifecycle,
                checkpoint=checkpoint,
                expected_anchor=anchor,
                label=f"{action} independent restore",
            )
            persist(f"{ordinal}0_{action}_restore_raw.json", restore_evidence)
            if restore_binding is not None:
                current_binding = dict(restore_binding)
                remember(current_binding)
            if restore_evidence.get("result") != "GREEN":
                raise _MatrixContractViolation(
                    str(restore_evidence.get("failure_reason"))
                )

            try:
                observation = inspect_b2_pip_prechoice(
                    service,
                    owner_character_id=owner_character_id,
                    request_nonce=f"zg361.phase2.b2.matrix.{action}.pre",
                )
            except B2PrechoiceInspectionError as error:
                persist(
                    f"{ordinal}1_{action}_prechoice_raw.json",
                    error.evidence,
                )
                raise
            persist(
                f"{ordinal}1_{action}_prechoice_raw.json", observation
            )
            _require_same_semantic_anchor(
                anchor, observation, label=f"{action} pre-choice"
            )
            observed_binding = observation.get("binding")
            if not isinstance(observed_binding, dict):
                raise _MatrixContractViolation(
                    f"{action} observation lacks a managed binding"
                )
            current_binding = dict(observed_binding)
            remember(current_binding)

            action_result, action_evidence = _run_action_arm(
                service,
                observation=observation,
                expected_anchor=anchor,
                owner_character_id=owner_character_id,
                action=action,
                action_executor=action_executor,
            )
            persist(
                f"{ordinal}2_{action}_action_raw.json", action_evidence
            )
            arms[action] = {
                "result": action_evidence.get("result"),
                "restore": restore_evidence,
                "prechoice": observation,
                "action": action_evidence,
            }
            if action_evidence.get("result") != "GREEN":
                raise _MatrixContractViolation(
                    str(action_evidence.get("failure_reason"))
                )
            if not isinstance(action_result, dict):
                raise _MatrixContractViolation(
                    f"{action} action lacks a typed result"
                )

        final_binding, final_restore = _restore_exact_checkpoint(
            service,
            lifecycle,
            checkpoint=checkpoint,
            expected_anchor=anchor,
            label="final baseline restore",
        )
        persist("40_final_restore_raw.json", final_restore)
        if final_binding is not None:
            current_binding = dict(final_binding)
            remember(current_binding)
        if final_restore.get("result") != "GREEN":
            raise _MatrixContractViolation(
                str(final_restore.get("failure_reason"))
            )
        try:
            final_observation = inspect_b2_pip_prechoice(
                service,
                owner_character_id=owner_character_id,
                request_nonce="zg361.phase2.b2.matrix.final",
            )
        except B2PrechoiceInspectionError as error:
            persist("41_final_prechoice_raw.json", error.evidence)
            raise
        persist("41_final_prechoice_raw.json", final_observation)
        _require_same_semantic_anchor(
            anchor, final_observation, label="final baseline"
        )
        final_baseline_restored = True
        report["final_baseline"] = {
            "restore": final_restore,
            "prechoice": final_observation,
        }

        if current_binding is None:
            raise _MatrixContractViolation("final managed PID is unknown")
        final_pid = int(current_binding["bridge_pid"])
        shutdown = lifecycle.stop_session(
            final_pid, reason="B2 same-checkpoint matrix complete"
        )
        dead_proof = lifecycle.prove_pid_dead(
            final_pid, reason="B2 same-checkpoint matrix final cleanup"
        )
        shutdown_payload = {
            "raw_shutdown": shutdown,
            "dead_proof": dead_proof,
        }
        persist("42_final_shutdown_raw.json", shutdown_payload)
        final_session_stopped = (
            isinstance(shutdown, dict)
            and shutdown.get("ck3_pid") == final_pid
            and shutdown.get("ok") is True
            and shutdown.get("cleanup_proven") is True
            and shutdown.get("tree_gone") is True
            and isinstance(dead_proof, dict)
            and dead_proof.get("pid") == final_pid
            and dead_proof.get("dead") is True
        )
        if not final_session_stopped:
            raise _MatrixContractViolation(
                "final restored session cleanup was not independently proven"
            )

        pid_proofs = [
            lifecycle.prove_pid_dead(
                pid, reason="B2 same-checkpoint final lineage audit"
            )
            for pid in tracked_pids
        ]
        cleanup_payload = {
            "schema_version": 1,
            "result": "GREEN"
            if all(
                isinstance(row, dict)
                and row.get("pid") == pid
                and row.get("dead") is True
                for pid, row in zip(tracked_pids, pid_proofs)
            )
            else "RED",
            "tracked_pids": list(tracked_pids),
            "proofs": pid_proofs,
        }
        persist("43_pid_lineage_cleanup_raw.json", cleanup_payload)
        if cleanup_payload["result"] != "GREEN":
            raise _MatrixContractViolation(
                "one or more managed PIDs leaked after matrix cleanup"
            )
        report["cleanup"] = cleanup_payload

        expected_generations = list(
            range(
                tracked_generations[0],
                tracked_generations[0] + len(tracked_generations),
            )
        )
        checks = {
            "one_checkpoint_saved": checkpoint is not None,
            "three_arms_green": set(arms) == set(MATRIX_ACTIONS)
            and all(
                isinstance(arms.get(action), dict)
                and arms[action].get("result") == "GREEN"
                for action in MATRIX_ACTIONS
            ),
            "four_exact_restores": len(tracked_pids) == 5,
            "pid_lineage_unique": len(set(tracked_pids))
            == len(tracked_pids),
            "connection_generations_consecutive": tracked_generations
            == expected_generations,
            "final_baseline_restored": final_baseline_restored,
            "all_managed_pids_dead": cleanup_payload["result"] == "GREEN",
            "no_ocr_coordinates_or_test_decisions": report["mcp_only"] is True
            and report["ocr_used"] is False
            and report["coordinates_used"] is False
            and report["test_decisions_used"] is False,
        }
        report["checks"] = checks
        failed = [name for name, passed in checks.items() if passed is not True]
        if failed:
            raise _MatrixContractViolation(
                "matrix final checks RED: " + ", ".join(failed)
            )
        report["result"] = "GREEN"
        report["failure_reason"] = None
        persist("99_b2_same_checkpoint_matrix.json", report)
        return report
    except Exception as error:
        report["failure_reason"] = f"{type(error).__name__}: {error}"
        recovery: dict[str, object] = {
            "attempted": False,
            "restore": None,
            "prechoice": None,
            "shutdown": None,
            "pid_proofs": [],
            "baseline_restored": False,
            "all_tracked_pids_dead": False,
            "errors": [],
        }
        report["recovery"] = recovery
        if checkpoint is not None and anchor is not None:
            recovery["attempted"] = True
            recovery_binding, recovery_restore = _restore_exact_checkpoint(
                service,
                lifecycle,
                checkpoint=checkpoint,
                expected_anchor=anchor,
                label="RED recovery final baseline restore",
            )
            persist("90_recovery_restore_raw.json", recovery_restore)
            recovery["restore"] = recovery_restore
            if recovery_binding is not None:
                current_binding = dict(recovery_binding)
                remember(current_binding)
            if recovery_restore.get("result") == "GREEN":
                try:
                    recovery_observation = inspect_b2_pip_prechoice(
                        service,
                        owner_character_id=owner_character_id,
                        request_nonce="zg361.phase2.b2.matrix.recovery",
                    )
                    _require_same_semantic_anchor(
                        anchor,
                        recovery_observation,
                        label="RED recovery baseline",
                    )
                    recovery["prechoice"] = recovery_observation
                    recovery["baseline_restored"] = True
                    persist(
                        "91_recovery_prechoice_raw.json",
                        recovery_observation,
                    )
                except Exception as recovery_error:
                    nested = getattr(recovery_error, "evidence", None)
                    recovery_payload = (
                        nested
                        if isinstance(nested, dict)
                        else _exception_evidence(recovery_error)
                    )
                    persist(
                        "91_recovery_prechoice_raw.json", recovery_payload
                    )
                    errors = recovery["errors"]
                    if isinstance(errors, list):
                        errors.append(_exception_evidence(recovery_error))
            else:
                errors = recovery["errors"]
                if isinstance(errors, list):
                    errors.append(
                        {
                            "error_type": "RestoreContractRed",
                            "message": str(
                                recovery_restore.get("failure_reason")
                            ),
                            "nested_evidence": recovery_restore,
                        }
                    )

        try:
            discovered_snapshot = service.snapshot()
            discovered_binding = _process_binding(
                discovered_snapshot, require_event=False
            )
            current_binding = discovered_binding
            remember(discovered_binding)
        except Exception as discovery_error:
            errors = recovery["errors"]
            if isinstance(errors, list):
                errors.append(_exception_evidence(discovery_error))

        if current_binding is not None and not final_session_stopped:
            final_pid = int(current_binding["bridge_pid"])
            try:
                shutdown = lifecycle.stop_session(
                    final_pid, reason="B2 same-checkpoint matrix RED cleanup"
                )
                dead = lifecycle.prove_pid_dead(
                    final_pid,
                    reason="B2 same-checkpoint matrix RED final PID",
                )
                recovery["shutdown"] = {
                    "raw_shutdown": shutdown,
                    "dead_proof": dead,
                }
                persist("92_recovery_shutdown_raw.json", recovery["shutdown"])
            except Exception as cleanup_error:
                errors = recovery["errors"]
                if isinstance(errors, list):
                    errors.append(_exception_evidence(cleanup_error))

        proofs: list[dict[str, object]] = []
        for pid in tracked_pids:
            try:
                proof = lifecycle.prove_pid_dead(
                    pid, reason="B2 same-checkpoint RED lineage audit"
                )
            except Exception as proof_error:
                proof = {
                    "pid": pid,
                    "dead": False,
                    "error": _exception_evidence(proof_error),
                }
            proofs.append(proof)
        recovery["pid_proofs"] = proofs
        recovery["all_tracked_pids_dead"] = all(
            row.get("pid") == pid and row.get("dead") is True
            for pid, row in zip(tracked_pids, proofs)
        )
        persist(
            "93_recovery_pid_lineage_cleanup_raw.json",
            {
                "tracked_pids": list(tracked_pids),
                "proofs": proofs,
                "all_tracked_pids_dead": recovery[
                    "all_tracked_pids_dead"
                ],
            },
        )
        report["pid_lineage"] = list(tracked_pids)
        report["connection_generation_lineage"] = list(tracked_generations)
        report["cleanup"] = {
            "result": "GREEN"
            if recovery["all_tracked_pids_dead"] is True
            else "RED",
            "proofs": proofs,
        }
        persist("99_b2_same_checkpoint_matrix.json", report)
        raise B2SameCheckpointMatrixError(str(error), report) from error


__all__ = [
    "B2CheckpointMatrixService",
    "B2ManagedProcessLifecycle",
    "B2PrechoiceInspectionError",
    "B2SameCheckpointMatrixError",
    "MATRIX_ACTIONS",
    "inspect_b2_pip_prechoice",
    "run_b2_same_checkpoint_matrix",
]
