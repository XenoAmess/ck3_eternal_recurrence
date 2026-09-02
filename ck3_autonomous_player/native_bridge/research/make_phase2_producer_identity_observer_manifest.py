#!/usr/bin/env python3
"""Create the no-launch acceptance manifest for the private producer observer."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re


GIT_SHA = re.compile(r"^[0-9a-fA-F]{40}$")
SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")
EXE_SHA = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
OPTION = "XAR_CK3_ENABLE_PHASE2_PRODUCER_IDENTITY_OBSERVER_V1"
HEARTBEAT = "phase2_producer_identity_observer_v1"
ABI = Path("ck3_autonomous_player/native_bridge/research/phase2_producer_identity_observer_v1_abi.json")
SOURCE_CONTRACT = Path("ck3_autonomous_player/native_bridge/research/fixtures/phase2_producer_identity_observer_v1_source_contract.json")
REPORT_SCHEMA = "ck3_autonomous_player/native_bridge/research/phase2_producer_identity_observer_v1_report.schema.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def create_manifest(
    source_root: Path, source_commit: str, bridge_sha: str, injector_sha: str
) -> dict[str, object]:
    if GIT_SHA.fullmatch(source_commit) is None:
        raise ValueError("source commit must be a full Git SHA")
    if SHA256.fullmatch(bridge_sha) is None or SHA256.fullmatch(injector_sha) is None:
        raise ValueError("binary hashes must be SHA-256 digests")
    abi = source_root / ABI
    source_contract = source_root / SOURCE_CONTRACT
    schema = source_root / REPORT_SCHEMA
    if not all(path.is_file() for path in (abi, source_contract, schema)):
        raise ValueError("observer source contract files are missing")
    fields = json.loads(source_contract.read_text(encoding="utf-8"))["required_report_fields"]
    return {
        "schema_version": 1,
        "kind": "zg361_phase2_native_observer_seam",
        "result": "GREEN",
        "source_git_commit": source_commit.lower(),
        "exact_build": {
            "game_version": "1.19.0.6",
            "game_executable_sha256": EXE_SHA.lower(),
        },
        "build": {
            "private_option": OPTION,
            "private_option_enabled": True,
            "bridge_dll_sha256": bridge_sha.lower(),
            "bridge_injector_sha256": injector_sha.lower(),
        },
        "seam": {
            "hooks": [
                {"rva": "0x3B9CFD2", "anchor_sha256": "9a7ae24d86bc3453a89a92e6b948ee54a6da043029ccf76e2b3d1443bd1bbe1e"},
                {"rva": "0x3B9CFD7", "anchor_sha256": "5d5bffd230909b1d43c43f744071889f298b8bc6f3253da74f979d4a19beeb6b"},
            ],
            "physical_transaction": "0x3B9CFD2..0x3B9CFE2",
            "task_register": "RBX",
            "callback_field_offset": "0x38",
            "heartbeat_object": HEARTBEAT,
            "prior_list_domain_callback_slot2_rva": "0x817C20",
            "abi": {"path": ABI.as_posix(), "sha256": digest(abi)},
            "source_contract": {
                "path": SOURCE_CONTRACT.as_posix(),
                "sha256": digest(source_contract),
            },
        },
        "report_contract": {
            "schema": REPORT_SCHEMA,
            "schema_sha256": digest(schema),
            "artifact_name": "phase2-producer-identity-observer-v1.json",
            "required_fields": fields,
        },
        "launch": {"performed": False, "authorized_by_manifest_alone": False},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--bridge-dll-sha256", required=True)
    parser.add_argument("--bridge-injector-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = create_manifest(
        args.source_root.resolve(), args.source_commit,
        args.bridge_dll_sha256, args.bridge_injector_sha256,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
