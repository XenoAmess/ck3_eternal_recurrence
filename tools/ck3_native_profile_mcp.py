#!/usr/bin/env python3
"""Attach the existing CK3 bridge to one frozen, offline, live-run profile."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
import uuid
from typing import Annotated, Literal
from pydantic import Field

NormalExitRevisionV1 = Annotated[int, Field(strict=True, gt=0, lt=2**64)]
NormalExitSignatureV1 = Annotated[str, Field(strict=True, min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")]
StressBaseAmountV1 = Annotated[int, Field(strict=True, ge=-300, le=300)]
StressQueryRevisionV1 = Annotated[int, Field(strict=True, ge=0, lt=2**64)]
OrdinaryInteractionKeyV1 = Annotated[str, Field(strict=True, min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_]+$")]
OrdinaryRecipientIdV1 = Annotated[int, Field(strict=True, ge=1, le=2**32 - 2)]

import desktop_semantic_action_mcp as desktop

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player/src"))
from xar_autoplayer.operator_mcp import _forbid_unknown_tool_arguments_v1


def _load_profile_common(path: Path, extra_fields: set[str]) -> dict:
    profile = desktop.exact_fields(json.loads(path.read_text(encoding="utf-8-sig")), {
        "schema_version", "guard_profile", "guard_profile_sha256", "userdir",
        "evidence_directory", "game_version",
    } | extra_fields, "native profile")
    if type(profile["schema_version"]) is not int or profile["schema_version"] != 1:
        raise ValueError("native profile schema_version must be 1")
    for name in ("guard_profile", "userdir", "evidence_directory"):
        if not isinstance(profile[name], str) or not Path(profile[name]).is_absolute():
            raise ValueError(f"{name} must be an absolute target-side path")
    digest = profile["guard_profile_sha256"]
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
        raise ValueError("guard profile requires SHA-256")
    guard_path = Path(profile["guard_profile"])
    if desktop.sha256(guard_path).lower() != digest.lower():
        raise ValueError("guard profile SHA-256 changed")
    profile["guard"] = desktop.load_profile(guard_path)
    if not isinstance(profile["game_version"], str) or not re.fullmatch(r"\d+\.\d+\.\d+\.\d+", profile["game_version"]):
        raise ValueError("game_version must be exact")
    if not Path(profile["userdir"]).is_dir():
        raise ValueError("isolated userdir is missing")
    profile["profile_sha256"] = desktop.sha256(path)
    return profile


def load_clock_profile(path: Path) -> dict:
    return _load_profile_common(path, set())


def load_profile(path: Path) -> dict:
    raw_profile = json.loads(path.read_text(encoding="utf-8-sig"))
    optional_fields = {"normal_exit_source_inventory"} & set(raw_profile)
    profile = _load_profile_common(path, {"state_directory", "dll", "injector"} | optional_fields)
    if "normal_exit_source_inventory" in profile:
        reference = desktop.exact_fields(profile["normal_exit_source_inventory"], {"path", "sha256"}, "normal exit source inventory")
        fixed_path = (Path(profile["userdir"]) / "normal-exit-source-inventory-v1.json").resolve()
        if (not isinstance(reference["path"], str) or not Path(reference["path"]).is_absolute()
                or Path(reference["path"]).resolve() != fixed_path
                or not isinstance(reference["sha256"], str)
                or not re.fullmatch(r"[0-9a-f]{64}", reference["sha256"])):
            raise ValueError("normal exit inventory must identify the fixed userdir file and exact SHA-256")
    if not isinstance(profile["state_directory"], str) or not Path(profile["state_directory"]).is_absolute():
        raise ValueError("state_directory must be an absolute target-side path")
    for name, expected in (("dll", "xar_ck3_bridge.dll"), ("injector", "xar_ck3_bridge_injector.exe")):
        row = desktop.exact_fields(profile[name], {"path", "sha256"}, name)
        if not isinstance(row["path"], str) or not Path(row["path"]).is_absolute() or Path(row["path"]).name.lower() != expected:
            raise ValueError(f"{name} must identify the authoritative bridge artifact")
        if not isinstance(row["sha256"], str) or not re.fullmatch(r"[0-9a-fA-F]{64}", row["sha256"]):
            raise ValueError(f"{name} requires SHA-256")
    return profile


class NativeProfileBackend:
    def observe(self, profile: dict) -> dict:
        import psutil
        observed = desktop.NativeDesktopBackend().observe(profile["guard"])
        process = psutil.Process(profile["guard"]["target"]["pid"])
        observed["command_line"] = process.cmdline()
        return observed

    def poll(self, profile: dict) -> dict:
        guard = profile["guard"]
        command = [sys.executable, guard["task_bus_script"],
                   "--expected-cli-sha256", guard["task_bus_sha256"],
                   "poll", "--task", guard["screen_task_id"], "--ack"]
        result = subprocess.run(command, capture_output=True, encoding="utf-8",
                                errors="replace", timeout=20, check=True)
        return json.loads(result.stdout)

    def inject(self, command: list[str]):
        from xar_autoplayer.windows_injector_job import run_contained_injector_command
        return run_contained_injector_command(command, timeout_seconds=30)

    def read_clock(self, profile: dict) -> dict:
        from ck3_native_clock_reader import read_live_clock
        target = profile["guard"]["target"]
        return read_live_clock(target["pid"], target["executable"], target["executable_sha256"], profile["game_version"])


class _PostconditionPending(RuntimeError):
    """The command was submitted but its native semantic frame is still pending."""


class NativeProfileService:
    """No caller can choose a process, artifact, pipe, command, or run identity."""
    def __init__(self, profile: dict, *, backend=None, driver_factory=None) -> None:
        self.profile = profile
        self.backend = backend or NativeProfileBackend()
        self.session_id = uuid.uuid4().hex
        self.pipe_name = rf"\\.\pipe\xar_profile_{self.session_id}"
        self._lock = threading.RLock()
        self._attach_result = None
        self._sequence = 0
        self.driver = None
        self.driver_factory = driver_factory
        self._gameplay = None
        self._postcondition_timeout_seconds = 5.0
        self._postcondition_poll_seconds = 0.05
        self._resume_timeout_seconds = 10.0

    def guard(self) -> dict:
        profile = self.profile
        self._reject_run_crash()
        if desktop.sha256(Path(profile["guard_profile"])).lower() != profile["guard_profile_sha256"].lower():
            raise RuntimeError("guard profile changed after server startup")
        observed = self.backend.observe(profile)
        desktop.validate_observation(profile["guard"], observed)
        userdirs = [arg.split("=", 1)[1] for arg in observed["command_line"]
                    if isinstance(arg, str) and arg.startswith("-userdir=")]
        if len(userdirs) != 1 or Path(userdirs[0]).resolve() != Path(profile["userdir"]).resolve():
            raise RuntimeError("live process isolated userdir does not match profile")
        self._reject_run_crash()
        return observed

    def _reject_run_crash(self) -> None:
        directory = Path(self.profile["userdir"]) / "crashes"
        if directory.exists() and (not directory.is_dir() or any(directory.iterdir())):
            raise RuntimeError("isolated run has a crash artifact; a live PID or native clock does not prove healthy gameplay")

    def _receipt(self, operation: str, value: dict) -> dict:
        self._sequence += 1
        directory = Path(self.profile["evidence_directory"]) / self.session_id
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{self._sequence:04d}-{operation}.json"
        result = {"schema": "ck3.native-profile-receipt.v1", "session_id": self.session_id,
                  "profile_sha256": self.profile["profile_sha256"], "pipe_name": self.pipe_name,
                  "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
                  **value, "receipt_path": str(path)}
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return result

    def inspect(self) -> dict:
        with self._lock:
            return self._receipt("inspect", {"status": "profile_bound", "observation": self.guard(),
                                           "attached": self._attach_result is not None
                                           and self._attach_result.get("status") in {
                                               "attached_snapshot_verified", "resumed_snapshot_verified"}})

    def _snapshot(self) -> dict:
        if self.driver is None:
            raise RuntimeError("profile bridge has not been attached")
        snapshot = self.driver.take_snapshot()
        return self._validate_snapshot_identity(snapshot)

    def _validate_snapshot_identity(self, snapshot: dict) -> dict:
        diagnostics = snapshot.get("diagnostics", {})
        hello = diagnostics.get("hello", {})
        target = self.profile["guard"]["target"]
        if (diagnostics.get("bridge_pid") != target["pid"]
                or hello.get("game_adapter_status") != "ready"
                or hello.get("expected_ck3_version") != self.profile["game_version"]
                or str(hello.get("expected_ck3_sha256", "")).lower() != target["executable_sha256"].lower()):
            raise RuntimeError("native hello is not the frozen target process and exact build")
        if type(snapshot.get("date_raw")) is not int or type(snapshot.get("paused")) is not bool or type(snapshot.get("speed")) is not int:
            raise RuntimeError("native date/paused/speed snapshot is unavailable")
        if snapshot.get("episode_projection") != "native_campaign":
            raise RuntimeError("native profile must consume the engine campaign without one-life projection")
        return snapshot

    def attach(self) -> dict:
        with self._lock:
            if self._attach_result is not None:
                return self._attach_result
            observed = self.guard()
            for name in ("dll", "injector"):
                row = self.profile[name]
                if desktop.sha256(Path(row["path"])).lower() != row["sha256"].lower():
                    raise RuntimeError(f"frozen {name} artifact SHA-256 changed")
            self.backend.poll(self.profile)
            self.guard()
            clock_before = self.backend.read_clock(self.profile)
            self.guard()
            if clock_before.get("paused") is not True:
                raise RuntimeError("profile bridge attach requires a paused initialized native clock")
            evidence = Path(self.profile["evidence_directory"])
            evidence.mkdir(parents=True, exist_ok=True)
            claim = evidence / "attach-claim.json"
            with claim.open("x", encoding="utf-8") as output:
                json.dump({"session_id": self.session_id, "profile_sha256": self.profile["profile_sha256"],
                           "pipe_name": self.pipe_name, "target": self.profile["guard"]["target"]}, output)
            if self.driver_factory is None:
                from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
                factory = NativeHeadlessGameplayDriver
            else:
                factory = self.driver_factory
            # Consume the one-shot before invoking the injector. A timeout or
            # failed readback must never replay a DLL attach into the same run.
            self._attach_result = {"status": "RED", "reason": "attach started"}
            injected = None
            try:
                self.driver = factory(self.pipe_name, state_dir=self.profile["state_directory"],
                                      save_dir=str(Path(self.profile["userdir"]) / "save games"),
                                      episode_projection="native_campaign")
                command = [self.profile["injector"]["path"], "--pipe", self.pipe_name,
                           str(self.profile["guard"]["target"]["pid"]), self.profile["dll"]["path"]]
                injected = self.backend.inject(command)
                if (injected.error is not None or injected.report.get("returncode") != 0
                        or injected.report.get("complete_process_tree_proven") is not True):
                    raise RuntimeError("injector did not prove a successful bounded attach")
                deadline = time.monotonic() + 10
                while True:
                    try:
                        snapshot = self._snapshot()
                        if (snapshot.get("map_ready") is not True or snapshot["paused"] is not True
                                or snapshot["date_raw"] != clock_before.get("date_raw")):
                            raise RuntimeError("first bridge snapshot does not match the paused map clock before attach")
                        break
                    except Exception:
                        if time.monotonic() >= deadline:
                            raise
                        time.sleep(0.05)
                after = self.guard()
                self._attach_result = self._receipt("attach", {
                    "status": "attached_snapshot_verified", "observation_before": observed,
                    "observation_after": after, "native_clock_before": clock_before,
                    "injector": injected.report, "snapshot": snapshot,
                    "uses_ocr": False, "uses_desktop_input": False})
            except Exception as error:
                self._attach_result = self._receipt("attach", {
                    "status": "RED", "reason": f"{type(error).__name__}: {error}",
                    "injector": injected.report if injected is not None else None})
            return self._attach_result

    def resume(self) -> dict:
        """Reconnect the original loaded DLL; never inject or replace its claim."""
        with self._lock:
            if self._attach_result is not None:
                return self._attach_result
            observed = self.guard()
            row = self.profile["dll"]
            if desktop.sha256(Path(row["path"])).lower() != row["sha256"].lower():
                raise RuntimeError("frozen DLL artifact SHA-256 changed")
            evidence = Path(self.profile["evidence_directory"])
            claim_path = evidence / "attach-claim.json"
            claim = desktop.exact_fields(json.loads(claim_path.read_text(encoding="utf-8-sig")),
                {"session_id", "profile_sha256", "pipe_name", "target"}, "original attach claim")
            original_id = claim["session_id"]
            if (not isinstance(original_id, str) or not re.fullmatch(r"[0-9a-f]{32}", original_id)
                    or claim["profile_sha256"] != self.profile["profile_sha256"]
                    or claim["target"] != self.profile["guard"]["target"]
                    or claim["pipe_name"] != rf"\\.\pipe\xar_profile_{original_id}"):
                raise RuntimeError("original attach claim is not this frozen profile and target")
            original_directory = evidence / original_id
            attach_paths = list(original_directory.glob("*-attach.json"))
            if len(attach_paths) != 1:
                raise RuntimeError("resume requires one original successful attach receipt")
            attach = json.loads(attach_paths[0].read_text(encoding="utf-8-sig"))
            receipt_paths = [(int(match.group(1)), path) for path in original_directory.glob("*.json")
                             if (match := re.fullmatch(r"(\d{4,})-[^.]+\.json", path.name))]
            latest_path = max(receipt_paths, key=lambda pair: pair[0])[1]
            latest = json.loads(latest_path.read_text(encoding="utf-8-sig"))
            for receipt in (attach, latest):
                if (receipt.get("schema") != "ck3.native-profile-receipt.v1"
                        or receipt.get("session_id") != original_id
                        or receipt.get("profile_sha256") != self.profile["profile_sha256"]
                        or receipt.get("pipe_name") != claim["pipe_name"]):
                    raise RuntimeError("original transport evidence identity changed")
            injector = attach.get("injector", {})
            if (attach.get("status") != "attached_snapshot_verified"
                    or injector.get("returncode") != 0
                    or injector.get("complete_process_tree_proven") is not True
                    or latest.get("status") != "native_snapshot_verified"):
                raise RuntimeError("resume requires successful attach and latest paused snapshot receipts")
            prior = self._validate_snapshot_identity(latest.get("snapshot", {}))
            self._validate_snapshot_identity(attach.get("snapshot", {}))
            prior_generation = prior["diagnostics"]["hello"].get("connection_generation")
            if (type(prior_generation) is not int or prior_generation < 1
                    or prior.get("paused") is not True or prior.get("map_ready") is not True):
                raise RuntimeError("original transport lacks a paused map and connection generation")
            self.backend.poll(self.profile)
            self.guard()
            clock_before = self.backend.read_clock(self.profile)
            self.guard()
            if (clock_before.get("paused") is not True
                    or type(clock_before.get("date_raw")) is not int
                    or type(clock_before.get("speed")) is not int
                    or clock_before["date_raw"] != prior["date_raw"]
                    or clock_before["speed"] != prior["speed"]):
                raise RuntimeError("resume clock is not the latest paused transport snapshot")
            # The original DLL's immutable pipe is evidence-owned, never an RPC argument.
            self.pipe_name = claim["pipe_name"]
            self._attach_result = {"status": "RED", "reason": "resume endpoint started"}
            try:
                if self.driver_factory is None:
                    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
                    factory = NativeHeadlessGameplayDriver
                else:
                    factory = self.driver_factory
                self.driver = factory(self.pipe_name, state_dir=self.profile["state_directory"],
                                      save_dir=str(Path(self.profile["userdir"]) / "save games"),
                                      episode_projection="native_campaign")
                deadline = time.monotonic() + self._resume_timeout_seconds
                while True:
                    self.guard()
                    try:
                        snapshot = self._snapshot()
                        generation = snapshot["diagnostics"]["hello"].get("connection_generation")
                        if (type(generation) is not int or generation <= prior_generation
                                or snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
                                or snapshot["date_raw"] != prior["date_raw"] or snapshot["speed"] != prior["speed"]
                                or snapshot.get("pending_character_interaction") != prior.get("pending_character_interaction")
                                or snapshot.get("active_event") != prior.get("active_event")):
                            raise RuntimeError("fresh reconnect snapshot has not preserved the paused campaign")
                        break
                    except Exception:
                        if time.monotonic() >= deadline:
                            raise
                        time.sleep(0.05)
                self.guard()
                clock_after = self.backend.read_clock(self.profile)
                if any(clock_after.get(key) != clock_before.get(key) for key in ("date_raw", "speed", "paused")):
                    raise RuntimeError("independent native clock changed during profile reconnect")
                after = self.guard()
                self._attach_result = self._receipt("resume", {
                    "status": "resumed_snapshot_verified", "prior_session_id": original_id,
                    "prior_connection_generation": prior_generation, "connection_generation": generation,
                    "original_claim_sha256": desktop.sha256(claim_path),
                    "original_attach_receipt": str(attach_paths[0]),
                    "original_attach_receipt_sha256": desktop.sha256(attach_paths[0]),
                    "prior_snapshot_receipt": str(latest_path), "prior_snapshot_receipt_sha256": desktop.sha256(latest_path),
                    "observation_before": observed, "observation_after": after,
                    "native_clock_before": clock_before, "native_clock_after": clock_after, "snapshot": snapshot,
                    "uses_injection": False, "uses_ocr": False, "uses_desktop_input": False})
            except Exception as error:
                self._attach_result = {"status": "RED", "reason": f"{type(error).__name__}: {error}"}
                if self.driver is not None:
                    self.driver.close()
                self._attach_result = self._receipt("resume", {**self._attach_result,
                    "prior_session_id": original_id, "prior_connection_generation": prior_generation,
                    "uses_injection": False, "uses_ocr": False, "uses_desktop_input": False})
            return self._attach_result

    def snapshot(self) -> dict:
        with self._lock:
            self.guard()
            snapshot = self._snapshot()
            after = self.guard()
            return self._receipt("snapshot", {"status": "native_snapshot_verified",
                                               "snapshot": snapshot, "observation_after": after})

    def _gameplay_service(self):
        if self._attach_result is None or self._attach_result.get("status") not in {
                "attached_snapshot_verified", "resumed_snapshot_verified"}:
            raise RuntimeError("ordinary gameplay requires a verified profile attachment")
        if self._gameplay is None:
            from xar_autoplayer.bridge.service import GameplayBridgeService
            self._gameplay = GameplayBridgeService(self.driver)
        return self._gameplay

    def _bound_frame(self, expected_revision: int, *, paused: bool = False) -> dict:
        if type(expected_revision) is not int or expected_revision < 0:
            raise ValueError("expected_revision must be a nonnegative integer")
        self.guard()
        frame = self._snapshot()
        if (frame.get("map_ready") is not True or type(frame.get("revision")) is not int
                or frame["revision"] != expected_revision):
            raise RuntimeError("ordinary gameplay requires the expected map-ready native revision")
        if paused and frame.get("paused") is not True:
            raise RuntimeError("this native operation requires a paused frame")
        return frame

    def query_ordinary_interaction(self, interaction_key: str, recipient_id: int, expected_revision: int) -> dict:
        from xar_autoplayer.bridge.ordinary_interaction_contract import (
            validate_interaction_key, validate_recipient_id, interaction_binding,
            same_query_frame, normalize_public_query,
        )
        validate_interaction_key(interaction_key)
        validate_recipient_id(recipient_id)
        with self._lock:
            before = self._bound_frame(expected_revision, paused=True)
            binding = interaction_binding(before, expected_revision)
            result = self._gameplay_service().query_character_interaction_ordinary_v1(
                interaction_key, recipient_id, expected_revision=expected_revision)
            after = self._bound_frame(expected_revision, paused=True)
            if not same_query_frame(before, after, binding):
                raise RuntimeError("profile ordinary query changed its actual frame")
            result = normalize_public_query(result, binding, interaction_key, recipient_id)
            return self._receipt("ordinary-interaction-query", {
                "status": ("native_ordinary_interaction_observed" if result["ordinary_interaction_context_ready"]
                           else "native_ordinary_interaction_unavailable"), "result": result,
                "business_effects_verified": False, "full_product_acceptance_credit": False})

    def initiate_ordinary_interaction(self, interaction_key: str, recipient_id: int, expected_revision: int) -> dict:
        from xar_autoplayer.bridge.ordinary_interaction_contract import (
            validate_interaction_key, validate_recipient_id, interaction_binding,
            after_control_binding, normalize_public_initiation,
        )
        validate_interaction_key(interaction_key)
        validate_recipient_id(recipient_id)
        with self._lock:
            before = self._bound_frame(expected_revision, paused=True)
            binding = interaction_binding(before, expected_revision, initiating=True)
            self.backend.poll(self.profile)
            self.guard()
            if binding["game_pid"] != self.profile["guard"]["target"]["pid"]:
                raise RuntimeError("ordinary initiation process is not the actual frozen profile target")
            self.driver._ordinary_interaction_host_provenance = {
                "process_create_time": self.profile["guard"]["target"]["process_create_time"],
                "profile_sha256": self.profile["profile_sha256"].lower(), "session_id": self.session_id,
                "pipe_name": self.pipe_name, "guard_profile_sha256": self.profile["guard_profile_sha256"].lower()}
            result = self._gameplay_service().initiate_character_interaction_ordinary_v1(
                interaction_key, recipient_id, expected_revision=expected_revision)
            # Never reuse _ordinary_action's verified gameplay postcondition.
            self.guard()
            after = self._snapshot()
            later = after_control_binding(before, after, binding)
            result = normalize_public_initiation(result, binding, interaction_key, recipient_id, later)
            self.backend.poll(self.profile)
            self.guard()
            return self._receipt("ordinary-interaction-initiate", {
                "status": ("native_ordinary_interaction_pending" if result["status"] == "pending"
                           else "native_ordinary_interaction_not_dispatched"), "result": result,
                "snapshot": after, "business_effects_verified": False, "full_product_acceptance_credit": False})

    def observe_normal_exit(self) -> dict:
        with self._lock:
            if self.driver is None or self._gameplay is None:
                raise RuntimeError("profile has no backend-owned pending exit observer")
            # Guard/snapshot/poll would require a live game after terminal dispatch.
            # The driver owns the original retained handle and frozen request binding.
            result = self._gameplay.observe_normal_exit_v1()
            return self._receipt("normal-exit-observe", {"status": result["status"],
                "result": result, "snapshot_after_required": False,
                "uses_ocr": False, "uses_desktop_input": False, "uses_injection": False})

    def query_normal_exit_context(self, expected_revision: int) -> dict:
        from xar_autoplayer.bridge.normal_exit_contract_v1 import normalize_query_arguments
        normalize_query_arguments({"expected_revision": expected_revision})
        with self._lock:
            before = self._bound_frame(expected_revision, paused=True)
            gameplay = self._gameplay_service()
            self.driver.normal_exit_managed_profile = self.profile
            result = gameplay.query_normal_exit_context_v1(expected_revision=expected_revision)
            after = self._bound_frame(expected_revision, paused=True)
            return self._receipt("normal-exit-query", {"status": result["status"], "result": result,
                "snapshot_before": before, "snapshot_after": after,
                "uses_ocr": False, "uses_desktop_input": False, "uses_injection": False})

    def request_normal_exit(self, action: str, expected_revision: int,
                            expected_exit_context_signature: str) -> dict:
        from xar_autoplayer.bridge.normal_exit_contract_v1 import normalize_request_arguments
        normalize_request_arguments({"action": action, "expected_revision": expected_revision,
                                     "expected_exit_context_signature": expected_exit_context_signature})
        with self._lock:
            before = self._bound_frame(expected_revision, paused=True)
            gameplay = self._gameplay_service()
            self.driver.normal_exit_managed_profile = self.profile
            self.backend.poll(self.profile)
            self._bound_frame(expected_revision, paused=True)
            result = gameplay.request_normal_exit_v1(action, expected_revision=expected_revision,
                expected_exit_context_signature=expected_exit_context_signature)
            # Terminal process facts remain readable after the pipe disappears.
            # Do not call guard/snapshot/ordinary-action after this submission.
            return self._receipt("normal-exit-" + action, {"status": result["status"],
                "result": result, "snapshot_before": before, "snapshot_after_required": False,
                "uses_ocr": False, "uses_desktop_input": False, "uses_injection": False})

    def query_stress_adjustment(self, base_amount: int, expected_revision: int) -> dict:
        from xar_autoplayer.bridge.current_actor_stress_adjustment_contract import (
            validate_base_amount, stress_query_binding, same_stress_query_frame, normalize_public_stress_query,
        )
        validate_base_amount(base_amount)
        with self._lock:
            before = self._bound_frame(expected_revision, paused=True)
            binding = stress_query_binding(before, expected_revision)
            result = self._gameplay_service().query_current_actor_stress_adjustment_v1(
                base_amount, expected_revision=expected_revision)
            after = self._bound_frame(expected_revision, paused=True)
            if not same_stress_query_frame(before, after, binding):
                raise RuntimeError("profile stress getter changed its actual player/frame")
            result = normalize_public_stress_query(result, binding, base_amount)
            return self._receipt("stress-adjustment-query", {
                "status": ("native_stress_adjustment_observed" if result["current_actor_stress_adjustment_ready"]
                           else "native_stress_adjustment_unavailable"),
                "result": result, "business_effects_verified": False, "full_product_acceptance_credit": False,
            })

    def query_event(self, event_instance_id: int, expected_revision: int) -> dict:
        with self._lock:
            self._bound_frame(expected_revision, paused=True)
            result = self._gameplay_service().query_current_event_window_context_v1(
                event_instance_id, expected_revision=expected_revision)
            self._bound_frame(expected_revision, paused=True)
            return self._receipt("event-query", {"status": "native_event_query_verified", "result": result})

    def query_decision(self, decision_key: str, expected_revision: int) -> dict:
        with self._lock:
            self._bound_frame(expected_revision, paused=True)
            result = self._gameplay_service().query_ingame_decision_item_v1(
                decision_key, expected_revision=expected_revision)
            self._bound_frame(expected_revision, paused=True)
            return self._receipt("decision-query", {"status": "native_decision_query_observed", "result": result,
                "business_effects_verified": False, "full_product_acceptance_credit": False})

    def decision_action(self, action: str, expected_revision: int, *, decision_key: str | None = None,
                        expected_outcome: str | None = None,
                        expected_event_definition_key: str | None = None) -> dict:
        from xar_autoplayer.bridge.ingame_decision_item_contract import validate_decision_key
        from xar_autoplayer.bridge.ingame_decision_outcome_contract import (
            SCHEMA, validate_expected_outcome, actual_expected_event, actual_closed_decision_detail,
        )
        if action not in {"open", "select", "confirm_outcome"}:
            raise ValueError("unsupported typed profile decision action")
        if action != "open":
            validate_decision_key(decision_key)
        if action == "confirm_outcome":
            validate_expected_outcome(expected_outcome, expected_event_definition_key)
        def invoke(gameplay):
            if action == "open":
                return gameplay.open_ingame_decisions_v1(expected_revision=expected_revision)
            if action == "select":
                return gameplay.select_ingame_decision_item_v1(decision_key, expected_revision=expected_revision)
            return gameplay.confirm_ingame_decision_outcome_v1(
                decision_key, expected_outcome, expected_event_definition_key=expected_event_definition_key,
                expected_revision=expected_revision)
        def verify(result, before, after):
            if (not isinstance(result, dict) or result.get("postcondition_verified") is not True
                    or result.get("verification_pending") is not False):
                raise _PostconditionPending("profile decision dispatch lacks an independently observed UI outcome")
            actor = before.get("played_character", {}).get("character_id")
            if (type(actor) is not int or actor <= 0
                    or before.get("played_character", {}).get("alive") is not True
                    or after.get("paused") is not True or before.get("date_raw") != after.get("date_raw")
                    or before.get("speed") != after.get("speed")
                    or before.get("played_character", {}).get("character_id") != after.get("played_character", {}).get("character_id")):
                raise RuntimeError("profile decision outcome changed its actor/date/paused frame")
            if action != "open" and result.get("decision_key") != decision_key:
                raise RuntimeError("profile decision outcome changed its actual definition")
            if action == "confirm_outcome":
                expected_key = expected_event_definition_key if expected_outcome == "event_window" else ""
                if (result.get("schema") != SCHEMA or result.get("action") != "confirm_outcome"
                        or result.get("expected_outcome") != expected_outcome
                        or result.get("expected_event_definition_key") != expected_key
                        or result.get("business_effects_verified") is not False
                        or result.get("full_product_acceptance_credit") is not False
                        or result.get("front_event_verified") is not False
                        or result.get("event_option_selection_authorized") is not False):
                    raise RuntimeError("profile generic Confirm returned a mismatched or overcredited outcome")
                proved = result.get("snapshot_after")
                if (not isinstance(proved, dict) or proved.get("active_event") != after.get("active_event")
                        or proved.get("native_revision") != after.get("native_revision")
                        or proved.get("revision") != after.get("revision")):
                    raise RuntimeError("profile generic Confirm actual readback no longer matches the current event frame")
                binding = {"date_raw": before["date_raw"], "played_character_id": actor}
                observation = result.get("later_actual_observation")
                verified = (actual_expected_event(observation, after, binding, expected_key)
                            if expected_outcome == "event_window" else
                            after.get("active_event") is None and actual_closed_decision_detail(observation))
                if not verified:
                    raise RuntimeError("profile generic Confirm lacks its actual declared outcome observation")
        return self._ordinary_action("decision-" + action, expected_revision, invoke, verify, paused=True)

    def query_pending_interaction(self, pending_interaction_id: int, expected_revision: int) -> dict:
        from xar_autoplayer.bridge.pending_character_interaction_context_contract import normalize_pending_interaction_id
        pending_interaction_id = normalize_pending_interaction_id(pending_interaction_id)
        with self._lock:
            before = self._bound_frame(expected_revision, paused=True)
            pending = before.get("pending_character_interaction")
            if not isinstance(pending, dict) or pending.get("instance_id") != pending_interaction_id:
                raise RuntimeError("pending interaction ID is not the current native profile frame")
            result = self._gameplay_service().query_pending_character_interaction_context_v1(
                pending_interaction_id, expected_revision=expected_revision)
            after = self._bound_frame(expected_revision, paused=True)
            if after.get("pending_character_interaction") != pending:
                raise RuntimeError("pending interaction changed during profile query")
            return self._receipt("pending-query", {"status": "native_pending_query_verified", "result": result,
                "snapshot_before": before, "snapshot_after": after, "uses_injection": False,
                "uses_ocr": False, "uses_desktop_input": False})

    def _ordinary_action(self, operation: str, expected_revision: int, invoke, verify, *, paused: bool = False) -> dict:
        with self._lock:
            before = self._bound_frame(expected_revision, paused=paused)
            gameplay = self._gameplay_service()
            self.backend.poll(self.profile)
            self._bound_frame(expected_revision, paused=paused)
            try:
                result = invoke(gameplay)
                after, observation = self._wait_postcondition(result, before, verify)
                return self._receipt(operation, {"status": "native_gameplay_postcondition_verified",
                    "result": result, "snapshot_before": before, "snapshot_after": after,
                    "observation_after": observation, "uses_ocr": False, "uses_desktop_input": False})
            except Exception as error:
                # A submitted action is never replayed here. Preserve failures
                # even when the native postcondition or foreground guard fails.
                return self._receipt(operation, {"status": "RED", "snapshot_before": before,
                    "reason": f"{type(error).__name__}: {error}"})

    def _wait_postcondition(self, result: dict, before: dict, verify) -> tuple[dict, dict]:
        deadline = time.monotonic() + self._postcondition_timeout_seconds
        while True:
            self.guard()
            after = self._snapshot()
            observation = self.guard()
            if after.get("map_ready") is not True:
                raise RuntimeError("native postcondition frame is not map-ready")
            try:
                verify(result, before, after)
                return after, observation
            except _PostconditionPending:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise
                # Polling only reads native state and profile guards. It never
                # resends the command or changes a caller's operation/revision.
                time.sleep(min(self._postcondition_poll_seconds, remaining))

    def simulation(self, action: str, expected_revision: int) -> dict:
        steps = {"pause": "pause-map", "resume": "resume-map",
                 "speed_1": "set-speed-1", "speed_3": "set-speed-3", "speed_5": "set-speed-5"}
        if action not in steps:
            raise ValueError("unsupported ordinary simulation action")
        def verify(result, before, after):
            if action in {"pause", "resume"} and after["paused"] is not (action == "pause"):
                raise _PostconditionPending("native pause/resume postcondition did not materialize before deadline")
            if action.startswith("speed_") and after["speed"] != int(action[-1]):
                raise _PostconditionPending("native speed postcondition did not materialize before deadline")
        return self._ordinary_action("simulation-" + action, expected_revision,
            lambda service: service.execute_step(steps[action], expected_revision=expected_revision), verify)

    def pause_current(self) -> dict:
        """Pause the bound live campaign using the provider's submission frame."""
        with self._lock:
            self.guard()
            gameplay = self._gameplay_service()
            self.backend.poll(self.profile)
            self.guard()
            before = self._snapshot()
            if (before.get("map_ready") is not True or type(before.get("revision")) is not int
                    or before["revision"] < 0):
                raise RuntimeError("current native pause requires a map-ready native revision")
            try:
                # This stateless desired-state command is the sole exception to
                # caller revision matching. The existing provider binds its own
                # fresh native submission frame; event/save/resume remain strict.
                result = gameplay.execute_step("pause-map", expected_revision=None)
                def verify_pause(result, before, after):
                    if after["date_raw"] < before["date_raw"]:
                        raise RuntimeError("current native pause raw date moved backwards")
                    if after["paused"] is not True:
                        raise _PostconditionPending("current native pause postcondition did not materialize before deadline")
                after, observation = self._wait_postcondition(result, before, verify_pause)
                return self._receipt("simulation-pause-current", {
                    "status": "native_gameplay_postcondition_verified", "result": result,
                    "snapshot_before": before, "snapshot_after": after,
                    "observation_after": observation, "revision_binding": "provider_submission_frame",
                    "uses_ocr": False, "uses_desktop_input": False})
            except Exception as error:
                # Never resend after a command ACK, timeout or failed readback.
                return self._receipt("simulation-pause-current", {"status": "RED",
                    "snapshot_before": before, "reason": f"{type(error).__name__}: {error}"})

    def select_event(self, option_number: int, event_instance_id: int, expected_revision: int) -> dict:
        if type(option_number) is not int or not 1 <= option_number <= 64:
            raise ValueError("option_number must be a public 1-based option ordinal")
        if type(event_instance_id) is not int or not 1 <= event_instance_id <= 2**31 - 1:
            raise ValueError("event_instance_id must be a positive full int32")
        def verify(result, before, after):
            active = after.get("active_event")
            if isinstance(active, dict) and active.get("instance_id") == event_instance_id:
                raise _PostconditionPending("selected event is still active after its native ACK before deadline")
        return self._ordinary_action("event-select", expected_revision,
            lambda service: service.select_event_option(option_number, event_instance_id=event_instance_id,
                                                        expected_revision=expected_revision), verify, paused=True)

    def reply_pending_interaction(self, accept: bool, pending_interaction_id: int, expected_revision: int) -> dict:
        from xar_autoplayer.bridge.pending_character_interaction_context_contract import normalize_pending_interaction_id
        if type(accept) is not bool:
            raise ValueError("accept must be a boolean")
        pending_interaction_id = normalize_pending_interaction_id(pending_interaction_id)
        with self._lock:
            frame = self._bound_frame(expected_revision, paused=True)
            pending = frame.get("pending_character_interaction")
            if not isinstance(pending, dict) or pending.get("instance_id") != pending_interaction_id:
                raise RuntimeError("pending interaction ID is not the current native profile frame")
            def verify(result, before, after):
                remaining = after.get("pending_character_interaction")
                if isinstance(remaining, dict) and remaining.get("instance_id") == pending_interaction_id:
                    raise _PostconditionPending("replied interaction is still pending after its native ACK before deadline")
                if after.get("paused") is not True or after["date_raw"] != before["date_raw"]:
                    raise RuntimeError("pending interaction reply did not retain the paused campaign date")
            return self._ordinary_action("pending-reply", expected_revision,
                lambda service: service.reply_pending_character_interaction(accept=accept,
                    interaction_instance_id=pending_interaction_id, expected_revision=expected_revision),
                verify, paused=True)

    def checkpoint(self, expected_revision: int) -> dict:
        def verify(result, before, after):
            checkpoint = result.get("checkpoint", {})
            path = Path(checkpoint.get("path", ""))
            expected_dir = (Path(self.profile["userdir"]) / "save games").resolve()
            if (checkpoint.get("status") != "saved" or not path.is_absolute()
                    or path.resolve().parent != expected_dir or not path.is_file()
                    or type(checkpoint.get("size")) is not int or checkpoint["size"] <= 0
                    or path.stat().st_size != checkpoint["size"]
                    or desktop.sha256(path).lower() != str(checkpoint.get("sha256", "")).lower()
                    or checkpoint.get("date_raw") != before["date_raw"]):
                raise RuntimeError("native checkpoint bytes/path/date did not materialize in the isolated userdir")
        return self._ordinary_action("checkpoint", expected_revision,
            lambda service: service.save_checkpoint(expected_revision=expected_revision), verify, paused=True)

    def close(self) -> None:
        if self.driver is not None:
            self.driver.close()


class NativeClockProfileService(NativeProfileService):
    def clock(self) -> dict:
        with self._lock:
            self.guard()
            clock = self.backend.read_clock(self.profile)
            after = self.guard()
            return self._receipt("clock", {"status": "native_clock_verified", "clock": clock,
                                            "observation_after": after,
                                            "uses_ocr": False, "uses_desktop_input": False,
                                            "uses_injection": False, "writes_process_memory": False})


def create_clock_server(service: NativeClockProfileService):
    from mcp.server import MCPServer
    from mcp.types import ToolAnnotations
    server = MCPServer("CK3 frozen native clock")
    @server.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def ck3_read_profile_native_clock_v1() -> dict[str, object]:
        return service.clock()
    _forbid_unknown_tool_arguments_v1(server, "ck3_read_profile_native_clock_v1")
    return server


def create_server(service: NativeProfileService):
    from mcp.server import MCPServer
    from mcp.types import ToolAnnotations
    server = MCPServer("CK3 frozen native profile")
    @server.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def ck3_query_native_profile_v1() -> dict[str, object]:
        return service.inspect()
    @server.tool(annotations=ToolAnnotations(readOnlyHint=False))
    def ck3_attach_profile_bridge_v1() -> dict[str, object]:
        return service.attach()
    @server.tool(annotations=ToolAnnotations(readOnlyHint=False))
    def ck3_resume_profile_bridge_v1() -> dict[str, object]:
        return service.resume()
    @server.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def ck3_take_profile_native_snapshot_v1() -> dict[str, object]:
        return service.snapshot()
    @server.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False))
    def ck3_query_profile_character_interaction_ordinary_v1(
        interaction_key: OrdinaryInteractionKeyV1, recipient_id: OrdinaryRecipientIdV1,
        expected_revision: StressQueryRevisionV1,
    ) -> dict[str, object]:
        return service.query_ordinary_interaction(interaction_key, recipient_id, expected_revision)
    @server.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=False, openWorldHint=False))
    def ck3_initiate_profile_character_interaction_ordinary_v1(
        interaction_key: OrdinaryInteractionKeyV1, recipient_id: OrdinaryRecipientIdV1,
        expected_revision: StressQueryRevisionV1,
    ) -> dict[str, object]:
        return service.initiate_ordinary_interaction(interaction_key, recipient_id, expected_revision)
    @server.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False))
    def ck3_observe_profile_normal_exit_v1() -> dict[str, object]:
        return service.observe_normal_exit()
    @server.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False))
    def ck3_query_normal_exit_context_v1(expected_revision: NormalExitRevisionV1) -> dict[str, object]:
        return service.query_normal_exit_context(expected_revision)
    @server.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=False, openWorldHint=False))
    def ck3_request_normal_exit_v1(
        action: Literal["prepare_confirmation", "continue_preparation", "confirm_desktop"], expected_revision: NormalExitRevisionV1,
        expected_exit_context_signature: NormalExitSignatureV1,
    ) -> dict[str, object]:
        return service.request_normal_exit(action, expected_revision, expected_exit_context_signature)
    @server.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False))
    def ck3_query_profile_current_actor_stress_adjustment_v1(
        base_amount: StressBaseAmountV1, expected_revision: StressQueryRevisionV1,
    ) -> dict[str, object]:
        """Read actual current-player stress adjustment without applying stress."""
        return service.query_stress_adjustment(base_amount, expected_revision)
    @server.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def ck3_query_profile_event_window_v1(event_instance_id: int, expected_revision: int) -> dict[str, object]:
        return service.query_event(event_instance_id, expected_revision)
    @server.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def ck3_query_profile_pending_interaction_v1(pending_interaction_id: int, expected_revision: int) -> dict[str, object]:
        return service.query_pending_interaction(pending_interaction_id, expected_revision)
    @server.tool(annotations=ToolAnnotations(readOnlyHint=False))
    def ck3_reply_profile_pending_interaction_v1(accept: bool, pending_interaction_id: int, expected_revision: int) -> dict[str, object]:
        return service.reply_pending_interaction(accept, pending_interaction_id, expected_revision)
    @server.tool(annotations=ToolAnnotations(readOnlyHint=False))
    def ck3_set_profile_simulation_v1(
        action: Literal["pause", "resume", "speed_1", "speed_3", "speed_5"], expected_revision: int,
    ) -> dict[str, object]:
        return service.simulation(action, expected_revision)
    @server.tool(annotations=ToolAnnotations(readOnlyHint=False))
    def ck3_pause_profile_simulation_v1() -> dict[str, object]:
        return service.pause_current()
    @server.tool(annotations=ToolAnnotations(readOnlyHint=False))
    def ck3_select_profile_event_option_v1(option_number: int, event_instance_id: int, expected_revision: int) -> dict[str, object]:
        return service.select_event(option_number, event_instance_id, expected_revision)
    @server.tool(annotations=ToolAnnotations(readOnlyHint=False))
    def ck3_save_profile_checkpoint_v1(expected_revision: int) -> dict[str, object]:
        return service.checkpoint(expected_revision)
    @server.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def ck3_query_profile_decision_item_v1(decision_key: str, expected_revision: int) -> dict[str, object]:
        return service.query_decision(decision_key, expected_revision)
    @server.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=False))
    def ck3_open_profile_decisions_v1(expected_revision: int) -> dict[str, object]:
        return service.decision_action("open", expected_revision)
    @server.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=False))
    def ck3_select_profile_decision_item_v1(decision_key: str, expected_revision: int) -> dict[str, object]:
        return service.decision_action("select", expected_revision, decision_key=decision_key)
    @server.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=False))
    def ck3_confirm_profile_decision_outcome_v1(
        decision_key: str, expected_outcome: Literal["event_window", "decision_closed"],
        expected_revision: int, expected_event_definition_key: str | None = None,
    ) -> dict[str, object]:
        return service.decision_action("confirm_outcome", expected_revision, decision_key=decision_key,
            expected_outcome=expected_outcome, expected_event_definition_key=expected_event_definition_key)
    for name in ("ck3_query_profile_character_interaction_ordinary_v1",
                  "ck3_initiate_profile_character_interaction_ordinary_v1",
                  "ck3_observe_profile_normal_exit_v1",
                  "ck3_query_normal_exit_context_v1", "ck3_request_normal_exit_v1",
                  "ck3_query_profile_current_actor_stress_adjustment_v1",
                 "ck3_query_profile_decision_item_v1", "ck3_open_profile_decisions_v1",
                 "ck3_select_profile_decision_item_v1", "ck3_confirm_profile_decision_outcome_v1",
                 "ck3_query_native_profile_v1", "ck3_attach_profile_bridge_v1", "ck3_resume_profile_bridge_v1", "ck3_take_profile_native_snapshot_v1",
                 "ck3_query_profile_event_window_v1", "ck3_set_profile_simulation_v1",
                 "ck3_query_profile_pending_interaction_v1",
                 "ck3_reply_profile_pending_interaction_v1",
                 "ck3_pause_profile_simulation_v1",
                 "ck3_select_profile_event_option_v1", "ck3_save_profile_checkpoint_v1"):
        _forbid_unknown_tool_arguments_v1(server, name)
    return server


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--clock-only", action="store_true")
    args = parser.parse_args()
    if args.clock_only:
        create_clock_server(NativeClockProfileService(load_clock_profile(args.profile))).run(transport="stdio")
        return
    service = NativeProfileService(load_profile(args.profile))
    try:
        create_server(service).run(transport="stdio")
    finally:
        service.close()


if __name__ == "__main__":
    main()
