"""Exact p01 source snapshot or read-only verification. No compiler/EXE action."""
import argparse,datetime,hashlib,json,os,sys
from pathlib import Path
S=Path('C:/ck3-war-episode04-research-20261004-a01/e04-r08-parent-dr-source-p01')
B=Path('C:/w/e04parentdr01');BOOT=B/'capacity';BC=B/'build-a01'
M='desktop-3fevhd2-1c74096080'
def now():return datetime.datetime.now(datetime.timezone.utc)
def data(p,limit=262144):
 p=Path(p);before=p.stat();assert before.st_size<=limit
 assert not getattr(before,'st_file_attributes',0)&0x400
 with p.open('rb') as f:raw=f.read(limit+1)
 after=p.stat();assert len(raw)==before.st_size and len(raw)<=limit
 assert (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)
 return raw
def pin(p):
 p=Path(p).resolve();raw=data(p);return dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def exact(ref):
 raw=data(ref['path']);assert len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'];return raw
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for key in ('plan','plan-sha256','capacity','capacity-sha256'):ap.add_argument('--'+key,required=True)
 ap.add_argument('--fresh-sha256');ap.add_argument('--verify-only',action='store_true');ap.add_argument('--manifest-sha256');a=ap.parse_args()
 cp=pin(a.capacity);assert cp['sha256']==a.capacity_sha256 and Path(cp['path']).parent==BOOT
 cap=json.loads(data(a.capacity));assert cap['admitted'] is True and cap['budget_status']=='GREEN' and cap['machine_id']==M
 assert cap['aggregate_ceiling_bytes']==67108864 and cap['component_ceiling_bytes']=={'source':2097152,'build':31457280,'protocol':33554432}
 assert Path(cap['component_roots']['source']).resolve()==S and Path(cap['component_roots']['build']).resolve()==B and Path(cap['build_root']).resolve()==BC
 deadline=datetime.datetime.fromisoformat(cap['hard_deadline_utc'].replace('Z','+00:00'));assert now()<deadline<=datetime.datetime(2026,10,20,19,15,tzinfo=datetime.timezone.utc)
 pp=pin(a.plan);assert pp['sha256']==a.plan_sha256 and Path(pp['path']).parent==BOOT
 assert all(cap['producer_plan'][k]==pp[k] for k in ('path','bytes','sha256'))
 plan=json.loads(data(a.plan));assert plan['machine_id']==M and Path(plan['source_root']).resolve()==S and Path(plan['build_root']).resolve()==BC
 exact(plan['installed_policy'])
 for ref in plan['entry_dependencies']:exact(ref)
 rows=plan['source_copy'];names=[r['relative_path'] for r in rows]
 assert len(rows)==14 and len(set(names))==14
 assert all(Path(n).name==n and n not in ('','.','..') and not Path(n).is_absolute() for n in names)
 assert any(Path(x['path']).resolve()==Path(__file__).resolve() and pin(__file__)['sha256']==x['sha256'] for x in plan['entry_dependencies'])
 blobs=[exact(r) for r in rows];outputs=[dict(path=str(S/r['relative_path']),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()) for r,raw in zip(rows,blobs)]
 manifest_path=S/'SOURCE-MANIFEST.actual.json'
 if a.verify_only:
  assert a.manifest_sha256 and S.is_dir() and S.resolve()==S and not getattr(S.lstat(),'st_file_attributes',0)&0x400
  mp=pin(manifest_path);assert mp['sha256']==a.manifest_sha256
  manifest=json.loads(data(manifest_path));assert manifest['producer_plan']==pp and manifest['files']==outputs and manifest['machine_id']==M
  for ref in outputs:exact(ref)
  assert {str(p.resolve()) for p in S.iterdir()}=={str(Path(x['path']).resolve()) for x in outputs}|{str(manifest_path.resolve())}
  print(json.dumps(dict(machine_id=M,observed_at_utc=now().isoformat(),source_manifest=mp,actual_destination_pins=outputs,verified_frozen_source_files=14,read_only=True)));return
 assert cap.get('source_freeze_execution_admitted') is True,'Source control admission is not source-copy admission'
 assert not os.path.lexists(S) and not os.path.lexists(BC),'Never overwrite/relabel a previous source or build child'
 assert a.fresh_sha256
 freshraw=sys.stdin.buffer.read(65537);assert len(freshraw)<=65536 and hashlib.sha256(freshraw).hexdigest()==a.fresh_sha256
 fresh=json.loads(freshraw);assert fresh['machine_id']==M and fresh['phase']=='source-copy' and fresh['admitted'] is True and fresh['budget_status']=='GREEN' and fresh['capacity']==cp
 age=(now()-datetime.datetime.fromisoformat(fresh['observed_at_utc'].replace('Z','+00:00'))).total_seconds();assert 0<=age<=30
 expected={str(Path(x['path']).resolve()):x for x in cap['bootstrap_files']};expected[cp['path']]=cp
 actual={};total=0
 assert BOOT.is_dir() and not getattr(B.lstat(),'st_file_attributes',0)&0x400
 for directory,dirs,files in os.walk(B):
  for name in dirs:
   p=Path(directory)/name;assert p==BOOT,'First-copy bootstrap is flat exact capacity leaves only';assert not getattr(p.lstat(),'st_file_attributes',0)&0x400
  for name in files:
   p=Path(directory)/name;assert p.is_relative_to(BOOT);ref=pin(p);actual[ref['path']]=ref;total+=ref['bytes']
 assert total<=65536 and set(actual)==set(expected)
 for path,ref in expected.items():assert all(actual[path][k]==ref[k] for k in ('path','bytes','sha256'))
 manifest=dict(schema='xar.e04.parent-dr.frozen-source.v1',machine_id=M,observed_at_utc=now().isoformat(),source_kind=plan['source_kind'],producer_plan=pp,capacity=cp,original_a02_freeze=plan['source_freeze'],source_copy_fresh_sha256=a.fresh_sha256,source_inputs=rows,files=outputs,compiled=False,native_qualification=False)
 encoded=(json.dumps(manifest,indent=2)+'\n').encode();assert sum(map(len,blobs))+len(encoded)<=2097152
 S.mkdir()
 for row,raw in zip(rows,blobs):
  with (S/row['relative_path']).open('xb') as f:f.write(raw)
 with manifest_path.open('xb') as f:f.write(encoded)
 for ref in outputs:exact(ref)
 print(json.dumps(dict(machine_id=M,observed_at_utc=now().isoformat(),source_manifest=pin(manifest_path),actual_destination_pins=outputs,source_copy_files=14,source_bytes=sum(map(len,blobs))+len(encoded),build_child_created=False,source_kind=plan['source_kind'],compiled=False)))
if __name__=='__main__':main()
