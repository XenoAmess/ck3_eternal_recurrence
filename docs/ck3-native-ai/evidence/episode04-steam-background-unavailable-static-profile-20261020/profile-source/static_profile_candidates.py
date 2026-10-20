import sys,os,json,time,hashlib,struct,re,bisect,datetime,ctypes
from pathlib import Path
import capstone
ROOT=Path("C:/ck3-e04-resume-20261020-a01/r08-steam-profile-source-2015-a01")
OUTPUT=ROOT/"STATIC-PROFILE-CANDIDATES.actual-a01.json"
start=time.monotonic()
if len(sys.argv)!=3:raise RuntimeError("exact extension capacity path and SHA required")
cap=Path(sys.argv[1]);capbytes=cap.read_bytes()
if hashlib.sha256(capbytes).hexdigest()!=sys.argv[2]:raise RuntimeError("extension capacity changed")
if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime(2026,10,20,20,15,tzinfo=datetime.timezone.utc):raise RuntimeError("scope deadline")
old=ROOT/"FILE-SOURCE-DIAGNOSTIC.actual-a01.json";oldbytes=old.read_bytes()
if hashlib.sha256(oldbytes).hexdigest()!="3b35f902057cf8603a4a4a90e613886d92f8a1a930ac91f3fe8368fb7956770e":raise RuntimeError("prior diagnostic changed")
prior=json.loads(oldbytes);expected=prior["files"][1];p=Path(expected["path"])
stamp=lambda p:(p.stat().st_size,p.stat().st_mtime_ns,p.stat().st_ino,p.stat().st_dev)
before=stamp(p)
oldstat=expected["path_identity_after"]
if before!=(oldstat["bytes"],oldstat["mtime_ns"],oldstat["ino"],oldstat["dev"]):raise RuntimeError("bound source stat changed")
data=p.read_bytes()
digest=hashlib.sha256(data).hexdigest()
if len(data)!=19449496 or digest!="1b9457943205dc3af0bd53463ba331cbd2a381388699705c02271aac7a2b1252":raise RuntimeError("exact source mismatch")
if stamp(p)!=before:raise RuntimeError("source changed during body read")
po=struct.unpack_from("<I",data,0x3c)[0];n=struct.unpack_from("<H",data,po+6)[0];opt=struct.unpack_from("<H",data,po+20)[0]
sections=[]
for i in range(n):
 a=struct.unpack_from("<8sIIIIIIHHI",data,po+24+opt+i*40)
 sections.append(dict(name=a[0].split(b"\0")[0].decode(),vsize=a[1],rva=a[2],rawsize=a[3],raw=a[4]))
def off(rva,length=1):
 for s in sections:
  if s["rva"]<=rva and rva+length<=s["rva"]+s["rawsize"]:return s["raw"]+rva-s["rva"]
 raise RuntimeError("RVA has no exact file-backed span: "+hex(rva))
def rva(raw):
 for s in sections:
  if s["raw"]<=raw<s["raw"]+s["rawsize"]:return s["rva"]+raw-s["raw"]
 raise RuntimeError("raw offset outside sections")
text=next(x for x in sections if x["name"]==".text")
code=data[text["raw"]:text["raw"]+text["rawsize"]];base=text["rva"]
pd=next(x for x in sections if x["name"]==".pdata")
funcs=[struct.unpack_from("<III",data,pd["raw"]+i) for i in range(0,pd["rawsize"]-11,12)]
funcs=[x for x in funcs if x[0]<x[1] and base<=x[0]<base+len(code)];funcs.sort();begins=[x[0] for x in funcs]
def function(address):
 i=bisect.bisect_right(begins,address)-1
 if i>=0 and address<funcs[i][1]:return funcs[i]
 return None
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
used={}
def snippet(address,length,role):
 f=function(address);end=min(address+length,f[1] if f else address+length)
 key=f[0] if f else address
 available=4096-used.get(key,0)
 length=min(end-address,available)
 if length<=0:return dict(role=role,rva=hex(address),status="PER_FUNCTION_4K_STOP")
 raw=data[off(address,length):off(address,length)+length];used[key]=used.get(key,0)+length
 ins=[dict(rva=hex(x.address),bytes=x.bytes.hex(),mnemonic=x.mnemonic,operands=x.op_str) for x in md.disasm(raw,address)]
 return dict(role=role,rva=hex(address),read_bytes=length,sha256=hashlib.sha256(raw).hexdigest(),function=[hex(x) for x in f] if f else None,complete_function=bool(f and address==f[0] and length==f[1]-f[0]),decoded_bytes=sum(len(bytes.fromhex(x["bytes"])) for x in ins),instructions=ins)
strings=[]
pos=0
while True:
 pos=data.find(b"bIsOfflineMode\0",pos)
 if pos<0:break
 strings.append(dict(raw_offset=pos,rva=rva(pos)));pos+=1
 if len(strings)>16:raise RuntimeError("string occurrence bound")
targets={x["rva"] for x in strings}
leas=[]
for m in re.finditer(rb"[\x48\x4c]\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]....",code,re.S):
 a=base+m.start();target=a+7+struct.unpack_from("<i",m.group(),3)[0]
 leas.append((a,target,m.group()))
refs=[x for x in leas if x[1] in targets]
if len(refs)>16:raise RuntimeError("producer xref bound")
producers=[]
for a,target,hx in refs:
 found=[]
 for j in range(max(0,a-base-64),a-base):
  if code[j:j+4]==b"\x44\x0f\xb6\x05" and j+8<=a-base:
   pc=base+j;value=pc+8+struct.unpack_from("<i",code,j+4)[0]
   found.append(dict(producer_rva=pc,value_rva=value,relative_to_string_lea=a-pc,snippet=snippet(pc,min(128,a-pc+80),"named_current_user_bool_producer_candidate")))
 producers.append(dict(string_rva=target,lea_rva=a,lea_hex=hx.hex(),preceding_movzx_candidates=found))
getter_pattern=rb"\x40\x53\x48\x83\xec\x20\x48\x8b\xd9\xe8....\x48\x8b\xc8\x48\x8b\x10\xff\x92....\x88\x83....\x48\x83\xc4\x20\x5b\xc3"
getters=[]
for m in re.finditer(getter_pattern,code,re.S):
 b=m.group();a=base+m.start()
 getters.append(dict(rva=a,interface_getter_call_target=a+14+struct.unpack_from("<i",b,10)[0],virtual_slot=struct.unpack_from("<I",b,22)[0],store_offset=struct.unpack_from("<I",b,28)[0],bytes=b.hex()))
 if len(getters)>64:raise RuntimeError("getter pattern bound")
chains=[]
for prod in producers:
 for z in prod["preceding_movzx_candidates"]:
  value=z["value_rva"]
  for g in getters:
   obj=value-g["store_offset"];callers=[]
   for a,t,hx in leas:
    i=a-base+7
    if t==obj and hx[:3]==b"\x48\x8d\x0d" and code[i:i+1]==b"\xe8" and i+5<=len(code):
     callee=base+i+5+struct.unpack_from("<i",code,i+1)[0]
     if callee==g["rva"]:callers.append(dict(rva=a,object_rva=obj,snippet=snippet(a,32,"same_global_object_refresh_caller")))
   if callers:
    chains.append(dict(producer_rva=z["producer_rva"],value_rva=value,global_object_rva=obj,getter=g,caller_candidates=callers,getter_source=snippet(g["rva"],38,"private_getter_field_write_candidate")))
trays=[]
for c in chains:
 value=c["value_rva"]
 for m in re.finditer(rb"\x80\x3d....\x00",code,re.S):
  a=base+m.start();referenced=a+7+struct.unpack_from("<i",m.group(),2)[0]
  if referenced!=value:continue
  # Only fixed current-user byte xrefs; inspect a small instruction-aligned window.
  fpeek=function(a);peekkey=fpeek[0] if fpeek else a
  if used.get(peekkey,0)+96>4096:raise RuntimeError("per_function4K_peek_stop")
  used[peekkey]=used.get(peekkey,0)+96
  ins=list(md.disasm(code[m.start():m.start()+96],a))
  four=next((x for x in ins if x.mnemonic=="mov" and x.op_str=="edx, 4"),None)
  if four is None:continue
  call=next((x for x in ins if x.address>four.address and x.mnemonic=="call" and x.op_str.startswith("0x")),None)
  if call is None:continue
  target=int(call.op_str,16)
  manager=[]
  for x in ins:
   if x.address>=four.address:break
   b=x.bytes
   if len(b)==7 and b[:3]==b"\x48\x8b\x0d":manager.append(x.address+7+struct.unpack_from("<i",b,3)[0])
  tf=function(target);length=min(512,tf[1]-target if tf else 512)
  trays.append(dict(branch_rva=a,value_rva=value,manager_pointer_rva_candidates=manager,edx4_rva=four.address,call_rva=call.address,callee_rva=target,branch_source=snippet(a,96,"offline_tray_state4_branch_candidate"),callee_source=snippet(target,length,"tray_compare_store_candidate_first512")))
  if len(trays)>8:raise RuntimeError("tray candidates bound")
out=dict(schema="xar.steam11-file-static-source-candidates.v1",machine_id="desktop-3fevhd2-1c74096080",observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status="CANDIDATES_ONLY_NOT_RUNTIME_QUALIFIED",input=dict(path=str(p),bytes=len(data),sha256=digest,before=before,after=stamp(p),identity_stable=stamp(p)==before),extension_capacity=dict(path=str(cap),bytes=len(capbytes),sha256=hashlib.sha256(capbytes).hexdigest()),root_continuation_authority="Root explicitly authorized same-purpose static pattern/bounded decode under unchanged exact two files/root128KiB/20:15; no new financial delta card required; prior cap/provider/a01 immutable",capstone_version=capstone.__version__,strings=strings,producer_xrefs=producers,getter_pattern_match_count=len(getters),same_object_source_chains=chains,tray_state4_candidates=trays,per_function_code_bytes={hex(k):v for k,v in used.items()},process_memory_reads=0,mode_observations=0,run_probe_calls=0,provider_or_allowlist_changes=0)
if time.monotonic()-start>115:raise RuntimeError("bounded_wallclock_stop")
payload=(json.dumps(out,separators=(",",":"))+"\n").encode()
if len(payload)>32768:raise RuntimeError("report32KiB_stop_no_output")
total=sum(x.stat().st_size for x in ROOT.rglob("*") if x.is_file())
if total+len(payload)>131072:raise RuntimeError("aggregate128KiB_stop")
with OUTPUT.open("xb") as f:f.write(payload);f.flush();os.fsync(f.fileno())
rb=OUTPUT.read_bytes()
print(json.dumps(dict(path=str(OUTPUT),bytes=len(rb),sha256=hashlib.sha256(rb).hexdigest(),strings=strings,producer_xrefs=len(refs),getter_candidates=len(getters),source_chains=len(chains),tray_candidates=len(trays),elapsed_seconds=round(time.monotonic()-start,3),aggregate_bytes=total+len(rb)),separators=(",",":")))
