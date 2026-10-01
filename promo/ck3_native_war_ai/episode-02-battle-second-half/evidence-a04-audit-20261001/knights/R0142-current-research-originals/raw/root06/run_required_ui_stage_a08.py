"""Collect required case UI after verifying stock in-combat selection routing."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
CONSUMER = ROOT / 'scoped_ui_research_a08.py'
SHA = '169EE7EA1DBF979B3EBE0C6221A4287B908E4F0F7BFA01A14DB86AC5D671F640'
def require(ok,msg):
    if not ok: raise RuntimeError(msg)
def ident(p): return {'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest().upper()}
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as stream: json.dump(v,stream,ensure_ascii=False,indent=2);stream.write('\n')
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bindings',type=Path,required=True)
    parser.add_argument('--phase',choices=['before','after'],required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    require(ident(CONSUMER)['sha256']==SHA,'Reviewed controller changed')
    config=read(args.bindings);evidence=Path(config['live_root'])/'scoped-ui-research-attempt-01'
    operations=[];retained=[]
    require((evidence/'variable-monitor-begin.json').is_file() and not (evidence/'variable-monitor-finish-intent.json').exists(),'Independent monitor must be armed')
    if args.phase=='before':
        require(not (evidence/'one-day-intent.json').exists(),'Before UI must precede any day')
        route=read(evidence/'actual-army-combat-route-readonly.json')
        body=route['readback_body']
        require(route['current_original_combat_verified'] is True and body['current_subject_id']==config['combat_id'] and body['effective_visible'] is True and route['source_values']['date_raw']==config['before_date_raw'],'Current original combat route not verified')
        for name in ('before-victim-character-original-ui-binding.json','before-killer-character-original-ui-binding.json'):
            record=evidence/name;old=read(record)
            require(old['source_binding']==ident(args.bindings) and old['phase']=='before','Existing role UI is not this current run')
            require(ident(Path(old['image']['image']['path']))==old['image']['image'],'Existing original role pixels changed')
            retained.append(ident(record))
        retained.append(ident(evidence/'actual-army-combat-route-readonly.json'))
    else:
        require((evidence/'one-day-finished.json').is_file(),'After UI requires completed original one-day trace')
        operations.append(('pre-ui-checkpoint',['--mode','extra-checkpoint']))
        for role in ('victim','killer'):
            operations.append((role+'-character',['--mode','ui','--window-kind','character','--character-role',role]))
    for kind in ('knights','combat'):
        operations.append((kind,['--mode','ui','--window-kind',kind]))
    operations.append(('combat-fit',['--mode','fit']))
    for side in ('left','right'):
        operations.append((side+'-knights-tooltip',['--mode','hover','--ui-side',side]))
    operations.append(('save',['--mode','save']))
    args.output_dir.mkdir(exist_ok=False)
    write(args.output_dir/'stage-intent.json',{'at_utc':datetime.now(timezone.utc).isoformat(),'phase':args.phase,
        'bindings':ident(args.bindings),'controller':ident(CONSUMER),'helper':ident(Path(__file__)),
        'retained_same_run_role_UI':retained,'operations':operations,
        'stock_route': 'Selecting this in-combat unit opens combat_window; an army_window frame is not a prerequisite for the six requested gaps',
        'prior_failed_army_visibility_check_stays_preserved':True,
        'army_selection_retried':False,'never_advances_a_day':True,'human_movie_signoff':False})
    receipts=[]
    for i,(label,flags) in enumerate(operations,1):
        prefix=f'{i:02d}-{args.phase}-{label}'
        argv=[sys.executable,'-X','utf8=0','-B',str(CONSUMER),'--bindings',str(args.bindings.resolve()),*flags,'--phase',args.phase,'--label',args.phase+'-'+label]
        if label=='pre-ui-checkpoint':
            argv=[sys.executable,'-X','utf8=0','-B',str(ROOT/'preserve_paused_ui_checkpoint_a06.py'),'--bindings',str(args.bindings.resolve()),'--phase',args.phase,'--label',args.phase+'-'+label]
        write(args.output_dir/(prefix+'-argv.json'),{'at_utc':datetime.now(timezone.utc).isoformat(),'argv':argv})
        out=args.output_dir/(prefix+'-stdout.bin');err=args.output_dir/(prefix+'-stderr.bin')
        print('start '+prefix,flush=True)
        with out.open('xb') as stdout,err.open('xb') as stderr: result=subprocess.run(argv,stdout=stdout,stderr=stderr)
        receipt={'argv':argv,'returncode':result.returncode,'stdout':ident(out),'stderr':ident(err)}
        write(args.output_dir/(prefix+'-result.json'),receipt);receipts.append(receipt)
        print('complete '+prefix+' exit='+str(result.returncode),flush=True)
        require(result.returncode==0,'Required UI stage stopped; preserve originals and inspect, never retry the action')
    write(args.output_dir/'completion.json',{'phase':args.phase,'retained_inputs':retained,'processes':receipts,
        'status':'REQUIRED_CASE_UI_CAPTURED_PENDING_ACTUAL_ROOT_PIXEL_REVIEW','original_pixels_actually_reviewed':False,'day_advance_count':0,'human_movie_signoff':False})
if __name__=='__main__': main()
