"""Ordinary-owner prehardening of exactly three reviewed input files; no installed writes."""
from pathlib import Path
from contextlib import ExitStack
import sys,json,hashlib,os,datetime as dt
ROOT=Path('C:/Program Files/XAR CK3 Project EXE Broker');O=Path(__file__).parent;B=O.parent/'native-build-a40-a01'
OWNER='S-1-5-21-4063940640-1897558599-686929869-1001';TRUSTED=(OWNER,'S-1-5-18','S-1-5-32-544')
ROWS={'maintain_a40_broker_root.py':(9066,'7b9e55a91f0f06dd533ffe93a007e2e81a9fb1e46bdbe5440b5f17c0f3ace33f'),'BROKER-POLICY-EXACT-A40-ROOT.candidate-a01.json':(1157,'9b8d2f551b4b2c305d551522008cd19d2e3aa0fdc932d425bcacdba96b4da1d1'),'BROKER-INSTALLATION-MANIFEST-EXACT-A40-ROOT.candidate-a01.json':(1119,'80670b731a5e173301117546de4ffbf4b770e681cb264fbed596ecf611d5e6a6')}
sys.path.insert(0,str(ROOT));from protected_runtime import activate_sealed_paths
activate_sealed_paths(ROOT)
from native_safety import NativeSafety,descriptor_proof
import win32security as sec
s=NativeSafety(OWNER,str(ROOT/'private-frozen'),str(ROOT/'receipts'));assert s.token_identity()=={'sid':OWNER,'admin':False}
backend=s._backend();backend._api();handles=[];before=[];after=[]
def write(path,v):
 with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
def exact(h,path,pin):
 state=backend.state(h);s._check_state(str(path),state,False)
 content=backend.read(h,max(pin[0],1));assert (len(content),hashlib.sha256(content).hexdigest())==pin
 assert state['security']['owner_sid']==OWNER
 return state
facts={'schema':'xar.e04.a40-source-input-prehardening.v1','machine_id':'desktop-3fevhd2-1c74096080','observed_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'actual_token':s.token_identity(),'scope':'Exactly three user-owned review inputs. No root/directory ACL, installed broker, task, UAC, Defender or EXE changes.'}
try:
 with s.lock_dir(str(O)):
  for name,pin in ROWS.items():
   path=O/name
   h=backend.CreateFile(backend._extended(str(path)),0x80040000,1,None,3,0x80|0x00200000,None)
   import ctypes
   if h==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
   handles.append((h,path,pin));state=exact(h,path,pin)
   sd=sec.GetSecurityInfo(int(h),sec.SE_FILE_OBJECT,sec.OWNER_SECURITY_INFORMATION|sec.GROUP_SECURITY_INFORMATION|sec.DACL_SECURITY_INFORMATION)
   before.append({'path':str(path),'pin':{'bytes':pin[0],'sha256':pin[1]},'state':state,'restore_sddl':sec.ConvertSecurityDescriptorToStringSecurityDescriptor(sd,1,0x7)})
  write(B/'A40-REVIEW-INPUT-SOURCE-ACL-BEFORE.actual-a01.json',{**facts,'before':before})
  target=sec.ConvertStringSecurityDescriptorToSecurityDescriptor('O:'+OWNER+'G:BAD:P'+''.join('(A;;FA;;;'+x+')' for x in TRUSTED),1)
  flags=sec.DACL_SECURITY_INFORMATION|sec.PROTECTED_DACL_SECURITY_INFORMATION
  assert flags&0xffffffff==0x80000004 and -2147483648<=flags<=2147483647
  for h,path,pin in handles:
   sec.SetSecurityInfo(int(h),sec.SE_FILE_OBJECT,flags,None,None,target.GetSecurityDescriptorDacl(),None)
   state=exact(h,path,pin);descriptor_proof(state['security'],expected_owner=OWNER,allowed_writers=TRUSTED,require_protected=True,allowed_readers=TRUSTED)
   assert len(state['security']['aces'])==3 and all(x['type']==0 and x['mask']==0x1f01ff and x['flags']==0 for x in state['security']['aces'])
   after.append({'path':str(path),'state':state})
finally:
 for h,path,pin in reversed(handles):backend.close(h)
with ExitStack() as leases:
 for name,pin in ROWS.items():
  lease=leases.enter_context(s.lock_file(str(O/name),owner_sid=OWNER));content=lease.read_bytes(pin[0]);assert hashlib.sha256(content).hexdigest()==pin[1]
 write(B/'A40-REVIEW-INPUT-SOURCE-ACL-AFTER.actual-a01.json',{**facts,'status':'THREE_EXACT_INPUTS_PROTECTED_AND_FRESH_READONLY_LEASES_VERIFIED','after':after,'Root_must_hold_final_readonly_source_leases_through_elevated_child':True})
print(json.dumps({'status':'PASS','files':3,'installed_writes':0}))
