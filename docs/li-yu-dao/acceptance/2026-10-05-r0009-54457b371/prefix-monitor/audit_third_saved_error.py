"""Linear read of the immutable third raw error prefix, no new live read."""

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "after-sign-and-first-join-prefix-003/raw-prefix/error.log"
DESTINATION = ROOT / "third-prefix-critical-audit-001"
DESTINATION.mkdir()
raw = SOURCE.read_bytes()
prior = (ROOT / "after-callback-prefix-002/raw-prefix/error.log").read_bytes()
if not raw.startswith(prior):
    raise ValueError("Third raw error prefix no longer starts with exact second prefix")
headers = list(re.finditer(rb"(?m)^\[([^]\r\n]+)\]\[([A-Z])\][^\r\n]*", raw))
counts = Counter()
by_time = defaultdict(Counter)
groups = {}
line = 1
previous_start = 0
for i, header in enumerate(headers):
    line += raw[previous_start:header.start()].count(b"\n")
    previous_start = header.start()
    if header[2] != b"E":
        continue
    end = headers[i + 1].start() if i + 1 < len(headers) else len(raw)
    payload = raw[header.start():end]
    text = payload.decode("utf-8", errors="replace")
    message = header[0].decode("utf-8", errors="replace")
    unused = re.search(r"Variable '(lyd_im_case_[0-9]+_(?:armed|acknowledged)|lyd_im_adopted)' is set but is never used\.", message)
    missing = re.search(r"(?:variable for|Invalid variable|Variable) ['\"]?(lyd_c2_[a-z0-9_]+)", text, re.I)
    tokens = re.findall(r"lyd_c2_(?:source_signed|target_signed|target_head_yes|snapshot_valid|check_count|check_rites|check_followers|check_players)\b", text)
    if unused:
        category = "known_fixture_unused_variable"
    elif tokens:
        category = "current_product_c2_missing_or_invalid_field"
    elif "lyd_c2_" in text:
        category = "other_current_product_c2_error"
    else:
        category = "other_error_unreviewed"
    variable = missing[1] if missing else (tokens[0] if tokens else None)
    location = re.search(r"Script location: (.+)", text)
    klass = re.search(r"\[E\]\[([^]]+)\]", message)
    key = (category, variable, location[1].strip() if location else None, klass[1] if klass else None)
    counts[category] += 1
    by_time[header[1].decode("ascii", errors="replace")][category] += 1
    group = groups.setdefault(key, {"category": category, "variable": variable, "location": key[2],
                                   "engine_error_class": key[3], "count": 0, "samples": []})
    group["count"] += 1
    sample = {"source_time": header[1].decode("ascii", errors="replace"), "line_start": line,
              "byte_start": header.start(), "byte_end_exclusive": end,
              "raw_group_sha256": hashlib.sha256(payload).hexdigest(), "raw_text": text}
    if not group["samples"] or category != "known_fixture_unused_variable" and len(group["samples"]) < 3:
        group["samples"].append(sample)
    group["last_sample"] = sample if category != "known_fixture_unused_variable" else {k: sample[k] for k in sample if k != "raw_text"}
report = {"result": "ACTUAL_R9_THIRD_SAVED_PREFIX_NEW_RED", "source": str(SOURCE), "bytes": len(raw),
          "raw_sha256": hashlib.sha256(raw).hexdigest(), "second_error_prefix_bytes": len(prior),
          "second_error_prefix_sha256": hashlib.sha256(prior).hexdigest(), "prior_prefix_exact": True,
          "new_bytes": len(raw) - len(prior), "new_raw_line_breaks": raw[len(prior):].count(b"\n"),
          "counts": dict(counts), "engine_time_counts": {key: dict(value) for key, value in sorted(by_time.items())},
          "group_summaries": list(groups.values()), "final_line_complete": not raw or raw.endswith(b"\n"),
          "scope_analysis": "Reported Script location is Character-root ready_to_confirm_trigger via lyd.220 option trigger. Current initiator ID/context/frame not independently supplied by these error groups.",
          "per_native_call_error_growth": "NOT_DETERMINED: no per-call before/after byte offsets were captured; engine second-level times show repeated evaluations, not a one-error-per-command relation.",
          "boundary": "Only already-copied third error prefix. No fresh game/process/main/pipe operation and no final whole-log assertion."}
for name, value in (("REPORT.json", report), ("SUMMARY.json", {k: report[k] for k in report if k not in {"group_summaries", "engine_time_counts"}})):
    with (DESTINATION / name).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
print(json.dumps({"directory": str(DESTINATION), "raw_bytes": len(raw), "raw_sha256": report["raw_sha256"],
                  "counts": report["counts"], "group_summaries": [{k: value for k, value in item.items() if k not in {"samples", "last_sample"}} for item in groups.values()],
                  "per_native_call_error_growth": report["per_native_call_error_growth"]}, ensure_ascii=False, indent=2))
