"""Verify actor-Rite strict doctrine collection and native group precedence offline."""
from __future__ import annotations
import argparse, hashlib, json, re, struct, sys
from pathlib import Path
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ck3_autonomous_player/native_bridge/research"))
from scan_anchors import PeImage

EXACT_SHA = "ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d"
MANIFEST = Path(__file__).with_name("religion_doctrine12002_rite_abi.json")
CONSTANTS = {"kRiteEffectiveDoctrineDataOffset": 0x7A0,
             "kRiteEffectiveDoctrineCapacityOffset": 0x7A8,
             "kRiteEffectiveDoctrineCountOffset": 0x7AC}
SPANS = [("CRite.HasDoctrine.reflection", 0x24FC3B0, 0x24FC498),
         ("CRite.initialize_effective_doctrines", 0x24FA130, 0x24FA716),
         ("Belief.HasDoctrineByKey.compatibility", 0x2590F10, 0x2590F82)]
SLICES = [("CRite.HasDoctrine.registration", 0x4EF689, 0x4EF727),
          ("native_pointer_array_append.layout", 0x880340, 0x88036A)]
SITES = [("actor_rite_doctrine_pointer", 0x24FC436),
         ("actor_rite_doctrine_count", 0x24FC442),
         ("actor_rite_doctrine_stride", 0x24FC449),
         ("native_pointer_membership_call", 0x24FC44D),
         ("native_pointer_membership_result", 0x24FC476),
         ("rite_doctrine_array_destination", 0x24FA1A6),
         ("existing_doctrine_pointer_array", 0x24FA233),
         ("existing_doctrine_count", 0x24FA237),
         ("existing_doctrine_stride", 0x24FA23C),
         ("existing_doctrine_group", 0x24FA2AA),
         ("faith_candidate_group", 0x24FA371),
         ("group_collision_skip", 0x24FA44C),
         ("candidate_eligibility_first", 0x24FA48A),
         ("candidate_eligibility_second", 0x24FA49E),
         ("append_eligible_candidate", 0x24FA4EE),
         ("stable_doctrine_key", 0x24FA541),
         ("compatibility_core_tenet_token", 0x2590F24),
         ("compatibility_doctrine_token", 0x2590F63),
         ("pointer_array_count", 0x880355),
         ("pointer_array_capacity", 0x88035C),
         ("reflection_registration_callback", 0x4EF717)]

def extract(exe: Path):
    data = exe.read_bytes()
    if hashlib.sha256(data).hexdigest() != EXACT_SHA:
        raise ValueError("Not the frozen CK3 1.20.0.2 EXE")
    pe = PeImage(data)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64); decoder.detail = True
    def read(rva, size):
        off = pe.rva_to_offset(rva)
        return data[off:off + size]
    header = ROOT / "ck3_autonomous_player/native_bridge/include/xar_bridge/religion_doctrine12002_rite.hpp"
    text = header.read_text(encoding="utf-8-sig")
    for name, value in CONSTANTS.items():
        match = re.search(rf"\b{name}\s*=\s*(0x[0-9a-fA-F]+)", text)
        if not match or int(match.group(1), 0) != value:
            raise ValueError("Actual reader constant differs: " + name)
    spans, dump = [], []
    for name, start, end in SPANS + SLICES:
        raw = read(start, end - start)
        spans.append({"name": name, "start_rva": hex(start), "end_exclusive_rva": hex(end),
                      "kind": "complete_function" if (name, start, end) in SPANS else "bounded_slice",
                      "bytes": raw.hex(" "), "sha256": hashlib.sha256(raw).hexdigest()})
        dump.append(f"\n{name} [{start:#x},{end:#x})")
        dump.extend(f"{ins.address:09X} {ins.bytes.hex(' '):32s} {ins.mnemonic:8s} {ins.op_str}"
                    for ins in decoder.disasm(raw, start))
    instructions = []
    for name, rva in SITES:
        ins = next(decoder.disasm(read(rva, 15), rva))
        instructions.append({"name": name, "rva": hex(rva), "bytes": ins.bytes.hex(" "),
            "instruction": f"{ins.mnemonic} {ins.op_str}",
            "direct_targets": [hex(op.imm) for op in ins.operands
                if op.type == X86_OP_IMM and ins.mnemonic in ("call", "jmp")],
            "rip_targets": [hex(ins.address + ins.size + op.mem.disp) for op in ins.operands
                if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP]})
    result = {"schema": "ck3_12002_rite_effective_doctrine_abi_v1", "game_version": "1.20.0.2",
        "executable_sha256": EXACT_SHA, "executable_size": len(data), "local_ck3_touched": False,
        "readiness": "static-confirmed", "source_constants": {k: hex(v) for k, v in CONSTANTS.items()},
        "native_spans": spans, "semantic_instructions": instructions,
        "semantic_scope": "played actor Rite actual strict effective Doctrine array",
        "identity": "full RiteID/FaithID; Doctrine/Group stable keys, no invented entity refs",
        "definition_copy_dependency": "religion_doctrine12002_intrinsic.hpp/cpp exact ABI",
        "not_claimed": ["authored row provenance after native merging", "full creation/edit legality",
                        "DoctrineByKey compatibility includes Tenets", "live verification"]}
    return result, "\n".join(dump) + "\n"

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exe", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--record", action="store_true")
    a = p.parse_args(); result, dump = extract(a.exe)
    if a.record:
        MANIFEST.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    elif json.loads(MANIFEST.read_text(encoding="utf-8")) != result:
        raise ValueError("Recorded exact ABI differs")
    a.output_dir.mkdir(parents=True, exist_ok=True)
    (a.output_dir / "native-disassembly.txt").write_text(dump, encoding="utf-8")
    receipt = {"status": "GREEN", "local_ck3_touched": False, "live_verified": False,
        "complete_functions": len(SPANS), "bounded_slices": len(SLICES),
        "semantic_instructions": len(SITES), "provider_constants": len(CONSTANTS),
        "manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
        "disassembly_sha256": hashlib.sha256(dump.encode()).hexdigest()}
    (a.output_dir / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
