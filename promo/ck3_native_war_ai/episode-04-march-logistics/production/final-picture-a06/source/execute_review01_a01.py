"""Execute one Root-frozen Review01. All prior candidates and attempts remain."""
from pathlib import Path
import argparse,json,hashlib,subprocess,sys,datetime
R=Path(__file__).resolve().parent
PY=Path('D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe')
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def pin(p):
 p=Path(p);assert p.stat().st_size<8*1024*1024 and p.suffix in ('.json','.py','.md','.ass')
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def new(p,d):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
def run(label,argv):
 d=R/'execution-a01'/label;d.mkdir(parents=True,exist_ok=False)
 cmd=list(map(str,argv));start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 new(d/'argv.json',{'argv':cmd,'cwd':str(R),'start_utc':start})
 print(json.dumps({'stage':label,'state':'STARTED','argv':cmd}),flush=True)
 with (d/'stdout.txt').open('x',encoding='utf-8',newline='\n') as out,(d/'stderr.txt').open('x',encoding='utf-8',newline='\n') as err:
  p=subprocess.Popen(cmd,cwd=R,stdout=subprocess.PIPE,stderr=err,encoding='utf-8',errors='replace')
  for line in p.stdout:
   out.write(line);out.flush()
   if 'ACTUAL_NEW_PICTURE_RENDERED' in line:print(line.rstrip(),flush=True)
  rc=p.wait()
 new(d/'result.json',{'returncode':rc,'start_utc':start,'end_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'argv':cmd,'stdout':str(d/'stdout.txt'),'stderr':str(d/'stderr.txt')})
 print(json.dumps({'stage':label,'returncode':rc}),flush=True)
 if rc:raise SystemExit(rc)
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--gate',type=Path,required=True)
p.add_argument('--run',action='store_true')
a=p.parse_args();gate=read(a.gate)
assert gate['schema']=='xar.e04.final-story-review-freeze.v1' and gate['approved_for_review_render'] is True
assert gate['picture_rows_json']==pin(R/'actual-row-binding-a03/picture-rows.json')
assert gate['pipeline_source']==pin(R/'candidate-a04/bc_pipeline.py')
assert gate['human_signoff'] is False and gate['winner'] is None and gate['C_controlled_comparison']=='NOT_GRANTED'
pending=read(R/'actual-row-binding-a03/pipeline-input-PENDING-Root-review.json')
pending['final']['Root_final_story_freeze']=pin(a.gate)
target=R/'execution-a01/pipeline-input-Root-frozen.json'
if not a.run:
 print(json.dumps({'state':'READ_ONLY_EXECUTION_PLAN','actual_Root_gate':pin(a.gate),'input_future':str(target),'fresh_workdir':str(R/'actual-render-a01'),'candidate':pin(R/'candidate-a04/bc_pipeline.py'),'movie_name':'CK3-War-AI-Episode04-March-Logistics-Review01.mp4','media_operations':0},ensure_ascii=False,indent=2))
 raise SystemExit(0)
assert not target.parent.exists() and not (R/'actual-render-a01').exists() and not (R/'toolchain-run-a01').exists()
new(target,pending)
run('metadata-check',[PY,'-B','-X','utf8',R/'candidate-a04/checked_entry.py','check','--input',target])
run('formal-start-run',[PY,'-B','-X','utf8','-m','xar_promo','start-run',pending['final']['project_config']['path'],'--run-id','war-e04-final-BC-Review01-20261006-a01','--run-directory',R/'toolchain-run-a01'])
run('actual-render',[PY,'-B','-X','utf8',R/'candidate-a04/checked_entry.py','render','--input',target,'--workdir',R/'actual-render-a01'])
print(json.dumps({'state':'RENDER_RETURNED','movie_receipt':str(R/'actual-render-a01/picture-receipt.json'),'unique_bound_probe':str(R/'actual-render-a01/picture.bound-probe.json'),'human_signoff':False}),flush=True)
