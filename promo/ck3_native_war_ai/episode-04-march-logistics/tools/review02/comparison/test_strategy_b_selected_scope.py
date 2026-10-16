"""Selected B query scope with full snapshot roster; no game or SDK requests."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'split_merge'))
import root_relay as R
import strategy_b_stages as B


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=getattr(sys, '_B_scope_scratch', None))
        self.addCleanup(self.temp.cleanup)
        self.assets = Path(self.temp.name)
        self.frame = {'snapshot_id': 'scope-only-unit', 'revision': 7, 'native_revision': 6,
            'date_raw': 1000, 'episode_run_id': 'scope-only', 'paused': True, 'map_ready': True,
            'played_character': {'character_id': 9, 'alive': True},
            'diagnostics': {'bridge_pid': 1, 'connection_generation': 2, 'connected': True,
                'hello': {'expected_ck3_version': '1.20.0.4', 'expected_ck3_sha256': R.EXE_SHA,
                    'game_adapter_status': 'ready', 'ck3_build_match': True, 'pid': 1, 'connection_generation': 2}},
            'player_armies': [self.unit(93), self.unit(18), self.unit(16777321)]}
        self.path = self.assets / 'state-a01/native-session/army-query-history-results/selected.json'
        self.path.parent.mkdir(parents=True)
        self.snapshot = self.put(self.assets / 'snapshot.json', {'body': self.frame})
        self.response = self.put(self.assets / 'response.json', {'body': {}})
        self.live = R.Relay.__new__(R.Relay)
        self.live.assets = self.assets
        self.live.a = SimpleNamespace(army_id=93, stage='rest')
        self.live.binding = {'pid': 1, 'generation': 2, 'actor': 9, 'episode': 'scope-only'}
        self.live.snapshot = lambda name: (deepcopy(self.frame), {'response': R.pin(self.snapshot)})
        self.live.normalize = lambda records: []
        self.live.observation = SimpleNamespace(compare_split_merge_cohorts=lambda old, new: {},
            read_bound_current_commander=lambda *a, **kw: 11)
        self.calls = []
        self.force_status = None
        self.force_scope = None
        self.reported_bytes = None
        self.live.request = self.request

    @staticmethod
    def unit(aid):
        return {'army_id': aid, 'source': 'native', 'owner_character_id': 9,
                'controllable': aid != 16777321, 'current_province_id': 50}

    @staticmethod
    def put(path, value):
        path.write_text(json.dumps(value), encoding='utf-8')
        return path

    def request(self, name, tool, arguments):
        self.calls.append((tool, deepcopy(arguments)))
        refs = {'response': R.pin(self.response)}
        if tool == 'ck3_get_capabilities':
            return {'body': {'bridge_capabilities': list(R.READ_CAPS)}}, refs
        if tool == 'ck3_query_army_commander_candidates_v1':
            aid = arguments['army_id']
            body = {'accepted': True, 'read_only': True, 'queried_snapshot_id': self.frame['snapshot_id'],
                'queried_revision': 7, 'queried_native_revision': 6, 'army_commander_candidates': {
                    'army_id': aid, 'native_carmy_id': aid + 1000, 'date_raw': 1000,
                    'snapshot_revision': 7, 'current_commander': {'character_id': 11}}}
            path = self.put(self.assets / ('commander-' + str(aid) + '.json'), {'body': body})
            return {'body': body}, {'response': R.pin(path)}
        self.assertEqual(tool, 'ck3_query_army_strengths')
        ids = arguments['army_ids']
        rows = []
        for aid in ids:
            row = {'army_id': aid, 'native_carmy_id': aid + 1000, 'status': 'available',
                'regiment_count': 0, 'current_soldiers': 0, 'maximum_soldiers': 0,
                'regiment_strengths': [], 'regiment_replenishment_records_v1': [],
                'native_army_resolution_v1': {'status': 'available', 'ready': True,
                    'branch': 'resolved', 'entry_full_id': aid + 1000},
                'current_supply_raw': 10000000, 'current_supply_scale': 100000,
                'current_supply_capacity_raw': 10000000, 'current_supply_capacity_scale': 100000}
            if aid == 16777321:
                row.update(status='unavailable', unavailable_reason='native_carmy_not_found')
            rows.append(row)
        query = {'accepted': True, 'status': self.force_status or ('partial' if 16777321 in ids else 'available'),
            'query_sequence': 1, 'army_strengths_profile': 'ordinary_core_v1',
            'army_strengths_query_scope': {'army_ids': self.force_scope if self.force_scope is not None else ids,
                                         'published_scope_status': 'available'},
            'army_strengths': rows, 'queried_connection_generation': 2}
        for key in ('snapshot_id', 'revision', 'native_revision', 'date_raw', 'episode_run_id'):
            query['queried_' + key] = self.frame[key]
        self.put(self.path, query)
        raw = R.pin(self.path)
        return {'request': {'request_id': 'unit-strength'}, 'army_history_evidence': {
            'machine_id': R.MACHINE, 'request_id': 'unit-strength', 'query_sequence': 1,
            'raw_result_reference': {**raw, 'bytes': self.reported_bytes or raw['bytes'],
                'kind': 'complete-driver-army-query-result-json-v1', 'wire_bytes_preserved': False}}}, refs

    def stage(self):
        value = B.BStages.__new__(B.BStages)
        value.r, value.live = R, self.live
        value.evidence = SimpleNamespace(file_limit=lambda path: 16 * 1024 * 1024)
        value.state = {'phase': 'rest', 'main_id': 93, 'child_id': 18}
        return value

    def test_selected_pair_preserves_entire_snapshot_and_complete_driver(self):
        original = deepcopy(self.frame)
        packet = self.live.packet('pair', army_ids=[93, 18], raw_file_limit=lambda path: 16 * 1024 * 1024)
        out = self.stage().full_packet(packet)
        self.assertEqual(set(out['rows']), {18, 93})
        self.assertEqual(set(R.roster(out['frame'])), {18, 93, 16777321})
        self.assertEqual(self.frame, original)
        self.assertEqual(packet['unrelated_physical_DATA_coverage'], 'not_requested')
        self.assertEqual(R.load(packet['refs']['strength_raw']['path'])['army_strengths_query_scope']['army_ids'], [18, 93])
        self.assertEqual([args['army_ids'] for tool, args in self.calls if tool == 'ck3_query_army_strengths'], [[18, 93]])
        self.assertEqual(set(out['assigned_commanders']), {18, 93})

    def test_default_R09_still_queries_full_roster_and_retains_unavailable_row(self):
        packet = self.live.packet('legacy')
        self.assertIsNone(packet['strategy_army_ids'])
        self.assertEqual(len(packet['query']['army_strengths']), 3)
        self.assertEqual(packet['excluded_unavailable_cohorts'][0]['army_id'], 16777321)
        self.assertEqual(packet['qualified_scope'], 'selected available pair; unchanged other available cohorts; explicit unavailable row excluded')

    def test_selected_partial_or_wrong_scope_is_refused_without_row_deletion(self):
        self.force_status = 'partial'
        with self.assertRaisesRegex(RuntimeError, 'selected query unavailable'):
            self.live.packet('partial', army_ids=[18, 93])
        self.assertEqual(R.load(self.path)['status'], 'partial')
        self.force_status = None
        self.force_scope = [93]
        with self.assertRaisesRegex(RuntimeError, 'query scope/profile differs'):
            self.live.packet('wrong-scope', army_ids=[18, 93])

    def test_split_child_comes_from_full_snapshot_delta_and_ambiguous_delta_refuses(self):
        before = [93, 16777321]
        self.assertEqual(R.selected_query_ids(self.frame, [93], split_before_roster=before), [18, 93])
        self.assertEqual(len(self.frame['player_armies']), 3)
        for bad in ([93], [93, 18, 16777321], [93, 99, 16777321]):
            with self.subTest(old=bad), self.assertRaisesRegex(RuntimeError, 'exact full snapshot addition'):
                R.selected_query_ids(self.frame, [93], split_before_roster=bad)

    def test_oversized_reference_stops_before_driver_hash_or_read(self):
        self.reported_bytes = 18672099
        with patch.object(R, 'driver_raw_pin', side_effect=AssertionError('must not hash oversized Driver')) as hashed:
            with self.assertRaisesRegex(RuntimeError, 'exceeds admitted input limit'):
                self.live.packet('oversize', army_ids=[18, 93], raw_file_limit=lambda path: 16 * 1024 * 1024)
            hashed.assert_not_called()
        packet = {'refs': {'strength_raw': {'path': str(self.path), 'bytes': 18672099}}}
        with patch.object(R, 'verify_pin', side_effect=AssertionError('must not read oversized Driver')) as verified:
            with self.assertRaisesRegex(RuntimeError, 'exceeds admitted input limit'):
                self.stage().full_packet(packet)
            verified.assert_not_called()

    def test_actual_strategy_ids_switch_to_survivor_and_snapshot_absence_refuses(self):
        stage = self.stage()
        self.assertEqual(stage.strategy_ids(), [18, 93])
        stage.state.update(phase='merged', surviving_army_id=18)
        self.assertEqual(stage.strategy_ids(), [18])
        with self.assertRaisesRegex(RuntimeError, 'absent from complete snapshot'):
            R.selected_query_ids(self.frame, [99])
        with self.assertRaisesRegex(RuntimeError, 'distinct selected Army IDs'):
            R.selected_query_ids(self.frame, [93, 93])


if __name__ == '__main__':
    unittest.main(verbosity=2)
