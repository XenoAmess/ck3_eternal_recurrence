"""Focused regression for explicit same-packet SDK warm attachment.

Exercises the actual reader with a fake MCP transport and temporary packet.
The cold startup block is checked against Root's original source reuse receipt;
no cold startup, native call, SDK subprocess or gameplay is executed.
"""
from pathlib import Path
from contextlib import asynccontextmanager
import ast
import asyncio
import hashlib
import importlib.util
import json
import sys
import tempfile
import textwrap
import types
import unittest
from unittest.mock import patch

CANDIDATE=Path(__file__).resolve().parents[1]/'tools/gameplay_mcp_packet_reader.py'
OUTPUT=None
SDK_ROOT=None
events=[]
RESTORED_PRIVATE_SWITCHES=('--private-government-runtime-adapter-query', '--private-current-first-heir-relationship-query', '--private-council-query', '--private-realm-law-paused-query', '--private-active-scheme-sway-query', '--private-active-scheme-sway-outcome-opinion-query', '--private-faction-gift-query', '--private-activity-feast-queries', '--private-realm-law-crown-action', '--private-prisoner-collection-query', '--private-active-scheme-sway-completion-query', '--private-active-scheme-sway-completion-execution-query', '--private-active-scheme-sway-completion-termination-query', '--private-active-scheme-sway-completion-invalidation-reason-query', '--private-player-religion-context-query', '--private-player-clergy-appointment-query', '--private-family-obligations-query', '--private-death-succession-modal-continue', '--private-war-cash-queries', '--private-council-action')

def write(p,value):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8') as f:
        json.dump(value,f,indent=2)
        f.write('\n')

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

events=[]
class Parameters:
    def __init__(self,command,args,cwd,**kwargs):
        self.command,self.args,self.cwd=command,args,cwd
        events.append({'event':'parameters','command':command,'args':args,'cwd':cwd})

@asynccontextmanager
async def fake_stdio(params,errlog):
    events.append({'event':'stdio_enter'})
    try:
        yield object(),object()
    finally:
        events.append({'event':'stdio_exit'})

class FakeResult:
    def model_dump(self,mode):
        assert mode=='json'
        return {'structuredContent':{'plan':{'selected_step':'ordinary-fixture-business'},
            'result':{'status':'fixture_business_response','request_replayed':False}},
            'content':[],'isError':False}

class Session:
    def __init__(self,*args):
        events.append({'event':'session_created'})
    async def __aenter__(self):
        return self
    async def __aexit__(self,*args):
        events.append({'event':'session_exit'})
    async def initialize(self):
        events.append({'event':'initialize'})
    async def call_tool(self,tool,arguments):
        events.append({'event':'tool','tool':tool,'arguments':arguments})
        assert tool=='ck3_auto_turn', 'warm startup or replayed tool was called'
        return FakeResult()

async def forbidden_cold_wait(*args):
    raise AssertionError('old cold core waiter executed during warm main')

def install_fake_MCP():
    mcp=types.ModuleType('mcp')
    mcp.__path__=[]
    mcp.ClientSession=Session
    mcp.StdioServerParameters=Parameters
    client=types.ModuleType('mcp.client')
    client.__path__=[]
    stdio=types.ModuleType('mcp.client.stdio')
    stdio.stdio_client=fake_stdio
    mcp.client=client
    client.stdio=stdio
    waiter=types.ModuleType('wait_restored_ck3_core_12004')
    waiter.wait_for_restored_core_v1=forbidden_cold_wait
    sys.modules.update({'mcp':mcp,'mcp.client':client,'mcp.client.stdio':stdio,
        'wait_restored_ck3_core_12004':waiter})

def load_actual_candidate():
    data=CANDIDATE.read_bytes()
    spec=importlib.util.spec_from_file_location('_root_actual_new_warm_reader',CANDIDATE)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def assert_default_cold_source_reused():
    new=CANDIDATE.read_text(encoding='utf-8-sig')
    marker='write(packet / "ROOT-REGISTRY-REUSED-FIRST77.json", {'
    start_new=new.index('                    '+marker)
    stop_new=new.index('                while True:\n',start_new)
    new_block=''.join(line[4:] if line.strip() else line for line in new[start_new:stop_new].splitlines(keepends=True))
    assert len(new_block.encode('utf-8'))==1731
    assert hashlib.sha256(new_block.encode('utf-8')).hexdigest()=='007a38dde30ed1a1cf7fba307e2fba9c34ef3c8a3888a9b1b8e1d37e76672a72'
    ast.parse('async def reused():\n'+textwrap.indent(textwrap.dedent(new_block),'    '))

def make_packet(name,exit_code):
    case=OUTPUT/name
    packet=case/'packet'
    inbox=packet/'gameplay-requests'
    outbox=packet/'gameplay-responses'
    inbox.mkdir(parents=True)
    outbox.mkdir()
    switches=list(RESTORED_PRIVATE_SWITCHES)
    argv=[sys.executable,str(SDK_ROOT/'ck3_autonomous_player/mcp_server.py'),
        '--driver','native-headless','--transport','stdio',*switches,
        '--allow-private-family-marriage-formal-trial',
        '--allow-private-construction-formal-trial','--allow-private-activity-feast-normal',
        '--allow-private-faction-gift-formal-trial','--private-faction-round-id','R94']
    write(packet/'BOOTSTRAP-DRAFT.json',{'gameplay_mcp':{'argv':argv},
        'restored_original_switches':switches,'native':{'source_head':'664c85d9dab3ff898826245e9b0a6053697e0bd6'},
        'run_identity':{'fixture_only':True}})
    write(packet/'ROOT-OPERATOR-HANDOFF.json',{'result':'ACCEPTED'})
    recovery=case/'historical-recovery.json'
    write(recovery,{'expected_character_id':29829,'expected_date_raw':53290152,
        'expected_episode_run_id':'fixture-old-episode','expected_paused':True})
    responded=inbox/'001-already-responded.json'
    write(responded,{'tool':'MUST_NOT_REPLAY','arguments':{}})
    write(outbox/responded.name,{'retained_response':True})
    exit_request=inbox/'100-last-successful-SDK-exit.json'
    write(exit_request,{'exit_client':True,'reason':'fixture exact completed close'})
    business=inbox/'200-existing-normal-business.json'
    write(business,{'tool':'ck3_auto_turn','arguments':{}})
    different_exit=inbox/'900-distinct-next-SDK-exit.json'
    write(different_exit,{'exit_client':True,'reason':'fixture new exit must return'})
    close=case/'normal-close.json'
    write(close,{'normal_sdk_exit_confirmed':True,'exit_code':exit_code,
        'Game_exit_requested':False,'exit_request':str(exit_request)})
    return packet,recovery,{
        'normal_sdk_exit_receipt':str(close),'expected_exit_request_name':exit_request.name,
        'evidence_directory':str(case/'warm-evidence'),'mcp_argv':argv},case

async def run_new_branch_cases(module):
    packet,recovery,warm,case=make_packet('successful-exact-close',0)
    await module.main(packet,SDK_ROOT,
        '86079fd65ba70df161702671d0254994ef0863d7',recovery,
        case/'prior-registry-reference.json',case/'source-metadata-reference.json',
        allow_private_construction_formal_trial=True,warm_resume=warm)
    assert [row['tool'] for row in events if row['event']=='tool']==['ck3_auto_turn']
    assert [row['event'] for row in events].count('initialize')==1
    assert [row['event'] for row in events].count('session_exit')==1
    assert [row['event'] for row in events].count('stdio_exit')==1
    response=read(packet/'gameplay-responses/200-existing-normal-business.json')
    assert response['result']['structuredContent']['result']['status']=='fixture_business_response'
    assert read(packet/'gameplay-responses/001-already-responded.json')=={'retained_response':True}
    assert not (packet/'gameplay-responses/100-last-successful-SDK-exit.json').exists()
    assert not (packet/'gameplay-responses/900-distinct-next-SDK-exit.json').exists()
    assert sorted(p.name for p in (packet/'gameplay-requests').glob('*.json'))==[
        '001-already-responded.json','100-last-successful-SDK-exit.json',
        '200-existing-normal-business.json','900-distinct-next-SDK-exit.json']
    attached=read(case/'warm-evidence/ROOT-WARM-TRANSPORT-ATTACHED.json')
    assert attached['status']=='MCP_INITIALIZED_RESTORE_NOT_YET_OBSERVED'
    assert attached['startup_core_queries']==attached['startup_full_snapshot_queries']==0
    assert attached['qualification_of_recovery_or_business_inferred'] is False
    assert not (packet/'ROOT-COLD-LOAD-CORE-WAIT-FIRST77.json').exists()
    assert not (packet/'ROOT-REGISTRY-REUSED-FIRST77.json').exists()
    events_before=list(events)
    failed_packet,failed_recovery,failed_warm,failed_case=make_packet('failed-normal-close',1)
    try:
        await module.main(failed_packet,SDK_ROOT,
            '86079fd65ba70df161702671d0254994ef0863d7',failed_recovery,
            failed_case/'prior-registry-reference.json',failed_case/'source-metadata-reference.json',
            allow_private_construction_formal_trial=True,warm_resume=failed_warm)
    except ValueError as error:
        assert str(error)=='warm resume requires the exact successful final SDK exit'
    else:
        raise AssertionError('failed normal close was accepted')
    assert events==events_before, 'failed close opened a new MCP transport'
    return {'actual_main_warm_success':True,'business_calls':1,'already_responded_replayed':False,
        'exact_successful_exit_skipped':True,'different_exit_returned':True,
        'failed_normal_close_rejected_before_MCP':True,'startup_core_queries':0,
        'startup_full_snapshot_queries':0,'no_new_request_created':True,
        'live_same_pid_restore_or_business_qualification_observed':False}

class GameplayMcpPacketReaderWarmTests(unittest.IsolatedAsyncioTestCase):
    async def test_explicit_warm_main_processes_existing_requests_once(self):
        global OUTPUT, SDK_ROOT
        with tempfile.TemporaryDirectory() as directory:
            OUTPUT=Path(directory)
            SDK_ROOT=OUTPUT/'full-sdk'
            events.clear()
            assert_default_cold_source_reused()
            with patch.dict(sys.modules):
                install_fake_MCP()
                actual=load_actual_candidate()
                result=await run_new_branch_cases(actual)
            self.assertTrue(result['actual_main_warm_success'])
            self.assertTrue(result['failed_normal_close_rejected_before_MCP'])
            self.assertFalse(result['live_same_pid_restore_or_business_qualification_observed'])


if __name__=='__main__':
    unittest.main()
