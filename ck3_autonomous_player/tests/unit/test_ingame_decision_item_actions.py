"""Focused synthetic action/claim regressions; no game endpoint or action callbacks."""
from copy import deepcopy
from pathlib import Path
import json, os, subprocess, sys, tempfile, threading, unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.ingame_decisions_open_contract import EXE_SHA256, opening_binding, result_build
from xar_autoplayer.bridge.ingame_decision_item_contract import STEP
from xar_autoplayer.bridge.ingame_decision_item_action_contract import (
    SELECT_STEP,SELECT_CAPABILITY,CONFIRM_STEP,CONFIRM_CAPABILITY,
    actual_inner_modal_tree, normalize_decision_action, parse_decision_navigation_identity,
)

KEY='ervc_courtier_creator_decision'
def frame():
    return dict(revision=1,native_revision=7,snapshot_id='synthetic-paused-7',
        episode_run_id='synthetic-decision-action-episode',paused=True,map_ready=True,date_raw=1234,
        played_character=dict(character_id=7001,alive=True),
        diagnostics=dict(connection_generation=1,pid=99999,hello=dict(pid=12700,ck3_build_match=True,
            game_adapter_id='ck3-1.20.0.3-msvc-x64',expected_ck3_version='1.20.0.3',expected_ck3_sha256=EXE_SHA256)))

def model(binding,selected=False):
    return dict(schema='ck3-ingame-decision-item-v1',step=STEP,read_only=True,game_version='1.20.0.3',
        executable_sha256=EXE_SHA256,available=True,
        **{k:binding[k] for k in ('native_revision','connection_generation','game_pid','played_character_id','date_raw')},
        owner_thread_verified=True,frame_verified=True,source_abi_pins_verified=True,gui_owner_binding_verified=True,
        decisions_tree_complete=True,decisions_root_visible=True,row_owner_verified=True,row_scope_reference_available=True,
        group_count=7,row_count=21,matching_row_count=1,row_context_reference_key=7001,decision_key=KEY,
        detail_tree_complete=True,detail_root_visible=selected,detail_definition_available=selected,
        detail_definition_matches_target=selected,detail_decision_key=KEY if selected else '',
        detail_actor_binding_verified=selected,detail_actor_reference_key=7001 if selected else -1,
        row_widget_datacontext_verified=False,action_qualified=False,unavailable_reason='')

def ack(binding,action='select',already_selected=False):
    return dict(schema='ck3-ingame-decision-item-action-v1',step=SELECT_STEP if action=='select' else CONFIRM_STEP,
        action=action,game_version='1.20.0.3',executable_sha256=EXE_SHA256,decision_key=KEY,
        **{k:binding[k] for k in ('native_revision','connection_generation','game_pid','played_character_id','date_raw')},
        owner_thread_verified=True,source_abi_pins_verified=True,action_abi_pins_verified=True,receiver_qualified=True,
        gui_owner_binding_verified=True,frame_verified=True,detail_actor_binding_verified=action=='confirm',
        no_blocking_modal_verified=action=='select',before_already_selected=already_selected,
        dispatch_invoked=not already_selected,native_call_completed=action=='select' and not already_selected,
        native_handled=False,native_after_read=True,selected_after_verified=False,
        inner_modal_visible=False,inner_modal_tree_complete=True,postcondition_verified=False,verification_pending=True,
        status='acknowledged_verification_pending',unavailable_reason='',
        before_actual_model=model(binding,selected=action=='confirm' or already_selected),
        after_actual_model={'available':False,'unavailable_reason':'actual_decision_row_disappeared_after_take'})

def tree(visible=True):
    return dict(schema='ck3-native-gui-window-tree-inspection-v1',step='inspect-gui-window-tree-v1',
        window_kind='vivhite_courtier',read_only=True,scope_root_name='ervc_courtier_creator_window',
        root_available=True,truncated=False,widget_count=2,widgets=[
            dict(child_path='',runtime_name='ervc_courtier_creator_window',effective_visible=True,child_count=1),
            dict(child_path='0',runtime_name='ervc_courtier_creator_modal',effective_visible=visible,child_count=0)])

class SyntheticDriver:
    select_ingame_decision_item_v1=NativeHeadlessGameplayDriver.select_ingame_decision_item_v1
    confirm_ingame_decision_item_v1=NativeHeadlessGameplayDriver.confirm_ingame_decision_item_v1
    _decision_item_action_v1=NativeHeadlessGameplayDriver._decision_item_action_v1
    def __init__(self,directory,*,action='select',native_ack=None,action_error=None,source_frame=None,already_selected=False):
        self.frame=deepcopy(frame() if source_frame is None else source_frame)
        self.directory=Path(directory);self.action=action;self.already_selected=already_selected
        self.native_ack=deepcopy(ack(opening_binding(self.frame),action,already_selected) if native_ack is None else native_ack)
        self.action_error=action_error;self.submissions=[];self.model_queries=[];self.tree_queries=[];self.records=[]
        self.tree_results=[tree()];self.rebind_on_tree=False
    def take_snapshot(self):return deepcopy(self.frame)
    def capabilities(self):return dict(bridge_capabilities=[SELECT_CAPABILITY,CONFIRM_CAPABILITY])
    def _native_driver_state_path(self):return self.directory/'synthetic-state.json'
    def _record_command(self,*args,**kwargs):self.records.append((args,kwargs))
    def query_ingame_decision_item_v1(self,key):
        self.model_queries.append(key)
        if self.action=='confirm' and len(self.model_queries)>1:raise AssertionError('Take postcondition must not depend on its disappeared row')
        return model(opening_binding(self.frame),selected=self.action=='confirm' or self.already_selected or len(self.model_queries)>1)
    def _execute_primitive_step(self,step,**kwargs):
        self.submissions.append((step,kwargs))
        if self.action_error:raise self.action_error
        return deepcopy(self.native_ack)
    def inspect_gui_window_tree_v1(self,kind):
        self.tree_queries.append(kind)
        result=deepcopy(self.tree_results.pop(0) if len(self.tree_results)>1 else self.tree_results[0])
        if self.rebind_on_tree:self.frame['diagnostics']['connection_generation']+=1
        return result

class DecisionActionTests(unittest.TestCase):
    def directory(self):
        parent=os.environ.get('XAR_WHITE_DECISION_ACTION_TEST_ARTIFACTS')
        if parent:Path(parent).mkdir(parents=True,exist_ok=True)
        return Path(tempfile.mkdtemp(prefix='synthetic-decision-claim-',dir=parent))
    def test_invalid_binding_rejects_before_claim_or_submission(self):
        driver=SyntheticDriver(self.directory());driver.frame['played_character']['alive']=False
        with self.assertRaises(BridgeUnavailableError):driver.select_ingame_decision_item_v1(KEY)
        self.assertEqual(driver.submissions,[]);self.assertEqual(driver.model_queries,[])
        self.assertFalse((driver.directory/'ingame-decision-item-actions').exists())
    def test_lost_ack_does_not_query_after_or_retry_even_after_reconnect(self):
        directory=self.directory();driver=SyntheticDriver(directory,action_error=TimeoutError('synthetic lost ACK'))
        with self.assertRaises(TimeoutError):driver.select_ingame_decision_item_v1(KEY)
        self.assertEqual(len(driver.submissions),1);self.assertEqual(driver.model_queries,[KEY]);self.assertEqual(driver.tree_queries,[])
        files=list((directory/'ingame-decision-item-actions').glob('*.claim.json'));self.assertEqual(len(files),1)
        saved=json.loads(files[0].read_text(encoding='utf-8'));self.assertEqual(saved['request_id'],driver.submissions[0][1]['protocol_request_id'])
        self.assertEqual(saved['status'],'claimed_result_unknown_no_retry')
        self.assertEqual(list(files[0].parent.glob('*.result.json')),[])
        reconnect=frame();reconnect['diagnostics']['connection_generation']=2
        driver=SyntheticDriver(directory,source_frame=reconnect)
        with self.assertRaisesRegex(BridgeUnavailableError,'already claimed'):driver.select_ingame_decision_item_v1(KEY)
        self.assertEqual(driver.submissions,[])
    def test_invalid_native_proof_consumes_claim_before_any_later_read(self):
        for field in ('receiver_qualified','action_abi_pins_verified','gui_owner_binding_verified','frame_verified'):
            with self.subTest(field=field):
                native=ack(opening_binding(frame()));native[field]=False
                driver=SyntheticDriver(self.directory(),native_ack=native)
                with self.assertRaises(ValueError):driver.select_ingame_decision_item_v1(KEY)
                self.assertEqual(len(driver.submissions),1);self.assertEqual(driver.model_queries,[KEY])
                with self.assertRaisesRegex(BridgeUnavailableError,'already claimed'):driver.select_ingame_decision_item_v1(KEY)
                self.assertEqual(len(driver.submissions),1)
    def test_pending_confirm_reads_actual_inner_and_never_requires_row_after_take(self):
        driver=SyntheticDriver(self.directory(),action='confirm');driver.tree_results=[tree(False),tree(True)]
        result=driver.confirm_ingame_decision_item_v1(KEY,'vivhite_courtier')
        self.assertEqual(len(driver.submissions),1);self.assertEqual(driver.model_queries,[KEY])
        self.assertEqual(driver.tree_queries,['vivhite_courtier','vivhite_courtier'])
        self.assertFalse(result['native_ack']['postcondition_verified']);self.assertTrue(result['postcondition_verified'])
        self.assertEqual(result['status'],'verified_inner_modal_visible')
    def test_outer_root_hidden_inner_duplicate_or_truncation_cannot_prove_open(self):
        self.assertTrue(actual_inner_modal_tree(tree(),'vivhite_courtier'))
        candidates=[tree(False)]
        partial=tree();partial['truncated']=True;candidates.append(partial)
        absent=tree();absent['widgets'].pop();absent['widget_count']=1;candidates.append(absent)
        duplicate=tree();duplicate['widgets'].append(deepcopy(duplicate['widgets'][1]));duplicate['widget_count']=3;candidates.append(duplicate)
        wrong=tree();wrong['widgets'][1]['runtime_name']='ervc_courtier_creator_panel';candidates.append(wrong)
        for candidate in candidates:self.assertFalse(actual_inner_modal_tree(candidate,'vivhite_courtier'))
    def test_already_selected_is_a_native_noop_and_requires_fresh_visible_detail(self):
        driver=SyntheticDriver(self.directory(),already_selected=True)
        result=driver.select_ingame_decision_item_v1(KEY)
        self.assertEqual(driver.submissions,[]);self.assertEqual(driver.model_queries,[KEY])
        self.assertIsNone(result['native_ack']);self.assertIsNone(result['action_claim_path'])
        self.assertTrue(result['read_only']);self.assertFalse(result['dispatch_invoked'])
        self.assertEqual(result['completion_source'],'observed_already_visible')
        self.assertTrue(result['postcondition_verified'])
        self.assertFalse((driver.directory/'ingame-decision-item-actions').exists())
        bad=deepcopy(driver.native_ack);bad['dispatch_invoked']=True
        with self.assertRaises(ValueError):normalize_decision_action(bad,opening_binding(frame()),KEY,'select')
    def test_later_rebinding_rejects_without_retrying_the_confirm(self):
        driver=SyntheticDriver(self.directory(),action='confirm');driver.rebind_on_tree=True
        with self.assertRaisesRegex(BridgeUnavailableError,'after-read crossed'):driver.confirm_ingame_decision_item_v1(KEY,'vivhite_courtier')
        self.assertEqual(len(driver.submissions),1);self.assertEqual(driver.tree_queries,['vivhite_courtier'])
        driver.rebind_on_tree=False
        with self.assertRaisesRegex(BridgeUnavailableError,'already claimed'):driver.confirm_ingame_decision_item_v1(KEY,'vivhite_courtier')
        self.assertEqual(len(driver.submissions),1)


class NavigationDriver(SyntheticDriver):
    """Owned GUI model; every submission still uses the production SDK method."""
    def __init__(self, directory: Path) -> None:
        super().__init__(directory)
        self.visible = False
        self.definition_available = False
        self.definition_matches = False
        self.query_barrier: threading.Barrier | None = None
        self.model_overrides: dict[str, object] = {}

    def close_detail(self) -> None:
        self.visible = False
        self.definition_available = False
        self.definition_matches = False

    def query_ingame_decision_item_v1(self, key: str) -> dict[str, object]:
        self.model_queries.append(key)
        packet: dict[str, object] = model(opening_binding(self.frame), selected=self.visible)
        packet.update(detail_definition_available=self.definition_available,
                      detail_definition_matches_target=self.definition_matches,
                      detail_decision_key=(KEY if self.definition_matches else 'other_decision')
                          if self.definition_available else '',
                      detail_actor_binding_verified=self.definition_available,
                      detail_actor_reference_key=7001 if self.definition_available else -1)
        packet.update(self.model_overrides)
        if self.query_barrier is not None:
            barrier, self.query_barrier = self.query_barrier, None
            barrier.wait(timeout=10)
        return packet

    def _execute_primitive_step(self, step: str, **kwargs: object) -> dict[str, object]:
        self.submissions.append((step, kwargs))
        if self.action_error is not None:
            raise self.action_error
        packet: dict[str, object] = ack(opening_binding(self.frame))
        self.visible = True
        self.definition_available = True
        self.definition_matches = True
        return packet


def _continuation_child(mode: str, directory: Path) -> int:
    """Executed in a new interpreter with fixture paths set before SDK import."""
    driver = NavigationDriver(directory)
    if mode == 'write-unknown':
        driver.action_error = TimeoutError('owned continuation lost ACK')
        try:
            driver.select_ingame_decision_item_v1(KEY)
        except TimeoutError:
            pass
        else:
            raise AssertionError('the lost ACK must remain unknown')
        expected_submissions = 1
    elif mode == 'reject-unknown':
        try:
            driver.select_ingame_decision_item_v1(KEY)
        except BridgeUnavailableError:
            pass
        else:
            raise AssertionError('a new interpreter replayed an unknown select')
        if driver.model_queries:
            raise AssertionError('unknown select must reject before model observation')
        expected_submissions = 0
    elif mode in ('write-verified', 'continue-verified'):
        result = driver.select_ingame_decision_item_v1(KEY, expected_revision=1)
        if result.get('postcondition_verified') is not True:
            raise AssertionError('actual SDK did not verify its owned selected model')
        expected_submissions = 1
    else:
        raise ValueError('unknown owned continuation mode')
    if len(driver.submissions) != expected_submissions:
        raise AssertionError('continuation submitted a different number of primitives')
    claims = list((directory/'ingame-decision-item-actions').glob('*.claim.json'))
    print(json.dumps({'mode': mode, 'pid': os.getpid(), 'submissions': len(driver.submissions),
                      'claims': len(claims), 'revision': driver.frame['revision']}))
    return 0


class DecisionNavigationTests(unittest.TestCase):
    def directory(self) -> Path:
        parent = os.environ.get('XAR_WHITE_DECISION_ACTION_TEST_ARTIFACTS')
        if parent:
            Path(parent).mkdir(parents=True, exist_ok=True)
        return Path(tempfile.mkdtemp(prefix='owned-navigation-', dir=parent))

    def test_invalid_actual_public_revision_rejects_before_claim_or_model(self) -> None:
        for revision in (True, 1.0, '1', None, -1):
            with self.subTest(revision=revision):
                driver = NavigationDriver(self.directory())
                driver.frame['revision'] = revision
                with self.assertRaises(BridgeUnavailableError):
                    driver.select_ingame_decision_item_v1(KEY)
                self.assertEqual(driver.model_queries, [])
                self.assertEqual(driver.submissions, [])
                self.assertFalse((driver.directory/'ingame-decision-item-actions').exists())

    def test_result_build_keeps_frozen_dataclass_identity_and_rejects_invalid_input(self) -> None:
        from xar_autoplayer.bridge.version_identity import CK3_12003, CK3_12004, NativeBuildIdentity
        for build in (CK3_12003, CK3_12004):
            raw = {'game_version': build.game_version,
                   'executable_sha256': build.executable_sha256.lower()}
            observed = result_build(json.loads(json.dumps(raw)))
            self.assertIsInstance(observed, NativeBuildIdentity)
            self.assertIs(observed, build)
        for invalid in (None, [], True, {}, {'game_version': True, 'executable_sha256': EXE_SHA256},
                        {'game_version': '1.20.0.3', 'executable_sha256': None},
                        {'game_version': '1.20.0.4', 'executable_sha256': EXE_SHA256}):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    result_build(invalid)

    def test_same_revision_verified_select_then_closed_null_gets_one_linked_attempt(self) -> None:
        driver = NavigationDriver(self.directory())
        first = driver.select_ingame_decision_item_v1(KEY, expected_revision=1)
        first_path = Path(first['action_claim_path'])
        first_bytes = first_path.read_bytes()
        verified_path = first_path.with_suffix('.verified.json')
        verified_bytes = verified_path.read_bytes()
        driver.close_detail()
        second = driver.select_ingame_decision_item_v1(KEY, expected_revision=1)
        self.assertEqual(driver.frame['revision'], 1)
        self.assertEqual(len(driver.submissions), 2)
        self.assertNotEqual(second['action_request_id'], first['action_request_id'])
        self.assertNotEqual(second['action_claim_path'], first['action_claim_path'])
        self.assertEqual(first_path.read_bytes(), first_bytes)
        self.assertEqual(verified_path.read_bytes(), verified_bytes)
        saved = json.loads(Path(second['action_claim_path']).read_bytes())
        predecessor = saved['action_identity']['navigation_predecessor']
        self.assertEqual(predecessor['request_id'], first['action_request_id'])
        self.assertEqual(Path(predecessor['claim']['path']), first_path)
        self.assertEqual(Path(predecessor['verified']['path']), verified_path)
        self.assertEqual(predecessor['claim']['bytes'], len(first_bytes))
        driver.close_detail()
        third = driver.select_ingame_decision_item_v1(KEY, expected_revision=1)
        self.assertNotEqual(third['action_claim_path'], second['action_claim_path'])
        self.assertEqual(len(driver.submissions), 3)

    def test_visible_completion_roundtrips_through_real_public_and_lyd_consumers(self) -> None:
        from xar_autoplayer.bridge.service import GameplayBridgeService
        # Use the real public case import root, without creating a tools.* alias.
        with patch.object(sys, 'path', [str(Path(__file__).resolve().parents[3]/'tools'), *sys.path]):
            from ck3_mod_acceptance_cases.lyd_i4_natural_expiry_adapter import validate_selected
        driver = NavigationDriver(self.directory())
        driver.frame['diagnostics']['bridge_pid'] = opening_binding(driver.frame)['game_pid']
        first = driver.select_ingame_decision_item_v1(KEY)
        service = object.__new__(GameplayBridgeService)
        with patch.object(service, 'driver', driver, create=True):
            observed = service.select_ingame_decision_item_v1(KEY, expected_revision=1)
        self.assertEqual(len(driver.submissions), 1)
        self.assertEqual(observed['completion_source'], 'observed_already_visible')
        self.assertIsNone(observed['native_ack'])
        self.assertIsNone(observed['action_request_id'])
        self.assertIsNone(observed['action_claim_path'])
        roundtrip = json.loads(json.dumps(observed))
        self.assertEqual(roundtrip, observed)
        actual = driver.query_ingame_decision_item_v1(KEY)
        observation = {'frame': driver.frame, 'model_after': actual}
        proof = validate_selected(roundtrip, driver.frame, observation, KEY)
        self.assertTrue(proof['postcondition_verified'])
        self.assertEqual(len(list(Path(first['action_claim_path']).parent.glob('*.claim.json'))), 1)

    def test_repeat_requires_complete_closed_null_and_leaves_old_claim_unchanged(self) -> None:
        for state in ('same-definition-hidden', 'different-definition-visible', 'different-definition-hidden'):
            with self.subTest(state=state):
                driver = NavigationDriver(self.directory())
                first = driver.select_ingame_decision_item_v1(KEY)
                driver.visible = state == 'different-definition-visible'
                driver.definition_available = True
                driver.definition_matches = state == 'same-definition-hidden'
                with self.assertRaises((BridgeUnavailableError, ValueError)):
                    driver.select_ingame_decision_item_v1(KEY)
                self.assertEqual(len(driver.submissions), 1)
                self.assertEqual(len(list(Path(first['action_claim_path']).parent.glob('*.claim.json'))), 1)

    def test_incomplete_or_malformed_closed_model_cannot_authorize_a_new_attempt(self) -> None:
        for changes in ({'detail_tree_complete': False}, {'detail_root_visible': None},
                        {'detail_definition_available': 0}, {'matching_row_count': True}):
            with self.subTest(changes=changes):
                driver = NavigationDriver(self.directory())
                driver.select_ingame_decision_item_v1(KEY)
                driver.close_detail()
                driver.model_overrides = changes
                with self.assertRaises((BridgeUnavailableError, ValueError)):
                    driver.select_ingame_decision_item_v1(KEY)
                self.assertEqual(len(driver.submissions), 1)

    def test_navigation_identity_and_file_pins_validate_before_typed_json_roundtrip(self) -> None:
        directory = self.directory()
        identity = {'game_pid': 12700, 'actor_id': 7001, 'episode_run_id': None,
                    'decision_key': KEY, 'action': 'select', 'public_revision': 1}
        parsed = parse_decision_navigation_identity(json.loads(json.dumps(identity)))
        self.assertEqual(parsed, identity)
        file_pin = {'path': str(directory/'original.claim.json'), 'bytes': 128, 'sha256': '0'*64}
        linked = {**identity, 'navigation_predecessor': {
            'request_id': 'original-request', 'claim': file_pin, 'verified': file_pin}}
        self.assertEqual(parse_decision_navigation_identity(json.loads(json.dumps(linked))), linked)
        invalid = []
        for field in ('game_pid', 'actor_id', 'public_revision'):
            for wrong in (True, 1.0, None):
                invalid.append({**identity, field: wrong})
        missing_episode = dict(identity)
        del missing_episode['episode_run_id']
        invalid.extend([missing_episode, {**identity, 'episode_run_id': []},
                        {**identity, 'navigation_predecessor': None},
                        {**identity, 'navigation_predecessor': {}},
                        {**identity, 'unexpected': None}])
        for field, wrong in (('bytes', True), ('bytes', 128.0), ('bytes', 0),
                             ('sha256', 'A'*64), ('path', 'relative.claim.json')):
            bad = deepcopy(linked)
            bad['navigation_predecessor']['claim'][field] = wrong
            invalid.append(bad)
        for raw in invalid:
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    parse_decision_navigation_identity(raw)

    def test_tampered_verified_predecessor_cannot_authorize_navigation(self) -> None:
        for field, bad in [('request_id', 'foreign-request'), ('queried_revision', True),
                           ('queried_revision', 1.0), ('postcondition_verified', False),
                           ('action_claim_path', 'foreign-claim')]:
            with self.subTest(field=field, bad=bad):
                driver = NavigationDriver(self.directory())
                first = driver.select_ingame_decision_item_v1(KEY)
                verified = Path(first['action_claim_path']).with_suffix('.verified.json')
                value = json.loads(verified.read_bytes())
                if field == 'request_id':
                    value[field] = bad
                else:
                    value['result'][field] = bad
                verified.write_text(json.dumps(value), encoding='utf-8')
                driver.close_detail()
                driver.model_queries.clear()
                with self.assertRaises(BridgeUnavailableError):
                    driver.select_ingame_decision_item_v1(KEY)
                self.assertEqual(driver.model_queries, [])
                self.assertEqual(len(driver.submissions), 1)

    def test_unknown_repeat_stays_locked_even_if_detail_is_currently_visible(self) -> None:
        driver = NavigationDriver(self.directory())
        driver.action_error = TimeoutError('owned lost ACK')
        with self.assertRaises(TimeoutError):
            driver.select_ingame_decision_item_v1(KEY)
        driver.visible = driver.definition_available = driver.definition_matches = True
        driver.action_error = None
        driver.model_queries.clear()
        with self.assertRaises(BridgeUnavailableError):
            driver.select_ingame_decision_item_v1(KEY)
        self.assertEqual(driver.model_queries, [])
        self.assertEqual(len(driver.submissions), 1)

    def test_competing_navigation_uses_the_same_exclusive_claim_slot(self) -> None:
        directory = self.directory()
        seed = NavigationDriver(directory)
        seed.select_ingame_decision_item_v1(KEY)
        barrier = threading.Barrier(2)
        drivers = [NavigationDriver(directory), NavigationDriver(directory)]
        for driver in drivers:
            driver.query_barrier = barrier

        def navigate(driver: NavigationDriver) -> bool:
            try:
                driver.select_ingame_decision_item_v1(KEY)
                return True
            except BridgeUnavailableError:
                return False

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(navigate, drivers))
        self.assertEqual(sorted(outcomes), [False, True])
        self.assertEqual(sum(len(driver.submissions) for driver in drivers), 1)
        self.assertEqual(len(list((directory/'ingame-decision-item-actions').glob('*.claim.json'))), 2)

    def test_verified_confirm_remains_once_only(self) -> None:
        driver = SyntheticDriver(self.directory(), action='confirm')
        driver.confirm_ingame_decision_item_v1(KEY, 'vivhite_courtier')
        with self.assertRaises(BridgeUnavailableError):
            driver.confirm_ingame_decision_item_v1(KEY, 'vivhite_courtier')
        self.assertEqual(len(driver.submissions), 1)

    def run_continuation_child(self, mode: str, directory: Path) -> dict[str, object]:
        temporary = directory/'child-temp'
        temporary.mkdir(exist_ok=True)
        environment = dict(os.environ)
        environment.update(XAR_AUTOPLAYER_STATE_DIR=str(directory/'state'),
                           XAR_WHITE_DECISION_ACTION_TEST_ARTIFACTS=str(directory),
                           TEMP=str(temporary), TMP=str(temporary), PYTHONDONTWRITEBYTECODE='1')
        # A new interpreter receives all fixture paths before importing this file or SDK.
        child = subprocess.run([sys.executable, '-B', '-X', 'utf8', str(Path(__file__).resolve()),
                                '--navigation-continuation-child', mode, str(directory)],
                               cwd=Path(__file__).resolve().parents[3], env=environment,
                               capture_output=True, text=True, timeout=30)
        self.assertEqual(child.returncode, 0, child.stdout+'\n'+child.stderr)
        result: object = json.loads(child.stdout)
        if not isinstance(result, dict):
            raise AssertionError('continuation child omitted its actual result')
        return {key: value for key, value in result.items()}

    def test_independent_processes_continue_verified_navigation_at_the_same_revision(self) -> None:
        directory = self.directory()
        first = self.run_continuation_child('write-verified', directory)
        second = self.run_continuation_child('continue-verified', directory)
        self.assertNotEqual(first['pid'], second['pid'])
        self.assertEqual(first['claims'], 1)
        self.assertEqual(second['claims'], 2)
        self.assertEqual(first['revision'], second['revision'])
        self.assertEqual(second['submissions'], 1)

    def test_independent_process_preserves_unknown_without_model_read_or_dispatch(self) -> None:
        directory = self.directory()
        first = self.run_continuation_child('write-unknown', directory)
        second = self.run_continuation_child('reject-unknown', directory)
        self.assertNotEqual(first['pid'], second['pid'])
        self.assertEqual(first['claims'], second['claims'])
        self.assertEqual(second['submissions'], 0)


if __name__=='__main__':
    if len(sys.argv) == 4 and sys.argv[1] == '--navigation-continuation-child':
        raise SystemExit(_continuation_child(sys.argv[2], Path(sys.argv[3])))
    unittest.main()
