"""R191 bounded JPEG-pipe source candidate. Import and fixtures never open raw media."""
from __future__ import annotations
import csv
import ctypes
from ctypes import wintypes
from dataclasses import dataclass, field
from datetime import datetime, timezone
from fractions import Fraction
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
from typing import BinaryIO, Protocol
from PIL import Image, ImageDraw, ImageFont
from r03_budget_a02 import CONTACT_CAP, AGGREGATE_CAP

ROOT = Path("C:/ck3-e04-resume-20261020-a01/r03-r191-continuous-review-2245-a01")
RAW = Path("D:/workspace/ck3_native_war_ai_promo_work/e04-r191-window-capture-a01/raw-window-a01/raw.mkv")
FFMPEG = Path("C:/Users/1/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.1-full_build/bin/ffmpeg.exe")
FONT = Path("C:/Windows/Fonts/consola.ttf")
MACHINE = "desktop-3fevhd2-1c74096080"
FRAMES = 1200
SHEETS = 75
MAX_JPEG = 2 * 1048576
MAX_STDERR = 4 * 1048576
DEADLINE = "2026-10-20T22:45:00+00:00"
RETAINED_STAT: dict[str, object] = {"bytes": 66574010, "mtime_ns": "1792186745751031500",
                 "st_dev": "7220568048185129294", "st_ino": "562949956071195"}
EXPECTED_ARGV = [str(FFMPEG), "-hide_banner", "-nostdin", "-nostats", "-v", "info", "-threads", "1",
                 "-i", str(RAW), "-an", "-vf",
                 "trim=start_frame=0:end_frame=1200,showinfo",
                 "-fps_mode", "passthrough", "-frames:v", "1200",
                 "-c:v", "mjpeg", "-q:v", "4", "-threads", "1",
                 "-f", "image2pipe", "pipe:1"]

def need(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)

def stamp() -> str:
    return datetime.now(timezone.utc).isoformat()

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def mapping(value: object) -> dict[str, object]:
    need(isinstance(value, dict), "Expected JSON object")
    result: dict[str, object] = {}
    if isinstance(value, dict):
        for key, item in value.items():
            need(isinstance(key, str), "JSON key must be string")
            if isinstance(key, str):
                result[key] = item
    return result

def text(value: object) -> str:
    need(isinstance(value, str), "Expected text")
    if isinstance(value, str):
        return value
    raise ValueError("Text unavailable")

def integer(value: object) -> int:
    need(isinstance(value, int) and not isinstance(value, bool), "Expected exact integer")
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    raise ValueError("Integer unavailable")

def decimal64(value: object) -> str:
    result = text(value)
    need(re.fullmatch(r"0|[1-9][0-9]*", result) is not None, "Noncanonical decimal64")
    need(int(result) < 2**64, "decimal64 overflow")
    return result

def load(path: Path) -> dict[str, object]:
    value: object = json.loads(path.read_text(encoding="utf-8-sig"))
    return mapping(value)

def encoded(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=True, separators=(",", ":")) + "\n").encode()

def source_stat(path: Path) -> dict[str, object]:
    st = path.stat()
    return {"bytes": st.st_size, "mtime_ns": str(st.st_mtime_ns),
            "st_dev": str(st.st_dev), "st_ino": str(st.st_ino)}

def validate_stat(value: object) -> dict[str, object]:
    row = mapping(value)
    need(set(row) == set(RETAINED_STAT), "Source stat fields differ")
    normalized: dict[str, object] = {"bytes": integer(row["bytes"])}
    for key in ("mtime_ns", "st_dev", "st_ino"):
        normalized[key] = decimal64(row[key])
    need(normalized == RETAINED_STAT, "Source identity differs")
    return normalized

@dataclass(frozen=True)
class Usage:
    contacts: int = 0
    endpoints: int = 0
    metadata: int = 0
    sources: int = 0
    @property
    def total(self) -> int:
        return self.contacts + self.endpoints + self.metadata + self.sources
    def check(self, category: str = "", extra: int = 0) -> None:
        need(extra >= 0, "Negative addition")
        need(self.contacts + (extra if category == "contacts" else 0) <= CONTACT_CAP, "Contact 12MiB cap")
        need(self.endpoints + (extra if category == "endpoints" else 0) <= 524288, "Endpoint 512KiB cap")
        need(self.metadata + (extra if category == "metadata" else 0) <= 786432, "Metadata 768KiB cap")
        need(self.sources + (extra if category == "sources" else 0) <= 524288, "Source/checks 512KiB cap")
        need(self.total + extra <= AGGREGATE_CAP, "Aggregate 14MiB cap")
    def wire(self) -> dict[str, int]:
        return {"contacts_bytes": self.contacts, "endpoints_bytes": self.endpoints,
                "metadata_bytes": self.metadata, "source_checks_bytes": self.sources, "aggregate_bytes": self.total}

def usage(root: Path) -> Usage:
    contacts = endpoints = metadata = sources = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        size = path.stat().st_size
        first = path.relative_to(root).parts[0]
        if first == "contacts":
            contacts += size
        elif first == "source-endpoints":
            endpoints += size
        elif first == "source":
            sources += size
        else:
            metadata += size
    return Usage(contacts, endpoints, metadata, sources)

def write_new(root: Path, relative: str, data: bytes, category: str = "metadata") -> dict[str, object]:
    path = root / relative
    need(not path.exists(), "Create-only output already exists: " + relative)
    usage(root).check(category, len(data))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        written = stream.write(data)
    need(written == len(data), "Short disk write")
    return {"path": relative, "bytes": len(data), "sha256": digest(data)}

class ByteReader(Protocol):
    def read(self, size: int = -1, /) -> bytes: ...

class JpegReader:
    """Marker-aware bounded parser; APP payloads may contain an apparent EOI."""
    def __init__(self, stream: ByteReader) -> None:
        self.stream = stream
        self.buffer = bytearray()
        self.pos = 0
    def take(self, count: int, allow_eof: bool = False) -> bytes:
        need(0 <= count <= MAX_JPEG, "Read bound")
        while len(self.buffer) - self.pos < count:
            self.buffer = self.buffer[self.pos:]
            self.pos = 0
            chunk = self.stream.read(65536)
            if not chunk:
                if allow_eof and not self.buffer:
                    return b""
                raise EOFError("Truncated JPEG/pipe")
            self.buffer.extend(chunk)
        result = bytes(self.buffer[self.pos:self.pos+count])
        self.pos += count
        return result
    @staticmethod
    def extend(target: bytearray, data: bytes) -> None:
        need(len(target) + len(data) <= MAX_JPEG, "JPEG RAM bound")
        target.extend(data)
    def one(self) -> bytes | None:
        first = self.take(2, True)
        if not first:
            return None
        need(first == b"\xff\xd8", "JPEG SOI differs")
        out = bytearray(first)
        pending: int | None = None
        while True:
            if pending is None:
                prefix = self.take(1)
                need(prefix == b"\xff", "Marker prefix differs")
                self.extend(out, prefix)
                code = self.take(1)
                while code == b"\xff":
                    self.extend(out, code)
                    code = self.take(1)
                pending = code[0]
                self.extend(out, code)
            if pending == 217:
                return bytes(out)
            need(pending not in (0, 216), "Unexpected JPEG marker")
            if pending == 1 or 208 <= pending <= 215:
                pending = None
                continue
            length = self.take(2)
            self.extend(out, length)
            count = int.from_bytes(length, "big")
            need(count >= 2, "Invalid JPEG segment length")
            self.extend(out, self.take(count-2))
            if pending != 218:
                pending = None
                continue
            while True:
                loc = self.buffer.find(b"\xff", self.pos)
                if loc < 0:
                    self.extend(out, bytes(self.buffer[self.pos:]))
                    self.pos = len(self.buffer)
                    self.take(1)
                    self.pos -= 1
                    continue
                self.extend(out, bytes(self.buffer[self.pos:loc+1]))
                self.pos = loc+1
                code = self.take(1)
                self.extend(out, code)
                while code == b"\xff":
                    code = self.take(1)
                    self.extend(out, code)
                if code == b"\x00" or 208 <= code[0] <= 215:
                    continue
                pending = code[0]
                break

@dataclass(frozen=True)
class FramePTS:
    index: int
    pts: int
    pts_time: str

@dataclass
class Timeline:
    rows: list[FramePTS] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    raw_stderr: bytearray = field(default_factory=bytearray)
    time_base: Fraction | None = None
    done: bool = False
    truncated: bool = False
    condition: threading.Condition = field(default_factory=threading.Condition)
    def line(self, data: bytes) -> None:
        with self.condition:
            if len(self.raw_stderr) + len(data) <= MAX_STDERR:
                self.raw_stderr.extend(data)
            else:
                self.truncated = True
                raise ValueError("stderr RAM bound; retained prefix only")
            if b"showinfo" not in data:
                return
            config = re.search(rb"config in time_base:\s*([0-9]+/[0-9]+)", data)
            if config:
                need(self.time_base is None, "Repeated showinfo input config")
                self.time_base = Fraction(config[1].decode())
                need(self.time_base == Fraction(1, 1000), "Actual source time base differs")
            match = re.search(rb"\bn:\s*(\d+)\s+pts:\s*(-?\d+)\s+pts_time:([^ ]+)", data)
            if match:
                index, pts = int(match[1]), int(match[2])
                label = match[3].decode()
                actual_base = self.time_base
                if actual_base is None:
                    raise ValueError("Frame precedes actual time-base")
                need(index == len(self.rows) and index < FRAMES, "Frame order/count differs")
                need(pts == 0 if index == 0 else pts-self.rows[-1].pts in (33, 34), "PTS start/step differs")
                need(Fraction(label) == pts*actual_base, "PTS textual value differs")
                self.rows.append(FramePTS(index, pts, label))
                self.condition.notify_all()
    def fail(self, error: BaseException) -> None:
        with self.condition:
            self.errors.append(type(error).__name__ + ": " + str(error))
            self.condition.notify_all()
    def frame(self, index: int) -> FramePTS:
        until = time.monotonic()+15
        with self.condition:
            while len(self.rows) <= index and not self.done and not self.errors:
                remaining = until-time.monotonic()
                need(remaining > 0, "PTS/JPEG join timed out")
                self.condition.wait(min(remaining, .2))
            need(not self.errors, "stderr/PTS failure: " + "; ".join(self.errors))
            need(index < len(self.rows), "Missing corresponding actual PTS")
            return self.rows[index]
    def finish(self) -> None:
        with self.condition:
            need(not self.errors and not self.truncated, "Partial stderr/PTS")
            need(self.done and len(self.rows) == FRAMES, "PTS terminal count differs")
            need(self.rows[-1].pts == 39967, "Actual final PTS differs")

def thumbnail(jpeg: bytes) -> Image.Image:
    with Image.open(io.BytesIO(jpeg)) as opened:
        need(opened.format == "JPEG" and opened.size == (1280, 720), "Actual JPEG geometry/format differs")
        opened.load()
        return opened.convert("RGB").resize((320, 180), Image.Resampling.LANCZOS)

def contact_bytes(canvas: Image.Image) -> bytes:
    need(canvas.size == (1280, 792), "Contact geometry differs")
    output = io.BytesIO()
    canvas.save(output, "JPEG", quality=60, subsampling=2, optimize=False)
    return output.getvalue()

class Waitable(Protocol):
    def poll(self) -> int | None: ...
    def terminate(self) -> None: ...
    def kill(self) -> None: ...
    def wait(self, timeout: float | None = None) -> int: ...

def terminate(proc: Waitable) -> None:
    if proc.poll() is None:
        try:
            proc.terminate()
        except OSError:
            pass

def original_wait(proc: Waitable) -> int:
    try:
        return proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        return proc.wait(timeout=10)

class Worker(Protocol):
    def start(self) -> None: ...
    def join(self, timeout: float | None = None) -> None: ...
    def is_alive(self) -> bool: ...

class Closeable(Protocol):
    def close(self) -> None: ...

class LineReader(Closeable, Protocol):
    def readline(self, size: int = -1, /) -> bytes: ...

@dataclass
class Custody:
    proc: Waitable
    started: list[Worker] = field(default_factory=list)
    def start(self, workers: list[Worker]) -> None:
        for worker in workers:
            worker.start()
            self.started.append(worker)
    def finish(self, failed: bool, stop: threading.Event, stdout: Closeable) -> int:
        if failed:
            terminate(self.proc)
        code = original_wait(self.proc)
        stop.set()
        stdout.close()
        for worker in self.started:
            worker.join(timeout=10)
        return code

def stderr_worker(pipe: LineReader, timeline: Timeline, proc: Waitable) -> None:
    try:
        while True:
            line = pipe.readline(65537)
            if not line:
                break
            try:
                need(len(line) <= 65536, "Oversize stderr line")
                timeline.line(line)
            except BaseException as exc:
                timeline.fail(exc)
                terminate(proc)
                # Continue draining both normal termination diagnostics and pipe EOF.
    except BaseException as exc:
        timeline.fail(exc)
        terminate(proc)
    finally:
        with timeline.condition:
            timeline.done = True
            timeline.condition.notify_all()
        pipe.close()

def pin_small(path: Path, size: int, sha: str) -> None:
    data = path.read_bytes()
    need(len(data) == size and digest(data) == sha, "Small source pin differs: " + str(path))

def preflight(recipe: dict[str, object]) -> None:
    need(text(recipe["machine_id"]) == MACHINE, "Machine contract differs")
    need(text(recipe["root"]) == str(ROOT), "Output root differs")
    need(text(recipe["raw"]) == str(RAW), "Source path differs")
    need(decimal64(recipe["historical_process_birth_filetime"]) == "134366591050798809", "Historical birth identity differs")
    validate_stat(recipe["retained_source_stat"])
    need(source_stat(RAW) == validate_stat(recipe["retained_source_stat"]), "Fresh source stat differs")
    need(recipe["argv"] == EXPECTED_ARGV, "Frozen argv differs")
    need(text(recipe["deadline_utc"]) == DEADLINE, "Deadline differs")
    need(FFMPEG.stat().st_size == 222229504, "Pinned tool size differs; no body rehash")
    pins = recipe["small_source_pins"]
    need(isinstance(pins, list), "Source pins must be list")
    if isinstance(pins, list):
        for item in pins:
            row = mapping(item)
            pin_small(Path(text(row["path"])), integer(row["bytes"]), text(row["sha256"]))
    need(time.time() < datetime.fromisoformat(DEADLINE).timestamp()-60, "Insufficient finite execution time")

def priority_class(pid: int) -> int:
    """Existing R11 narrow HANDLE/DWORD validation boundary."""
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    opener = kernel.OpenProcess
    opener.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    opener.restype = wintypes.HANDLE
    getter = kernel.GetPriorityClass
    getter.argtypes = [wintypes.HANDLE]
    getter.restype = wintypes.DWORD
    closer = kernel.CloseHandle
    closer.argtypes = [wintypes.HANDLE]
    closer.restype = wintypes.BOOL
    handle: object = opener(0x1000, False, pid)
    if type(handle) is not int or handle <= 0:
        raise OSError(ctypes.get_last_error(), "OpenProcess query priority failed")
    try:
        value: object = getter(ctypes.c_void_p(handle))
        return integer(value)
    finally:
        closer(ctypes.c_void_p(handle))

def run(recipe_path: Path) -> int:
    """Only called after Root's source adoption + exact source-bound once grant."""
    need(recipe_path.parent == ROOT, "Recipe must be exact new output root")
    recipe = load(recipe_path)
    preflight(recipe)
    usage(ROOT).check()
    for name in ("contacts", "source-endpoints", "ONCE-WAL.actual.json", "EXTRACTION.actual.json"):
        need(not (ROOT/name).exists(), "Once output already exists: " + name)
    write_new(ROOT, "ONCE-WAL.actual.json", encoded({"machine_id": MACHINE, "at_utc": stamp(),
              "recipe_sha256": digest(recipe_path.read_bytes()), "max_FFmpeg_Popen_attempts": 1,
              "status": "CLAIMED_BEFORE_RELEASE_AND_FFMPEG_NO_AUTOREPLAY"}))
    release = subprocess.run(["gh", "release", "view", "--repo", "XenoAmess/xar_promo_toolchain",
                              "--json", "tagName,isDraft,isPrerelease,publishedAt,url"],
                             capture_output=True, timeout=20, creationflags=subprocess.CREATE_NO_WINDOW)
    write_new(ROOT, "LATEST-RELEASE.actual.json", encoded({"at_utc": stamp(), "returncode": release.returncode,
              "stdout": release.stdout.decode("utf-8", "replace"), "stderr": release.stderr.decode("utf-8", "replace"),
              "no_download": True}))
    need(release.returncode == 0, "Latest release lookup failed; zero FFmpeg attempts")
    latest_value: object = json.loads(release.stdout)
    latest = mapping(latest_value)
    need(latest.get("tagName") == "v0.3.0" and latest.get("isDraft") is False and latest.get("isPrerelease") is False,
         "Latest formal release differs; zero FFmpeg attempts")
    machine = subprocess.run([sys.executable, "-B",
                              "D:/workspace/ck3_eternal_recurrence/tools/ck3_live_run_id.py", "machine"],
                             capture_output=True, timeout=10, creationflags=subprocess.CREATE_NO_WINDOW)
    actual_machine = machine.stdout.decode("utf-8", "replace").strip()
    write_new(ROOT, "MACHINE-READBACK.actual.json", encoded({"at_utc": stamp(),
              "returncode": machine.returncode, "machine_id": actual_machine,
              "stderr": machine.stderr.decode("utf-8", "replace")}))
    need(machine.returncode == 0 and actual_machine == MACHINE, "Actual machine identity differs")
    timeline = Timeline()
    stop = threading.Event()
    timer_errors: list[str] = []
    started = stamp()
    original = subprocess.Popen(EXPECTED_ARGV, stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS)
    out, err = original.stdout, original.stderr
    if out is None or err is None:
        terminate(original)
        code = original_wait(original)
        raise RuntimeError("Original pipe custody unavailable; wait=" + str(code))
    reader = threading.Thread(target=stderr_worker, args=(err, timeline, original), name="R191-stderr")
    def watchdog() -> None:
        until = min(time.monotonic()+240, time.monotonic()+datetime.fromisoformat(DEADLINE).timestamp()-time.time()-30)
        while not stop.wait(.05):
            if original.poll() is not None:
                return
            if time.monotonic() >= until:
                timer_errors.append("Finite wall/deadline stop")
                terminate(original)
                return
            try:
                usage(ROOT).check()
            except BaseException as exc:
                timer_errors.append(type(exc).__name__ + ": " + str(exc))
                terminate(original)
                return
    watch = threading.Thread(target=watchdog, name="R191-watchdog")
    rows: list[list[object]] = []
    sheets: list[dict[str, object]] = []
    endpoints: list[dict[str, object]] = []
    reason: str | None = None
    completed = 0
    parsed_JPEG_messages = 0
    stream_bytes = 0
    stream_hash = hashlib.sha256()
    custody = Custody(original)
    try:
        custody.start([reader, watch])
        write_new(ROOT, "OWNED-PROCESS.actual.json", encoded({"machine_id": MACHINE, "at_utc": started,
                  "original_Popen_pid": original.pid, "requested_priority": subprocess.BELOW_NORMAL_PRIORITY_CLASS}))
        actual_priority = priority_class(original.pid)
        need(actual_priority == subprocess.BELOW_NORMAL_PRIORITY_CLASS, "Actual FFmpeg priority differs")
        write_new(ROOT, "OWNED-PRIORITY.actual.json", encoded({"at_utc": stamp(),
                  "original_Popen_pid": original.pid, "actual_priority": actual_priority}))
        font = ImageFont.truetype(str(FONT), 14)
        parser = JpegReader(out)
        canvas = Image.new("RGB", (1280, 792), "black")
        draw = ImageDraw.Draw(canvas)
        for index in range(FRAMES):
            jpeg = parser.one()
            need(jpeg is not None, "Missing JPEG frame")
            if jpeg is None:
                raise ValueError("JPEG unavailable")
            parsed_JPEG_messages += 1
            point = timeline.frame(index)
            thumb = thumbnail(jpeg)
            stream_bytes += len(jpeg)
            stream_hash.update(jpeg)
            if index in (0, FRAMES-1):
                endpoints.append(write_new(ROOT, f"source-endpoints/frame{index:04d}.jpg", jpeg, "endpoints"))
            cell = index % 16
            x, y = (cell % 4)*320, (cell // 4)*198
            canvas.paste(thumb, (x, y))
            thumb.close()
            draw.text((x+3, y+181), f"f{index:04d} PTS {point.pts_time}s", font=font, fill="white")
            rows.append([index, index, point.pts, "1/1000", point.pts_time, len(jpeg), digest(jpeg)])
            completed += 1
            if cell == 15:
                data = contact_bytes(canvas)
                pin = write_new(ROOT, f"contacts/contact{index//16:03d}.jpg", data, "contacts")
                pin.update({"first_frame": index-15, "last_frame": index,
                            "first_pts": timeline.frame(index-15).pts, "last_pts": point.pts,
                            "valid_cells": 16, "padding_cells": 0})
                sheets.append(pin)
                canvas.close()
                canvas = Image.new("RGB", (1280, 792), "black")
                draw = ImageDraw.Draw(canvas)
        canvas.close()
        need(parser.one() is None, "Extra stdout JPEG after1200")
    except BaseException as exc:
        reason = type(exc).__name__ + ": " + str(exc)
        terminate(original)
    finally:
        code = custody.finish(reason is not None, stop, out)
        if reader not in custody.started:
            err.close()
    if reason is None:
        try:
            timeline.finish()
            need(code == 0 and not reader.is_alive() and not watch.is_alive(), "Original process/thread terminal differs")
            need(not timer_errors and completed == FRAMES and len(sheets) == SHEETS and len(endpoints) == 2,
                 "Materialized prefix incomplete")
        except BaseException as exc:
            reason = type(exc).__name__ + ": " + str(exc)
    write_new(ROOT, "ORIGINAL-WAIT.actual.json", encoded({"machine_id": MACHINE, "at_utc": stamp(),
              "original_Popen_pid": original.pid, "original_wait_returncode": code,
              "owned_FFmpeg_alive": original.poll() is None, "stderr_reader_alive": reader.is_alive(),
              "watchdog_alive": watch.is_alive(), "materialized_frames": len(sheets)*16,
              "processed_frame_records": completed, "complete_contact_sheets": len(sheets), "failure": reason,
              "no_retry": True}))
    csv_buffer = io.StringIO(newline="")
    csv_writer = csv.writer(csv_buffer)
    csv_writer.writerow(["local_index", "decoded_source_ordinal_from_zero", "actual_pts", "actual_time_base",
                         "actual_pts_seconds", "JPEG_bytes", "JPEG_sha256"])
    csv_writer.writerows(rows)
    trace_pin = write_new(ROOT, "source-frame-PTS.actual.csv", csv_buffer.getvalue().encode())
    log = bytes(timeline.raw_stderr)
    packed = gzip.compress(log, compresslevel=6, mtime=0)
    need(gzip.decompress(packed) == log, "Lossless stderr gzip CRC readback differs")
    log_pin = write_new(ROOT, "ffmpeg-stderr.actual.log.gz", packed)
    result = {"schema": "xar.R191.bounded-JPEG-pipe.actual.v1", "machine_id": MACHINE,
              "observed_at_utc": stamp(), "started_at_utc": started,
              "status": "EXTRACTION_COMPLETE_AI_REVIEW_PENDING" if reason is None else "PARTIAL_FAILED_PRESERVED_NO_RETRY",
              "reason": reason, "original_Popen_pid": original.pid, "original_wait_returncode": code,
              "owned_FFmpeg_alive": original.poll() is None, "stderr_reader_alive": reader.is_alive(),
              "watchdog_alive": watch.is_alive(), "timer_errors": timer_errors, "stderr_errors": timeline.errors,
              "stderr_truncated": timeline.truncated, "actual_time_base": str(timeline.time_base),
              "actual_PTS_count": len(timeline.rows), "materialized_frames": len(sheets)*16,
              "processed_frame_records": completed, "stdout_JPEG_messages_parsed": parsed_JPEG_messages, "sheets": sheets,
              "endpoints": endpoints, "source_frame_trace": trace_pin, "lossless_stderr": log_pin,
              "stderr_uncompressed_bytes": len(log), "stderr_uncompressed_sha256": digest(log),
              "gzip_CRC_readback_pass": True, "stdout_JPEG_bytes": stream_bytes,
              "stdout_JPEG_sha256": stream_hash.hexdigest(), "raw_stat_after": source_stat(RAW),
              "raw_body_hash_or_copy": False, "old3359frame_QA_repeated": False,
              "full1x_or_human_signoff": False, "formal_credit": 0,
              "actual_usage_before_receipt": usage(ROOT).wire()}
    write_new(ROOT, "EXTRACTION.actual.json", encoded(result))
    need(source_stat(RAW) == RETAINED_STAT, "Source stat changed after once extraction")
    usage(ROOT).check()
    return 0 if reason is None else 1
