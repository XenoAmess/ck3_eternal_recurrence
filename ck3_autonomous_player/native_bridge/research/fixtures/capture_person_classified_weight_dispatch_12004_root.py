"""Root-only, single exact4 classified-property dispatch capture.

This recipe is authored without execution. It never selects more code from
the returned instructions, hashes the EXE, or parses native metadata.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time


CAPTURES = {
    "dispatch": (0x2438980, 0x24389D7, "classified-weight-dispatch-02438980",
                 "Root-only one actual CALL2BA93D9 target; cached runtime row126853"),
    "continuation": (0x24389D7, 0x2438B75, "classified-weight-continuation-024389D7",
                     "Actual JNE24389CB->24389D7 and JMP24389D2->2438B5E; cached rows126854/126855"),
    "row-lookup": (0x23036E0, 0x2303705, "classified-row-key-lookup-023036E0",
                   "Actual weighted row CALL2438A6E->23036E0; cached row120551"),
    "row-lookup-remainder": (0x2303705, 0x2303783, "classified-row-key-remainder-02303705",
                             "Actual lookup fallthrough2303705; cached continuous rows120552..120555 before first alignment gap"),
}
TEXT_RVA = 0x1000
TEXT_RAW = 0x400
EXISTING_SHA = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--part", choices=tuple(CAPTURES), default="dispatch")
    args = parser.parse_args()
    begin, end, basename, authority = CAPTURES[args.part]
    # Root supplies its already qualified Capstone interpreter, never a game call.
    from capstone import CS_ARCH_X86, CS_MODE_64, Cs
    from capstone.x86 import X86_OP_IMM

    output = args.output_dir
    output.mkdir(parents=True, exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    offset = begin - TEXT_RVA + TEXT_RAW
    before = time.perf_counter()
    with args.exe.open("rb") as source:
        source.seek(offset)
        body = source.read(end - begin)
    read_seconds = time.perf_counter() - before
    binary = output / (basename + ".bin")
    assembly = output / (basename + ".asm")
    binary.write_bytes(body)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    instructions = list(decoder.disasm(body, begin))
    text = "".join(
        f"{item.address:08X} {item.bytes.hex():32} {item.mnemonic} {item.op_str}\n"
        for item in instructions
    )
    assembly.write_text(text, encoding="utf-8")
    targets = [
        {"source_rva": hex(item.address), "kind": item.mnemonic,
         "target_rva": hex(item.operands[0].imm)}
        for item in instructions
        if (item.mnemonic == "call" or item.mnemonic.startswith("j"))
        and item.operands and item.operands[0].type == X86_OP_IMM
    ]
    decoded = sum(item.size for item in instructions)
    result = {
        "schema": "xar.person.classified-weight-dispatch.capture.v1",
        "start_utc": started,
        "end_utc": datetime.now(timezone.utc).isoformat(),
        "authority": authority,
        "selected_part": args.part,
        "exe": str(args.exe),
        "existing_executable_sha256": EXISTING_SHA,
        "begin_rva": hex(begin), "end_rva_exclusive": hex(end),
        "file_offset": hex(offset), "requested_bytes": end - begin,
        "read_bytes": len(body), "read_count": 1,
        "read_seconds": read_seconds,
        "binary": str(binary), "assembly": str(assembly),
        "decoded_bytes": decoded,
        "decoded_instruction_count": len(instructions),
        "decode_complete": decoded == len(body) == end - begin,
        "literal_control_flow_targets": targets,
        "source_semantics_closed": False,
        "automatic_target_expansion": False,
        "fresh_hash_pe_pdata_unwind_bytes": 0,
        "game_sdk_process_build_test_calls": 0,
    }
    receipt = output / "SOURCE-CAPTURE.json"
    receipt.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"receipt": str(receipt), "read_bytes": len(body),
                      "decode_complete": result["decode_complete"]}))
    if not result["decode_complete"]:
        raise SystemExit("Exact selected fragment did not decode completely; keep original receipt")


if __name__ == "__main__":
    main()
