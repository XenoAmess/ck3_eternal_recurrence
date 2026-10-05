"""One bounded, read-only R9 engine-log prefix observation; never polls."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
LOGS = Path("C:/workspace/ck3_lyd_runtime_20261004/live-attempt-009/userdir/logs")
PARENT_CONTEXT = {"reported_clean_head": "544", "reported_pid": 20264,
                  "reported_process_create_time": 1791179349.2116988, "reported_hwnd": 5637378,
                  "game_identity_independently_requeried": False,
                  "boundary": "Parent supplied R9 context; this observer reads only logs, never game/main/pipe."}


def now():
    return datetime.now(timezone.utc).isoformat()


def metadata(stat):
    return {"size": stat.st_size, "mtime_ns": stat.st_mtime_ns, "ctime_ns": stat.st_ctime_ns,
            "birthtime_ns": getattr(stat, "st_birthtime_ns", None), "device": stat.st_dev, "inode": stat.st_ino}


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def write_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def classify(raw):
    headers = list(re.finditer(rb"(?m)^\[([^]\r\n]+)\]\[([A-Z])\][^\r\n]*", raw))
    groups = []
    counts = Counter()
    for number, match in enumerate(headers):
        if match[2] != b"E":
            continue
        start = match.start()
        end = headers[number + 1].start() if number + 1 < len(headers) else len(raw)
        group = raw[start:end]
        text = group.decode("utf-8", errors="replace")
        header = match[0].decode("utf-8", errors="replace")
        unused = re.search(r"Variable '(lyd_im_case_[0-9]+_(?:armed|acknowledged))' is set but is never used\.", header)
        target = re.search(r"lyd_c2_(?:source_signed|check_count|check_rites|check_followers|check_players)\b", text)
        if unused:
            category = "known_fixture_unused_variable"
        elif target:
            category = "current_product_c2_target_variable_error"
        elif "lyd_c2_" in text or "lyd_c2_" in header:
            category = "other_current_product_c2_error"
        elif "lyd_im_" in text or "lyd_i2_" in text:
            category = "other_fixture_error_unreviewed"
        else:
            category = "other_error_unreviewed"
        counts[category] += 1
        groups.append({"category": category, "source_time": match[1].decode("ascii", errors="replace"),
                       "byte_start": start, "byte_end_exclusive": end,
                       "line_start": raw[:start].count(b"\n") + 1, "raw_group_sha256": sha(group),
                       "header": header, "fixture_variable": unused[1] if unused else None,
                       "target_variable": target[0] if target else None,
                       "snippet": text if category != "known_fixture_unused_variable" else None})
    return {"error_headers": len(groups), "counts": dict(counts), "groups": groups,
            "prefix_final_line_complete": not raw or raw.endswith(b"\n"),
            "classification_rule": "Fixture-only known-unused requires exact lyd_im_case_<n>_(armed|acknowledged) variable diagnostic; all other E groups remain separately visible."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot-key", required=True)
    parser.add_argument("--phase", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z0-9-]+", args.snapshot_key) or not re.fullmatch(r"[a-z0-9-]+", args.phase):
        raise ValueError("Use explicit simple append-only labels")
    destination = ROOT / args.snapshot_key
    destination.mkdir()
    raw_dir = destination / "raw-prefix"
    raw_dir.mkdir()
    start = now()
    files = {}
    errors = None
    for original in sorted(LOGS.iterdir()):
        if not original.is_file():
            continue
        read_start = now()
        before_path = metadata(original.stat())
        with original.open("rb") as stream:
            before_handle = metadata(os.fstat(stream.fileno()))
            bound = before_handle["size"]
            payload = stream.read(bound)
            after_handle = metadata(os.fstat(stream.fileno()))
        after_path = metadata(original.stat())
        target = raw_dir / original.name
        with target.open("xb") as output:
            output.write(payload)
        files[original.name] = {"source_path": str(original), "saved_prefix": str(target),
                "read_start_utc": read_start, "read_end_utc": now(),
                "before_path_metadata": before_path, "before_open_handle_metadata": before_handle,
                "after_open_handle_metadata": after_handle, "after_path_metadata": after_path,
                "selected_prefix_byte_bound": bound, "captured_prefix_bytes": len(payload),
                "raw_prefix_sha256": sha(payload), "short_read": len(payload) != bound,
                "source_metadata_changed_during_read": before_handle != after_handle or before_path != after_path,
                "source_identity_changed_during_read": before_path["inode"] != after_path["inode"],
                "claim": "Exact copied bytes and selected size-bound prefix only; no claim that the live source remained frozen."}
        if original.name == "error.log":
            errors = classify(payload)
    if errors is None:
        raise FileNotFoundError("No captured error.log")
    write_json(destination / "CLASSIFICATION.json", errors)
    end = now()
    report = {"result": "ACTUAL_R9_LOG_PREFIX_CAPTURED", "phase": args.phase, "snapshot_key": args.snapshot_key,
              "capture_start_utc": start, "capture_end_utc": end, "parent_context": PARENT_CONTEXT,
              "files": files, "classification": {key: value for key, value in errors.items() if key != "groups"},
              "live_operations": 0, "main_operations": 0, "pipe_operations": 0,
              "prefix_bound_only": True, "formal_interaction_callback_coverage": "NOT_OBSERVED_BY_THIS_READER",
              "later_callbacks_and_whole_final_log_verdict": "NOT_CLAIMED",
              "next_action": "Wait for a concrete ROOT callback message; no automatic polling."}
    write_json(destination / "REPORT.json", report)
    index = {p.relative_to(destination).as_posix(): {"bytes": p.stat().st_size, "sha256": sha(p.read_bytes())}
             for p in sorted(destination.rglob("*")) if p.is_file()}
    write_json(destination / "INDEX.json", index)
    print(json.dumps({"snapshot": str(destination), "capture_start_utc": start, "capture_end_utc": end,
                      "captured_logs": len(files), "error_prefix": files["error.log"],
                      "classification": report["classification"], "whole_final_log_verdict": "NOT_CLAIMED"},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
