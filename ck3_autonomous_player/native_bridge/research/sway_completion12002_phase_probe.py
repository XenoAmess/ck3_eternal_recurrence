"""Bounded, file-only exact-build Sway phase evidence collector."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from scan_anchors import PeImage

EXE_SHA256 = "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--rva", action="append", default=[])
    parser.add_argument("--size", type=lambda s: int(s, 0), default=0x100)
    parser.add_argument("--table", action="append", default=[])
    parser.add_argument("--table-count", type=int, default=16)
    parser.add_argument("--caller", action="append", default=[])
    parser.add_argument("--strings-pattern")
    parser.add_argument("--dataref", action="append", default=[])
    parser.add_argument("--rip-target", action="append", default=[])
    parser.add_argument("--raw", action="append", default=[])
    parser.add_argument("--field-scan")
    parser.add_argument("--field-pattern", default=r"\+ 0x(?:78|350)\]")
    parser.add_argument("--member-disp", action="append", default=[])
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    data = args.exe.read_bytes()
    if hashlib.sha256(data).hexdigest().upper() != EXE_SHA256:
        raise ValueError("Exact frozen build mismatch")
    pe = PeImage(data)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.skipdata = True
    rows = []
    for value in args.rva:
        rva = int(value, 0)
        offset = pe.rva_to_offset(rva)
        payload = data[offset:offset + args.size]
        instructions = [{"rva": hex(ins.address), "bytes": ins.bytes.hex(),
                         "mnemonic": ins.mnemonic, "operands": ins.op_str}
                        for ins in decoder.disasm(payload, rva)]
        rows.append({"rva": hex(rva), "size": len(payload),
                     "sha256": hashlib.sha256(payload).hexdigest(), "instructions": instructions})
        print(hex(rva))
        for ins in instructions:
            print(ins["rva"], ins["mnemonic"], ins["operands"])
    tables = []
    for value in args.table:
        rva = int(value, 0)
        pointers = [hex(v - pe.image_base) for v in
                    struct.unpack_from("<" + str(args.table_count) + "Q", data, pe.rva_to_offset(rva))]
        tables.append({"rva": hex(rva), "function_rvas": pointers})
        print("table", hex(rva), pointers)
    callers = []
    for value in args.caller:
        target = int(value, 0)
        matches = []
        for va, _, raw, raw_size in pe.sections:
            if va != 0x1000:
                continue
            payload = data[raw:raw + raw_size]
            start = 0
            while True:
                index = payload.find(b"\xe8", start)
                if index < 0 or index + 5 > len(payload):
                    break
                rva = va + index
                if rva + 5 + struct.unpack_from("<i", payload, index + 1)[0] == target:
                    ins = next(decoder.disasm(payload[index:index + 5], rva))
                    if ins.mnemonic == "call":
                        matches.append(hex(rva))
                start = index + 1
        callers.append({"target_rva": hex(target), "caller_rvas": matches})
        print("callers", hex(target), matches)
    result = {"schema": "xar.ck3.sway-completion-phase-evidence.v1",
              "exe_sha256": EXE_SHA256, "game_version": "1.20.0.2",
              "read_only": True, "live_verified": False,
              "spans": rows, "tables": tables, "callers": callers}
    if args.dataref:
        refs = []
        for value in args.dataref:
            target = int(value, 0)
            needle = struct.pack("<Q", pe.image_base + target)
            offset = 0
            matches = []
            while True:
                offset = data.find(needle, offset)
                if offset < 0:
                    break
                rva = pe.offset_to_rva(offset)
                neighbors = [hex(v - pe.image_base) for v in struct.unpack_from("<12Q", data, offset - 32)]
                matches.append({"rva": hex(rva), "neighbors_first_rva": hex(rva - 32), "neighbors": neighbors})
                print("dataref", hex(target), hex(rva), neighbors)
                offset += 1
            refs.append({"target_rva": hex(target), "matches": matches})
        result["datarefs"] = refs
    if args.raw:
        result["raw"] = []
        for value in args.raw:
            rva = int(value, 0)
            offset = pe.rva_to_offset(rva)
            payload = data[offset - 32:offset + 96]
            row = {"start_rva": hex(rva - 32), "bytes": payload.hex(), "repr": repr(payload)}
            result["raw"].append(row)
            print("raw", hex(rva), row["repr"])
    if args.rip_target:
        references = []
        targets = [int(v, 0) for v in args.rip_target]
        for va, _, raw, raw_size in pe.sections:
            if va != 0x1000:
                continue
            payload = data[raw:raw + raw_size]
            for match in re.finditer(rb"[\x48\x4c][\x8d\x8b][\x05\x0d\x15\x1d\x25\x2d\x35\x3d]....", payload, re.DOTALL):
                rva = va + match.start()
                target = rva + 7 + struct.unpack_from("<i", match.group(), 3)[0]
                if any(abs(target - value) < 96 for value in targets):
                    ins = next(decoder.disasm(match.group(), rva))
                    row = {"rva": hex(rva), "target_rva": hex(target), "bytes": ins.bytes.hex(),
                           "instruction": ins.mnemonic + " " + ins.op_str}
                    references.append(row)
                    print("ripref", row["rva"], row["target_rva"], row["instruction"])
        result["riprefs"] = references
    if args.field_scan:
        first, last = [int(value, 0) for value in args.field_scan.split(":")]
        offset = pe.rva_to_offset(first)
        payload = data[offset:offset + last - first]
        decoded = list(decoder.disasm(payload, first))
        pattern = re.compile(args.field_pattern)
        rows = []
        for index, ins in enumerate(decoded):
            if not pattern.search(ins.op_str):
                continue
            window = decoded[max(0, index - 3):index + 5]
            row = {"rva": hex(ins.address), "window": [
                {"rva": hex(item.address), "bytes": item.bytes.hex(),
                 "mnemonic": item.mnemonic, "operands": item.op_str} for item in window]}
            rows.append(row)
            print("field", row["rva"])
            for item in row["window"]:
                print(item["rva"], item["mnemonic"], item["operands"])
        result["field_windows"] = rows
    if args.member_disp:
        rows = []
        wanted = {int(value, 0) for value in args.member_disp}
        for va, _, raw, raw_size in pe.sections:
            if va != 0x1000:
                continue
            payload = data[raw:raw + raw_size]
            for match in re.finditer(rb"[\x48-\x4f][\x8d\x8b\x89][\x80-\xbf]....", payload, re.DOTALL):
                encoded = match.group()
                if encoded[2] & 7 == 4 or struct.unpack_from("<i", encoded, 3)[0] not in wanted:
                    continue
                rva = va + match.start()
                ins = next(decoder.disasm(encoded, rva))
                row = {"rva": hex(rva), "bytes": ins.bytes.hex(),
                       "instruction": ins.mnemonic + " " + ins.op_str}
                rows.append(row)
                print("member", row["rva"], row["instruction"])
        result["member_displacements"] = rows
    if args.strings_pattern:
        pattern = re.compile(args.strings_pattern, re.IGNORECASE)
        strings = [{"rva": hex(pe.offset_to_rva(match.start())), "text": match.group().decode("ascii")}
                   for match in re.finditer(rb"[\x20-\x7e]{4,180}", data)
                   if pattern.search(match.group().decode("ascii"))]
        result["strings"] = strings
        for row in strings:
            print(row["rva"], row["text"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
