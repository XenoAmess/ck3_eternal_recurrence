"""Synthetic estate refresh: portable proof/WAL and separate Source20 wiring.

The integration runner must install the exact Source20 candidate in RAM.
No constructor starts an endpoint, and no game/native commands are sent.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from xar_autoplayer.bridge import driver_state_wal_v1 as wal, native_driver as nd
from xar_autoplayer.bridge import succession_binding_refresh_wal_v1 as policy
from xar_autoplayer.bridge.ingame_decision_outcome_contract import reject_unresolved_claims
from xar_autoplayer.bridge.succession_transition_contract import freeze_succession_expectation_v1
from xar_autoplayer.bridge.turn_bundle_contract import build_turn_bundle_v1
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.environment import write_bytes_atomic
from xar_autoplayer.native_session import NATIVE_SESSION_CHECKPOINT_FILENAME
from test_driver_state_wal_production_v1 import driver as fixture_driver, daily
from test_turn_bundle_v1 import _snapshot, _root

SCRATCH = None
PEAK_BOUND = 0
WRITE_COUNT = 0


def configure_scratch(root):
    global SCRATCH
    SCRATCH = Path(root).resolve(strict=True)


def bounded_write(path, data, **kwargs):
    global PEAK_BOUND, WRITE_COUNT
    path = Path(path).resolve()
    if SCRATCH is None or not path.is_relative_to(SCRATCH) or len(data) > 8192:
        raise ValueError("synthetic write outside scratch or body cap")
    total = sum(p.stat().st_size for p in SCRATCH.rglob('*') if p.is_file())
    # Includes an entire extra atomic temporary, not just the final file size.
    PEAK_BOUND = max(PEAK_BOUND, total + len(data))
    if PEAK_BOUND > 65536:
        raise ValueError("scratch peak bound exceeded")
    WRITE_COUNT += 1
    write_bytes_atomic(path, data, **kwargs)


def frame(revision=100):
    value = _snapshot()
    hello = dict(pid=12345, ck3_build_match=True, expected_ck3_version=CK3_12004.game_version,
                 expected_ck3_sha256=CK3_12004.executable_sha256)
    value.update(snapshot_id=f"native:{revision}", revision=revision, native_revision=revision,
                 date_raw=2400, source="injected-dll-named-pipe", map_ready=True,
                 one_life_terminal=False, episode_character_id=value['played_character']['character_id'],
                 episode_run_id="native-estate-refresh-fixture", local_player_id=42,
                 diagnostics=dict(connected=True, pipe_name=r"\\.\pipe\xar-wal-production-test",
                                  bridge_pid=12345, connection_generation=1, hello=hello))
    return value


def bundle(snapshot):
    root = _root()
    root['binding'].update({k: snapshot[k] for k in ('snapshot_id', 'revision', 'native_revision', 'date_raw')})
    root['binding']['expected_revision'] = snapshot['revision']
    root['campaign_root_context'].update(snapshot_revision=snapshot['native_revision'], date_raw=snapshot['date_raw'])
    return build_turn_bundle_v1(snapshot, root)


def publish(obj, snapshot):
    obj.snapshot = deepcopy(snapshot)
    obj.state._connected = True
    obj.state._public_revision = snapshot['revision']
    obj.state._connection_generation = snapshot['diagnostics']['connection_generation']
    obj.state._hello = deepcopy(snapshot['diagnostics']['hello'])
    obj.state._semantic_snapshot = {**deepcopy(snapshot), 'revision': snapshot['native_revision']}


def fields(snapshot):
    expectation = freeze_succession_expectation_v1(bundle(snapshot),
        episode_run_id=snapshot['episode_run_id'], episode_character_id=snapshot['episode_character_id'])
    return dict(format_version=2, pipe_name=snapshot['diagnostics']['pipe_name'], bridge_pid=12345,
                episode_character_id=snapshot['episode_character_id'], episode_run_id=snapshot['episode_run_id'],
                last_checkpoint=None, rollback_war_failure=None, rollback_war_failures=[],
                managed_restore_transaction=None, succession_expectation=expectation,
                succession_lifecycle=nd.legacy_rogue_one_life_binding_v1(), campaign_goal=None)


def proof_driver(old, new):
    obj = SimpleNamespace(state=nd.NativeProtocolState(old['diagnostics']['pipe_name']),
        pipe_name=old['diagnostics']['pipe_name'], _session_bridge_pid=12345,
        _episode_character_id=old['episode_character_id'], _episode_run_id=old['episode_run_id'],
        _driver_state_wal_barrier_generation=1, _driver_state_wal_committed_rows=2,
        _driver_state_wal_barrier_required=False, _driver_state_dirty=False,
        _driver_state_error=None, _succession_reconciliation=None,
        _driver_state_wal_document={}, _command_history=[{}, {}], state_dir=Path('.'),
        allow_driver_state_wal_v1=True)
    current = fields(old)
    obj._driver_state_wal_scalar_fields_locked_v1 = lambda: deepcopy(current)
    publish(obj, old)
    policy.finish_refresh(obj, old, current, 0)
    current.clear(); current.update(fields(new)); publish(obj, new)
    return obj


class PortableProofAndReplay(unittest.TestCase):
    def test_single_use_owner_proof_and_cross_direction_aliases(self):
        old, new = frame(), frame(101)
        obj = proof_driver(old, new)
        before, after = fields(old), fields(new)
        proof = policy.begin_refresh(obj, new, before, after)
        self.assertIsNotNone(proof)
        new['diagnostics']['hello']['pid'] = 999
        after['succession_expectation']['binding']['snapshot_id'] = 'mutated'
        rows = [dict(index=3, command='query-campaign-root-context-v1', ok=True)]
        obj._driver_state_dirty = False
        good = fields(frame(101))
        self.assertTrue(policy.consume_refresh(obj, proof, before, good, rows, lambda s: s.startswith('query-')))
        self.assertFalse(policy.consume_refresh(obj, proof, before, good, rows, lambda s: True))
        other = proof_driver(old, frame(101))
        another = policy.begin_refresh(obj, frame(101), before, good)
        self.assertFalse(policy.consume_refresh(other, another, before, good, rows, lambda s: True))

    def test_explicit_leaf_allowlist_rejects_business_type_shape_and_owner_drift(self):
        old, new = frame(), frame(101)
        changes = {
            'heir': lambda f: f['succession_expectation'].update(expected_successor_character_id=99),
            'estate': lambda f: f['succession_expectation']['title_expectations'][0]['title'].update(title_id=999),
            'title_extra': lambda f: f['succession_expectation']['title_expectations'][0]['title'].update(extra='new'),
            'title_order': lambda f: f['succession_expectation']['title_expectations'].reverse(),
            'risk': lambda f: f['succession_expectation'].update(risk_state='single_successor'),
            'episode': lambda f: f.update(episode_run_id='other'),
            'owner': lambda f: f.update(bridge_pid=999),
            'checkpoint': lambda f: f.update(last_checkpoint={'new': True}),
            'goal': lambda f: f.update(campaign_goal={'new': True}),
            'lifecycle': lambda f: f.update(succession_lifecycle={'new': True}),
            'restore': lambda f: f.update(managed_restore_transaction={'unknown': True}),
            'extra_scalar': lambda f: f.update(unknown_field=True),
            'bool_int': lambda f: f.update(bridge_pid=True),
            'backward_native': lambda f: f['succession_expectation']['binding'].update(native_revision=99, snapshot_id='native:99'),
            'opaque_snapshot': lambda f: f['succession_expectation']['binding'].update(snapshot_id='opaque'),
            'wrong_source': lambda f: f['succession_expectation']['binding'].update(revision=102),
        }
        for name, mutate in changes.items():
            with self.subTest(name=name):
                obj = proof_driver(old, new); after = fields(new); mutate(after)
                self.assertIsNone(policy.begin_refresh(obj, new, fields(old), after))
        for key, value in [('connection_generation', 2), ('bridge_pid', None), ('hello', {})]:
            with self.subTest(owner=key):
                obj = proof_driver(old, new); bad = deepcopy(new); bad['diagnostics'][key] = value
                self.assertIsNone(policy.begin_refresh(obj, bad, fields(old), fields(new)))
        obj = proof_driver(old, new)
        obj.state._public_revision += 1
        self.assertIsNone(policy.begin_refresh(obj, new, fields(old), fields(new)))

    def test_unchanged_real_wal_replays_entire_refreshed_state_fields(self):
        old, new = fields(frame()), fields(frame(101))
        base = wal._canonical({**old, 'command_history': []})
        sealed = wal.sealed_base_bytes(base)
        journal = wal.append_delta(wal.new_journal_header(sealed, 0),
            [dict(index=1, command='query-campaign-root-context-v1', ok=True)], new)
        replay, _ = wal.replay(sealed, wal._canonical(journal))
        self.assertEqual(policy._json({k: v for k, v in replay.items() if k != 'command_history'}), policy._json(new))
        self.assertEqual(replay['command_history'], journal['entries'][0]['history_rows'])


class Source20DriverIntegration(unittest.TestCase):
    def setUp(self):
        if SCRATCH is None:
            raise RuntimeError('run the admitted Source20 qualifier with configured scratch')
        self.temp = tempfile.TemporaryDirectory(prefix='case-', dir=SCRATCH)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.writer = patch.object(nd, 'write_bytes_atomic', side_effect=bounded_write)
        self.writer.start(); self.addCleanup(self.writer.stop)
        self.environment_writer = patch('xar_autoplayer.environment.write_bytes_atomic', side_effect=bounded_write)
        self.environment_writer.start(); self.addCleanup(self.environment_writer.stop)
        self.journal_writer = patch.object(wal, 'publish_journal', wraps=wal.publish_journal)
        self.journal_writer.start(); self.addCleanup(self.journal_writer.stop)
        self.obj = fixture_driver(self.root)
        self.obj._succession_binding_wal_anchor_v1 = None
        initial = frame()
        self.obj._episode_character_id = initial['episode_character_id']
        self.obj._episode_run_id = initial['episode_run_id']
        self.obj._succession_reconciliation = None
        self.obj.state = nd.NativeProtocolState(self.obj.pipe_name)
        self.reads = 0
        def existing_snapshot():
            self.reads += 1
            return deepcopy(self.obj.snapshot)
        self.obj.take_internal_semantic_snapshot = existing_snapshot
        publish(self.obj, initial)
        self.retain(initial)
        self.path = self.obj._native_driver_state_path()
        self.assertIsNotNone(self.obj._succession_binding_wal_anchor_v1, self.obj._driver_state_error)

    def retain(self, snapshot):
        return self.obj.retain_succession_expectation_v1(bundle(snapshot), expected_revision=snapshot['revision'])

    def deferred(self, revision):
        next_frame = frame(revision)
        publish(self.obj, next_frame)
        old = self.obj._driver_state_wal_committed_rows
        self.obj._record_command('query-campaign-root-context-v1', ok=True, result={'status': 'observed'})
        self.assertEqual(self.obj._driver_state_wal_committed_rows, old, 'readonly row was prematurely committed')
        return next_frame

    def activated(self):
        self.retain(self.deferred(101))
        self.assertEqual(json.loads(self.path.read_bytes())['format_version'], 3, self.obj._driver_state_error)
        return self.path.read_bytes()

    def test_real_query_record_retain_run_replays_identically_and_reads_once(self):
        frozen = self.activated()
        previous_reads = self.reads
        returned = self.retain(self.deferred(102))
        self.assertEqual(self.reads, previous_reads + 1, 'new snapshot observation introduced')
        self.assertEqual(self.path.read_bytes(), frozen)
        replay = self.obj._read_driver_state()
        self.assertEqual(replay['succession_expectation'], returned)
        self.assertEqual(replay['command_history'], self.obj._command_history)
        self.assertEqual(replay['succession_expectation']['binding'], fields(frame(102))['succession_expectation']['binding'])
        self.assertEqual(len(self.obj._driver_state_wal_document['entries']), 2)

    def test_no_row_and_reconciliation_drift_keep_full_barriers(self):
        self.activated()
        before_generation = self.obj._driver_state_wal_barrier_generation
        publish(self.obj, frame(102)); self.retain(frame(102))
        self.assertGreater(self.obj._driver_state_wal_barrier_generation, before_generation)
        self.assertEqual(json.loads(self.path.read_bytes())['format_version'], 2)
        self.obj._succession_reconciliation = {'unreviewed': True}
        self.retain(self.deferred(103))
        self.assertEqual(json.loads(self.path.read_bytes())['format_version'], 2)

    def test_unknown_row_failed_barrier_and_prefix_edit_cannot_hitchhike(self):
        self.activated()
        with patch.object(nd, 'write_bytes_atomic', side_effect=OSError('synthetic failed unknown barrier')):
            self.obj._record_command('submit-once-action', ok=False, error='UNKNOWN')
        self.assertTrue(self.obj._driver_state_wal_barrier_required)
        self.assertIsNone(self.obj._succession_binding_wal_anchor_v1)
        self.retain(self.deferred(102))
        self.assertEqual(json.loads(self.path.read_bytes())['format_version'], 2)
        self.assertEqual(self.obj._read_driver_state()['command_history'], self.obj._command_history)
        self.obj._command_history[0]['error'] = 'prefix edited'
        self.obj._driver_state_history_json.invalidate()
        self.retain(self.deferred(103))
        self.assertEqual(json.loads(self.path.read_bytes())['format_version'], 2)

    def test_dirty_race_consumes_proof_and_falls_back_to_full(self):
        self.activated()
        original = policy.consume_refresh
        def raced(driver, *args):
            driver._driver_state_dirty = True
            return original(driver, *args)
        with patch.object(policy, 'consume_refresh', side_effect=raced):
            self.retain(self.deferred(102))
        self.assertEqual(json.loads(self.path.read_bytes())['format_version'], 2)

    def _publication_failure(self, after_replace):
        self.activated()
        before = self.obj._read_driver_state()
        snap = self.deferred(102)
        real_publish = wal.publish_journal
        def fail(path, doc, writer):
            if after_replace:
                real_publish(path, doc, writer)
            raise OSError('synthetic before/after real publication')
        with patch.object(wal, 'publish_journal', side_effect=fail):
            self.retain(snap)
        self.assertTrue(self.obj._driver_state_wal_barrier_required)
        self.assertTrue(self.obj._driver_state_dirty)
        self.assertIsNone(self.obj._succession_binding_wal_anchor_v1)
        replay, _ = wal.load_pair(self.path)
        expected = fields(snap)['succession_expectation'] if after_replace else before['succession_expectation']
        self.assertEqual(replay['succession_expectation'], expected)
        self.assertEqual(len(replay['command_history']), len(before['command_history']) + int(after_replace))
        journal = self.path.with_name(wal.FILENAME).read_bytes()
        if after_replace:
            # The old in-memory journal cannot overwrite a published suffix.
            self.obj._persist_driver_state()
            self.assertEqual(self.path.with_name(wal.FILENAME).read_bytes(), journal)
            self.assertIsNotNone(self.obj._driver_state_error)
            wal.consolidate_closed_pair(self.path, owner_closed=True, write_atomic=bounded_write)
            self.assertEqual(wal.load_pair(self.path)[0]['succession_expectation'], expected)
        else:
            self.obj._persist_driver_state()
            self.assertEqual(json.loads(self.path.read_bytes())['format_version'], 2)

    def test_actual_write_before_publication_failure_recovers_old_commit(self):
        self._publication_failure(False)

    def test_actual_write_after_publication_failure_recovers_new_suffix_once(self):
        self._publication_failure(True)

    def test_save_close_cold_replay_and_unresolved_once_remain_strict(self):
        self.activated()
        claim_dir = self.path.parent / 'ingame-decision-item-actions'
        identity = dict(game_pid=12345, actor_id=self.obj._episode_character_id,
                        episode_run_id=self.obj._episode_run_id, decision_key='fixture_decision', action='confirm')
        claim = claim_dir / 'once.claim.json'
        claim_bytes = json.dumps(dict(action_identity=identity, status='claimed_result_unknown_no_retry')).encode()
        bounded_write(claim, claim_bytes)
        self.retain(self.deferred(102))
        self.assertEqual(claim.read_bytes(), claim_bytes)
        with self.assertRaises(ValueError):
            reject_unresolved_claims(claim_dir, identity)
        restored = self.root / 'closed-restore'
        restored_claim = restored / 'native-session' / claim_dir.name / claim.name
        bounded_write(restored_claim, claim_bytes)
        wal.materialize_closed_directory(self.obj.state_dir, restored, owner_closed=True,
            expected_base_sha256=hashlib.sha256(self.path.read_bytes()).hexdigest(),
            expected_journal_sha256=hashlib.sha256(self.path.with_name(wal.FILENAME).read_bytes()).hexdigest())
        self.assertEqual(json.loads((restored / 'native-session/driver-state.json').read_bytes())['succession_expectation'],
                         fields(frame(102))['succession_expectation'])
        with self.assertRaises(ValueError):
            reject_unresolved_claims(restored_claim.parent, identity)
        checkpoint = dict(name=NATIVE_SESSION_CHECKPOINT_FILENAME, size=4, sha256=hashlib.sha256(b'save').hexdigest(), date_raw=2400,
                          history_index=len(self.obj._command_history) + 1,
                          episode_character_id=self.obj._episode_character_id, episode_run_id=self.obj._episode_run_id,
                          succession_lifecycle=self.obj._succession_lifecycle)
        self.obj._last_checkpoint = checkpoint
        receipt = self.obj._record_command('save-checkpoint', ok=True, result={'checkpoint': checkpoint})
        self.assertEqual(receipt['status'], 'replaced')
        self.assertTrue(receipt['save_binding_verified'])
        self.assertIsNone(self.obj._succession_binding_wal_anchor_v1)
        self.assertEqual(json.loads(self.path.read_bytes())['format_version'], 2)
        # A same-instance cold load cannot manufacture a provenance anchor.
        self.obj._succession_binding_wal_anchor_v1 = None
        publish(self.obj, frame(103)); self.retain(frame(103))
        self.retain(self.deferred(104))
        closed = []
        self.obj.endpoint = SimpleNamespace(close=lambda: closed.append(True))
        with patch('xar_autoplayer.bridge.normal_exit_pending_observer_v1.dispose_normal_exit_observer_v1'):
            self.obj.close()
        self.assertEqual(closed, [True])
        self.assertEqual(json.loads(self.path.read_bytes())['format_version'], 2)
        self.assertFalse(self.path.with_name(wal.FILENAME).exists())
        self.assertEqual(claim.read_bytes(), claim_bytes)
        with self.assertRaises(ValueError):
            reject_unresolved_claims(claim_dir, identity)
