"""Read exact CK3 EXE/script bytes for the war-film target-selection study.

No process discovery, game launch, attachment, native invocation or emulation.
The output binds selected instruction windows and the containing pdata fragments;
the companion document supplies the human interpretation of those instructions.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import struct
import sys

import capstone
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP
import pefile

EXE_SHA256 = "2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86"

# End RVAs are exclusive. These are explicit evidence windows, not invented
# function boundaries. The separate pdata records below identify their owners.
WINDOWS = {
    "coordinator_call_and_commit": [(0x185A780, 0x185AA20)],
    "objective_blocks_and_shared_pair_pool": [(0x185AE6C, 0x185B345)],
    "ordinary_candidate_generation": [(0x185B8DC, 0x185B99B), (0x185BCB0, 0x185BD75),
                                      (0x185C45C, 0x185C4D5), (0x185C565, 0x185C660)],
    "province_dedup_and_priority": [(0x185C690, 0x185C803), (0x185C847, 0x185C8D9)],
    "pair_score_before_sort": [(0x185CC63, 0x185CD0E), (0x185D14E, 0x185D199),
                               (0x185E6E0, 0x185E7CF)],
    "pair_record_builder": [(0x1860A20, 0x1860BA8), (0x18618E0, 0x18619DF)],
    "insertion_sort_comparator": [(0x1862955, 0x1862B14)],
    "large_sort_dispatch": [(0x1862B40, 0x1862C3C)],
    "buffered_merge_comparator": [(0x1864BBC, 0x1864D2F), (0x1866949, 0x1866A62)],
    "merge_fallback_comparators": [(0x1864DA7, 0x1864DEF), (0x1864EE4, 0x1864F50),
                                   (0x1868510, 0x18685B5), (0x1868730, 0x18687C2),
                                   (0x1868916, 0x1868A89)],
    "shortlist_and_greedy_route_selection": [(0x185EC30, 0x185F000)],
    "selected_record_materialization": [(0x185B620, 0x185B7FE),
                                         (0x184BC6D, 0x184BC7B), (0x184BD41, 0x184BD53)],
    "native_route_wrapper": [(0x191A9C0, 0x191AAAC), (0x191A260, 0x191A2B0),
                             (0x191A660, 0x191A6C0)],
    "min_goals_registration": [(0x18AB9E8, 0x18ABA18), (0x18ABB08, 0x18ABB13),
                               (0x18ABB53, 0x18ABB5E)],
}

# Instruction bytes are an exact-build guard, not a semantic test or live result.
ANCHOR_BYTES = {
    0x185A83F: "e8fc010000", 0x185B225: "e8b6160000",
    0x185B26F: "e8bc760000", 0x185B30A: "e831780000",
    0x185B327: "e804390000", 0x185C7E0: "483b93a8000000",
    0x185C84D: "394508", 0x185C850: "7eb1",
    0x18629CD: "413b4e2c", 0x18629D1: "0f8e8a000000",
    0x1862A68: "7e4a", 0x1864C29: "7e22", 0x1866999: "7e41",
    0x185EDF6: "448b0491", 0x185EDFA: "418d4001", 0x185EDFE: "890491",
    0x185EE01: "443b05a0f0ea03", 0x185EE08: "0f8fa6010000",
    0x185EE10: "41ffc1", 0x185EF0D: "e8aeba0b00", 0x185EF1C: "752a",
    0x185EF7F: "c6040101", 0x185EF83: "43c644e52101", 0x185EF89: "c6433101",
    0x185B684: "41807e3100", 0x185A907: "f6879000000004",
    0x185A921: "740f", 0x185A925: "7e0b",
    0x185A927: "48897760", 0x185A92B: "44887778", 0x185A92F: "896f74",
    0x18ABB08: "488d059923e603",
}


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def extract(exe: Path) -> dict:
    raw = exe.read_bytes()
    if digest(raw) != EXE_SHA256:
        raise ValueError("EXE is not the frozen CK3 1.19.0.6 build")
    pe = pefile.PE(data=raw, fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase
    directory = pe.OPTIONAL_HEADER.DATA_DIRECTORY[
        pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_EXCEPTION"]]
    pdata = list(struct.iter_unpack("<III", pe.get_data(directory.VirtualAddress, directory.Size)))
    cs = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    cs.detail = True
    owners = {}
    decoded = {}
    for ranges in WINDOWS.values():
        for start, end in ranges:
            for a, b, unwind in pdata:
                if a < end and b > start and a not in owners:
                    code = pe.get_data(a, b - a)
                    if len(code) != b - a:
                        raise ValueError(f"Unbacked pdata span {a:#x}")
                    owners[a] = {"start_rva": hex(a), "end_rva": hex(b),
                                 "unwind_rva": hex(unwind), "byte_count": len(code),
                                 "sha256": digest(code)}
                    for insn in cs.disasm(code, base + a):
                        item = {"rva": hex(insn.address - base), "bytes": insn.bytes.hex(),
                                "mnemonic": insn.mnemonic, "operands": insn.op_str,
                                "pdata_start_rva": hex(a)}
                        rip = [insn.address + insn.size + op.mem.disp - base
                               for op in insn.operands
                               if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP]
                        if rip:
                            item["rip_targets"] = [hex(v) for v in rip]
                        imms = [op.imm - base for op in insn.operands
                                if op.type == X86_OP_IMM and base <= op.imm < base + pe.OPTIONAL_HEADER.SizeOfImage]
                        if imms:
                            item["image_immediates"] = [hex(v) for v in imms]
                        decoded[insn.address - base] = item
    anchors = {}
    for rva, expected in ANCHOR_BYTES.items():
        instruction = decoded.get(rva)
        if instruction is None or instruction["bytes"] != expected:
            raise ValueError(f"Instruction-boundary/byte mismatch at {rva:#x}")
        anchors[hex(rva)] = instruction
    if anchors["0x18abb08"]["rip_targets"] != ["0x570dea8"]:
        raise ValueError("MIN_GOALS_PER_STACK registration storage mismatch")
    if anchors["0x185ee01"]["rip_targets"] != ["0x570dea8"]:
        raise ValueError("MIN_GOALS_PER_STACK consumer storage mismatch")
    game = exe.parent.parent / "game"
    scripts = []
    for relative, ranges in [
        ("common/defines/ai/00_ai.txt", [(1293, 1297)]),
        ("common/ai_war_stances/_ai_war_stances.info", [(82, 110)]),
        ("common/ai_war_stances/00_ai_war_stances.txt", [(1, 80)]),
    ]:
        source = (game / relative).read_bytes()
        lines = source.decode("utf-8-sig").splitlines()
        scripts.append({"relative_path": relative, "sha256": digest(source),
                        "excerpts": [{"first_line": a, "last_line": b,
                                      "lines": lines[a - 1:b]} for a, b in ranges]})
    if not any("MIN_GOALS_PER_STACK = 10" in line
               for excerpt in scripts[0]["excerpts"] for line in excerpt["lines"]):
        raise ValueError("Unexpected authored MIN_GOALS_PER_STACK value")
    return {
        "schema": "xar.war-film-target-selection.static.v1",
        "scope": "offline exact EXE/script extraction; no native execution or emulation",
        "live_execution": False, "semantic_interpretation_automatically_verified": False,
        "build": {"version": "1.19.0.6", "exe_sha256": EXE_SHA256,
                  "exe_bytes": len(raw), "exe_path": str(exe.resolve())},
        "extractor_sha256": digest(Path(__file__).read_bytes()),
        "interpreter": sys.executable, "python_version": sys.version,
        "dependencies": {n: importlib.metadata.version(n) for n in ["capstone", "pefile"]},
        "pdata_boundary_note": "A pdata entry can be a fragment and can contain jump-table data; linear decode does not prove reachability.",
        "source_contracts": scripts, "instruction_anchor_count": len(anchors),
        "anchors": anchors, "pdata_fragments": [owners[a] for a in sorted(owners)],
        "windows": {label: {"ranges": [[hex(a), hex(b)] for a, b in ranges],
                            "instructions": [decoded[r] for r in sorted(decoded)
                                             if any(a <= r < b for a, b in ranges)]}
                    for label, ranges in WINDOWS.items()},
        "min_goals_counter_truth_table": {
            "kind": "Arithmetic interpretation of decoded signed compare; not a native replay",
            "define_value": 10,
            "rows": [{"old_counter": n, "stored_counter": n + 1,
                      "skip_budget_branch_old_gt_define": n > 10,
                      "increment_quota_counter_old_eq_define": n == 10}
                     for n in [0, 9, 10, 11]],
            "boundary": "The branch alone permits old counters 0..10. Other earlier/later gates and aggregate early stop mean no fixed number of paths is promised.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = extract(args.exe)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    with args.output.open("xb") as stream:
        stream.write(payload)
    print(json.dumps({"output": str(args.output), "sha256": digest(payload),
                      "anchors": result["instruction_anchor_count"],
                      "windows": len(result["windows"]), "live_execution": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
