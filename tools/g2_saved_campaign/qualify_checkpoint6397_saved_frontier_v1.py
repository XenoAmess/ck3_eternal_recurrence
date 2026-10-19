"""Detached exact-source qualification. No launch or external writes."""
import ast,copy,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
import checkpoint6397_saved_frontier_v1 as contract
T=Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime')
F=T.parent.parent/'p51-fresh1066-v20261019-prepare01/c15-session-interruption90'

def pin(p):
    b=p.read_bytes();return {'path':str(p.resolve()),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}

def main():
    cadence=T/'root_p37_checkpoint_cadence.py'
    contract.require(pin(cadence)['sha256']=='a017eded18ca03733700fd61b10cace8981e5379e73dbe99b4d281fb97e4ae87','actual cadence changed')
    tree=ast.parse(cadence.read_bytes())
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('_scope','checkpoint_saved')]
    ns={'STATE_KEY':'checkpoint_calendar_v1'}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-cadence-extracted','exec'),ns)
    a={'machine_id':contract.MACHINE,'frontier':pin(F/'SAVE6397-FRONTIER-DRAFT.json'),
       'historical_tail':pin(F/'POST-SAVE6397-HISTORICAL-TAIL234.json'),'interruption':pin(F/'FROZEN.json')}
    seed,gov=contract.project_saved_frontier(a,checkpoint_saved=ns['checkpoint_saved'])
    contract.validate_rollback(a,seed,gov,checkpoint_saved=ns['checkpoint_saved'])
    closure=contract.validate_abnormal_closure(a)
    contract.require(seed['completed_cycles']==gov['completed_cycles']==3039 and seed['pending_cycle'] is None
        and gov['pending_cycle'] is None and seed['counts']['checkpoint_saved']==35
        and seed['before']['date_raw']==53202720 and seed['checkpoint_dirty_since_save'] is False
        and seed['checkpoint_due_after_readonly_chain'] is False and seed['actual_saved_checkpoint']['sha256']==contract.SAVE_SHA,
        'saved current state failed')
    bad=copy.deepcopy(seed);bad['completed_cycles']=3273
    try:contract.validate_rollback(a,bad,gov,checkpoint_saved=ns['checkpoint_saved'])
    except ValueError:pass
    else:raise ValueError('future counts accepted')
    bad=copy.deepcopy(a)
    source=json.loads((F/'SAVE6397-FRONTIER-DRAFT.json').read_bytes())['sources']['CUM3039']
    bad['relocated_sources']={'CUM3039':{**source,'sha256':'0'*64}}
    try:contract.project_saved_frontier(bad,checkpoint_saved=ns['checkpoint_saved'])
    except ValueError:pass
    else:raise ValueError('wrong saved-turn pin accepted')
    report={'schema':'xar.SAVE6397-frontier-source-qualification/v1','machine_id':contract.MACHINE,
      'observed_at_utc':datetime.now(timezone.utc).isoformat(),'machine_id_source':'tools/ck3_live_run_id.py machine, chunk01de0e',
      'status':'SOURCE_FRONTIER_READY_NOT_RUNTIME_ADMITTED','source':pin(Path(contract.__file__)),
      'qualifier':pin(Path(__file__)),'actual_cadence':pin(cadence),'inputs':a,
      'cases':['actual saved3039/directSAVE6397 source reconstruction + actual cadence PASS',
               'future3273 current credit rejected','wrong CUM3039 identity pin rejected'],
      'restored_current':{'cycles':3039,'day':2433,'date_raw':53202720,'counted_cadence_saves':35,
        'maintenance_SAVE6397_adopted_separately':True,'save_history_index':2083},
      'historical_only':{'cycles':3273,'day':2504,'tail_cycles':234,'tail_days':71,
        'unknown_AUTO6874_replay':False,'tail_event6710_current_credit':False},
      'closure':closure,'scope':{'new_Game_Native_RPC_calls':0,'Driver_or_SAVE_bodies_read':False,
        'D_writes':0,'old_controller_or_contract_changed':False,'sidecars_or_durable_owner_qualified':False}}
    out=Path('_runtime/checkpoint6397-frontier-qualified90.json')
    with out.open('xb') as f:f.write(json.dumps(report,indent=2).encode())
    print(json.dumps(pin(out)))
if __name__=='__main__':main()
