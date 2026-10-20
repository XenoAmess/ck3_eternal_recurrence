"""Compose a source-bound C23 compiled-cold Native30 session pin in RAM only.

Artifact qualification and a planned pipe are metadata. No DLL/body read,
binary copy, process/Native call, file write or loaded-provider claim occurs.
"""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json

MACHINE = 'xenoamess-full-tower-eb9d2c1186'
T = Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime')
O = Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/p51-fresh1066-v20261019-prepare01/c23-source23-native30-cold100/native30-transition-metadata')
TARGET = {'path': str(O/'NATIVE30-TARGET-PIN.json'), 'bytes': 3475, 'sha256': 'cfe8b1be0a5c3f9681880f3916f17a2404b011e249037b811a3698f3d421e75c'}
REFS = {'path': str(O/'NATIVE30-TRANSITION-REFS.json'), 'bytes': 8758, 'sha256': 'ca10fbe37ae9f823f2949646b686ea0e3895d644180a9195d47265089809b857'}
PREPARE = {'path': str(O/'PREPARE-RECEIPT.json'), 'bytes': 3224, 'sha256': 'd5fed48bb6acd876b5835a69ec45e4fae96969da1255948e5e8e53418ea9a7df'}
BASE = {'path': str(T/'ROOT-NATIVE29-NATIVE-PIN-C16.json'), 'bytes': 4546, 'sha256': '8ace8deb48058b1043374ee49b4be3249359f75123cf236907e43067bbfc1e5b'}
DLL_SHA = '39350bd933549ff11e7a79e1b1e0340664bf87ee129a2aa8cdb7b0e9be269f56'
LABEL = 'Native30 continuous hotspot tracking and idle realm overview'
EXPORTS = {'XarCk3BridgeIdentity': 2812832, 'XarCk3BridgePrepareStartup': 2814448,
           'XarCk3BridgeStart': 2831248, 'XarCk3BridgeStartWithPipe': 2831264,
           'XarCk3BridgeStop': 2831360}


def require(ok, message):
    if not ok:
        raise ValueError('C23 Native30 session metadata denied: '+message)


def checked(ref, limit=131072):
    require(isinstance(ref, dict) and type(ref.get('path')) is str
            and Path(ref['path']).is_absolute() and type(ref.get('bytes')) is int
            and 0 < ref['bytes'] <= limit, 'bounded absolute JSON reference required')
    with Path(ref['path']).open('rb') as stream:
        raw = stream.read(limit+1)
    require(len(raw) == ref['bytes'] and hashlib.sha256(raw).hexdigest() == ref.get('sha256'),
            'exact small input identity differs')
    value = json.loads(raw)
    require(isinstance(value, dict), 'small JSON object required')
    return value


def compose(*, capacity_ref, observed_at_utc):
    """Return immutable candidate bytes/report; caller separately admits/writes.

    The explicit observation is frozen with the candidate, so a later install
    need not recompute time-dependent JSON or silently change its reviewed SHA.
    """
    stamp = datetime.fromisoformat(observed_at_utc.replace('Z', '+00:00'))
    require(stamp.tzinfo is not None and stamp.utcoffset().total_seconds() == 0,
            'actual UTC observation required')
    require(-10 <= (datetime.now(timezone.utc)-stamp).total_seconds() <= 600,
            'metadata observation is not current')
    target, refs, prepared, base = map(checked, (TARGET, REFS, PREPARE, BASE))
    capacity = checked(capacity_ref)
    require(capacity.get('machine_id') == MACHINE and capacity.get('status') == 'ADMITTED'
            and isinstance(capacity.get('approved_output_roots'), list)
            and any(T.resolve().is_relative_to(Path(root).resolve())
                    for root in capacity['approved_output_roots']),
            'then-actual C23 runtime capacity must admit this target root')
    review = capacity.get('review_at_utc')
    require(type(review) is str, 'capacity review deadline must be explicit')
    try:
        deadline = datetime.fromisoformat(review.replace('Z', '+00:00'))
    except ValueError as error:
        raise ValueError('C23 Native30 session metadata denied: invalid capacity review deadline') from error
    require(deadline.tzinfo is not None and deadline.utcoffset() is not None
            and datetime.now(timezone.utc) < deadline,
            'capacity review deadline must have a timezone and remain unexpired')
    require(all(row.get('machine_id') == MACHINE for row in (target, refs, prepared, base)),
            'input machine differs')
    transition = refs['native_transition']
    require(target.get('schema') == 'xar.Native30-artifact-and-closed09-pin/v1'
            and target.get('status') == 'ARTIFACT_AND_CLOSED09_SUBFACTS_BOUND_NOT_LOADED'
            and target.get('qualification_kind') == 'artifact_plus_closed09_functional_only'
            and target.get('native_build_label') == LABEL
            and target.get('actual_runtime_loaded') is False and target.get('deployed') is False
            and refs.get('actual_runtime_loaded') is False and refs.get('deployed') is False,
            'only the actual closed09/artifact11 metadata is eligible')
    require(target.get('native_dll_sha256') == DLL_SHA and target.get('native_dll_bytes') == 19469312
            and Path(target['native_dll_path']).name == 'xar_ck3_bridge.dll'
            and target.get('export_rvas') == EXPORTS
            and target.get('delivery') == transition['artifact11_delivery']
            and target.get('source_freeze') == transition['source_freeze']
            and target.get('source_commit') == transition.get('source_commit')
            == '704bdd3362bdc282ed5f5f8cf31fd3f50b90d747',
            'DLL/code exports/delivery/source authority differs')
    data = target.get('data_exports') or {}
    require(set(data) == {'XarRefillCoreCarrier12004'}
            and data['XarRefillCoreCarrier12004'].get('callable') is False
            and data['XarRefillCoreCarrier12004'].get('rva') == 18062160,
            'sixth noncallable DATA fact must remain separate')
    require(base.get('status') == 'COMPILED_COLD_NATIVE_IDENTITY_PINNED_NO_RUNTIME'
            and type(base.get('pipe_name')) is str
            and base['pipe_name'].startswith('\\\\.\\pipe\\'),
            'original persistent campaign pipe source required')
    pin = dict(target)
    pin.update(schema='xar.C23-Native30-compiled-cold-session/v1',
               status='COMPILED_COLD_NATIVE_IDENTITY_PINNED_NO_RUNTIME',
               observed_at_utc=observed_at_utc,
               artifact_status_preserved=target['status'],
               artifact_target=TARGET, native_transition_references=REFS,
               metadata_prepare_receipt=PREPARE, base_native_pipe_source=BASE,
               storage_admission=capacity_ref,
               dll={'path': target['native_dll_path'], 'bytes': target['native_dll_bytes'],
                    'sha256': target['native_dll_sha256']},
               pipe_name=base['pipe_name'],
               pipe_name_kind='planned persistent campaign endpoint; no process or connection issued',
               new_DLL_copy_created=False, DLL_body_reads_by_this_producer=0,
               new_Game_identity_issued=False, Game_or_Native_calls=0,
               actual_loaded_provider_issued=False)
    raw = json.dumps(pin, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    require(len(raw) <= 16384, 'bounded session metadata exceeded')
    return raw, {'machine_id': MACHINE, 'target': str(T/'ROOT-NATIVE30-NATIVE-PIN-C23.json'),
                 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
                 'source_only': True, 'outputs_created': 0, 'DLL_reads': 0,
                 'actual_runtime_loaded': False}
