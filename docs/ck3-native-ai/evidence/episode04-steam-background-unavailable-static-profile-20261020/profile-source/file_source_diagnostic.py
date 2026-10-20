import os,sys,time,json,hashlib,struct,ctypes,subprocess,datetime
from pathlib import Path
from ctypes import wintypes as w
ROOT=Path("C:/ck3-e04-resume-20261020-a01/r08-steam-profile-source-2015-a01")
CAP=ROOT/"STEAM-PROFILE-SOURCE128-ADMISSION.actual-a01.json"
U=Path("C:/ck3-e04-resume-20261020-a01/r08-parent-runtime-source-1930-a01/public-bundle-a01/tools")
OUT=ROOT/"FILE-SOURCE-DIAGNOSTIC.actual-a01.json"
began=time.monotonic()
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
machine=subprocess.check_output([sys.executable,"-B","D:/workspace/ck3_eternal_recurrence/tools/ck3_live_run_id.py","machine"],text=True).strip()
if machine!="desktop-3fevhd2-1c74096080": raise RuntimeError("machine mismatch")
def pin(p):
 b=p.read_bytes();return {"path":str(p),"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest()}
cp=pin(CAP)
if cp["sha256"]!="cedb0dea2c893d15f9e25abcf55009d389c96ed89d1de274d90554c36f953dd8": raise RuntimeError("capacity changed")
pv=pin(U/"steam_offline_native_provider_v1.py")
if pv["sha256"]!="b1c02586f60d4ba1a4b32aa26d695b22dd2a3ce647f7a66e0994afb92ff9e50a": raise RuntimeError("provider changed")
k=ctypes.WinDLL("kernel32",use_last_error=True)
v=ctypes.WinDLL("version",use_last_error=True)
class FI(ctypes.Structure):
 _fields_=[("attrs",w.DWORD),("created",w.FILETIME),("accessed",w.FILETIME),("modified",w.FILETIME),("volume",w.DWORD),("size_hi",w.DWORD),("size_lo",w.DWORD),("links",w.DWORD),("index_hi",w.DWORD),("index_lo",w.DWORD)]
k.CreateFileW.argtypes=[w.LPCWSTR,w.DWORD,w.DWORD,w.LPVOID,w.DWORD,w.DWORD,w.HANDLE];k.CreateFileW.restype=w.HANDLE
k.GetFileInformationByHandle.argtypes=[w.HANDLE,ctypes.POINTER(FI)];k.GetFileInformationByHandle.restype=w.BOOL
k.CloseHandle.argtypes=[w.HANDLE];k.CloseHandle.restype=w.BOOL
v.GetFileVersionInfoSizeW.argtypes=[w.LPCWSTR,ctypes.POINTER(w.DWORD)];v.GetFileVersionInfoSizeW.restype=w.DWORD
v.GetFileVersionInfoW.argtypes=[w.LPCWSTR,w.DWORD,w.DWORD,w.LPVOID];v.GetFileVersionInfoW.restype=w.BOOL
v.VerQueryValueW.argtypes=[w.LPCVOID,w.LPCWSTR,ctypes.POINTER(ctypes.c_void_p),ctypes.POINTER(w.UINT)];v.VerQueryValueW.restype=w.BOOL
def fid(h):
 z=FI()
 if not k.GetFileInformationByHandle(h,ctypes.byref(z)): raise ctypes.WinError(ctypes.get_last_error())
 ft=lambda a:(a.dwHighDateTime<<32)|a.dwLowDateTime
 return dict(volume_serial=z.volume,file_index=(z.index_hi<<32)|z.index_lo,bytes=(z.size_hi<<32)|z.size_lo,creation_filetime=ft(z.created),mtime_filetime=ft(z.modified),attributes=z.attrs,links=z.links)
def statid(p):
 z=p.stat(follow_symlinks=False);return dict(dev=z.st_dev,ino=z.st_ino,bytes=z.st_size,mtime_ns=z.st_mtime_ns)
def version(p):
 unused=w.DWORD();n=v.GetFileVersionInfoSizeW(str(p),ctypes.byref(unused))
 if not 0<n<=1048576: raise RuntimeError("invalid version resource size")
 b=ctypes.create_string_buffer(n)
 if not v.GetFileVersionInfoW(str(p),0,n,b): raise ctypes.WinError(ctypes.get_last_error())
 ptr=ctypes.c_void_p();size=w.UINT()
 if not v.VerQueryValueW(b,"\\",ctypes.byref(ptr),ctypes.byref(size)) or size.value<52: raise RuntimeError("missing fixed file info")
 x=ctypes.cast(ptr,ctypes.POINTER(w.DWORD*13)).contents
 if x[0]!=0xfeef04bd: raise RuntimeError("fixed version signature")
 fmt=lambda a,b:".".join(map(str,[a>>16,a&65535,b>>16,b&65535]))
 return dict(file_version=fmt(x[2],x[3]),product_version=fmt(x[4],x[5]),fixed_info_signature=hex(x[0]))
anchors=[
(0x616D0C,"440fb60513c9b000488d157d3b7400488bcbe81d9e3b00"),
(0x5D39B0,"40534883ec20488bd9e852d8f2ff488bc8488b10ff92880000008883e70100004883c4205bc3"),
(0x6869DF,"488d0d5acaa900e8c5cff4ff"),
(0x6158E4,"803d3cddb000007419488b0dacc1b0004533c0ba04000000e81fc7f6ff"),
(0x582038,"8bfa4c8bf1490f45f03b9154010000"),
(0x582071,"4189be54010000")]
def pe(f,total,check_anchors):
 def readat(o,n):
  if o<0 or o+n>total:raise RuntimeError("PE read out of file")
  f.seek(o);x=f.read(n)
  if len(x)!=n:raise RuntimeError("short PE read")
  return x
 if readat(0,2)!=b"MZ":raise RuntimeError("missing MZ")
 po=struct.unpack("<I",readat(0x3c,4))[0];h=readat(po,24)
 if h[:4]!=b"PE\0\0":raise RuntimeError("missing PE")
 machine,nsec,stamp=struct.unpack_from("<HHI",h,4);opsize=struct.unpack_from("<H",h,20)[0]
 if not 1<=nsec<=32 or not 64<=opsize<=4096:raise RuntimeError("PE shape")
 opt=readat(po+24,opsize);magic=struct.unpack_from("<H",opt)[0];imagesize=struct.unpack_from("<I",opt,56)[0]
 ss=[]
 for i in range(nsec):
  a=struct.unpack("<8sIIIIIIHHI",readat(po+24+opsize+i*40,40))
  ss.append(dict(name=a[0].split(b"\0")[0].decode("ascii","replace"),virtual_size=a[1],rva=a[2],raw_size=a[3],raw_offset=a[4]))
 result=dict(pe_offset=po,machine=hex(machine),timestamp=stamp,optional_magic=hex(magic),size_of_image=imagesize,sections=ss)
 if check_anchors:
  aa=[]
  for rva,hx in anchors:
   expected=bytes.fromhex(hx);row=dict(rva=hex(rva),bytes=len(expected),expected_hex=hx,mapped=False,match=False)
   for s in ss:
    if s["rva"]<=rva and rva+len(expected)<=s["rva"]+s["raw_size"]:
     off=s["raw_offset"]+rva-s["rva"];raw=readat(off,len(expected))
     row.update(mapped=True,raw_offset=off,actual_hex=raw.hex(),match=raw==expected);break
   aa.append(row)
  result["six_old_profile_anchors"]=aa
 return result
results=[]
for path in ["D:/Program Files (x86)/Steam/steam.exe","D:/Program Files (x86)/Steam/steamui.dll"]:
 p=Path(path);r=dict(path=path,status="STOP",mode_observation=False);handle=None
 try:
  if time.monotonic()-began>115:raise RuntimeError("deadline stop")
  sb=statid(p);r["path_identity_before"]=sb
  if not 0<sb["bytes"]<=67108864:raise RuntimeError("file exceeds bounded 64MiB input")
  handle=k.CreateFileW(str(p),0x80000000,1,None,3,0x08000000,None)
  if handle==ctypes.c_void_p(-1).value:
   handle=None;raise ctypes.WinError(ctypes.get_last_error())
  before=fid(handle);r["handle_identity_before"]=before
  if before["attributes"]&0x400:raise RuntimeError("reparse input")
  r["versions"]=version(p)
  with p.open("rb") as f:
   sha=hashlib.sha256();count=0
   while True:
    if time.monotonic()-began>115:raise RuntimeError("deadline stop")
    data=f.read(1048576)
    if not data:break
    count+=len(data);sha.update(data)
   if count!=before["bytes"]:raise RuntimeError("body size changed")
   r.update(bytes=count,sha256=sha.hexdigest(),pe=pe(f,count,p.name.lower()=="steamui.dll"))
  after=fid(handle);sa=statid(p);r.update(handle_identity_after=after,path_identity_after=sa,identity_stable=before==after and sb==sa)
  if not r["identity_stable"]:raise RuntimeError("identity changed")
  r["status"]="FILE_ONLY_COMPLETE"
 except Exception as e:r.update(error=str(e),winerror=getattr(e,"winerror",None))
 finally:
  if handle is not None:r["read_handle_closed"]=bool(k.CloseHandle(handle))
 results.append(r)
old=dict(exe_and_ui_version="10.96.30.42",ui_bytes=18962584,ui_sha256="cb387adefbbac64a3c1490d4275d00daf3a1e0219b4580726ef7681db7429278",ui_size_of_image=19238912)
ui=results[1]
if ui["status"]=="FILE_ONLY_COMPLETE":
 ui["old_profile_comparison"]=dict(size_match=ui["bytes"]==old["ui_bytes"],digest_match=ui["sha256"]==old["ui_sha256"],version_match=ui["versions"]["file_version"]==old["exe_and_ui_version"],image_size_match=ui["pe"]["size_of_image"]==old["ui_size_of_image"],anchors_all_match=all(x["match"] for x in ui["pe"]["six_old_profile_anchors"]))
record=dict(schema="xar.steam-file-only-profile-diagnostic.v1",machine_id=machine,observed_at_utc=now(),elapsed_seconds=round(time.monotonic()-began,3),capacity=cp,frozen_provider=pv,executor=pin(Path(__file__)),old_profile=old,files=results,run_probe_calls=0,Steam_process_memory_reads=0,Steam_mode_UI_switch_game_SDK_download=0,U_D_W_Git_mutations=0,unavailable_probe_not_rewritten=True,current_offline_mode=None)
payload=(json.dumps(record,ensure_ascii=True,indent=2)+"\n").encode()
used=sum(x.stat().st_size for x in ROOT.rglob("*") if x.is_file())
if used+len(payload)>131072:raise RuntimeError("output cap stop")
with OUT.open("xb") as f:f.write(payload);f.flush();os.fsync(f.fileno())
actual=pin(OUT)
if actual["sha256"]!=hashlib.sha256(payload).hexdigest():raise RuntimeError("receipt readback changed")
print(json.dumps(dict(delivery=actual,aggregate_bytes=sum(x.stat().st_size for x in ROOT.rglob("*") if x.is_file()),machine_id=machine,files=results),separators=(",",":")))
sys.exit(0 if all(x["status"]=="FILE_ONLY_COMPLETE" for x in results) else 2)
