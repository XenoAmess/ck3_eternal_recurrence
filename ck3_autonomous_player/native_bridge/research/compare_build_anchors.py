"""Find offline migration candidates; a byte match is not a verified ABI."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from capstone import CS_ARCH_X86, CS_MODE_64, CS_GRP_CALL, CS_GRP_JUMP, Cs
from capstone.x86 import X86_OP_MEM, X86_REG_RIP

from scan_anchors import PeImage, integer


def masked_pattern(code: bytes, rva: int, decoder: Cs) -> tuple[bytes, str]:
    if not code:
        raise ValueError("empty source signature")
    mask = bytearray(b"" * len(code))
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


def require_source_build(data: bytes, pe: PeImage, manifest: dict) -> None:
    expected = manifest["build"]
    actual = {"sha256": hashlib.sha256(data).hexdigest().upper(),
              "file_size": len(data), "pe_timestamp": pe.timestamp,
              "image_base": pe.image_base, "size_of_image": pe.size_of_image}
    for field, observed in actual.items():
        wanted = expected[field]
        wanted = str(wanted).upper() if field == "sha256" else integer(wanted)
        if observed != wanted:
            raise ValueError(f"source build {field} mismatch: {observed!r} != {wanted!r}")


def compare_builds(old_data: bytes, new_data: bytes, manifest: dict) -> dict:
    old_pe, new_pe = PeImage(old_data), PeImage(new_data)
    require_source_build(old_data, old_pe, manifest)
    # Anchors belong to the explicit source manifest. Never append addresses
    # from a different historical executable merely because a script knows them.
    anchors = manifest["signature_anchors"]
    names = [anchor["name"] for anchor in anchors]
    if not anchors or len(names) != len(set(names)):
        raise ValueError("source anchors must be nonempty and uniquely named")
    if not new_pe.executable_sections:
        raise ValueError("target has no file-backed executable sections")
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    rows = []
    for anchor in anchors:
        old_rva = integer(anchor["rva"])
        needle = bytes.fromhex(anchor["pattern"])
        offset = old_pe.rva_to_offset(old_rva)
        if not needle or old_data[offset:offset + len(needle)] != needle:
            raise ValueError(f"stale or empty source signature: {anchor['name']}")
        regex, display = masked_pattern(needle, old_rva, decoder)
        matches = []
        for code_rva, code_offset, code_size in new_pe.executable_sections:
            code = new_data[code_offset:code_offset + code_size]
            matches.extend(code_rva + match.start() for match in
                           re.finditer(b"(?=" + regex + b")", code, re.DOTALL))
        row = {"name": anchor["name"], "old_rva": hex(old_rva),
               "masked_pattern": display,
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
    return {"old_sha256": hashlib.sha256(old_data).hexdigest().upper(),
            "new_sha256": hashlib.sha256(new_data).hexdigest().upper(),
            "source_version": manifest["build"].get("product_version"),
            "implicit_historical_anchors": False,
            "method": "explicit source manifest; executable sections; mask RIP and branch immediates; preserve object offsets",
            "warning": "Single signatures are candidates for semantic review, never automatic runtime bindings.",
            "anchors": rows}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-exe", type=Path, required=True)
    parser.add_argument("--new-exe", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True,
                        help="exact source build identity and explicit signatures, including thread anchors if wanted")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
    result = compare_builds(args.old_exe.read_bytes(), args.new_exe.read_bytes(), manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
    rows = result["anchors"]
    print(json.dumps({"anchors": len(rows),
                      "single_candidates": sum(len(row["candidate_rvas"]) == 1 for row in rows),
                      "unresolved": [row["name"] for row in rows if len(row["candidate_rvas"]) != 1]}))


if __name__ == "__main__":
    main()
