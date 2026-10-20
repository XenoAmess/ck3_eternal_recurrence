from pathlib import Path
import datetime,difflib,hashlib,json
R=Path(__file__).parent;SRC=Path('C:/ck3-war-episode04-research-20261004-a01/e04-r08-parent-dr-source-p01')
CAP=R.parent/'capacity/SOURCE4-1930-ADMISSION.actual-a01.json'
assert hashlib.sha256(CAP.read_bytes()).hexdigest()=='3778ed6c3c01d381116882ac796b623afe42af1826dc5991cfb64ed8546b79fa'
assert datetime.datetime.now(datetime.timezone.utc)<datetime.datetime(2026,10,20,19,28,tzinfo=datetime.timezone.utc)
old={n:(SRC/n).read_text() for n in ('parent_entry_cold_target.cpp','run_parent_entry_cold.py')}
assert hashlib.sha256((SRC/'parent_entry_cold_target.cpp').read_bytes()).hexdigest()=='4ca7c7ea284438c0b0f727c24a6bda4718b07f33506ca7ffd66a3207189defaf'
assert hashlib.sha256((SRC/'run_parent_entry_cold.py').read_bytes()).hexdigest()=='226e244e1095914b359edff4b1bf1ccf1a05007a3637ce0b0411889872da3e46'
target=old['parent_entry_cold_target.cpp']
target=target.replace('worker_done=nullptr;','worker_done=nullptr,warmup_event=nullptr,warmed_event=nullptr;\n+volatile LONG occupied_warmup_calls=0;'.replace('\n+','\n'))
target=target.replace('c.Dr0=0x12345000;c.Dr7=(c.Dr7&~3ULL)|1ULL;','''// Intel SDM 253669-060US Fig17-1/17-2: DR7 bit10 is fixed1.
    // New fixture input only; not proof of the previous run's OS causality.
    c.Dr0=0x12345000;c.Dr6=0xffff0ff0ULL;c.Dr7=(c.Dr7&~3ULL)|0x401ULL;''')
target=target.replace('if(!tf_held&&!ResumeOwnedPeer(main_thread,main_tid))return 3;','''if(!tf_held&&!ResumeOwnedPeer(main_thread,main_tid))return 3;
  if(mode==L"occupied-dr"){
   SetEvent(warmup_event);
   if(WaitForSingleObject(warmed_event,kWait)!=WAIT_OBJECT_0)return 6;
  }''')
target=target.replace('worker_done=CreateEventW(nullptr,TRUE,FALSE,nullptr);','worker_done=CreateEventW(nullptr,TRUE,FALSE,nullptr);warmup_event=CreateEventW(nullptr,TRUE,FALSE,nullptr);warmed_event=CreateEventW(nullptr,TRUE,FALSE,nullptr);')
target=target.replace('||!worker_done||!main_thread','||!worker_done||!warmup_event||!warmed_event||!main_thread')
target=target.replace('if(WaitForSingleObject(initial_done,kWait)!=WAIT_OBJECT_0)return 5;','''if(mode==L"occupied-dr"){
  if(WaitForSingleObject(warmup_event,kWait)!=WAIT_OBJECT_0)return 5;
  // An ordinary main-thread round trip, not ParentEntryStart or an observer action.
  InterlockedIncrement(&occupied_warmup_calls);SetEvent(warmed_event);
 }
 if(WaitForSingleObject(initial_done,kWait)!=WAIT_OBJECT_0)return 5;''')
target=target.replace('fault_release_event,initial_done,audit_done,worker_done}', 'fault_release_event,initial_done,audit_done,worker_done,warmup_event,warmed_event}')
target=target.replace('<<",\\\"real_CK3_call\\\":false}', '<<",\\\"occupied_warmup_calls\\\":"<<occupied_warmup_calls<<",\\\"real_CK3_call\\\":false}')
runner=old['run_parent_entry_cold.py']
runner=runner.replace('debugger or releases an unaudited target to make a finite test look complete.','debugger. A proven detached synthetic target may finish after audit FAIL;\nthat explicit failed audit never becomes a PASS.')
helpers='''def assert_zero_arm_refusal(rows,observer_code,ready_exists):
    if type(observer_code) is not int or observer_code not in (1,2) or ready_exists:
        raise ValueError('Expected zero-arm refusal did not occur')
    for row in rows:
        if not isinstance(row,dict):raise ValueError('Unknown refusal diagnostic')
        if row.get('kind') in {'parent_entry','restore','foreign_resume','ready','cleanup_owned_execution'}:
            raise ValueError('Refusal contains execution or mutation evidence')
        if row.get('kind')=='arm':
            vector=row.get('armed_debug')
            if not(row.get('success') is False and row.get('saved_debug')==[] and row.get('readback') is True and
                   isinstance(vector,list) and len(vector)==6 and all(type(x) is int and 0<=x<2**64 for x in vector) and
                   all(type(row.get(k)) is int and row[k]>0 for k in ('thread_id','thread_generation','thread_created'))):
                raise ValueError('Actual, partial or unknown arm cannot pass refusal')

def synthetic_detached_cleanup_proven(rows,meta,identity,observer_closed,observer_waited,machine):
    if observer_closed is not True or observer_waited is not True or not isinstance(meta,dict):return False
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
    return same and all(t.get(k) is True for k in ('restored','detached','cleanup_complete')) and t.get('pending_event') is False

'''
runner=runner.replace('def run_case(options,case,machine,gate,win):',helpers+'def run_case(options,case,machine,gate,win):')
runner=runner.replace("if observer_code==0 or ready.exists() or any(x.get('kind') in {'arm','parent_entry'} for x in rows):raise ValueError('Expected zero-arm refusal did not occur')","assert_zero_arm_refusal(rows,observer_code,ready.exists())")
runner=runner.replace("        except BaseException as exc:\n            hold('Independent restoration proof failed: '+repr(exc),target);raise",'''        except BaseException as exc:
            write(out/'INDEPENDENT-DR-AUDIT-FAILED.actual.json',dict(machine_id=machine,observed_at_utc=now(),error=repr(exc),qualified=False,before=before if 'before' in locals() else None,after=after if 'after' in locals() else None))
            if synthetic_detached_cleanup_proven(rows,meta,win.identity(target),observer is not None and observer.poll() is not None,'observer' in waited,machine):
                # Normal end of this exact private fixture only. The failed six-DR
                # audit remains failed; never release an unknown debugger/restore.
                win.event(meta['finish_event']);released=True
                until=time.monotonic()+5
                while target.poll() is None and time.monotonic()<until:time.sleep(.01)
                if target.poll() is None:hold('Failed synthetic audit: original Finish did not close target',target)
                original_wait('target',target)
                raise
            hold('Independent restoration proof failed: '+repr(exc),target);raise''')
runner=runner.replace("            if alive:\n                hold('Final ownership backstop after incomplete case cleanup: '+label,p)\n                try:original_wait(label,p)\n                except BaseException:pass # Process is closed; missing receipt stays unknown.",'''            if alive:
                hold('Final ownership backstop after incomplete case cleanup: '+label,p)
            # Also consume the actual original Popen after an inner hold already
            # observed its exit. A new handle/current absence is never a wait.
            try:original_wait(label,p)
            except BaseException as wait_error:
                try:write(out/(label+'.WAIT-RECEIPT-ERROR.actual.json'),dict(machine_id=machine,observed_at_utc=now(),error=repr(wait_error),original_wait_receipt_missing=True,qualified=False))
                except BaseException:pass
        if error is not None and not (out/'FAILED.actual.json').exists():
            write(out/'FAILED.actual.json',dict(machine_id=machine,observed_at_utc=now(),error=error,cleanup_exception=repr(sys.exc_info()[1]),automatic_replay=False,qualified=False,target_audited=target_audited))''')
payloads={'parent_entry_cold_target.cpp':target.encode(),'run_parent_entry_cold.py':runner.encode()}
assert target!=old['parent_entry_cold_target.cpp'] and runner!=old['run_parent_entry_cold.py']
assert b'occupied_warmup_calls' in payloads['parent_entry_cold_target.cpp']
for n,raw in payloads.items():
 if n.endswith('.py'):compile(raw,str(R/n),'exec')
patch=''.join(''.join(difflib.unified_diff(old[n].splitlines(True),payloads[n].decode().splitlines(True),fromfile='a/'+n,tofile='b/'+n)) for n in payloads).encode()
assert sum(len(x) for x in payloads.values())+len(patch)+sum(p.stat().st_size for p in R.rglob('*') if p.is_file())<524288
for n,raw in {**payloads,'NATIVE-REPAIR.candidate.patch':patch}.items():
 with (R/n).open('xb') as f:f.write(raw)
print(json.dumps({n:dict(path=str(R/n),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()) for n,raw in payloads.items()}))
