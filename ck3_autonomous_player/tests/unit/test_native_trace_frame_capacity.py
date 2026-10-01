"""Offline local transport regressions. No CK3, injector or native gameplay."""
from pathlib import Path
import json
import os
import queue
import struct
import threading
import time
import unittest
import uuid

from xar_autoplayer.bridge.native_driver import MAXIMUM_FRAME_BYTES, NativeNamedPipeServer


def sized_frame(size):
    frame = {'type': 'command_result', 'protocol_version': 1, 'request_id': 'offline-capacity',
             'ok': True, 'result': {'offline_not_native_game_truth': True, 'padding': ''}}
    overhead = len(json.dumps(frame, separators=(',', ':')).encode('utf-8'))
    frame['result']['padding'] = 'x' * (size - overhead)
    payload = json.dumps(frame, separators=(',', ':')).encode('utf-8')
    assert len(payload) == size
    return frame, payload


@unittest.skipUnless(os.name == 'nt', 'Original Windows named-pipe endpoint')
class NativeTraceFrameCapacityTests(unittest.TestCase):
    def setUp(self):
        import pywintypes
        import win32file
        import win32pipe
        self.win32file, self.win32pipe = win32file, win32pipe
        self.frames = queue.Queue()
        self.disconnected = threading.Event()
        self.server = NativeNamedPipeServer(r'\\.\pipe\xar_offline_capacity_' + uuid.uuid4().hex,
                                           poll_interval_seconds=.001)
        self.server.start(self.frames.put, self.disconnected.set)
        self.client = None
        try:
            deadline = time.monotonic() + 3
            while self.client is None:
                try:
                    self.client = win32file.CreateFile(self.server.pipe_name,
                        win32file.GENERIC_READ | win32file.GENERIC_WRITE, 0, None,
                        win32file.OPEN_EXISTING, 0, None)
                except pywintypes.error as e:
                    if e.winerror not in (2, 231) or time.monotonic() >= deadline:
                        raise
                    time.sleep(.01)
            win32pipe.SetNamedPipeHandleState(self.client, win32pipe.PIPE_READMODE_BYTE, None, None)
        except BaseException:
            self.server.close()
            raise

    def tearDown(self):
        if self.client is not None:
            self.win32file.CloseHandle(self.client)
        self.server.close()

    def read_from_server(self):
        _, header = self.win32file.ReadFile(self.client, 4)
        size = struct.unpack('<I', header)[0]
        chunks = []
        remaining = size
        while remaining:
            _, chunk = self.win32file.ReadFile(self.client, remaining)
            self.assertTrue(chunk)
            chunks.append(chunk)
            remaining -= len(chunk)
        return size, json.loads(b''.join(chunks).decode('utf-8'))

    def test_reader_receives_actual_size_and_exact_cap_without_dropping_payload(self):
        for size in (1_217_950, MAXIMUM_FRAME_BYTES):
            frame, payload = sized_frame(size)
            self.win32file.WriteFile(self.client, struct.pack('<I', size) + payload)
            self.assertEqual(self.frames.get(timeout=4), frame)

    def test_reader_waits_for_complete_large_payload_after_length_header(self):
        frame, payload = sized_frame(1_217_950)
        self.win32file.WriteFile(self.client, struct.pack('<I', len(payload)))
        with self.assertRaises(queue.Empty):
            self.frames.get(timeout=.03)
        self.win32file.WriteFile(self.client, payload)
        self.assertEqual(self.frames.get(timeout=4), frame)

    def test_sender_sends_exact_cap_and_rejects_cap_plus_one(self):
        frame, _ = sized_frame(MAXIMUM_FRAME_BYTES)
        self.server.send(frame)
        size, observed = self.read_from_server()
        self.assertEqual(size, MAXIMUM_FRAME_BYTES)
        self.assertEqual(observed, frame)
        over, _ = sized_frame(MAXIMUM_FRAME_BYTES + 1)
        with self.assertRaisesRegex(ValueError, 'too large'):
            self.server.send(over)

    def test_reader_rejects_oversized_header_before_payload(self):
        self.win32file.WriteFile(self.client, struct.pack('<I', MAXIMUM_FRAME_BYTES + 1))
        self.assertTrue(self.disconnected.wait(3))
        self.assertTrue(self.frames.empty())

    def test_native_python_cap_and_ring_bound_are_paired(self):
        root = Path(__file__).resolve().parents[2]
        header = (root / 'native_bridge/include/xar_bridge/protocol.hpp').read_text()
        managed = (root / 'native_bridge/include/xar_bridge/combat_phase_event_trace_managed_v1.hpp').read_text()
        ring = (root / 'native_bridge/include/xar_bridge/combat_phase_event_trace_wire_v1.hpp').read_text()
        self.assertEqual(MAXIMUM_FRAME_BYTES, 2 * 1024 * 1024)
        self.assertIn('kMaximumFrameBytes = 2U * 1024U * 1024U', header)
        self.assertIn('xar::bridge::kMaximumFrameBytes - 128U * 1024U', managed)
        self.assertIn('900U * 1024U', ring)


if __name__ == '__main__':
    unittest.main()
