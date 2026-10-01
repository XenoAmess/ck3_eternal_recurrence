"""Verify changed ransom inputs against disk assets only; never execute CK3."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP

HERE = Path(__file__).resolve().parent
CONTRACT = HERE / "ck3_12002_prisoner_ransom_abi.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def verify_ransom(exe: Path, game_root: Path) -> dict:
    manifest = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    data = exe.read_bytes()
    exact = manifest["exact_build"]
    sha = hashlib.sha256(data).hexdigest()
    require(len(data) == exact["executable_size"], "EXE size mismatch")
    require(sha == exact["executable_sha256"], "EXE SHA mismatch")
    pe = pefile.PE(data=data, fast_load=True)
    require(pe.OPTIONAL_HEADER.ImageBase == int(exact["image_base"], 0),
            "image base mismatch")

    def read(rva: int, length: int) -> bytes:
        offset = pe.get_offset_from_rva(rva)
        require(0 <= offset <= len(data) - length, "native span outside image")
        return data[offset:offset + length]

    for row in manifest["native_spans"]:
        require(hashlib.sha256(read(int(row["rva"], 0), row["size"])).hexdigest()
                == row["sha256"], f"changed native span: {row['name']}")
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    for row in manifest["semantic_instructions"]:
        rva = int(row["rva"], 0)
        ins = next(decoder.disasm(read(rva, 15), rva))
        actual = {
            "bytes": ins.bytes.hex(" ").upper(),
            "instruction": f"{ins.mnemonic} {ins.op_str}",
            "rip_targets": [hex(ins.address + ins.size + op.mem.disp)
                            for op in ins.operands if op.type == X86_OP_MEM
                            and op.mem.base == X86_REG_RIP],
            "direct_targets": [hex(op.imm) for op in ins.operands
                               if op.type == X86_OP_IMM
                               and ins.mnemonic in ("call", "jmp")],
        }
        require(all(actual[key] == row[key] for key in actual),
                f"changed native instruction: {row['name']}")
    header = (HERE.parent / "include/xar_bridge/ck3_12002_prisoner_abi.hpp").read_text(
        encoding="utf-8-sig")
    for name, expected in manifest["source_constants"].items():
        match = re.search(rf"\b{re.escape(name)}\s*=\s*(0x[\dA-Fa-f]+)", header)
        require(match is not None and int(match.group(1), 0) == int(expected, 0),
                f"changed binding constant: {name}")

    source_texts = {}
    for row in manifest["stock_sources"]:
        path = game_root / row["path"].removeprefix("game/")
        raw = path.read_bytes()
        require(hashlib.sha256(raw).hexdigest() == row["sha256"],
                f"changed stock source: {row['path']}")
        source_texts[row["path"]] = raw.decode("utf-8-sig")
    stock = source_texts["game/common/character_interactions/00_prison_interactions.txt"]
    start = re.search(r"^ransom_interaction\s*=\s*\{", stock, re.M)
    end = re.search(r"^pay_ransom_interaction\s*=\s*\{", stock, re.M)
    require(start is not None and end is not None and start.start() < end.start(),
            "ransom interaction block missing")
    ransom_block = stock[start.start():end.start()]
    authored = re.sub(r"#[^\n]*", "", ransom_block)
    options = []
    for option in re.finditer(r"\bsend_option\s*=\s*\{", authored):
        depth = 1
        cursor = option.end()
        while depth and cursor < len(authored):
            depth += (authored[cursor] == "{") - (authored[cursor] == "}")
            cursor += 1
        require(depth == 0, "unbalanced authored send option")
        flags = re.findall(r"\bflag\s*=\s*(\w+)", authored[option.end():cursor])
        require(len(flags) == 1, "send option must have one authored flag")
        options.extend(flags)
    require(options == manifest["stock_option_order"],
            f"ransom authored option order changed: {options}")
    require("scope:secondary_recipient.normal_ransom_cost_value" in ransom_block,
            "ordinary ransom quote no longer uses prisoner normal value")
    provider = (HERE.parent / "src/ck3_12002_prisoner.cpp").read_text(
        encoding="utf-8-sig")
    require('kRansomCost = "normal_ransom_cost_value"' in provider,
            "production ordinary ransom key disagrees with stock")
    require(re.search(r"kOptionCount\s*=\s*9\s*;", provider) is not None,
            "production ransom provider does not handle nine options")
    for name, expected in {
        "kContextSize": "context_size",
        "kOptionDataOffset": "context_option_data",
        "kOptionCountOffset": "context_option_count",
        "kDefinitionOptionRowsOffset": "definition_option_data",
        "kDefinitionOptionCountOffset": "definition_option_count",
        "kDefinitionOptionRowStride": "definition_option_row_stride",
        "kDefinitionOptionFlagOffset": "option_flag_id",
    }.items():
        match = re.search(rf"\b{name}\s*=\s*(0x[\dA-Fa-f]+)", provider)
        require(match is not None and int(match.group(1), 0) ==
                int(manifest["source_layout"][expected], 0),
                f"production option field disagrees with native: {name}")
    return {
        "status": "GREEN", "readiness": "static-ready",
        "live_verified": False, "local_ck3_touched": False,
        "game_version": "1.20.0.2", "executable_sha256": sha,
        "contract_sha256": hashlib.sha256(CONTRACT.read_bytes()).hexdigest(),
        "native_spans": len(manifest["native_spans"]),
        "semantic_instructions": len(manifest["semantic_instructions"]),
        "binding_constants": len(manifest["source_constants"]),
        "authored_options": len(options), "stock_sources": len(source_texts),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--game-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify_ransom(args.exe, args.game_root)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"PASS ransom ABI: {result['native_spans']} spans, "
          f"{result['semantic_instructions']} instructions, "
          f"{result['binding_constants']} bindings, "
          f"{result['authored_options']} authored options; offline only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
