"""Project-only pending review wiring; uses the existing xar-promo engine."""
from pathlib import Path
from dataclasses import replace
import hashlib,json,os
from xar_promo.pipeline import PipelineDependencies,PipelineDraft,PipelineInvocation,SegmentDraft
from xar_promo.render import RenderOptions,plan_render
from xar_promo.sources import STILL,VIDEO,VisualSource,VisualProbeResult
from xar_promo.media import probe_media
from xar_promo.process import run_command
from war_ai_promo.composer import artifact,plan_capture_render

def need(ok,why):
 if not ok:raise ValueError(why)
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def select_path(ref,run,run_path):
 if run is None:return Path(ref['path'])
 record=next((r for r in run.artifacts if r.artifact_id==ref['artifact_id']),None)
 need(record is not None and record.bytes==ref['bytes'] and record.sha256.lower()==ref['sha256'].lower(),'missing or changed preserved source '+ref['artifact_id'])
 return artifact(run,run_path,ref['artifact_id'])
def metadata(ref,run,run_path):
 p=select_path(ref,run,run_path);b=p.read_bytes()
 need(len(b)==ref['bytes'] and hashlib.sha256(b).hexdigest()==ref['sha256'],'small metadata changed')
 return json.loads(b.decode('utf-8-sig'))
def compose(config,run,*,config_path,run_path,workdir,adapter_factory,preset_factory,validate_only):
 del config_path
 need(adapter_factory()['id']==config.adapter and preset_factory()['id']==config.preset,'wrong components')
 if run is None:
  need(validate_only is True,'build requires preserved native inputs')
  path=os.environ.get('XAR_E04_ROUGH_INPUT');need(path,'explicit rough input path required');data=load(path)
 else:data=load(artifact(run,run_path,'production-inputs-v1'))
 need(data.get('schema')=='xar.e04.rough-review-inputs.v1' and data.get('review_only')is True and data.get('human_signoff')is False,'explicit pending review scope required')
 need(data.get('render_geometry')==[1920,1080] and all(type(v)is int for v in data['render_geometry']),'explicit FHD required')
 measured=metadata(data['metadata']['measured'],run,run_path);method=metadata(data['metadata']['method'],run,run_path);raster=metadata(data['metadata']['raster'],run,run_path)
 rows=measured['cues'];cues=[q for ch in config.chapters for q in ch.cues];by={r['id']:r for r in rows}
 need(len(rows)==len(by)==69 and [r['id']for r in rows]==[q.cue_id for q in cues],'original69 mismatch')
 need(sum(v['end_frame_exclusive']-v['start_frame']for v in method['cues'])==58406,'actual clock changed')
 pending=set(data['pending_cues']);overrides=data['visual_overrides'];need(not(pending&set(overrides)),'pending and selected overlap')
 need(pending<=set(by) and set(overrides)<=set(by),'unknown cue')
 preview=data.get('preview_cue_ids');partial=preview is not None;selected=set(by)
 if partial:
  need(type(preview)is list and bool(preview) and all(type(k)is str for k in preview),'preview must be a nonempty cue list')
  need(len(preview)==len(set(preview)),'duplicate preview cue')
  selected=set(preview);need(selected<=set(by),'unknown preview cue')
  need(preview==[r['id']for r in rows if r['id']in selected],'preview cue order must match frozen69')
  need(not(selected&pending),'pending cue cannot enter preview')
  need(selected<=set(overrides),'preview requires actual rough inputs')
 if not validate_only:need(not(pending&selected),'key footage is pending; no static fallback allowed')
 cards={r['card_id']:r for r in raster['cards']};mapping={r['id']:r for r in method['cues']};segments=[];raw_sources={};raw_render_windows={}
 for row,cue in zip(rows,cues):
  key=row['id'];start=0.0;need(row['zh']==cue.narration['zh-CN']and row['en']==cue.subtitles['en'],'frozen speech differs')
  if key not in selected:continue
  audio=select_path({**row['audio'],'artifact_id':row['audio_artifact_id']},run,run_path)
  if key in pending:visual=VisualSource(key,VIDEO,Path('pending')/(key+'.mp4'),'pending-key-footage',requires_resolution=True,metadata={'pending':True})
  elif key in overrides:
   v=overrides[key];need(v['role']=='rough-context-only' and v['continuous_clean']is False and v['event_PTS']is None and v['approval']=='pending','rough limit absent')
   first,stop=v['source_frames'];need(type(first)is int and type(stop)is int and 0<=first<stop<=v['source_frame_count'],'invalid actual frame interval')
   hold=v.get('tail_hold_frames',0);need(type(hold)is int and 0<=hold<=27,'invalid rough context hold')
   need(stop-first+hold==round(row['duration_seconds']*30),'source interval plus labeled tail hold must cover exact measured cue')
   need(hold==0 or (key=='C01-01' and v['source']['sha256'].lower()=='665fe47cdcd6600cc526460818a9aaeae149857bb5505153510361e8c4000ab2' and first==15 and stop==600 and hold==27),'tail hold is only admitted for R204 C01-01')
   media=select_path(v['source'],run,run_path);visual=VisualSource(key,VIDEO,media,'rough-context-pending-review',metadata={'actual_outcome_credit':False,'continuous_clean':False,'event_PTS':None})
   source_key=str(media.resolve());pin=(v['source']['bytes'],v['source']['sha256'].lower(),v['source_frame_count'])
   need(source_key not in raw_sources or raw_sources[source_key]==pin,'same raw path has conflicting source pins')
   raw_sources[source_key]=pin
   cue_frames=round(row['duration_seconds']*30);window_key=(source_key,first,cue_frames);tail=(hold,stop-first,cue_frames)
   need(window_key not in raw_render_windows or raw_render_windows[window_key]==tail,'same source window has conflicting tail hold')
   raw_render_windows[window_key]=tail;start=first/30
  else:
   card=cards[mapping[key]['card_id']];ref={**card['png'],'path':str(Path(data['metadata']['raster']['path']).parent/card['png']['path']),'artifact_id':'source-card-still.'+card['card_id']}
   visual=VisualSource(key,STILL,select_path(ref,run,run_path),'source-explanation-card',metadata={'actual_outcome_credit':False})
  segments.append(SegmentDraft(key,visual,RenderOptions(1920,1080,30,row['duration_seconds'],preset='veryfast',crf=21),{'zh-CN':row['zh'],'en':row['en']},prepared_narration=audio,start_seconds=start))
 def subtitles(segment,narration,*,workdir):
  del narration,workdir
  ref=mapping[segment.segment_id]['subtitle'];ref={**ref,'path':str(Path(data['repo_root'])/ref['path']),'artifact_id':'source-subtitle.'+segment.segment_id}
  body=select_path(ref,run,run_path).read_text(encoding='utf-8-sig')
  label=('PARTIAL PREVIEW / NO SIGNOFF / 'if partial else '')+'REVIEW / CLEAN PENDING / EVENT FRAME UNVERIFIED'
  return body+'\nDialogue: 9,0:00:00.00,9:59:59.99,English,review,0,0,0,,{\\an7\\pos(48,48)\\fs36}'+label+'\n'
 def inspect(p):
  if Path(p).suffix.lower()=='.png':
   from PIL import Image
   with Image.open(p)as im:return VisualProbeResult('image/png',im.width,im.height)
  probe=probe_media(os.environ.get('WAR_PROMO_FFPROBE','ffprobe'),p,audit_directory=Path(workdir)/'audit'/'probe'/Path(p).stem);s=probe.video_streams[0]
  need((s.width,s.height)==(1280,720),'rough client geometry changed');return VisualProbeResult('video/mp4',s.width,s.height)
 def planner(**kwargs):
  key=str(Path(kwargs['video_input']).resolve())
  if key not in raw_sources:return plan_render(**kwargs)
  plan=plan_capture_render(**kwargs);commands=[]
  for command in plan.commands:
   argv=list(command.spec.argv);i=argv.index('-filter_complex')+1;old=argv[i]
   a='scale=1920:1080:force_original_aspect_ratio=decrease:flags=lanczos';b='pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black'
   need(old.count(a)==old.count(b)==1,'upstream geometry seam changed')
   graph=old.replace(a,'scale=1536:864:force_original_aspect_ratio=decrease:flags=lanczos').replace(b,'pad=1920:1080:192:0:color=black')
   window_key=(key,round(kwargs['start_seconds']*30),round(kwargs['options'].duration_seconds*30))
   hold,source_count,cue_count=raw_render_windows[window_key]
   if hold:
    target=f'[0:v]trim=duration={cue_count/30:.6f},setpts=';source=f'[0:v]trim=duration={source_count/30:.6f},setpts='
    seam='setsar=1,trim=duration='
    need(graph.count(target)==graph.count(seam)==1,'R204 selected trim or tail seam changed')
    graph=graph.replace(target,source,1).replace(seam,f'setsar=1,tpad=stop_mode=clone:stop={hold},trim=duration=',1)
   argv[i]=graph;argv[-1:-1]=['-threads','1','-filter_complex_threads','1'];commands.append(replace(command,spec=replace(command.spec,argv=tuple(argv))))
  return replace(plan,commands=tuple(commands))
 def unresolved(*args,**kwargs):raise ValueError('pending key footage cannot render or become a still')
 output=Path('episode04-review02-PARTIAL-ROUGH-PREVIEW-NO-SIGNOFF.mp4')if partial else Path('episode04-review02-MIXED-ROUGH-PENDING.mp4')
 artifact_id='episode04-review02-partial-rough-preview-no-signoff'if partial else 'episode04-review02-mixed-rough-pending'
 return PipelineInvocation(PipelineDraft(config,tuple(segments),output,artifact_id,'video/mp4'),PipelineDependencies(os.environ.get('WAR_PROMO_FFMPEG','ffmpeg'),subtitles,run_command,inspect,visual_resolver=unresolved,render_planner=planner),Path(workdir))
