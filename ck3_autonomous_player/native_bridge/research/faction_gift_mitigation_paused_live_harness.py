#!/usr/bin/env python3
"""Raw-first, one-submit paused-live harness for faction gift mitigation v1."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Protocol


CONTRACT = "g2-m4-faction-gift-mitigation-paused-live-harness-v1"
CANDIDATE_CONTRACT = "g2-m4-faction-gift-mitigation-candidate-v1"
GAME_VERSION = "1.19.0.6"
EXECUTABLE_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
GOLD_SCALE = 100_000
RETRY_POLICY = "forbid-same-candidate-after-submit-claim"


class RedType(str, Enum):
    NONE = "none"
    CONFIG = "config_red"
    CANDIDATE_MANIFEST_HASH = "candidate_manifest_hash_red"
    CANDIDATE_FILE_HASH = "candidate_file_hash_red"
    CANDIDATE_RETRY_FORBIDDEN = "candidate_retry_forbidden_red"
    TRANSPORT = "transport_red"
    TARGETING = "targeting_red"
    GATE = "gate_red"
    SUBMIT_ACK = "submit_ack_red"
    RECEIPT = "receipt_red"


@dataclass(frozen=True)
class RawStepResult:
    returncode: int
    stdout: bytes
    stderr: bytes = b""


class StepTransport(Protocol):
    def call(self, step: str, request: dict[str, Any]) -> RawStepResult: ...


class SubprocessStepTransport:
    def __init__(self, command: list[str], timeout_seconds: int) -> None:
        self._command = tuple(command)
        self._timeout_seconds = timeout_seconds

    def call(self, step: str, request: dict[str, Any]) -> RawStepResult:
        payload = json.dumps(
            request, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
        try:
            completed = subprocess.run(
                [*self._command, "--step", step],
                input=payload,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self._timeout_seconds,
                check=False,
            )
            return RawStepResult(
                completed.returncode, completed.stdout, completed.stderr
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            return RawStepResult(127, b"", str(error).encode("utf-8"))


@dataclass
class HarnessResult:
    terminal: str = "red"
    red_type: str = RedType.CONFIG.value
    phase: str = "admission"
    reason: str = "uninitialized"
    candidate_id: str = ""
    candidate_commit: str = ""
    candidate_manifest_sha256: str = ""
    submit_claimed: bool = False
    submit_ack_pending: bool = False
    receipt_status: str | None = None
    postcondition_verified: bool = False


class HarnessRed(RuntimeError):
    def __init__(self, red_type: RedType, phase: str, reason: str) -> None:
        super().__init__(reason)
        self.red_type = red_type
        self.phase = phase
        self.reason = reason


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def _read_json(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("JSON root must be an object")
    return raw, value


def _is_sha256(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    return all(character in "0123456789abcdefABCDEF" for character in value)


def _is_commit(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 40:
        return False
    return all(character in "0123456789abcdefABCDEF" for character in value)


def _integer(value: object, *, minimum: int | None = None) -> bool:
    if type(value) is not int:
        return False
    return minimum is None or value >= minimum


def _full_id(value: object) -> bool:
    return _integer(value, minimum=1) and value <= 0xFFFFFFFF


def _artifact_path(manifest_path: Path, relative: object) -> Path:
    if not isinstance(relative, str) or not relative:
        raise ValueError("candidate file path is missing")
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("candidate file path must be portable and relative")
    return manifest_path.parent / path


def _validate_admission(
    runtime_path: Path, candidate_path: Path
) -> tuple[dict[str, Any], dict[str, Any], str]:
    _, runtime = _read_json(runtime_path)
    candidate_raw, candidate = _read_json(candidate_path)
    manifest_sha = _sha256_bytes(candidate_raw)
    if (
        runtime.get("schema_version") != 1
        or runtime.get("contract") != CONTRACT
        or runtime.get("raw_first") is not True
        or runtime.get("launch_ck3") is not False
        or runtime.get("retry_policy") != RETRY_POLICY
    ):
        raise HarnessRed(RedType.CONFIG, "admission", "runtime_contract_invalid")
    exact = runtime.get("exact_build")
    policy = runtime.get("policy")
    command = runtime.get("transport_command")
    if (
        not isinstance(exact, dict)
        or exact.get("game_version") != GAME_VERSION
        or exact.get("executable_sha256") != EXECUTABLE_SHA256
        or not isinstance(policy, dict)
        or policy.get("gold_scale") != GOLD_SCALE
        or not _integer(policy.get("minimum_gold_reserve_raw"), minimum=0)
        or not isinstance(command, list)
        or not command
        or not all(isinstance(part, str) and part for part in command)
        or not _integer(runtime.get("transport_timeout_seconds"), minimum=1)
        or runtime["transport_timeout_seconds"] > 60
    ):
        raise HarnessRed(RedType.CONFIG, "admission", "runtime_inputs_invalid")
    expected = runtime.get("candidate")
    if (
        not isinstance(expected, dict)
        or not _is_sha256(expected.get("manifest_sha256"))
        or expected["manifest_sha256"].upper() != manifest_sha
    ):
        raise HarnessRed(
            RedType.CANDIDATE_MANIFEST_HASH,
            "admission",
            "candidate_manifest_hash_mismatch",
        )
    if (
        candidate.get("schema_version") != 1
        or candidate.get("contract") != CANDIDATE_CONTRACT
        or not isinstance(candidate.get("candidate_id"), str)
        or not candidate["candidate_id"]
        or not _is_commit(candidate.get("commit"))
        or expected.get("candidate_id") != candidate["candidate_id"]
        or expected.get("commit") != candidate["commit"]
    ):
        raise HarnessRed(
            RedType.CANDIDATE_MANIFEST_HASH,
            "admission",
            "candidate_identity_mismatch",
        )
    candidate_exact = candidate.get("exact_build")
    if (
        not isinstance(candidate_exact, dict)
        or candidate_exact != exact
        or not isinstance(candidate.get("files"), list)
        or not candidate["files"]
    ):
        raise HarnessRed(
            RedType.CANDIDATE_MANIFEST_HASH,
            "admission",
            "candidate_contract_invalid",
        )
    for entry in candidate["files"]:
        if (
            not isinstance(entry, dict)
            or not _is_sha256(entry.get("sha256"))
        ):
            raise HarnessRed(
                RedType.CANDIDATE_FILE_HASH,
                "admission",
                "candidate_file_contract_invalid",
            )
        try:
            artifact = _artifact_path(candidate_path, entry.get("path"))
            actual = _sha256_bytes(artifact.read_bytes())
        except (OSError, ValueError):
            raise HarnessRed(
                RedType.CANDIDATE_FILE_HASH,
                "admission",
                "candidate_file_unreadable",
            ) from None
        if actual != entry["sha256"].upper():
            raise HarnessRed(
                RedType.CANDIDATE_FILE_HASH,
                "admission",
                "candidate_file_hash_mismatch",
            )
    return runtime, candidate, manifest_sha


def _write_exclusive(path: Path, value: bytes) -> None:
    with path.open("xb") as output:
        output.write(value)
        output.flush()
        os.fsync(output.fileno())


def _write_result(artifact_dir: Path, result: HarnessResult) -> None:
    payload = json.dumps(
        asdict(result), ensure_ascii=False, indent=2, sort_keys=True
    ).encode("utf-8") + b"\n"
    path = artifact_dir / "harness-result.json"
    if path.exists():
        path.unlink()
    _write_exclusive(path, payload)


def _call_raw_first(
    transport: StepTransport,
    artifact_dir: Path,
    ordinal: int,
    step: str,
    request: dict[str, Any],
) -> dict[str, Any]:
    stem = f"{ordinal:02d}-{step}"
    request_raw = json.dumps(
        request, ensure_ascii=False, indent=2, sort_keys=True
    ).encode("utf-8") + b"\n"
    _write_exclusive(artifact_dir / f"{stem}.request.json", request_raw)
    raw = transport.call(step, request)
    _write_exclusive(artifact_dir / f"{stem}.stdout.raw", raw.stdout)
    _write_exclusive(artifact_dir / f"{stem}.stderr.raw", raw.stderr)
    meta = json.dumps(
        {"returncode": raw.returncode, "step": step},
        sort_keys=True,
    ).encode("utf-8") + b"\n"
    _write_exclusive(artifact_dir / f"{stem}.meta.json", meta)
    if raw.returncode != 0:
        raise HarnessRed(RedType.TRANSPORT, step, "transport_nonzero_exit")
    try:
        value = json.loads(raw.stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise HarnessRed(RedType.TRANSPORT, step, "transport_json_invalid") from None
    if not isinstance(value, dict):
        raise HarnessRed(RedType.TRANSPORT, step, "transport_result_not_object")
    return value


def _targeting_request(
    candidate: dict[str, Any], manifest_sha: str
) -> dict[str, Any]:
    return {
        "contract": CONTRACT,
        "candidate_id": candidate["candidate_id"],
        "candidate_commit": candidate["commit"],
        "candidate_manifest_sha256": manifest_sha,
        "require_paused": True,
        "require_targeting_row": True,
    }


def _validate_targeting(
    value: dict[str, Any], minimum_reserve: int
) -> dict[str, Any]:
    preview = value.get("gift_preview")
    if (
        value.get("status") != "ready"
        or value.get("paused") is not True
        or value.get("red_flags") != 0
        or not _integer(value.get("snapshot_revision"), minimum=1)
        or not _integer(value.get("native_snapshot_revision"), minimum=1)
        or not _integer(value.get("date_raw"))
        or not _full_id(value.get("player_character_id"))
        or not _full_id(value.get("source_faction_id"))
        or not _full_id(value.get("recipient_character_id"))
        or value.get("recipient_character_id") == value.get("player_character_id")
        or value.get("membership_role") not in {"leader", "character_member"}
        or value.get("source_faction_targeting_player") is not True
        or value.get("source_faction_at_war") is not False
        or not _integer(value.get("player_gold_raw"))
        or not isinstance(preview, dict)
        or preview.get("available") is not True
        or preview.get("definition_key") != "gift_interaction"
        or not _integer(preview.get("definition_stable_hash"), minimum=1)
        or preview.get("interaction_legal") is not True
        or preview.get("auto_accept") is not True
        or not _integer(preview.get("gold_cost_raw"), minimum=1)
        or preview.get("gold_scale") != GOLD_SCALE
        or not _integer(preview.get("opinion_delta"), minimum=1)
        or value["player_gold_raw"] - preview["gold_cost_raw"] < minimum_reserve
    ):
        raise HarnessRed(RedType.TARGETING, "targeting", "targeting_contract_red")
    token = value["source_faction_id"]
    recipient = value["recipient_character_id"]
    request_id = f"gift:{value['snapshot_revision']}:{token:08x}:{recipient:08x}"
    return {
        "request_id": request_id,
        "idempotency_key": request_id,
        "expected_revision": value["snapshot_revision"],
        "expected_native_revision": value["native_snapshot_revision"],
        "expected_date_raw": value["date_raw"],
        "player_character_id": value["player_character_id"],
        "source_faction_id": token,
        "recipient_character_id": recipient,
        "membership_role": value["membership_role"],
        "expected_definition_key": preview["definition_key"],
        "expected_definition_stable_hash": preview["definition_stable_hash"],
        "expected_gold_cost_raw": preview["gold_cost_raw"],
        "expected_gold_scale": preview["gold_scale"],
        "expected_opinion_delta": preview["opinion_delta"],
        "minimum_gold_reserve_raw": minimum_reserve,
        "minimum_gold_reserve_scale": GOLD_SCALE,
        "pre_player_gold_raw": value["player_gold_raw"],
    }


def _same_binding(value: dict[str, Any], request: dict[str, Any]) -> bool:
    return (
        value.get("player_character_id") == request["player_character_id"]
        and value.get("source_faction_id") == request["source_faction_id"]
        and value.get("recipient_character_id") == request["recipient_character_id"]
    )


def _validate_gate(value: dict[str, Any], request: dict[str, Any]) -> None:
    if (
        value.get("terminal") != "ready"
        or value.get("red_flags") != 0
        or value.get("ready_for_single_submit") is not True
        or value.get("action_callbacks_invoked") is not False
        or value.get("snapshot_revision") != request["expected_revision"]
        or value.get("native_snapshot_revision")
        != request["expected_native_revision"]
        or value.get("date_raw") != request["expected_date_raw"]
        or value.get("player_gold_raw") != request["pre_player_gold_raw"]
        or value.get("gift_gold_cost_raw") != request["expected_gold_cost_raw"]
        or value.get("minimum_gold_reserve_raw")
        != request["minimum_gold_reserve_raw"]
        or not _same_binding(value, request)
    ):
        raise HarnessRed(RedType.GATE, "gate", "integration_gate_red")


def _claim_candidate(state_dir: Path, candidate: dict[str, Any], sha: str) -> Path:
    state_dir.mkdir(parents=True, exist_ok=True)
    ledger = state_dir / f"{sha}.submit-claim.json"
    payload = json.dumps(
        {
            "candidate_id": candidate["candidate_id"],
            "candidate_commit": candidate["commit"],
            "candidate_manifest_sha256": sha,
            "state": "submit_claimed_no_retry",
        },
        indent=2,
        sort_keys=True,
    ).encode("utf-8") + b"\n"
    try:
        _write_exclusive(ledger, payload)
    except FileExistsError:
        raise HarnessRed(
            RedType.CANDIDATE_RETRY_FORBIDDEN,
            "submit",
            "candidate_submit_already_claimed",
        ) from None
    return ledger


def _validate_ack(value: dict[str, Any], request: dict[str, Any]) -> None:
    forbidden = {
        "success",
        "applied",
        "mitigation_applied",
        "postcondition_verified",
        "threat_resolved",
    }
    if (
        forbidden.intersection(value)
        or value.get("status") != "submitted_verification_pending"
        or value.get("verification_pending") is not True
        or value.get("request_id") != request["request_id"]
        or value.get("pre_snapshot_revision") != request["expected_revision"]
        or value.get("pre_native_snapshot_revision")
        != request["expected_native_revision"]
        or value.get("pre_observed_date_raw") != request["expected_date_raw"]
        or value.get("expected_gold_cost_raw")
        != request["expected_gold_cost_raw"]
        or value.get("expected_opinion_delta")
        != request["expected_opinion_delta"]
        or not _same_binding(value, request)
    ):
        raise HarnessRed(RedType.SUBMIT_ACK, "submit", "submit_ack_not_pending")


def _validate_receipt(value: dict[str, Any], request: dict[str, Any]) -> str:
    status = value.get("status")
    if (
        status not in {"mitigated", "left"}
        or value.get("request_id") != request["request_id"]
        or value.get("postcondition_verified") is not True
        or value.get("mitigation_applied") is not True
        or not _integer(value.get("post_snapshot_revision"), minimum=1)
        or value["post_snapshot_revision"] <= request["expected_revision"]
        or not _integer(value.get("post_native_snapshot_revision"), minimum=1)
        or value["post_native_snapshot_revision"]
        <= request["expected_native_revision"]
        or value.get("post_observed_date_raw") != request["expected_date_raw"]
        or value.get("post_player_gold_raw")
        != request["pre_player_gold_raw"] - request["expected_gold_cost_raw"]
        or value.get("post_gift_opinion_present") is not True
        or value.get("post_gift_opinion_modifier_value")
        != request["expected_opinion_delta"]
        or not _same_binding(value, request)
        or (status == "mitigated" and value.get("threat_resolved") is not False)
        or (status == "left" and value.get("threat_resolved") is not True)
    ):
        raise HarnessRed(RedType.RECEIPT, "receipt", "fresh_receipt_red")
    return status


def run_harness(
    runtime_config_path: Path,
    candidate_manifest_path: Path,
    artifact_dir: Path,
    *,
    state_dir: Path,
    transport: StepTransport | None = None,
) -> HarnessResult:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    result = HarnessResult()
    try:
        runtime, candidate, manifest_sha = _validate_admission(
            runtime_config_path, candidate_manifest_path
        )
        result.candidate_id = candidate["candidate_id"]
        result.candidate_commit = candidate["commit"]
        result.candidate_manifest_sha256 = manifest_sha
        ledger = state_dir / f"{manifest_sha}.submit-claim.json"
        if ledger.exists():
            raise HarnessRed(
                RedType.CANDIDATE_RETRY_FORBIDDEN,
                "admission",
                "candidate_submit_already_claimed",
            )
        if transport is None:
            transport = SubprocessStepTransport(
                runtime["transport_command"],
                runtime["transport_timeout_seconds"],
            )
        base = _targeting_request(candidate, manifest_sha)
        targeting = _call_raw_first(transport, artifact_dir, 1, "targeting", base)
        request = _validate_targeting(
            targeting, runtime["policy"]["minimum_gold_reserve_raw"]
        )
        gate = _call_raw_first(
            transport,
            artifact_dir,
            2,
            "gate",
            {**base, "action_request": request, "targeting_raw": targeting},
        )
        _validate_gate(gate, request)
        _claim_candidate(state_dir, candidate, manifest_sha)
        result.submit_claimed = True
        ack = _call_raw_first(
            transport,
            artifact_dir,
            3,
            "submit",
            {**base, "action_request": request, "gate_raw": gate},
        )
        _validate_ack(ack, request)
        result.submit_ack_pending = True
        receipt = _call_raw_first(
            transport,
            artifact_dir,
            4,
            "receipt",
            {
                **base,
                "action_request": request,
                "submit_ack_raw": ack,
                "require_fresh_paused_requery": True,
            },
        )
        result.receipt_status = _validate_receipt(receipt, request)
        result.postcondition_verified = True
        result.terminal = "green"
        result.red_type = RedType.NONE.value
        result.phase = "receipt"
        result.reason = ""
    except HarnessRed as error:
        result.terminal = "red"
        result.red_type = error.red_type.value
        result.phase = error.phase
        result.reason = error.reason
    except (OSError, ValueError, json.JSONDecodeError) as error:
        result.terminal = "red"
        result.red_type = RedType.CONFIG.value
        result.phase = "admission"
        result.reason = type(error).__name__
    _write_result(artifact_dir, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-config", type=Path, required=True)
    parser.add_argument("--candidate-manifest", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--state-dir", type=Path, required=True)
    arguments = parser.parse_args()
    result = run_harness(
        arguments.runtime_config,
        arguments.candidate_manifest,
        arguments.artifact_dir,
        state_dir=arguments.state_dir,
    )
    print(json.dumps(asdict(result), ensure_ascii=False, sort_keys=True))
    return 0 if result.terminal == "green" else 1


if __name__ == "__main__":
    raise SystemExit(main())
