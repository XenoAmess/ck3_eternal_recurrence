from __future__ import annotations
from dataclasses import replace
import datetime as dt
import json
from pathlib import Path
import shutil
import sys

from preflight import MACHINE,ROOT,pin,write
from assemble import MOVIE,RUN,CONFIG,total,validate,cli
from xar_promo import probe_and_write_bound_media
from xar_promo.process import CommandSpec,run_command

QA=ROOT/'qa-a01'

def call(label,argv):
 assert total()<234881024
 return run_command(CommandSpec.create(argv,label=label,cwd=ROOT),audit_directory=QA/'process'/label)

def main():
 sys.stdout.reconfigure(encoding='utf-8')
 assert not QA.exists()
 assembly=json.loads((ROOT/'ASSEMBLY.actual.json').read_bytes())
 assert pin(MOVIE)==assembly['movie']
 QA.mkdir()
 probe_and_write_bound_media(shutil.which('ffprobe'),MOVIE,output_path=QA/'movie.bound-probe.json',audit_directory=QA/'bound-probe-audit')
 meta=call('metadata-and-chapters',[shutil.which('ffprobe'),'-v','error','-show_streams','-show_format','-show_chapters','-of','json',str(MOVIE)])
 assert not meta.stderr
 parsed=json.loads(meta.stdout)
 video=next(r for r in parsed['streams'] if r['codec_type']=='video')
 audio=next(r for r in parsed['streams'] if r['codec_type']=='audio')
 assert video['codec_name']=='h264' and video['width']==1920 and video['height']==1080 and video['r_frame_rate']=='30/1'
 assert int(video['nb_frames'])==3899 and audio['codec_name']=='aac' and audio['sample_rate']=='48000' and audio['channels']==2
 assert len(parsed['chapters'])==4
 packets=call('packet-pts',[shutil.which('ffprobe'),'-v','error','-show_entries','packet=stream_index,pts_time,dts_time,duration_time','-of','json',str(MOVIE)])
 assert not packets.stderr
 data=json.loads(packets.stdout)['packets']
 videos=[p for p in data if p['stream_index']==video['index']]
 audios=[p for p in data if p['stream_index']==audio['index']]
 stamps=sorted(float(p['pts_time']) for p in videos)
 gaps=[b-a for a,b in zip(stamps,stamps[1:])]
 audio_pts=[float(p['pts_time']) for p in audios]
 agaps=[b-a for a,b in zip(audio_pts,audio_pts[1:])]
 assert len(videos)==3899 and min(gaps)>0 and max(gaps)<0.067
 assert min(agaps)>0 and max(agaps)<0.05
 for items in (videos,audios):
  dts=[float(p['dts_time']) for p in items]
  assert all(b>a for a,b in zip(dts,dts[1:]))
 decode=call('strict-full-AV-decode',[shutil.which('ffmpeg'),'-hide_banner','-nostdin','-v','error','-xerror','-threads','1','-filter_threads','1','-filter_complex_threads','1','-i',str(MOVIE),'-map','0:v:0','-map','0:a:0','-f','null','NUL'])
 assert decode.returncode==0 and not decode.stderr
 # Review accepts a deliberately small chapter timeline surface. Its chapter
 # ids are adapted explicitly from the retained general storyboard object.
 storyboard=json.loads((ROOT/'storyboard.actual.json').read_bytes())
 review_storyboard={'chapters':[{'id':c['chapter_id'],'start_seconds':c['start_seconds'],'end_seconds':min(float(c['end_seconds']),float(parsed['format']['duration']))} for c in storyboard['chapters']]}
 write('qa-a01/review-storyboard.actual.json',review_storyboard)
 args=[str(MOVIE),'--storyboard',str(QA/'review-storyboard.actual.json'),'--probe',str(QA/'movie.bound-probe.json'),'--output-directory',str(QA/'pending-review'),'--audit-directory',str(QA/'review-audit'),'--ffmpeg',shutil.which('ffmpeg')]
 cli('review-plan-only','review',*args,'--plan-only')
 assert not (QA/'pending-review').exists() and not (QA/'review-audit').exists()
 cli('pending-human-review','review',*args)
 result={'schema':'xar.e04.observations-130s-technical-qa.v1','machine_id':MACHINE,'observed_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
  'movie':pin(MOVIE),'bound_probe':pin(QA/'movie.bound-probe.json'),'metadata':parsed,
  'video_packets':len(videos),'video_first_pts':stamps[0],'video_last_pts':stamps[-1],'maximum_video_pts_gap_seconds':max(gaps),
  'audio_packets':len(audios),'maximum_audio_pts_gap_seconds':max(agaps),'video_and_audio_packet_dts_strictly_increasing':True,
  'strict_full_AV_decode_exit_code':decode.returncode,'strict_full_AV_decode_stderr':decode.stderr,
  'technical_status':'GREEN_AUTOMATED_PENDING_HUMAN_REVIEW','join_cadence_note':'Stream-copy keeps all input frames; AAC container tails introduce sub-frame join offsets. Nominal 30 fps, no new constant-frame-grid claim.',
  'new_full_decode_runs':1,'old_input_decode_runs':0,'old_input_QA_repeated':False,'reencoded_video_frames':0,
  'continuous_clean':False,'human_full_1x':False,'human_signoff':False,'formal_dynamic_credit_added':0,'ABC_credit_added':0,'external_upload':False,
  'pending_review_files':[pin(p) for p in (QA/'pending-review').rglob('*') if p.is_file()],'root_bytes_before_qa_receipt':total()}
 write('QA.actual.json',result)
 for ident,path,role in [('technical-qa-a01',ROOT/'QA.actual.json','technical-qa'),('bound-probe-a01',QA/'movie.bound-probe.json','bound-media-probe'),('review-storyboard-a01',QA/'review-storyboard.actual.json','storyboard')]:
  cli('preserve-'+ident,'preserve',path,'--run-manifest',RUN,'--artifact-id',ident,'--collection','derived','--role',role)
  validate('after-'+ident)
 for index,path in enumerate(sorted((QA/'pending-review').rglob('*'))):
  if path.is_file():
   ident='pending-review-'+str(index)
   cli('preserve-'+ident,'preserve',path,'--run-manifest',RUN,'--artifact-id',ident,'--collection','derived','--role','pending-human-review')
   validate('after-'+ident)
 print(json.dumps({'qa':pin(ROOT/'QA.actual.json'),'movie':pin(MOVIE),'duration':parsed['format']['duration'],'frames':len(videos),'max_video_pts_gap':max(gaps),'max_audio_pts_gap':max(agaps),'root_bytes':total()},ensure_ascii=False))

if __name__=='__main__':
 try: main()
 except Exception as exc:
  write('QA-FAILURE.actual.json',{'machine_id':MACHINE,'observed_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'error_type':type(exc).__name__,'error':str(exc),'all_attempt_material_preserved':True})
  raise
