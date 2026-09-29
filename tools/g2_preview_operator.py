"""Python-only operator wrapper for the frozen G2 preview package.

This keeps the documented Windows workflow in one reviewable Python entry
point: immutable ZIP verification, new-state preparation, exact preflight,
bounded production execution, stop requests, and report inspection.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import Any, Callable

if __package__:
    from .ck3_live_run_id import (
        STATE_ROOT_ENV,
        allocate_live_run_id,
        record_live_run_status,
        write_identity_receipt,
    )
else:
    from ck3_live_run_id import (
        STATE_ROOT_ENV,
        allocate_live_run_id,
        record_live_run_status,
        write_identity_receipt,
    )


R778_SOURCE_CHECKPOINT_SHA256 = (
    "2c0f4333ae186ee91f560ad7d14abb2f2e29aaa1b4d2eacfefe0c9a8e1e505e3"
)
R778_SOURCE_DRIVER_STATE_SHA256 = (
    "c3fa1268ffa72b49936d36e4c49c7cea182d3c18e2795ddc5586efff136200c9"
)
R778_CK3_EXE_SHA256 = (
    "2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86"
)
R781_PRIVATE_BRIDGE_SHA256 = (
    "4648c1c732b175d556effa11db71c8a16b4de122b941ad7a5e883a79272ee584"
)
R781_INJECTOR_SHA256 = (
    "adedb7c40e09822c8f2dd6f2d7f23af86e88adc8ac7014b09ac083f05f7377dd"
)
R778_CHARACTER_ID = 35465
R778_EPISODE_RUN_ID = "native-35465-cbdf997e3d80"
R778_DATE_RAW = 53411568
ROGUE_ONE_LIFE = "rogue_one_life"
ORDINARY_CAMPAIGN_SUCCESSION = "ordinary_campaign_succession"
LEGACY_LIFECYCLE_CONTRACT = {
    "xar_enabled": "xar_on",
    "succession_lifecycle": ROGUE_ONE_LIFE,
    "ordinary_campaign_no_pact": False,
}
ORDINARY_LIFECYCLE_CONTRACT = {
    "xar_enabled": "xar_off",
    "succession_lifecycle": ORDINARY_CAMPAIGN_SUCCESSION,
    "ordinary_campaign_no_pact": True,
}
ORDINARY_SEED_REBIND_V1_SCHEMA = "xar.ck3.ordinary-seed-rebind/v1"
CONSTRUCTION_PENDING_V1_SCHEMA = "xar.ck3.construction_formal_pending_v1"
CONSTRUCTION_SUBMIT_STEP = "private-submit-player-construction-v1"
CONSTRUCTION_RECEIPT_STEP = "private-query-player-construction-receipt-v1"
FAMILY_PENDING_V1_SCHEMA = "xar.ck3.first-heir-marriage-formal.v1"
FAMILY_ACTION_V1_SCHEMA = "xar.ck3.observed-first-heir-marriage-private-action.v1"
FAMILY_SUBMIT_STEP = "submit-observed-first-heir-marriage-v1-private"
CHILD_MATRILINEAL_SCHEMA = "xar.ck3.player-child-matrilineal-private-action.v1"
CHILD_MATRILINEAL_SUBMIT_STEP = "submit-player-child-matrilineal-marriage-v1-private"
CHILD_MATRILINEAL_PROOF_SCHEMA = "xar.ck3.child-matrilineal-formal-job/v1"
CHILD_MATRILINEAL_COLD_PROOF_SCHEMA = "xar.ck3.child-matrilineal-cold-result-job/v1"
CHILD_MATRILINEAL_RESULT_STEP = "query-player-child-matrilineal-marriage-result-v1-private"
FACTION_GIFT_PENDING_V1_SCHEMA = "xar.ck3.faction_gift_pending_v1"
SWAY_FORMAL_PENDING_V1_SCHEMA = "xar.ck3.active-scheme-sway-formal-private.v1"
SWAY_FORMAL_PENDING_FILENAME = "active-scheme-sway-formal-private-v1.json"
PRIVATE_LIFESTYLE_CMAKE_OPTION = (
    "XAR_CK3_ENABLE_G2_PLAYER_LIFESTYLE_FORMAL_WIRE_PRIVATE_V1"
)
PRIVATE_LIFESTYLE_QUERY_STEPS = (
    "private-query-player-lifestyle-current-state-v1",
    "private-query-player-lifestyle-formal-v1",
    "private-query-player-lifestyle-stock-focus-v1",
)
G2_LIVE_RUN_MOD_KEY = "eternal-recurrence"


def live_run_state_root(configured: Path | None) -> Path:
    """Use the machine's explicit persistent allocator, never its C: default."""
    value = configured or os.environ.get(STATE_ROOT_ENV)
    if not value:
        raise ValueError(
            f"G2 live run requires --live-run-state-root or {STATE_ROOT_ENV}"
        )
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        raise ValueError("G2 live-run state root must be an absolute path")
    root = candidate.resolve()
    if os.name == "nt" and root.drive.casefold() == "c:":
        raise ValueError("G2 live-run state root must be on a non-C drive")
    return root


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value


def write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as stream:
        temporary = Path(stream.name)
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def make_derived_state_owner_writable(path: Path) -> None:
    """Allow prepared state to diverge without changing its frozen source."""

    path.chmod(path.stat().st_mode | stat.S_IWRITE)


def receipt_target_sha256(receipt: dict[str, Any], section: str) -> str:
    section_value = receipt.get(section)
    value = section_value.get("target_sha256") if isinstance(section_value, dict) else None
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-fA-F]{64}", value) is None:
        raise RuntimeError(f"ordinary seed rebind receipt lacks {section}.target_sha256")
    return value.casefold()


def manifest_path(value: Any, field: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError(f"manifest field {field!r} must be a nonempty path")
    return Path(value).resolve()


def load_manifest(path: Path) -> dict[str, Any]:
    manifest = read_json(path)
    for field in ("python", "source_repo", "state_dir", "game_dir", "pipe", "dll", "injector"):
        if not isinstance(manifest.get(field), str) or not manifest[field]:
            raise ValueError(f"manifest field {field!r} is required")
    lifecycle_contract(manifest)
    display_mode_contract(manifest)
    return manifest


def verify_private_lifestyle_dll(manifest: dict[str, Any]) -> dict[str, Any]:
    """Check the pinned DLL contains the exact private LIFE query dispatch keys.

    This is a no-launch build admission check, not proof that a CK3 query works.
    The guarded native dispatch uses these byte strings only when its private
    CMake option is enabled.  Inspect the DLL that the manifest will load,
    rather than a potentially unrelated build directory's CMakeCache.
    """
    dll = manifest_path(manifest["dll"], "dll")
    expected = manifest.get("dll_sha256")
    if not isinstance(expected, str) or re.fullmatch(r"[0-9a-fA-F]{64}", expected) is None:
        raise ValueError("private LIFE DLL admission requires manifest dll_sha256")
    actual = sha256(dll)
    if actual.casefold() != expected.casefold():
        raise ValueError(f"private LIFE DLL hash mismatch: {actual} != {expected}")
    binary = dll.read_bytes()
    missing = [
        step for step in PRIVATE_LIFESTYLE_QUERY_STEPS
        if step.encode("ascii") not in binary
    ]
    if missing:
        raise ValueError(
            "private LIFE DLL lacks native query dispatch keys "
            f"{', '.join(missing)}; rebuild the pinned DLL with "
            f"-D{PRIVATE_LIFESTYLE_CMAKE_OPTION}=ON and rerun no-launch pairing"
        )
    return {
        "dll": str(dll),
        "dll_sha256": actual,
        "private_lifestyle_query_steps_present": list(PRIVATE_LIFESTYLE_QUERY_STEPS),
        "native_cmake_option_required": f"{PRIVATE_LIFESTYLE_CMAKE_OPTION}=ON",
        "game_launched": False,
    }


def command_verify_private_lifestyle_dll(args: argparse.Namespace) -> int:
    result = verify_private_lifestyle_dll(load_manifest(args.manifest.resolve()))
    print(json.dumps({"ok": True, **result}, ensure_ascii=False))
    return 0


def display_mode_contract(manifest: dict[str, Any]) -> str:
    mode = manifest.get("display_mode", "fullscreen")
    if mode not in ("fullscreen", "windowed"):
        raise ValueError("manifest display_mode must be fullscreen or windowed")
    return mode


def lifecycle_contract(manifest: dict[str, Any]) -> dict[str, Any]:
    """Return one complete preview lifecycle contract.

    Manifests created before ordinary-campaign support omitted all three
    fields and retain the legacy xar_on/rogue-one-life behavior.  A manifest
    that mentions any field must record the complete triple so an ordinary
    candidate cannot be inferred or partially relabelled.
    """

    fields = tuple(LEGACY_LIFECYCLE_CONTRACT)
    present = [field for field in fields if field in manifest]
    if not present:
        return {**LEGACY_LIFECYCLE_CONTRACT, "source": "legacy-default"}
    if len(present) != len(fields):
        missing = [field for field in fields if field not in manifest]
        raise ValueError(
            "preview lifecycle manifest is partial; lacks: "
            + ", ".join(missing)
        )
    candidate = {field: manifest[field] for field in fields}
    if candidate == LEGACY_LIFECYCLE_CONTRACT:
        return {**candidate, "source": "manifest"}
    if candidate == ORDINARY_LIFECYCLE_CONTRACT:
        return {**candidate, "source": "manifest"}
    raise ValueError("preview lifecycle manifest fields are inconsistent")


def preflight_lifecycle_arguments(contract: dict[str, Any]) -> list[str]:
    arguments = [
        "--xar-enabled",
        str(contract["xar_enabled"]),
        "--succession-lifecycle",
        str(contract["succession_lifecycle"]),
    ]
    if contract["ordinary_campaign_no_pact"] is True:
        arguments.append("--ordinary-campaign-no-pact")
    return arguments


def agent_command(manifest: dict[str, Any]) -> list[str]:
    source_repo = manifest_path(manifest["source_repo"], "source_repo")
    entry = source_repo / "ck3_autonomous_player" / "agent.py"
    return [
        str(manifest_path(manifest["python"], "python")),
        "-B",
        str(entry),
        "--state-dir",
        str(manifest_path(manifest["state_dir"], "state_dir")),
        "--game-dir",
        str(manifest_path(manifest["game_dir"], "game_dir")),
        "--bridge-mode",
        "native-headless",
        "--bridge-pipe",
        str(manifest["pipe"]),
        "--bridge-dll",
        str(manifest_path(manifest["dll"], "dll")),
        "--bridge-injector",
        str(manifest_path(manifest["injector"], "injector")),
    ]


def current_checkpoint_identity(manifest: dict[str, Any]) -> tuple[Path, Path, dict[str, Any]]:
    state_dir = manifest_path(manifest["state_dir"], "state_dir")
    save = state_dir / "profile" / "save games" / "xar_checkpoint.ck3"
    driver_path = state_dir / "native-session" / "driver-state.json"
    if not save.is_file() or not driver_path.is_file():
        raise FileNotFoundError("paired checkpoint save or driver state is missing")
    driver = read_json(driver_path)
    return save, driver_path, driver


def episode_value(driver: dict[str, Any], manifest: dict[str, Any], key: str) -> Any:
    value = driver.get(key, manifest.get(key))
    if value is None or value == "":
        raise ValueError(f"paired checkpoint does not provide {key!r}")
    return value


def construction_pending_sidecar_request(
    sidecar: dict[str, Any], driver: dict[str, Any], manifest: dict[str, Any]
) -> str:
    """Pair a submitted or applied construction ledger with saved driver evidence."""

    pending = sidecar.get("pending")
    applied = sidecar.get("applied")
    applied_prior = sidecar.get("applied_prior", [])
    # A later construction may be submitted while an earlier verified
    # building remains in `applied` for its completion and income readback.
    is_pending = isinstance(pending, dict)
    is_applied = pending is None and isinstance(applied, dict)
    record = pending if is_pending else applied
    checkpoint = driver.get("last_checkpoint")
    history = driver.get("command_history")
    if (sidecar.get("schema") != CONSTRUCTION_PENDING_V1_SCHEMA
            or not (is_pending or is_applied)
            or (is_pending and record.get("status") != "submitted_verification_pending")
            or (is_applied and (
                record.get("status") != "applied"
                or record.get("postcondition_verified") is not True
                or record.get("completion_status") not in ("in_progress", "completed")))
            or (applied is not None and not isinstance(applied, dict))
            or not isinstance(applied_prior, list)
            or any(not isinstance(prior, dict) for prior in applied_prior)
            or not isinstance(checkpoint, dict)
            or not isinstance(history, list)):
        raise ValueError("construction sidecar lacks a saved pending or applied action")
    request_id = record.get("action_request_id")
    actor = episode_value(driver, manifest, "episode_character_id")
    episode = episode_value(driver, manifest, "episode_run_id")
    checkpoint_index = checkpoint.get("history_index")
    if (not isinstance(request_id, str)
            or re.fullmatch(r"construction-submit-[0-9a-f]{32}", request_id) is None
            or type(actor) is not int or actor <= 0
            or not isinstance(episode, str)
            or record.get("actor_character_id") != actor
            or record.get("episode_run_id") != episode
            or checkpoint.get("episode_character_id") != actor
            or checkpoint.get("episode_run_id") != episode
            or type(checkpoint_index) is not int
            or not any(
                isinstance(row, dict)
                and row.get("command") == (
                    CONSTRUCTION_SUBMIT_STEP if is_pending else CONSTRUCTION_RECEIPT_STEP)
                and type(row.get("index")) is int
                and row["index"] <= checkpoint_index
                and row.get("result") == record
                for row in history
            )):
        raise ValueError("construction sidecar does not match checkpoint actor/episode/action")
    if is_applied and not any(
        isinstance(row, dict)
        and row.get("command") == CONSTRUCTION_SUBMIT_STEP
        and type(row.get("index")) is int
        and row["index"] <= checkpoint_index
        and isinstance(row.get("result"), dict)
        and row["result"].get("status") == "submitted_verification_pending"
        and row["result"].get("action_request_id") == request_id
        and row["result"].get("candidate") == record.get("candidate")
        for row in history
    ):
        raise ValueError("construction applied sidecar lacks its saved submit action")
    seen_requests = {request_id}
    current_candidate = record.get("candidate")
    seen_candidates = [current_candidate] if isinstance(current_candidate, dict) else []
    # When the newest action is pending, the previous `applied` is another
    # retained material receipt, with the same history requirement as priors.
    retained_applied = [applied] if is_pending and isinstance(applied, dict) else []
    for prior in [*retained_applied, *applied_prior]:
        prior_request_id = prior.get("action_request_id")
        prior_candidate = prior.get("candidate")
        if (prior.get("status") != "applied"
                or prior.get("postcondition_verified") is not True
                or prior.get("completion_status") not in ("in_progress", "completed")
                or not isinstance(prior_request_id, str)
                or re.fullmatch(r"construction-submit-[0-9a-f]{32}", prior_request_id) is None
                or not isinstance(prior_candidate, dict)
                or not prior_candidate
                or prior.get("actor_character_id") != actor
                or prior.get("episode_run_id") != episode
                or prior_request_id in seen_requests
                or prior_candidate in seen_candidates):
            raise ValueError("construction prior applied sidecar has invalid or duplicate action")
        if not any(
            isinstance(row, dict)
            and row.get("command") == CONSTRUCTION_RECEIPT_STEP
            and type(row.get("index")) is int
            and row["index"] <= checkpoint_index
            and row.get("result") == prior
            for row in history
        ):
            raise ValueError("construction prior applied sidecar does not match checkpoint receipt")
        if not any(
            isinstance(row, dict)
            and row.get("command") == CONSTRUCTION_SUBMIT_STEP
            and type(row.get("index")) is int
            and row["index"] <= checkpoint_index
            and isinstance(row.get("result"), dict)
            and row["result"].get("status") == "submitted_verification_pending"
            and row["result"].get("action_request_id") == prior_request_id
            and row["result"].get("candidate") == prior_candidate
            for row in history
        ):
            raise ValueError("construction prior applied sidecar lacks its saved submit action")
        seen_requests.add(prior_request_id)
        seen_candidates.append(prior_candidate)
    return request_id


def faction_gift_pending_sidecar_request(
    sidecar: dict[str, Any], driver: dict[str, Any],
    manifest: dict[str, Any], save_sha256: str,
) -> str:
    """Bind an unresolved gift to the exact pre-submit save and driver."""
    pending = sidecar.get("pending")
    checkpoint = driver.get("last_checkpoint")
    if (sidecar.get("schema") != FACTION_GIFT_PENDING_V1_SCHEMA
            or sidecar.get("format_version") != 1
            or not isinstance(pending, dict)
            or not isinstance(sidecar.get("resolved_request_outcomes"), dict)
            or not isinstance(checkpoint, dict)):
        raise ValueError("faction gift sidecar lacks one unresolved action")
    request_id = pending.get("request_id")
    actor = episode_value(driver, manifest, "episode_character_id")
    episode = episode_value(driver, manifest, "episode_run_id")
    if (not isinstance(request_id, str)
            or re.fullmatch(r"faction-gift-[0-9a-f]{32}", request_id) is None
            or request_id in sidecar["resolved_request_outcomes"]
            or pending.get("status") not in {
                "submission_started_unconfirmed",
                "submitted_verification_pending", "restore_requery_required",
            }
            or type(actor) is not int or actor <= 0
            or not isinstance(episode, str)
            or pending.get("pre_player_character_id") != actor
            or pending.get("episode_run_id") != episode
            or pending.get("pre_date_raw") != checkpoint.get("date_raw")
            or checkpoint.get("episode_character_id") != actor
            or checkpoint.get("episode_run_id") != episode
            or checkpoint.get("sha256") != save_sha256
            or pending.get("checkpoint_sha256_before_submit") != save_sha256):
        raise ValueError("faction gift sidecar does not match pre-submit save/driver")
    return request_id


def sway_formal_pending_sidecar_request(
    sidecar: dict[str, Any], driver: dict[str, Any],
    save_sha256: str, save_size: int,
) -> str:
    """Pair one unresolved native Sway ACK with its material checkpoint."""
    pending = sidecar.get("pending")
    checkpoint = driver.get("last_checkpoint")
    if (sidecar.get("schema") != SWAY_FORMAL_PENDING_V1_SCHEMA
            or sidecar.get("resolved") is not None
            or not isinstance(pending, dict)
            or pending.get("stage") != "receipt_pending"
            or not isinstance(checkpoint, dict)):
        raise ValueError("Sway sidecar lacks a saved pending native ACK")
    ack = pending.get("ack")
    actor = pending.get("actor_character_id")
    target = pending.get("target_character_id")
    action_id = pending.get("action_id")
    epoch = pending.get("pre_capture_epoch")
    generation = pending.get("pre_container_generation")
    date_raw = pending.get("pre_date_raw")
    opinion = pending.get("pre_target_opinion_of_actor")
    if (not isinstance(ack, dict)
            or not isinstance(action_id, str)
            or re.fullmatch(r"sway-[0-9a-f]{32}", action_id) is None
            or type(actor) is not int or actor <= 0
            or type(target) is not int or not 0 < target <= 0xFFFFFFFF
            or target == actor
            or type(epoch) is not int or epoch <= 0
            or type(generation) is not int or generation <= 0
            or type(date_raw) is not int
            or type(opinion) is not int or not -100 <= opinion <= 100
            or type(pending.get("pre_native_revision")) is not int
            or pending["pre_native_revision"] <= 0
            or ack.get("schema") != "active-scheme-sway-formal-private-v1"
            or ack.get("stage") != "submitted_verification_pending"
            or ack.get("action_id") != action_id
            or ack.get("actor_character_id") != actor
            or ack.get("target_character_id") != target
            or type(ack.get("pre_capture_epoch")) is not int
            or ack["pre_capture_epoch"] <= epoch
            or ack.get("pre_container_generation") != generation
            or ack.get("pre_date_raw") != date_raw
            or ack.get("submit_call_count") != 1
            or ack.get("receipt_pending") is not True
            or driver.get("episode_character_id") != actor
            or checkpoint.get("episode_character_id") != actor
            or checkpoint.get("episode_run_id") != driver.get("episode_run_id")
            or not isinstance(driver.get("episode_run_id"), str)
            or not driver["episode_run_id"]
            or checkpoint.get("date_raw") != date_raw
            or checkpoint.get("sha256") != save_sha256
            or checkpoint.get("size") != save_size):
        raise ValueError("Sway pending ACK does not match source save/driver")
    return action_id


def sway_formal_resolved_sidecar_pair(
    sidecar: dict[str, Any], driver: dict[str, Any],
    save_sha256: str, save_size: int,
    pending_report: dict[str, Any], applied_report: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    """Bind a cold native Sway postcondition to its earlier pending checkpoint."""
    pending_action = pending_report.get("private_active_scheme_sway_formal")
    pending_rows = pending_report.get("checkpoints")
    pending_observation = pending_report.get("private_active_scheme_sway_observation")
    if (sidecar.get("schema") != SWAY_FORMAL_PENDING_V1_SCHEMA
            or sidecar.get("pending") is not None
            or not isinstance(sidecar.get("resolved"), dict)
            or pending_report.get("status") != "private_active_scheme_sway_receipt_pending"
            or pending_report.get("ok") is not False
            or not isinstance(pending_action, dict)
            or pending_action.get("status") != "receipt_pending"
            or pending_action.get("checkpoint_saved") is not True
            or pending_action.get("postcondition_verified") is not False
            or not isinstance(pending_action.get("pending"), dict)
            or not isinstance(pending_rows, list) or len(pending_rows) != 1
            or not isinstance(pending_rows[0], dict)
            or not isinstance(pending_observation, dict)
            or pending_observation.get("same_frame") is not True
            or not isinstance(pending_observation.get("readback"), dict)):
        raise ValueError("resolved Sway lacks a paired prior pending report")
    previous = pending_rows[0]
    prior_ledger = {"schema": SWAY_FORMAL_PENDING_V1_SCHEMA,
                    "pending": pending_action["pending"], "resolved": None}
    prior_driver = {
        "episode_character_id": previous.get("episode_character_id"),
        "episode_run_id": previous.get("episode_run_id"),
        "last_checkpoint": previous,
    }
    action_id = sway_formal_pending_sidecar_request(
        prior_ledger, prior_driver, previous.get("sha256"), previous.get("size"))
    actor = pending_action["pending"]["actor_character_id"]
    target = pending_action["pending"]["target_character_id"]
    episode = previous.get("episode_run_id")
    prior_readback = pending_observation["readback"]
    fixed = applied_report.get("fixed_seed")
    readiness = applied_report.get("readiness")
    session = applied_report.get("session")
    auto_run = applied_report.get("auto_run")
    observation = applied_report.get("private_active_scheme_sway_observation")
    formal = applied_report.get("private_active_scheme_sway_formal")
    rows = applied_report.get("checkpoints")
    checkpoint = driver.get("last_checkpoint")
    prior_session = pending_report.get("session")
    if (previous.get("phase") != "private_active_scheme_sway_receipt_pending"
            or previous.get("status") != "saved"
            or type(previous.get("size")) is not int or previous["size"] <= 0
            or type(previous.get("history_index")) is not int
            or type(previous.get("date_raw")) is not int
            or not isinstance(prior_session, dict)
            or not isinstance(pending_report.get("auto_run"), dict)
            or pending_report["auto_run"].get("attempted_turns") != 0
            or pending_report["auto_run"].get("turns") != []
            or prior_readback.get("actor_character_id") != actor
            or prior_readback.get("target_character_id") != target
            or prior_readback.get("matching_sway_active") is not False
            or prior_readback.get("active_scheme_count") != 0
            or applied_report.get("status") != "private_active_scheme_sway_applied"
            or applied_report.get("ok") is not True
            or not isinstance(fixed, dict)
            or fixed.get("sha256") != previous["sha256"]
            or fixed.get("size") != previous["size"]
            or fixed.get("history_index") != previous["history_index"]
            or fixed.get("saved_date_raw") != previous["date_raw"]
            or not isinstance(session, dict)
            or type(session.get("pid")) is not int
            or session["pid"] == prior_session.get("pid")
            or not isinstance(readiness, dict)
            or readiness.get("bridge_pid") != session["pid"]
            or readiness.get("episode_character_id") != actor
            or readiness.get("episode_run_id") != episode
            or readiness.get("date_raw") != previous["date_raw"]
            or not isinstance(auto_run, dict)
            or auto_run.get("attempted_turns") != 0
            or auto_run.get("turns") != []
            or not isinstance(observation, dict)
            or observation.get("same_frame") is not True
            or not isinstance(observation.get("readback"), dict)
            or not isinstance(formal, dict)
            or not isinstance(rows, list) or len(rows) != 1
            or not isinstance(rows[0], dict)
            or not isinstance(checkpoint, dict)
            or not isinstance(applied_report.get("cleanup"), dict)
            or applied_report["cleanup"].get("ok") is not True):
        raise ValueError("resolved Sway reports do not form a cold continuation")
    readback = observation["readback"]
    saved = rows[0]
    resolved = sidecar["resolved"]
    if (formal.get("checkpoint_saved") is not True
            or {key: value for key, value in formal.items()
                if key != "checkpoint_saved"} != resolved
            or resolved.get("status") != "applied"
            or resolved.get("postcondition_verified") is not True
            or resolved.get("actor_character_id") != actor
            or resolved.get("target_character_id") != target
            or resolved.get("action_id") != action_id
            or resolved.get("pre_capture_epoch") != pending_action["pending"]["pre_capture_epoch"]
            or resolved.get("post_date_raw") != previous["date_raw"]
            or resolved.get("post_capture_epoch") != readback.get("capture_epoch")
            or resolved.get("post_native_revision") != readback.get("queried_native_revision")
            or observation.get("status") != "observed"
            or observation.get("target_character_id") != target
            or readback.get("actor_character_id") != actor
            or readback.get("target_character_id") != target
            or readback.get("date_raw") != previous["date_raw"]
            or readback.get("matching_sway_active") is not True
            or type(readback.get("active_scheme_count")) is not int
            or readback["active_scheme_count"] < 1
            or saved.get("phase") != "private_active_scheme_sway_applied"
            or saved.get("status") != "saved"
            or type(saved.get("history_index")) is not int
            or saved["history_index"] <= previous["history_index"]
            or saved.get("date_raw") != previous["date_raw"]
            or saved.get("sha256") != save_sha256
            or saved.get("size") != save_size
            or saved.get("episode_character_id") != actor
            or saved.get("episode_run_id") != episode
            or any(checkpoint.get(key) != saved.get(key) for key in (
                "sha256", "size", "history_index", "date_raw",
                "episode_character_id", "episode_run_id"))
            or driver.get("episode_character_id") != actor
            or driver.get("episode_run_id") != episode):
        raise ValueError("resolved Sway readback/checkpoint disagrees with paired state")
    return action_id, saved


def post_sway_child_pending_result_pair(
    report: dict[str, Any], sidecar: dict[str, Any],
    previous: dict[str, Any], driver: dict[str, Any], save_sha256: str | None,
) -> None:
    """Admit one linked pending result read after Sway or an earlier read."""
    fixed = report.get("fixed_seed")
    readiness = report.get("readiness")
    session = report.get("session")
    auto = report.get("auto_run")
    turns = auto.get("turns") if isinstance(auto, dict) else None
    checkpoints = report.get("checkpoints")
    turn = turns[0] if isinstance(turns, list) and len(turns) == 1 else None
    saved = checkpoints[0] if isinstance(checkpoints, list) and len(checkpoints) == 1 else None
    result = turn.get("result") if isinstance(turn, dict) else None
    before = turn.get("before") if isinstance(turn, dict) else None
    after = turn.get("after") if isinstance(turn, dict) else None
    pending = sidecar.get("pending")
    checkpoint = driver.get("last_checkpoint")
    history = driver.get("command_history")
    saved_index = saved.get("history_index") if isinstance(saved, dict) else None
    saved_row = (history[saved_index - 1]
                 if isinstance(history, list) and type(saved_index) is int
                 and 0 < saved_index <= len(history) else None)
    saved_result = saved_row.get("result") if isinstance(saved_row, dict) else None
    materialized = (saved_result.get("checkpoint")
                    if isinstance(saved_result, dict) else None)
    actor = driver.get("episode_character_id")
    episode = driver.get("episode_run_id")
    bound_red = (
        report.get("ok") is False
        and report.get("outcome") == "not_qualified"
        and isinstance(report.get("first_blocker"), dict)
        and report["first_blocker"].get("kind") == "run_bound_exhausted"
    )
    qualified_read = (
        report.get("ok") is True and report.get("outcome") == "qualified"
        and report.get("first_blocker") is None
    )
    if (report.get("kind") != "ck3_native_auto_run"
            or report.get("status") != "turn_limit"
            or report.get("completion_contract") != "bounded"
            or not (bound_red or qualified_read)
            or not isinstance(report.get("cleanup"), dict)
            or report["cleanup"].get("ok") is not True
            or not isinstance(fixed, dict) or not isinstance(readiness, dict)
            or not isinstance(session, dict) or type(session.get("pid")) is not int
            or not isinstance(auto, dict) or auto.get("attempted_turns") != 1
            or auto.get("visible_gameplay_turns") != 0
            or not isinstance(turn, dict) or not isinstance(result, dict)
            or not isinstance(before, dict) or not isinstance(after, dict)
            or not isinstance(saved, dict) or not isinstance(checkpoint, dict)
            or not isinstance(saved_row, dict)
            or saved_row.get("index") != saved_index
            or saved_row.get("command") != "save-checkpoint"
            or saved_row.get("ok") is not True
            or not isinstance(materialized, dict)
            or any(materialized.get(key) != saved.get(key) for key in (
                "sha256", "size", "history_index", "date_raw",
                "episode_character_id", "episode_run_id"))
            or not isinstance(pending, dict) or sidecar.get("resolved") is not None
            or fixed.get("sha256") != previous.get("sha256")
            or fixed.get("history_index") != previous.get("history_index")
            or fixed.get("saved_date_raw") != previous.get("date_raw")
            or readiness.get("bridge_pid") != session["pid"]
            or readiness.get("episode_character_id") != actor
            or readiness.get("episode_run_id") != episode
            or readiness.get("date_raw") != previous.get("date_raw")
            or turn.get("selected_step") != CHILD_MATRILINEAL_RESULT_STEP
            or turn.get("class") != "query" or turn.get("status") != "executed"
            or turn.get("ok") is not True
            or result.get("status") != "pending"
            or result.get("material_result") is not False
            or result.get("outbound_pending_state") != "active"
            or any(result.get(key) != pending.get(key) for key in (
                "heir_character_id", "candidate_character_id", "recipient_character_id"))
            or before.get("paused") is not True or after.get("paused") is not True
            or before.get("date_raw") != previous.get("date_raw")
            or after.get("date_raw") != previous.get("date_raw")
            or "child_matrilineal_result_checkpoint_saved" not in turn.get("evidence", [])
            or saved.get("phase") != "player_child_matrilineal_result_pending"
            or saved.get("ledger_status") != "pending"
            or saved.get("status") != "saved"
            or saved.get("turn_index") != turn.get("index")
            or type(saved.get("history_index")) is not int
            or saved["history_index"] <= previous.get("history_index", 0)
            or saved.get("date_raw") != previous.get("date_raw")
            or (save_sha256 is not None and saved.get("sha256") != save_sha256)
            or (bound_red and report["first_blocker"].get(
                "last_durable_checkpoint") != saved)
            or saved.get("episode_character_id") != actor
            or saved.get("episode_run_id") != episode
            or (save_sha256 is not None and any(
                checkpoint.get(key) != saved.get(key)
                for key in ("history_index", "date_raw", "sha256",
                            "episode_character_id", "episode_run_id")))
            or pending.get("played_character_id") != actor
            or pending.get("episode_run_id") != episode
            or (save_sha256 is not None and (
                pending.get("last_checked_bridge_pid") != session["pid"]
                or pending.get("last_checked_native_revision") != result.get("post_native_revision")
                or pending.get("last_outbound_pending_state") != result.get("outbound_pending_state")))):
        raise ValueError("post-Sway child pending read lacks its paired checkpoint")


def saved_in_progress_construction_without_sidecar(driver: dict[str, Any]) -> bool:
    """A saved material receipt needs its ledger until completion and income settle."""

    checkpoint = driver.get("last_checkpoint")
    history = driver.get("command_history")
    if not isinstance(checkpoint, dict) or not isinstance(history, list):
        return False
    checkpoint_index = checkpoint.get("history_index")
    if type(checkpoint_index) is not int:
        return False
    actor = driver.get("episode_character_id")
    episode = driver.get("episode_run_id")
    if (type(actor) is not int or not isinstance(episode, str)
            or checkpoint.get("episode_character_id") != actor
            or checkpoint.get("episode_run_id") != episode):
        return False
    latest: dict[str, dict[str, Any]] = {}
    for row in history:
        if (not isinstance(row, dict)
                or row.get("command") != CONSTRUCTION_RECEIPT_STEP
                or type(row.get("index")) is not int
                or row["index"] > checkpoint_index
                or not isinstance(row.get("result"), dict)):
            continue
        receipt = row["result"]
        request_id = receipt.get("action_request_id")
        if (isinstance(request_id, str)
                and receipt.get("status") == "applied"
                and receipt.get("postcondition_verified") is True
                and receipt.get("actor_character_id") == actor
                and receipt.get("episode_run_id") == episode):
            previous = latest.get(request_id)
            if previous is None or row["index"] > previous["index"]:
                latest[request_id] = row
    return any(
        row["result"].get("completion_status") == "in_progress"
        or (row["result"].get("completion_status") == "completed"
            and row["result"].get("observed_player_monthly_gold_income_raw") is None)
        for row in latest.values()
    )


def family_pending_sidecar_pair(
    sidecar: dict[str, Any], driver: dict[str, Any],
    manifest: dict[str, Any], save_sha256: str,
    formal_report: dict[str, Any] | list[dict[str, Any]],
) -> int:
    """Bind a saved first-heir proposal through consecutive formal checkpoints."""
    reports = formal_report if isinstance(formal_report, list) else [formal_report]
    if not reports or any(not isinstance(report, dict) for report in reports):
        raise ValueError("family sidecar lacks saved pending proposal proof")
    submit_report = reports[0]
    pending = sidecar.get("pending")
    checkpoint = driver.get("last_checkpoint")
    report_checkpoints = submit_report.get("checkpoints")
    auto_run = submit_report.get("auto_run")
    turns = auto_run.get("turns") if isinstance(auto_run, dict) else None
    session = submit_report.get("session")
    if (sidecar.get("schema") != FAMILY_PENDING_V1_SCHEMA
            or sidecar.get("resolved") is not None
            or not isinstance(pending, dict)
            or not isinstance(checkpoint, dict)
            or not isinstance(report_checkpoints, list)
            or not isinstance(turns, list)
            or not isinstance(session, dict)):
        raise ValueError("family sidecar lacks saved pending proposal proof")
    actor = episode_value(driver, manifest, "episode_character_id")
    episode = episode_value(driver, manifest, "episode_run_id")
    heir = pending.get("heir_character_id")
    candidate = pending.get("candidate_character_id")
    recipient = pending.get("recipient_character_id")
    source_date = pending.get("source_date_raw")
    latest_index = checkpoint.get("history_index")
    latest_date = checkpoint.get("date_raw")
    if (pending.get("schema") != FAMILY_ACTION_V1_SCHEMA
            or pending.get("status") != "receipt_pending"
            or pending.get("submission_state") != "receipt_pending"
            or pending.get("material_result") is not False
            or pending.get("accepted") is not True
            or pending.get("played_character_id") != actor
            or pending.get("episode_run_id") != episode
            or type(heir) is not int or heir <= 0 or heir == actor
            or type(candidate) is not int or candidate <= 0
            or type(recipient) is not int or recipient <= 0
            or type(source_date) is not int
            or pending.get("source_bridge_pid") != session.get("pid")
            or checkpoint.get("episode_character_id") != actor
            or checkpoint.get("episode_run_id") != episode
            or type(latest_index) is not int or latest_index <= 0
            or type(latest_date) is not int or latest_date < source_date
            or checkpoint.get("sha256") != save_sha256):
        raise ValueError("family pending identity disagrees with paired save")
    submitted_checkpoints = [row for row in report_checkpoints
                if isinstance(row, dict)
                and row.get("phase") == "first_heir_marriage_submitted_pending"
                and row.get("date_raw") == source_date
                and row.get("status") == "saved"
                and isinstance(row.get("sha256"), str)
                and re.fullmatch(r"[0-9a-fA-F]{64}", row["sha256"]) is not None
                and type(row.get("history_index")) is int
                and 0 < row["history_index"] <= latest_index
                and row.get("episode_character_id") == actor
                and row.get("episode_run_id") == episode
                and isinstance(row.get("pending_action"), dict)
                and row["pending_action"].get("heir_character_id") == heir
                and row["pending_action"].get("candidate_character_id") == candidate
                and row["pending_action"].get("recipient_character_id") == recipient
                and row["pending_action"].get("episode_run_id") == episode]
    submitted = [row for row in turns if isinstance(row, dict)
                 and row.get("selected_step") == FAMILY_SUBMIT_STEP]
    if len(submitted_checkpoints) != 1 or len(submitted) != 1:
        raise ValueError("family proposal is not proven by one saved formal submit")
    source = submitted_checkpoints[0]
    submit = submitted[0]
    result = submit.get("result")
    plan = submit.get("plan")
    if (type(source.get("turn_index")) is not int
            or type(submit.get("index")) is not int
            or source["turn_index"] != submit["index"]
            or not isinstance(result, dict)
            or result.get("status") != "receipt_pending"
            or result.get("accepted") is not True
            or result.get("played_character_id") != actor
            or result.get("heir_character_id") != heir
            or result.get("candidate_character_id") != candidate
            or result.get("recipient_character_id") != recipient
            or result.get("episode_run_id") != episode
            or not isinstance(plan, dict)
            or not isinstance(plan.get("family_marriage_choice"), dict)
            or plan["family_marriage_choice"].get("candidate_character_id") != candidate):
        raise ValueError("family proposal is not proven by one saved formal submit")
    previous_checkpoint = None
    previous_pid = None
    for report_number, report in enumerate(reports):
        run = report.get("auto_run")
        run_turns = run.get("turns") if isinstance(run, dict) else None
        run_session = report.get("session")
        checkpoints = report.get("checkpoints")
        if (not isinstance(run_turns, list)
                or not isinstance(run_session, dict)
                or not isinstance(checkpoints, list)):
            raise ValueError("family proof chain lacks formal run data")
        run_pid = run_session.get("pid")
        if type(run_pid) is not int or run_pid <= 0:
            raise ValueError("family proof chain lacks formal run identity")
        if report_number:
            fixed_seed = report.get("fixed_seed")
            readiness = report.get("readiness")
            if (report.get("ok") is not True
                    or run_pid == previous_pid
                    or not isinstance(fixed_seed, dict)
                    or not isinstance(readiness, dict)
                    or readiness.get("bridge_pid") != run_pid
                    or readiness.get("episode_character_id") != actor
                    or readiness.get("episode_run_id") != episode
                    or fixed_seed.get("sha256") != previous_checkpoint.get("sha256")
                    or fixed_seed.get("history_index") != previous_checkpoint.get("history_index")
                    or fixed_seed.get("saved_date_raw") != previous_checkpoint.get("date_raw")
                    or any(isinstance(row, dict)
                           and row.get("selected_step") == FAMILY_SUBMIT_STEP
                           for row in run_turns)):
                raise ValueError("family proof chain does not continue prior checkpoint")
        saved = [row for row in checkpoints if isinstance(row, dict)
                 and row.get("status") == "saved"
                 and type(row.get("history_index")) is int
                 and type(row.get("date_raw")) is int
                 and type(row.get("turn_index")) is int
                 and isinstance(row.get("sha256"), str)
                 and re.fullmatch(r"[0-9a-fA-F]{64}", row["sha256"]) is not None
                 and row.get("episode_character_id") == actor
                 and row.get("episode_run_id") == episode]
        if not saved:
            raise ValueError("family proof chain lacks paired checkpoint")
        paired = max(saved, key=lambda row: row["history_index"])
        if (sum(row["history_index"] == paired["history_index"] for row in saved) != 1
                or paired["history_index"] < source["history_index"]
                or (report_number == 0 and paired["turn_index"] < source["turn_index"])
                or (previous_checkpoint is not None and (
                    paired["history_index"] < previous_checkpoint["history_index"]
                    or paired["date_raw"] < previous_checkpoint["date_raw"]
                    or (paired["history_index"] == previous_checkpoint["history_index"]
                        and paired["sha256"] != previous_checkpoint["sha256"])))):
            raise ValueError("family proof chain has ambiguous checkpoint")
        if report_number == len(reports) - 1:
            if (paired["sha256"] != save_sha256
                    or paired["history_index"] != latest_index
                    or paired["date_raw"] != latest_date):
                raise ValueError("family proof chain does not reach paired save")
        if (report_number == 0 and paired["history_index"] == source["history_index"]
                and paired["sha256"] != source["sha256"]):
            raise ValueError("family proof chain has ambiguous checkpoint")
        if paired["history_index"] > source["history_index"]:
            later_reads = [row for row in run_turns if isinstance(row, dict)
                           and row.get("selected_step") ==
                           "query-observed-first-heir-marriage-result-v1-private"
                           and type(row.get("index")) is int
                           and (report_number != 0 or row["index"] > source["turn_index"])
                           and row["index"] <= paired["turn_index"]]
            if (not later_reads or any(
                    not isinstance(row.get("result"), dict)
                    or row["result"].get("status") not in {"pending", "accepted_pending"}
                    or row["result"].get("heir_character_id") != heir
                    or row["result"].get("candidate_character_id") != candidate
                    for row in later_reads)):
                raise ValueError("later paired save lacks pending family result query")
        previous_checkpoint = paired
        previous_pid = run_pid
    if (len(reports) > 1
            and pending.get("last_checked_bridge_pid") != previous_pid):
        raise ValueError("family proof chain disagrees with latest pending reader")
    return candidate


def family_resolved_sidecar_pair(
    sidecar: dict[str, Any], driver: dict[str, Any],
    manifest: dict[str, Any], save_sha256: str,
) -> int:
    """Admit a saved material family result without editing its old receipt."""
    resolved = sidecar.get("resolved")
    checkpoint = driver.get("last_checkpoint")
    if (sidecar.get("schema") != FAMILY_PENDING_V1_SCHEMA
            or sidecar.get("pending") is not None
            or not isinstance(resolved, dict)
            or resolved.get("status") not in {"betrothal", "marriage"}
            or resolved.get("material_result") is not True
            or not isinstance(checkpoint, dict)):
        raise ValueError("family sidecar lacks a material resolved proposal")
    actor = episode_value(driver, manifest, "episode_character_id")
    episode = episode_value(driver, manifest, "episode_run_id")
    pending = resolved.get("source_pending")
    heir = resolved.get("heir_character_id")
    candidate = resolved.get("candidate_character_id")
    if (not isinstance(pending, dict)
            or pending.get("schema") != FAMILY_ACTION_V1_SCHEMA
            or pending.get("status") != "receipt_pending"
            or pending.get("material_result") is not False
            or pending.get("played_character_id") != actor
            or pending.get("episode_run_id") != episode
            or pending.get("heir_character_id") != heir
            or pending.get("candidate_character_id") != candidate
            or resolved.get("episode_run_id") != episode
            or type(heir) is not int or heir <= 0 or heir == actor
            or type(candidate) is not int or candidate <= 0
            or checkpoint.get("episode_character_id") != actor
            or checkpoint.get("episode_run_id") != episode
            or checkpoint.get("sha256") != save_sha256
            or type(checkpoint.get("history_index")) is not int
            or checkpoint["history_index"] <= 0):
        raise ValueError("resolved family sidecar disagrees with paired checkpoint")
    return candidate


def child_matrilineal_pending_sidecar_pair(
    sidecar: dict[str, Any], driver: dict[str, Any],
    manifest: dict[str, Any], save_sha256: str,
    attempt: dict[str, Any] | list[dict[str, Any]],
    *, sway_continuation: dict[str, Any] | None = None,
    sway_sidecar: dict[str, Any] | None = None,
    sway_applied_continuation: dict[str, Any] | None = None,
    post_sway_result: dict[str, Any] | None = None,
    post_sway_followups: list[dict[str, Any]] | None = None,
) -> int:
    """Pair a child proposal through consecutive saved formal pending reads."""
    reports = attempt if isinstance(attempt, list) else [attempt]
    if not reports or any(not isinstance(row, dict) for row in reports):
        raise ValueError("child proposal lacks a saved formal pending proof")
    submit_attempt = reports[0]
    pending = sidecar.get("pending")
    checkpoint = driver.get("last_checkpoint")
    formal = submit_attempt.get("formal_auto_run")
    turns = formal.get("auto_run", {}).get("turns") if isinstance(formal, dict) else None
    checkpoints = formal.get("checkpoints") if isinstance(formal, dict) else None
    session = formal.get("session") if isinstance(formal, dict) else None
    submit_ledger = submit_attempt.get("child_ledger")
    submit_pending = submit_ledger.get("pending") if isinstance(submit_ledger, dict) else None
    if (sidecar.get("schema") != CHILD_MATRILINEAL_SCHEMA
            or sidecar.get("resolved") is not None or not isinstance(pending, dict)
            or not isinstance(checkpoint, dict)
            or submit_attempt.get("schema") != CHILD_MATRILINEAL_PROOF_SCHEMA
            or submit_attempt.get("status") != "receipt_pending_checkpointed"
            or submit_attempt.get("ok") is not True
            or not isinstance(submit_pending, dict)
            or (len(reports) == 1 and submit_ledger != sidecar)
            or not isinstance(formal, dict)
            or formal.get("status") != "turn_limit"
            or not isinstance(formal.get("cleanup"), dict)
            or formal["cleanup"].get("ok") is not True
            or not isinstance(turns, list) or len(turns) != 1
            or not isinstance(turns[0], dict)
            or not isinstance(checkpoints, list)
            or not isinstance(session, dict)):
        raise ValueError("child proposal lacks a saved formal pending proof")
    actor = episode_value(driver, manifest, "episode_character_id")
    episode = episode_value(driver, manifest, "episode_run_id")
    heir = pending.get("heir_character_id")
    candidate = pending.get("candidate_character_id")
    recipient = pending.get("recipient_character_id")
    date_raw = pending.get("source_date_raw")
    index = checkpoint.get("history_index")
    if (pending.get("schema") != CHILD_MATRILINEAL_SCHEMA
            or pending.get("status") != "receipt_pending"
            or pending.get("submission_state") != "receipt_pending"
            or pending.get("material_result") is not False
            or pending.get("accepted") is not True
            or pending.get("matrilineal_option_selected") is not True
            or pending.get("played_character_id") != actor
            or pending.get("episode_run_id") != episode
            or pending.get("source_bridge_pid") != session.get("pid")
            or any(submit_pending.get(key) != pending.get(key) for key in (
                "schema", "status", "submission_state", "material_result",
                "accepted", "matrilineal_option_selected", "played_character_id",
                "heir_character_id", "candidate_character_id", "recipient_character_id",
                "episode_run_id", "source_bridge_pid", "source_date_raw"))
            or type(heir) is not int or heir <= 0 or heir == actor
            or type(candidate) is not int or candidate <= 0
            or type(recipient) is not int or recipient <= 0
            or type(date_raw) is not int
            or checkpoint.get("episode_character_id") != actor
            or checkpoint.get("episode_run_id") != episode
            or type(checkpoint.get("date_raw")) is not int
            or checkpoint["date_raw"] < date_raw
            or checkpoint.get("sha256") != save_sha256
            or type(index) is not int or index <= 0):
        raise ValueError("child pending identity disagrees with paired save")
    turn = turns[0]
    result = turn.get("result") if isinstance(turn, dict) else None
    matching = [row for row in checkpoints if isinstance(row, dict)
                and row.get("phase") == "player_child_matrilineal_submitted_pending"
                and row.get("status") == "saved"
                and type(row.get("history_index")) is int
                and 0 < row["history_index"] <= index
                and row.get("date_raw") == date_raw
                and isinstance(row.get("sha256"), str)
                and row.get("episode_character_id") == actor
                and row.get("episode_run_id") == episode]
    if (turn.get("selected_step") != CHILD_MATRILINEAL_SUBMIT_STEP
            or turn.get("status") != "executed"
            or not isinstance(result, dict)
            or result.get("step") != CHILD_MATRILINEAL_SUBMIT_STEP
            or result.get("status") != "receipt_pending"
            or result.get("accepted") is not True
            or result.get("material_result") is not False
            or any(result.get(key) != value for key, value in (
                ("played_character_id", actor), ("heir_character_id", heir),
                ("candidate_character_id", candidate),
                ("recipient_character_id", recipient), ("episode_run_id", episode)))
            or len(matching) != 1
            or matching[0].get("turn_index") != turn.get("index")
            or not isinstance(matching[0].get("pending_action"), dict)
            or matching[0]["pending_action"].get("matrilineal_option_selected") is not True
            or any(matching[0]["pending_action"].get(key) != value for key, value in (
                ("heir_character_id", heir), ("candidate_character_id", candidate),
                ("recipient_character_id", recipient), ("episode_run_id", episode)))):
        raise ValueError("child pending proposal is not paired with its saved submit")
    previous = matching[0]
    previous_pid = session["pid"]
    for continuation in reports[1:]:
        later = continuation.get("formal_auto_run")
        later_turns = later.get("auto_run", {}).get("turns") if isinstance(later, dict) else None
        later_checkpoints = later.get("checkpoints") if isinstance(later, dict) else None
        later_session = later.get("session") if isinstance(later, dict) else None
        fixed_seed = later.get("fixed_seed") if isinstance(later, dict) else None
        readiness = later.get("readiness") if isinstance(later, dict) else None
        if (continuation.get("schema") != CHILD_MATRILINEAL_COLD_PROOF_SCHEMA
                or not isinstance(later, dict) or later.get("ok") is not True
                or not isinstance(later.get("cleanup"), dict)
                or later["cleanup"].get("ok") is not True
                or not isinstance(later_turns, list)
                or not isinstance(later_checkpoints, list)
                or not isinstance(later_session, dict)
                or not isinstance(fixed_seed, dict)
                or not isinstance(readiness, dict)
                or type(later_session.get("pid")) is not int
                or later_session["pid"] == previous_pid
                or readiness.get("bridge_pid") != later_session["pid"]
                or readiness.get("episode_character_id") != actor
                or readiness.get("episode_run_id") != episode
                or fixed_seed.get("sha256") != previous["sha256"]
                or fixed_seed.get("history_index") != previous["history_index"]
                or fixed_seed.get("saved_date_raw") != previous["date_raw"]
                or any(isinstance(row, dict)
                       and row.get("selected_step") == CHILD_MATRILINEAL_SUBMIT_STEP
                       for row in later_turns)):
            raise ValueError("child proof chain does not continue prior checkpoint")
        reads = [row for row in later_turns if isinstance(row, dict)
                 and row.get("selected_step") == CHILD_MATRILINEAL_RESULT_STEP
                 and row.get("status") == "executed"
                 and isinstance(row.get("result"), dict)]
        if (not reads or any(
                row["result"].get("status") != "pending"
                or row["result"].get("accepted") is not True
                or row["result"].get("material_result") is not False
                or row["result"].get("heir_character_id") != heir
                or row["result"].get("candidate_character_id") != candidate
                or row["result"].get("recipient_character_id") != recipient
                for row in reads)):
            raise ValueError("child proof chain lacks matching pending result read")
        saved = [row for row in later_checkpoints if isinstance(row, dict)
                 and row.get("status") == "saved"
                 and type(row.get("history_index")) is int
                 and type(row.get("date_raw")) is int
                 and isinstance(row.get("sha256"), str)
                 and row.get("episode_character_id") == actor
                 and row.get("episode_run_id") == episode]
        if not saved:
            raise ValueError("child proof chain lacks saved checkpoint")
        paired = max(saved, key=lambda row: row["history_index"])
        if (sum(row["history_index"] == paired["history_index"] for row in saved) != 1
                or paired["history_index"] <= previous["history_index"]
                or paired["date_raw"] < previous["date_raw"]):
            raise ValueError("child proof chain has ambiguous checkpoint")
        later_ledger = continuation.get("child_ledger")
        last_read = reads[-1]["result"]
        if (not isinstance(later_ledger, dict)
                or later_ledger.get("schema") != CHILD_MATRILINEAL_SCHEMA
                or not isinstance(later_ledger.get("pending"), dict)
                or later_ledger.get("resolved") is not None
                or later_ledger["pending"].get("last_checked_bridge_pid") != later_session["pid"]
                or type(last_read.get("post_native_revision")) is not int
                or later_ledger["pending"].get("last_checked_native_revision") !=
                   last_read["post_native_revision"]
                or later_ledger["pending"].get("last_outbound_pending_state") !=
                   last_read.get("outbound_pending_state")
                or any(later_ledger["pending"].get(key) != pending.get(key)
                       for key in ("played_character_id", "heir_character_id",
                                   "candidate_character_id", "recipient_character_id",
                                   "episode_run_id", "source_bridge_pid", "source_date_raw",
                                   "matrilineal_option_selected"))):
            raise ValueError("child proof chain disagrees with pending ledger")
        previous = paired
        previous_pid = later_session["pid"]
    if sway_applied_continuation is not None and sway_continuation is None:
        raise ValueError("applied Sway continuation needs prior pending report")
    if sway_continuation is not None:
        sway_run = sway_continuation
        sway_action = sway_run.get("private_active_scheme_sway_formal")
        sway_fixed = sway_run.get("fixed_seed")
        sway_readiness = sway_run.get("readiness")
        sway_session = sway_run.get("session")
        sway_auto = sway_run.get("auto_run")
        sway_checkpoints = sway_run.get("checkpoints")
        sway_cleanup = sway_run.get("cleanup")
        sway_blocker = sway_run.get("first_blocker")
        expected_pending = (sway_sidecar.get("pending")
                            if isinstance(sway_sidecar, dict)
                            and sway_applied_continuation is None
                            else sway_action.get("pending")
                            if isinstance(sway_action, dict) else None)
        expected_interim_hash = (
            sway_applied_continuation.get("fixed_seed", {}).get("sha256")
            if isinstance(sway_applied_continuation, dict) else save_sha256)
        expected_interim_size = (
            sway_applied_continuation.get("fixed_seed", {}).get("size")
            if isinstance(sway_applied_continuation, dict)
            else checkpoint.get("size"))
        if (not isinstance(sway_sidecar, dict)
                or sway_sidecar.get("schema") != SWAY_FORMAL_PENDING_V1_SCHEMA
                or (sway_applied_continuation is None and (
                    sway_sidecar.get("resolved") is not None
                    or not isinstance(sway_sidecar.get("pending"), dict)))
                or not isinstance(expected_pending, dict)
                or sway_run.get("kind") != "ck3_native_auto_run"
                or sway_run.get("mode") != "native-headless"
                or sway_run.get("status") != "private_active_scheme_sway_receipt_pending"
                or sway_run.get("ok") is not False
                or not isinstance(sway_fixed, dict)
                or sway_fixed.get("sha256") != previous["sha256"]
                or sway_fixed.get("history_index") != previous["history_index"]
                or sway_fixed.get("saved_date_raw") != previous["date_raw"]
                or not isinstance(sway_session, dict)
                or type(sway_session.get("pid")) is not int
                or sway_session["pid"] == previous_pid
                or not isinstance(sway_readiness, dict)
                or sway_readiness.get("bridge_pid") != sway_session["pid"]
                or sway_readiness.get("episode_character_id") != actor
                or sway_readiness.get("episode_run_id") != episode
                or sway_readiness.get("date_raw") != previous["date_raw"]
                or not isinstance(sway_auto, dict)
                or sway_auto.get("attempted_turns") != 0
                or sway_auto.get("turns") != []
                or not isinstance(sway_action, dict)
                or sway_action.get("status") != "receipt_pending"
                or sway_action.get("pending") != expected_pending
                or sway_action.get("checkpoint_saved") is not True
                or sway_action.get("postcondition_verified") is not False
                or not isinstance(sway_checkpoints, list)
                or len(sway_checkpoints) != 1
                or not isinstance(sway_checkpoints[0], dict)
                or not isinstance(sway_cleanup, dict)
                or sway_cleanup.get("ok") is not True
                or not isinstance(sway_blocker, dict)
                or sway_blocker.get("last_durable_checkpoint") != sway_checkpoints[0]
                or (post_sway_result is None
                    and reports[-1].get("child_ledger") != sidecar)):
            raise ValueError("Sway continuation does not preserve child pending chain")
        saved = sway_checkpoints[0]
        if (saved.get("phase") != "private_active_scheme_sway_receipt_pending"
                or saved.get("status") != "saved"
                or type(saved.get("history_index")) is not int
                or saved["history_index"] <= previous["history_index"]
                or saved.get("date_raw") != previous["date_raw"]
                or saved.get("sha256") != expected_interim_hash
                or saved.get("episode_character_id") != actor
                or saved.get("episode_run_id") != episode
                or saved.get("size") != expected_interim_size):
            raise ValueError("Sway continuation does not reach paired checkpoint")
        previous = saved
    if sway_applied_continuation is not None:
        applied_saved = sway_applied_continuation.get("checkpoints", [None])[0]
        if post_sway_result is not None and not isinstance(applied_saved, dict):
            raise ValueError("post-Sway result lacks prior applied checkpoint")
        applied_driver = (
            {**driver, "last_checkpoint": applied_saved}
            if post_sway_result is not None else driver
        )
        _, previous = sway_formal_resolved_sidecar_pair(
            sway_sidecar, applied_driver,
            applied_saved["sha256"] if post_sway_result is not None else save_sha256,
            applied_saved["size"] if post_sway_result is not None else checkpoint.get("size"),
            sway_continuation, sway_applied_continuation)
    if post_sway_result is not None:
        if sway_applied_continuation is None:
            raise ValueError("post-Sway child result needs resolved Sway proof")
        for result_index, result_report in enumerate(
                [post_sway_result, *(post_sway_followups or [])]):
            final = result_index == len(post_sway_followups or [])
            post_sway_child_pending_result_pair(
                result_report, sidecar, previous, driver,
                save_sha256 if final else None)
            previous = result_report["checkpoints"][0]
    elif post_sway_followups:
        raise ValueError("child result followups need the first post-Sway result")
    if (previous["history_index"] != index
            or previous["date_raw"] != checkpoint["date_raw"]
            or previous["sha256"] != save_sha256
            or (post_sway_result is None
                and reports[-1].get("child_ledger") != sidecar)):
        raise ValueError("child proof chain does not reach paired save and ledger")
    return candidate


def run_logged(
    command: list[str], stdout_path: Path, stderr_path: Path,
    *, on_started: Callable[[int], None] | None = None,
) -> int:
    with stdout_path.open("w", encoding="utf-8", newline="") as stdout_stream:
        with stderr_path.open("w", encoding="utf-8", newline="") as stderr_stream:
            environment = {**os.environ, "PYTHONIOENCODING": "utf-8"}
            if on_started is None:
                return subprocess.run(
                    command, stdout=stdout_stream, stderr=stderr_stream,
                    check=False, env=environment,
                ).returncode
            process = subprocess.Popen(
                command, stdout=stdout_stream, stderr=stderr_stream,
                env=environment,
            )
            try:
                on_started(process.pid)
                return process.wait()
            except BaseException:
                if process.poll() is None:
                    process.terminate()
                    process.wait()
                raise


def private_faction_round_id(value: str) -> str:
    if re.fullmatch(r"R[1-9][0-9]*", value) is None:
        raise argparse.ArgumentTypeError(
            "private faction round ID must be R followed by a positive integer"
        )
    return value


def private_timeline_query_round_id(value: str) -> str:
    if re.fullmatch(r"R[1-9][0-9]*", value) is None:
        raise argparse.ArgumentTypeError(
            "private timeline query round ID must be R followed by a positive integer"
        )
    return value


def private_family_alliance_round_id(value: str) -> str:
    """Accept the exact padded suffix emitted by ck3_live_run_id.py."""
    if (re.fullmatch(r"R[0-9]{4,}", value) is None
            or int(value[1:]) <= 0
            or value != f"R{int(value[1:]):04d}"):
        raise argparse.ArgumentTypeError(
            "family alliance round ID must match the allocated R number"
        )
    return value


def private_timeline_action_round_id(value: str) -> str:
    if re.fullmatch(r"R[1-9][0-9]*", value) is None:
        raise argparse.ArgumentTypeError(
            "private timeline action round ID must be R followed by a positive integer"
        )
    return value


def frozen_source_identity(manifest: dict[str, Any]) -> dict[str, Any]:
    source_repo = manifest_path(manifest["source_repo"], "source_repo")
    expected_commit = manifest.get("source_commit")
    if not isinstance(expected_commit, str) or re.fullmatch(
        r"[0-9a-fA-F]{40}", expected_commit
    ) is None:
        raise ValueError("manifest field 'source_commit' must be a 40-character SHA")
    actual_commit = subprocess.check_output(
        ["git", "-C", str(source_repo), "rev-parse", "HEAD"], text=True
    ).strip()
    if actual_commit.casefold() != expected_commit.casefold():
        raise ValueError(
            f"frozen source commit mismatch: {actual_commit} != {expected_commit}"
        )
    dirty = subprocess.check_output(
        ["git", "-C", str(source_repo), "status", "--porcelain"], text=True
    ).strip()
    if dirty:
        raise ValueError("frozen source repository is dirty")
    agent = source_repo / "ck3_autonomous_player" / "agent.py"
    cli = source_repo / "ck3_autonomous_player" / "src" / "xar_autoplayer" / "cli.py"
    operator = source_repo / "tools" / "g2_preview_operator.py"
    for path in (agent, cli, operator):
        if not path.is_file():
            raise FileNotFoundError(path)
    return {
        "repo": str(source_repo),
        "commit": actual_commit,
        "agent_entry": str(agent),
        "agent_entry_sha256": sha256(agent),
        "agent_cli_sha256": sha256(cli),
        "operator_sha256": sha256(operator),
    }


def native_auto_run_command(
    common: list[str],
    *,
    turns: int,
    timeout: int,
    readiness_timeout: int,
    private_faction_round_id_value: str | None,
    private_lifestyle_formal_trial: bool = False,
    private_construction_formal_trial: bool = False,
    private_family_marriage_formal_trial: bool = False,
    private_m5_joint_collector: bool = False,
    private_prisoner_collection_observation: bool = False,
    private_active_scheme_sway_target: int | None = None,
    private_child_matrilineal_pending_read: tuple[int, int] | None = None,
    private_child_matrilineal_pending_recovery: tuple[int, int] | None = None,
    private_active_scheme_sway_formal_trial: bool = False,
    private_realm_law_paused_query: bool = False,
    private_activity_planner_diag_query: bool = False,
    private_activity_feast_planner_open: bool = False,
    private_activity_feast_stage1_option_read: bool = False,
    private_activity_cost_slot12_raw_read: bool = False,
    private_activity_feast_stage1_confirm: bool = False,
    private_activity_feast_stage2_gate_read: bool = False,
    private_activity_feast_stage2_location_provinces: tuple[int, ...] | None = None,
    require_initial_lifestyle_focus_before_date_advance: bool = False,
    succession_lifecycle: str = ROGUE_ONE_LIFE,
    ordinary_campaign_no_pact: bool = False,
    exact_war_move_stop_contract: Path | None = None,
    exact_war_move_stop_sha256: str | None = None,
) -> list[str]:
    command = [
        *common,
        "native-auto-run",
        "--turns",
        str(turns),
        "--timeout",
        str(timeout),
        "--readiness-timeout",
        str(readiness_timeout),
        "--cold-start-checkpoint",
        "--succession-lifecycle",
        succession_lifecycle,
    ]
    if ordinary_campaign_no_pact:
        command.append("--ordinary-campaign-no-pact")
    if exact_war_move_stop_contract is not None:
        if exact_war_move_stop_sha256 is None:
            raise ValueError("exact war move stop contract requires SHA-256")
        command.extend([
            "--exact-war-move-stop-contract", str(exact_war_move_stop_contract),
            "--exact-war-move-stop-sha256", exact_war_move_stop_sha256,
        ])
    if private_lifestyle_formal_trial:
        command.append("--allow-private-lifestyle-formal-trial")
    if private_construction_formal_trial:
        command.append("--allow-private-construction-formal-trial")
    if private_family_marriage_formal_trial:
        command.append("--allow-private-family-marriage-formal-trial")
    if private_m5_joint_collector:
        command.append("--allow-private-m5-joint-collector")
    if private_prisoner_collection_observation:
        command.append("--allow-private-prisoner-collection-observation")
    if private_active_scheme_sway_target is not None:
        command.extend([
            "--private-active-scheme-sway-target",
            str(private_active_scheme_sway_target),
        ])
    if private_child_matrilineal_pending_read is not None:
        command.extend([
            "--private-child-matrilineal-pending-read",
            *(str(value) for value in private_child_matrilineal_pending_read),
        ])
    if private_child_matrilineal_pending_recovery is not None:
        command.extend([
            "--private-child-matrilineal-pending-recovery",
            *(str(value) for value in private_child_matrilineal_pending_recovery),
        ])
    if private_active_scheme_sway_formal_trial:
        command.append("--allow-private-active-scheme-sway-formal-trial")
    if private_realm_law_paused_query:
        command.append("--private-realm-law-paused-query")
    if private_activity_planner_diag_query:
        command.append("--private-activity-planner-diag-query")
    if private_activity_feast_planner_open:
        command.append("--private-activity-feast-planner-open")
    if private_activity_feast_stage1_option_read:
        command.append("--private-activity-feast-stage1-option-read")
    if private_activity_feast_stage1_confirm:
        command.append("--private-activity-feast-stage1-confirm")
    if private_activity_feast_stage2_gate_read:
        command.append("--private-activity-feast-stage2-gate-read")
    if private_activity_feast_stage2_location_provinces is not None:
        for province_id in private_activity_feast_stage2_location_provinces:
            command.extend([
                "--private-activity-feast-stage2-location-province",
                str(province_id),
            ])
    if private_activity_cost_slot12_raw_read:
        command.append("--private-activity-cost-slot12-raw-read")
    if require_initial_lifestyle_focus_before_date_advance:
        command.append("--require-initial-lifestyle-focus-before-date-advance")
    if private_faction_round_id_value is not None:
        command.extend([
            "--allow-private-faction-gift-formal-trial",
            "--private-faction-round-id",
            private_faction_round_id_value,
        ])
    return command


def timeline_blocker_query_command(
    common: list[str],
    *,
    timeout: int,
    readiness_timeout: int,
    private_timeline_query_round_id_value: str,
) -> list[str]:
    return [
        *common,
        "native-query-current-timeline-blocker-context-v1",
        "--timeout",
        str(timeout),
        "--readiness-timeout",
        str(readiness_timeout),
        "--cold-start-checkpoint",
        "--private-timeline-query-round-id",
        private_timeline_query_round_id_value,
    ]


def family_alliance_result_query_command(
    common: list[str], *, timeout: int, readiness_timeout: int,
    ownership_round_id: str, proposal_report: Path,
    proposal_report_sha256: str, recipient_character_id: int,
) -> list[str]:
    return [
        *common, "native-query-first-heir-marriage-alliance-result-v1",
        "--timeout", str(timeout),
        "--readiness-timeout", str(readiness_timeout),
        "--cold-start-checkpoint",
        "--ownership-round-id", ownership_round_id,
        "--proposal-report", str(proposal_report.resolve()),
        "--proposal-report-sha256", proposal_report_sha256,
        "--recipient-character-id", str(recipient_character_id),
    ]


def death_succession_modal_action_command(
    common: list[str],
    *,
    timeout: int,
    readiness_timeout: int,
    private_timeline_action_round_id_value: str,
    expected_played_character_id: int,
    expected_episode_run_id: str,
    expected_date_raw: int,
) -> list[str]:
    return [
        *common,
        "native-continue-death-succession-modal-v1",
        "--timeout",
        str(timeout),
        "--readiness-timeout",
        str(readiness_timeout),
        "--cold-start-checkpoint",
        "--private-timeline-action-round-id",
        private_timeline_action_round_id_value,
        "--expected-played-character-id",
        str(expected_played_character_id),
        "--expected-episode-run-id",
        expected_episode_run_id,
        "--expected-date-raw",
        str(expected_date_raw),
    ]


def command_verify_zip(args: argparse.Namespace) -> int:
    archive = args.zip.resolve()
    actual = sha256(archive)
    expected = args.expected_sha256.casefold()
    if actual != expected:
        raise ValueError(f"preview ZIP hash mismatch: expected {expected}, got {actual}")
    print(json.dumps({"ok": True, "zip": str(archive), "bytes": archive.stat().st_size, "sha256": actual}))
    return 0


def command_prepare_state(args: argparse.Namespace) -> int:
    manifest_file = args.manifest.resolve()
    manifest = load_manifest(manifest_file)
    lifecycle = lifecycle_contract(manifest)
    state_dir = manifest_path(manifest["state_dir"], "state_dir")
    sample_dir = args.sample_dir.resolve()
    save_source = sample_dir / "xar_checkpoint.ck3"
    driver_source = sample_dir / "driver-state.json"
    explicit_sidecar = getattr(args, "construction_sidecar", None)
    pending_source = (explicit_sidecar.resolve() if explicit_sidecar is not None
                      else sample_dir / "construction-formal-pending-v1.json")
    family_sidecar_arg = getattr(args, "family_sidecar", None)
    family_report_arg = getattr(args, "family_proof_report", None)
    family_report_sources = (
        [family_report_arg] if isinstance(family_report_arg, Path)
        else list(family_report_arg or [])
    )
    if family_sidecar_arg is None and family_report_sources:
        raise ValueError("family proof report requires a family sidecar")
    family_source = family_sidecar_arg.resolve() if family_sidecar_arg else None
    family_report_sources = [path.resolve() for path in family_report_sources]
    child_sidecar_arg = getattr(args, "child_matrilineal_sidecar", None)
    child_proof_arg = getattr(args, "child_matrilineal_proof_report", None)
    child_proof_sources = (
        [child_proof_arg] if isinstance(child_proof_arg, Path)
        else list(child_proof_arg or [])
    )
    if (child_sidecar_arg is None) != (not child_proof_sources):
        raise ValueError("child pending sidecar requires its formal proof report")
    child_source = child_sidecar_arg.resolve() if child_sidecar_arg else None
    child_proof_sources = [path.resolve() for path in child_proof_sources]
    child_continuation_arg = getattr(args, "child_matrilineal_continuation_report", None)
    if child_continuation_arg is not None and child_source is None:
        raise ValueError("child continuation requires pending sidecar and proof chain")
    child_continuation_source = (child_continuation_arg.resolve()
                                 if child_continuation_arg is not None else None)
    faction_sidecar_arg = getattr(args, "faction_gift_sidecar", None)
    faction_source = (faction_sidecar_arg.resolve() if faction_sidecar_arg is not None
                      else sample_dir / "faction-gift-pending-v1.json")
    sway_sidecar_arg = getattr(args, "sway_formal_sidecar", None)
    sway_source = (sway_sidecar_arg.resolve() if sway_sidecar_arg is not None
                   else sample_dir / SWAY_FORMAL_PENDING_FILENAME)
    sway_applied_arg = getattr(args, "sway_formal_applied_report", None)
    if sway_applied_arg is not None and child_continuation_source is None:
        raise ValueError("resolved Sway needs its prior pending continuation report")
    sway_applied_source = (sway_applied_arg.resolve()
                           if sway_applied_arg is not None else None)
    post_sway_arg = getattr(args, "child_matrilineal_post_sway_result_report", None)
    if post_sway_arg is not None and (child_source is None or sway_applied_source is None):
        raise ValueError("post-Sway child result needs child and resolved Sway proofs")
    post_sway_source = post_sway_arg.resolve() if post_sway_arg else None
    followup_sources = [path.resolve() for path in (
        getattr(args, "child_matrilineal_followup_result_report", None) or [])]
    if followup_sources and post_sway_source is None:
        raise ValueError("child result followups need the first post-Sway result")
    save_target = state_dir / "profile" / "save games" / "xar_checkpoint.ck3"
    driver_target = state_dir / "native-session" / "driver-state.json"
    pending_target = state_dir / "construction-formal-pending-v1.json"
    family_target = state_dir / "first-heir-marriage-formal-v1.json"
    child_target = state_dir / "player-child-matrilineal-formal-v1.json"
    faction_target = state_dir / "native-session" / "faction-gift-pending-v1.json"
    sway_target = state_dir / SWAY_FORMAL_PENDING_FILENAME
    for path in (save_source, driver_source):
        if not path.is_file():
            raise FileNotFoundError(path)
    for path in (save_target, driver_target):
        if path.exists():
            raise FileExistsError(f"refusing to overwrite prepared state: {path}")
    pending_request_id = None
    pending_source_sha256 = None
    pending_record = None
    driver_source_record = read_json(driver_source)
    if explicit_sidecar is not None and not pending_source.is_file():
        raise FileNotFoundError(pending_source)
    if pending_source.exists():
        if not pending_source.is_file():
            raise FileNotFoundError(pending_source)
        if pending_target.exists():
            raise FileExistsError(f"refusing to overwrite prepared state: {pending_target}")
        pending_record = read_json(pending_source)
        pending_request_id = construction_pending_sidecar_request(
            pending_record, driver_source_record, manifest)
        pending_source_sha256 = sha256(pending_source)
    elif saved_in_progress_construction_without_sidecar(driver_source_record):
        raise ValueError(
            "saved unresolved construction receipt requires --construction-sidecar "
            "or construction-formal-pending-v1.json in sample-dir"
        )
    family_candidate = None
    family_source_sha256 = None
    family_report_sha256 = None
    family_kind = None
    family_record = None
    formal_report = None
    if family_source is not None:
        if not family_source.is_file():
            raise FileNotFoundError(family_source)
        if family_target.exists():
            raise FileExistsError(f"refusing to overwrite prepared state: {family_target}")
        family_record = read_json(family_source)
        if family_record.get("pending") is not None:
            if not family_report_sources or any(
                    not path.is_file() for path in family_report_sources):
                raise ValueError("family pending recovery needs formal proof report")
            formal_report = [read_json(path) for path in family_report_sources]
            family_candidate = family_pending_sidecar_pair(
                family_record, driver_source_record, manifest,
                sha256(save_source), formal_report)
            family_kind = "pending"
            family_report_sha256 = [sha256(path) for path in family_report_sources]
        else:
            if family_report_sources:
                raise ValueError("resolved family sidecar does not take a proof report")
            family_candidate = family_resolved_sidecar_pair(
                family_record, driver_source_record, manifest,
                sha256(save_source))
            family_kind = "resolved"
        family_source_sha256 = sha256(family_source)
    child_continuation = None
    child_continuation_sha256 = None
    if child_continuation_source is not None:
        if not child_continuation_source.is_file():
            raise FileNotFoundError(child_continuation_source)
        child_continuation = read_json(child_continuation_source)
        child_continuation_sha256 = sha256(child_continuation_source)
    sway_applied = None
    sway_applied_sha256 = None
    if sway_applied_source is not None:
        if not sway_applied_source.is_file():
            raise FileNotFoundError(sway_applied_source)
        sway_applied = read_json(sway_applied_source)
        sway_applied_sha256 = sha256(sway_applied_source)
    post_sway_result = None
    post_sway_sha256 = None
    if post_sway_source is not None:
        if not post_sway_source.is_file():
            raise FileNotFoundError(post_sway_source)
        post_sway_result = read_json(post_sway_source)
        post_sway_sha256 = sha256(post_sway_source)
    if any(not path.is_file() for path in followup_sources):
        raise FileNotFoundError("child result followup proof report missing")
    followup_results = [read_json(path) for path in followup_sources]
    followup_sha256 = [sha256(path) for path in followup_sources]
    sway_action_id = None
    sway_ledger_status = None
    sway_source_sha256 = None
    sway_record = None
    if sway_sidecar_arg is not None and not sway_source.is_file():
        raise FileNotFoundError(sway_source)
    if sway_source.exists():
        if not sway_source.is_file():
            raise FileNotFoundError(sway_source)
        if sway_target.exists():
            raise FileExistsError(f"refusing to overwrite prepared state: {sway_target}")
        sway_record = read_json(sway_source)
        if sway_record.get("pending") is not None:
            if sway_applied is not None:
                raise ValueError("pending Sway ledger cannot use applied report")
            sway_action_id = sway_formal_pending_sidecar_request(
                sway_record, driver_source_record,
                sha256(save_source), save_source.stat().st_size)
            sway_ledger_status = "pending"
        else:
            if child_continuation is None or sway_applied is None:
                raise ValueError("resolved Sway needs pending and applied reports")
            applied_saved = (sway_applied.get("checkpoints", [None])[0]
                             if post_sway_result is not None else None)
            if post_sway_result is not None and not isinstance(applied_saved, dict):
                raise ValueError("post-Sway child result lacks applied checkpoint")
            sway_action_id, _ = sway_formal_resolved_sidecar_pair(
                sway_record,
                {**driver_source_record, "last_checkpoint": applied_saved}
                if post_sway_result is not None else driver_source_record,
                applied_saved["sha256"] if post_sway_result is not None
                else sha256(save_source),
                applied_saved["size"] if post_sway_result is not None
                else save_source.stat().st_size,
                child_continuation, sway_applied)
            sway_ledger_status = "applied"
        sway_source_sha256 = sha256(sway_source)
    child_candidate = None
    child_source_sha256 = None
    child_proof_sha256 = None
    child_record = None
    child_proof = None
    if child_source is not None and child_proof_sources:
        if not child_source.is_file() or any(
                not path.is_file() for path in child_proof_sources):
            raise FileNotFoundError("child pending sidecar or formal proof report missing")
        if child_target.exists():
            raise FileExistsError(f"refusing to overwrite prepared state: {child_target}")
        child_record = read_json(child_source)
        child_proof = [read_json(path) for path in child_proof_sources]
        child_candidate = child_matrilineal_pending_sidecar_pair(
            child_record, driver_source_record, manifest,
            sha256(save_source), child_proof,
            sway_continuation=child_continuation, sway_sidecar=sway_record,
            sway_applied_continuation=sway_applied,
            post_sway_result=post_sway_result,
            post_sway_followups=followup_results)
        child_source_sha256 = sha256(child_source)
        child_proof_sha256 = [sha256(path) for path in child_proof_sources]
    faction_request_id = None
    faction_source_sha256 = None
    faction_record = None
    if faction_sidecar_arg is not None and not faction_source.is_file():
        raise FileNotFoundError(faction_source)
    if faction_source.exists():
        if not faction_source.is_file():
            raise FileNotFoundError(faction_source)
        if faction_target.exists():
            raise FileExistsError(f"refusing to overwrite prepared state: {faction_target}")
        faction_record = read_json(faction_source)
        resolved = faction_record.get("resolved_request_outcomes")
        resolved_only = (
            set(faction_record) == {
                "schema", "format_version", "pending", "resolved_request_outcomes"
            }
            and faction_record.get("schema") == FACTION_GIFT_PENDING_V1_SCHEMA
            and faction_record.get("format_version") == 1
            and faction_record["pending"] is None
            and isinstance(resolved, dict)
            and all(isinstance(key, str) and key
                    and value in {"applied", "unchanged"}
                    for key, value in resolved.items())
        )
        if resolved_only:
            if faction_sidecar_arg is not None:
                raise ValueError("explicit faction gift sidecar has no unresolved action")
        else:
            faction_request_id = faction_gift_pending_sidecar_request(
                faction_record, driver_source_record, manifest, sha256(save_source)
            )
            faction_source_sha256 = sha256(faction_source)
    rebind_receipt = state_dir / "ordinary-seed-rebind-v1.json"
    if lifecycle == {**ORDINARY_LIFECYCLE_CONTRACT, "source": "manifest"}:
        if rebind_receipt.exists():
            raise FileExistsError(
                f"refusing to overwrite ordinary rebind receipt: {rebind_receipt}"
            )
    common = agent_command(manifest)
    profile_rule = ["--xar-enabled", str(lifecycle["xar_enabled"])]
    if "display_mode" in manifest:
        profile_rule.extend(["--display-mode", display_mode_contract(manifest)])
    if subprocess.run(
        [*common, "prepare-profile", *profile_rule], check=False
    ).returncode != 0:
        raise RuntimeError("production profile preparation failed")
    save_target.parent.mkdir(parents=True, exist_ok=True)
    driver_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(save_source, save_target)
    shutil.copy2(driver_source, driver_target)
    make_derived_state_owner_writable(save_target)
    make_derived_state_owner_writable(driver_target)
    if subprocess.run(
        [*common, "verify-profile", *profile_rule], check=False
    ).returncode != 0:
        raise RuntimeError("production profile verification failed")
    preparation: dict[str, Any] = {
        "ok": True,
        "state_dir": str(state_dir),
        "checkpoint_sha256": sha256(save_target),
        "driver_state_sha256": sha256(driver_target),
        "lifecycle": lifecycle,
        "display_mode": display_mode_contract(manifest),
    }
    if lifecycle == {**ORDINARY_LIFECYCLE_CONTRACT, "source": "manifest"}:
        rebind_command = [
            *common,
            "rebind-ordinary-seed-v1",
            "--expected-pipe",
            str(manifest["pipe"]),
            "--receipt",
            str(rebind_receipt),
        ]
        if subprocess.run(rebind_command, check=False).returncode != 0:
            raise RuntimeError("ordinary seed environment rebind failed")
        receipt = read_json(rebind_receipt)
        expectations = receipt.get("no_launch_preflight_expectations")
        if (
            receipt.get("schema") != ORDINARY_SEED_REBIND_V1_SCHEMA
            or receipt.get("ok") is not True
            or receipt.get("status") != "rebound"
            or receipt.get("ck3_launch_attempted") is not False
            or receipt.get("pipe_name") != manifest["pipe"]
            or not isinstance(expectations, dict)
            or expectations.get("pipe_name") != manifest["pipe"]
            or expectations.get("xar_enabled") != "xar_off"
            or expectations.get("succession_lifecycle")
            != ORDINARY_CAMPAIGN_SUCCESSION
            or expectations.get("ordinary_campaign_no_pact") is not True
        ):
            raise RuntimeError("ordinary seed rebind receipt is inconsistent")
        character_id = expectations.get("expected_character_id")
        episode_run_id = expectations.get("expected_episode_run_id")
        checkpoint_sha256 = expectations.get("expected_checkpoint_sha256")
        driver_state_sha256 = expectations.get("expected_driver_state_sha256")
        if (
            isinstance(character_id, bool)
            or not isinstance(character_id, int)
            or character_id <= 0
            or not isinstance(episode_run_id, str)
            or not episode_run_id
            or not isinstance(checkpoint_sha256, str)
            or len(checkpoint_sha256) != 64
            or not isinstance(driver_state_sha256, str)
            or len(driver_state_sha256) != 64
        ):
            raise RuntimeError("ordinary seed rebind receipt lacks preflight pins")
        preflight = [
            *common,
            "native-one-generation-preflight",
            "--expected-character-id",
            str(character_id),
            "--expected-episode-run-id",
            episode_run_id,
            "--expected-checkpoint-sha256",
            checkpoint_sha256,
            "--expected-driver-state-sha256",
            driver_state_sha256,
            *preflight_lifecycle_arguments(lifecycle),
        ]
        if subprocess.run(preflight, check=False).returncode != 0:
            raise RuntimeError("ordinary seed no-launch preflight failed")
        environment_sha256 = receipt_target_sha256(receipt, "environment")
        rebound_driver_sha256 = receipt_target_sha256(receipt, "driver_state")
        actual_driver_sha256 = sha256(driver_target)
        if rebound_driver_sha256 != actual_driver_sha256:
            raise RuntimeError("ordinary seed rebind driver hash does not match prepared state")
        manifest["environment_sha256"] = environment_sha256
        manifest["driver_state_sha256"] = rebound_driver_sha256
        write_json_atomic(manifest_file, manifest)
        preparation.update({
            "environment_sha256": environment_sha256,
            "driver_state_sha256": rebound_driver_sha256,
            "manifest_updated": str(manifest_file),
            "ordinary_seed_rebind_receipt": str(rebind_receipt.resolve()),
            "ordinary_seed_rebind_receipt_sha256": sha256(rebind_receipt),
            "ordinary_no_launch_preflight": "passed",
        })
    if pending_request_id is not None:
        if construction_pending_sidecar_request(
            pending_record, read_json(driver_target), manifest
        ) != pending_request_id:
            raise RuntimeError("prepared driver no longer matches construction pending sidecar")
        if pending_target.exists():
            raise FileExistsError(f"refusing to overwrite prepared state: {pending_target}")
        shutil.copy2(pending_source, pending_target)
        make_derived_state_owner_writable(pending_target)
        if sha256(pending_target) != pending_source_sha256:
            raise RuntimeError("prepared construction pending sidecar hash mismatch")
        preparation["construction_pending_sidecar"] = {
            "status": "paired_no_launch",
            "ledger_status": "pending" if pending_record["pending"] is not None else "applied",
            "source": str(pending_source),
            "path": str(pending_target),
            "sha256": pending_source_sha256,
            "action_request_id": pending_request_id,
        }
    if family_candidate is not None:
        prepared_driver = read_json(driver_target)
        checked_candidate = (
            family_pending_sidecar_pair(
                family_record, prepared_driver, manifest,
                sha256(save_target), formal_report)
            if family_kind == "pending" else
            family_resolved_sidecar_pair(
                family_record, prepared_driver, manifest, sha256(save_target))
        )
        if checked_candidate != family_candidate:
            raise RuntimeError("prepared driver no longer matches family proposal")
        shutil.copy2(family_source, family_target)
        make_derived_state_owner_writable(family_target)
        if sha256(family_target) != family_source_sha256:
            raise RuntimeError("prepared family sidecar hash mismatch")
        preparation["family_pending_sidecar" if family_kind == "pending"
                    else "family_resolved_sidecar"] = {
            "status": "paired_no_launch",
            "source": str(family_source),
            "path": str(family_target),
            "sha256": family_source_sha256,
            "formal_proof_report": (
                str(family_report_sources[0]) if len(family_report_sources) == 1
                else None),
            "formal_proof_report_sha256": (
                family_report_sha256[0] if len(family_report_sources) == 1
                else None),
            "formal_proof_reports": [str(path) for path in family_report_sources],
            "formal_proof_reports_sha256": family_report_sha256,
            "candidate_character_id": family_candidate,
        }
    if child_candidate is not None:
        if child_matrilineal_pending_sidecar_pair(
            child_record, read_json(driver_target), manifest,
            sha256(save_target), child_proof,
            sway_continuation=child_continuation, sway_sidecar=sway_record,
            sway_applied_continuation=sway_applied,
            post_sway_result=post_sway_result,
            post_sway_followups=followup_results,
        ) != child_candidate:
            raise RuntimeError("prepared driver no longer matches child proposal")
        shutil.copy2(child_source, child_target)
        make_derived_state_owner_writable(child_target)
        if sha256(child_target) != child_source_sha256:
            raise RuntimeError("prepared child pending sidecar hash mismatch")
        preparation["child_matrilineal_pending_sidecar"] = {
            "status": "paired_no_launch",
            "source": str(child_source), "path": str(child_target),
            "sha256": child_source_sha256,
            "formal_proof_report": (
                str(child_proof_sources[0]) if len(child_proof_sources) == 1 else None),
            "formal_proof_report_sha256": (
                child_proof_sha256[0] if len(child_proof_sources) == 1 else None),
            "formal_proof_reports": [str(path) for path in child_proof_sources],
            "formal_proof_reports_sha256": child_proof_sha256,
            "cross_domain_continuation_report": (
                str(child_continuation_source) if child_continuation_source else None),
            "cross_domain_continuation_report_sha256": child_continuation_sha256,
            "sway_applied_continuation_report": (
                str(sway_applied_source) if sway_applied_source else None),
            "sway_applied_continuation_report_sha256": sway_applied_sha256,
            "post_sway_child_result_report": (
                str(post_sway_source) if post_sway_source else None),
            "post_sway_child_result_report_sha256": post_sway_sha256,
            "child_result_followup_reports": [str(path) for path in followup_sources],
            "child_result_followup_reports_sha256": followup_sha256,
            "candidate_character_id": child_candidate,
        }
    if faction_request_id is not None:
        if faction_gift_pending_sidecar_request(
            faction_record, read_json(driver_target), manifest, sha256(save_target)
        ) != faction_request_id:
            raise RuntimeError("prepared driver no longer matches faction gift pending action")
        shutil.copy2(faction_source, faction_target)
        make_derived_state_owner_writable(faction_target)
        if sha256(faction_target) != faction_source_sha256:
            raise RuntimeError("prepared faction gift sidecar hash mismatch")
        preparation["faction_gift_pending_sidecar"] = {
            "status": "paired_no_launch",
            "source": str(faction_source),
            "path": str(faction_target),
            "sha256": faction_source_sha256,
            "action_request_id": faction_request_id,
            "pre_submit_checkpoint_sha256": sha256(save_target),
        }
    if sway_action_id is not None:
        prepared_driver = read_json(driver_target)
        prepared_sway_action_id = (
            sway_formal_pending_sidecar_request(
                sway_record, prepared_driver,
                sha256(save_target), save_target.stat().st_size)
            if sway_ledger_status == "pending" else
            sway_formal_resolved_sidecar_pair(
                sway_record,
                {**prepared_driver, "last_checkpoint": applied_saved}
                if post_sway_result is not None else prepared_driver,
                applied_saved["sha256"] if post_sway_result is not None
                else sha256(save_target),
                applied_saved["size"] if post_sway_result is not None
                else save_target.stat().st_size,
                child_continuation, sway_applied)[0])
        if prepared_sway_action_id != sway_action_id:
            raise RuntimeError("prepared driver no longer matches Sway pending ACK")
        shutil.copy2(sway_source, sway_target)
        make_derived_state_owner_writable(sway_target)
        if sha256(sway_target) != sway_source_sha256:
            raise RuntimeError("prepared Sway pending sidecar hash mismatch")
        preparation["sway_formal_pending_sidecar"
                    if sway_ledger_status == "pending" else "sway_formal_resolved_sidecar"] = {
            "status": "paired_no_launch",
            "ledger_status": sway_ledger_status,
            "source": str(sway_source), "path": str(sway_target),
            "sha256": sway_source_sha256,
            "action_id": sway_action_id,
            "checkpoint_sha256": sha256(save_target),
            "driver_state_sha256": sha256(driver_target),
            "pending_report_sha256": (child_continuation_sha256
                                      if sway_ledger_status == "applied" else None),
            "applied_report_sha256": (sway_applied_sha256
                                      if sway_ledger_status == "applied" else None),
        }
    print(json.dumps(preparation))
    return 0


def command_run(args: argparse.Namespace) -> int:
    child_pair = args.private_child_matrilineal_pending_read
    child_recovery_pair = args.private_child_matrilineal_pending_recovery
    recovery_proof_args = (
        args.child_matrilineal_recovery_proof_report,
        args.child_matrilineal_recovery_continuation_report,
        args.child_matrilineal_recovery_sway_sidecar,
        args.child_matrilineal_recovery_sway_applied_report,
        args.child_matrilineal_recovery_post_sway_result_report,
    )
    if child_recovery_pair is None and any(value is not None for value in recovery_proof_args):
        raise ValueError("child recovery proof inputs require the pending recovery route")
    if child_pair is not None and (
        len(child_pair) != 2 or any(type(value) is not int or not 0 < value < 2**31
                                    for value in child_pair)
        or child_pair[0] == child_pair[1]
    ):
        raise ValueError("private child pending read needs two distinct positive IDs")
    if child_recovery_pair is not None:
        if (child_pair is not None or not args.private_lifestyle_formal_trial
                or args.turns not in {None, 1}
                or len(child_recovery_pair) != 2
                or any(type(value) is not int or not 0 < value < 2**31
                       for value in child_recovery_pair)
                or child_recovery_pair[0] == child_recovery_pair[1]):
            raise ValueError("private child pending recovery needs one LIFE turn and a distinct pair")
        if (args.private_activity_feast_planner_open
                or args.private_activity_feast_stage1_option_read
                or args.private_activity_cost_slot12_raw_read
                or args.private_activity_feast_stage1_confirm
                or args.private_activity_feast_stage2_gate_read
                or args.private_activity_feast_stage2_location_province
                or args.private_activity_planner_diag_query
                or args.private_construction_formal_trial
                or args.private_family_marriage_formal_trial
                or args.private_m5_joint_collector
                or args.private_active_scheme_sway_target is not None
                or args.private_active_scheme_sway_formal_trial
                or args.private_faction_round_id is not None):
            raise ValueError("private child pending recovery must run alone")
    if (args.private_activity_feast_planner_open
            or args.private_activity_feast_stage1_option_read
            or args.private_activity_cost_slot12_raw_read
            or args.private_activity_feast_stage1_confirm):
        if (child_pair is not None or args.private_activity_planner_diag_query
                or (args.private_activity_feast_planner_open
                    and args.private_activity_feast_stage1_option_read)
                or (args.private_activity_cost_slot12_raw_read
                    and args.private_activity_feast_stage1_option_read)
                or (args.private_activity_feast_stage1_confirm and (
                    args.private_activity_feast_planner_open
                    or args.private_activity_feast_stage1_option_read
                    or args.private_activity_cost_slot12_raw_read))):
            raise ValueError("select one private feast paused frame route")
    if (args.private_activity_feast_stage2_gate_read
            and not args.private_activity_feast_stage1_confirm):
        raise ValueError("private stage-2 gate read requires stage-1 Confirm")
    if args.private_activity_feast_stage2_location_province:
        province_ids = args.private_activity_feast_stage2_location_province
        if not args.private_activity_feast_stage1_confirm:
            raise ValueError("private stage-2 location read requires stage-1 Confirm")
        if (not 1 <= len(province_ids) <= 8
                or len(set(province_ids)) != len(province_ids)
                or any(type(value) is not int or not 0 < value <= 0xFFFFFFFF
                       for value in province_ids)):
            raise ValueError("private stage-2 location read needs 1-8 distinct province IDs")
    if (args.private_active_scheme_sway_formal_trial
            and args.private_active_scheme_sway_target is None):
        raise ValueError("private Sway formal trial requires an explicit target")
    if args.private_active_scheme_sway_target is not None and not (
        0 < args.private_active_scheme_sway_target <= 0xFFFFFFFF
    ):
        raise ValueError("private sway target must be a full positive character ID")
    if (
        args.require_initial_lifestyle_focus_before_date_advance
        and not args.private_lifestyle_formal_trial
    ):
        raise ValueError(
            "initial LIFE focus gate requires --private-lifestyle-formal-trial"
        )
    manifest = load_manifest(args.manifest.resolve())
    if args.private_lifestyle_formal_trial:
        verify_private_lifestyle_dll(manifest)
    lifecycle = lifecycle_contract(manifest)
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(f"attempt output already exists: {output}")
    save, driver_path, driver = current_checkpoint_identity(manifest)
    child_recovery_proof = None
    if child_recovery_pair is not None:
        proof_paths = list(args.child_matrilineal_recovery_proof_report or [])
        if not proof_paths:
            raise ValueError("private child pending recovery requires saved formal proof")
        state_dir = manifest_path(manifest["state_dir"], "state_dir")
        rebind = read_json(state_dir / "ordinary-seed-rebind-v1.json")
        rebound_driver = rebind.get("driver_state")
        rebound_save = rebind.get("save")
        prepared_driver_sha = sha256(driver_path)
        prepared_save_sha = sha256(save)
        if (lifecycle != {**ORDINARY_LIFECYCLE_CONTRACT, "source": "manifest"}
                or rebind.get("schema") != ORDINARY_SEED_REBIND_V1_SCHEMA
                or rebind.get("ok") is not True
                or rebind.get("status") != "rebound"
                or not isinstance(rebound_driver, dict)
                or not isinstance(rebound_save, dict)
                or not isinstance(rebound_save.get("target"), dict)
                or str(rebound_driver.get("source_sha256", "")).casefold()
                != str(manifest.get("raw_source_driver_sha256", "")).casefold()
                or str(rebound_driver.get("target_sha256", "")).casefold()
                != prepared_driver_sha
                or str(manifest.get("driver_state_sha256", "")).casefold()
                != prepared_driver_sha
                or str(manifest.get("checkpoint_sha256", "")).casefold()
                != prepared_save_sha
                or rebound_save.get("bytes_unchanged") is not True
                or str(rebound_save.get("target", {}).get("sha256", "")).casefold()
                != prepared_save_sha):
            raise ValueError("private child recovery raw/prepared pair differs from official rebind")
        child_ledger_path = (manifest_path(manifest["state_dir"], "state_dir")
                             / "player-child-matrilineal-formal-v1.json")
        child_ledger = read_json(child_ledger_path)
        reports = [read_json(path.resolve()) for path in proof_paths]
        continuation = (read_json(args.child_matrilineal_recovery_continuation_report.resolve())
                        if args.child_matrilineal_recovery_continuation_report else None)
        sway_sidecar = (read_json(args.child_matrilineal_recovery_sway_sidecar.resolve())
                        if args.child_matrilineal_recovery_sway_sidecar else None)
        sway_applied = (read_json(args.child_matrilineal_recovery_sway_applied_report.resolve())
                        if args.child_matrilineal_recovery_sway_applied_report else None)
        post_sway_result = (
            read_json(args.child_matrilineal_recovery_post_sway_result_report.resolve())
            if args.child_matrilineal_recovery_post_sway_result_report else None
        )
        candidate = child_matrilineal_pending_sidecar_pair(
            child_ledger, driver, manifest, sha256(save), reports,
            sway_continuation=continuation, sway_sidecar=sway_sidecar,
            sway_applied_continuation=sway_applied,
            post_sway_result=post_sway_result,
        )
        pending = child_ledger["pending"]
        actor = episode_value(driver, manifest, "episode_character_id")
        episode = episode_value(driver, manifest, "episode_run_id")
        if (candidate != child_recovery_pair[1]
                or pending.get("heir_character_id") != child_recovery_pair[0]
                or pending.get("candidate_character_id") != child_recovery_pair[1]
                or pending.get("played_character_id") != actor
                or pending.get("episode_run_id") != episode):
            raise ValueError("private child recovery target differs from paired pending proposal")
        child_recovery_proof = {
            "status": "paired_no_launch", "actor": actor, "episode": episode,
            "heir_character_id": child_recovery_pair[0],
            "candidate_character_id": child_recovery_pair[1],
            "pending_ledger_sha256": sha256(child_ledger_path),
            "raw_source_driver_sha256": rebound_driver["source_sha256"],
            "prepared_driver_state_sha256": prepared_driver_sha,
            "checkpoint_sha256": prepared_save_sha,
            "ordinary_rebind_receipt_sha256": sha256(state_dir / "ordinary-seed-rebind-v1.json"),
            "formal_proof_sha256": [sha256(path.resolve()) for path in proof_paths],
            "post_sway_result_report_sha256": (
                sha256(args.child_matrilineal_recovery_post_sway_result_report.resolve())
                if args.child_matrilineal_recovery_post_sway_result_report else None
            ),
        }
    output.mkdir(parents=True)
    exact_stop_path = args.exact_war_move_stop_contract
    exact_stop_sha = args.exact_war_move_stop_sha256
    if bool(exact_stop_path) != bool(exact_stop_sha):
        raise ValueError("exact war move stop requires both contract path and SHA-256")
    if exact_stop_path is not None:
        exact_stop_path = exact_stop_path.resolve()
        raw_contract = exact_stop_path.read_bytes()
        if hashlib.sha256(raw_contract).hexdigest() != exact_stop_sha.lower():
            raise ValueError("exact war move stop contract SHA-256 changed")
        exact_contract = json.loads(raw_contract.decode("utf-8-sig"))
        if not isinstance(exact_contract, dict) or (
            str(exact_contract.get("source_save_sha256", "")).lower() != sha256(save)
            or str(exact_contract.get("source_driver_sha256", "")).lower() != sha256(driver_path)
        ):
            raise ValueError("exact war move stop contract source pair differs from prepared state")
    character_id = episode_value(driver, manifest, "episode_character_id")
    episode_run_id = episode_value(driver, manifest, "episode_run_id")
    common = agent_command(manifest)
    preflight = [
        *common,
        "native-one-generation-preflight",
        "--expected-character-id",
        str(character_id),
        "--expected-episode-run-id",
        str(episode_run_id),
        "--expected-checkpoint-sha256",
        sha256(save),
        "--expected-driver-state-sha256",
        sha256(driver_path),
        *preflight_lifecycle_arguments(lifecycle),
    ]
    preflight_exit = run_logged(
        preflight,
        output / "preflight-stdout.txt",
        output / "preflight-stderr.txt",
    )
    receipt: dict[str, Any] = {
        "schema": "xar-g2-preview-python-operator-v1",
        "manifest": str(args.manifest.resolve()),
        "output": str(output),
        "checkpoint_sha256_before": sha256(save),
        "driver_state_sha256_before": sha256(driver_path),
        "exact_war_move_stop_contract": str(exact_stop_path) if exact_stop_path else None,
        "exact_war_move_stop_sha256": exact_stop_sha,
        "preflight_exit_code": preflight_exit,
        "lifecycle": lifecycle,
        "display_mode": display_mode_contract(manifest),
        "private_lifestyle_formal_trial": args.private_lifestyle_formal_trial,
        "private_construction_formal_trial": args.private_construction_formal_trial,
        "private_family_marriage_formal_trial": args.private_family_marriage_formal_trial,
        "private_m5_joint_collector": args.private_m5_joint_collector,
        "private_prisoner_collection_observation": (
            args.private_prisoner_collection_observation
        ),
        "private_active_scheme_sway_target": args.private_active_scheme_sway_target,
        "private_child_matrilineal_pending_read": child_pair,
        "private_child_matrilineal_pending_recovery": child_recovery_proof,
        "private_active_scheme_sway_formal_trial": (
            args.private_active_scheme_sway_formal_trial
        ),
        "private_realm_law_paused_query": args.private_realm_law_paused_query,
        "private_activity_planner_diag_query": (
            args.private_activity_planner_diag_query
        ),
        "private_activity_feast_planner_open": (
            args.private_activity_feast_planner_open
        ),
        "private_activity_feast_stage1_option_read": (
            args.private_activity_feast_stage1_option_read
        ),
        "private_activity_cost_slot12_raw_read": (
            args.private_activity_cost_slot12_raw_read
        ),
        "private_activity_feast_stage1_confirm": (
            args.private_activity_feast_stage1_confirm
        ),
        "private_activity_feast_stage2_gate_read": (
            args.private_activity_feast_stage2_gate_read
        ),
        "private_activity_feast_stage2_location_provinces": (
            args.private_activity_feast_stage2_location_province
        ),
        "require_initial_lifestyle_focus_before_date_advance": (
            args.require_initial_lifestyle_focus_before_date_advance
        ),
    }
    if preflight_exit != 0:
        receipt.update({"ok": False, "status": "preflight_blocked", "game_launched": False})
        (output / "operator-receipt.json").write_text(
            json.dumps(receipt, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return preflight_exit
    turns = (1 if child_recovery_pair is not None else args.turns
             if args.turns is not None else int(manifest.get("formal_turns", 20)))
    timeout = args.timeout if args.timeout is not None else int(manifest.get("timeout_seconds", 390))
    readiness_timeout = args.readiness_timeout if args.readiness_timeout is not None else int(
        manifest.get("readiness_timeout_seconds", 300)
    )
    formal_report = output / "formal-report.txt"
    formal_stderr = output / "formal-stderr.txt"
    stop_path = manifest_path(manifest["state_dir"], "state_dir") / "native-auto-run.stop"
    print(f"Operator stop request file: {stop_path}", file=sys.stderr, flush=True)
    private_faction_round = args.private_faction_round_id
    run_state_root = live_run_state_root(args.live_run_state_root)
    run_identity = allocate_live_run_id(
        G2_LIVE_RUN_MOD_KEY, state_root=run_state_root
    )
    try:
        identity_receipt = write_identity_receipt(output, (run_identity,))
    except Exception:
        record_live_run_status(
            run_identity, "voided",
            reason="identity receipt could not be persisted before launch",
            state_root=run_state_root,
        )
        raise
    receipt["live_run_id"] = run_identity.run_id
    receipt["live_run_identity_receipt"] = str(identity_receipt)
    def record_formal_child_start(pid: int) -> None:
        record_live_run_status(
            run_identity, "launch-started",
            reason=f"native-auto-run child started; pid={pid}",
            state_root=run_state_root,
        )
        receipt["formal_runner_pid"] = pid

    try:
        formal_exit = run_logged(
            native_auto_run_command(
                common,
                turns=turns,
                timeout=timeout,
                readiness_timeout=readiness_timeout,
                private_faction_round_id_value=private_faction_round,
                private_lifestyle_formal_trial=args.private_lifestyle_formal_trial,
                private_construction_formal_trial=args.private_construction_formal_trial,
                private_family_marriage_formal_trial=args.private_family_marriage_formal_trial,
                private_m5_joint_collector=args.private_m5_joint_collector,
                private_prisoner_collection_observation=(
                    args.private_prisoner_collection_observation
                ),
                private_active_scheme_sway_target=(
                    args.private_active_scheme_sway_target
                ),
                private_child_matrilineal_pending_read=(
                    tuple(args.private_child_matrilineal_pending_read)
                    if args.private_child_matrilineal_pending_read is not None else None
                ),
                private_child_matrilineal_pending_recovery=(
                    tuple(child_recovery_pair) if child_recovery_pair is not None else None
                ),
                private_active_scheme_sway_formal_trial=(
                    args.private_active_scheme_sway_formal_trial
                ),
                private_realm_law_paused_query=args.private_realm_law_paused_query,
                private_activity_planner_diag_query=(
                    args.private_activity_planner_diag_query
                ),
                private_activity_feast_planner_open=(
                    args.private_activity_feast_planner_open
                ),
                private_activity_feast_stage1_option_read=(
                    args.private_activity_feast_stage1_option_read
                ),
                private_activity_cost_slot12_raw_read=(
                    args.private_activity_cost_slot12_raw_read
                ),
                private_activity_feast_stage1_confirm=(
                    args.private_activity_feast_stage1_confirm
                ),
                private_activity_feast_stage2_gate_read=(
                    args.private_activity_feast_stage2_gate_read
                ),
                private_activity_feast_stage2_location_provinces=(
                    tuple(args.private_activity_feast_stage2_location_province)
                    if args.private_activity_feast_stage2_location_province else None
                ),
                require_initial_lifestyle_focus_before_date_advance=(
                    args.require_initial_lifestyle_focus_before_date_advance
                ),
                succession_lifecycle=str(lifecycle["succession_lifecycle"]),
                ordinary_campaign_no_pact=(
                    lifecycle["ordinary_campaign_no_pact"] is True
                ),
                exact_war_move_stop_contract=exact_stop_path,
                exact_war_move_stop_sha256=exact_stop_sha,
            ),
            formal_report,
            formal_stderr,
            on_started=record_formal_child_start,
        )
    except BaseException as error:
        record_live_run_status(
            run_identity, "completed-red",
            reason=f"native-auto-run raised {type(error).__name__}",
            state_root=run_state_root,
        )
        raise
    record_live_run_status(
        run_identity,
        "completed-green" if formal_exit == 0 else "completed-red",
        reason=f"native-auto-run exited {formal_exit}",
        state_root=run_state_root,
    )
    receipt.update({
        "ok": formal_exit == 0,
        "status": "completed" if formal_exit == 0 else "formal_run_failed",
        "game_launched": True,
        "formal_exit_code": formal_exit,
        "formal_report": str(formal_report),
        "formal_stderr": str(formal_stderr),
        "turns": turns,
        "timeout_seconds": timeout,
        "readiness_timeout_seconds": readiness_timeout,
        "private_faction_gift_formal_trial": private_faction_round is not None,
        "private_faction_round_id": private_faction_round,
        "checkpoint_sha256_after": sha256(save) if save.is_file() else None,
        "driver_state_sha256_after": sha256(driver_path) if driver_path.is_file() else None,
    })
    (output / "operator-receipt.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt, ensure_ascii=False))
    return formal_exit


def command_query_current_timeline_blocker_context_v1(
    args: argparse.Namespace,
) -> int:
    manifest_path_value = args.manifest.resolve()
    manifest = load_manifest(manifest_path_value)
    source = frozen_source_identity(manifest)
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(f"attempt output already exists: {output}")
    output.mkdir(parents=True)
    save, driver_path, driver = current_checkpoint_identity(manifest)
    character_id = episode_value(driver, manifest, "episode_character_id")
    episode_run_id = episode_value(driver, manifest, "episode_run_id")
    common = agent_command(manifest)
    checkpoint_before = sha256(save)
    driver_before = sha256(driver_path)
    preflight = [
        *common,
        "native-one-generation-preflight",
        "--expected-character-id",
        str(character_id),
        "--expected-episode-run-id",
        str(episode_run_id),
        "--expected-checkpoint-sha256",
        checkpoint_before,
        "--expected-driver-state-sha256",
        driver_before,
    ]
    preflight_exit = run_logged(
        preflight,
        output / "preflight-stdout.txt",
        output / "preflight-stderr.txt",
    )
    receipt: dict[str, Any] = {
        "schema": "xar-g2-private-timeline-query-operator-v1",
        "mode": "query-current-timeline-blocker-context-v1",
        "manifest": str(manifest_path_value),
        "output": str(output),
        "source": source,
        "round": args.private_timeline_query_round_id,
        "private_build": True,
        "advertised": False,
        "checkpoint_sha256_before": checkpoint_before,
        "driver_state_sha256_before": driver_before,
        "preflight_exit_code": preflight_exit,
        "gameplay_actions": 0,
        "ui_inputs": 0,
        "date_advance_actions": 0,
        "close_actions": 0,
        "marriage_actions": 0,
        "death_terminal_actions": 0,
        "python_successor_continuations": 0,
    }
    receipt_path = output / "operator-receipt.json"
    if preflight_exit != 0:
        receipt.update({"ok": False, "status": "preflight_blocked", "game_launched": False})
        receipt_path.write_text(
            json.dumps(receipt, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return preflight_exit

    timeout = args.timeout if args.timeout is not None else int(
        manifest.get("timeout_seconds", 390)
    )
    readiness_timeout = (
        args.readiness_timeout
        if args.readiness_timeout is not None
        else int(manifest.get("readiness_timeout_seconds", 300))
    )
    query_stdout = output / "query-report.json"
    query_stderr = output / "query-stderr.txt"
    query_exit = run_logged(
        timeline_blocker_query_command(
            common,
            timeout=timeout,
            readiness_timeout=readiness_timeout,
            private_timeline_query_round_id_value=(
                args.private_timeline_query_round_id
            ),
        ),
        query_stdout,
        query_stderr,
    )
    query_report: dict[str, Any] | None = None
    query_report_error: str | None = None
    try:
        query_report = read_json(query_stdout)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        query_report_error = f"{type(error).__name__}: {error}"

    checkpoint_after = sha256(save) if save.is_file() else None
    driver_after = sha256(driver_path) if driver_path.is_file() else None
    query_checks = (
        query_report.get("checks") if isinstance(query_report, dict) else None
    )
    ok = bool(
        query_exit == 0
        and isinstance(query_report, dict)
        and query_report.get("ok") is True
        and query_report.get("round") == args.private_timeline_query_round_id
        and checkpoint_after == checkpoint_before
        and isinstance(query_checks, dict)
        and query_checks.get("date_unchanged") is True
        and query_checks.get("single_cold_restore_bookkeeping") is True
        and query_checks.get("query_history_unchanged") is True
        and query_checks.get("driver_history_matches_query_after") is True
        and query_checks.get("cleanup_proven") is True
    )
    receipt.update({
        "ok": ok,
        "status": "GREEN_READ_ONLY" if ok else "query_failed",
        "game_launched": True,
        "query_exit_code": query_exit,
        "query_report": str(query_stdout),
        "query_stderr": str(query_stderr),
        "query_report_error": query_report_error,
        "timeout_seconds": timeout,
        "readiness_timeout_seconds": readiness_timeout,
        "checkpoint_sha256_after": checkpoint_after,
        "driver_state_sha256_after": driver_after,
        "checkpoint_unchanged": checkpoint_after == checkpoint_before,
        "driver_state_unchanged": driver_after == driver_before,
        "driver_state_cold_restore_bookkeeping_exact": (
            query_checks.get("single_cold_restore_bookkeeping")
            if isinstance(query_checks, dict)
            else False
        ),
        "driver_state_query_history_unchanged": (
            query_checks.get("query_history_unchanged")
            if isinstance(query_checks, dict)
            else False
        ),
        "date_before": (
            query_report.get("before", {}).get("date_raw")
            if isinstance(query_report, dict)
            and isinstance(query_report.get("before"), dict)
            else None
        ),
        "date_after": (
            query_report.get("after", {}).get("date_raw")
            if isinstance(query_report, dict)
            and isinstance(query_report.get("after"), dict)
            else None
        ),
        "date_unchanged": (
            query_checks.get("date_unchanged")
            if isinstance(query_checks, dict)
            else False
        ),
        "query_envelope": (
            query_report.get("query_envelope")
            if isinstance(query_report, dict)
            else None
        ),
        "cleanup": (
            query_report.get("cleanup")
            if isinstance(query_report, dict)
            else None
        ),
        "agent_report": query_report,
    })
    receipt_path.write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt, ensure_ascii=False))
    return 0 if ok else (query_exit if query_exit != 0 else 1)


def command_query_first_heir_marriage_alliance_result_v1(
    args: argparse.Namespace,
) -> int:
    manifest = load_manifest(args.manifest.resolve())
    lifecycle = lifecycle_contract(manifest)
    source = frozen_source_identity(manifest)
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(f"attempt output already exists: {output}")
    output.mkdir(parents=True)
    save, driver_path, driver = current_checkpoint_identity(manifest)
    actor = episode_value(driver, manifest, "episode_character_id")
    episode = episode_value(driver, manifest, "episode_run_id")
    checkpoint_before = sha256(save)
    driver_before = sha256(driver_path)
    report_path = args.proposal_report.resolve()
    report_sha = sha256(report_path)
    common = agent_command(manifest)
    receipt: dict[str, Any] = {
        "schema": "xar-g2-private-family-alliance-query-operator-v1",
        "mode": "query-first-heir-marriage-alliance-result-v1",
        "manifest": str(args.manifest.resolve()),
        "output": str(output), "source": source,
        "round": args.ownership_round_id,
        "private_build": True, "advertised": False,
        "proposal_report": str(report_path),
        "proposal_report_sha256": report_sha,
        "recipient_character_id": args.recipient_character_id,
        "checkpoint_sha256_before": checkpoint_before,
        "driver_state_sha256_before": driver_before,
        "gameplay_actions": 0, "date_advance_actions": 0,
        "marriage_actions": 0, "ui_inputs": 0,
    }
    receipt_path = output / "operator-receipt.json"
    if (report_sha.casefold() != args.proposal_report_sha256.casefold()
            or args.recipient_character_id <= 0):
        receipt.update({"ok": False, "status": "proposal_binding_blocked",
                        "game_launched": False})
        receipt_path.write_text(json.dumps(receipt, indent=2) + "\n",
                                encoding="utf-8")
        return 1
    preflight_exit = run_logged([
        *common, "native-one-generation-preflight",
        "--expected-character-id", str(actor),
        "--expected-episode-run-id", str(episode),
        "--expected-checkpoint-sha256", checkpoint_before,
        "--expected-driver-state-sha256", driver_before,
        *preflight_lifecycle_arguments(lifecycle),
    ], output / "preflight-stdout.txt", output / "preflight-stderr.txt")
    receipt["preflight_exit_code"] = preflight_exit
    if preflight_exit != 0:
        receipt.update({"ok": False, "status": "preflight_blocked",
                        "game_launched": False})
        receipt_path.write_text(json.dumps(receipt, indent=2) + "\n",
                                encoding="utf-8")
        return preflight_exit
    timeout = args.timeout if args.timeout is not None else int(
        manifest.get("timeout_seconds", 390))
    readiness_timeout = args.readiness_timeout if args.readiness_timeout is not None else int(
        manifest.get("readiness_timeout_seconds", 300))
    query_stdout = output / "query-report.json"
    query_stderr = output / "query-stderr.txt"
    query_exit = run_logged(family_alliance_result_query_command(
        common, timeout=timeout, readiness_timeout=readiness_timeout,
        ownership_round_id=args.ownership_round_id,
        proposal_report=report_path,
        proposal_report_sha256=report_sha,
        recipient_character_id=args.recipient_character_id,
    ), query_stdout, query_stderr)
    try:
        report = read_json(query_stdout)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        report = None
    checks = report.get("checks") if isinstance(report, dict) else None
    after_save = sha256(save) if save.is_file() else None
    after_driver = sha256(driver_path) if driver_path.is_file() else None
    ok = bool(query_exit == 0 and isinstance(report, dict)
              and report.get("ok") is True
              and report.get("round") == args.ownership_round_id
              and isinstance(checks, dict)
              and checks.get("paused_frame_unchanged") is True
              and checks.get("date_unchanged") is True
              and checks.get("checkpoint_unchanged") is True
              and checks.get("window_minimized_or_hidden") is True
              and checks.get("cleanup_proven") is True
              and after_save == checkpoint_before)
    receipt.update({
        "ok": ok, "status": "GREEN_READ_ONLY" if ok else "query_failed",
        "game_launched": (
            report.get("launch_attempted")
            if isinstance(report, dict) else None
        ), "query_exit_code": query_exit,
        "query_report": str(query_stdout), "query_stderr": str(query_stderr),
        "query_envelope": report.get("query_envelope") if isinstance(report, dict) else None,
        "window_state_after_readiness": (
            report.get("window_state_after_readiness")
            if isinstance(report, dict) else None
        ),
        "before_frame": report.get("before", {}).get("frame") if isinstance(report, dict) else None,
        "after_frame": report.get("after", {}).get("frame") if isinstance(report, dict) else None,
        "checkpoint_sha256_after": after_save,
        "driver_state_sha256_after": after_driver,
        "cleanup": report.get("cleanup") if isinstance(report, dict) else None,
    })
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n",
                            encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False))
    return 0 if ok else (query_exit if query_exit != 0 else 1)


def command_continue_death_succession_modal_v1(
    args: argparse.Namespace,
) -> int:
    """Run the sealed succession action and emit a complete immutable receipt."""

    manifest_path_value = args.manifest.resolve()
    manifest = load_manifest(manifest_path_value)
    source = frozen_source_identity(manifest)
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(f"attempt output already exists: {output}")
    output.mkdir(parents=True)
    save, driver_path, driver = current_checkpoint_identity(manifest)
    character_id = int(episode_value(driver, manifest, "episode_character_id"))
    episode_run_id = str(episode_value(driver, manifest, "episode_run_id"))
    checkpoint_before = sha256(save)
    driver_before = sha256(driver_path)
    game_exe = manifest_path(manifest["game_dir"], "game_dir") / "binaries" / "ck3.exe"
    dll = manifest_path(manifest["dll"], "dll")
    injector = manifest_path(manifest["injector"], "injector")
    runtime_identities = {
        "ck3_exe": {"path": str(game_exe), "sha256": sha256(game_exe)},
        "private_bridge": {"path": str(dll), "sha256": sha256(dll)},
        "injector": {"path": str(injector), "sha256": sha256(injector)},
    }
    exact_input = bool(
        checkpoint_before == R778_SOURCE_CHECKPOINT_SHA256
        and driver_before == R778_SOURCE_DRIVER_STATE_SHA256
        and character_id == R778_CHARACTER_ID
        and episode_run_id == R778_EPISODE_RUN_ID
        and args.expected_date_raw == R778_DATE_RAW
        and runtime_identities["ck3_exe"]["sha256"] == R778_CK3_EXE_SHA256
        and runtime_identities["private_bridge"]["sha256"]
        == R781_PRIVATE_BRIDGE_SHA256
        and runtime_identities["injector"]["sha256"] == R781_INJECTOR_SHA256
    )
    receipt: dict[str, Any] = {
        "schema": "xar-g2-private-death-succession-action-operator-v1",
        "mode": "continue-death-succession-modal-v1",
        "manifest": str(manifest_path_value),
        "output": str(output),
        "source": source,
        "runtime_identities": runtime_identities,
        "round": args.private_timeline_action_round_id,
        "private_build": True,
        "advertised": False,
        "expected_played_character_id": character_id,
        "expected_episode_run_id": episode_run_id,
        "expected_date_raw": args.expected_date_raw,
        "checkpoint_sha256_before": checkpoint_before,
        "driver_state_sha256_before": driver_before,
        "exact_sealed_input": exact_input,
        "close_actions": 0,
        "life_advance_actions": 0,
        "checkpoint_actions": 0,
        "marriage_actions": 0,
        "marriage_queries": 0,
        "death_terminal_actions": 0,
        "python_successor_continuations": 0,
        "ui_inputs": 0,
        "other_gameplay_actions": 0,
    }
    receipt_path = output / "operator-receipt.json"
    if not exact_input:
        receipt.update(
            {"ok": False, "status": "input_binding_blocked", "game_launched": False}
        )
        receipt_path.write_text(
            json.dumps(receipt, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return 1

    common = agent_command(manifest)
    preflight = [
        *common,
        "native-one-generation-preflight",
        "--expected-character-id",
        str(character_id),
        "--expected-episode-run-id",
        episode_run_id,
        "--expected-checkpoint-sha256",
        checkpoint_before,
        "--expected-driver-state-sha256",
        driver_before,
    ]
    preflight_exit = run_logged(
        preflight,
        output / "preflight-stdout.txt",
        output / "preflight-stderr.txt",
    )
    receipt["preflight_exit_code"] = preflight_exit
    if preflight_exit != 0:
        receipt.update(
            {"ok": False, "status": "preflight_blocked", "game_launched": False}
        )
        receipt_path.write_text(
            json.dumps(receipt, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return preflight_exit

    timeout = args.timeout if args.timeout is not None else int(
        manifest.get("timeout_seconds", 390)
    )
    readiness_timeout = (
        args.readiness_timeout
        if args.readiness_timeout is not None
        else int(manifest.get("readiness_timeout_seconds", 300))
    )
    action_stdout = output / "action-report.json"
    action_stderr = output / "action-stderr.txt"
    action_exit = run_logged(
        death_succession_modal_action_command(
            common,
            timeout=timeout,
            readiness_timeout=readiness_timeout,
            private_timeline_action_round_id_value=(
                args.private_timeline_action_round_id
            ),
            expected_played_character_id=character_id,
            expected_episode_run_id=episode_run_id,
            expected_date_raw=args.expected_date_raw,
        ),
        action_stdout,
        action_stderr,
    )
    action_report: dict[str, Any] | None = None
    action_report_error: str | None = None
    try:
        action_report = read_json(action_stdout)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        action_report_error = f"{type(error).__name__}: {error}"

    checkpoint_after = sha256(save) if save.is_file() else None
    driver_after = sha256(driver_path) if driver_path.is_file() else None
    checks = action_report.get("checks") if isinstance(action_report, dict) else None
    counts = (
        action_report.get("action_counts") if isinstance(action_report, dict) else None
    )
    forbidden = (
        action_report.get("forbidden_action_counts")
        if isinstance(action_report, dict)
        else None
    )
    action_result = (
        action_report.get("action_result") if isinstance(action_report, dict) else None
    )
    checkpoint = (
        action_report.get("checkpoint") if isinstance(action_report, dict) else None
    )
    ok = bool(
        action_exit == 0
        and isinstance(action_report, dict)
        and action_report.get("ok") is True
        and action_report.get("status") == "GREEN_MATERIAL"
        and action_report.get("round") == args.private_timeline_action_round_id
        and isinstance(checks, dict)
        and checks
        and all(value is True for value in checks.values())
        and counts == {"close": 1, "life_advance": 1, "checkpoint": 1}
        and isinstance(forbidden, dict)
        and forbidden
        and all(value == 0 for value in forbidden.values())
        and checkpoint_after is not None
        and checkpoint_after != checkpoint_before
        and isinstance(checkpoint, dict)
        and checkpoint.get("history_index") == 6
        and checkpoint.get("sha256") == checkpoint_after
        and isinstance(action_result, dict)
        and action_result.get("starting_date_raw") == R778_DATE_RAW
        and isinstance(action_result.get("ending_date_raw"), int)
        and action_result.get("ending_date_raw") > R778_DATE_RAW
    )
    submission_ack = (
        action_result.get("submission_ack")
        if isinstance(action_result, dict)
        else None
    )
    initial_query = (
        action_result.get("initial_query")
        if isinstance(action_result, dict)
        else None
    )
    post_query = (
        action_result.get("postcondition_query")
        if isinstance(action_result, dict)
        else None
    )
    post_queries = (
        action_result.get("postcondition_queries")
        if isinstance(action_result, dict)
        else None
    )
    post_query_attempts = (
        action_result.get("post_query_attempts")
        if isinstance(action_result, dict)
        else None
    )
    submitted_unconfirmed = bool(
        isinstance(action_report, dict)
        and action_report.get("status") == "RED_SUBMITTED_UNCONFIRMED"
        and isinstance(action_result, dict)
        and action_result.get("status") == "submitted_unconfirmed"
    )
    life_advance = (
        action_result.get("life_advance_result")
        if isinstance(action_result, dict)
        else None
    )
    receipt.update(
        {
            "ok": ok,
            "status": (
                "GREEN_MATERIAL"
                if ok
                else "RED_SUBMITTED_UNCONFIRMED"
                if submitted_unconfirmed
                else "action_failed"
            ),
            "game_launched": True,
            "action_exit_code": action_exit,
            "action_report": str(action_stdout),
            "action_report_sha256": sha256(action_stdout)
            if action_stdout.is_file()
            else None,
            "action_stderr": str(action_stderr),
            "action_stderr_sha256": sha256(action_stderr)
            if action_stderr.is_file()
            else None,
            "action_report_error": action_report_error,
            "timeout_seconds": timeout,
            "readiness_timeout_seconds": readiness_timeout,
            "checkpoint_sha256_after": checkpoint_after,
            "driver_state_sha256_after": driver_after,
            "initial_query": initial_query,
            "submission_ack": submission_ack,
            "independent_postcondition_query": post_query,
            "postcondition_queries": post_queries,
            "post_query_attempts": post_query_attempts,
            "post_failure": (
                action_result.get("post_failure")
                if isinstance(action_result, dict)
                else None
            ),
            "life_advance_result": life_advance,
            "checkpoint": checkpoint,
            "checks": checks,
            "cleanup": action_report.get("cleanup")
            if isinstance(action_report, dict)
            else None,
            "close_actions": counts.get("close", 0)
            if isinstance(counts, dict)
            else 0,
            "life_advance_actions": counts.get("life_advance", 0)
            if isinstance(counts, dict)
            else 0,
            "checkpoint_actions": counts.get("checkpoint", 0)
            if isinstance(counts, dict)
            else 0,
            "agent_report": action_report,
        }
    )
    receipt_path.write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt, ensure_ascii=False))
    return 0 if ok else (action_exit if action_exit != 0 else 1)


def command_request_stop(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.manifest.resolve())
    stop_path = manifest_path(manifest["state_dir"], "state_dir") / "native-auto-run.stop"
    if stop_path.exists():
        raise FileExistsError(f"stale or active stop request already exists: {stop_path}")
    stop_path.write_text("stop\n", encoding="utf-8")
    print(json.dumps({"ok": True, "stop_request": str(stop_path)}))
    return 0


def tasklist_ck3() -> list[dict[str, str]]:
    if sys.platform != "win32":
        return []
    completed = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq ck3.exe", "/FO", "CSV", "/NH"],
        check=False,
        capture_output=True,
        text=True,
    )
    rows = []
    for row in csv.reader(completed.stdout.splitlines()):
        if row and row[0].casefold() == "ck3.exe":
            rows.append({"image": row[0], "pid": row[1], "memory": row[4] if len(row) > 4 else ""})
    return rows


def _owned_ck3_inventory(source_repo: Path) -> tuple[dict[str, Any], Any]:
    source_path = str(source_repo / "ck3_autonomous_player" / "src")
    if source_path not in sys.path:
        sys.path.insert(0, source_path)
    from xar_autoplayer.environment import (  # noqa: PLC0415
        ck3_process_inventory,
        same_process_creation_time,
    )

    return ck3_process_inventory(), same_process_creation_time


def _owned_ck3_window_states(pid: int) -> dict[int, bool]:
    import win32gui
    import win32process

    states: dict[int, bool] = {}

    def collect(hwnd: int, _extra: object) -> bool:
        if win32gui.IsWindowVisible(hwnd):
            _thread, window_pid = win32process.GetWindowThreadProcessId(hwnd)
            if int(window_pid) == pid:
                states[int(hwnd)] = bool(win32gui.IsIconic(hwnd))
        return True

    win32gui.EnumWindows(collect, None)
    return states


def _minimize_owned_ck3_windows(handles: list[int]) -> None:
    import win32con
    import win32gui

    for handle in handles:
        win32gui.ShowWindow(handle, win32con.SW_MINIMIZE)


def command_owned_window(args: argparse.Namespace) -> int:
    """Observe or minimize only the CK3 process owned by this live state."""
    if sys.platform != "win32":
        raise RuntimeError("owned-window requires Windows")
    manifest = load_manifest(args.manifest.resolve())
    state_dir = manifest_path(manifest["state_dir"], "state_dir")
    control = read_json(state_dir / "control" / "ck3.json")
    expected_exe = (
        manifest_path(manifest["game_dir"], "game_dir") / "binaries" / "ck3.exe"
    ).resolve()
    if (
        control.get("ck3_pid") != args.expected_pid
        or control.get("creation_date") != args.expected_creation_date
        or Path(str(control.get("executable", ""))).resolve() != expected_exe
    ):
        raise RuntimeError("owned-window live control identity differs")
    inventory, same_creation = _owned_ck3_inventory(
        manifest_path(manifest["source_repo"], "source_repo")
    )
    processes = inventory.get("processes", [])
    if len(processes) != 1:
        raise RuntimeError("owned-window requires exactly one live CK3 process")
    process = processes[0]
    if (
        int(process.get("pid", 0)) != args.expected_pid
        or str(process.get("name", "")).casefold() != "ck3.exe"
        or not same_creation(
            process.get("creation_date"), args.expected_creation_date
        )
        or (
            process.get("executable")
            and Path(str(process["executable"])).resolve() != expected_exe
        )
    ):
        raise RuntimeError("owned-window process inventory identity differs")
    before = _owned_ck3_window_states(args.expected_pid)
    if not before:
        raise RuntimeError("owned-window has no visible CK3 top-level window")
    if args.minimize:
        _minimize_owned_ck3_windows(list(before))
    after = _owned_ck3_window_states(args.expected_pid)
    if not after or (args.minimize and not all(after.values())):
        raise RuntimeError("owned-window state could not be verified")
    print(json.dumps({
        "ok": True,
        "pid": args.expected_pid,
        "creation_date": args.expected_creation_date,
        "action": "minimize" if args.minimize else "status",
        "before_minimized": all(before.values()),
        "after_minimized": all(after.values()),
        "window_count": len(after),
    }))
    return 0


def command_status(args: argparse.Namespace) -> int:
    report_path = args.report.resolve()
    report: Any = None
    if report_path.is_file():
        text = report_path.read_text(encoding="utf-8-sig")
        try:
            report = json.loads(text)
        except json.JSONDecodeError:
            report = {"unparsed_report": str(report_path), "bytes": report_path.stat().st_size}
    summary = {"report": report, "ck3_processes": tasklist_ck3()}
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)

    verify_zip = commands.add_parser("verify-zip")
    verify_zip.add_argument("--zip", type=Path, required=True)
    verify_zip.add_argument("--expected-sha256", required=True)
    verify_zip.set_defaults(handler=command_verify_zip)

    prepare = commands.add_parser("prepare-state")
    prepare.add_argument("--manifest", type=Path, required=True)
    prepare.add_argument("--sample-dir", type=Path, required=True)
    prepare.add_argument("--construction-sidecar", type=Path)
    prepare.add_argument("--family-sidecar", type=Path)
    prepare.add_argument("--family-proof-report", type=Path, action="append")
    prepare.add_argument("--child-matrilineal-sidecar", type=Path)
    prepare.add_argument("--child-matrilineal-proof-report", type=Path, action="append")
    prepare.add_argument("--child-matrilineal-continuation-report", type=Path)
    prepare.add_argument("--child-matrilineal-post-sway-result-report", type=Path)
    prepare.add_argument("--child-matrilineal-followup-result-report", type=Path,
                         action="append")
    prepare.add_argument("--faction-gift-sidecar", type=Path)
    prepare.add_argument("--sway-formal-sidecar", type=Path)
    prepare.add_argument("--sway-formal-applied-report", type=Path)
    prepare.set_defaults(handler=command_prepare_state)

    verify_life_dll = commands.add_parser("verify-private-lifestyle-dll")
    verify_life_dll.add_argument("--manifest", type=Path, required=True)
    verify_life_dll.set_defaults(handler=command_verify_private_lifestyle_dll)

    run = commands.add_parser("run")
    run.add_argument("--manifest", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--turns", type=int)
    run.add_argument("--timeout", type=int)
    run.add_argument("--readiness-timeout", type=int)
    run.add_argument("--exact-war-move-stop-contract", type=Path)
    run.add_argument("--exact-war-move-stop-sha256")
    run.add_argument(
        "--live-run-state-root", type=Path,
        help=f"persistent machine-local live-run allocator root; defaults to {STATE_ROOT_ENV}",
    )
    run.add_argument(
        "--private-lifestyle-formal-trial",
        action="store_true",
        help="enable the bounded unadvertised lifestyle focus/perk formal route",
    )
    run.add_argument(
        "--private-construction-formal-trial",
        action="store_true",
        help="enable the bounded unadvertised construction formal route",
    )
    run.add_argument(
        "--private-family-marriage-formal-trial",
        action="store_true",
        help="enable the bounded unadvertised first-heir marriage formal route",
    )
    run.add_argument(
        "--private-m5-joint-collector",
        action="store_true",
        help="enable the bounded unadvertised M5 peacetime proposal collector",
    )
    run.add_argument(
        "--private-prisoner-collection-observation",
        action="store_true",
        help="read one paused private prisoner collection without prisoner actions",
    )
    run.add_argument(
        "--private-active-scheme-sway-target", type=int,
        help="read one explicit sway target on a paused frame and stop before action",
    )
    run.add_argument(
        "--private-child-matrilineal-pending-read", type=int, nargs=2,
        metavar=("HEIR_ID", "CANDIDATE_ID"),
        help="cold-read one paired child proposal on a paused frame",
    )
    run.add_argument(
        "--private-child-matrilineal-pending-recovery", type=int, nargs=2,
        metavar=("HEIR_ID", "CANDIDATE_ID"),
        help="consume one paired pending child result through the formal LIFE route",
    )
    run.add_argument("--child-matrilineal-recovery-proof-report", type=Path,
                     action="append")
    run.add_argument("--child-matrilineal-recovery-continuation-report", type=Path)
    run.add_argument("--child-matrilineal-recovery-sway-sidecar", type=Path)
    run.add_argument("--child-matrilineal-recovery-sway-applied-report", type=Path)
    run.add_argument("--child-matrilineal-recovery-post-sway-result-report", type=Path)
    run.add_argument(
        "--private-active-scheme-sway-formal-trial", action="store_true",
        help="run the bounded, unadvertised Sway submit/receipt/recovery consumer",
    )
    run.add_argument(
        "--private-realm-law-paused-query", action="store_true",
        help="read current-player final realm-law terms on a paused frame",
    )
    run.add_argument(
        "--private-activity-planner-diag-query", action="store_true",
        help="read current-player planner metadata on a paused frame",
    )
    run.add_argument(
        "--private-activity-feast-planner-open", action="store_true",
        help="open the private feast planner on one paused frame without starting it",
    )
    run.add_argument(
        "--private-activity-feast-stage1-option-read", action="store_true",
        help="open feast then read its selected stage-1 option on one paused frame",
    )
    run.add_argument(
        "--private-activity-feast-stage1-confirm", action="store_true",
        help="confirm one legal feast stage-1 option then independently read stage 2",
    )
    run.add_argument(
        "--private-activity-feast-stage2-gate-read", action="store_true",
        help="after private stage-1 Confirm, read the native stage-2 gate",
    )
    run.add_argument(
        "--private-activity-feast-stage2-location-province", type=int,
        action="append",
        help="after private stage-1 Confirm, query native destination legality for one province (repeat up to eight times)",
    )
    run.add_argument(
        "--private-activity-cost-slot12-raw-read", action="store_true",
        help="read one passive raw slot-12 capture; may combine with feast planner open",
    )
    run.add_argument(
        "--require-initial-lifestyle-focus-before-date-advance",
        action="store_true",
        help="stop the bounded run if focus is not verified and consumed before time moves",
    )
    run.add_argument(
        "--private-faction-round-id",
        type=private_faction_round_id,
        help=(
            "enable the bounded unadvertised faction-gift formal route for "
            "the allocated CK3 ownership round"
        ),
    )
    run.set_defaults(handler=command_run)

    timeline_query = commands.add_parser(
        "query-current-timeline-blocker-context-v1"
    )
    timeline_query.add_argument("--manifest", type=Path, required=True)
    timeline_query.add_argument("--output", type=Path, required=True)
    timeline_query.add_argument("--timeout", type=int)
    timeline_query.add_argument("--readiness-timeout", type=int)
    timeline_query.add_argument(
        "--private-timeline-query-round-id",
        type=private_timeline_query_round_id,
        required=True,
        help=(
            "enable the bounded unadvertised read-only query for the allocated "
            "monotonic CK3 ownership round"
        ),
    )
    timeline_query.set_defaults(
        handler=command_query_current_timeline_blocker_context_v1
    )

    family_alliance_query = commands.add_parser(
        "query-first-heir-marriage-alliance-result-v1")
    family_alliance_query.add_argument("--manifest", type=Path, required=True)
    family_alliance_query.add_argument("--output", type=Path, required=True)
    family_alliance_query.add_argument("--proposal-report", type=Path, required=True)
    family_alliance_query.add_argument("--proposal-report-sha256", required=True)
    family_alliance_query.add_argument("--recipient-character-id", type=int,
                                       required=True)
    family_alliance_query.add_argument("--ownership-round-id",
                                       type=private_family_alliance_round_id,
                                       required=True)
    family_alliance_query.add_argument("--timeout", type=int)
    family_alliance_query.add_argument("--readiness-timeout", type=int)
    family_alliance_query.set_defaults(
        handler=command_query_first_heir_marriage_alliance_result_v1)

    timeline_action = commands.add_parser(
        "continue-death-succession-modal-v1"
    )
    timeline_action.add_argument("--manifest", type=Path, required=True)
    timeline_action.add_argument("--output", type=Path, required=True)
    timeline_action.add_argument("--timeout", type=int)
    timeline_action.add_argument("--readiness-timeout", type=int)
    timeline_action.add_argument(
        "--private-timeline-action-round-id",
        type=private_timeline_action_round_id,
        required=True,
        help=(
            "enable the single bounded unadvertised typed Close for the "
            "allocated monotonic CK3 ownership round"
        ),
    )
    timeline_action.add_argument(
        "--expected-date-raw",
        type=int,
        required=True,
        help="bind the sealed R777 source date (53411568)",
    )
    timeline_action.set_defaults(
        handler=command_continue_death_succession_modal_v1
    )

    request_stop = commands.add_parser("request-stop")
    request_stop.add_argument("--manifest", type=Path, required=True)
    request_stop.set_defaults(handler=command_request_stop)

    status = commands.add_parser("status")
    status.add_argument("--report", type=Path, required=True)
    status.set_defaults(handler=command_status)

    owned_window = commands.add_parser("owned-window")
    owned_window.add_argument("--manifest", type=Path, required=True)
    owned_window.add_argument("--expected-pid", type=int, required=True)
    owned_window.add_argument("--expected-creation-date", required=True)
    owned_window.add_argument("--minimize", action="store_true")
    owned_window.set_defaults(handler=command_owned_window)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        return int(args.handler(args))
    except Exception as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
