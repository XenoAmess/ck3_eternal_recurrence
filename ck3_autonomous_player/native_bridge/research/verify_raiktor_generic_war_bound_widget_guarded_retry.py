#!/usr/bin/env python3
"""Verify the fifth caller-local guarded G2 retry without launching CK3."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import re


HERE = Path(__file__).resolve().parent
BASE_PATH = HERE / "verify_raiktor_generic_war_bound_guarded_retry.py"
SPEC = importlib.util.spec_from_file_location("_xar_four_guard_verify", BASE_PATH)
assert SPEC is not None and SPEC.loader is not None
BASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BASE)

WIDGET_OPTION = "XAR_CK3_ENABLE_STARTUP_WIDGET_NULL_FLAG_CALL_GUARD_V1"
FIFTH_GUARD = "InstallStartupWidgetNullFlagCallGuardV1"


def verify(**kwargs: object) -> dict[str, object]:
    result = BASE.verify(**kwargs)
    contract_path = Path(kwargs["contract_path"])
    source_root = Path(kwargs["source_root"])
    build_dir = Path(kwargs["build_dir"])
    bridge_dll = Path(kwargs["bridge_dll"])
    contract = BASE._read_json(contract_path)
    native = source_root / "ck3_autonomous_player/native_bridge"
    cmake_text = (native / "CMakeLists.txt").read_text(encoding="utf-8-sig")
    bridge_text = (native / "src/bridge.cpp").read_text(encoding="utf-8-sig")
    cache = BASE._cmake_cache(build_dir / "CMakeCache.txt")
    source_contract_path = (
        native
        / "research/fixtures/startup_widget_null_flag_call_guard_v1_source_contract.json"
    )
    source_contract = BASE._read_json(source_contract_path)
    compact_cmake = re.sub(r"\s+", " ", cmake_text)
    checks = result["checks"]
    assert isinstance(checks, dict)
    checks["widget_guard_source_contract_present"] = source_contract_path.is_file()
    checks["widget_guard_option_default_off"] = (
        re.search(
            rf"option\s*\(\s*{WIDGET_OPTION}\s+\"[^\"]+\"\s+OFF\s*\)",
            compact_cmake,
        )
        is not None
    )
    checks["widget_guard_compile_definition_wired"] = (
        f"{WIDGET_OPTION}=1" in cmake_text
    )
    checks["widget_guard_macro_bound"] = (
        f"defined({WIDGET_OPTION})" in bridge_text
        and "kStartupWidgetNullFlagCallGuardEnabledV1 = true" in bridge_text
        and "kStartupWidgetNullFlagCallGuardEnabledV1 = false" in bridge_text
    )
    expected_order = list(BASE.GUARD_ORDER) + [FIFTH_GUARD]
    checks["five_guard_install_order"] = BASE._in_order(bridge_text, expected_order)
    checks["widget_guard_cache_on"] = cache.get(WIDGET_OPTION, "").upper() == "ON"
    checks["widget_guard_requires_containment"] = (
        "static_assert(!kStartupWidgetNullFlagCallGuardEnabledV1 ||"
        in bridge_text
        and cache.get(BASE.OPTION, "").upper() == "ON"
    )
    previous_sha = str(
        contract.get("frozen_previous_four_guard_bridge_dll_sha256", "")
    ).upper()
    checks["fifth_guard_dll_differs_from_four_guard_candidate"] = (
        BASE._sha256_file(bridge_dll) != previous_sha
    )
    semantics = source_contract.get("guard_semantics")
    checks["caller_local_not_global_callee"] = (
        isinstance(semantics, dict)
        and semantics.get("global_callee_patch") is False
        and semantics.get("default_enabled") is False
        and semantics.get("continue_rva") == "0xAF4EED"
    )
    result["kind"] = "ck3_raiktor_generic_war_bound_widget_guarded_retry_verify_only"
    result["configuration"]["widget_guard_cache"] = cache.get(WIDGET_OPTION)
    result["configuration"]["guard_install_order"] = expected_order
    result["identities"]["widget_guard_source_contract_sha256"] = (
        BASE._sha256_file(source_contract_path)
    )
    ok = all(bool(value) for value in checks.values()) and not result["errors"]
    result["ok"] = ok
    result["status"] = "READY_TO_FREEZE" if ok else "BLOCKED"
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--build-dir", type=Path, required=True)
    parser.add_argument("--base-manifest", type=Path, required=True)
    parser.add_argument("--bridge-dll", type=Path, required=True)
    parser.add_argument("--bridge-injector", type=Path, required=True)
    parser.add_argument("--runner", type=Path, required=True)
    parser.add_argument("--attempt-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    result = verify(
        contract_path=args.contract.resolve(),
        source_root=args.source_root.resolve(),
        build_dir=args.build_dir.resolve(),
        base_manifest_path=args.base_manifest.resolve(),
        bridge_dll=args.bridge_dll.resolve(),
        bridge_injector=args.bridge_injector.resolve(),
        runner_path=args.runner.resolve(),
        attempt_dir=args.attempt_dir.resolve(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
