#!/usr/bin/env python3
"""Verify the private exact-build proposal payload source extension."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


PRIVATE_KEY = "character_interaction_proposal_payload_source_extension_v1"
UPSTREAM_KEY = "character_interaction_proposal_action_core_v1"
BASELINE = "9f987c9d53fc73130de68c74480e5e671560a797"
EXE_SIZE = 95_206_008
EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
EXPECTED_KEYS = [
    "educate_child_interaction",
    "offer_ward_interaction",
    "offer_guardianship_interaction",
    "grant_titles_interaction",
    "grant_vassal_interaction",
    "ransom_interaction",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


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
    parser.add_argument(
        "--exe", type=Path, help="optional frozen 1.19.0.6 executable to hash"
    )
    args = parser.parse_args()
    native_root = Path(__file__).resolve().parents[1]
    repo_root = native_root.parents[1]
    header = (
        native_root
        / "include/xar_bridge/character_interaction_proposal_payload_source_extension_v1.hpp"
    ).read_text(encoding="utf-8")
    source = (
        native_root
        / "src/character_interaction_proposal_payload_source_extension_v1.cpp"
    ).read_text(encoding="utf-8")
    test = (
        native_root
        / "src/character_interaction_proposal_payload_source_extension_v1_test.cpp"
    ).read_text(encoding="utf-8")
    docs = (
        repo_root
        / "docs/ck3-native-ai/character-interaction-proposal-payload-source-extension.md"
    ).read_text(encoding="utf-8")
    abi = load_json(
        native_root
        / "research/character_interaction_proposal_payload_source_extension_v1_abi.json"
    )
    contract = load_json(
        native_root
        / "research/fixtures/character_interaction_proposal_payload_source_extension_v1_contract.json"
    )
    upstream = load_json(
        native_root / "research/character_interaction_proposal_action_core_v1_abi.json"
    )

    require(abi["schema_version"] == 1, "ABI schema drifted")
    require(abi["private_key"] == PRIVATE_KEY, "private key drifted")
    require(abi["upstream"]["private_key"] == UPSTREAM_KEY, "upstream key drifted")
    require(abi["upstream"]["baseline_commit"] == BASELINE, "DIPLO4 base drifted")
    require(
        abi["upstream"]["typed_payload_source_keys"] == EXPECTED_KEYS,
        "typed payload key order drifted",
    )
    require(upstream["private_key"] == UPSTREAM_KEY, "upstream ABI unavailable")
    require(abi["exact_build"]["executable_size"] == EXE_SIZE, "EXE size drifted")
    require(
        abi["exact_build"]["executable_sha256"] == EXE_SHA256,
        "EXE hash drifted",
    )
    require(contract["schema_version"] == 1, "contract schema drifted")
    require(contract["private_key"] == PRIVATE_KEY, "contract key drifted")
    require(contract["upstream_private_key"] == UPSTREAM_KEY, "contract upstream drifted")
    require(contract["upstream_baseline_commit"] == BASELINE, "contract base drifted")
    require(
        [row["interaction_key"] for row in contract["expected_payload_sources"]]
        == EXPECTED_KEYS,
        "fixture payload set drifted",
    )

    memory = abi["collector_memory"]
    require(
        memory
        == {
            "context_size": "0x338",
            "definition_offset": "0x00",
            "actor_full_character_id_offset": "0x2D8",
            "recipient_full_character_id_offset": "0x2DC",
            "secondary_actor_full_character_id_offset": "0x2E0",
            "secondary_recipient_full_character_id_offset": "0x2E4",
            "intermediary_full_character_id_offset": "0x2E8",
            "selected_options_data_offset": "0x300",
            "selected_options_capacity_offset": "0x308",
            "selected_options_count_offset": "0x30C",
            "special_data_offset": "0x330",
            "definition_selected_options_count_offset": "0x2554",
        },
        "collector memory layout drifted",
    )
    require(
        abi["grant_titles_offer"] == {
            "vtable_rva": "0x4112BA8",
            "selected_id_data_offset": "0x08",
            "selected_id_capacity_offset": "0x10",
            "selected_id_count_offset": "0x14",
            "element": "signed int32 full LandedTitleID",
            "maximum_published_count": 128,
        },
        "grant-titles offer layout drifted",
    )
    require(
        all(value is False for value in abi["scope"].values()),
        "private scope claimed a forbidden integration",
    )
    readiness = abi["readiness"]
    require(
        all(
            readiness[key] is True
            for key in (
                "six_typed_payload_sources_implemented",
                "exact_collector_memory_bound",
                "full_generation_identity_preserved",
                "frame_proof_and_date_preserved",
                "religious_option_deferred",
            )
        ),
        "implemented readiness regressed",
    )
    require(
        readiness["private_source_wired_to_public_bridge"] is False
        and readiness["production_action_live"] is False,
        "unwired private extension was overstated",
    )

    require_tokens(
        header,
        (
            '"character_interaction_proposal_payload_source_extension_v1"',
            "kCharacterInteractionProposalPayloadCharacterStorageSlotRvaV1",
            "kCharacterInteractionProposalPayloadTitleStorageSlotRvaV1",
            "kCharacterInteractionProposalPayloadGrantTitlesOfferVtableRvaV1",
            "proof_epoch",
            "date_raw",
            "selected_title_ids",
            "ReadCharacterInteractionProposalPayloadSourceV1",
        ),
        "header",
    )
    require_tokens(
        source,
        tuple(f'"{key}"' for key in EXPECTED_KEYS)
        + (
            "kContextSecondaryActorOffset = 0x2E0",
            "kContextSecondaryRecipientOffset = 0x2E4",
            "kContextSpecialDataOffset = 0x330",
            "kDefinitionSelectedOptionsCountOffset = 0x2554",
            "stored_id != full_id",
            "collector.frame.proof_epoch",
            "collector.frame.date_raw",
            "Failure::religious_option_deferred",
            "kCharacterInteractionProposalPayloadGrantTitlesOfferVtableRvaV1",
            "payload.fingerprint = Fingerprint(output)",
        ),
        "source",
    )
    require_tokens(
        test,
        (
            "TestAllSixTypedPayloads",
            "TestGenerationBearingIdentityIsMandatory",
            "TestProofAndDateCannotDrift",
            "TestReligiousEducationOptionRemainsDeferred",
            "TestGrantTitleCollectorAndGenerationGates",
            "TestMalformedOptionsAndExactBuildStayRed",
        ),
        "native test",
    )
    require_tokens(
        docs,
        (
            "static-ready, private and unwired",
            "0x2C3F000",
            "0x4112BA8",
            "proof epoch",
            "Faith conversion remains explicitly deferred",
        ),
        "documentation",
    )

    combined_code = header + "\n" + source
    forbidden = (
        "SubmitCharacterInteractionProposalOnceV1(",
        "submit_once(",
        "ConstructSendCharacterInteractionCommand",
        "execute_effect",
    )
    present = [token for token in forbidden if token in combined_code]
    require(not present, f"forbidden action tokens present: {present}")
    cmake_text = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in native_root.rglob("CMakeLists.txt")
    )
    bridge_text = (native_root / "src/bridge.cpp").read_text(
        encoding="utf-8", errors="replace"
    )
    require(PRIVATE_KEY not in cmake_text, "private extension entered shared CMake")
    require(PRIVATE_KEY not in bridge_text, "private extension entered bridge.cpp")

    if args.exe is not None:
        executable = args.exe.resolve()
        require(executable.is_file(), f"missing executable: {executable}")
        require(executable.stat().st_size == EXE_SIZE, "frozen EXE size mismatch")
        require(digest(executable) == EXE_SHA256, "frozen EXE hash mismatch")
        image = PortableExecutable(executable.read_bytes())
        for anchor in abi["exact_build"]["code_anchors"]:
            span = image.read_rva(int(anchor["rva"], 16), anchor["size"])
            require(
                hashlib.sha256(span).hexdigest().upper() == anchor["sha256"],
                f"code anchor drifted: {anchor['name']}",
            )
        game_root = executable.parent.parent
        for row in abi["stock_sources"]:
            stock = game_root / Path(row["relative_path"])
            require(stock.is_file(), f"missing stock source: {stock}")
            require(stock.stat().st_size == row["size"], f"stock size drifted: {stock}")
            require(digest(stock) == row["sha256"], f"stock hash drifted: {stock}")

    print("character_interaction_proposal_payload_source_extension_v1 contract: GREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
