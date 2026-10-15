"""Build a reviewable control adaptation of the existing runner; no live calls."""
from __future__ import annotations
import argparse,ast,hashlib,importlib.util,json
from pathlib import Path
P=Path(__file__).resolve().parent

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive-root',type=Path,required=True);p.add_argument('--manifest',required=True)
    p.add_argument('--runner-source',required=True);p.add_argument('--runner-sha256',required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    spec=importlib.util.spec_from_file_location('common_t0_validator',P/'validate_common_t0_control.py')
    validator=importlib.util.module_from_spec(spec);spec.loader.exec_module(validator)
    archive=args.archive_root.resolve()
    manifest_path=(archive/args.manifest).resolve()
    validator.need(not Path(args.manifest).is_absolute() and manifest_path.is_relative_to(archive),'manifest must be archive-relative')
    validator.need(manifest_path.stat().st_size<=1024*1024,'manifest exceeds bounded JSON')
    manifest=json.loads(manifest_path.read_text(encoding='utf-8-sig'))
    checked=validator.check(manifest,'baseline',archive);arm=manifest['control']
    SOURCE=validator.resolve(args.runner_source);SOURCE_SHA=args.runner_sha256
    validator.need(SOURCE.suffix=='.py' and SOURCE.stat().st_size<=30*1024,'explicit bounded reviewed Python runner required')
    original=SOURCE.read_bytes()
    if hashlib.sha256(original).hexdigest()!=SOURCE_SHA:raise ValueError('reviewed base runner changed')
    tree=ast.parse(original,filename=str(SOURCE));values={
        'BASE':str(archive),'REPO':str(Path(__file__).resolve().parents[5]),
        'ASSETS':str(validator.resolve(arm['assets_root'])),'RUN_ID':arm['run_id'],'PID':arm['pid'],'CREATED':arm['create_filetime'],
        'EPISODE':arm['episode'],'GEN':arm['generation'],'START':validator.T0,
        'DRIVER_STATE':str(validator.resolve(arm['driver_state_path']))}
    for node in tree.body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            name=node.targets[0].id
            if name in values:
                value=values.pop(name)
                node.value=ast.Call(func=ast.Name(id='Path',ctx=ast.Load()),args=[ast.Constant(value=value)],keywords=[])
                if name not in ('ASSETS','DRIVER_STATE','BASE','REPO'):node.value=ast.Constant(value=value)
    if values:raise ValueError('expected fixed runner binding assignment absent')
    data=ast.unparse(ast.fix_missing_locations(tree))
    old="helper = BASE / 'scoped_requests_a04.py'"
    if data.count(old)!=1:raise ValueError('reviewed helper binding shape changed')
    helper=validator.resolve(arm['request_helper']);validator.need(helper.is_absolute() and helper.is_file(),'actual Root helper required')
    data=data.replace(old,'helper = Path('+repr(str(helper))+')')
    data=data.replace('1 <= args.first_day <= args.last_day <= 30','1 <= args.first_day <= args.last_day <= 21')
    data=data.replace("'day range must be1..30'","'control range must be1..21'")
    # Constrain the existing request machinery, not a new gameplay platform.
    insert='''
_route_check_from_reviewed_runner=check_frame
def check_frame(frame,date=None,paused=True):
    row=_route_check_from_reviewed_runner(frame,date=date,paused=paused)
    need(row.get('current_province_id')==2624 and row.get('route_read_status')=='complete_empty'
        and row.get('route_source_count')==0 and row.get('route_province_ids')==[]
        and row.get('move_target_province_id') is None and row.get('army_state')!='embarked',
        'stationary control changed location/route/boarding state; stop this control')
    return row
_BaseRunner=Runner
class StationaryControlRunner(_BaseRunner):
    def payment(self,prefix,date):
        result=super().payment(prefix,date)
        need(not result[0]['qualified_boarding_debits'],
             'control has a qualified boarding callback; retain conflict, never count this as no-boarding')
        return result
Runner=StationaryControlRunner
'''
    marker="if __name__ == '__main__':"
    if data.count(marker)!=1:raise ValueError('main guard shape changed')
    data=data.replace(marker,insert+'\n'+marker)+'\n'
    compile(ast.parse(data),str(args.output),'exec')
    raw=data.encode('utf-8')
    if len(raw)>30*1024:raise ValueError('adapted candidate exceeds30KiB')
    with args.output.open('xb') as h:h.write(raw)
    receipt={'candidate':{'path':str(args.output),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()},
        'archive_root':str(archive),'manifest':str(args.manifest),'reviewed_runner_sha256':SOURCE_SHA,'baseline_validation':checked,'AST_compile':'PASS',
        'candidate_imported_or_executed':False,'SDK_game_calls':0,
        'Root_next':'Review emitted exact source, run day1 alone with actual own admission; after review continue2..21. No Start/Move/Halt/enable is submitted by this binder.'}
    with args.output.with_suffix('.binding.json').open('x',encoding='utf-8') as h:json.dump(receipt,h,ensure_ascii=False,indent=2)
    print(json.dumps(receipt['candidate'],ensure_ascii=False))

if __name__=='__main__':main()
