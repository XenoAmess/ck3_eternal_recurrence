"""Compare two already-saved R9 prefixes; no further live reads or polling."""

from collections import Counter
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
FIRST = ROOT / "after-callback-prefix-002"
SECOND = ROOT / "after-sign-and-first-join-prefix-recovery-004"
OUTPUT = ROOT / "compare-second-to-recovered-third-001"


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def ref(path):
    payload = path.read_bytes()
    return {"path": str(path), "bytes": len(payload), "sha256": sha(payload)}


def write_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def main():
    OUTPUT.mkdir()
    tails = OUTPUT / "raw-added-prefix-tails"
    tails.mkdir()
    first_report = json.loads((FIRST / "REPORT.json").read_text(encoding="utf-8"))
    second_report = json.loads((SECOND / "REPORT.json").read_text(encoding="utf-8"))
    comparisons = {}
    occurrences = []
    line_count = 0
    if first_report["files"].keys() != second_report["files"].keys():
        raise ValueError("Observed log topology changed; no append comparison")
    ledger = OUTPUT / "ADDED-RAW-LINES.jsonl"
    with ledger.open("x", encoding="utf-8") as stream:
        for name in first_report["files"]:
            before = (FIRST / "raw-prefix" / name).read_bytes()
            after = (SECOND / "raw-prefix" / name).read_bytes()
            if sha(before) != first_report["files"][name]["raw_prefix_sha256"] or sha(after) != second_report["files"][name]["raw_prefix_sha256"]:
                raise ValueError("Saved raw prefix digest changed")
            if not after.startswith(before):
                raise ValueError(f"Saved prefix is not a byte-identical append: {name}")
            added = after[len(before):]
            with (tails / name).open("xb") as output:
                output.write(added)
            line_start = before.count(b"\n") + 1
            offset = len(before)
            file_lines = 0
            for part in added.splitlines(keepends=True):
                text = part.decode("utf-8", errors="replace")
                tokens = re.findall(r"lyd_c2_(?:source_signed|check_count|check_rites|check_followers|check_players)\b", text)
                category = "c2_target_token_new_raw_line" if tokens else "other_new_raw_line"
                row = {"source_log": name, "absolute_line": line_start + file_lines,
                       "absolute_byte_start": offset, "absolute_byte_end_exclusive": offset + len(part),
                       "raw_line_sha256": sha(part), "category": category, "target_tokens": tokens,
                       "e_header": bool(re.match(r"^\[[^]]+\]\[E\]", text)),
                       "text": text.rstrip("\r\n")}
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                if tokens:
                    occurrences.append(row)
                offset += len(part)
                file_lines += 1
            line_count += file_lines
            comparisons[name] = {"before_bytes": len(before), "after_bytes": len(after),
                "before_sha256": sha(before), "after_sha256": sha(after),
                "saved_prefix_byte_identical": True, "added_bytes": len(added), "added_raw_lines": file_lines,
                "added_raw_sha256": sha(added), "before_final_line_complete": not before or before.endswith(b"\n"),
                "after_final_line_complete": not after or after.endswith(b"\n")}
    error_added = (tails / "error.log").read_bytes()
    error_after = (SECOND / "raw-prefix/error.log").read_bytes()
    second_class = json.loads((SECOND / "CLASSIFICATION.json").read_text(encoding="utf-8"))
    fixture_unused = 0
    product_errors = []
    for group in second_class["groups"]:
        if (group["category"] == "known_fixture_unused_variable"
                or (group["category"] == "other_fixture_error_unreviewed"
                    and "Variable 'lyd_im_adopted' is set but is never used." in group["header"])):
            fixture_unused += 1
        elif group["category"] in {"current_product_c2_target_variable_error", "other_current_product_c2_error"}:
            product_errors.append(group)
    report = {"result": "ACTUAL_R9_SAVED_PREFIX_COMPARISON", "prefix_only": True,
              "first_capture": {"start_utc": first_report["capture_start_utc"], "end_utc": first_report["capture_end_utc"]},
              "second_capture": {"start_utc": second_report["capture_start_utc"], "end_utc": second_report["capture_end_utc"]},
              "parent_reported_callbacks": [
                  {"request": "0027", "reported_behavior": "First ordinary JOIN commit; exact time not supplied to this reader"},
                  {"request": "0050", "reported_behavior": "DETACH source signing in lyd.220; exact time not supplied to this reader"}],
              "callback_execution_independently_inspected_by_this_log_reader": False,
              "saved_vote_counts": "NOT_ASSESSED; separate reader owns immutable save readback",
              "files": comparisons, "added_raw_lines_reviewed": line_count, "new_relevant_lines": occurrences,
              "new_error_log_bytes": len(error_added), "new_error_log_raw_lines": comparisons["error.log"]["added_raw_lines"],
              "new_error_e_headers": len(re.findall(rb"(?m)^\[[^]\r\n]+\]\[E\]", error_added)),
              "second_prefix_fixture_unused_e": fixture_unused, "second_prefix_all_e": second_class["error_headers"],
              "second_prefix_current_c2_product_e": len(product_errors), "current_c2_product_errors": product_errors,
              "second_prefix_source_signed_or_scratch_error_groups": second_class["counts"].get("current_product_c2_target_variable_error", 0),
              "error_prefix": {"bytes": len(error_after), "sha256": sha(error_after)},
              "evidence": {"first_report": ref(FIRST / "REPORT.json"), "second_report": ref(SECOND / "REPORT.json"),
                           "second_classification": ref(SECOND / "CLASSIFICATION.json"), "raw_line_ledger": ref(ledger)},
              "boundary": "Exact two saved prefix intervals only. No final-whole-log, future-callback, gameplay, native UI or vote correctness verdict. No live reads in comparison; no automatic polling."}
    write_json(OUTPUT / "REPORT.json", report)
    index = {p.relative_to(OUTPUT).as_posix(): {"bytes": p.stat().st_size, "sha256": sha(p.read_bytes())}
             for p in sorted(OUTPUT.rglob("*")) if p.is_file()}
    write_json(OUTPUT / "INDEX.json", index)
    print(json.dumps({key: report[key] for key in ("result", "first_capture", "second_capture", "added_raw_lines_reviewed",
                    "new_error_log_bytes", "new_error_e_headers", "second_prefix_fixture_unused_e", "second_prefix_all_e",
                    "second_prefix_current_c2_product_e", "second_prefix_source_signed_or_scratch_error_groups", "error_prefix")},
                    ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
