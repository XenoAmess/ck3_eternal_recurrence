"""Prepare and run an isolated native MCP acceptance session for Superman Qiang.

All mounted inputs and failed attempts remain external. The live mode exposes a
file inbox of actual MCP tool requests, retaining every request and response.
The default fixture marker belongs to the historical v1.0.0 42-case matrix.
For the v1.1.0 health matrix, select its baseline-ready marker explicitly, then
save that baseline before choosing the actual fixture action event. Session
completion never substitutes for the separate mechanism/UI/readback gates.
"""
from __future__ import annotations
import argparse
import asyncio
from dataclasses import asdict,is_dataclass
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

REPO=Path(os.environ['SXAD_REPO_ROOT']) if 'SXAD_REPO_ROOT' in os.environ else Path(__file__).resolve().parents[2]
sys.path.insert(0,str(REPO/'tools'))
sys.path.insert(0,str(REPO/'ck3_autonomous_player/src'))

def sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(asdict(value) if is_dataclass(value) else value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def utc() -> str: return datetime.now(timezone.utc).isoformat()

def prepare(args) -> dict:
    output=args.output.resolve()
    if output.exists(): raise ValueError('output must be a new external directory')
    vanilla=getattr(args,'vanilla',False)
    if vanilla and (args.production is not None or args.fixture is not None):
        raise ValueError('vanilla preparation must not mount production or fixture mods')
    if not vanilla and args.production is None:
        raise ValueError('production input required unless --vanilla is explicit')
    for source in (args.dll,args.injector,args.game/'binaries/ck3.exe') + (() if vanilla else (args.production,)):
        if not source.exists():raise ValueError('missing preparation input: '+str(source))
    output.mkdir(parents=True)
    profile=output/'state/profile'
    profile.mkdir(parents=True)
    mounts=[] if vanilla else [('product',args.production)]
    if args.fixture is not None:mounts.append(('fixture',args.fixture))
    for name,source in mounts:
        target=profile/'mod-content'/name
        shutil.copytree(source,target)
        outer=profile/'mod'/f'sxad_{name}.mod';outer.parent.mkdir(exist_ok=True)
        inner=(target/'descriptor.mod').read_text(encoding='utf-8-sig')
        outer.write_text(inner.rstrip()+'\n'+f'path="{target.as_posix()}"\n',encoding='utf-8-sig')
    for name in ('logs','save games','player/game_rules'):(profile/name).mkdir(parents=True)
    checkpoint=getattr(args,'checkpoint',None)
    checkpoint_input=None
    if checkpoint is not None:
        checkpoint=checkpoint.resolve()
        if not checkpoint.is_file():raise ValueError('checkpoint input missing')
        target=profile/'save games/xar_checkpoint.ck3'
        shutil.copy2(checkpoint,target)
        checkpoint_input={'source':str(checkpoint),'sha256':sha(target),'size':target.stat().st_size,'load_save_name':'xar_checkpoint'}
    write(profile/'dlc_load.json',{'enabled_mods':[f'mod/sxad_{name}.mod' for name,_ in mounts],'disabled_dlcs':[]})
    import pyautogui
    width,height=pyautogui.size()
    settings=f'''"game"={{
"promt_for_tutorial"={{ version=0 enabled=no }}
"prompt_for_china_tutorial"={{ version=0 enabled=no }}
"cloud_save"={{ version=0 enabled=no }}
}}
"Graphics"={{
"display_mode"={{ version=0 value="fullscreen" }}
"display_index"={{ version=0 value="0" }}
"fullscreen_resolution"={{ version=0 value="{width}x{height}" }}
}}
"System"={{ "language"={{ version=0 value="l_simp_chinese" }} }}
'''
    (profile/'pdx_settings.txt').write_text(settings,encoding='utf-8')
    (profile/'tutorial.txt').write_text('last_lesson_chain="reactive_advice"\ncompleted_lessons={\n}\n',encoding='utf-8')
    # Copy already available shader caches, without contacting Steam or changing
    # the user's real profile. Every copied cache is recorded as an input.
    real=getattr(args,'warm_cache_source',None) or Path.home()/'Documents/Paradox Interactive/Crusader Kings III'
    warm=[]
    for name in (() if getattr(args,'skip_warm_cache',False) else ('shadercache','shadercache_dx11')):
        if (real/name).is_dir(): shutil.copytree(real/name,profile/name);warm.append(name)
    if args.fixture is not None:
        fixture_manifest=args.fixture.parent/f'{args.fixture.name}.fixture.json'
        shutil.copy2(fixture_manifest,output/'fixture.json')
    if not vanilla:
        production_manifest=args.production.parent/f'{args.production.name}.manifest.json'
        shutil.copy2(production_manifest,output/'production.manifest.json')
    inputs={p.relative_to(profile).as_posix():sha(p) for p in profile.rglob('*') if p.is_file()}
    game_exe=args.game/'binaries/ck3.exe'
    source_head=os.environ['SXAD_SOURCE_COMMIT'] if 'SXAD_SOURCE_COMMIT' in os.environ else subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
    data={'schema':'sxad.native-acceptance-preparation.v1','prepared_at_utc':utc(),'game_dir':str(args.game.resolve()),'game_exe_sha256':sha(game_exe),'game_version':'1.20.0.3','profile':str(profile),'input_sha256':inputs,'production_source':str(args.production.resolve()) if not vanilla else None,'vanilla':vanilla,'fixture_source':str(args.fixture.resolve()) if args.fixture is not None else None,'native_dll':{'path':str(args.dll.resolve()),'sha256':sha(args.dll)},'native_injector':{'path':str(args.injector.resolve()),'sha256':sha(args.injector)},'python':sys.executable,'python_version':sys.version,'warm_cache_directories':warm,'warm_cache_source':str(real.resolve()),'desktop_size':[width,height],'repository_head':source_head,'runner_sha256':sha(Path(__file__)),'ck3_launch_attempted':False}
    data['checkpoint_input']=checkpoint_input
    data['fixture_ready_marker']=getattr(args,'fixture_ready_marker','SXAT: END production-effect-matrix')
    write(output/'preparation.json',data)
    (output/'inbox').mkdir();(output/'receipts').mkdir()
    return data

def check_inputs(run: Path) -> dict:
    data=json.loads((run/'preparation.json').read_text(encoding='utf-8'))
    profile=Path(data['profile'])
    for rel,wanted in data['input_sha256'].items():
        if sha(profile/rel)!=wanted: raise ValueError('prepared input changed: '+rel)
    for key in ('native_dll','native_injector'):
        if sha(Path(data[key]['path']))!=data[key]['sha256']: raise ValueError('native artifact changed: '+key)
    if sha(Path(data['game_dir'])/'binaries/ck3.exe')!=data['game_exe_sha256']: raise ValueError('game executable changed')
    return data

def mcp_server(run: Path) -> int:
    data=json.loads((run/'preparation.json').read_text(encoding='utf-8'))
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from xar_autoplayer.bridge.mcp_server import create_server
    driver=NativeHeadlessGameplayDriver(data['pipe_name'],state_dir=run/'state',save_dir=Path(data['profile'])/'save games',episode_projection='native_campaign',frontend_transition_timeout_seconds=600)
    try:create_server(driver,profile_dir=data['profile']).run(transport='stdio')
    finally:driver.close()
    return 0

async def interact(run: Path, handle, data: dict, timeout: float) -> dict:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    params=StdioServerParameters(command=sys.executable,args=['-X','utf8',str(Path(__file__)),'--mcp-server','--run-dir',str(run)],env={**os.environ,'PYTHONUTF8':'1','PYTHONIOENCODING':'utf-8'})
    sequence=0
    async with stdio_client(params,errlog=(run/'mcp-server.stderr.log').open('w',encoding='utf-8')) as (read,send):
        async with ClientSession(read,send) as session:
            await session.initialize()
            listing=await session.list_tools();write(run/'mcp-tools.json',listing.model_dump(mode='json'))
            async def call(name,args=None, label=None):
                nonlocal sequence
                sequence+=1
                request={'name':name,'arguments':args or {},'at_utc':utc()}
                write(run/'receipts'/f'{sequence:04d}-{label or name}-request.json',request)
                result=await session.call_tool(name,args or {})
                body=result.model_dump(mode='json');write(run/'receipts'/f'{sequence:04d}-{label or name}-response.json',body)
                if result.is_error: raise RuntimeError(str(body))
                value=result.structured_content
                if value is None:
                    value=json.loads(next(x.text for x in result.content if x.type=='text'))
                return value
            # Preserve early unavailable observations; query-only retries never
            # resubmit a Start or another mutating native operation.
            deadline=time.monotonic()+timeout
            while True:
                try:
                    cap=await call('ck3_get_capabilities')
                    if data.get('checkpoint_input') is not None:
                        snapshot=await call('ck3_take_snapshot',{'include_native_command_history':False})
                        if snapshot.get('map_ready') and (snapshot.get('played_character') or {}).get('character_id'):
                            route={'route':'checkpoint_map','snapshot':snapshot};break
                    else:
                        route=await call('ck3_query_frontend_gui_route_v1')
                        if route.get('route')=='main_menu':break
                except Exception as error:
                    write(run/f'boot-observation-{sequence:04d}.json',{'error':str(error),'at_utc':utc()})
                if handle.process.poll() is not None:raise RuntimeError('CK3 exited before main menu')
                if time.monotonic()>deadline:raise TimeoutError('native main menu deadline')
                await asyncio.sleep(2)
            write(run/'native-main-menu.json',{'capabilities':cap,'route':route})
            print('NATIVE_MAIN_MENU_READY',flush=True)
            if data.get('checkpoint_input') is None:
                await call('ck3_activate_frontend_new_game_v1')
                started=await call('ck3_activate_frontend_start_1066_bookmark_character_v1',{'character_name_key':'bookmark_rags_to_riches_duke_robert'})
            else:
                started={'intent':'native-load-save','checkpoint_input':data['checkpoint_input'],'native_map_readback':route['snapshot']}
            write(run/'native-start.json',started)
            print('ROBERT_CAMPAIGN_READY',flush=True)
            snapshot=await call('ck3_take_snapshot',{'include_native_command_history':False})
            write(run/'initial-snapshot.json',snapshot)
            run_matrix=data['fixture_source'] is not None and data.get('checkpoint_input') is None
            for step in (('set-speed-5','resume-map') if run_matrix else ()):
                deadline=time.monotonic()+120
                while True:
                    snapshot=await call('ck3_take_snapshot',{'include_native_command_history':False})
                    try:
                        await call('ck3_execute_step',{'step':step,'expected_revision':snapshot['revision']})
                        break
                    except RuntimeError as error:
                        if 'CK3 map state is unavailable' not in str(error) or time.monotonic()>deadline:raise
                        # This is a typed rejection before command submission;
                        # retain it, observe again, then retry the idempotent
                        # speed/pause state request. Never repeat a Start.
                        await call('ck3_query_frontend_gui_route_v1')
                        await asyncio.sleep(.5)
            # Delayed block boundaries release CK3's event recursion stack.
            # Fixture readiness comes from its explicit marker, not elapsed time.
            deadline=time.monotonic()+(300 if run_matrix else 0)
            fixture_seen=False
            while time.monotonic()<deadline:
                await asyncio.sleep(.25)
                snapshot=await call('ck3_take_snapshot',{'include_native_command_history':False})
                logs=Path(data['profile'])/'logs'
                fixture_seen=any(data.get('fixture_ready_marker','SXAT: END production-effect-matrix') in p.read_text(encoding='utf-8',errors='replace') for p in logs.glob('*.log'))
                if fixture_seen:break
            if run_matrix or not snapshot.get('paused'):
                await call('ck3_execute_step',{'step':'pause-map','expected_revision':snapshot['revision']})
            snapshot=await call('ck3_take_snapshot',{'include_native_command_history':False})
            write(run/'after-fixture-snapshot.json',snapshot)
            write(run/'fixture-progress.json',{'ready_marker':data.get('fixture_ready_marker','SXAT: END production-effect-matrix'),'ready_marker_seen':fixture_seen,'end_seen':fixture_seen if data.get('fixture_ready_marker','SXAT: END production-effect-matrix')=='SXAT: END production-effect-matrix' else None,'at_utc':utc(),'date_raw':snapshot.get('date_raw')})
            print('FIXTURE_MATRIX_END_SEEN',fixture_seen,flush=True)
            print('SESSION_HOLDING_FOR_INBOX',flush=True)
            write(run/'ready.json',{'at_utc':utc(),'pid':handle.process.pid,'uses_ocr':False})
            seen=set()
            while not (run/'stop').exists():
                if handle.process.poll() is not None:raise RuntimeError('owned CK3 process exited')
                for path in sorted((run/'inbox').glob('*.json')):
                    if path.name in seen:continue
                    seen.add(path.name)
                    try:
                        request=json.loads(path.read_text(encoding='utf-8'))
                        result=await call(request['name'],request.get('arguments'),label=path.stem)
                        write(run/'receipts'/f'inbox-{path.name}',{'request_path':str(path),'request_sha256':sha(path),'result':result,'ok':True})
                    except Exception as error:write(run/'receipts'/f'inbox-{path.name}',{'request_path':str(path),'request_sha256':sha(path),'error':str(error),'ok':False})
                await asyncio.sleep(.25)
            return {'status':'controlled_stop','last_receipt_sequence':sequence,'mcp_tools_discovered':len(listing.tools)}

def live(args) -> dict:
    run=args.run_dir.resolve();data=check_inputs(run)
    from xar_autoplayer.environment import EnvironmentSpec,ck3_process_inventory
    from xar_autoplayer.runtime import NativeBridgeLaunchConfig,launch,stop_tracked
    from ck3_live_run_id import allocate_live_run_id,load_live_run_identity,record_live_run_status
    bus=Path(args.task_bus);env={**os.environ,'PYTHONUTF8':'1','PYTHONIOENCODING':'utf-8'}
    subprocess.run([sys.executable,str(bus),'poll','--task',args.screen_task,'--ack','--limit','10000'],capture_output=True,check=True,env=env)
    inventory=ck3_process_inventory();write(run/'prelaunch-inventory.json',inventory)
    if inventory['processes']:raise RuntimeError('CK3 already running')
    identity=load_live_run_identity(args.run_id,mod_key='superman-qiang',external_mod=True) if args.run_id else allocate_live_run_id('superman-qiang',external_mod=True)
    write(run/'live-run-identity.json',identity)
    data['pipe_name']=rf'\\.\pipe\sxad_acceptance_{uuid.uuid4().hex}'
    write(run/'preparation.json',data)
    report={'schema':'sxad.native-acceptance-session.v1','started_at_utc':utc(),'run_identity':asdict(identity),'ck3_launch_attempted':False,'ok':False}
    write(run/'report.json',report)
    @contextmanager
    def gate():
        result=subprocess.run([sys.executable,str(bus),'list'],capture_output=True,check=True,env=env)
        tasks=json.loads(result.stdout.decode('utf-8'))['tasks']
        owners=[x for x in tasks if 'ck3-screen:acquired' in x.get('resources',[]) and x.get('state')=='running' and x.get('age_seconds',10000)<=600]
        if len(owners)!=1 or owners[0]['task_id']!=args.screen_task:raise RuntimeError('fresh screen lease absent')
        yield
    handle=None
    try:
        native=NativeBridgeLaunchConfig(mode='native-headless',pipe_name=data['pipe_name'],dll_path=Path(data['native_dll']['path']),injector_path=Path(data['native_injector']['path']))
        report['ck3_launch_attempted']=True;write(run/'report.json',report)
        load_kwargs={'load_save_name':data['checkpoint_input']['load_save_name']} if data.get('checkpoint_input') else {}
        handle=launch(EnvironmentSpec(run/'state',Path(data['game_dir']),'1.20.0.3'),native_bridge=native,verify_prepared_profile=False,before_process_create=gate,**load_kwargs)
        record_live_run_status(identity,'launch-started',reason=f'tracked CK3 PID {handle.process.pid}')
        report['process']={'pid':handle.process.pid,'creation_date':handle.ck3_creation_date,'arguments':handle.command,'injection':handle.injector_attestation}
        write(run/'report.json',report)
        report['interaction']=asyncio.run(interact(run,handle,data,args.timeout))
    except BaseException as error:
        report['error']=f'{type(error).__name__}: {error}'
        if handle is None or isinstance(error,(KeyboardInterrupt,SystemExit)):raise
        report['hot_retry_required']=True
        write(run/'report.json',report)
        write(run/'hot-retry-required.json',{'error':report['error'],'pid':handle.process.pid,'at_utc':utc(),'instruction':'same pipe may be adopted by a fresh MCP consumer; create stop only for controlled owned-process shutdown'})
        print('NATIVE_HOT_RETRY_REQUIRED',handle.process.pid,flush=True)
        while handle.process.poll() is None and not (run/'stop').exists():time.sleep(.25)
    finally:
        if handle is not None:
            report['shutdown']=stop_tracked(handle,require_running=False)
        report['post_shutdown_inventory']=ck3_process_inventory();report['finished_at_utc']=utc()
        report['completion_scope']='native session reached holding state and completed controlled cleanup; product mechanism/UI/persistence acceptance requires independent gates'
        report['ok']=bool(not report.get('error') and (report.get('interaction') or {}).get('status')=='controlled_stop' and (report.get('shutdown') or {}).get('cleanup_proven') and not report['post_shutdown_inventory']['processes'])
        write(run/'report.json',report)
    return report

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True);mode.add_argument('--prepare',action='store_true');mode.add_argument('--live',action='store_true');mode.add_argument('--mcp-server',action='store_true')
    parser.add_argument('--output',type=Path);parser.add_argument('--production',type=Path);parser.add_argument('--fixture',type=Path);parser.add_argument('--game',type=Path);parser.add_argument('--dll',type=Path);parser.add_argument('--injector',type=Path)
    parser.add_argument('--run-dir',type=Path);parser.add_argument('--run-id');parser.add_argument('--timeout',type=float,default=1200)
    parser.add_argument('--skip-warm-cache',action='store_true')
    parser.add_argument('--warm-cache-source',type=Path)
    parser.add_argument('--fixture-ready-marker',default='SXAT: END production-effect-matrix',help='Historical v1.0.0 default; v1.1.0 health uses SXAT: BASELINE_READY health-1.1.0 and requires a saved baseline before actions')
    parser.add_argument('--checkpoint',type=Path)
    parser.add_argument('--vanilla',action='store_true',help='Prepare a genuine unmodded profile for existing-save installation acceptance')
    parser.add_argument('--task-bus',default=r'D:\workspace\.codex-task-bus\bin\codex_task_bus.py');parser.add_argument('--screen-task')
    args=parser.parse_args()
    if args.mcp_server:return mcp_server(args.run_dir)
    if args.live:
        print('Legacy direct CK3 acceptance launch is disabled. Use tools/ck3_mod_acceptance.py plan / prepare / allocate / preflight / run / verify with the selected common runtime manifest.', file=sys.stderr)
        return 2
    try:
        result=prepare(args) if args.prepare else live(args)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        if args.live and not result.get('ok'):return 1
    except (OSError,ValueError,RuntimeError,TimeoutError) as error:parser.exit(1,f'SXAD ACCEPTANCE FAILED: {error}\n')
    return 0
if __name__=='__main__':raise SystemExit(main())
