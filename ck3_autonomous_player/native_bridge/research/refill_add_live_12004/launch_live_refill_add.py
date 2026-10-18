"""Root-only supervisor. No SDK, advance, retry, kill, or automatic consumer."""
from pathlib import Path
import argparse, hashlib, json, os, subprocess, time
from datetime import datetime, timezone

def need(ok, why):
    if not ok: raise ValueError(why)

def sha(raw): return hashlib.sha256(raw).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()
def write(path, value):
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2); f.write('\n'); f.flush(); os.fsync(f.fileno())

def pin(path):
    if not path.is_file(): return {'path':str(path),'present':False}
    size=path.stat().st_size
    return {'path':str(path),'present':True,'bytes':size,
            'sha256':sha(path.read_bytes()) if size<=2097152 else None}

def validate_prepared_ready_scope(prepared):
    """Check existing argv and the declared ready owner; perform no I/O or launch."""
    need(type(prepared) is dict, 'PREPARED object')
    schema=prepared.get('schema')
    need(schema in ('xar.ck3.refill_ADD_12004.prepared_live_argv.v1',
                    'xar.ck3.refill_ADD_12004.prepared_live_argv.v2'), 'PREPARED schema')
    need(prepared.get('observer_launched') is False and prepared.get('actual_ADD_observed') is False,'unlaunched preparation')
    argv=prepared['native_argv']; consume=prepared['consume_argv']
    need(type(argv) is list and len(argv)==20 and all(type(x) is str and x for x in argv),'structured native argv')
    need(argv[1]=='--enable' and argv[2::2]==['--pid','--thread','--regiment','--slot','--created','--timeout-ms','--raw','--ready','--machine-id'],'existing production CLI only')
    need(Path(argv[0]).name=='refill_add_hwprobe_12004.exe' and argv[13]=='30000','live target and 30s native window')
    values=dict(zip(argv[2::2],argv[3::2])); expected=prepared['ready_must_match']
    ready_schema=('xar.ck3.refill_ADD_12004.hwprobe_ready.v3'
                  if schema.endswith('.v2') else 'xar.ck3.refill_ADD_12004.hwprobe_ready.v2')
    need(type(expected) is dict and expected.get('schema')==ready_schema,'production ready contract')
    for flag,key in [('--pid','pid'),('--thread','thread_id'),('--regiment','regi_full_id_u32'),('--slot','physical_slot'),('--created','process_created_filetime')]:
        need(type(expected.get(key)) is int and str(expected[key])==values[flag],'same prepared '+key)
    need(expected.get('machine_id')==prepared.get('machine_id')==values['--machine-id'],'same prepared machine')
    if schema.endswith('.v2'):
        module=prepared.get('carrier_module_path'); epoch=prepared.get('carrier_source_epoch')
        need(type(module) is str and Path(module).is_absolute()
             and Path(module).name.lower()=='xar_ck3_bridge.dll', 'prepared actual carrier module path')
        need(type(epoch) is int and epoch==20261018, 'prepared carrier source epoch')
        need(type(expected.get('carrier_module_path')) is str and expected['carrier_module_path']==module
             and type(expected.get('carrier_source_epoch')) is int and expected['carrier_source_epoch']==epoch,
             'same prepared/ready carrier module and source epoch')
    return argv, consume, expected, values


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--prepared',type=Path,required=True)
    p.add_argument('--prepared-sha256',required=True)
    p.add_argument('--output-root',type=Path,required=True)
    a=p.parse_args()
    raw=a.prepared.read_bytes()
    need(0<len(raw)<=2097152 and sha(raw)==a.prepared_sha256,'exact bounded PREPARED pin')
    prepared=json.loads(raw)
    argv,consume,expected,values=validate_prepared_ready_scope(prepared)
    native_raw=Path(values['--raw']); ready=Path(values['--ready']); out=a.output_root.resolve()
    need(not out.exists() and not native_raw.exists() and not ready.exists(),'fresh launch/raw/ready outputs')
    need(type(consume) is list and all(type(x) is str for x in consume),'preserved consumer argv')
    out.mkdir(parents=True,exist_ok=False)
    record={'schema':'xar.ck3.refill_ADD_12004.root_launch.v1','machine_id':prepared['machine_id'],
      'started_at_utc':now(),'prepared':{'path':str(a.prepared.resolve()),'bytes':len(raw),'sha256':sha(raw)},'native_argv':argv,'consume_argv':consume,
      'target_pid':expected['pid'],'process_created_filetime':expected['process_created_filetime'],
      'automatic_advance':False,'automatic_consumer':False,'automatic_retry':False,'force_kill':False}
    proc=None; verified=False; ready_error=None; error=None
    with (out/'observer.stdout').open('xb') as so,(out/'observer.stderr').open('xb') as se:
        try:
            proc=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=so,stderr=se,creationflags=subprocess.CREATE_NO_WINDOW)
            record['observer_pid']=proc.pid; write(out/'STARTED.actual.json',record)
            while proc.poll() is None:
                if not verified and ready.is_file():
                    try:
                        content=ready.read_bytes(); need(0<len(content)<=16384,'bounded ready')
                        value=json.loads(content)
                        need(type(value) is dict and all(type(value.get(k)) is type(v) and value[k]==v for k,v in expected.items()),'ready exact owner/generation/slot mismatch')
                        if proc.poll() is None:
                            verified=True
                            item={**record,'observed_at_utc':now(),'ready':{'path':str(ready),'bytes':len(content),'sha256':sha(content)},'ready_verified':True,'observer_alive_at_check':True,'actual_ADD_observed':False}
                            write(out/'READY.actual.json',item)
                            print(json.dumps({'ready_verified':True,'receipt':str(out/'READY.actual.json'),'observer_pid':proc.pid}),flush=True)
                    except (json.JSONDecodeError,PermissionError): pass
                    except (ValueError,KeyError,TypeError) as ex: ready_error=repr(ex)
                time.sleep(.05)
        except BaseException as ex:
            error=repr(ex)
        finally:
            # Native owns its 30s window and DR cleanup. Never terminate it.
            if proc is not None:
                while proc.poll() is None:
                    try: proc.wait()
                    except KeyboardInterrupt: pass
            so.flush(); se.flush()
    result={**record,'finished_at_utc':now(),'observer_exit_code':None if proc is None else proc.returncode,
      'ready_verified':verified,'ready_error':ready_error,'launcher_error':error,
      'raw':pin(native_raw),'native_ready':pin(ready),'stdout':pin(out/'observer.stdout'),'stderr':pin(out/'observer.stderr'),
      'actual_ADD_observed':False,'full_R06_qualified':False}
    write(out/'EXIT.actual.json',result)
    print(json.dumps({'exit_receipt':str(out/'EXIT.actual.json'),'observer_exit_code':result['observer_exit_code']}),flush=True)
    return 0 if proc is not None and proc.returncode==0 and verified and error is None else 1

if __name__=='__main__': raise SystemExit(main())
