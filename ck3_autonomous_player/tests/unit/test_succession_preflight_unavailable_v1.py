"""Source-bound unavailable observations never freeze an estate or execute a plan."""
from __future__ import annotations

import copy
from types import SimpleNamespace

import pytest

import xar_autoplayer.bridge.service as service_module
from xar_autoplayer.bridge.campaign_root_context_contract import QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.succession_preflight_unavailable_v1 import observe_unavailable_preflight_v1
from xar_autoplayer.bridge.turn_bundle_contract import build_turn_bundle_v1


def frame():
    return {'snapshot_id':'native:82','revision':7,'native_revision':82,'date_raw':12000,
            'paused':True,'map_ready':True,'played_character':{'character_id':101,'alive':True},
            'episode_run_id':'offline-101','diagnostics':{'bridge_pid':55,'connection_generation':2},
            'native_command_history':[],'one_life_terminal_reason':None}


def unavailable(snapshot):
    return build_turn_bundle_v1(snapshot, {
        'status':'unavailable','query_sequence':9,
        'binding':{k:snapshot[k] for k in ('snapshot_id','revision','native_revision','date_raw')},
        'campaign_root_context':{'status':'unavailable','snapshot_revision':snapshot['native_revision'],
            'date_raw':snapshot['date_raw'],'unavailable_reason':'adjacent_external_province_holders_unavailable'}})


class FakeService(GameplayBridgeService):
    def __init__(self, snapshot):
        self.current=copy.deepcopy(snapshot)
        self.queries=self.retains=self.executions=0
        self.driver=SimpleNamespace(
            retain_succession_expectation_v1=self.retain,
            reconcile_retained_succession_transition_v1=lambda *a,**k:None,
            take_internal_semantic_snapshot=lambda:copy.deepcopy(self.current),
            _with_internal_planning_view=lambda *a:None,
            require_initial_lifestyle_focus_before_date_advance=True)

    def retain(self,*args,**kwargs):
        self.retains+=1

    def query_turn_bundle_v1(self,**kwargs):
        self.queries+=1
        return unavailable(self.current)

    def capabilities(self):
        return {}

    def plan_turn(self):
        return self._plan_turn_internal()

    def _execute_planned_turn(self,*args,**kwargs):
        self.executions+=1
        raise AssertionError('unavailable preflight must not dispatch')


def test_actual_service_defer_is_readonly_and_next_turn_requeries(monkeypatch):
    monkeypatch.setattr(service_module,'action_step_set',lambda _: {QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP})
    service=FakeService(frame())
    body=service.auto_turn(before_submit=lambda *_:pytest.fail('no submission hook'))
    assert body['status']=='readonly_unavailable' and body['selected_step'] is None
    assert body['result']['unavailable_reason']=='adjacent_external_province_holders_unavailable'
    assert body['result']['binding']==body['planning_source_frame']
    assert service.queries==1 and service.retains==service.executions==0
    assert service.auto_turn()['status']=='readonly_unavailable'
    assert service.queries==2 and service.retains==service.executions==0


@pytest.mark.parametrize('field,value',[
    ('schema','unknown'),('unavailable_reason',''),('source',{'query_sequence':9}),
    ('binding',{'snapshot_id':'different'}),
])
def test_unknown_or_cross_frame_cannot_be_a_defer(field,value):
    snapshot=frame();bundle=unavailable(snapshot);bundle[field]=value
    with pytest.raises(ValueError):
        observe_unavailable_preflight_v1(bundle,snapshot,GameplayBridgeService._observed_planning_source_frame(snapshot))


@pytest.mark.parametrize('field,value',[
    ('paused',False),('map_ready',False),('one_life_terminal_reason','played_character_changed'),
    ('active_event',{'instance_id':1}),('pending_character_interaction',{'instance_id':2}),
])
def test_defer_never_waives_live_frame_or_successor_handoff(field,value):
    snapshot=frame();bundle=unavailable(snapshot);snapshot[field]=value
    with pytest.raises(ValueError):
        observe_unavailable_preflight_v1(bundle,snapshot,GameplayBridgeService._observed_planning_source_frame(snapshot))
