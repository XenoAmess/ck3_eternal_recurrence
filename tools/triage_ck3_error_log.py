#!/usr/bin/env python3
"""Freeze and group a CK3 error log offline; no game or desktop dependencies."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re
from typing import Iterator

SCHEMA = "xar.ck3.error-log-triage/v1"
# Matches the existing server-bound engine diagnostics' single-log bound.
MAX_LOG_BYTES = 64 * 1024 * 1024
HEADER = re.compile(
    r"^\[([^\]]+)\]\[([A-Z])\](?:\[([^\]]+)\])?(?::[ \t]?|[ \t]+)(.*)$"
)
HEADER_LIKE = re.compile(r"^\[[^\]]+\]\[")
LOCATION = re.compile(
    r"^\s*(?:(Script location):\s*)?file:\s*(.*?)\s+line:\s*(\d+)\s*\((.*)\)\s*$"
)
ERROR = re.compile(r"^\s*Error:\s*(.*)$")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def read_stable_bytes(source: Path) -> bytes:
    """Require two equal bounded reads; does not promise an atomic engine snapshot."""
    payloads = []
    for _ in range(2):
        with source.open("rb") as stream:
            payload = stream.read(MAX_LOG_BYTES + 1)
        if len(payload) > MAX_LOG_BYTES:
            raise ValueError(f"log exceeds {MAX_LOG_BYTES} bytes")
        payloads.append(payload)
    if payloads[0] != payloads[1]:
        raise ValueError("log bytes changed between reads; preserve a closed copy and use a new attempt")
    return payloads[0]


def _records(raw_lines: list[str]) -> Iterator[dict]:
    record = None
    for number, raw in enumerate(raw_lines, 1):
        line = raw.rstrip("\r\n")
        match = HEADER.match(line)
        if match:
            if record is not None:
                yield record
            record = {
                "time": match[1], "level": match[2], "emitter": match[3] or "",
                "header_message": match[4], "start_line": number, "end_line": number,
                "raw_lines": [raw],
            }
        elif record is not None:
            record["raw_lines"].append(raw)
            record["end_line"] = number
    if record is not None:
        yield record


def _record_details(record: dict) -> tuple[list[str], dict | None, list[dict]]:
    errors, primary, locations = [], None, []
    for number, raw in enumerate(record["raw_lines"], record["start_line"]):
        line = raw.rstrip("\r\n")
        error = ERROR.match(line)
        if error:
            errors.append(error[1])
        location = LOCATION.match(line)
        if location:
            entry = {
                "file": location[2], "line": int(location[3]), "context": location[4],
                "log_line": number,
                "role": "primary" if location[1] and primary is None else "caller",
            }
            if entry["role"] == "primary":
                primary = entry
            locations.append(entry)
    return errors, primary, locations


def triage_bytes(
    payload: bytes, *, declared_error_cap: int | None = None,
    cap_marker_literal: str | None = None,
) -> dict:
    """Group every E header plus its continuations, without truncating group rankings."""
    if len(payload) > MAX_LOG_BYTES:
        raise ValueError(f"log exceeds {MAX_LOG_BYTES} bytes")
    if declared_error_cap is not None and declared_error_cap < 1:
        raise ValueError("declared error cap must be positive")
    if cap_marker_literal is not None and (
        not cap_marker_literal or any(c in cap_marker_literal for c in "\r\n\0")
    ):
        raise ValueError("cap marker must be a nonempty single-line literal")
    decode_error = None
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        decode_error = {"start_byte": error.start, "end_byte": error.end, "reason": error.reason}
        text = payload.decode("utf-8-sig", errors="replace")
    raw_lines = text.splitlines(keepends=True)
    levels, groups, positions = Counter(), {}, {"primary": {}, "caller": {}}
    record_count, without_primary, multiple_error_lines = 0, 0, 0
    first_record, last_record, last_error = None, None, None
    for record in _records(raw_lines):
        record_count += 1
        levels[record["level"]] += 1
        boundary = {key: record[key] for key in ("time", "level", "start_line", "end_line")}
        if first_record is None:
            first_record = boundary
        last_record = boundary
        if record["level"] != "E":
            continue
        last_error = boundary
        errors, primary, locations = _record_details(record)
        without_primary += primary is None
        multiple_error_lines += len(errors) > 1
        primary_identity = (
            (primary["file"], primary["line"], primary["context"]) if primary else None
        )
        # Preserve literal IDs/numbers and full error messages. Generic headings
        # such as 'Script system error!' cannot distinguish different failures.
        key = (record["emitter"], record["header_message"], tuple(errors), primary_identity)
        if key not in groups:
            group_id = _sha256(json.dumps(key, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
            groups[key] = {
                "group_id": group_id, "emitter": record["emitter"],
                "header_message": record["header_message"],
                "error": errors[0] if errors else record["header_message"],
                "error_messages": errors, "primary_script_location": primary,
                "record_count": 0, "first_time": record["time"], "last_time": record["time"],
                "occurrence_line_ranges": [],
                "representative": {
                    "start_line": record["start_line"], "end_line": record["end_line"],
                    "raw_text": "".join(record["raw_lines"]), "locations": locations,
                },
            }
        group = groups[key]
        group["record_count"] += 1
        group["last_time"] = record["time"]
        group["occurrence_line_ranges"].append([record["start_line"], record["end_line"]])
        # Count an identical position only once per record, separately by role.
        seen = set()
        for location in locations:
            identity = (location["role"], location["file"], location["line"], location["context"])
            if identity in seen:
                continue
            seen.add(identity)
            role, file, line, context = identity
            item = positions[role].setdefault((file, line, context), {
                "file": file, "line": line, "context": context, "record_count": 0, "group_ids": set(),
            })
            item["record_count"] += 1
            item["group_ids"].add(group["group_id"])
    ranked_groups = sorted(groups.values(), key=lambda item: (
        -item["record_count"], item["emitter"], item["error"], item["group_id"],
    ))
    ranked_positions = {}
    for role, entries in positions.items():
        ordered = sorted(entries.values(), key=lambda item: (
            -item["record_count"], item["file"], item["line"], item["context"],
        ))
        ranked_positions[role] = [{**item, "group_ids": sorted(item["group_ids"])} for item in ordered]
    unsupported = [
        {"line": number, "text": raw.rstrip("\r\n")}
        for number, raw in enumerate(raw_lines, 1)
        if HEADER_LIKE.match(raw) and not HEADER.match(raw.rstrip("\r\n"))
    ]
    marker_lines = [
        {"line": number, "text": raw.rstrip("\r\n")}
        for number, raw in enumerate(raw_lines, 1)
        if cap_marker_literal is not None and cap_marker_literal in raw.rstrip("\r\n")
    ]
    return {
        "schema": SCHEMA, "source_bytes": len(payload), "source_sha256": _sha256(payload),
        "line_count": len(raw_lines), "record_count": record_count,
        "level_record_counts": dict(sorted(levels.items())), "error_record_count": levels["E"],
        "group_count": len(ranked_groups), "groups": ranked_groups,
        "script_locations": ranked_positions,
        "record_boundaries": {"first": first_record, "last": last_record, "last_error": last_error},
        "parse_evidence": {
            "encoding": "utf-8-sig", "decode_error": decode_error,
            "preamble_line_count": first_record["start_line"] - 1 if first_record else len(raw_lines),
            "unsupported_header_like_lines": unsupported,
            "error_records_without_primary_location": without_primary,
            "error_records_with_multiple_error_lines": multiple_error_lines,
            "final_line_terminated": not payload or payload.endswith((b"\n", b"\r")),
        },
        "cap_evidence": {
            "declared_error_cap": declared_error_cap,
            "error_records_reach_declared_cap": None if declared_error_cap is None else levels["E"] >= declared_error_cap,
            "marker_literal": cap_marker_literal, "marker_line_count": len(marker_lines),
            "marker_lines": marker_lines,
            "engine_cap_confirmed": None,
            "interpretation": "Threshold and literal matches are evidence only; engine configuration and coverage after the last record are not inferred.",
        },
        "count_semantics": "Occurrences in these frozen bytes; not independent bugs, game dates, or a gameplay acceptance verdict.",
    }


def write_triage(
    source: Path, output_dir: Path, *, declared_error_cap: int | None = None,
    cap_marker_literal: str | None = None,
) -> dict:
    if output_dir.exists():
        raise FileExistsError(f"output already exists; choose a new attempt: {output_dir}")
    payload = read_stable_bytes(source)
    report = triage_bytes(payload, declared_error_cap=declared_error_cap, cap_marker_literal=cap_marker_literal)
    report["source"] = {"path": str(source.resolve()), "snapshot": "source.log", "two_reads_equal": True}
    report["tool"] = {"file": Path(__file__).name, "sha256": _sha256(Path(__file__).read_bytes())}
    output_dir.mkdir(parents=True, exist_ok=False)
    # Partial attempts remain available if an I/O error interrupts a write.
    with (output_dir / "source.log").open("xb") as stream:
        stream.write(payload)
    with (output_dir / "triage.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, sort_keys=True, indent=2)
        stream.write("\n")
    with (output_dir / "groups.csv").open("x", encoding="utf-8", newline="") as stream:
        fields = ["rank", "record_count", "emitter", "error", "file", "line", "context", "group_id"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for rank, group in enumerate(report["groups"], 1):
            location = group["primary_script_location"] or {}
            writer.writerow({
                "rank": rank, **{field: group[field] for field in ("record_count", "emitter", "error", "group_id")},
                **{field: location.get(field, "") for field in ("file", "line", "context")},
            })
    with (output_dir / "script-locations.csv").open("x", encoding="utf-8", newline="") as stream:
        fields = ["role", "rank", "record_count", "file", "line", "context"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for role, entries in report["script_locations"].items():
            for rank, entry in enumerate(entries, 1):
                writer.writerow({"role": role, "rank": rank, **{field: entry[field] for field in fields[2:]}})
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="Explicit existing log or closed log copy")
    parser.add_argument("--output-dir", type=Path, required=True, help="New attempt directory; existing targets refused")
    parser.add_argument("--declared-error-cap", type=int, help="Externally evidenced E-record cap; no assumed default")
    parser.add_argument("--cap-marker-literal", help="Optional exact single-line cap message to count")
    args = parser.parse_args(argv)
    try:
        report = write_triage(args.source, args.output_dir, declared_error_cap=args.declared_error_cap, cap_marker_literal=args.cap_marker_literal)
    except (OSError, ValueError) as error:
        parser.exit(2, f"error: {error}\n")
    print(json.dumps({
        "schema": report["schema"], "source_sha256": report["source_sha256"],
        "record_count": report["record_count"], "error_record_count": report["error_record_count"],
        "group_count": report["group_count"], "output_dir": str(args.output_dir),
        "top_groups": [{key: group[key] for key in ("record_count", "emitter", "error")} for group in report["groups"][:10]],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
