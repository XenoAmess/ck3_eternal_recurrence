"""Synthetic paused-cash envelopes through the existing production consumer/query.

No wallet callback is constructed. These cases grant no native/runtime credit.
"""
from __future__ import annotations
import copy
import json
from pathlib import Path
import sys
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT.parent),str(ROOT/'src')]
from xar_autoplayer.bridge import war_cash_private_transport_v1 as cash
from xar_autoplayer.bridge.version_identity import CK3_12002,CK3_12003,CK3_12004

KEY='current_raw_context_v1'
F=ROOT/'native_bridge/research/fixtures/ck3_12002_war_cash_current-resources-normal.json'
LEGACY=json.loads(F.read_text(encoding='utf-8'))

def require(ok,message):
    if not ok:raise RuntimeError(message)

def current(*,leaf=True,build=CK3_12004):
    value=copy.deepcopy(LEGACY)
    value.update(game_version=build.game_version,executable_sha256=build.executable_sha256)
    value['readiness']['same_frame_ready']=True
    if leaf:
        value[KEY]=dict(schema_version=1,observation_kind='paused_current_raw_context',attribution_scope='current_raw_context_only',
            maintenance_attribution='unclosed',character=0x100000,character_full_id=value['played_character_id'],
            snapshot_revision=value['snapshot_revision'],date_raw=value['date_raw'],actor_identity_stable=True,same_frame_ready=True,
            values=dict(context_identity_before=0x300000,context_identity_after=0x300000,value_2c0=0,value_2c8=0,value_28=0,value_30=0,
                capture_complete=True,context_stable=True,failed_reads=0),admission_ready=True,unavailable_reason=None)
    return value

def snapshot(value):
    return dict(paused=True,map_ready=True,revision=value['snapshot_revision']+1,native_revision=value['snapshot_revision'],
        snapshot_id='synthetic-current-cash-frame',date_raw=value['date_raw'],played_character=dict(character_id=value['played_character_id'],alive=True),
        diagnostics=dict(hello=dict(expected_ck3_version=value['game_version'],expected_ck3_sha256=value['executable_sha256'])))

@pytest.mark.parametrize('build',[CK3_12002,CK3_12003,CK3_12004],ids=['legacy.2','legacy.3','legacy.4'])
def test_absent_optional_leaf_preserves_existing_wire(build):
    value=current(leaf=False,build=build);original=copy.deepcopy(value)
    result=cash.normalize_war_cash_current_resources_v1(value,snapshot=snapshot(value))
    require(result==original and value==original and result is not value,'Legacy/defaultOFF cash wire changed')
    require(KEY not in result,'Absent raw leaf was manufactured')

def incomplete(value):
    raw=value[KEY];raw['values'].update(value_2c8=None,failed_reads=1,capture_complete=False)
    raw.update(admission_ready=False,unavailable_reason='war_cash_current_raw_context_incomplete')
def changed_pointer(value):
    raw=value[KEY];raw['values'].update(context_identity_after=0x400000,context_stable=False,capture_complete=False)
    raw.update(admission_ready=False,unavailable_reason='war_cash_current_raw_context_incomplete')
def null_context(value):
    raw=value[KEY];raw['values'].update(context_identity_before=0,context_identity_after=0,value_2c0=None,value_2c8=None,value_28=None,value_30=None,
        context_stable=False,capture_complete=False)
    raw.update(admission_ready=False,unavailable_reason='war_cash_current_raw_context_incomplete')
def unaligned(value):
    raw=value[KEY];raw['values'].update(context_identity_before=0x300001,context_identity_after=0x300001)
    raw.update(admission_ready=False,unavailable_reason='war_cash_current_raw_context_unaligned_or_overflow')
def frame_unqualified(value):
    value['readiness']['same_frame_ready']=False
    value[KEY].update(same_frame_ready=False,admission_ready=False,unavailable_reason='war_cash_current_raw_context_frame_unqualified')
def signed_values(value):
    value[KEY]['values'].update(value_2c0=-(1<<63),value_2c8=(1<<63)-1,value_28=-1,value_30=0)

@pytest.mark.parametrize('change',[lambda v:None,incomplete,changed_pointer,null_context,unaligned,frame_unqualified,signed_values],
    ids=['observed_zero','failed_read','changed_context','null_context','unaligned_diagnostic','frame_diagnostic','signed64_boundaries'])
def test_fresh_raw_diagnostics_round_trip_without_callback(change):
    value=current();change(value);original=copy.deepcopy(value)
    result=cash.normalize_war_cash_current_resources_v1(value,snapshot=snapshot(value))
    require(result==original and value==original,'Raw diagnostics changed')
    require(result[KEY]['maintenance_attribution']=='unclosed','Raw read promoted business attribution')
    require('generic_wallet_context_v1' not in result and 'war_payment_observations_v1' not in result,'Fake callback created')

def negative_cases():
    result=[]
    def add(name,change):result.append(pytest.param(change,id=name))
    add('leaf_null',lambda v:v.update({KEY:None}))
    add('leaf_scalar',lambda v:v.update({KEY:0}))
    for key in current()[KEY]:add('missing_leaf:'+key,lambda v,k=key:v[KEY].pop(k))
    for key in ('amount_raw','caller_return_rva','parent_trace','before_formula_matches_amount','pid','session_epoch'):
        add('forbidden_extra:'+key,lambda v,k=key:v[KEY].update({k:1}))
    for key,value in (('schema_version',True),('schema_version',2),('observation_kind','wallet_callback'),('attribution_scope','military'),
        ('maintenance_attribution','closed'),('character',0),('character',True),('character',-1),('character',1<<64),
        ('character_full_id',0),('character_full_id',True),('character_full_id',1<<31),('character_full_id',999999),
        ('snapshot_revision',True),('snapshot_revision',1<<64),('snapshot_revision',999999),('date_raw',True),('date_raw',1<<31),('date_raw',-999999),
        ('actor_identity_stable',False),('actor_identity_stable',1),('same_frame_ready',1),('same_frame_ready',False),
        ('admission_ready',1),('admission_ready',False),('unavailable_reason','invented')):
        add('malformed_leaf:'+key+':'+repr(value),lambda v,k=key,x=value:v[KEY].update({k:x}))
    for key in current()[KEY]['values']:add('missing_value:'+key,lambda v,k=key:v[KEY]['values'].pop(k))
    add('extra_value',lambda v:v[KEY]['values'].update(scale=100000))
    add('values_null',lambda v:v[KEY].update(values=None))
    for key,value in (('context_identity_before',True),('context_identity_after',1<<64),('value_2c0',True),('value_2c8',1<<63),
        ('value_28',-(1<<63)-1),('value_30',0.0),('capture_complete',1),('context_stable',1),('failed_reads',1<<32),
        ('capture_complete',False),('context_stable',False),('failed_reads',1)):
        add('malformed_value:'+key+':'+repr(value),lambda v,k=key,x=value:v[KEY]['values'].update({k:x}))
    add('null_pointer_with_values',lambda v:v[KEY]['values'].update(context_identity_before=None,context_stable=False,capture_complete=False))
    add('changed_pointer_still_admitted',lambda v:v[KEY]['values'].update(context_identity_after=0x400000,context_stable=False,capture_complete=False))
    add('unaligned_still_admitted',lambda v:v[KEY]['values'].update(context_identity_before=0x300001,context_identity_after=0x300001))
    add('overflow_still_admitted',lambda v:v[KEY]['values'].update(context_identity_before=(1<<64)-0x100,context_identity_after=(1<<64)-0x100))
    add('wrong_readiness_type',lambda v:v['readiness'].update(same_frame_ready=1))
    return result

@pytest.mark.parametrize('change',negative_cases())
def test_rejects_wrong_raw_frame_or_fabricated_callback(change):
    value=current();change(value)
    with pytest.raises(ValueError):cash.normalize_war_cash_current_resources_v1(value,snapshot=snapshot(value))

@pytest.mark.parametrize('change',[lambda s:s.update(paused=False),lambda s:s.update(map_ready=False),lambda s:s['played_character'].update(alive=False)],
    ids=['unpaused','map_unready','dead_actor'])
def test_rejects_admission_against_unqualified_snapshot(change):
    value=current();state=snapshot(value);change(state)
    with pytest.raises(ValueError):cash.normalize_war_cash_current_resources_v1(value,snapshot=state)

def test_leaf_cannot_be_relabeled_as_legacy_build():
    value=current(build=CK3_12003)
    with pytest.raises(ValueError):cash.normalize_war_cash_current_resources_v1(value,snapshot=snapshot(value))

class Driver:
    allow_private_war_cash_query=True
    command_timeout_seconds=1.0
    def __init__(self,value):self.value=value;self.endpoint=self.state=self;self.requests=[];self.frame=snapshot(value)
    def take_snapshot(self):return copy.deepcopy(self.frame)
    def take_snapshot_without_native_command_history(self):return self.take_snapshot()
    def send(self,request):self.requests.append(copy.deepcopy(request))
    def wait_for_command_result(self,request_id,timeout):
        return dict(type='command_result',protocol_version=1,request_id=request_id,ok=True,
            result=dict(step=cash.CURRENT_STEP,accepted=True,private_build=True,read_only=True,advertised=False,war_cash_current_resources=copy.deepcopy(self.value)))

def test_existing_query_returns_fresh_leaf_once_without_new_request_fields():
    value=current();driver=Driver(value)
    result=cash.query_war_cash_current_resources_private_v1(driver,expected_revision=driver.frame['revision'])
    require(result[KEY]==value[KEY] and len(driver.requests)==1,'Existing cash query lost raw leaf or retried')
    require(driver.requests[0]['step']==cash.CURRENT_STEP,'New query was introduced')
    require(not any(key.startswith('war_payment_') for key in driver.requests[0]),'Fake callback/control request introduced')
    require(result['queried_native_revision']==value['snapshot_revision'],'Existing query frame binding changed')
