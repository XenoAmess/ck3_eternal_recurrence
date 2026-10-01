"""Frozen-file verification of the nonwar CK3 AI reform caller and state getter.

Reads the exact PE and selected stock lines only. No CK3/Steam/process/UI access.
"""
from __future__ import annotations
import argparse, hashlib, json, re, struct
from pathlib import Path
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP
from scan_anchors import PeImage

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SHA = "ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d"
MAP = HERE / "religion_reform12002_willingness_abi.json"
HEADER = HERE.parent / "include/xar_bridge/religion_reform12002_willingness.hpp"
SPANS = [
    ("native_ai_reform_handler",0x1A9D890,0x1A9DA1F),
    ("Faith.IsUnreformed",0x2BD8960,0x2BD89B6),
    ("Faith.GetMainRite",0x2444360,0x244439D),
    ("Faith.IsUnreformed.reflection",0x2444600,0x2444635),
    ("Faith.default_draft.mode_1",0x2BDB1A0,0x2BDB2C8),
    ("CCreateRiteCommand.owning_clone",0x29A7030,0x29A70C2),
    ("AI.ToggleReligiousReformation.registration",0x337820,0x3379F8),
]
SLICES = [
    ("rare_dispatch.reform_only",0x19E87C8,0x19E87D9),
    ("rare_queue.callsite",0x1A3219C,0x1A32246),
    ("Faith.IsUnreformed.registration",0x4D5B19,0x4D5BB7),
    ("profiler.enum_22_label",0x24B82BF,0x24B82C7),
]
SITES = [
    ("ai_bit_0_required",0x1A9D899),
    ("ai_bit_6_required",0x1A9D8A3),
    ("ai_special_state_zero",0x1A9D8B2),
    ("ai_actor_pointer",0x1A9D8BC),
    ("character_rite_full_id",0x1A9D8CC),
    ("rite_faith_full_id",0x1A9D900),
    ("native_unreformed_call",0x1A9D943),
    ("default_draft_mode_1",0x1A9D950),
    ("default_draft_call",0x1A9D961),
    ("actor_full_id",0x1A9D967),
    ("command_vtable",0x1A9D97A),
    ("draft_copy_call",0x1A9D99E),
    ("final_can_execute",0x1A9D9B8),
    ("final_gate_result",0x1A9D9BF),
    ("clone_virtual_40",0x1A9D9D3),
    ("queue_priority_7",0x1A9D9E5),
    ("owning_queue_call",0x1A9D9F0),
    ("faith_main_rite_full_id",0x2BD897B),
    ("native_main_rite_full_generation",0x2BD89A1),
    ("native_main_rite_unreformed_bool",0x2BD89AE),
    ("reflection_bool_call",0x2444611),
    ("reflection_registration_callback",0x4D5BA7),
    ("AI_toggle_global",0x3378E8),
    ("rare_toggle_comparison",0x19E87C8),
    ("rare_handler_call",0x19E87D4),
    ("rare_queue_actor_loop",0x1A32234),
    ("clone_allocation_778",0x29A704A),
    ("clone_actor_id",0x29A7098),
]
SOURCE_BINDINGS = {
    "kFaithMainRiteGetterRva":0x2444360,
    "kFaithIsUnreformedGetterRva":0x2BD8960,
    "kFaithMainRiteIdOffset":0x98,
    "kObjectFullReferenceOffset":8,
    "kRiteUnreformedOffset":0x8B0,
}
STOCK = {
    "common/on_action/religion_on_actions.txt":[(3,17),(207,225),(390,436),(483,537),(563,572),(694,701)],
    "common/scripted_effects/00_religion_effects.txt":[(338,344)],
    "common/script_values/02_religion_values.txt":[(4805,4806)],
}
def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exe",required=True,type=Path)
    p.add_argument("--game",required=True,type=Path)
    p.add_argument("--output-dir",required=True,type=Path)
    p.add_argument("--record",action="store_true")
    a=p.parse_args(); data=a.exe.read_bytes()
    if hashlib.sha256(data).hexdigest()!=SHA:raise ValueError("Exact EXE differs")
    pe=PeImage(data);cs=Cs(CS_ARCH_X86,CS_MODE_64);cs.detail=True
    def read(rva,n):off=pe.rva_to_offset(rva);return data[off:off+n]
    source=HEADER.read_text(encoding="utf-8-sig")
    for name,expected in SOURCE_BINDINGS.items():
        m=re.search(rf"\b{name}\s*=\s*(0x[0-9A-Fa-f]+)",source)
        if not m or int(m[1],0)!=expected:raise ValueError(name)
    spans=[];dump=[]
    for name,start,end in SPANS+SLICES:
        raw=read(start,end-start)
        spans.append({"name":name,"start_rva":hex(start),"end_exclusive_rva":hex(end),
                      "kind":"complete_function" if (name,start,end) in SPANS else "slice",
                      "sha256":hashlib.sha256(raw).hexdigest(),"bytes":raw.hex(" ")})
        dump.append(f"{name} [{start:#x},{end:#x})")
        dump.extend(f"{i.address:09X} {i.bytes.hex(' '):36s} {i.mnemonic} {i.op_str}" for i in cs.disasm(raw,start))
    instructions=[]
    for name,rva in SITES:
        i=next(cs.disasm(read(rva,15),rva))
        instructions.append({"name":name,"rva":hex(rva),"bytes":i.bytes.hex(" "),
                             "instruction":f"{i.mnemonic} {i.op_str}",
                             "rip_targets":[hex(i.address+i.size+o.mem.disp) for o in i.operands if o.type==X86_OP_MEM and o.mem.base==X86_REG_RIP],
                             "direct_targets":[hex(o.imm) for o in i.operands if o.type==X86_OP_IMM and i.mnemonic in ("call","jmp")]})
    semantic={r["name"]:r for r in instructions}
    for name,target in [("native_unreformed_call",0x2BD8960),("default_draft_call",0x2BDB1A0),
                        ("draft_copy_call",0x29A1F10),("final_can_execute",0x29A2F60),
                        ("owning_queue_call",0x37EBC40),("reflection_bool_call",0x2BD8960),
                        ("rare_handler_call",0x1A9D890),("rare_queue_actor_loop",0x19E8780)]:
        if semantic[name]["direct_targets"]!=[hex(target)]:raise ValueError(name)
    if semantic["AI_toggle_global"]["rip_targets"]!=["0x5448579"] or semantic["rare_toggle_comparison"]["rip_targets"]!=["0x5448579"]:
        raise ValueError("console toggle and actual AI gate disagree")
    if semantic["reflection_registration_callback"]["rip_targets"]!=["0x2444600"]:
        raise ValueError("IsUnreformed callback binding")
    # Registration copies the literal in 8+4 byte slices; no direct LEA exists.
    if read(0x472FD18,13)!=b"IsUnreformed\0":raise ValueError("reflection name")
    vtable={"rva":"0x4770550","validator_slot":"0x30","validator_rva":"0x29a2f60",
            "clone_slot":"0x40","clone_rva":"0x29a7030"}
    for offset,target in [(0x30,0x29A2F60),(0x40,0x29A7030)]:
        if struct.unpack('<Q',read(0x4770550+offset,8))[0]-pe.image_base!=target:raise ValueError("command vtable")
    stock=[];stock_dump=[]
    for rel,ranges in STOCK.items():
        path=a.game/rel;lines=path.read_text(encoding="utf-8-sig").splitlines()
        stock.append({"path":rel,"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"ranges":ranges})
        stock_dump.append(rel)
        for first,last in ranges:
            if not 1<=first<=last<=len(lines):raise ValueError(rel)
            stock_dump.extend(f"{n+1}: {lines[n]}" for n in range(first-1,last))
    result={"schema":"ck3_12002_religion_reform_willingness_research_v1","executable_sha256":SHA,
            "game_version":"1.20.0.2","readiness":"static-confirmed","local_ck3_touched":False,
            "native_spans":spans,"semantic_instructions":instructions,"command_vtable":vtable,
            "reflection_name":{"rva":"0x472fd18","literal":"IsUnreformed"},
            "source_bindings":{k:hex(v) for k,v in SOURCE_BINDINGS.items()},"stock_sources":stock,
            "unresolved":["AI masks semantic names", "Rare queue scheduling period and membership",
                          "general non-unreformed AI Rite creation", "native outcome hook dispatch and independent post-action readback"]}
    # JSON round trip makes recorded stock ranges stable lists rather than tuples.
    result=json.loads(json.dumps(result))
    if a.record:MAP.write_text(json.dumps(result,indent=2)+"\n",encoding="utf8")
    elif json.loads(MAP.read_text(encoding="utf8"))!=result:raise ValueError("reviewed ABI differs")
    a.output_dir.mkdir(parents=True,exist_ok=True)
    native_output=a.output_dir/'native-disassembly.txt';native_output.write_text('\n'.join(dump)+'\n',encoding='utf8')
    stock_output=a.output_dir/'stock-evidence.txt';stock_output.write_text('\n'.join(stock_dump)+'\n',encoding='utf8')
    receipt={"status":"GREEN","readiness":"static-confirmed","local_ck3_touched":False,"live_verified":False,
             "complete_functions":len(SPANS),"slices":len(SLICES),"semantic_instructions":len(SITES),
             "exact_executable_sha256":SHA,"abi_manifest_sha256":hashlib.sha256(MAP.read_bytes()).hexdigest(),
             "artifacts":{x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in [native_output,stock_output]}}
    (a.output_dir/'abi-verification.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
    print(json.dumps(receipt,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
