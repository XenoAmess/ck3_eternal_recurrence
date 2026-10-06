"""Default PLAN. Verify bounded relative JSON metadata; never open media paths."""
import argparse,hashlib,json
from pathlib import Path,PurePosixPath
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');a=p.parse_args()
 if not a.verify:print(json.dumps({'status':'PLAN_ONLY','source_reads':0}));return 0
 try:
  root=Path(__file__).resolve().parent;manifest=json.loads((root/'manifest.json').read_bytes());objects={}
  for row in manifest['files']:
   relative=PurePosixPath(row['path'])
   if relative.is_absolute() or '..' in relative.parts or ':' in row['path'] or '\\' in row['path'] or relative.suffix!='.json':raise ValueError('safe relative JSON only')
   path=root.joinpath(*relative.parts)
   if not path.resolve().is_relative_to(root) or not 0<row['bytes']<=2*1024*1024:raise ValueError('bounded local leaf')
   raw=path.read_bytes()
   if len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('exact metadata bytes')
   objects[row['path']]=json.loads(raw)
  report=objects['unique4-report.json'];seal=objects['closed-recorder.json'];review=objects['Root-four-coded-review.json']
  if report['state']!='PASS' or seal['state']!='NORMAL_TREE_EMPTY' or seal['job']['returncode']!=0 or seal['job']['job_active_processes']!=0:raise ValueError('actual source audit and closed recorder state')
  if report['source_identity']!=seal['raw'] or review['closed_raw_reported_identity_reused_without_read_hash']!=seal['raw']:raise ValueError('same sealed raw metadata identity')
  report_pin=next(r for r in manifest['files'] if r['path']=='unique4-report.json')
  if review['unique_four_media_audit']['bytes']!=report_pin['bytes'] or review['unique_four_media_audit']['sha256']!=report_pin['sha256']:raise ValueError('Root exact report join')
  if len(review['images'])!=4 or not all(row['Root_directly_viewed_exact_original'] is True for row in review['images']):raise ValueError('four actual Root original reviews')
  if any(row['exact_native_event_PTS'] is not False for row in review['images']) or review['human_signoff'] is not False or review['continuous_clean_span'] is not False:raise ValueError('no event/clean/full-film credit')
  print(json.dumps({'status':'PASS_METADATA_ONLY_S04_SOURCE_JOINS','source_files':len(objects),'raw_media_or_native_observation_reads':0,'new_media_audit_or_clean_human_credit':0,'winner':None},indent=2));return 0
 except (OSError,ValueError,KeyError,TypeError) as e:print(json.dumps({'status':'FAIL_METADATA_ADDON','error':str(e)}));return 2
if __name__=='__main__':raise SystemExit(main())
