"""Run one reviewed current-run mode with create-only raw process evidence."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import subprocess
import sys
ROOT=Path(__file__).resolve().parent
def ident(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest().upper()}
def write(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as stream:json.dump(v,stream,indent=2);stream.write('\n')
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=['save','finish'],required=True)
    parser.add_argument('--phase',choices=['before','after'])
    parser.add_argument('--label',required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    helper=ROOT/'scoped_ui_research_a09.py'
    if ident(helper)['sha256']!='E51DC8EE492815EDB79A31FB1C84B70D8826D8FC1B3EEA3EC70582D7955D0F36':raise RuntimeError('Current controller bytes changed')
    argv=[sys.executable,'-X','utf8=0','-B',str(helper),'--bindings',str(ROOT/'current-run-bindings.json'),'--mode',args.mode,'--label',args.label]
    if args.phase:argv+=['--phase',args.phase]
    args.output_dir.mkdir(exist_ok=False)
    write(args.output_dir/'intent.json',{'at_utc':datetime.now(timezone.utc).isoformat(),'argv':argv,'controller':ident(helper),'binding':ident(ROOT/'current-run-bindings.json')})
    out=args.output_dir/'stdout.bin';err=args.output_dir/'stderr.bin'
    with out.open('xb') as stdout,err.open('xb') as stderr:r=subprocess.run(argv,stdout=stdout,stderr=stderr)
    write(args.output_dir/'result.json',{'argv':argv,'returncode':r.returncode,'stdout':ident(out),'stderr':ident(err)})
    print(json.dumps({'returncode':r.returncode,'stdout_summary':out.read_bytes().decode('utf-8',errors='replace')[-4000:],'stderr_summary':err.read_bytes().decode('utf-8',errors='replace')[-2000:]}))
    raise SystemExit(r.returncode)
if __name__=='__main__':main()
