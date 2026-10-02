#!/usr/bin/env python3
"""Disk-only source and native ABI admission for the default-off H2743 reader.

This never starts CK3 or certifies a loaded DLL. The existing exact-build
extractor checks EXE bytes, PE metadata, eight instruction ranges and call
edges; the two-root verifier checks six exact stock script files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import extract_g2_actual_truce_expiry_abi as native
import verify_h2743_surrender_root_coverage as roots


SOURCE_FILES = (
    "CMakeLists.txt",
    "include/xar_bridge/ck3_11906.hpp",
    "include/xar_bridge/game_adapter.hpp",
    "include/xar_bridge/game_contract.hpp",
    "include/xar_bridge/h2743_preaction_existing_truce_v1.hpp",
    "include/xar_bridge/protocol.hpp",
    "include/xar_bridge/raiktor_actual_truce_expiry_v1.hpp",
    "src/attach_host.cpp",
    "src/bridge.cpp",
    "src/ck3_11906.cpp",
    "src/ck3_11906_adapter.cpp",
    "src/game_adapter.cpp",
    "src/game_adapter_test.cpp",
    "src/h2743_preaction_existing_truce_v1.cpp",
    "src/h2743_preaction_existing_truce_v1_test.cpp",
    "src/protocol.cpp",
    "src/raiktor_actual_truce_expiry_v1.cpp",
    "research/extract_g2_actual_truce_expiry_abi.py",
    "research/probe_h2743_preaction_truce_abi.py",
    "research/verify_h2743_existing_truce_source_abi_v1.py",
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def source_hashes(native_root: Path) -> dict[str, str]:
    return {
        name: digest((native_root / name).read_bytes())
        for name in SOURCE_FILES
    }


def validate_source_contract(texts: dict[str, str]) -> None:
    required = {
        "CMakeLists.txt": (
            "XAR_CK3_ENABLE_H2743_PREACTION_EXISTING_TRUCE_CANDIDATE_V1\n"
            "  \"Enable the exact H2743 read-only attacker-to-defender existing-slot query\"\n"
            "  OFF",
            "src/h2743_preaction_existing_truce_v1.cpp",
        ),
        "src/ck3_11906.cpp": (
            "ResolveWar(bindings, *bindings.game_state_slot,",
            "individual_county_de_jure_cb",
            "kWarTargetedTitleIdsOffset",
            "bindings.has_character_truce",
            "bindings.get_character_truce_end_date",
        ),
        "src/ck3_11906_adapter.cpp": (
            "#if defined(XAR_CK3_ENABLE_H2743_PREACTION_EXISTING_TRUCE_CANDIDATE_V1)\n"
            "    + 1\n#endif",
            "#if defined(XAR_CK3_ENABLE_H2743_PREACTION_EXISTING_TRUCE_CANDIDATE_V1)\n"
            "    ck3_11906::kH2743ExistingTruceV1Capability,\n#endif",
        ),
        "src/game_adapter.cpp": (
            "#if defined(XAR_CK3_ENABLE_H2743_PREACTION_EXISTING_TRUCE_CANDIDATE_V1)\n"
            "  } else if (capability.empty() &&\n"
            "             step == ck3_11906::kH2743ExistingTruceV1Step) {\n"
            "    capability = ck3_11906::kH2743ExistingTruceV1Capability;\n"
            "#endif",
        ),
        "src/game_adapter_test.cpp": (
            "!exact_adapter->supports_step(\n"
            "          xar::ck3_11906::kH2743ExistingTruceV1Step)",
            "default-off H2743 read-only step was advertised",
            "partial.supports_step(xar::ck3_11906::kH2743ExistingTruceV1Step)",
        ),
        "src/bridge.cpp": (
            "expected_checkpoint_sha256",
            "expected_episode_id",
            "expected_exe_sha256",
            "expected_public_revision",
            "expected_native_revision",
            "expected_actor_character_id",
            "expected_war_id",
            "AdmitH2743PreactionFrameClaimV1",
            "expected_revision == state_revision",
            "ReadH2743PreactionExistingTruceV1(game, existing)",
        ),
        "src/h2743_preaction_existing_truce_v1.cpp": (
            "claim.snapshot_id != \"native:\" + std::to_string(state_revision)",
            "claim.public_revision == 0",
            "IsExactPausedFrame(actual)",
            "GuardedHasTruce",
            "GuardedEndDate",
            "war_after != war_before",
            "expiry_first != expiry_second",
            "post_surrender_actual_expiry_date_raw\\\":null",
            "action_literal\\\":null",
        ),
    }
    for name, tokens in required.items():
        source = texts[name]
        for token in tokens:
            if token not in source:
                raise ValueError(f"H2743 source contract missing {name}: {token}")
    core = texts["src/h2743_preaction_existing_truce_v1.cpp"]
    for forbidden in ("evaluate_truce_duration_days", "add_truce_one_way",
                      "setup_de_jure_cb", "resolve_title_and_vassal_change"):
        if forbidden in core:
            raise ValueError(f"H2743 read-only core contains {forbidden}")


def collect(exe: Path, game_root: Path, native_root: Path) -> dict[str, Any]:
    abi = native.extract(exe, native_root)
    root_result = roots.verify(game_root, roots.REQUIRED_ROOTS)
    if abi["build"]["executable_sha256"] != native.EXPECTED_SHA256:
        raise ValueError("exact executable SHA drift")
    if (abi["candidate"]["owner_binding"] !=
            "living current played character"):
        raise ValueError("old truce reader owner binding changed")
    if root_result["status"] != "known_script_roots_bound_only":
        raise ValueError("H2743 stock script-root status changed")
    validate_source_contract({
        name: (native_root / name).read_text(encoding="utf-8")
        for name in SOURCE_FILES
    })
    return {
        "schema": "xar.ck3.h2743_existing_truce_source_abi.v1",
        "status": "static_source_abi_verified_build_pending",
        "candidate_compile_option":
            "XAR_CK3_ENABLE_H2743_PREACTION_EXISTING_TRUCE_CANDIDATE_V1=ON",
        "default_enabled": False,
        "live_observed": False,
        "loaded_dll_sha256": None,
        "checkpoint_bytes_authenticated_here": False,
        "episode_authenticated_here": False,
        "post_surrender_actual_expiry_date_raw": None,
        "effect_projection_complete": False,
        "material_complete": False,
        "action_literal": None,
        "build": abi["build"],
        "native_ranges": abi["native_ranges"],
        "native_bindings": abi["bindings"],
        "stock_script_sha256": root_result["source_sha256"],
        "stock_required_root_sha256": root_result["root_sha256"],
        "source_sha256": source_hashes(native_root),
    }


def admit_frozen(actual: dict[str, Any], frozen: dict[str, Any]) -> None:
    if frozen.get("schema") != "xar.ck3.h2743_existing_truce_source_abi.v1":
        raise ValueError("wrong frozen H2743 source/ABI schema")
    if (frozen.get("status") != "static_source_abi_verified_build_pending"
            or frozen.get("default_enabled") is not False
            or frozen.get("live_observed") is not False
            or frozen.get("loaded_dll_sha256") is not None
            or frozen.get("post_surrender_actual_expiry_date_raw") is not None
            or frozen.get("effect_projection_complete") is not False
            or frozen.get("material_complete") is not False
            or frozen.get("action_literal") is not None):
        raise ValueError("frozen H2743 candidate overclaims readiness or effect")
    if actual != frozen:
        raise ValueError("H2743 source, stock scripts or exact native ABI drift")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--game-root", type=Path,
                        default=Path("C:/SteamLibrary/steamapps/common/Crusader Kings III/game"))
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).with_name(
                            "h2743_existing_truce_source_abi_v1.json"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    native_root = Path(__file__).resolve().parents[1]
    try:
        result = collect(args.exe.resolve(), args.game_root.resolve(),
                         native_root)
        rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.check:
            if not args.output.exists():
                raise ValueError("frozen H2743 source/ABI artifact is missing")
            admit_frozen(result, json.loads(args.output.read_text(encoding="utf-8")))
            if args.output.read_text(encoding="utf-8") != rendered:
                raise ValueError("frozen H2743 source/ABI formatting changed")
            print("OK: exact H2743 source and native ABI; build/live pending")
        else:
            if args.output.exists():
                raise ValueError("refusing to overwrite an existing source/ABI artifact")
            args.output.write_text(rendered, encoding="utf-8", newline="\n")
            print(args.output)
    except (OSError, UnicodeError, ValueError, roots.CoverageError) as error:
        print(json.dumps({"status": "RED", "reason": str(error),
                          "effect_projection_complete": False,
                          "action_literal": None}, ensure_ascii=False))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
