"""Check that a new frozen SDK actually carries the first-campaign repairs.

Run once after source freeze and source-knowledge import, before launch. This
does not query a game, add a planner gate, or qualify future war outcomes.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[2]
CATALOGUE = Path(__file__).with_name("robert_first30_lessons_v1.json")
MAX_SOURCE_BYTES = 16 * 1024 * 1024


def source_pin(path: Path) -> dict:
    if path.stat().st_size > MAX_SOURCE_BYTES:
        raise ValueError("source exceeds the 16 MiB per-file bound")
    raw = path.read_bytes()
    normalized = raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    return {"path": str(path.resolve()), "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "utf8_lf_sha256": hashlib.sha256(normalized).hexdigest()}


def audit_sources(package_root: Path, reference_root: Path, catalogue: dict) -> dict:
    """Compare actual adopted leaves with the caller's reviewed source root."""
    package = package_root.resolve(strict=True) / "xar_autoplayer"
    reference = reference_root.resolve(strict=True) / "xar_autoplayer"
    names = sorted({name for lesson in catalogue["lessons"] for name in lesson["sources"]})
    rows = []
    for name in names:
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("catalogue source must remain inside the package")
        target, expected = package / relative, reference / relative
        row = {"relative_source": name, "status": "FAIL"}
        try:
            if not target.resolve(strict=True).is_relative_to(package.resolve(strict=True)):
                raise ValueError("adopted source link leaves the selected package")
            if not expected.resolve(strict=True).is_relative_to(reference.resolve(strict=True)):
                raise ValueError("reference source link leaves its reviewed package")
            row["adopted"], row["reviewed"] = source_pin(target), source_pin(expected)
            row["status"] = ("PASS" if row["adopted"]["utf8_lf_sha256"]
                             == row["reviewed"]["utf8_lf_sha256"] else "FAIL")
            if row["status"] == "FAIL":
                row["reason"] = "frozen_source_differs_from_reviewed_repair"
        except (OSError, ValueError, UnicodeError) as error:
            row["reason"] = str(error)
        rows.append(row)
    return {"status": "PASS" if rows and all(row["status"] == "PASS" for row in rows) else "FAIL",
            "source_comparison": catalogue["source_comparison"], "sources": rows}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--reference-root", type=Path, required=True,
                        help="reviewed fixed source root containing xar_autoplayer")
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error("output must be new; preserve previous qualification receipts")
    knowledge_output = args.output.with_name(args.output.stem + "-populist-source.json")
    if knowledge_output.exists():
        parser.error("derived source-knowledge receipt must also be new")
    catalogue = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    audit = audit_sources(args.package_root, args.reference_root, catalogue)
    machine = subprocess.check_output([sys.executable, "-B", "-X", "utf8",
        str(REPO / "tools/ck3_live_run_id.py"), "machine"], text=True, encoding="utf-8").strip()
    knowledge = {"status": "NOT_RUN", "reason": "source_adoption_audit_failed"}
    if audit["status"] == "PASS":
        result = subprocess.run([sys.executable, "-B", "-X", "utf8",
            str(Path(__file__).with_name("qualify_populist_source.py")),
            "--package-root", str(args.package_root), "--state-dir", str(args.state_dir),
            "--verify-cold-id-rebind", "--output", str(knowledge_output)],
            text=True, encoding="utf-8", capture_output=True, timeout=60)
        knowledge = {"status": "FAIL", "exit_code": result.returncode,
                     "stdout": result.stdout[-4096:], "stderr": result.stderr[-4096:]}
        if knowledge_output.exists():
            body = json.loads(knowledge_output.read_text(encoding="utf-8"))
            knowledge.update(receipt=source_pin(knowledge_output), reported_status=body.get("status"))
            if result.returncode == 0 and body.get("status") == "PASS":
                knowledge["status"] = "PASS"
    report = {"schema": "xar.robert-first30-lessons-adoption-qualification/v1",
        "machine_id": machine, "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if audit["status"] == knowledge["status"] == "PASS" else "FAIL",
        "catalogue": source_pin(CATALOGUE), "lesson_version": catalogue["lesson_version"],
        "source_adoption": audit, "carried_source_knowledge": knowledge,
        "Game_MCP_OBS_calls": 0, "gameplay_commands_submitted": 0,
        "current_game_observed": False, "business_success_inferred": False,
        "boundary": "Software/source and carried knowledge only; actual Host/App/Queue/Native tuple and current native outcomes still require their own receipts."}
    with args.output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps({"status": report["status"], "receipt": source_pin(args.output)}, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
