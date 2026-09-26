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
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import Any


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
    is_pending = isinstance(pending, dict) and applied is None
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
    return request_id


def saved_in_progress_construction_without_sidecar(driver: dict[str, Any]) -> bool:
    """A saved material receipt needs its ledger for later completion checks."""

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
    return any(row["result"].get("completion_status") == "in_progress"
               for row in latest.values())


def run_logged(command: list[str], stdout_path: Path, stderr_path: Path) -> int:
    with stdout_path.open("w", encoding="utf-8", newline="") as stdout_stream:
        with stderr_path.open("w", encoding="utf-8", newline="") as stderr_stream:
            completed = subprocess.run(command, stdout=stdout_stream, stderr=stderr_stream, check=False)
    return completed.returncode


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
    require_initial_lifestyle_focus_before_date_advance: bool = False,
    succession_lifecycle: str = ROGUE_ONE_LIFE,
    ordinary_campaign_no_pact: bool = False,
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
    if private_lifestyle_formal_trial:
        command.append("--allow-private-lifestyle-formal-trial")
    if private_construction_formal_trial:
        command.append("--allow-private-construction-formal-trial")
    if private_family_marriage_formal_trial:
        command.append("--allow-private-family-marriage-formal-trial")
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
    save_target = state_dir / "profile" / "save games" / "xar_checkpoint.ck3"
    driver_target = state_dir / "native-session" / "driver-state.json"
    pending_target = state_dir / "construction-formal-pending-v1.json"
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
            "saved in-progress construction receipt requires --construction-sidecar "
            "or construction-formal-pending-v1.json in sample-dir"
        )
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
    print(json.dumps(preparation))
    return 0


def command_run(args: argparse.Namespace) -> int:
    if (
        args.require_initial_lifestyle_focus_before_date_advance
        and not args.private_lifestyle_formal_trial
    ):
        raise ValueError(
            "initial LIFE focus gate requires --private-lifestyle-formal-trial"
        )
    manifest = load_manifest(args.manifest.resolve())
    lifecycle = lifecycle_contract(manifest)
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(f"attempt output already exists: {output}")
    output.mkdir(parents=True)
    save, driver_path, driver = current_checkpoint_identity(manifest)
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
        "preflight_exit_code": preflight_exit,
        "lifecycle": lifecycle,
        "display_mode": display_mode_contract(manifest),
        "private_lifestyle_formal_trial": args.private_lifestyle_formal_trial,
        "private_construction_formal_trial": args.private_construction_formal_trial,
        "private_family_marriage_formal_trial": args.private_family_marriage_formal_trial,
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
    turns = args.turns if args.turns is not None else int(manifest.get("formal_turns", 20))
    timeout = args.timeout if args.timeout is not None else int(manifest.get("timeout_seconds", 390))
    readiness_timeout = args.readiness_timeout if args.readiness_timeout is not None else int(
        manifest.get("readiness_timeout_seconds", 300)
    )
    formal_report = output / "formal-report.txt"
    formal_stderr = output / "formal-stderr.txt"
    stop_path = manifest_path(manifest["state_dir"], "state_dir") / "native-auto-run.stop"
    print(f"Operator stop request file: {stop_path}", file=sys.stderr, flush=True)
    private_faction_round = args.private_faction_round_id
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
            require_initial_lifestyle_focus_before_date_advance=(
                args.require_initial_lifestyle_focus_before_date_advance
            ),
            succession_lifecycle=str(lifecycle["succession_lifecycle"]),
            ordinary_campaign_no_pact=(
                lifecycle["ordinary_campaign_no_pact"] is True
            ),
        ),
        formal_report,
        formal_stderr,
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
    prepare.set_defaults(handler=command_prepare_state)

    run = commands.add_parser("run")
    run.add_argument("--manifest", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--turns", type=int)
    run.add_argument("--timeout", type=int)
    run.add_argument("--readiness-timeout", type=int)
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
