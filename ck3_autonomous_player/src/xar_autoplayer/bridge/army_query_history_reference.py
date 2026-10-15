"""Read a complete Driver result only through its successful immutable receipt."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re

from .army_query_history_store import ARMY_QUERY_STEP, REFERENCE_KIND, SUMMARY_SCHEMA


def read_army_query_history_reference(
    summary: object, *, evidence_dir: Path, maximum_bytes: int,
) -> tuple[dict[str, object], dict[str, object]]:
    """Validate one exact reference; never glob, choose latest, retry or promote a partial.

    ``maximum_bytes`` is the caller's admitted finite read budget. This returns
    complete Driver JSON, not original transport bytes or independent gameplay
    qualification. Failed store writes deliberately remain unread as evidence.
    """
    if type(maximum_bytes) is not int or maximum_bytes <= 0:
        raise ValueError('a positive admitted sidecar read limit is required')
    if (not isinstance(summary,dict) or summary.get('history_summary_schema') != SUMMARY_SCHEMA
            or summary.get('full_result_preserved') is not True
            or summary.get('step') != ARMY_QUERY_STEP):
        raise ValueError('no successful complete Army sidecar reference is available')
    ref=summary.get('raw_result_reference')
    if (not isinstance(ref,dict) or ref.get('kind') != REFERENCE_KIND
            or ref.get('wire_bytes_preserved') is not False
            or type(ref.get('bytes')) is not int or not 0 < ref['bytes'] <= maximum_bytes
            or type(ref.get('sha256')) is not str or re.fullmatch('[0-9a-fA-F]{64}',ref['sha256']) is None
            or type(ref.get('path')) is not str):
        raise ValueError('Army sidecar reference lacks exact size/hash/type admission')
    path=Path(ref['path'])
    if (not path.is_absolute() or re.fullmatch('army-query-[0-9a-f]{32}\\.json',path.name) is None
            or path.resolve().parent != Path(evidence_dir).resolve()):
        raise ValueError('Army sidecar reference is outside the exact session evidence leaf')
    expected=ref['bytes'];digest=hashlib.sha256();parts=[];total=0
    with path.open('rb') as stream:
        before=os.fstat(stream.fileno())
        if before.st_size != expected:
            raise ValueError('Army sidecar actual size disagrees with its successful receipt')
        while chunk:=stream.read(min(1024*1024,expected-total+1)):
            total+=len(chunk)
            if total>expected:
                raise ValueError('Army sidecar grew beyond its successful receipt')
            digest.update(chunk);parts.append(chunk)
        after=os.fstat(stream.fileno())
    if ((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)
            !=(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)
            or total!=expected or digest.hexdigest()!=ref['sha256'].lower()):
        raise ValueError('Army sidecar bytes or identity changed from the successful receipt')
    value=json.loads(b''.join(parts).decode('utf-8'))
    required=('step','accepted','query_sequence','queried_snapshot_id','queried_revision','queried_native_revision')
    if (not isinstance(value,dict) or any(k not in summary or k not in value for k in required)
            or any(value[k]!=summary[k] for k in required)
            or type(value.get('accepted')) is not bool
            or type(value.get('query_sequence')) is not int or value['query_sequence'] <= 0
            or type(value.get('queried_revision')) is not int or value['queried_revision'] <= 0
            or type(value.get('queried_native_revision')) is not int or value['queried_native_revision'] <= 0
            or type(value.get('queried_snapshot_id')) is not str
            or not value['queried_snapshot_id']
            or not isinstance(value.get('army_strengths'),list)
            or type(summary.get('army_count')) is not int or summary['army_count']!=len(value['army_strengths'])):
        raise ValueError('Army sidecar body disagrees with its exact query summary')
    for key in ('status','backend_id','army_strengths_profile','army_observed_phase_coverage'):
        if key in summary and value.get(key)!=summary[key]:
            raise ValueError('Army sidecar profile/source differs from its summary')
    return value,dict(path=str(path.resolve()),bytes=total,sha256=digest.hexdigest(),
                      kind=REFERENCE_KIND,wire_bytes_preserved=False)
