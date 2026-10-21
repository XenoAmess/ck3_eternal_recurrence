from __future__ import annotations
import io
import subprocess
import threading
import unittest
from pathlib import Path
from PIL import Image
from r13_once_contacts import Custody, jpeg_read
from r13_contract import RawStat, Recipe, decimal64, load_map

class FakeProcess:
    def __init__(self, timeout: bool = False) -> None:
        self.alive = True
        self.waits = 0
        self.terminations = 0
        self.kills = 0
        self.timeout = timeout
    def poll(self) -> int | None:
        return None if self.alive else 0
    def terminate(self) -> None:
        self.terminations += 1
        self.alive = False
    def kill(self) -> None:
        self.kills += 1
        self.alive = False
    def wait(self, timeout: float | None = None) -> int:
        self.waits += 1
        if self.timeout and self.waits == 1:
            raise subprocess.TimeoutExpired('synthetic only', timeout or 0)
        self.alive = False
        return 0

class FakeWorker:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.started = False
        self.joins = 0
    def start(self) -> None:
        if self.fail:
            raise RuntimeError('synthetic start failure')
        self.started = True
    def join(self, timeout: float | None = None) -> None:
        self.joins += 1
        self.started = False
    def is_alive(self) -> bool:
        return self.started

class Guards(unittest.TestCase):
    def test_numeric_aliases_refused_at_all_selected_window_fields(self) -> None:
        original=load_map(Path(__file__).parent.parent/'R13-ONCE-CONTACT-RECIPE.prepared-a01.json')
        Recipe.parse(original)
        for field,value in [('source_frames',900.0),('sheets',57.0),('JPEG_q',18.0),
                            ('source_frames',True),('sheets',False),('JPEG_q',True),
                            ('source_frames_half_open',[0.0,900]),
                            ('source_frames_half_open',[0,900.0]),
                            ('source_frames_half_open',[False,900])]:
            wrong=original.copy()
            wrong[field]=value
            with self.subTest(field=field,value=value),self.assertRaises(ValueError):
                Recipe.parse(wrong)
    def jpeg(self) -> bytes:
        stream = io.BytesIO()
        Image.new('RGB',(2,2)).save(stream,format='JPEG')
        return stream.getvalue()
    def test_fill_exact_and_concatenated_boundaries(self) -> None:
        original = self.jpeg()
        filled = original[:2]+b'\xff'+original[2:]
        stream = io.BytesIO(filled+original)
        self.assertEqual(jpeg_read(stream),filled)
        self.assertEqual(jpeg_read(stream),original)
        self.assertEqual(stream.read(),b'')
    def test_truncated_JPEG_is_rejected(self) -> None:
        with self.assertRaises(EOFError):
            jpeg_read(io.BytesIO(self.jpeg()[:-1]))
    def test_second_start_failure_still_waits_original_once(self) -> None:
        proc = FakeProcess()
        first, second = FakeWorker(), FakeWorker(True)
        custody = Custody(proc)
        output = io.BytesIO()
        stop = threading.Event()
        try:
            with self.assertRaises(RuntimeError):
                custody.start([first,second])
        finally:
            self.assertEqual(custody.finish(True,stop,output),0)
        self.assertEqual((proc.waits,proc.terminations,proc.kills),(1,1,0))
        self.assertEqual((first.joins,second.joins),(1,0))
        self.assertTrue(stop.is_set() and output.closed)
    def test_timeout_kills_and_reaps_same_original(self) -> None:
        proc = FakeProcess(True)
        self.assertEqual(Custody(proc).finish(False,threading.Event(),io.BytesIO()),0)
        self.assertEqual((proc.waits,proc.kills),(2,1))
    def test_uint64_roundtrip_and_wrong_type_refusal(self) -> None:
        original = RawStat(60656946,'1792089485622771700','13886423844274364792','562949955377337')
        self.assertEqual(RawStat.parse(original.wire()),original)
        wrong = original.wire()
        wrong['st_dev'] = 13886423844274364792
        with self.assertRaises(ValueError):
            RawStat.parse(wrong)
        for value in ('01','-1','18446744073709551616'):
            with self.assertRaises(ValueError):
                decimal64(value,'fixture')

if __name__ == '__main__':
    unittest.main()
