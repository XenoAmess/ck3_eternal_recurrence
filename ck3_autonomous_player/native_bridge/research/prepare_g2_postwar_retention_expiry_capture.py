#!/usr/bin/env python3
"""Freeze the no-launch ticket for a future G2 postwar/expiry receipt.

This tool never starts or attaches to CK3. It binds the retained production
pre-war report (including the exact regiment generations behind the observed
598 soldiers) to the default-OFF loss candidate and emits a deterministic
ticket for a future action-bound postwar cleanup plus persisted-expiry query.
It can also validate that future receipt without changing public readiness.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Callable

import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
PACKAGE_ROOT = REPOSITORY_ROOT / "ck3_autonomous_player" / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer.bridge.raiktor_war_bound_regiment_contract import (  # noqa: E402
    normalize_raiktor_war_bound_regiment,
)


DEFAULT_MANIFEST = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "g2_postwar_retention_expiry_no_launch_manifest.json"
)
EXPECTED_EXE_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
EXPECTED_RECEIPT_SCHEMA = "xar.ck3.g2_postwar_retention_expiry.v1"
EXPECTED_RECEIPT_STATUS = "GREEN_ACTION_BOUND_POSTWAR_RETENTION_EXPIRY"
EXPECTED_EXPIRY_SOURCE = "persisted_native_truce_row"


class PreflightError(RuntimeError):
    """Manifest, immutable input, process, or receipt contract mismatch."""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _sha256_json(value: object) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest().upper()


def _object(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise PreflightError(f"{name} must be an object")
    return value


def _integer(value: object, name: str, *, minimum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise PreflightError(f"{name} must be an integer")
    if minimum is not None and value < minimum:
        raise PreflightError(f"{name} must be >= {minimum}")
    return value


def _sha256(value: object, name: str) -> str:
    result = str(value).upper()
    if re.fullmatch(r"[0-9A-F]{64}", result) is None:
        raise PreflightError(f"{name} must be a SHA-256")
    return result


def _load_object(path: Path, name: str) -> dict[str, object]:
    try:
        return _object(json.loads(path.read_text(encoding="utf-8")), name)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise PreflightError(f"could not read {name}: {error}") from error


def _resolve(path_value: object, *, repo_root: Path) -> Path:
    path = Path(str(path_value))
    return path.resolve() if path.is_absolute() else (repo_root / path).resolve()


def _default_process_inventory() -> list[dict[str, object]]:
    completed = subprocess.run(
        [
            "tasklist.exe",
            "/FI",
            "IMAGENAME eq ck3.exe",
            "/FO",
            "CSV",
            "/NH",
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        raise PreflightError("could not inventory CK3 processes")
    rows = []
    for line in completed.stdout.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("INFO:"):
            continue
        if stripped.lower().startswith('"ck3.exe"'):
            rows.append({"raw": stripped})
    return rows


def _generation_vector(value: dict[str, object]) -> list[dict[str, object]]:
    regiments = value.get("regiments")
    if not isinstance(regiments, list) or not regiments:
        raise PreflightError("pre observation has no frozen regiments")
    vector: list[dict[str, object]] = []
    for regiment_value in regiments:
        regiment = _object(regiment_value, "pre regiment")
        current_rows = regiment.get("composition_rows")
        if not isinstance(current_rows, list):
            raise PreflightError("pre regiment composition is missing")
        present = []
        for row_value in current_rows:
            row = _object(row_value, "pre composition row")
            if row.get("current_army_regiment_id") is None:
                continue
            present.append(
                {
                    "composition_ordinal": row.get("composition_ordinal"),
                    "current_army_regiment_id": row.get(
                        "current_army_regiment_id"
                    ),
                    "raised_carmy_id": row.get("raised_carmy_id"),
                    "current_soldiers": row.get("current_soldiers"),
                }
            )
        vector.append(
            {
                "persistent_regiment_id": regiment.get(
                    "persistent_regiment_id"
                ),
                "current_rows": present,
            }
        )
    return vector


def _structured_query(report: dict[str, object], key: str) -> dict[str, object]:
    sequence = _object(report.get("mcp_sequence"), "source mcp_sequence")
    envelope = _object(sequence.get(key), f"source {key}")
    if envelope.get("is_error") is not False:
        raise PreflightError(f"source {key} is an MCP error")
    return _object(envelope.get("structured_content"), f"source {key} payload")


def _normalize_pre_observation(
    query: dict[str, object], expected: dict[str, object]
) -> dict[str, object]:
    terms = _object(query.get("war_termination_terms"), "pre terms")
    generic = terms.get("generic_war_bound_current")
    try:
        return normalize_raiktor_war_bound_regiment(
            generic,
            expected_war_id=_integer(expected["war_id"], "war_id"),
            expected_attacker_character_id=_integer(
                expected["character_id"], "character_id"
            ),
            expected_defender_character_id=_integer(
                expected["opponent_character_id"], "opponent_character_id"
            ),
            expected_snapshot_revision=_integer(
                expected["revision"], "revision", minimum=0
            ),
            expected_native_revision=_integer(
                expected["native_revision"], "native_revision", minimum=0
            ),
            expected_date_raw=_integer(expected["date_raw"], "date_raw"),
        )
    except (TypeError, ValueError, KeyError) as error:
        raise PreflightError(f"pre war-bound observation rejected: {error}") from error


def _validate_compact_pre_receipt(
    receipt: dict[str, object], expected: dict[str, object]
) -> None:
    exact = _object(receipt.get("exact_build"), "pre receipt exact_build")
    binding = _object(receipt.get("paused_binding"), "pre receipt binding")
    war_bound = _object(
        receipt.get("war_bound_observation"), "pre receipt war-bound"
    )
    boundaries = _object(receipt.get("boundaries"), "pre receipt boundaries")
    if (
        receipt.get("status")
        != "GREEN_PRODUCTION_LIVE_EVALUATED_DAYS_PRIMITIVE"
        or exact.get("game_executable_sha256") != EXPECTED_EXE_SHA256
        or binding.get("war_id") != expected["war_id"]
        or binding.get("character_id") != expected["character_id"]
        or binding.get("date_raw") != expected["date_raw"]
        or binding.get("snapshot_id") != expected["snapshot_id"]
        or binding.get("revision") != expected["revision"]
        or binding.get("native_revision") != expected["native_revision"]
        or binding.get("connection_generation")
        != expected["connection_generation"]
        or binding.get("episode_run_id") != expected["episode_run_id"]
        or war_bound.get("observed_current_soldiers")
        != expected["pre_termination_soldiers"]
        or war_bound.get("source_specific_attribution_ready") is not False
        or war_bound.get("proven_soldier_loss_observable") is not False
        or boundaries.get("actual_expiry_observable") is not False
        or boundaries.get("war_bound_loss_ready") is not False
        or boundaries.get("decision_ready") is not False
        or boundaries.get("automatic_surrender_ready") is not False
        or boundaries.get("gen034_closed") is not False
    ):
        raise PreflightError("compact pre receipt disagrees with frozen boundary")


def _validate_candidate_receipt(receipt: dict[str, object]) -> None:
    if (
        receipt.get("result") != "GREEN_STATIC"
        or receipt.get("live") is not False
        or receipt.get("ck3_started_or_attached") is not False
        or _object(receipt.get("exact_build"), "candidate exact_build").get(
            "ck3_exe_sha256"
        )
        != EXPECTED_EXE_SHA256
        or _object(receipt.get("proved"), "candidate proved").get(
            "exact_generation_cleanup_pairing"
        )
        is not True
    ):
        raise PreflightError("loss candidate receipt is not frozen GREEN_STATIC")
    not_proved = _object(receipt.get("not_proved"), "candidate not_proved")
    for name in (
        "event_source_attribution",
        "termination_action_binding",
        "surrender_causality",
        "public_terms_readiness",
        "automatic_surrender",
        "gen_034",
        "production_live",
    ):
        if not_proved.get(name) is not True:
            raise PreflightError(f"candidate receipt overclaims {name}")


def _validate_source_report(
    report: dict[str, object], expected: dict[str, object]
) -> tuple[dict[str, object], list[dict[str, object]]]:
    if report.get("status") != "green" or report.get("ok") is not True:
        raise PreflightError("source production report is not GREEN")
    first = _structured_query(report, "first_query")
    second = _structured_query(report, "second_query")
    first_observation = _normalize_pre_observation(first, expected)
    second_observation = _normalize_pre_observation(second, expected)
    if first_observation != second_observation:
        raise PreflightError("source production war-bound queries differ")
    for query, sequence in ((first, 1), (second, 2)):
        if (
            query.get("query_sequence") != sequence
            or query.get("queried_snapshot_id") != expected["snapshot_id"]
            or query.get("queried_revision") != expected["revision"]
            or query.get("queried_native_revision")
            != expected["native_revision"]
            or query.get("queried_connection_generation")
            != expected["connection_generation"]
            or query.get("episode_run_id") != expected["episode_run_id"]
            or query.get("war_id") != expected["war_id"]
        ):
            raise PreflightError("source query receipt binding drifted")
    soldiers = _object(first_observation.get("soldiers"), "pre soldiers")
    if (
        soldiers.get("observed_current_soldiers")
        != expected["pre_termination_soldiers"]
        or soldiers.get("pre_soldiers_observable") is not False
        or soldiers.get("proven_soldier_loss_observable") is not False
    ):
        raise PreflightError("source soldier boundary drifted")
    session = _object(report.get("session"), "source session")
    if session.get("pid") != expected["ck3_pid"]:
        raise PreflightError("source CK3 PID drifted")
    return first_observation, _generation_vector(first_observation)


def _validate_file(
    path_value: object,
    hash_value: object,
    *,
    repo_root: Path,
    name: str,
) -> Path:
    path = _resolve(path_value, repo_root=repo_root)
    if not path.is_file():
        raise PreflightError(f"{name} is missing: {path}")
    expected = _sha256(hash_value, f"{name} hash")
    actual = _sha256_file(path)
    if actual != expected:
        raise PreflightError(f"{name} hash differs: {actual} != {expected}")
    return path


def build_retention_ticket(
    manifest: dict[str, object], *, repo_root: Path
) -> dict[str, object]:
    expected = _object(manifest.get("pre_binding"), "pre_binding")
    paths = _object(manifest.get("paths"), "paths")
    hashes = _object(manifest.get("sha256"), "sha256")
    if (
        manifest.get("schema")
        != "xar.ck3.g2_postwar_retention_expiry_no_launch_manifest.v1"
        or manifest.get("default_off") is not True
        or manifest.get("live_authorized") is not False
        or manifest.get("public_readiness_promoted") is not False
        or manifest.get("gen034_closed") is not False
    ):
        raise PreflightError("manifest boundary is invalid")

    checked: dict[str, Path] = {}
    for name in (
        "runner",
        "pre_receipt",
        "source_report",
        "loss_candidate_receipt",
        "loss_candidate_source_contract",
    ):
        checked[name] = _validate_file(
            paths[name], hashes[name], repo_root=repo_root, name=name
        )
    pre_receipt = _load_object(checked["pre_receipt"], "pre receipt")
    source_report = _load_object(checked["source_report"], "source report")
    candidate_receipt = _load_object(
        checked["loss_candidate_receipt"], "loss candidate receipt"
    )
    source_contract = _load_object(
        checked["loss_candidate_source_contract"],
        "loss candidate source contract",
    )
    _validate_compact_pre_receipt(pre_receipt, expected)
    _validate_candidate_receipt(candidate_receipt)
    if (
        source_contract.get("ck3_exe_sha256") != EXPECTED_EXE_SHA256
        or _object(
            source_contract.get("implementation"), "candidate implementation"
        ).get("default_enabled")
        is not False
        or _object(
            source_contract.get("hard_boundaries"), "candidate boundaries"
        ).get("termination_action_bound")
        is not False
    ):
        raise PreflightError("loss candidate source contract boundary drifted")

    observation, generations = _validate_source_report(source_report, expected)
    generation_sha256 = _sha256_json(generations)
    if generation_sha256 != _sha256(
        expected["frozen_generation_sha256"], "frozen_generation_sha256"
    ):
        raise PreflightError("source frozen-generation vector drifted")
    query = _structured_query(source_report, "first_query")
    truce = _object(
        _object(query.get("war_termination_terms"), "pre terms").get("truce"),
        "pre truce",
    )
    if (
        truce.get("evaluated_days_observable") is not True
        or truce.get("evaluated_days") != expected["evaluated_days"]
        or truce.get("actual_expiry_observable") is not False
        or truce.get("expiry_date_raw") is not None
    ):
        raise PreflightError("pre truce duration/expiry boundary drifted")

    ticket_body = {
        "schema": "xar.ck3.g2_postwar_retention_ticket.v1",
        "exact_build_sha256": EXPECTED_EXE_SHA256,
        "source_report_sha256": hashes["source_report"],
        "war_id": expected["war_id"],
        "character_id": expected["character_id"],
        "opponent_character_id": expected["opponent_character_id"],
        "source_snapshot_id": expected["snapshot_id"],
        "source_revision": expected["revision"],
        "source_native_revision": expected["native_revision"],
        "date_raw": expected["date_raw"],
        "source_connection_generation": expected["connection_generation"],
        "source_episode_run_id": expected["episode_run_id"],
        "source_ck3_pid": expected["ck3_pid"],
        "pre_termination_soldiers": expected["pre_termination_soldiers"],
        "evaluated_days": expected["evaluated_days"],
        "frozen_generation_sha256": generation_sha256,
        "frozen_generations": generations,
    }
    ticket = copy.deepcopy(ticket_body)
    ticket["retention_ticket_id"] = _sha256_json(ticket_body)
    ticket["source_attribution_ready"] = False
    ticket["termination_action_bound"] = False
    ticket["actual_expiry_observable"] = False
    ticket["public_readiness_promoted"] = False
    ticket["gen034_closed"] = False
    ticket["pre_observation_backend_id"] = observation.get("backend_id")
    return ticket


def validate_postwar_receipt(
    value: object, ticket: dict[str, object]
) -> dict[str, object]:
    receipt = _object(value, "postwar receipt")
    exact = _object(receipt.get("exact_build"), "post exact_build")
    session = _object(receipt.get("session_binding"), "post session_binding")
    pre = _object(receipt.get("pre"), "post pre")
    termination = _object(receipt.get("termination"), "termination")
    post = _object(receipt.get("post"), "post")
    cleanup = _object(post.get("war_bound_cleanup"), "post cleanup")
    expiry = _object(post.get("truce_expiry"), "post expiry")
    boundaries = _object(receipt.get("boundaries"), "post boundaries")
    pre_generations = pre.get("frozen_generations")
    generations = cleanup.get("frozen_generations")
    pre_generation_sha256 = _sha256_json(pre_generations)
    generation_sha256 = _sha256_json(generations)
    runtime_pid = _integer(session.get("ck3_pid"), "runtime ck3_pid", minimum=1)
    runtime_connection = _integer(
        session.get("connection_generation"),
        "runtime connection_generation",
        minimum=1,
    )
    runtime_episode = session.get("episode_run_id")
    if not isinstance(runtime_episode, str) or not runtime_episode:
        raise PreflightError("runtime episode_run_id must be nonempty")
    pre_revision = _integer(pre.get("revision"), "pre revision", minimum=0)
    pre_native_revision = _integer(
        pre.get("native_revision"), "pre native_revision", minimum=0
    )
    pre_terms_query_sequence = _integer(
        pre.get("terms_query_sequence"), "pre terms_query_sequence", minimum=2
    )
    pre_receipt_sequence = _integer(
        pre.get("receipt_sequence"), "pre receipt_sequence", minimum=1
    )
    action_receipt_sequence = _integer(
        termination.get("receipt_sequence"),
        "termination receipt_sequence",
        minimum=2,
    )
    post_revision = _integer(
        post.get("revision"), "post revision", minimum=0
    )
    post_native_revision = _integer(
        post.get("native_revision"), "post native_revision", minimum=0
    )
    post_date_raw = _integer(post.get("date_raw"), "post date_raw")
    expiry_date_raw = _integer(
        expiry.get("expiry_date_raw"), "expiry_date_raw"
    )
    post_receipt_sequence = _integer(
        post.get("receipt_sequence"), "post receipt_sequence", minimum=3
    )
    required_mutation = f"surrender-war-{ticket['war_id']}"
    checks = {
        "schema": receipt.get("schema") == EXPECTED_RECEIPT_SCHEMA,
        "status": receipt.get("status") == EXPECTED_RECEIPT_STATUS,
        "ticket": receipt.get("retention_ticket_id")
        == ticket["retention_ticket_id"],
        "exact_build": exact.get("game_executable_sha256")
        == EXPECTED_EXE_SHA256,
        "runtime_binding": runtime_pid > 0
        and runtime_connection > 0
        and bool(runtime_episode),
        "same_character": session.get("character_id")
        == ticket["character_id"],
        "same_war": session.get("war_id") == ticket["war_id"],
        "pre_report": pre.get("source_report_sha256")
        == ticket["source_report_sha256"],
        "pre_runtime_binding": pre.get("ck3_pid") == runtime_pid
        and pre.get("connection_generation") == runtime_connection
        and pre.get("episode_run_id") == runtime_episode
        and isinstance(pre.get("snapshot_id"), str)
        and bool(pre["snapshot_id"])
        and pre.get("date_raw") == ticket["date_raw"],
        "pre_soldiers": pre.get("pre_termination_soldiers")
        == ticket["pre_termination_soldiers"],
        "pre_generation": pre.get("frozen_generation_sha256")
        == ticket["frozen_generation_sha256"],
        "pre_generation_vector": pre_generations
        == ticket["frozen_generations"]
        and pre_generation_sha256 == ticket["frozen_generation_sha256"],
        "one_typed_action": termination.get("submitted") is True
        and termination.get("accepted") is True
        and termination.get("step") == required_mutation
        and termination.get("war_id") == ticket["war_id"]
        and termination.get("ck3_pid") == runtime_pid
        and termination.get("connection_generation") == runtime_connection
        and termination.get("episode_run_id") == runtime_episode
        and pre_terms_query_sequence == 2
        and action_receipt_sequence == pre_receipt_sequence + 1
        and isinstance(termination.get("receipt_id"), str)
        and bool(termination["receipt_id"]),
        "post_successor": post.get("ck3_pid") == runtime_pid
        and post.get("connection_generation") == runtime_connection
        and post.get("episode_run_id") == runtime_episode
        and post_receipt_sequence == action_receipt_sequence + 1
        and post_revision > pre_revision
        and post_native_revision > pre_native_revision
        and post_date_raw >= ticket["date_raw"]
        and post.get("paused") is True,
        "war_absent": post.get("old_full_generation_war_id_absent") is True
        and post.get("war_id") == ticket["war_id"],
        "same_generation_cleanup": generations == ticket["frozen_generations"]
        and generation_sha256 == ticket["frozen_generation_sha256"],
        "destroyed_cleanup": cleanup.get("observable") is True
        and cleanup.get("status") == "destroyed"
        and cleanup.get("post_termination_soldiers") == 0
        and cleanup.get("proven_boundary_soldiers_lost")
        == ticket["pre_termination_soldiers"],
        "persisted_expiry": expiry.get("observable") is True
        and expiry.get("source") == EXPECTED_EXPIRY_SOURCE
        and expiry.get("formula_derived") is False
        and expiry.get("from_character_id") == ticket["character_id"]
        and expiry.get("to_character_id") == ticket["opponent_character_id"]
        and expiry.get("evaluated_days") == ticket["evaluated_days"]
        and expiry.get("queried_at_date_raw") == post_date_raw
        and expiry_date_raw > post_date_raw,
        "mutation_boundary": receipt.get("mutation_commands")
        == [required_mutation],
        "no_promotion": boundaries.get("source_specific_attribution_ready")
        is False
        and boundaries.get("public_readiness_promoted") is False
        and boundaries.get("decision_ready") is False
        and boundaries.get("automatic_surrender_ready") is False
        and boundaries.get("gen034_closed") is False,
    }
    return {"checks": checks, "ok": all(checks.values())}


def run_preflight(
    manifest_path: Path,
    output_path: Path,
    *,
    repo_root: Path = REPOSITORY_ROOT,
    process_inventory: Callable[[], list[dict[str, object]]] = (
        _default_process_inventory
    ),
    receipt_path: Path | None = None,
) -> dict[str, object]:
    before = process_inventory()
    if before:
        raise PreflightError("CK3 must be absent during no-launch preflight")
    manifest = _load_object(manifest_path.resolve(), "manifest")
    paths = _object(manifest.get("paths"), "paths")
    fresh_attempt = _resolve(paths["fresh_attempt"], repo_root=repo_root)
    if fresh_attempt.exists():
        raise PreflightError(f"fresh attempt path already exists: {fresh_attempt}")
    ticket = build_retention_ticket(manifest, repo_root=repo_root)
    receipt_validation = None
    if receipt_path is not None:
        receipt_validation = validate_postwar_receipt(
            _load_object(receipt_path.resolve(), "postwar receipt"), ticket
        )
        if receipt_validation["ok"] is not True:
            raise PreflightError("postwar receipt did not satisfy the ticket")
    after = process_inventory()
    if after:
        raise PreflightError("CK3 appeared during no-launch preflight")
    report = {
        "schema": "xar.ck3.g2_postwar_retention_expiry_preflight.v1",
        "status": "GREEN_STATIC_RETENTION_TICKET",
        "ok": True,
        "manifest": str(manifest_path.resolve()),
        "manifest_sha256": _sha256_file(manifest_path.resolve()),
        "ck3_started_or_attached": False,
        "process_inventory_before": before,
        "process_inventory_after": after,
        "fresh_attempt_absent": not fresh_attempt.exists(),
        "retention_ticket": ticket,
        "postwar_receipt_validation": receipt_validation,
        "boundaries": {
            "default_off": True,
            "live_authorized": False,
            "native_expiry_reader_available": False,
            "termination_action_bound": False,
            "actual_expiry_observable": False,
            "public_readiness_promoted": False,
            "decision_ready": False,
            "automatic_surrender_ready": False,
            "gen034_closed": False,
        },
        "next_gate": (
            "wire a private default-OFF persisted-truce expiry query and "
            "postwar cleanup receipt to this exact ticket; only an exclusive "
            "action-bound live run may fill the future receipt"
        ),
    }
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--validate-receipt", type=Path)
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    try:
        report = run_preflight(
            arguments.manifest,
            arguments.output,
            receipt_path=arguments.validate_receipt,
        )
    except PreflightError as error:
        print(f"RED: {error}")
        return 2
    ticket = _object(report["retention_ticket"], "retention_ticket")
    print(
        "GREEN_STATIC_RETENTION_TICKET "
        f"ticket={ticket['retention_ticket_id']} "
        f"generations={ticket['frozen_generation_sha256']} "
        "live_authorized=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
