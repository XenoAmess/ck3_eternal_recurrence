#!/usr/bin/env python3
"""Reusable MCP-owned AF5 terminal verification job.

The process is inert until the operator sends ``run-af5`` on stdin.  A live
failure is preserved paused and requires the explicit ``cleanup`` control. Execution roots and exact input
hashes come from the frozen activation, independent of a moving main checkout.
"""

from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import importlib
import json
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Callable, Mapping, Sequence


KIND = "zg361_af5_operator_activation_v1"
HASH_FIELDS = (
    "checkpoint_sha256", "product_tree_sha256", "projection_manifest_sha256",
    "bridge_dll_sha256", "game_exe_sha256", "vanilla_game_rules_sha256",
)
RESULT_EVENT = "zg361comp.1"
TERMINAL_OPTION = 42
TERMINAL_NATIVE_INDEX = 41
ROUND_RE = re.compile(r"R([1-9][0-9]*)")
SHA_RE = re.compile(r"[0-9A-Fa-f]{64}")
PIPE_RE = re.compile(r"\\\\\.\\pipe\\xar_ck3_bridge_zg361_[0-9a-f]{32}")
STARTUP_ASSETS = ("shadercache", "account", "dlc_signature")


class Af5JobError(RuntimeError):
    def __init__(self, message: str, evidence: Mapping[str, object] | None = None) -> None:
        super().__init__(message)
        self.evidence = copy.deepcopy(dict(evidence)) if evidence is not None else None


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def file_record(path: Path) -> dict[str, object]:
    resolved = path.expanduser().resolve()
    return {
        "path": str(resolved),
        "bytes": resolved.stat().st_size,
        "sha256": sha256(resolved),
    }


def read_object(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise Af5JobError(f"JSON is not an object: {path}")
    return value


def write_object(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def bootstrap_evidence_json_value(value: object) -> object:
    """Convert only the bootstrap evidence's known Path-bearing containers."""

    if isinstance(value, Path):
        return str(value)
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Mapping):
        converted: dict[str, object] = {}
        for key, child in value.items():
            if not isinstance(key, str):
                raise TypeError("bootstrap evidence mapping keys must be strings")
            converted[key] = bootstrap_evidence_json_value(child)
        return converted
    if isinstance(value, (list, tuple)):
        return [bootstrap_evidence_json_value(child) for child in value]
    raise TypeError(
        f"unsupported bootstrap evidence type: {type(value).__name__}"
    )


def mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise Af5JobError(f"{label} must be an object")
    return value


def positive_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise Af5JobError(f"{label} must be a positive integer")
    return value


def checked_file(value: object, label: str) -> Path:
    row = mapping(value, label)
    raw_path = row.get("path")
    expected_bytes = row.get("bytes")
    expected_sha = row.get("sha256")
    if not isinstance(raw_path, str) or not raw_path:
        raise Af5JobError(f"{label}.path is absent")
    path = Path(raw_path).expanduser()
    if not path.is_absolute() or not path.is_file():
        raise Af5JobError(f"{label} is not an absolute existing file: {path}")
    actual = file_record(path)
    if (
        isinstance(expected_bytes, bool)
        or not isinstance(expected_bytes, int)
        or actual["bytes"] != expected_bytes
        or not isinstance(expected_sha, str)
        or SHA_RE.fullmatch(expected_sha) is None
        or str(actual["sha256"]).casefold() != expected_sha.casefold()
    ):
        raise Af5JobError(f"{label} hash/size binding differs")
    return path.resolve()


def checked_directory(value: object, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise Af5JobError(f"{label} is absent")
    path = Path(value).expanduser()
    if not path.is_absolute() or not path.is_dir():
        raise Af5JobError(f"{label} is not an absolute existing directory: {path}")
    return path.resolve()


def ck3_pids() -> list[int]:
    """Read only the global CK3 process inventory."""

    if sys.platform != "win32":
        return []
    command = (
        "@(Get-Process -Name ck3 -ErrorAction SilentlyContinue | "
        "Select-Object -ExpandProperty Id) | ConvertTo-Json -Compress"
    )
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
        check=True,
        capture_output=True,
        text=True,
    )
    text = completed.stdout.strip()
    if not text:
        return []
    value = json.loads(text)
    values = value if isinstance(value, list) else [value]
    return sorted(int(item) for item in values)


def git_identity(repository_root: Path) -> dict[str, object]:
    head = subprocess.run(
        ["git", "-C", str(repository_root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    dirty = subprocess.run(
        ["git", "-C", str(repository_root), "status", "--porcelain", "--untracked-files=no"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return {"head": head, "tracked_dirty": bool(dirty)}


def _projection_identity(path: Path, expected_tree_sha256: str) -> dict[str, object]:
    projection = read_object(path)
    if (
        projection.get("schema_version") != 1
        or projection.get("kind") != "zg361_phase2_product_projection"
        or str(projection.get("source_tree_sha256", "")).upper()
        != expected_tree_sha256.upper()
    ):
        raise Af5JobError("production projection is not the required current tree")
    return projection


def validate_activation(
    activation_path: Path,
    *,
    process_probe: Callable[[], list[int]] = ck3_pids,
    require_empty_slot: bool,
) -> dict[str, object]:
    path = activation_path.expanduser().resolve()
    value = read_object(path)
    if value.get("schema_version") != 1 or value.get("kind") != KIND:
        raise Af5JobError("activation schema/kind differs")
    expected_hashes = mapping(value.get("expected_hashes"), "expected_hashes")
    expected: dict[str, str] = {}
    for name in HASH_FIELDS:
        candidate = expected_hashes.get(name)
        if not isinstance(candidate, str) or SHA_RE.fullmatch(candidate) is None:
            raise Af5JobError(f"expected_hashes.{name} must be a SHA-256")
        expected[name] = candidate.upper()
    code_commit = expected_hashes.get("code_commit")
    if not isinstance(code_commit, str) or re.fullmatch(r"[0-9a-fA-F]{40}", code_commit) is None:
        raise Af5JobError("expected_hashes.code_commit must be a full Git commit")
    expected["code_commit"] = code_commit.lower()
    rounds = mapping(value.get("rounds"), "rounds")
    if set(rounds) != {"frontend_warmup", "gameplay"}:
        raise Af5JobError("rounds must contain frontend_warmup and gameplay")
    warmup_round = rounds.get("frontend_warmup")
    gameplay_round = rounds.get("gameplay")
    warmup_match = ROUND_RE.fullmatch(warmup_round) if isinstance(warmup_round, str) else None
    gameplay_match = ROUND_RE.fullmatch(gameplay_round) if isinstance(gameplay_round, str) else None
    if (
        warmup_match is None
        or gameplay_match is None
        or int(gameplay_match.group(1)) != int(warmup_match.group(1)) + 1
    ):
        raise Af5JobError("gameplay round must immediately follow frontend warm-up round")
    repository_root = checked_directory(value.get("repository_root"), "repository_root")
    game_directory = checked_directory(value.get("game_directory"), "game_directory")
    product_root = checked_directory(value.get("product_root"), "product_root")
    startup_profile = checked_directory(
        value.get("startup_template_profile"), "startup_template_profile"
    )
    for relative in (
        "tools/run_zhongguo_acceptance.py",
        "tools/run_acceptance.py",
        "tools/zg361_phase2_af5_action_cell.py",
        "ck3_autonomous_player/src/xar_autoplayer/native_session.py",
    ):
        if not (repository_root / relative).is_file():
            raise Af5JobError(f"repository_root lacks {relative}")
    repository_identity = git_identity(repository_root)
    if repository_identity != {"head": expected["code_commit"], "tracked_dirty": False}:
        raise Af5JobError(f"repository identity differs: {repository_identity!r}")
    for name in ("pdx_settings.txt", "shadercache"):
        if not (startup_profile / name).exists():
            raise Af5JobError(f"startup template lacks {name}")
    checkpoint = checked_file(value.get("checkpoint"), "checkpoint")
    projection_path = checked_file(
        value.get("product_projection_manifest"), "product_projection_manifest"
    )
    if sha256(projection_path) != expected["projection_manifest_sha256"]:
        raise Af5JobError("production projection manifest differs")
    bridge_dll = checked_file(value.get("bridge_dll"), "bridge_dll")
    bridge_injector = checked_file(value.get("bridge_injector"), "bridge_injector")
    prior_cleanup = checked_file(value.get("prior_cleanup"), "prior_cleanup")
    game_exe = game_directory / "binaries" / "ck3.exe"
    if not game_exe.is_file() or sha256(game_exe) != expected["game_exe_sha256"]:
        raise Af5JobError("CK3 exact-build executable differs")
    vanilla_game_rules = checked_file(
        value.get("vanilla_game_rules"), "vanilla_game_rules"
    )
    expected_game_rules = (
        game_directory / "game" / "common" / "game_rules" / "00_game_rules.txt"
    ).resolve()
    if (
        vanilla_game_rules != expected_game_rules
        or sha256(vanilla_game_rules) != expected["vanilla_game_rules_sha256"]
    ):
        raise Af5JobError(
            "vanilla game rules are not hash-bound under the explicit game_directory"
        )
    if sha256(checkpoint) != expected["checkpoint_sha256"]:
        raise Af5JobError("AF5 source checkpoint differs")
    if sha256(bridge_dll) != expected["bridge_dll_sha256"]:
        raise Af5JobError("promotion-only bridge DLL differs")
    projection = _projection_identity(projection_path, expected["product_tree_sha256"])
    cleanup = read_object(prior_cleanup)
    if cleanup.get("result") != "GREEN" or cleanup.get("scope") != "phase2_managed_native_session_cleanup":
        raise Af5JobError("prior CK3 cleanup is not canonical GREEN")
    state_directory = Path(str(value.get("state_directory", ""))).expanduser()
    artifact_directory = Path(str(value.get("artifact_directory", ""))).expanduser()
    for output, label in (
        (state_directory, "state_directory"),
        (artifact_directory, "artifact_directory"),
    ):
        if not output.is_absolute():
            raise Af5JobError(f"{label} must be absolute")
        if require_empty_slot and output.exists():
            raise Af5JobError(f"fresh {label} must not exist")
    if state_directory.resolve() == artifact_directory.resolve():
        raise Af5JobError("state and artifact directories must differ")
    pipe = value.get("bridge_pipe")
    warmup_pipe = value.get("warmup_bridge_pipe")
    if not isinstance(pipe, str) or PIPE_RE.fullmatch(pipe) is None:
        raise Af5JobError("bridge_pipe must be a run-unique bridge pipe")
    if not isinstance(warmup_pipe, str) or PIPE_RE.fullmatch(warmup_pipe) is None:
        raise Af5JobError("warmup_bridge_pipe must be a run-unique bridge pipe")
    if pipe.casefold() == warmup_pipe.casefold():
        raise Af5JobError("warm-up and final bridge pipes must differ")
    observed = process_probe()
    if require_empty_slot and observed:
        raise Af5JobError(f"exclusive CK3 slot is occupied: {observed!r}")
    return {
        "activation": copy.deepcopy(value),
        "expected_hashes": expected,
        "activation_record": file_record(path),
        "round": gameplay_round,
        "rounds": {"frontend_warmup": warmup_round, "gameplay": gameplay_round},
        "repository_identity": repository_identity,
        "repository_root": repository_root,
        "game_directory": game_directory,
        "product_root": product_root,
        "startup_template_profile": startup_profile,
        "checkpoint": checkpoint,
        "product_projection_manifest": projection_path,
        "product_projection": projection,
        "bridge_dll": bridge_dll,
        "bridge_injector": bridge_injector,
        "prior_cleanup": prior_cleanup,
        "vanilla_game_rules": vanilla_game_rules,
        "state_directory": state_directory.resolve(),
        "artifact_directory": artifact_directory.resolve(),
        "bridge_pipe": pipe,
        "warmup_bridge_pipe": warmup_pipe,
        "observed_ck3_pids_read_only": observed,
    }


def _copy_startup_assets(source: Path, target: Path) -> list[dict[str, object]]:
    copied: list[dict[str, object]] = []
    for name in STARTUP_ASSETS:
        source_path = source / name
        if not source_path.exists():
            continue
        target_path = target / name
        if target_path.exists():
            raise Af5JobError(f"bootstrap unexpectedly created startup asset: {target_path}")
        if source_path.is_dir():
            shutil.copytree(source_path, target_path)
            copied.append({"name": name, "kind": "directory"})
        else:
            shutil.copy2(source_path, target_path)
            copied.append({"name": name, **file_record(target_path)})
    if {row["name"] for row in copied} < {"shadercache"}:
        raise Af5JobError("required startup assets were not copied")
    return copied


def render_presets_from_explicit_vanilla(
    acceptance: object, vanilla_game_rules: Path
) -> str:
    defaults = acceptance.declared_vanilla_rule_defaults(vanilla_game_rules)
    settings = [setting for _, setting in defaults]
    settings.extend(("zg361_on", "zg361_freq_yearly", "zg361_ratio_strict"))
    if len(settings) != len(set(settings)):
        raise Af5JobError("duplicate game-rule setting in explicit vanilla preset")
    return (
        "game_rules_preset={\n"
        '\tname="LastAppliedRules"\n'
        f"\tsetting={{ {' '.join(settings)} }}\n"
        "\tironman=no\n"
        "}\n"
    )


class Af5OperatorJob:
    def __init__(self, activation_path: Path) -> None:
        self.activation_path = activation_path.expanduser().resolve()
        self.lock = threading.RLock()
        self.stop_requested = threading.Event()
        self.worker: threading.Thread | None = None
        self.state = "READY_NO_LAUNCH"
        self.failure_reason: str | None = None
        self.product_result = "PENDING"
        self.stage = "ready"
        self.failure_evidence: dict[str, object] | None = None
        self.bound: dict[str, object] | None = None
        self.supervisor: dict[str, object] | None = None
        self.driver: object | None = None
        self.service: object | None = None
        self.runner: object | None = None
        self.binding: dict[str, object] | None = None
        self.af5_evidence: dict[str, object] | None = None
        self.cleanup: dict[str, object] | None = None
        self.attempt = 1

    def status(self) -> dict[str, object]:
        with self.lock:
            return {
                "schema_version": 1,
                "kind": "zg361_rn_af5_operator_status_v1",
                "state": self.state,
                "result": (
                    "RED" if self.failure_reason or self.product_result == "RED" or (self.cleanup and self.cleanup.get("result") == "RED")
                    else self.product_result
                ),
                "product_result": self.product_result,
                "cleanup_result": self.cleanup.get("result") if self.cleanup else "PENDING",
                "stage": self.stage,
                "attempt": self.attempt,
                "round": self.bound.get("round") if self.bound else None,
                "rounds": self.bound.get("rounds") if self.bound else None,
                "bridge_pid": self.binding.get("bridge_pid") if self.binding else None,
                "connection_generation": self.binding.get("connection_generation") if self.binding else None,
                "ck3_pids": ck3_pids(),
                "failure_reason": self.failure_reason,
                "af5_evidence": (
                    file_record(Path(str(self.bound["artifact_directory"])) / "af5-terminal-green.json")
                    if self.bound and (Path(str(self.bound["artifact_directory"])) / "af5-terminal-green.json").is_file()
                    else None
                ),
                "cleanup": copy.deepcopy(self.cleanup),
                "controls": ["status", "run-af5", "retry-policy", "retry-af5", "cleanup"],
                "video_lock_touched": False,
            }

    def start(self) -> dict[str, object]:
        # Import the desktop automation stack on the process main thread before
        # the live worker starts.  OpenCV/Numpy can stall indefinitely while
        # loading native modules for the first time from a background thread.
        # The worker's imports below then resolve from sys.modules.
        bound = mapping(self.bound, "validated activation")
        root = Path(str(bound["repository_root"]))
        sys.path.insert(0, str(root / "ck3_autonomous_player" / "src"))
        sys.path.insert(0, str(root / "tools"))
        importlib.import_module("run_zhongguo_acceptance")
        with self.lock:
            if self.worker is not None or self.state != "READY_NO_LAUNCH":
                return {**self.status(), "control": "run-af5", "idempotent": True}
            self.state = "RUNNING_AF5"
            self.worker = threading.Thread(target=self._run, name="af5-live", daemon=False)
            self.worker.start()
            return {**self.status(), "control": "run-af5", "accepted": True}

    def _run(self) -> None:
        try:
            bound = validate_activation(self.activation_path, require_empty_slot=True)
            with self.lock:
                self.bound = bound
            self._execute(bound)
        except BaseException as error:
            self._record_failure(error)
        finally:
            print(json.dumps({**self.status(), "notification": "run-af5-finished"}, ensure_ascii=False), flush=True)

    def retry(self) -> dict[str, object]:
        """Resume before option 42 from an explicitly frozen repaired checkout."""
        with self.lock:
            if (self.state != "AF5_RED_PARKED" or self.stage != "af5_terminal_action"
                    or self.service is None or self.binding is None
                    or (self.worker is not None and self.worker.is_alive())):
                return {**self.status(), "control": "retry-af5", "accepted": False,
                        "reason": "no completed pre-selection action failure on a retained session"}
            failed_action = mapping((self.failure_evidence or {}).get("evidence"), "failed action evidence")
            if failed_action.get("selected_option_number") is not None or failed_action.get("selection") is not None:
                return {**self.status(), "control": "retry-af5", "accepted": False,
                        "reason": "terminal input already attempted; retain original evidence without reselection"}
            self.state = "RUNNING_AF5"
            self.worker = threading.Thread(target=self._run_retry, name="af5-hot-retry", daemon=False)
            self.worker.start()
            return {**self.status(), "control": "retry-af5", "accepted": True}

    def retry_policy(self) -> dict[str, object]:
        """Expose one machine-readable retry control across operator jobs.

        Job-specific retry names remain compatible aliases. A job which is
        not on an eligible retained pre-input RED frame returns a structured
        rejection instead of omitting retry from its control protocol.
        """

        response = dict(self.retry())
        job_control = str(response.get("control", "retry-af5"))
        accepted = response.get("accepted") is True
        reason = response.get("reason")
        if accepted:
            reason_code = "RETRY_ACCEPTED"
        elif isinstance(reason, str) and "input already attempted" in reason:
            reason_code = "TARGET_INPUT_ALREADY_ATTEMPTED"
        elif isinstance(reason, str) and "no completed" in reason:
            reason_code = "NO_ELIGIBLE_RETAINED_FAILURE"
        else:
            reason_code = "JOB_RETRY_REJECTED"
        response.update(
            control="retry-policy",
            job_retry_control=job_control,
            retry_policy={
                "schema_version": 1,
                "kind": "xar_pre_input_retry_policy_v1",
                "accepted": accepted,
                "reason_code": reason_code,
                "requires_frozen_red": True,
                "requires_zero_target_input": True,
                "requires_same_paused_binding": True,
                "loaded_game_inputs_must_match": True,
                "python_policy_reload_only": True,
                "prior_attempt_immutable": True,
                "new_attempt_artifact_required": True,
                "game_deadline_may_expand": False,
            },
        )
        return response

    def _run_retry(self) -> None:
        try:
            original = mapping(self.bound, "original activation")
            artifacts = Path(str(original["artifact_directory"]))
            # Preserve the failed attempt before any validation/import can fail.
            prior_red = artifacts / "af5-red.json"
            if prior_red.is_file():
                shutil.copy2(prior_red, artifacts / f"af5-red-attempt-{self.attempt:02d}.json")
            retry_path = self.activation_path.with_name("retry-activation.json")
            repaired = validate_activation(retry_path, require_empty_slot=False)
            old_hashes = mapping(original["expected_hashes"], "original hashes")
            new_hashes = mapping(repaired["expected_hashes"], "repaired hashes")
            if any(old_hashes[key] != new_hashes[key] for key in HASH_FIELDS):
                raise Af5JobError("hot retry changed loaded game inputs")
            for key in ("game_directory", "product_root", "product_projection_manifest", "checkpoint",
                        "bridge_dll", "bridge_injector", "state_directory", "artifact_directory",
                        "bridge_pipe", "warmup_bridge_pipe", "rounds"):
                if original[key] != repaired[key]:
                    raise Af5JobError(f"hot retry changed loaded session input: {key}")
            before = self._retained_binding()
            self._reload_action_modules(Path(str(repaired["repository_root"])))
            after = self._retained_binding()
            if before != after:
                raise Af5JobError("paused session changed while reloading Python")
            self.attempt += 1
            write_object(artifacts / f"af5-retry-attempt-{self.attempt:02d}.json", {
                "schema_version": 1, "result": "GREEN", "same_process_retained": True,
                "before": before, "after": after,
                "original_code_commit": old_hashes["code_commit"],
                "repaired_code_commit": new_hashes["code_commit"],
                "repaired_repository_root": str(repaired["repository_root"]),
                "activation": repaired["activation_record"],
            })
            self.bound = repaired
            self.failure_reason = None
            self.product_result = "PENDING"
            self._execute_action(repaired)
        except BaseException as error:
            self._record_failure(error)
        finally:
            print(json.dumps({**self.status(), "notification": "retry-af5-finished"}, ensure_ascii=False), flush=True)

    def _retained_binding(self) -> dict[str, object]:
        snapshot = self.service.snapshot()
        diagnostics = mapping(snapshot.get("diagnostics"), "retained diagnostics")
        binding = mapping(self.binding, "initial native binding")
        pid = binding["bridge_pid"]
        if not (snapshot.get("paused") is True and diagnostics.get("connected") is True
                and diagnostics.get("bridge_pid") == pid and ck3_pids() == [pid]
                and diagnostics.get("connection_generation") == binding["connection_generation"]):
            raise Af5JobError("retained native session is not the same healthy paused process")
        event = snapshot.get("active_event")
        return {"bridge_pid": pid, "connection_generation": binding["connection_generation"],
                "played_character": snapshot.get("played_character"), "date_raw": snapshot.get("date_raw"),
                "event_instance_id": event.get("instance_id") if isinstance(event, Mapping) else None}

    @staticmethod
    def _reload_action_modules(root: Path) -> None:
        sys.path.insert(0, str(root / "tools"))
        # Keep the existing bridge/service objects and native-session modules.
        # Redirect only the data registry and gameplay policy dependencies.
        package = importlib.import_module("xar_autoplayer")
        package.__path__ = [str(root / "ck3_autonomous_player/src/xar_autoplayer")]
        vanilla = sys.modules.get("xar_autoplayer.vanilla_events")
        if vanilla is not None:
            vanilla.__path__ = [str(root / "ck3_autonomous_player/src/xar_autoplayer/vanilla_events")]
        importlib.invalidate_caches()
        for name in ("zg361_phase2_promotion_compensation_action_cell",
                     "zg361_phase2_promotion_source_production_entry", "zg361_phase2_af5_action_cell"):
            module = importlib.import_module(name)
            module = importlib.reload(module)
            if not Path(str(module.__file__)).resolve().is_relative_to(root):
                raise Af5JobError(f"repaired action module did not load from frozen checkout: {name}")

    def _record_failure(self, error: BaseException) -> None:
        rendered = f"{type(error).__name__}: {error}"
        failure_snapshot = None
        pause_error = None
        if self.service is not None:
            try:
                failure_snapshot = self.service.snapshot()
                if failure_snapshot.get("paused") is not True:
                    self.service.execute_step("pause-map", expected_revision=int(failure_snapshot["revision"]))
                    failure_snapshot = self.service.snapshot()
            except BaseException as observed_error:
                pause_error = f"{type(observed_error).__name__}: {observed_error}"
        evidence = {
            "schema_version": 1,
            "result": "RED",
            "product_result": "GREEN" if self.af5_evidence else "RED",
            "failure_stage": self.stage,
            "failure_reason": rendered,
            "reason_code": getattr(error, "reason_code", None),
            "failure_snapshot": bootstrap_evidence_json_value(failure_snapshot),
            "pause_error": pause_error,
            "attempt": self.attempt,
            "evidence": bootstrap_evidence_json_value(getattr(error, "evidence", None)),
            "red_preserved": True,
            "ck3_pids": ck3_pids(),
            "video_lock_touched": False,
        }
        with self.lock:
            self.failure_reason = rendered
            self.product_result = str(evidence["product_result"])
            self.failure_evidence = evidence
            self.state = "AF5_RED_PARKED" if evidence["ck3_pids"] else "AF5_RED_NO_LIVE_PROCESS"
        if self.bound is not None:
            write_object(Path(str(self.bound["artifact_directory"])) / "af5-red.json", evidence)

    def _execute(self, bound: Mapping[str, object]) -> None:
        root = Path(str(bound["repository_root"]))
        expected = mapping(bound["expected_hashes"], "expected_hashes")
        self.stage = "materialization"
        sys.path.insert(0, str(root / "ck3_autonomous_player" / "src"))
        sys.path.insert(0, str(root / "tools"))
        runner = importlib.import_module("run_zhongguo_acceptance")
        acceptance = importlib.import_module("run_acceptance")
        action_module = importlib.import_module(
            "zg361_phase2_af5_action_cell"
        )
        environment = importlib.import_module("xar_autoplayer.environment")
        native_driver = importlib.import_module("xar_autoplayer.bridge.native_driver")
        service_module = importlib.import_module("xar_autoplayer.bridge.service")
        for module in (runner, acceptance, action_module, environment, native_driver, service_module):
            module_path = Path(str(module.__file__)).resolve()
            if not module_path.is_relative_to(root):
                raise Af5JobError(f"execution module is outside the frozen root: {module_path}")
        artifacts = Path(str(bound["artifact_directory"]))
        state_dir = Path(str(bound["state_directory"]))
        artifacts.mkdir(parents=True, exist_ok=False)
        state_dir.mkdir(parents=True, exist_ok=False)
        profile = state_dir / "profile"
        activation = mapping(bound["activation"], "activation")
        vanilla_game_rules = Path(str(bound["vanilla_game_rules"]))
        # The frozen harness lives outside the installation, so its historical
        # module-level ROOT must never decide where vanilla data comes from.
        # Supply the independently hash-bound installation file explicitly.
        runner.render_presets = lambda: render_presets_from_explicit_vanilla(
            acceptance, vanilla_game_rules
        )
        bootstrap = runner.bootstrap_userdir(
            profile,
            Path(str(bound["product_root"])),
            None,
            game_dir=Path(str(bound["game_directory"])),
            include_acceptance_fixture=False,
            product_projection=str(activation["product_projection_name"]),
            product_projection_manifest=Path(str(bound["product_projection_manifest"])),
        )
        loaded_tree = mapping(bootstrap.get("tree_sha256"), "bootstrap tree").get("product")
        if str(loaded_tree).upper() != expected["product_tree_sha256"]:
            raise Af5JobError(f"materialized product tree differs: {loaded_tree!r}")
        startup_assets = _copy_startup_assets(
            Path(str(bound["startup_template_profile"])), profile
        )
        save_dir = profile / "save games"
        save_dir.mkdir(parents=True, exist_ok=True)
        for target in (save_dir / "autosave.ck3", profile / "last_save.ck3"):
            shutil.copy2(Path(str(bound["checkpoint"])), target)
            if sha256(target) != expected["checkpoint_sha256"]:
                raise Af5JobError("checkpoint materialization differs")
        write_object(
            artifacts / "01-materialization.json",
            {
                "schema_version": 1,
                "result": "GREEN",
                "product_tree_sha256": expected["product_tree_sha256"],
                "checkpoint": file_record(Path(str(bound["checkpoint"]))),
                "vanilla_game_rules": file_record(vanilla_game_rules),
                "vanilla_game_root": str(Path(str(bound["game_directory"]))),
                "vanilla_path_was_explicit": True,
                "startup_assets": startup_assets,
                "bootstrap": bootstrap_evidence_json_value(bootstrap),
                "fixture_used": False,
            },
        )
        acceptance.configure_runtime_userdir(profile)
        spec = environment.make_spec(
            state_dir=state_dir, game_dir=Path(str(bound["game_directory"]))
        )
        bridge = runner.resolve_native_bridge_config(
            str(bound["bridge_dll"]), str(bound["bridge_injector"]), str(bound["bridge_pipe"])
        )
        warmup_bridge = runner.resolve_native_bridge_config(
            str(bound["bridge_dll"]), str(bound["bridge_injector"]), str(bound["warmup_bridge_pipe"])
        )
        self.stage = "native_startup"
        supervisor = runner.start_phase2_native_session_supervisor(
            spec,
            bridge,
            runtime_timeout_seconds=float(activation.get("runtime_timeout_seconds", 1800.0)),
            frontend_first_load_save_name="autosave",
            frontend_first_timeout_seconds=float(activation.get("frontend_timeout_seconds", 300.0)),
            frontend_first_warmup_bridge=warmup_bridge,
        )
        driver = native_driver.NativeHeadlessGameplayDriver(
            str(bound["bridge_pipe"]),
            state_dir=state_dir,
            save_dir=save_dir,
            command_timeout_seconds=runner.NATIVE_TITLE_COMMAND_TIMEOUT_S,
        )
        service = service_module.GameplayBridgeService(driver)
        with self.lock:
            self.runner = runner
            self.supervisor = supervisor
            self.driver = driver
            self.service = service
        binding = runner.wait_for_phase2_native_session_binding(service, supervisor, artifacts)
        pid = positive_int(binding.get("bridge_pid"), "bridge PID")
        generation = positive_int(binding.get("connection_generation"), "generation")
        if ck3_pids() != [pid]:
            raise Af5JobError("new round is not the sole CK3 process")
        with self.lock:
            self.binding = binding
        self.stage = "loader"
        loader = runner.run_loader_gate(
            service,
            artifacts,
            profile,
            bootstrap,
            tracked_ck3_pid=pid,
            phase2_live_batch=False,
            managed_restore_supervisor=True,
            native_session_supervisor=supervisor,
            phase2_promotion_source_capture_live=True,
        )
        if loader.get("result") != "GREEN":
            raise Af5JobError("exact-build loader gate returned non-GREEN")
        self._execute_action(bound)

    def _execute_action(self, bound: Mapping[str, object]) -> None:
        runner = self.runner
        service = self.service
        action_module = importlib.import_module("zg361_phase2_af5_action_cell")
        artifacts = Path(str(bound["artifact_directory"]))
        expected = mapping(bound["expected_hashes"], "expected_hashes")
        binding = mapping(self.binding, "native binding")
        pid = positive_int(binding.get("bridge_pid"), "bridge PID")
        generation = positive_int(binding.get("connection_generation"), "generation")
        self.stage = "af5_terminal_action"
        evidence = dict(action_module.run_af5_terminal_action_cell(
            service,
            advance_to_af5=action_module.advance_to_af5,
            request_nonce=f"{bound['round']}.af5.terminal",
        ))
        if not (
            evidence.get("result") == "GREEN"
            and evidence.get("provider_observed") is True
            and evidence.get("terminal_postcondition_verified") is True
            and evidence.get("action_ack_is_business_postcondition") is False
        ):
            raise Af5JobError("AF5 terminal action or independent provider returned RED", evidence)
        evidence.update(
            round=bound["round"],
            execution_identity={"repository_root": str(bound["repository_root"]), "code_commit": expected["code_commit"]},
            bridge_pid=pid,
            connection_generation=generation,
            checkpoint=file_record(Path(str(bound["checkpoint"]))),
            product_tree_sha256=expected["product_tree_sha256"],
            bridge_dll=file_record(Path(str(bound["bridge_dll"]))),
            production_live=True,
            fixture_used=False,
            console_used=False,
            ocr_used=False,
            coordinates_used=False,
            video_lock_touched=False,
        )
        write_object(artifacts / "af5-terminal-green.json", evidence)
        with self.lock:
            self.af5_evidence = evidence
            self.product_result = "GREEN"
        self.stage = "terminal_checkpoint"
        terminal_snapshot = service.snapshot()
        save_result = service.save_checkpoint(expected_revision=int(terminal_snapshot["revision"]))
        write_object(artifacts / "af5-terminal-save.json", bootstrap_evidence_json_value(save_result))
        checkpoint = mapping(save_result.get("checkpoint"), "terminal checkpoint")
        if save_result.get("accepted") is not True or checkpoint.get("status") != "saved":
            raise Af5JobError("terminal save did not materialize", save_result)
        archive = runner._phase2_archive_checkpoint(
            checkpoint,
            artifacts / "af5-terminal.ck3",
            save_lineage_id=f"{bound['round']}.af5.terminal",
        )
        write_object(artifacts / "af5-terminal-checkpoint.json", {
            "schema_version": 1,
            "result": "GREEN",
            "checkpoint": archive,
            "terminal_evidence": file_record(artifacts / "af5-terminal-green.json"),
        })
        terminal_snapshot = service.snapshot()
        write_object(
            artifacts / "af5-park.json",
            {
                "schema_version": 1,
                "result": "PARKED",
                "paused": terminal_snapshot.get("paused"),
                "round": bound["round"],
                "bridge_pid": pid,
                "connection_generation": generation,
                "snapshot": terminal_snapshot,
                "terminal_checkpoint": archive,
            },
        )
        with self.lock:
            self.state = "AF5_GREEN_PARKED"
            self.stage = "terminal_verified_and_saved"
            self.failure_reason = None

    def perform_cleanup(self) -> dict[str, object]:
        with self.lock:
            if self.state == "RUNNING_AF5":
                return {**self.status(), "control": "cleanup", "accepted": False, "reason": "run-af5 is active"}
            if self.cleanup is not None:
                self.stop_requested.set()
                return {**self.status(), "control": "cleanup", "idempotent": True}
            if self.supervisor is None:
                if ck3_pids():
                    return {**self.status(), "control": "cleanup", "accepted": False, "reason": "no owned supervisor and CK3 exists"}
                self.cleanup = {"schema_version": 1, "result": "GREEN", "cleanup_proven": True, "no_launch": True}
                self.state = "CLEANED"
                self.stop_requested.set()
                return {**self.status(), "control": "cleanup", "accepted": True}
            runner = self.runner
            supervisor = self.supervisor
            service = self.service
            binding = self.binding or {}
            bound = self.bound
        capabilities: object = None
        if service is not None:
            try:
                capabilities = service.capabilities()
            except BaseException:
                capabilities = None
        cleanup = runner.stop_phase2_native_session_supervisor(
            supervisor,
            Path(str(bound["artifact_directory"])),
            initial_pid=binding.get("bridge_pid"),
            initial_generation=binding.get("connection_generation"),
            expected_pipe=str(bound["bridge_pipe"]),
            scenario_evidence=self.af5_evidence or self.failure_evidence or {"result": "RED", "restore_expected": False},
            final_capabilities=capabilities,
        )
        close = getattr(self.driver, "close", None)
        if callable(close):
            close()
        proven = cleanup.get("result") == "GREEN" and ck3_pids() == []
        packaged = {
            "schema_version": 1,
            "kind": "zg361_rn_af5_managed_cleanup_v1",
            "result": "GREEN" if proven else "RED",
            "cleanup_proven": proven,
            "canonical_cleanup": cleanup,
            "ck3_pids_after": ck3_pids(),
        }
        if bound is not None:
            write_object(Path(str(bound["artifact_directory"])) / "af5-managed-cleanup.json", packaged)
        with self.lock:
            self.cleanup = packaged
            self.state = "CLEANED" if proven else "CLEANUP_RED"
            self.stop_requested.set()
        return {**self.status(), "control": "cleanup", "accepted": True}

    def serve(self) -> int:
        self.bound = validate_activation(self.activation_path, require_empty_slot=False)
        print(json.dumps(self.status(), ensure_ascii=False), flush=True)
        while not self.stop_requested.is_set():
            line = sys.stdin.readline()
            if line == "":
                self.stop_requested.wait(30.0)
                continue
            command = line.strip().casefold()
            if command == "status":
                response = self.status()
            elif command == "run-af5":
                response = self.start()
            elif command == "retry-af5":
                response = self.retry()
            elif command == "retry-policy":
                response = self.retry_policy()
            elif command == "cleanup":
                response = self.perform_cleanup()
            else:
                response = {"result": "RED", "error": "unknown control", "controls": ["status", "run-af5", "retry-policy", "retry-af5", "cleanup"]}
            print(json.dumps(response, ensure_ascii=False), flush=True)
        worker = self.worker
        if worker is not None and worker.is_alive():
            worker.join()
        return self.exit_code()

    def exit_code(self) -> int:
        return 0 if not self.failure_reason and self.product_result != "RED" and self.state == "CLEANED" and self.cleanup and self.cleanup.get("result") == "GREEN" else 1


def no_launch_preflight(activation_path: Path | None = None) -> dict[str, object]:
    result: dict[str, object] = {
        "schema_version": 1,
        "kind": "zg361_rn_af5_operator_no_launch_preflight_v1",
        "result": "GREEN",
        "launch_requested": False,
        "cleanup_requested": False,
        "controls": ["status", "run-af5", "retry-policy", "retry-af5", "cleanup"],
        "single_ck3_gate": True,
        "af5_route": {"event_definition_key": RESULT_EVENT, "authored_option": 42, "native_index": 41},
        "action_ack_is_business_postcondition": False,
        "video_lock_touched": False,
        "observed_ck3_pids_read_only": ck3_pids(),
        "activation_state": "not_supplied",
    }
    if activation_path is not None:
        try:
            bound = validate_activation(activation_path, require_empty_slot=False)
            result["activation_state"] = "STATIC_READY"
            result["activation"] = bound["activation_record"]
            result["round"] = bound["round"]
            result["rounds"] = bound["rounds"]
            result["expected_hashes"] = bound["expected_hashes"]
            result["repository_root"] = str(bound["repository_root"])
        except BaseException as error:
            result["result"] = "RED"
            result["activation_state"] = "RED"
            result["failure_reason"] = f"{type(error).__name__}: {error}"
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--activation", type=Path)
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--preflight-output", type=Path)
    args = parser.parse_args(argv)
    if args.serve:
        if args.activation is None:
            parser.error("--serve requires --activation")
        return Af5OperatorJob(args.activation).serve()
    result = no_launch_preflight(args.activation)
    if args.preflight_output is not None:
        write_object(args.preflight_output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("result") == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
