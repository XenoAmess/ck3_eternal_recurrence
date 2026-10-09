"""Root-only capture of the six declared actual4 person-merger gaps.

The 284 already-held bytes are deliberately not read. Cached runtime rows
select candidates; a complete decode alone does not prove merger semantics.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86_const import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP


SPANS = (
    (0x2303100, 0x2303109),
    (0x2303116, 0x2303142),
    (0x230314F, 0x2303190),
    (0x2303198, 0x2303218),
    (0x230321F, 0x2303276),
    (0x2303380, 0x2303488),
)
EXISTING_SHA = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    started = datetime.now(timezone.utc).isoformat()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    rows = []
    with args.exe.open("rb") as source:
        for begin, end in SPANS:
            source.seek(begin - 3072)
            raw = source.read(end - begin)
            instructions, assembly = [], []
            for insn in decoder.disasm(raw, begin):
                rip_targets, branch_targets = [], []
                for operand in insn.operands:
                    if operand.type == X86_OP_MEM and operand.mem.base == X86_REG_RIP:
                        rip_targets.append(hex(insn.address + insn.size + operand.mem.disp))
                    elif operand.type == X86_OP_IMM and (
                        insn.mnemonic == "call" or insn.mnemonic.startswith("j")
                    ):
                        branch_targets.append(hex(operand.imm))
                instructions.append({
                    "rva": hex(insn.address), "size": insn.size,
                    "raw_hex": bytes(insn.bytes).hex(), "mnemonic": insn.mnemonic,
                    "operands": insn.op_str, "rip_targets": rip_targets,
                    "branch_targets": branch_targets,
                })
                assembly.append(
                    f"{insn.address:08X} {bytes(insn.bytes).hex(' '):<32} "
                    f"{insn.mnemonic} {insn.op_str}".rstrip()
                )
            decoded = sum(item["size"] for item in instructions)
            raw_path = args.output_dir / f"{begin:X}.bin"
            asm_path = args.output_dir / f"{begin:X}.asm"
            with raw_path.open("xb") as output:
                output.write(raw)
            with asm_path.open("x", encoding="utf-8") as output:
                output.write("\n".join(assembly) + "\n")
            rows.append({
                "begin_rva": hex(begin), "end_rva": hex(end),
                "file_offset": begin - 3072, "requested_bytes": end - begin,
                "actual_bytes": len(raw), "decoded_bytes": decoded,
                "decoded_complete": len(raw) == end - begin and decoded == len(raw),
                "raw_path": str(raw_path.resolve()), "asm_path": str(asm_path.resolve()),
                "raw_hex": raw.hex(), "instructions": instructions,
                "actual_ret_rvas": [item["rva"] for item in instructions
                                    if item["mnemonic"] in ("ret", "retf")],
            })
    complete = all(row["decoded_complete"] for row in rows)
    receipt = {
        "schema": "xar.person-six-stage-merger.root-gap-capture-12004.v1",
        "status": "COMPLETE" if complete else "CAPTURE_OR_DECODE_PARTIAL",
        "operator": "Root", "started_at_utc": started,
        "ended_at_utc": datetime.now(timezone.utc).isoformat(),
        "exe": str(args.exe.resolve()), "existing_exe_sha256_not_rehashed": EXISTING_SHA,
        "section_metadata_reused": {"text_rva": 4096, "text_raw_offset": 1024},
        "file_offset_formula": "rva-3072", "requested_bytes": 597,
        "actual_bytes": sum(row["actual_bytes"] for row in rows),
        "new_exe_reads": len(rows), "held_bytes_not_reread": 284,
        "metadata_candidate_union_bytes": 881,
        "semantic_closure_claimed": False,
        "other_target_or_rip_data_reads": 0,
        "PE_pdata_hash_game_SDK_process_compiler_test": 0,
        "spans": rows,
    }
    receipt_path = args.output_dir / "SOURCE-CAPTURE.json"
    with receipt_path.open("x", encoding="utf-8") as output:
        json.dump(receipt, output, ensure_ascii=False, indent=2)
        output.write("\n")
    print(json.dumps({
        "status": receipt["status"], "bytes": receipt["actual_bytes"],
        "reads": receipt["new_exe_reads"], "receipt": str(receipt_path.resolve()),
    }))
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
