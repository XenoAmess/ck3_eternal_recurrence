"""New consumer/transport focus over actual compiled serialized payment bytes."""
from __future__ import annotations
import asyncio,copy,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(R),str(R/'ck3_autonomous_player/src')]
import pytest
from mcp.server.mcpserver.exceptions import ToolError
from xar_autoplayer.bridge import war_payment_observations_v1 as payment
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.bridge.war_cash_private_transport_v1 import CURRENT_STEP

F=Path(__file__).with_name('fixtures')/'war_payment_compiled_12004_a06.json'
CASES={r['case']:r['value'].get(payment.JOURNAL_KEY,r['value']) for r in json.loads(F.read_text(encoding='utf-8'))}


def snapshot(j):
    s=j['current_session'];date=s['native_date_raw']&0xffffffff
    if date>=1<<31:date-=1<<32
    return dict(paused=True,map_ready=True,revision=s['snapshot_revision']+1,
        native_revision=s['snapshot_revision'],date_raw=date,snapshot_id='synthetic-cash-payment:'+str(s['snapshot_revision']),
        played_character=dict(character_id=s['player_character_full_id'],alive=True),
        diagnostics=dict(bridge_pid=s['pid'],connection_generation=s['connection_generation'],
            hello=dict(expected_ck3_version=CK3_12004.game_version,expected_ck3_sha256=CK3_12004.executable_sha256)))


class Driver:
    allow_private_war_cash_query=True
    command_timeout_seconds=1.0
    query_war_cash_current_resources_private_v1=NativeHeadlessGameplayDriver.query_war_cash_current_resources_private_v1

    def __init__(self,j):
        self.j=copy.deepcopy(j);self.snapshot=snapshot(j);self.requests=[];self.endpoint=self.state=self
        # This legacy cash object is an explicitly synthetic envelope, not .4
        # native cash validation. Payment records remain compiled fixture bytes.
        p=R/'ck3_autonomous_player/native_bridge/research/fixtures/ck3_12002_war_cash_current-resources-normal.json'
        self.cash=json.loads(p.read_text(encoding='utf-8'))
        self.cash.update(game_version=CK3_12004.game_version,executable_sha256=CK3_12004.executable_sha256,
            played_character_id=self.snapshot['played_character']['character_id'],
            snapshot_revision=self.snapshot['native_revision'],date_raw=self.snapshot['date_raw'])
        for row in self.cash['military_expenses'].values():
            row.update(owner_character_id=self.cash['played_character_id'],resource_id=str(self.cash['played_character_id']))
        self.extra={}

    def take_snapshot(self):return copy.deepcopy(self.snapshot)
    def take_snapshot_without_native_command_history(self):return self.take_snapshot()
    def send(self,request):self.requests.append(copy.deepcopy(request))
    def wait_for_command_result(self,request_id,timeout):
        return dict(type='command_result',protocol_version=1,request_id=request_id,ok=True,
            result=dict(step=CURRENT_STEP,accepted=True,status=self.cash['status'],private_build=True,
                read_only=True,advertised=False,war_cash_current_resources=copy.deepcopy(self.cash),**copy.deepcopy(self.extra)))


def test_new_compiled_payment_consumer_and_registered_transport_focus(monkeypatch):
    from tools import ck3_live_run_id
    machine=CASES['controlled_window_personal']['machine_id']
    monkeypatch.setattr(ck3_live_run_id,'current_machine_id',lambda override=None:machine)
    # Nine unchanged compiled serializer cases, including absent parent and positive land,
    # zero/negative raw amounts and generic signed resource arguments. No source
    # execution or replay of B's older qualification tests occurs here.
    for name,j in CASES.items():
        assert payment.normalize_journal(j,snapshot=snapshot(j),machine_id=machine)==j,name
    j=copy.deepcopy(CASES['controlled_window_personal'])
    good=snapshot(j)
    # High date bits survive unchanged; only low32 binds to native snapshot.
    high=copy.deepcopy(j);high['current_session']['native_date_raw']|=7<<32
    assert payment.normalize_journal(high,snapshot=good,machine_id=machine)==high
    # Reject invented debit qualifications even if the native claim boolean says
    # true. Mutate raw evidence while leaving the asserted debit vector intact.
    corruptions=[
        lambda x:x['records'][0].update(amount_raw=0),
        lambda x:x['records'][0].update(amount_raw=-1),
        lambda x:x['records'][0].update(amount_raw=True),
        lambda x:x['records'][0]['after'].update(wrapper_balance_bits=123),
        lambda x:x['records'][0]['parent_gateway_entry'].update(sequence=999),
        lambda x:x['records'][0]['session_return'].update(connection_generation=99),
        lambda x:x['records'][0]['returned_event'].update(clock_identity=999),
        lambda x:x['natural_parent_returns'][0].update(original_returned=False),
        lambda x:x['natural_parent_returns'][0].update(returned_date_raw=1),
        lambda x:x['natural_parent_returns'][0].update(returned_absolute_day_raw=1),
        lambda x:x.update(install_failure_flags=1),
        lambda x:x.update(overwritten=1),
        lambda x:x.update(publication_failures=1),
        lambda x:x['sampling'].update(busy=True,active_captures=1),
        lambda x:x['records'][1].update(journal_sequence=1),
        lambda x:x['qualified_boarding_debits'].append(copy.deepcopy(x['qualified_boarding_debits'][0])),
        lambda x:x['qualified_boarding_debits'][0].update(requested_amount_raw=500001),
        lambda x:x['current_session'].update(pid=999),
        lambda x:x['current_session'].update(native_date_raw=1),
        lambda x:x.update(machine_id='wrong-machine'),
    ]
    for change in corruptions:
        bad=copy.deepcopy(j);change(bad)
        with pytest.raises(ValueError):payment.normalize_journal(bad,snapshot=good,machine_id=machine)
    # Incomplete capture retains real counts; empty raw vector does not acquire
    # zero-observation meaning or become an accepted boarding debit.
    busy=copy.deepcopy(j);busy.update(read_complete=False,records=[],qualified_boarding_debits=[])
    busy['sampling'].update(busy=True,active_captures=1)
    assert payment.normalize_journal(busy,snapshot=good,machine_id=machine)==busy

    driver=Driver(j);server=create_server(driver)
    tool='ck3_query_war_cash_current_resources_private_v1'
    revision=driver.snapshot['revision']
    # Ordinary default response and request are unchanged; no payment fields.
    ordinary=asyncio.run(server.call_tool(tool,dict(expected_revision=revision)))
    assert not ordinary.is_error and payment.JOURNAL_KEY not in ordinary.structured_content
    assert not any(k.startswith('war_payment_') for k in driver.requests[-1])
    # Existing enabled window can be read without a control parameter.
    driver.extra={payment.JOURNAL_KEY:j}
    unchanged=asyncio.run(server.call_tool(tool,dict(expected_revision=revision)))
    assert unchanged.structured_content[payment.JOURNAL_KEY]==j
    assert not any(k.startswith('war_payment_') for k in driver.requests[-1])
    # Explicit enable carries exact machine+contract only once and preserves the
    # complete callback/natural returns instead of reducing them to balances.
    driver.extra[payment.CONTROL_KEY]=dict(requested='enable',accepted=True,reason='enabled_controlled_no_load_window')
    enabled=asyncio.run(server.call_tool(tool,dict(expected_revision=revision,payment_sampling='enable',
        payment_window_contract=payment.WINDOW_CONTRACT)))
    assert not enabled.is_error and enabled.structured_content[payment.JOURNAL_KEY]==j
    assert {k:v for k,v in driver.requests[-1].items() if k.startswith('war_payment_')}=={
        'war_payment_sampling':'enable','war_payment_machine_id':machine,'war_payment_window_contract':payment.WINDOW_CONTRACT}
    assert driver.requests[-1]['expected_revision']==driver.snapshot['native_revision']
    # An actual control refusal is returned without action retry or pretending
    # all payment sampling/install conditions are ready.
    driver.extra[payment.CONTROL_KEY]=dict(requested='enable',accepted=False,reason='natural_phase_sampling_must_be_enabled')
    sent=len(driver.requests)
    failed=asyncio.run(server.call_tool(tool,dict(expected_revision=revision,payment_sampling='enable',
        payment_window_contract=payment.WINDOW_CONTRACT)))
    assert not failed.is_error and failed.structured_content[payment.CONTROL_KEY]['accepted'] is False
    assert len(driver.requests)==sent+1
    # Misuse is rejected before transport, including non-enable contracts.
    invalid=[dict(payment_sampling='enable'),dict(payment_sampling='query',payment_window_contract=payment.WINDOW_CONTRACT),
             dict(payment_window_contract=payment.WINDOW_CONTRACT),dict(payment_sampling=True)]
    for extra in invalid:
        sent=len(driver.requests)
        with pytest.raises(ToolError):asyncio.run(server.call_tool(tool,dict(expected_revision=revision,**extra)))
        assert len(driver.requests)==sent
    # Requested control with absent native receipt cannot become successful.
    driver.extra={}
    with pytest.raises(BridgeUnavailableError):driver.query_war_cash_current_resources_private_v1(
        expected_revision=revision,payment_sampling='query')
    assert len(driver.requests)==sent+1
    # Explicit query preserves the actual gate diagnostic. Successful disable
    # additionally requires the independent raw sampling clear state.
    off=copy.deepcopy(j);off.update(controlled_window_admitted=False,session_basis='unqualified',records=[],qualified_boarding_debits=[])
    off['current_session'].update(controlled_window_id=0,same_owned_process_no_load_window=False)
    off['sampling'].update(capture_enabled=False,clear_completed=True,retained_records=0)
    driver.extra={payment.JOURNAL_KEY:off,payment.CONTROL_KEY:dict(requested='query',accepted=True,reason='not_enabled')}
    queried=asyncio.run(server.call_tool(tool,dict(expected_revision=revision,payment_sampling='query')))
    assert not queried.is_error and queried.structured_content[payment.JOURNAL_KEY]==off
    assert 'war_payment_window_contract' not in driver.requests[-1]
    driver.extra[payment.CONTROL_KEY]=dict(requested='disable',accepted=True,reason='disabled')
    disabled=asyncio.run(server.call_tool(tool,dict(expected_revision=revision,payment_sampling='disable')))
    assert not disabled.is_error and disabled.structured_content[payment.CONTROL_KEY]['accepted'] is True
    # An uninstalled observer can still return truthful inactive diagnostics on
    # explicit query. No fake per-run identity is synthesized from old records.
    unavailable=copy.deepcopy(off);unavailable['installed']=False
    unavailable['current_session'].update(pid=0,process_create_time_100ns=0,connection_generation=0,
        player_character_full_id=None,snapshot_revision=None,native_date_raw=None,absolute_day_raw=None)
    unavailable['sampling'].update(available=False)
    driver.extra={payment.JOURNAL_KEY:unavailable,payment.CONTROL_KEY:dict(requested='query',accepted=True,reason='not_enabled')}
    result=asyncio.run(server.call_tool(tool,dict(expected_revision=revision,payment_sampling='query')))
    assert not result.is_error and result.structured_content[payment.JOURNAL_KEY]==unavailable
    driver.snapshot['diagnostics']['hello']['expected_ck3_version']='1.20.0.3'
    sent=len(driver.requests)
    with pytest.raises(BridgeUnavailableError):driver.query_war_cash_current_resources_private_v1(
        expected_revision=revision,payment_sampling='query')
    assert len(driver.requests)==sent
