"""Verify exact-source and frozen private Council scene inputs without CK3."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from inspect_council_final_gate_scene import inspect


class EvidenceMissing(Exception):
    pass


class ContractRed(Exception):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def frozen_file(path: Path, expected_sha256: str, label: str) -> None:
    if not path.is_file():
        raise EvidenceMissing(f"{label} absent: {path}")
    if sha256(path) != expected_sha256.upper():
        raise ContractRed(f"{label} SHA-256 differs: {path}")


def source_preflight(contract: dict[str, object], game: Path,
                     repo: Path) -> dict[str, object]:
    build = contract["game"]
    frozen_file(game / "binaries" / "ck3.exe", build["exe_sha256"],
                "exact CK3 EXE")
    rows = contract["exact_source"]
    if not isinstance(rows, list) or len(rows) != 11:
        raise ContractRed("exact source row count differs")
    for row in rows:
        relative = row["path"]
        path = game / "game" / relative
        frozen_file(path, row["sha256"], relative)
        source = path.read_text(encoding="utf-8-sig", errors="replace")
        if any(anchor not in source for anchor in row["anchors"]):
            raise ContractRed(f"exact source anchor differs: {relative}")
    abi = contract["native_abi"]
    frozen_file(repo / abi["repo_path"], abi["sha256"],
                "Council exact-build ABI manifest")
    return {"status": "exact_source_green", "source_file_count": len(rows),
            "exe_sha256": build["exe_sha256"],
            "native_abi_sha256": abi["sha256"]}


def historic_preflight(contract: dict[str, object],
                       r695: Path | None, r700: Path | None) -> dict[str, object]:
    if r695 is None and r700 is None:
        return {"status": "historical_evidence_not_supplied"}
    if r695 is None or r700 is None:
        raise EvidenceMissing("R695 and R700 terminals must be supplied together")
    evidence = contract["historical_evidence"]
    try:
        scenes = [
            inspect(r695, evidence["r695_private_terminal_sha256"]),
            inspect(r700, evidence["r700_private_terminal_sha256"]),
        ]
    except (OSError, ValueError, json.JSONDecodeError) as failure:
        raise EvidenceMissing(f"historical private terminal unavailable: {failure}") from failure
    missing = (
        "isolated_guest_rejection_ids",
        "isolated_candidate_pending_rejection_ids",
        "isolated_replacement_fireability_denial_ids",
    )
    if any(scene[field] for scene in scenes for field in missing):
        raise ContractRed("frozen R695/R700 unexpectedly contain a positive missing gate")
    if scenes[0]["incumbent_character_id"] != 32716 or (
            scenes[1]["incumbent_character_id"] !=
            evidence["r700_replacement_incumbent"]):
        raise ContractRed("historical incumbent mapping differs")
    return {"status": "historical_complete_three_positive_scenes_absent",
            "r695_candidate_count": scenes[0]["candidate_count"],
            "r700_candidate_count": scenes[1]["candidate_count"],
            "r700_incumbent_character_id": scenes[1]["incumbent_character_id"],
            "already_councillor_positive_ids":
            scenes[0]["already_councillor_positive_ids"]}


def runtime_preflight(arguments: argparse.Namespace,
                      contract: dict[str, object]) -> dict[str, object]:
    names = ("checkpoint", "checkpoint_sha256", "driver_state",
             "driver_sha256", "bridge_dll", "bridge_dll_sha256", "injector",
             "injector_sha256", "cmake_cache", "dlc_load")
    values = [getattr(arguments, name) for name in names]
    if all(value is None for value in values):
        return {"status": "fresh_runtime_pair_not_supplied",
                "owned_ck3_inventory": "must_be_checked_by_sole_operator"}
    if any(value is None for value in values):
        raise EvidenceMissing("freeze checkpoint, driver, DLL, injector, CMake cache and DLC/mod list together")
    for label, path, expected in (
            ("game checkpoint", arguments.checkpoint, arguments.checkpoint_sha256),
            ("agent driver state", arguments.driver_state, arguments.driver_sha256),
            ("native bridge DLL", arguments.bridge_dll, arguments.bridge_dll_sha256),
            ("native injector", arguments.injector, arguments.injector_sha256)):
        frozen_file(path, expected, label)
    if arguments.checkpoint.open("rb").read(7) != b"SAV0101":
        raise ContractRed("game checkpoint header differs")
    if not arguments.cmake_cache.is_file():
        raise EvidenceMissing("frozen native CMake cache absent")
    cmake = arguments.cmake_cache.read_text(encoding="utf-8", errors="replace")
    for flag, value in contract["interface"]["private_query_build_flags"].items():
        if f"{flag}:BOOL={value}" not in cmake:
            raise ContractRed(f"private gate-only native build option differs: {flag}")
    if not arguments.dlc_load.is_file():
        raise EvidenceMissing("frozen DLC/mod list absent")
    loaded = json.loads(arguments.dlc_load.read_text(encoding="utf-8-sig"))
    if loaded != {"enabled_mods": ["mod/xar_autoplayer.mod"],
                  "disabled_dlcs": []}:
        raise ContractRed("standard preview DLC/mod declaration differs")
    return {
        "status": "frozen_pair_and_private_gate_only_build_green",
        "checkpoint_sha256": arguments.checkpoint_sha256.upper(),
        "driver_state_sha256": arguments.driver_sha256.upper(),
        "bridge_dll_sha256": arguments.bridge_dll_sha256.upper(),
        "injector_sha256": arguments.injector_sha256.upper(),
        "owned_ck3_inventory": "must_be_checked_by_sole_operator",
        "paused_feudal_live_identity": "still_requires_real_native_frame",
    }


def scene_preflight(arguments: argparse.Namespace,
                    contract: dict[str, object]) -> dict[str, object]:
    if arguments.scene_terminal is None:
        return {"status": "waiting_real_naturally_positive_paused_scene",
                "unmet": list(contract["scene_requirements"])}
    if arguments.scene_terminal_sha256 is None:
        raise EvidenceMissing("scene terminal SHA-256 must be frozen")
    try:
        scene = inspect(arguments.scene_terminal,
                        arguments.scene_terminal_sha256)
    except (OSError, ValueError, json.JSONDecodeError) as failure:
        raise EvidenceMissing(f"same-frame native scene query unavailable: {failure}") from failure
    positive = {
        gate: scene[requirement["native_classification_field"]]
        for gate, requirement in contract["scene_requirements"].items()
    }
    return {
        "status": "private_read_only_scene_classified_no_action",
        "owner_character_id": scene["owner_character_id"],
        "incumbent_character_id": scene["incumbent_character_id"],
        "candidate_count": scene["candidate_count"],
        "snapshot": scene["snapshot"],
        "isolated_positive_ids": positive,
        "unmet": [gate for gate, ids in positive.items() if not ids],
        "typed_rejection_and_game_state": "still_requires_controlled_live_action",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=Path(__file__).with_name(
        "council_final_gate_natural_scenes_1_19_0_6.json"))
    parser.add_argument("--contract-sha256", required=True)
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--r695-terminal", type=Path)
    parser.add_argument("--r700-terminal", type=Path)
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--checkpoint-sha256")
    parser.add_argument("--driver-state", type=Path)
    parser.add_argument("--driver-sha256")
    parser.add_argument("--bridge-dll", type=Path)
    parser.add_argument("--bridge-dll-sha256")
    parser.add_argument("--injector", type=Path)
    parser.add_argument("--injector-sha256")
    parser.add_argument("--cmake-cache", type=Path)
    parser.add_argument("--dlc-load", type=Path)
    parser.add_argument("--scene-terminal", type=Path)
    parser.add_argument("--scene-terminal-sha256")
    arguments = parser.parse_args()
    try:
        frozen_file(arguments.contract, arguments.contract_sha256,
                    "Council natural-scene contract")
        contract = json.loads(arguments.contract.read_text(encoding="utf-8"))
        if contract.get("schema") != (
                "xar.ck3.private.council-final-gate-natural-scenes/1.19.0.6-v1"):
            raise ContractRed("Council natural-scene contract schema differs")
        result = {
            "status": "no_launch_preflight_complete",
            "ck3_launched": False,
            "public_council_registered_or_advertised": False,
            "contract_sha256": arguments.contract_sha256.upper(),
            "source": source_preflight(contract, arguments.game_dir,
                                       arguments.repo_root),
            "historical": historic_preflight(
                contract, arguments.r695_terminal, arguments.r700_terminal),
            "runtime": runtime_preflight(arguments, contract),
            "scene": scene_preflight(arguments, contract),
        }
    except ContractRed as failure:
        print(json.dumps({"status": "RED_EXACT_CONTRACT_MISMATCH",
                          "reason": str(failure), "ck3_launched": False},
                         sort_keys=True), file=sys.stderr)
        return 1
    except (EvidenceMissing, OSError, ValueError, json.JSONDecodeError) as failure:
        print(json.dumps({"status": "evidence_insufficient",
                          "reason": str(failure), "ck3_launched": False},
                         sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
