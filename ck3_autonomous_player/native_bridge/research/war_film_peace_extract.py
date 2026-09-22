"""Extract bounded exact-build PE functions and validated direct/RIP xrefs offline."""
from __future__ import annotations

import argparse
from bisect import bisect_right
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import struct
import sys

import capstone
from capstone.x86_const import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP
import pefile

EXPECTED_SHA = "2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86"


def number(value):
    return int(value, 0)


def window(value):
    start, count = (int(part, 0) for part in value.split(":"))
    if start < 0 or not 0 < count <= 4096:
        raise argparse.ArgumentTypeError("window requires RVA:COUNT, 1..4096 bytes")
    return start, count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rva", type=number, action="append", default=[])
    parser.add_argument("--call-target", type=number, action="append", default=[])
    parser.add_argument("--literal", action="append", default=[])
    parser.add_argument("--pointer", type=number, action="append", default=[])
    parser.add_argument("--window", type=window, action="append", default=[],
                        help="Explicit byte window, NOT a claimed function boundary; useful for a directly called leaf without pdata")
    parser.add_argument("--data-window", type=window, action="append", default=[])
    args = parser.parse_args()
    raw = args.exe.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_SHA:
        raise ValueError("Exact EXE SHA mismatch")
    pe = pefile.PE(data=raw, fast_load=True)
    pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_EXCEPTION"]])
    base = pe.OPTIONAL_HEADER.ImageBase
    functions = sorted((entry.struct.BeginAddress, entry.struct.EndAddress)
                       for entry in pe.DIRECTORY_ENTRY_EXCEPTION)
    begins = [start for start, _ in functions]
    decoder = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    decoder.detail = True
    cache = {}

    def containing(rva):
        index = bisect_right(begins, rva) - 1
        if index >= 0 and functions[index][0] <= rva < functions[index][1]:
            return functions[index]
        return None

    def decode_function(rva):
        bounds = containing(rva)
        if not bounds:
            raise ValueError(f"No .pdata function for {rva:#x}; do not guess an entry")
        start, end = bounds
        if start not in cache:
            data = pe.get_data(start, end - start)
            instructions = []
            by_address = {}
            for insn in decoder.disasm(data, base + start):
                item = {"rva": hex(insn.address - base), "bytes": insn.bytes.hex(),
                        "mnemonic": insn.mnemonic, "operands": insn.op_str}
                immediates = [op.imm - base for op in insn.operands if op.type == X86_OP_IMM and base <= op.imm < base + pe.OPTIONAL_HEADER.SizeOfImage]
                rip_refs = [insn.address + insn.size + op.mem.disp - base for op in insn.operands if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP]
                if immediates:
                    item["image_immediates"] = [hex(x) for x in immediates]
                if rip_refs:
                    item["rip_targets"] = [hex(x) for x in rip_refs]
                instructions.append(item)
                by_address[insn.address - base] = item
            cache[start] = {"start_rva": hex(start), "end_rva": hex(end), "byte_count": len(data),
                            "sha256": hashlib.sha256(data).hexdigest(), "instructions": instructions,
                            "decoded_end_rva": hex(int(instructions[-1]["rva"], 16) + len(bytes.fromhex(instructions[-1]["bytes"]))) if instructions else None,
                            "by_address": by_address}
        return cache[start]

    literals = []
    literal_targets = set()
    for value in args.literal:
        needle = value.encode("ascii") + b"\0"
        for match in re.finditer(re.escape(needle), raw):
            rva = pe.get_rva_from_offset(match.start())
            literal_targets.add(rva)
            literals.append({"text": value, "rva": hex(rva), "file_offset": hex(match.start())})
    call_targets = set(args.call_target)
    direct = []
    rip_candidates = []
    requested_functions = set(args.rva)
    for section in pe.sections:
        if not section.Characteristics & 0x20000000:
            continue
        data = section.get_data()
        va = section.VirtualAddress
        for match in re.finditer(b"[\xe8\xe9]", data):
            index = match.start()
            if index + 5 > len(data):
                continue
            target = va + index + 5 + struct.unpack_from("<i", data, index + 1)[0]
            if target not in call_targets:
                continue
            at = va + index
            bounds = containing(at)
            if not bounds:
                direct.append({"at_rva": hex(at), "target_rva": hex(target), "verified_instruction_boundary": False,
                               "reason": "no pdata owner"})
                continue
            owner = decode_function(at)
            insn = owner["by_address"].get(at)
            valid = bool(insn and insn["mnemonic"] in {"call", "jmp"} and hex(target) in insn.get("image_immediates", []))
            direct.append({"at_rva": hex(at), "target_rva": hex(target), "owner_start_rva": owner["start_rva"],
                           "verified_instruction_boundary": valid})
            if valid:
                requested_functions.add(bounds[0])
        if literal_targets:
            pattern = rb"[\x48-\x4f][\x8b\x8d\x89][\x05\x0d\x15\x1d\x25\x2d\x35\x3d]"
            for match in re.finditer(pattern, data):
                index = match.start()
                if index + 7 > len(data):
                    continue
                target = va + index + 7 + struct.unpack_from("<i", data, index + 3)[0]
                if target not in literal_targets:
                    continue
                at = va + index
                bounds = containing(at)
                if not bounds:
                    continue
                owner = decode_function(at)
                insn = owner["by_address"].get(at)
                valid = bool(insn and hex(target) in insn.get("rip_targets", []))
                rip_candidates.append({"at_rva": hex(at), "target_rva": hex(target),
                                       "owner_start_rva": owner["start_rva"], "verified_instruction_boundary": valid})
                if valid:
                    requested_functions.add(bounds[0])
    pointers = []
    for target in args.pointer:
        needle = struct.pack("<Q", base + target)
        for match in re.finditer(re.escape(needle), raw):
            at = pe.get_rva_from_offset(match.start())
            pointers.append({"storage_rva": hex(at), "target_rva": hex(target), "kind": "pointer-locator-only"})
    extracts = []
    for rva in sorted(requested_functions):
        function = decode_function(rva)
        if any(item["start_rva"] == function["start_rva"] for item in extracts):
            continue
        extracts.append({key: value for key, value in function.items() if key != "by_address"})
    windows = []
    for start, count in args.window:
        data = pe.get_data(start, count)
        if len(data) != count:
            raise ValueError("Explicit code window is not fully file-backed")
        windows.append({"start_rva": hex(start), "byte_count": count,
                        "boundary_authority": "author-requested-window-not-function",
                        "bytes": data.hex(), "sha256": hashlib.sha256(data).hexdigest(),
                        "instructions": [{"rva": hex(i.address - base), "bytes": i.bytes.hex(),
                                          "mnemonic": i.mnemonic, "operands": i.op_str}
                                         for i in decoder.disasm(data, base + start)]})
    data_windows = []
    for start, count in args.data_window:
        data = pe.get_data(start, count)
        if len(data) != count:
            raise ValueError("Explicit data window is not fully file-backed")
        data_windows.append({"start_rva": hex(start), "byte_count": count,
                             "bytes": data.hex(), "sha256": hashlib.sha256(data).hexdigest()})
    args.output.mkdir(parents=True, exist_ok=False)
    result = {"scope": "exact-build-offline-extraction", "live_execution": False, "semantics_automatically_verified": False,
              "exe": {"path": str(args.exe.resolve()), "bytes": len(raw), "sha256": digest, "image_base": hex(base)},
              "extractor": {"path": str(Path(__file__).resolve()), "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
              "python": sys.executable, "versions": {name: importlib.metadata.version(name) for name in ["capstone", "pefile"]},
              "args": {"rva": [hex(x) for x in args.rva], "call_target": [hex(x) for x in args.call_target], "literal": args.literal, "pointer": [hex(x) for x in args.pointer],
                       "window": [[hex(a), n] for a, n in args.window], "data_window": [[hex(a), n] for a, n in args.data_window]},
              "literals": literals, "direct_xrefs": direct, "rip_xrefs": rip_candidates, "pointer_locators": pointers, "functions": extracts,
              "explicit_code_windows": windows, "data_windows": data_windows}
    with (args.output / "extract.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    for function in extracts:
        with (args.output / (function["start_rva"] + ".asm")).open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(f"; .pdata {function['start_rva']}..{function['end_rva']} SHA256 {function['sha256']}\n")
            for instruction in function["instructions"]:
                stream.write(f"{instruction['rva']:>11}  {instruction['bytes']:<32} {instruction['mnemonic']:<8} {instruction['operands']}\n")
    print(json.dumps({"output": str(args.output), "functions": len(extracts), "literals": literals,
                      "direct_xrefs": direct, "rip_xrefs": rip_candidates, "pointer_locators": pointers}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
