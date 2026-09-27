#!/usr/bin/env python3
"""Bind an experimental War31 hardware-probe raw stream to a source manifest.

This runs offline. A structurally paired stream is not authenticated CK3 or
permission to submit a surrender; formal action evidence remains separate.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = Path(__file__).with_name("validate_war31_change_type_trace.py")
CHECKPOINT_SHA256 = "1AF4055F978AF60267FB3A0D8658224047CD6BFDA884C66886A13B74EE34A90A"
SOURCE_DRIVER_STATE_SHA256 = "1DE61CF0AC47EDD1D63FE1F3D77668D5F499EA6CA06B90BC83B068CF35F16336"
BRIDGE_DLL_SHA256 = "C36ECCEB67A0DCA7C8C1C6C855A5036771B46617E9F1BF5F4185D965C1951BCE"
DATE_RAW = 53215920


def _validator():
    spec = importlib.util.spec_from_file_location(VALIDATOR.stem, VALIDATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("two-point validator unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _hash(value: object, field: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[A-Fa-f0-9]{64}", value) is None:
        raise ValueError(f"{field} must be a SHA-256 hex string")
    return value.upper()


def _nonempty(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a nonempty string")
    return value


def assemble(raw_bytes: bytes, manifest: dict[str, object]) -> dict[str, object]:
    validator = _validator()
    if not isinstance(manifest, dict) or manifest.get("schema") != "xar.ck3.war31.hwprobe_manifest.v1":
        raise ValueError("wrong hardware-probe manifest schema")
    if manifest.get("request_id") != validator.REQUEST_ID:
        raise ValueError("wrong War31 request")
    if manifest.get("war_id") != validator.WAR_ID or manifest.get("episode_run_id") != validator.EPISODE_RUN_ID:
        raise ValueError("wrong War31 episode")
    if _hash(manifest.get("ck3_exe_sha256"), "ck3_exe_sha256") != validator.EXE_SHA256:
        raise ValueError("wrong exact CK3 build")
    for field, frozen in (("bridge_dll_sha256", BRIDGE_DLL_SHA256),
                          ("checkpoint_sha256", CHECKPOINT_SHA256),
                          ("source_driver_state_sha256", SOURCE_DRIVER_STATE_SHA256)):
        if _hash(manifest.get(field), field) != frozen:
            raise ValueError(f"{field} differs from the frozen War31 source")
    for field in ("driver_state_sha256", "rebind_receipt_sha256",
                  "authorization_receipt_sha256"):
        _hash(manifest.get(field), field)
    for field in ("action_attempt_id", "effect_invocation_id", "frame_token"):
        _nonempty(manifest.get(field), field)
    for field in ("date_raw", "expected_pid", "expected_process_created_filetime"):
        if type(manifest.get(field)) is not int or manifest[field] <= 0:
            raise ValueError(f"{field} must be a positive integer")
    if manifest["date_raw"] != DATE_RAW:
        raise ValueError("date_raw differs from the frozen War31 frame")
    if manifest.get("approved_action_step") != "surrender-war-16777231":
        raise ValueError("manifest does not identify the one authorized War31 action")
    if manifest.get("source_evidence_status") != "separately_authorized_unverified_by_probe":
        raise ValueError("authorization boundary is not explicit")

    try:
        events = [json.loads(line) for line in raw_bytes.decode("utf-8").splitlines()]
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("raw probe stream is not valid UTF-8 JSON lines") from error
    if len(events) != 4 or [event.get("kind") for event in events] != [
        "start", "sample", "sample", "terminal"
    ]:
        raise ValueError("raw stream must have one start, two samples and one terminal")
    start, first, second, terminal = events
    if (start.get("schema") != "xar.ck3.war31.hwprobe_raw.v1"
            or start.get("fixture") is not False):
        raise ValueError("fixture or wrong raw probe stream is forbidden")
    if (start.get("pid") != manifest["expected_pid"]
            or start.get("process_created_filetime") != manifest["expected_process_created_filetime"]):
        raise ValueError("raw process identity differs from manifest")
    if (terminal.get("status") != "paired" or terminal.get("reason") != "paired"
            or terminal.get("debug_registers_cleared") is not True
            or terminal.get("detached") is not True or terminal.get("hit_count") != 2):
        raise ValueError("raw probe did not prove a clean two-point detach")
    if [first.get("site_rva"), second.get("site_rva")] != [
        validator.SITES[0][0], validator.SITES[1][0]
    ]:
        raise ValueError("raw sample sites or order differ")
    if first.get("pid") != start["pid"] or second.get("pid") != start["pid"]:
        raise ValueError("raw samples belong to another process")
    if first.get("thread_id") != second.get("thread_id"):
        raise ValueError("raw samples belong to different threads")
    if first.get("rax_change_pointer") != second.get("rax_change_pointer"):
        raise ValueError("raw samples have different change pointers")
    if (first.get("event_ordinal"), second.get("event_ordinal")) != (1, 2):
        raise ValueError("raw sample event order differs")
    if (type(first.get("qpc")) is not int or type(second.get("qpc")) is not int
            or first["qpc"] <= 0 or second["qpc"] <= first["qpc"]):
        raise ValueError("raw sample timestamps differ or are out of order")
    for sample in (first, second):
        if sample.get("memory_read_status") != "ok":
            raise ValueError("raw sample memory read failed")

    raw_digest = _sha256(raw_bytes)
    process_instance = f"{start['pid']}:{start['process_created_filetime']}"
    common = {
        "process_instance_id": process_instance,
        "thread_id": first["thread_id"],
        "action_attempt_id": manifest["action_attempt_id"],
        "effect_invocation_id": manifest["effect_invocation_id"],
        "frame_token": manifest["frame_token"],
        "war_id": validator.WAR_ID,
        "episode_run_id": validator.EPISODE_RUN_ID,
        "date_raw": manifest["date_raw"],
        "checkpoint_sha256": manifest["checkpoint_sha256"],
        "bridge_dll_sha256": manifest["bridge_dll_sha256"],
        "raw_capture_sha256": raw_digest,
        "memory_read_status": "ok",
        "capture_timing": "before_instruction",
    }
    samples = []
    for sample, (site, opcode, phase) in zip((first, second), validator.SITES):
        samples.append({**common, "site_rva": site, "instruction_bytes": opcode,
                        "site_phase": phase, "event_ordinal": sample["event_ordinal"],
                        "rax_change_pointer": sample["rax_change_pointer"],
                        "change_type_dword": sample["change_type_dword"]})
    paired = {"schema": validator.SCHEMA, "request_id": validator.REQUEST_ID,
              "ck3_exe_sha256": validator.EXE_SHA256, "samples": samples,
              "authorization_receipt_sha256": manifest["authorization_receipt_sha256"],
              "source_authenticity": "REQUIRES_SEPARATE_FORMAL_ACTION_VERIFICATION"}
    structural = validator.validate(paired)
    return {"schema": "xar.ck3.war31.hwprobe_assembled_v1",
            "status": "STRUCTURAL_PAIR_ONLY", "raw_sha256": raw_digest,
            "trace": paired, "structural_validation": structural,
            "limit": "The manifest's WarID, episode, action and authorization are source assertions; the probe only saw instruction hits. Formal action pairing and persisted settlement remain unverified."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; keep attempts append-only")
    rendered = assemble(args.raw.read_bytes(),
                        json.loads(args.manifest.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(rendered, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8", newline="\n")
    print(json.dumps({"status": rendered["status"], "output": str(args.output),
                      "raw_sha256": rendered["raw_sha256"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
