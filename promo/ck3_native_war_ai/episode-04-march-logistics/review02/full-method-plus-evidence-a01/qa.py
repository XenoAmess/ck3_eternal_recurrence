from __future__ import annotations
from dataclasses import replace
import json
from pathlib import Path
import shutil
import sys
sys.dont_write_bytecode=True

from intake import ROOT,MACHINE,now,pin,write
from assemble import MOVIE,MANIFEST,total,cli,preserve,runner
from xar_promo import probe_and_write_bound_media
from xar_promo.media import load_bound_media_probe
from xar_promo.process import CommandSpec
from xar_promo.review import plan_review_package,execute_review_frame_plan,write_review_template

QA=ROOT/'qa-a01'

def call(label,argv):
 assert total()<251658240
 return runner(CommandSpec.create(argv,label=label,cwd=ROOT),audit_directory=QA/'process'/label)

def main():
 sys.stdout.reconfigure(encoding='utf-8')
 assert not QA.exists()
 assembly=json.loads((ROOT/'ASSEMBLY.actual.json').read_bytes()); assert pin(MOVIE)==assembly['movie']
 QA.mkdir()
 probe_and_write_bound_media(shutil.which('ffprobe'),MOVIE,output_path=QA/'movie.bound-probe.json',audit_directory=QA/'bound-probe-audit')
 metadata=call('metadata-and-chapters',[shutil.which('ffprobe'),'-v','error','-show_streams','-show_format','-show_chapters','-of','json',str(MOVIE)])
 assert not metadata.stderr
 meta=json.loads(metadata.stdout); video=next(s for s in meta['streams'] if s['codec_type']=='video'); audio=next(s for s in meta['streams'] if s['codec_type']=='audio')
 assert video['codec_name']=='h264' and [video['width'],video['height']]==[1920,1080] and video['r_frame_rate']=='30/1' and int(video['nb_frames'])==62305
 assert audio['codec_name']=='aac' and audio['sample_rate']=='48000' and audio['channels']==2
 assert len(meta['chapters'])==5
 print(json.dumps({'phase':'packet-pts','movie_bytes':meta['format']['size'],'duration':meta['format']['duration']}),flush=True)
 packets=call('packet-pts',[shutil.which('ffprobe'),'-v','error','-show_entries','packet=stream_index,pts_time,dts_time,duration_time','-of','compact=p=0:nk=0',str(MOVIE)])
 assert not packets.stderr
 groups={video['index']:[],audio['index']:[]}
 for line in packets.stdout.splitlines():
  fields=dict(item.split('=',1) for item in line.split('|') if '=' in item)
  if 'stream_index' not in fields: continue
  index=int(fields['stream_index'])
  if index in groups: groups[index].append((float(fields['pts_time']),float(fields['dts_time'])))
 videos=groups[video['index']]; audios=groups[audio['index']]
 vpts=sorted(p[0] for p in videos); apts=[p[0] for p in audios]
 vgaps=[b-a for a,b in zip(vpts,vpts[1:])]; agaps=[b-a for a,b in zip(apts,apts[1:])]
 assert len(videos)==62305 and min(vgaps)>0 and max(vgaps)<0.067 and min(agaps)>0 and max(agaps)<0.05
 for values in groups.values():
  dts=[p[1] for p in values]; assert all(b>a for a,b in zip(dts,dts[1:]))
 print(json.dumps({'phase':'strict-new-file-full-AV-decode','frames':len(videos),'single_FFmpeg_thread':True}),flush=True)
 decode=call('strict-new-file-full-AV-decode',[shutil.which('ffmpeg'),'-hide_banner','-nostdin','-v','error','-xerror','-threads','1','-filter_threads','1','-filter_complex_threads','1','-i',str(MOVIE),'-map','0:v:0','-map','0:a:0','-f','null','NUL'])
 assert decode.returncode==0 and not decode.stderr
 print(json.dumps({'phase':'full-AV-decode-passed-pending-review-frames'}),flush=True)
 storyboard=json.loads((ROOT/'storyboard.actual.json').read_bytes())
 broad={'chapters':[{'id':p['id'],'start_seconds':p['start_seconds'],'end_seconds':min(p['end_seconds'],float(meta['format']['duration']))} for p in storyboard['main_parts']]}
 write('qa-a01/review-storyboard.actual.json',broad)
 cli('review-plan-only','review',MOVIE,'--storyboard',QA/'review-storyboard.actual.json','--probe',QA/'movie.bound-probe.json','--output-directory',QA/'pending-review','--audit-directory',QA/'review-audit','--ffmpeg',shutil.which('ffmpeg'),'--plan-only')
 assert not (QA/'pending-review').exists()
 bound=load_bound_media_probe(QA/'movie.bound-probe.json',media_path=MOVIE)
 plan=plan_review_package(ffmpeg=shutil.which('ffmpeg'),artifact_path=MOVIE,probe=bound.probe,storyboard_timeline=broad,output_directory=QA/'pending-review',audit_directory=QA/'review-audit',working_directory=ROOT)
 adapted=[]; adaptations=[]
 for frame in plan.frames:
  original=frame.command.spec; argv=list(original.argv); i=argv.index('-ss'); seek=argv[i:i+2]; del argv[i:i+2]
  i=argv.index('-i'); argv[i:i]=['-threads','1',*seek]
  argv[-1:-1]=['-threads','1']
  changed=replace(original,argv=tuple(argv),label=original.label+' (input seek, exact decode)')
  adapted.append(replace(frame,command=replace(frame.command,spec=changed)))
  adaptations.append({'frame':frame.frame_id,'original_plan_argv':list(original.argv),'actual_argv':argv,'target_seconds':str(frame.timestamp_seconds),'reason':'Avoid decoding all preceding32min for sparse frame; FFmpeg default accurate input seek decodes from keyframe to target; no stream-copy seek.'})
 plan=replace(plan,frames=tuple(adapted))
 write('qa-a01/REVIEW-FRAME-PLAN.actual.json',{'machine_id':MACHINE,'observed_at_utc':now().isoformat(),'public_api':'plan_review_package + execute_review_frame_plan + write_review_template','CLI_actual_review_executed':False,'CLI_review_plan_only_executed':True,'adaptations':adaptations})
 results=execute_review_frame_plan(plan,command_runner=runner)
 template=QA/'pending-review/review-template.json'; write_review_template(template,plan)
 pending={'schema':'xar.e04.full-review-public-api-pending-package.v1','machine_id':MACHINE,'observed_at_utc':now().isoformat(),'state':'pending-human-review','is_signoff':False,'approval_granted':False,'artifact':pin(MOVIE),'template':pin(template),'public_plan':pin(QA/'REVIEW-FRAME-PLAN.actual.json'),'frames':[{'id':f.frame_id,'timestamp_seconds':str(f.timestamp_seconds),'file':pin(f.final_output),'actual_command_returncode':r.returncode,'actual_command_audit':str(r.audit_directory)} for f,r in zip(plan.frames,results)]}
 write('qa-a01/pending-review/PENDING-PACKAGE.actual.json',pending)
 result={'schema':'xar.e04.full-review-technical-qa.v1','machine_id':MACHINE,'observed_at_utc':now().isoformat(),'status':'GREEN_AUTOMATED_PENDING_SPARSE_AI_AND_HUMAN_REVIEW','movie':pin(MOVIE),'metadata':meta,'bound_probe':pin(QA/'movie.bound-probe.json'),'video_packets':len(videos),'audio_packets':len(audios),'first_video_pts':vpts[0],'last_video_pts':vpts[-1],'maximum_video_pts_gap_seconds':max(vgaps),'maximum_audio_pts_gap_seconds':max(agaps),'video_audio_dts_strictly_increasing':True,'strict_new_file_full_AV_decode_returncode':decode.returncode,'strict_new_file_full_AV_decode_stderr':decode.stderr,'new_full_AV_decode_runs':1,'old_input_full_decode_runs':0,'old_QA_repeated':False,'reencoded_video_frames':0,'new_TTS_calls':0,'human_full_1x':False,'continuous_clean':False,'human_signoff':False,'formal_dynamic_credit_added':0,'ABC_credit_added':0,'external_upload':False,'pending_review':pin(QA/'pending-review/PENDING-PACKAGE.actual.json'),'root_bytes_before_QA_receipt':total()}
 write('QA.actual.json',result)
 for ident,path,role in [('technical-qa-a01',ROOT/'QA.actual.json','technical-qa'),('bound-probe-a01',QA/'movie.bound-probe.json','bound-media-probe'),('pending-package-a01',QA/'pending-review/PENDING-PACKAGE.actual.json','pending-human-review'),('pending-template-a01',template,'pending-human-review'),('review-frame-plan-a01',QA/'REVIEW-FRAME-PLAN.actual.json','review-plan')]: preserve(ident,path,role)
 for frame in plan.frames: preserve('pending-'+frame.frame_id,frame.final_output,'pending-human-review')
 print(json.dumps({'qa':pin(ROOT/'QA.actual.json'),'movie':pin(MOVIE),'duration':meta['format']['duration'],'video_frames':len(videos),'max_video_pts_gap':max(vgaps),'max_audio_pts_gap':max(agaps),'root_bytes':total(),'frames':[{'id':f.frame_id,'path':str(f.final_output)} for f in plan.frames]},ensure_ascii=False),flush=True)

if __name__=='__main__':
 try: main()
 except Exception as exc:
  write('QA-FAILURE.actual.json',{'machine_id':MACHINE,'observed_at_utc':now().isoformat(),'error_type':type(exc).__name__,'error':str(exc),'all_attempt_material_retained':True,'root_bytes':total()})
  raise
