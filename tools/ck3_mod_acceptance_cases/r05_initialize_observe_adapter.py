"""Controlled R05 initialization and bounded natural observation, public host."""
from pathlib import Path
import hashlib
import json
import time

class InitializerBudget:
    """Bound the existing initializer calls inside the original cleanup room."""
    def __init__(self,client,settings,command_timeout):
        self.client=client;self.settings=settings;self.command_timeout=command_timeout;self.serial=0
    def __getattr__(self,key):return getattr(self.client,key)
    def execute_plan(self,steps,name,timeout=None):
        from xar_autoplayer.bridge.r05_supply_observation_case import require
        reserve=self.settings['normal_close_reserve_seconds']+self.settings['cleanup_save_reserve_seconds']
        remaining=min(self.client.remaining(),self.settings['deadline_unix_seconds']-time.time())
        require(remaining>reserve+1,'original initializer cleanup/normal-close reserve exhausted')
        self.client.guard(reserve=reserve+1)
        allowed=min(self.command_timeout if timeout is None else timeout,remaining-reserve)
        return self.client.execute_plan(steps,name,timeout=allowed)
    def snapshot(self):
        self.serial+=1;name='r05init-budget-snapshot-'+str(self.serial).zfill(3)
        rows=self.execute_plan([{'id':name,'tool':'ck3_take_snapshot',
            'args':{'include_native_command_history':False},'fresh_revision':False}],name)
        from xar_autoplayer.bridge.r05_supply_observation_case import require
        require(len(rows)==1 and rows[0].get('id')==name and rows[0].get('ok') is True and not rows[0].get('error'),
            'actual initializer snapshot failed; never replay')
        frame=rows[0]['result'];self.client.validate_frame(frame);return frame

def initializer(context):
    # Source selected by the same public repo_root, not an external host path.
    import importlib.util
    path=Path(context['repo_root'])/'tools/ck3_mod_acceptance_cases/r05_low_supply_adapter.py'
    spec=importlib.util.spec_from_file_location('r05_existing_initializer_adapter',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def post_initializer_camera_settings(value):
    """An explicit bounded coordination option; absent or disabled never waits."""
    from xar_autoplayer.bridge.r05_low_supply_fixture import require
    if value is None:
        return None
    require(type(value) is dict and type(value.get('enabled')) is bool,
            'post_initializer_camera needs an explicit boolean enabled')
    require(set(value) <= {'enabled','maximum_wait_seconds'}, 'unknown post_initializer_camera setting')
    if value['enabled'] is False:
        return None
    seconds=value.get('maximum_wait_seconds')
    require(type(seconds) is int and 1 <= seconds <= 900,
            'post_initializer_camera maximum_wait_seconds must be explicit1..900')
    return {'maximum_wait_seconds':seconds}


def await_post_initializer_camera(context,client,settings,initialization,camera,*,
                                  _time=time.time,_monotonic=time.monotonic,_sleep=time.sleep):
    """Read only a Root Start signal under the original hold; never start a camera.

    The signal is coordination, not video/R05 qualification. Its fixed path is
    client.output/post-initializer-camera-started.actual.json. Required fields:
    machine_id, run_id, bridge_pid, date_raw, camera_started=true, and
    start_receipt={path,bytes,sha256}. A relative receipt path is relative to the
    signal directory. Root writes the actual receipt before publishing signal.
    """
    from xar_autoplayer.bridge.r05_low_supply_fixture import require
    if camera is None:
        return None
    assessment=initialization.get('assessment',{})
    after=initialization.get('independent_after',{})
    frame=after.get('machine_independent_frame',{})
    stock=after.get('current_supply_raw')
    require(assessment.get('status')=='prepared_low_stock' and assessment.get('low_stock_observed') is True
            and assessment.get('physical_soldiers_unchanged') is True and type(stock) is int
            and 0 <= stock < 1000000 and assessment.get('actual_after_stock_raw')==stock,
            'camera wait requires independently verified prepared low stock')
    machine=context['machine_id'];run_id=client.selection.run_dir.name;pid=after.get('pid');date=frame.get('date_raw')
    require(initialization.get('machine_id')==machine and initialization.get('pid')==pid
            and type(pid) is int and pid>0 and type(date) is int
            and frame.get('episode_run_id')==run_id and initialization.get('natural_days_advanced')==0,
            'camera wait initializer machine/run/PID/date binding differs')
    signal=Path(client.output)/'post-initializer-camera-started.actual.json'
    reserve=settings['normal_close_reserve_seconds']+settings['cleanup_save_reserve_seconds']
    binding={'machine_id':machine,'run_id':run_id,'bridge_pid':pid,'date_raw':date}
    checkpoint={**binding,'stock_raw':stock,'original_hold_unix_seconds':client._hold,
                'original_deadline_unix_seconds':settings['deadline_unix_seconds'],
                'cleanup_normal_close_reserve_seconds':reserve,'maximum_wait_seconds':camera['maximum_wait_seconds'],
                'signal_path':str(signal),'coordination_only':True,'video_or_R05_PASS_inferred':False}
    client.checkpoint('post-initializer-camera-awaiting',checkpoint)
    started=_monotonic()
    while True:
        left=camera['maximum_wait_seconds']-(_monotonic()-started)
        require(left>0,'post-initializer camera Start signal wait timed out')
        room=min(client.remaining(),client._hold-_time(),settings['deadline_unix_seconds']-_time())-reserve
        require(room>1,'original camera wait cleanup/normal-close reserve exhausted')
        client.guard(reserve=reserve+1)
        value=None
        if signal.exists():
            try:
                value=json.loads(signal.read_bytes())
            except json.JSONDecodeError:
                # A partially published signal is never an ACK; the same bound applies.
                pass
        if value is not None:
            require(type(value) is dict and all(type(value.get(k)) is type(v) and value.get(k)==v
                    for k,v in binding.items()) and value.get('camera_started') is True,
                    'Root camera Start signal machine/run/PID/date differs')
            ref=value.get('start_receipt')
            require(type(ref) is dict and type(ref.get('path')) is str and ref['path']
                    and type(ref.get('bytes')) is int and 0<ref['bytes']<=1048576
                    and type(ref.get('sha256')) is str and len(ref['sha256'])==64
                    and all(c in '0123456789abcdef' for c in ref['sha256'].lower()),
                    'Root camera Start signal needs an actual small JSON receipt pin')
            path=Path(ref['path']);path=path if path.is_absolute() else signal.parent/path
            require(path.suffix.lower()=='.json' and path.is_file() and path.stat().st_size==ref['bytes'],
                    'Root camera Start receipt absent or size differs')
            raw=path.read_bytes()
            require(len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'].lower()
                    and type(json.loads(raw)) is dict,'Root camera Start receipt SHA/JSON differs')
            accepted={**checkpoint,'camera_started':True,'start_receipt':ref,
                      'elapsed_wait_seconds':_monotonic()-started,'signal_only_accepted':True}
            client.checkpoint('post-initializer-camera-signal-accepted',accepted)
            return accepted
        _sleep(min(0.25,left,room-1))



def validate_contract(context):
    from xar_autoplayer.bridge.r05_supply_observation_case import observation_settings
    from xar_autoplayer.bridge.r05_low_supply_fixture import require
    require(context['case_contract'].get('schema')=='xar.r05-initialize-observe-common-case.v1',
        'initialize-observe case contract differs')
    # Public plan can remain explicitly unbound; prepare/run cannot.
    value=context['case_inputs'].get('observation')
    if value is not None:observation_settings(value)
    post_initializer_camera_settings(context['case_inputs'].get('post_initializer_camera'))

def prepare_case(context):
    post_initializer_camera_settings(context['case_inputs'].get('post_initializer_camera'))
    from xar_autoplayer.bridge.r05_supply_observation_case import observation_settings
    settings=observation_settings(context['case_inputs']['observation'])
    result=initializer(context).prepare_case(context)
    result.update(observation=settings,observation_connected=True,maximum_actual_days=settings['maximum_actual_days'],
        natural_callback_or_starvation_qualified=False,observation_runtime_status='NOT_RUN')
    return result

def run_case(context,client):
    from ck3_mod_acceptance_full_army import ensure_common_full_army_client
    client=ensure_common_full_army_client(client)
    from ck3_live_run_id import current_machine_id
    from xar_autoplayer.bridge import r05_supply_observation_case as observe
    settings=observe.observation_settings(context['case_inputs']['observation'])
    camera=post_initializer_camera_settings(context['case_inputs'].get('post_initializer_camera'))
    reserve=settings['normal_close_reserve_seconds']+settings['cleanup_save_reserve_seconds']
    # All commands, initializer and observation consume the same original hold.
    observe.require(type(client._hold) in (int,float),
        'actual owned hold must be numeric')
    observe.require(min(client.remaining(),settings['deadline_unix_seconds']-time.time())>
        reserve+settings['one_day_timeout_seconds'],'no original observation/normal-close room before initialization')
    client.guard(reserve=reserve+settings['one_day_timeout_seconds'])
    budget=getattr(client.selection,'effective_budgets',client.selection.case['budgets'])
    initializer(context).run_case(context,InitializerBudget(client,settings,budget['command_timeout']))
    source=Path(context['output'])/'r05-controlled-initializer-outcome.json'
    init=json.loads(source.read_bytes())
    actual_context={**context,'machine_id':current_machine_id(),'command_timeout':budget['command_timeout']}
    await_post_initializer_camera(actual_context,client,settings,init,camera)
    result=observe.observe_initialized_supply(client,settings,context=actual_context,initialization=init)
    return {'machine_id':actual_context['machine_id'],'status':result['status'],
        'verified_actual_days':result['verified_actual_days'],'R05_physical_predicate':result['R05_positive'],
        'sampling_OFF_clear_verified':result['cleanup']['sampling_OFF_clear_verified'],
        'normal_save_verified':result['cleanup']['save_verified'],'normal_close_pending':True,
        'business_pass':False,'product_release_pass':False}

def verify_case(context):
    path=Path(context['output'])/'r05-initialize-and-observe-result.json'
    if not path.is_file():return {'machine_id':'unknown','case_contract_qualified':False,
        'gui_contract_qualified':False,'R05_pass':False,'reason':'actual observation evidence absent'}
    result=json.loads(path.read_bytes());cleanup=result.get('cleanup',{})
    qualified=(result.get('R05_positive') is True and 1<=result.get('verified_actual_days',0)<=30 and
        cleanup.get('sampling_OFF_clear_verified') is True and cleanup.get('save_verified') is True)
    init=initializer(context).verify_case(context)
    closed=Path(context['output'])/'normal-close-result.json'
    normal=json.loads(closed.read_bytes()) if closed.is_file() else {}
    return {'machine_id':result['machine_id'],'case_contract_qualified':qualified,
        'gui_contract_qualified':init.get('gui_contract_qualified') is True,
        'R05_physical_predicate':result.get('R05_positive') is True,
        'R05_pass':qualified and init.get('gui_contract_qualified') is True and normal.get('normal_close_qualified') is True,
        'case_acceptance_pass':False,'business_contract_applicable':False,'business_pass':False,
        'scope':'controlled fixture plus natural periodic physical starvation predicate',
        'updater_AL_observed':False,'status':result['status'],'cleanup':cleanup}
