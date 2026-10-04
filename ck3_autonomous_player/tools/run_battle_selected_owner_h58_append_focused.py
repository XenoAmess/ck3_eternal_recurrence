"""Run the one new V63 ordered H58 creation scenario against frozen source."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

sys.dont_write_bytecode = True


def pin(path: Path) -> dict[str, object]:
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module-path", type=Path, required=True)
    parser.add_argument("--source-seal", type=Path, required=True)
    parser.add_argument("--reference-src", type=Path, required=True)
    parser.add_argument("--build-dir", type=Path, required=True)
    parser.add_argument("--test-file", type=Path, default=Path(__file__).resolve().parents[1] /
                        "tests/test_battle_selected_owner_h58_append_12003.py")
    args = parser.parse_args()
    output = args.build_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    report = {"status": "HARNESS-RED", "case_count": 1, "tests_exit": None,
              "game": 0, "SDK": 0, "pipe": 0, "window": 0, "new_days": 0,
              "shared_mutation": 0, "Git": 0, "old_tests": 0, "native_full_build": 0}
    started = time.perf_counter()
    try:
        report["module"] = pin(args.module_path)
        report["source_seal"] = pin(args.source_seal)
        report["test_file"] = pin(args.test_file)
        report["runner"] = pin(Path(__file__).resolve())
        if report["module"]["sha256"] != "8a02d091bc489e5336754d8cbfc0e748d43b6844791d31671ef1d66fc446e16b":
            raise RuntimeError("module differs from the final V63 producer freeze")
        if report["source_seal"]["sha256"] != "67c0371dfa484e621295429d0d1f8f2ea5518d57c4f4ef39f76a732f354979ed":
            raise RuntimeError("source-first V63 seal differs from the producer delivery")
        command = [sys.executable, "-B", "-O", str(args.test_file),
                   "--module-path", str(args.module_path),
                   "--reference-src", str(args.reference_src),
                   "--out", str(output / "CASES.json")]
        report["argv"] = command
        completed = subprocess.run(command, capture_output=True, timeout=30)
        (output / "tests.log").write_bytes(completed.stdout+completed.stderr)
        report.update(tests_exit=completed.returncode, tests_log=pin(output / "tests.log"))
        if completed.returncode:
            raise RuntimeError("new focused V63 scenario failed")
        cases = json.loads((output / "CASES.json").read_text(encoding="utf-8"))
        if cases["status"] != "GREEN" or cases["case_count"] != 1 or len(cases["cases"]) != 1:
            raise RuntimeError("fixture did not complete exactly one new case")
        report.update(status="GREEN", readiness="static-ready", checks=cases["checks"],
                      cases=cases["cases"], case_receipt=pin(output / "CASES.json"))
    except Exception as error:
        report["error"] = f"{type(error).__name__}: {error}"
    report["elapsed_seconds"] = time.perf_counter()-started
    receipt = output / "RESULT.json"
    receipt.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="")
    print(json.dumps({"status": report["status"], "checks": report.get("checks"),
                      "receipt": pin(receipt), "error": report.get("error")}, indent=2))
    return 0 if report["status"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
