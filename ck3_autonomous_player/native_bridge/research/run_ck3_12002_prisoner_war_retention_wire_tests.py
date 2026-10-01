"""Compile the new production wire boundary and emit actual positive/empty JSON."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    bridge = root / "ck3_autonomous_player/native_bridge"
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    spec = importlib.util.spec_from_file_location("native_msvc", root / "tools/run_native_msvc.py")
    helper = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(helper)
    environment = helper.child_environment(output)
    installation = helper.visual_studio_installation(None, environment)
    environment, tools = helper.initialize_msvc(installation, output, environment)
    sources = [bridge / "src" / name for name in (
        "ck3_12002.cpp", "ck3_12002_world.cpp", "ck3_12002_province.cpp",
        "ck3_12002_army.cpp", "ck3_12002_prisoner_war_retention.cpp",
        "ck3_12002_prisoner_wire.cpp", "player_prisoner_ransom_wire_v1.cpp",
        "player_prisoner_collection_query_v1_private.cpp",
        "ck3_12002_prisoner_war_retention_wire_test.cpp")]
    executable = output / "ck3_12002_prisoner_war_retention_wire_test.exe"
    command = [tools["cl"], "/nologo", "/std:c++20", "/EHsc", "/W4", "/WX",
               "/utf-8", "/O2", "/I" + str(bridge / "include"),
               *map(str, sources), "/Fe" + str(executable)]
    compiled = subprocess.run(command, cwd=output, env=environment, capture_output=True)
    (output / "compile.log").write_bytes(compiled.stdout + compiled.stderr)
    row = {"compile_returncode": compiled.returncode}
    if compiled.returncode == 0:
        snapshots = output / "actual-wire"
        test = subprocess.run([str(executable), str(snapshots)], cwd=output,
                              env=environment, capture_output=True)
        (output / "test.log").write_bytes(test.stdout + test.stderr)
        row.update(test_returncode=test.returncode,
                   output=(test.stdout + test.stderr).decode("utf-8", errors="replace"),
                   actual_wire_files={name: {"path": str(snapshots / name),
                       "sha256": hashlib.sha256((snapshots / name).read_bytes()).hexdigest()}
                       for name in ("positive.json", "empty.json") if (snapshots / name).is_file()})
    ok = row.get("test_returncode") == 0
    report = {"schema": "xar.ck3_12002_prisoner_war_retention_wire_fixture.v1",
              "status": "GREEN" if ok else "RED", "local_ck3_used": False,
              "live_verified": False, "result": row,
              "source_sha256": {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in sources}}
    (output / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return int(not ok)


if __name__ == "__main__":
    raise SystemExit(main())
