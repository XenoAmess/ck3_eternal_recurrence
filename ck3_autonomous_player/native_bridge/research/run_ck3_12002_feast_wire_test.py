"""Compile the current Feast serializer blocks and emit a synthetic wire fixture.

Native providers and paused captures are qualified separately. This fixture
uses production serialization code without linking an unrelated native
executor or pretending to observe game objects.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
NATIVE = ROOT / "ck3_autonomous_player/native_bridge"

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.build_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    source = NATIVE / "src/activity_feast_stage5_start_private_transport_v1.cpp"
    text = source.read_text(encoding="utf-8-sig")
    helpers_start = text.index("void AppendIdentities(")
    helpers = text[helpers_start:text.index("\n} // namespace\n", helpers_start)]
    serializer = text[text.index("std::string SerializeActivityFeastStage5PrivateV1("):
                      text.rindex("\n} // namespace xar::ck3_11906")]
    join = (NATIVE / "src/activity_stage5_feast_guest_join_v1.cpp").read_text(encoding="utf-8-sig")
    status = join[join.index("std::string_view ActivityFeastGuestJoinStatusKeyV1("):
                  join.rindex("\n} // namespace xar::bridge")]
    extracted = output / "production-serializer.cpp"
    extracted.write_text(
        '#include "activity_feast_stage5_start_private_transport_v1.hpp"\n'
        'namespace xar::bridge {\n' + status + '\n}\n'
        'namespace xar::ck3_11906 { namespace {\n' + helpers + '\n}\n' + serializer + '\n}\n',
        encoding="utf-8")
    spec = importlib.util.spec_from_file_location("xar_msvc", ROOT / "tools/run_native_msvc.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    env = module.child_environment(output)
    installation = module.visual_studio_installation(None, env)
    env, tools = module.initialize_msvc(installation, output, env)
    executable = output / "serializer-fixture.exe"
    command = [tools["cl"], "/nologo", "/std:c++20", "/EHsc", "/W4", "/WX", "/O2", "/utf-8",
               f"/I{NATIVE / 'include'}", f"/I{NATIVE / 'src'}", f"/Fe:{executable}",
               str(extracted), str(NATIVE / "src/ck3_12002_activity_feast_wire_test.cpp")]
    compiled = subprocess.run(command, cwd=output, env=env, capture_output=True)
    (output / "compile.log").write_bytes(compiled.stdout + compiled.stderr)
    report = {"schema": "xar.ck3_12002.feast_cpp_wire_fixture.v1",
              "local_ck3_contacted": False, "input_fixture_is_synthetic": True,
              "actual_production_cpp_blocks": True,
              "source_file": str(source.relative_to(NATIVE)),
              "source_sha256": hashlib.sha256(text.encode()).hexdigest(),
              "serializer_block_sha256": hashlib.sha256(serializer.encode()).hexdigest(),
              "compile_exit": compiled.returncode}
    if compiled.returncode == 0:
        wire = output / "actual-hosted-post-wire.json"
        executed = subprocess.run([str(executable), str(wire)], cwd=output, env=env, capture_output=True)
        report["run_exit"] = executed.returncode
        report["wire_path"] = str(wire)
        if wire.exists():
            report["wire_sha256"] = hashlib.sha256(wire.read_bytes()).hexdigest()
    report["passed"] = compiled.returncode == 0 and report.get("run_exit") == 0
    (output / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
