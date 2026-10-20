"""Join four already-rendered E04 review clips without re-encoding their streams.

The installed public render API produces this external material. The native CLI
then preserves it with its exact recipe; no pipeline build or human signoff is
claimed. Input decoding is intentionally not repeated.
"""
from __future__ import annotations
from dataclasses import replace
import datetime as dt
import json
from pathlib import Path
import shutil
import subprocess
import sys

from preflight import MACHINE, ROOT, pin, run, write
from xar_promo.process import run_command
from xar_promo.render import execute_render_plan, plan_concat
from xar_promo.model import ProjectConfig
from xar_promo.storyboard import plan_storyboard, TimelineSpacing

CONFIG=ROOT/'project/promo-project.json'
RUN=ROOT/'run-a01/run-manifest.json'
WORK=ROOT/'work-a01'
MOVIE=WORK/'E04-ARMY-OBSERVATIONS-130s-REVIEW-DRAFT-a01.mp4'
HARD=268435456
SOFT=234881024
TITLES=[
 ('分兵、合军与登船：独立回放','Split, merge and embarkation: separate replays'),
 ('受控零库存：337与另外67分列','Controlled zero stock: 337 and another 67 separated'),
 ('月界净增10人：物理闭包未完','Month boundary: net ten, physical closure incomplete'),
 ('县边到站与净减少：损失来源待验','County arrival and net loss: attribution unresolved'),
]

def now(): return dt.datetime.now(dt.timezone.utc)

def total(): return sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())

def cli(label,*args):
 result=run([sys.executable,'-m','xar_promo',*map(str,args)])
 write('commands/'+label+'.actual.json',{'machine_id':MACHINE,'observed_at_utc':now().isoformat(),'argv':[sys.executable,'-m','xar_promo',*map(str,args)],'returncode':0,'stdout':result})
 return result

def validate(label):
 cli(label+'-config-validate','validate',CONFIG,'--json')
 cli(label+'-run-validate','validate',RUN,'--json')

def main():
 sys.stdout.reconfigure(encoding='utf-8')
 admission_path=Path(sys.argv[1]); expected_admission_sha=sys.argv[2]
 admission=pin(admission_path); assert admission['sha256']==expected_admission_sha
 intake=json.loads((ROOT/'INTAKE.actual.json').read_bytes())
 assert intake['machine_id']==MACHINE
 assert not WORK.exists() and not CONFIG.exists() and not RUN.exists()
 assert now()<dt.datetime(2026,10,20,8,tzinfo=dt.timezone.utc)
 assert total()<1048576
 rows=intake['inputs']
 assert sum(r['file']['bytes'] for r in rows)<16*1024*1024
 # Identity and completed-input hashes were verified in this task's intake.
 # The unchanged files are checked by size/mtime while the read-only concat runs.
 stats=[]
 for row in rows:
  p=Path(row['file']['path']); st=p.stat()
  assert st.st_size==row['file']['bytes']
  stats.append((str(p),st.st_size,st.st_mtime_ns))
 config={'format_version':1,'kind':'xar_promo_project_config',
  'project':{'id':'ck3-war-ai-e04-observations-130s-review-a01','title':'军队人数变化：四段独立实录审阅章'},
  'pipeline':{'adapter':'generic','preset':'default'},
  'locales':{'narration':'zh-CN','subtitles':['zh-CN','en']},
  'constraints':{'duration_limit_seconds':2400},
  'chapters':[{'id':row['id'],'type':'documentary','state':'planned','title':{'zh-CN':title[0],'en':title[1]},'cues':[{'id':row['id'],'narration':{'zh-CN':title[0]},'subtitles':{'zh-CN':title[0],'en':title[1]}}]} for row,title in zip(rows,TITLES)]}
 CONFIG.parent.mkdir()
 with CONFIG.open('x',encoding='utf-8',newline='\n') as stream: json.dump(config,stream,ensure_ascii=False,indent=2); stream.write('\n')
 durations={r['id']:r['probe']['format']['duration'] for r in rows}
 timeline=plan_storyboard(ProjectConfig.from_mapping(config),narration_duration_resolver=None,
  draft_estimator=lambda p,c,q:durations[q.cue_id],spacing=TimelineSpacing(cue_gap_seconds=0,chapter_gap_seconds=0),validate_only=True)
 write('storyboard.actual.json',timeline.to_dict())
 cli('01-config-validate','validate',CONFIG,'--json')
 cli('02-start-run','start-run',CONFIG,'--run-id','e04-observations-130s-a01','--run-directory',RUN.parent)
 validate('03-started')
 WORK.mkdir()
 meta=[';FFMETADATA1','title=军队人数变化：四段独立实录审阅章','comment=Review draft. Separate replays. No human signoff.']
 for chapter,title in zip(timeline.chapters,TITLES):
  meta.extend(('[CHAPTER]','TIMEBASE=1/1000000',f'START={round(chapter.start_seconds*1000000)}',f'END={round(chapter.end_seconds*1000000)}','title='+title[0]))
 with (WORK/'chapters.ffmetadata').open('x',encoding='utf-8',newline='\n') as stream: stream.write('\n'.join(meta)+'\n')
 plan=plan_concat(ffmpeg=shutil.which('ffmpeg'),segment_paths=tuple(Path(r['file']['path']) for r in rows),concat_path=WORK/'sources.ffconcat',partial_output=WORK/'chapter.partial.mp4',final_output=MOVIE,audit_directory=WORK/'audit',working_directory=WORK)
 command=plan.commands[0]; argv=list(command.spec.argv)
 # The concat demuxer keeps packet content; automatic H.264 Annex-B handling
 # carries the input SPS at a clip boundary without decoding/re-encoding.
 output_index=len(argv)-1
 argv[output_index:output_index]=['-map','0:v:0','-map','0:a:0','-map_chapters','1','-map_metadata','1']
 input_index=argv.index('-c')
 argv[input_index:input_index]=['-i',str(WORK/'chapters.ffmetadata')]
 argv[1:1]=['-threads','1']
 plan=replace(plan,commands=(replace(command,spec=replace(command.spec,argv=tuple(argv))),))
 write('PLAN.actual.json',{'machine_id':MACHINE,'observed_at_utc':now().isoformat(),'mode':'installed plan_concat/execute_render_plan external-material route; CLI native preserve follows','admission':admission,'intake':pin(ROOT/'INTAKE.actual.json'),'implementation':pin(Path(__file__)),'argv':argv,'generated_files':[{'path':str(g.path),'content':g.content} for g in plan.generated_files],'output':str(MOVIE),'input_stat_guards':stats,'reencoding':False,'full_native_build_claimed':False,'maximum_concurrent_ffmpeg_jobs':1})
 def guarded_process(argv,**kwargs):
  assert total()<SOFT and now()<dt.datetime(2026,10,20,8,tzinfo=dt.timezone.utc)
  # The formal admission owns the common-volume floor; local enforcement limits
  # this admitted root and this one bounded, small stream-copy process.
  kwargs.pop('check',None)
  result=subprocess.run(argv,timeout=120,**kwargs)
  assert total()<HARD
  return result
 def runner(spec,*,audit_directory): return run_command(spec,audit_directory=audit_directory,run=guarded_process)
 execute_render_plan(plan,command_runner=runner)
 for path,size,mtime in stats:
  st=Path(path).stat(); assert (st.st_size,st.st_mtime_ns)==(size,mtime)
 result={'schema':'xar.e04.observations-130s-assembly.v1','machine_id':MACHINE,'observed_at_utc':now().isoformat(),'movie':pin(MOVIE),'admission':admission,'intake':pin(ROOT/'INTAKE.actual.json'),'plan':pin(ROOT/'PLAN.actual.json'),'storyboard':pin(ROOT/'storyboard.actual.json'),'status':'STREAMCOPY_ASSEMBLED_PENDING_NEW_BYTES_QA','reencoded_video_frames':0,'new_TTS_calls':0,'old_input_bytes_changed':False,'old_input_QA_repeated':False,'human_1x':False,'human_signoff':False,'continuous_clean':False,'formal_dynamic_credit_added':0,'upload_performed':False,'root_bytes':total()}
 write('ASSEMBLY.actual.json',result)
 for ident,path,role in [('chapter-deliverable-a01',MOVIE,'deliverable'),('source-intake-a01',ROOT/'INTAKE.actual.json','source-index'),('assembly-recipe-a01',ROOT/'PLAN.actual.json','render-plan'),('assembly-result-a01',ROOT/'ASSEMBLY.actual.json','assembly-result'),('storyboard-a01',ROOT/'storyboard.actual.json','storyboard'),('assembly-implementation-a01',Path(__file__),'implementation')]:
  cli('preserve-'+ident,'preserve',path,'--run-manifest',RUN,'--artifact-id',ident,'--collection','derived','--role',role)
  validate('after-'+ident)
 print(json.dumps({'movie':result['movie'],'native_manifest':str(RUN),'root_bytes':total(),'status':result['status']},ensure_ascii=False))

if __name__=='__main__': main()
