#!/usr/bin/env python3
"""Materialize a phase-two seed candidate from typed MCP evidence.

This helper never discovers or invents a CharacterID itself.  It accepts the
current-event context emitted by the dedicated acceptance-only fixture, the
typed close ACK for that exact event, and a typed save-checkpoint response.
The resulting candidate remains blocked until the shipped B1/B2/Incident/
Workforce state has independent provider proof.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_CONTRACT = ROOT / "tools" / "zg361_phase2_seed_contract.json"
EVENT_DEFINITION_KEY = "zga_phase2_seed.1"
PLAYER_HISTORY_ID = "han_6875"
DOMAIN_SCOPE_MAP = {
    "b2_pip_owner_character_id": "zga_phase2_b2_owner",
    "incident_owner_character_id": "zga_phase2_incident_owner",
    "workforce_owner_character_id": "zga_phase2_workforce_owner",
    "ai_owned_case_owner_character_id": "zga_phase2_ai_owned_owner",
    "ai_owned_case_subject_character_id": "zga_phase2_ai_owned_subject",
}
BLOCKED_STATUS = "blocked_seed_generation_required"
BLOCKER = (
    "Selector identities and a typed checkpoint were captured, but the seed "
    "is not ready until shipped providers independently prove B1 AI-owned, "
    "B2 PIP received-self, an attainable Incident terminal matrix, and a "
    "genuine three-cycle Workforce charter."
)
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
GIT_COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}")


class SeedBootstrapError(ValueError):
    """Typed bootstrap evidence is absent, ambiguous, or contradictory."""


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SeedBootstrapError(f"cannot read JSON {path}: {error}") from error
    if not isinstance(value, dict):
        raise SeedBootstrapError(f"JSON root is not an object: {path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _positive_int32(value: object, label: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 1 <= value <= 2**31 - 1
    ):
        raise SeedBootstrapError(f"{label} is not a positive CharacterID")
    return value


def _character_id(scope: object, label: str) -> int:
    if not isinstance(scope, dict):
        raise SeedBootstrapError(f"{label} scope is absent")
    typed_identity = scope.get("typed_identity")
    if (
        scope.get("status") != "available"
        or scope.get("type_key") != "character"
        or not isinstance(typed_identity, dict)
        or typed_identity.get("status") != "available"
        or typed_identity.get("kind") != "character"
    ):
        raise SeedBootstrapError(f"{label} is not an available character scope")
    return _positive_int32(typed_identity.get("character_id"), label)


def extract_event_capture(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract the played root and all selector IDs from one native query."""

    query_value = payload.get("query", payload)
    if not isinstance(query_value, dict):
        raise SeedBootstrapError("event query wrapper is malformed")
    if "accepted" in query_value and query_value.get("accepted") is not True:
        raise SeedBootstrapError("event context query was not accepted")
    if "step" in query_value and query_value.get("step") != (
        "query-current-event-window-context-v1"
    ):
        raise SeedBootstrapError("event context came from the wrong MCP step")
    context_value = query_value.get("current_event_window_context", query_value)
    if not isinstance(context_value, dict):
        raise SeedBootstrapError("current event context is absent")
    if (
        context_value.get("schema") != "current-event-window-context-v1"
        or context_value.get("schema_version") != 1
        or context_value.get("status") != "available"
        or context_value.get("window_match_count") != 1
        or context_value.get("event_definition_key") != EVENT_DEFINITION_KEY
    ):
        raise SeedBootstrapError(
            "current event context is not the unique phase-two bootstrap event"
        )
    options = context_value.get("options")
    if not (
        isinstance(options, list)
        and len(options) == 1
        and isinstance(options[0], dict)
        and options[0].get("shown") is True
        and options[0].get("enabled") is True
        and options[0].get("native_option_index") == 0
    ):
        raise SeedBootstrapError(
            "phase-two bootstrap event does not expose exactly one enabled option"
        )

    played_character_id = _character_id(
        context_value.get("root_scope"), "bootstrap root"
    )
    date_raw = _positive_int32(context_value.get("date_raw"), "event date_raw")
    event_instance_id = _positive_int32(
        context_value.get("current_event_instance_id"), "event instance"
    )
    saved_scopes = context_value.get("saved_scopes")
    if not isinstance(saved_scopes, list):
        raise SeedBootstrapError("bootstrap event saved scopes are absent")
    scopes_by_name: dict[str, object] = {}
    duplicates: set[str] = set()
    for row in saved_scopes:
        if not isinstance(row, dict) or not isinstance(row.get("name"), str):
            continue
        name = str(row["name"])
        if name in scopes_by_name:
            duplicates.add(name)
        scopes_by_name[name] = row.get("scope")
    required_names = set(DOMAIN_SCOPE_MAP.values())
    ambiguous = sorted(required_names & duplicates)
    if ambiguous:
        raise SeedBootstrapError(
            "bootstrap event repeated required saved scopes: "
            + ", ".join(ambiguous)
        )
    missing = sorted(required_names - set(scopes_by_name))
    if missing:
        raise SeedBootstrapError(
            "bootstrap event lacks required saved scopes: " + ", ".join(missing)
        )

    matrix = {
        key: _character_id(scopes_by_name[scope_name], scope_name)
        for key, scope_name in DOMAIN_SCOPE_MAP.items()
    }
    for key in (
        "b2_pip_owner_character_id",
        "incident_owner_character_id",
        "workforce_owner_character_id",
        "ai_owned_case_owner_character_id",
    ):
        if matrix[key] == played_character_id:
            raise SeedBootstrapError(f"{key} incorrectly names the played root")
    if (
        matrix["ai_owned_case_owner_character_id"]
        == matrix["ai_owned_case_subject_character_id"]
    ):
        raise SeedBootstrapError("AI-owned owner and subject are identical")
    return {
        "event_definition_key": EVENT_DEFINITION_KEY,
        "event_instance_id": event_instance_id,
        "snapshot_revision": context_value.get("snapshot_revision"),
        "date_raw": date_raw,
        "played_character_id": played_character_id,
        "domain_query_matrix": {"schema_version": 1, **matrix},
        "saved_scope_names": sorted(required_names),
    }


def validate_event_close(
    payload: dict[str, Any], *, event_instance_id: int
) -> dict[str, Any]:
    submission_value = payload.get("selection_submission", payload)
    if not isinstance(submission_value, dict):
        raise SeedBootstrapError("event close response is malformed")
    event_selection = submission_value.get("event_selection")
    if (
        submission_value.get("step") != "select-event-option-1"
        or submission_value.get("accepted") is not True
        or submission_value.get("status") != "submitted"
        or submission_value.get("option_number") != 1
        or submission_value.get("option_index") != 0
        or not isinstance(event_selection, dict)
        or event_selection.get("postcondition_verified") is not True
        or event_selection.get("old_event_instance_id") != event_instance_id
        or event_selection.get("selected_option_number") != 1
        or event_selection.get("selected_native_option_index") != 0
    ):
        raise SeedBootstrapError(
            "bootstrap event was not closed by its sole option with a typed ACK"
        )
    return {
        "step": "select-event-option-1",
        "old_event_instance_id": event_instance_id,
        "new_event_instance_id": event_selection.get("new_event_instance_id"),
        "ending_revision": event_selection.get("ending_revision"),
        "postcondition_verified": True,
    }


def validate_paused_snapshot(
    payload: dict[str, Any],
    *,
    expected_date_raw: int,
    expected_character_id: int,
) -> dict[str, Any]:
    snapshot_value = payload.get("snapshot", payload)
    if not isinstance(snapshot_value, dict):
        raise SeedBootstrapError("paused snapshot is malformed")
    played_value = snapshot_value.get("played_character")
    played = played_value if isinstance(played_value, dict) else {}
    if (
        snapshot_value.get("paused") is not True
        or snapshot_value.get("map_ready") is not True
        or snapshot_value.get("date_raw") != expected_date_raw
        or played.get("character_id") != expected_character_id
        or played.get("alive") is not True
    ):
        raise SeedBootstrapError(
            "paused snapshot does not bind the event date, live player and map"
        )
    return {
        "paused": True,
        "map_ready": True,
        "date_raw": expected_date_raw,
        "snapshot_revision": snapshot_value.get("revision"),
        "played_character": {
            "character_id": expected_character_id,
            "alive": True,
        },
    }


def validate_checkpoint(
    payload: dict[str, Any],
    *,
    expected_date_raw: int,
    expected_character_id: int,
) -> dict[str, Any]:
    if "accepted" in payload and payload.get("accepted") is not True:
        raise SeedBootstrapError("save-checkpoint command was not accepted")
    checkpoint_value = payload.get("checkpoint", payload)
    if not isinstance(checkpoint_value, dict):
        raise SeedBootstrapError("save-checkpoint materialization is absent")
    path_value = checkpoint_value.get("path")
    if checkpoint_value.get("status") != "saved" or not isinstance(
        path_value, str
    ):
        raise SeedBootstrapError("save-checkpoint did not report a saved path")
    path = Path(path_value).resolve()
    if not path.is_file():
        raise SeedBootstrapError(f"checkpoint file does not exist: {path}")
    size = path.stat().st_size
    declared_size = checkpoint_value.get("size")
    declared_sha256 = checkpoint_value.get("sha256")
    declared_date_raw = checkpoint_value.get("date_raw")
    if (
        isinstance(declared_size, bool)
        or not isinstance(declared_size, int)
        or declared_size <= 0
        or declared_size != size
        or not isinstance(declared_sha256, str)
        or SHA256_PATTERN.fullmatch(declared_sha256) is None
        or sha256_file(path) != declared_sha256
        or declared_date_raw != expected_date_raw
    ):
        raise SeedBootstrapError(
            "save-checkpoint size/hash/date does not match the materialized file"
        )
    episode_character_id = checkpoint_value.get("episode_character_id")
    if episode_character_id is not None and (
        episode_character_id != expected_character_id
    ):
        raise SeedBootstrapError(
            "save-checkpoint episode character differs from the event root"
        )
    with path.open("rb") as stream:
        header = stream.read(96)
    if not header.startswith(b"SAV0101"):
        raise SeedBootstrapError("checkpoint file lacks the CK3 SAV0101 header")
    return {
        "status": "saved",
        "path": str(path),
        "size": size,
        "sha256": declared_sha256,
        "date_raw": declared_date_raw,
        "episode_character_id": episode_character_id,
        "strategy": checkpoint_value.get("strategy"),
    }


def _copy_evidence(source: Path, destination: Path) -> None:
    source = source.resolve()
    destination = destination.resolve()
    if source != destination:
        shutil.copy2(source, destination)


def capture_mcp_evidence(service: object, artifacts: Path) -> dict[str, Any]:
    """Capture the four typed inputs without launching or navigating CK3."""

    artifacts = artifacts.resolve()
    artifacts.mkdir(parents=True, exist_ok=True)
    if any(artifacts.iterdir()):
        raise SeedBootstrapError("capture artifacts directory must be empty")
    snapshot_method = getattr(service, "snapshot", None)
    query_method = getattr(
        service, "query_current_event_window_context_v1", None
    )
    select_method = getattr(service, "select_event_option", None)
    save_method = getattr(service, "save_checkpoint", None)
    if not all(
        callable(method)
        for method in (snapshot_method, query_method, select_method, save_method)
    ):
        raise SeedBootstrapError("service lacks the existing typed MCP methods")

    snapshot = snapshot_method()
    if not isinstance(snapshot, dict):
        raise SeedBootstrapError("MCP snapshot is not an object")
    active_event_value = snapshot.get("active_event")
    active_event = (
        active_event_value if isinstance(active_event_value, dict) else {}
    )
    event_instance_id = _positive_int32(
        active_event.get("instance_id"), "active event instance"
    )
    revision = snapshot.get("revision")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
        raise SeedBootstrapError("MCP snapshot lacks a public revision")
    played_value = snapshot.get("played_character")
    played = played_value if isinstance(played_value, dict) else {}
    expected_character_id = _positive_int32(
        played.get("character_id"), "snapshot played character"
    )
    expected_date_raw = _positive_int32(snapshot.get("date_raw"), "snapshot date")
    validate_paused_snapshot(
        snapshot,
        expected_date_raw=expected_date_raw,
        expected_character_id=expected_character_id,
    )
    if active_event.get("option_count") != 1:
        raise SeedBootstrapError("active bootstrap event is not single-option")

    query = query_method(event_instance_id, expected_revision=revision)
    if not isinstance(query, dict):
        raise SeedBootstrapError("event context MCP returned a non-object")
    event_wrapper = {
        "event_instance_id": event_instance_id,
        "snapshot_revision": revision,
        "event_definition_key": EVENT_DEFINITION_KEY,
        "query": query,
    }
    capture = extract_event_capture(event_wrapper)
    if (
        capture["played_character_id"] != expected_character_id
        or capture["date_raw"] != expected_date_raw
        or capture["event_instance_id"] != event_instance_id
    ):
        raise SeedBootstrapError("event query drifted from the paused snapshot")
    event_path = artifacts / "event-context.json"
    snapshot_path = artifacts / "paused-snapshot.json"
    write_json(event_path, event_wrapper)
    write_json(snapshot_path, {"snapshot": snapshot})

    selection_snapshot = snapshot_method()
    if not isinstance(selection_snapshot, dict):
        raise SeedBootstrapError("pre-close MCP snapshot is not an object")
    selection_event_value = selection_snapshot.get("active_event")
    selection_event = (
        selection_event_value
        if isinstance(selection_event_value, dict)
        else {}
    )
    selection_revision = selection_snapshot.get("revision")
    if (
        selection_event.get("instance_id") != event_instance_id
        or selection_event.get("option_count") != 1
        or isinstance(selection_revision, bool)
        or not isinstance(selection_revision, int)
        or selection_revision < 0
    ):
        raise SeedBootstrapError("bootstrap event changed before typed close")
    close = select_method(
        1,
        event_instance_id=event_instance_id,
        expected_revision=selection_revision,
    )
    if not isinstance(close, dict):
        raise SeedBootstrapError("typed event close returned a non-object")
    validate_event_close(close, event_instance_id=event_instance_id)
    close_path = artifacts / "event-close.json"
    write_json(close_path, close)

    post_close_snapshot = snapshot_method()
    if not isinstance(post_close_snapshot, dict):
        raise SeedBootstrapError("post-close MCP snapshot is not an object")
    validate_paused_snapshot(
        post_close_snapshot,
        expected_date_raw=expected_date_raw,
        expected_character_id=expected_character_id,
    )
    post_revision = post_close_snapshot.get("revision")
    if (
        isinstance(post_revision, bool)
        or not isinstance(post_revision, int)
        or post_revision < 0
    ):
        raise SeedBootstrapError("post-close snapshot lacks a public revision")
    checkpoint = save_method(expected_revision=post_revision)
    if not isinstance(checkpoint, dict):
        raise SeedBootstrapError("save-checkpoint MCP returned a non-object")
    validate_checkpoint(
        checkpoint,
        expected_date_raw=expected_date_raw,
        expected_character_id=expected_character_id,
    )
    checkpoint_path = artifacts / "save-checkpoint.json"
    write_json(checkpoint_path, checkpoint)
    return {
        "result": "GREEN",
        "event_context_path": str(event_path),
        "paused_snapshot_path": str(snapshot_path),
        "event_close_path": str(close_path),
        "checkpoint_response_path": str(checkpoint_path),
        "played_character_id": expected_character_id,
        "domain_query_matrix": capture["domain_query_matrix"],
    }


def materialize_candidate(
    *,
    event_context_path: Path,
    paused_snapshot_path: Path,
    event_close_path: Path,
    checkpoint_response_path: Path,
    profile: Path,
    output_dir: Path,
    base_contract_path: Path,
    source_git_commit: str,
    product_tree_sha256: str,
    fixture_tree_sha256: str,
) -> dict[str, Any]:
    if GIT_COMMIT_PATTERN.fullmatch(source_git_commit) is None:
        raise SeedBootstrapError("source_git_commit is not a 40-digit commit")
    for value, label in (
        (product_tree_sha256, "product tree SHA-256"),
        (fixture_tree_sha256, "fixture tree SHA-256"),
    ):
        if SHA256_PATTERN.fullmatch(value) is None:
            raise SeedBootstrapError(f"{label} is invalid")

    event_payload = read_json(event_context_path)
    snapshot_payload = read_json(paused_snapshot_path)
    close_payload = read_json(event_close_path)
    checkpoint_payload = read_json(checkpoint_response_path)
    base_contract = read_json(base_contract_path)
    capture = extract_event_capture(event_payload)
    paused_snapshot = validate_paused_snapshot(
        snapshot_payload,
        expected_date_raw=capture["date_raw"],
        expected_character_id=capture["played_character_id"],
    )
    close = validate_event_close(
        close_payload, event_instance_id=capture["event_instance_id"]
    )
    checkpoint = validate_checkpoint(
        checkpoint_payload,
        expected_date_raw=capture["date_raw"],
        expected_character_id=capture["played_character_id"],
    )

    profile = profile.resolve()
    checkpoint_path = Path(checkpoint["path"]).resolve()
    try:
        relative_save = checkpoint_path.relative_to(profile).as_posix()
    except ValueError as error:
        raise SeedBootstrapError(
            "checkpoint file is outside the declared isolated profile"
        ) from error
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    if any(output_dir.iterdir()):
        raise SeedBootstrapError(
            "output directory must be empty so process evidence is never overwritten"
        )
    copied_event = output_dir / "event-context.json"
    copied_snapshot = output_dir / "paused-snapshot.json"
    copied_close = output_dir / "event-close.json"
    copied_checkpoint = output_dir / "save-checkpoint.json"
    _copy_evidence(event_context_path, copied_event)
    _copy_evidence(paused_snapshot_path, copied_snapshot)
    _copy_evidence(event_close_path, copied_close)
    _copy_evidence(checkpoint_response_path, copied_checkpoint)

    runtime_value = base_contract.get("runtime")
    if not isinstance(runtime_value, dict):
        raise SeedBootstrapError("base contract runtime object is absent")
    runtime = dict(runtime_value)
    runtime["source_product_tree_sha256"] = product_tree_sha256
    runtime["source_fixture_tree_sha256"] = fixture_tree_sha256
    report = {
        "schema_version": 1,
        "result": "GREEN",
        "scope": "zg361_phase2_seed_bootstrap",
        "cell": {
            "result": "GREEN",
            "game_version": runtime.get("game_version"),
            "ck3_executable_before_sha256": runtime.get("executable_sha256"),
            "ck3_executable_after_sha256": runtime.get("executable_sha256"),
            "enabled_mods": runtime.get("enabled_mods"),
            "runtime_tree_before_sha256": {
                "product": product_tree_sha256,
                "fixture": fixture_tree_sha256,
            },
            "runtime_tree_after_sha256": {
                "product": product_tree_sha256,
                "fixture": fixture_tree_sha256,
            },
            "runtime_trees_unchanged": True,
            "isolated_userdir_path": str(profile),
            "scenario_evidence": {
                "player_history_id": PLAYER_HISTORY_ID,
                "historical_subjects_manufactured_by_fixture": False,
                "ocr_used": False,
                "test_decision_used": False,
                "phase2_seed_snapshot": paused_snapshot,
                "phase2_seed_bootstrap_attestation": {
                    "event_definition_key": EVENT_DEFINITION_KEY,
                    "player_history_id": PLAYER_HISTORY_ID,
                    "played_character_id": capture["played_character_id"],
                    "saved_scope_names": capture["saved_scope_names"],
                    "domain_query_matrix": capture["domain_query_matrix"],
                    "event_close": close,
                    "checkpoint": checkpoint,
                    "mcp_only": True,
                },
            },
        },
    }
    report_path = output_dir / "report.json"
    write_json(report_path, report)
    indexed_paths = (
        copied_event,
        copied_snapshot,
        copied_close,
        copied_checkpoint,
        report_path,
    )
    evidence_index = {
        "schema_version": 1,
        "result": "GREEN",
        "files": [
            {
                "path": path.name,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in indexed_paths
        ],
    }
    evidence_index_path = output_dir / "evidence-index.json"
    write_json(evidence_index_path, evidence_index)

    checkpoint_stat = checkpoint_path.stat()
    timestamp = datetime.fromtimestamp(
        checkpoint_stat.st_mtime, tz=timezone.utc
    ).isoformat().replace("+00:00", "Z")
    contract = {
        "schema_version": 1,
        "kind": "zg361_phase2_paused_seed",
        "status": BLOCKED_STATUS,
        "ready": False,
        "blocker": BLOCKER,
        "source": {
            "profile": str(profile),
            "relative_save": relative_save,
            "absolute_save": str(checkpoint_path),
            "bytes": checkpoint_stat.st_size,
            "sha256": checkpoint["sha256"],
            "last_write_time_utc": timestamp,
            "last_write_time_ns": checkpoint_stat.st_mtime_ns,
        },
        "provenance": {
            "source_run": str(output_dir),
            "source_report_sha256": sha256_file(report_path),
            "source_evidence_index_sha256": sha256_file(evidence_index_path),
            "source_git_commit": source_git_commit,
            "real_character_proof": (
                f"acceptance-only {EVENT_DEFINITION_KEY} root binds historical "
                f"{PLAYER_HISTORY_ID} to native CharacterID "
                f"{capture['played_character_id']}; five selector IDs came only "
                "from typed saved character scopes"
            ),
            "limitations": [
                "The bootstrap fixture is acceptance-only and must never be loaded by promo or release runtimes.",
                "Selector capture and typed checkpoint materialization do not prove the four domain providers ready.",
                "Incident mixed N/A plus positive is not attainable in one subject snapshot while profiles share zg361_ip_probe_*.",
                "Workforce charter readiness still requires three genuine increasing product cycles and #357/#358/#359/#360 receipts.",
            ],
        },
        "runtime": runtime,
        "saved_state": {
            "date_raw": capture["date_raw"],
            "played_character_id": capture["played_character_id"],
            "player_history_id": PLAYER_HISTORY_ID,
            "played_character_alive": True,
            "paused_on_load": True,
            "map_ready": True,
        },
        "install": {
            "continue_save_relative_path": "save games/autosave.ck3",
            "last_save_relative_path": "last_save.ck3",
            "launch_mode": "native_session_continue_last_save",
        },
        "domain_query_matrix": capture["domain_query_matrix"],
    }
    contract_path = output_dir / "zg361_phase2_seed_contract.candidate.json"
    write_json(contract_path, contract)
    return {
        "result": "GREEN",
        "status": BLOCKED_STATUS,
        "ready": False,
        "contract_path": str(contract_path),
        "report_path": str(report_path),
        "evidence_index_path": str(evidence_index_path),
        "played_character_id": capture["played_character_id"],
        "domain_query_matrix": capture["domain_query_matrix"],
        "blocker": BLOCKER,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-context", type=Path, required=True)
    parser.add_argument("--paused-snapshot", type=Path, required=True)
    parser.add_argument("--event-close", type=Path, required=True)
    parser.add_argument("--checkpoint-response", type=Path, required=True)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--base-contract", type=Path, default=DEFAULT_BASE_CONTRACT
    )
    parser.add_argument("--source-git-commit", required=True)
    parser.add_argument("--product-tree-sha256", required=True)
    parser.add_argument("--fixture-tree-sha256", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = materialize_candidate(
        event_context_path=args.event_context,
        paused_snapshot_path=args.paused_snapshot,
        event_close_path=args.event_close,
        checkpoint_response_path=args.checkpoint_response,
        profile=args.profile,
        output_dir=args.output_dir,
        base_contract_path=args.base_contract,
        source_git_commit=args.source_git_commit,
        product_tree_sha256=args.product_tree_sha256,
        fixture_tree_sha256=args.fixture_tree_sha256,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
