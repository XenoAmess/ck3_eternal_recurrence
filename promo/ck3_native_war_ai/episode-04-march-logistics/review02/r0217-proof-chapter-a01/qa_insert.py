import json
from pathlib import Path
import sys
sys.dont_write_bytecode=True
from context import *
from render_insert import MOVIE,MANIFEST

def main():
 sys.stdout.reconfigure(encoding='utf-8')
 admitted(); assert not (ROOT/'QA.actual.json').exists()
 encoded=json.loads((ROOT/'ENCODE.actual.json').read_bytes()); assert pin(MOVIE)==encoded['movie']
 meta=process('new-movie-metadata',[FFPROBE,'-v','error','-show_entries','stream=index,codec_name,codec_type,width,height,pix_fmt,r_frame_rate,avg_frame_rate,time_base,duration,start_time,nb_frames,sample_rate,channels:format=duration,size','-of','json',str(MOVIE)])
 assert not meta.stderr
 metadata=json.loads(meta.stdout); video=next(s for s in metadata['streams'] if s['codec_type']=='video'); audio=next(s for s in metadata['streams'] if s['codec_type']=='audio')
 assert video['codec_name']=='h264' and [video['width'],video['height']]==[1920,1080] and video['r_frame_rate']=='30/1' and int(video['nb_frames'])==1080
 assert audio['codec_name']=='aac' and audio['sample_rate']=='48000' and audio['channels']==2
 assert abs(float(metadata['format']['duration'])-36)<0.06
 argv=[FFPROBE,'-v','error','-show_entries','packet=stream_index,pts_time,dts_time','-of','compact=p=0:nk=0',str(MOVIE)]
 guard(); p=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',errors='replace',creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 try: psutil.Process(p.pid).nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
 except psutil.NoSuchProcess: pass
 groups={video['index']:[],audio['index']:[]}
 for line in p.stdout:
  values=dict(v.split('=',1) for v in line.strip().split('|') if '=' in v)
  if 'stream_index' not in values: continue
  index=int(values['stream_index'])
  if index in groups: groups[index].append((float(values['pts_time']),float(values['dts_time'])))
 stderr=p.stderr.read(); rc=p.wait(timeout=30); assert rc==0 and not stderr
 summaries={}
 for index,values in groups.items():
  pts=sorted(v[0] for v in values); dts=[v[1] for v in values]
  gaps=[b-a for a,b in zip(pts,pts[1:])]
  assert min(gaps)>0 and max(gaps)<0.04 and all(b>a for a,b in zip(dts,dts[1:]))
  summaries[str(index)]={'packets':len(values),'first_display_pts':pts[0],'last_display_pts':pts[-1],'max_display_pts_gap':max(gaps),'DTS_strictly_increasing':True,'display_PTS_unique':True}
 assert summaries[str(video['index'])]['packets']==1080
 write('new-movie-PTS.actual.json',{'machine_id':MACHINE,'observed_at_utc':now().isoformat(),'argv':argv,'returncode':rc,'stderr':stderr,'stream_summaries':summaries,'full_packet_dump_written':False})
 decoded=process('new-movie-strict-full-AV-decode',[FFMPEG,'-hide_banner','-nostdin','-v','error','-xerror','-threads','1','-filter_threads','1','-filter_complex_threads','1','-i',str(MOVIE),'-map','0:v:0','-map','0:a:0','-progress','pipe:1','-nostats','-f','null','NUL'])
 assert not decoded.stderr
 final={}
 for line in decoded.stdout.splitlines():
  if '=' in line:
   k,v=line.split('=',1); final[k]=v
 assert final.get('progress')=='end' and int(final['frame'])==1080
 choice=json.loads((ROOT/'ROOT-WINDOW-CHOICE.actual.json').read_bytes())
 frames=[]
 for label,seconds in [('caption-1-before',1.),('caption-2-boundary',7.6),('caption-3-boundary',15.1),('caption-4-boundary',22.6),('end-card',34.)]:
  path=ROOT/'movie-samples'/f'{label}.jpg'; path.parent.mkdir(exist_ok=True)
  result=process('new-movie-frame-'+label,[FFMPEG,'-hide_banner','-nostdin','-v','error','-threads','1','-ss',str(seconds),'-i',str(MOVIE),'-frames:v','1','-q:v','12','-n',str(path)])
  assert not result.stderr
  frames.append({'label':label,'requested_seconds':seconds,'image':pin(path),'Root_direct_view_pending':True})
 own=[]
 for p in psutil.process_iter(['name','cmdline']):
  try:
   if (p.info['name'] or '').lower()=='ffmpeg.exe' and any(str(ROOT).lower() in v.lower() for v in p.info['cmdline'] or []): own.append(p.pid)
  except (psutil.NoSuchProcess,psutil.AccessDenied): pass
 assert not own
 result={'schema':'xar.e04.r0217-proof-review-technical-QA.v1','machine_id':MACHINE,'observed_at_utc':now().isoformat(),'run_id':RUN_ID,'status':'NEW_BYTES_TECHNICAL_QA_PASS_PENDING_ROOT_IMAGES_AND_HUMAN_REVIEW','movie':pin(MOVIE),'metadata':metadata,'PTS_summary':summaries,'strict_new_movie_AV_decode_exit_code':decoded.returncode,'strict_new_movie_AV_decode_stderr':decoded.stderr,'strict_new_movie_AV_decode_count':1,'decoded_frames':1080,'sample_frames':frames,'raw_QA_repeated':False,'old_movie_QA_repeated':False,'new_TTS_calls':0,'other_run_footage_used':False,'county_total_debit':None,'R04_entire_card_closed':False,'formal_dynamic_credit_added':0,'continuous_clean':False,'human_full_1x':False,'human_signoff':False,'Root_direct_new_movie_frames_reviewed':False,'owned_FFmpeg_at_close':own,'usage_before_QA_receipt':usage(),'D_heavy_write_bytes':0,'external_upload':False}
 write('QA.actual.json',result)
 cli('preserve-QA','preserve',ROOT/'QA.actual.json','--run-manifest',MANIFEST,'--artifact-id','r0217-proof-QA-a01','--collection','derived','--role','technical-qa')
 cli('final-config-validate','validate',ROOT/'project/promo-project.json','--json')
 cli('final-run-validate','validate',MANIFEST,'--json')
 print(json.dumps({'movie':pin(MOVIE),'QA':pin(ROOT/'QA.actual.json'),'samples':frames,'usage':usage()},ensure_ascii=False))

if __name__=='__main__':
 try: main()
 except Exception as exc:
  write('QA-FAILURE.actual.json',{'machine_id':MACHINE,'observed_at_utc':now().isoformat(),'error_type':type(exc).__name__,'error':str(exc),'usage':usage(),'all_attempt_material_retained':True})
  raise
