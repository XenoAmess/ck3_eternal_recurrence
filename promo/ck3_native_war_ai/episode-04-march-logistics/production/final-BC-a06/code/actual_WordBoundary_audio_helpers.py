"""Actual bounded a04 stable TTS; reuse six old MP3s, preserve WordBoundary.

No CK3/UI/Git, no raw-video reads, no rendered picture or human signoff.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import importlib.metadata as md
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace
import urllib.request
import wave

PREP=Path(__file__).resolve().parent
CROOT=PREP.parent
INPUTS=CROOT/'e04-full-production-inputs-a04-a01'
ROOT=CROOT/'e04-stable-audio-production-a02'
API='https://api.github.com/repos/XenoAmess/xar_promo_toolchain/releases/latest'
MEDIA=Path('C:/Users/1/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.1-full_build/bin')
VOICE='zh-CN-XiaoxiaoNeural';RATE='-5%'

def now():return datetime.now(timezone.utc).isoformat()
def read(path):return json.loads(Path(path).read_bytes())
def pin(path):
    path=Path(path);data=path.read_bytes()
    return {'path':str(path),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
def write(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as stream:json.dump(data,stream,ensure_ascii=False,indent=2);stream.write('\n')
def copy(original,target):
    target=Path(target);target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as stream:stream.write(Path(original).read_bytes())
def command(folder,label,argv,timeout=120):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    write(folder/(label+'.argv.json'),[str(value) for value in argv])
    started=now();exit_code=None;error=None
    with (folder/(label+'.stdout.txt')).open('xb') as stdout,(folder/(label+'.stderr.txt')).open('xb') as stderr:
        try:
            result=subprocess.run([str(value) for value in argv],stdout=stdout,stderr=stderr,shell=False,timeout=timeout)
            exit_code=result.returncode
        except Exception as exception:error={'type':type(exception).__name__,'message':str(exception)}
    write(folder/(label+'.receipt.json'),{'started_utc':started,'finished_utc':now(),'exit_code':exit_code,'exception':error})
    if exit_code!=0:raise RuntimeError('Process failed or timed out: '+label)
    return folder/(label+'.stdout.txt')
def validate(label):
    command(ROOT/'logs',label,[sys.executable,'-B','-m','xar_promo','validate',ROOT/'native-run/run-manifest.json','--json'])
def preserve(path,artifact_id,role='process-evidence',media_type='application/json'):
    from xar_promo.operations import preserve_artifact
    preserve_artifact(ROOT/'native-run/run-manifest.json',Path(path),artifact_id=artifact_id,
        collection='derived' if role!='production-input' else 'raw',role=role,label=Path(path).name,media_type=media_type)
    validate('validate-'+artifact_id)
def wav_info(path):
    with wave.open(str(path),'rb') as wav:
        if (wav.getnchannels(),wav.getsampwidth(),wav.getframerate(),wav.getcomptype())!=(1,2,24000,'NONE'):
            raise ValueError('Decoded audio must be mono16bit24000HzPCM')
        count=wav.getnframes()
    return {'sample_rate':24000,'channels':1,'sample_width_bytes':2,'sample_frames':count,'seconds':count/24000}
def decode(folder,audio):
    decoded=folder/'decoded.wav'
    command(folder/'logs','decode',[MEDIA/'ffmpeg.exe','-hide_banner','-nostdin','-loglevel','error','-n','-i',audio,
        '-vn','-ac','1','-ar','24000','-c:a','pcm_s16le',decoded])
    probe_path=command(folder/'logs','probe',[MEDIA/'ffprobe.exe','-v','error','-show_format','-show_streams','-of','json',audio])
    probe=read(probe_path);duration=float(probe['format']['duration'])
    if duration<=0:raise ValueError('Nonpositive actual MP3 duration')
    return {'audio':pin(audio),'MP3_probe':pin(probe_path),'MP3_container_seconds':duration,
        'decoded_audio':pin(decoded),'decoded_PCM':wav_info(decoded)}

def prepare(workers):
    if ROOT.exists():raise FileExistsError('A fresh append-only production run is required')
    ROOT.mkdir();(ROOT/'sources').mkdir();(ROOT/'logs').mkdir()
    try:
        frozen=read(INPUTS/'ROOT-DELIVERY.json')
        if pin(INPUTS/'promo-project-planned-a04.json')!=frozen['project_config']:raise ValueError('Frozen full config changed')
        for row in frozen['files']:
            if pin(row['path'])!=row:raise ValueError('Frozen production input changed')
        fragments=read(INPUTS/'narration-fragments-and-audio-reuse-a04.json')
        config_rows={cue['id']:cue for chapter in read(INPUTS/'promo-project-planned-a04.json')['chapters'] for cue in chapter['cues']}
        for paragraph in fragments['paragraphs']:
            if ''.join(f['text_zh'] for f in paragraph['segments'])!=config_rows[paragraph['id']]['narration']['zh']:raise ValueError('Fragment text reconstruction changed')
            for fragment in paragraph['segments']:
                if hashlib.sha256(fragment['text_zh'].encode()).hexdigest()!=fragment['text_sha256']:raise ValueError('Frozen text SHA mismatch')
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(urllib.request.Request(API,headers={'User-Agent':'XAR-E4-stable-a04-actual-TTS'}),timeout=30) as response:raw=response.read()
        with (ROOT/'sources/latest-release-response.json').open('xb') as stream:stream.write(raw)
        release=json.loads(raw);wheel=next(asset for asset in release['assets'] if asset['name'].endswith('.whl'))
        dist=md.distribution('xar-promo-toolchain');direct=json.loads(dist.read_text('direct_url.json'))
        installed_sha=direct['archive_info']['hashes']['sha256']
        write(ROOT/'sources/latest-release-query.json',{'queried_utc':now(),'API':API,'response':pin(ROOT/'sources/latest-release-response.json'),
            'actual_latest_tag':release['tag_name'],'actual_installed_version':dist.version,'direct_url':direct,
            'python':sys.executable,'python_version':sys.version,'Pillow':md.version('Pillow'),'edge_tts':md.version('edge-tts'),
            'package_source_override_present':bool(os.environ.get('XAR_PROMO_SOURCE') or os.environ.get('XAR_PROMO_TOOLCHAIN_SOURCE')),
            'install_actions':0})
        if release['draft'] or release['prerelease'] or release['tag_name'].lstrip('v')!=dist.version:raise ValueError('Installed wheel is not fresh latest stable')
        if wheel.get('digest')!='sha256:'+installed_sha or direct['url']!=wheel['browser_download_url']:raise ValueError('Actual installed wheel provenance mismatch')
        import edge_tts
        from xar_promo.tts import EdgeTtsProvider,TtsRequest
        assert 'boundary' in inspect.signature(edge_tts.Communicate).parameters
        assert 'metadata_fname' in inspect.signature(edge_tts.Communicate.save_sync).parameters
        source_files=[INPUTS/'promo-project-planned-a04.json',INPUTS/'narration-fragments-and-audio-reuse-a04.json',
            INPUTS/'source-freeze.json',INPUTS/'ROOT-DELIVERY.json',INPUTS/'sources/claim-ledger-player-a04.json',
            INPUTS/'sources/english-subtitles-a04.json',INPUTS/'sources/six-chapter-player-narration-a04.md',Path(__file__),
            Path(inspect.getfile(EdgeTtsProvider)),Path(inspect.getfile(edge_tts.Communicate))]
        snapshots=[]
        for index,original in enumerate(source_files):
            target=ROOT/'sources'/f'{index:02d}-{original.name}'
            copy(original,target);snapshots.append({'original':pin(original),'snapshot':pin(target)})
        write(ROOT/'input-freeze.json',{'schema':'xar.e04.stable-TTS-input-freeze.v2','created_utc':now(),
            'sources':snapshots,'workers':workers,'provider':'EdgeTtsProvider with bounded metadata-recording module injection',
            'native_edge_boundary':'WordBoundary','metadata_ticks_per_second':10000000,
            'reused_six_audio_not_regenerated':True,'pending_editorial_blocks_not_spoken':['P-ABC','P-STARVATION'],
            'ABC_results':None,'ABC_winner':None,'human_listening_signoff':False})
        config=ROOT/'sources/00-promo-project-planned-a04.json'
        command(ROOT/'logs','validate-config',[sys.executable,'-B','-m','xar_promo','validate',config,'--json'])
        command(ROOT/'logs','native-start-run',[sys.executable,'-B','-m','xar_promo','start-run',config,
            '--run-id',ROOT.name,'--run-directory',ROOT/'native-run'])
        validate('validate-initial-native-run')
        for index,path in enumerate([ROOT/'input-freeze.json',*sorted((ROOT/'sources').glob('*'))]):
            preserve(path,f'e4a04-input-{index:02d}','production-input','text/x-python' if path.suffix=='.py' else 'application/json')
        return read(ROOT/'sources/01-narration-fragments-and-audio-reuse-a04.json')
    except Exception as error:
        write(ROOT/'prepare-failure.json',{'finished_utc':now(),'type':type(error).__name__,'message':str(error),'provider_calls':0})
        raise

def request_one(paragraph,fragment,attempt):
    from xar_promo.tts import EdgeTtsProvider,TtsRequest
    import edge_tts
    work=ROOT/'tts'/fragment['id']/f'attempt-a{attempt:02d}';work.mkdir(parents=True,exist_ok=False)
    audio=work/'speech.mp3';metadata=work/'word-boundary.jsonl'
    request=TtsRequest(fragment['text_zh'],voice=VOICE,rate=RATE,pitch='+0Hz',volume='+0%',audio_format='mp3',
        cache_salt='episode04-a04-wordboundary-a02')
    returned=[]
    class RecordingCommunicate:
        def __init__(self,text,voice,*,rate,volume,pitch):
            self.communicate=edge_tts.Communicate(text,voice,rate=rate,volume=volume,pitch=pitch,boundary='WordBoundary')
        def save_sync(self,destination):
            if Path(destination)!=audio:raise ValueError('Unexpected provider destination')
            value=self.communicate.save_sync(str(audio),str(metadata));returned.append(value)
            return value
    provider=EdgeTtsProvider(module=SimpleNamespace(Communicate=RecordingCommunicate),tool_version=md.version('edge-tts'))
    write(work/'request.json',{'fragment_id':fragment['id'],'paragraph_id':paragraph['id'],'chapter_id':paragraph['chapter_id'],
        'provider':{'id':provider.identity.provider_id,'version':provider.identity.tool_version},'request':request.cache_payload(),
        'metadata_request':{'boundary':'WordBoundary','ticks_per_second':10000000,'save_sync_audio_and_metadata':True},
        'text_sha256':fragment['text_sha256'],'source_keys':paragraph['source_keys'],'attempt':attempt,'started_utc':now()})
    started=now();stage='provider'
    try:
        provider.synthesize(request,audio)
        if returned!=[None]:raise ValueError('Unexpected actual save_sync return')
        if not audio.is_file() or audio.stat().st_size<512:raise ValueError('Returned MP3 missing or empty')
        stage='metadata'
        boundaries=[]
        if metadata.is_file():
            for line in metadata.read_text(encoding='utf-8').splitlines():
                row=json.loads(line)
                if row['type']!='WordBoundary' or not isinstance(row['offset'],int) or not isinstance(row['duration'],int):raise ValueError('Unexpected metadata type/units')
                if row['offset']<0 or row['duration']<0 or not isinstance(row['text'],str):raise ValueError('Invalid metadata bounds')
                boundaries.append(row)
        if not boundaries:raise ValueError('No actual WordBoundary metadata returned')
        stage='decode-and-probe';decoded=decode(work,audio)
        max_end=max(row['offset']+row['duration'] for row in boundaries)/10000000
        receipt={'fragment_id':fragment['id'],'paragraph_id':paragraph['id'],'chapter_id':paragraph['chapter_id'],
            'status':'PRODUCED_ACTUAL_AUDIO_AND_WORD_BOUNDARY_PENDING_LISTENING','kind':'new-generated-audio',
            'started_utc':started,'finished_utc':now(),'attempt':attempt,'request':pin(work/'request.json'),
            'text_sha256':fragment['text_sha256'],'text_zh':fragment['text_zh'],'provider_return':None,
            'voice':VOICE,'rate':RATE,'pitch':'+0Hz','volume':'+0%','metadata':pin(metadata),
            'WordBoundary_count':len(boundaries),'native_metadata_seconds_divisor':10000000,
            'native_max_boundary_end_seconds':max_end,'native_boundary_not_refitted_to_audio':True,
            'boundary_extent_within_decoded_audio_plus_250ms':max_end<=decoded['decoded_PCM']['seconds']+.25,
            'human_listening_signoff':False,'subtitle_alignment_signoff':False,**decoded}
        write(work/'receipt.json',receipt);return receipt,None
    except Exception as error:
        status=getattr(error,'status',None)
        failure={'fragment_id':fragment['id'],'paragraph_id':paragraph['id'],'chapter_id':paragraph['chapter_id'],
            'status':'FAILED_ATTEMPT_PRESERVED','started_utc':started,'finished_utc':now(),'attempt':attempt,
            'stage':stage,'exception_type':type(error).__name__,'message':str(error),'HTTP_status':status,
            'partial_audio':pin(audio) if audio.is_file() else None,'partial_metadata':pin(metadata) if metadata.is_file() else None,
            'transient_retry_eligible':stage=='provider' and (status in (429,500,502,503,504) or type(error).__name__ in ('ServerTimeoutError','ConnectionTimeoutError','SocketTimeoutError','ClientConnectionError','NoAudioReceived'))}
        write(work/'failure.json',failure);return None,failure

def generate(paragraph,fragment):
    if fragment['kind']=='existing-exact-text-audio':
        source=fragment['audio']
        if pin(source['path'])!=source:raise ValueError('Old audio byte identity changed')
        work=ROOT/'reused'/fragment['id'];work.mkdir(parents=True,exist_ok=False)
        decoded=decode(work,Path(source['path']))
        receipt={'fragment_id':fragment['id'],'paragraph_id':paragraph['id'],'chapter_id':paragraph['chapter_id'],
            'kind':'existing-exact-text-audio','status':'REUSED_EXACT_AUDIO_PENDING_LISTENING',
            'text_sha256':fragment['text_sha256'],'text_zh':fragment['text_zh'],'old_cue_id':fragment['old_cue_id'],
            'voice':VOICE,'rate':RATE,'metadata':None,'WordBoundary_count':None,
            'metadata_unknown_reason':'Original six audio requests did not retain boundary metadata; no duplicate request made.',
            'provider_calls':0,'human_listening_signoff':False,**decoded}
        write(work/'receipt.json',receipt);return receipt
    for attempt in range(1,4):
        receipt,failure=request_one(paragraph,fragment,attempt)
        if receipt:return receipt
        if not failure['transient_retry_eligible'] or attempt==3:return failure
        seconds=3*(2**(attempt-1))
        write(ROOT/'tts'/fragment['id']/f'backoff-after-a{attempt:02d}.json',{'seconds':seconds,'reason':'Recorded transient provider failure; next attempt has its own directory','started_utc':now()})
        time.sleep(seconds)
    raise AssertionError('Unreachable retry state')

def join_wav(target,paths):
    with wave.open(str(target),'wb') as out:
        out.setnchannels(1);out.setsampwidth(2);out.setframerate(24000)
        for path in paths:
            with wave.open(str(path),'rb') as source:
                assert (source.getnchannels(),source.getsampwidth(),source.getframerate())==(1,2,24000)
                while data:=source.readframes(65536):out.writeframesraw(data)
    return wav_info(target)

def publish_chapter(chapter,paragraphs,results):
    work=ROOT/'chapters'/chapter;work.mkdir(parents=True,exist_ok=False)
    ordered=[];cursor=0;paragraph_rows=[]
    for paragraph in paragraphs:
        start=cursor;rows=[]
        for fragment in paragraph['segments']:
            result=results[fragment['id']]
            if 'decoded_PCM' not in result:raise ValueError('Chapter has a failed fragment')
            frames=result['decoded_PCM']['sample_frames']
            row={**result,'chapter_start_sample':cursor,'chapter_end_sample':cursor+frames,
                'chapter_start_seconds':cursor/24000,'chapter_end_seconds':(cursor+frames)/24000}
            rows.append(row);ordered.append(row);cursor+=frames
        paragraph_rows.append({'id':paragraph['id'],'subtitles_zh':paragraph['subtitles_zh'],'subtitles_en':paragraph['subtitles_en'],
            'chapter_start_sample':start,'chapter_end_sample':cursor,'chapter_start_seconds':start/24000,
            'chapter_end_seconds':cursor/24000,'fragments':rows})
    audio=work/'narration.wav';info=join_wav(audio,[row['decoded_audio']['path'] for row in ordered])
    if info['sample_frames']!=cursor:raise ValueError('Actual WAV assembly sample conservation failed')
    index={'schema':'xar.e04.actual-stable-chapter-audio.v2','chapter_id':chapter,'created_utc':now(),'audio':pin(audio),
        'actual_PCM':info,'paragraphs':paragraph_rows,'sample_offsets_are_actual_concatenated_PCM':True,
        'inserted_silence_frames':0,'WordBoundary_scope':'New fragments preserve actual provider ticks relative to returned fragment audio; six reused fragments have null word metadata.',
        'ABC_results':None,'ABC_winner':None,'human_listening_signoff':False,'final_film_ready':False}
    write(work/'audio-index.json',index)
    preserve(audio,f'e4a04-{chapter.lower()}-audio','narration','audio/wav')
    preserve(work/'audio-index.json',f'e4a04-{chapter.lower()}-index')
    print(json.dumps({'event':'CHAPTER_AUDIO_READY','chapter':chapter,'actual_audio_seconds':info['seconds'],
        'index':pin(work/'audio-index.json')},ensure_ascii=False),flush=True)
    return index

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute',action='store_true');parser.add_argument('--workers',type=int,default=4)
    args=parser.parse_args()
    if not args.execute:raise ValueError('Use --execute for authorized real provider calls')
    if not 4<=args.workers<=8:raise ValueError('Provider workers must be4..8')
    for key in list(os.environ):
        if key.upper() in ('HTTP_PROXY','HTTPS_PROXY','ALL_PROXY'):del os.environ[key]
    inputs=prepare(args.workers)
    paragraphs=inputs['paragraphs'];jobs=[(p,f) for p in paragraphs for f in p['segments']]
    assert len(paragraphs)==69 and sum(f['kind']=='existing-exact-text-audio' for p,f in jobs)==6
    assert not any(p['id'].startswith('P-') for p in paragraphs)
    write(ROOT/'execution-argv.json',sys.argv)
    write(ROOT/'progress-start.json',{'created_utc':now(),'paragraphs':69,'fragments':len(jobs),
        'new_provider_fragments':len(jobs)-6,'reused_fragments':6,'workers':args.workers,
        'not_spoken_editorial_blocks':['P-ABC','P-STARVATION'],'C05_scope':'Stable a04 methods/observed qualifications/current unknown boundaries only; no fabricated terminal results.'})
    results={};chapters={};chapter_paragraphs={f'E4-{i:02d}':[p for p in paragraphs if p['chapter_id']==f'E4-{i:02d}'] for i in range(1,7)}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures={pool.submit(generate,p,f):(p,f) for p,f in jobs}
        for future in as_completed(futures):
            paragraph,fragment=futures[future]
            try:result=future.result()
            except Exception as error:
                result={'fragment_id':fragment['id'],'paragraph_id':paragraph['id'],'chapter_id':paragraph['chapter_id'],
                    'status':'FAILED_WORKER_PRESERVED','exception_type':type(error).__name__,'message':str(error)}
                write(ROOT/'failures'/(fragment['id']+'.json'),result)
            results[fragment['id']]=result
            print(json.dumps({'event':'FRAGMENT_FINISHED','id':fragment['id'],'status':result['status'],
                'completed':len(results),'total':len(jobs)},ensure_ascii=False),flush=True)
            chapter=paragraph['chapter_id'];expected=[f['id'] for p in chapter_paragraphs[chapter] for f in p['segments']]
            if chapter not in chapters and all(fid in results for fid in expected):
                if all('decoded_PCM' in results[fid] for fid in expected):chapters[chapter]=publish_chapter(chapter,chapter_paragraphs[chapter],results)
                else:chapters[chapter]={'status':'PARTIAL_CHAPTER_AUDIO_PRESERVED','chapter_id':chapter}
    generated=[r for r in results.values() if r.get('kind')=='new-generated-audio']
    reused=[r for r in results.values() if r.get('kind')=='existing-exact-text-audio']
    failures=[r for r in results.values() if 'decoded_PCM' not in r]
    joined=None;chapter_timeline=[];cursor=0
    if not failures and all('audio' in chapters[f'E4-{i:02d}'] for i in range(1,7)):
        ordered_chapters=[chapters[f'E4-{i:02d}'] for i in range(1,7)]
        for chapter in ordered_chapters:
            frames=chapter['actual_PCM']['sample_frames']
            chapter_timeline.append({'chapter_id':chapter['chapter_id'],'start_sample':cursor,'end_sample':cursor+frames,
                'start_seconds':cursor/24000,'end_seconds':(cursor+frames)/24000,
                'index':pin(ROOT/'chapters'/chapter['chapter_id']/'audio-index.json')})
            cursor+=frames
        full_audio=ROOT/'stable-narration-a04.wav';info=join_wav(full_audio,[row['audio']['path'] for row in ordered_chapters])
        assert info['sample_frames']==cursor
        joined={'audio':pin(full_audio),'actual_PCM':info,'inserted_silence_frames':0,'contains_pending_ABC_result_block':False}
    report={'schema':'xar.e04.actual-full-stable-TTS.v2','created_utc':now(),
        'status':'ALL_STABLE_A04_AUDIO_PRODUCED_PENDING_LISTENING' if not failures else 'PARTIAL_STABLE_AUDIO_ATTEMPT_PRESERVED',
        'paragraphs':69,'fragments':len(jobs),'new_generated_fragments':len(generated),'reused_fragments':len(reused),'failures':failures,
        'actual_all_MP3_container_seconds_sum':sum(r['MP3_container_seconds'] for r in results.values() if 'MP3_container_seconds' in r),
        'actual_stable_decoded_audio_seconds':joined['actual_PCM']['seconds'] if joined else None,
        'stable_assembly':joined,'chapter_timeline':chapter_timeline,'fragments':[results[f['id']] for p,f in jobs],
        'actual_final_episode_seconds':None,'ABC_results':None,'ABC_winner':None,
        'target_editor_seconds':[1800,2100],'delivery_seconds':[1200,2400],
        'actual_stable_audio_in_delivery_range':1200<=joined['actual_PCM']['seconds']<=2400 if joined else None,
        'human_listening_signoff':False,'subtitle_or_film_signoff':False,'original6_audio_regenerated':False,
        'pending':['actualABC final result block','actual bilingual subtitle timing/reading-speed review','complete picture','human1xlistening/viewing/signoff']}
    write(ROOT/'AUDIO-RESULTS.json',report)
    # Each completed chapter is already published for the subtitle lane. All
    # remaining native immutable manifest mutations happen serially here.
    assets=[]
    for parent in (ROOT/'tts',ROOT/'reused',ROOT/'failures'):
        if parent.exists():assets.extend(path for path in sorted(parent.rglob('*')) if path.is_file())
    for index,path in enumerate(assets):
        media='audio/mpeg' if path.suffix=='.mp3' else 'audio/wav' if path.suffix=='.wav' else 'application/x-ndjson' if path.suffix=='.jsonl' else 'text/plain' if path.suffix=='.txt' else 'application/json'
        preserve(path,f'e4a04-output-{index:04d}','narration' if path.suffix in ('.wav','.mp3') else 'process-evidence',media)
    if joined:preserve(ROOT/'stable-narration-a04.wav','e4a04-stable-full-audio','narration','audio/wav')
    preserve(ROOT/'AUDIO-RESULTS.json','e4a04-audio-results')
    write(ROOT/'ROOT-DELIVERY.json',{'schema':'xar.e04.actual-stable-audio-delivery.v2','created_utc':now(),'status':report['status'],
        'report':pin(ROOT/'AUDIO-RESULTS.json'),'native_run':pin(ROOT/'native-run/run-manifest.json'),
        'stable_assembly':joined,'chapters':chapter_timeline,'new_generated_fragments':len(generated),'reused_fragments':len(reused),
        'failed_fragments':len(failures),'actual_final_episode_seconds':None,'ABC_results':None,'ABC_winner':None,
        'human_listening_signoff':False,'subtitle_or_film_signoff':False})
    print(json.dumps({'event':'STABLE_AUDIO_ATTEMPT_COMPLETE','status':report['status'],'new_generated':len(generated),
        'reused':len(reused),'failed':len(failures),'actual_stable_audio_seconds':report['actual_stable_decoded_audio_seconds'],
        'delivery':pin(ROOT/'ROOT-DELIVERY.json')},ensure_ascii=False),flush=True)
    return 1 if failures else 0
if __name__=='__main__':sys.exit(main())
