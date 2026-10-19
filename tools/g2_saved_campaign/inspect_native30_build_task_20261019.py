"""Read only the exact Native30 owner identities and named phase-file metadata."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
ROOT = Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/p51-fresh1066-v20261019-prepare01/native30-build-owner01/owner-spec")
NATIVE = Path("D:/codex-ck3-demos/2026-10-19-robert-v20261019-native30-camera01")
SPEC_SHA = "14f9ef19709a710a298f3275df61a2288b2beaf5c55ec5e1aa000fc799156152"
BOOT_SHA = "c0d76a7064996cafd7412f8f39ba2bb5c5cb6271627246b84e946c00bafb864f"

def main():
    source = REPO / "tools/g2_saved_campaign/interactive_task_owner_v1.py"
    if hashlib.sha256(source.read_bytes()).hexdigest() != BOOT_SHA:
        raise RuntimeError("owner source pin changed")
    module_spec = importlib.util.spec_from_file_location("native30_status_owner", source)
    owner = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(owner)
    spec = owner.checked_spec(ROOT / "SPEC.json", SPEC_SHA)
    api = owner.Windows()
    owner.require_caller(spec, api.current())
    start = owner.read(ROOT / "STARTED.json")
    identities = {}
    for name in ("bootstrap", "child"):
        expected = start[name]
        try:
            handle = api.open(expected["pid"])
            try:
                actual = api.identity(handle)
                actual["matches_started"] = all(actual.get(k) == expected.get(k) for k in
                    ("pid", "creation_filetime", "image", "image_file_id", "session"))
                identities[name] = actual
            finally:
                api.close(handle)
        except OSError as error:
            identities[name] = {"pid": expected["pid"], "read_error": str(error), "alive": None}
    names = ["source-freeze.json", "configure/native-msvc-result.json", "selected-fileapi-graph.json",
             "phase-00/native-msvc-result.json", "RESULT.json", "FILES-CLOSED.json"]
    phases = {name: (NATIVE / "evidence" / name).stat().st_size
              if (NATIVE / "evidence" / name).is_file() else None for name in names}
    source_stats = [path.stat().st_size for path in (NATIVE / "source").rglob("*") if path.is_file()]
    print(json.dumps({"machine_id": spec["machine_id"], "utc": datetime.now(timezone.utc).isoformat(),
        "identities": identities, "named_phase_bytes": phases,
        "source_metadata_sample_not_atomic": {"files": len(source_stats), "eof_bytes": sum(source_stats)},
        "owner_terminal_files": {name: (ROOT / name).is_file() for name in ("CLOSED.json", "FAILED.json")}}))

if __name__ == "__main__":
    main()
