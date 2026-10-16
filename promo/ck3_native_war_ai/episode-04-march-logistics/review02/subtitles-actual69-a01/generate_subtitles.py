"""Text/timing-only E04 subtitle export via existing legacy captions and xar-promo ASS API."""
from pathlib import Path
from datetime import datetime,timezone
from decimal import Decimal,ROUND_HALF_UP
import bisect,hashlib,html,importlib.metadata,json,math,sys
REPO=Path('D:/workspace/ck3_eternal_recurrence');ROOT=Path('C:/ck3-e04-resume-20261015-a01')
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(REPO/'promo/ck3_native_war_ai/integration/src'))
import war_ai_promo.captions as legacy
from xar_promo.subtitles import AssCue,AssDocumentConfig,AssStyleConfig,SubtitleTrackConfig,render_ass_document
MACHINE='desktop-3fevhd2-1c74096080'
def need(ok,why):
    if not ok:raise ValueError(why)
def sha(data):return hashlib.sha256(data).hexdigest()
def pin(path):
    data=path.read_bytes();return {'path':path.as_posix(),'bytes':len(data),'sha256':sha(data)}
def read_bound(row):
    path=Path(row['path']);raw=path.read_bytes();need(len(raw)==row['bytes'] and sha(raw)==row['sha256'],'changed metadata '+str(path));return json.loads(raw)
def write(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
def dump(path,obj):write(path,json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def milliseconds(seconds):return int((Decimal(str(seconds))*1000).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
def srt_time(ms):
    hours,remaining=divmod(ms,3600000);minutes,remaining=divmod(remaining,60000);seconds,millis=divmod(remaining,1000)
    return f'{hours:02}:{minutes:02}:{seconds:02},{millis:03}'
def srt(rows):
    return '\n\n'.join(f'{i}\n{srt_time(row[0])} --> {srt_time(row[1])}\n{row[2]}' for i,row in enumerate(rows,1))+'\n'
def normalized(value):return ''.join(value.split())
def shared_bilingual(zh,en):
    breaks=sorted({x for row in zh+en for x in row[:2]});result=[];i=j=0
    for start,end in zip(breaks,breaks[1:]):
        while i<len(zh) and zh[i][1]<=start:i+=1
        while j<len(en) and en[j][1]<=start:j+=1
        z=zh[i][2] if i<len(zh) and zh[i][0]<=start<zh[i][1] else ''
        e=en[j][2] if j<len(en) and en[j][0]<=start<en[j][1] else ''
        text='\n'.join(x for x in [z,e] if x)
        if text:
            if result and result[-1][1]==start and result[-1][2]==text:result[-1]=(result[-1][0],end,text)
            else:result.append((start,end,text))
    return result
def main():
    need(not (OUT/'ROOT-DELIVERY.actual.json').exists(),'sealed attempt exists')
    need(importlib.metadata.version('xar-promo-toolchain')=='0.2.1','this text-only export binds existing0.2.1 API')
    result_path=ROOT/'review02-tts-rest68-a03/RESULT.actual.json';actual=json.loads(result_path.read_bytes())
    measured_binding=actual['merged69']['production_inputs69'];time_binding=actual['merged69']['timeline69']
    need(measured_binding['sha256']=='fe7d7d291805859a9ffac81bb48a25388b73004297f475da20aedd8404894e50','unexpected source merged69')
    need(time_binding['sha256']=='14b41b9aa02f8f969d4e21449840a5b6d03c2c96283595f52b312958616dc8c0','unexpected source timeline69')
    measured=read_bound(measured_binding);timeline=read_bound(time_binding)
    materialized=ROOT/'review02-render-inputs-a03-materialized-a01'
    script_path=materialized/'inputs/narration.cues.bilingual.json';english_path=materialized/'inputs/english.cues.json'
    config_path=materialized/'project/promo-project.json'
    need(pin(script_path)['sha256']=='8d7de9e7c01e691dd2ac72af335ba35717f2c3a6238a0fe6045ddc4f7b6bfc16','spoken source changed')
    need(pin(english_path)['sha256']=='401734ae8f00c890ebec49504bb50b8a551b85fa17f525fddf54aad6b8b682ff','English source changed')
    script=json.loads(script_path.read_bytes());english=json.loads(english_path.read_bytes());config=json.loads(config_path.read_bytes())
    english_by_id={r['id']:r for r in english['cues']};rows=measured['cues'];timing=timeline['cues']
    need(len(rows)==len(timing)==len(script['cues'])==len(english_by_id)==69,'expected69 exact joined cues')
    need([r['id'] for r in rows]==[r['id'] for r in timing]==[r['id'] for r in script['cues']],'cue order differs')
    global_cues=[];srt_tracks={'zh':[],'en':[]};cue_audit=[];source_rows=[]
    for row,timed,original in zip(rows,timing,script['cues']):
        key=row['id'];eng=english_by_id[key]
        need(row['zh']==original['zh'] and row['en']==original['en']==eng['en'],'frozen bilingual text differs '+key)
        need(sha(row['zh'].encode())==eng['chinese_utf8_sha256'],'English ChineseSHA binding differs '+key)
        need(math.isclose(row['duration_seconds'],timed['frames']/30,abs_tol=1e-9),'duration/frame mismatch '+key)
        local=legacy.caption_cues(row);base=timed['start_frame']/30
        zh=[cue for cue in local if cue.track_id=='zh'];en=[cue for cue in local if cue.track_id=='en']
        need(normalized(''.join(cue.text for cue in zh))==normalized(row['zh']),'Chinese caption text conservation '+key)
        need(normalized(''.join(cue.text for cue in en))==normalized(row['en']),'English caption text conservation '+key)
        for cue in local:
            need(0<=cue.start_seconds<cue.end_seconds<=row['speech_duration_seconds']+1e-8,'caption outside actualspeech '+key)
            shifted=AssCue(key+'-'+cue.cue_id,cue.track_id,base+cue.start_seconds,base+cue.end_seconds,cue.text)
            global_cues.append(shifted)
            msrow=(milliseconds(shifted.start_seconds),milliseconds(shifted.end_seconds),shifted.text)
            need(msrow[0]<msrow[1],'zero-length millisecond caption '+key)
            srt_tracks[cue.track_id].append(msrow)
        # Use the exact current composer subtitle route for each unbound cue.
        # Gameplay-specific placement must be regenerated after actual visual binding.
        write(OUT/'per-cue-ass'/f'{key}.ass',legacy.subtitle_document(row))
        cue_audit.append({'id':key,'start_frame':timed['start_frame'],'end_frame_exclusive':timed['end_frame_exclusive'],'speech_seconds':row['speech_duration_seconds'],'duration_seconds':row['duration_seconds'],'Chinese_source_utf8_sha256':sha(row['zh'].encode()),'English_utf8_sha256':sha(row['en'].encode()),'Chinese_provider_sentence_events':sum(e.get('type')=='SentenceBoundary' for e in row.get('sentence_boundaries',[])),'zh_caption_events':len(zh),'en_caption_events':len(en),'normalized_text_conservation':True})
        source_rows.append({'id':key,'chapter_id':row['chapter_id'],'shot_id':row['shot_id'],'zh':row['zh'],'en':row['en'],'speech_duration_seconds':row['speech_duration_seconds'],'duration_seconds':row['duration_seconds'],'sentence_boundaries':row.get('sentence_boundaries',[]),'audio_binding_reference_only':row['audio']})
    total=timeline['total_frames']/30
    tracks=[SubtitleTrackConfig('zh','zh-CN',2,AssStyleConfig(name='Chinese',font_name='Microsoft YaHei',font_size=49,bold=True,alignment=2,margin_left=145,margin_right=145,margin_vertical=178,outline=2.5)),SubtitleTrackConfig('en','en',1,AssStyleConfig(name='English',font_name='Microsoft YaHei',font_size=31,bold=False,primary_colour='&H00BBC4C9',margin_left=145,margin_right=145,margin_vertical=65,outline=2))]
    ass=render_ass_document(AssDocumentConfig('CK3 Episode04 Review02 actual69 narration',2560,1440,duration_seconds=total),tracks,global_cues,available_font_names={'Microsoft YaHei'})
    write(OUT/'subtitles.zh-en.ass',ass)
    for lang,track in srt_tracks.items():
        need(all(a[1]<=b[0] for a,b in zip(track,track[1:])),'within-language overlap '+lang)
        write(OUT/f'subtitles.{lang}.srt',srt(track))
    bilingual=shared_bilingual(srt_tracks['zh'],srt_tracks['en']);write(OUT/'subtitles.zh-en.srt',srt(bilingual))
    chapter_title={c['id']:c['title']['zh-CN'] for c in config['chapters']}
    chapters=[]
    for timed in timing:
        if not chapters or chapters[-1]['chapter_id']!=timed['chapter_id']:
            chapters.append({'chapter_id':timed['chapter_id'],'title':chapter_title[timed['chapter_id']],'start_frame':timed['start_frame'],'end_frame_exclusive':timed['end_frame_exclusive'],'cue_ids':[timed['id']]})
        else:chapters[-1]['end_frame_exclusive']=timed['end_frame_exclusive'];chapters[-1]['cue_ids'].append(timed['id'])
    for c in chapters:c.update(start_seconds=c['start_frame']/30,end_seconds=c['end_frame_exclusive']/30,duration_seconds=(c['end_frame_exclusive']-c['start_frame'])/30)
    need(len(chapters)==6 and chapters[0]['start_frame']==0 and chapters[-1]['end_frame_exclusive']==58406,'chapter coverage mismatch')
    dump(OUT/'chapter-timing.actual.json',{'machine_id':MACHINE,'frame_rate':30,'total_frames':58406,'duration_seconds':total,'chapters':chapters,'video_rendered':False})
    write(OUT/'chapters.ffmetadata',';FFMETADATA1\n'+''.join(f"\n[CHAPTER]\nTIMEBASE=1/30\nSTART={c['start_frame']}\nEND={c['end_frame_exclusive']}\nTITLE={c['title'].replace('=',r'\=')}\n" for c in chapters))
    write(OUT/'chapters.txt','\n'.join(f"{int(c['start_seconds'])//60:02}:{int(c['start_seconds'])%60:02} {c['title']}" for c in chapters)+'\n')
    dump(OUT/'subtitle-inputs.actual.json',{'format_version':1,'machine_id':MACHINE,'frame_rate':30,'duration_seconds':total,'cues':source_rows,'audio_payload_read':False,'English_timing':'Proportional English sentences within each actual measured speech span; not English forcedalignment','Chinese_timing':'Existing legacy.caption_cues uses actual provider SentenceBoundary offsets/durations then unchanged timed_groups','placement':'Existing defaultcard bilingual style only; actual gameplay placement remains pending visual binding'})
    dump(OUT/'CHECK.actual.json',{'machine_id':MACHINE,'at_utc':datetime.now(timezone.utc).isoformat(),'xar_promo_toolchain_version':importlib.metadata.version('xar-promo-toolchain'),'legacy_captions_source':pin(Path(legacy.__file__)),'existing_public_ASS_API':'xar_promo.subtitles.render_ass_document','original69_order_exact':True,'originalChinese_and_newEnglish_hash_join':True,'normalized_caption_text_conserved_all69':True,'per_track_no_overlap':True,'ASS_contract_validation_PASS':True,'total_frames':58406,'duration_seconds':total,'chapter_count':6,'cue_audit':cue_audit,'subtitle_event_counts':{k:len(v) for k,v in srt_tracks.items()}|{'bilingual_srt':len(bilingual)},'minimum_bilingual_srt_interval_milliseconds':min(e-s for s,e,_ in bilingual),'provider_calls':0,'audio_payload_reads':0,'audio_probes':0,'media_processes':0,'SDK_desktop_calls':0,'video_rendered':False,'human_signoff':False})
    dump(OUT/'SOURCE-PINS.json',{'machine_id':MACHINE,'at_utc':datetime.now(timezone.utc).isoformat(),'actual_result':pin(result_path),'measured69_metadata':measured_binding,'timeline69_metadata':time_binding,'bilingual_script':pin(script_path),'English_hashbound':pin(english_path),'project_config':pin(config_path),'audio_source_pins_referenced_only':True,'input_path_resolution':'Root RESULT merged69 points to review02-audio-rest68-edge731-a03; no assumed same-name path under tts-run'})
    write(OUT/'README.md','''# Review02 actual69字幕

由现有legacy.caption_cues/subtitle_document与xar-promo0.2.1公开ASS API生成，仅使用冻结双语文本、actual provider SentenceBoundary和actual30fps合并时间线。ZH时间来自实际中文provider句边界；EN按已有工具规则在该段真实语音时长内按句长比例分配，不是英文强制对齐。没有读取MP3、调用provider、ffprobe、转码或接入游戏。

subtitles.zh-en.ass保留项目2560×1440的49/31号双语样式；zh/en.srt分别保存独立轨，zh-en.srt将两轨边界取并集，保留两轨各自实际/比例计时。per-cue-ass供现有composer接线。当前是未绑定画面的默认图卡布局，实际gameplay镜头确定后必须按原工具重新定位，不能把这些字幕视作画面避让已签核。

chapter-timing.actual.json与chapters.ffmetadata保留30fps整数帧边界。chapters.txt只是便于阅读的向下取整MM:SS入口。全长58406帧/1946.866666667秒。源文及输入哈希见SOURCE-PINS.json，逐段守恒、轨内无重叠和ASS合同验证见CHECK.actual.json。

subtitle-inputs.actual.json是可复用文本/计时输入；audio_binding_reference_only只是原机器的来源引用，不能拿本机同名MP3冒充。视频尚未render、人工完整1×审阅和签核均未完成，研究卡信用不变。
''')
    destination='promo/ck3_native_war_ai/episode-04-march-logistics/review02/subtitles-actual69-a01'
    deliverable=[p for p in sorted(OUT.rglob('*')) if p.is_file()]
    copies=[{'source':str(p),'destination_repo_relative':destination+'/'+p.relative_to(OUT).as_posix(),'bytes':p.stat().st_size,'sha256':pin(p)['sha256']} for p in deliverable]
    dump(OUT/'copy-plan.json',{'schema':'episode04.subtitle-copy-plan.v1','source_machine_id':MACHINE,'copies':copies,'copy_audio':False,'copy_video':False,'reject_different_existing_bytes':True,'Root_intake_only':True})
    current=sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())
    receipt={'machine_id':MACHINE,'at_utc':datetime.now(timezone.utc).isoformat(),'state':'ACTUAL69_TEXT_TIMED_BILINGUAL_SUBTITLE_EXPORTED_NOT_RENDERED','source_pins':pin(OUT/'SOURCE-PINS.json'),'check':pin(OUT/'CHECK.actual.json'),'copy_plan':pin(OUT/'copy-plan.json'),'key_outputs':[pin(OUT/name) for name in ['subtitles.zh-en.ass','subtitles.zh.srt','subtitles.en.srt','subtitles.zh-en.srt','chapter-timing.actual.json','chapters.ffmetadata','subtitle-inputs.actual.json']],'per_cue_ASS_count':69,'chapter_count':6,'duration_seconds':total,'package_bytes_before_receipt':current,'package_cap_bytes':2*1024**2,'actual_audio_read_or_rehash':0,'provider_calls':0,'media_processes':0,'main_tree_writes':0,'human_signoff':False,'rendered_video_count':0,'research_card_credit_added':0}
    dump(OUT/'ROOT-DELIVERY.actual.json',receipt)
    final=sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file());need(final<=2*1024**2,'package2MiB exceeded')
    print(json.dumps({'delivery':pin(OUT/'ROOT-DELIVERY.actual.json'),'bytes':final,'counts':{k:len(v) for k,v in srt_tracks.items()}|{'bilingual_srt':len(bilingual)},'chapters':chapters,'audio_read':0,'rendered_video':0},ensure_ascii=False))
if __name__=='__main__':main()
