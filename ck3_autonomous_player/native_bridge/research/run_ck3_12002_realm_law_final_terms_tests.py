"""Compile changed law terms and actual-provider JSON fixtures without CK3."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from run_ck3_12002_lifestyle_tests import msvc_environment


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    native = Path(__file__).resolve().parents[1]
    environment = msvc_environment(output)
    compiler = shutil.which("cl.exe", path=environment.get("Path", environment.get("PATH")))
    if compiler is None:
        raise RuntimeError("MSVC unavailable")
    specs = {
        "final_terms": ["ck3_12002_realm_law_final_terms.cpp", "ck3_12002_realm_law_final_terms_test.cpp"],
        "wire": ["realm_law_active_collection_11906.cpp", "realm_law_candidate_collection_11906.cpp", "ck3_12002_realm_law_active_collection.cpp", "ck3_12002_realm_law_candidate_collection.cpp", "ck3_12002_realm_law_final_terms.cpp", "ck3_12002_realm_law.cpp", "ck3_12002_realm_law_wire_test.cpp"],
    }
    rows = []
    for name, sources in specs.items():
        for optimization in ("Od", "O2"):
            cell = output / (name + "-" + optimization)
            cell.mkdir(exist_ok=True)
            executable = cell / (name + "_test.exe")
            command = [compiler, "/nologo", "/std:c++20", "/W4", "/WX", "/EHsc", "/utf-8", "/UNDEBUG", "/" + optimization, "/I" + str(native / "include"), *[str(native / "src" / source) for source in sources], "/Fe" + str(executable)]
            compiled = subprocess.run(command, cwd=cell, env=environment, capture_output=True, text=True)
            (cell / "compile.log").write_text(compiled.stdout + compiled.stderr, encoding="utf-8")
            row = {"name": name, "mode": optimization, "compile_returncode": compiled.returncode}
            if compiled.returncode == 0:
                arguments = [str(executable)]
                if name == "wire": arguments.append(str(cell / "realm-law-final-terms-wire.json"))
                executed = subprocess.run(arguments, cwd=cell, env=environment, capture_output=True, text=True)
                (cell / "test.log").write_text(executed.stdout + executed.stderr, encoding="utf-8")
                row.update(test_returncode=executed.returncode, output=executed.stdout + executed.stderr, executable_sha256=hashlib.sha256(executable.read_bytes()).hexdigest())
            rows.append(row)
    success = all(row.get("test_returncode") == 0 for row in rows)
    report = {"schema": "xar.ck3_12002_realm_law_terms_offline_result.v1", "status": "GREEN" if success else "RED", "results": rows, "ck3_launched": False, "running_process_access": False}
    (output / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
