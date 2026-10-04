"""Capture independent I3 hooks without touching their authoritative source."""

from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
source = ROOT.parent / "iteration3-leadership-candidate/source/common/scripted_effects/lyd_c3_migration_hooks.txt.in"
destination = ROOT / "source/common/scripted_effects/lyd_c3_migration_hooks.txt"
report = ROOT / "evidence/shared-migration-hooks-dependency.json"
if destination.exists() or report.exists():
    raise ValueError("Preserve captured dependency")
payload = source.read_bytes()
destination.write_bytes(payload)
report.write_text(json.dumps({"source": str(source), "source_sha256": hashlib.sha256(payload).hexdigest(),
                             "snapshot": str(destination), "live": "NOT_RUN",
                             "boundary": "I3 hooks only; no c2 locks/serial/electorates/native-title mutation; load one shared definition."}, indent=2) + "\n", encoding="utf-8")
print(destination)
