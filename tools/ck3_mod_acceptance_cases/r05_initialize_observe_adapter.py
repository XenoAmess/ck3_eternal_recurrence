"""Controlled R05 initialization and bounded natural observation, public host."""
from pathlib import Path
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

def validate_contract(context):
    from xar_autoplayer.bridge.r05_supply_observation_case import observation_settings
    from xar_autoplayer.bridge.r05_low_supply_fixture import require
    require(context['case_contract'].get('schema')=='xar.r05-initialize-observe-common-case.v1',
        'initialize-observe case contract differs')
    # Public plan can remain explicitly unbound; prepare/run cannot.
    value=context['case_inputs'].get('observation')
    if value is not None:observation_settings(value)

def prepare_case(context):
    from xar_autoplayer.bridge.r05_supply_observation_case import observation_settings
    settings=observation_settings(context['case_inputs']['observation'])
    result=initializer(context).prepare_case(context)
    result.update(observation=settings,observation_connected=True,maximum_actual_days=settings['maximum_actual_days'],
        natural_callback_or_starvation_qualified=False,observation_runtime_status='NOT_RUN')
    return result

def run_case(context,client):
    from ck3_live_run_id import current_machine_id
    from xar_autoplayer.bridge import r05_supply_observation_case as observe
    settings=observe.observation_settings(context['case_inputs']['observation'])
    reserve=settings['normal_close_reserve_seconds']+settings['cleanup_save_reserve_seconds']
    # All commands, initializer and observation consume the same original hold.
    observe.require(type(client._hold) in (int,float) and client._hold<=settings['deadline_unix_seconds'],
        'actual owned hold exceeds the Root-bound original deadline')
    observe.require(min(client.remaining(),settings['deadline_unix_seconds']-time.time())>
        reserve+settings['one_day_timeout_seconds'],'no original observation/normal-close room before initialization')
    client.guard(reserve=reserve+settings['one_day_timeout_seconds'])
    budget=getattr(client.selection,'effective_budgets',client.selection.case['budgets'])
    initializer(context).run_case(context,InitializerBudget(client,settings,budget['command_timeout']))
    source=Path(context['output'])/'r05-controlled-initializer-outcome.json'
    init=json.loads(source.read_bytes())
    actual_context={**context,'machine_id':current_machine_id(),'command_timeout':budget['command_timeout']}
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
