"""Make a byte-exact A05 input layout for the existing pursuit comparator.

The comparator expects the 004-era term-dXX names. This adapter copies A05
responses without modification, records each original path and hash, and
labels the package as a new A05 run. Never present it as 004 footage.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def identity(path: Path) -> dict:
    data = path.read_bytes()
    return {"path": str(path.resolve()), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest().upper()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--a05-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        parser.error("output directory exists; use an append-only path")
    source_dir = args.a05_root / "ck3-output" / "interactive-requests-responses"
    target_dir = args.output_dir / "ck3-output" / "interactive-requests-responses"
    target_dir.mkdir(parents=True, exist_ok=False)
    mark_path = args.a05_root / "recording-e2-09-terminal-a02" / "marks.jsonl"
    marks = {row["kind"]: row for line in mark_path.read_text(encoding="utf-8").splitlines()
             if (row := json.loads(line)).get("kind")}
    rows = []
    copies = []
    for day in range(28, 33):
        last = day == 32
        source_name = f"e2t-s02-d{day}-{'terminal' if last else 'control'}.json"
        target_name = f"term-d{day}-{'terminal' if last else 'control'}.json"
        source = source_dir / source_name
        target = target_dir / target_name
        shutil.copyfile(source, target)
        source_id, target_id = identity(source), identity(target)
        if source_id["sha256"] != target_id["sha256"] or source_id["bytes"] != target_id["bytes"]:
            raise ValueError(f"byte copy mismatch: {source}")
        response = json.loads(source.read_text(encoding="utf-8"))
        body = response["body"]
        snapshot = body["battle_terminal_transition"] if last else body["battle_control_snapshot"]
        date_raw = 53146896 + (day - 28) * 24
        if last:
            if (snapshot["observed_date_raw"], snapshot["prior_combat_id"],
                snapshot["prior"]["terminal_kind"], snapshot["prior"]["winner_raw"]) != (
                    date_raw, 16777218, "normal_result", 0):
                raise ValueError("A05 terminal identity mismatch")
            mark = marks["e2t-s02-d32-writer"]
            index = {"day": day, "date_raw": date_raw, "terminal_sha256": source_id["sha256"],
                     "screenshot_sha256": mark["screenshot"]["sha256"]}
        else:
            if (snapshot["observed_date_raw"], snapshot["combat_id"], snapshot["phase"],
                snapshot["phase_day"], snapshot["winner_raw"]) != (
                    date_raw, 16777218, "pursuit", day - 28, 0):
                raise ValueError(f"A05 day{day} identity mismatch")
            mark = marks[f"e2t-s02-d{day}-visible"]
            index = {"day": day, "date_raw": date_raw, "phase_day": day - 28,
                     "control_sha256": source_id["sha256"],
                     "screenshot_sha256": mark["screenshot"]["sha256"]}
        rows.append(index)
        copies.append({"original": source_id, "adapter_copy": target_id})
    index_path = args.output_dir / "terminal-replay-d28-d32.jsonl"
    with index_path.open("x", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    manifest_path = args.output_dir / "a05-adapter-provenance.json"
    with manifest_path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump({"schema": "ck3.episode02.a05-pursuit-parity-adapter.v1",
                   "created_utc": datetime.now(timezone.utc).isoformat(),
                   "source_capture_report": identity(args.a05_root / "ck3-output" / "capture-report.json"),
                   "source_marks": identity(mark_path),
                   "source_recorder_final": identity(args.a05_root / "recording-e2-09-terminal-a02" / "recorder-final.json"),
                   "index": identity(index_path), "copies": copies,
                   "purpose": "layout-only byte copies for compare_native_pursuit_receipts.py; A05 remains a separate run"},
                  stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"adapter": str(args.output_dir),
                      "provenance_sha256": identity(manifest_path)["sha256"],
                      "index_sha256": identity(index_path)["sha256"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
