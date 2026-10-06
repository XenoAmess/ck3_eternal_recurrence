"""Read-only PLAN/verify for carried text bytes, methods and recorded PCM clock.

Never opens historical absolute paths, imports production code, invokes TTS or
media tools, or grants availability of omitted audio/raw/CAS artifacts.
"""
from pathlib import Path,PurePosixPath
import argparse
import ast
import hashlib
import json
import re

def relative(root,value):
    if not isinstance(value,str) or not value or '\\' in value or ':' in value:
        raise ValueError('Only explicit portable POSIX relative paths accepted')
    pure=PurePosixPath(value)
    if pure.is_absolute() or '..' in pure.parts:raise ValueError('Path escapes portable package')
    path=(root/Path(*pure.parts)).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():raise ValueError('Carried file unavailable: '+value)
    return path
def read(root,value):return json.loads(relative(root,value).read_bytes())
def verify(root):
    catalog=read(root,'FILE-CATALOG.json')
    if catalog['schema']!='ck3.e04.final-BC-production-text-catalog.v1':raise ValueError('Unknown catalog')
    allowed={'.json','.jsonl','.md','.py','.txt'}
    seen=set()
    for row in catalog['files']:
        if row['path'] in seen:raise ValueError('Duplicate carried file')
        seen.add(row['path']);path=relative(root,row['path'])
        if path.suffix not in allowed and path.name!='.gitattributes':raise ValueError('Audio/raw/executable binary cannot be carried here')
        raw=path.read_bytes()
        if len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('Carried bytes/hash changed: '+row['path'])
    methods=read(root,'METHOD-MAP.json')
    for row in methods['code_files']:
        tree=ast.parse(relative(root,row['path']).read_text(encoding='utf-8-sig'))
        names={node.name for node in ast.walk(tree) if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))}
        if not set(row['functions'])<=names:raise ValueError('Archived production method missing')
    text=relative(root,'narration/six-chapter-final-BC-Chinese-a06.md').read_bytes()
    body=dict(re.findall(r'^\[(C\d\d-\d\d)\] (.+)$',text.decode('utf-8-sig'),re.M))
    expected=[f'C{chapter:02d}-{part:02d}' for chapter,count in enumerate((8,12,12,11,16,10),1) for part in range(1,count+1)]
    if list(body)!=expected:raise ValueError('Narration69 ordered identity changed')
    ledger=read(root,'narration/claim-ledger-final-BC-a06.json')
    review=read(root,'narration/Root-NO-BLOCK.json')
    if review['source_review_status']!='NO_BLOCK' or review['final_freeze'] is not True:raise ValueError('Historical actual Root review changed')
    if review['chinese_body_sha256']!=hashlib.sha256(text).hexdigest():raise ValueError('Review/body binding changed')
    if review['chinese_ledger_sha256']!=hashlib.sha256(relative(root,'narration/claim-ledger-final-BC-a06.json').read_bytes()).hexdigest():raise ValueError('Review/ledger binding changed')
    clock=read(root,'RECORDED-CLOCK.json')
    cursor=0;ids=[];new_WB=0;reused_fragments=0;null_WB=0
    for chapter in clock['chapters']:
        index=read(root,chapter['carried_index_path'])
        frames=index['actual_PCM']['sample_frames']
        if type(frames) is not int or chapter['start_sample']!=cursor or chapter['end_sample']!=cursor+frames:
            raise ValueError('Recorded integer chapter clock changed')
        if (index['actual_PCM']['sample_rate'],index['actual_PCM']['channels'],index['actual_PCM']['sample_width_bytes'])!=(24000,1,2):
            raise ValueError('Recorded PCM format changed')
        cursor+=frames
        for paragraph in index['paragraphs']:
            key=paragraph['id'];ids.append(key)
            if paragraph['subtitles_zh']!=body[key] or ''.join(row['text_zh'] for row in paragraph['fragments'])!=body[key]:
                raise ValueError('Recorded audio text/fragment binding changed')
            if key in clock['voice_changed_ids']:
                fragment=paragraph['fragments'][0]
                metadata_path=clock['new_WordBoundary_files'][key]
                raw=relative(root,metadata_path).read_bytes()
                if hashlib.sha256(raw).hexdigest()!=fragment['metadata']['sha256']:raise ValueError('New WB/index pin mismatch')
                events=[json.loads(line) for line in raw.decode('utf-8').splitlines()]
                if len(events)!=fragment['WordBoundary_count']:raise ValueError('New actual WB count changed')
                if any(row['type']!='WordBoundary' or type(row['offset']) is not int or type(row['duration']) is not int for row in events):
                    raise ValueError('New WB native tick schema changed')
                new_WB+=len(events)
            else:
                reused_fragments+=len(paragraph['fragments'])
                null_WB+=sum(row.get('metadata') is None for row in paragraph['fragments'])
    if ids!=expected or cursor!=41658624 or cursor!=clock['recorded_actual_PCM']['sample_frames']:
        raise ValueError('Recorded69/global sample count changed')
    if new_WB!=774 or reused_fragments!=67 or null_WB!=6:raise ValueError('Recorded actual/reuse metadata counts changed')
    native=read(root,'native/run-manifest.json')
    if len(native['artifacts'])!=118 or len({row['id'] for row in native['artifacts']})!=118:raise ValueError('Historical118 native record set changed')
    configuration=relative(root,'configuration/promo-project-final-Chinese-audio.json').read_bytes()
    if native['project_config']['bytes']!=len(configuration) or native['project_config']['sha256'].lower()!=hashlib.sha256(configuration).hexdigest():
        raise ValueError('Historical native manifest/config byte binding changed')
    result=read(root,'native/publication-result.json')
    if result['completed_count']!=118 or result['queued_count']!=118 or result['final_validation']['returncode']!=0:
        raise ValueError('Historical actual native receipt changed')
    release=read(root,'toolchain/actual-latest-release-query.json')
    if release['matched'] is not True or release['latest_tag']!='v0.2.1' or release['install_actions']!=0:
        raise ValueError('Historical fresh release receipt changed')
    return {'status':'PASS_CARRIED_TEXT_BYTES_METHODS_AND_RECORDED_CLOCK','carried_files':len(seen),
      'paragraphs':69,'new_actual_WB_events':new_WB,'recorded_PCM_samples':cursor,'recorded_seconds':cursor/24000,
      'native_records_as_metadata':118,'actual_production_native_validation_receipt_preserved':True,
      'current_package_full_native_validation_performed':False,'external_audio_PCM_RAW_CAS_availability':'NOT_CARRIED_NOT_GRANTED',
      'external_original_paths_opened':0,'production_code_imported_or_executed':False,
      'new_TTS_media_process_SDK_Game_UI_Git_calls':0,'human_listening_or_film_signoff':False}
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',nargs='?',choices=('plan','verify'),default='plan')
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    args=parser.parse_args()
    result=verify(args.root);result['command']=args.command
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
