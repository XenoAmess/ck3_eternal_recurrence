import asyncio,copy,json
from pathlib import Path
from unittest import mock
import pytest
from test_army_profile_cache_regression import make_scenario,CORE,FULL,PROFILE,COVERAGE,STEP
from test_native_bridge_driver import _hello,_army_strength
from xar_autoplayer.bridge.driver import BridgeUnavailableError,UnsupportedStepError
from xar_autoplayer.bridge.army_strengths_profile_contract import OBSERVED_PHASE_KEYS
from xar_autoplayer.bridge.army_query_history_reference import read_army_query_history_reference

CAP='game.command.query-army-strengths-scoped-v1'

def scenario(tmp_path, *, mutation=None, published_status='partial', unavailable=False):
    with mock.patch('test_army_profile_cache_regression._hello',side_effect=lambda *args:_hello(*args,CAP)):
        value=make_scenario(tmp_path/'state')
    value.driver.army_query_history_sidecar_limit_bytes=16*1024*1024
    def answer(frame):
        if frame.get('type')!='execute_step':return
        ids=frame.get('army_ids');assert ids is not None
        rows=[]
        for army_id in ids:
            row=_army_strength(army_id,'player',[45,46] if army_id==81 else [],status='unavailable' if unavailable else 'available')
            if frame[PROFILE]==FULL:row.update({key:None for key in OBSERVED_PHASE_KEYS})
            rows.append(row)
        result={'step':STEP,'accepted':True,'status':'partial' if unavailable else 'available',
                'query_sequence':3,'army_strengths':rows,PROFILE:frame[PROFILE],
                COVERAGE:'exported_retained' if frame[PROFILE]==FULL else 'not_requested',
                'army_strengths_query_scope':{'army_ids':ids,'published_scope_status':published_status}}
        if mutation:mutation(result)
        value.endpoint.publish({'type':'command_result','protocol_version':1,'request_id':frame['request_id'],'ok':True,'result':result})
    value.endpoint.send_hook=answer
    return value

@pytest.mark.parametrize('profile',[CORE,FULL])
def test_scoped_real_driver_uses_native_scope_before_recording_and_does_not_poison_cache(tmp_path,profile):
    value=scenario(tmp_path)
    try:
        result=value.driver.query_scoped_army_strengths([81],profile=profile,expected_revision=value.before['revision'])
        assert value.endpoint.frames[-1]['army_ids']==[81]
        assert [r['army_id'] for r in result['army_strengths']]==[81]
        assert result['army_strengths_query_scope']=={'army_ids':[81],'published_scope_status':'partial'}
        assert result['status']=='available' # selected status never blesses published scope
        assert value.driver._army_strength_query is None
        assert value.driver.take_snapshot()['army_strengths']==[]
        recorded=value.driver._command_history[-1]
        assert recorded['ok'] is True
        # History is a real finite evidence reference, never an invented summary.
        summary=recorded['result']
        actual,_=read_army_query_history_reference(summary,evidence_dir=Path(summary['raw_result_reference']['path']).parent,maximum_bytes=16*1024*1024)
        assert actual==result and [r['army_id'] for r in actual['army_strengths']]==[81]
    finally:value.driver.close()

@pytest.mark.parametrize('profile',[CORE,FULL])
def test_real_service_scopes_at_native_export_and_preserves_published_partial(tmp_path,profile):
    from xar_autoplayer.bridge.service import GameplayBridgeService
    value=scenario(tmp_path)
    try:
        result=GameplayBridgeService(value.driver).query_army_strengths([81],profile=profile,expected_revision=value.before['revision'])
        assert value.endpoint.frames[-1]['army_ids']==[81]
        assert result['army_ids']==[81] and result['scope_army_ids']==[82,81]
        assert result['status']=='available' and result['scope_status']=='partial'
        assert len(result['army_strengths'])==1 and result['army_strengths'][0]['army_id']==81
    finally:value.driver.close()

def test_registered_mcp_scoped_route_reaches_real_driver_once(tmp_path):
    from xar_autoplayer.bridge.mcp_server import create_server
    value=scenario(tmp_path)
    try:
        response=asyncio.run(create_server(value.driver).call_tool('ck3_query_army_strengths',{'army_ids':[81],'profile':FULL,'expected_revision':value.before['revision']}))
        assert response.is_error is False
        assert value.endpoint.frames[-1]['army_ids']==[81]
        assert len([frame for frame in value.endpoint.frames if frame.get('type')=='execute_step'])==1
    finally:value.driver.close()

def test_unavailable_selected_row_keeps_partial_through_driver_and_service(tmp_path):
    from xar_autoplayer.bridge.service import GameplayBridgeService
    value=scenario(tmp_path,unavailable=True)
    try:
        result=GameplayBridgeService(value.driver).query_army_strengths([81],expected_revision=value.before['revision'])
        assert result['status']=='partial' and result['scope_status']=='partial'
        assert result['army_strengths'][0]['status']=='unavailable'
        assert result['army_strengths'][0]['current_soldiers'] is None
        assert result['army_strengths'][0]['unavailable_reason']=='regiment_generation_mismatch'
    finally:value.driver.close()

def test_requested_order_not_published_order_is_retained(tmp_path):
    value=scenario(tmp_path)
    try:
        result=value.driver.query_scoped_army_strengths([81,82],expected_revision=value.before['revision'])
        assert [r['army_id'] for r in result['army_strengths']]==[81,82]
    finally:value.driver.close()

@pytest.mark.parametrize('ids',[[81,81],[],[True],[-1],[2**31],list(range(65))])
def test_malformed_scope_never_reaches_native(tmp_path,ids):
    value=scenario(tmp_path)
    try:
        count=len(value.endpoint.frames)
        with pytest.raises(ValueError):value.driver.query_scoped_army_strengths(ids)
        assert len(value.endpoint.frames)==count
    finally:value.driver.close()

def test_outside_published_scope_and_missing_capability_do_not_fallback(tmp_path):
    value=scenario(tmp_path)
    try:
        count=len(value.endpoint.frames)
        with pytest.raises(BridgeUnavailableError,match='outside'):value.driver.query_scoped_army_strengths([83])
        assert len(value.endpoint.frames)==count
    finally:value.driver.close()
    value=make_scenario(tmp_path/'old')
    try:
        count=len(value.endpoint.frames)
        with pytest.raises(UnsupportedStepError):value.driver.query_scoped_army_strengths([81])
        assert len(value.endpoint.frames)==count
    finally:value.driver.close()

@pytest.mark.parametrize('mutation',[
    lambda r:r.pop('army_strengths_query_scope'),
    lambda r:r['army_strengths_query_scope'].update(army_ids=[82]),
    lambda r:r['army_strengths_query_scope'].update(army_ids=[81.0]),
    lambda r:r['army_strengths_query_scope'].update(published_scope_status='available_all'),
    lambda r:r['army_strengths_query_scope'].update(extra=True),
    lambda r:r['army_strengths'].append(_army_strength(82,'player',[])),
    lambda r:r.update(army_strengths=[]),
    lambda r:r.update(status='partial'),
])
def test_bad_echo_extra_missing_rows_or_disagreeing_selected_status_remains_failure(tmp_path,mutation):
    value=scenario(tmp_path,mutation=mutation)
    try:
        with pytest.raises(BridgeUnavailableError):value.driver.query_scoped_army_strengths([81])
        assert value.driver._army_strength_query is None
        assert value.driver._command_history[-1]['ok'] is False
        assert len([f for f in value.endpoint.frames if f.get('type')=='execute_step'])==1
    finally:value.driver.close()

def test_all_published_scope_changes_still_invalidate_scoped_query(tmp_path):
    value=scenario(tmp_path);old=value.driver.take_internal_semantic_snapshot;sent=False
    original_answer=value.endpoint.send_hook
    def answer(frame):
        nonlocal sent
        original_answer(frame);sent=True
    def current():
        snap=old()
        if sent:
            snap=copy.deepcopy(snap);snap['player_armies'].reverse()
        return snap
    value.endpoint.send_hook=answer
    try:
        with mock.patch.object(value.driver,'take_internal_semantic_snapshot',side_effect=current):
            with pytest.raises(BridgeUnavailableError,match='scope changed'):
                value.driver.query_scoped_army_strengths([81])
        assert value.driver._command_history[-1]['ok'] is False
    finally:value.driver.close()
