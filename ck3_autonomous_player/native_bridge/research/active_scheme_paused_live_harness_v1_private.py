#!/usr/bin/env python3
"""Reusable raw-first harness for one hash-bound paused active-scheme action."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Protocol


SCHEMA = "active-scheme-paused-live-harness-v1-private"
CANDIDATE_SCHEMA = "active-scheme-paused-live-candidate-v1-private"
REPORT_SCHEMA = "active-scheme-paused-live-report-v1-private"
EXACT_VERSION = "1.19.0.6"
EXACT_EXE_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
INTERACTIONS = {
    "sway_interaction": ("sway", "0x5783F850"),
    "start_murder_interaction": ("murder", "0xDF3F9819"),
}
MURDER_STARTERS = {
    "agent_focus_balance",
    "agent_focus_success",
    "agent_focus_speed",
    "agent_focus_secrecy",
}
STAGES = ("snapshot", "definition", "precondition", "submit_ack", "receipt")


class CandidateError(ValueError):
    def __init__(self, failure: str, message: str) -> None:
        super().__init__(message)
        self.failure = failure


@dataclass(frozen=True)
class ArtifactBinding:
    role: str
    path: Path
    relative_path: str
    size: int
    sha256: str


@dataclass(frozen=True)
class Candidate:
    manifest_path: Path
    manifest_sha256: str
    candidate_id: str
    request_id: str
    interaction_key: str
    scheme_type_key: str
    actor_character_id: int
    target_character_id: int
    selected_starter_package: str
    expected_capture_epoch: int
    expected_container_generation: int
    expected_date_raw: int
    artifacts: tuple[ArtifactBinding, ...]


class PausedLiveBackend(Protocol):
    def capture_snapshot(self, candidate: Candidate) -> bytes: ...

    def resolve_definition(
        self, candidate: Candidate, snapshot: Mapping[str, Any]
    ) -> bytes: ...

    def capture_precondition(
        self,
        candidate: Candidate,
        snapshot: Mapping[str, Any],
        definition: Mapping[str, Any],
    ) -> bytes: ...

    def submit_once(
        self,
        candidate: Candidate,
        snapshot: Mapping[str, Any],
        definition: Mapping[str, Any],
        precondition: Mapping[str, Any],
    ) -> bytes: ...

    def verify_fresh_receipt(
        self, candidate: Candidate, submit_ack: Mapping[str, Any]
    ) -> bytes: ...


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _digest(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise CandidateError("candidate_contract", f"{field} must be a SHA-256")
    normalized = value.upper()
    if len(normalized) != 64 or any(ch not in "0123456789ABCDEF" for ch in normalized):
        raise CandidateError("candidate_contract", f"{field} must be a SHA-256")
    return normalized


def _integer(value: Any, field: str, *, positive: bool = False) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise CandidateError("candidate_contract", f"{field} must be an integer")
    if positive and value <= 0:
        raise CandidateError("candidate_contract", f"{field} must be positive")
    return value


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise CandidateError("candidate_contract", f"{field} must be nonempty text")
    return value


def _relative_artifact(manifest: Path, value: Any) -> tuple[str, Path]:
    relative = _text(value, "artifact.path").replace("\\", "/")
    pure = PurePosixPath(relative)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise CandidateError(
            "candidate_contract", "artifact paths must be portable relative paths"
        )
    resolved = (manifest.parent / Path(*pure.parts)).resolve()
    root = manifest.parent.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise CandidateError(
            "candidate_contract", "artifact path leaves candidate directory"
        ) from exc
    return relative, resolved


def load_candidate(manifest_path: Path, expected_manifest_sha256: str) -> Candidate:
    """Hash the manifest before parsing, then bind every referenced artifact."""

    manifest = manifest_path.resolve()
    expected = _digest(expected_manifest_sha256, "expected_manifest_sha256")
    try:
        raw = manifest.read_bytes()
    except OSError as exc:
        raise CandidateError("candidate_unavailable", str(exc)) from exc
    actual = _sha256_bytes(raw)
    if actual != expected:
        raise CandidateError(
            "candidate_hash_mismatch", f"candidate manifest {actual} != {expected}"
        )
    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CandidateError("candidate_contract", "candidate JSON is invalid") from exc
    if not isinstance(payload, dict) or payload.get("schema") != CANDIDATE_SCHEMA:
        raise CandidateError("candidate_contract", "candidate schema mismatch")
    build = payload.get("build")
    action = payload.get("action")
    if not isinstance(build, dict) or not isinstance(action, dict):
        raise CandidateError("candidate_contract", "build/action object missing")
    if build.get("game_version") != EXACT_VERSION:
        raise CandidateError("exact_build_mismatch", "game version mismatch")
    if _digest(build.get("executable_sha256"), "build.executable_sha256") != EXACT_EXE_SHA256:
        raise CandidateError("exact_build_mismatch", "executable SHA mismatch")

    interaction = _text(action.get("interaction_key"), "action.interaction_key")
    if interaction not in INTERACTIONS:
        raise CandidateError("interaction_not_allowed", interaction)
    scheme_type, _ = INTERACTIONS[interaction]
    if action.get("scheme_type_key") != scheme_type:
        raise CandidateError("candidate_contract", "interaction/type mapping mismatch")
    actor = _integer(action.get("actor_character_id"), "actor_character_id", positive=True)
    target = _integer(action.get("target_character_id"), "target_character_id", positive=True)
    if actor == target:
        raise CandidateError("candidate_contract", "actor and target must differ")
    starter = action.get("selected_starter_package", "")
    if not isinstance(starter, str):
        raise CandidateError("candidate_contract", "starter package must be text")
    if interaction == "sway_interaction" and starter:
        raise CandidateError("starter_package_invalid", "sway has no starter package")
    if interaction == "start_murder_interaction" and starter not in MURDER_STARTERS:
        raise CandidateError("starter_package_invalid", "murder starter is invalid")

    artifact_rows = payload.get("artifacts")
    if not isinstance(artifact_rows, list) or not artifact_rows:
        raise CandidateError("candidate_contract", "at least one artifact is required")
    artifacts: list[ArtifactBinding] = []
    roles: set[str] = set()
    for row in artifact_rows:
        if not isinstance(row, dict):
            raise CandidateError("candidate_contract", "artifact row must be an object")
        role = _text(row.get("role"), "artifact.role")
        if role in roles:
            raise CandidateError("candidate_contract", f"duplicate artifact role: {role}")
        roles.add(role)
        relative, path = _relative_artifact(manifest, row.get("path"))
        size = _integer(row.get("size"), "artifact.size")
        sha = _digest(row.get("sha256"), "artifact.sha256")
        if not path.is_file():
            raise CandidateError("candidate_artifact_unavailable", f"missing {role}: {path}")
        if path.stat().st_size != size or _sha256_file(path) != sha:
            raise CandidateError("candidate_artifact_hash_mismatch", role)
        artifacts.append(ArtifactBinding(role, path, relative, size, sha))

    return Candidate(
        manifest_path=manifest,
        manifest_sha256=actual,
        candidate_id=_text(payload.get("candidate_id"), "candidate_id"),
        request_id=_text(action.get("request_id"), "action.request_id"),
        interaction_key=interaction,
        scheme_type_key=scheme_type,
        actor_character_id=actor,
        target_character_id=target,
        selected_starter_package=starter,
        expected_capture_epoch=_integer(
            action.get("expected_capture_epoch"), "expected_capture_epoch", positive=True
        ),
        expected_container_generation=_integer(
            action.get("expected_container_generation"),
            "expected_container_generation",
            positive=True,
        ),
        expected_date_raw=_integer(action.get("expected_date_raw"), "expected_date_raw"),
        artifacts=tuple(artifacts),
    )


def _write_exclusive(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _claim(candidate: Candidate, ledger_dir: Path) -> Path:
    marker = ledger_dir / f"{candidate.manifest_sha256}.attempt.json"
    payload = {
        "schema": SCHEMA,
        "candidate_id": candidate.candidate_id,
        "candidate_manifest_sha256": candidate.manifest_sha256,
        "consumed": True,
        "status": "claimed",
    }
    try:
        _write_exclusive(marker, _json_bytes(payload))
    except FileExistsError as exc:
        raise CandidateError("candidate_already_consumed", str(marker)) from exc
    except OSError as exc:
        raise CandidateError("candidate_claim_failed", str(exc)) from exc
    return marker


def _update_marker(marker: Path, report: Mapping[str, Any]) -> None:
    payload = {
        "schema": SCHEMA,
        "candidate_id": report["candidate_id"],
        "candidate_manifest_sha256": report["candidate_manifest_sha256"],
        "consumed": True,
        "status": report["status"],
        "failure": report["failure"],
        "submit_call_count": report["submit_call_count"],
    }
    temporary = marker.with_name(marker.name + f".tmp-{os.getpid()}")
    _write_exclusive(temporary, _json_bytes(payload))
    os.replace(temporary, marker)


def _raw_path(evidence_dir: Path, candidate: Candidate, stage: str) -> Path:
    return evidence_dir / f"{candidate.manifest_sha256}.{stage}.raw.json"


def _persist_and_parse(
    evidence_dir: Path, candidate: Candidate, stage: str, raw: bytes
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(raw, bytes) or not raw:
        raise CandidateError(f"{stage}_capture_failed", "backend returned no raw bytes")
    path = _raw_path(evidence_dir, candidate, stage)
    try:
        _write_exclusive(path, raw)
    except OSError as exc:
        raise CandidateError(f"{stage}_raw_storage_failed", str(exc)) from exc
    binding = {
        "path": path.name,
        "size": len(raw),
        "sha256": _sha256_bytes(raw),
    }
    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CandidateError(f"{stage}_raw_invalid", "raw JSON is invalid") from exc
    if not isinstance(payload, dict):
        raise CandidateError(f"{stage}_raw_invalid", "raw stage must be an object")
    return payload, binding


def _require(condition: bool, failure: str, message: str) -> None:
    if not condition:
        raise CandidateError(failure, message)


def _validate_snapshot(candidate: Candidate, value: Mapping[str, Any]) -> None:
    _require(value.get("status") == "available", "snapshot_unavailable", "snapshot unavailable")
    _require(value.get("application_main_thread") is True, "snapshot_thread_mismatch", "not application main thread")
    _require(value.get("paused") is True, "snapshot_not_paused", "snapshot is not paused")
    _require(value.get("game_version") == EXACT_VERSION and value.get("executable_sha256") == EXACT_EXE_SHA256, "exact_build_mismatch", "snapshot build mismatch")
    _require(value.get("capture_epoch") == candidate.expected_capture_epoch, "snapshot_mismatch", "capture epoch mismatch")
    _require(value.get("container_generation") == candidate.expected_container_generation, "snapshot_mismatch", "container generation mismatch")
    _require(value.get("date_raw") == candidate.expected_date_raw, "snapshot_mismatch", "date mismatch")
    _require(value.get("played_character_id") == candidate.actor_character_id, "snapshot_mismatch", "actor mismatch")


def _validate_definition(candidate: Candidate, value: Mapping[str, Any]) -> None:
    _, stable_hash = INTERACTIONS[candidate.interaction_key]
    _require(value.get("identity_round_trip") is True, "definition_unavailable", "definition identity unavailable")
    _require(value.get("interaction_key") == candidate.interaction_key and value.get("scheme_type_key") == candidate.scheme_type_key, "definition_mismatch", "definition key/type mismatch")
    _require(value.get("stable_key_hash") == stable_hash, "definition_mismatch", "definition hash mismatch")
    _require(isinstance(value.get("definition_generation"), int) and value["definition_generation"] > 0, "definition_unavailable", "definition generation unavailable")
    _require(isinstance(value.get("proof_epoch"), int) and value["proof_epoch"] > 0, "definition_unavailable", "definition proof epoch unavailable")


def _preview_valid(value: Any) -> bool:
    if not isinstance(value, dict) or value.get("status") not in {"available", "explicitly_unavailable"}:
        return False
    return value.get("status") != "available" or (
        isinstance(value.get("value"), int)
        and not isinstance(value.get("value"), bool)
        and 0 <= value["value"] <= 100
    )


def _validate_precondition(candidate: Candidate, snapshot: Mapping[str, Any], value: Mapping[str, Any]) -> None:
    _require(value.get("available") is True and value.get("paused") is True, "precondition_unavailable", "precondition unavailable")
    _require(value.get("capture_epoch") == snapshot.get("capture_epoch") and value.get("date_raw") == snapshot.get("date_raw"), "precondition_mismatch", "precondition frame mismatch")
    _require(value.get("actor_character_id") == candidate.actor_character_id and value.get("target_kind") == "character" and value.get("target_id") == candidate.target_character_id, "precondition_mismatch", "precondition identity mismatch")
    _require(value.get("interaction_key") == candidate.interaction_key and value.get("scheme_type_key") == candidate.scheme_type_key, "precondition_mismatch", "precondition key/type mismatch")
    _require(value.get("shown_evaluated") is True and value.get("shown") is True, "interaction_not_shown", "interaction not shown")
    _require(value.get("validity_evaluated") is True and value.get("valid") is True, "interaction_not_valid", "interaction invalid")
    _require(value.get("can_start_scheme_evaluated") is True and value.get("can_start_scheme") is True, "can_start_scheme_denied", "can-start denied")
    previews = [value.get(name) for name in ("success_chance", "maximum_success_chance", "secrecy")]
    _require(all(_preview_valid(preview) for preview in previews), "preview_unresolved", "preview unresolved or invalid")
    if previews[0]["status"] == previews[1]["status"] == "available":
        _require(previews[0]["value"] <= previews[1]["value"], "preview_invalid", "success exceeds maximum")
    if candidate.interaction_key == "start_murder_interaction":
        _require(value.get("starter_options_evaluated") is True and value.get("starter_options_exclusive") is True and value.get("starter_option_count") == 4 and value.get("selected_starter_package") == candidate.selected_starter_package, "starter_package_invalid", "murder starter mismatch")
    else:
        _require(not value.get("selected_starter_package"), "starter_package_invalid", "sway starter must be absent")


def _validate_ack(candidate: Candidate, snapshot: Mapping[str, Any], value: Mapping[str, Any]) -> None:
    _require(value.get("status") == "submitted_verification_pending" and value.get("failure") == "none", "submit_rejected", "submit ACK rejected")
    _require(value.get("submit_attempted") is True and value.get("submit_call_count") == 1 and value.get("verification_pending") is True, "submit_ack_invalid", "submit ACK is not single/pending")
    _require(value.get("request_id") == candidate.request_id and value.get("interaction_key") == candidate.interaction_key and value.get("scheme_type_key") == candidate.scheme_type_key, "submit_ack_invalid", "submit ACK identity mismatch")
    _require(value.get("actor_character_id") == candidate.actor_character_id and value.get("target_kind") == "character" and value.get("target_id") == candidate.target_character_id, "submit_ack_invalid", "submit ACK target mismatch")
    _require(value.get("pre_capture_epoch") == snapshot.get("capture_epoch") and value.get("pre_container_generation") == snapshot.get("container_generation") and value.get("pre_date_raw") == snapshot.get("date_raw"), "submit_ack_invalid", "submit ACK snapshot mismatch")


def _validate_receipt(candidate: Candidate, snapshot: Mapping[str, Any], value: Mapping[str, Any]) -> None:
    _require(value.get("status") == "applied" and value.get("failure") == "none" and value.get("postcondition_verified") is True, "receipt_red", "fresh receipt is not applied")
    _require(value.get("request_id") == candidate.request_id, "receipt_mismatch", "receipt request mismatch")
    _require(isinstance(value.get("post_capture_epoch"), int) and value["post_capture_epoch"] > snapshot["capture_epoch"], "receipt_not_fresh", "receipt snapshot is not fresh")
    _require(isinstance(value.get("scheme_instance_id"), int) and value["scheme_instance_id"] > 0 and isinstance(value.get("scheme_instance_generation"), int) and value["scheme_instance_generation"] > 0, "receipt_mismatch", "new scheme identity unavailable")


def validate_completed_stage_payloads(
    candidate: Candidate, payloads: Mapping[str, Mapping[str, Any]]
) -> None:
    """Independently validate a persisted five-stage transaction."""

    snapshot = payloads["snapshot"]
    definition = payloads["definition"]
    precondition = payloads["precondition"]
    submit_ack = payloads["submit_ack"]
    receipt = payloads["receipt"]
    _validate_snapshot(candidate, snapshot)
    _validate_definition(candidate, definition)
    _validate_precondition(candidate, snapshot, precondition)
    _validate_ack(candidate, snapshot, submit_ack)
    _validate_receipt(candidate, snapshot, receipt)


def run_candidate(
    candidate: Candidate,
    backend: PausedLiveBackend,
    *,
    evidence_dir: Path,
    ledger_dir: Path,
) -> dict[str, Any]:
    """Consume one candidate and run exactly one ordered live transaction."""

    report: dict[str, Any] = {
        "schema": REPORT_SCHEMA,
        "candidate_id": candidate.candidate_id,
        "candidate_manifest": candidate.manifest_path.name,
        "candidate_manifest_sha256": candidate.manifest_sha256,
        "interaction_key": candidate.interaction_key,
        "scheme_type_key": candidate.scheme_type_key,
        "status": "RED",
        "failure": "candidate_claim_failed",
        "reason": "",
        "submit_call_count": 0,
        "same_candidate_retry_allowed": False,
        "events": [],
        "raw_artifacts": {},
    }
    try:
        marker = _claim(candidate, ledger_dir)
    except CandidateError as exc:
        report["failure"] = exc.failure
        report["reason"] = str(exc)
        return report

    def stage(name: str, invoke: Any) -> dict[str, Any]:
        ordinal = len(report["events"]) + 1
        report["events"].append({"ordinal": ordinal, "stage": name, "status": "started"})
        try:
            raw = invoke()
        except Exception as exc:
            raise CandidateError(f"{name}_capture_failed", str(exc)) from exc
        payload, binding = _persist_and_parse(evidence_dir, candidate, name, raw)
        report["raw_artifacts"][name] = binding
        report["events"][-1]["status"] = "raw_persisted_before_parse"
        return payload

    try:
        snapshot = stage("snapshot", lambda: backend.capture_snapshot(candidate))
        _validate_snapshot(candidate, snapshot)
        definition = stage(
            "definition", lambda: backend.resolve_definition(candidate, snapshot)
        )
        _validate_definition(candidate, definition)
        precondition = stage(
            "precondition",
            lambda: backend.capture_precondition(candidate, snapshot, definition),
        )
        _validate_precondition(candidate, snapshot, precondition)
        report["submit_call_count"] = 1
        ack = stage(
            "submit_ack",
            lambda: backend.submit_once(
                candidate, snapshot, definition, precondition
            ),
        )
        _validate_ack(candidate, snapshot, ack)
        receipt = stage(
            "receipt", lambda: backend.verify_fresh_receipt(candidate, ack)
        )
        _validate_receipt(candidate, snapshot, receipt)
        report["status"] = "GREEN"
        report["failure"] = "none"
    except CandidateError as exc:
        report["failure"] = exc.failure
        report["reason"] = str(exc)
        if report["events"]:
            report["events"][-1]["status"] = "RED"

    report_path = evidence_dir / f"{candidate.manifest_sha256}.report.json"
    report["attempt_marker"] = marker.name
    report["report_path"] = report_path.name
    try:
        _update_marker(marker, report)
        _write_exclusive(report_path, _json_bytes(report))
    except OSError as exc:
        report["status"] = "RED"
        report["failure"] = "report_storage_failed"
        report["reason"] = str(exc)
    return report
