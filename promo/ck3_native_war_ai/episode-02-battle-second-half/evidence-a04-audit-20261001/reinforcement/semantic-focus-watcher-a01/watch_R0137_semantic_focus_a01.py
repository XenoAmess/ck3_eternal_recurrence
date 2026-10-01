"""Root-owned one-shot HWND focus routing; never creates a manual UI review."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys,time,subprocess,psutil,win32gui,win32process
ROOT=Path(__file__).resolve().parent
BASE=Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001')
CTL=BASE/'reinforcement-attempt-35-semantic-focus-watched-sdk/paused-pair-controller'
CONFIG=BASE/'reinforcement-attempt-33-semantic-focus-watched/ui-controller-config.frozen-semantic-focus-watched-a01.json'
TASK='war-reinforcement-screen-20261001-a15'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def identity(p):return {'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest().upper()}
def candidates(req,now):
 age=(now-datetime.fromisoformat(req['observed_at'])).total_seconds()
 if not 0<=age<=60:raise ValueError('Current focus request outside unchanged60-second freshness')
 pid=req['expected_ck3_pid']
 rows=[w for w in req['candidate_windows'] if w.get('pid')==pid and w.get('title')=='Crusader Kings III' and w.get('visible') is True and not w.get('minimized')]
 if len(rows)!=1:raise ValueError('Focus target not uniquely request-bound visible CK3')
 return pid,rows[0]['hwnd']
def check_lease():
 task=load(Path('D:/workspace/.codex-task-bus/tasks')/(TASK+'.json'))
 age=(datetime.now(timezone.utc)-datetime.fromisoformat(task['updated_at_utc'])).total_seconds()
 if task['state']!='running' or task['resources']!=['ck3-screen:acquired'] or not 0<=age<=600:raise ValueError('Fresh exclusive screen lease absent')
 if task['git']['head']!='1901473429deb1297be7d5d4451169082629858b':raise ValueError('Screen source changed')
 others=[]
 for p in Path('D:/workspace/.codex-task-bus/tasks').glob('*.json'):
  q=load(p)
  if q['task_id']==TASK or 'ck3-screen:acquired' not in q.get('resources',[]):continue
  if (datetime.now(timezone.utc)-datetime.fromisoformat(q['updated_at_utc'])).total_seconds()<=600:others.append(q['task_id'])
 if others:raise ValueError('Another fresh screen owner exists')
 return task
def main():
 out=ROOT/'R0137-focus-watch-a01';out.mkdir(exist_ok=False)
 request=CTL/'00-root-focus-request.json';receipt=CTL/'00-root-focus-result.json'
 start=time.monotonic();checked=None
 while not request.is_file():
  if time.monotonic()-start>1200:raise TimeoutError('No fresh focus request; no input sent')
  if checked is None or time.monotonic()-checked>20:check_lease();checked=time.monotonic()
  time.sleep(.2)
 if receipt.exists():raise FileExistsError('Existing focus receipt; never overwrite or repeat')
 request_body=load(request);pid,hwnd=candidates(request_body,datetime.now(timezone.utc));lease=check_lease()
 if psutil.Process(pid).name().lower()!='ck3.exe':raise ValueError('Request-owned process is not CK3')
 if win32process.GetWindowThreadProcessId(hwnd)[1]!=pid or win32gui.GetWindowText(hwnd)!='Crusader Kings III' or not win32gui.IsWindowVisible(hwnd):raise ValueError('Current HWND differs from request')
 config=load(CONFIG);helper_row=config['root_window_focus_helper'];helper=Path(helper_row['path'])
 if identity(helper)!=helper_row:raise ValueError('Frozen semantic focus helper changed')
 argv=[sys.executable,'-X','utf8=0','-B',str(helper),'--request',str(request),'--hwnd',str(hwnd),'--focus','--receipt',str(receipt),'--evidence-dir',str(CTL/'00-root-focus-evidence')]
 record={'schema':'ck3.root.one-shot-semantic-focus/v1','at':datetime.now(timezone.utc).isoformat(),'request':identity(request),'helper':helper_row,'argv':argv,'lease':lease,'one_shot':True,'manual_review_created':False,'mouse_or_gameplay_action_by_watcher':False}
 with (out/'invocation.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(record,f,indent=2);f.write('\n')
 with (out/'stdout.bin').open('xb') as stdout,(out/'stderr.bin').open('xb') as stderr:
  result=subprocess.run(argv,stdout=stdout,stderr=stderr,stdin=subprocess.DEVNULL,timeout=45,creationflags=subprocess.CREATE_NO_WINDOW)
 final={'exit_code':result.returncode,'receipt':identity(receipt) if receipt.is_file() else None,'status':load(receipt).get('status') if receipt.is_file() else None,'helper_called_once':True,'manual_UI_approval_created':False}
 with (out/'result.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(final,f,indent=2);f.write('\n')
 print(json.dumps(final),flush=True)
 return result.returncode
if __name__=='__main__':raise SystemExit(main())
