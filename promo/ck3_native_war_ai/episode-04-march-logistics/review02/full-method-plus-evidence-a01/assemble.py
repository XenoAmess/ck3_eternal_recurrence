"""External stream-copy assembly through the installed public rendering API."""
from __future__ import annotations
from dataclasses import replace
import datetime as dt
import json
from pathlib import Path
import shutil
import subprocess
import sys
sys.dont_write_bytecode=True
import psutil
from intake import ROOT,REPO,MACHINE,TASK,now,pin,write,run
from xar_promo.process import run_command
from xar_promo.render import execute_render_plan,plan_concat

CONFIG=ROOT/'project/promo-project.json'
MANIFEST=ROOT/'run-a01/run-manifest.json'
WORK=ROOT/'work-a01'
MOVIE=WORK/'E04-METHOD69-PLUS-INDEPENDENT-EVIDENCE-34m37s-REVIEW-a01.mp4'
HARD=268435456
SOFT=251658240
DEADLINE=dt.datetime(2026,10,20,8,tzinfo=dt.timezone.utc)

def total(): return sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())
def cli(label,*args):
 argv=[sys.executable,'-m','xar_promo',*map(str,args)]
 stdout=run(argv)
 write('commands/'+label+'.actual.json',{'machine_id':MACHINE,'observed_at_utc':now().isoformat(),'argv':argv,'returncode':0,'stdout':stdout})
 return stdout
def validate(label):
 cli(label+'-config-validate','validate',CONFIG,'--json')
 cli(label+'-run-validate','validate',MANIFEST,'--json')
def preserve(ident,path,role):
 cli('preserve-'+ident,'preserve',path,'--run-manifest',MANIFEST,'--artifact-id',ident,'--collection','derived','--role',role)
 validate('after-'+ident)
def guarded_process(argv,**kwargs):
 assert total()<SOFT and now()<DEADLINE
 kwargs.pop('check',None)
 process=subprocess.Popen(argv,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),**kwargs)
 psutil.Process(process.pid).nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
 try:
  stdout,stderr=process.communicate(timeout=600)
 except subprocess.TimeoutExpired:
  process.terminate(); stdout,stderr=process.communicate(timeout=10); raise
 assert total()<HARD
 return subprocess.CompletedProcess(argv,process.returncode,stdout,stderr)
def runner(spec,*,audit_directory): return run_command(spec,audit_directory=audit_directory,run=guarded_process)

def main():
 sys.stdout.reconfigure(encoding='utf-8')
 admission_path=Path(sys.argv[1]); expected_sha=sys.argv[2]
 admission=pin(admission_path); assert admission['sha256']==expected_sha
 cap=json.loads(admission_path.read_bytes()); intake=json.loads((ROOT/'INTAKE.actual.json').read_bytes())
 assert cap['machine_id']==intake['machine_id']==MACHINE
 assert not WORK.exists() and not CONFIG.exists() and not MANIFEST.exists() and now()<DEADLINE
 sources=intake['sources']
 for source in sources:
  st=Path(source['file']['path']).stat(); assert st.st_size==source['fresh_stat']['size'] and st.st_mtime_ns==source['fresh_stat']['mtime_ns']
 assert total()<1048576
 config={'format_version':1,'kind':'xar_promo_project_config',
  'project':{'id':'ck3-war-ai-e04-full-method-plus-evidence-review-a01','title':'战争四期：原方法版与独立实录补充审阅电影'},
  'pipeline':{'adapter':'generic','preset':'default'},'locales':{'narration':'zh-CN','subtitles':['zh-CN','en']},'constraints':{'duration_limit_seconds':2400},
  'chapters':[{'id':row['id'],'type':'documentary','state':'planned','title':{'zh-CN':title},'cues':[{'id':row['id'],'narration':{'zh-CN':title},'subtitles':{'zh-CN':title,'en':english}}]} for row,title,english in zip(sources,['原方法审阅版：其状态属于历史录制','后续独立实录补充章：四段独立回放'],['Historical method review: source-attempt status','Later independent evidence appendix: separate replays'])]}
 write('project/promo-project.json',config)
 cli('01-config-validate','validate',CONFIG,'--json')
 cli('02-start-run','start-run',CONFIG,'--run-id','e04-full-method-plus-evidence-review-a01','--run-directory',MANIFEST.parent)
 validate('03-started')
 method_seconds=float(sources[0]['probe']['format']['duration'])
 appendix_seconds=float(sources[1]['probe']['format']['duration'])
 appendix_story=json.loads(Path('C:/ck3-e04-resume-20261020-a01/media/storyboard.actual.json').read_bytes())
 chapters=[{'id':'historical-method69','start_seconds':0.,'end_seconds':method_seconds,'title':'第一部分／原方法审阅版（历史状态）'}]
 for row,title in zip(appendix_story['chapters'],['实录补充／分兵合军与登船（独立回放）','实录补充／受控零库存（供给337另67）','实录补充／月界净增10（闭包未完）','实录补充／县边净减236（归因待验）']):
  chapters.append({'id':row['chapter_id'],'start_seconds':method_seconds+float(row['start_seconds']),'end_seconds':method_seconds+float(row['end_seconds']),'title':title})
 write('storyboard.actual.json',{'machine_id':MACHINE,'observed_at_utc':now().isoformat(),'main_parts':[{'id':'historical-method69','start_seconds':0.,'end_seconds':method_seconds},{'id':'later-evidence-appendix','start_seconds':method_seconds,'end_seconds':method_seconds+appendix_seconds}],'chapters':chapters,'causal_unification':False})
 WORK.mkdir()
 meta=[';FFMETADATA1','title=战争四期：原方法版＋独立实录补充（审阅）','comment=Historical method review followed by a later independent evidence appendix. No human signoff.']
 for chapter in chapters:
  meta.extend(('[CHAPTER]','TIMEBASE=1/1000000',f'START={round(chapter["start_seconds"]*1000000)}',f'END={round(chapter["end_seconds"]*1000000)}','title='+chapter['title']))
 with (WORK/'chapters.ffmetadata').open('x',encoding='utf-8',newline='\n') as stream: stream.write('\n'.join(meta)+'\n')
 plan=plan_concat(ffmpeg=shutil.which('ffmpeg'),segment_paths=tuple(Path(row['file']['path']) for row in sources),concat_path=WORK/'sources.ffconcat',partial_output=WORK/'movie.partial.mp4',final_output=MOVIE,audit_directory=WORK/'audit',working_directory=WORK)
 command=plan.commands[0]; argv=list(command.spec.argv)
 i=argv.index('-c'); argv[i:i]=['-i',str(WORK/'chapters.ffmetadata')]
 argv[-1:-1]=['-map','0:v:0','-map','0:a:0','-map_chapters','1','-map_metadata','1']
 argv[1:1]=['-threads','1']
 plan=replace(plan,commands=(replace(command,spec=replace(command.spec,argv=tuple(argv))),))
 write('PLAN.actual.json',{'schema':'xar.e04.full-review-plan.v1','machine_id':MACHINE,'observed_at_utc':now().isoformat(),'admission':admission,'intake':pin(ROOT/'INTAKE.actual.json'),'implementation':pin(Path(__file__)),'mode':'public plan_concat/execute_render_plan external material followed by native CLI preserve','argv':argv,'generated_files':[{'path':str(g.path),'content':g.content} for g in plan.generated_files],'reencoding':False,'new_TTS':False,'expected_frames':62305,'estimated_container_seconds':method_seconds+appendix_seconds,'nominal_fps':30,'historical_method_status_is_not_rewritten':True,'four_appendix_replays_are_not_one_causal_run':True})
 execute_render_plan(plan,command_runner=runner)
 for source in sources:
  st=Path(source['file']['path']).stat(); assert st.st_size==source['fresh_stat']['size'] and st.st_mtime_ns==source['fresh_stat']['mtime_ns']
 result={'schema':'xar.e04.full-review-assembly.v1','machine_id':MACHINE,'observed_at_utc':now().isoformat(),'movie':pin(MOVIE),'admission':admission,'input_index':pin(ROOT/'INTAKE.actual.json'),'plan':pin(ROOT/'PLAN.actual.json'),'status':'ASSEMBLED_STREAM_COPY_PENDING_NEW_BYTES_QA','full_native_build_executed':False,'reencoded_video_frames':0,'new_TTS_calls':0,'old_input_QA_repeated':False,'formal_dynamic_credit_added':0,'human_1x':False,'human_signoff':False,'uploaded':False,'root_bytes':total()}
 write('ASSEMBLY.actual.json',result)
 for ident,path,role in [('full-review-deliverable-a01',MOVIE,'deliverable'),('intake-a01',ROOT/'INTAKE.actual.json','source-index'),('plan-a01',ROOT/'PLAN.actual.json','render-plan'),('assembly-a01',ROOT/'ASSEMBLY.actual.json','assembly-result'),('storyboard-a01',ROOT/'storyboard.actual.json','storyboard'),('implementation-a01',Path(__file__),'implementation')]: preserve(ident,path,role)
 print(json.dumps({'movie':result['movie'],'manifest':str(MANIFEST),'root_bytes':total(),'status':result['status']},ensure_ascii=False))

if __name__=='__main__': main()
