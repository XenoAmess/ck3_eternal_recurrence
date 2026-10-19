"""Small repository receipt from the already closed Native27 manifest."""
from pathlib import Path
import hashlib
import json

ROOT = Path("D:/codex-ck3-demos/2026-10-19-robert-v20261019-native27-termination01")
OUT = Path("docs/ck3-native-ai/evidence/native27-termination-build-qualification-2026-10-19.json")
manifest = ROOT / "FILES-CLOSED.json"
raw = manifest.read_bytes()
assert len(raw) == 12954 and hashlib.sha256(raw).hexdigest() == "ffec55d7a3299dc8f000cb6b8fc2dc23917ef2c84939c475b169dc36ae030861"
closed = json.loads(raw)
pins = {row["relative_path"].replace("\\", "/"): row for row in closed["files_excluding_this_manifest"]}


def small(name):
    pin = pins[name]
    assert pin["bytes"] < 1024 * 1024
    body = Path(pin["path"]).read_bytes()
    assert len(body) == pin["bytes"] and hashlib.sha256(body).hexdigest() == pin["sha256"]
    return json.loads(body)


result = small("QUALIFICATION.json")
compiled = small("COMPILE-RESULT.json")
target = "ExecuteSwayCompletionTerminationMailboxV1"
result["production_exact4_relocation"] = {
    "function": compiled["actual_exact4_registration"]["function_symbol"],
    "section": compiled["actual_exact4_registration"]["section"],
    "old_target_relocations": sum(target in row["symbol"] for row in compiled["baseline_exact4_registration"]["relocations"]),
    "new_target_relocations": [row for row in compiled["actual_exact4_registration"]["relocations"] if target in row["symbol"]]}
result["source_qualification"] = pins["QUALIFICATION.json"]
result["closed_manifest"] = {"path": str(manifest), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
result["storage"] = {key: closed[key] for key in ("logical_bytes_including_manifest", "allocated_bytes", "future_writes_bytes", "owned_build_or_fixture_subprocesses_remaining")}
result["storage"]["files_including_manifest"] = len(pins) + 1
result["scope"] = "Only80B executor assignment over Native26;1router object/355retained direct/612archive members,546project headers unchanged. No M4 ABI, Game/RPC, production loading, natural terminal occurrence or performance qualification. Sequential1worker BELOW_NORMAL; no PDB/newEXE/retry. Closed root future0."
output = (json.dumps(result, ensure_ascii=True, indent=2) + "\n").encode()
assert len(output) <= 12 * 1024
OUT.write_bytes(output)
print(json.dumps({"path": str(OUT), "bytes": len(output), "sha256": hashlib.sha256(output).hexdigest()}))
