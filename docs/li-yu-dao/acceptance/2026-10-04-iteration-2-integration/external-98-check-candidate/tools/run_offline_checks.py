"""Preserve fresh offline receipts without changing the pinned checkout."""

from __future__ import annotations

from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from gen_school_consent import CHECKOUT, ROOT, generate
from school_consent_data import BASELINE_COMMIT, NATIVE_PRIMITIVE_STATUS


def run(arguments: list[str]) -> subprocess.CompletedProcess:
    environment = dict(os.environ, LYD_C2_CHECKOUT_ROOT=str(CHECKOUT))
    return subprocess.run(arguments, cwd=ROOT, capture_output=True, check=False, env=environment)


def frozen_identity() -> dict:
    head = run(["git", "-C", str(CHECKOUT), "rev-parse", "HEAD"])
    dirty = run(["git", "-C", str(CHECKOUT), "diff", "--name-only", "HEAD"])
    files = (
        "docs/ck3-confucian-repeatable-reunion-and-schism-design.md",
        "docs/ck3-1.20.0.3-rites-split-and-reunion.md",
        "mod_li_yu_dao/tools/gen_runtime.py",
        "mod_li_yu_dao/tools/content_data.py",
        "mod_li_yu_dao/common/scripted_effects/lyd_entry_effects.txt",
        "mod_li_yu_dao/common/scripted_triggers/lyd_player_triggers.txt",
    )
    return {"head": head.stdout.decode("utf-8", "replace").strip(),
            "tracked_diff": dirty.stdout.decode("utf-8", "replace").splitlines(),
            "read_sources": {relative: hashlib.sha256((CHECKOUT / relative).read_bytes()).hexdigest() for relative in files}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-evidence", type=Path)
    parser.add_argument("--checkout-root", type=Path, help="Read-only project root for external candidate verification")
    parser.add_argument("--checkout-head", default=BASELINE_COMMIT,
                        help="Exact expected read-only checkout HEAD; does not change primitive evidence baseline")
    args = parser.parse_args()
    before = frozen_identity()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    attempt = ROOT / "evidence" / f"offline-{stamp}"
    attempt.mkdir(parents=True, exist_ok=False)
    rendered = generate(native_evidence=args.native_evidence)
    checked = generate(check=True, native_evidence=args.native_evidence)
    tests = run([sys.executable, "-B", "-X", "utf8", str(ROOT / "tools/test_school_consent.py")])
    (attempt / "tests.stdout.bin").write_bytes(tests.stdout)
    (attempt / "tests.stderr.bin").write_bytes(tests.stderr)
    after = frozen_identity()
    unchanged = before == after
    pinned = before["head"] == args.checkout_head and not before["tracked_diff"]
    report = {
        "result": "PASS_OFFLINE" if tests.returncode == 0 and not checked["mismatches"] and unchanged and pinned else "FAIL_OFFLINE",
        "layer": "model-and-structural-only", "test_exit_code": tests.returncode,
        "test_summary": tests.stderr.decode("utf-8", "replace").splitlines()[-5:],
        "render": rendered, "check": checked,
        "checkout_before": before, "checkout_after": after, "checkout_unchanged": unchanged,
        "checkout_is_pinned_clean": pinned, "native_primitive": rendered["native_primitive"],
        "checkout_expected_head": args.checkout_head,
        "primitive_evidence_baseline": BASELINE_COMMIT,
        "live": "NOT_RUN",
        "not_proven": ["native trigger/effect scope typing", "consent delivery and AI response in CK3",
                       "saved scope and serial lifetime", "list/tenet-status/doctrine iterator semantics",
                       "pair divergence before/after migration", "characters/counties and head bindings",
                       "D+1/D+30 postconditions", "natural cooldown expiry", "save/load", "DLC and UI"],
        "authored_source_sha256": {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                                   for prefix in ("tools", "source") for path in sorted((ROOT / prefix).rglob("*"))
                                   if path.is_file() and "__pycache__" not in path.parts},
    }
    report_path = attempt / "offline-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(report_path), "result": report["result"],
                      "native_primitive": rendered["native_primitive"], "live": "NOT_RUN"}, indent=2))
    return int(report["result"] != "PASS_OFFLINE")


if __name__ == "__main__":
    raise SystemExit(main())
