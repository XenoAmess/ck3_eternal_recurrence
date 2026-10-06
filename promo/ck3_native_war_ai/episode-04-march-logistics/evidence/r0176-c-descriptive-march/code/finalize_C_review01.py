"""PLAN by default. Explicit --finalize consumes completed JSON pins once into fresh output.

No raw/save/media/process/UI/SDK/bus/Git/network calls. Never follows absolute
paths appearing inside evidence bodies. Failures and partial outputs stay intact.
"""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,re,shutil
from datetime import datetime,timezone
from pathlib import Path

def load_core():
    spec=importlib.util.spec_from_file_location('review01_core',Path(__file__).with_name('review01_core.py'))
    core=importlib.util.module_from_spec(spec); spec.loader.exec_module(core); return core

def strict_json(raw):
    def pairs(rows):
        result={}
        for key,value in rows:
            if key in result: raise ValueError('duplicate JSON member '+key)
            result[key]=value
        return result
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda x: (_ for _ in ()).throw(ValueError('nonfinite JSON')))

def execute(base,input_map,output):
    core=load_core(); manifest,objects,cache=core.read_manifest(base)
    core.need(output is not None and not output.exists(),'never-used output directory required')
    core.need(input_map.is_file() and 0<input_map.stat().st_size<=core.MAX_FILE,'bounded terminal input map')
    request=strict_json(input_map.read_bytes())
    core.need(request['schema']=='ck3.e04.C.review01.terminal-inputs.v1','explicit completed terminal schema')
    sources=[]; rawfiles={}; roles={}
    for pin in request['files']:
        role=pin['role']; core.need(re.fullmatch('[a-zA-Z0-9_-]{1,80}',role),'strict unique source role')
        core.need(role not in roles and pin['completed'] is True,'one actual completed source per role')
        p=Path(pin['source']); core.need(p.is_absolute() and p.suffix=='.json','explicit absolute JSON source only')
        core.need(type(pin['bytes']) is int and 0<pin['bytes']<=core.MAX_FILE,'bounded completed JSON source')
        core.need(p.is_file() and p.stat().st_size==pin['bytes'],'actual completed source size '+role)
        raw=p.read_bytes(); core.need(core.sha(raw)==pin['sha256'],'actual completed source SHA '+role)
        value=strict_json(raw); rel='terminal/inputs/'+role+'.json'
        rawfiles[rel]=raw; objects[rel]=value; roles[role]=rel
        sources.append({'role':role,'source':str(p),'relative':rel,'bytes':len(raw),'sha256':core.sha(raw),'completed':True})
    for role in request.get('role_aliases',{}):
        source=request['role_aliases'][role]
        core.need(role not in roles and source in roles,'declared existing role alias only'); roles[role]=roles[source]
    contract={'schema':request['schema'],'roles':roles,'field_bindings':request['field_bindings'],
              'original_terminal_input_map_sha256':core.sha(input_map.read_bytes()),
              'original_terminal_input_map':request,'media_bytes_read':False}
    objects['terminal/terminal-source-contract.json']=contract
    # Validate every known source before creating any output. Existing observer
    # executes only the previously exact-pinned local stdlib code.
    projection=core.derive(base,objects,{**cache,**rawfiles})
    core.need(projection['terminal'] is not None,'actual terminal source projection required')
    output.mkdir(parents=True,exist_ok=False)
    try:
        for rel,raw in cache.items():
            if rel in ('C-review01-values.json','normalized_C_result.json'): continue
            dst=output.joinpath(*core.relative(rel).parts); dst.parent.mkdir(parents=True,exist_ok=True)
            with dst.open('xb') as f: f.write(raw)
        # Old values are history, never silently replaced or relabelled as terminal.
        old=output/'history/preterminal-Review01-values.json'; old.parent.mkdir(parents=True,exist_ok=True)
        with old.open('xb') as f: f.write(cache['C-review01-values.json'])
        with (output/'history/preterminal-normalized-C-result.json').open('xb') as f:
            f.write(cache['normalized_C_result.json'])
        for rel,raw in rawfiles.items():
            dst=output/rel; dst.parent.mkdir(parents=True,exist_ok=True)
            with dst.open('xb') as f: f.write(raw)
        for rel,value in [('terminal/terminal-source-contract.json',contract),
                          ('terminal/completed-source-pins.json',{'files':sources}),
                          ('C-review01-values.json',projection),
                          ('normalized_C_result.json',projection['normalized_C_result'])]:
            dst=output/rel; dst.parent.mkdir(parents=True,exist_ok=True)
            with dst.open('xb') as f: f.write(core.dumps(value))
        spec=importlib.util.spec_from_file_location('C_closed_document',base/'code/write_C_closed_document.py')
        renderer=importlib.util.module_from_spec(spec); spec.loader.exec_module(renderer)
        with (output/'C-DESCRIPTIVE-MARCH.md').open('xb') as f:
            f.write(renderer.document(projection).encode('utf-8'))
        files=[]
        for p in sorted(output.rglob('*')):
            if p.is_file():
                raw=p.read_bytes(); files.append({'path':p.relative_to(output).as_posix(),'bytes':len(raw),'sha256':core.sha(raw)})
        with (output/'manifest.json').open('xb') as f:
            f.write(core.dumps({'schema':'ck3.e04.C.review01.text-manifest.v1','files':files,
                               'scope':'Relative bounded text evidence only; no raw/save data copied.'}))
        # New package replay catches missing relative source or serializer drift.
        finalmanifest,finalobjects,finalcache=core.read_manifest(output)
        core.need(core.derive(output,finalobjects,finalcache)==projection,'portable terminal projection replay')
        return {'status':'C_REVIEW01_CLOSED_DESCRIPTIVE_PACKAGE_CREATED','output':str(output),
                'files':len(files),'terminal_status':projection['terminal']['status'],
                'arrival_interval_raw':projection['terminal']['arrival_interval_raw'],
                'sampling_deviations':len(projection['sampling_deviations']),
                'controlled_comparison_eligibility':'NOT_GRANTED','winner':None,
                'manifest':{'bytes':(output/'manifest.json').stat().st_size,
                            'sha256':core.sha((output/'manifest.json').read_bytes())},
                'raw_save_Game_SDK_UI_bus_Git_or_network_actions':0}
    except Exception as exc:
        failure=output/'FINALIZE-FAILURE.json'
        if not failure.exists():
            with failure.open('xb') as f: f.write(core.dumps({'status':'FAILED_PARTIAL_PRESERVED','error':str(exc)}))
        raise

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--finalize',action='store_true')
    p.add_argument('--base-package',type=Path,default=Path(__file__).resolve().parent.parent)
    p.add_argument('--terminal-inputs',type=Path)
    p.add_argument('--output',type=Path)
    args=p.parse_args()
    if not args.finalize:
        print(json.dumps({'status':'PLAN_ONLY','external_source_reads':0,'output_created':False,
                          'requires':'Completed exact JSON pins, all mandatory terminal source roles, fresh output.',
                          'terminal':None,'winner':None,'controlled_comparison_eligibility':'NOT_GRANTED'})); return 0
    if args.terminal_inputs is None or args.output is None: p.error('--finalize requires --terminal-inputs and --output')
    try:
        print(json.dumps(execute(args.base_package,args.terminal_inputs,args.output),ensure_ascii=False,indent=2)); return 0
    except (OSError,ValueError,KeyError,TypeError,AssertionError) as exc:
        print(json.dumps({'status':'FAIL_C_REVIEW01_FINALIZE_PRESERVED','error':str(exc)},ensure_ascii=False,indent=2)); return 2

if __name__=='__main__': raise SystemExit(main())
