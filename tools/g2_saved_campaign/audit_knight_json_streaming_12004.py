"""Audit the finite source rewrite without a compiler or a Native/Game call.

This is source conservation evidence, not executable or wire equivalence. It
reads only five small source blobs from a fixed Git baseline and the worktree.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone


BASELINE = "652e873ab164cfb78b654854c0dc2ca35ef816b3"
ROOT = Path(__file__).resolve().parents[2]
NATIVE = "ck3_autonomous_player/native_bridge/"


def replace_once(source: str, before: str, after: str) -> str:
    count = source.count(before)
    if count != 1:
        raise ValueError(f"Expected one source span, found {count}: {before[:80]!r}")
    return source.replace(before, after, 1)


def expected_rewrite(path: str, source: str) -> str:
    if path.endswith("include/xar_bridge/ck3_12004_person_six_stage_capture.hpp"):
        source = replace_once(source, "#include <atomic>\n", "#include <atomic>\n#include <iosfwd>\n")
        before = "std::string SerializePersonSixStageCapture12004(\n    const PersonSixStageCapture12004DTO &dto);"
        return replace_once(source, before, before + "\n// Writes the same JSON directly into an enclosing serializer's default-format\n// stream, without materializing a second complete capture string.\nvoid WritePersonSixStageCapture12004(\n    std::ostream &out, const PersonSixStageCapture12004DTO &dto);")
    if path.endswith("include/xar_bridge/person_callback_entry_inputs_12004.hpp"):
        source = replace_once(source, "#include <array>\n", "#include <array>\n#include <iosfwd>\n")
        before = "std::string SerializePersonCallbackEntryInputs12004(\n    const PersonCallbackEntryInputs12004 &inputs);"
        return replace_once(source, before, before + "\n// The enclosing serializer supplies its default-format JSON stream. The\n// retained preparation is emitted directly, with no temporary JSON string.\nvoid WritePersonCallbackEntryInputs12004(\n    std::ostream &out, const PersonCallbackEntryInputs12004 &inputs);")
    if path.endswith("src/ck3_12004_person_six_stage_capture.cpp"):
        source = replace_once(source,
            "std::string SerializePersonSixStageCapture12004(\n    const PersonSixStageCapture12004DTO &dto) {\n  std::ostringstream out;\n",
            "void WritePersonSixStageCapture12004(\n    std::ostream &out, const PersonSixStageCapture12004DTO &dto) {\n")
        before = "  out << \",\\\"historical_capture\\\":\" << (dto.historical_capture ? \"true\" : \"false\") << '}';\n"
        source = replace_once(source, before, before + "}\n\nstd::string SerializePersonSixStageCapture12004(\n    const PersonSixStageCapture12004DTO &dto) {\n  std::ostringstream out;\n  WritePersonSixStageCapture12004(out, dto);\n")
        return replace_once(source, "    out << SerializePersonSixStageCapture12004(capture);", "    WritePersonSixStageCapture12004(out, capture);")
    if path.endswith("src/person_callback_entry_inputs_12004.cpp"):
        source = replace_once(source,
            "std::string SerializePersonCallbackEntryInputs12004(\n    const PersonCallbackEntryInputs12004 &inputs) {\n  std::ostringstream out;\n",
            "void WritePersonCallbackEntryInputs12004(\n    std::ostream &out, const PersonCallbackEntryInputs12004 &inputs) {\n")
        source = replace_once(source, "    out << SerializePersonSixStageCapture12004(*inputs.preparation_at_entry);", "    WritePersonSixStageCapture12004(out, *inputs.preparation_at_entry);")
        before = "  JsonString(out, inputs.reason);\n  out << '}';\n"
        return replace_once(source, before, before + "}\n\nstd::string SerializePersonCallbackEntryInputs12004(\n    const PersonCallbackEntryInputs12004 &inputs) {\n  std::ostringstream out;\n  WritePersonCallbackEntryInputs12004(out, inputs);\n")
    if path.endswith("src/ck3_12004_knight_stat_consumption_serializer.cpp"):
        source = replace_once(source,
            "    out << \",\\\"preparation_capture_at_consumption\\\":\"\n        << SerializePersonSixStageCapture12004(*context.preparation_capture_at_consumption);",
            "    out << \",\\\"preparation_capture_at_consumption\\\":\";\n    WritePersonSixStageCapture12004(out, *context.preparation_capture_at_consumption);")
        return replace_once(source,
            "    out << \",\\\"preparation_entry_inputs\\\":\"\n        << SerializePersonCallbackEntryInputs12004(*context.preparation_entry_inputs);",
            "    out << \",\\\"preparation_entry_inputs\\\":\";\n    WritePersonCallbackEntryInputs12004(out, *context.preparation_entry_inputs);")
    raise ValueError(f"Unowned file: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", default=BASELINE)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    started = datetime.now(timezone.utc).isoformat()
    machine_id = subprocess.check_output(
        [sys.executable, str(ROOT / "tools/ck3_live_run_id.py"), "machine"],
        cwd=ROOT, text=True, encoding="utf-8").strip()
    capacity = shutil.disk_usage(ROOT)
    paths = [
        NATIVE + "include/xar_bridge/ck3_12004_person_six_stage_capture.hpp",
        NATIVE + "include/xar_bridge/person_callback_entry_inputs_12004.hpp",
        NATIVE + "src/ck3_12004_person_six_stage_capture.cpp",
        NATIVE + "src/person_callback_entry_inputs_12004.cpp",
        NATIVE + "src/ck3_12004_knight_stat_consumption_serializer.cpp",
    ]
    checks = []
    for path in paths:
        before = subprocess.check_output(
            ["git", "show", f"{args.baseline}:{path}"], cwd=ROOT).decode("utf-8")
        after = (ROOT / path).read_text(encoding="utf-8")
        expected = expected_rewrite(path, before)
        checks.append({
            "path": path,
            "baseline_utf8_sha256": hashlib.sha256(before.encode()).hexdigest(),
            "candidate_utf8_sha256": hashlib.sha256(after.encode()).hexdigest(),
            "candidate_utf8_bytes": len(after.encode()),
            "whole_source_equals_only_declared_rewrite": after == expected,
        })
    passed = all(item["whole_source_equals_only_declared_rewrite"] for item in checks)
    report = {
        "schema": "xar.ck3.knight-json-streaming-source-conservation/v1",
        "machine_id": machine_id,
        "observed_at_utc": started,
        "evidence_source": "tools/ck3_live_run_id.py machine; fixed Git source blobs; current worktree; shutil.disk_usage(project_root)",
        "baseline_commit": args.baseline,
        "scope": "five small source leaves, UTF-8 with line endings normalized by text reader",
        "checks": checks,
        "source_conservation_passed": passed,
        "preserved_source_scope": "all DTO fields, output literals, ordering loops, string/number/pointer helpers, capture/history access and unrelated code",
        "removed_temporary_string_edges": [
            "knight Context -> preparation_capture_at_consumption",
            "knight Context -> preparation_entry_inputs",
            "callback entry -> preparation_at_entry",
            "six-stage query -> character_captures item",
        ],
        "runtime_boundary": {
            "qualification": "source-only",
            "cpp_build": "NOTRUN",
            "executable_equivalence": "NOTRUN",
            "native_game_mcp_calls": 0,
            "large_historical_payload_reads": 0,
            "latency_or_speedup_claimed": False,
            "output_size_reduction_claimed": False,
            "deployment_claimed": False,
        },
        "storage": {
            "policy_version": "1.0.0",
            "machine_id": machine_id,
            "root": str(ROOT),
            "volume_total_bytes": capacity.total,
            "volume_available_bytes": capacity.free,
            "write_limit_bytes": 16777216,
            "this_lane_heavy_write_performed": False,
            "deletion_performed": False,
            "root_owns_full_capacity_reservation_and_expiry_checks": True,
        },
    }
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        if len(encoded.encode("utf-8")) > 1048576:
            raise ValueError("Audit result exceeds the policy metadata limit")
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
