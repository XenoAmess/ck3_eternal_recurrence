"""Build Feast cost source/serializer fixtures offline with x64 MSVC."""
from pathlib import Path
import argparse
import sys, importlib.util, subprocess, hashlib, json
root=Path(__file__).resolve().parents[3]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--new-only',action='store_true')
args=parser.parse_args()
out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
sys.stdout.reconfigure(encoding='utf-8')
spec=importlib.util.spec_from_file_location('msvc',root/'tools/run_native_msvc.py')
msvc=importlib.util.module_from_spec(spec);spec.loader.exec_module(msvc)
environment=msvc.child_environment(out)
environment,tools=msvc.initialize_msvc(msvc.visual_studio_installation(None,environment),out,environment)
bridge=root/'ck3_autonomous_player/native_bridge'
common=[bridge/'src'/x for x in ['activity_cost_slot12_passive_v1.cpp','activity_planner_diag_v1.cpp','activity_stage5_gold_cost_v1.cpp','activity_stage5_feast_full_cost_v1.cpp','activity_stage5_canstart_read_v1.cpp','activity_stage5_canstart_failure_display_v1.cpp','ck3_12002_activity_feast_cost_private_transport_v1.cpp']]
tests=['ck3_12002_activity_feast_costs_test.cpp','activity_stage5_feast_full_cost_v1_test.cpp','activity_cost_slot12_passive_v1_test.cpp']
if args.new_only: tests=tests[:1]
results=[]
for mode in ['Od','O2']:
    cell=out/mode;cell.mkdir(exist_ok=True)
    for test in tests:
        exe=cell/Path(test).with_suffix('.exe').name
        command=[tools['cl'],'/nologo','/std:c++20','/EHsc','/W4','/WX','/utf-8',f'/{mode}','/I'+str(bridge/'include'),*map(str,common),str(bridge/'src'/test),'/Fe'+str(exe)]
        compiled=subprocess.run(command,cwd=cell,env=environment,capture_output=True)
        (cell/(test+'.compile.log')).write_bytes(compiled.stdout+compiled.stderr)
        row={'mode':mode,'test':test,'compile_returncode':compiled.returncode}
        if compiled.returncode==0:
            run=subprocess.run([str(exe)],cwd=cell,env=environment,capture_output=True)
            (cell/(test+'.run.log')).write_bytes(run.stdout+run.stderr)
            row.update(run_returncode=run.returncode,exe_sha256=hashlib.sha256(exe.read_bytes()).hexdigest())
            if test.startswith('ck3_12002') and run.returncode==0:
                wire=json.loads(run.stdout.decode('utf-8')); row['wire_schema']=wire['schema']
                assert wire['resources']['piety']['configured_cost_raw']==-100000
                assert wire['resources']['gold']['configured_cost_raw']==18500000
                assert wire['final_can_start'] is False
                (cell/'fullcost-wire.json').write_text(json.dumps(wire,indent=2)+'\n',encoding='utf-8')
        else:
            print((compiled.stdout+compiled.stderr).decode('utf-8',errors='replace')[-4000:])
        results.append(row);print(json.dumps(row))
        if compiled.returncode: break
report={'status':'GREEN' if all(x.get('run_returncode')==0 for x in results) and len(results)==2*len(tests) else 'RED','local_ck3_contacted':False,'readiness':'static-ready','results':results,'sources':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in common+[bridge/'src'/x for x in tests]}}
(out/'fixture-result.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
raise SystemExit(0 if report['status']=='GREEN' else 1)
