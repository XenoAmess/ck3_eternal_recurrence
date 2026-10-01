#!/usr/bin/env python3
"""Verify the actual member collector ABI against the pinned PE; file-only."""
from __future__ import annotations
import importlib.util
from pathlib import Path

# Reuse the scoped PE extraction/semantic-instruction verifier. This module's
# private instance binds only this member provider; it does not change files.
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("organization_member_verifier", HERE / "religion_rite_governance12002_organization.py")
assert spec is not None and spec.loader is not None
verifier = importlib.util.module_from_spec(spec); spec.loader.exec_module(verifier)
verifier.HEADER = HERE.parent / "ck3_autonomous_player/native_bridge/include/xar_bridge/religion_rite_governance12002_organization_members.hpp"
verifier.MANIFEST = HERE / "religion_rite_governance12002_organization_members_abi.json"
verifier.CONSTANTS = {
    "kFaithCharacterCollectorRva": 0x1C610E0, "kRiteCountyCollectorRva": 0x1D2B6F0,
    "kTitleStorageSlotRva": 0x5D1DAF8, "kAlivePoolOffset": 0x2EE60, "kAlivePoolSizeOffset": 0x2EE6C,
    "kReligionCountyPoolOffset": 0x200, "kReligionCountyPoolSizeOffset": 0x20C,
    "kTitleIdentityOffset": 0x10, "kTitleTemplateOffset": 0x48, "kTitleTemplateRankOffset": 0x64,
    "kCharacterScope": 0x04, "kTitleScope": 0x05, "kFaithScope": 0x0D, "kRiteScope": 0x2A,
}
verifier.SPANS = [
    ("Faith.alive_character_collector.complete", 0x1C610E0, 0x1C61225, "complete collector; chained unwind spans"),
    ("Rite.county_title_collector.complete", 0x1D2B6F0, 0x1D2B92D, "complete collector; chained unwind spans"),
    ("scope_array.append.complete", 0x880230, 0x880335, "complete append plus growth branch"),
    ("county.script_list.caller", 0x1D40DFB, 0x1D40E27, "caller arguments and collector edge"),
    ("county.collector.dispatcher", 0x1D223B0, 0x1D2240A, "complete collector dispatcher"),
]
verifier.SITES = [
    ("faith_input_kind", 0x1C610EE, "cmp word ptr [rax], 0xd", []),
    ("faith_storage_slot", 0x1C61100, None, [0x5D1E300]),
    ("game_state_slot", 0x1C6113E, None, [0x5C68C50]),
    ("native_alive_source_pointer", 0x1C6114C, "mov rbx, qword ptr [rcx + 0x2ee60]", []),
    ("native_alive_source_size", 0x1C61153, "movsxd rax, dword ptr [rcx + 0x2ee6c]", []),
    ("character_rite_full_id", 0x1C61188, "mov r8d, dword ptr [rdx + 0xb4]", []),
    ("faith_full_identity_filter", 0x1C611BC, "cmp dword ptr [rcx + 0x4b8], eax", []),
    ("alive_filter", 0x1C611C4, "cmp qword ptr [rdx + 0x1d0], 0", []),
    ("character_output_full_id", 0x1C611D6, "mov eax, dword ptr [rdx + 0x18]", []),
    ("character_output_kind", 0x1C611E6, "mov dword ptr [rsp + 0x20], 4", []),
    ("faith_append", 0x1C611EE, None, [0x880230]),
    ("rite_input_kind", 0x1D2B6FF, "cmp word ptr [rax], 0x2a", []),
    ("rite_to_faith_full_id", 0x1D2B75B, "mov r8d, dword ptr [rsi + 0x4b8]", []),
    ("faith_to_religion_full_id", 0x1D2B79B, "mov r8d, dword ptr [rax + 0x8c]", []),
    ("religion_county_source", 0x1D2B7CF, "mov rbx, qword ptr [rax + 0x200]", []),
    ("religion_county_source_size", 0x1D2B7D6, "movsxd rax, dword ptr [rax + 0x20c]", []),
    ("title_storage_slot", 0x1D2B7EA, None, [0x5D1DAF8]),
    ("county_exact_rite_filter", 0x1D2B80A, "cmp dword ptr [rcx + 0x384], eax", []),
    ("county_title_full_ref", 0x1D2B81B, "mov edx, dword ptr [rcx + 0x18]", []),
    ("title_full_generation_identity", 0x1D2B83C, "cmp dword ptr [rcx + 0x10], edx", []),
    ("title_definition_pointer", 0x1D2B844, "mov rax, qword ptr [rcx + 0x48]", []),
    ("county_rank", 0x1D2B848, "cmp dword ptr [rax + 0x64], 2", []),
    ("parent_title_full_ref", 0x1D2B850, "mov eax, dword ptr [rcx + 0x108]", []),
    ("county_output_full_id", 0x1D2B8A2, "mov r10d, dword ptr [rcx + 0x10]", []),
    ("county_output_kind", 0x1D2B8B4, "mov dword ptr [rsp + 0x20], 5", []),
    ("county_native_dedup", 0x1D2B8D2, "cmp qword ptr [rcx + 8], r10", []),
    ("county_append", 0x1D2B8F5, None, [0x880230]),
    ("native_array_size", 0x880244, "movsxd rax, dword ptr [rcx + 0xc]", []),
    ("native_array_capacity", 0x88024B, "mov ecx, dword ptr [rcx + 8]", []),
    ("native_growth_only_if_full", 0x880253, "jne 0x8802fb", []),
    ("native_append_caller_buffer", 0x880307, "movups xmmword ptr [rax + rcx*8], xmm0", []),
    ("native_append_increment_size", 0x88030B, "inc dword ptr [rbx + 0xc]", []),
    ("collector_dispatch_to_native", 0x1D223D1, None, [0x1D2B6F0]),
]

base_extract = verifier.extract
def extract(exe: Path) -> tuple[dict, str]:
    result, dump = base_extract(exe)
    result["schema"] = "ck3_12002_rite_organization_members_research_v1"
    result["production_scope"] = "native_faith_members_exact_rite_projection_and_native_rite_counties"
    result["unresolved"] = ["Rite count refresh producer timing", "actual paused member readback",
                            "central governance/MCP query integration", "native governance AI and final action gates"]
    return result, dump
verifier.extract = extract

if __name__ == "__main__": raise SystemExit(verifier.main())
