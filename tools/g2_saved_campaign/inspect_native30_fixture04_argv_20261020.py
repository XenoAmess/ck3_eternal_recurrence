"""Read only the two named compile metadata files; emit one fixture diff."""
import difflib
import hashlib
import json
import os
from pathlib import Path
import sys
from datetime import datetime, timezone
import native30_resume_guard_20261019 as guard

root, output = map(Path, sys.argv[1:])
paths = [root / "attempt02/selected-fileapi-graph.json", root / "build/compile_commands.json"]
rows, pins = [], []
for path in paths:
    data = path.read_bytes()
    value = json.loads(data)
    candidates = value["selected_compile_rows"] if isinstance(value, dict) else value
    selected = [r for r in candidates if Path(r["file"]).name == "camera_tracking_v1_test.cpp"]
    assert len(selected) == 1
    rows.append(selected[0])
    pins.append({"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})

def normalized(row):
    args = row.get("arguments") or guard.windows_argv(row["command"])
    canonical = lambda v: os.path.normcase(v.replace("\\", "/"))
    source, obj = row["file"], str(guard.output_from_command(row))
    result = []
    for arg in args:
        if canonical(arg) == canonical(source): arg = "$FIXTURE_SOURCE"
        elif arg[:3].lower() in ("/fo", "-fo") and canonical(arg[3:]) == canonical(obj):
            arg = arg[:3] + "$FIXTURE_OBJECT"
        result.append(arg)
    return result

left, right = map(normalized, rows)
changes = [{"operation": op, "old": left[a:b], "new": right[c:d]}
           for op, a, b, c, d in difflib.SequenceMatcher(a=left, b=right).get_opcodes() if op != "equal"]
result = {"machine_id": "xenoamess-full-tower-eb9d2c1186", "utc": datetime.now(timezone.utc).isoformat(),
          "inputs": pins, "outputs": [r.get("output") for r in rows],
          "normalized_token_counts": [len(left), len(right)], "changes": changes}
data = (json.dumps(result, indent=2) + "\n").encode()
assert len(data) <= 4096
with output.open("xb") as stream: stream.write(data)
print(data.decode())
