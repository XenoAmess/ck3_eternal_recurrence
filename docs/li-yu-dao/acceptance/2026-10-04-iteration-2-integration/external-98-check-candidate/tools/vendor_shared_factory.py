"""Snapshot the agreed shared factory; never edit the leadership candidate."""

from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
source = ROOT.parent / "iteration3-leadership-candidate/source/common/scripted_effects/lyd_c3_head_factory.txt.in"
destination = ROOT / "source/common/scripted_effects/lyd_c3_head_factory.txt"
report = ROOT / "evidence/shared-factory-dependency.json"
if destination.exists() or report.exists():
    raise ValueError("Preserve the captured dependency")
payload = source.read_bytes()
destination.write_bytes(payload)
report.parent.mkdir(parents=True, exist_ok=True)
report.write_text(json.dumps({"source": str(source), "source_sha256": hashlib.sha256(payload).hexdigest(),
                             "snapshot": str(destination), "live": "NOT_RUN", "shared_interface": "lyd_c3_create_owned_temporal_head_effect",
                             "authorization_variable": "lyd_c3_head_creation_authorized",
                             "boundary": "Exactly one shared factory definition at integration; do not load duplicate snapshots alongside I3."}, indent=2) + "\n", encoding="utf-8")
print(destination)
