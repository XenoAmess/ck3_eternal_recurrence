"""Deliver one explicitly selected Episode 03 MP4 using the saved OneDrive workflow.

This project wrapper pins and calls the retained Episode 02 transfer/probe
primitives; it does not vendor them or configure OneDrive. An automatic PASS
and a byte-bound frame review marked pending human review permit a review copy.
They never establish a human 1x viewing, listening approval, or remote readback.

Run with the explicitly verified project venv and all four required arguments:
  python delivery.py --final-artifact FINAL.json --machine-audit AUDIT.json
                     --frame-review FRAMES.json --attempt NEW_EXTERNAL_DIRECTORY

FINAL.json is a {path, bytes, sha256} MP4 reference. AUDIT.json must contain
machine_condition_status=PASS and subject (or final_artifact) with the same
bytes/SHA. FRAMES.json must contain subject and either
verdict=PASS_PENDING_HUMAN_REVIEW, or verdict/status=PENDING_HUMAN_REVIEW plus
machine_condition_status=PASS. No human signoff is required or created.

The fixed destination uses the source MP4 basename. Every invocation needs a
new attempt outside OneDrive; targets and attempts are never overwritten.
Only the exact new file is sampled for client metadata, at 10 second intervals
for at most 60 samples. All partial files, receipts and stdio remain in place.
Exit 0: client metadata in sync (independent remote bytes unverified).
Exit 3: copy verified locally, client sync pending. Exit 2: refused/failed.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from datetime import datetime, timezone


DELIVERY_FOLDER = Path("C:/Users/1/OneDrive/CK3-War-AI-20260923")
ONEDRIVE_ROOT = Path("C:/Users/1/OneDrive")
TRANSFER_PATH = Path("D:/workspace/ck3_native_war_ai_promo_work/episode02-five-raw-onedrive-transfer-20260930-a01/transfer_one.py")
TRANSFER_SHA256 = "346BB245ECEF307BBD8480F1FF655414B107D347493DDF085C62C22EA9613DB6"
PROBE_PATH = Path("D:/ck3-research-artifacts/onedrive-cloud-status-probe-20260930-a01/probe.py")
PROBE_SHA256 = "8488B9A4BC152825A6664C762CD842288348AD4B80271DF153E4C6F81CF03E85"
SYNC_ROOT_FILE_ID = 5910974510929700
SAMPLE_COUNT = 60
SAMPLE_INTERVAL_SECONDS = 10


def now():
    return datetime.now(timezone.utc).isoformat()


def path_key(path):
    return os.path.normcase(os.path.abspath(os.fspath(path)))


def outside_onedrive(path):
    # Inspect the supplied local path and its ancestors only; never enumerate
    # the cloud tree or read other cloud files as a validation side effect.
    path = Path(os.path.abspath(os.fspath(path)))
    root = path_key(ONEDRIVE_ROOT)
    if path_key(path) == root or root in [path_key(p) for p in path.parents]:
        raise ValueError(f"Inputs and attempts must be outside OneDrive: {path}")
    resolved = path.resolve(strict=False)
    if path_key(resolved) == root or root in [path_key(p) for p in resolved.parents]:
        raise ValueError(f"Local path resolves into OneDrive: {path}")
    return path


def write_json(path, data):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")


def pin_file(path):
    path = outside_onedrive(path)
    before = path.stat(follow_symlinks=False)
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Expected a regular local file: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    after = path.stat(follow_symlinks=False)
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError(f"Input changed while hashing: {path}")
    return {"path": str(path), "bytes": after.st_size,
            "sha256": digest.hexdigest().upper()}


def reference(value):
    if not isinstance(value, dict):
        raise ValueError("A byte-bound reference must be an object")
    size, sha = value.get("bytes"), value.get("sha256")
    if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
        raise ValueError("A byte-bound reference requires positive integer bytes")
    if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", sha):
        raise ValueError("A byte-bound reference requires a SHA-256")
    return size, sha.upper()


def load_json(path):
    pinned = pin_file(path)
    data = json.loads(Path(pinned["path"]).read_text(encoding="utf-8"))
    if pin_file(path) != pinned:
        raise ValueError(f"JSON input changed while reading: {path}")
    return data, pinned


def validate_inputs(final_artifact, machine_audit, frame_review):
    final, final_pin = load_json(final_artifact)
    audit, audit_pin = load_json(machine_audit)
    frames, frames_pin = load_json(frame_review)
    expected = reference(final)
    source = outside_onedrive(final["path"])
    if source.suffix.lower() != ".mp4":
        raise ValueError("The selected deliverable must be a single MP4")
    actual = pin_file(source)
    if reference(actual) != expected:
        raise ValueError("Final MP4 bytes/SHA do not match final-artifact.json")
    if audit.get("machine_condition_status") != "PASS":
        raise ValueError("Machine audit must have machine_condition_status=PASS")
    if reference(audit.get("subject", audit.get("final_artifact"))) != expected:
        raise ValueError("Machine audit is bound to different final bytes/SHA")
    verdict = frames.get("verdict", frames.get("status"))
    valid_frames = verdict == "PASS_PENDING_HUMAN_REVIEW" or (
        verdict == "PENDING_HUMAN_REVIEW"
        and frames.get("machine_condition_status") == "PASS")
    if not valid_frames:
        raise ValueError("Frame review must declare PASS with human review pending")
    if reference(frames.get("subject", frames.get("final_artifact"))) != expected:
        raise ValueError("Frame review is bound to different final bytes/SHA")
    return {"subject": actual, "inputs": {"final_artifact": final_pin,
            "machine_audit": audit_pin, "frame_review": frames_pin},
            "machine_condition_status": "PASS",
            "frame_review_verdict": verdict, "human_signoff": "not-provided"}


def load_transfer():
    pinned = pin_file(TRANSFER_PATH)
    if pinned["sha256"] != TRANSFER_SHA256:
        raise ValueError("Retained transfer primitive SHA has changed")
    spec = importlib.util.spec_from_file_location("episode03_retained_transfer", TRANSFER_PATH)
    if spec is None or spec.loader is None:
        raise ValueError("Cannot import the retained transfer primitive")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if path_key(module.TARGET_ROOT) != path_key(DELIVERY_FOLDER):
        raise ValueError("Retained transfer has a different fixed destination")
    return module


def run_probe(target):
    # probe.py has an unguarded argv loop: importing it would probe unrelated
    # wrapper arguments. Run its pinned bytes with exactly one target argument.
    if pin_file(PROBE_PATH)["sha256"] != PROBE_SHA256:
        raise ValueError("Retained no-recall metadata probe SHA has changed")
    argv = [sys.executable, "-X", "utf8", "-B", str(PROBE_PATH), str(target)]
    try:
        return subprocess.run(argv, capture_output=True, check=False, timeout=20)
    except subprocess.TimeoutExpired as error:
        return subprocess.CompletedProcess(argv, 124, error.stdout or b"",
                                           (error.stderr or b"") + b"\nMetadata probe timed out\n")


def parse_probe(completed, target):
    stdout = completed.stdout.decode("utf-8-sig", errors="replace")
    lines = [line for line in stdout.splitlines() if line.strip()]
    if completed.returncode != 0 or len(lines) != 1:
        return {"path": str(target), "error": "Probe failed or returned other than one row",
                "exit_code": completed.returncode}
    try:
        row = json.loads(lines[0])
    except (ValueError, TypeError):
        return {"path": str(target), "error": "Probe output is not JSON"}
    if not isinstance(row, dict) or path_key(row.get("path", "")) != path_key(target):
        return {"path": str(target), "error": "Probe did not describe the exact new target"}
    return row


def metadata_in_sync(row, expected_size):
    # These are the retained client's observable conditions. They establish
    # client metadata, not a separately downloaded/hashed remote object.
    return (not row.get("error") and row.get("size") == expected_size
            and row.get("stable_size_mtime") is True
            and row.get("sync_root_hresult") == "0x00000000"
            and row.get("placeholder_hresult") == "0x00000000"
            and row.get("sync_root_file_id") == SYNC_ROOT_FILE_ID
            and row.get("in_sync_state") == 1
            and row.get("validated") == expected_size
            and row.get("modified") == 0)


def deliver(final_artifact, machine_audit, frame_review, attempt, *,
            transfer_loader=load_transfer, probe_runner=run_probe, sleeper=time.sleep):
    attempt = outside_onedrive(attempt)
    attempt.mkdir(parents=True, exist_ok=False)
    started = now()
    try:
        validated = validate_inputs(final_artifact, machine_audit, frame_review)
        source = Path(validated["subject"]["path"])
        size, sha = reference(validated["subject"])
        target = DELIVERY_FOLDER / source.name
        transfer_pin, probe_pin = pin_file(TRANSFER_PATH), pin_file(PROBE_PATH)
        if transfer_pin["sha256"] != TRANSFER_SHA256 or probe_pin["sha256"] != PROBE_SHA256:
            raise ValueError("Frozen transfer/probe input pins do not match")
        write_json(attempt / "01-inputs.json", {"at_utc": started, **validated,
                   "target": str(target), "file_count": 1,
                   "primitives": {"transfer": transfer_pin, "probe": probe_pin},
                   "interpreter": sys.executable, "python": sys.version,
                   "probe_interval_seconds": SAMPLE_INTERVAL_SECONDS,
                   "probe_max_samples": SAMPLE_COUNT})
        module = transfer_loader()
        if path_key(module.TARGET_ROOT) != path_key(DELIVERY_FOLDER):
            raise ValueError("Transfer destination must remain the fixed OneDrive folder")
        # Replace the historical five-raw-MKV input list before ANY invocation.
        module.FILES = (("episode03-final", source, size, sha),)
        module.ATTEMPT_ROOT = attempt / "copy"
        transfer_argv = [str(TRANSFER_PATH), "1"]
        write_json(attempt / "02-transfer-command.json", {"argv": transfer_argv,
                   "file_count": len(module.FILES), "target": str(target)})
        saved_argv = sys.argv
        with (attempt / "transfer.stdout.txt").open("x", encoding="utf-8") as stdout, \
             (attempt / "transfer.stderr.txt").open("x", encoding="utf-8") as stderr:
            try:
                sys.argv = transfer_argv
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    exit_code = module.main()
            finally:
                sys.argv = saved_argv
        if exit_code != 0:
            raise RuntimeError(f"Single-file transfer failed with exit code {exit_code}; partial retained")
        receipt_path = module.ATTEMPT_ROOT / "file-01-episode03-final" / "04-local-copy-verified.json"
        receipt, receipt_pin = load_json(receipt_path)
        if (receipt.get("status") != "LOCAL_COPY_VERIFIED_CLOUD_PENDING"
                or path_key(receipt.get("source", "")) != path_key(source)
                or path_key(receipt.get("target", "")) != path_key(target)
                or reference(receipt) != (size, sha)
                or receipt.get("copy_stream_sha256", "").upper() != sha):
            raise ValueError("Local copy receipt does not bind the selected file and exact new target")
        write_json(attempt / "03-copy-receipt.json", {"receipt": receipt_pin, "verified": True})
        samples = []
        in_sync = False
        for index in range(SAMPLE_COUNT):
            completed = probe_runner(target)
            stem = f"probe-{index + 1:02d}"
            (attempt / f"{stem}.stdout.txt").write_bytes(completed.stdout)
            (attempt / f"{stem}.stderr.txt").write_bytes(completed.stderr)
            row = parse_probe(completed, target)
            in_sync = metadata_in_sync(row, size)
            sample = {"sample": index + 1, "at_utc": now(), "target": str(target),
                      "argv": [sys.executable, "-X", "utf8", "-B", str(PROBE_PATH), str(target)],
                      "exit_code": completed.returncode,
                      "metadata": row, "client_metadata_in_sync": in_sync}
            write_json(attempt / f"{stem}.json", sample)
            samples.append(sample)
            print(json.dumps({"sample": index + 1, "max_samples": SAMPLE_COUNT,
                  "client_metadata_in_sync": in_sync, "target": str(target)}), flush=True)
            if in_sync:
                break
            if index + 1 < SAMPLE_COUNT:
                sleeper(SAMPLE_INTERVAL_SECONDS)
        # Recheck only local inputs; do not open a cloud object to reconfirm it.
        if validate_inputs(final_artifact, machine_audit, frame_review) != validated:
            raise ValueError("Selected local inputs changed during delivery")
        result = {"started_utc": started, "finished_utc": now(), **validated,
                  "target": str(target), "file_count": 1,
                  "status": "CLIENT_METADATA_IN_SYNC_REMOTE_UNVERIFIED" if in_sync else "CLIENT_SYNC_PENDING",
                  "local_copy_receipt": receipt_pin, "probe_samples": len(samples),
                  "independent_remote_readback": False,
                  "human_1x_full_review": "not-provided", "human_signoff": "not-provided",
                  "delivery_kind": "review-copy", "process_assets_retained": True}
        write_json(attempt / "delivery-result.json", result)
        print(json.dumps({"status": result["status"], "target": str(target),
                          "sha256": sha, "file_count": 1, "attempt": str(attempt),
                          "human_signoff": "not-provided"}), flush=True)
        return 0 if in_sync else 3
    except Exception as error:
        write_json(attempt / "failure.json", {"at_utc": now(), "error": str(error),
                   "exception": type(error).__name__, "all_partial_assets_retained": True,
                   "human_signoff": "not-provided"})
        print(f"Delivery refused/failed; retained attempt: {attempt}: {error}", file=sys.stderr)
        return 2


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--final-artifact", required=True, type=Path)
    parser.add_argument("--machine-audit", required=True, type=Path)
    parser.add_argument("--frame-review", required=True, type=Path)
    parser.add_argument("--attempt", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        return deliver(args.final_artifact, args.machine_audit, args.frame_review, args.attempt)
    except Exception as error:
        print(f"Delivery refused before a new attempt could be created: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
