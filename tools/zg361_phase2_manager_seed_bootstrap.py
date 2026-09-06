#!/usr/bin/env python3
"""Materialize a player-manager Phase-2 seed from typed MCP evidence.

The dedicated fixture only exposes a live, eligible human manager and one
already-existing direct reviewable vassal.  This helper records those typed
identities and the paused checkpoint; it never creates product receipts and
never treats the acceptance event itself as a product business result.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import zg361_phase2_seed_bootstrap as shared


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_CONTRACT = ROOT / "tools" / "zg361_phase2_manager_seed_contract.json"
EVENT_DEFINITION_KEY = "zga_phase2_manager_seed.1"
MANAGER_SCOPE = "zga_phase2_manager_owner"
SUBJECT_SCOPE = "zga_phase2_manager_subject"
READY_STATUS = "ready"
GIT_COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}")
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


class ManagerSeedBootstrapError(shared.SeedBootstrapError):
    """Player-manager evidence is absent, ambiguous, or contradictory."""


def _context(payload: dict[str, Any]) -> dict[str, Any]:
    query = payload.get("query", payload)
    if not isinstance(query, dict):
        raise ManagerSeedBootstrapError("event query wrapper is malformed")
    if "accepted" in query and query.get("accepted") is not True:
        raise ManagerSeedBootstrapError("event context query was not accepted")
    if "step" in query and query.get("step") != (
        "query-current-event-window-context-v1"
    ):
        raise ManagerSeedBootstrapError("event context came from the wrong MCP step")
    context = query.get("current_event_window_context", query)
    if not isinstance(context, dict):
        raise ManagerSeedBootstrapError("current event context is absent")
    return context


def extract_event_capture(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract one played manager and one existing direct vassal identity."""

    context = _context(payload)
    if (
        context.get("schema") != "current-event-window-context-v1"
        or context.get("schema_version") != 1
        or context.get("status") != "available"
        or context.get("window_match_count") != 1
        or context.get("event_definition_key") != EVENT_DEFINITION_KEY
    ):
        raise ManagerSeedBootstrapError(
            "current event context is not the unique player-manager seed event"
        )
    options = context.get("options")
    if not (
        isinstance(options, list)
        and len(options) == 1
        and isinstance(options[0], dict)
        and options[0].get("shown") is True
        and options[0].get("enabled") is True
        and options[0].get("native_option_index") == 0
    ):
        raise ManagerSeedBootstrapError(
            "player-manager seed event does not expose one enabled option"
        )

    manager_id = shared._character_id(context.get("root_scope"), "manager root")
    date_raw = shared._positive_int32(context.get("date_raw"), "event date_raw")
    event_instance_id = shared._positive_int32(
        context.get("current_event_instance_id"), "event instance"
    )
    saved_scopes = context.get("saved_scopes")
    if not isinstance(saved_scopes, list):
        raise ManagerSeedBootstrapError("manager seed saved scopes are absent")
    by_name: dict[str, object] = {}
    duplicates: set[str] = set()
    for row in saved_scopes:
        if not isinstance(row, dict) or not isinstance(row.get("name"), str):
            continue
        name = str(row["name"])
        if name in by_name:
            duplicates.add(name)
        by_name[name] = row.get("scope")
    required = {MANAGER_SCOPE, SUBJECT_SCOPE}
    if required & duplicates:
        raise ManagerSeedBootstrapError("manager seed repeated a required saved scope")
    missing = sorted(required - set(by_name))
    if missing:
        raise ManagerSeedBootstrapError(
            "manager seed lacks required saved scopes: " + ", ".join(missing)
        )
    saved_manager_id = shared._character_id(by_name[MANAGER_SCOPE], MANAGER_SCOPE)
    subject_id = shared._character_id(by_name[SUBJECT_SCOPE], SUBJECT_SCOPE)
    if saved_manager_id != manager_id:
        raise ManagerSeedBootstrapError(
            "saved manager identity differs from the played event root"
        )
    if subject_id == manager_id:
        raise ManagerSeedBootstrapError("manager and reviewable subject are identical")
    return {
        "event_definition_key": EVENT_DEFINITION_KEY,
        "event_instance_id": event_instance_id,
        "snapshot_revision": context.get("snapshot_revision"),
        "date_raw": date_raw,
        "played_character_id": manager_id,
        "manager_entry": {
            "schema_version": 1,
            "manager_character_id": manager_id,
            "reviewable_subject_character_id": subject_id,
            "manager_scope": MANAGER_SCOPE,
            "subject_scope": SUBJECT_SCOPE,
            "human": True,
            "alive": True,
            "landed": True,
            "celestial_liege": True,
            "game_rule_enabled": True,
            "existing_direct_reviewable_vassal_count_minimum": 1,
            "b1_active": False,
            "central_active": False,
            "pp_active": False,
            "review_now_eligible": True,
        },
    }


def capture_mcp_evidence(service: object, artifacts: Path) -> dict[str, Any]:
    """Capture event scopes, close ACK and checkpoint through typed MCP only."""

    artifacts = artifacts.resolve()
    artifacts.mkdir(parents=True, exist_ok=True)
    if any(artifacts.iterdir()):
        raise ManagerSeedBootstrapError("capture artifacts directory must be empty")
    methods = {
        "snapshot": getattr(service, "snapshot", None),
        "query": getattr(service, "query_current_event_window_context_v1", None),
        "select": getattr(service, "select_event_option", None),
        "save": getattr(service, "save_checkpoint", None),
    }
    if not all(callable(method) for method in methods.values()):
        raise ManagerSeedBootstrapError("service lacks the existing typed MCP methods")

    snapshot = methods["snapshot"]()
    if not isinstance(snapshot, dict):
        raise ManagerSeedBootstrapError("MCP snapshot is not an object")
    active = snapshot.get("active_event")
    if not isinstance(active, dict) or active.get("option_count") != 1:
        raise ManagerSeedBootstrapError("active manager seed event is not single-option")
    event_instance_id = shared._positive_int32(
        active.get("instance_id"), "active event instance"
    )
    revision = snapshot.get("revision")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
        raise ManagerSeedBootstrapError("MCP snapshot lacks a public revision")
    played = snapshot.get("played_character")
    played_id = shared._positive_int32(
        played.get("character_id") if isinstance(played, dict) else None,
        "snapshot played character",
    )
    date_raw = shared._positive_int32(snapshot.get("date_raw"), "snapshot date")
    shared.validate_paused_snapshot(
        snapshot,
        expected_date_raw=date_raw,
        expected_character_id=played_id,
    )
    query = methods["query"](event_instance_id, expected_revision=revision)
    if not isinstance(query, dict):
        raise ManagerSeedBootstrapError("event context MCP returned a non-object")
    event_wrapper = {
        "event_instance_id": event_instance_id,
        "snapshot_revision": revision,
        "event_definition_key": EVENT_DEFINITION_KEY,
        "query": query,
    }
    capture = extract_event_capture(event_wrapper)
    if (
        capture["played_character_id"] != played_id
        or capture["date_raw"] != date_raw
        or capture["event_instance_id"] != event_instance_id
    ):
        raise ManagerSeedBootstrapError("manager event query drifted from snapshot")

    event_path = artifacts / "event-context.json"
    snapshot_path = artifacts / "paused-snapshot.json"
    shared.write_json(event_path, event_wrapper)
    shared.write_json(snapshot_path, {"snapshot": snapshot})
    pre_close = methods["snapshot"]()
    pre_active = pre_close.get("active_event") if isinstance(pre_close, dict) else None
    pre_revision = pre_close.get("revision") if isinstance(pre_close, dict) else None
    if (
        not isinstance(pre_active, dict)
        or pre_active.get("instance_id") != event_instance_id
        or pre_active.get("option_count") != 1
        or isinstance(pre_revision, bool)
        or not isinstance(pre_revision, int)
        or pre_revision < 0
    ):
        raise ManagerSeedBootstrapError("manager seed event changed before close")
    close = methods["select"](
        1,
        event_instance_id=event_instance_id,
        expected_revision=pre_revision,
    )
    if not isinstance(close, dict):
        raise ManagerSeedBootstrapError("typed event close returned a non-object")
    shared.validate_event_close(close, event_instance_id=event_instance_id)
    close_path = artifacts / "event-close.json"
    shared.write_json(close_path, close)

    post_close = methods["snapshot"]()
    if not isinstance(post_close, dict):
        raise ManagerSeedBootstrapError("post-close MCP snapshot is not an object")
    shared.validate_paused_snapshot(
        post_close,
        expected_date_raw=date_raw,
        expected_character_id=played_id,
    )
    post_revision = post_close.get("revision")
    if (
        isinstance(post_revision, bool)
        or not isinstance(post_revision, int)
        or post_revision < 0
    ):
        raise ManagerSeedBootstrapError("post-close snapshot lacks a public revision")
    checkpoint = methods["save"](expected_revision=post_revision)
    if not isinstance(checkpoint, dict):
        raise ManagerSeedBootstrapError("save-checkpoint MCP returned a non-object")
    shared.validate_checkpoint(
        checkpoint,
        expected_date_raw=date_raw,
        expected_character_id=played_id,
    )
    checkpoint_path = artifacts / "save-checkpoint.json"
    shared.write_json(checkpoint_path, checkpoint)
    return {
        "result": "GREEN",
        "event_context_path": str(event_path),
        "paused_snapshot_path": str(snapshot_path),
        "event_close_path": str(close_path),
        "checkpoint_response_path": str(checkpoint_path),
        "played_character_id": played_id,
        "manager_entry": capture["manager_entry"],
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
    """Build one hash-bound manager contract without product-state claims."""

    if GIT_COMMIT_PATTERN.fullmatch(source_git_commit) is None:
        raise ManagerSeedBootstrapError("source_git_commit is not a 40-digit commit")
    for value, label in (
        (product_tree_sha256, "product tree SHA-256"),
        (fixture_tree_sha256, "fixture tree SHA-256"),
    ):
        if SHA256_PATTERN.fullmatch(value) is None:
            raise ManagerSeedBootstrapError(f"{label} is invalid")
    event_payload = shared.read_json(event_context_path)
    snapshot_payload = shared.read_json(paused_snapshot_path)
    close_payload = shared.read_json(event_close_path)
    checkpoint_payload = shared.read_json(checkpoint_response_path)
    base = shared.read_json(base_contract_path)
    capture = extract_event_capture(event_payload)
    paused = shared.validate_paused_snapshot(
        snapshot_payload,
        expected_date_raw=capture["date_raw"],
        expected_character_id=capture["played_character_id"],
    )
    close = shared.validate_event_close(
        close_payload, event_instance_id=capture["event_instance_id"]
    )
    checkpoint = shared.validate_checkpoint(
        checkpoint_payload,
        expected_date_raw=capture["date_raw"],
        expected_character_id=capture["played_character_id"],
    )
    profile = profile.resolve()
    checkpoint_path = Path(checkpoint["path"]).resolve()
    try:
        relative_save = checkpoint_path.relative_to(profile).as_posix()
    except ValueError as error:
        raise ManagerSeedBootstrapError(
            "checkpoint file is outside the declared isolated profile"
        ) from error
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    if any(output_dir.iterdir()):
        raise ManagerSeedBootstrapError("output directory must be empty")
    copied = []
    for source, name in (
        (event_context_path, "event-context.json"),
        (paused_snapshot_path, "paused-snapshot.json"),
        (event_close_path, "event-close.json"),
        (checkpoint_response_path, "save-checkpoint.json"),
    ):
        destination = output_dir / name
        shared._copy_evidence(source, destination)
        copied.append(destination)

    runtime = base.get("runtime")
    saved_state = base.get("saved_state")
    if not isinstance(runtime, dict) or not isinstance(saved_state, dict):
        raise ManagerSeedBootstrapError("base manager contract is malformed")
    runtime = dict(runtime)
    runtime["source_product_tree_sha256"] = product_tree_sha256
    runtime["source_fixture_tree_sha256"] = fixture_tree_sha256
    report = {
        "schema_version": 1,
        "result": "GREEN",
        "scope": "zg361_phase2_player_manager_seed_bootstrap",
        "mcp_only": True,
        "product_receipts_written_by_fixture": False,
        "fixture_opened_product_b1": False,
        "typed_manager_entry": capture["manager_entry"],
        "paused_snapshot": paused,
        "event_close": close,
        "checkpoint": checkpoint,
        "runtime_tree_sha256": {
            "product": product_tree_sha256,
            "fixture": fixture_tree_sha256,
        },
    }
    report_path = output_dir / "report.json"
    shared.write_json(report_path, report)
    copied.append(report_path)
    evidence_index = {
        "schema_version": 1,
        "result": "GREEN",
        "files": [
            {
                "path": path.name,
                "bytes": path.stat().st_size,
                "sha256": shared.sha256_file(path),
            }
            for path in copied
        ],
    }
    index_path = output_dir / "evidence-index.json"
    shared.write_json(index_path, evidence_index)
    stat = checkpoint_path.stat()
    timestamp = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )
    contract = {
        "schema_version": 1,
        "kind": "zg361_phase2_player_manager_paused_seed",
        "seed_purpose": "player-manager",
        "status": READY_STATUS,
        "ready": True,
        "blocker": "",
        "source": {
            "profile": str(profile),
            "relative_save": relative_save,
            "absolute_save": str(checkpoint_path),
            "bytes": stat.st_size,
            "sha256": checkpoint["sha256"],
            "last_write_time_utc": timestamp,
            "last_write_time_ns": stat.st_mtime_ns,
        },
        "provenance": {
            "source_run": str(output_dir),
            "source_report_sha256": shared.sha256_file(report_path),
            "source_evidence_index_sha256": shared.sha256_file(index_path),
            "source_git_commit": source_git_commit,
            "real_character_proof": (
                f"typed {EVENT_DEFINITION_KEY} binds played manager CharacterID "
                f"{capture['played_character_id']} and existing direct vassal "
                f"CharacterID {capture['manager_entry']['reviewable_subject_character_id']}"
            ),
            "limitations": [
                "The acceptance-only fixture event proves entry eligibility and typed identities; it is not a product receipt.",
                "Promotion-source completion remains a separate product-only managed run.",
            ],
        },
        "runtime": runtime,
        "saved_state": {
            "date_raw": capture["date_raw"],
            "played_character_id": capture["played_character_id"],
            # The current native event query proves CharacterID only.  A
            # different valid manager save must not inherit han_6875 from the
            # blocked input request or guess another history key.
            "player_history_id": None,
            "played_character_alive": True,
            "paused_on_load": True,
            "map_ready": True,
        },
        # Full-tree acceptance starts from the captured human manager.  Its
        # already-existing direct reviewable vassal is the subject for the
        # AI-owned and manager-governance cells; every owner-facing domain is
        # intentionally bound to the same played manager.
        "domain_query_matrix": {
            "schema_version": 1,
            "b2_pip_owner_character_id": capture["played_character_id"],
            "incident_owner_character_id": capture["played_character_id"],
            "workforce_owner_character_id": capture["played_character_id"],
            "ai_owned_case_owner_character_id": capture["played_character_id"],
            "ai_owned_case_subject_character_id": capture["manager_entry"][
                "reviewable_subject_character_id"
            ],
        },
        "install": {
            "continue_save_relative_path": "save games/autosave.ck3",
            "last_save_relative_path": "last_save.ck3",
            "launch_mode": "native_session_continue_last_save",
        },
        "manager_entry": capture["manager_entry"],
    }
    contract_path = output_dir / "zg361_phase2_manager_seed_contract.candidate.json"
    shared.write_json(contract_path, contract)
    return {
        "result": "GREEN",
        "status": READY_STATUS,
        "ready": True,
        "contract_path": str(contract_path),
        "report_path": str(report_path),
        "evidence_index_path": str(index_path),
        "played_character_id": capture["played_character_id"],
        "manager_entry": capture["manager_entry"],
        "blocker": "",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-context", type=Path, required=True)
    parser.add_argument("--paused-snapshot", type=Path, required=True)
    parser.add_argument("--event-close", type=Path, required=True)
    parser.add_argument("--checkpoint-response", type=Path, required=True)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--base-contract", type=Path, default=DEFAULT_BASE_CONTRACT)
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
