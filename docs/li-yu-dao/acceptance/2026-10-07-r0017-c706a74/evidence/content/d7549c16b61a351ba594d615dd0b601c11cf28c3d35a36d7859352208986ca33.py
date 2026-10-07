"""Explicit compact queue wrapper; preserve complete stdout/stderr once."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,subprocess,sys,uuid
from runtime_bindings import load,ref,write

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bindings',required=True,type=Path);p.add_argument('command',nargs=argparse.REMAINDER);a=p.parse_args()
    if not a.command:p.error('explicit queue command required')
    b=load(a.bindings);out=Path(b['dispatch_output'])/'compact';out.mkdir(parents=True,exist_ok=True)
    helper=Path(__file__).with_name('root_queue_ops.py');argv=[sys.executable,'-B','-X','utf8',str(helper),'--bindings',str(a.bindings),'--compact',*a.command]
    started=datetime.now(timezone.utc).isoformat();stamp=uuid.uuid4().hex;proc=subprocess.run(argv,capture_output=True)
    stdout=out/(stamp+'.stdout');stderr=out/(stamp+'.stderr');stdout.write_bytes(proc.stdout);stderr.write_bytes(proc.stderr)
    record={'argv':argv,'helper':ref(helper),'bindings':b['_binding_ref'],'started_utc':started,'ended_utc':datetime.now(timezone.utc).isoformat(),'exit_code':proc.returncode,'stdout':ref(stdout),'stderr':ref(stderr),'automatic_retry':False}
    write(out/(stamp+'.json'),record);print(json.dumps(record,ensure_ascii=False));print(proc.stdout.decode('utf-8','replace'))
    if proc.returncode:print(proc.stderr.decode('utf-8','replace'))
    return proc.returncode

if __name__=='__main__':raise SystemExit(main())
