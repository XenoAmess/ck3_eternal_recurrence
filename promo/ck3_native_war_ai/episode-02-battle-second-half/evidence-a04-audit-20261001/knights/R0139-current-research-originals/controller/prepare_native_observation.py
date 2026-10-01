from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,sys,subprocess
ROOT=Path(__file__).resolve().parent
SOURCE=Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001/reinforcement-attempt-12-R0129-native-center-diagnostic/source')
LIVE=Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-ui-live-20261001-a02')
def ident(p):
    p=Path(p).resolve();return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest().upper()}
plan={'schema':'xar.native-research-plan.v1','topic':'episode02-six-gap-current-native-research','purpose':'engine-transition',
      'question':'What exact selector, death request/commit and ordered roster/entry transitions occur in the episode D26 natural knight event, and which same-run original UI states are visible?',
      'build':{'version':'1.19.0.6','exe_sha256':'2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86'},
      'observation':{'mode':'passive-runtime','actor_kind':'engine','identity_kind':'generation-id','producer_trigger':'daily-tick',
          'owner_scope':'One isolated vanilla process and CombatID16777218, actor29829, War4, Army18; knight33437/reg65 and observed enemy selector return',
          'identity_lifetime':'Every native full ID must resolve in the same process/revision; event pointer/load identity expires on process reload',
          'producer':'Original native daily dispatch and experimental passive phase trace, plus explicitly paused original UI and DTO reads',
          'caller':'Original CCombatManager daily calls; root only submits one managed life-advance with current revision',
          'consumer':'Episode02 mechanism explanation and new typed observation research; no video revision until all six user gaps are closed',
          'cache_lifetime':'One generation/revision/query, no reused post-hover or post-day cached state',
          'expected_signal':'Before and after exact full-ID ordered rosters, bounded GUI census, seven original boundaries and scoped causal/writeback data',
          'zero_sample_meaning':'Zero event/selector/death calls is no hit in this natural window, not proof of impossibility; failed identity remains failed',
          'stop_condition':'One explicit managed day at most; preserve all originals, never retry ambiguous day; finish same owner and verify cleanup',
          'runtime_window_ref':str(ROOT/'ui-launch-plan.json')},
      'evidence':[],
      'nodes':[{'id':'loaded','label':'Paused source D26'},{'id':'event','label':'Native scheduled event and selector'},
               {'id':'request','label':'Death request and deferred commit'},{'id':'after','label':'Paused next-day character/roster/UI'}],
      'edges':[{'id':'loaded-event','from':'loaded','to':'event','label':'Natural daily schedule and actual selected target','status':'unknown','evidence':[],
                'open_question':'Current run original daily phase/selector capture is pending'},
               {'id':'event-death','from':'event','to':'request','label':'Actual death request and commit provenance','status':'unknown','evidence':[],
                'open_question':'Full event effect and native deferred death boundaries must be observed'},
               {'id':'death-after','from':'request','to':'after','label':'Current full-ID roster/entry and character UI writes','status':'unknown','evidence':[],
                'open_question':'Legitimate retired RegimentID must be observed without relaxing generation equality'}],
      'cases':[{'id':'knight-d26','question':'Same natural event, actual death and exact next-day roster/character?','status':'pending','evidence':[]}]}
for eid,path,claim in [('frozen-source',SOURCE/'promo/ck3_native_war_ai/integration/capture_session.py','Source-bound managed capture and owner request service'),
                       ('current-profile',ROOT/'operator-profile-a01.json','New run exact source, DLL, save and exclusive screen binding')]:
    p=ident(path);plan['evidence'].append({'id':eid,'layer':'source-contract','path':p['path'],'sha256':p['sha256'],
                         'exe_sha256':plan['build']['exe_sha256'],'supports':claim})
with (ROOT/'native-research-plan.json').open('x',encoding='utf-8') as f:json.dump(plan,f,ensure_ascii=False,indent=2)
p=subprocess.run([sys.executable,str(SOURCE/'tools/native_research_plan.py'),'check',str(ROOT/'native-research-plan.json'),
                  '--for-observation','--output',str(ROOT/'native-research-plan-check.json')],capture_output=True,text=True,encoding='utf-8')
with (ROOT/'native-plan-check-process.json').open('x',encoding='utf-8') as f:json.dump({'argv':p.args,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr},f,indent=2)
if p.returncode:raise RuntimeError(p.stdout+p.stderr)
old=Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001/root-attempt-03/knight_saved_pair.py')
text=old.read_text(encoding='utf-8').replace("Path('C:/w/ep2a04')",'Path('+repr(str(SOURCE))+')')
text=text.replace('episode02-e2-05-d26-nextday-live-20261001-a03','episode02-e2-05-d26-six-gap-ui-live-20261001-a02')
with (ROOT/'knight_saved_pair.py').open('x',encoding='utf-8',newline='\n') as f:f.write(text)
print('Sampling plan check PASS; current source-bound saved-pair consumer prepared.')
