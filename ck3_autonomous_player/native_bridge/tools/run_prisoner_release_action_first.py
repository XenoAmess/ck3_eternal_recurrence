"""Root-only new release-action FIRST using the current qualified runtime.

Compile one fixture main or reuse Root's already compiled fixture executable,
then run the sole native five-case and registered MCP compound once. No game,
pipe, configure, runtime rebuild, historical test replay or replacement provider.
Source authoring does not execute this helper.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-receipt", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    parser.add_argument("--native-exe", type=Path,
        help="Reuse the unique M6 fixture executable already compiled by Root's joined build")
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": "ck3.actual4.prisoner-release-action-standalone-first.v1",
        "status": "NOTRUN", "runtime_receipt": str(args.runtime_receipt.resolve()),
        "source_root": str(args.source_root.resolve()), "output_dir": str(output),
        "stages": [], "configured": False, "runtime_rebuilt": False,
        "old_tests_replayed": False, "replacement_provider_defined": False,
        "game_or_pipe_contacted": False, "production_live": False,
        "natural_action_submitted": False,
    }
    try:
        native = args.source_root.resolve() / "ck3_autonomous_player" / "native_bridge"
        # Reuse already delivered stdlib compile/link orchestration helpers.
        # The imported helper's main guard does not execute its historical FIRST.
        helper_path = native / "tools" / "run_prisoner_release_material_first.py"
        spec = importlib.util.spec_from_file_location("release_first_helpers", helper_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("could not load the existing Root compilation helpers")
        helpers = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helpers)
        receipt_path = args.runtime_receipt.resolve()
        receipt = helpers.read_json(receipt_path)
        if receipt.get("dll_build_status") != "GREEN":
            raise ValueError("FIRST needs Root's completed qualified runtime receipt")
        report["runtime_source_head"] = receipt.get("source_head")
        if args.native_exe is not None:
            executable = args.native_exe.resolve()
            # Root's joined build already compiled/linked the unique fixture
            # against its genuine qualified Bridge/runtime/Protocol closure.
            # No compiler environment or second fixture build is needed here.
            environment = None
            report.update({"native_fixture_reused": True,
                "native_fixture_executable": str(executable),
                "fixture_compiled_translation_units": 0})
        else:
            manifest_path = helpers.referenced_path(receipt["manifest"], receipt_path.parent)
            manifest = helpers.read_json(manifest_path)
            plan_path = helpers.referenced_path(manifest["new_compile_and_link_plan"], manifest_path.parent)
            plan = helpers.read_json(plan_path)
            compile_path = helpers.referenced_path(manifest["actual_compile_commands"], manifest_path.parent)
            rows = helpers.read_json(compile_path)
            preferred = "ck3_12004_prisoner_release_action.cpp"
            row = next((item for item in rows if Path(item["file"]).name == preferred), rows[0])
            source = native / "tests" / "ck3_12004_prisoner_release_action_whole_first.cpp"
            obj = output / "prisoner-release-action-first.obj"
            executable = output / "prisoner-release-action-first.exe"
            arguments = helpers.fixture_compile_arguments(row, source, obj, output)
            toolchain = manifest["toolchain"]
            environment = helpers.compiler_environment(
                helpers.referenced_path(toolchain["vcvars64"], manifest_path.parent), output,
                plan.get("compiler_environment_added", {}))
            report.update({"native_fixture_reused": False,
                "manifest": str(manifest_path), "qualified_build_plan": str(plan_path),
                "qualified_compile_commands": str(compile_path), "fixture_compiled_translation_units": 1})
            helpers.execute("fixture-compile", arguments, Path(row["directory"]), environment, output, report)
            qualified_rsp = helpers.referenced_path(plan["response_file"], plan_path.parent)
            rsp = output / "fixture-link.rsp"
            rsp.write_text(subprocess.list2cmdline([str(obj)]) + "\n" +
                qualified_rsp.read_text(encoding="utf-8-sig"), encoding="utf-8", newline="\n")
            report["qualified_bridge_runtime_protocol_response_file"] = str(qualified_rsp)
            helpers.execute("fixture-link", [str(helpers.referenced_path(toolchain["link"], manifest_path.parent)),
                "/nologo", "@" + str(rsp), "/out:" + str(executable), "/machine:x64", "/INCREMENTAL:NO"],
                Path(plan["link_cwd"]), environment, output, report)
        wires, consumed = output / "native", output / "registered"
        helpers.execute("native-first", [str(executable), str(wires)], output, environment, output, report)
        consumer = args.source_root.resolve() / "tools" / \
            "replay_prisoner_release_action_private_12004.py"
        helpers.execute("registered-first", [str(args.python.resolve()), str(consumer),
            "--source-root", str(args.source_root.resolve()), "--native-wire-dir", str(wires),
            "--output-dir", str(consumed)], output, environment, output, report)
        native_receipt = helpers.read_json(wires / "NATIVE-FIRST.json")
        public_receipt = helpers.read_json(consumed / "CONSUMER-FIRST.json")
        if (native_receipt.get("compound_cases") != 5 or public_receipt.get("status") != "GREEN"
                or public_receipt.get("compound_methods") != 1 or len(public_receipt.get("rows", [])) != 5):
            raise ValueError("FIRST did not complete the sole native/public five-case compound")
        report.update({"status": "GREEN", "native_receipt": str(wires / "NATIVE-FIRST.json"),
            "public_receipt": str(consumed / "CONSUMER-FIRST.json"), "compound_methods": 1,
            "native_whole_cases": 5, "public_cases": 5})
    except Exception as error:
        report.update({"status": "RED", "error": str(error)})
    report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    path = output / "ROOT-STANDALONE-FIRST.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "receipt": str(path)}))
    return 0 if report["status"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
