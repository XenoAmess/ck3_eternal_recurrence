"""Bounded retained-byte proof for this exact 1118-byte native parent.

Default checks byte coverage/recorded instruction boundaries and decodes direct
relative control edges with stdlib. --independent-decode additionally rebuilds
the boundaries with installed Capstone; neither mode reads EXE/process memory.
"""
from pathlib import Path
import argparse,copy,hashlib,json
HERE=Path(__file__).resolve().parent
START=0x28F7840;END=0x28F7C9E;SETTLEMENT=0x28F7934
CRITICAL={0x28F7850:"488bea",0x28F7931:"488bcd",SETTLEMENT:"e8d7f3faff",
 0x28F7AD5:"e8a682fcff",0x28F7C30:"e82bc33100"}
def need(ok,why):
 if not ok:raise ValueError(why)
def edges(raw,rows):
 table={r[0]:r for r in rows};need(len(table)==len(rows),"Duplicate instruction boundary")
 cursor=START;graph={};calls={};returns=[]
 for address,size,hexbytes,mnemonic,operands in rows:
  b=bytes.fromhex(hexbytes)
  need(address==cursor and len(b)==size and raw[address-START:address-START+size]==b,"Instruction/raw coverage differs")
  cursor+=size;nextpc=address+size;target=None
  if b[0]==0xE8:
   need(mnemonic=="call" and size==5,"Direct CALL boundary differs")
   calls[address]=nextpc+int.from_bytes(b[1:],"little",signed=True);out=[nextpc]
  elif b[0] in (0xE9,0xEB):
   need(mnemonic=="jmp" and size in (2,5),"Direct JMP boundary differs")
   target=nextpc+int.from_bytes(b[1:],"little",signed=True);out=[target]
  elif 0x70<=b[0]<=0x7F or b[:1]==b"\x0f" and len(b)>1 and 0x80<=b[1]<=0x8F:
   need(mnemonic.startswith("j") and mnemonic!="jmp" and size in (2,6),"Jcc boundary differs")
   target=nextpc+int.from_bytes(b[1:] if size==2 else b[2:],"little",signed=True);out=[target,nextpc]
  elif mnemonic=="ret":
   need(b[0] in (0xC3,0xC2),"RET bytes differ");returns.append(address);out=[]
  else:
   need(mnemonic not in ("call","jmp") and not mnemonic.startswith("j"),"Unmodeled indirect control edge")
   need(mnemonic not in ("loop","loope","loopne","jrcxz"),"Unmodeled loop edge");out=[nextpc]
  graph[address]=out
 need(cursor==END,"Full parent extent incomplete")
 need(all(q in graph for out in graph.values() for q in out),"Own-body branch escapes extent or boundary")
 return graph,calls,returns
def reachable(graph,start,target,blocked=None):
 todo=[start];seen=set()
 while todo:
  pc=todo.pop()
  if pc==blocked or pc in seen:continue
  if pc==target:return True
  seen.add(pc);todo.extend(graph[pc])
 return False
def analyze(raw,rows):
 graph,calls,returns=edges(raw,rows);normal_counts=set();todo=[(START,0)];seen=set()
 while todo:
  pc,count=todo.pop();count=min(2,count+int(pc==SETTLEMENT))
  if (pc,count) in seen:continue
  seen.add((pc,count))
  if pc in returns:normal_counts.add(count)
  else:todo.extend((n,count) for n in graph[pc])
 need(calls.get(SETTLEMENT)==0x28A6D10,"Settlement target changed")
 getter_calls={"top_liege":[p for p,t in calls.items() if t==0x28BFD80],
  "current_maintenance":[p for p,t in calls.items() if t==0x2C13F60]}
 return {"normal_return_settlement_counts":sorted(normal_counts),
  "exactly_once_on_all_own_body_normal_paths":normal_counts=={1},
  "direct_calls_before_settlement":[p for p in calls if p<SETTLEMENT],
  "getter_calls":getter_calls,
  "getter_can_reach_earlier_settlement":{k:any(reachable(graph,p,SETTLEMENT) for p in ps) for k,ps in getter_calls.items()},
  "getter_reachable_without_settlement":{k:any(reachable(graph,START,p,SETTLEMENT) for p in ps) for k,ps in getter_calls.items()},
  "entry_character_saved_RDX_and_passed_as_RCX":raw[0x28F7850-START:0x28F7853-START]==bytes.fromhex("488bea")
    and raw[0x28F7931-START:SETTLEMENT-START]==bytes.fromhex("488bcd")}
def verify(path,*,independent_decode=False,counterexample=False):
 proof=json.loads(Path(path).read_bytes());raw=bytes.fromhex(proof["body_hex"]);rows=proof["instructions"]
 need(proof["game_version"]=="1.20.0.4" and proof["steam_build_id"]==25734779
      and proof["exe_sha256"]=="98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518","Original source image binding changed")
 need(len(raw)==1118 and hashlib.sha256(raw).hexdigest()=="c115401592983d13238154255b9b2583fe85222089d71fde10f0e8aae6c9753c","Frozen actual parent changed")
 cursor=START
 for part in proof["fragments"]:
  need(part["begin_rva"]==cursor and part["end_rva_exclusive"]-cursor==part["bytes"],"Retained fragment extent changed")
  b=raw[cursor-START:part["end_rva_exclusive"]-START]
  need(hashlib.sha256(b).hexdigest()==part["sha256"],"Retained fragment SHA changed")
  cursor=part["end_rva_exclusive"]
 need(cursor==END,"Retained fragment closure incomplete")
 for pc,h in CRITICAL.items():need(raw[pc-START:pc-START+len(bytes.fromhex(h))]==bytes.fromhex(h),"Critical dataflow/call bytes changed")
 # Original RBP=entryRDX is preserved throughout the own-body prefix.
 need([r[0] for r in rows if r[0]<SETTLEMENT and r[3]=="mov" and r[4].split(",")[0].strip()=="rbp"]==[0x28F7850],
      "Prefix Character register overwritten")
 if independent_decode:
  import capstone
  md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
  decoded=[(i.address,i.size,i.bytes.hex()) for i in md.disasm(raw,START)]
  need(decoded==[(r[0],r[1],r[2]) for r in rows],"Independent decoder boundaries differ")
 result=analyze(raw,rows)
 need(result["exactly_once_on_all_own_body_normal_paths"] and not result["direct_calls_before_settlement"],"Parent settlement order theorem failed")
 need(result["entry_character_saved_RDX_and_passed_as_RCX"],"Entry Character dataflow failed")
 need(result["getter_calls"]=={"top_liege":[0x28F7AD5],"current_maintenance":[0x28F7C30]},"Known getter callsites differ")
 need(not any(result["getter_can_reach_earlier_settlement"].values()) and not any(result["getter_reachable_without_settlement"].values()),"Getter order theorem failed")
 if counterexample:
  # A synthetic bypass Jcc must invalidate the theorem. No native code runs.
  pc=0x28F7872;target=0x28F7C94;changed=bytearray(raw);offset=pc-START
  replacement=b"\x0f\x84"+(target-(pc+6)).to_bytes(4,"little",signed=True)
  changed[offset:offset+6]=replacement;altered=copy.deepcopy(rows)
  for row in altered:
   if row[0]==pc:row[2]=replacement.hex()
  negative=analyze(bytes(changed),altered)
  need(not negative["exactly_once_on_all_own_body_normal_paths"],"Synthetic bypass counterexample was wrongly accepted")
  result["synthetic_bypass_normal_counts"]=negative["normal_return_settlement_counts"]
 result.update(status="PASS_RETAINED_STATIC_PARENT_ORDER",SDK_calls=0,new_EXE_reads=0,game_actions=0,
  normal_control_flow_only=True,opaque_callee_effects_not_modeled=True,exceptions_or_reentrancy_not_qualified=True,
  military_paid_amount=None,payer_from_static_getter_name=None,calendar_cadence=None,
  independent_decode=independent_decode)
 return result
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--source",type=Path,default=HERE/"PARENT-ORDER-SOURCE.actual.json")
 p.add_argument("--independent-decode",action="store_true");p.add_argument("--counterexample",action="store_true")
 a=p.parse_args();print(json.dumps(verify(a.source,independent_decode=a.independent_decode,counterexample=a.counterexample),indent=2))
