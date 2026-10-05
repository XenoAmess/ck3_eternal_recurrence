"""Incrementally assemble 69 real dry cue MOVs; no original-raw access."""
import json,hashlib,math,wave,importlib.util
from pathlib import Path
from fractions import Fraction
from datetime import datetime,timezone
from xar_promo import probe_and_write_bound_media
from xar_promo.audio import AudioMixSpec,AudioStem,plan_audio_mix
from xar_promo.process import CommandSpec,run_command
from xar_promo.render import ass_burn_in_filter
R=Path(__file__).parent;C=R.parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def pin(p):
 p=Path(p);h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return {'path':str(p),'bytes':p.stat().st_size,'sha256':h.hexdigest()}
def exact(p):
 assert pin(p['path'])==p,p
 return Path(p['path'])
def new(p,d):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8',newline='\n') as f:
  if isinstance(d,str):f.write(d)
  else:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
def run(argv,label,audit,partial):
 result=run_command(CommandSpec.create(argv,label=label,cwd=R,partial_artifacts=(partial,)),audit_directory=audit)
 print(json.dumps({'step':label,'returncode':result.returncode},ensure_ascii=False),flush=True)
spec=read(R/'picture-input-reviewed-preview-a02.json')
old_path=C/'e4-stable-full-picture-roughcut-a01/actual-render-a01/picture-receipt.json'
new_path=R/'actual-C05-render-a01/picture-receipt.json'
old=read(old_path);inc=read(new_path)
audio=read(exact(spec['A_only_audio_delivery']))
subdelivery_path=C/'e04-A-only-subtitle-timeline-a01/actual-subtitles-a02/ROOT-DELIVERY.json'
subdelivery=read(subdelivery_path)
master=read(exact(subdelivery['full_global']['timeline']));ass=exact(subdelivery['full_global']['subtitles'])
assert audio['actual_PCM']['sample_frames']==master['sample_frames']==37900224
assert master['picture_frames_30fps']==47376
assert audio['B'] is None and audio['C'] is None and audio['ABC_winner'] is None
assert old['total_frames']==35795 and inc['total_frames']==11581
entries={e['cue_id']:(e,'exact-existing-stable-dry-reuse') for e in old['timeline']}
entries.update({e['cue_id']:(e,'new-A-only-C05-dry-render') for e in inc['timeline']})
assert len(entries)==69 and len(master['paragraphs'])==69
root=R/'actual-full-assembly-a01';root.mkdir(exist_ok=False)
ffmpeg=exact(spec['tools']['ffmpeg']);ffprobe=exact(spec['tools']['ffprobe'])
music=exact(spec['music']['source']);narration=exact(audio['stable_audio'])
assert spec['music']['title']=='Quiet Courtly Tension' and spec['music']['gain_db']==-17 and spec['music']['ducking'] is False and spec['music']['normalize'] is False
with wave.open(str(narration),'rb') as f:
 assert (f.getframerate(),f.getnchannels(),f.getsampwidth(),f.getnframes())==(24000,1,2,37900224)
oldclaims=read(C/'e04-full-production-inputs-a04-a01/sources/claim-ledger-player-a04.json')
newclaims=read(exact(spec['claim_ledger']))
oc={v['id']:v for v in oldclaims['claims']};nc={v['id']:v for v in newclaims['claims']}
timeline=[];outputs=[];cursor=0
for paragraph in master['paragraphs']:
 key=paragraph['id'];e,mode=entries[key]
 if not key.startswith('C05'):assert oc[key]['claim_summary']==nc[key]['claim_summary']
 output=exact(e['output']);bound=read(exact(e['bound_probe']))
 v=next(s for s in bound['ffprobe']['streams'] if s['codec_type']=='video')
 assert (v['width'],v['height'],v['r_frame_rate'],int(v['nb_frames']))==(1920,1080,'30/1',e['duration_frames'])
 assert not any(s['codec_type']=='audio' for s in bound['ffprobe']['streams'])
 expected_start=math.ceil(Fraction(paragraph['global_start_sample']*30,24000))
 expected_end=math.ceil(Fraction(paragraph['global_end_sample']*30,24000))
 offset=cursor-expected_start;endoffset=cursor+e['duration_frames']-expected_end
 assert abs(offset)<=1 and abs(endoffset)<=1,(key,offset,endoffset)
 timeline.append({'cue_id':key,'reuse_mode':mode,'output':e['output'],'old_or_increment_bound_probe':e['bound_probe'],'actual_picture_start_frame':cursor,'actual_picture_end_frame':cursor+e['duration_frames'],'canonical_PCM_start_sample':paragraph['global_start_sample'],'canonical_PCM_end_sample':paragraph['global_end_sample'],'canonical_picture_start_frame':expected_start,'canonical_picture_end_frame':expected_end,'picture_cut_start_offset_frames':offset,'picture_cut_end_offset_frames':endoffset,'source_claim':{'ledger':spec['claim_ledger'],'id':key,'source_keys':nc[key]['source_keys'],'status':nc[key]['status']},'original_render_receipt':pin(new_path if key.startswith('C05') else old_path),'dynamic_source_windows':e['dynamic_source_windows'],'actual_source_decodes':e['actual_source_decodes'],'inserted_audio_silence_samples':0})
 outputs.append(e['output']);cursor+=e['duration_frames']
assert cursor==47376
new(root/'ASSEMBLY-INPUT-SNAPSHOT.json',{'input':pin(R/'picture-input-reviewed-preview-a02.json'),'audio_delivery':spec['A_only_audio_delivery'],'full_audio':audio['stable_audio'],'subtitle_delivery':pin(subdelivery_path),'global_ASS':subdelivery['full_global']['subtitles'],'global_timeline':subdelivery['full_global']['timeline'],'old_53_render_receipt':pin(old_path),'new_16_render_receipt':pin(new_path),'producer':pin(__file__),'ordered_cues':timeline,'duration_frames':cursor,'actual_PCM_samples':37900224,'B_C_winner':None})
concat=root/'picture-concat.txt'
assert all("'" not in p['path'] and '\n' not in p['path'] for p in outputs)
new(concat,'ffconcat version 1.0\n'+''.join("file '"+Path(p['path']).as_posix()+"'\n" for p in outputs))
dry=root/'picture-dry.mov'
run([ffmpeg,'-hide_banner','-nostdin','-n','-f','concat','-safe','0','-i',concat,'-map','0:v:0','-an','-c','copy','-movflags','+faststart',dry],'69 ordered native-picture cue assembly',root/'concat-command-audit',dry)
duration=cursor/30
theme=AudioMixSpec(stems=(AudioStem('narration',narration),AudioStem('series-theme',music,gain_db=-17)),duration_seconds=duration,sample_rate=48000,channels=2,normalize=False,metadata={'ducking':False,'music':'Quiet Courtly Tension','gain_db':-17,'continuous_across_cues':True,'exact_narration_PCM_no_inserted_silence':True})
mix=plan_audio_mix(theme,input_start_index=1,output_label='mixed')
graph='[0:v]'+ass_burn_in_filter(ass)+'[subtitled];'+mix.filtergraph
final=root/'picture-A-only-review.mp4'
run([ffmpeg,'-hide_banner','-nostdin','-n','-threads','1','-i',dry,'-i',narration,'-stream_loop','-1','-i',music,'-filter_complex_threads','1','-filter_complex',graph,'-map','[subtitled]','-map','[mixed]','-c:v','libx264','-preset','ultrafast','-crf','22','-threads','2','-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-frames:v',str(cursor),'-t',f'{duration:.9f}','-movflags','+faststart',final],'A-only full global subtitle clock and fixed minus17dB series theme',root/'final-encode-command-audit',final)
probe_and_write_bound_media(str(ffprobe),final,output_path=root/'picture.bound-probe.json',audit_directory=root/'final-probe-command-audit')
bound=read(root/'picture.bound-probe.json');v=next(s for s in bound['ffprobe']['streams'] if s['codec_type']=='video');a=next(s for s in bound['ffprobe']['streams'] if s['codec_type']=='audio')
assert (v['width'],v['height'],v['r_frame_rate'],int(v['nb_frames']))==(1920,1080,'30/1',47376)
assert abs(float(v['duration'])-duration)<0.000002
assert (a['codec_name'],a['sample_rate'],a['channels'])==('aac','48000',2)
report={'schema':'xar.e04.incremental-A-only-full-picture.v1','state':'ACTUAL_SIX_CHAPTER_A_ONLY_REVIEW_CANDIDATE_RENDERED','created_utc':datetime.now(timezone.utc).isoformat(),'picture':pin(final),'dry_picture':pin(dry),'bound_probe':pin(root/'picture.bound-probe.json'),'assembly_input':pin(root/'ASSEMBLY-INPUT-SNAPSHOT.json'),'producer':pin(__file__),'timeline':timeline,'actual_PCM_samples':37900224,'actual_PCM_seconds':1579.176,'duration_frames':47376,'actual_video_seconds':duration,'final_grid_tail_seconds':duration-1579.176,'inserted_narration_silence_samples':0,'old_53_exact_dry_MOVs_reused':53,'new_C05_cues_rendered':16,'original_stable_raw_redecodes':0,'no_frame_holds_or_source_loops':True,'music_gain_db':-17,'ducking':False,'normalize':False,'B':None,'C':None,'winner':None,'exact_A_arrival_tick':None,'continuous_source_clean_review':False,'human_full_1x_review':False,'human_signoff':False,'full_film_ready':False,'preview_only':True,'SDK_UI_Game_bus_Git_operations':0}
new(root/'picture-receipt.json',report)
print(json.dumps({'state':report['state'],'picture':report['picture'],'frames':47376,'actual_PCM_seconds':1579.176},ensure_ascii=False),flush=True)
