#!/usr/bin/env python3
"""Exact-file native proof for CK3 1.20.0.2 effective boolean parameters."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ck3_autonomous_player/native_bridge/research"))
from scan_anchors import PeImage

EXACT_SHA = "ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d"
MANIFEST = Path(__file__).with_name("religion_doctrine12002_tenet_abi.json")
HEADER = ROOT / "ck3_autonomous_player/native_bridge/include/xar_bridge/religion_doctrine12002_tenet.hpp"
CONSTANTS = {"kBooleanParameterMembershipRva": 0xB9DE80, "kParameterTokenKeyRva": 0x3F4F900,
             "kRiteBooleanParameterOffset": 0x7B8, "kArrayDataOffset": 0, "kArrayCountOffset": 0xC}
SPANS = [
    ("Faith.has_doctrine_parameter.evaluate", 0x2B29170, 0x2B2921E),
    ("Rite.rite_has_parameter.evaluate", 0x2AE9F70, 0x2AE9FDE),
    ("sorted_boolean_token_membership.complete_chained_body", 0xB9DE80, 0xB9DF06),
    ("token_to_actual_CString", 0x3F4F900, 0x3F4FA24),
    ("TenetDoctrineContainer.rebuild", 0x2591180, 0x2591694),
    ("TokenParameter.bool_typed_access", 0x22C80F0, 0x22C8194),
    ("TokenParameter.number_typed_access", 0x22C81A0, 0x22C8259),
]
SITES = [0x2B291CC, 0x2B29209, 0x2B29214, 0x2AE9FC9, 0x2AE9FD4,
         0xB9DE84, 0xB9DE8A, 0xB9DEA6, 0xB9DEB9, 0xB9DEE8,
         0x3F4F94E, 0x3F4F954, 0x3F4F958,
         0x25911DD, 0x2591331, 0x2591346, 0x2591350,
         0x25913D1, 0x25913F7, 0x2591401,
         0x22C80F4, 0x22C818B, 0x22C81A6, 0x22C8249]

def extract(exe: Path) -> tuple[dict, str]:
    data = exe.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != EXACT_SHA: raise ValueError("Frozen 1.20.0.2 executable SHA differs")
    pe = PeImage(data)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    def read(rva: int, size: int) -> bytes:
        o = pe.rva_to_offset(rva); return data[o:o+size]
    header = HEADER.read_text(encoding="utf-8-sig")
    for name, value in CONSTANTS.items():
        match = re.search(rf"\b{name}\s*=\s*(0x[0-9a-fA-F]+)", header)
        if not match or int(match.group(1), 0) != value:
            raise ValueError(f"Actual provider constant differs: {name}")
    spans, dump = [], []
    for name, start, end in SPANS:
        raw = read(start, end-start)
        spans.append({"name": name, "start_rva": hex(start), "end_exclusive_rva": hex(end),
                      "sha256": hashlib.sha256(raw).hexdigest(), "bytes": raw.hex(" ")})
        dump.append(f"\n{name} [{start:#x},{end:#x})")
        dump.extend(f"{i.address:09X} {i.bytes.hex(' '):32s} {i.mnemonic:8s} {i.op_str}"
                    for i in decoder.disasm(raw, start))
    instructions = []
    for rva in SITES:
        i = next(decoder.disasm(read(rva, 15), rva))
        instructions.append({"rva": hex(rva), "bytes": i.bytes.hex(" "),
                             "instruction": f"{i.mnemonic} {i.op_str}"})
    rtti = []
    for cls in ("CHasDoctrineParameterTrigger", "CRiteHasParameterTrigger", "CTenetDoctrineContainer",
                "CTenetTypeDatabase", "CDoctrineTypeDatabase"):
        text = f".?AV{cls}@@".encode()+b"\0"
        position = data.find(text)
        if position < 0 or data.find(text, position+1) >= 0:
            raise ValueError(f"Exact class RTTI not unique: {cls}")
        rtti.append({"class": cls, "type_descriptor_rva": hex(pe.offset_to_rva(position)-16)})
    vtables = []
    for name, rva, slot, function in [("Faith.has_doctrine_parameter",0x47BA968,25,0x2B29170),
                                     ("Rite.rite_has_parameter",0x4785288,25,0x2AE9F70)]:
        raw = read(rva+slot*8,8)
        import struct
        if struct.unpack("<Q",raw)[0]-pe.image_base != function:
            raise ValueError(f"Actual trigger vtable differs: {name}")
        vtables.append({"name":name,"vtable_rva":hex(rva),"slot":slot,"evaluate_rva":hex(function)})
    result = {"schema":"ck3_12002_rite_boolean_parameters_abi_v1","game_version":"1.20.0.2",
              "executable_sha256":digest,"executable_size":len(data),"readiness":"static-confirmed",
              "local_ck3_touched":False,"live_verified":False,
              "provider_constants":{k:hex(v) for k,v in CONSTANTS.items()},
              "complete_native_spans":spans,"semantic_instructions":instructions,
              "class_rtti":rtti,"trigger_vtables":vtables,
              "known":"Faith parameter scope reads main Rite; actor Rite source kept separately",
              "unresolved":["numeric effective parameter merge/evaluation","Core/personal Tenet row production reader"]}
    return result,"\n".join(dump)+"\n"

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exe",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--record",action="store_true")
    a=p.parse_args();result,dump=extract(a.exe)
    if a.record: MANIFEST.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    elif json.loads(MANIFEST.read_text(encoding="utf-8"))!=result:
        raise ValueError("Frozen ABI manifest differs from exact PE extraction")
    a.output_dir.mkdir(parents=True,exist_ok=True)
    (a.output_dir/"native-disassembly.txt").write_text(dump,encoding="utf-8")
    receipt={"status":"GREEN","readiness":"static-confirmed","local_ck3_touched":False,"live_verified":False,
             "executable_sha256":EXACT_SHA,"complete_native_spans":len(SPANS),
             "semantic_instructions":len(SITES),"class_rtti":len(result["class_rtti"]),
             "trigger_vtables":len(result["trigger_vtables"]),
             "manifest_sha256":hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
             "disassembly_sha256":hashlib.sha256(dump.encode()).hexdigest()}
    (a.output_dir/"native-verification.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(receipt,indent=2));return 0
if __name__=="__main__": raise SystemExit(main())
