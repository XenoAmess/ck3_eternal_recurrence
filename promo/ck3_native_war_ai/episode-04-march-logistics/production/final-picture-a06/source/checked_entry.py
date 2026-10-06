"""Exact small Root row gate, then delegate to the frozen actual a02 API."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,sys
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def exact(pin):
    p=Path(pin['path'])
    if p.suffix.lower() not in ('.json','.py','.md','.ass') or p.stat().st_size>8*1024*1024:
        raise ValueError('small JSON/source only')
    b=p.read_bytes()
    if len(b)!=pin['bytes'] or hashlib.sha256(b).hexdigest()!=pin['sha256'].lower():
        raise ValueError('changed small binding: '+str(p))
    return p
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('operation',nargs='?',choices=('plan','check','render'),default='plan')
    p.add_argument('--input',type=Path,default=Path(__file__).with_name('pipeline-input-pending-a01.json'))
    p.add_argument('--workdir',type=Path)
    args=p.parse_args()
    try:
        entry=read(Path(__file__).with_name('entry-config.json'))
        source=exact(entry['pipeline'])
        loader=importlib.util.spec_from_file_location('actual_final_BC_a02',source)
        api=importlib.util.module_from_spec(loader);loader.loader.exec_module(api)
        spec=read(args.input)
        if args.operation=='plan':result=api.metadata_plan(spec)
        else:
            freeze_pin=spec['final']['Root_final_story_freeze']
            if freeze_pin is None:raise ValueError('Root final story review pending')
            freeze=read(exact(freeze_pin))
            rows_pin=spec['final'].get('picture_rows_json')
            if rows_pin is None or freeze.get('picture_rows_json')!=rows_pin:
                raise ValueError('Root has not bound exact final card/source rows')
            if read(exact(rows_pin))!=spec['final']['picture_rows']:
                raise ValueError('embedded picture_rows differ from Root-bound JSON')
            if freeze.get('C_controlled_comparison')!='NOT_GRANTED' or freeze.get('winner') is not None:
                raise ValueError('C sampling deviation forbids a strict ABC winner')
            if args.operation=='check':
                ready=api.check(spec)
                result={'state':'ROOT_BOUND_A02_METADATA_READY_FOR_ONE_REVIEW_RENDER',
                        'audio_changed_ids':sorted(ready['changed']),
                        'subtitle_changed_ids':sorted(ready['subtitle_changed']),
                        'picture_refresh_ids':sorted(ready['refresh']),
                        'samples':ready['samples'],'frames':ready['frames'],
                        'media_reads':0,'human_signoff':False}
            else:
                if args.workdir is None:raise ValueError('render needs fresh --workdir')
                result=api.render(spec,args.workdir)
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0
    except (ValueError,KeyError,StopIteration,OSError) as e:
        print(json.dumps({'state':'STOP','reason':str(e),'human_signoff':False},ensure_ascii=False),file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
