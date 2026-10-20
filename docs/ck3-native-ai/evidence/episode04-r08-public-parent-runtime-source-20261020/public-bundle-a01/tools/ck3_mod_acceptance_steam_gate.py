"""Consume one current-machine background observation; never operate Steam/UI."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Protocol, TypedDict

from steam_offline_state_contract import ProcessIdentity, ProbeResult, parse_result
from steam_offline_native_provider_v1 import _qualified_source, _validated_identity


class FilePin(TypedDict):
    path: str
    bytes: int
    sha256: str


class OfflineAdmission(TypedDict):
    schema: str
    machine_id: str
    observed_at_utc: str
    receipt: FilePin
    steam_pid: int
    steam_birth_filetime: str
    observation_method: str
    background_only: bool


class IdentityReader(Protocol):
    def identity(self, pid: int) -> ProcessIdentity: ...


def file_pin(path: Path) -> FilePin:
    size = path.stat().st_size
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    if path.stat().st_size != size:
        raise ValueError('Source changed during observation')
    return FilePin(path=str(path.resolve()), bytes=size, sha256=digest.hexdigest())


def validate_observation(value: object, *, machine_id: str, reader: IdentityReader,
                         now: datetime | None = None) -> ProbeResult:
    result = parse_result(value)
    now = now or datetime.now(timezone.utc)
    stamp = datetime.fromisoformat(result.observed_at_utc.replace('Z', '+00:00'))
    if (result.machine_id != machine_id or result.status != 'offline'
            or stamp.tzinfo is None or not 0 <= (now - stamp).total_seconds() <= 30
            or result.steam is None or result.source is None):
        raise ValueError('Fresh same-machine background offline observation required')
    if reader.identity(result.steam.pid) != result.steam:
        raise ValueError('Observed Steam incarnation changed')
    _validated_identity(result.steam)
    # This launch profile admits only the exact native offline-positive producer.
    # The general parser also understands CEF, which this launch profile does not qualify.
    from steam_offline_native_provider_v1 import (IMAGE_SHA256, IMAGE_BYTES, IMAGE_SIZE,
        VALUE_RVA, PRODUCER_RVA, PRODUCER, TRAY_MANAGER_RVA, TRAY_OFFSET)
    evidence = result.native_evidence
    if (result.observation_method != 'native_current_user_byte' or evidence is None
            or result.source.sha256 != IMAGE_SHA256 or result.source.bytes != IMAGE_BYTES
            or Path(result.source.path).resolve() != (Path(result.steam.exe).parent/'steamui.dll').resolve()
            or evidence.module_size != IMAGE_SIZE or int(evidence.value_rva) != VALUE_RVA
            or int(evidence.producer_rva) != PRODUCER_RVA
            or evidence.producer_anchor_hex != PRODUCER.hex()
            or int(evidence.tray_manager_pointer_rva) != TRAY_MANAGER_RVA
            or int(evidence.tray_state_offset) != TRAY_OFFSET):
        raise ValueError('Background provider source/profile is not qualified for this launch')
    return result


def validate_receipt(path: Path, *, machine_id: str, reader: IdentityReader,
                     now: datetime | None = None) -> OfflineAdmission:
    if not 0 < path.stat().st_size <= 65536:
        raise ValueError('Bounded actual Steam receipt required')
    payload = path.read_bytes()
    if len(payload) > 65536:
        raise ValueError('Steam receipt grew')
    result = validate_observation(json.loads(payload), machine_id=machine_id,
                                  reader=reader, now=now)
    source = result.source
    if source is None:
        raise ValueError('Actual source absent')
    actual_source = _qualified_source(source.path)
    if actual_source != source:
        raise ValueError('Observed Steam source changed')
    receipt = FilePin(path=str(path.resolve()), bytes=len(payload),
                      sha256=hashlib.sha256(payload).hexdigest())
    if path.read_bytes() != payload or reader.identity(result.steam.pid) != result.steam:
        raise ValueError('Receipt or Steam incarnation changed before admission')
    validate_observation(json.loads(payload), machine_id=machine_id, reader=reader)
    return OfflineAdmission(schema='ck3-mod-acceptance-background-offline-admission-v1',
        machine_id=machine_id, observed_at_utc=result.observed_at_utc, receipt=receipt,
        steam_pid=result.steam.pid, steam_birth_filetime=result.steam.birth_filetime,
        observation_method=str(result.observation_method), background_only=True)


def recheck_before_popen(admission: OfflineAdmission, *, reader: IdentityReader) -> None:
    ref = admission['receipt']
    path = Path(ref['path'])
    if path.stat().st_size != ref['bytes'] or not 0 < ref['bytes'] <= 65536:
        raise ValueError('Actual admission receipt changed')
    payload = path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != ref['sha256']:
        raise ValueError('Actual admission receipt content changed')
    validate_observation(json.loads(payload), machine_id=admission['machine_id'], reader=reader)
