"""Finite actual metadata closure: source/text/audio pins, WB and native result."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib
import json
import re
CROOT=Path('C:/ck3-war-episode04-research-20261004-a01')
OUT=CROOT/'e04-final-BC-audio-close-a01';OUT.mkdir(exist_ok=False)
def pin(path):
    path=Path(path);raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def read(path):return json.loads(Path(path).read_bytes())
def write(path,value):
    with path.open('xb') as stream:stream.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
PROD=CROOT/'e04-final-BC-audio-production-a01'
FINAL=CROOT/'e04-final-BC-audio-English-binding-a01/ROOT-DELIVERY.json'
audio=read(FINAL)
assert pin(FINAL)['sha256']=='46269c38b047b783662862c3e336e03f2978abcc67449aad330daf9b90c7b1f0'
native=read(PROD/'native-publication-a01/RESULT.json')
assert native['mode']=='ACTUAL_PUBLIC_LIBRARY_API' and native['completed_count']==native['queued_count'] and native['final_validation']['returncode']==0
assert read(CROOT/'e04-final-BC-audio-launch-a01/RESULT.json')['exit_code']==0
release=read(PROD/'sources/latest-release-query.json')
assert release['matched'] is True and release['latest_tag']=='v0.2.1' and release['installed_version']=='0.2.1' and release['install_actions']==0
body_path=CROOT/'e04-final-BC-story-a01/actual-story-a02/six-chapter-final-BC-Chinese-a06.md'
ledger_path=body_path.with_name('claim-ledger-final-BC-a06.json')
body=dict(re.findall(r'^\[(C\d\d-\d\d)\] (.+)$',body_path.read_text(encoding='utf-8'),re.M))
EN=read(CROOT/'e04-final-BC-subtitle-production-a01/English-diff-final-BC-a01.json')
english={row['id']:row['subtitles_en'] for row in EN['paragraphs']}
old=read(CROOT/'e04-A-only-audio-production-a01/ROOT-DELIVERY.json')
baseline={row['id']:row for chapter in old['chapter_timeline'] for row in read(chapter['index']['path'])['paragraphs']}
voice=audio['voice_changed_ids'];allrows=[];new_WB=0;new_fragments=0;reused_fragments=0;null_WB=0;cursor=0
perchapter=[]
for chapter in audio['chapter_timeline']:
    assert chapter['start_sample']==cursor
    index=read(chapter['index']['path']);assert pin(chapter['index']['path'])==chapter['index']
    assert index['actual_PCM']['sample_rate']==24000 and index['actual_PCM']['channels']==1 and index['actual_PCM']['sample_width_bytes']==2
    assert chapter['end_sample']-chapter['start_sample']==index['actual_PCM']['sample_frames']
    cursor=chapter['end_sample'];allrows.extend(index['paragraphs'])
    for row in index['paragraphs']:
        key=row['id'];assert row['subtitles_zh']==body[key]
        assert row['subtitles_en']==english.get(key,baseline[key]['subtitles_en'])
        assert ''.join(fragment['text_zh'] for fragment in row['fragments'])==body[key]
        if key not in voice:
            assert len(row['fragments'])==len(baseline[key]['fragments'])
            for current,prior in zip(row['fragments'],baseline[key]['fragments']):
                for field in ('audio','decoded_audio','metadata'):assert current.get(field)==prior.get(field)
                reused_fragments+=1
                null_WB+=current.get('metadata') is None
        else:
            assert len(row['fragments'])==1
            fragment=row['fragments'][0];new_fragments+=1
            assert fragment['boundary_extent_within_decoded_audio_plus_250ms'] is True
            assert pin(fragment['metadata']['path'])==fragment['metadata']
            events=[json.loads(line) for line in Path(fragment['metadata']['path']).read_text(encoding='utf-8').splitlines()]
            assert len(events)==fragment['WordBoundary_count'] and all(event['type']=='WordBoundary' and type(event['offset']) is int and type(event['duration']) is int for event in events)
            new_WB+=len(events)
    perchapter.append({'chapter_id':chapter['chapter_id'],'index':chapter['index'],'audio':index['audio'],
      'sample_frames':index['actual_PCM']['sample_frames'],'actual_seconds':index['actual_PCM']['seconds'],
      'paragraphs':len(index['paragraphs'])})
assert [row['id'] for row in allrows]==list(body) and len(allrows)==69
assert new_fragments==7 and null_WB==6 and reused_fragments==audio['exact_reused_fragments']
assert new_WB==audio['new_metadata_events'] and cursor==41658624==audio['actual_PCM']['sample_frames']
assert audio['actual_PCM']['seconds']==cursor/24000==1735.776 and 1200<=audio['actual_PCM']['seconds']<=2400
assert audio['inserted_silence_frames']==0 and audio['ABC_winner'] is None
report={'schema':'ck3.e04.actual-final-BC-audio-metadata-closure.v1','created_utc':datetime.now(timezone.utc).isoformat(),
 'status':'PASS_ACTUAL_SOURCE_69_TEXT_PCM_WB_AND_SERIAL_NATIVE_AUTHORING_VALIDATION',
 'Chinese_body':pin(body_path),'ledger':pin(ledger_path),'Root_NO_BLOCK':pin(CROOT/'e04-final-BC-Root-actual-source-review-a01/Root-NO-BLOCK.json'),
 'actual_final_audio_delivery':pin(FINAL),'actual_Chinese_audio_delivery':pin(PROD/'ROOT-DELIVERY.json'),
 'actual_native_publication':pin(PROD/'native-publication-a01/RESULT.json'),'actual_native_run':pin(PROD/'native-run/run-manifest.json'),
 'actual_native_count':native['completed_count'],'actual_native_validate_returncode':0,
 'fresh_release_query':pin(PROD/'sources/latest-release-query.json'),'actual_release':'v0.2.1','wheel_SHA256':release['wheel_digest'],
 'actual_PCM':audio['actual_PCM'],'actual_minutes_seconds':'28:55.776','delivery20_to40min':True,
 'paragraphs':69,'voice_changed_ids':voice,'new_generated_fragments':new_fragments,
 'exact_reused_fragments':reused_fragments,'exact_reused_Chinese_paragraphs':62,
 'new_actual_WordBoundary_events':new_WB,'six_original_reused_fragments_WordBoundary':None,
 'six_original_reused_fragments_not_regenerated_or_fitted':True,'chapters':perchapter,
 'inserted_silence_frames':0,'new_English_binding_provider_calls':0,'new_English_binding_PCM_WAVs':0,
 'ABC_winner':None,'C_controlled_comparison_eligibility':'NOT_GRANTED','final_movie':None,
 'human_listening_signoff':False,'human_fullfilm_1x':False,'film_signoff':False}
write(OUT/'ACTUAL-CLOSURE.json',report)
write(OUT/'ROOT-DELIVERY.json',{'status':'ACTUAL_FINAL_BC_NARRATION_READY_FOR_REVIEW01_PICTURE_AND_SUBTITLE',
 'report':pin(OUT/'ACTUAL-CLOSURE.json'),'final_audio_delivery':pin(FINAL),
 'Chinese_audio_delivery':pin(PROD/'ROOT-DELIVERY.json'),'actual_native_publication':pin(PROD/'native-publication-a01/RESULT.json'),
 'actual_PCM':audio['actual_PCM'],'actual_minutes_seconds':'28:55.776','new7voices':7,'old62Chinese_exact':True,
 'new_actual_WB_events':new_WB,'native_count':native['completed_count'],'new_English_TTS':0,
 'fullfilm_or_human_signoff':False})
print(json.dumps({'status':'ACTUAL_AUDIO_CLOSED','delivery':pin(OUT/'ROOT-DELIVERY.json'),
 'report':pin(OUT/'ACTUAL-CLOSURE.json'),'actual_PCM':audio['actual_PCM'],'new_WB':new_WB,'new7voices':7,
 'reused_fragments':reused_fragments,'native_count':native['completed_count']}))
