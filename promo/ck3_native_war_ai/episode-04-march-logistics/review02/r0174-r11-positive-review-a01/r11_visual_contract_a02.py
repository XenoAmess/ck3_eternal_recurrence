"""R11 v2 JSON boundary. uint64 identity/time is canonical decimal text.
Legacy source receipts remain byte-exact; only newly produced wire fields use this domain.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re

MAX_SAFE_INTEGER = 2**53-1
MAX_UINT64 = 2**64-1

def object_map(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(label+" must be object")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError(label+" key must be text")
        result[key] = item
    return result

def load_map(path: Path) -> dict[str, object]:
    value: object = json.loads(path.read_text(encoding="utf8"))
    return object_map(value, str(path))

def text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(label+" must be nonempty text")
    return value

def integer(value: object, label: str, lower: int = 0) -> int:
    if type(value) is not int or not lower <= value <= MAX_SAFE_INTEGER:
        raise ValueError(label+" must be exact safe integer")
    return value

def decimal64(value: object, label: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"0|[1-9][0-9]*", value) is None:
        raise ValueError(label+" must be canonical decimal text")
    if int(value)>MAX_UINT64:
        raise ValueError(label+" exceeds uint64")
    return value

def decimal_from_native(value: int, label: str) -> str:
    if type(value) is not int or not 0 <= value <= MAX_UINT64:
        raise ValueError(label+" invalid native uint64")
    return str(value)

def string_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(label+" must be array")
    return [text(item, label+" item") for item in value]

@dataclass(frozen=True)
class FilePin:
    path: str
    bytes: int
    sha256: str

    @classmethod
    def read(cls, path: Path) -> FilePin:
        body=path.read_bytes()
        return cls(str(path), len(body), hashlib.sha256(body).hexdigest())

    @classmethod
    def parse(cls, value: object, label: str) -> FilePin:
        row=object_map(value,label)
        digest=text(row.get("sha256"), label+".sha256")
        if re.fullmatch("[0-9a-f]{64}",digest) is None:
            raise ValueError(label+" digest differs")
        return cls(text(row.get("path"),label+".path"),
                   integer(row.get("bytes"),label+".bytes"),digest)

    def wire(self) -> dict[str, object]:
        return dict(path=self.path,bytes=self.bytes,sha256=self.sha256)

@dataclass(frozen=True)
class RawStat:
    bytes: int
    mtime_ns: str
    st_dev: str
    st_ino: str

    @classmethod
    def from_native(cls, value: os.stat_result) -> RawStat:
        return cls(integer(value.st_size,"native size"),
            decimal_from_native(value.st_mtime_ns,"native mtime_ns"),
            decimal_from_native(value.st_dev,"native st_dev"),
            decimal_from_native(value.st_ino,"native st_ino"))

    @classmethod
    def parse(cls, value: object) -> RawStat:
        row=object_map(value,"retained_source_stat")
        if set(row)!=set(("bytes","mtime_ns","st_dev","st_ino")):
            raise ValueError("RawStat fields differ")
        return cls(integer(row.get("bytes"),"RawStat.bytes"),
            decimal64(row.get("mtime_ns"),"RawStat.mtime_ns"),
            decimal64(row.get("st_dev"),"RawStat.st_dev"),
            decimal64(row.get("st_ino"),"RawStat.st_ino"))

    def wire(self) -> dict[str, object]:
        return dict(bytes=self.bytes,mtime_ns=self.mtime_ns,st_dev=self.st_dev,st_ino=self.st_ino)

@dataclass(frozen=True)
class Recipe:
    machine_id: str
    output_root: Path
    hard_deadline_utc: str
    runner: FilePin
    retained_source: FilePin
    retained_source_stat: RawStat
    argv: list[str]
    cwd: str
    dimensions: tuple[int,int]
    process_birth_filetime: str

    @classmethod
    def parse(cls, value: object) -> Recipe:
        row=object_map(value,"recipe")
        dims=row.get("expected_sheet_dimensions")
        if not isinstance(dims,list) or len(dims)!=2:
            raise ValueError("dimensions must have2 entries")
        dimension=(integer(dims[0],"width",1),integer(dims[1],"height",1))
        if dimension!=(1280,792):
            raise ValueError("R11 geometry differs")
        binding=object_map(row.get("historical_binding"),"historical_binding")
        return cls(text(row.get("machine_id"),"machine_id"),
            Path(text(row.get("output_root"),"output_root")),
            text(row.get("hard_deadline_utc"),"deadline"),
            FilePin.parse(row.get("runner"),"runner"),
            FilePin.parse(row.get("retained_source"),"retained_source"),
            RawStat.parse(row.get("retained_source_stat")),
            string_list(row.get("argv"),"argv"),text(row.get("cwd"),"cwd"),
            dimension,decimal64(binding.get("process_birth_filetime"),"process_birth_filetime"))
