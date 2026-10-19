"""Local-only exact Workshop cache tombstones. No Steam API/network calls.

An elevated administrator with SeRestorePrivilege can restore backup DACLs.
This blocks the pinned filesystem destinations, not all CDN network traffic.
"""
from pathlib import Path
import argparse, datetime, hashlib, json, os, sys
import win32api, win32con, win32file, win32security as s, pywintypes

MACHINE='desktop-3fevhd2-1c74096080'
IDS=['2291024373','2993056101','2962333032','3192256710','2224124758']
EVERYONE=s.ConvertStringSidToSid('S-1-1-0')
OWNER=s.ConvertStringSidToSid('S-1-3-4')
SEC=s.DACL_SECURITY_INFORMATION|s.OWNER_SECURITY_INFORMATION
DC=0x40; DELETE=0x10000; WDAC=0x40000; WOWNER=0x80000
FILE_DENY=DELETE|WDAC|WOWNER|0x2|0x4|0x10|0x100
PARENT_DENY=DC|WDAC|WOWNER

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(path,obj):
 p=Path(path)
 body=json.dumps(obj,ensure_ascii=False,indent=2).encode('utf-8')
 with p.open('xb') as f:f.write(body);f.flush();os.fsync(f.fileno())
 if p.read_bytes()!=body:raise RuntimeError('Durable JSON readback mismatch')
def sd(path):return s.GetNamedSecurityInfo(str(path),s.SE_FILE_OBJECT,SEC)
def sddl(desc):return s.ConvertSecurityDescriptorToStringSecurityDescriptor(desc,1,SEC)
def acl_signature(acl):
 if acl is None:return None
 return [(tuple(acl.GetAce(i)[0]),acl.GetAce(i)[1],s.ConvertSidToStringSid(acl.GetAce(i)[2])) for i in range(acl.GetAceCount())]
def acl_parent(original):
 a=s.ACL()
 a.AddAccessDeniedAceEx(s.ACL_REVISION,0,PARENT_DENY,EVERYONE)
 a.AddAccessDeniedAceEx(s.ACL_REVISION,0,WDAC|WOWNER,OWNER)
 old=original.GetSecurityDescriptorDacl()
 if old is None:raise RuntimeError('NULL original DACL forbidden')
 for i in range(old.GetAceCount()):
  (typ,flags),mask,sid=old.GetAce(i)
  if typ==0:a.AddAccessAllowedAceEx(s.ACL_REVISION,flags,mask,sid)
  elif typ==1:a.AddAccessDeniedAceEx(s.ACL_REVISION,flags,mask,sid)
  else:raise RuntimeError('Unsupported original ACE type; no lossy copy')
 return a
def acl_file():
 a=s.ACL()
 a.AddAccessDeniedAceEx(s.ACL_REVISION,0,FILE_DENY,EVERYONE)
 a.AddAccessDeniedAceEx(s.ACL_REVISION,0,WDAC|WOWNER,OWNER)
 a.AddAccessAllowedAceEx(s.ACL_REVISION,0,0x120089,EVERYONE)
 return a
def hold_dacl(path):
 return win32file.CreateFile(str(path),WDAC|0x20000,7,None,3,win32con.FILE_FLAG_BACKUP_SEMANTICS,None)
def setacl(path,acl,protected=False):
 info=s.DACL_SECURITY_INFORMATION
 if protected:info|=s.PROTECTED_DACL_SECURITY_INFORMATION
 s.SetNamedSecurityInfo(str(path),s.SE_FILE_OBJECT,info,None,None,acl,None)
def restore_handle(handle,original):
 ctl=original.GetSecurityDescriptorControl()[0]
 info=s.DACL_SECURITY_INFORMATION|(s.PROTECTED_DACL_SECURITY_INFORMATION if ctl&0x1000 else s.UNPROTECTED_DACL_SECURITY_INFORMATION)
 s.SetSecurityInfo(handle,s.SE_FILE_OBJECT,info,None,None,original.GetSecurityDescriptorDacl(),None)
def safe_parent(p):
 p=Path(p).resolve(strict=True)
 if not p.is_dir() or p.is_symlink() or p.stat().st_file_attributes&0x400:raise RuntimeError('Unsafe/reparse parent')
 return p
def install(parents,backup_path):
 originals=[]; files=[]; handles=[]
 # Preflight the entire set before changing any destination.
 for parent in parents:
  parent=safe_parent(parent)
  for item in IDS:
   q=parent/item
   if q.exists() or q.is_symlink():raise RuntimeError(f'Destination must be absent: {q}')
  for name in ['normal-replacement','normal-sibling','normal-renamed','normal-file','normal-file-renamed']:
   if (parent/name).exists() or (parent/name).is_symlink():raise RuntimeError('Reserved verification name already exists')
  original=sd(parent);handle=hold_dacl(parent)
  originals.append((parent,original,handle));handles.append(handle)
 backup={'schema':'ck3-local-workshop-block-dacl-backup-v1','machine_id':MACHINE,'observed_at_utc':now(),'item_ids':IDS,'parents':[{'path':str(p),'original_sddl':sddl(d)} for p,d,h in originals],'tombstones':[{'path':str(p/i),'originally_absent':True} for p,d,h in originals for i in IDS],'undo_policy':'Enable SeBackupPrivilege and SeRestorePrivilege; open all parent/child WRITE_DAC handles with BACKUP_SEMANTICS before mutation; grant each exact zero-byte tombstone recovery ACL; restore original parent DACL; close handles and unlink tombstones.'}
 save(backup_path,backup) # Never make the permanent mutation without durable original bytes.
 try:
  for parent,original,handle in originals:
   for item in IDS:
    q=parent/item
    with q.open('xb'):pass
    fdesc=sd(q);fh=hold_dacl(q);handles.append(fh)
    files.append((q,fdesc,fh))
    setacl(q,acl_file(),True)
   setacl(parent,acl_parent(original))
  return originals,files,handles
 except BaseException:
  for q,d,h in reversed(files):restore_handle(h,d)
  for p,d,h in reversed(originals):restore_handle(h,d)
  for q,d,h in reversed(files):q.unlink()
  for h in handles:h.Close()
  raise

def adversarial(parents,originals):
 rows=[]
 def blocked(name,p,fn):
  try:fn(); rows.append({'test':name,'path':str(p),'blocked':False})
  except (OSError,pywintypes.error) as ex:rows.append({'test':name,'path':str(p),'blocked':True,'winerror':getattr(ex,'winerror',None),'errno':getattr(ex,'errno',None)})
 for parent in parents:
  for item in IDS:
   q=parent/item
   blocked('CreateDirectory',q,lambda:q.mkdir())
   blocked('mkdir_descendant',q/'payload',lambda:(q/'payload').mkdir())
   blocked('write_truncate',q,lambda:q.write_bytes(b'x'))
   blocked('write_alternate_stream',q,lambda:Path(str(q)+':payload').write_bytes(b'x'))
   blocked('delete_file',q,q.unlink)
   blocked('rename_file',q,lambda:q.rename(parent/(item+'.moved')))
   blocked('replace_target',q,lambda:(parent/'normal-replacement').replace(q))
   blocked('set_file_DACL',q,lambda:setacl(q,s.ACL()))
  old=next(d for p,d,h in originals if p==parent)
  blocked('set_parent_DACL',parent,lambda:setacl(parent,old.GetSecurityDescriptorDacl()))
  normal=parent/'normal-sibling';normal.mkdir();(normal/'payload').write_bytes(b'normal');(normal/'payload').unlink();normal.rename(parent/'normal-renamed');(parent/'normal-renamed').rmdir()
  normal=parent/'normal-file';normal.write_bytes(b'ok');normal.rename(parent/'normal-file-renamed');(parent/'normal-file-renamed').unlink()
  rows.append({'test':'normal_sibling_create_write_rename_delete','path':str(parent),'success':True})
 return rows

def selftest(root,out):
 root=Path(root)
 root.mkdir(exist_ok=False)
 parents=[]
 for n in ['content_1158310','downloads_1158310','temp_1158310']:
  p=root/n;p.mkdir();parents.append(p)
 parents=[p.resolve() for p in parents]
 originals=files=handles=[]
 result={'machine_id':MACHINE,'observed_at_utc':now(),'kind':'owned-temp-real-NTFS-adversarial','steam_paths_changed':False}
 try:
  originals,files,handles=install(parents,root/'DACL-BACKUP.json')
  # Replacement source exists: a missing source would be a meaningless rejection.
  for p in parents:(p/'normal-replacement').write_bytes(b'normal')
  rows=adversarial(parents,originals)
  result['tests']=rows; result['all_blocked_and_siblings_ok']=all(r.get('blocked',r.get('success',False)) for r in rows)
  import subprocess
  child=Path(__file__).parent/'steam_workshop_local_block_child_verify.py'
  child_out=Path(out).parent/(root.name+'-CHILD-ADVERSARIAL.actual.json')
  cp=subprocess.run([sys.executable,'-B','-X','utf8',str(child),str(root/'DACL-BACKUP.json'),str(child_out)],capture_output=True,text=True,timeout=30)
  result['separate_process']={'returncode':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr,'receipt':str(child_out)}
  if cp.returncode!=0:result['all_blocked_and_siblings_ok']=False
  for p in parents:(p/'normal-replacement').unlink()
  verify_out=Path(out).parent/(root.name+'-VERIFY.actual.json')
  verify(root/'DACL-BACKUP.json',verify_out,owned_test=True)
  result['independent_verify_receipt']=str(verify_out)
  result['after_sddl']=[{'path':str(p),'sddl':sddl(sd(p))} for p in parents]
  result['placeholder_sddl']=sddl(sd(parents[0]/IDS[0]))
 finally:
  for p,d,h in reversed(originals):restore_handle(h,d)
  for p,d,h in reversed(files):restore_handle(h,d)
  for h in handles:h.Close()
  # Only remove exact zero-byte tombstones created by this test.
  for p,d,h in files:
   if p.exists() and p.is_file() and p.stat().st_size==0:p.unlink()
  result['restored_original_parent_dacls']=all(sddl(sd(p))==sddl(d) for p,d,h in originals)
  result['ended_at_utc']=now();save(out,result)
 print(json.dumps({k:v for k,v in result.items() if k!='tests'},indent=2))
 if not result.get('all_blocked_and_siblings_ok') or not result.get('restored_original_parent_dacls'):sys.exit(2)

def require_reviewed_machine():
 # This tool remains limited to the reviewed machine and exact local library.
 # Resolve the repository tools directory from tools/maintenance, not a drive.
 previous=list(sys.path)
 try:
  sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
  from ck3_live_run_id import current_machine_id
  actual=current_machine_id()
 finally:sys.path[:]=previous
 if actual!=MACHINE:raise RuntimeError('Actual machine ID does not match the reviewed machine')
 return actual

def main():
 a=argparse.ArgumentParser();sub=a.add_subparsers(dest='command',required=True)
 t=sub.add_parser('selftest');t.add_argument('--root',required=True);t.add_argument('--receipt',required=True)
 p=sub.add_parser('apply');p.add_argument('--plan',required=True);p.add_argument('--backup',required=True);p.add_argument('--receipt',required=True)
 u=sub.add_parser('undo');u.add_argument('--backup',required=True);u.add_argument('--receipt',required=True)
 v=sub.add_parser('verify');v.add_argument('--backup',required=True);v.add_argument('--receipt',required=True)
 args=a.parse_args()
 require_reviewed_machine()
 if args.command=='selftest':return selftest(args.root,args.receipt)
 if args.command=='undo':return undo(args.backup,args.receipt)
 if args.command=='verify':return verify(args.backup,args.receipt)
 plan=json.loads(Path(args.plan).read_text('utf-8'))
 if plan['machine_id']!=MACHINE or plan['item_ids']!=IDS:raise RuntimeError('Wrong machine/items')
 allowed=Path('C:/SteamLibrary/steamapps/workshop').resolve()
 parents=[]
 for v in plan['parents']:
  p=Path(v).resolve(strict=True)
  if not p.is_relative_to(allowed) or p.name!='1158310' or p.parent.name not in ['content','downloads','temp']:raise RuntimeError('Unapproved exact parent')
  parents.append(p)
 if not parents or len(parents)!=len(set(parents)):raise RuntimeError('Empty/duplicate parent plan')
 originals,files,handles=install(parents,args.backup)
 try:
  for p in parents:(p/'normal-replacement').write_bytes(b'normal')
  rows=adversarial(parents,originals)
  passed=all(r.get('blocked',r.get('success',False)) for r in rows)
  if not passed:raise RuntimeError('Adversarial or sibling test failed')
  save(args.receipt,{'machine_id':MACHINE,'observed_at_utc':now(),'installed':True,'all_blocked_and_siblings_ok':passed,'parents':[str(p) for p in parents],'item_ids':IDS,'tests':rows,'filesystem_only':True,'subscription_changes':False,'network_tested':False,'restore_requires_elevated_SeRestorePrivilege':True,'parent_sd':[{'path':str(p),'sddl':sddl(sd(p))} for p in parents],'placeholder_sd':[{'path':str(p),'sddl':sddl(sd(p))} for p,d,h in files]})
 except BaseException:
  for p,d,h in reversed(originals):restore_handle(h,d)
  for p,d,h in reversed(files):restore_handle(h,d)
  for p,d,h in files:
   if p.exists() and p.is_file() and p.stat().st_size==0:p.unlink()
  raise
 finally:
  for p in parents:
   q=p/'normal-replacement'
   if q.exists() and q.is_file() and q.read_bytes()==b'normal':q.unlink()
  for h in handles:h.Close()

def undo(backup_path,receipt_path):
 backup=json.loads(Path(backup_path).read_text('utf-8'))
 if backup['machine_id']!=MACHINE or backup['item_ids']!=IDS:raise RuntimeError('Wrong machine/items')
 token=s.OpenProcessToken(win32api.GetCurrentProcess(),s.TOKEN_ADJUST_PRIVILEGES|s.TOKEN_QUERY)
 try:
  for name in ['SeBackupPrivilege','SeRestorePrivilege']:
   luid=s.LookupPrivilegeValue(None,name)
   s.AdjustTokenPrivileges(token,False,[(luid,s.SE_PRIVILEGE_ENABLED)])
   if not any(priv==luid and attr&s.SE_PRIVILEGE_ENABLED for priv,attr in s.GetTokenInformation(token,s.TokenPrivileges)):raise RuntimeError('Administrator '+name+' required')
 finally:token.Close()
 parents=[];children=[];handles=[]
 try:
  for row in backup['parents']:
   p=safe_parent(row['path'])
   if not p.is_relative_to(Path('C:/SteamLibrary/steamapps/workshop').resolve()) or p.name!='1158310' or p.parent.name not in ['content','downloads','temp']:raise RuntimeError('Unapproved restore path')
   original=s.ConvertStringSecurityDescriptorToSecurityDescriptor(row['original_sddl'],1)
   previous=sd(p);h=hold_dacl(p);handles.append(h);parents.append((p,original,previous,h))
   for item in IDS:
    q=p/item
    if not q.is_file() or q.is_symlink() or q.stat().st_file_attributes&0x400 or q.stat().st_size!=0:raise RuntimeError('Tombstone changed; manual review required')
    actual=sd(q)
    if not actual.GetSecurityDescriptorControl()[0]&0x1000 or acl_signature(actual.GetSecurityDescriptorDacl())!=acl_signature(acl_file()):raise RuntimeError('Unexpected tombstone ACL; manual review required')
    h=hold_dacl(q);handles.append(h);children.append((q,actual,h))
  # All privileged handles are obtained before any permission mutation.
  try:recover_owned_objects(parents,children)
  except BaseException:
   for p,original,previous,h in reversed(parents):restore_handle(h,previous)
   for q,previous,h in reversed(children):restore_handle(h,previous)
   raise
 finally:
  for h in handles:h.Close()
 rows=[]
 for p,original,previous,h in parents:
  for item in IDS:(p/item).unlink()
  rows.append({'parent':str(p),'original_sddl_restored':True,'child_deny_removed_before_delete':True,'tombstones_absent':all(not (p/i).exists() for i in IDS)})
 save(receipt_path,{'machine_id':MACHINE,'observed_at_utc':now(),'undo':rows,'subscription_changes':False})

def recover_owned_objects(parents,children):
 token=s.OpenProcessToken(win32api.GetCurrentProcess(),s.TOKEN_QUERY)
 try:user=s.GetTokenInformation(token,s.TokenUser)[0]
 finally:token.Close()
 recovery=s.ACL()
 for sid in [user,s.ConvertStringSidToSid('S-1-5-18'),s.ConvertStringSidToSid('S-1-5-32-544')]:recovery.AddAccessAllowedAceEx(s.ACL_REVISION,0,0x1f01ff,sid)
 desc=s.SECURITY_DESCRIPTOR();desc.SetSecurityDescriptorDacl(1,recovery,0);desc.SetSecurityDescriptorControl(0x1000,0x1000)
 for q,previous,h in children:
  restore_handle(h,desc)
  if acl_signature(sd(q).GetSecurityDescriptorDacl())!=acl_signature(recovery):raise RuntimeError('Child recovery ACL readback mismatch')
 for p,original,previous,h in parents:
  restore_handle(h,original)
  if sddl(sd(p))!=sddl(original):raise RuntimeError('Original parent SDDL exact readback mismatch')

def verify(backup_path,receipt_path,owned_test=False):
 backup=json.loads(Path(backup_path).read_text('utf-8'))
 if backup['machine_id']!=MACHINE or backup['item_ids']!=IDS:raise RuntimeError('Wrong machine/items')
 originals=[];parents=[]
 for row in backup['parents']:
  p=safe_parent(row['path'])
  if not owned_test and (not p.is_relative_to(Path('C:/SteamLibrary/steamapps/workshop').resolve()) or p.name!='1158310' or p.parent.name not in ['content','downloads','temp']):raise RuntimeError('Unapproved verify parent')
  for name in ['normal-replacement','normal-sibling','normal-renamed','normal-file','normal-file-renamed']:
   if (p/name).exists() or (p/name).is_symlink():raise RuntimeError('Reserved verification name already exists')
  for item in IDS:
   q=p/item
   if not q.is_file() or q.is_symlink() or q.stat().st_size!=0 or acl_signature(sd(q).GetSecurityDescriptorDacl())!=acl_signature(acl_file()):raise RuntimeError('Unexpected or missing tombstone')
  original=s.ConvertStringSecurityDescriptorToSecurityDescriptor(row['original_sddl'],1)
  if acl_signature(sd(p).GetSecurityDescriptorDacl())!=acl_signature(acl_parent(original)):raise RuntimeError('Parent DACL differs from reviewed block')
  originals.append((p,original,None));parents.append(p)
 try:
  for p in parents:
   with (p/'normal-replacement').open('xb') as f:f.write(b'normal')
  rows=adversarial(parents,originals)
  passed=all(r.get('blocked',r.get('success',False)) for r in rows)
  save(receipt_path,{'machine_id':MACHINE,'observed_at_utc':now(),'verification':'fresh-named-handle-and-sibling-operations','all_blocked_and_siblings_ok':passed,'tests':rows,'subscription_changes':False,'network_tested':False})
 finally:
  for p in parents:
   q=p/'normal-replacement'
   if q.exists() and q.is_file() and q.read_bytes()==b'normal':q.unlink()
 if not passed:sys.exit(2)

if __name__=='__main__':main()
