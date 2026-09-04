#!/usr/bin/env python3
"""Plan, preflight, or run one fresh ZhongGuo phase-two capture attempt.

The default mode is no-launch: it creates only an append-only attempt manifest.
Passing ``--execute`` is the sole launch boundary and is refused until the
observer, canonical ready seed, source-checkpoint registry, exact product
projection, media receipt, bridge pair, and eight-handler contract are all
bound.  The delegated acceptance runner owns CK3, recorder, timeouts, and
cleanup; this wrapper never invokes FFmpeg.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Mapping, Sequence

from zhongguo_phase2_capture_choreography import PHASE2_CAPTURE_SCENARIOS
from zhongguo_phase2_promo_producer import (
    PHASE2_PROMO_CAPTURE_CONTRACT_VERSION,
    PHASE2_PROMO_CAPTURE_MODE,
    PHASE2_PROMO_CAPTURE_SPAN_MAP,
)
from zhongguo_phase2_source_checkpoint_provider import (
    Phase2SourceCheckpointError,
    Phase2SourceCheckpointProvider,
)


KIND = "zg361_phase2_capture_attempt_plan"
MEDIA_KIND = "zhongguo-361-phase2-media-environment-preflight"
LEGACY_SEED_SHA256 = (
    "98687d21fe816a4a42d1d6bef85cea9d8a0ed9e74d53cdeadf653b0d3a57ecb3"
)
LOADED_SEED_ARTIFACT = "cell/04_phase2_seed_loaded.json"
CAPTURE_TIMELINE_ARTIFACT = "cell/promo/capture-timeline.json"
CAPTURE_REPORT_ARTIFACT = "report.json"
EVIDENCE_INDEX_ARTIFACT = "evidence-index.json"
_GIT_SHA = re.compile(r"^[0-9a-fA-F]{40}$")


class PlanError(RuntimeError):
    pass


def _sha256(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    try:
        size = path.stat().st_size
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as error:
        raise PlanError(f"cannot bind {path}: {error}") from error
    return size, digest.hexdigest().upper()


def _json(path: Path) -> Mapping[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise PlanError(f"cannot read JSON {path}: {error}") from error
    if not isinstance(value, Mapping):
        raise PlanError(f"JSON root is not an object: {path}")
    return value


def _record(path: Path) -> dict[str, object]:
    size, digest = _sha256(path)
    return {"path": str(path.resolve()), "bytes": size, "sha256": digest}


def _utc(value: object) -> dt.datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(dt.timezone.utc)


def _seed_gate(path: Path | None) -> tuple[dict[str, object], list[str]]:
    blockers: list[str] = []
    row: dict[str, object] = {"required": True, "record": None, "checks": {}}
    if path is None or not path.is_file():
        blockers.append("seed_artifact_pending")
        return row, blockers
    payload = _json(path)
    source = payload.get("source") if isinstance(payload.get("source"), Mapping) else {}
    assert isinstance(source, Mapping)
    checks = {
        "schema_v1": payload.get("schema_version") == 1,
        "status_ready": payload.get("status") == "ready",
        "ready_true": payload.get("ready") is True,
        "not_legacy_save": str(source.get("sha256", "")).lower()
        != LEGACY_SEED_SHA256,
        "selectors_complete": isinstance(payload.get("domain_query_matrix"), Mapping)
        and all(
            isinstance(payload["domain_query_matrix"].get(key), int)
            and not isinstance(payload["domain_query_matrix"].get(key), bool)
            and int(payload["domain_query_matrix"][key]) > 0
            for key in (
                "b2_pip_owner_character_id",
                "incident_owner_character_id",
                "workforce_owner_character_id",
                "ai_owned_case_owner_character_id",
                "ai_owned_case_subject_character_id",
            )
        ),
    }
    row.update(record=_record(path), checks=checks)
    if not all(checks.values()):
        blockers.append(
            "legacy_seed_forbidden"
            if checks["not_legacy_save"] is False
            else "seed_contract_not_ready"
        )
    return row, blockers


def _source_checkpoint_gate(
    path: Path | None,
    *,
    seed_contract: Path | None,
) -> tuple[dict[str, object], list[str]]:
    row: dict[str, object] = {"required": True, "record": None, "checks": {}}
    if path is None or not path.is_file():
        return row, ["source_checkpoint_registry_pending"]
    if seed_contract is None or not seed_contract.is_file():
        return row, ["source_checkpoint_registry_seed_pending"]
    seed = _json(seed_contract)
    source = seed.get("source") if isinstance(seed.get("source"), Mapping) else {}
    seed_sha = str(source.get("sha256", "")).lower()
    expected_lineage = (
        f"zg361-phase2-seed-{seed_sha}"
        if re.fullmatch(r"[0-9a-f]{64}", seed_sha)
        else None
    )
    checks = {
        "registry_preflight_green": False,
        "seed_lineage_bound": expected_lineage is not None,
    }
    error: dict[str, object] | None = None
    try:
        preflight = Phase2SourceCheckpointProvider(
            _json(path),
            restore_registered_checkpoint=lambda _checkpoint: {},
            expected_seed_lineage_id=expected_lineage,
        ).preflight()
        checks["registry_preflight_green"] = preflight.get("result") == "GREEN"
    except Phase2SourceCheckpointError as caught:
        error = caught.evidence
    row.update(record=_record(path), checks=checks, error=error)
    return row, ([] if all(checks.values()) else ["source_checkpoint_registry_not_green"])


def _product_projection_gate(
    source: Path | None,
    *,
    projection: str | None,
    manifest: Path | None,
) -> tuple[dict[str, object], list[str]]:
    resolved = None if source is None else source.expanduser().resolve()
    projection_name = projection.strip() if isinstance(projection, str) else ""
    named_manifest_required = bool(projection_name and projection_name != "broad")
    manifest_present = manifest is not None and manifest.expanduser().resolve().is_file()
    checks = {
        "product_source_directory": resolved is not None and resolved.is_dir(),
        "projection_named": bool(projection_name),
        "projection_manifest_present": not named_manifest_required or manifest_present,
    }
    row: dict[str, object] = {
        "required": True,
        "source": None if resolved is None else str(resolved),
        "projection": projection_name or None,
        "manifest": None if not manifest_present else _record(manifest.expanduser().resolve()),
        "checks": checks,
    }
    return row, ([] if all(checks.values()) else ["product_projection_not_bound"])


def _observer_gate(path: Path | None) -> tuple[dict[str, object], list[str]]:
    row: dict[str, object] = {"required": True, "record": None, "checks": {}}
    if path is None or not path.is_file():
        return row, ["completion_observer_artifact_pending"]
    payload = _json(path)
    status = str(payload.get("status", "")).lower()
    schema = payload.get("schema")
    checks = {
        "result_green": payload.get("result") == "GREEN",
        "observer_ready": status in {
            "ready",
            "ready-to-live",
            "green",
            "completion_observed",
            "observer_ready",
        },
        "schema_supported": schema in {
            None,
            "xar.phase2.completion_observer_ready_to_live.v1",
        },
        "not_fixture_claim": payload.get("fixture_only") is not True,
    }
    row.update(record=_record(path), checks=checks)
    return row, ([] if all(checks.values()) else ["completion_observer_not_green"])


def _media_gate(
    path: Path | None,
    expected_sha256: str | None,
    *,
    now: dt.datetime,
) -> tuple[dict[str, object], list[str]]:
    row: dict[str, object] = {"required": True, "record": None, "checks": {}}
    if path is None or not path.is_file():
        return row, ["media_preflight_receipt_pending"]
    payload = _json(path)
    record = _record(path)
    promo = payload.get("promo_toolchain")
    promo = promo if isinstance(promo, Mapping) else {}
    expires = _utc(payload.get("expires_at_utc"))
    checks = {
        "expected_sha_bound": isinstance(expected_sha256, str)
        and record["sha256"] == expected_sha256.upper(),
        "kind": payload.get("kind") == MEDIA_KIND,
        "result_green": payload.get("result") == "GREEN",
        "unexpired": expires is not None and now < expires,
        "toolchain_version_bound": isinstance(promo.get("version"), str)
        and bool(str(promo["version"]).strip()),
        "toolchain_clean": promo.get("clean") is True,
        "toolchain_at_origin_main": isinstance(promo.get("head"), str)
        and promo.get("head") == promo.get("origin_main"),
        "byte_bound_media": all(
            isinstance(value, Mapping)
            and isinstance(value.get("bytes"), int)
            and isinstance(value.get("sha256"), str)
            for value in (
                payload.get("media", {}).get("ffmpeg")
                if isinstance(payload.get("media"), Mapping)
                else None,
                payload.get("media", {}).get("ffprobe")
                if isinstance(payload.get("media"), Mapping)
                else None,
            )
        ),
    }
    row.update(record=record, checks=checks, expires_at_utc=payload.get("expires_at_utc"))
    return row, ([] if all(checks.values()) else ["media_preflight_receipt_not_bound"])


def prepare_plan(
    *,
    attempt_dir: Path,
    source_root: Path,
    source_git_commit: str,
    python: Path,
    observer_artifact: Path | None,
    seed_contract: Path | None,
    media_preflight_report: Path | None,
    expected_media_preflight_sha256: str | None,
    bridge_dll: Path | None,
    bridge_injector: Path | None,
    source_checkpoint_registry: Path | None = None,
    product_source: Path | None = None,
    product_projection: str | None = None,
    product_projection_manifest: Path | None = None,
    frontend_first_load_save_name: str | None = None,
    now: dt.datetime | None = None,
) -> tuple[dict[str, object], Path]:
    attempt = attempt_dir.expanduser().resolve()
    if not _GIT_SHA.fullmatch(source_git_commit):
        raise PlanError("source_git_commit must be a full 40-hex commit")
    if attempt.exists():
        raise PlanError(f"attempt directory already exists: {attempt}")
    if not attempt.parent.is_dir():
        raise PlanError(f"attempt parent does not exist: {attempt.parent}")
    attempt.mkdir()
    moment = (now or dt.datetime.now(dt.timezone.utc)).astimezone(dt.timezone.utc)
    source = source_root.expanduser().resolve()
    capture = attempt / "capture"
    pipe = rf"\\.\pipe\xar_ck3_bridge_zg361_phase2_capture_{uuid.uuid4().hex}"
    blockers: list[str] = []
    observer, new = _observer_gate(observer_artifact)
    blockers.extend(new)
    seed, new = _seed_gate(seed_contract)
    blockers.extend(new)
    source_checkpoints, new = _source_checkpoint_gate(
        source_checkpoint_registry,
        seed_contract=seed_contract,
    )
    blockers.extend(new)
    product, new = _product_projection_gate(
        product_source,
        projection=product_projection,
        manifest=product_projection_manifest,
    )
    blockers.extend(new)
    media, new = _media_gate(
        media_preflight_report,
        expected_media_preflight_sha256,
        now=moment,
    )
    blockers.extend(new)
    dependencies: dict[str, object] = {}
    for label, path in (
        ("python", python),
        ("runner", source / "tools" / "run_zhongguo_acceptance.py"),
        ("bridge_dll", bridge_dll),
        ("bridge_injector", bridge_injector),
    ):
        present = path is not None and path.expanduser().resolve().is_file()
        dependencies[label] = {
            "path": None if path is None else str(path.expanduser().resolve()),
            "present": present,
        }
        if not present:
            blockers.append(f"{label}_pending")
    scenarios = [
        {
            "ordinal": ordinal,
            "span_id": scenario.span_id,
            "producer_key": scenario.producer_key,
            "handler": scenario.handler,
            "clean_begin": f"{scenario.span_id}_clean_begin",
            "clean_end": f"{scenario.span_id}_clean_end",
        }
        for ordinal, scenario in enumerate(PHASE2_CAPTURE_SCENARIOS, start=1)
    ]
    handlers_match = tuple(
        (row["span_id"], row["producer_key"]) for row in scenarios
    ) == PHASE2_PROMO_CAPTURE_SPAN_MAP and len({row["handler"] for row in scenarios}) == 8
    if not handlers_match:
        blockers.append("default_handler_contract_not_eight_of_eight")
    command = [
        str(python.expanduser().resolve()),
        str(source / "tools" / "run_zhongguo_acceptance.py"),
        "--phase2-promo-capture",
        "--phase2-seed-contract",
        (
            "<PENDING>"
            if seed_contract is None
            else str(seed_contract.expanduser().resolve())
        ),
        "--artifacts-dir",
        str(capture),
        "--bridge-dll",
        "<PENDING>" if bridge_dll is None else str(bridge_dll.expanduser().resolve()),
        "--bridge-injector",
        "<PENDING>" if bridge_injector is None else str(bridge_injector.expanduser().resolve()),
        "--bridge-pipe",
        pipe,
        "--phase2-source-checkpoint-registry",
        (
            "<PENDING>"
            if source_checkpoint_registry is None
            else str(source_checkpoint_registry.expanduser().resolve())
        ),
        "--phase2-product-source",
        "<PENDING>" if product_source is None else str(product_source.expanduser().resolve()),
        "--phase2-product-projection",
        product_projection or "<PENDING>",
    ]
    if product_projection_manifest is not None:
        command.extend(
            [
                "--phase2-product-projection-manifest",
                str(product_projection_manifest.expanduser().resolve()),
            ]
        )
    if frontend_first_load_save_name:
        command.extend(
            ["--phase2-frontend-first-load-save-name", frontend_first_load_save_name]
        )
    status = "ready-to-run" if not blockers else "waiting-for-bound-inputs"
    result = "GREEN" if not blockers else "RED"
    manifest: dict[str, object] = {
        "schema_version": 1,
        "kind": KIND,
        "result": result,
        "status": status,
        "reason_code": None if not blockers else blockers[0],
        "blockers": blockers,
        "generated_at_utc": moment.isoformat(),
        "scope": "no-launch capture planning; not live evidence or media",
        "source": {
            "root": str(source),
            "origin_master_base": source_git_commit.lower(),
        },
        "no_launch_attestation": {
            "ck3_started": False,
            "ffmpeg_started": False,
            "media_generated": False,
            "capture_directory_created": capture.exists(),
        },
        "attempt": {
            "root": str(attempt),
            "capture_directory": str(capture),
            "capture_directory_must_not_exist_before_launch": True,
            "failed_attempt_retention": "retain; retry in another new directory",
        },
        "inputs": {
            "completion_observer": observer,
            "seed_contract": seed,
            "source_checkpoint_registry": source_checkpoints,
            "product_projection": product,
            "media_preflight": media,
            "runtime_dependencies": dependencies,
        },
        "capture_contract": {
            "mode": PHASE2_PROMO_CAPTURE_MODE,
            "version": PHASE2_PROMO_CAPTURE_CONTRACT_VERSION,
            "default_handlers": "8/8" if handlers_match else "RED",
            "spans": scenarios,
        },
        "pre_recorder_gates": [
            "seed contract status=ready and old save SHA forbidden",
            "managed native session and loader GREEN",
            "paused map bound to tracked PID",
            "04_phase2_seed_loaded.json schema_version=2 GREEN",
            "all eight loaded-feature requirements GREEN",
            "all eight default handlers available",
        ],
        "managed_session_handoff": {
            "seed_generation_session_reused": False,
            "reason": (
                "run_zg361_phase2_seed_capture.py always stops its supervisor "
                "and closes its driver before returning GREEN"
            ),
            "capture_session_sequence": [
                "install the explicit generated seed contract",
                "start a managed native session for the first span",
                "complete loader and paused-map gates",
                "write 04_phase2_seed_loaded.json schema v2 bound by seed save hash",
                "record each span inside one continuous pre/action/post session",
                "allow clean managed CK3 restart only between spans",
                "stop recorder and prove cleanup for every observed session/PID",
            ],
            "same_session_boundary": "per-span-pre-action-post-only",
            "cross_span_restart_allowed": True,
            "seed_generation_continuity": "save-hash-and-source-provenance",
        },
        "recorder_contract": {
            "start_after_all_pre_recorder_gates": True,
            "clean_frame_gate_count": 8,
            "timeline_artifact": CAPTURE_TIMELINE_ARTIFACT,
            "report_artifact": CAPTURE_REPORT_ARTIFACT,
            "evidence_index_artifact": EVIDENCE_INDEX_ARTIFACT,
            "loaded_seed_v2_artifact": LOADED_SEED_ARTIFACT,
        },
        "timeouts_seconds": {
            "native_session_readiness": 300,
            "native_session_runtime": 21600,
            "paused_seed_readiness": 300,
            "exact_event_each": 30,
        },
        "cleanup": {
            "owner": "run_zhongguo_acceptance.py finally block",
            "recorder_stop_if_started": True,
            "managed_supervisor_stop": True,
            "driver_close": True,
            "locks_release": True,
            "logs_and_immutability_evidence_retained": True,
        },
        "single_capture_command": {"argv": command, "shell": False},
        "next_action": (
            "invoke the single capture command exactly once"
            if not blockers
            else "supply the listed bound inputs and create a new plan attempt"
        ),
    }
    manifest_path = attempt / "capture-plan.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest, manifest_path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-dir", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, default=Path.cwd())
    parser.add_argument("--source-git-commit", required=True)
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    parser.add_argument("--observer-artifact", type=Path)
    parser.add_argument("--seed-contract", type=Path)
    parser.add_argument("--media-preflight-report", type=Path)
    parser.add_argument("--expected-media-preflight-sha256")
    parser.add_argument("--bridge-dll", type=Path)
    parser.add_argument("--bridge-injector", type=Path)
    parser.add_argument("--source-checkpoint-registry", type=Path)
    parser.add_argument("--product-source", type=Path)
    parser.add_argument("--product-projection")
    parser.add_argument("--product-projection-manifest", type=Path)
    parser.add_argument("--frontend-first-load-save-name")
    parser.add_argument("--execute", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        manifest, path = prepare_plan(
            attempt_dir=args.attempt_dir,
            source_root=args.source_root,
            source_git_commit=args.source_git_commit,
            python=args.python,
            observer_artifact=args.observer_artifact,
            seed_contract=args.seed_contract,
            media_preflight_report=args.media_preflight_report,
            expected_media_preflight_sha256=args.expected_media_preflight_sha256,
            bridge_dll=args.bridge_dll,
            bridge_injector=args.bridge_injector,
            source_checkpoint_registry=args.source_checkpoint_registry,
            product_source=args.product_source,
            product_projection=args.product_projection,
            product_projection_manifest=args.product_projection_manifest,
            frontend_first_load_save_name=args.frontend_first_load_save_name,
        )
    except PlanError as error:
        print(f"PHASE2 CAPTURE PLAN ERROR: {error}", file=sys.stderr)
        return 2
    _, manifest_sha = _sha256(path)
    print(f"manifest={path}")
    print(f"manifest_sha256={manifest_sha}")
    if manifest["result"] != "GREEN":
        print(
            f"PHASE2 CAPTURE PLAN WAITING [{manifest['reason_code']}]",
            file=sys.stderr,
        )
        return 2
    if not args.execute:
        print("PHASE2 CAPTURE PLAN: GREEN / NO-LAUNCH")
        return 0
    command = manifest["single_capture_command"]["argv"]
    assert isinstance(command, list)
    completed = subprocess.run(command, shell=False, check=False)
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
