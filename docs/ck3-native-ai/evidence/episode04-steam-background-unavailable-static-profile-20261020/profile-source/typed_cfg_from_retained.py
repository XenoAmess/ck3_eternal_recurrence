import json,hashlib,struct,datetime,os
from pathlib import Path
import capstone
from capstone.x86_const import X86_OP_IMM
r=Path("C:/ck3-e04-resume-20261020-a01/r08-steam-profile-source-2015-a01");p=r/"TRAY-CHAINED-CONTINUATION.actual-a01.json";b=p.read_bytes()
if hashlib.sha256(b).hexdigest()!="098bb1b32bc8d55fcc01082c929973a6aefa8ac7a304692d1c8c0b9347c04422":raise RuntimeError("source report changed")
d=json.loads(b);raw=bytes.fromhex("".join(x["bytes"] for x in d["instructions"]))
if len(raw)!=484 or hashlib.sha256(raw).hexdigest()!=d["source_span"]["sha256"]:raise RuntimeError("raw reconstruction incomplete")
base=0x5a28c0;table=0x5a2a8c;codeend=0x5a2a8b
targets=list(struct.unpack_from("<6I",raw,table-base))
if targets[3]!=0x5a295f:raise RuntimeError("state4 target mismatch")
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);md.detail=True
pending=[base];seen={};jumps=[];bad=[]
while pending:
 a=pending.pop()
 if a in seen:continue
 if not base<=a<codeend:bad.append(hex(a));continue
 xx=list(md.disasm(raw[a-base:],a,count=1))
 if len(xx)!=1:raise RuntimeError("decode failure")
 x=xx[0];seen[a]=x
 if x.group(capstone.CS_GRP_RET):continue
 if x.group(capstone.CS_GRP_JUMP):
  if x.operands[0].type==X86_OP_IMM:ts=[x.operands[0].imm]
  elif a==0x5a2943:ts=targets
  else:raise RuntimeError("unresolved indirect jump")
  jumps.append(dict(at=hex(a),targets=[hex(t) for t in ts]))
  pending.extend(ts)
  if x.mnemonic!="jmp":pending.append(a+x.size)
 else:pending.append(a+x.size)
if bad:raise RuntimeError("reachable edge outside code: "+str(bad))
if not any(x.mnemonic=="ret" for x in seen.values()):raise RuntimeError("no reachable return")
icon_rows=[x for x in d["instructions"] if x["rva"] in ["0x5a295f","0x5a296b"]]
candidate=dict(status="SOURCE_CANDIDATE_REQUIRES_INDEPENDENT_REVIEW_NO_RUNTIME_Q",steam_exe_version="11.12.30.7",steam_exe_sha256="7895a1a7ba04461d057fc14c47e83fcb0d6f5441682b6dfa83802324d06de347",steamui_version="11.12.30.7",steamui_bytes=19449496,steamui_sha256="1b9457943205dc3af0bd53463ba331cbd2a381388699705c02271aac7a2b1252",image_size=19730432,value_rva="0x1194ec7",current_user_object_rva="0x1194d40",getter_object_offset="0x187",tray_manager_rva="0x11932e0",tray_state_offset="0x154",anchors=[
dict(role="producer",rva="0x63ea4c",hex="440fb6057364b500488d150da37700488bcbe83d703d00"),
dict(role="getter_writer",rva="0x5f7d00",hex="40534883ec20488bd9e8c280f2ff488bc8488b10ff92880000008883870100004883c4205bc3"),
dict(role="global_refresh_caller",rva="0x6b2fff",hex="488d0d3a1dae00e8f54cf4ff"),
dict(role="offline_tray_branch",rva="0x63d524",hex="803d9c79b500007419488b0dac5db5004533c0ba04000000e87f53f6ff"),
dict(role="tray_compare",rva="0x5a28de",hex="8bfa4c8bf13b9154010000"),
dict(role="tray_store",rva="0x5a290e",hex="4189be54010000")])
out=dict(schema="xar.steam11-typed-controlflow-and-profile-candidate.v1",machine_id="desktop-3fevhd2-1c74096080",observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),basis=dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()),correction="Continuation-a01 linearly decoded pdata-tail jump-table data5A2A8C..5A2AA4 as pseudo instructions. Its all_local_jump_targets=false is not a CFG verdict. Original retained unchanged; reachable code is separately classified here.",code_range=["0x5a28c0","0x5a2a8b"],padding_range=["0x5a2a8b","0x5a2a8c"],jump_table=dict(begin="0x5a2a8c",bytes=24,hex=raw[table-base:].hex(),index="unsigned(state-1); CMP5/JA guards six entries",targets=[hex(t) for t in targets],state4_index=3,state4_target="0x5a295f"),local_cfg=dict(reachable_instructions=len(seen),unresolved_local_edges=bad,reachable_return_rvas=[hex(a) for a,x in seen.items() if x.mnemonic=="ret"],indirect_jump_resolved="5A2943 uses six static table targets",opaque_calls_not_followed=True,no_transitive_or_runtime_claim=True),offline_icon_source=icon_rows,icon_strings=["public/steam_offline","#Steam_Tooltip_Offline"],profile_candidate=candidate,current_offline_mode=None,process_memory_reads=0,mode_reads=0,run_probe_calls=0,new_DLL_body_reads=0,provider_changed=False)
payload=(json.dumps(out,separators=(",",":"))+"\n").encode()
reports=[r/x for x in ["STATIC-PROFILE-CANDIDATES.actual-a01.json","STATIC-COMPLETENESS-CORRECTION.actual-a01.json","TRAY-CHAINED-CONTINUATION.actual-a01.json"]]
if sum(x.stat().st_size for x in reports)+len(payload)>32768:raise RuntimeError("report32K")
if sum(x.stat().st_size for x in r.rglob("*") if x.is_file())+len(payload)>131072:raise RuntimeError("root128K")
o=r/"TYPED-CFG-AND-PROFILE-CANDIDATE.actual-a01.json"
with o.open("xb") as f:f.write(payload);f.flush();os.fsync(f.fileno())
print(json.dumps(dict(path=str(o),bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest(),local_cfg=out["local_cfg"],source_reports_total=sum(x.stat().st_size for x in reports)+len(payload),aggregate_bytes=sum(x.stat().st_size for x in r.rglob("*") if x.is_file())),separators=(",",":")))
