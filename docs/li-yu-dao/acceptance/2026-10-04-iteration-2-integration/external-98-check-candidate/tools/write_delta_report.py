"""Record exact candidate source/output deltas against the preserved candidate."""

from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT.parent / "iteration2-candidate"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def compare(prefix):
    current = ROOT / prefix
    previous = OLD / prefix
    names = {path.relative_to(current).as_posix() for path in current.rglob("*") if path.is_file()}
    names |= {path.relative_to(previous).as_posix() for path in previous.rglob("*") if path.is_file()}
    result = []
    for name in sorted(names):
        before, after = digest(previous / name), digest(current / name)
        if before != after:
            result.append({"path": f"{prefix}/{name}", "before_sha256": before, "after_sha256": after,
                           "change": "added" if before is None else "deleted" if after is None else "modified"})
    return result


report = ROOT / "evidence/actual-delta-files.json"
if report.exists():
    raise ValueError("Preserve prior delta report")
record = {"baseline": str(OLD), "candidate": str(ROOT), "live": "NOT_RUN",
          "authored": compare("tools") + compare("source"), "rendered": compare("generated/mod_li_yu_dao")}
report.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"report": str(report), "authored_changed": len(record["authored"]),
                  "rendered_changed": len(record["rendered"]), "rendered_paths": [item["path"] for item in record["rendered"]]}, indent=2))
