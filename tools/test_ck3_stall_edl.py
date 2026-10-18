from copy import deepcopy
import hashlib
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import ck3_stall_edl as e
from tools import collect_stall_edl as collector
from tools import ck3_recording_stall_hook as hook


class StallMetadataIntegration(unittest.TestCase):
    def test_new_text_recording_keeps_metadata_collector_without_legacy_window_identity(self):
        with tempfile.TemporaryDirectory() as folder:
            session=Path(folder)/'session';root=session/'recordings/new';root.mkdir(parents=True)
            source=session/'STARTED.json'
            publisher={'schema':'xar.ck3.decision-text-publisher/v1','status':'DECISION_TEXT_PUBLISHER_STARTED',
                'qualified_for_game_recording':True,'session':str(session),'game':{'pid':10,'creation_filetime':100},
                'decision_text_file':str(session/'decision.txt')}
            raw=json.dumps(publisher).encode();source.write_bytes(raw)
            reference={'path':str(source),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
            job={'session_id':'new','receipt_root':str(root),'recording_root':str(session/'recordings'),'capture_mode':'game_decision_text',
                'pid':10,'game_creation_filetime':100,'overlay':None,'decision_text_publisher':publisher,
                'decision_text_publisher_receipt':reference,'decision_text_file':publisher['decision_text_file']}
            started={'state':'recording','at_utc':'2026-10-17T00:00:00Z','game_pid':10,'game_creation_filetime':100,
                'capture_mode':'game_decision_text','decision_source':True,'decision_text_publisher':publisher,
                'decision_settings':{'read_from_file':True,'file':publisher['decision_text_file']}}
            e.create(root/'job.json',job);e.create(root/'started.json',started)
            calls=[]
            def launch(*args,**kwargs):calls.append(args);return type('SyntheticChild',(),{'pid':99})()
            result=hook.start_collector(job,started,python='synthetic-no-execution.exe',popen=launch)
            self.assertEqual(len(calls),1)
            self.assertFalse(result['runtime_qualified'])
            segment=e.read(root/'stall-edits/seed.json')['segments'][0]
            self.assertTrue(segment['source_decision_text_retained'])
            self.assertEqual(segment['decision_source_kind'],'independent_text')
            self.assertNotIn('overlay_pid',segment)
            with self.assertRaisesRegex(ValueError,'publisher/OBS'):
                hook.start_collector(job,{**started,'decision_text_publisher':{}},popen=lambda *a,**k:self.fail('Foreign source launched a child'))

    def setup_recording(self, root):
        receipt = root / 'capture-a'
        receipt.mkdir()
        session = root / 'campaign'
        session.mkdir()
        job = {'session_id': 'capture-a', 'receipt_root': str(receipt),
            'recording_root': str(root), 'capture_mode': 'game_decision',
            'pid': 10, 'game_creation_filetime': 100,
            'overlay': {'session': str(session), 'game_pid': 10, 'game_creation_filetime': 100}}
        started = {'state': 'recording', 'at_utc': '2026-10-17T00:00:00Z',
            'game_pid': 10, 'game_creation_filetime': 100,
            'capture_mode': 'game_decision', 'decision_source': True}
        e.create(receipt / 'job.json', job)
        e.create(receipt / 'started.json', started)
        return job, started

    def test_actual_started_binding_requests_one_hidden_metadata_child(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            job, started = self.setup_recording(root)
            calls = []
            class Child: pid = 99
            def launch(*args, **kwargs):
                calls.append((args, kwargs))
                return Child()
            result = hook.start_collector(job, started, python='verified-python.exe', popen=launch)
            self.assertEqual(result['status'], 'requested')
            self.assertFalse(result['runtime_qualified'])
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0][0][0][0], 'verified-python.exe')
            self.assertEqual(result['spec']['windows_creationflags'], 'CREATE_NO_WINDOW')
            policy = e.read(root / 'capture-a/stall-edits/policy.json')
            self.assertEqual((policy['keep_error_head_seconds'], policy['keep_recovery_tail_seconds'],
                              policy['max_recorded_middle_seconds']), (2, 2, 4))
            seed = e.read(root / 'capture-a/stall-edits/seed.json')
            self.assertEqual(seed['intervals'], [])
            self.assertTrue(seed['segments'][0]['source_decision_overlay_retained'])
            self.assertTrue(hook.request_stop(job))
            self.assertTrue((root / 'capture-a/stall-edits/STOP-COLLECTOR').is_file())
            with self.assertRaises(FileExistsError):
                hook.start_collector(job, started, popen=launch)
            self.assertEqual(len(calls), 1)

    def test_not_started_or_foreign_capture_never_launches_child(self):
        with tempfile.TemporaryDirectory() as folder:
            job, started = self.setup_recording(Path(folder))
            for change in ({'state': 'requested'}, {'game_creation_filetime': 101}, {'decision_source': False}):
                with self.subTest(change=change):
                    with self.assertRaises(ValueError):
                        hook.start_collector(job, {**started, **change},
                            popen=lambda *a, **k: self.fail('Unqualified recording launched a child'))
            result = hook.start_collector({**job, 'capture_mode': 'game_only'}, started)
            self.assertFalse(result['child_launched'])

    def test_recorder_keeps_capture_active_if_metadata_dependency_fails(self):
        from tools import ck3_obs_capture as capture
        with tempfile.TemporaryDirectory() as folder:
            job, started = self.setup_recording(Path(folder))
            root = Path(job['receipt_root'])
            with patch.object(hook, 'start_collector', side_effect=ImportError('missing metadata dependency')):
                self.assertIsNone(capture._start_stall_edl_metadata(job, root))
            failure = e.read(root / 'stall-edl-start-failed.json')
            self.assertTrue(failure['metadata_only_failure'])
            self.assertFalse(failure['recording_stop_requested_by_metadata_failure'])
            self.assertIn('missing metadata dependency', failure['error'])

    def test_current_snapshot_is_immutable_and_late_notice_does_not_extend_wait(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            store = root / 'metadata'
            store.mkdir()
            config = {'segments': [{'session_id': 'capture-a', 'started_at_utc': '2026-10-17T00:00:00Z',
                'duration_seconds': 3600, 'game_pid': 10, 'game_creation_filetime': 100,
                'source_decision_overlay_retained': True}],
                'intervals': [{'id': 'wait-a', 'start_at_utc': '2026-10-17T00:00:10Z',
                    'end_at_utc': None, 'original_auto_sequence': 9,
                    'source_sdk_prefix': 'old', 'game_pid': 10}]}
            auto = {'request': {'tool': 'ck3_auto_turn'}, 'ended_at_utc': '2026-10-17T00:10:10Z',
                'result': {'structured_content': {'status': 'executed', 'selected_step': 'life-advance',
                    'result': {'starting_date_raw': 100, 'ending_date_raw': 124}}}}
            auto_path = root / 'auto.json'
            e.create(auto_path, auto)
            state = {'schema': 'xar.runtime-repair-status/v1', 'incident_id': 'issue',
                'binding': {'game_pid': 10, 'game_creation_filetime': 100, 'sdk_prefix': 'old'},
                'original_request': {'sequence': 9}, 'pause_reason': 'synthetic pause',
                'phase': 'resolved', 'resolved_at_utc': '2026-10-17T00:20:00Z',
                'recovery_proof': {'kind': 'actual_settled_AUTO_and_paired_MET_calendar_progress',
                    'AUTO': e.pin(auto_path), 'actual_progress_ended_at_utc': auto['ended_at_utc'],
                    'actual_date_delta_raw': 24, 'Game_pid': 10}}
            source = root / 'CURRENT.json'
            e.create(source, state)
            original = source.read_bytes()
            target, result = collector.consume(e.build(config), source, store,
                Path(hook.__file__).with_name('recording-stall-policy.json'))
            source.write_text('{}')
            snapshot = next(store.glob('*-STATUS-IMMUTABLE.json'))
            self.assertEqual(snapshot.read_bytes(), original)
            self.assertEqual(result['intervals'][0]['end_at_utc'], auto['ended_at_utc'])
            self.assertEqual(result['intervals'][0]['edited_middle_seconds'], 4)
            self.assertEqual(result['markers'][0]['at_utc'], '2026-10-17T00:20:00Z')
            self.assertEqual(result['final_render_qualification'],
                'ACTUAL_PTS_AND_ROOT_BOUNDARY_PIXEL_REVIEW_STILL_REQUIRED')
            self.assertTrue(target.is_file())
            duplicate = {**state, 'incident_id': 'reopened-old-fault', 'phase': 'repairing'}
            duplicate.pop('recovery_proof')
            duplicate_path = root / 'duplicate.json'
            e.create(duplicate_path, duplicate)
            same = e.sync_status(result, duplicate_path)
            self.assertEqual(len(same['intervals']), 1)
            self.assertEqual(same['intervals'][0]['incident_id'], 'issue')
            self.assertEqual(same['intervals'][0]['end_at_utc'], auto['ended_at_utc'])
            withdrawal = {**duplicate, 'phase': 'expired', 'withdrawn': True,
                          'EDL_wait_interval_allowed': False,
                          'withdrawn_at_utc': '2026-10-17T00:30:00Z'}
            withdrawn_path = root / 'withdrawn.json'
            e.create(withdrawn_path, withdrawal)
            same = e.sync_status(same, withdrawn_path)
            self.assertEqual(len(same['intervals']), 1)
            self.assertEqual(same['intervals'][0]['incident_id'], 'issue')
            self.assertTrue(any(m['kind'] == 'withdrawn_false_incident_no_edit' for m in same['markers']))

    def test_withdrawn_open_false_interval_has_no_edit_or_fabricated_endpoint(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            seed = e.build({'segments': [{'session_id': 'capture-a',
                'started_at_utc': '2026-10-17T00:00:00Z', 'duration_seconds': 1000,
                'game_pid': 10, 'game_creation_filetime': 100}],
                'intervals': [{'id': 'false', 'incident_id': 'false',
                    'start_at_utc': '2026-10-17T00:00:10Z', 'end_at_utc': None}]})
            state = {'schema': 'xar.runtime-repair-status/v1', 'incident_id': 'false',
                'binding': {'game_pid': 10, 'game_creation_filetime': 100},
                'phase': 'expired', 'withdrawn': True, 'EDL_wait_interval_allowed': False,
                'opened_at_utc': '2026-10-17T00:00:10Z'}
            path = root / 'withdrawn.json'
            e.create(path, state)
            result = e.sync_status(seed, path)
            self.assertEqual(result['intervals'], [])
            self.assertFalse(result['markers'][0]['recovery_claimed'])


if __name__ == '__main__':
    unittest.main()
