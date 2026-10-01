"""Preserve exact a08 media, process material and honest audit/delivery boundaries."""
from pathlib import Path
import argparse,mimetypes,json
from xar_promo.operations import preserve_artifact
from xar_promo.project import load_document
from xar_promo.runlog import append_automated_audit_record,append_phase_record
import review_story_a04 as p
def main(run):
    final=p.read(run/'final-artifact.json');machine=p.read(run/'audit/machine-report.json');quality=p.read(run/'frame-review/final-frame-quality.json');delivery=p.read(run/'delivery/final-delivery.json');manifest=run/'native-run/run-manifest.json'
    if not machine['passed'] or quality['verdict']!='PASS_PENDING_HUMAN_REVIEW' or delivery['status']!='CLIENT_METADATA_IN_SYNC_REMOTE_UNVERIFIED':raise ValueError('Actual media/frame/client evidence required')
    for row in (machine['artifact'],quality['subject'],delivery['final_artifact']):
        if row['sha256']!=final['sha256']:raise ValueError('Audit/delivery belongs to other bytes')
    record=preserve_artifact(manifest,Path(final['path']),artifact_id='a08-deliverable',collection='derived',role='deliverable',label=Path(final['path']).name,media_type='video/mp4');records=[record.to_dict()]
    paths=[x for x in sorted(run.rglob('*'))if x.is_file() and 'native-run'not in x.parts and x!=Path(final['path'])]
    selected=[(run/'audit/machine-report.json','a08-machine-report'),(run/'frame-review/final-frame-quality.json','a08-frame-review'),(run/'delivery/final-delivery.json','a08-client-delivery')]
    claimed={path for path,aid in selected}
    for index,path in enumerate(paths,1):
        aid=next((aid for item,aid in selected if item==path),f'a08-process-{index:04d}')
        r=preserve_artifact(manifest,path,artifact_id=aid,collection='derived',role='process-evidence',label=path.name,media_type=mimetypes.guess_type(path.name)[0]or'application/octet-stream');records.append(r.to_dict())
    first=run.parent/'episode02-brown-gold-research-20261002-a01'
    index={'at_utc':p.stamp(),'final_artifact':final,'exact_process_files':[p.ref(x)for x in paths],'earlier_attempts_retained_in_place':str(first),'external_audio':[{'key':u['key'],'raw':u['tts_raw'],'trimmed':u['tts_trimmed']}for c in p.read(run/'timeline.json')['chapters']for u in c['utterances']],'original_capture_roots':['C:/Users/1/ck3-e2-six-gap-research-20261001/root-attempt-12-identifier-append-safe','C:/Users/1/ck3-e2-six-gap-research-20261001/root-attempt-13-reinforcement-full-frame'],'human_signoff':'not-provided','full_1x_human_review':False,'independent_remote_readback':False}
    p.write(run/'retained-process-index.json',index);preserve_artifact(manifest,run/'retained-process-index.json',artifact_id='a08-process-index',collection='derived',role='process-index',label='retained-process-index.json',media_type='application/json')
    append_phase_record(manifest,phase_id='a08-finite-research-video-optimization',status='succeeded',artifact_ids=['a08-deliverable'],detail='Six finite R148 research gaps closed first; R149 full-frame joining recaptured; 25 new boards and 25 changed Chinese cues, with one subsequently corrected A01/R149 transition. Brown/gold packaging, recalculated timing and rebuilt affected audio; old raw notice remains independently labelled.')
    append_automated_audit_record(manifest,check_id='a08-declared-media-checks',status='passed',subject_artifact_id='a08-deliverable',report_artifact_id='a08-machine-report')
    append_phase_record(manifest,phase_id='a08-limited-actual-final-frame-review',status='succeeded',artifact_ids=['a08-frame-review'],detail='Root viewed 34 actual final frames in 9 sheets; no full 1x human viewing or listening signoff.')
    append_phase_record(manifest,phase_id='a08-one-authorized-video-client-sync',status='succeeded',artifact_ids=['a08-client-delivery'],detail='One exact MP4 copied, local SHA matched, client metadata InSync. Independent remote readback remains unperformed.')
    loaded=load_document(manifest,check_files=True)
    if loaded.run.signoffs:raise ValueError('No human signoff occurred in this task')
    p.write(run/'native-preservation-complete.json',{'at_utc':p.stamp(),'manifest':p.ref(manifest),'preserved_artifact_count':len(records)+1,'human_signoffs':0,'full_human_review':'pending','remote_readback':'not-performed'})
    p.command(run,'validate-preserved-run',[__import__('sys').executable,'-X','utf8','-m','xar_promo','validate',str(manifest)])
    print(json.dumps({'preserved_artifacts':len(records)+1,'human_signoffs':0}))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--run',required=True,type=Path);main(a.parse_args().run)
