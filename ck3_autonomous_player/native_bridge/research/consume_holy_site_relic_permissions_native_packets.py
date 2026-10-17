"""Consume new C++ permissions packets through actual Driver, Service and MCP."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback
import unittest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-source-root", type=Path, required=True)
    parser.add_argument("--native-fixtures", type=Path)
    parser.add_argument("--required-native-fixture", action="append", default=[])
    parser.add_argument("--native-packet-contract", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        raise FileExistsError("Consumer receipts are immutable; supply a new --output path")
    repo = Path(__file__).resolve().parents[3]
    base = args.base_source_root.resolve()
    contract_path = args.native_packet_contract or repo / "tools/relic-permissions-native-packets-contract-a01.json"
    contract_raw = contract_path.read_bytes()
    contract = json.loads(contract_raw.decode("utf-8"))
    expected_filenames = args.required_native_fixture or contract["expected_filenames"]
    if (not isinstance(expected_filenames, list) or not expected_filenames
            or len(expected_filenames) != len(set(expected_filenames))
            or any(not isinstance(name, str) or Path(name).name != name or not name.endswith(".json")
                   for name in expected_filenames)):
        parser.error("Freeze a unique list of new producer JSON packet basenames")
    os.environ["XAR_RELIC_PERMISSIONS_BASE_SOURCE_ROOT"] = str(base)
    if args.native_fixtures:
        os.environ["XAR_RELIC_PERMISSIONS_NATIVE_FIXTURES"] = str(args.native_fixtures.resolve())
    else:
        os.environ.pop("XAR_RELIC_PERMISSIONS_NATIVE_FIXTURES", None)
    os.environ["XAR_RELIC_PERMISSIONS_REQUIRED_FIXTURES"] = json.dumps(expected_filenames)
    test_path = repo / "ck3_autonomous_player/tests/unit/test_player_holy_site_relic_permissions_12004_native_mcp.py"
    machine = subprocess.check_output([sys.executable, "-B", "-X", "utf8", str(base / "tools/ck3_live_run_id.py"), "machine"], text=True).strip()
    report = {"schema": "relic-permissions-native-mcp-consumer-v1", "machine_id": machine,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(), "status": "FAILED",
        "live_game_qualification": False, "real_engine_getter_execution_proven": False,
        "native_boundary_mocked": ["endpoint I/O", "hello", "state_snapshot"],
        "production_layers": ["NativeHeadlessGameplayDriver", "GameplayBridgeService", "create_server", "MCP ClientSession"],
        "test_path": str(test_path), "test_sha256": hashlib.sha256(test_path.read_bytes()).hexdigest(),
        "required_native_fixtures": expected_filenames,
        "native_packet_contract": {"path": str(contract_path), "sha256": hashlib.sha256(contract_raw).hexdigest()},
        "native_fixture_directory": str(args.native_fixtures) if args.native_fixtures else None,
        "tests_run": 0, "tests_skipped": [], "failures": [], "errors": [], "mcp_results": []}
    stream = io.StringIO()
    try:
        spec = importlib.util.spec_from_file_location("relic_permissions_native_mcp_tests", test_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
        complete = bool(args.native_fixtures) and result.wasSuccessful() and not result.skipped
        report.update(status="COMPILED_NATIVE_PERMISSIONS_PACKETS_THROUGH_REAL_MCP_PASS" if complete else
                      "STATIC_OPTIN_ONLY_PASS_WITH_NATIVE_TESTS_SKIPPED" if result.wasSuccessful() else "FAILED",
                      tests_run=result.testsRun,
                      tests_skipped=[{"test": str(test), "reason": reason} for test, reason in result.skipped],
                      failures=[{"test": str(test), "detail": detail} for test, detail in result.failures],
                      errors=[{"test": str(test), "detail": detail} for test, detail in result.errors],
                      mcp_results=module.RelicPermissionsNativeMcpTests.actual_mcp_results,
                      common_source_hooks=module.HOOKS,
                      loaded_source_files={name: {"path": getattr(sys.modules.get(name), "__file__", None),
                                "candidate_hook_sha256": getattr(sys.modules.get(name), "__candidate_hook_sha256__", None)}
                          for name in ("xar_autoplayer.bridge.native_driver", "xar_autoplayer.bridge.service",
                            "xar_autoplayer.bridge.mcp_server", "xar_autoplayer.bridge.player_holy_site_relic_permissions_private_transport")})
    except Exception:
        report["errors"].append({"test": "consumer_bootstrap", "detail": traceback.format_exc()})
    report["test_log"] = stream.getvalue()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="") as output:
        json.dump(report, output, ensure_ascii=False, indent=2)
        output.write("\n")
    print(stream.getvalue(), end="")
    print(json.dumps({"status": report["status"], "machine_id": machine, "output": str(args.output),
                      "bytes": args.output.stat().st_size, "mcp_results": len(report["mcp_results"])}, ensure_ascii=False))
    return 0 if report["status"] != "FAILED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
