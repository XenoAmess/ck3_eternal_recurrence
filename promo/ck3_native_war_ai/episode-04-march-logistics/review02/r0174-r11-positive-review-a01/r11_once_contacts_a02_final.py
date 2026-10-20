"""R11 a02 typed selected-prefix extractor. No invocation before Root once grant and updated source-bound cap.
JPEG boundary parsing is inherited from qualified R07. New JSON fields use the shared validated domain.
"""
from __future__ import annotations
import argparse
import csv
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
import datetime
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import threading
import time
from typing import Protocol
from PIL import Image
from r11_visual_contract_a02 import FilePin, RawStat, Recipe, integer, load_map, object_map, text

def stamp() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def need(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)

@dataclass(frozen=True)
class Usage:
    contacts: int
    metadata: int

    @property
    def aggregate(self) -> int:
        return self.contacts+self.metadata

    def wire(self) -> dict[str, object]:
        return dict(contacts=self.contacts,metadata=self.metadata,aggregate=self.aggregate)

def usage(root: Path) -> Usage:
    contacts=0
    metadata=0
    for path in root.rglob("*"):
        if path.is_file():
            if path.name.startswith("contact-"):
                contacts+=path.stat().st_size
            else:
                metadata+=path.stat().st_size
    return Usage(contacts,metadata)

def save(root: Path, name: str, value: dict[str, object]) -> FilePin:
    body=(json.dumps(value,ensure_ascii=True,separators=(",",":"))+"\n").encode()
    current=usage(root)
    need(current.metadata+len(body)<=262144,"Metadata hard limit")
    need(current.aggregate+len(body)<=5242880,"Aggregate hard limit")
    path=root/name
    with path.open("xb") as stream:
        stream.write(body)
    return FilePin.read(path)

class ByteReader(Protocol):
    def read(self, size: int = -1, /) -> bytes: ...

def jpeg_read(stream: ByteReader) -> bytes:
    def readn(count: int) -> bytes:
        data=stream.read(count)
        if len(data)!=count:
            raise EOFError("Incomplete JPEG or pipe EOF")
        return data
    data=bytearray(readn(2))
    need(data==b"\xff\xd8","JPEG SOI differs")
    marker: int | None=None
    while True:
        need(len(data)<=2*1024*1024,"Single JPEG memory bound")
        if marker is None:
            need(readn(1)==b"\xff","JPEG marker prefix differs")
            code=readn(1)
            while code==b"\xff":
                code=readn(1)
            marker=code[0]
            data.extend((255,marker))
        if marker==217:
            return bytes(data)
        need(marker not in (0,216),"Invalid JPEG marker")
        if marker==1 or 208<=marker<=215:
            marker=None
            continue
        length=readn(2)
        data.extend(length)
        count=int.from_bytes(length,"big")
        need(count>=2,"JPEG segment length differs")
        data.extend(readn(count-2))
        if marker!=218:
            marker=None
            continue
        while True:
            code=readn(1)
            data.extend(code)
            if code!=b"\xff":
                continue
            code=readn(1)
            data.extend(code)
            while code==b"\xff":
                code=readn(1)
                data.extend(code)
            if code==b"\x00" or 208<=code[0]<=215:
                continue
            marker=code[0]
            break

def ffmpeg_census(root: Path, machine_id: str) -> None:
    """OS process-name census only; avoid an untyped psutil import."""
    argv=["C:/Windows/System32/tasklist.exe","/FI","IMAGENAME eq ffmpeg.exe","/FO","CSV","/NH"]
    done: subprocess.CompletedProcess[bytes]=subprocess.run(argv,capture_output=True,
        timeout=10,creationflags=subprocess.CREATE_NO_WINDOW)
    output=done.stdout.decode("utf8","replace")
    save(root,"FFMPEG-CENSUS-BEFORE.actual.json",dict(machine_id=machine_id,
        observed_at_utc=stamp(),argv=argv,returncode=done.returncode,
        stdout=output,stderr=done.stderr.decode("utf8","replace"),
        query_only=True))
    need(done.returncode==0,"OS FFmpeg census failed")
    need("ffmpeg.exe" not in output.casefold(),"Another FFmpeg is active")

def priority_class(pid: int) -> int:
    """Narrow ctypes boundary: validate native HANDLE/DWORD before publishing."""
    kernel=ctypes.WinDLL("kernel32",use_last_error=True)
    opener=kernel.OpenProcess
    opener.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
    opener.restype=wintypes.HANDLE
    getter=kernel.GetPriorityClass
    getter.argtypes=[wintypes.HANDLE]
    getter.restype=wintypes.DWORD
    closer=kernel.CloseHandle
    closer.argtypes=[wintypes.HANDLE]
    closer.restype=wintypes.BOOL
    handle: object=opener(0x1000,False,pid)
    if type(handle) is not int or handle<=0:
        raise OSError(ctypes.get_last_error(),"OpenProcess query priority failed")
    try:
        value: object=getter(ctypes.c_void_p(handle))
        return integer(value,"actual process priority",1)
    finally:
        closer(ctypes.c_void_p(handle))

@dataclass(frozen=True)
class Trace:
    frame: int
    ticks: int
    seconds: str

@dataclass(frozen=True)
class Sheet:
    sheet_id: int
    image: FilePin
    first: int
    end: int
    dimensions: tuple[int,int]

    def wire(self, trace: list[Trace]) -> dict[str, object]:
        pts: list[int] | None=None
        if len(trace)>=self.end:
            pts=[trace[self.first].ticks,trace[self.end-1].ticks]
        return dict(sheet_id=self.sheet_id,image=self.image.wire(),
            source_frames_half_open=[self.first,self.end],
            local_frames_half_open=[self.first,self.end],
            valid_cells=self.end-self.first,actual_dimensions=list(self.dimensions),
            actual_PTS_ticks_first_last=pts)

def check_execution(recipe: Recipe, recipe_path: Path, recipe_sha: str,
                    capacity_path: Path, capacity_sha: str) -> None:
    need(FilePin.read(recipe_path).sha256==recipe_sha,"Recipe pin differs")
    need(FilePin.read(capacity_path).sha256==capacity_sha,"Capacity pin differs")
    cap=load_map(capacity_path)
    need(cap.get("machine_id")==recipe.machine_id,"Capacity machine differs")
    need(cap.get("source_bound_single_extraction_execution_admitted") is True and
        cap.get("FFmpeg_execution_admitted") is True,"Financial-only capacity refuses")
    need(Path(text(cap.get("aggregate_root"),"aggregate_root")).resolve()==recipe.output_root.resolve(),
         "Exact root differs")
    need(FilePin.parse(cap.get("recipe"),"cap.recipe")==FilePin.read(recipe_path),"Capacity recipe differs")
    need(FilePin.parse(cap.get("runner"),"cap.runner")==recipe.runner,"Capacity runner differs")
    need(FilePin.read(Path(__file__))==recipe.runner,"Frozen runner differs")

def execute(recipe_path: Path, recipe_sha: str, capacity_path: Path, capacity_sha: str) -> None:
    recipe=Recipe.parse(load_map(recipe_path))
    check_execution(recipe,recipe_path,recipe_sha,capacity_path,capacity_sha)
    root=recipe.output_root
    need(root.exists() and all(p.is_file() for p in root.iterdir()),"Unexpected root/directory")
    need(not (root/"ONCE-CLAIM.actual.json").exists() and not list(root.glob("contact-*.jpg")),
         "Existing/unknown attempt; no replay")
    deadline=datetime.datetime.fromisoformat(recipe.hard_deadline_utc.replace("Z","+00:00")).timestamp()
    need(time.time()<deadline-60,"Too little original time for closure")
    save(root,"ONCE-CLAIM.actual.json",dict(machine_id=recipe.machine_id,observed_at_utc=stamp(),
        recipe=FilePin.read(recipe_path).wire(),capacity=FilePin.read(capacity_path).wire(),
        runner=FilePin.read(Path(__file__)).wire(),
        Root_authorization="Updated a02 source-bound cap plus Root actual once grant; one FFmpeg only",
        max_FFmpeg_attempts=1,conditional_fullres=False,
        historical_process_birth_filetime=recipe.process_birth_filetime))
    fixture=io.BytesIO()
    Image.new("RGB",(2,2)).save(fixture,format="JPEG")
    synthetic=fixture.getvalue()
    need(jpeg_read(io.BytesIO(synthetic))==synthetic,"Inherited JPEG parser sanity failed")
    save(root,"PARSER-SANITY.actual.json",dict(kind="In-memory2x2 JPEG only",
        file_or_FFmpeg_or_source_calls=0,passed=True))
    release_argv=["gh","release","view","--repo","XenoAmess/xar_promo_toolchain",
        "--json","tagName,isDraft,isPrerelease,publishedAt,url"]
    latest: subprocess.CompletedProcess[bytes]=subprocess.run(release_argv,capture_output=True,
        timeout=20,creationflags=subprocess.CREATE_NO_WINDOW)
    save(root,"LATEST-RELEASE.actual.json",dict(observed_at_utc=stamp(),returncode=latest.returncode,
        argv=release_argv,stdout=latest.stdout.decode("utf8","replace"),
        stderr=latest.stderr.decode("utf8","replace"),no_download=True))
    need(latest.returncode==0,"Latest formal Release read-only query failed; no FFmpeg")
    released: object=json.loads(latest.stdout)
    release=object_map(released,"release")
    need(release.get("isDraft") is False and release.get("isPrerelease") is False,"Not formal Release")
    source=Path(recipe.retained_source.path)
    before=RawStat.from_native(source.stat())
    need(before==recipe.retained_source_stat,"Retained raw stat identity differs")
    ffmpeg_census(root,recipe.machine_id)
    save(root,"SOURCE-STAT-BEFORE.actual.json",dict(machine_id=recipe.machine_id,
        observed_at_utc=stamp(),actual=before.wire(),body_rehashed=False))
    save(root,"COMMAND.actual.json",dict(argv=recipe.argv,cwd=recipe.cwd,
        expected_dimensions=list(recipe.dimensions),new_raw_probe=False))
    stderr_path=root/"ffmpeg-stderr.actual.log.gz"
    trace: list[Trace]=[]
    sheets: list[Sheet]=[]
    reason: str | None=None
    errors: list[str]=[]
    raw_hash=hashlib.sha256()
    raw_bytes: list[int]=[0]
    truncated: list[bool]=[False]
    diagnostics=(root/"image-dimensions.actual.jsonl").open("x",encoding="utf8")
    usages=(root/"usage-by-sheet.actual.csv").open("x",encoding="utf8",newline="")
    writer=csv.writer(usages)
    writer.writerow(["sheet","JPEG_bytes","contacts_bytes","metadata_bytes","aggregate_bytes"])
    started=stamp()
    clock=time.monotonic()
    proc: subprocess.Popen[bytes]=subprocess.Popen(recipe.argv,cwd=recipe.cwd,
        stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
    out=proc.stdout
    err=proc.stderr
    if out is None or err is None:
        proc.terminate()
        proc.wait(timeout=10)
        raise RuntimeError("Original process pipes unavailable")
    try:
        save(root,"OWNED-PROCESS.actual.json",dict(pid=proc.pid,started_at_utc=started,
            requested_priority=subprocess.BELOW_NORMAL_PRIORITY_CLASS))
        actual_priority=priority_class(proc.pid)
        need(actual_priority==subprocess.BELOW_NORMAL_PRIORITY_CLASS,"Actual process priority differs")
        save(root,"OWNED-PRIORITY.actual.json",dict(pid=proc.pid,
            actual_priority=actual_priority,observed_at_utc=stamp()))
    except BaseException as exc:
        if proc.poll() is None:
            proc.terminate()
        try:
            failed_code=proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            failed_code=proc.wait(timeout=5)
        out.close()
        err.close()
        diagnostics.close()
        usages.close()
        save(root,"SPAWN-READBACK-FAILURE.actual.json",dict(machine_id=recipe.machine_id,
            observed_at_utc=stamp(),original_Popen_pid=proc.pid,original_wait_returncode=failed_code,
            owned_FFmpeg_alive=proc.poll() is None,error=type(exc).__name__+": "+str(exc),no_retry=True))
        raise
    stop=threading.Event()
    def stderr_reader() -> None:
        try:
            with gzip.open(stderr_path,"xb",compresslevel=6) as log:
                for rawline in iter(err.readline,b""):
                    log.write(rawline)
                    raw_hash.update(rawline)
                    raw_bytes[0]+=len(rawline)
                    match=re.search(rb"n:\s*(\d+)\s+pts:\s*(-?\d+)\s+pts_time:([^ ]+)",rawline)
                    if match:
                        trace.append(Trace(int(match[1]),int(match[2]),match[3].decode()))
                    if usage(root).metadata>196608:
                        errors.append("Metadata guard; partial stderr explicitly retained")
                        truncated[0]=True
                        proc.terminate()
                        break
        except BaseException as exc:
            errors.append(type(exc).__name__+": "+str(exc))
        finally:
            err.close()
    def watchdog() -> None:
        nonlocal reason
        while not stop.wait(.05) and proc.poll() is None:
            if time.time()>=deadline-20:
                reason="Original2200deadline closure reserve"
                try:
                    proc.terminate()
                except OSError:
                    pass
                return
    reader=threading.Thread(target=stderr_reader)
    watch=threading.Thread(target=watchdog)
    reader.start()
    watch.start()
    try:
        for index in range(38):
            data=jpeg_read(out)
            digest=hashlib.sha256(data).hexdigest()
            with Image.open(io.BytesIO(data)) as image:
                dimensions=image.size
                diagnostics.write(json.dumps(dict(sheet=index,actual_dimensions=list(dimensions),
                    expected_dimensions=list(recipe.dimensions),JPEG_bytes=len(data),sha256=digest))+"\n")
                diagnostics.flush()
                image.load()
            need(dimensions==recipe.dimensions,"Actual JPEG geometry differs")
            current=usage(root)
            if current.contacts+len(data)>4194304 or current.aggregate+len(data)+131072>5242880:
                reason="Next exact JPEG exceeds4MiB contacts/5MiB total reserve"
                proc.terminate()
                break
            path=root/("contact-%03d.jpg"%index)
            with path.open("xb") as stream:
                stream.write(data)
            first=index*16
            end=min(first+16,600)
            sheets.append(Sheet(index,FilePin(str(path),len(data),digest),first,end,dimensions))
            current=usage(root)
            writer.writerow([index,len(data),current.contacts,current.metadata,current.aggregate])
            usages.flush()
            if index%8==7:
                print(json.dumps(dict(sheets=index+1,usage=current.wire())),flush=True)
    except BaseException as exc:
        reason=reason or type(exc).__name__+": "+str(exc)
        if proc.poll() is None:
            proc.terminate()
    try:
        code=proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        reason=reason or "Original terminate wait timeout"
        proc.kill()
        code=proc.wait(timeout=5)
    stop.set()
    watch.join(timeout=5)
    reader.join(timeout=5)
    diagnostics.close()
    usages.close()
    out.close()
    need(not reader.is_alive() and not watch.is_alive(),"Owned reader/watch did not close")
    trace_path=root/"source-frame-PTS.actual.csv"
    with trace_path.open("x",encoding="utf8",newline="") as trace_stream:
        csvwriter=csv.writer(trace_stream)
        csvwriter.writerow(["frame","PTS_ticks","PTS_seconds"])
        csvwriter.writerows((t.frame,t.ticks,t.seconds) for t in trace)
    complete=(code==0 and reason is None and not errors and len(sheets)==38 and len(trace)==600 and
        [t.frame for t in trace]==list(range(600)) and trace[0].ticks==0 and trace[-1].ticks==19967 and
        all(right.ticks-left.ticks in (33,34) for left,right in zip(trace,trace[1:])))
    after=RawStat.from_native(source.stat())
    if after!=before:
        reason=reason or "Source raw stat changed during read"
        complete=False
    result=save(root,"EXTRACTION.actual.json",dict(schema="xar.R0174.600-prefix-contact-extraction.v2",
        machine_id=recipe.machine_id,observed_at_utc=stamp(),
        status="EXTRACTION_COMPLETE_AI_REVIEW_PENDING" if complete else "PARTIAL_FAILED_PRESERVED_NO_RETRY",
        original_Popen_pid=proc.pid,original_Popen_wait_returned=True,exit_code=code,
        elapsed_seconds=time.monotonic()-clock,reason=reason,reader_error=errors,
        source_trace_count=len(trace),source_trace=FilePin.read(trace_path).wire(),
        complete_sheets=len(sheets),materialized_valid_cells=sum(s.end-s.first for s in sheets),
        sheets=[s.wire(trace) for s in sheets],
        dimensions_diagnostics=FilePin.read(root/"image-dimensions.actual.jsonl").wire(),
        usage_by_sheet=FilePin.read(root/"usage-by-sheet.actual.csv").wire(),
        full_stderr_lossless_gzip=FilePin.read(stderr_path).wire(),
        uncompressed_stderr_bytes=raw_bytes[0],uncompressed_stderr_SHA256=raw_hash.hexdigest(),
        stderr_truncated=truncated[0],actual_source_stat_after=after.wire(),
        raw_hash_or_probe_or_copy=False,old_fullraw_QA_repeated=False,fullraw_EOF_claim=False,
        clean=False,human1x=False,human_signoff=False,formal_credit=0,remaining_heavy=0,
        usage_before_result=usage(root).wire()))
    crc_hash=hashlib.sha256()
    crc_bytes=0
    with gzip.open(stderr_path,"rb") as crc_stream:
        for chunk in iter(lambda:crc_stream.read(65536),b""):
            crc_hash.update(chunk)
            crc_bytes+=len(chunk)
    crc_ok=crc_bytes==raw_bytes[0] and crc_hash.hexdigest()==raw_hash.hexdigest()
    need(crc_ok,"Independent gzip EOF/CRC readback differs")
    save(root,"GZIP-CRC-AND-OWNED-WAIT.actual.json",dict(machine_id=recipe.machine_id,
        observed_at_utc=stamp(),lossless_gzip=FilePin.read(stderr_path).wire(),
        gzip_EOF_CRC_readback_pass=True,bytes=crc_bytes,sha256=crc_hash.hexdigest(),
        original_Popen_pid=proc.pid,original_wait_returncode=code,owned_FFmpeg_alive=proc.poll() is None,
        reader_alive=reader.is_alive(),watchdog_alive=watch.is_alive(),no_retry=True))
    current=usage(root)
    need(current.contacts<=4194304 and current.metadata<=262144 and current.aggregate<=5242880,
        "Final cap differs")
    print(json.dumps(dict(result=result.wire(),
        status="EXTRACTION_COMPLETE_AI_REVIEW_PENDING" if complete else "PARTIAL_FAILED_PRESERVED_NO_RETRY",
        usage=current.wire(),remaining_heavy=0)),flush=True)

def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--recipe",required=True)
    parser.add_argument("--recipe-sha",required=True)
    parser.add_argument("--capacity",required=True)
    parser.add_argument("--capacity-sha",required=True)
    args=parser.parse_args()
    recipe_name: object=args.recipe
    recipe_sha: object=args.recipe_sha
    capacity_name: object=args.capacity
    capacity_sha: object=args.capacity_sha
    execute(Path(text(recipe_name,"recipe argument")),text(recipe_sha,"recipe SHA argument"),
            Path(text(capacity_name,"capacity argument")),text(capacity_sha,"capacity SHA argument"))

if __name__=="__main__":
    main()
