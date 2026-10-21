"""RAM-only meaningful guard fixtures: no raw/probe/FFmpeg/SDK/UI."""
from __future__ import annotations
import io
import json
import subprocess
import threading
import unittest
from PIL import Image
from r03_pipeline import (FRAMES, Custody, JpegReader, RETAINED_STAT, Timeline, Usage,
                          contact_bytes, decimal64, original_wait, thumbnail, validate_stat)

class Chunked:
    def __init__(self, data: bytes, chunk: int) -> None:
        self.stream = io.BytesIO(data)
        self.chunk = chunk
    def read(self, size: int = -1, /) -> bytes:
        return self.stream.read(min(size, self.chunk) if size >= 0 else self.chunk)

def jpeg(size: tuple[int, int] = (1280, 720)) -> bytes:
    output = io.BytesIO()
    with Image.new("RGB", size, (41, 102, 153)) as image:
        image.save(output, "JPEG", quality=80)
    return output.getvalue()

def clock_line(index: int, pts: int | None = None) -> bytes:
    actual = (index*1000+15)//30 if pts is None else pts
    return f"[Parsed_showinfo_1] n: {index} pts: {actual} pts_time:{actual//1000}.{actual%1000:03d} duration:33\n".encode()

def ready() -> Timeline:
    timeline = Timeline()
    timeline.line(b"[Parsed_showinfo_1] config in time_base: 1/1000, frame_rate: 30/1\n")
    return timeline

class FakeWait:
    def __init__(self, timeout_first: bool) -> None:
        self.timeout_first = timeout_first
        self.waits = 0
        self.kills = 0
    def poll(self) -> int | None:
        return -9 if self.kills else None
    def terminate(self) -> None:
        self.kills += 1
    def kill(self) -> None:
        self.kills += 1
    def wait(self, timeout: float | None = None) -> int:
        self.waits += 1
        if self.timeout_first and self.waits == 1:
            raise subprocess.TimeoutExpired("synthetic-only", timeout or 0)
        return -9 if self.kills else 0

class GuardTests(unittest.TestCase):
    def test_header_fill_bytes_are_preserved_exactly(self) -> None:
        original = jpeg()
        filled = original[:2] + b"\xff" + original[2:]
        for chunk in (1,7,65536):
            self.assertEqual(JpegReader(Chunked(filled,chunk)).one(),filled)
        image = thumbnail(filled)
        image.close()
    def test_worker_start_failure_keeps_original_wait(self) -> None:
        class FakeWorker:
            def __init__(self, fail: bool) -> None:
                self.fail=fail
                self.joins=0
            def start(self) -> None:
                if self.fail:
                    raise RuntimeError("synthetic start failure")
            def join(self, timeout: float | None = None) -> None:
                self.joins+=1
            def is_alive(self) -> bool:
                return False
        proc=FakeWait(False)
        first,second=FakeWorker(False),FakeWorker(True)
        custody=Custody(proc)
        with self.assertRaisesRegex(RuntimeError,"start failure"):
            custody.start([first,second])
        code=custody.finish(True,threading.Event(),io.BytesIO())
        self.assertEqual((code,proc.waits,proc.kills),(-9,1,1))
        self.assertEqual((first.joins,second.joins),(1,0))
    def test_JPEG_stream_chunk_boundaries_and_EOF(self) -> None:
        data = jpeg()
        for chunk in (1, 2, 7, 65536):
            with self.subTest(chunk=chunk):
                parser = JpegReader(Chunked(data+data, chunk))
                self.assertEqual(parser.one(), data)
                self.assertEqual(parser.one(), data)
                self.assertIsNone(parser.one())
    def test_APP_embedded_EOI_is_not_frame_boundary(self) -> None:
        original = jpeg()
        payload = b"prefix\xff\xd9suffix"
        modified = original[:2] + b"\xff\xe2" + (len(payload)+2).to_bytes(2, "big") + payload + original[2:]
        parser = JpegReader(Chunked(modified, 7))
        self.assertEqual(parser.one(), modified)
        image = thumbnail(modified)
        self.assertEqual(image.size, (320, 180))
        image.close()
    def test_truncation_and_bad_markers_refuse(self) -> None:
        for data in (b"\xff", b"xx", jpeg()[:-2], b"\xff\xd8\xff\xe0\x00\x01"):
            with self.subTest(length=len(data)):
                with self.assertRaises((EOFError, ValueError)):
                    JpegReader(Chunked(data, 7)).one()
    def test_JPEG_memory_bound(self) -> None:
        app = b"\xff\xe2\xff\xff" + bytes(65533)
        data = b"\xff\xd8" + app*33 + b"\xff\xd9"
        with self.assertRaisesRegex(ValueError, "RAM bound"):
            JpegReader(Chunked(data, 65536)).one()
    def test_actual_geometry_is_checked_before_resize(self) -> None:
        with self.assertRaisesRegex(ValueError, "geometry"):
            thumbnail(jpeg((2, 2)))
        with Image.new("RGB", (1280, 792), "black") as image:
            data = contact_bytes(image)
        with Image.open(io.BytesIO(data)) as result:
            self.assertEqual(result.size, (1280, 792))
    def test_all1200_actual_PTS_and_terminal(self) -> None:
        timeline = ready()
        for index in range(FRAMES):
            timeline.line(clock_line(index))
            self.assertEqual(timeline.frame(index).index, index)
        timeline.done = True
        timeline.finish()
        self.assertEqual(timeline.rows[-1].pts, 39967)
        with self.assertRaisesRegex(ValueError, "order/count"):
            timeline.line(clock_line(FRAMES))
    def test_PTS_missing_duplicate_gap_and_text_mismatch(self) -> None:
        cases = [b"[Parsed_showinfo] n: 0 pts: 0 pts_time:0\n",
                 clock_line(1), clock_line(0, 1)]
        for position, data in enumerate(cases):
            timeline = Timeline() if position == 0 else ready()
            with self.subTest(data=data):
                with self.assertRaises(ValueError):
                    timeline.line(data)
        timeline = ready()
        timeline.line(clock_line(0))
        for data in (clock_line(0), clock_line(1, 100),
                     b"[Parsed_showinfo] n: 1 pts: 33 pts_time:0.034\n"):
            with self.assertRaises(ValueError):
                timeline.line(data)
        timeline.done = True
        with self.assertRaises(ValueError):
            timeline.frame(1)
        with self.assertRaises(ValueError):
            timeline.finish()
    def test_unknown_timebase_refuses(self) -> None:
        with self.assertRaisesRegex(ValueError, "time base"):
            Timeline().line(b"[Parsed_showinfo] config in time_base: 1/90000, frame_rate: 30/1\n")
    def test_independent_partition_and_total_limits(self) -> None:
        Usage(7*1048576, 524288, 786432).check()
        for current, category in [(Usage(7*1048576), "contacts"),
                                  (Usage(0,524288), "endpoints"),
                                  (Usage(0,0,786432), "metadata"),
                                  (Usage(sources=524288), "sources")]:
            with self.assertRaises(ValueError):
                current.check(category, 1)
        with self.assertRaises(ValueError):
            Usage().check("metadata", -1)
    def test_uint64_decimal_string_and_roundtrip_domain(self) -> None:
        self.assertEqual(decimal64("134366591050798809"), "134366591050798809")
        for invalid in (134366591050798809, True, 1.0, "01", "-1", str(2**64)):
            with self.assertRaises(ValueError):
                decimal64(invalid)
        consumed: object = json.loads(json.dumps(RETAINED_STAT))
        self.assertEqual(validate_stat(consumed), RETAINED_STAT)
        wrong: dict[str, object] = dict(RETAINED_STAT)
        wrong["st_ino"] = 562949956071195
        with self.assertRaises(ValueError):
            validate_stat(wrong)
        missing: dict[str, object] = dict(RETAINED_STAT)
        del missing["st_dev"]
        with self.assertRaises(ValueError):
            validate_stat(missing)
    def test_original_wait_custody_and_kill_fallback(self) -> None:
        normal = FakeWait(False)
        self.assertEqual(original_wait(normal), 0)
        self.assertEqual(normal.waits, 1)
        slow = FakeWait(True)
        self.assertEqual(original_wait(slow), -9)
        self.assertEqual((slow.waits, slow.kills), (2, 1))

if __name__ == "__main__":
    unittest.main(verbosity=2)
