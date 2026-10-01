"""Verify alliance-war native inputs against an exact frozen EXE file only."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP
from scan_anchors import PeImage

HERE = Path(__file__).resolve().parent
CONTRACT = HERE / "ck3_12002_family_obligations_alliance_abi.json"


def require(value: bool, reason: str) -> None:
    if not value:
        raise ValueError(reason)


def verify(executable: Path, stock_game: Path | None = None) -> dict:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    data = executable.read_bytes()
    image = PeImage(data)
    build = contract["exact_build"]
    require(len(data) == build["executable_size"] and
            hashlib.sha256(data).hexdigest().upper() == build["executable_sha256"],
            "exact executable build differs")

    def read(rva: int, length: int) -> bytes:
        offset = image.rva_to_offset(rva)
        return data[offset:offset + length]

    for span in contract["native_spans"]:
        start, end = int(span["rva_start"], 0), int(span["rva_end_exclusive"], 0)
        raw = read(start, end - start)
        require(raw.hex() == span["raw_hex"] and hashlib.sha256(raw).hexdigest() == span["sha256"],
                f"native span differs: {span['name']}")
    for call in contract["direct_calls"]:
        site, target = int(call["site"], 0), int(call["target"], 0)
        raw = read(site, 5)
        require(raw[0] in (0xE8, 0xE9) and site + 5 + struct.unpack_from("<i", raw, 1)[0] == target,
                f"native call differs: {call['site']}")
    header = (HERE.parent / "include/xar_bridge/ck3_12002_family_obligations_alliance.hpp").read_text(
        encoding="utf-8-sig")
    constants = {}
    for name, expected in contract["source_constants"].items():
        match = re.search(rf"\b{re.escape(name)}\s*=\s*(0x[0-9A-Fa-f]+|\d+)", header)
        require(match is not None and int(match.group(1), 0) == int(expected, 0),
                f"source constant differs: {name}")
        constants[name] = int(expected, 0)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    for row in contract["native_operand_bindings"]:
        rva = int(row["rva"], 0)
        instruction = next(decoder.disasm(read(rva, 15), rva))
        require(instruction.bytes.hex() == row["bytes"] and
                f"{instruction.mnemonic} {instruction.op_str}" == row["instruction"],
                f"native source operand differs: {row['rva']}")
        if row["kind"] == "rip":
            operands = [instruction.address + instruction.size + value.mem.disp
                        for value in instruction.operands if value.type == X86_OP_MEM and
                        value.mem.base == X86_REG_RIP]
        elif row["kind"] == "immediate":
            operands = [value.imm for value in instruction.operands if value.type == X86_OP_IMM]
        else:
            operands = [value.mem.disp for value in instruction.operands if value.type == X86_OP_MEM]
        require(constants[row["constant"]] in operands,
                f"source constant absent from native operand: {row['constant']}")
    if stock_game is not None:
        stock = stock_game / contract["stock_source"]["relative_path"]
        require(hashlib.sha256(stock.read_bytes()).hexdigest() ==
                contract["stock_source"]["file_sha256"], "stock CallAlly source differs")
    return {"status": "GREEN", "readiness": "static-ready", "process_access": False,
            "live_validation": False, "executable_sha256": build["executable_sha256"],
            "native_span_count": len(contract["native_spans"]), "direct_call_count": len(contract["direct_calls"]),
            "native_operand_binding_count": len(contract["native_operand_bindings"]),
            "source_constant_count": len(constants), "stock_source_verified": stock_game is not None,
            "contract_sha256": hashlib.sha256(CONTRACT.read_bytes()).hexdigest()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--stock-game", type=Path)
    parser.add_argument("--result", type=Path)
    args = parser.parse_args()
    report = verify(args.exe.resolve(), args.stock_game.resolve() if args.stock_game else None)
    if args.result:
        args.result.parent.mkdir(parents=True, exist_ok=True)
        args.result.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
