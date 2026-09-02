#!/usr/bin/env python3
"""Static handshake for the next Phase-2 native observer.

The module deliberately knows no new hook address.  It binds a native-team
seam manifest to the frozen seed runner inputs and to the already-observed
0x817C20 list-domain fact and the verified producer seam before the runner may
cross its launch boundary.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any


SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")
GIT_SHA = re.compile(r"^[0-9a-fA-F]{40}$")
RVA = re.compile(r"^0x[0-9A-Fa-f]+$")
CONTRACT_KIND = "zg361_phase2_list_domain_acceptance_contract"
MANIFEST_KIND = "zg361_phase2_native_observer_seam"
GATE_KIND = "zg361_phase2_acceptance_observer_gate"


class ObserverGateError(ValueError):
    """The frozen observer handshake is absent or inconsistent."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ObserverGateError(f"{label} is not readable JSON: {error}") from error
    if not isinstance(value, dict):
        raise ObserverGateError(f"{label} root must be an object")
    return value


def _require_sha(value: object, label: str) -> str:
    if not isinstance(value, str) or SHA256.fullmatch(value) is None:
        raise ObserverGateError(f"{label} must be a SHA-256 hex digest")
    return value.lower()


def _source_artifact(
    clean_source: Path, row: object, label: str
) -> dict[str, Any]:
    if not isinstance(row, dict):
        raise ObserverGateError(f"{label} must be an object")
    raw_path = row.get("path")
    if not isinstance(raw_path, str) or not raw_path:
        raise ObserverGateError(f"{label}.path is missing")
    relative = Path(raw_path)
    if relative.is_absolute():
        raise ObserverGateError(f"{label}.path must be source-relative")
    source_root = clean_source.resolve()
    path = (source_root / relative).resolve()
    try:
        path.relative_to(source_root)
    except ValueError as error:
        raise ObserverGateError(f"{label}.path escapes the clean source") from error
    if not path.is_file():
        raise ObserverGateError(f"{label} is missing from the clean source: {raw_path}")
    expected = _require_sha(row.get("sha256"), f"{label}.sha256")
    observed = _sha256(path)
    if observed != expected:
        raise ObserverGateError(
            f"{label} hash mismatch: expected {expected}, observed {observed}"
        )
    return {"path": relative.as_posix(), "bytes": path.stat().st_size, "sha256": observed}


def evaluate_observer_gate(
    *,
    contract_path: Path,
    observer_manifest_path: Path | None,
    clean_source: Path,
    frozen_git_commit: str,
    game_version: str,
    game_executable_sha256: str,
    bridge_dll_sha256: str,
    bridge_injector_sha256: str,
    source_zip_sha256: str,
    clean_source_tree_sha256: str,
    pipe_name: str,
) -> dict[str, Any]:
    """Return a replayable GREEN gate or a typed waiting/RED gate."""

    contract = _load_object(contract_path, "acceptance observer contract")
    if contract.get("schema_version") != 1 or contract.get("kind") != CONTRACT_KIND:
        raise ObserverGateError("acceptance observer contract schema/kind mismatch")
    known = contract.get("known_live_input")
    producer_v1 = contract.get("producer_v1_live_input")
    seam_contract = contract.get("native_seam")
    if not all(isinstance(row, dict) for row in (known, producer_v1, seam_contract)):
        raise ObserverGateError("acceptance observer contract sections are malformed")
    assert isinstance(known, dict) and isinstance(producer_v1, dict)
    assert isinstance(seam_contract, dict)
    if known.get("callback_slot2_rva") != "0x817C20":
        raise ObserverGateError("known list-domain callback slot2 binding drifted")
    if known.get("repeat_live_forbidden") is not True:
        raise ObserverGateError("known list-domain attempt must remain non-repeatable")
    if (
        producer_v1.get("producer_0x3B9CFD2_entry_count") != 1838
        or producer_v1.get("producer_0x3B9CFD7_entry_count") != 1838
        or producer_v1.get("last_callback_slot2_rva") != "0x817C20"
        or producer_v1.get("repeat_live_forbidden") is not True
    ):
        raise ObserverGateError("producer v1 last-only live input drifted")
    required_fields = seam_contract.get("required_report_fields")
    if not isinstance(required_fields, list) or not all(
        isinstance(field, str) and field for field in required_fields
    ):
        raise ObserverGateError("native seam required_report_fields is malformed")

    base: dict[str, Any] = {
        "schema_version": 1,
        "kind": GATE_KIND,
        "result": "RED",
        "status": "waiting-producer-histogram-v2",
        "runner_observer_gate_ready": False,
        "launch_authorized_by_gate": False,
        "contract": {
            "path": str(contract_path.resolve()),
            "bytes": contract_path.stat().st_size,
            "sha256": _sha256(contract_path),
        },
        "known_live_input": known,
        "producer_v1_live_input": producer_v1,
        "observer_manifest": None,
        "pending_native_seam_fields": [
            "hooks[0x3B9CFD2].anchor_sha256",
            "hooks[0x3B9CFD7].anchor_sha256",
            "private_build_option",
            "abi.path",
            "abi.sha256",
            "source_contract.path",
            "source_contract.sha256",
            "report_contract.schema",
            "report_contract.artifact_name",
            "report_contract.required_fields",
            "session_binding.source_zip_sha256",
            "session_binding.clean_source_tree_sha256",
            "session_binding.pipe_name",
        ],
        "failure_reason": "native_observer_manifest_pending",
    }
    if observer_manifest_path is None:
        return base

    manifest_path = observer_manifest_path.resolve()
    manifest = _load_object(manifest_path, "native observer seam manifest")
    base["observer_manifest"] = {
        "path": str(manifest_path),
        "bytes": manifest_path.stat().st_size,
        "sha256": _sha256(manifest_path),
    }
    try:
        if manifest.get("schema_version") != 1 or manifest.get("kind") != MANIFEST_KIND:
            raise ObserverGateError("native observer seam manifest schema/kind mismatch")
        if manifest.get("result") != "GREEN":
            raise ObserverGateError("native observer seam manifest is not GREEN")
        source_commit = manifest.get("source_git_commit")
        if not isinstance(source_commit, str) or GIT_SHA.fullmatch(source_commit) is None:
            raise ObserverGateError("source_git_commit must be a full Git SHA")
        if source_commit.lower() != frozen_git_commit.lower():
            raise ObserverGateError("native observer source commit differs from frozen source")

        exact_build = manifest.get("exact_build")
        build = manifest.get("build")
        seam = manifest.get("seam")
        report_contract = manifest.get("report_contract")
        session_binding = manifest.get("session_binding")
        if not all(
            isinstance(row, dict)
            for row in (exact_build, build, seam, report_contract, session_binding)
        ):
            raise ObserverGateError("native observer manifest sections are malformed")
        assert isinstance(exact_build, dict) and isinstance(build, dict)
        assert isinstance(seam, dict) and isinstance(report_contract, dict)
        assert isinstance(session_binding, dict)
        if exact_build.get("game_version") != game_version:
            raise ObserverGateError("native observer game version binding drifted")
        if _require_sha(exact_build.get("game_executable_sha256"), "exact_build.game_executable_sha256") != game_executable_sha256.lower():
            raise ObserverGateError("native observer executable binding drifted")
        if build.get("private_option_enabled") is not True or not isinstance(build.get("private_option"), str) or not build.get("private_option"):
            raise ObserverGateError("native observer private build option is not enabled")
        if _require_sha(build.get("bridge_dll_sha256"), "build.bridge_dll_sha256") != bridge_dll_sha256.lower():
            raise ObserverGateError("native observer DLL binding drifted")
        if _require_sha(build.get("bridge_injector_sha256"), "build.bridge_injector_sha256") != bridge_injector_sha256.lower():
            raise ObserverGateError("native observer injector binding drifted")
        if _require_sha(session_binding.get("source_zip_sha256"), "session_binding.source_zip_sha256") != source_zip_sha256.lower():
            raise ObserverGateError("native observer source ZIP binding drifted")
        if _require_sha(session_binding.get("clean_source_tree_sha256"), "session_binding.clean_source_tree_sha256") != clean_source_tree_sha256.lower():
            raise ObserverGateError("native observer source tree binding drifted")
        if session_binding.get("pipe_name") != pipe_name:
            raise ObserverGateError("native observer pipe binding drifted")
        hooks = seam.get("hooks")
        if not isinstance(hooks, list) or len(hooks) != 2:
            raise ObserverGateError("native seam must bind exactly two producer hooks")
        hook_map: dict[str, dict[str, Any]] = {}
        for index, hook in enumerate(hooks):
            if not isinstance(hook, dict):
                raise ObserverGateError(f"seam.hooks[{index}] must be an object")
            rva = hook.get("rva")
            if not isinstance(rva, str) or RVA.fullmatch(rva) is None:
                raise ObserverGateError(f"seam.hooks[{index}].rva is missing")
            if rva in hook_map:
                raise ObserverGateError(f"duplicate native seam hook: {rva}")
            _require_sha(hook.get("anchor_sha256"), f"seam.hooks[{index}].anchor_sha256")
            hook_map[rva] = hook
        if set(hook_map) != {"0x3B9CFD2", "0x3B9CFD7"}:
            raise ObserverGateError("native seam producer hook RVAs drifted")
        if seam.get("task_register") != "RBX":
            raise ObserverGateError("native seam task register must remain RBX")
        if seam.get("callback_field_offset") != "0x38":
            raise ObserverGateError("native seam callback field must remain [RBX+0x38]")
        if seam.get("heartbeat_object") != seam_contract.get("heartbeat_object"):
            raise ObserverGateError("native seam heartbeat object drifted")
        if seam.get("prior_list_domain_callback_slot2_rva") != "0x817C20":
            raise ObserverGateError("native seam does not bind the known 0x817C20 domain")
        histogram = seam.get("histogram")
        expected_histogram = seam_contract.get("histogram")
        if not isinstance(histogram, dict) or histogram != expected_histogram:
            raise ObserverGateError("native seam bounded histogram contract drifted")
        abi = _source_artifact(clean_source, seam.get("abi"), "seam.abi")
        source_contract = _source_artifact(
            clean_source, seam.get("source_contract"), "seam.source_contract"
        )
        schema = report_contract.get("schema")
        artifact_name = report_contract.get("artifact_name")
        observed_fields = report_contract.get("required_fields")
        if schema != seam_contract.get("report_schema"):
            raise ObserverGateError("report_contract.schema drifted")
        if not isinstance(artifact_name, str) or Path(artifact_name).name != artifact_name:
            raise ObserverGateError("report_contract.artifact_name must be a file name")
        if not isinstance(observed_fields, list):
            raise ObserverGateError("report_contract.required_fields is malformed")
        if observed_fields != required_fields:
            raise ObserverGateError("native observer report fields drifted")
    except ObserverGateError as error:
        base["status"] = "native-seam-invalid"
        base["failure_reason"] = str(error)
        return base

    base.update(
        {
            "result": "GREEN",
            "status": "static-wiring-ready",
            "runner_observer_gate_ready": True,
            "launch_authorized_by_gate": True,
            "pending_native_seam_fields": [],
            "failure_reason": None,
            "bindings": {
                "source_git_commit": frozen_git_commit.lower(),
                "game_version": game_version,
                "game_executable_sha256": game_executable_sha256.lower(),
                "bridge_dll_sha256": bridge_dll_sha256.lower(),
                "bridge_injector_sha256": bridge_injector_sha256.lower(),
                "hooks": hooks,
                "task_register": "RBX",
                "callback_field_offset": "0x38",
                "heartbeat_object": seam["heartbeat_object"],
                "abi": abi,
                "source_contract": source_contract,
                "report_contract": report_contract,
                "session_binding": {
                    "source_zip_sha256": source_zip_sha256.lower(),
                    "clean_source_tree_sha256": clean_source_tree_sha256.lower(),
                    "pipe_name": pipe_name,
                },
            },
        }
    )
    return base
