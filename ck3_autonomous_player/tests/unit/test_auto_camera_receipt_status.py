"""Offline real public camera worker/Service; only Native presentation I/O is fake."""
from __future__ import annotations
import threading
import unittest
from xar_autoplayer.bridge import auto_camera_follow as camera
from xar_autoplayer.bridge import realm_overview_camera as realm
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.war_hotspot_camera import LandedProvinceIndex

class Client:
    actual = None
    def latest(self):
        return self.actual


class ServiceProbe:
    _select_auto_camera_hotspot = GameplayBridgeService._select_auto_camera_hotspot
    def __init__(self):
        self._war_hotspot_camera_index = LandedProvinceIndex({4242: 'b_test'}, {4242: 'c_test'}, ())
        self._peace_realm_camera_policy = realm.PeaceRealmCameraPolicy()
        self._camera_presentation_client = Client()
        self._camera_presentation_requested_sequence = None
        self._camera_presentation_failure_sequence = None
        self._camera_presentation_retry_after_raw = None
        self.submissions = []
        self.publish_error = False

    def _publish_camera_presentation_v1(self, intent, payload):
        if self.publish_error:
            raise OSError('fixture_mapping_unavailable')
        sequence = 2 + len(self.submissions) * 2
        self.submissions.append((dict(intent), payload['source_frame']['date_raw']))
        self._camera_presentation_requested_sequence = sequence
        return {'status': 'queued_native_presentation', 'request_sequence': sequence}


def payload(date, title='b_syracusa'):
    return {'source_frame': {'actor_character_id': 40526, 'episode_run_id': 'test',
            'bridge_pid': 51028, 'connection_generation': 1, 'date_raw': date},
            'active_wars': [{'war_id': 42, 'war_objective_province_ids': [4242]}],
            'map_ready': True}


def native(sequence=2, status='unavailable', verified=False):
    return {'request_sequence': sequence, 'status': status,
            'camera_postcondition_verified': verified, 'coverage_verified': False}


class CameraStatusTests(unittest.TestCase):
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
            self.assertIsNone(service._peace_realm_camera_policy.last_hotspot)
        self.assertEqual(len(service.submissions), 1)
        receipt = service._select_auto_camera_hotspot(payload(1744))
        self.assertEqual(receipt['status'], 'queued_native_presentation')
        self.assertEqual(len(service.submissions), 2)
        service._select_auto_camera_hotspot(payload(1768))
        self.assertEqual(len(service.submissions), 2)
        service._camera_presentation_client.actual = native(4)
        service._select_auto_camera_hotspot(payload(1792))
        self.assertEqual(service._camera_presentation_retry_after_raw, 2512)

    def test_wrong_sequence_does_not_reset_policy_or_start_cooldown(self):
        service = ServiceProbe()
        service._select_auto_camera_hotspot(payload(1000))
        service._camera_presentation_client.actual = native(200)
        receipt = service._select_auto_camera_hotspot(payload(1024))
        self.assertIsNone(receipt['native_actual'])
        self.assertIsNone(service._camera_presentation_retry_after_raw)
        self.assertEqual(len(service.submissions), 1)

    def test_mapping_exception_cooldown_does_not_remember_unsent_hotspot(self):
        service = ServiceProbe()
        service.publish_error = True
        service._select_auto_camera_hotspot(payload(1000))
        self.assertEqual(service._camera_presentation_retry_after_raw, 1720)
        service.publish_error = False
        service._select_auto_camera_hotspot(payload(1024))
        self.assertIsNone(service._peace_realm_camera_policy.last_hotspot)
        self.assertEqual(len(service.submissions), 0)
        service._select_auto_camera_hotspot(payload(1720))
        self.assertEqual(len(service.submissions), 1)

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
