#!/usr/bin/env python3
"""File-only bounded literal/xref and decoded native evidence for Sway."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

EXE_SHA = "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--literal", action="append", default=[])
    parser.add_argument("--rtti-pattern")
    parser.add_argument("--rva", type=lambda value: int(value, 0))
    parser.add_argument("--containing-function", action="store_true")
    parser.add_argument("--size", type=lambda value: int(value, 0), default=0x100)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    data = args.exe.read_bytes()
    actual_sha = hashlib.sha256(data).hexdigest().upper()
    if actual_sha != EXE_SHA:
        raise ValueError("Executable does not match frozen CK3 1.20.0.2")
    pe = pefile.PE(data=data, fast_load=True)
    image_base = pe.OPTIONAL_HEADER.ImageBase
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    result = {"schema": "xar.ck3.sway-outcome-native-slice", "schema_version": 1,
              "build": "1.20.0.2", "exe_sha256": actual_sha,
              "read_only": True, "live_verified": False, "literals": []}
    text = next(section for section in pe.sections if section.Name.rstrip(b"\0") == b".text")
    text_data = text.get_data()
    references = []
    # Candidate rip-relative LEA/MOV sites are confirmed by the decoder before use.
    for match in (re.finditer(rb"[\x48\x4c][\x8d\x8b][\x05\x0d\x15\x1d\x25\x2d\x35\x3d]....", text_data, re.DOTALL) if args.literal else []):
        rva = text.VirtualAddress + match.start()
        displacement = struct.unpack_from("<i", match.group(), 3)[0]
        references.append((rva + 7 + displacement, rva))
    for literal in args.literal:
        needle = literal.encode("ascii") + b"\0"
        rows = []
        position = 0
        while True:
            position = data.find(needle, position)
            if position < 0:
                break
            rva = pe.get_rva_from_offset(position)
            rows.append({"rva": hex(rva), "xrefs": [hex(source) for target, source in references if target == rva]})
            position += 1
        result["literals"].append({"literal": literal, "occurrences": rows})
    if args.rtti_pattern:
        pattern = re.compile(args.rtti_pattern, re.IGNORECASE)
        result["rtti"] = [{"rva": hex(pe.get_rva_from_offset(match.start()) - 16),
                           "name": match.group().rstrip(b"\0").decode("ascii")}
                          for match in re.finditer(rb"\.\?[A-Z][ -~]{3,240}?@@\x00", data)
                          if pattern.search(match.group().decode("ascii"))]
    if args.rva is not None:
        if args.containing_function:
            pdata = next(section for section in pe.sections if section.Name.rstrip(b"\0") == b".pdata").get_data()
            spans = [struct.unpack_from("<III", pdata, i) for i in range(0, len(pdata) - 11, 12)]
            containing = [(first, last, unwind) for first, last, unwind in spans if first <= args.rva < last]
            result["containing_runtime_functions"] = [{"start_rva": hex(first), "end_rva": hex(last), "unwind_rva": hex(unwind)}
                                                      for first, last, unwind in containing]
            if len(containing) != 1:
                raise ValueError("Expected one containing native runtime function")
            args.rva, last, _ = containing[0]
            args.size = last - args.rva
        offset = pe.get_offset_from_rva(args.rva)
        payload = data[offset:offset + args.size]
        result["span"] = {"start_rva": hex(args.rva), "end_rva": hex(args.rva + args.size),
                          "sha256": hashlib.sha256(payload).hexdigest().upper(),
                          "instructions": [{"rva": hex(ins.address - image_base),
                                            "bytes": ins.bytes.hex(), "mnemonic": ins.mnemonic,
                                            "operands": ins.op_str}
                                           for ins in decoder.disasm(payload, image_base + args.rva)]}
    output = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    print(json.dumps({"output": str(args.output), "exe_sha256": actual_sha,
                      "span": {key: value for key, value in result.get("span", {}).items() if key != "instructions"}})
          if args.quiet else output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
