"""Actual minimal Chinese TTS increment and later English-index binding.

plan is read-only except its new report. generate requires actual frozen story
sources and --execute. No provider call, run creation or media work on import.
"""
from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor,as_completed
import argparse
import copy
import hashlib
import importlib.metadata as md
import importlib.util
import json
import os
import re
import sys
import urllib.request

API='https://api.github.com/repos/XenoAmess/xar_promo_toolchain/releases/latest'
def now():return datetime.now(timezone.utc).isoformat()
def pin(path):
    path=Path(path);raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    raw=obj if isinstance(obj,bytes) else (json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    with path.open('xb') as stream:stream.write(raw)
def read_pin(row,base):
    if not isinstance(row,dict) or set(row)!={'path','bytes','sha256'}:raise ValueError('Exact path/bytes/sha256 pin required')
    path=Path(row['path'])
    if not path.is_absolute():path=base/path
    raw=path.read_bytes()
    if len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('Frozen source pin changed: '+str(path))
    return path,raw
def load_module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj)
    return obj
def voice_subtitle_ids(body,old_rows,review):
    voice=[key for key in body if old_rows[key]['subtitles_zh']!=body[key]]
    if review.get('changed_paragraph_ids')!=voice:raise ValueError('Actual voice diff differs from source review')
    subtitle=review.get('subtitle_changed_ids',voice)
    if not isinstance(subtitle,list) or len(set(subtitle))!=len(subtitle):raise ValueError('Subtitle IDs must be a unique list')
    if subtitle!=[key for key in body if key in subtitle] or not set(voice)<=set(subtitle):
        raise ValueError('Subtitle IDs must be ordered actual paragraph IDs and include each changed voice')
    return voice,subtitle
def English_mapping(diff,subtitle_ids,claims):
    rows=diff.get('paragraphs')
    if not isinstance(rows,list) or [row.get('id') for row in rows]!=subtitle_ids:
        raise ValueError('English rows must match ordered actual subtitle IDs, including EN-only rows')
    for row in rows:
        if not isinstance(row.get('subtitles_en'),str) or not row['subtitles_en']:
            raise ValueError('English text empty')
        if row.get('source_keys')!=claims[row['id']]['source_keys']:
            raise ValueError('English claim source keys differ from final authoritative ledger')
    return {row['id']:row for row in rows}
def input_plan(request_path,need_final):
    req=json.loads(request_path.read_bytes())
    if req.get('schema')!='ck3.e04.final-BC-audio-request.v1':raise ValueError('Unknown audio request schema')
    if type(req.get('workers')) is not int or not 4<=req['workers']<=8:raise ValueError('Actual provider concurrency must be4..8')
    tool_path,_=read_pin(req['oral_tool'],request_path.parent)
    oral_path,_=read_pin(req['oral_request'],request_path.parent)
    tool=load_module(tool_path,'pinned_final_BC_oral_tool')
    oral=tool.load_request(oral_path)
    if need_final:
        validated,raw=tool.validate_freeze(oral,oral_path)
        body=tool.paragraphs(raw['final_chinese_body'])
        ledger=json.loads(raw['final_claim_ledger'])
        review=json.loads(raw['source_review'])
        changed=validated['audio_changed_ids']
    else:
        validated=tool.plan(oral,oral_path)
        body=tool.paragraphs(tool.read_pin(oral['current_partial_draft_body'],oral_path.parent))
        changed=None;ledger=None;review=None
    _,base_raw=read_pin(req['baseline_audio_delivery'],request_path.parent)
    baseline=json.loads(base_raw)
    old_rows={};chapter_rows=[]
    for chapter in baseline['chapter_timeline']:
        index_path,index_raw=read_pin(chapter['index'],request_path.parent)
        index=json.loads(index_raw)
        if index['chapter_id']!=chapter['chapter_id']:raise ValueError('Actual chapter ID/index mismatch')
        chapter_rows.append((index_path,index))
        for row in index['paragraphs']:
            if row['id'] in old_rows:raise ValueError('Duplicate old audio paragraph')
            old_rows[row['id']]=row
    if set(old_rows)!=set(body):raise ValueError('Baseline audio must cover exactly final69 paragraph IDs')
    if need_final:
        actual_delta,_=voice_subtitle_ids(body,old_rows,review)
        if actual_delta!=changed:raise ValueError('Actual old audio text diff differs from frozen source review')
    return req,tool,oral,validated,body,ledger,review,baseline,chapter_rows,old_rows
def fresh_release(folder):
    for key in ('HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','http_proxy','https_proxy','all_proxy'):
        os.environ.pop(key,None)
    if os.environ.get('XAR_PROMO_SOURCE') or os.environ.get('XAR_PROMO_TOOLCHAIN_SOURCE'):
        raise ValueError('Source override cannot masquerade as a formal wheel')
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(urllib.request.Request(API,headers={'User-Agent':'XAR-E4-finalBC-actual-TTS','Cache-Control':'no-cache'}),timeout=30) as response:
        raw=response.read()
    write(folder/'latest-release-response.json',raw)
    release=json.loads(raw);dist=md.distribution('xar-promo-toolchain')
    direct=json.loads(dist.read_text('direct_url.json'))
    asset=next(item for item in release['assets'] if item['name'].endswith('.whl'))
    matched=(not release['draft'] and not release['prerelease'] and release['tag_name'].lstrip('v')==dist.version
       and direct['url']==asset['browser_download_url']
       and asset.get('digest')=='sha256:'+direct['archive_info']['hashes']['sha256'])
    result={'queried_utc':now(),'API':API,'response':pin(folder/'latest-release-response.json'),
        'latest_tag':release['tag_name'],'installed_version':dist.version,'wheel_digest':asset.get('digest'),
        'direct_url':direct,'matched':bool(matched),'python':sys.executable,
        'Pillow':md.version('Pillow'),'edge_tts':md.version('edge-tts'),'install_actions':0}
    write(folder/'latest-release-query.json',result)
    if not matched:raise ValueError('Installed wheel is not the freshly queried latest formal release; no install performed')
    return result
def generate(request_path,output):
    req,tool,oral,validated,body,ledger,review,baseline,chapters,old_rows=input_plan(request_path,True)
    workers=req.get('workers',4)
    if type(workers) is not int or not 4<=workers<=8:raise ValueError('Actual provider concurrency must be4..8')
    helper_path,helper_raw=read_pin(req['actual_audio_helper'],request_path.parent)
    writer_path,writer_raw=read_pin(req['serial_native_writer'],request_path.parent)
    config_path,config_raw=read_pin(req['baseline_project_config'],request_path.parent)
    output.mkdir(parents=True,exist_ok=False)
    (output/'sources').mkdir();(output/'logs').mkdir()
    try:
        release=fresh_release(output/'sources')
        helper=load_module(helper_path,'e4_pinned_actual_WB_audio_helpers')
        helper.ROOT=output
        helper.preserve=lambda *_args,**_kwargs:(_ for _ in ()).throw(RuntimeError('No per-file native CLI publication'))
        changed=validated['audio_changed_ids']
        claims={row['id']:row for row in ledger['claims']}
        config=json.loads(config_raw)
        config['project']['id']=output.name+'-Chinese-audio'
        config['locales']={'narration':'zh-CN','subtitles':['zh-CN']}
        for chapter in config['chapters']:
            for cue in chapter['cues']:
                text=body[cue['id']]
                cue['narration']={'zh-CN':text};cue['subtitles']={'zh-CN':text}
        chinese_config=output/'sources/promo-project-final-Chinese-audio.json'
        write(chinese_config,config)
        source_rows=[]
        for name,row in (('oral-request',req['oral_request']),('oral-tool',req['oral_tool']),
            ('baseline-audio-delivery',req['baseline_audio_delivery']),('actual-audio-helper',req['actual_audio_helper']),
            ('serial-native-writer',req['serial_native_writer']),('baseline-project-config',req['baseline_project_config'])):
            path,raw=read_pin(row,request_path.parent)
            target=output/'sources'/(name+path.suffix);write(target,raw)
            source_rows.append({'original':pin(path),'snapshot':pin(target)})
        oral_path,_=read_pin(req['oral_request'],request_path.parent)
        story_sources={name:oral['future'][name] for name in ('final_C_terminal_source','final_chinese_body','final_claim_ledger','source_review')}
        story_sources.update({name:oral[name] for name in ('current_C_Root_basis_source','current_C_Main_scope_source') if oral.get(name) is not None})
        for name,row in story_sources.items():
            path,raw=read_pin(row,oral_path.parent)
            target=output/'sources'/(name+path.suffix);write(target,raw)
            source_rows.append({'original':pin(path),'snapshot':pin(target)})
        write(output/'input-freeze.json',{'created_utc':now(),'request':req,'source_snapshots':source_rows,
            'actual_release':release,'changed_Chinese_IDs':changed,'workers':workers,
            'English_subtitle_pending_is_not_TTS_gate':True,'human_signoff':False})
        helper.command(output/'logs','validate-Chinese-config',[sys.executable,'-I','-B','-m','xar_promo','validate',chinese_config,'--json'])
        from xar_promo.operations import start_run
        native_path=start_run(chinese_config,run_id=output.name,run_directory=output/'native-run')
        write(output/'native-start-run-receipt.json',{'actual_public_API':'xar_promo.operations.start_run',
            'config':pin(chinese_config),'run_manifest_after':pin(native_path),'returned_path':str(native_path)})
        results={}
        with ThreadPoolExecutor(max_workers=workers) as pool:
            tasks={}
            for key in changed:
                paragraph={'id':key,'chapter_id':'E4-'+key[1:3],'source_keys':claims[key]['source_keys']}
                fragment={'id':key+'-F01','kind':'new-audio-pending','text_zh':body[key],
                    'text_sha256':hashlib.sha256(body[key].encode('utf-8')).hexdigest()}
                tasks[pool.submit(helper.generate,paragraph,fragment)]=key
            for task in as_completed(tasks):
                key=tasks[task]
                try:results[key]=task.result()
                except Exception as error:
                    results[key]={'paragraph_id':key,'status':'FAILED_WORKER_PRESERVED',
                        'exception_type':type(error).__name__,'message':str(error)}
                    write(output/'worker-failures'/(key+'.json'),results[key])
                print(json.dumps({'event':'ACTUAL_FINAL_BC_FRAGMENT_RETURNED','id':key,
                    'status':results[key]['status'],'completed':len(results),'total':len(changed)}),flush=True)
        failed=[value for value in results.values() if 'decoded_PCM' not in value or value.get('boundary_extent_within_decoded_audio_plus_250ms') is not True]
        if failed:
            write(output/'FAILED-PROVIDER-RESULTS.json',{'failures':failed,'attempts_preserved':True})
            raise ValueError('Actual changed-fragment provider attempt remains partial')
        timeline=[];indexes=[];cursor=0;reused=0;generated=0
        for old_index_path,old_index in chapters:
            chapter_id=old_index['chapter_id'];affected=any(key in changed for key in (row['id'] for row in old_index['paragraphs']))
            if not affected:
                index=old_index;index_path=old_index_path
                reused+=sum(len(row['fragments']) for row in index['paragraphs'])
            else:
                folder=output/'chapters'/chapter_id;folder.mkdir(parents=True)
                paragraph_rows=[];ordered=[];chapter_cursor=0
                for old_row in old_index['paragraphs']:
                    key=old_row['id'];start=chapter_cursor
                    values=[copy.deepcopy(results[key])] if key in changed else copy.deepcopy(old_row['fragments'])
                    if key in changed:generated+=1
                    else:reused+=len(values)
                    for fragment in values:
                        for field in ('audio','decoded_audio'):
                            if pin(fragment[field]['path'])!=fragment[field]:raise ValueError('Audio exact reuse/generated pin changed')
                        frames=fragment['decoded_PCM']['sample_frames']
                        if type(frames) is not int or frames<=0:raise ValueError('Actual PCM frame count invalid')
                        fragment.update(chapter_start_sample=chapter_cursor,chapter_end_sample=chapter_cursor+frames,
                            chapter_start_seconds=chapter_cursor/24000,chapter_end_seconds=(chapter_cursor+frames)/24000,
                            exact_reused_in_final_BC=key not in changed)
                        ordered.append(fragment['decoded_audio']['path']);chapter_cursor+=frames
                    paragraph_rows.append({'id':key,'subtitles_zh':body[key],
                        'subtitles_en':None if key in changed else old_row['subtitles_en'],
                        'English_final_binding_pending':key in changed,
                        'chapter_start_sample':start,'chapter_end_sample':chapter_cursor,
                        'chapter_start_seconds':start/24000,'chapter_end_seconds':chapter_cursor/24000,
                        'fragments':values})
                audio=folder/'narration.wav';info=helper.join_wav(audio,ordered)
                if info['sample_frames']!=chapter_cursor:raise ValueError('Actual chapter sample conservation failed')
                index={'schema':'xar.e04.actual-final-BC-Chinese-chapter-audio.v1','chapter_id':chapter_id,
                    'audio':pin(audio),'actual_PCM':info,'paragraphs':paragraph_rows,
                    'inserted_silence_frames':0,'ABC_results':review['ABC_results'],'ABC_winner':None,
                    'C_subject_scope':review.get('C_subject_scope'),'human_listening_signoff':False}
                index_path=folder/'audio-index.json';write(index_path,index)
            if pin(index['audio']['path'])!=index['audio']:raise ValueError('Actual chapter audio source changed')
            frames=index['actual_PCM']['sample_frames']
            timeline.append({'chapter_id':chapter_id,'start_sample':cursor,'end_sample':cursor+frames,
                'start_seconds':cursor/24000,'end_seconds':(cursor+frames)/24000,'index':pin(index_path),
                'exact_old_chapter_audio_reuse':not affected})
            indexes.append(index);cursor+=frames
        stable=output/'final-Chinese-narration.wav';info=helper.join_wav(stable,[index['audio']['path'] for index in indexes])
        if info['sample_frames']!=cursor:raise ValueError('Actual global sample conservation failed')
        delivery={'schema':'xar.e04.actual-final-BC-Chinese-audio-delivery.v1','created_utc':now(),
            'status':'ACTUAL_CHINESE_AUDIO_READY_FINAL_ENGLISH_INDEX_BINDING_PENDING',
            'chapter_timeline':timeline,'stable_audio':pin(stable),'actual_PCM':info,
            'voice_changed_ids':changed,'exact_reused_Chinese_ids':validated['exact_reused_Chinese_ids'],
            'new_generated_fragments':generated,'exact_reused_fragments':reused,
            'new_metadata_events':sum(row['WordBoundary_count'] for row in results.values()),
            'actual_duration_20_to40_minutes':1200<=info['seconds']<=2400,'inserted_silence_frames':0,
            'ABC_results':review['ABC_results'],'ABC_winner':None,'C_subject_scope':review.get('C_subject_scope'),
            'chinese_body_sha256':oral['future']['final_chinese_body']['sha256'],
            'chinese_ledger_sha256':oral['future']['final_claim_ledger']['sha256'],
            'source_review':oral['future']['source_review'],'oral_request':req['oral_request'],
            'actual_final_movie_clock':None,'human_listening_signoff':False,'subtitle_or_film_signoff':False}
        write(output/'AUDIO-READY.json',delivery)
        print(json.dumps({'event':'ACTUAL_FINAL_BC_CHINESE_AUDIO_READY','delivery':pin(output/'AUDIO-READY.json'),
            'actual_seconds':info['seconds'],'new_generated':generated,'exact_reused':reused}),flush=True)
        writer=load_module(writer_path,'pinned_single_process_native_writer')
        files=[path for path in sorted(output.rglob('*')) if path.is_file() and 'native-run' not in path.relative_to(output).parts]
        queue=[]
        for number,path in enumerate(files):
            media='audio/mpeg' if path.suffix=='.mp3' else 'audio/wav' if path.suffix=='.wav' else 'application/x-ndjson' if path.suffix=='.jsonl' else 'application/json' if path.suffix=='.json' else 'text/plain'
            queue.append({'id':f'e4-finalBC-{number:04d}',**pin(path),'collection':'derived',
                'role':'narration' if path.suffix in ('.wav','.mp3') else 'process-evidence','label':path.name,'media_type':media})
        publication=writer.publish_serial(native_path,queue,output/'native-publication-a01')
        delivery['native_run']=pin(native_path);delivery['native_publication']=pin(output/'native-publication-a01/RESULT.json')
        delivery['native_queue_count']=publication['queued_count']
        write(output/'ROOT-DELIVERY.json',delivery)
        return delivery
    except Exception as error:
        write(output/'FAILED-ATTEMPT.json',{'finished_utc':now(),'type':type(error).__name__,'message':str(error),
            'all_partial_and_failed_assets_preserved':True,'no_native_retry':True,'human_signoff':False})
        raise
def bind_English(request_path,audio_pin,English_pin,output):
    req,tool,oral,validated,body,ledger,review,baseline,chapters,old_rows=input_plan(request_path,True)
    _,raw=read_pin(audio_pin,request_path.parent);audio=json.loads(raw)
    _,raw=read_pin(English_pin,request_path.parent);diff=json.loads(raw)
    if diff.get('source_review_status')!='NO_BLOCK':raise ValueError('English source review pending')
    if diff.get('chinese_body_sha256')!=audio['chinese_body_sha256'] or diff.get('chinese_ledger_sha256')!=audio['chinese_ledger_sha256']:
        raise ValueError('Final English is not bound to the actual Chinese audio story')
    voice,subtitle=voice_subtitle_ids(body,old_rows,review)
    if audio['voice_changed_ids']!=voice or audio['chinese_body_sha256']!=oral['future']['final_chinese_body']['sha256'] or audio['chinese_ledger_sha256']!=oral['future']['final_claim_ledger']['sha256']:
        raise ValueError('Audio delivery must bind exact final body, ledger and actual changed voices')
    claims={row['id']:row for row in ledger['claims']}
    English_rows=English_mapping(diff,subtitle,claims)
    output.mkdir(parents=True,exist_ok=False)
    timeline=[]
    for chapter in audio['chapter_timeline']:
        _,raw=read_pin(chapter['index'],request_path.parent);index=json.loads(raw)
        for row in index['paragraphs']:
            if row['id'] in English_rows:
                text=English_rows[row['id']]['subtitles_en']
                if not isinstance(text,str) or not text:raise ValueError('English text empty')
                row['subtitles_en']=text;row['English_final_binding_pending']=False
            if row.get('English_final_binding_pending'):raise ValueError('English binding remains pending')
        target=output/'chapters'/chapter['chapter_id']/'audio-index.json';write(target,index)
        timeline.append({**chapter,'index':pin(target)})
    final={**audio,'schema':'xar.e04.actual-final-BC-audio-delivery.v1',
        'status':'ACTUAL_VOICE_AUDIO_AND_FINAL_ENGLISH_INDEX_BOUND_PENDING_LISTENING',
        'chapter_timeline':timeline,'subtitle_changed_ids':subtitle,
        'final_English_diff':English_pin,'source_audio_delivery':audio_pin,
        'new_provider_calls_in_English_binding':0,'new_PCM_WAVs_in_English_binding':0,
        'human_listening_signoff':False,'subtitle_or_film_signoff':False}
    write(output/'ROOT-DELIVERY.json',final)
    return final
def prepare_final_request(request_path,oral_pin,output):
    req=json.loads(request_path.read_bytes())
    path,_=read_pin(oral_pin,request_path.parent)
    req['oral_request']=pin(path)
    # Resolve its existing runtime inputs before relocating the new request.
    for field in ('oral_tool','baseline_audio_delivery','actual_audio_helper','serial_native_writer','baseline_project_config'):
        source,_=read_pin(req[field],request_path.parent);req[field]=pin(source)
    # An actual final oral JSON, not a caller flag, must pass the source freeze.
    tool_path,_=read_pin(req['oral_tool'],request_path.parent)
    tool=load_module(tool_path,'pinned_oral_final_request_check')
    oral=tool.load_request(path);validated,_=tool.validate_freeze(oral,path)
    write(output,req)
    return {'status':'ACTUAL_SOURCE_FROZEN_AUDIO_REQUEST_READY','request':pin(output),
        'voice_changed_ids':validated['audio_changed_ids'],'provider_calls':0,
        'new_native_run_created':False,'human_signoff':False}
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('plan','prepare-final-request','generate','bind-english'))
    parser.add_argument('--request',required=True,type=Path)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--output-dir',type=Path)
    parser.add_argument('--audio-delivery-pin',type=Path)
    parser.add_argument('--English-diff-pin',type=Path)
    parser.add_argument('--oral-request-pin',type=Path)
    parser.add_argument('--execute',action='store_true')
    args=parser.parse_args()
    if args.command=='plan':
        result=input_plan(args.request,False)[3]
        result={'schema':'ck3.e04.final-BC-actual-audio-plan.v1','oral_plan':result,
            'status':'PENDING_ACTUAL_C_FROZEN_CHINESE_STORY','new_provider_calls':0,
            'new_native_run_created':False,'new_PCM_seconds':None,'human_signoff':False}
        if args.output is None:raise ValueError('plan needs new --output')
        write(args.output,result)
    elif args.command=='prepare-final-request':
        if args.oral_request_pin is None or args.output is None:raise ValueError('prepare-final-request needs actual --oral-request-pin JSON and fresh --output')
        result=prepare_final_request(args.request,json.loads(args.oral_request_pin.read_bytes()),args.output)
    else:
        if not args.execute or args.output_dir is None:raise ValueError('Actual new output requires --execute and a fresh --output-dir')
        if args.command=='generate':result=generate(args.request,args.output_dir)
        else:
            if args.audio_delivery_pin is None or args.English_diff_pin is None:raise ValueError('Two exact pin-JSON files required')
            result=bind_English(args.request,json.loads(args.audio_delivery_pin.read_bytes()),
                json.loads(args.English_diff_pin.read_bytes()),args.output_dir)
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
