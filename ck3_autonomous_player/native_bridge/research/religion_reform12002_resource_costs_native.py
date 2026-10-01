#!/usr/bin/env python3
"""File-only proof of Rite/Faith command base-resource fees on CK3 1.20.0.2."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP
from scan_anchors import PeImage

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "religion_reform12002_resource_costs_abi.json"
EXACT = "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"
# The first Execute has three chained unwind regions: retain their complete
# contiguous body. CCost's final forty bytes are its jump table, not code.
SPANS = [
    ("create_command_secondary_execute", 0x29A2DE0, 0x29A2F5A),
    ("edit_command_secondary_execute", 0x29A25B0, 0x29A263B),
    ("new_faith_or_reform_wrapper", 0x29A7950, 0x29A7D1E),
    ("new_rite_wrapper", 0x29A7D20, 0x29A8033),
    ("new_faith_or_reform_budget", 0x29D1350, 0x29D1819),
    ("new_rite_create_and_change", 0x29A3210, 0x29A3363),
    ("new_rite_budget", 0x29C8390, 0x29C8789),
    ("edit_owned_rite_budget", 0x29A2BF0, 0x29A2DD1),
    ("faith_internal_rite_allocation_no_second_base_debit", 0x29C81A0, 0x29C8390),
    ("tracked_resource_delta", 0x28D7000, 0x28D7117),
    ("piety_delta_leaf", 0x28CDCF0, 0x28CDD20),
    ("new_rite_affordability_vector", 0x29C98A1, 0x29C999C),
    ("new_faith_affordability_vector", 0x29D1970, 0x29D1A6F),
    ("edit_rite_affordability_vector", 0x29C8ECE, 0x29C8F91),
    ("CCost_CanAfford_code", 0x310E710, 0x310EDAC),
    ("on_action_created_updated_edited_name_registration", 0x25B032E, 0x25B03DC),
]
CALLS = {
    0x29A2EB3: 0x2BDCA90, 0x29A2EC9: 0x29A7950,
    0x29A2ED0: 0x29A7D20, 0x29A25F9: 0x29A2BF0,
    0x29A79DE: 0x29D1350, 0x29A7D90: 0x29A3210,
    0x29A3239: 0x29C8390, 0x29D1581: 0x29C81A0,
    0x29D1625: 0x2C64200, 0x29D1671: 0x2C62CE0,
    0x29D1725: 0x28D7000, 0x29C84C2: 0x2C64200,
    0x29C850A: 0x2C62CE0, 0x29C8541: 0x28D7000,
    0x29A2CE2: 0x2C64730, 0x29A2D32: 0x2C62CE0,
    0x29A2D71: 0x28D7000,
    0x29C9997: 0x310E710, 0x29D1A6A: 0x310E710,
    0x29C8F8C: 0x310E710,
    0x29A7C67: 0x37CCC50, 0x29A7F77: 0x37CCC50,
}
SITES = {
    "create_secondary_vtable_installed": 0x14F5704,
    "create_secondary_price_draft": 0x29A2EA8,
    "create_secondary_to_primary_adjustment": 0x29A2EAF,
    "faith_negative_base_fee": 0x29D16F4,
    "faith_actor_extension": 0x29D16F7,
    "faith_piety_resource_object": 0x29D1703,
    "faith_piety_delta_callback": 0x29D171B,
    "rite_negative_base_fee": 0x29C8513,
    "rite_actor_extension": 0x29C8516,
    "rite_piety_resource_object": 0x29C8522,
    "rite_piety_delta_callback": 0x29C8537,
    "edit_negative_base_fee": 0x29A2D3F,
    "edit_actor_extension": 0x29A2D42,
    "edit_piety_resource_object": 0x29A2D4E,
    "edit_piety_delta_callback": 0x29A2D67,
    "generic_delta_stack_argument": 0x28D7067,
    "generic_delta_callback_call": 0x28D706F,
    "piety_nonpositive_branch": 0x28CDCF3,
    "piety_current_balance_write": 0x28CDD1B,
    "cost_resource_count": 0x310ED39,
    "cost_slot_indexed_read": 0x310ED09,
    "piety_current_balance_read": 0x310E873,
    "faith_created_on_action_pointer": 0x29A7C26,
    "rite_created_on_action_pointer": 0x29A7F36,
    "faith_created_name": 0x25B033F,
    "rite_created_name": 0x25B035C,
    "rite_updated_name": 0x25B03B3,
    "rite_edited_name": 0x25B03D0,
}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args()
    raw = args.exe.read_bytes()
    sha = hashlib.sha256(raw).hexdigest().upper()
    assert sha == EXACT and len(raw) == 101039736
    pe = PeImage(raw)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64); decoder.detail = True
    def read(rva: int, size: int) -> bytes:
        offset = pe.rva_to_offset(rva)
        return raw[offset:offset + size]
    def instruction(rva: int):
        return next(decoder.disasm(read(rva, 15), rva))
    def evidence(name: str, rva: int):
        item = instruction(rva)
        return {"name": name, "rva": hex(rva), "bytes": item.bytes.hex(" "),
                "instruction": item.mnemonic + " " + item.op_str,
                "direct_targets": [hex(o.imm) for o in item.operands if
                                   o.type == X86_OP_IMM and item.mnemonic in ("call", "jmp")],
                "rip_targets": [hex(item.address + item.size + o.mem.disp) for o in item.operands
                                if o.type == X86_OP_MEM and o.mem.base == X86_REG_RIP]}
    spans = []; dump = []; instructions = []
    for name, start, end in SPANS:
        code = read(start, end - start)
        spans.append({"name": name, "start_rva": hex(start), "end_exclusive_rva": hex(end),
                      "sha256": hashlib.sha256(code).hexdigest(), "bytes": code.hex(" ")})
        decoded = list(decoder.disasm(code, start))
        assert decoded and decoded[-1].address + decoded[-1].size == end, name
        dump.append(f"\n{name} [{start:#x},{end:#x})")
        dump.extend(f"{i.address:08X} {i.bytes.hex(' '):32s} {i.mnemonic} {i.op_str}" for i in decoded)
    for site, target in CALLS.items():
        item = evidence("direct_callee", site)
        assert item["direct_targets"] == [hex(target)], item
        instructions.append(item)
    instructions.extend(evidence(name, site) for name, site in SITES.items())
    vtables = []
    for name, slot, target in [("create_execute_secondary", 0x4770410, 0x29A2DE0),
                              ("edit_execute_secondary", 0x4770528, 0x29A25B0),
                              ("create_validator_primary_reused", 0x4770580, 0x29A2F60),
                              ("create_clone_primary_reused", 0x4770590, 0x29A7030)]:
        pointer = struct.unpack("<Q", read(slot, 8))[0]
        assert pointer - pe.image_base == target, name
        vtables.append({"name": name, "slot_rva": hex(slot), "target_rva": hex(target),
                        "bytes": read(slot, 8).hex(" ")})
    vectors = []
    for name, zeros, field, call in [
        ("new_rite", [0x29C98A4, 0x29C98AB, 0x29C98B2, 0x29C98B9, 0x29C98C0], 0x29C9983, 0x29C9997),
        ("new_faith_or_reform", [0x29D1973, 0x29D197A, 0x29D1981, 0x29D1988, 0x29D198F], 0x29D1A56, 0x29D1A6A),
        ("edit_owned_current_rite", [0x29C8F4E, 0x29C8F55, 0x29C8F5C, 0x29C8F63, 0x29C8F6A], 0x29C8F78, 0x29C8F8C),
    ]:
        offsets = [instruction(rva).operands[0].mem.disp for rva in zeros]
        assert offsets == list(range(offsets[0], offsets[0] + 0x50, 0x10))
        assert all(instruction(rva).mnemonic == "movups" for rva in zeros)
        assert instruction(field).operands[0].mem.disp - offsets[0] == 0x10
        vectors.append({"branch": name, "zero_entire_CCost_bytes": 0x50,
                        "zero_write_rvas": [hex(rva) for rva in zeros],
                        "only_nonzero_slot": 2, "piety_write_rva": hex(field),
                        "affordability_call_rva": hex(call)})
    table = struct.unpack("<10I", read(0x310EDAC, 40))
    # Stable public names are restricted to exact dispatch entries proved here.
    assert table[:3] == (0x310E7B7, 0x310E807, 0x310E851)
    slots = [{"index": index, "offset": hex(index * 8), "dispatch_rva": hex(target),
              "name": {0: "gold", 1: "prestige", 2: "piety"}.get(index)}
             for index, target in enumerate(table)]
    source = HERE / "religion_reform12002_costs_abi.json"
    reused = json.loads(source.read_text(encoding="utf-8"))
    assert reused["executable_sha256"] == sha
    abi = {"schema": "xar.ck3_12002_rite_creation_base_resource_cost_abi.v1",
           "game_version": "1.20.0.2", "executable_sha256": sha,
           "executable_size": len(raw), "readiness": "static-confirmed",
           "local_ck3_touched": False, "live_verified": False,
           "native_spans": spans, "semantic_instructions": instructions,
           "vtable_slots": vtables, "affordability_vectors": vectors,
           "CCost_resource_dispatch": slots,
           "reused_piety_quote_manifest": {"path": source.name,
               "sha256": hashlib.sha256(source.read_bytes()).hexdigest()},
           "contract": {"scope": "native command draft base-fee quote",
               "raw_scale": 100000, "slots": 10, "piety_slot": 2,
               "non_piety_base_fee_slots_zero": True,
               "actual_negative_debit_changes_current_piety_only": True,
               "actual_debit_observed": False,
               "post_action_net_resource_change_observed": False},
           "unknown": ["post-action total net resource outcome and event choices",
                       "paused production quote and actual action outcome"]}
    if args.record:
        MANIFEST.write_text(json.dumps(abi, indent=2) + "\n", encoding="utf-8")
    else:
        assert abi == json.loads(MANIFEST.read_text(encoding="utf-8"))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    disassembly = "\n".join(dump) + "\n"
    (args.output_dir / "native-disassembly.txt").write_text(disassembly, encoding="utf-8")
    receipt = {"status": "GREEN", "readiness": "static-confirmed",
               "executable_sha256": sha, "local_ck3_touched": False, "live_verified": False,
               "native_spans": len(spans), "semantic_instructions": len(instructions),
               "vtable_slots": len(vtables), "affordability_vectors": len(vectors),
               "resource_dispatch_slots": len(slots),
               "abi_manifest": str(MANIFEST),
               "abi_manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
               "native_disassembly_sha256": hashlib.sha256(disassembly.encode()).hexdigest()}
    (args.output_dir / "native-result.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
