import ctypes as c
from ctypes import wintypes as w
import os,pathlib

class Info(c.Structure):
    _fields_=[('attr',w.DWORD),('created',w.FILETIME),('accessed',w.FILETIME),('written',w.FILETIME),('volume',w.DWORD),('high',w.DWORD),('low',w.DWORD),('links',w.DWORD),('index_high',w.DWORD),('index_low',w.DWORD)]
class Standard(c.Structure):_fields_=[('allocation',c.c_longlong),('eof',c.c_longlong),('links',w.DWORD),('pending',w.BOOLEAN),('directory',w.BOOLEAN)]
class Disposition(c.Structure):_fields_=[('delete',w.BOOLEAN)]
k=c.WinDLL('kernel32',use_last_error=True)
k.CreateFileW.argtypes=[w.LPCWSTR,w.DWORD,w.DWORD,c.c_void_p,w.DWORD,w.DWORD,w.HANDLE];k.CreateFileW.restype=w.HANDLE
k.CloseHandle.argtypes=[w.HANDLE];k.CloseHandle.restype=w.BOOL
k.GetFileInformationByHandle.argtypes=[w.HANDLE,c.POINTER(Info)];k.GetFileInformationByHandle.restype=w.BOOL
k.GetFileInformationByHandleEx.argtypes=[w.HANDLE,c.c_int,c.c_void_p,w.DWORD];k.GetFileInformationByHandleEx.restype=w.BOOL
k.GetFinalPathNameByHandleW.argtypes=[w.HANDLE,w.LPWSTR,w.DWORD,w.DWORD];k.GetFinalPathNameByHandleW.restype=w.DWORD
k.SetFileInformationByHandle.argtypes=[w.HANDLE,c.c_int,c.c_void_p,w.DWORD];k.SetFileInformationByHandle.restype=w.BOOL
BAD=c.c_void_p(-1).value
def open_handle(p,desired,share):
    h=k.CreateFileW(str(p),desired,share,None,3,0x00200000,None)
    if h==BAD:raise c.WinError(c.get_last_error())
    return h
def get_info(h,p):
    i=Info()
    if not k.GetFileInformationByHandle(h,c.byref(i)):raise c.WinError(c.get_last_error())
    if i.attr&0x410:raise RuntimeError('Reparse or directory leaf rejected')
    buf=c.create_unicode_buffer(32768);n=k.GetFinalPathNameByHandleW(h,buf,len(buf),0)
    if not n or n>=len(buf):raise RuntimeError('Final handle path unavailable')
    final=buf.value[4:] if buf.value.startswith('\\\\?\\') else buf.value
    if os.path.normcase(os.path.abspath(final))!=os.path.normcase(str(p)):raise RuntimeError('Handle points elsewhere')
    s=Standard();allocation=s.allocation if k.GetFileInformationByHandleEx(h,1,c.byref(s),c.sizeof(s)) else None
    return {'id':[i.volume,(i.index_high<<32)|i.index_low],'b':(i.high<<32)|i.low,'ft':(i.written.dwHighDateTime<<32)|i.written.dwLowDateTime,'links':i.links,'allocation':allocation}
def inspect(p):
    h=open_handle(p,0x80,7)
    try:return get_info(h,p)
    finally:k.CloseHandle(h)
def exact_retire(root,relative,size,mtime_ns,allowed_suffixes=None):
    root=pathlib.Path(root).resolve(strict=True);p=(root/relative).resolve(strict=True)
    r={'p':relative,'b':size,'status':'not_deleted'};h=None
    try:
        if not p.is_relative_to(root):raise RuntimeError('Outside authorized root')
        if allowed_suffixes is not None and p.suffix.lower() not in allowed_suffixes:raise RuntimeError('Suffix outside authorized scope')
        for q in [p]+list(p.parents):
            if not q.is_relative_to(root):break
            if q.lstat().st_file_attributes&0x400:raise RuntimeError('Reparse ancestor rejected')
        before=inspect(p)
        if before['b']!=size or before['ft']!=mtime_ns//100+116444736000000000:raise RuntimeError('Reviewed size/mtime changed')
        h=open_handle(p,0x10000|0x80,0);actual=get_info(h,p)
        if actual!=before:raise RuntimeError('File identity changed between handles')
        r.update(id=actual['id'],a=actual['allocation'],links=actual['links'],ft=actual['ft'])
        flag=Disposition(True)
        if not k.SetFileInformationByHandle(h,4,c.byref(flag),c.sizeof(flag)):raise c.WinError(c.get_last_error())
        k.CloseHandle(h);h=None;r['exists_after']=p.exists()
        if r['exists_after']:raise RuntimeError('Absence not confirmed')
        r['status']='deleted'
    except Exception as ex:r['error']=str(ex)
    finally:
        if h is not None:k.CloseHandle(h)
    return r
