#!/usr/bin/env python3
"""Standalone normal/-O tests for the private active-scheme live harness."""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any, Mapping

from active_scheme_paused_live_harness_v1_private import (
    CANDIDATE_SCHEMA,
    EXACT_EXE_SHA256,
    EXACT_VERSION,
    Candidate,
    CandidateError,
    load_candidate,
    run_candidate,
)
from verify_active_scheme_paused_live_harness_v1_private import verify_report


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def encoded(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, sort_keys=True) + "\n").encode("utf-8")


def write_candidate(root: Path, interaction: str) -> tuple[Path, str]:
    root.mkdir(parents=True)
    artifact = root / "candidate.bin"
    artifact.write_bytes(("candidate-" + interaction).encode("ascii"))
    artifact_hash = hashlib.sha256(artifact.read_bytes()).hexdigest().upper()
    murder = interaction == "start_murder_interaction"
    manifest = {
        "schema": CANDIDATE_SCHEMA,
        "candidate_id": "fixture-" + ("murder" if murder else "sway"),
        "build": {
            "game_version": EXACT_VERSION,
            "executable_sha256": EXACT_EXE_SHA256,
        },
        "action": {
            "request_id": "request-" + ("murder" if murder else "sway"),
            "interaction_key": interaction,
            "scheme_type_key": "murder" if murder else "sway",
            "actor_character_id": 0x0100002A,
            "target_character_id": 0x01000039,
            "selected_starter_package": "agent_focus_speed" if murder else "",
            "expected_capture_epoch": 17,
            "expected_container_generation": 71,
            "expected_date_raw": 53_175_816,
        },
        "artifacts": [
            {
                "role": "private_bridge_candidate",
                "path": "candidate.bin",
                "size": artifact.stat().st_size,
                "sha256": artifact_hash,
            }
        ],
    }
    path = root / "candidate.json"
    path.write_bytes(encoded(manifest))
    return path, hashlib.sha256(path.read_bytes()).hexdigest().upper()


class FakeBackend:
    def __init__(self, evidence_dir: Path, failure: str = "") -> None:
        self.evidence_dir = evidence_dir
        self.failure = failure
        self.order: list[str] = []
        self.submit_calls = 0

    def _entered(self, candidate: Candidate, stage: str, prior: str = "") -> None:
        if prior:
            prior_path = self.evidence_dir / (
                f"{candidate.manifest_sha256}.{prior}.raw.json"
            )
            require(prior_path.is_file(), f"{stage} ran before {prior} raw persisted")
        self.order.append(stage)

    def capture_snapshot(self, candidate: Candidate) -> bytes:
        self._entered(candidate, "snapshot")
        if self.failure == "malformed_snapshot":
            return b"{"
        return encoded(
            {
                "status": "available",
                "application_main_thread": True,
                "paused": True,
                "game_version": EXACT_VERSION,
                "executable_sha256": EXACT_EXE_SHA256,
                "capture_epoch": candidate.expected_capture_epoch,
                "container_generation": candidate.expected_container_generation,
                "date_raw": candidate.expected_date_raw,
                "played_character_id": candidate.actor_character_id,
            }
        )

    def resolve_definition(
        self, candidate: Candidate, snapshot: Mapping[str, Any]
    ) -> bytes:
        self._entered(candidate, "definition", "snapshot")
        stable_hash = (
            "0x5783F850"
            if candidate.interaction_key == "sway_interaction"
            else "0xDF3F9819"
        )
        if self.failure == "definition_mismatch":
            stable_hash = "0x00000001"
        return encoded(
            {
                "identity_round_trip": True,
                "interaction_key": candidate.interaction_key,
                "scheme_type_key": candidate.scheme_type_key,
                "stable_key_hash": stable_hash,
                "definition_generation": 81,
                "proof_epoch": 900,
            }
        )

    def capture_precondition(
        self,
        candidate: Candidate,
        snapshot: Mapping[str, Any],
        definition: Mapping[str, Any],
    ) -> bytes:
        self._entered(candidate, "precondition", "definition")
        murder = candidate.interaction_key == "start_murder_interaction"
        allowed = self.failure != "precondition_denied"
        available = {"status": "available", "value": 61}
        explicit = {"status": "explicitly_unavailable", "value": 0}
        return encoded(
            {
                "available": True,
                "paused": True,
                "capture_epoch": snapshot["capture_epoch"],
                "date_raw": snapshot["date_raw"],
                "actor_character_id": candidate.actor_character_id,
                "target_kind": "character",
                "target_id": candidate.target_character_id,
                "interaction_key": candidate.interaction_key,
                "scheme_type_key": candidate.scheme_type_key,
                "shown_evaluated": True,
                "shown": True,
                "validity_evaluated": True,
                "valid": True,
                "can_start_scheme_evaluated": True,
                "can_start_scheme": allowed,
                "starter_options_evaluated": murder,
                "starter_options_exclusive": murder,
                "starter_option_count": 4 if murder else 0,
                "selected_starter_package": candidate.selected_starter_package,
                "success_chance": available if murder else explicit,
                "maximum_success_chance": {
                    "status": "available",
                    "value": 95,
                }
                if murder
                else explicit,
                "secrecy": {
                    "status": "available",
                    "value": 73,
                }
                if murder
                else explicit,
                "definition_generation": definition["definition_generation"],
            }
        )

    def submit_once(
        self,
        candidate: Candidate,
        snapshot: Mapping[str, Any],
        definition: Mapping[str, Any],
        precondition: Mapping[str, Any],
    ) -> bytes:
        self._entered(candidate, "submit_ack", "precondition")
        self.submit_calls += 1
        if self.failure == "submit_rejected":
            return encoded(
                {
                    "status": "rejected_before_submit",
                    "failure": "submit_rejected",
                    "submit_attempted": True,
                    "submit_call_count": 1,
                    "verification_pending": False,
                }
            )
        return encoded(
            {
                "status": "submitted_verification_pending",
                "failure": "none",
                "submit_attempted": True,
                "submit_call_count": 1,
                "verification_pending": True,
                "request_id": candidate.request_id,
                "interaction_key": candidate.interaction_key,
                "scheme_type_key": candidate.scheme_type_key,
                "actor_character_id": candidate.actor_character_id,
                "target_kind": "character",
                "target_id": candidate.target_character_id,
                "pre_capture_epoch": snapshot["capture_epoch"],
                "pre_container_generation": snapshot["container_generation"],
                "pre_date_raw": snapshot["date_raw"],
                "definition_generation": definition["definition_generation"],
                "can_start_scheme": precondition["can_start_scheme"],
            }
        )

    def verify_fresh_receipt(
        self, candidate: Candidate, submit_ack: Mapping[str, Any]
    ) -> bytes:
        self._entered(candidate, "receipt", "submit_ack")
        epoch = candidate.expected_capture_epoch
        if self.failure != "stale_receipt":
            epoch += 1
        return encoded(
            {
                "status": "applied",
                "failure": "none",
                "request_id": submit_ack["request_id"],
                "post_capture_epoch": epoch,
                "post_container_generation":
                    candidate.expected_container_generation + 1,
                "post_date_raw": candidate.expected_date_raw + 1,
                "scheme_instance_id": 0x0000000200000042,
                "scheme_instance_generation": 8,
                "postcondition_verified": True,
            }
        )


def run_fixture(root: Path, interaction: str, failure: str = "") -> tuple[dict[str, Any], FakeBackend, Candidate, Path, Path]:
    candidate_path, candidate_hash = write_candidate(root / "candidate", interaction)
    candidate = load_candidate(candidate_path, candidate_hash)
    evidence = root / "evidence"
    ledger = root / "ledger"
    backend = FakeBackend(evidence, failure)
    report = run_candidate(candidate, backend, evidence_dir=evidence, ledger_dir=ledger)
    return report, backend, candidate, evidence, ledger


def test_sway_and_murder_green_and_no_retry(root: Path) -> None:
    for index, interaction in enumerate(
        ("sway_interaction", "start_murder_interaction")
    ):
        report, backend, candidate, evidence, ledger = run_fixture(
            root / f"green-{index}", interaction
        )
        require(report["status"] == "GREEN", f"{interaction} was RED")
        require(backend.order == ["snapshot", "definition", "precondition", "submit_ack", "receipt"], "pipeline order mismatch")
        require(backend.submit_calls == 1 and report["submit_call_count"] == 1, "submit count mismatch")
        report_path = evidence / report["report_path"]
        errors = verify_report(
            report_path,
            candidate.manifest_path,
            candidate.manifest_sha256,
            ledger,
        )
        require(not errors, "GREEN verifier errors: " + "; ".join(errors))
        retry = run_candidate(candidate, backend, evidence_dir=evidence, ledger_dir=ledger)
        require(retry["status"] == "RED" and retry["failure"] == "candidate_already_consumed", "same candidate retry was not RED")
        require(backend.submit_calls == 1, "same candidate submitted twice")


def test_typed_red_matrix(root: Path) -> None:
    cases = (
        ("definition_mismatch", "definition_mismatch", 0),
        ("precondition_denied", "can_start_scheme_denied", 0),
        ("submit_rejected", "submit_rejected", 1),
        ("stale_receipt", "receipt_not_fresh", 1),
    )
    for index, (mode, failure, submits) in enumerate(cases):
        report, backend, candidate, evidence, ledger = run_fixture(
            root / f"red-{index}", "sway_interaction", mode
        )
        require(report["status"] == "RED" and report["failure"] == failure, f"wrong typed RED for {mode}")
        require(backend.submit_calls == submits, f"wrong submit count for {mode}")
        retry = run_candidate(candidate, backend, evidence_dir=evidence, ledger_dir=ledger)
        require(retry["failure"] == "candidate_already_consumed", f"{mode} retry was not blocked")
        require(backend.submit_calls == submits, f"{mode} retried submit")


def test_raw_persisted_before_parse(root: Path) -> None:
    report, backend, candidate, evidence, ledger = run_fixture(
        root / "malformed", "sway_interaction", "malformed_snapshot"
    )
    require(report["status"] == "RED" and report["failure"] == "snapshot_raw_invalid", "malformed raw was not typed RED")
    raw = evidence / f"{candidate.manifest_sha256}.snapshot.raw.json"
    require(raw.is_file() and raw.read_bytes() == b"{", "malformed raw was not preserved first")
    retry = run_candidate(candidate, backend, evidence_dir=evidence, ledger_dir=ledger)
    require(retry["failure"] == "candidate_already_consumed" and backend.submit_calls == 0, "malformed candidate retried")


def test_candidate_hash_binding(root: Path) -> None:
    path, digest = write_candidate(root / "hash", "sway_interaction")
    try:
        load_candidate(path, "0" * 64)
    except CandidateError as exc:
        require(exc.failure == "candidate_hash_mismatch", "wrong manifest hash RED")
    else:
        raise RuntimeError("manifest hash mismatch was accepted")
    candidate = load_candidate(path, digest)
    candidate.artifacts[0].path.write_bytes(b"tampered")
    try:
        load_candidate(path, digest)
    except CandidateError as exc:
        require(exc.failure == "candidate_artifact_hash_mismatch", "wrong artifact hash RED")
    else:
        raise RuntimeError("artifact hash mismatch was accepted")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="scheme8-harness-") as temporary:
        root = Path(temporary)
        test_sway_and_murder_green_and_no_retry(root)
        test_typed_red_matrix(root)
        test_raw_persisted_before_parse(root)
        test_candidate_hash_binding(root)
    print("active scheme paused-live harness normal/-O fixtures: GREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
