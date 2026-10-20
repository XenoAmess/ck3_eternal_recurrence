"""Read-only public producer/SYSTEM verification, then new metadata only."""
import argparse,datetime,hashlib,importlib.util,json
from pathlib import Path
B=Path('C:/w/e04parentdr02');BC=B/'build-a01'
S=Path('C:/ck3-war-episode04-research-20261004-a01/e04-r08-parent-dr-source-p02')
M='desktop-3fevhd2-1c74096080'
def pin(p):
 p=Path(p);size=p.stat().st_size;assert size<=524288
 with p.open('rb') as f:b=f.read(524289)
 assert len(b)==size;return dict(path=str(p),bytes=size,sha256=hashlib.sha256(b).hexdigest())
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for k in ('plan','plan-sha256','capacity','capacity-sha256','source-manifest-sha256'):p.add_argument('--'+k,required=True)
 a=p.parse_args();cp=pin(a.capacity);assert cp['sha256']==a.capacity_sha256
 c=json.loads(Path(a.capacity).read_bytes());assert c['machine_id']==M and c['admitted'] and c['budget_status']=='GREEN' and c['build_execution_admitted']
 assert Path(c['build_root'])==BC and Path(cp['path']).parent==B/'capacity'
 pp=pin(a.plan);assert pp['sha256']==a.plan_sha256 and c['producer_plan']==pp
 plan=json.loads(Path(a.plan).read_bytes());mp=pin(S/'SOURCE-MANIFEST.actual.json');assert mp['sha256']==a.source_manifest_sha256
 manifest=json.loads((S/'SOURCE-MANIFEST.actual.json').read_bytes())
 expected=[dict(path=str(S/r['relative_path']),bytes=r['bytes'],sha256=r['sha256']) for r in plan['source_copy']]
 assert manifest['producer_plan']==pp and manifest['machine_id']==M and manifest['files']==expected and len(expected)==14
 for ref in manifest['files']:
  actual=pin(ref['path']);assert all(actual[k]==ref[k] for k in ('path','bytes','sha256'))
 wp=B/'build-execution-a01/ORIGINAL-WAIT.actual-a01.json';wait=json.loads(wp.read_bytes())
 assert wait['machine_id']==M and wait['original_Popen'] is True and wait['original_wait'] is True and wait['exit_code']==0
 assert wait['argv']==plan['phase_argv']['MSVC-build-and-ordinary-SYSTEM']
 report=json.loads((BC/'native-msvc-result.json').read_bytes());assert report['build_succeeded'] is True and Path(report['source_dir'])==S
 record=dict(machine_id=M,observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),returncode=0,argv=wait['argv'],source_pins=manifest['files'],source_manifest=mp,source_kind=plan['source_kind'],original_wait=pin(wp),producer=pin(BC/'native-msvc-result.json'))
 recordpath=B/'MACHINE-BUILD.actual.json'
 with recordpath.open('x',encoding='utf-8',newline='\n') as f:json.dump(record,f,indent=2);f.write('\n')
 spec=importlib.util.spec_from_file_location('frozen_parent_cold_runner',S/'run_parent_entry_cold.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 opts=argparse.Namespace(build_dir=BC,machine_build_record=recordpath)
 gate=module.verify_build(opts,M);gate.update(schema='xar.e04.parent-dr.exact-SYSTEM-gate.v1',source_manifest=mp,source_kind=plan['source_kind'],new_project_EXE_executions=0,cold_qualification=False)
 out=B/'EXECUTION-GATE.actual.json'
 with out.open('x',encoding='utf-8',newline='\n') as f:json.dump(gate,f,indent=2);f.write('\n')
 print(json.dumps(dict(machine_build_record=pin(recordpath),SYSTEM_gate=pin(out))))
if __name__=='__main__':main()
