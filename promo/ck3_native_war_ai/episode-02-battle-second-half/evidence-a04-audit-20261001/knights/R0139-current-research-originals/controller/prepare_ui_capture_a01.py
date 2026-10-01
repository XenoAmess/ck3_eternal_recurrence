from pathlib import Path
from datetime import datetime, timezone
import hashlib, importlib.metadata, json, os, subprocess, sys, uuid
ROOT=Path(__file__).resolve().parent
SOURCE=Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001/reinforcement-attempt-12-R0129-native-center-diagnostic/source')
NATIVE=SOURCE.parent
BUS=Path('D:/workspace/.codex-task-bus/bin/codex_task_bus.py')
BUS_SHA='B3C44B42F7BDF401B593D863E3210106A46412DCD7D89F8596C74F4C27392DEE'
TASK='war-e2-six-gap-screen-20261001-a01'
LIVE=Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-ui-live-20261001-a02')
STATIC=Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-ui-preflight-20261001-a02')
def identity(path):
    p=Path(path).resolve()
    return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest().upper()}
def write(path,obj):
    with path.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2)
if LIVE.exists() or STATIC.exists():raise RuntimeError('New run paths already exist')
q=subprocess.run(['gh','api','repos/XenoAmess/xar_promo_toolchain/releases/latest'],capture_output=True,text=True,encoding='utf-8',timeout=30)
write(ROOT/'capture-toolchain-release-query.json',{'at_utc':datetime.now(timezone.utc).isoformat(),'argv':q.args,'returncode':q.returncode,'stdout':q.stdout,'stderr':q.stderr})
if q.returncode:raise RuntimeError('Current formal release unavailable')
rel=json.loads(q.stdout)
wheel=next(v for v in rel['assets'] if v['name'].endswith('.whl'))
version=importlib.metadata.version('xar-promo-toolchain')
direct=json.loads(importlib.metadata.distribution('xar-promo-toolchain').read_text('direct_url.json'))
if rel['draft'] or rel['prerelease'] or rel['tag_name'].removeprefix('v')!=version or direct['archive_info']['hashes']['sha256'].upper()!=wheel['digest'].removeprefix('sha256:').upper():
    raise RuntimeError('Update latest wheel before new capture run')
probes=[]
for flags in [['--version'],['--help']]:
    p=subprocess.run([sys.executable,'-m','xar_promo',*flags],capture_output=True,text=True,encoding='utf-8')
    probes.append({'argv':p.args,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
    if p.returncode:raise RuntimeError('Current toolchain probe failed')
write(ROOT/'capture-toolchain-interpreter-probe.json',{'at_utc':datetime.now(timezone.utc).isoformat(),'purpose':'required dependency of native capture; no video revision or rendering',
      'version':version,'wheel':wheel,'interpreter':identity(sys.executable),'python':sys.version,'probes':probes})
frame=ROOT/'wgc-steam-library-change-a01/frame-03.png'
change=ROOT/'wgc-steam-library-change-a01/receipt.json'
offline=ROOT/'steam-offline-reviewed-a01.json'
write(offline,{'schema':'ck3.steam-offline.visual-wgc-window/v1','current_offline_ui_observed':True,'observed_at':datetime.now(timezone.utc).isoformat(),
      'screenshot':identity(frame),'reviewer':'root-agent direct inspection of current original HWND pixels',
      'observation':'Current BG3 library body states Steam 当前处于离线模式; bottom 离线模式. Current semantic navigation changed CK3 library to BG3.',
      'capture_kind':'original WGC HWND frame','hwnd':197612,'pid':7068,'process_create_time':1790777038.7610564,
      'freshness':{'semantic_navigation':'steam://nav/games/details/1086940','previous_desktop':identity(ROOT.parent/'root-attempt-01/wgc-steam-library-change-a01/frame-03.png'),
                   'changing_content_receipt':identity(change),'old_desktop_clock_stale':True,'same_window_semantic_page_changed':True},
      'steam_mode_changed':False,'human_video_signoff':False})
hb=subprocess.run([sys.executable,str(BUS),'--expected-cli-sha256',BUS_SHA,'heartbeat','--task',TASK,'--expected-sequence','3356','--repo',str(SOURCE)],capture_output=True,text=True,encoding='utf-8')
write(ROOT/'screen-heartbeat-before-ui.json',{'argv':hb.args,'returncode':hb.returncode,'stdout':hb.stdout,'stderr':hb.stderr})
if hb.returncode:raise RuntimeError('Exclusive screen heartbeat refused')
sequence=json.loads(hb.stdout)['task']['last_sequence']
plan=json.loads(Path('C:/w/e2gold1001/promo/ck3_native_war_ai/episode-02-battle-second-half/evidence-a04-audit-20261001/knights/capture-nextday-plan.json').read_text(encoding='utf-8'))
args=[sys.executable,'-X','utf8=0','-B',str(SOURCE/'promo/ck3_native_war_ai/integration/capture_session.py'),
      '--game-dir','C:/SteamLibrary/steamapps/common/CRUSAD~1','--bridge-dll',str(NATIVE/'build-attempt-01/build/xar_ck3_bridge.dll'),
      '--bridge-injector',str(NATIVE/'build-attempt-01/build/xar_ck3_bridge_injector.exe'),
      '--state-dir',str(LIVE/'ck3-state'),'--output-dir',str(LIVE/'ck3-output'),'--pipe-name',r'\\.\pipe\xar_ck3_e2_six_gap_ui_'+uuid.uuid4().hex,
      '--checkpoint-save',plan['exact_input']['save']['path'],'--checkpoint-receipt',plan['exact_input']['receipt']['path'],
      '--frontend-timeout','900','--gui-scale','1.0','--import-a04-ui-gui-100',
      '--a04-ui-settings-snapshot',plan['source_reuse']['gui_settings_snapshot']['path'],
      '--a04-ui-preservation-receipt',plan['source_reuse']['gui_preservation_receipt']['path'],
      '--interactive-seconds','3600','--recovery-seconds','180','--hold-seconds','30','--enable-private-phase-trace',
      '--steam-offline-receipt',str(offline),'--screen-task-id',TASK,'--screen-expected-sequence',str(sequence),'--screen-cli-sha256',BUS_SHA]
staticargs=[a.replace(str(LIVE),str(STATIC)) for a in args]
write(ROOT/'ui-no-launch-argv.json',staticargs)
result=subprocess.run(staticargs,cwd=SOURCE,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
with (ROOT/'ui-no-launch-stdout.txt').open('x',encoding='utf-8') as f:f.write(result.stdout)
with (ROOT/'ui-no-launch-stderr.txt').open('x',encoding='utf-8') as f:f.write(result.stderr)
write(ROOT/'ui-no-launch-process.json',{'argv':staticargs,'returncode':result.returncode,'stdout':identity(ROOT/'ui-no-launch-stdout.txt'),'stderr':identity(ROOT/'ui-no-launch-stderr.txt')})
if result.returncode:raise RuntimeError('No-launch preflight RED; preserve originals')
required=[]
for path in [args[4],args[8],args[10],plan['exact_input']['save']['path'],plan['exact_input']['receipt']['path'],
             plan['source_reuse']['gui_settings_snapshot']['path'],plan['source_reuse']['gui_preservation_receipt']['path'],offline,frame,
             ROOT/'capture-toolchain-interpreter-probe.json',ROOT/'ui-no-launch-process.json',STATIC/'ck3-output/preflight.json']:
    pin=identity(path);required.append({'path':pin['path'],'kind':'file','size':pin['bytes'],'sha256':pin['sha256']})
profile={'schema_version':1,'target':{'id':'ck3-six-gap-ui-20261001-a02','display_name':'Episode02 character/roster/full-battle UI research',
         'expected':{'token_user':'1','desktop':'WinSta0\\Default','machine':'DESKTOP-3FEVHD2'}},'endpoint':{'transport':'stdio'},
         'state_directory':str(ROOT/'operator-state-a01'),'jobs':{'six-gap-ui-capture':{'command':args+['--capture'],'working_directory':str(SOURCE),
         'exclusive_process_names':['ck3.exe','xar_ck3_bridge_injector.exe','ffmpeg.exe','obs64.exe','dowser.exe'],
         'required_paths':required,'absent_paths':[str(LIVE)],'controls':{}}}}
write(ROOT/'operator-profile-a01.json',profile)
write(ROOT/'ui-launch-plan.json',{'at_utc':datetime.now(timezone.utc).isoformat(),'args':args+['--capture'],'profile':identity(ROOT/'operator-profile-a01.json'),
      'source_head':'1901473429deb1297be7d5d4451169082629858b','native_pair':[identity(args[8]),identity(args[10])],
      'screen_sequence':sequence,'new_live_run_id':None,'scope':'UI research capture; broader trace extension remains separate new source/run',
      'expected_before_raw':53146848,'expected_after_raw':53146872,'expected_before_ui':'1066.12.29','expected_after_ui':'1066.12.30','master_intake':False})
print(json.dumps({'result':'PREFLIGHT_GREEN_NOT_LAUNCHED','profile':str(ROOT/'operator-profile-a01.json'),'screen_sequence':sequence,'latest':version},ensure_ascii=False))
