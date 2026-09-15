#!/usr/bin/env python3
"""Validate the private DEV21 construction runtime source contract."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


EXPECTED_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
EXPECTED_SIZE = 95_206_008


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _contains_all(text: str, tokens: list[str], label: str) -> None:
    missing = [token for token in tokens if token not in text]
    _require(not missing, f"{label} is missing tokens: {missing}")


def run(root: Path, ck3_executable: Path) -> None:
    native = root / "ck3_autonomous_player/native_bridge"
    header = (native / "src/domain_construction_application_main_runtime_v1.hpp").read_text(
        encoding="utf-8"
    )
    source = (native / "src/domain_construction_application_main_runtime_v1.cpp").read_text(
        encoding="utf-8"
    )
    cmake = (native / "CMakeLists.txt").read_text(encoding="utf-8")
    bridge = (native / "src/bridge.cpp").read_text(encoding="utf-8")
    mailbox_header = (
        native / "include/xar_bridge/main_thread_query_mailbox_v1.hpp"
    ).read_text(encoding="utf-8")
    mailbox_source = (native / "src/main_thread_query_mailbox_v1.cpp").read_text(
        encoding="utf-8"
    )
    docs = (root / "docs/ck3-native-ai/domain-construction-ai.md").read_text(
        encoding="utf-8-sig"
    )
    abi = json.loads(
        (native / "research/domain_construction_application_main_runtime_v1_abi.json").read_text(
            encoding="utf-8"
        )
    )

    _contains_all(
        header,
        [
            "DomainConstructionBorrowedCollectorFrameV1",
            "DomainConstructionConcreteCandidateCaptureV1",
            "DomainConstructionExactNativeCallsV1",
            "BindCurrentProcessDomainConstructionExactNativeCallsV1",
            "ExecuteDomainConstructionApplicationMainRuntimeV1",
            "kDomainConstructionBuildingPrimaryVtableRvaV1",
            "kDomainConstructionReceiverSingletonRvaV1",
        ],
        "runtime header",
    )
    _contains_all(
        source,
        [
            "CaptureDomainConstructionCostLegalityDoubleSampleV1",
            "PrepareDomainConstructionSharedCandidateV1",
            "SubmitDomainConstructionSharedCandidateV1",
            "candidate.expected_binding.proof_epoch != stamp.pump_epoch",
            "candidate.expected_binding.date_raw != stamp.date_raw",
            "CurrentValidateBuilding",
            "CurrentValidateHolding",
            "CurrentMaterialize",
            "CurrentReceive",
            "CurrentRelease",
            "result.shared.candidate_live = !request.offline_fixture",
        ],
        "runtime source",
    )
    for path in abi["build_integration"]["compiled_sources"]:
        _require(path in cmake, f"default bridge does not compile {path}")
    _require(
        "permitted_executor_quintrigintary" in mailbox_header
        and "permitted_executor_quintrigintary" in mailbox_source,
        "application-main mailbox lacks the private DEV21 executor slot",
    )
    _require(
        "permitted_executor_quintrigintary" in bridge
        and "ExecuteDomainConstructionApplicationMainRuntimeV1" in bridge,
        "default bridge does not register the private DEV21 executor",
    )
    _require(
        "static-ready-private-application-main-runtime-live-pending" in docs,
        "domain construction documentation lacks the DEV21 status",
    )
    _require(abi["schema_version"] == 1, "unexpected DEV21 schema version")
    _require(not abi["application_main_collector"]["engine_pointer_in_result"],
             "engine pointers must not enter the runtime result")
    _require(not abi["verification"]["production_live"],
             "offline DEV21 verification must not claim production live")

    executable = ck3_executable.read_bytes()
    _require(len(executable) == EXPECTED_SIZE, "unexpected CK3 executable size")
    _require(
        hashlib.sha256(executable).hexdigest().upper() == EXPECTED_SHA256,
        "unexpected CK3 executable SHA-256",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[3]
    )
    parser.add_argument("--ck3-executable", type=Path, required=True)
    arguments = parser.parse_args()
    run(arguments.root.resolve(), arguments.ck3_executable.resolve())
    print("domain-construction-application-main-source-contract: GREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
