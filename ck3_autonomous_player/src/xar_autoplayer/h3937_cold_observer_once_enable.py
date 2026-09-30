"""One fresh, isolated H3937 cold-load-observer read-only entry.

Only an external, reviewed GO receipt can admit this one managed session. The
three underlying module gates are enabled in memory for the call and restored in
all outcomes. This module never authorizes a game date or gameplay action.
"""

from __future__ import annotations

import hashlib
import json
import os
import ctypes
import importlib
from pathlib import Path
import re
import secrets
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone

from . import h3937_combined_paused_war_scope_run as outer
from . import h3937_combined_readonly_queries as inner
from . import h3937_target_readonly_queries as target_reads
from .environment import EnvironmentSpec
from .runtime import NativeBridgeLaunchConfig


ROUND = "R3948"
LIVE_RUN_ID = "desktop-3fevhd2-1c74096080--vanilla--R0117"
LIVE_EXECUTION_ID = "2be36b8a-029f-4dc5-a017-ce7d0b3809d7"
PIPE = r"\\.\pipe\xar-g2-robert-1066-seed-66f926d"
TASK_BUS = Path(r"D:\workspace\.codex-task-bus")
BUS_CLI_SHA256 = "D6629F52EE098C709C5A85ADBC629F40E8B2724BE9CC1F29FAF48AF215E96121"
SCREEN_TASK_ID = "war-h3937-cold-observer-readonly-live-20260930-a14"
LEASE_MAX_AGE_SECONDS = 600
GO_MAX_AGE_SECONDS = 300
CLOCK_SKEW_SECONDS = 10
NO_LAUNCH = Path(r"D:\ck3-research-artifacts\war-h3937-combined-no-launch-20260930\attempt-14")
FROZEN_PYTHON = Path(r"D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe")
FROZEN_PYTHON_VERSION = "Python 3.14.7"
STATE = NO_LAUNCH / "state"
OUTPUT = Path(r"D:\ck3-research-artifacts\war-h3937-combined-live-20260930\attempt-14")
GO = OUTPUT.parent / "go-attempt-14.json"
SCREEN = OUTPUT.parent / "screen-attempt-14"
LIVE_IDENTITY = NO_LAUNCH / "live-run-identity.json"
GAME = Path(r"C:\SteamLibrary\steamapps\common\Crusader Kings III")
DLL = NO_LAUNCH / "source-verified" / "xar_ck3_bridge.dll"
INJECTOR = NO_LAUNCH / "source-verified" / "xar_ck3_bridge_injector.exe"
SUPERVISOR_TIMEOUT_SECONDS = 2050
SUPERVISOR_HEARTBEAT_SECONDS = 120
RUN_CONFIG_PATH: Path | None = None
RUN_CONFIG_SHA256 = ""
RUN_CONFIG_BYTES = b""
INVENTORY_IMAGES = (
    "ck3.exe", "obs64.exe", "obs32.exe", "obs.exe", "ffmpeg.exe",
    "xar_ck3_bridge_injector.exe",
)


def _monotonic() -> float:
    return time.monotonic()


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _write_json(path: Path, value: dict[str, object]) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as target:
        target.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _time(value: object, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError as error:
        raise ValueError(f"invalid {label} time") from error
    if parsed.tzinfo is None:
        raise ValueError(f"unqualified {label} time")
    return parsed.astimezone(timezone.utc)


def _recent(value: object, label: str, limit_seconds: int, now: datetime) -> datetime:
    observed = _time(value, label)
    age = (now - observed).total_seconds()
    if age < -CLOCK_SKEW_SECONDS or age > limit_seconds:
        raise ValueError(f"stale or future {label}")
    return observed


def _git(*args: str) -> str:
    checkout = Path(__file__).resolve().parents[3]
    result = subprocess.run(["git", *args], cwd=checkout, capture_output=True,
                            text=True, check=True, timeout=30)
    return result.stdout.strip()


def _image_inventory(image: str) -> dict[str, object]:
    result = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {image}",
                             "/FO", "CSV"], capture_output=True, timeout=30)
    raw = result.stdout.decode("utf-8", errors="replace")
    return {"image": image, "returncode": result.returncode,
            "found": image.casefold() in raw.casefold(), "raw": raw}


def _require_zero_live_inventory() -> dict[str, dict[str, object]]:
    inventory = {image: _image_inventory(image) for image in INVENTORY_IMAGES}
    if any(item["returncode"] != 0 or item["found"] is not False
           for item in inventory.values()):
        raise ValueError("one-shot live process inventory not empty or unavailable")
    return inventory


def _require_pipe_server_absent() -> None:
    """Refuse a leftover server on the exact source-pair pipe name."""
    if os.name != "nt":
        raise RuntimeError("named-pipe absence check requires Windows")
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    wait = kernel32.WaitNamedPipeW
    wait.argtypes = (ctypes.c_wchar_p, ctypes.c_uint32)
    wait.restype = ctypes.c_int
    if wait(PIPE, 0):
        raise RuntimeError("source-pair pipe server already exists")
    error = ctypes.get_last_error()
    if error != 2:  # ERROR_FILE_NOT_FOUND; busy or inaccessible is RED.
        raise RuntimeError(f"source-pair pipe state unavailable: winerror={error}")


def _require_live_screen_lease(expected_sequence: object | None = None) -> dict[str, object]:
    """Read the main cooperative bus, never a worktree-relative bus copy."""
    if not TASK_BUS.is_dir() or not (TASK_BUS / "tasks").is_dir():
        raise ValueError("main task bus unavailable")
    now = datetime.now(timezone.utc)
    owners = []
    for path in (TASK_BUS / "tasks").glob("*.json"):
        if path.is_symlink():
            raise ValueError("screen task snapshot link is unavailable")
        snapshot = _read_json(path)
        resources = snapshot.get("resources")
        if type(resources) is not list or any(type(item) is not str for item in resources):
            raise ValueError("screen task resources are invalid")
        if "ck3-screen:acquired" not in resources:
            continue
        if resources != ["ck3-screen:acquired"] or snapshot.get("task_id") != path.stem:
            raise ValueError("unreleased screen record is malformed")
        updated = _time(snapshot.get("updated_at_utc"), "screen task")
        age = (now - updated).total_seconds()
        if (age < -CLOCK_SKEW_SECONDS or age > LEASE_MAX_AGE_SECONDS
                or snapshot.get("state") != "running"):
            raise ValueError("unreleased stale or nonrunning screen record blocks this attempt")
        owners.append(snapshot)
    if len(owners) != 1 or owners[0].get("task_id") != SCREEN_TASK_ID:
        raise ValueError("current ck3-screen task is not uniquely owned by this attempt")
    owner = owners[0]
    sequence = owner.get("last_sequence")
    if (owner.get("schema") != "codex.task_bus.v1"
            or owner.get("state") != "running"
            or type(sequence) is not int or sequence <= 0
            or (expected_sequence is not None and sequence != expected_sequence)):
        raise ValueError("current ck3-screen task state or sequence changed")
    return owner


def _require_bus_cli_pair() -> Path:
    checkout = Path(__file__).resolve().parents[3]
    source = checkout / "tools" / "codex_task_bus.py"
    installed = TASK_BUS / "bin" / "codex_task_bus.py"
    if (not source.is_file() or not installed.is_file()
            or source.is_symlink() or installed.is_symlink()
            or _sha(source) != BUS_CLI_SHA256
            or _sha(installed) != BUS_CLI_SHA256):
        raise ValueError("authoritative task-bus CLI source/install bytes differ")
    return source


def _managed_screen_heartbeat() -> None:
    """Renew the exact main-bus lease while a long cold load is supervised."""
    owner = _require_live_screen_lease()
    sequence = owner["last_sequence"]
    source = _require_bus_cli_pair()
    try:
        result = subprocess.run(
            [sys.executable, str(source),
             "--bus-dir", str(TASK_BUS),
             "--expected-cli-sha256", BUS_CLI_SHA256, "heartbeat",
             "--task", SCREEN_TASK_ID,
             "--expected-sequence", str(sequence),
             "--repo", str(Path(__file__).resolve().parents[3])],
            capture_output=True, text=True, check=False, timeout=30)
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("managed screen heartbeat timed out") from error
    if result.returncode != 0 or result.stderr:
        raise RuntimeError("managed screen heartbeat CAS refused or emitted stderr")
    try:
        receipt = json.loads(result.stdout)
        event = receipt["event"]
        task = receipt["task"]
        renewed_sequence = event["sequence"]
    except (ValueError, KeyError, TypeError) as error:
        raise RuntimeError("managed screen heartbeat CAS receipt unavailable") from error
    if (receipt.get("ok") is not True
            or event.get("kind") != "heartbeat"
            or event.get("task_id") != SCREEN_TASK_ID
            or type(renewed_sequence) is not int
            or renewed_sequence <= sequence
            or task.get("task_id") != SCREEN_TASK_ID
            or task.get("state") != "running"
            or task.get("resources") != ["ck3-screen:acquired"]
            or task.get("last_sequence") != renewed_sequence):
        raise RuntimeError("managed screen heartbeat CAS result differs")
    _require_bus_cli_pair()
    _require_live_screen_lease(renewed_sequence)


def issue_screen_challenge(entry_path: Path) -> dict[str, object]:
    """After screen acquisition, create a unique pre-capture challenge only."""
    entry = _require_entry_blob(entry_path)
    owner = _require_live_screen_lease()
    if not SCREEN.is_dir():
        raise ValueError("new screen attempt directory missing")
    challenge = {
        "schema": "xar.war.h3937-cold-observer-screen-challenge.v1",
        "issued_at_utc": _now(), "challenge_nonce": secrets.token_hex(24),
        "candidate_head": entry["head"], "round": ROUND,
        "live_run_id": LIVE_RUN_ID,
        "screen_attempt_dir": str(SCREEN.resolve()),
        "task_bus_dir": str(TASK_BUS.resolve()),
        "screen_task_id": SCREEN_TASK_ID,
        "screen_task_last_sequence": owner["last_sequence"],
    }
    _write_json(SCREEN / "screen-challenge.json", challenge)
    return challenge


def _require_entry_blob(entry_path: Path) -> dict[str, str]:
    if RUN_CONFIG_PATH is None:
        raise ValueError("an explicit new H3937 run config is required")
    checkout = Path(__file__).resolve().parents[3]
    entry = entry_path.resolve()
    if _git("status", "--porcelain=v1", "--untracked-files=all"):
        raise ValueError("one-shot checkout is dirty")
    try:
        relative = entry.relative_to(checkout.resolve()).as_posix()
    except ValueError as error:
        raise ValueError("one-shot entry outside exact checkout") from error
    head = _git("rev-parse", "HEAD")
    blob = _git("hash-object", "--", str(entry))
    if blob != _git("rev-parse", "--verify", f"{head}:{relative}"):
        raise ValueError("one-shot direct entry differs from HEAD")
    return {"head": head, "entry_blob": blob, "entry_sha256": _sha(entry)}


def _source_blob_identity() -> tuple[str, dict[str, str]]:
    """Recompute the exact producer and every current source module blob."""
    paths = {"producer_module": Path(outer.__file__)}
    for name in outer._SOURCE_MODULES:
        module = importlib.import_module(name, package=outer.__package__)
        if not isinstance(module.__file__, str):
            raise ValueError(f"source module has no file: {name}")
        paths[f"source_module_{name}"] = Path(module.__file__)
    return outer._clean_checkout_and_blob_identity(paths)


def _require_exact_admission() -> dict[str, object]:
    actual_version = (
        f"Python {sys.version_info.major}.{sys.version_info.minor}."
        f"{sys.version_info.micro}"
    )
    if (Path(sys.executable).resolve() != FROZEN_PYTHON.resolve()
            or actual_version != FROZEN_PYTHON_VERSION):
        raise ValueError("one-shot interpreter differs from frozen main venv")
    if not all(
        isinstance(value, str) and re.fullmatch(r"[0-9a-fA-F]{64}", value)
        for value in (outer.COMBINED_DLL_SHA256, outer.COMBINED_INJECTOR_SHA256)
    ):
        raise ValueError("exact Release binary pins are not frozen")
    if _git("status", "--porcelain=v1", "--untracked-files=all"):
        raise ValueError("one-shot checkout is dirty")
    head = _git("rev-parse", "HEAD")
    self_rel = Path(__file__).resolve().relative_to(Path(__file__).resolve().parents[3]).as_posix()
    if _git("hash-object", "--", str(Path(__file__).resolve())) != _git(
        "rev-parse", "--verify", f"{head}:{self_rel}"
    ):
        raise ValueError("one-shot entry bytes differ from HEAD")
    admission_path = NO_LAUNCH / "admission.json"
    manifest_path = NO_LAUNCH / "operator-manifest.json"
    admission = _read_json(admission_path)
    manifest = _read_json(manifest_path)
    live_identity = _read_json(LIVE_IDENTITY)
    live_identity_sha256 = _sha(LIVE_IDENTITY)
    if not (
        live_identity.get("schema") == "xar.ck3-live-run-identity.v1"
        and live_identity.get("run_id") == LIVE_RUN_ID
        and live_identity.get("execution_id") == LIVE_EXECUTION_ID
        and live_identity.get("machine_id") == "desktop-3fevhd2-1c74096080"
        and live_identity.get("mod_key") == "vanilla"
        and live_identity.get("sequence") == 117
        and admission.get("schema")
            == "xar.war.h3937-cold-observer-disabled-no-launch-admission.v1"
        and admission.get("candidate_head") == manifest.get("candidate_head") == head
        and admission.get("candidate_checkout_clean") is True
        and manifest.get("candidate_clean") is True
        and Path(str(manifest.get("python"))).resolve() == FROZEN_PYTHON.resolve()
        and manifest.get("python_version") == FROZEN_PYTHON_VERSION
        and admission.get("task_bus_cli_sha256") == BUS_CLI_SHA256
        and manifest.get("task_bus_cli_sha256") == BUS_CLI_SHA256
        and admission.get("live_run_id") == manifest.get("live_run_id")
            == LIVE_RUN_ID
        and admission.get("live_run_identity_sha256")
            == manifest.get("live_run_identity_sha256")
            == live_identity_sha256
        and admission.get("cold_load_observer_default_off") is True
        and admission.get("cold_load_observer_live_enabled") is False
        and manifest.get("cold_load_observer_default_off") is True
        and manifest.get("cold_load_observer_live_enabled") is False
        and Path(str(admission.get("prepared_state"))).resolve() == STATE.resolve()
        and Path(str(manifest.get("state_dir"))).resolve() == STATE.resolve()
        and manifest.get("bridge_pipe") == PIPE
        and Path(str(manifest.get("bridge_dll"))).resolve() == DLL.resolve()
        and Path(str(manifest.get("bridge_injector"))).resolve() == INJECTOR.resolve()
        and Path(str(manifest.get("game_dir"))).resolve() == GAME.resolve()
        and admission.get("episode_run_id") == "native-29829-2bc2d599f7f9"
        and admission.get("actor") == 29829
        and admission.get("date_raw") == 53219928
        and admission.get("history_index") == 3937
        and admission.get("raw_driver_sha256")
            == "2F0673EC4D0AFA2A77DE59FE9405EC032CF00F79D9484BBD3DC4361EC1311722"
        and manifest.get("source_raw_driver_sha256")
            == admission.get("raw_driver_sha256")
        and manifest.get("source_checkpoint_sha256")
            == "92A06F540E98A767D3E1DB95A6F3870674E0A7F084C2A14BD2D04D354E53DAF6"
        and manifest.get("source_child_sidecar_sha256")
            == "798F16F572FB83399CC9AB7ABD16561E87C47CEF7109CF23D255DAE660A8D8A7"
        and manifest.get("prepared_driver_sha256")
            == admission.get("prepared_driver_sha256")
        and manifest.get("rebind_receipt_sha256")
            == admission.get("official_rebind_receipt_sha256")
        and manifest.get("preflight_report_sha256")
            == admission.get("official_preflight_report_sha256")
        and manifest.get("environment_sha256")
            == admission.get("environment_sha256")
        and admission.get("dll_sha256") == outer.COMBINED_DLL_SHA256
        and admission.get("injector_sha256") == outer.COMBINED_INJECTOR_SHA256
        and admission.get("combined_outer_hard_gate") is False
        and admission.get("combined_inner_hard_gate") is False
        and admission.get("target_inner_hard_gate") is False
        and admission.get("ck3_launch_attempted") is False
        and admission.get("live_authorized") is False
        and manifest.get("outer_hard_gate") is False
        and manifest.get("inner_hard_gate") is False
        and manifest.get("target_hard_gate") is False
        and manifest.get("ck3_launch_attempted") is False
        and manifest.get("live_output_created") is False
        and isinstance(manifest.get("source_git_blobs"), dict)
        and len(manifest["source_git_blobs"]) == 16
        and "source_module_.h3937_cold_load_observer"
            in manifest["source_git_blobs"]
    ):
        raise ValueError("one-shot no-launch identity mismatch")
    _require_bus_cli_pair()
    blob_head, actual_blobs = _source_blob_identity()
    if blob_head != head or manifest["source_git_blobs"] != actual_blobs:
        raise ValueError("one-shot source Git blobs differ from candidate HEAD")
    expected = {
        DLL: outer.COMBINED_DLL_SHA256,
        INJECTOR: outer.COMBINED_INJECTOR_SHA256,
        NO_LAUNCH / "source-verified" / "driver-state.json":
            "2F0673EC4D0AFA2A77DE59FE9405EC032CF00F79D9484BBD3DC4361EC1311722",
        NO_LAUNCH / "source-verified" / "xar_checkpoint.ck3":
            "92A06F540E98A767D3E1DB95A6F3870674E0A7F084C2A14BD2D04D354E53DAF6",
        NO_LAUNCH / "source-verified" / "player-child-matrilineal-formal-v1.json":
            "798F16F572FB83399CC9AB7ABD16561E87C47CEF7109CF23D255DAE660A8D8A7",
        STATE / "profile" / "save games" / "xar_checkpoint.ck3":
            "92A06F540E98A767D3E1DB95A6F3870674E0A7F084C2A14BD2D04D354E53DAF6",
        STATE / "player-child-matrilineal-formal-v1.json":
            "798F16F572FB83399CC9AB7ABD16561E87C47CEF7109CF23D255DAE660A8D8A7",
        STATE / "native-session" / "driver-state.json":
            str(admission.get("prepared_driver_sha256", "")),
        STATE / "ordinary-seed-rebind-v1.json":
            str(admission.get("official_rebind_receipt_sha256", "")),
        Path(str(admission.get("official_preflight_report"))):
            str(admission.get("official_preflight_report_sha256", "")),
    }
    if not all(_sha(path) == digest.upper() for path, digest in expected.items()):
        raise ValueError("one-shot prepared source asset hash mismatch")
    preflight_path = Path(str(admission["official_preflight_report"]))
    if not preflight_path.resolve().is_relative_to((STATE / "preflights").resolve()):
        raise ValueError("one-shot official preflight outside exact state")
    rebind = _read_json(STATE / "ordinary-seed-rebind-v1.json")
    if not (
        rebind.get("ok") is True and rebind.get("status") == "rebound"
        and rebind.get("ck3_launch_attempted") is False
        and rebind.get("desktop_interaction") is False
        and rebind.get("pipe_name") == PIPE
        and Path(str(rebind.get("state_dir"))).resolve() == STATE.resolve()
        and rebind.get("environment", {}).get("target_sha256")
            == admission.get("environment_sha256")
        and str(rebind.get("driver_state", {}).get("target_sha256", "")).upper()
            == str(admission.get("prepared_driver_sha256", "")).upper()
    ):
        raise ValueError("one-shot official rebind contract mismatch")
    preflight = _read_json(preflight_path)
    anchor = preflight.get("resume_anchor")
    if not (
        preflight.get("status") == "ready" and preflight.get("ok") is True
        and preflight.get("ck3_launch_attempted") is False
        and preflight.get("desktop_interaction") is False
        and preflight.get("process_inventory", {}).get("processes") == []
        and isinstance(anchor, dict)
        and anchor.get("checkpoint", {}).get("saved_date_raw") == 53219928
        and anchor.get("checkpoint", {}).get("history_index") == 3937
        and anchor.get("driver_state", {}).get("episode_character_id") == 29829
        and anchor.get("driver_state", {}).get("episode_run_id")
            == "native-29829-2bc2d599f7f9"
        and anchor.get("checkpoint", {}).get("succession_lifecycle")
            == anchor.get("driver_state", {}).get("succession_lifecycle")
        and anchor.get("checkpoint", {}).get("succession_lifecycle", {}).get("lifecycle")
            == "ordinary_campaign_succession"
        and anchor.get("checkpoint", {}).get("succession_lifecycle", {}).get("xar_enabled")
            == "xar_off"
        and anchor.get("checkpoint", {}).get("succession_lifecycle", {}).get("pact_contract")
            == "absent_by_fresh_campaign_xar_off_contract"
        and anchor.get("checkpoint", {}).get("succession_lifecycle", {}).get("environment_sha256")
            == admission.get("environment_sha256")
        and preflight.get("profile", {}).get("environment_sha256")
            == admission.get("environment_sha256")
        and str(preflight.get("profile", {}).get("ck3_executable_sha256", "")).upper()
            == _sha(GAME / "binaries" / "ck3.exe")
    ):
        raise ValueError("one-shot official preflight contract mismatch")
    if (outer.H3937_COMBINED_OUTER_LIVE_AUTHORIZED is not False
            or inner.H3937_COMBINED_LIVE_AUTHORIZED is not False
            or target_reads.H3937_TARGET_LIVE_AUTHORIZED is not False):
        raise ValueError("combined candidate gates already enabled")
    if not (
        _sha(DLL) == str(manifest.get("bridge_dll_sha256", "")).upper()
        and _sha(INJECTOR) == str(manifest.get("bridge_injector_sha256", "")).upper()
    ):
        raise ValueError("one-shot manifest binary SHA mismatch")
    return {"head": head, "admission_sha256": _sha(admission_path),
            "manifest_sha256": _sha(manifest_path),
            "preflight_sha256": _sha(Path(str(admission["official_preflight_report"]))),
            "rebind_sha256": _sha(STATE / "ordinary-seed-rebind-v1.json"),
            "live_run_identity_sha256": live_identity_sha256}


def _require_go(identity: dict[str, object]) -> tuple[dict[str, object], str]:
    raw_go = GO.read_bytes()
    go_sha = hashlib.sha256(raw_go).hexdigest().upper()
    go = json.loads(raw_go.decode("utf-8"))
    if not isinstance(go, dict):
        raise ValueError("one-shot GO receipt is not a JSON object")
    if not (
        go.get("schema") == "xar.war.h3937-cold-observer-once-go.v1"
        and go.get("decision") == "GO_READ_ONLY_H3937_COMBINED"
        and go.get("candidate_head") == identity["head"]
        and go.get("round") == ROUND
        and go.get("live_run_id") == LIVE_RUN_ID
        and go.get("live_run_identity_sha256")
            == identity["live_run_identity_sha256"]
        and go.get("cold_load_observer_enabled") is True
        and go.get("cold_load_observer_dir")
            == str((OUTPUT / "cold-load-observation").resolve())
        and Path(str(go.get("state_dir"))).resolve() == STATE.resolve()
        and Path(str(go.get("output_dir"))).resolve() == OUTPUT.resolve()
        and go.get("pipe") == PIPE
        and go.get("admission_sha256") == identity["admission_sha256"]
        and go.get("operator_manifest_sha256") == identity["manifest_sha256"]
        and go.get("preflight_sha256") == identity["preflight_sha256"]
        and go.get("rebind_sha256") == identity["rebind_sha256"]
        and Path(str(go.get("task_bus_dir"))).resolve() == TASK_BUS.resolve()
        and go.get("screen_task_id") == SCREEN_TASK_ID
        and type(go.get("screen_task_last_sequence")) is int
        and go.get("screen_attempt_dir") == str(SCREEN.resolve())
        and go.get("screen_lease_exclusive") is True
        and go.get("steam_offline_direct_visual_reviewed") is True
        and go.get("account_single_instance_clear") is True
        and go.get("ck3_zero_process_before") is True
        and go.get("recorder_zero_before") is True
        and go.get("authorized_scope") == "six_paused_readonly_queries"
        and type(go.get("maximum_query_actions")) is int
        and go.get("maximum_query_actions") == 6
    ):
        raise ValueError("one-shot external GO receipt missing or mismatched")
    owner = _require_live_screen_lease(go["screen_task_last_sequence"])
    for name in ("steam_original", "steam_frame_receipt", "screen_challenge",
                 "screen_lease_receipt"):
        path = Path(str(go.get(f"{name}_path")))
        if not path.resolve().is_relative_to(SCREEN.resolve()):
            raise ValueError(f"one-shot {name} outside exact screen attempt")
        if _sha(path) != str(go.get(f"{name}_sha256", "")).upper():
            raise ValueError(f"one-shot {name} bytes changed")
    if (Path(str(go["screen_challenge_path"])).resolve()
            != (SCREEN / "screen-challenge.json").resolve()
            or Path(str(go["screen_lease_receipt_path"])).resolve()
            != (SCREEN / "screen-lease-snapshot.json").resolve()):
        raise ValueError("one-shot screen challenge or lease copy path changed")
    if _read_json(Path(str(go["screen_lease_receipt_path"]))) != owner:
        raise ValueError("screen lease receipt differs from current task bus")
    now = datetime.now(timezone.utc)
    challenge = _read_json(Path(str(go["screen_challenge_path"])))
    frame = _read_json(Path(str(go["steam_frame_receipt_path"])))
    before_path = Path(str(frame.get("before_path")))
    if (not before_path.resolve().is_relative_to(SCREEN.resolve())
            or _sha(before_path) != frame.get("before_sha256")):
        raise ValueError("Steam before-frame bytes or attempt changed")
    if not (
        challenge.get("schema") == "xar.war.h3937-cold-observer-screen-challenge.v1"
        and challenge.get("candidate_head") == identity["head"]
        and challenge.get("round") == ROUND
        and challenge.get("live_run_id") == LIVE_RUN_ID
        and challenge.get("screen_attempt_dir") == str(SCREEN.resolve())
        and challenge.get("task_bus_dir") == str(TASK_BUS.resolve())
        and challenge.get("screen_task_id") == SCREEN_TASK_ID
        and challenge.get("screen_task_last_sequence") == owner["last_sequence"]
        and isinstance(challenge.get("challenge_nonce"), str)
        and len(challenge["challenge_nonce"]) == 48
        and all(ch in "0123456789abcdef" for ch in challenge["challenge_nonce"])
        and go.get("screen_challenge_nonce") == challenge["challenge_nonce"]
        and frame.get("schema") == "ck3.steam_fresh_desktop_frame.v1"
        and frame.get("moving_edge_changed") is True
        and isinstance(frame.get("pixel_difference_bbox"), list)
        and len(frame["pixel_difference_bbox"]) == 4
        and frame.get("before_sha256") != frame.get("moved_sha256")
        and frame.get("before_rect") != frame.get("moved_rect")
        and frame.get("restored_rect") == frame.get("before_rect")
        and not (isinstance(frame.get("clock_check"), dict)
                 and frame["clock_check"].get("clock_pixels_unchanged") is True)
        and Path(str(frame.get("moved_path"))).resolve()
            == Path(str(go["steam_original_path"])).resolve()
        and frame.get("moved_sha256") == go["steam_original_sha256"]
        and isinstance(frame.get("moved_identity"), dict)
        and frame["moved_identity"].get("sha256") == go["steam_original_sha256"]
        and Path(str(frame["moved_identity"].get("path"))).resolve()
            == Path(str(go["steam_original_path"])).resolve()
        and frame["moved_identity"].get("bytes")
            == Path(str(go["steam_original_path"])).stat().st_size
    ):
        raise ValueError("screen challenge or fresh Steam frame mismatched")
    challenge_at = _recent(challenge.get("issued_at_utc"), "screen challenge",
                           LEASE_MAX_AGE_SECONDS, now)
    capture_at = _recent(frame.get("captured_at_utc"), "Steam frame",
                         GO_MAX_AGE_SECONDS, now)
    review_binding = go.get("operator_direct_review_evidence")
    if not isinstance(review_binding, dict):
        raise ValueError("direct Steam review binding absent")
    review_path = Path(str(review_binding.get("review_receipt_path")))
    if (review_path.resolve() !=
            (SCREEN / "steam-offline-direct-review.json").resolve()
            or _sha(review_path) !=
                str(review_binding.get("review_receipt_sha256", "")).upper()
            or review_binding.get("latest_original_sha256")
                != go["steam_original_sha256"]):
        raise ValueError("direct Steam review bytes or path changed")
    review = _read_json(review_path)
    if not (
        review.get("schema") == "xar.war.h3937-a14-steam-offline-direct-review.v1"
        and review.get("candidate_head") == identity["head"]
        and review.get("round") == ROUND
        and review.get("live_run_id") == LIVE_RUN_ID
        and review.get("screen_task_id") == SCREEN_TASK_ID
        and review.get("screen_challenge_nonce") == challenge["challenge_nonce"]
        and isinstance(review.get("reviewer"), str)
        and bool(review["reviewer"].strip())
        and review.get("steam_offline_direct_reviewed") is True
        and review.get("offline_indicator_text") == "离线模式"
        and Path(str(review.get("original_image"))).resolve()
            == Path(str(go["steam_original_path"])).resolve()
        and review.get("original_sha256") == go["steam_original_sha256"]
        and Path(str(review.get("freshness_receipt"))).resolve()
            == Path(str(go["steam_frame_receipt_path"])).resolve()
        and review.get("freshness_receipt_sha256")
            == go["steam_frame_receipt_sha256"]
        and review.get("screen_challenge_sha256")
            == go["screen_challenge_sha256"]
        and review.get("screen_lease_snapshot_sha256")
            == go["screen_lease_receipt_sha256"]
        and review.get("reviewed_at_utc")
            == go.get("steam_direct_reviewed_at_utc")
    ):
        raise ValueError("direct Steam review contents mismatched")
    review_at = _recent(go.get("steam_direct_reviewed_at_utc"), "direct Steam review",
                         GO_MAX_AGE_SECONDS, now)
    go_at = _recent(go.get("issued_at_utc"), "external GO",
                    GO_MAX_AGE_SECONDS, now)
    if not (challenge_at <= capture_at <= review_at <= go_at):
        raise ValueError("screen challenge, fresh frame, review, and GO out of order")
    if _sha(GO) != go_sha:
        raise ValueError("GO receipt bytes changed during validation")
    return go, go_sha


def _require_preworker_screen_gate(entry: dict[str, str]) -> None:
    """Refuse even worker creation until the exact current screen proof is valid."""
    identity = _require_exact_admission()
    if identity["head"] != entry["head"]:
        raise ValueError("preworker source HEAD changed")
    _require_go(identity)
    _require_zero_live_inventory()
    _require_pipe_server_absent()


def _require_no_launch_unchanged(identity: dict[str, object]) -> None:
    """Read back exact admission and allocator bytes after the native call."""
    admission_path = NO_LAUNCH / "admission.json"
    admission = _read_json(admission_path)
    bound = {
        LIVE_IDENTITY: identity["live_run_identity_sha256"],
        admission_path: identity["admission_sha256"],
        NO_LAUNCH / "operator-manifest.json": identity["manifest_sha256"],
        STATE / "ordinary-seed-rebind-v1.json": identity["rebind_sha256"],
        Path(str(admission["official_preflight_report"])):
            identity["preflight_sha256"],
    }
    if any(_sha(path) != digest for path, digest in bound.items()):
        raise ValueError("no-launch identity bytes changed")


def run_exact_once(claim_nonce: str) -> dict[str, object]:
    """Consume one exact output path; every failure remains as a RED attempt."""
    if not OUTPUT.is_dir():
        raise FileNotFoundError("one-shot supervisor claim directory missing")
    _write_json(OUTPUT / "worker-started.json", {
        "schema": "xar.war.h3937-cold-observer-worker-started.v1",
        "at_utc": _now(), "claim_nonce": claim_nonce,
        "live_run_id": LIVE_RUN_ID,
    })
    started = _now()
    primary_error: str | None = None
    outer_report: dict[str, object] | None = None
    identity: dict[str, object] | None = None
    go_sha: str | None = None
    go_attestation: dict[str, object] | None = None
    before: dict[str, object] | None = None
    after: dict[str, object] | None = None
    screen_lease_after: dict[str, object] | None = None
    original_outer = outer.H3937_COMBINED_OUTER_LIVE_AUTHORIZED
    original_inner = inner.H3937_COMBINED_LIVE_AUTHORIZED
    original_target = target_reads.H3937_TARGET_LIVE_AUTHORIZED
    try:
        claim = _read_json(OUTPUT / "supervisor-claim.json")
        if not (
            claim.get("schema") == "xar.war.h3937-cold-observer-supervisor-claim.v1"
            and claim.get("claim_nonce") == claim_nonce
            and claim.get("round") == ROUND
            and claim.get("live_run_id") == LIVE_RUN_ID
            and claim.get("run_config_sha256") == RUN_CONFIG_SHA256
            and Path(str(claim.get("output_dir"))).resolve() == OUTPUT.resolve()
            and claim.get("head") == _git("rev-parse", "HEAD")
        ):
            raise ValueError("one-shot supervisor claim mismatch")
        identity = _require_exact_admission()
        go_attestation, go_sha = _require_go(identity)
        before = _require_zero_live_inventory()
        _require_pipe_server_absent()
        _require_live_screen_lease(go_attestation["screen_task_last_sequence"])
        if _sha(GO) != go_sha:
            raise ValueError("GO receipt changed immediately before native session")
        _write_json(OUTPUT / "invocation.json", {
            "schema": "xar.war.h3937-cold-observer-once-invocation.v1",
            "at_utc": _now(), "round": ROUND, "candidate": identity,
            "live_run_id": LIVE_RUN_ID,
            "no_launch_path": str(NO_LAUNCH), "go_receipt_path": str(GO),
            "go_receipt_sha256": go_sha, "state_dir": str(STATE),
            "output_dir": str(OUTPUT), "pipe": PIPE, "dll": str(DLL),
            "injector": str(INJECTOR), "game_dir": str(GAME),
            "cold_load_observer_enabled": True,
            "cold_load_observer_dir": str(OUTPUT / "cold-load-observation"),
            "process_inventory_before": before,
            "date_move_attack_authorized": False,
        })
        outer.H3937_COMBINED_OUTER_LIVE_AUTHORIZED = True
        inner.H3937_COMBINED_LIVE_AUTHORIZED = True
        target_reads.H3937_TARGET_LIVE_AUTHORIZED = True
        try:
            outer_report = outer.collect_h3937_combined_paused_war_scope_once(
                EnvironmentSpec(state_dir=STATE, game_dir=GAME),
                ownership_round_id=ROUND, cold_start_checkpoint=True,
                readiness_timeout_screenshot_path=(
                    OUTPUT / "readiness-timeout-desktop.png"),
                readiness_timeout_screen_lease_check=_require_live_screen_lease,
                readiness_timeout_diagnostic_probe=True,
                readiness_stall_watchdog=True,
                cold_load_observation_dir=OUTPUT / "cold-load-observation",
                timeout_seconds=1890,
                readiness_timeout_seconds=1800,
                native_bridge=NativeBridgeLaunchConfig(
                    mode="native-headless", pipe_name=PIPE,
                    dll_path=DLL, injector_path=INJECTOR,
                ),
            )
        finally:
            outer.H3937_COMBINED_OUTER_LIVE_AUTHORIZED = original_outer
            inner.H3937_COMBINED_LIVE_AUTHORIZED = original_inner
            target_reads.H3937_TARGET_LIVE_AUTHORIZED = original_target
        _write_json(OUTPUT / "outer-report.json", outer_report)
    except BaseException as error:
        primary_error = f"{type(error).__name__}: {error}"
        with (OUTPUT / "error-traceback.txt").open("x", encoding="utf-8") as target:
            target.write(traceback.format_exc())
    finally:
        outer.H3937_COMBINED_OUTER_LIVE_AUTHORIZED = original_outer
        inner.H3937_COMBINED_LIVE_AUTHORIZED = original_inner
        target_reads.H3937_TARGET_LIVE_AUTHORIZED = original_target
        try:
            after = {image: _image_inventory(image) for image in INVENTORY_IMAGES}
        except BaseException as error:
            primary_error = primary_error or f"post inventory: {type(error).__name__}: {error}"
        try:
            if go_sha is not None and _sha(GO) != go_sha:
                primary_error = primary_error or "GO receipt bytes changed"
            if identity is not None:
                _require_no_launch_unchanged(identity)
            if go_attestation is not None:
                for name in ("steam_original", "steam_frame_receipt",
                             "screen_challenge", "screen_lease_receipt"):
                    path = Path(str(go_attestation[f"{name}_path"]))
                    if _sha(path) != str(go_attestation[f"{name}_sha256"]).upper():
                        primary_error = primary_error or f"{name} bytes changed"
                review_binding = go_attestation["operator_direct_review_evidence"]
                review_path = Path(str(review_binding["review_receipt_path"]))
                if _sha(review_path) != str(
                    review_binding["review_receipt_sha256"]
                ).upper():
                    primary_error = primary_error or "direct Steam review bytes changed"
                screen_lease_after = _require_live_screen_lease()
        except BaseException as error:
            primary_error = primary_error or f"GO/screen readback: {type(error).__name__}: {error}"
    cleanup = outer_report.get("cleanup") if isinstance(outer_report, dict) else None
    gates_restored = (
        outer.H3937_COMBINED_OUTER_LIVE_AUTHORIZED is original_outer is False
        and inner.H3937_COMBINED_LIVE_AUTHORIZED is original_inner is False
        and target_reads.H3937_TARGET_LIVE_AUTHORIZED is original_target is False
    )
    processes_gone = bool(after and all(
        item["returncode"] == 0 and item["found"] is False for item in after.values()
    ))
    green = bool(
        primary_error is None and isinstance(outer_report, dict)
        and outer_report.get("ok") is True
        and outer_report.get("status") == "GREEN_READ_ONLY_TARGET"
        and outer_report.get("action_authorized") is False
        and outer_report.get("date_advance_authorized") is False
        and outer_report.get("gameplay_actions") == 0
        and outer_report.get("query_actions") == 6
        and isinstance(cleanup, dict) and cleanup.get("ok") is True
        and gates_restored and processes_gone
    )
    completion = {
        "schema": "xar.war.h3937-cold-observer-once-completion.v1",
        "started_at_utc": started, "finished_at_utc": _now(),
        "round": ROUND, "live_run_id": LIVE_RUN_ID,
        "status": "GREEN_READ_ONLY" if green else "RED",
        "outer_report_path": str(OUTPUT / "outer-report.json")
            if (OUTPUT / "outer-report.json").is_file() else None,
        "outer_report_sha256": _sha(OUTPUT / "outer-report.json")
            if (OUTPUT / "outer-report.json").is_file() else None,
        "error": primary_error,
        "gates_restored": gates_restored,
        "process_inventory_after": after,
        "processes_gone": processes_gone,
        "screen_lease_after": screen_lease_after,
        "outer_cleanup_proven": isinstance(cleanup, dict) and cleanup.get("ok") is True,
        "action_authorized": False, "date_advance_authorized": False,
        "one_shot_output_consumed": True,
    }
    _write_json(OUTPUT / "completion.json", completion)
    return completion


def main(claim_nonce: str) -> int:
    completion = run_exact_once(claim_nonce)
    print(json.dumps(completion, ensure_ascii=True))
    return 0 if completion["status"] == "GREEN_READ_ONLY" else 1


def supervise_exact_once(entry_path: Path) -> int:
    """Bound the worker, retain stdio, and prove its process tree is gone."""
    if RUN_CONFIG_PATH is None:
        raise ValueError("an explicit new H3937 run config is required")
    OUTPUT.mkdir(parents=True, exist_ok=False)
    with (OUTPUT / "run-config.snapshot.json").open("xb") as snapshot:
        snapshot.write(RUN_CONFIG_BYTES)
    try:
        entry = _require_entry_blob(entry_path)
    except BaseException as error:
        _write_json(OUTPUT / "supervisor-completion.json", {
            "schema": "xar.war.h3937-cold-observer-once-supervisor.v1",
            "finished_at_utc": _now(), "status": "RED",
            "round": ROUND, "live_run_id": LIVE_RUN_ID,
            "prelaunch_source_refusal": f"{type(error).__name__}: {error}",
            "worker_started": False, "ck3_launch_attempted": False,
            "action_authorized": False, "date_advance_authorized": False,
            "one_shot_output_consumed": True,
        })
        return 1
    claim_nonce = secrets.token_hex(16)
    _write_json(OUTPUT / "supervisor-claim.json", {
        "schema": "xar.war.h3937-cold-observer-supervisor-claim.v1",
        "at_utc": _now(), "claim_nonce": claim_nonce,
        "parent_pid": os.getpid(), "round": ROUND,
        "live_run_id": LIVE_RUN_ID,
        "head": entry["head"], "entry_blob": entry["entry_blob"],
        "entry_sha256": entry["entry_sha256"],
        "output_dir": str(OUTPUT),
        "run_config_path": str(RUN_CONFIG_PATH),
        "run_config_sha256": RUN_CONFIG_SHA256,
    })
    started = _now()
    worker = None
    stdout = b""
    stderr = b""
    timeout = False
    supervisor_error: str | None = None
    kill_result: dict[str, object] | None = None

    def kill_tree(process: object) -> dict[str, object]:
        try:
            killed = subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                capture_output=True, check=False, timeout=30,
            )
            receipt = {
                "worker_pid": process.pid, "returncode": killed.returncode,
                "stdout": killed.stdout.decode("utf-8", errors="replace"),
                "stderr": killed.stderr.decode("utf-8", errors="replace"),
            }
            if killed.returncode != 0:
                try:
                    process.kill()
                    receipt["worker_fallback_kill_attempted"] = True
                except BaseException as error:
                    receipt["worker_fallback_kill_error"] = f"{type(error).__name__}: {error}"
            return receipt
        except BaseException as error:
            receipt = {"worker_pid": process.pid,
                       "error": f"{type(error).__name__}: {error}"}
            try:
                process.kill()
                receipt["worker_fallback_kill_attempted"] = True
            except BaseException as fallback_error:
                receipt["worker_fallback_kill_error"] = (
                    f"{type(fallback_error).__name__}: {fallback_error}")
            return receipt

    def reap_after_kill(process: object) -> None:
        """Collect worker tail bytes and prove exit after either kill path."""
        nonlocal stdout, stderr, supervisor_error
        try:
            later_stdout, later_stderr = process.communicate(timeout=30)
            stdout = later_stdout if later_stdout is not None else stdout
            stderr = later_stderr if later_stderr is not None else stderr
        except subprocess.TimeoutExpired as error:
            stdout = error.stdout or stdout
            stderr = error.stderr or stderr
            supervisor_error = (
                f"{supervisor_error or ''}; worker remained after bounded taskkill"
            ).lstrip("; ")
            try:
                process.kill()
                later_stdout, later_stderr = process.communicate(timeout=5)
                stdout = later_stdout if later_stdout is not None else stdout
                stderr = later_stderr if later_stderr is not None else stderr
            except BaseException as final_error:
                supervisor_error += (
                    f"; final worker reap: {type(final_error).__name__}: {final_error}")
        except BaseException as error:
            supervisor_error = (
                f"{supervisor_error or ''}; worker reap: {type(error).__name__}: {error}"
            ).lstrip("; ")

    try:
        _require_preworker_screen_gate(entry)
        worker = subprocess.Popen(
            [sys.executable, str(entry_path), "--config", str(RUN_CONFIG_PATH),
             "--worker", claim_nonce],
            cwd=entry_path.resolve().parent,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            supervisor_deadline = _monotonic() + SUPERVISOR_TIMEOUT_SECONDS
            while True:
                remaining = supervisor_deadline - _monotonic()
                if remaining <= 0:
                    raise subprocess.TimeoutExpired(worker.args, SUPERVISOR_TIMEOUT_SECONDS)
                try:
                    stdout, stderr = worker.communicate(
                        timeout=min(SUPERVISOR_HEARTBEAT_SECONDS, remaining))
                    break
                except subprocess.TimeoutExpired:
                    if _monotonic() >= supervisor_deadline:
                        raise
                    _managed_screen_heartbeat()
        except subprocess.TimeoutExpired as error:
            timeout = True
            stdout = error.stdout or b""
            stderr = error.stderr or b""
            kill_result = kill_tree(worker)
            reap_after_kill(worker)
    except BaseException as error:
        supervisor_error = f"{type(error).__name__}: {error}"
        if worker is not None:
            if worker.returncode is None and kill_result is None:
                kill_result = kill_tree(worker)
            reap_after_kill(worker)
    for name, data in (("stdout", stdout), ("stderr", stderr)):
        try:
            with (OUTPUT / f"supervisor.{name}.txt").open("x", encoding="utf-8") as target:
                target.write(data.decode("utf-8", errors="replace"))
        except BaseException as error:
            supervisor_error = supervisor_error or (
                f"supervisor {name} retention: {type(error).__name__}: {error}")
    after: dict[str, object] | None = None
    try:
        after = {image: _image_inventory(image) for image in INVENTORY_IMAGES}
    except BaseException as error:
        supervisor_error = supervisor_error or (
            f"post inventory: {type(error).__name__}: {error}")
    worker_exited = worker is not None and worker.returncode is not None
    kill_proven = not timeout or bool(
        kill_result and kill_result.get("returncode") == 0 and worker_exited)
    processes_gone = bool(after and worker_exited and kill_proven and all(
        item["returncode"] == 0 and item["found"] is False for item in after.values()
    ))
    child_completion_path = OUTPUT / "completion.json"
    child_completion = None
    try:
        if child_completion_path.is_file():
            child_completion = _read_json(child_completion_path)
    except BaseException as error:
        supervisor_error = supervisor_error or (
            f"child completion readback: {type(error).__name__}: {error}")
    child_report_path = OUTPUT / "outer-report.json"
    try:
        report_sha = _sha(child_report_path) if child_report_path.is_file() else None
    except BaseException as error:
        report_sha = None
        supervisor_error = supervisor_error or (
            f"outer report readback: {type(error).__name__}: {error}")
    ok = bool(
        not timeout and supervisor_error is None and worker is not None
        and worker.returncode == 0 and processes_gone
        and isinstance(child_completion, dict)
        and child_completion.get("status") == "GREEN_READ_ONLY"
        and child_completion.get("action_authorized") is False
        and child_completion.get("date_advance_authorized") is False
        and child_completion.get("outer_cleanup_proven") is True
        and child_completion.get("gates_restored") is True
        and child_completion.get("processes_gone") is True
        and report_sha is not None
        and child_completion.get("outer_report_sha256") == report_sha
    )
    def receipt_sha(path: Path) -> str | None:
        nonlocal supervisor_error, ok
        try:
            return _sha(path) if path.is_file() else None
        except BaseException as error:
            ok = False
            supervisor_error = supervisor_error or (
                f"supervisor receipt hash: {type(error).__name__}: {error}")
            return None

    stdout_sha = receipt_sha(OUTPUT / "supervisor.stdout.txt")
    stderr_sha = receipt_sha(OUTPUT / "supervisor.stderr.txt")
    completion_sha = receipt_sha(child_completion_path)
    if stdout_sha is None or stderr_sha is None or completion_sha is None:
        ok = False
    _write_json(OUTPUT / "supervisor-completion.json", {
        "schema": "xar.war.h3937-cold-observer-once-supervisor.v1",
        "started_at_utc": started, "finished_at_utc": _now(),
        "round": ROUND, "live_run_id": LIVE_RUN_ID,
        "status": "GREEN_READ_ONLY" if ok else "RED",
        "worker_pid": worker.pid if worker is not None else None,
        "worker_started": worker is not None,
        "worker_returncode": worker.returncode if worker is not None else None,
        "timeout": timeout, "timeout_seconds": SUPERVISOR_TIMEOUT_SECONDS,
        "taskkill": kill_result, "error": supervisor_error,
        "stdout_sha256": stdout_sha,
        "stderr_sha256": stderr_sha,
        "child_completion_sha256": completion_sha,
        "process_inventory_after": after, "processes_gone": processes_gone,
        "action_authorized": False, "date_advance_authorized": False,
    })
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
