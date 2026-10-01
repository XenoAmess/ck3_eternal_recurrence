"""Bounded exact-build file-only native Sway cancellation exploration."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

SHA = "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--literal", action="append", default=[])
    parser.add_argument("--rva", type=lambda value: int(value, 0), action="append", default=[])
    parser.add_argument("--xref", type=lambda value: int(value, 0), action="append", default=[])
    parser.add_argument("--xref32", type=lambda value: int(value, 0), action="append", default=[])
    parser.add_argument("--descriptor", type=lambda value: int(value, 0), action="append", default=[])
    parser.add_argument("--region", nargs=2, type=lambda value: int(value, 0))
    parser.add_argument("--filter")
    parser.add_argument("--data", nargs=2, type=lambda value: int(value, 0), action="append", default=[])
    parser.add_argument("--token", type=lambda value: int(value, 0), action="append", default=[])
    parser.add_argument("--rtti")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = args.exe.read_bytes()
    if len(data) != 101039736 or hashlib.sha256(data).hexdigest().upper() != SHA:
        raise ValueError("Expected exact frozen CK3 1.20.0.2 executable")
    pe = pefile.PE(data=data, fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    sections = {section.Name.rstrip(b"\0"): section for section in pe.sections}
    pdata = sections[b".pdata"].get_data()
    functions = [struct.unpack_from("<III", pdata, i) for i in range(0, len(pdata) - 11, 12)]
    def containing(rva: int):
        hits = [first for first, last, _ in functions if first <= rva < last]
        return hex(hits[0]) if len(hits) == 1 else None
    text = sections[b".text"]
    text_data = text.get_data()
    rip = []
    for match in re.finditer(rb"(?=([\x40-\x4f][\x8d\x8b][\x05\x0d\x15\x1d\x25\x2d\x35\x3d]....))", text_data, re.DOTALL):
        source = text.VirtualAddress + match.start()
        payload = match.group(1)
        ins = next(md.disasm(payload, source), None)
        if ins and ins.size == 7 and "rip" in ins.op_str:
            rip.append((source + 7 + struct.unpack_from("<i", payload, 3)[0], source))
    def references(target: int):
        rows = [{"rva": hex(source), "function": containing(source), "kind": "RIP-relative"}
                for destination, source in rip if destination == target]
        needle = struct.pack("<Q", base + target)
        at = 0
        while True:
            at = data.find(needle, at)
            if at < 0:
                break
            try:
                source = pe.get_rva_from_offset(at)
                rows.append({"rva": hex(source), "function": containing(source), "kind": "absolute-pointer"})
            except pefile.PEFormatError:
                pass
            at += 1
        # Direct E8/E9 candidates must be decoded and map into .pdata functions.
        for match in re.finditer(rb"(?=([\xe8\xe9]....))", text_data, re.DOTALL):
            source = text.VirtualAddress + match.start()
            payload = match.group(1)
            if source + 5 + struct.unpack_from("<i", payload, 1)[0] == target:
                function = containing(source)
                if function is not None:
                    ins = next(md.disasm(payload, source), None)
                    if ins and ins.size == 5:
                        rows.append({"rva": hex(source), "function": function, "kind": "direct-" + ins.mnemonic})
        return rows
    result = {"schema": "xar.sway.cancel.exploration.v1", "exe_sha256": SHA,
              "read_only": True, "live_verified": False, "literals": [], "spans": [], "xrefs": []}
    for literal in args.literal:
        rows = []
        needle = literal.encode("ascii")
        at = 0
        while True:
            at = data.find(needle, at)
            if at < 0:
                break
            start = data.rfind(b"\0", max(at - 120, 0), at) + 1
            end = data.find(b"\0", at, at + 240)
            end = at + len(needle) if end < 0 else end
            try:
                rva = pe.get_rva_from_offset(start)
                surrounding = data[start:end].decode("ascii", errors="backslashreplace")
                rows.append({"rva": hex(rva), "literal": surrounding, "xrefs": references(rva)})
            except pefile.PEFormatError:
                pass
            at += len(needle)
        result["literals"].append({"requested": literal, "occurrences": rows})
    for target in args.xref:
        result["xrefs"].append({"target": hex(target), "references": references(target)})
    for target in args.xref32:
        rows = []
        needle = struct.pack("<I", target)
        at = 0
        while True:
            at = data.find(needle, at)
            if at < 0:
                break
            try:
                source = pe.get_rva_from_offset(at)
                rows.append({"rva": hex(source), "context": data[max(0, at - 24):at + 40].hex()})
            except pefile.PEFormatError:
                pass
            at += 1
        result["xrefs"].append({"target": hex(target), "kind": "rva32", "references": rows})
    result["descriptors"] = []
    for target in args.descriptor:
        at = 0
        cols = []
        while True:
            at = data.find(struct.pack("<I", target), at)
            if at < 0:
                break
            if at >= 12:
                fields = struct.unpack_from("<6I", data, at - 12)
                try:
                    col_rva = pe.get_rva_from_offset(at - 12)
                    if fields[0] == 1 and fields[3] == target and fields[5] == col_rva:
                        tables = []
                        for reference in references(col_rva):
                            if reference["kind"] == "absolute-pointer":
                                table = int(reference["rva"], 0) + 8
                                offset = pe.get_offset_from_rva(table)
                                pointers = struct.unpack_from("<20Q", data, offset)
                                tables.append({"rva": hex(table), "entries": [hex(value - base) for value in pointers]})
                        cols.append({"rva": hex(col_rva), "offset": fields[1], "vtables": tables})
                except pefile.PEFormatError:
                    pass
            at += 1
        result["descriptors"].append({"rva": hex(target), "cols": cols})
    for requested in args.rva:
        hits = [(first, last, unwind) for first, last, unwind in functions if first <= requested < last]
        if not hits:
            first, last, unwind = requested, requested + 0x100, None
        elif len(hits) != 1:
            raise ValueError("Expected one .pdata span for " + hex(requested))
        else:
            first, last, unwind = hits[0]
        at = pe.get_offset_from_rva(first)
        payload = data[at:at + last - first]
        result["spans"].append({"requested": hex(requested), "first": hex(first), "last": hex(last),
            "unwind": None if unwind is None else hex(unwind), "sha256": hashlib.sha256(payload).hexdigest(),
            "instructions": [{"rva": hex(ins.address), "bytes": ins.bytes.hex(),
                              "asm": ins.mnemonic + " " + ins.op_str}
                             for ins in md.disasm(payload, first)]})
    if args.rtti:
        pattern = re.compile(args.rtti, re.IGNORECASE)
        result["rtti"] = [{"rva": hex(pe.get_rva_from_offset(match.start()) - 16),
                           "name": match.group().rstrip(b"\0").decode("ascii")}
                          for match in re.finditer(rb"\.\?[A-Z][ -~]{3,240}?@@\x00", data)
                          if pattern.search(match.group().decode("ascii"))]
    if args.region:
        result["region"] = []
        low, high = args.region
        for first, last, unwind in functions:
            if low <= first < high:
                at = pe.get_offset_from_rva(first)
                for ins in md.disasm(data[at:at + last - first], first):
                    asm = ins.mnemonic + " " + ins.op_str
                    if args.filter is None or args.filter in asm:
                        result["region"].append({"function": hex(first), "rva": hex(ins.address),
                                                  "bytes": ins.bytes.hex(), "asm": asm})
    result["data"] = []
    for rva, size in args.data:
        at = pe.get_offset_from_rva(rva)
        payload = data[at:at + size]
        result["data"].append({"rva": hex(rva), "bytes": payload.hex(),
                               "u32": [hex(value[0]) for value in struct.iter_unpack("<I", payload[:len(payload) // 4 * 4])],
                               "sha256": hashlib.sha256(payload).hexdigest()})
    result["tokens"] = []
    for token in args.token:
        low, high = pe.get_offset_from_rva(0x46e0000), pe.get_offset_from_rva(0x46f8000)
        for at in range(low, high, 8):
            number, pointer = struct.unpack_from("<QQ", data, at)
            if number != token or not base <= pointer < base + pe.OPTIONAL_HEADER.SizeOfImage:
                continue
            target = pointer - base
            target_at = pe.get_offset_from_rva(target)
            end = data.find(b"\0", target_at, target_at + 256)
            if end >= 0:
                result["tokens"].append({"token": hex(token), "registry_rva": hex(pe.get_rva_from_offset(at)),
                                         "literal_rva": hex(target), "key": data[target_at:end].decode("ascii", errors="replace")})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "span_count": len(result["spans"]),
                      "literal_count": len(result["literals"]), "rtti_count": len(result.get("rtti", []))}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
