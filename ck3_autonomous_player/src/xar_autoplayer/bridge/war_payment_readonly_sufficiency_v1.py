"""Prevent a cash-rate/raw-context reading from becoming a paid-ledger claim.

Pure assessment of already validated exact .4 current-cash DTOs. No query,
sampling, Driver, game, source locator, or payment attribution is performed.
Equal numeric readings are not a producer/transaction/cadence proof.
"""
from collections.abc import Mapping

MASK=(1<<64)-1
EXE='98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518'

def assess_readonly_maintenance_sufficiency_v1(current):
    if not isinstance(current,Mapping) or current.get('game_version')!='1.20.0.4' or str(current.get('executable_sha256','')).lower()!=EXE:
        raise ValueError('Exact .4 validated current cash DTO required')
    def fixed(key):
        v=current.get(key)
        return v['raw'] if isinstance(v,Mapping) and type(v.get('raw')) is int and v.get('scale')==100000 else None
    def expense(kind):
        v=(current.get('military_expenses') or {}).get(kind) or {}
        return v['gold_raw'] if v.get('status')=='available' and v.get('raw_scale')==100000 and type(v.get('gold_raw')) is int else None
    raw=current.get('current_raw_context_v1') or {};values=raw.get('values') or {}
    frame=(raw.get('observation_kind')=='paused_current_raw_context'
        and raw.get('attribution_scope')=='current_raw_context_only' and raw.get('maintenance_attribution')=='unclosed'
        and raw.get('admission_ready') is True and raw.get('same_frame_ready') is True
        and raw.get('character_full_id')==current.get('played_character_id')
        and raw.get('snapshot_revision')==current.get('snapshot_revision')
        and raw.get('date_raw')==current.get('date_raw')
        and values.get('capture_complete') is True and values.get('context_stable') is True
        and values.get('failed_reads')==0)
    terms=[values.get(k) for k in ('value_2c0','value_2c8','value_28','value_30')]
    complete=frame and all(type(v) is int and -(1<<63)<=v<(1<<63) for v in terms)
    wrap=lambda x:((x+(1<<63))&MASK)-(1<<63)
    a,b,c,d=terms if complete else [None]*4
    formula=wrap(a-b-(c+d)) if complete else None
    total=wrap(c+d) if complete else None
    gross,expenses,net=fixed('player_monthly_gross_income'),fixed('player_monthly_total_expenses'),fixed('player_monthly_net_income')
    current_rate,all_raised=expense('current'),expense('all_raised')
    eq=lambda x,y: x==y if x is not None and y is not None else None
    return {'schema':'xar.war-payment-readonly-sufficiency.v1','date_raw':current.get('date_raw'),
        'character_full_id':current.get('played_character_id'),'snapshot_revision':current.get('snapshot_revision'),
        'raw_context_qualified':bool(complete),'four_raw':[a,b,c,d],'raw_c_plus_d':total,'raw_formula_net':formula,
        'raw_term_scale':None,'raw_term_time_basis':None,'getter_scale':100000,'getter_time_basis':'month',
        'getters':{'gross':gross,'total_expenses':expenses,'net':net,'current_military_gold':current_rate,'all_raised_military_gold':all_raised},
        'literal_value_equal':{'c_to_current_military':eq(c,current_rate),'c_plus_d_to_current_military':eq(total,current_rate),
            'raw_formula_to_monthly_net':eq(formula,net),'a_to_gross':eq(a,gross),'b_to_total_expenses':eq(b,expenses)},
        'literal_comparison_establishes_units_or_producer':False,
        'maintenance_attribution':'unclosed','military_paid_raw':None,'military_payer':None,'cadence':None,
        'may_substitute_c_or_c_plus_d_for_current_military':False,'may_substitute_four_raw_formula_for_monthly_net':False,
        'may_infer_paid_from_rate_or_net_or_owner':False,
        'reason':'Existing DTO has rates/raw readings, not military producer, same-settlement application, payer or calendar selection evidence.'}
