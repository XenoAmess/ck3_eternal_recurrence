"""Actual production host continuation for native pending notifications."""
from __future__ import annotations
import ast
import json
from pathlib import Path
import sys
from typing import Protocol,runtime_checkable
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'ck3_autonomous_player/src'))
from xar_autoplayer.bridge import campaign_interaction_boundary_v1 as subject
import test_ck3_mod_acceptance_campaign_event as existing

def object_row(value: object) -> dict[str,object]:
    if not isinstance(value,dict):raise AssertionError('Actual test interface object required')
    result: dict[str,object]={}
    for key,item in value.items():
        if not isinstance(key,str):raise AssertionError('String field required')
        result[key]=item
    return result

def legacy_call(owner: object,name: str,*args: object,**kwargs: object) -> object:
    """One validated boundary to the existing untyped host extraction fixture."""
    operation: object=getattr(owner,name)
    if not callable(operation):raise AssertionError('Existing test provider method missing')
    result: object=operation(*args,**kwargs)
    return result

def notification(instance: int=33554443) -> dict[str,object]:
    return {'instance_id':instance,'sender_character_id':31408,'auto_accept_notification':False,'source':'native'}

def frame(date: int,*,paused: bool=False,revision: int=9) -> dict[str,object]:
    return object_row(legacy_call(existing,'campaign_frame',date,paused=paused,revision=revision))

def step() -> dict[str,object]:
    return {'days':1,'timeout':5,'allow_event_boundary':True}

@runtime_checkable
class HostFixturePort(Protocol):
    snapshot: dict[str,object]
    report: dict[str,object]
    calls: list[tuple[str,dict[str,object]]]
    async def advance_event_boundary(self,step: dict[str,object]) -> dict[str,object]: ...

def client(owner: object,frames: list[dict[str,object]]) -> HostFixturePort:
    result=legacy_call(existing.CampaignEventTests,'client',owner,frames)
    if not isinstance(result,HostFixturePort):raise AssertionError('Actual extracted host interface required')
    return result

class NotificationBoundaryTests(unittest.IsolatedAsyncioTestCase):
    definitions: list[ast.FunctionDef | ast.AsyncFunctionDef]

    @classmethod
    def setUpClass(cls) -> None:
        legacy_call(existing.CampaignEventTests,'setUpClass')
        definitions: object=getattr(existing.CampaignEventTests,'definitions')
        if not isinstance(definitions,list):raise AssertionError('Actual host definitions missing')
        cls.definitions=[]
        for node in definitions:
            if not isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):raise AssertionError('Unexpected extracted node')
            cls.definitions.append(node)

    async def test_native_pending_notification_stops_and_pauses_without_selecting(self) -> None:
        for date in (112,124):
            running=frame(date);paused=frame(date,paused=True,revision=10)
            running['pending_character_interaction']=notification();paused['pending_character_interaction']=notification()
            port=client(self,[running,paused]);result=await port.advance_event_boundary(step())
            self.assertEqual(object_row(result['event_boundary'])['pending_character_interaction'],notification())
            self.assertIs(object_row(result['after'])['paused'],True)
            self.assertEqual(result['requested_interval_complete'],date==124)
            self.assertEqual(result['selected_event_options'],0)
            self.assertEqual([args['step'] for name,args in port.calls if name=='ck3_execute_step'],
                ['pause-map','resume-map','pause-map'])

    async def test_notification_arriving_during_pause_is_retained(self) -> None:
        paused=frame(124,paused=True,revision=10);paused['pending_character_interaction']=notification()
        result=await client(self,[frame(124),paused]).advance_event_boundary(step())
        self.assertEqual(object_row(result['event_boundary'])['pending_character_interaction'],notification())

    async def test_lost_replaced_or_malformed_notification_never_passes(self) -> None:
        for pending in (None,notification(33554444),{**notification(),'instance_id':True}):
            running=frame(112);running['pending_character_interaction']=notification()
            paused=frame(112,paused=True,revision=10);paused['pending_character_interaction']=pending
            with self.assertRaises((RuntimeError,ValueError)):
                await client(self,[running,paused]).advance_event_boundary(step())

    def test_identity_policy_and_native_json_round_trip_are_exact(self) -> None:
        before=(11,1,22,1,1,'pipe',33,None)
        after=before[:7]+(object_row(json.loads(json.dumps(notification()))),)
        self.assertFalse(subject.owner_identities_match_v1(before,after))
        self.assertTrue(subject.owner_identities_match_v1(before,after,allowed_interaction_instance=33554443))
        for bad in (True,33554443.0,0,-1):
            self.assertIs(legacy_call(subject,'owner_identities_match_v1',before,after,allowed_interaction_instance=bad),False)
        for index in (0,1,2,3,4,5,6):
            changed: list[object]=list(after);changed[index]='other' if index==5 else 2
            self.assertFalse(subject.owner_identities_match_v1(before,changed,allowed_interaction_instance=33554443))
        for field,value in [('instance_id',True),('sender_character_id',False),('auto_accept_notification',1),('source','fixture')]:
            with self.assertRaises(ValueError):subject.pending_instance_v1({**notification(),field:value})

    def test_zero_local_player_id_preserves_existing_native_owner_contract(self) -> None:
        before=(11,1,22,0,1,'pipe',33,None)
        after=before[:7]+(notification(),)
        self.assertTrue(subject.owner_identities_match_v1(before,before))
        self.assertTrue(subject.owner_identities_match_v1(before,after,allowed_interaction_instance=33554443))
        for invalid in (False,0.0,-1,2**31):
            wrong=list(before);wrong[3]=invalid
            self.assertFalse(subject.owner_identities_match_v1(wrong,wrong))
            self.assertFalse(subject.owner_identities_match_v1(wrong,after,allowed_interaction_instance=33554443))

    def test_held_control_failure_contract_rejects_wrong_types_and_round_trips(self) -> None:
        record=subject.control_plan_failure_hold_v1('owned-once.json',RuntimeError('original failure'),101.0)
        self.assertEqual(json.loads(json.dumps(record)),record)
        self.assertEqual(record['original_hold_deadline'],101.0)
        for value in (True,None,'101',float('nan'),float('inf'),-1):
            with self.assertRaises(ValueError):legacy_call(subject,'control_plan_failure_hold_v1','owned-once.json',RuntimeError('original'),value)

    async def test_original_read_failure_attempts_pause_once_and_preserves_error(self) -> None:
        port=client(self,[frame(112),frame(112,paused=True,revision=10)])
        original=RuntimeError('synthetic observation failed after native resume')
        async def failed(*args: object,**kwargs: object) -> object:
            port.snapshot=frame(112)
            raise original
        setattr(port,'wait_campaign_running_successor',failed)
        with self.assertRaises(RuntimeError) as caught:
            await port.advance_event_boundary(step())
        self.assertIs(caught.exception,original)
        observations=port.report['campaign_failed_advance_pause']
        if not isinstance(observations,list) or len(observations)!=1:raise AssertionError('Original pause evidence missing')
        cleanup=object_row(observations[0])
        self.assertIs(cleanup['pause_attempted'],True)
        self.assertEqual(cleanup['status'],'FULL_PAUSED_FRAME_OBSERVED')
        self.assertEqual([args['step'] for name,args in port.calls if name=='ck3_execute_step'],
            ['pause-map','resume-map','pause-map'])

if __name__=='__main__':unittest.main()
