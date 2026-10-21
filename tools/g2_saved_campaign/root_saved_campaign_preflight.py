"""Outer queue helpers. No SDK, Native, desktop or process actions."""
from pathlib import Path
import copy
import hashlib
import json

PARAMETER_ERRORS = frozenset((
    "readonly research requires its exact typed public revision",
    "readonly Node research requires one bounded declaration ID",
    "exact current revision and explicit Army AB mode required",
    "collect requires the original bounded request ID and current revision",
))


def require(ok, message):
    if not ok:
        raise ValueError(message)


from datetime import datetime
from importlib import import_module
from typing import Callable, Literal, Mapping, Protocol, TypedDict, runtime_checkable


class SavedCampaignVisualArgsV1(Protocol):
    @property
    def first_frame_admission(self) -> Path: ...


class SavedCampaignVisualQueueV1(Protocol):
    @property
    def launch(self) -> Mapping[str, object]: ...
    @property
    def record_job(self) -> Path: ...
    @property
    def args(self) -> SavedCampaignVisualArgsV1: ...


class SavedCampaignJsonReaderV1(Protocol):
    def __call__(self, path: Path, limit: int = 1048576) -> object: ...


class SavedCampaignVisualEnvV1(TypedDict):
    N: Path
    R: Path
    read: SavedCampaignJsonReaderV1
    aware: Callable[[str], datetime]
    now: Callable[[], datetime]


class SavedCampaignVisualAdmissionV1(TypedDict):
    recording_session_id: str
    first_frame_admission: str
    camera_required: Literal[False]
    new_business_credit: Literal[0]


@runtime_checkable
class SavedCampaignSegmentVerifierV1(Protocol):
    def __call__(
        self, n: Path, r: Path, launch: Mapping[str, object], root: Path,
        first_path: Path, read: SavedCampaignJsonReaderV1,
        aware: Callable[[str], datetime], now: Callable[[], datetime],
    ) -> object: ...


def _visual_record_v1(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("saved campaign visual object required")
    result: dict[str, object] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("saved campaign visual text key required")
        result[key] = item
    return result


def _visual_uint_v1(value: object, maximum: int) -> int:
    if type(value) is not int or not 0 < value < maximum:
        raise ValueError("saved campaign visual exact positive integer required")
    return value


def _visual_text_v1(value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError("saved campaign visual nonempty text required")
    return value


def require_saved_campaign_visual(
    queue: SavedCampaignVisualQueueV1, env: SavedCampaignVisualEnvV1,
) -> SavedCampaignVisualAdmissionV1:
    """Validate the canonical text receipt after the exact C23 segment gate."""
    launch = _visual_record_v1(queue.launch)
    pid = _visual_uint_v1(launch.get("pid"), 2**32)
    birth = _visual_uint_v1(launch.get("creation_filetime"), 2**64)
    candidate: object = getattr(
        import_module("root_continuous_segment_auto_c23"), "verify_segment", None)
    if not callable(candidate) or not isinstance(candidate, SavedCampaignSegmentVerifierV1):
        raise ValueError("saved campaign C23 segment verifier required")
    segment = candidate(
        env["N"], env["R"], launch, queue.record_job,
        queue.args.first_frame_admission, env["read"], env["aware"], env["now"])
    if not isinstance(segment, tuple) or len(segment) != 3:
        raise ValueError("saved campaign segment must return its three records")
    job, first = _visual_record_v1(segment[0]), _visual_record_v1(segment[2])
    session_id = _visual_text_v1(job.get("session_id"))
    if (_visual_uint_v1(first.get("game_pid"), 2**32) != pid
            or _visual_uint_v1(first.get("game_creation_filetime"), 2**64) != birth
            or _visual_text_v1(first.get("recorder_session_id")) != session_id):
        raise ValueError("saved campaign visual Game/recording identity differs")
    reviewer = _visual_text_v1(first.get("reviewer"))
    if reviewer not in ("/root", "automatic_text_continuity"):
        raise ValueError("saved campaign canonical text reviewer required")
    if reviewer == "/root" and (
            first.get("schema") != "xar.ck3.decision-text-first-frame/v1"
            or first.get("stage") != "saved_map"
            or "decision_overlay_visible" in first
            or first.get("Game_map_visible") is not True
            or first.get("decision_text_visible") is not True
            or first.get("legacy_blue_window_visible") is not False):
        raise ValueError(
            "saved campaign needs actual reviewed Game map and decision text")
    return {"recording_session_id": session_id,
            "first_frame_admission": str(queue.args.first_frame_admission),
            "camera_required": False, "new_business_credit": 0}


def qualify_zero_rpc_preflight(queue, env, fresh_sequence):
    original, state = queue.halted, queue.full_loop_state
    require(isinstance(original, dict) and isinstance(state, dict),
            'retained rejection and settled state required')
    request = original.get('request') or {}
    sequence = request.get('sequence')
    cause = queue.halt_cause or {}
    require(type(sequence) is int and sequence > 0
            and original.get('row') is None and original.get('response') is None
            and cause.get('error_type') == 'ValueError',
            'only a retained ValueError before a response or dispatch is eligible')
    message = cause.get('message', '')
    readonly = request.get('tool') in env['READONLY_RESEARCH']
    full = request.get('command') == 'full_loop' and 'tool' not in request
    missing_camera = (message.startswith('missing or oversized named input: ')
                      and Path(message.split(': ', 1)[1]).name.startswith(
                          'ROOT-INITIAL-CAMERA-PIXELS-ADMITTED-')
                      and message.endswith('.json'))
    visual_error = message in {
        'saved campaign needs actual reviewed Game map and decision text',
        'Root must review actual visible map pixels after the native initial camera',
        'each full_loop batch max_turns must be 1..30',
    }
    require((readonly and message in PARAMETER_ERRORS)
            or (full and (missing_camera or visual_error)),
            'only reviewed readonly-argument or full-loop preflight failures are eligible')
    require(all(state.get(key) is None for key in (
        'pending_cycle', 'pending_checkpoint', 'terminal', 'pending_natural_succession',
        'pending_unsafe_route_halt')), 'unsettled work must retain its original recovery')
    require(not (env['Q'] / f'INFLIGHT-{sequence:04d}.json').exists()
            and not (env['Q'] / f'{sequence:04d}-before-action.json').exists(),
            'original dispatch evidence excludes zero-RPC recovery')
    require(type(fresh_sequence) is int and sequence < fresh_sequence < queue.next_sequence,
            'an already completed independent fresh SEM must follow the rejection')
    # A later business call would invalidate the no-action/same-frame argument.
    for marker in env['Q'].glob('INFLIGHT-*.json'):
        token = marker.stem.removeprefix('INFLIGHT-')
        if token.isdecimal() and sequence <= int(token) < queue.next_sequence:
            inflight = env['read'](marker, 16384)
            item = inflight.get('request', inflight)
            require(item.get('tool') in {env['SEMANTIC'], env['METRICS']},
                    'only independent readonly SEM/METRICS may follow the rejection')
    source = env['OUTBOX'] / f'{fresh_sequence:04d}-1-result.json'
    row = env['read'](source, env['REPLY_RESERVE'])
    fresh_request = row.get('request') or {}
    require(fresh_request.get('sequence') == fresh_sequence
            and fresh_request.get('tool') == env['SEMANTIC']
            and fresh_request.get('arguments') == {}
            and (row.get('result') or {}).get('is_error') is False
            and row.get('client_error') is None,
            'actual independent successful SEM is required')
    body = env['decoded'](row)
    actual = env['frame'](body, semantic=True,
                          expected_lifecycle=queue.expected_lifecycle_binding)
    before, diagnostics = state['before'], body.get('diagnostics') or {}
    require(all(actual[key] == before[key] for key in (
                'actor_character_id', 'episode_run_id', 'date_raw'))
            and actual['native_revision'] >= before['native_revision']
            and diagnostics.get('bridge_pid') == queue.launch['pid']
            and (diagnostics.get('hello') or {}).get('pid') == queue.launch['pid'],
            'fresh paused living same-Game actor/date/episode is required')
    if full:
        require(queue.initial_save is not None and queue.checkpoint_bootstrap_verified,
                'actual SAVE/restore bootstrap must remain verified')
        queue.require_camera_pixel_admission()
    return {'original_request': copy.deepcopy(request), 'original_error': copy.deepcopy(cause),
            'original_response': None, 'qualification': 'zero_rpc_preflight_rejection',
            'fresh_frame': actual, 'fresh_semantic_response': str(source),
            'fresh_semantic_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'completed_cycles': state['completed_cycles'], 'counts_unchanged': True,
            'new_MCP_or_native_calls': 0, 'original_request_replayed': False,
            'new_business_credit': 0}


async def recover_zero_rpc_preflight_original(queue, session, request, path, env):
    require(request.get('command') == 'clear_zero_rpc_preflight_rejection'
            and 'tool' not in request and set(request.get('arguments', {})) == {
                'fresh_semantic_sequence'}, 'exact local preflight recovery command required')
    receipt = qualify_zero_rpc_preflight(
        queue, env, request['arguments']['fresh_semantic_sequence'])
    receipt.update(status='zero_rpc_preflight_rejection_cleared',
                   control_sequence=request['sequence'], at_utc=env['now']().isoformat())
    require(len(json.dumps(receipt, ensure_ascii=False).encode('utf-8')) < 12000,
            'preflight recovery receipt exceeds its bounded allocation')
    sequence = queue.consume_sequence(request)
    env['atomic'](env['Q'] / f'ZERO-RPC-PREFLIGHT-RECOVERY-{sequence:04d}.json', receipt, limit=16384)
    queue.full_loop_state.update(before=copy.deepcopy(receipt['fresh_frame']),
                                before_metrics_response=receipt['fresh_semantic_response'])
    queue.persist_loop_state()
    env['atomic'](env['N'] / env['CURRENT_HALT_NAME'], receipt, replace=True, limit=16384)
    env['atomic'](env['OUTBOX'] / path.name,
                  {'request': request, 'result': {'is_error': False,
                   'structured_content': receipt}}, limit=16384)
    queue.halted = queue.current_attempt = queue.held_control = None
    queue.halt_cause = None
    return receipt


async def recover_before_c4_pointer200(queue, session, request, path, env):
    if request.get("arguments") == {"recovery_kind": "completed_metrics153_metadata154"}:
        source = Path(__file__).with_name("root_completed_metrics153_metadata_clear.py")
        payload = source.read_bytes()
        if len(payload) > 16384 or hashlib.sha256(payload).hexdigest() != 'a3e765a6fa4e63cb3c7d3494047f816fe4eb4e103febf4050b8b1afc7fc98d5b':
            raise ValueError("reviewed MET153 metadata recovery source differs")
        scope = {}
        exec(compile(payload, str(source), "exec"), scope)
        return await scope["recover_completed_metadata_v1"](queue, session, request, path, env)
    return await recover_zero_rpc_preflight_original(queue, session, request, path, env)


async def recover_before_estate255(queue, session, request, path, env):
    if request.get("arguments") == {"repair_kind": "saved61_cold_semantic_pointer198"}:
        source = Path(__file__).with_name("root_c4_cold_semantic_pointer_repair.py")
        payload = source.read_bytes()
        if len(payload) > 32768 or hashlib.sha256(payload).hexdigest() != 'ce892cbf7684fc34a9b0b4ffabf19ebec398967f93e3de8790a1a943619fb8dd':
            raise ValueError("reviewed C4 source-pointer repair differs")
        scope = {}
        exec(compile(payload, str(source), "exec"), scope)
        from root_p37_known_pause_recovery_control import process_birth_filetime
        return await scope["recover"](queue, session, request, path, env,
            retained={'p37-responses/0198-1-result.json': {'path': 'D:\\codex-ck3-demos\\2026-10-14-robert-30year\\continuation42-cold-prep\\p51-fresh1066-v20261019-prepare01\\c4-source-index-before-repair58\\05-0198-1-result.json', 'bytes': 48771, 'sha256': '900303320147c02c96f257de6caf75ae6f400523e5010b48b459babaa063a16f'}, 'p37-responses/0199-1-result.json': {'path': 'D:\\codex-ck3-demos\\2026-10-14-robert-30year\\continuation42-cold-prep\\p51-fresh1066-v20261019-prepare01\\c4-source-index-before-repair58\\06-0199-1-result.json', 'bytes': 57813, 'sha256': 'a0e4603f08ceb65d4fcbf03da71f0429f91e2777d63d0a2fae001b876fe27cc1'}, 'p37-queue/ROOT-CUMULATIVE-LOOP-STATE.json': {'path': 'D:\\codex-ck3-demos\\2026-10-14-robert-30year\\continuation42-cold-prep\\p51-fresh1066-v20261019-prepare01\\c4-source-index-before-repair58\\00-ROOT-CUMULATIVE-LOOP-STATE.json', 'bytes': 3892, 'sha256': 'c1b83e736d3774c4d4804c24cbea0a2dce54f8ab859afe6be6a72d3e9a3e797e'}, 'p37-queue/ROOT-GOVERNANCE-RESULT-STATE.json': {'path': 'D:\\codex-ck3-demos\\2026-10-14-robert-30year\\continuation42-cold-prep\\p51-fresh1066-v20261019-prepare01\\c4-source-index-before-repair58\\01-ROOT-GOVERNANCE-RESULT-STATE.json', 'bytes': 458, 'sha256': '34d671291162f5b4aba42708b8287e8a0f94048f25edf649580c06a5d4bfa7ba'}, 'p37-queue/ROOT-SAVED61-COLD-BOUND.json': {'path': 'D:\\codex-ck3-demos\\2026-10-14-robert-30year\\continuation42-cold-prep\\p51-fresh1066-v20261019-prepare01\\c4-source-index-before-repair58\\02-ROOT-SAVED61-COLD-BOUND.json', 'bytes': 1666, 'sha256': '53b4c0859ddb2eb76e065581bc172e9b30a87016449215059053a9b7adbd354b'}, 'NEXT-SEQUENCE-P37.json': {'path': 'D:\\codex-ck3-demos\\2026-10-14-robert-30year\\continuation42-cold-prep\\p51-fresh1066-v20261019-prepare01\\c4-source-index-before-repair58\\03-NEXT-SEQUENCE-P37.json', 'bytes': 65, 'sha256': 'ba817bf341637fd23118e1ae59fe45a5bd5f72b25f772765c9088ebff84217d2'}}, birth_reader=process_birth_filetime)
    return await recover_before_c4_pointer200(queue, session, request, path, env)


async def recover_before_faction515(queue,session,request,path,env):
    if request.get("arguments")=={"repair_kind":"estate255_before_dispatch_for_readonly_PLAN"}:
        source=Path(__file__).with_name("root_c5_estate255_predispatch_clear.py")
        payload=source.read_bytes()
        if len(payload)>32768 or hashlib.sha256(payload).hexdigest()!='f2f96175c74ba94408d823cf85878850472732be9208496ca7c132b2084d2a2f':
            raise ValueError("reviewed estate255 clear leaf differs")
        scope={}
        exec(compile(payload,str(source),"exec"),scope)
        from root_p37_known_pause_recovery_control import process_birth_filetime
        return await scope["recover"](queue,session,request,path,env,
            retained={'p37-queue/ROOT-CUMULATIVE-LOOP-STATE.json': {'path': 'D:\\codex-ck3-demos\\2026-10-14-robert-30year\\continuation42-cold-prep\\p51-fresh1066-v20261019-prepare01\\c5-estate255-failure66\\00-ROOT-CUMULATIVE-LOOP-STATE.json', 'bytes': 5072, 'sha256': '1d40e45069d6ba610006419b97f591a1f97ae1a1c258e12b4f00650dfccb7cc0'}, 'p37-queue/ROOT-GOVERNANCE-RESULT-STATE.json': {'path': 'D:\\codex-ck3-demos\\2026-10-14-robert-30year\\continuation42-cold-prep\\p51-fresh1066-v20261019-prepare01\\c5-estate255-failure66\\01-ROOT-GOVERNANCE-RESULT-STATE.json', 'bytes': 855, 'sha256': 'afaacd28c74b98f559bab592b8645656f775f7f52556e45c7c8eb2b6d271727a'}, 'ROOT-CURRENT-HALT-P37.json': {'path': 'D:\\codex-ck3-demos\\2026-10-14-robert-30year\\continuation42-cold-prep\\p51-fresh1066-v20261019-prepare01\\c5-estate255-failure66\\02-ROOT-CURRENT-HALT-P37.json', 'bytes': 708, 'sha256': '8fbedd0fe2d7863c4707dc1562a4451673a30aa3418268710be54783e5da5e1e'}, 'NEXT-SEQUENCE-P37.json': {'path': 'D:\\codex-ck3-demos\\2026-10-14-robert-30year\\continuation42-cold-prep\\p51-fresh1066-v20261019-prepare01\\c5-estate255-failure66\\03-NEXT-SEQUENCE-P37.json', 'bytes': 65, 'sha256': 'c9578ca84f974d13a36b76e9e7b1b05b7d9734e960b7079ef07dcd48670cc8aa'}, 'p37-responses/0252-1-result.json': {'path': 'D:\\codex-ck3-demos\\2026-10-14-robert-30year\\continuation42-cold-prep\\p51-fresh1066-v20261019-prepare01\\c5-estate255-failure66\\06-0252-1-result.json', 'bytes': 50837, 'sha256': '76c62d88abeda99e05f2937c8cdffdd54ab0e5bb3cbc7333f38aa181756c3155'}, 'p37-responses/0253-1-result.json': {'path': 'D:\\codex-ck3-demos\\2026-10-14-robert-30year\\continuation42-cold-prep\\p51-fresh1066-v20261019-prepare01\\c5-estate255-failure66\\07-0253-1-result.json', 'bytes': 57855, 'sha256': 'fa451ba86216bdc0943f3d27fa63093f40c19efd45274da2b860fb4e4c2dd68b'}, 'p37-responses/0255-1-result.json': {'path': 'D:\\codex-ck3-demos\\2026-10-14-robert-30year\\continuation42-cold-prep\\p51-fresh1066-v20261019-prepare01\\c5-estate255-failure66\\09-0255-1-result.json', 'bytes': 563, 'sha256': '2169d7152cc02bf3b59c39d72f8161fe5c5c5ac151b67bc66f6c537853b93d52'}, 'p37-queue/ROOT-PUBLISHER251-WARM-BOUND.json': {'path': 'D:\\codex-ck3-demos\\2026-10-14-robert-30year\\continuation42-cold-prep\\p51-fresh1066-v20261019-prepare01\\c5-estate255-failure66\\05-ROOT-PUBLISHER251-WARM-BOUND.json', 'bytes': 1171, 'sha256': 'adf312fa7af93b2bb523b615d9738610d791bca9cfa3ba5a88fa91d8318b800d'}},birth_reader=process_birth_filetime,source_contract={'path': 'D:\\codex-ck3-demos\\2026-10-14-robert-30year\\continuation42-cold-prep\\robert30-v20261019-campaign01\\c5-estate255-clear-review02\\SOURCE-CONTRACT.json', 'bytes': 2201, 'sha256': '2e116861cb695029275fd81aa9aaa27e3d01e44a1ddee1d739167b2a99939e07'})
    return await recover_before_estate255(queue,session,request,path,env)


async def recover_before_map520(queue,session,request,path,env):
    if request.get("arguments")=={"repair_kind":'faction515_presubmit_newer_paused_frame_for_readonly_PLAN'}:
        source=Path(__file__).with_name("root_c6_faction515_predispatch_clear.py")
        payload=source.read_bytes()
        if len(payload)>32768 or hashlib.sha256(payload).hexdigest()!='89713c56b7492f960ccc7908cbf06071150218f4493b3e048a03e3940da43079':
            raise ValueError("reviewed faction515 clear leaf differs")
        scope={}
        exec(compile(payload,str(source),"exec"),scope)
        from root_p37_known_pause_recovery_control import process_birth_filetime
        return await scope["recover"](queue,session,request,path,env,packet_ref={'path': 'D:\\codex-ck3-demos\\2026-10-14-robert-30year\\continuation42-cold-prep\\p51-fresh1066-v20261019-prepare01\\c6-faction515-failure73\\FROZEN.json', 'bytes': 5914, 'sha256': 'd69a3998558f8220d70061bd162339f0f2f8e1fe991fce86df52c73eeb76d182'},context_ref={'path': 'D:\\codex-ck3-demos\\2026-10-14-robert-30year\\continuation42-cold-prep\\p51-fresh1066-v20261019-prepare01\\c6-faction515-failure73\\context\\CONTEXT.json', 'bytes': 4973, 'sha256': 'f0ec60d1288d2d297e3358ed6316b5222acd96491ccc314d44461894bd6c1e6c'},
            source_contract={'path': 'D:\\codex-ck3-demos\\2026-10-14-robert-30year\\continuation42-cold-prep\\robert30-v20261019-campaign01\\c6-faction515-clear-review01\\SOURCE-CONTRACT.json', 'bytes': 2723, 'sha256': 'a7b8ef43a4f3f4f016df6058dbb10c8f806badb2e1987c714a332cff49aa199f'},birth_reader=process_birth_filetime)
    return await recover_before_faction515(queue,session,request,path,env)


async def recover_zero_rpc_preflight(queue,session,request,path,env):
    if request.get("arguments")=={"repair_kind":'map520_local_preflight_after_Root_primary_review'}:
        source=Path(__file__).with_name("root_c7_map520_preflight_clear.py")
        payload=source.read_bytes()
        if len(payload)>32768 or hashlib.sha256(payload).hexdigest()!='011e1d41a2719090f16b3d0da8dbbcefa382a6d18c0c865ae1c7cd9c248ac45c':
            raise ValueError("reviewed map520 local preflight leaf differs")
        scope={}
        exec(compile(payload,str(source),"exec"),scope)
        from root_p37_known_pause_recovery_control import process_birth_filetime
        return await scope["recover"](queue,session,request,path,env,packet_ref={'path': 'D:\\codex-ck3-demos\\2026-10-14-robert-30year\\continuation42-cold-prep\\p51-fresh1066-v20261019-prepare01\\c7-map520-rejection75\\FROZEN.json', 'bytes': 5639, 'sha256': 'ba5c98d373ef20dc14358ebcebe895f142ca28b3ad31c3a17febd5d2a739c3b6'},corrected_map_ref={'path': 'D:\\codex-ck3-demos\\2026-10-14-robert-30year\\continuation42-cold-prep\\robert30-v20261019-campaign01\\runtime\\ROOT-CAMPAIGN-MAP-ADMITTED-C7.json', 'bytes': 3462, 'sha256': '7c00ba6454f7997a564bd1b2d0ba6e45a2e7a4eda1ed51994f17b16367f10678'},
            root_review_ref={'path': 'Z:\\ck3_mod_rewrite\\docs\\ck3-native-ai\\evidence\\c7-current381-root-pixel-review-2026-10-19.json', 'bytes': 2352, 'sha256': '17e3cb081b1065102127513c3a650464d66227b7e64cfa537642f956d2f185b6'},birth_reader=process_birth_filetime)
    return await recover_before_map520(queue,session,request,path,env)


recover_before_checkpoint4226 = recover_zero_rpc_preflight
async def recover_zero_rpc_preflight(queue,session,request,path,env):
    if request.get("arguments")=={"repair_kind":'checkpoint4226_source_bound_before_native_save'}:
        source=Path(__file__).with_name("root_c10_checkpoint4226_clear.py")
        payload=source.read_bytes()
        if len(payload)!=7170 or hashlib.sha256(payload).hexdigest()!='9e2c197159a34965e77c70eb9a5e3b0711106ce13c8dccd9716c106871055a7a':
            raise ValueError("reviewed SAVE4226 finite helper differs")
        scope={}
        exec(compile(payload,str(source),"exec"),scope)
        return await scope["recover"](queue,session,request,path,env)
    return await recover_before_checkpoint4226(queue,session,request,path,env)

recover_before4230 = recover_zero_rpc_preflight
async def recover_zero_rpc_preflight(queue,session,request,path,env):
    if request.get("arguments")=={"repair_kind":'direct_SAVE4230_before_driver_identity_guard'}:
        source=Path(__file__).with_name("root_c10b_save4230_clear.py")
        payload=source.read_bytes()
        if len(payload)!=5097 or hashlib.sha256(payload).hexdigest()!='8ed8cc3a0c7a7143ffd7223d2271f796873da50419eb990253636fd4d2abdcab':
            raise ValueError("reviewed directSAVE4230 helper differs")
        scope={}
        exec(compile(payload,str(source),"exec"),scope)
        return await scope["recover"](queue,session,request,path,env)
    return await recover_before4230(queue,session,request,path,env)

recover_before_clock10476 = recover_zero_rpc_preflight
async def recover_zero_rpc_preflight(queue,session,request,path,env):
    if request.get('arguments') == {'repair_kind': 'c20_clock10476_status_semantic_save_maintenance'}:
        source=Path(__file__).with_name('root_c20_clock10476_maintenance.py')
        payload=source.read_bytes()
        if len(payload)>24576 or hashlib.sha256(payload).hexdigest()!='febb6cc2007057e678a05ebe5380fa369ee240953e55c71e31f54df5e277da55':
            raise ValueError('reviewed F98 maintenance source differs')
        scope={'__file__':str(source)}
        exec(compile(payload,str(source),'exec'),scope)
        return await scope['recover'](queue,session,request,path,env)
    return await recover_before_clock10476(queue,session,request,path,env)


import re


class SavedMapFileRefV1(TypedDict):
    path: str
    bytes: int
    sha256: str


class SavedMapFrameV1(TypedDict):
    label: str
    at_utc: str
    game: SavedMapFileRefV1
    scene: SavedMapFileRefV1
    mutable_latest_frame: Literal[False]


class SavedMapFirstFrameV1(TypedDict):
    schema: Literal["xar.ck3.decision-text-first-frame/v1"]
    machine_id: str
    status: Literal["GREEN"]
    stage: Literal["saved_map"]
    reviewer: Literal["/root"]
    at_utc: str
    reviewed_at_utc: str
    game_pid: int
    game_creation_filetime: int
    game_creation_date: str
    recorder_session_id: str
    recording_job_root: str
    publisher_started: SavedMapFileRefV1
    frame: SavedMapFrameV1
    before_selection_game_pixels_reviewed: Literal[True]
    before_selection_decision_pixels_reviewed: Literal[True]
    decision_text_visible: Literal[True]
    legacy_blue_window_visible: Literal[False]
    Game_map_visible: Literal[True]
    film_title_visible: Literal[False]
    observed_map_date: str
    observed_pause_banner: bool
    native_source_dimensions: list[int]
    native_capture_scale: list[int]
    rich_actual_plan_visible: bool
    initial_waiting_text_is_not_planner_output: Literal[True]


def _visual_bool_v1(value: object) -> bool:
    if type(value) is not bool:
        raise ValueError("saved map exact boolean required")
    return value


def _visual_true_v1(value: object) -> Literal[True]:
    if value is not True:
        raise ValueError("saved map explicit reviewed true required")
    return True


def _visual_false_v1(value: object) -> Literal[False]:
    if value is not False:
        raise ValueError("saved map explicit reviewed false required")
    return False


def _visual_at_v1(value: object) -> str:
    text = _visual_text_v1(value)
    actual = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if actual.tzinfo is None or actual.utcoffset() is None:
        raise ValueError("saved map aware timestamp required")
    return text


def _visual_abs_v1(value: object) -> str:
    text = _visual_text_v1(value)
    if "\x00" in text or not Path(text).is_absolute() or ".." in Path(text).parts:
        raise ValueError("saved map absolute JSON path required")
    return text


def _visual_pair_v1(value: object) -> list[int]:
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError("saved map two integer JSON dimensions required")
    return [_visual_uint_v1(item, 2**32) for item in value]


def _visual_ref_v1(value: object, maximum: int) -> SavedMapFileRefV1:
    row = _visual_record_v1(value)
    if set(row) != {"path", "bytes", "sha256"}:
        raise ValueError("saved map exact file reference fields required")
    digest = _visual_text_v1(row["sha256"])
    if re.fullmatch("[0-9a-f]{64}", digest) is None:
        raise ValueError("saved map canonical SHA256 required")
    return {"path": _visual_abs_v1(row["path"]),
            "bytes": _visual_uint_v1(row["bytes"], maximum + 1), "sha256": digest}


def build_saved_map_first_frame_v1(
    reviewed: object, *, expected_machine_id: str,
) -> SavedMapFirstFrameV1:
    """Encode explicit Root review values, not evidence verification.

    FILETIME keeps the legacy Python recorder integer ABI; never round-trip
    this 64-bit value through JavaScript Number.
    """
    row = _visual_record_v1(reviewed)
    if set(row) != SavedMapFirstFrameV1.__required_keys__:
        raise ValueError("saved map exact first-frame fields required")
    machine = _visual_text_v1(row["machine_id"])
    if machine != _visual_text_v1(expected_machine_id):
        raise ValueError("saved map review machine differs")
    for key, literal in (("schema", "xar.ck3.decision-text-first-frame/v1"),
                         ("status", "GREEN"), ("stage", "saved_map"),
                         ("reviewer", "/root")):
        if type(row[key]) is not str or row[key] != literal:
            raise ValueError("saved map canonical " + key + " required")
    at = _visual_at_v1(row["at_utc"])
    reviewed_at = _visual_at_v1(row["reviewed_at_utc"])
    if datetime.fromisoformat(reviewed_at.replace("Z", "+00:00")) < datetime.fromisoformat(at.replace("Z", "+00:00")):
        raise ValueError("saved map review predates its captured frame")
    root = _visual_abs_v1(row["recording_job_root"])
    source = _visual_record_v1(row["frame"])
    if set(source) != SavedMapFrameV1.__required_keys__:
        raise ValueError("saved map exact frame fields required")
    frame: SavedMapFrameV1 = {
        "label": _visual_text_v1(source["label"]),
        "at_utc": _visual_at_v1(source["at_utc"]),
        "game": _visual_ref_v1(source["game"], 8 * 1024**2),
        "scene": _visual_ref_v1(source["scene"], 8 * 1024**2),
        "mutable_latest_frame": _visual_false_v1(source["mutable_latest_frame"])}
    if (datetime.fromisoformat(frame["at_utc"].replace("Z", "+00:00")) != datetime.fromisoformat(at.replace("Z", "+00:00"))
            or not Path(frame["game"]["path"]).is_relative_to(Path(root))
            or not Path(frame["scene"]["path"]).is_relative_to(Path(root))):
        raise ValueError("saved map exact frame time/recording root differs")
    return {
        "schema": "xar.ck3.decision-text-first-frame/v1", "machine_id": machine,
        "status": "GREEN", "stage": "saved_map", "reviewer": "/root",
        "at_utc": at, "reviewed_at_utc": reviewed_at,
        "game_pid": _visual_uint_v1(row["game_pid"], 2**32),
        "game_creation_filetime": _visual_uint_v1(row["game_creation_filetime"], 2**64),
        "game_creation_date": _visual_text_v1(row["game_creation_date"]),
        "recorder_session_id": _visual_text_v1(row["recorder_session_id"]),
        "recording_job_root": root,
        "publisher_started": _visual_ref_v1(row["publisher_started"], 1024**2),
        "frame": frame,
        "before_selection_game_pixels_reviewed": _visual_true_v1(row["before_selection_game_pixels_reviewed"]),
        "before_selection_decision_pixels_reviewed": _visual_true_v1(row["before_selection_decision_pixels_reviewed"]),
        "decision_text_visible": _visual_true_v1(row["decision_text_visible"]),
        "legacy_blue_window_visible": _visual_false_v1(row["legacy_blue_window_visible"]),
        "Game_map_visible": _visual_true_v1(row["Game_map_visible"]),
        "film_title_visible": _visual_false_v1(row["film_title_visible"]),
        "observed_map_date": _visual_text_v1(row["observed_map_date"]),
        "observed_pause_banner": _visual_bool_v1(row["observed_pause_banner"]),
        "native_source_dimensions": _visual_pair_v1(row["native_source_dimensions"]),
        "native_capture_scale": _visual_pair_v1(row["native_capture_scale"]),
        "rich_actual_plan_visible": _visual_bool_v1(row["rich_actual_plan_visible"]),
        "initial_waiting_text_is_not_planner_output": _visual_true_v1(row["initial_waiting_text_is_not_planner_output"])}
