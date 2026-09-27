#!/usr/bin/env python3
"""Preflight or arm a passive War31 two-site hardware probe.

This never starts CK3 or submits surrender. `capture` only attaches to the
explicit, source-matched PID after an external authorization receipt exists.
Debug attachment changes execution timing and thread debug registers.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

import psutil


ROOT = Path(__file__).resolve().parents[3]
ASSEMBLER = Path(__file__).with_name("assemble_war31_hwprobe_trace.py")
EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
CHECKPOINT_SHA256 = "1AF4055F978AF60267FB3A0D8658224047CD6BFDA884C66886A13B74EE34A90A"
SOURCE_DRIVER_STATE_SHA256 = "1DE61CF0AC47EDD1D63FE1F3D77668D5F499EA6CA06B90BC83B068CF35F16336"
BRIDGE_DLL_SHA256 = "C36ECCEB67A0DCA7C8C1C6C855A5036771B46617E9F1BF5F4185D965C1951BCE"
DATE_RAW = 53215920
REQUEST_ID = "WAR-INPUT-R0221-WAR31-20260927"
WAR_ID = 16777231
EPISODE = "native-29829-2bc2d599f7f9"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _assembler():
    spec = importlib.util.spec_from_file_location(ASSEMBLER.stem, ASSEMBLER)
    if spec is None or spec.loader is None:
        raise RuntimeError("War31 trace assembler unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _receipt(value: dict[str, object], manifest: dict[str, object]) -> None:
    required = {
        "schema": "xar.ck3.war31.single_action_authorization.v1",
        "request_id": REQUEST_ID,
        "war_id": WAR_ID,
        "episode_run_id": EPISODE,
        "action_attempt_id": manifest["action_attempt_id"],
        "approved_action_step": "surrender-war-16777231",
        "authorization_status": "authorized",
    }
    if not isinstance(value, dict) or any(value.get(k) != v for k, v in required.items()):
        raise ValueError("authorization receipt lacks the exact War31 single-action assertion")
    if not isinstance(value.get("authorization_source"), str) or not value["authorization_source"].strip():
        raise ValueError("authorization receipt lacks its external source")


def _positive_int(value: object, field: str) -> None:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{field} must be a positive integer")


def _hash_string(value: object, field: str) -> None:
    if not isinstance(value, str) or re.fullmatch(r"[A-F0-9]{64}", value) is None:
        raise ValueError(f"{field} must be an uppercase SHA-256 hex string")


def _verify_rebound_driver(
    source_path: Path, rebound_path: Path, receipt_path: Path,
    environment_path: Path,
    identities: dict[str, object],
) -> None:
    """Require the target driver to differ only by the official lifecycle rebind."""
    receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
    driver = receipt.get("driver_state") if isinstance(receipt, dict) else None
    save = receipt.get("save") if isinstance(receipt, dict) else None
    environment = receipt.get("environment") if isinstance(receipt, dict) else None
    if (
        not isinstance(driver, dict) or not isinstance(save, dict)
        or not isinstance(environment, dict)
        or receipt.get("schema") != "xar.ck3.ordinary-seed-rebind/v1"
        or receipt.get("status") != "rebound" or receipt.get("ok") is not True
        or driver.get("source_sha256", "").upper() != SOURCE_DRIVER_STATE_SHA256
        or driver.get("target_sha256", "").upper()
        != identities["driver_state"]["sha256"]
        or save.get("bytes_unchanged") is not True
        or not isinstance(save.get("source"), dict)
        or not isinstance(save.get("target"), dict)
        or save["source"].get("sha256", "").upper() != CHECKPOINT_SHA256
        or save["target"].get("sha256", "").upper() != CHECKPOINT_SHA256
    ):
        raise ValueError("rebind receipt does not connect frozen source and derived driver")
    source = json.loads(source_path.read_text(encoding="utf-8-sig"))
    rebound = json.loads(rebound_path.read_text(encoding="utf-8-sig"))
    current_environment = json.loads(environment_path.read_text(encoding="utf-8-sig"))
    if (not isinstance(source, dict) or not isinstance(rebound, dict)
            or not isinstance(current_environment, dict)):
        raise ValueError("source, derived driver or environment is not a JSON object")
    pipe = source.get("pipe_name")
    if not isinstance(pipe, str) or not pipe or pipe != rebound.get("pipe_name"):
        raise ValueError("derived driver changed the source bridge pipe")
    if receipt.get("pipe_name") != pipe:
        raise ValueError("rebind receipt bridge pipe differs from source driver")
    source_binding = source.get("succession_lifecycle")
    target_binding = rebound.get("succession_lifecycle")
    if (
        not isinstance(source_binding, dict)
        or not isinstance(target_binding, dict)
        or environment.get("source_sha256") != source_binding.get("environment_sha256")
        or environment.get("target_sha256") != target_binding.get("environment_sha256")
        or current_environment.get("environment_sha256") != environment.get("target_sha256")
        or current_environment.get("environment_sha256") == environment.get("source_sha256")
    ):
        raise ValueError("sidecar is not the newly prepared environment bound by rebind")
    source_checkpoint = source.get("last_checkpoint")
    if (
        source.get("format_version") != 2
        or source.get("episode_character_id") != 29829
        or source.get("episode_run_id") != EPISODE
        or not isinstance(source_checkpoint, dict)
        or source_checkpoint.get("sha256", "").upper() != CHECKPOINT_SHA256
        or source_checkpoint.get("date_raw") != DATE_RAW
        or source_checkpoint.get("history_index") != 2134
    ):
        raise ValueError("source driver lacks the frozen R0197 checkpoint anchor")
    expected = copy.deepcopy(source)
    try:
        binding = rebound["succession_lifecycle"]
        if (not isinstance(binding, dict)
                or binding.get("lifecycle") != "ordinary_campaign_succession"
                or binding.get("xar_enabled") != "xar_off"):
            raise ValueError("derived driver lacks the ordinary xar_off lifecycle")
        expected["succession_lifecycle"] = copy.deepcopy(binding)
        expected["last_checkpoint"]["succession_lifecycle"] = copy.deepcopy(binding)
        anchor = expected["command_history"][2133]
        if anchor.get("command") != "save-checkpoint" or anchor.get("index") != 2134:
            raise ValueError("source driver has the wrong history anchor")
        anchor["result"]["checkpoint"]["succession_lifecycle"] = copy.deepcopy(binding)
    except (IndexError, KeyError, TypeError) as error:
        raise ValueError("source driver has an incomplete rebind anchor") from error
    if rebound != expected:
        raise ValueError("derived driver changed fields outside the three lifecycle anchors")


def preflight_assets(args: argparse.Namespace) -> tuple[dict[str, object], dict[str, object]]:
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("schema") != "xar.ck3.war31.hwprobe_manifest.v1":
        raise ValueError("wrong War31 hardware-probe manifest")
    if (manifest.get("request_id") != REQUEST_ID or manifest.get("war_id") != WAR_ID
            or manifest.get("episode_run_id") != EPISODE
            or manifest.get("ck3_exe_sha256") != EXE_SHA256):
        raise ValueError("manifest differs from frozen War31/exact executable")
    for key, frozen in (
        ("bridge_dll_sha256", BRIDGE_DLL_SHA256),
        ("checkpoint_sha256", CHECKPOINT_SHA256),
        ("source_driver_state_sha256", SOURCE_DRIVER_STATE_SHA256),
    ):
        if manifest.get(key) != frozen:
            raise ValueError(f"{key} differs from frozen R0197/R0221 source")
    if manifest.get("date_raw") != DATE_RAW:
        raise ValueError("date_raw differs from frozen R0197/R0221 frame")
    if manifest.get("approved_action_step") != "surrender-war-16777231":
        raise ValueError("manifest does not identify the one authorized action")
    if manifest.get("source_evidence_status") != "separately_authorized_unverified_by_probe":
        raise ValueError("manifest does not state the external evidence boundary")
    for field in ("date_raw", "expected_pid", "expected_process_created_filetime"):
        _positive_int(manifest.get(field), field)
    for field in ("action_attempt_id", "effect_invocation_id", "frame_token"):
        if not isinstance(manifest.get(field), str) or not manifest[field].strip():
            raise ValueError(f"manifest lacks {field}")
    files = {
        "ck3_exe": (args.game_exe, "ck3_exe_sha256"),
        "bridge_dll": (args.bridge_dll, "bridge_dll_sha256"),
        "checkpoint": (args.checkpoint, "checkpoint_sha256"),
        "source_driver_state": (args.source_driver_state,
                                "source_driver_state_sha256"),
        "driver_state": (args.driver_state, "driver_state_sha256"),
        "rebind_receipt": (args.rebind_receipt, "rebind_receipt_sha256"),
        "sidecar": (args.sidecar, "sidecar_sha256"),
        "sampler": (args.probe, "sampler_sha256"),
        "authorization_receipt": (args.authorization_receipt,
                                  "authorization_receipt_sha256"),
    }
    identities = {}
    for label, (path, key) in files.items():
        _hash_string(manifest.get(key), key)
        if not path.is_file():
            raise ValueError(f"missing {label}: {path}")
        actual = _sha256(path)
        if actual != manifest.get(key):
            raise ValueError(f"{label} SHA-256 differs from manifest")
        identities[label] = {"path": str(path.resolve()), "sha256": actual,
                             "size": path.stat().st_size}
    authorization = json.loads(args.authorization_receipt.read_text(encoding="utf-8"))
    _receipt(authorization, manifest)
    _verify_rebound_driver(args.source_driver_state, args.driver_state,
                           args.rebind_receipt, args.sidecar, identities)
    return manifest, identities


def inspect_live(args: argparse.Namespace, manifest: dict[str, object]) -> dict[str, object]:
    if args.pid is None or args.pid <= 0 or args.pid > 0xFFFFFFFF:
        raise ValueError("an explicit positive CK3 PID is required")
    process = psutil.Process(args.pid)
    if not Path(process.exe()).samefile(args.game_exe):
        raise ValueError("PID executable path differs from exact game executable")
    result = subprocess.run([str(args.probe), "--inspect-pid", str(args.pid)],
                            capture_output=True, text=True, encoding="utf-8",
                            errors="replace", timeout=10)
    if result.returncode:
        raise RuntimeError(f"read-only PID/anchor inspect failed: {result.stderr[-500:]}")
    identity = json.loads(result.stdout)
    if (identity.get("schema") != "xar.ck3.war31.hwprobe_inspect.v1"
            or identity.get("pid") != manifest.get("expected_pid")
            or identity.get("process_created_filetime") != manifest.get("expected_process_created_filetime")
            or identity.get("exact_in_memory_sites") is not True
            or identity.get("attached") is not False):
        raise ValueError("live PID creation identity or exact instruction anchors differ")
    return identity


def _write_new(path: Path, value: dict[str, object]) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as target:
        json.dump(value, target, indent=2, ensure_ascii=False)
        target.write("\n")


def capture(args: argparse.Namespace, manifest: dict[str, object],
            identities: dict[str, object], live: dict[str, object]) -> int:
    if not args.arm:
        raise ValueError("capture requires the explicit --arm flag")
    if args.attempt is None or args.attempt.exists():
        raise ValueError("fresh attempt directory is required and must not exist")
    if args.timeout_ms < 1000 or args.timeout_ms > 300000:
        raise ValueError("timeout_ms is outside the probe's bounded range")
    args.attempt.mkdir(parents=True, exist_ok=False)
    _write_new(args.attempt / "preflight.json", {
        "schema": "xar.ck3.war31.hwprobe_preflight.v1",
        "source_assertions_not_authenticated_by_probe": True,
        "manifest_sha256": _sha256(args.manifest),
        "assets": identities, "live_inspect": live,
        "action_attempt_id": manifest["action_attempt_id"],
        "probe_submits_gameplay_action": False,
    })
    raw = args.attempt / "raw.ndjson"
    ready = args.attempt / "probe-ready.json"
    command = [str(args.probe), "--pid", str(args.pid),
               "--timeout-ms", str(args.timeout_ms), "--raw", str(raw),
               "--ready", str(ready)]
    with (args.attempt / "probe-stdout.txt").open("wb") as stdout, \
         (args.attempt / "probe-stderr.txt").open("wb") as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr,
                                   creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        started = time.monotonic()
        while not ready.exists() and process.poll() is None and time.monotonic() - started < 15:
            time.sleep(0.05)
        if ready.exists():
            print(json.dumps({"status": "armed", "ready": str(ready),
                              "action_attempt_id": manifest["action_attempt_id"]}), flush=True)
        try:
            returncode = process.wait(timeout=args.timeout_ms / 1000 + 20)
        except subprocess.TimeoutExpired:
            # Request the sampler's own DR-clear-and-detach path. Never claim
            # cleanup GREEN merely because a process termination was observed.
            process.send_signal(signal.CTRL_BREAK_EVENT)
            try:
                returncode = process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                _write_new(args.attempt / "manual-recovery-required.json", {
                    "status": "red", "reason": "sampler_hung_after_control_break",
                    "sampler_pid": process.pid, "ck3_pid": args.pid,
                    "debugger_cleanup_proven": False,
                })
                raise RuntimeError("sampler hung; preserve process and coordinate manual recovery")

    raw_digest = _sha256(raw) if raw.is_file() else None
    report: dict[str, object] = {
        "schema": "xar.ck3.war31.hwprobe_attempt.v1",
        "status": "red", "sampler_exit": returncode,
        "raw_path": str(raw), "raw_sha256": raw_digest,
        "ready_path": str(ready) if ready.exists() else None,
        "paired_trace_path": None, "action_submitted_by_probe": False,
        "capture_authenticity": "REQUIRES_EXTERNAL_FORMAL_PAIRING",
    }
    ready_valid = False
    if ready.is_file():
        try:
            ready_value = json.loads(ready.read_text(encoding="utf-8"))
            ready_valid = (
                ready_value.get("schema") == "xar.ck3.war31.hwprobe_ready.v1"
                and ready_value.get("pid") == args.pid
                and ready_value.get("site_0") == "0x2E9F746"
                and ready_value.get("site_1") == "0x2EC4410"
                and ready_value.get("module_base") == live.get("module_base")
            )
        except (OSError, UnicodeError, json.JSONDecodeError, AttributeError):
            ready_valid = False
    if returncode == 0 and raw.is_file() and ready_valid:
        try:
            assembled = _assembler().assemble(raw.read_bytes(), manifest)
            paired_path = args.attempt / "paired-trace.json"
            _write_new(paired_path, assembled)
        except (ValueError, OSError, RuntimeError) as error:
            report["reason"] = f"offline_pair_rejected: {error}"
        else:
            report["status"] = "structural_pair_only"
            report["paired_trace_path"] = str(paired_path)
    elif returncode == 0 and not ready_valid:
        report["reason"] = "missing_or_mismatched_probe_ready_receipt"
    if report["status"] == "structural_pair_only":
        changed = []
        for label, (path, _) in {
            "ck3_exe": (args.game_exe, "ck3_exe_sha256"),
            "bridge_dll": (args.bridge_dll, "bridge_dll_sha256"),
            "checkpoint": (args.checkpoint, "checkpoint_sha256"),
            "source_driver_state": (args.source_driver_state,
                                    "source_driver_state_sha256"),
            "driver_state": (args.driver_state, "driver_state_sha256"),
            "rebind_receipt": (args.rebind_receipt, "rebind_receipt_sha256"),
            "sidecar": (args.sidecar, "sidecar_sha256"),
            "sampler": (args.probe, "sampler_sha256"),
            "authorization_receipt": (args.authorization_receipt,
                                      "authorization_receipt_sha256"),
            "manifest": (args.manifest, None),
        }.items():
            expected = (identities[label]["sha256"] if label != "manifest"
                        else json.loads((args.attempt / "preflight.json").read_text(encoding="utf-8"))["manifest_sha256"])
            if not path.is_file() or _sha256(path) != expected:
                changed.append(label)
        if changed:
            report["status"] = "red"
            report["reason"] = "source_bytes_changed_during_attempt: " + ", ".join(changed)
    _write_new(args.attempt / "report.json", report)
    print(json.dumps({"status": report["status"], "report": str(args.attempt / "report.json")}))
    return 0 if report["status"] == "structural_pair_only" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("assets", "live", "capture"), required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--authorization-receipt", type=Path, required=True)
    parser.add_argument("--game-exe", type=Path, required=True)
    parser.add_argument("--bridge-dll", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--source-driver-state", type=Path, required=True)
    parser.add_argument("--driver-state", type=Path, required=True)
    parser.add_argument("--rebind-receipt", type=Path, required=True)
    parser.add_argument("--sidecar", type=Path, required=True)
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--pid", type=int)
    parser.add_argument("--attempt", type=Path)
    parser.add_argument("--timeout-ms", type=int, default=120000)
    parser.add_argument("--arm", action="store_true")
    args = parser.parse_args()
    manifest, identities = preflight_assets(args)
    if args.mode == "assets":
        print(json.dumps({"status": "assets_only", "assets": identities,
                          "game_started": False, "attached": False}))
        return 0
    live = inspect_live(args, manifest)
    if args.mode == "live":
        print(json.dumps({"status": "live_readonly_preflight", "identity": live,
                          "attached": False}))
        return 0
    return capture(args, manifest, identities, live)


if __name__ == "__main__":
    raise SystemExit(main())
