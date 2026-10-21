"""Ordinary Save materialization and native bracketing, without episode claims.

No SDK, file hashing or state mutation occurs here. File facts come from the
existing native Save producer. The independently requested snapshots supply
native owner evidence; host managed-run metadata supplies consistency only.
"""
from __future__ import annotations
from collections.abc import Callable, Mapping
from dataclasses import dataclass
import math
from pathlib import Path
import re
from typing import Literal, TypeAlias, TypedDict

JsonValue: TypeAlias = None|bool|int|float|str|list['JsonValue']|dict[str,'JsonValue']
JsonObject: TypeAlias = dict[str,JsonValue]
Call: TypeAlias = Callable[[str,str,dict[str,object]],Mapping[str,object]]
Snapshot: TypeAlias = Callable[[str],Mapping[str,object]]
Payment: TypeAlias = Callable[[str,str],Mapping[str,object]]
NullableRepresentation: TypeAlias = Literal['missing','explicit_null']
SCOPE='producer_materialization_and_native_bracketing'
MAX_SAFE_JSON_INTEGER=(1<<53)-1

class SaveUnconfirmed(ValueError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail);self.code=code;self.detail=detail

def obj(value: object, label: str) -> Mapping[str,object]:
    if not isinstance(value,dict) or not all(isinstance(k,str) for k in value):
        raise SaveUnconfirmed('missing_or_malformed',label+' object unavailable')
    return value

def text(value: object, label: str) -> str:
    if not isinstance(value,str) or not value:raise SaveUnconfirmed('missing_or_malformed',label+' string unavailable')
    return value

def integer(value: object, label: str, *, maximum: int=MAX_SAFE_JSON_INTEGER) -> int:
    if type(value) is not int or not isinstance(value,int) or not 0<value<=maximum:
        raise SaveUnconfirmed('missing_or_malformed',label+' positive integer unavailable')
    return value

def require(ok: bool, code: str, detail: str) -> None:
    if not ok:raise SaveUnconfirmed(code,detail)

def nullable_representation(row: Mapping[str,object], key: str) -> NullableRepresentation:
    if key not in row:return 'missing'
    require(row[key] is None,'projection','Ordinary snapshot has non-null '+key)
    return 'explicit_null'

class EpisodeRepresentation(TypedDict):
    episode_run_id: NullableRepresentation
    episode_character_id: NullableRepresentation

@dataclass(frozen=True,slots=True)
class ManagedRun:
    run_id: str
    state_dir: str
    bridge_pipe: str
    host_path: str
    frozen_argv_sha256: str

@dataclass(frozen=True,slots=True)
class NativeOwner:
    actor: int
    local_player: int
    pid: int
    generation: int
    pipe: str
    date_raw: int
    revision: int
    native_revision: int
    snapshot_id: str
    run: ManagedRun
    episode_run_id_representation: NullableRepresentation
    episode_character_id_representation: NullableRepresentation

@dataclass(frozen=True,slots=True)
class RetainedClient:
    client: object
    handle: object
    pid: int

@dataclass(frozen=True,slots=True)
class SaveStart:
    owner: NativeOwner
    retained: RetainedClient

class FileFact(TypedDict):
    path: str
    bytes: int
    sha256: str
    date_raw: int

class SaveProof(TypedDict):
    status: Literal['verified']
    scope: str
    file: FileFact
    actor: int
    local_player: int
    bridge_pid: int
    connection_generation: int
    pipe: str
    managed_run_id: str
    before_episode_identity_representation: EpisodeRepresentation
    after_episode_identity_representation: EpisodeRepresentation
    before_snapshot_id: str
    after_snapshot_id: str
    before_revision: int
    after_revision: int
    before_native_revision: int
    after_native_revision: int
    native_frame_advanced: bool
    independent_after_request: bool
    same_retained_case_client: bool
    consumer_rehashed_file: bool
    one_life_identity_proven: bool
    limitations: list[str]

def native_owner(value: object) -> NativeOwner:
    row=obj(value,'snapshot');played=obj(row.get('played_character'),'played_character');diag=obj(row.get('diagnostics'),'diagnostics')
    run_representation=nullable_representation(row,'episode_run_id')
    character_representation=nullable_representation(row,'episode_character_id')
    require(row.get('episode_projection')=='native_campaign','projection','Ordinary Save cannot acquire oneLife identity')
    require(row.get('backend_id')=='native-headless' and row.get('source')=='injected-dll-named-pipe'
        and row.get('map_ready') is True and row.get('paused') is True
        and played.get('alive') is True and played.get('source')=='native'
        and diag.get('connected') is True,'native_owner_unavailable','Current paused native player/transport unavailable')
    run=obj(row.get('managed_campaign_run_binding'),'managed_campaign_run_binding')
    digest=text(run.get('frozen_argv_sha256'),'frozen_argv_sha256')
    require(re.fullmatch('[0-9a-f]{64}',digest) is not None,'run_binding','Allocated frozen SHA malformed')
    binding=ManagedRun(text(run.get('run_id'),'managed.run_id'),text(run.get('state_dir'),'managed.state_dir'),
        text(run.get('bridge_pipe'),'managed.bridge_pipe'),text(run.get('host_path'),'managed.host_path'),digest)
    pipe=text(diag.get('pipe_name'),'diagnostics.pipe_name')
    require(pipe==binding.bridge_pipe,'run_binding','Native transport crossed allocated pipe')
    return NativeOwner(integer(played.get('character_id'),'character_id',maximum=(1<<32)-1),
        integer(row.get('local_player_id'),'local_player_id',maximum=(1<<32)-1),
        integer(diag.get('bridge_pid'),'bridge_pid',maximum=(1<<32)-1),
        integer(diag.get('connection_generation'),'connection_generation'),pipe,
        integer(row.get('date_raw'),'date_raw'),integer(row.get('revision'),'revision'),
        integer(row.get('native_revision'),'native_revision'),text(row.get('snapshot_id'),'snapshot_id'),binding,
        run_representation,character_representation)

def retained_client(client: object) -> RetainedClient:
    handle=getattr(client,'_handle',None);process=obj(getattr(client,'_process',None),'retained CaseClient process')
    require(handle is not None,'retained_client','Original retained CaseClient handle unavailable')
    return RetainedClient(client,handle,integer(process.get('pid'),'retained pid',maximum=(1<<32)-1))

def begin_save(before: object, retained: RetainedClient) -> SaveStart:
    owner=native_owner(before)
    require(owner.pid==retained.pid,'retained_client','Retained OS/native PID differs')
    return SaveStart(owner,retained)

def verify_save(start: SaveStart, result: object, after: object, retained: RetainedClient) -> SaveProof:
    old=start.owner;new=native_owner(after)
    require(start.retained.client is retained.client and start.retained.handle is retained.handle
        and retained.pid==start.retained.pid==new.pid,'retained_client','Original CaseClient/retained handle changed')
    require((new.actor,new.local_player,new.pid,new.generation,new.pipe,new.date_raw,new.run)==
        (old.actor,old.local_player,old.pid,old.generation,old.pipe,old.date_raw,old.run),
        'owner_drift','Independent native actor/run/PID/generation/pipe/date differs')
    require(new.revision>=old.revision and new.native_revision>=old.native_revision,
        'snapshot_drift','Independent snapshot sequence regressed')
    require((new.native_revision==old.native_revision)==(new.snapshot_id==old.snapshot_id),
        'snapshot_drift','Native snapshot identity/sequence domain inconsistent')
    saved=obj(result,'Save result');ck=obj(saved.get('checkpoint'),'checkpoint');mat=obj(saved.get('materialization'),'materialization');submission=obj(saved.get('submission'),'submission')
    require(saved.get('step')=='save-checkpoint' and saved.get('accepted') is True
        and saved.get('backend_id')=='native-headless' and ck.get('status')=='saved'
        and mat.get('available') is True,'materialization','Actual native Save materialization unavailable')
    require({'succession_lifecycle','episode_run_id','episode_character_id'} <= ck.keys(),'projection_fields_missing',
        'Checkpoint nullable lifecycle/episode fields must be explicit')
    require(ck.get('episode_projection')=='native_campaign' and ck.get('succession_lifecycle') is None
        and ck.get('episode_character_id') is None and ck.get('episode_run_id') is None,
        'projection','Save result must retain absent oneLife identities')
    require(ck.get('strategy')=='native-autosave-command-v1','materialization','Unknown Save producer strategy')
    date=integer(ck.get('date_raw'),'checkpoint.date_raw');submitted=integer(submission.get('date_raw'),'submission.date_raw')
    integer(submission.get('sequence'),'submission.sequence')
    # Legacy producer mtime_ns is not an owner or new proof field; retain it only in the untouched response.
    require(date==submitted==old.date_raw,'save_date','Saved/submitted/native dates differ')
    path=Path(text(ck.get('path'),'checkpoint.path'));directory=Path(text(mat.get('save_dir'),'materialization.save_dir'));name=text(ck.get('name'),'checkpoint.name')
    require(path.is_absolute() and directory.is_absolute() and name=='xar_checkpoint.ck3'
        and path.resolve()==(directory/name).resolve()
        and directory.resolve()==(Path(old.run.state_dir)/'profile'/'save games').resolve(),
        'save_path','Materialized Save crossed this managed profile')
    size=integer(ck.get('size'),'checkpoint.size');digest=text(ck.get('sha256'),'checkpoint.sha256')
    require(re.fullmatch('[0-9a-f]{64}',digest) is not None,'materialization','Save producer SHA256 malformed')
    return SaveProof(status='verified',scope=SCOPE,file=FileFact(path=str(path),bytes=size,sha256=digest,date_raw=date),
        actor=old.actor,local_player=old.local_player,bridge_pid=old.pid,connection_generation=old.generation,
        pipe=old.pipe,managed_run_id=old.run.run_id,
        before_episode_identity_representation=EpisodeRepresentation(episode_run_id=old.episode_run_id_representation,
            episode_character_id=old.episode_character_id_representation),
        after_episode_identity_representation=EpisodeRepresentation(episode_run_id=new.episode_run_id_representation,
            episode_character_id=new.episode_character_id_representation),before_snapshot_id=old.snapshot_id,after_snapshot_id=new.snapshot_id,
        before_revision=old.revision,after_revision=new.revision,before_native_revision=old.native_revision,
        after_native_revision=new.native_revision,native_frame_advanced=new.native_revision>old.native_revision,
        independent_after_request=True,same_retained_case_client=True,consumer_rehashed_file=False,
        one_life_identity_proven=False,limitations=['File size/SHA are from the existing native Save producer, not a second consumer hash',
          'Static managed-run metadata proves consistency, not native freshness',
          'Save result has no atomic actor/generation frame; file-internal actor and native FILETIME are not proven',
          'Equal native sequence means an independent snapshot request returned the same native sample; no new frame is claimed'])

def unconfirmed(error: BaseException) -> JsonObject:
    return {'status':'unconfirmed','scope':SCOPE,'reason_code':error.code if isinstance(error,SaveUnconfirmed) else type(error).__name__,
            'detail':str(error),'one_life_identity_proven':False}

def finite_json(value: object) -> JsonValue:
    if value is None or isinstance(value,(str,bool,int)):return value
    if isinstance(value,float) and math.isfinite(value):return value
    if isinstance(value,list):return [finite_json(x) for x in value]
    if isinstance(value,dict):return {text(k,'JSON key'):finite_json(v) for k,v in value.items()}
    raise SaveUnconfirmed('malformed_cleanup','Cleanup result is not finite JSON')

def cleanup_result(value: object) -> tuple[JsonObject,list[str],int|None]:
    require(isinstance(value,tuple) and len(value)==3,'malformed_cleanup','Cleanup tuple required')
    if not isinstance(value,tuple):raise SaveUnconfirmed('malformed_cleanup','Cleanup tuple required')
    result,errors,days=value
    parsed=finite_json(result)
    if not isinstance(parsed,dict) or not isinstance(errors,list) or not all(isinstance(e,str) for e in errors):
        raise SaveUnconfirmed('malformed_cleanup','Cleanup fields malformed')
    if days is not None and (type(days) is not int or not isinstance(days,int) or days<0):raise SaveUnconfirmed('malformed_cleanup','Cleanup actual_days malformed')
    strings=[text(e,'cleanup error') for e in errors]
    return parsed,strings,days
