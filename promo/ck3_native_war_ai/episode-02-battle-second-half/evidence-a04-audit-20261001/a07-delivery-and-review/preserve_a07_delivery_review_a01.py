from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys,subprocess
from xar_promo.operations import preserve_artifact
from xar_promo.project import load_document
from xar_promo.runlog import append_phase_record
r=Path(__file__).resolve().parent
run=Path('C:/Users/1/AppData/Local/ck3-review-render/episode02-brown-gold-native-supplement-20261001-a01')
audit=Path('C:/Users/1/ck3-a07-native-supplement-media-audit-20261001/attempt-01')
review=Path('C:/Users/1/ck3-a07-evidence-plan-20261001/attempt-05-pending-human-review')
manifest=run/'native-run/run-manifest.json'
def ref(p):return {'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest().upper()}
def read(p):return json.loads(p.read_text(encoding='utf-8'))
final=read(run/'final-artifact.json');expected={k:final[k] for k in ['path','bytes','sha256']}
assert expected['sha256']=='634CFD093F17C8B027DA38AE6C3462362A485A4CDF6AC2B0FE14BED5CCC3C342' and ref(Path(expected['path']))==expected
machine=read(audit/'delivery-gate-report-a01.json');quality=read(audit/'delivery-quality-report-a01.json')
assert machine['machine_condition_status']=='PASS' and machine['final_artifact']['sha256']==expected['sha256']
assert quality['verdict']=='PASS_PENDING_HUMAN_REVIEW' and quality['subject']==expected
delivery=read(run/'delivery/final-delivery.json')
assert delivery['status']=='CLIENT_METADATA_IN_SYNC_REMOTE_UNVERIFIED' and delivery['files_transferred']==1
assert all(delivery['last_client_sample']['checks'].values()) and delivery['remote_independent_readback_performed'] is False
pkg=read(review/'pending-human-review/review-package.json');completion=read(review/'completion.json')
assert completion['state']=='pending-human-review' and completion['approval_granted'] is False
assets=[]
for d in [audit,run/'delivery',review,r.parent/'a07-pending-review-helper-other-a02']:
 for p in sorted(d.rglob('*')):
  if p.is_file():assets.append(ref(p))
index=run/'post-render-retained-process-index-a01.json'
with index.open('x',encoding='utf-8',newline='\n') as f:json.dump({'schema':'ck3.a07.retained-post-render-assets/v1','at':datetime.now(timezone.utc).isoformat(),'subject':expected,'files':assets,'old_assets_deleted_or_overwritten':False,'human_signoff':'not-provided'},f,ensure_ascii=False,indent=2);f.write('\n')
before=read(manifest);assert not before['signoffs']
items=[('media-audit',audit/'delivery-gate-report-a01.json'),('limited-frame-quality',audit/'delivery-quality-report-a01.json'),('one-file-client-sync',run/'delivery/final-delivery.json'),('pending-review-package',review/'pending-human-review/review-package.json'),('pending-review-template',review/'pending-human-review/review-template.json'),('bound-media-probe',review/'bound-media-probe-v1.json'),('review-execution',review/'completion.json'),('retained-post-process-index',index)]
saved=[]
for key,p in items:
 artifact_id='a07-post-'+key
 assert all(x['id']!=artifact_id for x in before['artifacts'])
 preserve_artifact(manifest,p,artifact_id=artifact_id,collection='derived',role=key,label=p.name,media_type='application/json')
 saved.append({'artifact_id':artifact_id,'source':ref(p)})
append_phase_record(manifest,phase_id='external-machine-checks-client-sync-and-pending-review',status='succeeded',artifact_ids=[x['artifact_id'] for x in saved],detail='External210structural/pixelchecks andfullAVdecode/AACidentity passed; exactoneMP4 clientmetadata in-sync; pendingreviewpack36isolatedframes only. No human1x/listening/signoff or independentremote readback.')
loaded=load_document(manifest,check_files=True)
after=read(manifest);assert not after['signoffs'] and len(after['artifacts'])==len(before['artifacts'])+8
result={'at':datetime.now(timezone.utc).isoformat(),'result':'POST_RENDER_EVIDENCE_PRESERVED_PENDING_HUMAN_REVIEW','manifest':ref(manifest),'before_artifacts':len(before['artifacts']),'after_artifacts':len(after['artifacts']),'native_integrity_audits':len(after['audits']),'signoffs':0,'saved':saved,'retained_post_process_index':ref(index),'client_sync_status':delivery['status'],'human1x_full_watch':False,'human_full_listen':False,'remote_independent_readback':False}
out=run/'post-render-preservation-complete-a01.json'
with out.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'result':result['result'],'receipt':ref(out),'artifacts':result['after_artifacts'],'signoffs':0}))
