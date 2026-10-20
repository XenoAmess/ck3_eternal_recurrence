"""Read each new journal line within2s; immediately notify Root's task on RED/stall."""
from packet_common import *
import psutil,subprocess
STOP=B/'R0221-LIVE-ALARM-WATCH.STOP';OWNER=B/'R0221-LIVE-ALARM-WATCH-OWNED.actual-a01.json'
assert not STOP.exists() and not OWNER.exists()
target='e04-r06-resume-20261020-a02'
put(OWNER,{'machine_id':M,'observed_at_utc':now(),'pid':os.getpid(),'create_time':psutil.Process().create_time(),
 'source':pin(__file__),'argv':psutil.Process().cmdline(),'stop_flag':str(STOP),'deadline_utc':DEADLINE,
 'poll_seconds':2,'task_bus_notify_target':target,'no_ledger_capacity_or_scene_mutation':True,'new_heavy_budget_bytes':0})
paths=sorted(B.glob('R06-ACTUAL-UNSPENT-GUARD.actual-part*.jsonl'));assert paths
current=paths[-1];offset=current.stat().st_size;pending=b''
with current.open('rb') as f:
 f.seek(max(0,offset-32768));last=json.loads(f.read().splitlines()[-1])
sequence=0;active_alarm=False;stale_notified=False
def notify(kind,row,reference=None,error=None):
 global sequence
 sequence+=1;assert sequence<=40,'Bounded alarm receipts exhausted; inspect explicitly'
 receipt=put(B/('R0221-LIVE-ALARM-%03d.actual.json'%sequence),{
  'machine_id':M,'observed_at_utc':now(),'kind':kind,'run_id':M+'--vanilla--R0221',
  'journal_path':str(current),'journal_row':row,'error':error,'source':pin(__file__),
  'ledger_or_capacity_changed':False,'automatic_stop_of_game_or_producer_not_claimed':True,
  'Root_phase_checker_still_required_before_new_camera_worker':True})
 message='machine_id:'+M+' R0221 capacity '+kind+' observed='+str(row.get('observed_at_utc'))+' receipt='+receipt['path']+' SHA='+receipt['sha256']+' alarms='+json.dumps(row.get('alarms',[]))
 r=subprocess.run([sys.executable,'-B','-X','utf8',str(R/'tools/codex_task_bus.py'),'notify','--task',T,'--to',target,'--level','action' if kind!='RECOVERED_COMPLETE_GREEN' else 'info','--message',message],capture_output=True,text=True,encoding='utf-8')
 n=put(B/('R0221-LIVE-ALARM-%03d-BUS-NOTIFY.actual.json'%sequence),{
  'machine_id':M,'observed_at_utc':now(),'alarm_receipt':receipt,'target_task':target,
  'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
 print(json.dumps({'kind':kind,'receipt':receipt,'bus_notification':n,'notify_returncode':r.returncode}),flush=True)
 assert r.returncode==0,'Bus notify failed; inspect original receipt'
while not STOP.exists() and datetime.now(timezone.utc)<datetime.fromisoformat(DEADLINE.replace('Z','+00:00')):
 paths=sorted(B.glob('R06-ACTUAL-UNSPENT-GUARD.actual-part*.jsonl'))
 # Drain current part fully before switching, retaining a partial append for next pass.
 with current.open('rb') as f:f.seek(offset);new=f.read();offset+=len(new)
 pending+=new
 while b'\n' in pending:
  raw,pending=pending.split(b'\n',1);row=json.loads(raw);last=row;stale_notified=False
  bad=bool(row['alarms']) or row['measurement_coverage_complete'] is not True or row['budget_status']!='GREEN'
  if bad:notify('RED_OR_COVERAGE_GAP',row);active_alarm=True
  elif active_alarm:notify('RECOVERED_COMPLETE_GREEN',row);active_alarm=False
 if current!=paths[-1] and not pending:current=paths[-1];offset=0
 age=(datetime.now(timezone.utc)-datetime.fromisoformat(last['observed_at_utc'])).total_seconds()
 if age>45 and not stale_notified:
  notify('GUARD_OBSERVATION_STALE_OVER45S',last,error='Latest observation age='+str(age));stale_notified=True;active_alarm=True
 time.sleep(2)
print(json.dumps({'machine_id':M,'observed_at_utc':now(),'alarm_watcher_exited':True,'exact_stop_flag_present':STOP.exists()}),flush=True)
