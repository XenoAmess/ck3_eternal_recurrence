from __future__ import annotations
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
from typing import Literal, TypedDict
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.g2_saved_campaign.write_source27_canonical_ref_v1 import FileRef, parse_ref
MACHINE_ID = "xenoamess-full-tower-eb9d2c1186"
SOURCE28_COMMIT = "442beeae4676bad9a9d53cb7070a01f06e965761"
RELATIVE: Literal["xar_autoplayer/bridge/service.py"] = "xar_autoplayer/bridge/service.py"
BEFORE_BYTES = 879793
BEFORE_SHA = "d532887e030750ba9ef52d6a580a255e9f21f11758dd87eded113bad9a4e3aa4"
BEFORE_BLOB = "deef4c8d4b5cc33cac567a9b28d5801d5ddcd12f"
AFTER_BYTES = 879865
AFTER_SHA = "0dec3ce2404bd4fa2c0d1aa2d635c415816080052c2e47339d82759320b5e657"
ANCHOR_BYTES = 17555
ANCHOR_SHA = "3f0f25f46e6e0e9a260c9fa24b3c9ae2f9b7febeaf1c7d91c58b7c39f9b16dac"
BASE_BYTES = 411438
BASE_SHA = "0d903bb46616b91e4947ee838c64662ddcf3be14c89999bd1a5272f01c48f585"
FUNCTION_PINS = {
    "_observe_opening_lifestyle_perks_v1":
        "2fa2550f56209a7a3455960139a816f681677387cc5d47b575c57da8f7e19ff1",
    "_observe_opening_martial_authority_v1":
        "93d3245247a5b31ed9be64b5473a93e5d2a3544a1322366542576dd4557c5801",
}
class CandidateFileV1(TypedDict):
    relative: Literal["xar_autoplayer/bridge/service.py"]
    before_pin: FileRef
    after_pin: FileRef
class CandidateManifestV1(TypedDict):
    schema: Literal["xar.Source28-lifestyle-snapshot-lean-candidate/v1"]
    status: Literal["CANDIDATE_NOT_DEPLOYED"]
    machine_id: str
    parent_commit: str
    source28_anchor: FileRef
    source28_BASE: FileRef
    producer_ref: FileRef
    test_ref: FileRef
    qualification_ref: FileRef
    observed_at_utc: str
    files: list[CandidateFileV1]
    candidate_root: str
    runtime_calls: Literal[0]
    new_campaign_credit: Literal[0]
    original_whole_wall_start_utc: str
    never_replay: Literal[True]
def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
def _object(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(label + " must be an object")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError(label + " key type")
        result[key] = item
    return result
def _json_object(data: bytes, label: str) -> dict[str, object]:
    value: object = json.loads(data)
    return _object(value, label)
def _read(path: Path, limit: int) -> bytes:
    before = path.stat()
    if not path.is_file() or not 0 < before.st_size <= limit:
        raise ValueError("file bound: " + str(path))
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
        opened = os.fstat(stream.fileno())
    after = path.stat()
    def ident(stat: os.stat_result) -> tuple[int, int, int, int]:
        return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns
    if ident(before) != ident(opened) or ident(opened) != ident(after):
        raise ValueError("read ident changed: " + str(path))
    if len(data) != before.st_size:
        raise ValueError("read extent changed: " + str(path))
    return data
def _ref(path: Path, data: bytes) -> FileRef:
    return parse_ref({"path": str(path.resolve()), "bytes": len(data), "sha256": _sha(data)})
def _blob(data: bytes) -> str:
    blob = b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    return hashlib.sha1(blob).hexdigest()
def _check(data: bytes, size: int, digest: str, label: str) -> None:
    if len(data) != size or _sha(data) != digest:
        raise ValueError(label + " bytes/SHA mismatch")
def patch_service_functions_v1(source: bytes) -> bytes:
    text = source.decode("utf-8")
    tree = ast.parse(text)
    found: dict[str, ast.FunctionDef] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in FUNCTION_PINS:
            if node.name in found:
                raise ValueError("duplicate function")
            digest = _sha(ast.dump(node, include_attributes=False).encode("utf-8"))
            if digest != FUNCTION_PINS[node.name]:
                raise ValueError("function AST mismatch: " + node.name)
            found[node.name] = node
    if set(found) != set(FUNCTION_PINS):
        raise ValueError("missing function")
    lines = text.splitlines(keepends=True)
    changes = 0
    for node in found.values():
        if node.end_lineno is None:
            raise ValueError("missing extent")
        count = 0
        for index in range(node.lineno - 1, node.end_lineno):
            if "self.snapshot()" in lines[index]:
                count += lines[index].count("self.snapshot()")
                lines[index] = lines[index].replace(
                    "self.snapshot()", "self.snapshot(include_native_command_history=False)")
        if count != 1:
            raise ValueError("snapshot count")
        changes += count
    result = "".join(lines).encode("utf-8")
    if changes != 2 or len(result) != len(source) + 72:
        raise ValueError("bad transform extent")
    compile(result, "<Source28-lifestyle-candidate>", "exec")
    return result
def _write_new(path: Path, data: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    if _read(path, len(data)) != data:
        raise ValueError("readback mismatch: " + str(path))
def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")
def prepare_candidate_v1(
    *, anchor_path: Path, base_path: Path, candidate_root: Path,
    test_path: Path, machine_id: str,
) -> CandidateManifestV1:
    if machine_id != MACHINE_ID:
        raise ValueError("machine mismatch")
    anchor_data, base_data = _read(anchor_path, ANCHOR_BYTES), _read(base_path, BASE_BYTES)
    _check(anchor_data, ANCHOR_BYTES, ANCHOR_SHA, "anchor")
    _check(base_data, BASE_BYTES, BASE_SHA, "BASE")
    anchor, base = _json_object(anchor_data, "anchor"), _json_object(base_data, "BASE")
    if (anchor.get("schema") != "xar.source28.canonical-git-anchor/v1"
            or anchor.get("status") != "CANONICAL_REF_CREATED_NOT_DEPLOYED"
            or anchor.get("commit") != SOURCE28_COMMIT
            or base.get("schema") != "root.ck3.final-sdk-freeze/v1"
            or base.get("status") != "FINAL_SOURCE_FROZEN"
            or base.get("business_source_commit") != SOURCE28_COMMIT
            or anchor.get("machine_id") != machine_id or base.get("machine_id") != machine_id):
        raise ValueError("Source28 binding")
    anchor_ref = _ref(anchor_path, anchor_data)
    if _object(base.get("source28_canonical_anchor"), "anchor") != anchor_ref:
        saved = _object(base.get("source28_canonical_anchor"), "anchor")
        if (set(saved) != {"path", "bytes", "sha256"} or type(saved["bytes"]) is not int
                or saved["bytes"] != ANCHOR_BYTES or saved["sha256"] != ANCHOR_SHA
                or not isinstance(saved["path"], str)
                or Path(saved["path"]).resolve() != anchor_path.resolve()):
            raise ValueError("anchor mismatch")
    rows = base.get("files")
    if not isinstance(rows, list) or len(rows) != 1464:
        raise ValueError("file inventory mismatch")
    matches: list[dict[str, object]] = []
    for value in rows:
        row = _object(value, "file row")
        if row.get("relative") == RELATIVE:
            matches.append(row)
    if len(matches) != 1:
        raise ValueError("service row count")
    wanted = {"relative": RELATIVE, "bytes": BEFORE_BYTES, "sha256": BEFORE_SHA,
                "git_blob_sha1": BEFORE_BLOB, "git_mode": "100644"}
    if (matches[0] != wanted or type(matches[0].get("bytes")) is not int):
        raise ValueError("service row mismatch")
    source_root = base.get("source_root")
    if not isinstance(source_root, str) or not Path(source_root).is_absolute():
        raise ValueError("source_root relative")
    source_path = Path(source_root) / RELATIVE
    source_data = _read(source_path, BEFORE_BYTES)
    _check(source_data, BEFORE_BYTES, BEFORE_SHA, "service source")
    if _blob(source_data) != BEFORE_BLOB:
        raise ValueError("service blob mismatch")
    result = patch_service_functions_v1(source_data)
    _check(result, AFTER_BYTES, AFTER_SHA, "service")
    self_path = Path(__file__).resolve()
    self_data, test_data = _read(self_path, 24576), _read(test_path, 24576)
    if len(self_data) + len(test_data) > 24576:
        raise ValueError("producer/test exceed 24KiB")
    if not candidate_root.is_absolute() or candidate_root.exists():
        raise ValueError("output root invalid")
    if candidate_root.resolve().is_relative_to(Path(source_root).resolve()):
        raise ValueError("candidate overlaps SDK")
    candidate_root.mkdir()
    service_out = candidate_root / RELATIVE
    service_out.parent.mkdir(parents=True)
    _write_new(service_out, result)
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    run = subprocess.run(
        [sys.executable, "-B", str(test_path), "--before", str(source_path),
         "--after", str(service_out)], env=environment, capture_output=True, check=False)
    if run.returncode != 0:
        sys.stderr.buffer.write(run.stderr)
        raise RuntimeError("qual failed")
    qual = _json_object(run.stdout, "qual stdout")
    if (qual.get("schema") != "xar.Source28-lifestyle-snapshot-lean-qualification/v1"
            or qual.get("status") != "PASS"
            or type(qual.get("runtime_cases_passed")) is not int
            or qual.get("runtime_cases_passed") != 12
            or qual.get("new_campaign_credit") != 0
            or type(qual.get("new_campaign_credit")) is not int):
        raise ValueError("qual mismatch")
    qual.update(
        machine_id=machine_id, source28_anchor=anchor_ref,
        source28_BASE=_ref(base_path, base_data),
        before_pin=_ref(source_path, source_data), after_pin=_ref(service_out, result),
        producer_ref=_ref(self_path, self_data), test_ref=_ref(test_path, test_data))
    qual_path = candidate_root / "SOURCE29-LIFESTYLE-LEAN-QUALIFICATION.json"
    qual_data = _json_bytes(qual)
    _write_new(qual_path, qual_data)
    manifest: CandidateManifestV1 = {
        "schema": "xar.Source28-lifestyle-snapshot-lean-candidate/v1",
        "status": "CANDIDATE_NOT_DEPLOYED", "machine_id": machine_id,
        "parent_commit": SOURCE28_COMMIT, "source28_anchor": anchor_ref,
        "source28_BASE": _ref(base_path, base_data),
        "producer_ref": _ref(self_path, self_data), "test_ref": _ref(test_path, test_data),
        "qualification_ref": _ref(qual_path, qual_data),
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "files": [{"relative": RELATIVE, "before_pin": _ref(source_path, source_data), "after_pin": _ref(service_out, result)}],
        "candidate_root": str(candidate_root.resolve()), "runtime_calls": 0,
        "new_campaign_credit": 0,
        "original_whole_wall_start_utc": "2026-10-19T03:26:49.420926Z", "never_replay": True}
    _write_new(candidate_root / "SOURCE29-LIFESTYLE-LEAN-CANDIDATE.json", _json_bytes(manifest))
    return manifest
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source28-anchor", required=True, type=Path)
    parser.add_argument("--source28-base", required=True, type=Path)
    parser.add_argument("--candidate-root", required=True, type=Path)
    parser.add_argument("--test", required=True, type=Path)
    parser.add_argument("--machine-id", required=True)
    args = parser.parse_args()
    manifest = prepare_candidate_v1(
        anchor_path=args.source28_anchor, base_path=args.source28_base,
        candidate_root=args.candidate_root, test_path=args.test,
        machine_id=args.machine_id)
    print(_json_bytes(manifest).decode("utf-8"), end="")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
