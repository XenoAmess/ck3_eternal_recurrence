import json,pathlib,subprocess,sys
from datetime import datetime,timezone
OUT=pathlib.Path(__file__).resolve().parent
REPO=pathlib.Path('D:/workspace/ck3_eternal_recurrence')
BUS='D:/workspace/.codex-task-bus/bin/codex_task_bus.py'
TASK='e04-r06-public-review-fix-20261020-a01'
def call(args):
 r=subprocess.run([sys.executable,'-X','utf8',BUS,*args],cwd=REPO,capture_output=True,text=True,encoding='utf-8',check=True)
 return json.loads(r.stdout)
registration=call(['register','--task',TASK,'--summary','Source_only_fix_actual_observer_SHA_and_postcamera300s_TTL_18focused_1route_PASS','--repo',str(REPO)])
poll=call(['poll','--task',TASK,'--ack','--limit','1'])
listed=call(['list','--require-existing'])
active=[x for x in listed.get('tasks',[]) if x.get('last_sequence',0)>=7280 and x.get('state')!='done']
finish=call(['status','--task',TASK,'--state','done','--summary','Both_independent_review_rejections_fixed_18focused_1R04_PASS_no_game_native_edits_commit','--next-step','Root_final_source_only_review_and_commit','--repo',str(REPO)])
record=dict(schema='xar.e04.r06.review_fix.taskbus_receipt.v1',machine_id='desktop-3fevhd2-1c74096080',observed_at_utc=datetime.now(timezone.utc).isoformat(),
 registration=registration.get('event'),poll_summary={k:v for k,v in poll.items() if k!='events'},recent_active_tasks_at_list=active,completion=finish)
p=OUT/'BUS-REVIEW-FIX.actual.json';p.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(path=str(p),completed_sequence=finish.get('event',{}).get('sequence'),state=finish.get('task',{}).get('state'),recent_active_tasks=active),ensure_ascii=False))
