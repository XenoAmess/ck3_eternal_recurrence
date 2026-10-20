from __future__ import annotations
import datetime as dt
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys
sys.dont_write_bytecode=True

ROOT=Path(__file__).resolve().parent
REPO=Path('D:/workspace/ck3_eternal_recurrence')
MACHINE='desktop-3fevhd2-1c74096080'
TASK='e04-full-review-media-20261020-a01'
SOURCES=[
 ('historical-method69','D:/workspace/ck3_native_war_ai_promo_work/e04-review02-full69-typo-repair-a02/runs/review02-full69-typography-a02/artifacts/derived/sha256/8F/8F7496F357B392504EE18C842B7A6B29F31EAE81E8475FF8EC7C31AD3BED946B.mp4',89450267,'8f7496f357b392504ee18c842b7a6b29f31eae81e8475ff8ec7c31ad3bed946b',58406),
 ('later-evidence-appendix','C:/ck3-e04-resume-20261020-a01/media/work-a01/E04-ARMY-OBSERVATIONS-130s-REVIEW-DRAFT-a01.mp4',12222689,'74480cf62a07bcf18fc86c16a0ccc6a7554b4a835c179c4b4d68c405143b0d00',3899),
]

def now(): return dt.datetime.now(dt.timezone.utc)
def pin(p):
 p=Path(p)
 with p.open('rb') as stream: digest=hashlib.file_digest(stream,'sha256').hexdigest()
 return {'path':str(p),'bytes':p.stat().st_size,'sha256':digest}
def write(name,data):
 p=ROOT/name; p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8',newline='\n') as stream: json.dump(data,stream,ensure_ascii=False,indent=2); stream.write('\n')
def run(argv):
 p=subprocess.run([str(a) for a in argv],capture_output=True,text=True,encoding='utf-8',errors='replace',cwd=ROOT)
 if p.returncode: raise RuntimeError(json.dumps({'argv':[str(a) for a in argv],'rc':p.returncode,'stderr':p.stderr}))
 return p.stdout

def main():
 sys.stdout.reconfigure(encoding='utf-8')
 cli='D:/workspace/.codex-task-bus/bin/codex_task_bus.py'
 bus=json.loads(run([sys.executable,'-X','utf8',cli,'poll','--task',TASK,'--ack','--limit','10000']))
 tasks=json.loads(run([sys.executable,'-X','utf8',cli,'list']))
 write('TASKBUS-INTAKE.actual.json',{'machine_id':MACHINE,'observed_at_utc':now().isoformat(),'ack':bus.get('acknowledged_cursor'),'current_events':bus.get('events',[]),'current_tasks':[t for t in tasks.get('tasks',[]) if not t.get('stale') and t.get('state')!='done']})
 release=json.loads(run(['gh','api','repos/XenoAmess/xar_promo_toolchain/releases/latest']))
 asset=next(a for a in release['assets'] if a['name'].endswith('.whl'))
 dist=metadata.distribution('xar-promo-toolchain'); direct=json.loads((Path(dist._path)/'direct_url.json').read_text(encoding='utf-8'))
 assert not release['draft'] and not release['prerelease'] and dist.version==release['tag_name'].removeprefix('v')=='0.3.0'
 assert direct['url']==asset['browser_download_url'] and direct['archive_info']['hash']==asset['digest'].replace(':','=')
 sources=[]
 for identifier,path,size,sha,frames in SOURCES:
  p=Path(path); assert p.is_file() and p.stat().st_size==size
  # The exact keeper was freshly hash-verified by capacity in this same work
  # session. Do not reread the 89 MB body before heavy admission merely to
  # repeat that identity check; the corresponding receipt is explicitly bound.
  probe=json.loads(run([shutil.which('ffprobe'),'-v','error','-show_streams','-show_format','-show_data_hash','sha256','-of','json',p]))
  sources.append({'id':identifier,'file':{'path':str(p),'bytes':size,'sha256':sha},'expected_frames_from_existing_QA':frames,'fresh_stat':{'size':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns},'probe':probe})
 result={'schema':'xar.e04.full-review-intake.v1','machine_id':MACHINE,'observed_at_utc':now().isoformat(),'source_commit':run(['git','-C',REPO,'rev-parse','HEAD']).strip(),
  'official_release':{'query_argv':['gh','api','repos/XenoAmess/xar_promo_toolchain/releases/latest'],'tag':release['tag_name'],'release_id':release['id'],'url':release['html_url'],'wheel_url':asset['browser_download_url'],'wheel_digest':asset['digest']},
  'interpreter':{'path':sys.executable,'version':sys.version,'installed_version':dist.version,'direct_url':direct},
  'skill':pin('D:/workspace/xar_promo_toolchain/codex-skill/promo-video-pipeline/SKILL.md'),
  'source_CAS_retirement_receipt':pin('C:/ck3-e04-resume-20261020-a01/capacity/D-TWO-WORK-MOVIES-RETIREMENT.actual.json'),
  'appendix_delivery':pin('C:/ck3-e04-resume-20261020-a01/media/DELIVERY.actual.json'),
  'input_identity_reused_from_same_session_exact_receipts':True,'sources':sources,
  'semantics':{'first_part':'Historical method review; its pending-shot assertions describe that source attempt','second_part':'Later four-insert review appendix across separate replays','causal_unification':False,'formal_movie_claim':False,'old_source_QA_repeated':False},
  'expected_frames':sum(r[4] for r in SOURCES),'estimated_video_seconds':sum(r[4] for r in SOURCES)/30,
  'estimated_final_bytes':sum(r[2] for r in SOURCES),'estimated_peak_bytes':234881024,'requested_ceiling_bytes':268435456,'C_volume':dict(zip(('total','used','free'),shutil.disk_usage('C:/'))),
  'cli':{str(args):run([sys.executable,'-m','xar_promo',*args]) for args in [ ['--version'],['--help'],['start-run','--help'],['preserve','--help'],['review','--help'] ]}}
 write('INTAKE.actual.json',result)
 print(json.dumps({'intake':pin(ROOT/'INTAKE.actual.json'),'estimated_frames':result['expected_frames'],'estimated_seconds':result['estimated_video_seconds'],'source_streams':[{'id':row['id'],'streams':[{k:s.get(k) for k in ['codec_name','codec_type','profile','level','width','height','pix_fmt','sample_rate','channels','time_base','r_frame_rate','avg_frame_rate','start_time','duration','nb_frames','extradata_hash']} for s in row['probe']['streams']]} for row in sources]},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
