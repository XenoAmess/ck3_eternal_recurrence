"""Read-only exact-build PE extraction for the war-film retreat research package.

The output is a locator/disassembly record, not a semantic or live verifier.
Direct references are accepted only at instruction starts in a PE runtime-function
range. Absolute-pointer hits remain unclassified data references. No game process
is started or attached. Existing output files are never overwritten.
"""
from __future__ import annotations

import argparse
import bisect
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import struct
import sys

import pefile
from capstone import CS_ARCH_X86, CS_MODE_64, Cs

EXPECTED_SHA256 = "2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("functions", "refs", "riprefs", "fields", "data"))
    parser.add_argument("rva", nargs="+", type=lambda value: int(value, 0))
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--extent", type=lambda value: int(value, 0), help="functions: explicit bounded window from each containing fragment's start")
    parser.add_argument("--start", type=lambda value: int(value, 0))
    parser.add_argument("--end", type=lambda value: int(value, 0))
    args = parser.parse_args()
    data = args.exe.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(f"exact-build mismatch: {digest}")
    pe = pefile.PE(data=data, fast_load=True)
    image_base = pe.OPTIONAL_HEADER.ImageBase
    directory = pe.OPTIONAL_HEADER.DATA_DIRECTORY[3]
    offset = pe.get_offset_from_rva(directory.VirtualAddress)
    functions = list(struct.iter_unpack("<III", data[offset:offset + directory.Size]))
    starts = [row[0] for row in functions]
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoded = {}

    def container(rva):
        index = bisect.bisect_right(starts, rva) - 1
        if index >= 0 and functions[index][0] <= rva < functions[index][1]:
            return functions[index]
        return None

    def instructions(fn):
        begin, end, _unwind = fn
        if begin not in decoded:
            raw = pe.get_data(begin, end - begin)
            decoded[begin] = list(decoder.disasm_lite(raw, image_base + begin))
        return decoded[begin]

    result = {
        "schema": "xar.war-film-retreat-extract.v1", "proof_layer": "exact-build-locator-disassembly",
        "semantic_correctness_verified": False, "live_execution_performed": False,
        "exe": str(args.exe.resolve()), "exe_sha256": digest, "exe_size": len(data),
        "image_base": hex(image_base), "python": sys.executable, "python_version": sys.version,
        "dependencies": {name: importlib.metadata.version(name) for name in ("capstone", "pefile")},
        "argv": sys.argv, "mode": args.mode, "targets": [hex(rva) for rva in args.rva],
    }
    if args.mode == "functions":
        rows = []
        for rva in args.rva:
            fn = container(rva)
            runtime_function = list(fn) if fn else None
            if fn is None and args.extent:
                fn = (rva, rva + args.extent, 0)
            if fn is None:
                rows.append({"target": hex(rva), "runtime_function": None})
                continue
            begin, end, unwind = fn
            if args.extent:
                end = begin + args.extent
                fn = (begin, end, unwind)
            rows.append({"target": hex(rva), "begin": hex(begin), "end": hex(end), "unwind": hex(unwind),
                         "runtime_function": [hex(item) for item in runtime_function] if runtime_function else None,
                         "anchor_kind": "pdata-fragment" if runtime_function else "explicit-rva-not-boundary-verified",
                         "explicit_window": bool(args.extent),
                         "sha256": hashlib.sha256(pe.get_data(begin, end - begin)).hexdigest(),
                         "instructions": [f"{address - image_base:09X}  {pe.get_data(address - image_base, size).hex(' '):<32} {mnemonic:<8} {operands}" for address, size, mnemonic, operands in instructions(fn)]})
        result["functions"] = rows
    elif args.mode == "data":
        extent = args.extent or 0x80
        result["data"] = [{"rva": hex(rva), "hex": pe.get_data(rva, extent).hex(" "), "ascii_prefix": pe.get_data(rva, extent).split(b"\0", 1)[0].decode("ascii", errors="replace")} for rva in args.rva]
    elif args.mode in {"riprefs", "fields"}:
        if args.start is None or args.end is None or args.start >= args.end:
            raise ValueError("riprefs/fields requires a nonempty --start/--end RVA interval")
        targets = set(args.rva)
        rows = []
        pattern = re.compile(r"\[rip\s*([+-])\s*(0x[0-9a-f]+)\]")
        for fn in functions:
            if not (args.start <= fn[0] < args.end):
                continue
            for address, size, mnemonic, operands in instructions(fn):
                if args.mode == "fields":
                    for target in targets:
                        if re.search(r"\[[^\]]+\+ " + hex(target) + r"\]", operands):
                            rows.append({"source": hex(address - image_base), "field_displacement": hex(target), "instruction": f"{mnemonic} {operands}", "runtime_function": [hex(item) for item in fn]})
                    continue
                for match in pattern.finditer(operands):
                    displacement = int(match.group(2), 0) * (1 if match.group(1) == "+" else -1)
                    target = address - image_base + size + displacement
                    if target in targets:
                        rows.append({"source": hex(address - image_base), "target": hex(target), "instruction": f"{mnemonic} {operands}", "runtime_function": [hex(item) for item in fn]})
        result["range"] = [hex(args.start), hex(args.end)]
        result["rip_references" if args.mode == "riprefs" else "field_occurrences"] = rows
        result["limitations"] = ["Only PE runtime-function ranges beginning in the declared interval were decoded.", "Indirect memory aliases and references outside the declared interval are not enumerated."]
    else:
        targets = set(args.rva)
        candidates = []
        for section in pe.sections:
            if not section.IMAGE_SCN_MEM_EXECUTE:
                continue
            raw = section.get_data()
            for match in re.finditer(b"[\xe8\xe9]", raw):
                index = match.start()
                if index + 5 > len(raw):
                    continue
                source = section.VirtualAddress + index
                target = source + 5 + struct.unpack_from("<i", raw, index + 1)[0]
                if target in targets:
                    fn = container(source)
                    accepted = False
                    if fn:
                        accepted = any(address == image_base + source and size == 5 and mnemonic in ("call", "jmp") for address, size, mnemonic, _operands in instructions(fn))
                    candidates.append({"source": hex(source), "target": hex(target), "kind": "call" if raw[index] == 0xE8 else "jmp", "runtime_function": [hex(item) for item in fn] if fn else None, "instruction_boundary_verified": accepted})
        pointers = []
        for target in sorted(targets):
            needle = struct.pack("<Q", image_base + target)
            for match in re.finditer(re.escape(needle), data):
                source = pe.get_rva_from_offset(match.start())
                pointers.append({"source": hex(source), "target": hex(target), "classification": "unclassified-absolute-pointer"})
        result["direct_references"] = candidates
        result["absolute_pointers"] = pointers
        result["limitations"] = ["Does not enumerate indirect/vtable calls or RIP-relative LEA references.", "A .pdata function range is a decoding anchor; it can be a split fragment rather than a complete semantic function.", "An absent direct reference does not establish absence of a native policy."]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps({"output": str(args.output.resolve()), "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(), "mode": args.mode, "exe_sha256": digest}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
