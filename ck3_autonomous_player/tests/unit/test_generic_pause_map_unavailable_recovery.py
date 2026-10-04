"""Normal registered MCP/service/driver; only the transport Endpoint is fake."""
from __future__ import annotations
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from xar_autoplayer.bridge.driver import BridgeUnavailableError,PreSubmissionRevisionMismatchError,StepPostconditionError
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12003,CK3_12002
class FakeEndpoint:
    def __init__(self, pipe_name: str = r"\\.\pipe\xar_fixture") -> None:
        self.pipe_name = pipe_name
        self.frames: list[dict[str, object]] = []
        self.on_frame = None
        self.on_disconnect = None
        self.send_hook = None
        self.closed = False
        self.error: str | None = None

    def start(self, on_frame, on_disconnect) -> None:
        self.on_frame = on_frame
        self.on_disconnect = on_disconnect

    def publish(self, frame: dict[str, object]) -> None:
        assert self.on_frame is not None
        self.on_frame(frame)

    def send(self, frame: dict[str, object]) -> None:
        self.frames.append(frame)
        if self.send_hook is not None:
            self.send_hook(frame)

    def close(self) -> None:
        self.closed = True

    def transport_error(self) -> str | None:
        return self.error

def _hello(*capabilities: str) -> dict[str, object]:
    return {
        "type": "hello",
        "protocol_version": 1,
        "bridge_version": "0.1.0",
        "pid": 4242,
        "session_generation": 0,
        "capabilities": list(capabilities),
    }

def _snapshot(
    revision: int = 1,
    *,
    active_event: dict[str, object] | None = None,
    date_raw: int = 53_171_400,
    speed: int = 1,
    paused: bool = True,
    map_ready: bool = True,
    pending_character_interaction: dict[str, object] | None = None,
    played_character: dict[str, object] | None = None,
    played_character_gold: dict[str, object] | None = None,
    played_character_prestige: dict[str, object] | None = None,
    played_character_piety: dict[str, object] | None = None,
    one_life_settlement: dict[str, object] | None = None,
    active_wars: list[dict[str, object]] | None = None,
    player_armies: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "type": "state_snapshot",
        "protocol_version": 1,
        "snapshot_id": f"native:{revision}",
        "revision": revision,
        "state": {
            "phase": "map_hud",
            "date": "1066.9.15",
            "date_raw": date_raw,
            "speed": speed,
            "paused": paused,
            "map_ready": map_ready,
            "history": [],
            "active_event": active_event,
            "pending_character_interaction": pending_character_interaction,
            "played_character": played_character,
            "played_character_gold": played_character_gold,
            "played_character_prestige": played_character_prestige,
            "played_character_piety": played_character_piety,
            "one_life_settlement": one_life_settlement,
            "active_wars": active_wars,
            "player_armies": player_armies,
        },
    }

ERROR='CK3 map state is unavailable'

def fixture(*, first_error=ERROR, second_error=None, source_paused=False,
            refresh_mutation=None, refresh_hello=None, publish_refresh=True,
            publish_final=True, final_mutation=None, first_success=False):
    endpoint=FakeEndpoint()
    driver=NativeHeadlessGameplayDriver(endpoint.pipe_name,endpoint=endpoint,command_timeout_seconds=0.1)
    hello=_hello('game.state.snapshot','game.command.pause-map','game.command.resume-map','game.command.set-speed-1')
    hello.update(expected_ck3_version=CK3_12003.game_version,expected_ck3_sha256=CK3_12003.executable_sha256,
                 ck3_build_match=True,game_adapter_id='ck3-1.20.0.3-msvc-x64')
    endpoint.publish(hello)
    before=_snapshot(40,date_raw=53_147_160,paused=source_paused,map_ready=True,
                     speed=1,played_character={'character_id':33388,'alive':True})
    endpoint.publish(before)
    refreshed=copy.deepcopy(before);refreshed.update(snapshot_id='native:41',revision=41)
    refreshed['state']['date_raw']+=24
    if refresh_mutation:refresh_mutation(refreshed['state'])
    final=copy.deepcopy(refreshed);final.update(snapshot_id='native:42',revision=42)
    final['state']['paused']=True
    if final_mutation:final_mutation(final['state'])
    calls=[]
    def answer(request):
        if request.get('type')!='execute_step':return
        calls.append(request)
        reply={'type':'command_result','protocol_version':1,'request_id':request['request_id']}
        if len(calls)==1 and not first_success:
            endpoint.publish({**reply,'ok':False,'error':first_error})
            if refresh_hello:endpoint.publish({**hello,**refresh_hello})
            if publish_refresh:endpoint.publish(refreshed)
        elif second_error:
            endpoint.publish({**reply,'ok':False,'error':second_error})
        else:
            endpoint.publish({**reply,'ok':True,'result':{'step':request['step'],'accepted':True,
                             'status':'already_paused' if source_paused else 'submitted'}})
            if publish_final:endpoint.publish(final)
    endpoint.send_hook=answer
    return driver,endpoint,calls,before,refreshed,final,hello

class GenericPauseMapUnavailableRecoveryTests(unittest.TestCase):
    def setup_fixture(self,**kwargs):
        x=fixture(**kwargs);self.addCleanup(x[0].close);return x

    def test_same_owner_running_refresh_retries_once_and_observes_paused(self):
        driver,_,calls,*_=self.setup_fixture()
        result=GameplayBridgeService(driver).execute_step('pause-map')
        recovery=result['map_control_recovery']
        self.assertTrue(result['accepted']);self.assertTrue(recovery['postcondition_verified'])
        self.assertTrue(driver.take_snapshot()['paused'])
        self.assertEqual(len(calls),2)
        self.assertNotEqual(calls[0]['request_id'],calls[1]['request_id'])
        self.assertEqual([c['expected_revision'] for c in calls],[40,41])
        self.assertEqual(recovery['attempts'][0]['request_id'],calls[0]['request_id'])
        self.assertEqual(recovery['attempts'][0]['error'],ERROR)
        self.assertEqual(recovery['ending_native_revision'],42)
        self.assertEqual(driver._command_history[-1]['result']['map_control_recovery'],recovery)

    def test_initial_explicit_stale_revision_rejects_without_send(self):
        driver,_,calls,*_=self.setup_fixture()
        with self.assertRaises(PreSubmissionRevisionMismatchError):
            GameplayBridgeService(driver).execute_step('pause-map',expected_revision=driver.take_snapshot()['revision']+1)
        self.assertEqual(calls,[])

    def test_explicit_fresh_first_revision_can_recover_running_date_advance(self):
        driver,_,calls,*_=self.setup_fixture()
        result=GameplayBridgeService(driver).execute_step('pause-map',expected_revision=driver.take_snapshot()['revision'])
        self.assertTrue(result['map_control_recovery']['postcondition_verified']);self.assertEqual(len(calls),2)

    def test_other_native_rejection_is_not_retried(self):
        driver,_,calls,*_=self.setup_fixture(first_error='native owner unavailable')
        with self.assertRaisesRegex(BridgeUnavailableError,'native owner unavailable'):
            driver.execute_step('pause-map')
        self.assertEqual(len(calls),1)

    def test_second_rejection_keeps_two_attempt_bound_and_original_error(self):
        driver,_,calls,*_=self.setup_fixture(second_error=ERROR)
        with self.assertRaises(StepPostconditionError) as raised:driver.execute_step('pause-map')
        self.assertEqual(len(calls),2)
        rec=raised.exception.step_result['map_control_recovery']
        self.assertEqual(rec['attempts'][0]['error'],ERROR)
        self.assertEqual(rec['failure'],'second pause request failed')
        self.assertFalse(driver._command_history[-1]['ok'])
        self.assertEqual(driver._command_history[-1]['result']['map_control_recovery'],rec)

    def test_no_new_semantic_frame_does_not_retry_cached_running_state(self):
        driver,_,calls,*_=self.setup_fixture(publish_refresh=False)
        with self.assertRaisesRegex(StepPostconditionError,'no fresh semantic frame'):driver.execute_step('pause-map')
        self.assertEqual(len(calls),1)

    def test_reconnect_or_exact_build_change_stops_before_second_send(self):
        for hello in ({'session_generation':1},{'expected_ck3_version':CK3_12002.game_version,
                       'expected_ck3_sha256':CK3_12002.executable_sha256}):
            with self.subTest(hello=hello):
                driver,_,calls,*_=self.setup_fixture(refresh_hello=hello)
                with self.assertRaises(BridgeUnavailableError):driver.execute_step('pause-map')
                self.assertEqual(len(calls),1)

    def test_actor_event_pending_speed_or_map_change_stops_before_retry(self):
        mutations=(lambda s:s.update(played_character={'character_id':33389,'alive':True}),
                   lambda s:s.update(active_event={'event_id':'fixture_event','options':[]}),
                   lambda s:s.update(pending_character_interaction={'interaction_id':'fixture_pending','sender_character_id':999}),
                   lambda s:s.update(speed=2),lambda s:s.update(map_ready=False))
        for change in mutations:
            with self.subTest(change=change):
                driver,_,calls,*_=self.setup_fixture(refresh_mutation=change)
                with self.assertRaises(BridgeUnavailableError):driver.execute_step('pause-map')
                self.assertEqual(len(calls),1)

    def test_second_submitted_ack_without_actual_paused_frame_is_red(self):
        driver,_,calls,*_=self.setup_fixture(publish_final=False)
        with self.assertRaisesRegex(StepPostconditionError,'paused map not observed'):driver.execute_step('pause-map')
        self.assertEqual(len(calls),2)

    def test_postread_actor_or_event_drift_is_red(self):
        for change in (lambda s:s.update(played_character={'character_id':33389,'alive':True}),
                       lambda s:s.update(active_event={'event_id':'fixture_event','options':[]})):
            driver,_,calls,*_=self.setup_fixture(final_mutation=change)
            with self.assertRaises(BridgeUnavailableError):driver.execute_step('pause-map')
            self.assertEqual(len(calls),2)

    def test_actual_fresh_already_paused_after_rejection_needs_no_second_command(self):
        driver,_,calls,*_=self.setup_fixture(refresh_mutation=lambda s:s.update(paused=True))
        result=driver.execute_step('pause-map')
        self.assertEqual(result['status'],'already_paused')
        self.assertTrue(result['map_control_recovery']['postcondition_verified'])
        self.assertEqual(len(calls),1)

    def test_original_success_path_retains_primitive_result(self):
        driver,_,calls,*_=self.setup_fixture(first_success=True)
        result=driver.execute_step('pause-map')
        self.assertEqual(result['status'],'submitted');self.assertNotIn('map_control_recovery',result)
        self.assertEqual(len(calls),1)

    def test_original_already_paused_path_keeps_existing_real_frame_verification(self):
        driver,_,calls,*_=self.setup_fixture(first_success=True,source_paused=True)
        result=driver.execute_step('pause-map')
        self.assertEqual(result['status'],'already_paused')
        self.assertEqual(result['map_control_postcondition']['status'],'observed')
        self.assertNotIn('map_control_recovery',result)
        self.assertEqual(len(calls),1)

    def test_timeout_does_not_retry_an_ambiguous_pause_submission(self):
        driver,endpoint,_,*_=self.setup_fixture()
        endpoint.send_hook=lambda frame:None
        with self.assertRaisesRegex(BridgeUnavailableError,'command_result timed out'):
            driver.execute_step('pause-map')
        self.assertEqual(len([r for r in endpoint.frames if r.get('type')=='execute_step']),1)

    def test_resume_and_speed_commands_do_not_retry_identical_error(self):
        for step in ('resume-map','set-speed-1'):
            with self.subTest(step=step):
                driver,_,calls,*_=self.setup_fixture(source_paused=True)
                with self.assertRaisesRegex(BridgeUnavailableError,ERROR):driver.execute_step(step)
                self.assertEqual(len(calls),1)

class GenericPauseMapRegisteredMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_registered_generic_mcp_recovery_sends_only_two_pause_requests(self):
        from mcp import Client
        from xar_autoplayer.bridge.mcp_server import create_server
        driver,_,calls,*_=fixture();self.addCleanup(driver.close)
        async with Client(create_server(driver)) as client:
            reply=await client.call_tool('ck3_execute_step',{'step':'pause-map','expected_revision':None})
        self.assertFalse(reply.is_error)
        self.assertTrue(reply.structured_content['map_control_recovery']['postcondition_verified'])
        self.assertEqual([c['step'] for c in calls],['pause-map','pause-map'])
        self.assertNotEqual(calls[0]['request_id'],calls[1]['request_id'])

if __name__=='__main__':unittest.main()
