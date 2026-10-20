"""Owner parent holds exact final sources across one standard native runas child."""
from pathlib import Path
from contextlib import ExitStack
import json,hashlib,subprocess,datetime as dt,time,ctypes,sys,os
from ctypes import wintypes as w
O=Path(__file__).parent;B=O.parent/'native-build-a40-a01';ROOT=Path('C:/Program Files/XAR CK3 Project EXE Broker')
MID='desktop-3fevhd2-1c74096080';OWNER='S-1-5-21-4063940640-1897558599-686929869-1001';TRUSTED=(OWNER,'S-1-5-18','S-1-5-32-544')
FILES={'maintain_a40_broker_root.py':(9066,'7b9e55a91f0f06dd533ffe93a007e2e81a9fb1e46bdbe5440b5f17c0f3ace33f'),'BROKER-POLICY-EXACT-A40-ROOT.candidate-a01.json':(1157,'9b8d2f551b4b2c305d551522008cd19d2e3aa0fdc932d425bcacdba96b4da1d1'),'BROKER-INSTALLATION-MANIFEST-EXACT-A40-ROOT.candidate-a01.json':(1119,'80670b731a5e173301117546de4ffbf4b770e681cb264fbed596ecf611d5e6a6')}
def now():return dt.datetime.now(dt.timezone.utc).isoformat()
def pin(p):
 data=Path(p).read_bytes();return {'path':str(p),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
def write(name,value):
 p=B/name
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 return pin(p)
assert pin(ROOT/'native_safety.py')['sha256']=='873ec34e49d2549493ffddeb934d4d7d12e7a97de76fecc43c5135c0ee5118e2'
sys.path.insert(0,str(ROOT));from native_safety import NativeSafety,descriptor_proof
s=NativeSafety(OWNER,str(ROOT/'private-frozen'),str(ROOT/'receipts'));token=s.token_identity();assert token['sid']==OWNER
argv=[str(ROOT/'runtime/python.exe'),'-I','-S','-B',str(O/'maintain_a40_broker_root.py'),'--expected-helper-sha256',FILES['maintain_a40_broker_root.py'][1],'--apply']
facts={'schema':'xar.e04.a40-native-runas-maintenance-launch.v1','machine_id':MID,'observed_at_utc':now(),'parent_token':token,'argv':argv,'scope':'One reviewed fixed two-leaf maintenance; no arbitrary command or directory. No game/SDK/project-output EXE execution.','actual_child_exit_code':None,'status':'PENDING_NATIVE_ADMIN_CHILD','source_facts':[]}
with ExitStack() as held:
 leases=[]
 for name,expected in FILES.items():
  lease=held.enter_context(s.lock_file(str(O/name),owner_sid=OWNER));leases.append(lease);data=lease.read_bytes(max(expected[0],1));assert (len(data),hashlib.sha256(data).hexdigest())==expected
  desc=s.inspect_descriptor(str(O/name));descriptor_proof(desc['security'],expected_owner=OWNER,allowed_writers=TRUSTED,require_protected=True,allowed_readers=TRUSTED)
  facts['source_facts'].append({'path':str(O/name),'file_id':lease.file_id,'pin':pin(O/name),'descriptor':desc})
 assert not (B/'BROKER-EXACT-ROOT-MAINTENANCE.actual-a01.json').exists()
 facts['held_source_count']=3;facts['intent']=write('BROKER-MAINTENANCE-NATIVE-LAUNCH-INTENT.actual-a01.json',facts)
 print(json.dumps({'status':'FINAL_THREE_SOURCE_LEASES_HELD_ENTERING_NATIVE_RUNAS','observed_at_utc':now()}),flush=True)
 child=None;handle=None
 try:
  if token['admin']:
   facts['method']='already-admin exact argv Popen'
   with (B/'BROKER-MAINTENANCE-ADMIN.stdout-a01.txt').open('xb') as out,(B/'BROKER-MAINTENANCE-ADMIN.stderr-a01.txt').open('xb') as err:
    child=subprocess.Popen(argv,stdout=out,stderr=err,creationflags=0x08000000,cwd=str(B));facts['actual_child_pid']=child.pid
    while child.poll() is None:time.sleep(1)
    facts['actual_child_exit_code']=child.returncode
  else:
   class SHELLEXECUTEINFOW(ctypes.Structure):
    _fields_=[('cbSize',w.DWORD),('fMask',w.ULONG),('hwnd',w.HWND),('lpVerb',w.LPCWSTR),('lpFile',w.LPCWSTR),('lpParameters',w.LPCWSTR),('lpDirectory',w.LPCWSTR),('nShow',ctypes.c_int),('hInstApp',w.HINSTANCE),('lpIDList',ctypes.c_void_p),('lpClass',w.LPCWSTR),('hkeyClass',w.HKEY),('dwHotKey',w.DWORD),('hIcon',w.HANDLE),('hProcess',w.HANDLE)]
   shell=ctypes.WinDLL('shell32',use_last_error=True);shell.ShellExecuteExW.argtypes=[ctypes.POINTER(SHELLEXECUTEINFOW)];shell.ShellExecuteExW.restype=w.BOOL
   k=ctypes.WinDLL('kernel32',use_last_error=True)
   k.GetProcessId.argtypes=[w.HANDLE];k.GetProcessId.restype=w.DWORD
   k.WaitForSingleObject.argtypes=[w.HANDLE,w.DWORD];k.WaitForSingleObject.restype=w.DWORD
   k.GetExitCodeProcess.argtypes=[w.HANDLE,ctypes.POINTER(w.DWORD)];k.GetExitCodeProcess.restype=w.BOOL
   k.CloseHandle.argtypes=[w.HANDLE];k.CloseHandle.restype=w.BOOL
   info=SHELLEXECUTEINFOW();info.cbSize=ctypes.sizeof(info);info.fMask=0x40;info.lpVerb='runas';info.lpFile=argv[0];info.lpParameters=subprocess.list2cmdline(argv[1:]);info.lpDirectory=str(B);info.nShow=0
   facts['method']='ShellExecuteExW verb=runas SEE_MASK_NOCLOSEPROCESS SW_HIDE'
   if not shell.ShellExecuteExW(ctypes.byref(info)):
    error=ctypes.get_last_error();facts.update(status='OS_UAC_CANCELLED_OR_REFUSED_NO_SUCCESS_CLAIM',win32_error=error,error=ctypes.FormatError(error))
   else:
    handle=info.hProcess
    if not handle:raise RuntimeError('native call ACK returned no process handle; cannot prove child lifecycle')
    facts['actual_child_pid']=k.GetProcessId(handle);print(json.dumps({'actual_native_child_pid':facts['actual_child_pid'],'receipt_still_required':True}),flush=True)
    while True:
     wait=k.WaitForSingleObject(handle,1000)
     if wait==0:break
     if wait==0xffffffff:raise ctypes.WinError(ctypes.get_last_error())
     if wait!=258:raise RuntimeError('unexpected native wait result '+str(wait))
    code=w.DWORD();assert k.GetExitCodeProcess(handle,ctypes.byref(code));facts['actual_child_exit_code']=code.value
  receipt=B/'BROKER-EXACT-ROOT-MAINTENANCE.actual-a01.json'
  if receipt.exists():
   facts['actual_maintenance_receipt']=pin(receipt);value=json.loads(receipt.read_bytes());facts['actual_maintenance_status']=value['status']
   if facts['actual_child_exit_code']==0 and value['status']=='EXACT_A40_BUILD_ROOT_INSTALLED_AND_READ_BACK':facts['status']='ACTUAL_ADMIN_MAINTENANCE_SUCCESS'
   else:facts['status']='ACTUAL_ADMIN_MAINTENANCE_FAILED_OR_PARTIAL'
  elif facts.get('win32_error') is None:facts['status']='CHILD_EXITED_WITHOUT_REQUIRED_MAINTENANCE_RECEIPT'
 except BaseException as error:facts.update(status='NATIVE_LAUNCH_OR_CHILD_FAILURE_NO_SUCCESS_CLAIM',error=repr(error))
 finally:
  if handle:k.CloseHandle(handle)
 for lease in leases:lease.revalidate()
 facts['final_sources_revalidated_before_release']=True;facts['finished_at_utc']=now();result=write('BROKER-MAINTENANCE-NATIVE-LAUNCH-RESULT.actual-a01.json',facts)
 print(json.dumps({'status':facts['status'],'result':result}),flush=True)
 if facts['status']!='ACTUAL_ADMIN_MAINTENANCE_SUCCESS':raise SystemExit(1)
