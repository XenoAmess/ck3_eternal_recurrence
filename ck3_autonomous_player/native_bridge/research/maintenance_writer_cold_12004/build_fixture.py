"""Build this standalone project with the standard producer and a host-labelled receipt."""
from pathlib import Path
import argparse,datetime as dt,hashlib,json,subprocess,sys
def require(ok,message):
    if not ok:raise RuntimeError(message)
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',type=Path,required=True);p.add_argument('--build-dir',type=Path,required=True);p.add_argument('--jobs',type=int,default=2);a=p.parse_args()
repo=a.repo.resolve();build=a.build_dir.resolve();source=Path(__file__).resolve().parent
require(not build.exists(),'New external build directory required')
sys.dont_write_bytecode=True;sys.path.insert(0,str(repo));from tools.ck3_live_run_id import current_machine_id
machine=current_machine_id();pins=[dict(path=str(source/name),bytes=(source/name).stat().st_size,sha256=hashlib.sha256((source/name).read_bytes()).hexdigest()) for name in ['CMakeLists.txt','cold_observer.cpp','cold_target.cpp','synthetic_write.asm']]
argv=[sys.executable,'-B','-X','utf8',str(repo/'tools/run_native_msvc.py'),'--source-dir',str(source),'--build-dir',str(build),'--configuration','Release','--jobs',str(a.jobs),'--defender-external-candidate','e04-maintenance-writer-cold-12004','--configure','--build','--target','maintenance_writer_cold_target','maintenance_writer_cold_observer']
run=subprocess.run(argv,cwd=repo,check=False)
record=dict(machine_id=machine,observed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),argv=argv,source_pins=pins,returncode=run.returncode,project_EXE_executed=False)
if build.exists():
    with (build/'MACHINE-BUILD.actual.json').open('x',encoding='utf-8') as f:json.dump(record,f,indent=2);f.write('\n')
raise SystemExit(run.returncode)
