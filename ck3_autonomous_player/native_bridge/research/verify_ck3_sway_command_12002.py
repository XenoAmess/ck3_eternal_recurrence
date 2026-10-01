"""Verify the frozen 1.20 Sway command ABI; reads files only."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_REG_RIP
from scan_anchors import PeImage


def require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def verify_sway_command(exe: Path) -> dict:
    native = Path(__file__).resolve().parents[1]
    fixture = native / "research/ck3_sway_command_12002_abi.json"
    manifest = json.loads(fixture.read_text(encoding="utf-8-sig"))
    data = exe.read_bytes()
    require(len(data) == manifest["build"]["size"], "frozen EXE size changed")
    require(hashlib.sha256(data).hexdigest().upper() == manifest["build"]["sha256"],
            "frozen EXE SHA changed")
    pe = PeImage(data)
    def span(rva: str, size: int) -> bytes:
        start = pe.rva_to_offset(int(rva, 0))
        return data[start:start + size]
    for anchor in manifest["anchors"]:
        expected = bytes.fromhex(anchor["bytes"])
        require(span(anchor["rva"], anchor["size"]) == expected and data.count(expected) == 1,
                "mapped function mismatch: " + anchor["name"])
        require(hashlib.sha256(expected).hexdigest() == anchor["sha256"], "anchor hash changed")
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    md.detail = True
    decoded = {}
    for row in manifest["semantics"]:
        instruction = next(md.disasm(span(row["rva"], 15), int(row["rva"], 0)))
        actual = {"bytes": instruction.bytes.hex(), "instruction": instruction.mnemonic + " " + instruction.op_str,
                  "rip_targets": [hex(instruction.address + instruction.size + item.mem.disp)
                                  for item in instruction.operands
                                  if item.type == X86_OP_MEM and item.mem.base == X86_REG_RIP],
                  "direct_targets": [hex(item.imm) for item in instruction.operands
                                     if item.type == X86_OP_IMM and instruction.mnemonic in ("call", "jmp")]}
        require(all(actual[key] == row[key] for key in actual), "instruction mismatch: " + row["name"])
        decoded[row["name"]] = row
    image_base = 0x140000000
    for table in manifest["vtables"]:
        actual = struct.unpack("<" + "Q" * len(table["function_rvas"]),
                               span(table["rva"], len(table["function_rvas"]) * 8))
        require([hex(value - image_base) for value in actual] == table["function_rvas"],
                "vtable mismatch: " + table["name"])
    for rtti in manifest["rtti"]:
        expected = bytes.fromhex(rtti["bytes"])
        require(span(rtti["rva"], len(expected)) == expected, "definition RTTI/COL changed")
    stock = exe.parent.parent / manifest["stock"]["relative_path"]
    stock_bytes = stock.read_bytes()
    require(hashlib.sha256(stock_bytes).hexdigest() == manifest["stock"]["file_sha256"], "stock file changed")
    stock_text = stock.read_text(encoding="utf-8-sig")
    begin = stock_text.index("sway_interaction = {")
    end = stock_text.index("\n}", begin) + 2
    require(hashlib.sha256(stock_text[begin:end].encode()).hexdigest() ==
            manifest["stock"]["sway_block_sha256"], "stock Sway native tree changed")

    # Compare actual production binding constants to native decoded operands;
    # this is not a source-token substitute for a native reader fixture.
    header_text = "\n".join((native / "include/xar_bridge" / name).read_text(encoding="utf-8-sig")
                             for name in ("ck3_12002_sway_command.hpp", "ck3_12002_context.hpp",
                                          "ck3_12002_diplomacy.hpp", "ck3_12002_commands.hpp"))
    constants = {
        "kSwayDefinitionPrimaryVtableRva": "definition_primary",
        "kSwayDefinitionSecondaryVtableRva": "definition_secondary",
        "kSwayDefinitionSecondaryOffset": "definition_secondary_offset",
        "kSwayDatabaseRowsOffset": "database_rows", "kSwayDatabaseCountOffset": "database_count",
        "kSwayShownRva": "shown", "kSwayValidityRva": "validity",
        "kConstructInteractionContextRva": "construct",
        "kMarriageValidateInteractionContextRva": "can_send",
        "kMarriageInteractionDatabaseSlotRva": "database_slot",
        "kMarriageConstructSendInteractionCommandRva": "send_constructor",
        "kCommandManagerRva": "manager", "kQueueOwnedCommandRva": "owned_queue"}
    for name, binding in constants.items():
        found = re.search(r"\b" + name + r"\s*=\s*(0x[0-9A-Fa-f]+)\s*;", header_text)
        require(found is not None and int(found.group(1), 0) == int(manifest["bindings"][binding], 0),
                "production constant differs from reviewed mapping: " + name)
    for name, binding in (("database_singleton_slot", "database_slot"),
                          ("definition_primary_vtable", "definition_primary"),
                          ("definition_secondary_vtable", "definition_secondary")):
        require([int(item, 0) for item in decoded[name]["rip_targets"]] ==
                [int(manifest["bindings"][binding], 0)], "native RIP producer differs: " + binding)
    for name, binding in (("native_ui_two_role_context", "construct"), ("native_ui_shown", "shown"),
                          ("can_send_native_validity", "validity")):
        require([int(item, 0) for item in decoded[name]["direct_targets"]] ==
                [int(manifest["bindings"][binding], 0)], "native call producer differs: " + binding)
    require(int(manifest["vtables"][2]["function_rvas"][8], 0) == 0x86D760,
            "CSendCharacterInteractionCommand clone entry changed")
    return {"status": "GREEN", "readiness": "static-ready ABI; provider fixture separately required",
            "game_version": "1.20.0.2", "executable_sha256": manifest["build"]["sha256"],
            "abi_sha256": hashlib.sha256(fixture.read_bytes()).hexdigest(),
            "unique_function_count": len(manifest["anchors"]), "instruction_count": len(decoded),
            "vtable_count": len(manifest["vtables"]), "production_constant_count": len(constants),
            "local_ck3_touched": False, "live_verified": False, "known_gaps": manifest["known_gaps"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify_sway_command(args.exe.resolve())
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"PASS Sway 1.20 ABI: {result['unique_function_count']} unique functions, "
          f"{result['instruction_count']} instructions, {result['vtable_count']} vtables, "
          f"{result['production_constant_count']} production constants; offline only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
