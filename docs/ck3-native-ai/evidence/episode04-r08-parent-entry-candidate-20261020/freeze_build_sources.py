"""Prepared exact source copier. Requires a future source-bound execution cap."""
import argparse,datetime,hashlib,json
from pathlib import Path
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for key in ('plan','capacity'):p.add_argument('--'+key,type=Path,required=True);p.add_argument('--'+key+'-sha256',required=True)
 a=p.parse_args();assert digest(a.plan)==a.plan_sha256 and digest(a.capacity)==a.capacity_sha256
 plan=json.loads(a.plan.read_text());cap=json.loads(a.capacity.read_text())
 assert cap.get('admitted') is True and cap.get('budget_status')=='GREEN' and cap.get('source_freeze_execution_admitted') is True and not cap.get('template_only',False)
 assert cap['producer_plan']['sha256']==a.plan_sha256
 now=datetime.datetime.now(datetime.timezone.utc);assert now<datetime.datetime.fromisoformat(cap['hard_deadline_utc'].replace('Z','+00:00'))
 source=Path(plan['source_root']);build=Path(plan['build_root'])
 assert source==Path('C:/ck3-war-episode04-research-20261004-a01/e04-r08-parent-entry-source-p01')
 assert build==Path('C:/w/e04parenta01') and not source.exists() and not build.exists()
 assert Path(cap['approved_source_root']).resolve()==source.resolve() and Path(cap['build_root']).resolve()==build.resolve()
 rows=[];payload=[]
 for row in plan['source_copy']:
  raw=Path(row['path']).read_bytes();assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
  relative=Path(row['relative_path']);assert not relative.is_absolute() and '..' not in relative.parts
  rows.append(dict(row,destination=str(source/relative)));payload.append((source/relative,raw))
 manifest={'schema':'xar.parent-entry.explicit-candidate-source-freeze.v1','machine_id':cap['machine_id'],
  'observed_at_utc':now.isoformat(),'source_kind':'unpublished candidate; not a compiled Git source head',
  'base_head':plan['base_head'],'plan_sha256':a.plan_sha256,'capacity_sha256':a.capacity_sha256,'files':rows}
 data=(json.dumps(manifest,indent=2)+'\n').encode();assert sum(len(b) for _,b in payload)+len(data)<=131072
 source.mkdir(parents=True,exist_ok=False)
 for dest,raw in payload:
  dest.parent.mkdir(parents=True,exist_ok=True)
  with dest.open('xb') as f:f.write(raw)
  assert digest(dest)==hashlib.sha256(raw).hexdigest()
 with (source/'SOURCE-MANIFEST.actual.json').open('xb') as f:f.write(data)
 print(json.dumps({'source_root':str(source),'files':len(rows),'bytes':sum(len(b) for _,b in payload)+len(data),'build_root_created':False}))
if __name__=='__main__':main()
