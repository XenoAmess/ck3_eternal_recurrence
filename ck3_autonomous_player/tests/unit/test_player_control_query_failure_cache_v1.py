"""Only the newly found query-entry failure gap; all native facts are offline fixtures."""
from contextlib import ExitStack
from pathlib import Path
import copy,hashlib,json,os,tempfile,unittest
from unittest.mock import patch

import test_player_control_v1 as flow_fixtures
import test_player_control_readonly_capability_v1 as readonly_fixtures
from xar_autoplayer.bridge import player_control_driver_v1 as driver_module
from xar_autoplayer.bridge.driver import BridgeUnavailableError,PreSubmissionRevisionMismatchError,UnsupportedStepError
from xar_autoplayer.bridge.player_control_contract_v1 import ACTIONS

_default_artifacts_root = None

def artifacts_root():
    """Keep all fixture artifacts; an explicit output directory takes priority."""
    global _default_artifacts_root
    explicit = os.environ.get('LYD_PLAYER_CONTROL_CACHE_GAP_ARTIFACTS')
    if explicit:
        return Path(explicit)
    if _default_artifacts_root is None:
        _default_artifacts_root = Path(tempfile.mkdtemp(prefix='lyd-pc-cache-gap-'))
        print('LYD_PLAYER_CONTROL_CACHE_GAP_ARTIFACTS=' + str(_default_artifacts_root))
    return _default_artifacts_root

def files(directory):
    directory = driver_module._file(directory)
    return {path.relative_to(directory).as_posix():{'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
            for path in directory.rglob('*') if path.is_file()}

def memory(driver):
    return copy.deepcopy({name:getattr(driver,name) for name in (
        '_command_history','_normal_exit_map_contexts','_episode_character_id','_episode_run_id',
        '_declarable_wars','_pending_declaration_query','persist_calls','_player_control_authorization_blocked_v1')})

class QueryFailureCacheGapTests(unittest.TestCase):
    def seed(self,name):
        root=artifacts_root()
        directory=root/'fixtures'/name;directory.mkdir(parents=True)
        driver=readonly_fixtures.OfflinePartialDriver(directory);driver.partial_mode=False
        first=driver.query_player_control_context_v1(expected_revision=72)
        claimed=driver.request_player_control_v1('open_pause_menu',expected_revision=72,
            expected_control_context_signature=first['control_context_signature'],candidate_character_id=None)
        self.assertTrue(claimed['claim_consumed'])
        eligible=driver.query_player_control_context_v1(expected_revision=72)
        signature=eligible['control_context_signature']
        self.assertIn(signature,driver._player_control_contexts)
        self.assertEqual(driver._player_control_contexts[signature]['native']['phase'],'pause_menu')
        self.assertTrue(driver._player_control_authorization_blocked_v1)
        durable=files(directory)
        self.assertEqual(sum(path.endswith('.claim.json') for path in durable),1)
        return root,directory,driver,signature,durable,memory(driver),len(driver.sent)

    def assert_retired(self,directory,driver,signature,durable,history,sent):
        self.assertEqual(driver._player_control_contexts,{})
        self.assertNotIn(signature,driver._player_control_contexts)
        self.assertEqual(memory(driver),history)
        self.assertTrue(driver._player_control_authorization_blocked_v1)
        self.assertEqual(len(driver.sent),sent)
        self.assertEqual(files(directory),durable)

    def mutations(self,driver,signature,service=None):
        for action in ACTIONS:
            candidate=None if action in ACTIONS[:2] else flow_fixtures.DESTINATION
            with self.subTest(action=action),self.assertRaisesRegex(BridgeUnavailableError,'latest eligible backend query'):
                if service is None:
                    driver.request_player_control_v1(action,expected_revision=72,
                        expected_control_context_signature=signature,candidate_character_id=candidate)
                else:
                    service.request_player_control(action,72,signature,candidate)

    def preserve(self,root,name,driver,signature,durable,error):
        report={'scenario':name,'actual_test_error':{'type':type(error).__name__,'text':str(error)},
            'previous_signature':signature,'current_ephemeral_contexts':driver._player_control_contexts,
            'durable_once_barrier_unchanged':driver._player_control_authorization_blocked_v1 is True,
            'all_request_history_flow_and_claim_file_bytes_unchanged':True,'all_four_mutations_new_packet_count':0,
            'all_four_mutations_new_claim_count':0,'preserved_files':durable,'native_runtime_credit':False,
            'scope':'Offline fixture only; not an actual native query, callback, DLL, profile or PID'}
        with (root/(name+'.receipt.json')).open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(report,stream,indent=2);stream.write('\n')

    def test_driver_argument_and_prepare_refusals_retire_signature_keep_durable_once(self):
        for failure in ('arguments','capability','inventory_reference','source_inventory','revision','paused_frame','process_identity'):
            with self.subTest(failure=failure),readonly_fixtures.driver_sources():
                name='driver-'+failure
                root,directory,driver,signature,durable,history,sent=self.seed(name)
                revision=72;original_profile=driver.player_control_managed_profile
                try:
                    with ExitStack() as faults:
                        if failure=='arguments':revision=True
                        elif failure=='capability':driver.capability_enabled=False
                        elif failure=='inventory_reference':driver.player_control_managed_profile={}
                        elif failure=='source_inventory':faults.enter_context(patch.object(driver_module,'verify_source_inventory_v1',side_effect=ValueError('OFFLINE new source proof failure')))
                        elif failure=='revision':driver.revision=73
                        elif failure=='paused_frame':
                            snapshot=driver.take_snapshot();snapshot['paused']=False
                            faults.enter_context(patch.object(driver,'take_snapshot',return_value=snapshot))
                        else:driver.api.creation=None
                        with self.assertRaises((ValueError,BridgeUnavailableError,PreSubmissionRevisionMismatchError,UnsupportedStepError)) as raised:
                            driver.query_player_control_context_v1(expected_revision=revision)
                        error=raised.exception
                finally:
                    driver.capability_enabled=True;driver.player_control_managed_profile=original_profile
                    driver.revision=72;driver.api.creation=flow_fixtures.CREATION
                self.assert_retired(directory,driver,signature,durable,history,sent)
                self.mutations(driver,signature)
                self.assert_retired(directory,driver,signature,durable,history,sent)
                self.preserve(root,name,driver,signature,durable,error)

    def test_profile_argument_guard_frame_and_attach_refusals_retire_signature_before_driver(self):
        for failure in ('arguments','guard','revision','paused_frame','attach'):
            with self.subTest(failure=failure),readonly_fixtures.driver_sources():
                name='profile-'+failure
                root,directory,driver,signature,durable,history,sent=self.seed(name)
                service=readonly_fixtures.OfflineProfileService(driver);revision=72
                try:
                    with ExitStack() as faults:
                        if failure=='arguments':revision=True
                        elif failure=='guard':faults.enter_context(patch.object(service,'guard',side_effect=RuntimeError('OFFLINE new actual guard failure')))
                        elif failure=='revision':driver.revision=73
                        elif failure=='paused_frame':
                            snapshot=driver.take_snapshot();snapshot['paused']=False
                            faults.enter_context(patch.object(driver,'take_snapshot',return_value=snapshot))
                        else:faults.enter_context(patch.object(service,'_gameplay_service',side_effect=RuntimeError('OFFLINE attachment unavailable')))
                        with self.assertRaises((ValueError,RuntimeError,BridgeUnavailableError)) as raised:
                            service.query_player_control_context(revision)
                        error=raised.exception
                finally:driver.revision=72
                self.assert_retired(directory,driver,signature,durable,history,sent)
                self.mutations(driver,signature,service)
                self.assert_retired(directory,driver,signature,durable,history,sent)
                self.preserve(root,name,driver,signature,durable,error)

if __name__=='__main__':unittest.main()
