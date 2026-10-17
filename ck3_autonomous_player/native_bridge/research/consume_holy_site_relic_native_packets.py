"""Run the real MCP consumer against externally compiled native fixture packets."""
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
import unittest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-source-root", type=Path)
    parser.add_argument("--native-fixtures", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        raise FileExistsError("Consumer receipts are immutable; supply a new --output path")
    repo = Path(__file__).resolve().parents[3]
    base = (args.base_source_root or repo).resolve()
    os.environ["XAR_HOLY_SITE_RELIC_BASE_SOURCE_ROOT"] = str(base)
    if args.native_fixtures is not None:
        os.environ["XAR_HOLY_SITE_RELIC_NATIVE_FIXTURES"] = str(args.native_fixtures.resolve())
    else:
        os.environ.pop("XAR_HOLY_SITE_RELIC_NATIVE_FIXTURES", None)
    test_path = repo / "ck3_autonomous_player/tests/unit/test_player_holy_site_relic_context_12004_native_mcp.py"
    spec = importlib.util.spec_from_file_location("relic_native_mcp_consumer_tests", test_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
    machine = subprocess.check_output([sys.executable, "-B", "-X", "utf8", str(base / "tools/ck3_live_run_id.py"), "machine"], text=True).strip()
    report = {
        "schema_version": 1,
        "machine_id": machine,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": ("COMPILED_NATIVE_PACKETS_THROUGH_REAL_MCP_PASS" if args.native_fixtures else "STATIC_OPTIN_ONLY_PASS") if result.wasSuccessful() else "FAILED",
        "live_game_qualification": False,
        "real_engine_getter_execution_proven": False,
        "native_boundary_mocked": ["endpoint I/O", "hello", "state_snapshot"],
        "production_layers": ["NativeHeadlessGameplayDriver", "GameplayBridgeService", "create_server", "MCP ClientSession"],
        "test_path": str(test_path),
        "test_sha256": hashlib.sha256(test_path.read_bytes()).hexdigest(),
        "tests_run": result.testsRun,
        "tests_skipped": [{"test": str(test), "reason": reason} for test, reason in result.skipped],
        "failures": [{"test": str(test), "detail": detail} for test, detail in result.failures],
        "errors": [{"test": str(test), "detail": detail} for test, detail in result.errors],
        "test_log": stream.getvalue(),
        "mcp_results": module.RelicNativeMcpTests.actual_mcp_results,
        "loaded_source_files": {name: getattr(sys.modules.get(name), "__file__", None) for name in (
            "xar_autoplayer.bridge.native_driver", "xar_autoplayer.bridge.service",
            "xar_autoplayer.bridge.mcp_server", "xar_autoplayer.bridge.player_holy_site_relic_context_private_transport")},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="") as output:
        output.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(stream.getvalue(), end="")
    print(json.dumps({"status": report["status"], "machine_id": machine, "output": str(args.output),
                      "bytes": args.output.stat().st_size, "mcp_results": len(report["mcp_results"])}, ensure_ascii=False))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
