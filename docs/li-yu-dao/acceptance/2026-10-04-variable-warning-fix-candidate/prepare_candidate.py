"""Capture current inputs and author only external warning-repair templates."""
from pathlib import Path
import collections
import datetime
import difflib
import hashlib
import json
import re
import shutil
import sys

BASE = Path(__file__).resolve().parent
REPO = Path("C:/workspace/ck3_eternal_recurrence")
MOD = REPO / "mod_li_yu_dao"
sys.path.insert(0, str(REPO / "tools"))
from extract_auto_upgrade_buildings import Block, parse_clausewitz

STALE = {
    "lyd_c2_latest_faith", "lyd_c2_retired_teacher", "lyd_c2_retired_head_title",
    "lyd_c2_previous_rite_head", "lyd_c2_teacher_character", "lyd_c3_vacancy",
}
FILES = [
    "tools/school_consent_templates/common/scripted_effects/lyd_c2_commit_effects.txt",
    "tools/school_consent_templates/common/scripted_effects/lyd_c2_head_effects.txt",
    "tools/leadership_templates/common/scripted_effects/lyd_c3_council_effects.txt.in",
    "tools/leadership_templates/common/scripted_effects/lyd_c3_lifecycle_effects.txt.in",
    "tools/leadership_templates/common/scripted_effects/lyd_c3_migration_hooks.txt.in",
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def walk(block):
    for entry in block.entries:
        yield entry
        if isinstance(entry.value, Block):
            yield from walk(entry.value)


def main():
    if (BASE / "report.json").exists():
        raise ValueError("Frozen candidate exists; use a new directory")
    (BASE / "evidence").mkdir()
    evidence = REPO / "docs/li-yu-dao/acceptance/2026-10-04-R0004-cold-loading-red/error-classification.json"
    shutil.copyfile(evidence, BASE / "evidence/r4-error-classification.json")
    classification = json.loads(evidence.read_text(encoding="utf-8"))
    runtime = [MOD / "descriptor.mod"]
    for folder in ["common", "events", "localization", "history"]:
        runtime += [path for path in (MOD / folder).rglob("*") if path.is_file()]
    runtime = sorted(runtime)
    if len(runtime) != 59:
        raise ValueError(f"Expected current 59-file projection, got {len(runtime)}")
    runtime_sha = {path.relative_to(MOD).as_posix(): digest(path) for path in runtime}
    rows = []
    by_variable = collections.defaultdict(list)
    for entry in classification["entries"]:
        if entry["domain"] == "production" and entry["category"].startswith("VARIABLE_"):
            name = re.search(r"Variable '([^']+)'", entry["raw_header"]).group(1)
            by_variable[name].append(entry)
    for name, old in sorted(by_variable.items()):
        refs = []
        for path in runtime:
            for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
                if name in line:
                    refs.append({"path": path.relative_to(MOD).as_posix(), "line": number, "text": line.strip()})
        rows.append({"variable": name, "r4_category": old[0]["category"], "r4_occurrences": len(old),
                     "r4_error_lines": [entry["line"] for entry in old], "current_references": refs,
                     "source_judgment": "STILL_UNUSED_REMOVE_REDUNDANT_METADATA" if name in STALE else "REAL_I3_WRITER_OR_CONSUMER_NOW_REACHABLE",
                     "native_after_fix": "NOT_RUN"})
    deltas, checks = [], []
    for relative in FILES:
        original = MOD / relative
        before = BASE / "before/mod_li_yu_dao" / relative
        after = BASE / "candidate/mod_li_yu_dao" / relative
        before.parent.mkdir(parents=True, exist_ok=True)
        after.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original, before)
        text = original.read_text(encoding="utf-8-sig")
        if relative.endswith("lyd_c2_head_effects.txt"):
            old = """        var:lyd_c2_moving_rite = {
            set_variable = { name = lyd_c2_retired_teacher value = scope:lyd_c2_actor.var:lyd_c2_source_head }
            set_variable = { name = lyd_c2_retired_head_title value = scope:lyd_c2_actor.var:lyd_c2_source_head_title }
            if = { limit = { exists = scope:lyd_c2_actor.var:lyd_c2_source_rite_head }
                set_variable = { name = lyd_c2_previous_rite_head value = scope:lyd_c2_actor.var:lyd_c2_source_rite_head }
            }
        }
"""
            if text.count(old) != 1:
                raise ValueError("Head history block changed during review")
            text = text.replace(old, "")
            old = """        if = { limit = { faith.religious_head = scope:lyd_c2_actor }
            rite = { set_variable = { name = lyd_c2_teacher_character value = scope:lyd_c2_actor } }
        }
"""
            if text.count(old) != 1:
                raise ValueError("Teacher metadata block changed during review")
            text = text.replace(old, "")
        else:
            text = "\n".join(line for line in text.splitlines()
                             if not any(name in line for name in STALE)) + "\n"
        # Preserve original UTF-8 BOM policy; root generator owns runtime bytes.
        encoding = "utf-8-sig" if original.read_bytes().startswith(b"\xef\xbb\xbf") else "utf-8"
        after.write_bytes(text.encode(encoding))
        left, right = parse_clausewitz(original.read_text(encoding="utf-8-sig")), parse_clausewitz(text)
        def calls(ast):
            return collections.Counter(entry.key for entry in walk(ast) if entry.key in {
                "set_parent_faith", "detach_rite_to_new_faith", "remove_religious_head_title",
                "destroy_title", "lyd_c3_create_owned_temporal_head_effect",
                "lyd_c2_ready_to_confirm_trigger", "lyd_c2_retirement_postcondition_trigger",
                "lyd_c3_withdraw_claim_effect", "lyd_c3_leave_teacher_effect",
                "add_to_variable_list", "remove_list_variable",
            })
        checks.append({"path": relative, "balanced_parse": True, "protected_calls_unchanged": calls(left) == calls(right)})
        if not checks[-1]["protected_calls_unchanged"]:
            raise ValueError(f"Protected behavior changed: {relative}")
        diff = "".join(difflib.unified_diff(original.read_text(encoding="utf-8-sig").splitlines(keepends=True), text.splitlines(keepends=True), fromfile="before/mod_li_yu_dao/" + relative, tofile="candidate/mod_li_yu_dao/" + relative))
        destination = BASE / "evidence" / (relative.replace("/", "__") + ".diff")
        destination.write_text(diff, encoding="utf-8")
        deltas.append({"path": "mod_li_yu_dao/" + relative, "before_sha256": digest(before), "after_sha256": digest(after), "diff": destination.name})
    if {path.relative_to(MOD).as_posix(): digest(path) for path in runtime} != runtime_sha:
        raise ValueError("Current runtime changed during read-only audit")
    final = {"created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
             "r4_classification_sha256": digest(evidence), "r4_counts": {"used_never_set": 10, "set_never_used": 14},
             "deduplicated_counts": {"used_never_set": 5, "set_never_used": 7},
             "runtime_files": runtime_sha, "variables": rows, "authored_deltas": deltas,
             "bounded_static_checks": checks, "scope": "current 59 production inputs, R4 twelve unique variable diagnostics only",
             "result": "SOURCE_AUDIT_PATCH_READY", "native_after_fix": "NOT_RUN",
             "old_102_suite": "NOT_RERUN_ROOT_FULL_L0_OWNS_NEXT_CHECKS", "tracked_writes": False}
    (BASE / "report.json").write_text(json.dumps(final, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": final["result"], "runtime_files": len(runtime_sha), "variables": len(rows), "authored_deltas": len(deltas)}, indent=2))


if __name__ == "__main__":
    main()
