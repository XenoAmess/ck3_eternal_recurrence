"""Find offline migration candidates; a byte match is not a verified ABI."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from capstone import CS_ARCH_X86, CS_MODE_64, CS_GRP_CALL, CS_GRP_JUMP, Cs
from capstone.x86 import X86_OP_MEM, X86_REG_RIP

from scan_anchors import PeImage


def masked_pattern(code: bytes, rva: int, decoder: Cs) -> tuple[bytes, str]:
    mask = bytearray(b"\x01" * len(code))
    for instruction in decoder.disasm(code, rva):
        offset = instruction.address - rva
        if any(op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP
               for op in instruction.operands):
            for index in range(instruction.disp_size):
                mask[offset + instruction.disp_offset + index] = 0
        if instruction.group(CS_GRP_CALL) or instruction.group(CS_GRP_JUMP):
            for index in range(instruction.imm_size):
                mask[offset + instruction.imm_offset + index] = 0
    regex = b"".join(re.escape(bytes([value])) if keep else b"."
                     for value, keep in zip(code, mask))
    display = " ".join(f"{value:02X}" if keep else "??" for value, keep in zip(code, mask))
    return regex, display


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-exe", type=Path, required=True)
    parser.add_argument("--new-exe", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=Path(__file__).with_name("ck3_1_19_0_6_anchors.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    old_data, new_data = args.old_exe.read_bytes(), args.new_exe.read_bytes()
    old_pe, new_pe = PeImage(old_data), PeImage(new_data)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
    if hashlib.sha256(old_data).hexdigest().upper() != manifest["build"]["sha256"]:
        raise ValueError("Old executable does not match the source anchor manifest")
    anchors = list(manifest["signature_anchors"])
    # The owning-thread chain is recorded in main_thread_query_mailbox_v1_abi.json.
    for name, rva, size in (
        ("sdl_windows_pump", 0x3CE41E0, 0x30),
        ("sdl_pump_events", 0x3CD3600, 0x40),
        ("handle_pdx_events_wrapper", 0x3A2EC30, 0x40),
        ("handle_pdx_events_body", 0x3A2EE60, 0x40),
        ("main_thread_context_getter", 0x3B86430, 0x30),
        ("application_event_function", 0x3555190, 0x40),
    ):
        offset = old_pe.rva_to_offset(rva)
        anchors.append({"name": name, "rva": hex(rva), "pattern": old_data[offset:offset + size].hex(" ")})
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    # Restrict candidate search to file-backed code, not data containing bytes.
    code_sections = [(rva, offset, raw) for rva, _, offset, raw in new_pe.sections
                     if rva == 0x1000]
    if len(code_sections) != 1:
        raise ValueError("Expected one code section starting at RVA 0x1000")
    code_rva, code_offset, code_size = code_sections[0]
    code = new_data[code_offset:code_offset + code_size]
    rows = []
    for anchor in anchors:
        old_rva = int(anchor["rva"], 0)
        needle = bytes.fromhex(anchor["pattern"])
        offset = old_pe.rva_to_offset(old_rva)
        if old_data[offset:offset + len(needle)] != needle:
            raise ValueError(f"Stale source signature: {anchor['name']}")
        regex, display = masked_pattern(needle, old_rva, decoder)
        matches = [code_rva + match.start() for match in re.finditer(b"(?=" + regex + b")", code, re.DOTALL)]
        row = {"name": anchor["name"], "old_rva": hex(old_rva), "masked_pattern": display,
               "candidate_rvas": [hex(value) for value in matches],
               "status": "candidate-single-signature" if len(matches) == 1 else "unresolved",
               "abi_verified": False, "live_verified": False}
        if len(matches) == 1:
            new_rva = matches[0]
            offset = new_pe.rva_to_offset(new_rva)
            row["disassembly"] = [
                {"rva": hex(ins.address), "bytes": ins.bytes.hex(" "),
                 "instruction": f"{ins.mnemonic} {ins.op_str}",
                 "rip_targets": [hex(ins.address + ins.size + op.mem.disp)
                                 for op in ins.operands
                                 if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP]}
                for ins in decoder.disasm(new_data[offset:offset + 0x240], new_rva)]
        rows.append(row)
    result = {"old_sha256": hashlib.sha256(old_data).hexdigest().upper(),
              "new_sha256": hashlib.sha256(new_data).hexdigest().upper(),
              "method": "mask RIP-relative displacement and direct branch/call immediates; preserve object offsets",
              "warning": "Single signatures are candidates for semantic review, never automatic runtime bindings.",
              "anchors": rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"anchors": len(rows), "single_candidates": sum(len(r["candidate_rvas"]) == 1 for r in rows),
                      "unresolved": [r["name"] for r in rows if len(r["candidate_rvas"]) != 1]}))


if __name__ == "__main__":
    main()
