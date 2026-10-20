from pathlib import Path
import difflib
R=Path(__file__).parent;H=R/'rejected-a01';H.mkdir()
for n in ['run_parent_entry_cold.py','NATIVE-REPAIR.candidate.patch']:
 with (H/n).open('xb') as f:f.write((R/n).read_bytes())
p=R/'run_parent_entry_cold.py';s=p.read_text();a=s.index('def synthetic_detached_cleanup_proven(');b=s.index('def run_case(',a)
fn='''def synthetic_detached_cleanup_proven(rows,meta,identity,observer_code,observer_waited,machine,refusal):
    # Only a strict zero-mutation refusal can take this failed-audit exception.
    # A raw restored=True never overrides unknown or contradicted owned state.
    if refusal is not True or observer_waited is not True or not isinstance(meta,dict):return False
    if not isinstance(rows,list) or any(not isinstance(r,dict) or r.get('kind') not in {'start','arm','terminal'} for r in rows):return False
    try:assert_zero_arm_refusal(rows,observer_code,False)
    except ValueError:return False
    starts=[r for r in rows if r.get('kind')=='start'];terms=[r for r in rows if r.get('kind')=='terminal']
    if len(starts)!=1 or len(terms)!=1 or not rows or rows[-1] is not terms[0]:return False
    s,t=starts[0],terms[0]
    try:
        same=(meta['parent_schema']=='xar.maintenance.parent_entry.cold-meta.v1' and
              s['schema']=='xar.maintenance.parent_entry.raw.v1' and s['mode']=='parent-entry-execution-once-v1' and
              s['machine_id']==machine and s['synthetic'] is True and 'owner_binding' in s and s['owner_binding'] is None and
              int(s['pid'])==int(meta['pid'])==identity['pid'] and int(s['created'])==int(meta['created'])==identity['created'] and
              int(s['entry'])==int(meta['parent_entry']))
    except (KeyError,TypeError,ValueError):return False
    return same and all(t.get(k) is True for k in ('restored','detached','cleanup_complete')) and t.get('pending_event') is False and t.get('process_exited') is False

'''
s=s[:a]+fn+s[b:];s=s.replace("observer is not None and observer.poll() is not None,'observer' in waited,machine)","observer.returncode if observer is not None and observer.poll() is not None else None,'observer' in waited,machine,case in REFUSALS)")
p.write_text(s,encoding='utf-8',newline='\n')
old=(R/'test_native_repair.py').read_text();t=old.replace("pending_event=False)","pending_event=False,process_exited=False)")
addition=''' def test_failed_audit_finish_exception_rejects_any_mutation_or_unknown(self):
  meta=dict(parent_schema='xar.maintenance.parent_entry.cold-meta.v1',pid='1',created='2',parent_entry='3')
  identity=dict(pid=1,created=2)
  start=dict(kind='start',schema='xar.maintenance.parent_entry.raw.v1',mode='parent-entry-execution-once-v1',machine_id=M,synthetic=True,owner_binding=None,pid=1,created=2,entry=3)
  end=dict(kind='terminal',restored=True,detached=True,cleanup_complete=True,pending_event=False,process_exited=False)
  def check(rows,code=1,waited=True,refusal=True):return m.synthetic_detached_cleanup_proven(rows,meta,identity,code,waited,M,refusal)
  self.assertTrue(check([start,arm(),end]))
  for row in [dict(arm(),success=True,saved_debug=[0]*6),dict(arm(),saved_debug=[0]*6),dict(arm(),readback=False),dict(kind='parent_entry'),dict(kind='restore'),dict(kind='unknown')]:
   with self.subTest(row=row):self.assertFalse(check([start,row,end]))
  for code,waited,refusal in [(None,True,True),(0,True,True),(1,False,True),(1,True,False)]:
   self.assertFalse(check([start,arm(),end],code,waited,refusal))
  self.assertFalse(check([start,arm(),dict(end,process_exited=True)]))
'''
t=t.replace("if __name__=='__main__':unittest.main(verbosity=2)",addition+"if __name__=='__main__':unittest.main(verbosity=2)")
with (R/'test_native_repair_a02.py').open('x',encoding='utf-8',newline='\n') as f:f.write(t)
SRC=Path('C:/ck3-war-episode04-research-20261004-a01/e04-r08-parent-dr-source-p01')
patch=''.join(''.join(difflib.unified_diff((SRC/n).read_text().splitlines(True),(R/n).read_text().splitlines(True),fromfile='a/'+n,tofile='b/'+n)) for n in ['parent_entry_cold_target.cpp','run_parent_entry_cold.py'])
(R/'NATIVE-REPAIR.candidate.patch').write_text(patch,encoding='utf-8',newline='\n')
print('a02 narrow refusal-only finish candidate created; rejected a01 preserved')
