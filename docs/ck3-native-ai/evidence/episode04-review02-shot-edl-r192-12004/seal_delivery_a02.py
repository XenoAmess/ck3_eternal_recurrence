from pathlib import Path
from datetime import datetime, timezone
import hashlib,json
p=Path(__file__).resolve().parent
def j(name):return json.loads((p/name).read_text(encoding='utf-8'))
edl=j('EDIT-CANDIDATES.actual-a01.json'); plan=j('NATIVE-PLAN.actual.json'); pins=j('INPUTPINS.actual.json')
assert len(edl['cues'])==len({r['id'] for r in edl['cues']})==69
assert sum(r['timeline_frames'][1]-r['timeline_frames'][0] for r in edl['cues'])==58406
assert all(r['capture_clip'] is None and r['movie_visual_artifact_id'] is None and r['continuous_clean'] is False for r in edl['cues'])
assert all(c.get('native_event_PTS') is None for c in edl['candidates'])
assert plan['exit_code']==2 and 'Composition requires preserved production inputs in a native run' in plan['stderr']
assert plan['new_run_created'] is False and plan['workdir_exists_after'] is False
for r in pins['fresh_small_file_pins']:
 b=Path(r['path']).read_bytes();assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']
files=[]
for f in sorted(p.iterdir()):
 if f.is_file():
  b=f.read_bytes();files.append({'path':str(f),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
base=sum(r['bytes'] for r in files)
result={'schema':'xar.e04.review02.small-candidate-edl-delivery.v1','machine_id':edl['machine_id'],'observed_at_utc':datetime.now(timezone.utc).isoformat(),'source_head':edl['source_head'],'files':files,'checks':{'original_cues':69,'frames':58406,'candidate_groups':len(edl['candidates']),'all_capture_bindings_pending':True,'actual_cli_plan_missing_native_inputs_exit2':True,'small_source_pins_unchanged':True,'main_tree_modified':False,'SDK_desktop_media_provider_calls':0,'raw_audio_PNG_body_reads':0,'new_native_run_created':False},'bytes_after_seal':0,'limit_bytes':131072}
while True:
 b=(json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf-8');n=base+len(b)
 if n==result['bytes_after_seal']:break
 result['bytes_after_seal']=n
assert n<=131072
with(p/'ROOT-DELIVERY.actual-a02.json').open('xb')as f:f.write(b)
print(json.dumps({'path':str(p/'ROOT-DELIVERY.actual-a02.json'),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'total_bytes':n},ensure_ascii=False))
