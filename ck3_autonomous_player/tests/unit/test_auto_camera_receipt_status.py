"""Offline real public camera worker/Service; only Native presentation I/O is fake."""
from __future__ import annotations
import threading
import unittest
from unittest.mock import patch
from xar_autoplayer.bridge import auto_camera_follow as camera
from xar_autoplayer.bridge import realm_overview_camera as realm
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.war_hotspot_camera import LandedProvinceIndex

class Client:
    def __init__(self, service, pid):
        self.service, self.pid, self.actual, self.closed = service, pid, None, False

    def latest(self):
        return self.actual

    def submit(self, intent, frame, source):
        if self.service.publish_error:
            raise OSError('fixture_mapping_unavailable')
        sequence = 2 + len(self.service.submissions) * 2
        self.service.submissions.append((dict(intent), frame['date_raw']))
        return {'status': 'queued_native_presentation', 'request_sequence': sequence}

    def close(self):
        self.closed = True


class ServiceProbe(GameplayBridgeService):
    def __init__(self):
        super().__init__(object())
        self._auto_camera_worker.close_without_wait()
        self.bind_war_hotspot_camera_index(
            LandedProvinceIndex({4242: 'b_test'}, {4242: 'c_test'}, ()))
        self.submissions = []
        self.publish_error = False

    def _publish_camera_presentation_v1(self, intent, payload):
        # Keep production owner/sequence/original-frame publication binding;
        # replace only the OS/shared-memory Native client boundary.
        with patch.object(realm, 'NativeCameraPresentationClient',
                          lambda pid: Client(self, pid)):
            return super()._publish_camera_presentation_v1(intent, payload)


def payload(date, **frame_changes):
    return {'source_frame': {'actor_character_id': 40526, 'episode_run_id': 'test',
            'bridge_pid': 51028, 'connection_generation': 1, 'date_raw': date,
            'snapshot_id': f'native:{date}', 'revision': date, 'native_revision': date,
            **frame_changes},
            'active_wars': [{'war_id': 42, 'allied_armies': [{
                'army_id': 7, 'current_province_id': 4242,
                'in_combat': True, 'controllable': True}]}],
            'map_ready': True,
            'source_build': {'game_version': '1.20.0.4', 'executable_sha256': realm.EXACT_SHA}}


def native(sequence=2, status='unavailable', verified=False, *, date=1024, actor=40526):
    return {'request_sequence': sequence, 'status': status,
            'actor_character_id': actor, 'date_raw': date,
            'target': [1., 2., 3., 4., 5., 6.], 'current': [1., 2., 3., 4., 5., 6.],
            'camera_postcondition_verified': verified, 'coverage_verified': False}


class CameraStatusTests(unittest.TestCase):
    def setUp(self):
        timing = patch.dict('os.environ', {'XAR_CK3_ARMY_TIMING_JSONL': ''})
        timing.start()
        self.addCleanup(timing.stop)

    def test_nested_native_failure_and_partial_never_completed(self):
        for status, verified in [('unavailable', False), ('settled', False),
                                 ('bounds_available', False), ('stale_actor', False)]:
            with self.subTest(status=status):
                outcome = camera.camera_receipt_outcome({'status': 'war_objective', 'native_actual': native(status=status, verified=verified)})
                self.assertEqual(outcome[:2], ('failed', False))

    def test_queue_ack_is_pending_and_verified_postcondition_is_completed(self):
        self.assertEqual(camera.camera_receipt_outcome({'status': 'queued_native_presentation'})[:2], ('pending', False))
        self.assertEqual(camera.camera_receipt_outcome({'native_actual': native(status='submitted')})[:2], ('pending', False))
        self.assertEqual(camera.camera_receipt_outcome({'native_actual': native(status='settled', verified=True)})[:2], ('completed', True))

    def test_publish_error_cannot_reuse_prior_settled_result(self):
        self.assertEqual(camera.camera_receipt_outcome({'status': 'unavailable', 'native_actual': native(status='settled', verified=True)})[:2], ('failed', False))

    def test_failed_same_hotspot_retries_once_after_thirty_days(self):
        service = ServiceProbe()
        self.assertFalse(service._select_auto_camera_hotspot(payload(1000))['available'])
        self.assertEqual(len(service.submissions), 1)
        service._camera_presentation_client.actual = native()
        for date in [1024, 1048, 1720, 1743]:
            receipt = service._select_auto_camera_hotspot(payload(date))
            self.assertEqual(receipt['status'], 'unavailable')
            self.assertFalse(receipt['available'])
            self.assertEqual(receipt['retry_after_raw'], 1744)
            self.assertEqual(service._peace_realm_camera_policy.last_hotspot, 'b_test')
            self.assertIsNone(service._peace_realm_camera_policy.quiet_since)
        self.assertEqual(len(service.submissions), 1)
        receipt = service._select_auto_camera_hotspot(payload(1744))
        self.assertEqual(receipt['status'], 'queued_native_presentation')
        self.assertEqual(len(service.submissions), 2)
        service._select_auto_camera_hotspot(payload(1768))
        self.assertEqual(len(service.submissions), 2)
        service._camera_presentation_client.actual = native(4, date=1792)
        service._select_auto_camera_hotspot(payload(1792))
        key = service._camera_presentation_request_context['key']
        self.assertEqual(service._camera_presentation_target_backoffs, {key: 2512})

    def test_wrong_sequence_does_not_reset_policy_or_start_cooldown(self):
        service = ServiceProbe()
        service._select_auto_camera_hotspot(payload(1000))
        service._camera_presentation_client.actual = native(200)
        receipt = service._select_auto_camera_hotspot(payload(1024))
        self.assertIsNone(receipt['native_actual'])
        self.assertEqual(service._camera_presentation_target_backoffs, {})
        self.assertIsNone(service._camera_presentation_failure_sequence)
        self.assertEqual(service._peace_realm_camera_policy.last_hotspot, 'b_test')
        self.assertEqual(len(service.submissions), 1)

    def test_mapping_exception_cooldown_does_not_remember_unsent_hotspot(self):
        service = ServiceProbe()
        service.publish_error = True
        service._select_auto_camera_hotspot(payload(1000))
        self.assertEqual(list(service._camera_presentation_target_backoffs.values()), [1720])
        service.publish_error = False
        service._select_auto_camera_hotspot(payload(1024))
        # The policy observes activity during backoff, but an unsent request
        # has no publication context/sequence and must still retry on expiry.
        self.assertIsNone(service._camera_presentation_request_context)
        self.assertIsNone(service._camera_presentation_requested_sequence)
        self.assertEqual(len(service.submissions), 0)
        service._select_auto_camera_hotspot(payload(1720))
        self.assertEqual(len(service.submissions), 1)

    def test_owner_change_clears_target_backoff_and_rejects_old_native_result(self):
        for field, value in [('actor_character_id', 40527), ('episode_run_id', 'new'),
                             ('bridge_pid', 51029), ('connection_generation', 2)]:
            with self.subTest(field=field):
                service = ServiceProbe()
                service._select_auto_camera_hotspot(payload(1000))
                old_client = service._camera_presentation_client
                old_client.actual = native()
                service._select_auto_camera_hotspot(payload(1024))
                self.assertEqual(list(service._camera_presentation_target_backoffs.values()), [1744])
                changed = payload(1048, **{field: value})
                receipt = service._select_auto_camera_hotspot(changed)
                self.assertEqual(len(service.submissions), 2)
                self.assertEqual(service._camera_presentation_target_backoffs, {})
                self.assertEqual(service._camera_presentation_request_context['frame'], changed['source_frame'])
                self.assertIsNone(receipt['native_actual'])
                self.assertFalse(receipt['available'])
                following = service._select_auto_camera_hotspot(payload(1072, **{field: value}))
                self.assertIsNone(following['native_actual'])
                self.assertEqual(service._camera_presentation_target_backoffs, {})
                self.assertEqual(len(service.submissions), 2)
                if field == 'bridge_pid':
                    self.assertTrue(old_client.closed)

    def test_actual_worker_reports_failure_and_deduplicates_same_native_failure(self):
        completed = threading.Event()
        observed = []
        def on_complete(actual):
            observed.append(actual)
            completed.set()
        worker = camera.LatestCameraFollowWorker(lambda value: {'status': 'war_objective', 'native_actual': native()}, on_complete=on_complete, quiet_seconds=0)
        try:
            for unused in range(2):
                completed.clear()
                worker.schedule()
                self.assertTrue(completed.wait(2))
            self.assertEqual([row['status'] for row in observed], ['failed', 'failed'])
            self.assertTrue(all(row['available'] is False for row in observed))
            self.assertEqual(len(worker.recent_failures()), 1)
            self.assertFalse(worker._reference(worker.latest_actual())['available'])
        finally:
            worker.close_without_wait()

    def test_worker_schedule_remains_nonblocking_while_work_is_running(self):
        started, release, done = threading.Event(), threading.Event(), threading.Event()
        def work(value):
            started.set()
            release.wait(2)
            return {'status': 'queued_native_presentation'}
        worker = camera.LatestCameraFollowWorker(work, on_complete=lambda row: done.set(), quiet_seconds=0)
        try:
            worker.schedule('first')
            self.assertTrue(started.wait(2))
            scheduled = worker.schedule('second')
            self.assertEqual(scheduled['status'], 'scheduled')
            self.assertFalse(done.is_set())
        finally:
            worker.close_without_wait()
            release.set()


if __name__ == '__main__':
    unittest.main(verbosity=2)
