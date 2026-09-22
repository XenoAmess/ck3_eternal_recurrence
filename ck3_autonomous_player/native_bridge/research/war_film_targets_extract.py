"""Extract CK3 1.19.0.6 coordinator countdown branches; never attach to CK3."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import struct
import sys

import capstone
import pefile

EXE_SHA256 = "2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86"
SPANS = {
    "constructor": (0x1852400, 0x185276E),
    "update": (0x18550D0, 0x18554EF),
    "lopsided": (0x185A41B, 0x185A53F),
    "refresh_request": (0x1854D30, 0x1854E6E),
    "participant_probe": (0x1854E70, 0x1854F57),
    "target_commit": (0x185A780, 0x185AA3E),
    "direct_dispatch": (0x18876D0, 0x188817E),
}
REGISTRATIONS = {
    "UPDATE_WAR_STANCE_TICK": (0x18A9620, 0x18A9877, 0x4194DD0, 0x570DF44, "30"),
    "UPDATE_SPLIT_MERGE_TICK": (0x18A9960, 0x18A9BB7, 0x4194DB8, 0x570DF60, "14"),
    "UPDATE_TARGETS_TICK": (0x18A9CA0, 0x18A9EF7, 0x4194DA0, 0x570DF40, "7"),
    "UPDATE_TARGETS_TICK_LOPSIDED": (0x18A9FE0, 0x18AA237, 0x4194D80, 0x570DF64, "14"),
    "LOPSIDED_WAR_RATIO_THRESHOLD": (0x18AF5F0, 0x18AF675, 0x4196240, 0x570DF20, "0.33"),
}
ANCHORS = {
    0x1855108: ("dec", "r13d"),
    0x1855115: ("dec", "eax"),
    0x185513A: ("dec", "dword ptr [rcx + 0x9c]"),
    0x1855147: ("jg", "0x185514e"),
    0x18552C6: ("call", "0x185a270"),
    0x18552D1: ("mov", "dword ptr [rbx + 0x94], eax"),
    0x18552E1: ("call", "0x1858200"),
    0x18552EC: ("mov", "dword ptr [rbx + 0x98], eax"),
    0x1855305: ("call", "0x185a780"),
    0x185531E: ("mov", "dword ptr [rbx + 0x9c], eax"),
    0x185A521: ("setl", "al"),
    0x185A524: ("mov", "byte ptr [rsi + 0xa0], al"),
    0x1854E54: ("or", "word ptr [rbx + 0x68], 2"),
    0x18878F1: ("call", "0x18550d0"),
}


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def extract(exe: Path, out: Path) -> dict:
    raw = exe.read_bytes()
    if digest(raw) != EXE_SHA256:
        raise ValueError("EXE does not match CK3 1.19.0.6 research baseline")
    defines = exe.parent.parent / "game/common/defines/ai/00_ai.txt"
    source = defines.read_bytes()
    text = source.decode("utf-8-sig")
    pe = pefile.PE(data=raw, fast_load=True)
    cs = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    cs.detail = True
    exception = pe.OPTIONAL_HEADER.DATA_DIRECTORY[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_EXCEPTION"]]
    pdata = list(struct.iter_unpack("<III", pe.get_data(exception.VirtualAddress, exception.Size)))
    out.mkdir(parents=True, exist_ok=False)
    result = {
        "schema": "xar.war-film-target-countdowns.v1", "exe_sha256": EXE_SHA256,
        "exe_bytes": len(raw), "exe_path": str(exe.resolve()),
        "interpreter": sys.executable,
        "dependencies": {name: importlib.metadata.version(name) for name in ["capstone", "pefile"]},
        "defines_sha256": digest(source), "spans": {}, "registrations": {}, "anchors": {},
        "proof": "Pinned executable bytes, disassembly and define registration; semantic interpretation remains in the companion document.",
        "live_execution": False,
    }
    decoded = {}
    for name, (a, b) in SPANS.items():
        code = pe.get_data(a, b-a)
        instructions = list(cs.disasm(code, a))
        decoded.update({i.address: i for i in instructions})
        lines = []
        for i in instructions:
            refs = [i.address+i.size+o.mem.disp for o in i.operands
                    if o.type == capstone.x86.X86_OP_MEM and o.mem.base == capstone.x86.X86_REG_RIP]
            lines.append(f"{i.address:08X} {i.bytes.hex()} {i.mnemonic} {i.op_str}"
                         + (" ; RIP " + ",".join(hex(r) for r in refs) if refs else ""))
        body = ("\n".join(lines)+"\n").encode()
        (out/f"{name}.asm.txt").write_bytes(body)
        result["spans"][name] = {
            "begin": hex(a), "end_exclusive": hex(b), "bytes_sha256": digest(code),
            "disassembly_sha256": digest(body), "instruction_count": len(instructions),
            "pdata_fragments": [[hex(x),hex(y),hex(z)] for x,y,z in pdata if a <= x < b],
        }
    for address, expected in ANCHORS.items():
        i = decoded[address]
        if (i.mnemonic, i.op_str) != expected:
            raise ValueError(f"instruction changed at {address:#x}")
        result["anchors"][hex(address)] = {"bytes": i.bytes.hex(), "mnemonic": i.mnemonic, "operands": i.op_str}
    for name, (a,b,string_rva,slot,value) in REGISTRATIONS.items():
        if pe.get_data(string_rva,len(name)+1) != name.encode()+b"\0":
            raise ValueError(f"registration name mismatch: {name}")
        code = pe.get_data(a,b-a)
        refs = {}
        for i in cs.disasm(code,a):
            for o in i.operands:
                if o.type == capstone.x86.X86_OP_MEM and o.mem.base == capstone.x86.X86_REG_RIP:
                    rva = i.address+i.size+o.mem.disp
                    if rva in {slot,string_rva}: refs[hex(i.address)] = hex(rva)
        if not {hex(slot),hex(string_rva)}.issubset(refs.values()):
            raise ValueError(f"registration does not bind name and slot: {name}")
        match = re.search(r"^\s*"+re.escape(name)+r"\s*=\s*([0-9.]+)\s*(?:#.*)?$",text,re.M)
        if not match or match[1] != value:
            raise ValueError(f"vanilla define differs: {name}")
        result["registrations"][name] = {"begin":hex(a),"end_exclusive":hex(b),"slot":hex(slot),
            "string_rva":hex(string_rva),"value":value,"bytes_sha256":digest(code),"rip_references":refs}
    (out/"summary.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8",newline="\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = extract(args.exe,args.out)
    print(json.dumps({"result":"PASS","anchors":len(result["anchors"]),
                      "registrations":len(result["registrations"]),"summary":str(args.out/"summary.json"),"live_execution":False}))


if __name__ == "__main__":
    main()
