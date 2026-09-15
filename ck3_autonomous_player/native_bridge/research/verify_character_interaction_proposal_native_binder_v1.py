#!/usr/bin/env python3
"""Verify the exact 1.19.0.6 private diplomacy native binder."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


PRIVATE_KEY = "character_interaction_proposal_native_binder_v1"
ACTION_KEY = "character_interaction_proposal_action_core_v1"
PAYLOAD_KEY = "character_interaction_proposal_payload_source_extension_v1"
BASELINE = "25f444782348f063baa0c092d0209ffa02e0faf6"
EXE_SIZE = 95_206_008
EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require_tokens(text: str, tokens: tuple[str, ...], label: str) -> None:
    missing = [token for token in tokens if token not in text]
    require(not missing, f"{label} missing required tokens: {missing}")


class PortableExecutable:
    def __init__(self, data: bytes) -> None:
        self.data = data
        pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
        require(data[pe_offset : pe_offset + 4] == b"PE\0\0", "invalid PE")
        section_count = struct.unpack_from("<H", data, pe_offset + 6)[0]
        optional_size = struct.unpack_from("<H", data, pe_offset + 20)[0]
        section_table = pe_offset + 24 + optional_size
        self.sections: list[tuple[int, int, int, int]] = []
        for index in range(section_count):
            offset = section_table + index * 40
            virtual_size, virtual_address, raw_size, raw_offset = struct.unpack_from(
                "<IIII", data, offset + 8
            )
            self.sections.append(
                (virtual_address, max(virtual_size, raw_size), raw_offset, raw_size)
            )

    def read_rva(self, rva: int, size: int) -> bytes:
        for virtual_address, mapped_size, raw_offset, raw_size in self.sections:
            delta = rva - virtual_address
            if 0 <= delta and delta + size <= mapped_size and delta + size <= raw_size:
                return self.data[raw_offset + delta : raw_offset + delta + size]
        raise RuntimeError(f"RVA span is not file-backed: 0x{rva:X}+{size}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, required=True)
    args = parser.parse_args()

    native_root = Path(__file__).resolve().parents[1]
    repo_root = native_root.parents[1]
    header = (
        native_root
        / "include/xar_bridge/character_interaction_proposal_native_binder_v1.hpp"
    ).read_text(encoding="utf-8")
    source = (
        native_root / "src/character_interaction_proposal_native_binder_v1.cpp"
    ).read_text(encoding="utf-8")
    test = (
        native_root / "src/character_interaction_proposal_native_binder_v1_test.cpp"
    ).read_text(encoding="utf-8")
    docs = (
        repo_root
        / "docs/ck3-native-ai/character-interaction-proposal-native-binder.md"
    ).read_text(encoding="utf-8")
    abi = json.loads(
        (
            native_root
            / "research/character_interaction_proposal_native_binder_v1_abi.json"
        ).read_text(encoding="utf-8")
    )
    action_abi = json.loads(
        (
            native_root
            / "research/character_interaction_proposal_action_core_v1_abi.json"
        ).read_text(encoding="utf-8")
    )
    payload_abi = json.loads(
        (
            native_root
            / "research/character_interaction_proposal_payload_source_extension_v1_abi.json"
        ).read_text(encoding="utf-8")
    )

    require(abi["schema_version"] == 1, "ABI schema drifted")
    require(abi["private_key"] == PRIVATE_KEY, "private key drifted")
    require(abi["upstream"]["action_core_private_key"] == ACTION_KEY, "action key drifted")
    require(abi["upstream"]["payload_source_private_key"] == PAYLOAD_KEY, "payload key drifted")
    require(abi["upstream"]["baseline_commit"] == BASELINE, "baseline drifted")
    require(abi["upstream"]["allowlisted_interaction_count"] == 11, "allowlist count drifted")
    require(abi["upstream"]["typed_special_count"] == 6, "typed count drifted")
    require(action_abi["private_key"] == ACTION_KEY, "DIPLO4 ABI unavailable")
    require(payload_abi["private_key"] == PAYLOAD_KEY, "DIPLO5 ABI unavailable")
    require(abi["exact_build"]["product_version"] == "1.19.0.6", "version drifted")
    require(abi["exact_build"]["executable_size"] == EXE_SIZE, "EXE size contract drifted")
    require(abi["exact_build"]["executable_sha256"] == EXE_SHA256, "EXE hash contract drifted")

    layout = abi["native_layout"]
    require(
        layout
        == {
            "character_storage_slot_rva": "0x570C130",
            "landed_title_storage_slot_rva": "0x570C410",
            "command_manager_rva": "0x57621F0",
            "context_size": "0x338",
            "command_size": "0x368",
            "command_primary_vtable_rva": "0x40829F8",
            "command_secondary_vtable_rva": "0x40829C8",
            "command_secondary_vtable_offset": "0x18",
            "command_embedded_context_offset": "0x20",
            "submit_flags": "0x0E",
        },
        "native command layout drifted",
    )
    require(
        all(value is False for value in abi["scope"].values()),
        "private binder claimed forbidden shared/live scope",
    )
    readiness = abi["readiness"]
    require(
        all(
            readiness[key] is True
            for key in (
                "private_native_binder_implemented",
                "eleven_key_command_spine_ready",
                "typed_special_reconstruction_seam_ready",
                "diplo5_recheck_ready",
                "exact_command_lifecycle_ready",
            )
        ),
        "implemented readiness regressed",
    )
    require(
        readiness["shared_glue_registered"] is False
        and readiness["public_schema_registered"] is False
        and readiness["production_action_live"] is False,
        "private static binder readiness was overstated",
    )

    require_tokens(
        header,
        (
            '"character_interaction_proposal_native_binder_v1"',
            "kCharacterInteractionProposalCommandManagerRvaV1 = 0x57621F0",
            "kCharacterInteractionProposalConstructCommandRvaV1 = 0x26B3220",
            "kCharacterInteractionProposalSubmitCommandRvaV1 = 0x0973E00",
            "kCharacterInteractionProposalNativeContextSizeV1 = 0x338",
            "kCharacterInteractionProposalNativeCommandSizeV1 = 0x368",
            "kCharacterInteractionProposalCommandContextOffsetV1 = 0x20",
            "kCharacterInteractionProposalSubmitFlagsV1 = 0x0E",
            "MaterializeCharacterInteractionProposalSpecialContextV1",
            "ExecuteCharacterInteractionProposalFromNativeBinderV1",
        ),
        "header",
    )
    require_tokens(
        source,
        (
            "ResolveCharacter(environment, request.actor_character_id)",
            "InvokeMaterializer(",
            "InvokeConstructTwoRole(",
            "InvokeRefresh(environment.refresh_context, native_context)",
            "InvokeStep(environment.finalize_context, native_context)",
            "ReReadSpecialSource(*binder, native_context, definition)",
            "ReReadSpecialSource(*binder,",
            "InvokeCanSend(environment.complete_can_send",
            "kCharacterInteractionProposalCommandSecondaryVtableOffsetV1",
            "InvokeSubmit(",
            "DestroyIfOwned(environment, native_context)",
            "environment.submit_abi_certified = !binder.environment.offline_fixture",
        ),
        "source",
    )
    require_tokens(
        test,
        (
            "TestExactEnvironmentAndConfigurationGates",
            "TestTwoRoleSubmitOnceAndCleanup",
            "TestTypedSpecialRereadAndDrift",
            "TestIdentityCanSendCommandAndQueueFailures",
            "fixture.destroy_calls == 2",
            'ack.reason == "capture_drift"',
            'ack.reason == "typed_payload_source_mismatch"',
            'ack.reason == "character_identity_unavailable"',
            'ack.reason == "complete_can_send_rejected"',
            'ack.reason == "command_identity_mismatch"',
            'ack.reason == "command_queue_rejected"',
        ),
        "native test",
    )
    require_tokens(
        docs,
        (
            "static-ready, private and unwired",
            "1.19.0.6",
            "0x26B3220",
            "0x40829F8",
            "DIPLO5",
            "submitted_verification_pending",
            "Live pending",
        ),
        "documentation",
    )

    cmake_text = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in native_root.rglob("CMakeLists.txt")
    )
    bridge_text = (native_root / "src/bridge.cpp").read_text(
        encoding="utf-8", errors="replace"
    )
    require(PRIVATE_KEY not in cmake_text, "private binder entered shared CMake")
    require(PRIVATE_KEY not in bridge_text, "private binder entered bridge.cpp")

    executable = args.exe.resolve()
    require(executable.is_file(), f"missing executable: {executable}")
    executable_bytes = executable.read_bytes()
    require(len(executable_bytes) == EXE_SIZE, "frozen EXE size mismatch")
    require(digest(executable_bytes) == EXE_SHA256, "frozen EXE hash mismatch")
    image = PortableExecutable(executable_bytes)
    anchors = abi["exact_build"]["code_anchors"]
    require(len(anchors) == 10, "anchor count drifted")
    for anchor in anchors:
        span = image.read_rva(int(anchor["rva"], 16), anchor["size"])
        require(
            digest(span) == anchor["sha256"],
            f"code anchor drifted: {anchor['name']}",
        )

    print("character_interaction_proposal_native_binder_v1 contract: GREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
