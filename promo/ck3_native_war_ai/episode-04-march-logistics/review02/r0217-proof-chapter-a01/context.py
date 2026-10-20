from __future__ import annotations
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys
sys.dont_write_bytecode=True
import psutil

ROOT=Path(__file__).resolve().parent
REPO=Path('D:/workspace/ck3_eternal_recurrence')
CAP=Path('C:/ck3-e04-resume-20261020-a01/capacity/R0217-PROOF-CHAPTER-C-ADMISSION.actual-a01.json')
CAP_SHA='684f1335ab366436f2c298cd889962648428b52fc7850ec36192890d16c1df2d'
MACHINE='desktop-3fevhd2-1c74096080'
RUN_ID='desktop-3fevhd2-1c74096080--vanilla--R0217'
TASK='e04-r0217-proof-chapter-20261020-a01'
CONFIG=Path('C:/ck3-e04-resume-20261020-a01/window-preparation/r0217-take01/take01-input.actual.json')
RAW=Path('C:/ck3-e04-resume-20261020-a01/r221-scene-a01/raw-a01/take01/raw.mkv')
MUSIC=REPO/'promo/ck3_native_war_ai/assets/music/quiet-courtly-tension.wav'
DEADLINE=dt.datetime(2026,10,20,6,30,tzinfo=dt.timezone.utc)
FFMPEG=json.loads(CONFIG.read_bytes())['ffmpeg']['path']
FFPROBE=str(Path(FFMPEG).with_name('ffprobe.exe'))

def now(): return dt.datetime.now(dt.timezone.utc)
def pin(path):
 path=Path(path)
 with path.open('rb') as f: sha=hashlib.file_digest(f,'sha256').hexdigest()
 return {'path':str(path),'bytes':path.stat().st_size,'sha256':sha}
def usage():
 files=[p for p in ROOT.rglob('*') if p.is_file()]
 return {'aggregate_bytes':sum(p.stat().st_size for p in files),'JPEG_bytes':sum(p.stat().st_size for p in files if p.suffix.lower() in ['.jpg','.jpeg']),'metadata_bytes':sum(p.stat().st_size for p in files if p.suffix.lower() not in ['.jpg','.jpeg','.mp4','.mkv','.wav','.mp3','.png'])}
def guard():
 value=usage(); assert now()<DEADLINE and value['aggregate_bytes']<134217728 and value['JPEG_bytes']<=1048576 and value['metadata_bytes']<=262144,value
def write(name,data):
 path=ROOT/name; path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('x',encoding='utf-8',newline='\n') as f: json.dump(data,f,ensure_ascii=False,indent=2); f.write('\n')
 guard()
def run(argv):
 p=subprocess.run([str(v) for v in argv],capture_output=True,text=True,encoding='utf-8',errors='replace',cwd=ROOT)
 if p.returncode: raise RuntimeError((p.returncode,p.stderr))
 return p.stdout
def identity(path):
 st=Path(path).stat(); return {'bytes':st.st_size,'mtime_ns':st.st_mtime_ns,'st_dev':st.st_dev,'st_ino':st.st_ino}
def admitted():
 assert pin(CAP)['sha256']==CAP_SHA
 data=json.loads(CAP.read_bytes())
 assert data['machine_id']==MACHINE and data['run_id']==RUN_ID and Path(data['aggregate_root']).resolve()==ROOT and data['admitted']
 assert identity(RAW)==data['input_raw_fresh_identity']
 guard(); return data
def guarded_run(argv,**kwargs):
 guard(); kwargs.pop('check',None)
 p=subprocess.Popen(argv,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),**kwargs)
 try: psutil.Process(p.pid).nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
 except psutil.NoSuchProcess: pass
 stdout,stderr=p.communicate(timeout=600)
 guard(); return subprocess.CompletedProcess(argv,p.returncode,stdout,stderr)
def process(name,argv):
 from xar_promo.process import CommandSpec,run_command
 return run_command(CommandSpec.create(argv,label=name,cwd=ROOT),audit_directory=ROOT/'commands'/name,run=guarded_run)
def cli(name,*args):
 stdout=run([sys.executable,'-m','xar_promo',*map(str,args)])
 write('cli-'+name+'.json',{'machine_id':MACHINE,'observed_at_utc':now().isoformat(),'argv':[sys.executable,'-m','xar_promo',*map(str,args)],'returncode':0,'stdout':stdout})
 return stdout
