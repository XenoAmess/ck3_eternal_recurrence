"""Pure, explicitly frozen C hold after first arrival; no native calls."""
from copy import deepcopy
import importlib.util
from pathlib import Path

POLICY = 'hold-arrival-position-until-day90'


def _adapter(value):
    if value is not None:
        return value
    path = Path(__file__).with_name('strategy_c_next_decision.py')
    spec = importlib.util.spec_from_file_location('_C_horizon_existing_adapter', path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def check_saved_state(plan, state, *, adapter=None):
    a = _adapter(adapter)
    c = a.c
    c.need(plan.get('status') == 'frozen' and plan.get('follow_after_arrival_to_day90') is True
           and plan.get('post_arrival_policy') == POLICY, 'freeze the explicit C hold-until-day90 policy')
    destinations = c.targets(plan)
    c.need(state.get('phase') == 'arrived' and state.get('target_index') == len(destinations),
           'common horizon requires original arrived terminal state')
    arrivals = state.get('arrivals')
    c.need(isinstance(arrivals, list) and [r.get('province_id') for r in arrivals] == destinations
           and arrivals[-1]['day'] <= state['last_day'] <= 90, 'complete original C first arrivals are required')
    anchor = state.get('common_horizon_anchor')
    c.need(isinstance(anchor, dict) and anchor.get('first_arrivals') == arrivals
           and anchor.get('targets') == destinations, 'missing/changed first-arrival anchor; no historical backfill')
    return a


def _data(a, plan, observation):
    a._whole_data(plan, observation)
    ep = observation['endpoint']
    return {'army_id': ep['units'][0]['army_id'],
            'native_carmy_id': observation['binding']['native_carmy_id'],
            'groups': [{'army_regiment_id': row['army_regiment_id'],
                'native_data_record_count': row['native_data_record_count'],
                'records': [[record.get(k) for k in ('record_index', 'persistent_regiment_id',
                    'chunk_index', 'maximum_soldiers', 'chunk_army_regiment_id')]
                    for record in row['records']]} for row in ep['DATA']]}


def bind_first_arrival(plan, previous, arrived, observation, *, adapter=None):
    """Only the actual marching-to-arrived transition may create the anchor."""
    a = _adapter(adapter)
    c = a.c
    ep, unit, binding = c._valid_observation(plan, observation)
    c._same_subject(previous, ep, unit, binding)
    c.need(previous['phase'] == 'marching' and arrived['phase'] == 'arrived'
           and 'common_horizon_anchor' not in arrived
           and ep['day'] == arrived['last_day'] == previous['last_day']+1
           and arrived['arrivals'][:-1] == previous['arrivals']
           and arrived['arrivals'][-1]['day'] == ep['day'], 'anchor only on actual first final arrival')
    generation = c._clock(previous, observation)
    c.need(arrived['binding'] == binding and arrived['last_clock_generation'] == generation,
           'first arrival state must retain this exact actual frame and clock')
    c.need(c._stationary_at(unit, plan['goal_province_id'], plan['arrival_states']),
           'first arrival must actually be stationary at the frozen goal')
    new = deepcopy(arrived)
    new['common_horizon_anchor'] = {'first_arrivals': deepcopy(arrived['arrivals']),
        'targets': c.targets(plan), 'data_identity_max': _data(a, plan, observation),
        'first_arrival_binding': deepcopy(binding)}
    check_saved_state(plan, new, adapter=a)
    return new


def _current(plan, state, observation, adapter):
    a = check_saved_state(plan, state, adapter=adapter)
    c = a.c
    ep, unit, binding = c._valid_observation(plan, observation)
    c._same_subject(state, ep, unit, binding)
    c.need(c._stationary_at(unit, plan['goal_province_id'], plan['arrival_states']),
           'C common horizon cannot move away from the actual arrival position')
    c.need(_data(a, plan, observation) == state['common_horizon_anchor']['data_identity_max'],
           'whole DATA identity/order/max changed after first arrival')
    return c, ep, binding


def read_common_horizon_endpoint(plan, state, observation, *, adapter=None):
    c, ep, binding = _current(plan, state, observation, adapter)
    c.need(ep['day'] == state['last_day'], 'readonly common endpoint must remain on the same day')
    new = deepcopy(state)
    new['binding'] = deepcopy(binding)
    return new


def observe_common_horizon(plan, state, observation, *, adapter=None):
    c, ep, binding = _current(plan, state, observation, adapter)
    c.need(ep['day'] == state['last_day']+1, 'common horizon requires exactly the next natural day')
    generation = c._clock(state, observation)
    new = deepcopy(state)
    new.update(last_day=ep['day'], last_clock_generation=generation, binding=deepcopy(binding))
    return new
