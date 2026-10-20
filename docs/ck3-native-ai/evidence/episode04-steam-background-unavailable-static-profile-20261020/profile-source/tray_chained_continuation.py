import json,struct,hashlib,datetime,os
from pathlib import Path
import capstone
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP
r=Path("C:/ck3-e04-resume-20261020-a01/r08-steam-profile-source-2015-a01")
diag=json.loads((r/"FILE-SOURCE-DIAGNOSTIC.actual-a01.json").read_text())
oldp=r/"STATIC-PROFILE-CANDIDATES.actual-a01.json";oldbytes=oldp.read_bytes()
if hashlib.sha256(oldbytes).hexdigest()!="813c36b61ed3caeb393843e5302bb52c31295392ea54438076bed81a44f7b30b":raise RuntimeError("old report changed")
old=json.loads(oldbytes);inp=diag["files"][1];p=Path(inp["path"]);before=p.stat();prior=inp["path_identity_after"]
identity=lambda s:(s.st_size,s.st_mtime_ns,s.st_ino,s.st_dev)
if identity(before)!=(prior["bytes"],prior["mtime_ns"],prior["ino"],prior["dev"]):raise RuntimeError("source identity changed")
sections=inp["pe"]["sections"]
def section(a):
 return next(s for s in sections if s["rva"]<=a<s["rva"]+s["raw_size"])
def off(a):
 s=section(a);return s["raw_offset"]+a-s["rva"]
prefix=bytes.fromhex("".join(x["bytes"] for x in old["tray_state4_candidates"][0]["callee_source"]["instructions"]))
if len(prefix)!=73:raise RuntimeError("prior prefix incomplete")
with p.open("rb") as f:
 f.seek(off(0x5a2909));tail=f.read(0x5a2aa4-0x5a2909)
 if len(tail)!=411:raise RuntimeError("short continuation")
 raw=prefix+tail
 pd=next(s for s in sections if s["name"]==".pdata")
 chain=[]
 for index in [39643,39644,39645]:
  f.seek(pd["raw_offset"]+12*index);entry=f.read(12);a,b,u=struct.unpack("<III",entry)
  f.seek(off(u));h=f.read(4);total=4+((h[2]+1)&~1)*2+(12 if h[0]>>3&4 else 0)
  f.seek(off(u));unwind=f.read(total)
  chain.append(dict(index=index,begin=hex(a),end=hex(b),unwind_rva=hex(u),flags=h[0]>>3,entry_hex=entry.hex(),unwind_hex=unwind.hex()))
 if [(x["begin"],x["end"]) for x in chain]!=[("0x5a28c0","0x5a2909"),("0x5a2909","0x5a2a76"),("0x5a2a76","0x5a2aa4")]:raise RuntimeError("extent changed")
 md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);md.detail=True
 ins=list(md.disasm(raw,0x5a28c0))
 rows=[dict(rva=hex(x.address),bytes=x.bytes.hex(),mnemonic=x.mnemonic,operands=x.op_str) for x in ins]
 branches=[];calls=[];strings=[]
 for x in ins:
  if x.group(capstone.CS_GRP_JUMP):
   target=x.operands[0].imm if x.operands and x.operands[0].type==X86_OP_IMM else None
   branches.append(dict(at=hex(x.address),kind=x.mnemonic,target=hex(target) if target is not None else None,local=target is not None and 0x5a28c0<=target<0x5a2aa4))
  if x.group(capstone.CS_GRP_CALL):calls.append(dict(at=hex(x.address),target=x.op_str,transitive_source_not_read=True))
  if x.mnemonic=="lea":
   for op in x.operands:
    if op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP:
     target=x.address+x.size+op.mem.disp
     try:
      if section(target)["name"]!=".rdata":continue
      f.seek(off(target));b=f.read(96);s=b.split(b"\0")[0]
      if len(s)>=3 and all(32<=z<127 for z in s):strings.append(dict(at=hex(x.address),target_rva=hex(target),ascii=s.decode("ascii")))
     except (StopIteration,ValueError):pass
after=p.stat()
if identity(after)!=identity(before):raise RuntimeError("source changed")
out=dict(schema="xar.steam11-tray-chained-source-continuation.v1",machine_id="desktop-3fevhd2-1c74096080",observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status="STATIC_SOURCE_CANDIDATE_NOT_RUNTIME_QUALIFICATION",source=dict(path=str(p),retained_sha256=inp["sha256"],identity_before=identity(before),identity_after=identity(after)),original_report=dict(path=str(oldp),bytes=len(oldbytes),sha256=hashlib.sha256(oldbytes).hexdigest()),correction="Original complete_function=true was a pdata-segment heuristic error. These chained extents plus actual decoded control flow are separate facts.",source_span=dict(begin="0x5a28c0",end_exclusive="0x5a2aa4",bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),prefix_reused_bytes=len(prefix),new_file_code_bytes=len(tail)),pdata_chain=chain,instructions=rows,decoded_bytes=sum(x.size for x in ins),all_local_jump_targets_in_span=all(x["local"] for x in branches),branches=branches,calls=calls,ret_rvas=[hex(x.address) for x in ins if x.mnemonic.startswith("ret")],state154_writes=[x for x in rows if x["mnemonic"]=="mov" and "0x154]" in x["operands"]],rdata_strings=strings,Root_authority="same open profile128/20:15; correction plus finite continuation to actual write/return; no old file overwrite",mode_observations=0,process_memory_reads=0,run_probe_calls=0,provider_changes=0)
b=(json.dumps(out,separators=(",",":"))+"\n").encode()
source_reports=sum(z.stat().st_size for z in [oldp,r/"STATIC-COMPLETENESS-CORRECTION.actual-a01.json"])
if len(b)+source_reports>32768:raise RuntimeError("combined source report32KiB_stop")
if sum(z.stat().st_size for z in r.rglob("*") if z.is_file())+len(b)>131072:raise RuntimeError("scope128KiB_stop")
o=r/"TRAY-CHAINED-CONTINUATION.actual-a01.json"
with o.open("xb") as f:f.write(b);f.flush();os.fsync(f.fileno())
print(json.dumps(dict(path=str(o),bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),state154_writes=out["state154_writes"],ret_rvas=out["ret_rvas"],local_branches=out["all_local_jump_targets_in_span"],rdata_strings=strings,aggregate_bytes=sum(z.stat().st_size for z in r.rglob("*") if z.is_file())),separators=(",",":")))
