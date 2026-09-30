"""Preserve actual six-chapter composition and exact independent evidence.

No manual approval is created. External inputs retain their original locations.
"""
from pathlib import Path
import argparse,json,hashlib,mimetypes
from xar_promo.operations import preserve_artifact
from xar_promo.runlog import append_phase_record,append_automated_audit_record
from xar_promo.project import load_document

def ref(path):
    h=hashlib.sha256();path=Path(path)
    with path.open('rb') as f:
        for data in iter(lambda:f.read(1024*1024),b''):h.update(data)
    return {'path':str(path),'bytes':path.stat().st_size,'sha256':h.hexdigest().upper()}
def write(path,data):
    with path.open('x',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2)
def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--machine',type=Path,required=True);p.add_argument('--quality',type=Path,required=True);a=p.parse_args()
    run=a.run;manifest=run/'native-run/run-manifest.json';rows=[]
    def preserve(path,aid,role):
        record=preserve_artifact(manifest,path,artifact_id=aid,collection='derived',role=role,label=path.name,media_type=mimetypes.guess_type(path.name)[0] or 'application/octet-stream')
        rows.append({'source':ref(path),'preserved':record.to_dict()});return record
    final=json.loads((run/'final-artifact.json').read_text(encoding='utf-8'))
    machine=json.loads(a.machine.read_text(encoding='utf-8-sig'));quality=json.loads(a.quality.read_text(encoding='utf-8-sig'))
    if machine.get('machine_condition_status')!='PASS' or machine['final_artifact']['sha256']!=final['sha256']:raise ValueError('exact final media machine PASS missing')
    if quality.get('verdict')!='PASS_PENDING_HUMAN_REVIEW' or quality['subject']['sha256']!=final['sha256'] or quality['outstanding_blockers_in_review_scope']:raise ValueError('exact final media limited product PASS missing')
    preserve(Path(final['path']),'a04-deliverable','deliverable')
    sourcefiles=[(run/'timeline.json','timeline'),(run/'sources/story.json','narration-script'),(run/'sources/environment.json','environment'),(run/'sources/producer-source.py','composer-source'),(run/'edit.json','edit-plan'),(run/'input-freeze.json','input-freeze'),(run/'edit-input-freeze.json','edit-freeze'),(run/'release-query.json','release-query'),(run/'chapter-render-receipts.json','chapters'),(run/'tts-raw-receipts.json','tts-receipts'),(run/'final-artifact.json','final-identity')]
    for path,role in sourcefiles:preserve(path,'a04-'+role,role)
    for c in json.loads((run/'timeline.json').read_text(encoding='utf-8'))['chapters']:
        root=run/'chapters'/c['id'];preserve(root/'chunk-receipts.json','a04-'+c['id']+'-chunks','render-receipts')
        for path in sorted(root.glob('chunk-*/*')):
            if path.name in ['subtitles.ass','filter.txt']:preserve(path,'a04-'+c['id']+'-'+path.parent.name+'-'+path.stem.replace('.','-'),'subtitles' if path.suffix=='.ass' else 'composition-filter')
    for path in sorted((run/'logs').glob('*.receipt.json')):preserve(path,'a04-command-'+path.stem.replace('.','-'),'command-receipt')
    for name in ['final-join.argv.json','final-join.stdout.txt','final-join.stderr.txt']:
        path=run/'logs'/name;preserve(path,'a04-'+name.replace('.','-'),'command-audit')
    for name in ['bound-media-probe.json','bound-probe-provenance.json']:
        preserve(run/name,'a04-'+name.replace('.','-'),'media-probe')
    frames=run/'shared-actual-frames-a01'
    preserve(frames/'shared-frames.json','a04-shared-frames','review-package')
    for path in sorted(frames.glob('*.png')):preserve(path,'a04-frame-'+path.stem,'frame')
    preserve(a.machine,'a04-machine-report','machine-audit');preserve(a.quality,'a04-product-report','product-review')
    index={'kind':'permanently-retained-process-index','subject':final,'sources':[],'external_input_refs':[],'human_signoff':'not-provided'}
    for path in sorted(run.rglob('*')):
        if path.is_file() and 'native-run' not in path.parts and path.name!='retained-process-index.json':index['sources'].append(ref(path))
    timeline=json.loads((run/'timeline.json').read_text(encoding='utf-8'))
    for c in timeline['chapters']:
        for u in c['utterances']:index['external_input_refs'].append(u['tts_raw'])
    edit=json.loads((run/'edit.json').read_text(encoding='utf-8'))
    for u in edit['utterances'].values():index['external_input_refs'].append(ref(Path(u['image'])))
    write(run/'retained-process-index.json',index);preserve(run/'retained-process-index.json','a04-process-index','process-index')
    append_phase_record(manifest,phase_id='project-external-composition',status='succeeded',artifact_ids=['a04-deliverable','a04-timeline','a04-composer-source','a04-chapters'],detail='Original six chapters rendered as bounded chunks in six parallel workers, then copied joins. Project composer executed directly; no CLI build claim.')
    append_automated_audit_record(manifest,check_id='independent-machine-media',status='passed',subject_artifact_id='a04-deliverable',report_artifact_id='a04-machine-report')
    append_phase_record(manifest,phase_id='independent-product-frame-review',status='succeeded',artifact_ids=['a04-deliverable','a04-product-report','a04-shared-frames'],detail='Complete script and targeted actual frames independently reviewed. Human listening, full 1x review, clean admission and signoff remain pending.')
    loaded=load_document(manifest,check_files=True)
    report={'kind':'native-preservation-complete','manifest':ref(manifest),'artifacts':rows,'human_signoffs':len(loaded.run.signoffs),'scope':'Exact retained bytes and declared machine/limited product conditions, no human approval'}
    write(run/'native-preservation-complete.json',report);print(json.dumps(ref(run/'native-preservation-complete.json')))
if __name__=='__main__':main()
