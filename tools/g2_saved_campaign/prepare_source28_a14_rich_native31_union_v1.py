"""A14 Source28/Native31 source preparation only; no Game, Task or runtime writer.
Accepted A13 inventories remain the intake. A13 closure, fresh Driver review,
current NEXT, full quota, Steam proof, new nonces and Root runtime release must
be bound separately before any new cold factory can be admitted.
"""
from __future__ import annotations
import ast
from collections import Counter
from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
from typing import Literal, TypedDict
import prepare_rich_decision_graph_v1 as rich_api
from file_stat_identity_v1 import (
    SCHEMA, StatIdentitySchema, normalize_file_stat_identity_v1,
    parse_file_stat_identity_v1,
)

MACHINE_ID='xenoamess-full-tower-eb9d2c1186'
ACCEPTED_ROOT=Path('D:\\codex-ck3-demos\\2026-10-14-robert-30year\\continuation42-cold-prep\\robert30-v20261019-campaign01\\runtime-a13')
ACCEPTED_PREPARED: ExactRef={'path': 'D:\\codex-ck3-demos\\2026-10-14-robert-30year\\continuation42-cold-prep\\p51-fresh1066-v20261019-prepare01\\c23-source23-native30-cold100\\A13-PREPARED01.json', 'bytes': 38283, 'sha256': '9e0befe5c9a359a17f50c56eb2d3063a49f7c55a1d8725080aa68a59188a9ad8'}
ACCEPTED_QUOTE: ExactRef={'path': 'D:\\codex-ck3-demos\\2026-10-14-robert-30year\\continuation42-cold-prep\\p51-fresh1066-v20261019-prepare01\\c23-source23-native30-cold100\\source28-a13-prep01\\A13-ROOT-QUOTE02.json', 'bytes': 148151, 'sha256': '3f3315044e0eef8a9cc57cc78aac12e105f8d614c4cd84dc5be9ac699e730caf'}
OPS14_NAMES=('ROOT-FINAL-SDK-FREEZE-P37C23-A12.json', 'ROOT-NATIVE30-NATIVE-PIN-C23-A12.json', 'ROOT-LAUNCH-CONFIG-C23-A12.json', 'ROOT-CLEAN-SOURCE-FROZEN-C23-A12.json', 'ROOT-NATIVE30-SDK-BINDING-C23-A12.json')
OPS14_PINS={'launch_sdk_p37c23_owner.py': (6011, '8ed8d13b1fa8c1dae5583545f4733319f1b125bb8ce926a17ac535131b70599a'), 'root_c23_canonical_outer.py': (18780, '69fa5a5ae134f4264b849a0b34825ddee5fea366c4d8d8cd57f7747fa8f46438'), 'root_native_build_binding_p37c23.py': (4118, '01614f487b4c9dda6cd20857d30abf3b267563f3eb0d17ee338dda4821b86cf3'), 'root_p37c23_mcp_entry.py': (12908, '07946a54a9295066185951a64222c68acd30a1393baecfc2a8e97b1f128c1d50'), 'root_p37c23_same_game_loop_feeder100.py': (41720, '4ca46864ee6f4ee3651cc8d603098e255a1952d617a5798dcc7b00367eb827ae'), 'root_p37c23_sdk_queue.py': (269348, '3b9a8801b6e5db1618e39b6548219b7ed04aa5ae425022a88d4d2daf162cbc7f')}
OPS14_COUNTS={'launch_sdk_p37c23_owner.py': {'ROOT-FINAL-SDK-FREEZE-P37C23-A12.json': 3}, 'root_c23_canonical_outer.py': {'ROOT-FINAL-SDK-FREEZE-P37C23-A12.json': 1}, 'root_native_build_binding_p37c23.py': {'ROOT-FINAL-SDK-FREEZE-P37C23-A12.json': 1, 'ROOT-NATIVE30-NATIVE-PIN-C23-A12.json': 1, 'ROOT-LAUNCH-CONFIG-C23-A12.json': 1, 'ROOT-CLEAN-SOURCE-FROZEN-C23-A12.json': 1, 'ROOT-NATIVE30-SDK-BINDING-C23-A12.json': 1}, 'root_p37c23_mcp_entry.py': {'ROOT-FINAL-SDK-FREEZE-P37C23-A12.json': 3}, 'root_p37c23_same_game_loop_feeder100.py': {'ROOT-FINAL-SDK-FREEZE-P37C23-A12.json': 1}, 'root_p37c23_sdk_queue.py': {'ROOT-FINAL-SDK-FREEZE-P37C23-A12.json': 8, 'ROOT-CLEAN-SOURCE-FROZEN-C23-A12.json': 1}}
NATIVE31_SIDECARS=('observer_journal_v1.py', 'native31_mcp_extension_v1.py')
REG31='    from typing import Callable\n\n    Native31ReadonlyCallbackV1 = Callable[[], dict[str, object]]\n    Native31ReadonlyRegisterV1 = Callable[[Native31ReadonlyCallbackV1], object]\n    Native31ExistingEnsureV1 = Callable[[object], object]\n\n    def native31_loaded_readonly_registration_v1(\n            register: Native31ReadonlyRegisterV1,\n            ensure: Native31ExistingEnsureV1, *,\n            owner: object) -> Native31ReadonlyRegisterV1:\n        """Registration is inert. Only an explicit read enters the existing gate.\n        None from the legacy gate is not issuance proof: the original callback\n        still validates the actual cached DTO, seal, owner, DLL and Game identity.\n        """\n        def decorate(callback: Native31ReadonlyCallbackV1) -> object:\n            def ck3_observe_native31_time_command_journal_v1() -> dict[str, object]:\n                from xar_autoplayer.bridge.native_loaded_provider_custody_v1 import (\n                    CustodyIssueResultV1, _PreloadCustodyV1, _RESOURCE_SEAL)\n                from xar_autoplayer.bridge.native_loaded_provider_origin_v1 import _OriginSessionV1\n                outcome = ensure(owner)\n                if outcome is not None:\n                    if (not isinstance(outcome, CustodyIssueResultV1)\n                            or type(outcome.issued) is not bool or outcome.issued is not True):\n                        raise ValueError("existing loaded Native custody issuer unavailable")\n                holder: object = getattr(owner, "_player_heir_loaded_custody_v1", None)\n                if (not isinstance(holder, _PreloadCustodyV1)\n                        or getattr(holder, "seal", None) is not _RESOURCE_SEAL\n                        or getattr(holder, "closed", None) is not False\n                        or getattr(holder, "owner", None) is not owner):\n                    raise ValueError("same open loaded Native custody holder required")\n                session: object = getattr(holder, "_origin_session_v1", None)\n                if (type(session) is not _OriginSessionV1\n                        or getattr(session, "holder", None) is not holder):\n                    raise ValueError("same existing loaded Native origin session required")\n                owner_epoch: object = getattr(owner, "epoch", None)\n                session_epoch: object = getattr(session, "epoch", None)\n                if (type(owner_epoch) is not str or not owner_epoch\n                        or type(session_epoch) is not str or owner_epoch != session_epoch):\n                    raise ValueError("same existing loaded Native origin epoch required")\n                return callback()\n            return register(ck3_observe_native31_time_command_journal_v1)\n        return decorate\n    # Native31: two exact cold sidecars, original canonical owner, no eager query.\n    import hashlib as _n31_hashlib\n    for _n31_name, _n31_sha in (\n        (\'observer_journal_v1.py\',\'f77710b050f839da36c308a1da66a8aec79fa0ec8bec167100f62c688a029712\'),\n        (\'native31_mcp_extension_v1.py\',\'9c56a270f8029360de26560ded0cb3f7938749684f65921b9245f30ee49004a0\')):\n        if _n31_hashlib.sha256((N/_n31_name).read_bytes()).hexdigest()!=_n31_sha:\n            raise RuntimeError(\'Native31 cold sidecar source differs: \'+_n31_name)\n    import native31_mcp_extension_v1 as _n31_extension\n    import observer_journal_v1 as _n31_reader\n    if (Path(_n31_extension.__file__).resolve()!=N/\'native31_mcp_extension_v1.py\'\n            or Path(_n31_reader.__file__).resolve()!=N/\'observer_journal_v1.py\'):\n        raise RuntimeError(\'Native31 sidecars imported from another source\')\n    _n31_owner=getattr(driver,\'_player_heir_candidate_owner_v1\',None)\n    if _canonical is None or _n31_owner is None:\n        raise RuntimeError(\'Native31 requires the original canonical App owner\')\n    from xar_autoplayer.bridge.native_loaded_provider_origin_v1 import ensure_received_provider_v1\n    from mcp.types import ToolAnnotations as _N31ToolAnnotations\n    _n31_extension.register_native31_journal_v1(\n        native31_loaded_readonly_registration_v1(\n            server.tool(annotations=_N31ToolAnnotations(readOnlyHint=True,\n                destructiveHint=False,idempotentHint=True,openWorldHint=False)),\n            ensure_received_provider_v1,owner=_n31_owner),\n        owner=_n31_owner,driver=driver,machine_id=_n31_owner.machine)\n'
RUN_LOOP_PIN=(7299, '55a9b9f96beacd797ee6b3ffb6ba461a9285b4c4bfb5f0c818670e7d2b573812')
JOURNAL_HELPER_SOURCE='from typing import Literal, Protocol\nclass _N31ToolResultV1(Protocol):\n    def model_dump(self, *, mode: Literal["json"]) -> dict[str,object]: ...\nclass _N31SessionV1(Protocol):\n    async def call_tool(self, name: str, arguments: dict[str,object], *,\n                       read_timeout_seconds: float) -> _N31ToolResultV1: ...\nclass _N31QueueV1(Protocol):\n    halted: object\n    current_attempt: object\n    full_loop_state: object\n    checkpoint_bootstrap_verified: bool\n    initial_save: object\n    next_sequence: int\n    def consume_sequence(self, request: dict[str,object]) -> int: ...\n\nasync def observe_native31_journal_root_v1(\n        queue: _N31QueueV1, session: _N31SessionV1,\n        request: dict[str,object], path: Path) -> None:\n    expected = {"schema", "sequence", "command", "execution_owner", "root_direct_execution_release"}\n    if (set(request) != expected or request.get("schema") != "xar.native31.root-journal-observation/v1"\n            or request.get("command") != "observe_native31_journal"\n            or request.get("execution_owner") != "Root"\n            or request.get("root_direct_execution_release") is not True\n            or type(request.get("sequence")) is not int\n            or request["sequence"] != queue.next_sequence\n            or not queue.checkpoint_bootstrap_verified or queue.initial_save is None\n            or path != INBOX / f"{queue.next_sequence:04d}-1-result.json"):\n        raise ValueError("one exact Root journal observation after cold bind required")\n    halted, attempt, state = queue.halted, queue.current_attempt, queue.full_loop_state\n    sequence = queue.next_sequence\n    response = OUTBOX / path.name\n    inflight = Q / f"INFLIGHT-{sequence:04d}.json"\n    if response.exists() or inflight.exists():\n        raise FileExistsError("journal observation already attempted; no retry")\n    context = {"request": request, "observed_at_utc": now().isoformat(),\n               "readonly_journal": True, "replay_allowed": False,\n               "ordinary_cycle_credit": 0, "day_credit": 0}\n    atomic(inflight, context, limit=16384)\n    queue.consume_sequence(request)\n    started, mono = now().isoformat(), time.monotonic()\n    row: dict[str,object] = {"request": request, "started_at_utc": started,\n        "readonly_journal": True, "replay_allowed": False,\n        "ordinary_cycle_credit": 0, "day_credit": 0,\n        "original_halt_retained": halted is not None}\n    try:\n        result = await session.call_tool("ck3_observe_native31_time_command_journal_v1", {},\n                                         read_timeout_seconds=30.0)\n        row["result"] = result.model_dump(mode="json")\n    except Exception as error:\n        row["client_error"] = repr(error)[:4096]\n    row["ended_at_utc"] = now().isoformat()\n    row["elapsed_seconds"] = time.monotonic() - mono\n    if (queue.halted is not halted or queue.current_attempt is not attempt\n            or queue.full_loop_state is not state):\n        raise RuntimeError("journal observation changed retained Queue objects")\n    atomic(response, row, limit=262144)\n\n'

class ExactRef(TypedDict):
    path: str
    bytes: int
    sha256: str

class SourceIntakeV1(TypedDict):
    source: dict[str,bytes]
    display: dict[str,bytes]
    immutable: dict[Path,bytes]
    review: dict[str,object]

def _ref_value(value: object) -> ExactRef:
    data=_record(value)
    path,size,digest=data.get("path"),data.get("bytes"),data.get("sha256")
    if (set(data)!={"path","bytes","sha256"} or not isinstance(path,str)
            or type(size) is not int or not 0<size<=1048576
            or not isinstance(digest,str) or len(digest)!=64
            or any(c not in "0123456789abcdef" for c in digest)):
        raise ValueError("exact bounded file ref required")
    return {"path":path,"bytes":size,"sha256":digest}

def _checked_bytes(reference: ExactRef) -> bytes:
    path=Path(reference["path"])
    with path.open("rb") as stream:
        raw=stream.read(1048577)
    if (len(raw)>1048576 or len(raw)!=reference["bytes"]
            or hashlib.sha256(raw).hexdigest()!=reference["sha256"]):
        raise ValueError("actual bounded ref changed: "+str(path))
    return raw

def _actual_ref(path: Path) -> ExactRef:
    with path.open("rb") as stream:
        raw=stream.read(1048577)
    if not 0<len(raw)<=1048576:
        raise ValueError("one bounded actual file required")
    return {"path":str(path.resolve()),"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}

def require_stat_identity_v1(path: Path, expected: object, *, schema: StatIdentitySchema) -> None:
    """Preparation only; known OS-ns identity, SHA/links remain independent."""
    parsed=parse_file_stat_identity_v1(expected,schema=schema)
    if normalize_file_stat_identity_v1(path.stat())!=parsed:
        raise ValueError("actual OS stat identity differs")

def read_accepted_a13_sources_v1(current_next_ref: ExactRef) -> SourceIntakeV1:
    prepared=_record(json.loads(_checked_bytes(ACCEPTED_PREPARED)))
    quote=_record(json.loads(_checked_bytes(ACCEPTED_QUOTE)))
    old_rows=prepared.get("outputs")
    quoted=quote.get("files")
    if not isinstance(old_rows,list) or not isinstance(quoted,list):
        raise ValueError("actual accepted140 source inventory required")
    expected=[{key:_record(row)[key] for key in ("path","bytes","sha256")} for row in quoted]
    if (len(old_rows)!=140 or old_rows!=expected
            or prepared.get("machine_id")!=MACHINE_ID or quote.get("machine_id")!=MACHINE_ID):
        raise ValueError("same-machine actual A13 prepared/quote140 required")
    profile=_record(json.loads(_checked_bytes(_actual_ref(ACCEPTED_ROOT/"ROOT-OBS-PROFILE-C23.json"))))
    config,name=profile.get("config_root"),profile.get("profile_name")
    if not isinstance(config,str) or not isinstance(name,str):
        raise ValueError("actual old private profile metadata required")
    mutable={Path(config)/"basic/profiles"/name/"basic.ini",
             Path(config)/"basic/scenes"/(name+".json")}
    next_path=ACCEPTED_ROOT/"NEXT-SEQUENCE-P37.json"
    if Path(current_next_ref["path"]).resolve()!=next_path.resolve():
        raise ValueError("explicit current same-root NEXT ref required")
    current_next=_record(json.loads(_checked_bytes(current_next_ref)))
    if type(current_next.get("next_sequence")) is not int:
        raise ValueError("actual current NEXT integer required")
    immutable:dict[Path,bytes]={}
    observations:list[object]=[]
    for item in old_rows:
        row=_ref_value(item);path=Path(row["path"]).resolve()
        if path in mutable:
            observations.append(_actual_ref(path));continue
        if path==next_path:
            continue
        immutable[path]=_checked_bytes(row)
    if len(immutable)!=137 or len(observations)!=2:
        raise ValueError("137 immutable plus two OBS observations and current NEXT required")
    source_review=_record(quote.get("sources"))
    names=source_review.get("runtime_source_output_names")
    if not isinstance(names,list) or len(names)!=110:
        raise ValueError("actual source110 review required")
    source:dict[str,bytes]={}
    for value in names:
        if not isinstance(value,str) or value in source:
            raise ValueError("unique actual source name required")
        path=(ACCEPTED_ROOT/value).resolve()
        if not path.is_relative_to(ACCEPTED_ROOT) or path not in immutable:
            raise ValueError("source escapes accepted immutable graph")
        source[value]=immutable[path]
    display_review=_record(quote.get("display"));display_rows=display_review.get("files")
    if not isinstance(display_rows,list) or len(display_rows)!=18:
        raise ValueError("accepted display18 required")
    display:dict[str,bytes]={}
    for value in display_rows:
        display_row=_record(value);name=display_row.get("relative_path")
        if not isinstance(name,str) or name in display:
            raise ValueError("one exact display relative path required")
        path=Path(str(display_row.get("path"))).resolve()
        if path!=(ACCEPTED_ROOT/name).resolve() or path not in immutable:
            raise ValueError("actual display input outside immutable graph")
        display[name]=immutable[path]
    return {"source":source,"display":display,"immutable":immutable,
        "review":{"machine_id":MACHINE_ID,"status":"SOURCE_ONLY_NO_COLD_OR_RUNTIME_CREDIT",
                  "accepted_prepared":ACCEPTED_PREPARED,"accepted_quote":ACCEPTED_QUOTE,
                  "immutable_files":137,"OBS_mutable_observations":observations,
                  "current_NEXT":current_next_ref,"next_sequence":current_next["next_sequence"],
                  "prior_closure_is_still_required":True,
                  "Game_Task_RPC_calls":0,"outputs_written":0}}

def owner_complete_v1(sources: dict[str,bytes], names: dict[str,str]) -> dict[str,bytes]:
    if set(names)!=set(OPS14_NAMES) or len(set(names.values()))!=5:
        raise ValueError("exact five metadata lookup names required")
    if any(not value.endswith(".json") or "/" in value or "\\" in value or value==old for old,value in names.items()):
        raise ValueError("independent metadata basenames required")
    result=dict(sources)
    for leaf,pin in OPS14_PINS.items():
        raw=sources.get(leaf)
        if raw is None or (len(raw),hashlib.sha256(raw).hexdigest())!=pin:
            raise ValueError("accepted A13 operational source differs: "+leaf)
        before=raw.decode("utf-8")
        count=Counter(node.value for node in ast.walk(ast.parse(before))
            if isinstance(node,ast.Constant) and isinstance(node.value,str) and node.value in names)
        if dict(count)!=OPS14_COUNTS[leaf]:
            raise ValueError("operational lookup AST differs")
        after=before
        for old,new in names.items():
            for quote in ("'",'"'):
                after=after.replace(quote+old+quote,quote+new+quote)
        inverse=after
        for old,new in reversed(tuple(names.items())):
            for quote in ("'",'"'):
                inverse=inverse.replace(quote+new+quote,quote+old+quote)
        if inverse!=before or after==before:
            raise ValueError("lookup transform is not reversible")
        compile(after,leaf,"exec")
        result[leaf]=after.encode("utf-8")
    return result

def native31_overlay_v1(source: Mapping[str,bytes], sidecars: Mapping[str,bytes],
                           export_rvas: Mapping[str,int], *, native_build_label: str) -> dict[str,bytes]:
    out=dict(source)
    def swap(name: str, before: str, after: str) -> None:
        old=before.encode();new=after.encode();raw=out[name]
        if raw.count(old)!=1:
            raise ValueError('Native31 exact seam differs: '+name)
        out[name]=raw.replace(old,new)
    pins={'observer_journal_v1.py':'f77710b050f839da36c308a1da66a8aec79fa0ec8bec167100f62c688a029712',
          'native31_mcp_extension_v1.py':'9c56a270f8029360de26560ded0cb3f7938749684f65921b9245f30ee49004a0'}
    for name,digest in pins.items():
        raw=sidecars[name]
        if name in out or hashlib.sha256(raw).hexdigest()!=digest:
            raise ValueError('Native31 duplicate or unqualified sidecar: '+name)
        out[name]=raw
    binder='root_native_build_binding_p37c23.py'
    swap(binder,"binding.get('status') != 'NATIVE30_SDKC23_SOURCE_BOUND_NOT_RUNTIME_ADMITTED'",
                "binding.get('status') != 'NATIVE31_SDKC23_SOURCE_BOUND_NOT_RUNTIME_ADMITTED'")
    if set(export_rvas)!={'XarCk3BridgeIdentity', 'XarCk3BridgeStop', 'XarCk3BridgeStart', 'XarCk3BridgeStartWithPipe', 'XarCk3BridgePrepareStartup'} or any(type(v) is not int or v<=0 for v in export_rvas.values()):
        raise ValueError("five exact positive Native31 function RVAs required")
    expected=repr(dict(sorted(export_rvas.items())))
    swap(binder,"    dll = pinned(native['dll'])",
        "    if (native.get('native_dll_sha256') != '3d43cd01c908013f7bb2704aa1844acd518fa691ae96ef4e09413284dd59038d'\n"
        "            or native.get('native_dll_bytes') != 19528704\n"
        "            or native.get('export_rvas') != "+expected+"):\n"
        "        raise ValueError('qualified Native31 DLL/export identity differs')\n"
        "    dll = pinned(native['dll'])")
    swap(binder,"    return {'native_build_label': native['native_build_label'],",
        "    if config.get('native_bridge_after_saved_load') is not False:\n"
        "        raise ValueError('Native31 requires original before-resume startup')\n"
        "    return {'native_build_label': native['native_build_label'],")
    entry='root_p37c23_mcp_entry.py'
    swap(entry,"        _canonical.install_service(service)\n",
        "        _canonical.install_service(service)\n"+REG31)
    outer='root_c23_canonical_outer.py'
    swap(outer,"'root_p37c23_mcp_entry.py', 'root_c23_canonical_outer.py'}",
        "'root_p37c23_mcp_entry.py', 'root_c23_canonical_outer.py',\n"
        "            'observer_journal_v1.py','native31_mcp_extension_v1.py'}")
    swap(outer,"'root_p37c23_mcp_entry.py','root_c23_canonical_outer.py'}",
        "'root_p37c23_mcp_entry.py','root_c23_canonical_outer.py',\n"
        "        'observer_journal_v1.py','native31_mcp_extension_v1.py'}")
    swap(outer,"len(rows)==6","len(rows)==8")
    swap(outer,"exact six canonical entries required","exact eight canonical entries required")
    cold='root_checkpoint_bootstrap_c23.py'
    swap(cold,"    bridge = runtime.NativeBridgeLaunchConfig(",
        "    require(pre_native_resume is not None, 'Native31 original pre-resume custody callback required')\n"
        "    bridge = runtime.NativeBridgeLaunchConfig(")
    swap(cold,"        start_minimized=True, before_process_create=before_process_create, **preload_options)",
        "        start_minimized=True, native_bridge_after_saved_load=False,\n"
        "        before_process_create=before_process_create, **preload_options)")
    resume='root_p37c23_cold_resume.py'
    if not isinstance(native_build_label,str) or not native_build_label:
        raise ValueError('qualified Native31 target label required')
    swap(resume,"freeze['native_build_label'] == 'Native30 continuous hotspot tracking and idle realm overview'",
        "freeze['native_build_label'] == "+repr(native_build_label))
    raw=out[outer]
    nodes=[n for n in ast.parse(raw).body if isinstance(n,ast.Assign)
        and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)
        and n.targets[0].id=='_C23_EXTERNAL_IMPORT_PINS']
    if len(nodes)!=1:
        raise ValueError('one existing external import assignment required')
    node=nodes[0]
    literal=ast.literal_eval(node.value)
    if not isinstance(literal,dict):
        raise ValueError('external imports must be a literal mapping')
    updated={}
    for key in literal:
        if not isinstance(key,str):
            raise ValueError('external import stem must be text')
        item=literal[key]
        if not isinstance(item,(tuple,list)) or len(item)!=2:
            raise ValueError('external import pin pair required')
        size=item[0];prior_digest=item[1]
        if (not isinstance(size,int) or isinstance(size,bool) or size<=0
            or not isinstance(prior_digest,str) or len(prior_digest)!=64
            or any(c not in '0123456789abcdef' for c in prior_digest)):
            raise ValueError('external import size/digest differs')
        updated[key]=(size,prior_digest)
    for name,digest in pins.items():
        stem=name[:-3]
        if stem in updated:
            raise ValueError('duplicate Native31 external import')
        updated[stem]=(len(sidecars[name]),digest)
    end_line=node.end_lineno;end_column=node.end_col_offset
    if end_line is None or end_column is None:
        raise ValueError('exact external assignment boundary unavailable')
    lines=raw.splitlines(keepends=True)
    start=sum(map(len,lines[:node.lineno-1]))+node.col_offset
    end=sum(map(len,lines[:end_line-1]))+end_column
    out[outer]=raw[:start]+('_C23_EXTERNAL_IMPORT_PINS='+repr(updated)).encode()+raw[end:]
    for name in (binder,entry,outer,cold,resume,*pins):
        ast.parse(out[name],filename=name)
    return out
def patch_journal_queue_v1(source: bytes) -> bytes:
    if len(source)>1048576:
        raise ValueError("bounded actual Queue source required")
    text=source.decode("utf-8")
    nodes=[node for node in ast.parse(text).body
           if isinstance(node,ast.AsyncFunctionDef) and node.name=="run_request_loop"]
    if len(nodes)!=1:
        raise ValueError("one actual request loop required")
    loop=ast.get_source_segment(text,nodes[0])
    if loop is None or (len(loop.encode()),hashlib.sha256(loop.encode()).hexdigest())!=RUN_LOOP_PIN:
        raise ValueError("accepted A13 actual request loop changed")
    marker='                    elif command == "observe_original_start" and "tool" not in request:\n'
    replacement=('                    elif command == "observe_native31_journal" and "tool" not in request:\n'
                 '                        await observe_native31_journal_root_v1(queue, session, request, path)\n'
                 + marker)
    if text.count(marker)!=1 or text.count("async def run_request_loop(queue, session):")!=1:
        raise ValueError("one bounded native journal dispatch seam required")
    after=text.replace(marker,replacement,1)
    beforeclear='if command is not None and getattr(queue, "halted", None) is None:'
    afterclear='if command is not None and command != "observe_native31_journal" and getattr(queue, "halted", None) is None:'
    if after.count(beforeclear)!=1:
        raise ValueError("one original command cleanup branch required")
    after=after.replace(beforeclear,afterclear,1)
    after=after.replace("async def run_request_loop(queue, session):",
                        JOURNAL_HELPER_SOURCE+"async def run_request_loop(queue, session):",1)
    inverse=after.replace(JOURNAL_HELPER_SOURCE,"",1).replace(afterclear,beforeclear,1).replace(replacement,marker,1)
    if inverse!=text:
        raise ValueError("journal dispatch transform is not reversible")
    compile(after,"future-A14-Queue-journal","exec")
    return after.encode("utf-8")


def _record(value: object) -> dict[str,object]:
    if not isinstance(value,dict) or not all(isinstance(key,str) for key in value):
        raise ValueError("JSON object required")
    return {key:item for key,item in value.items()}

def _encode(value: dict[str,object]) -> bytes:
    return (json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n").encode()

def _one(source: str, before: str, after: str) -> str:
    if source.count(before)!=1:
        raise ValueError("one actual source seam required: "+before)
    value=source.replace(before,after,1)
    ast.parse(value)
    return value

def derive_owner_compose_v1(source: str) -> str:
    """New recipe only: stage all deltas before the first policy/freeze seal."""
    if source.count("len(replaced)==44")!=1 or source.count("len(display_values)==18")!=1:
        raise ValueError("original complete44/display18 intake guards required")
    marker="    policy_ref=put('ROOT-C23-CANONICAL-PRELOAD-POLICY-A05.json',policy)"
    call=("    policy,six,replaced,display_values,display_review=apply_a14_policy_stage_v1("
          "policy,outputs,source,display_values,display_review,source_review,T5,"
          "A14_QUALIFIED_RICH,A14_NATIVE_SIDECARS,A14_EXPORT_RVAS,A14_NATIVE_LABEL)\n")
    value=_one(source,marker,call+marker)
    return _one(value,"'all_entry_rows':44","'all_entry_rows':len(replaced)")

def derive_complete_postguard_v1(source: str) -> str:
    return _one(source,'len(outputs)==quote["unique_files"]==140',
                'len(outputs)==quote["unique_files"]==144')

def derive_cold_owner_v1(source: str) -> str:
    return _one(source,"len(entries)==44 and len(policy['canonical_entry_source_pins'])==6",
                "len(entries)==47 and len(policy['canonical_entry_source_pins'])==8")

def derive_display_task_v1(source: str) -> str:
    return _one(source,"len(display_values) == 18","len(display_values) == 19")

def _pairs(value: object) -> list[list[str]]:
    if not isinstance(value,list):
        raise ValueError("exact source pairs required")
    rows:list[list[str]]=[]
    for row in value:
        if (not isinstance(row,(list,tuple)) or len(row)!=2
                or not isinstance(row[0],str) or not isinstance(row[1],str)):
            raise ValueError("exact path/SHA pair required")
        rows.append([row[0],row[1]])
    return rows

def _future_ref(root: Path, name: str, raw: bytes) -> dict[str,object]:
    return {"path":str(root/name),"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}

def apply_a14_policy_stage_v1(
        policy: dict[str,object], outputs: dict[Path,bytes], source: dict[str,bytes],
        display_values: dict[str,bytes], display_review: dict[str,object],
        source_review: dict[str,object], target_root: Path,
        qualified_sources: Mapping[str,bytes], native_sidecars: Mapping[str,bytes],
        export_rvas: Mapping[str,int], native_label: str
) -> tuple[dict[str,object],list[list[str]],list[list[str]],dict[str,bytes],dict[str,object]]:
    """Accepted owner-complete110/44 + target display18 -> Native31/rich47/8/19."""
    before=len(outputs)
    entries=_pairs(policy.get("entry_source_pins"))
    if len(entries)!=44 or len(display_values)!=18:
        raise ValueError("accepted complete44/display18 required before any delta")
    roots={Path(path).relative_to(target_root).as_posix():outputs[Path(path)] for path,digest in entries}
    machine=policy.get("machine_id")
    if machine!=MACHINE_ID:
        raise ValueError("actual machine required")
    projected=rich_api.compose_rich_graph(roots,display_values,_encode(policy),qualified_sources,
                                        runtime_root=str(target_root),machine_id=MACHINE_ID)
    final=native31_overlay_v1(projected.root_sources,native_sidecars,export_rvas,
                             native_build_label=native_label)
    final["root_p37c23_sdk_queue.py"]=patch_journal_queue_v1(final["root_p37c23_sdk_queue.py"])
    final["root_p37c23_mcp_entry.py"]=patch_mod_absence_binding_v1(final["root_p37c23_mcp_entry.py"])
    if len(final)!=47 or len(projected.display_sources)!=19:
        raise ValueError("actual complete47/display19 required")
    for name,raw in final.items():
        outputs[target_root/name]=raw
        source[name]=raw
    for name,raw in projected.display_sources.items():
        outputs[target_root/name]=raw
    if len(outputs)!=before+4:
        raise ValueError("exactly four new paths: two rich contracts and two Native31 sidecars")
    next_policy=_record(json.loads(projected.policy))
    complete=[[str(target_root/name),hashlib.sha256(raw).hexdigest()] for name,raw in sorted(final.items())]
    canonical_names=set(rich_api.CANONICAL)|set(NATIVE31_SIDECARS)
    eight=[row for row in complete if Path(row[0]).name in canonical_names]
    if len(complete)!=47 or len(eight)!=8:
        raise ValueError("exact complete47/canonical8 required")
    outer_nodes=[node for node in ast.parse(final["root_c23_canonical_outer.py"]).body
        if isinstance(node,ast.Assign) and len(node.targets)==1
        and isinstance(node.targets[0],ast.Name)
        and node.targets[0].id=="_C23_EXTERNAL_IMPORT_PINS"]
    if len(outer_nodes)!=1:
        raise ValueError("one final external source map required")
    external=_record(ast.literal_eval(outer_nodes[0].value))
    if len(external)!=26:
        raise ValueError("actual external26 required")
    external_refs:dict[str,object]={}
    for stem in external:
        name=stem+".py"
        if name not in final:
            raise ValueError("missing external source: "+name)
        external_refs[stem]=_future_ref(target_root,name,final[name])
    prior_imports=next_policy.get("runtime_import_source_pins")
    if not isinstance(prior_imports,list) or len(prior_imports)!=21:
        raise ValueError("all original21 runtime/import/recovery dependencies required")
    imports:list[object]=list(prior_imports)
    imports.extend(_future_ref(target_root,name,final[name]) for name in NATIVE31_SIDECARS)
    next_policy.update(entry_source_pins=complete,canonical_entry_source_pins=eight,
                       external_import_source_pins=external_refs,runtime_import_source_pins=imports)
    names=source_review.get("runtime_source_output_names")
    if not isinstance(names,list) or len(names)!=110 or not all(isinstance(name,str) for name in names):
        raise ValueError("actual original110 source review required")
    source_review["runtime_source_output_names"]=sorted(source)
    source_review["A14_stage"]={"complete":47,"canonical":8,"external":26,"runtime_import":23,
        "display":19,"added_runtime_paths":4,"closure_still_required":True}
    root_files=[dict(_future_ref(target_root,name,raw),relative_path=name)
                for name,raw in sorted(final.items())]
    changed=sorted(name for name,raw in final.items() if roots.get(name)!=raw)
    review={**display_review,**projected.review(),"target_runtime":str(target_root),
            "root_files":root_files,"root_source_count":47,"canonical_source_count":8,
            "external_source_count":26,"root_changed":changed,
            "unchanged_root":sum(roots.get(name)==raw for name,raw in final.items()),
            "canonical_source_ref_vector_sha256":hashlib.sha256(json.dumps(
                eight,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
            "runtime_import_count":23,"final_complete_count":47,"final_canonical_count":8,
            "final_external_count":26,"runtime_or_Game_credit":False}
    return next_policy,eight,complete,dict(projected.display_sources),review


def derive_current_frontier_metadata_v1(source: str, current_next_ref: ExactRef) -> str:
    """Four live frontier slots only; historical F99/SAVE10481 stays untouched."""
    if Path(current_next_ref["path"]).resolve()!=(ACCEPTED_ROOT/"NEXT-SEQUENCE-P37.json").resolve():
        raise ValueError("actual predecessor NEXT metadata required")
    packet=_record(json.loads(_checked_bytes(current_next_ref)))
    value=packet.get("next_sequence")
    if type(value) is not int or not 10538<=value<2**63:
        raise ValueError("same-source monotonic actual NEXT required")
    functions={node.name:node for node in ast.parse(source).body if isinstance(node,ast.FunctionDef)}
    raw=source.encode("utf-8");lines=raw.splitlines(keepends=True)
    changes:list[tuple[int,int,bytes]]=[]
    for name,count in (("_base",1),("saved_basis",1),("compose",2)):
        function=functions.get(name)
        if function is None:
            raise ValueError("one actual metadata function required")
        nodes=[node for node in ast.walk(function)
               if isinstance(node,ast.Constant) and type(node.value) is int and node.value==10538]
        if len(nodes)!=count:
            raise ValueError("actual live frontier slots changed: "+name)
        for node in nodes:
            if node.end_lineno is None or node.end_col_offset is None:
                raise ValueError("one exact literal boundary required")
            begin=sum(map(len,lines[:node.lineno-1]))+node.col_offset
            end=sum(map(len,lines[:node.end_lineno-1]))+node.end_col_offset
            if raw[begin:end]!=b"10538":
                raise ValueError("one live frontier literal required")
            changes.append((begin,end,str(value).encode()))
    for begin,end,replacement in sorted(changes,reverse=True):
        raw=raw[:begin]+replacement+raw[end:]
    result=raw.decode("utf-8")
    compile(result,"A14-actual-current-frontier-metadata","exec")
    return result

MOD_CLEAN_RUNTIME14="def _clean_object_v1(value: object, label: str) -> dict[str, object]:\n    if not isinstance(value,dict):\n        raise ValueError(label+' must be an object')\n    result: dict[str,object]={}\n    for key,item in value.items():\n        if not isinstance(key,str):\n            raise ValueError(label+' keys must be strings')\n        result[key]=item\n    return result\n\n\ndef _clean_generation_v1(value: dict[str,object], pid_key: str, birth_key: str) -> tuple[int,int]:\n    pid=value.get(pid_key);birth=value.get(birth_key)\n    if type(pid) is not int or not 0<pid<2**32:\n        raise ValueError('exact positive uint32 Game PID required')\n    if type(birth) is not int or not 0<birth<2**64:\n        raise ValueError('legacy v1 exact positive uint64 Game FILETIME int required')\n    return pid,birth\n\n\ndef _clean_mod_ref_v1(reference: object) -> dict[str, object]:\n    import hashlib as _clean_hashlib\n    ref=_clean_object_v1(reference,'admitted Mod absence reference')\n    if set(ref)!={'path','bytes','sha256'}:\n        raise ValueError('exact admitted Mod absence reference required')\n    path=ref['path'];size=ref['bytes'];digest=ref['sha256']\n    if (not isinstance(path,str) or not Path(path).is_absolute()\n            or type(size) is not int or not 0<size<=32768\n            or not isinstance(digest,str) or len(digest)!=64\n            or any(c not in '0123456789abcdef' for c in digest)):\n        raise ValueError('bounded admitted Mod absence reference required')\n    with Path(path).open('rb') as stream:\n        raw=stream.read(32769)\n    if len(raw)!=size or _clean_hashlib.sha256(raw).hexdigest()!=digest:\n        raise ValueError('admitted Mod absence bytes changed')\n    value: object=json.loads(raw)\n    return _clean_object_v1(value,'Mod absence')\n\n\ndef bind_clean_lifecycle(manifest: dict[str, object], **kwargs: object) -> object:\n    launch_value: object=json.loads((N/'ROOT-ACTUAL-GAME-LAUNCH-C23.json').read_bytes())\n    launch=_clean_object_v1(launch_value,'actual Game launch')\n    with (N/'ROOT-P37C23-COLD-RESUME-ADMISSION.json').open('rb') as stream:\n        raw=stream.read(131073)\n    if len(raw)>131072:\n        raise ValueError('bounded actual cold admission required')\n    admission_value: object=json.loads(raw)\n    admission=_clean_object_v1(admission_value,'actual cold admission')\n    proof=_clean_mod_ref_v1(admission.get('mod_absence'))\n    if (_clean_generation_v1(launch,'pid','creation_filetime')\n            !=_clean_generation_v1(proof,'game_pid','game_creation_filetime')):\n        raise ValueError('actual vanilla evidence belongs to another Game generation')\n    return original_bind_lifecycle({**manifest,'verified_mod_absence':proof},**kwargs)\n"

def patch_mod_absence_binding_v1(source: bytes) -> bytes:
    """Use the exact admitted proof ref; legacy v1 Game identity stays strict int."""
    if len(source)>1048576:
        raise ValueError("bounded entry source required")
    text=source.decode("utf-8")
    nodes=[n for n in ast.parse(text).body
        if isinstance(n,ast.FunctionDef) and n.name=="bind_clean_lifecycle"]
    if len(nodes)!=1 or nodes[0].decorator_list:
        raise ValueError("one original clean lifecycle binding required")
    node=nodes[0]
    original=ast.get_source_segment(text,node)
    if original is None or original!=MOD_CLEAN_LEGACY14 or hashlib.sha256(original.encode()).hexdigest()!="fa639ebf85f63eb5aef0ae3c856f66416813a1023997e2e135a48009b8a33dcd":
        raise ValueError("actual legacy clean lifecycle function differs")
    if "_clean_mod_ref_v1" in text:
        raise ValueError("clean Mod ref transform already applied")
    result=_one(text,original,MOD_CLEAN_RUNTIME14.rstrip())
    compile(result,"A14-exact-admitted-Mod-proof","exec")
    return result.encode()

class ModAbsenceIdentityV1(TypedDict):
    schema: Literal["xar.verified-xar-mod-absence/v1"]
    game_pid: int
    game_creation_filetime: int

def build_mod_absence_identity_v1(launch: Mapping[str,object]) -> ModAbsenceIdentityV1:
    """Canonical v1 identity fragment; separate actual profile/log review is required."""
    pid=launch.get("pid");birth=launch.get("creation_filetime")
    if type(pid) is not int or not 0<pid<2**32:
        raise ValueError("actual launch PID must be an exact positive uint32")
    if type(birth) is not int or not 0<birth<2**64:
        raise ValueError("legacy v1 FILETIME must be an exact positive uint64 int")
    return {"schema":"xar.verified-xar-mod-absence/v1",
            "game_pid":pid,"game_creation_filetime":birth}

NATIVE31_LOADED_WRAPPER_SOURCE='from __future__ import annotations\nfrom typing import Callable\n\nNative31ReadonlyCallbackV1 = Callable[[], dict[str, object]]\nNative31ReadonlyRegisterV1 = Callable[[Native31ReadonlyCallbackV1], object]\nNative31ExistingEnsureV1 = Callable[[object], object]\n\ndef native31_loaded_readonly_registration_v1(\n        register: Native31ReadonlyRegisterV1,\n        ensure: Native31ExistingEnsureV1, *,\n        owner: object) -> Native31ReadonlyRegisterV1:\n    """Registration is inert. Only an explicit read enters the existing gate.\n    None from the legacy gate is not issuance proof: the original callback\n    still validates the actual cached DTO, seal, owner, DLL and Game identity.\n    """\n    def decorate(callback: Native31ReadonlyCallbackV1) -> object:\n        def ck3_observe_native31_time_command_journal_v1() -> dict[str, object]:\n            from xar_autoplayer.bridge.native_loaded_provider_custody_v1 import (\n                CustodyIssueResultV1, _PreloadCustodyV1, _RESOURCE_SEAL)\n            from xar_autoplayer.bridge.native_loaded_provider_origin_v1 import _OriginSessionV1\n            outcome = ensure(owner)\n            if outcome is not None:\n                if (not isinstance(outcome, CustodyIssueResultV1)\n                        or type(outcome.issued) is not bool or outcome.issued is not True):\n                    raise ValueError("existing loaded Native custody issuer unavailable")\n            holder: object = getattr(owner, "_player_heir_loaded_custody_v1", None)\n            if (not isinstance(holder, _PreloadCustodyV1)\n                    or getattr(holder, "seal", None) is not _RESOURCE_SEAL\n                    or getattr(holder, "closed", None) is not False\n                    or getattr(holder, "owner", None) is not owner):\n                raise ValueError("same open loaded Native custody holder required")\n            session: object = getattr(holder, "_origin_session_v1", None)\n            if (type(session) is not _OriginSessionV1\n                    or getattr(session, "holder", None) is not holder):\n                raise ValueError("same existing loaded Native origin session required")\n            owner_epoch: object = getattr(owner, "epoch", None)\n            session_epoch: object = getattr(session, "epoch", None)\n            if (type(owner_epoch) is not str or not owner_epoch\n                    or type(session_epoch) is not str or owner_epoch != session_epoch):\n                raise ValueError("same existing loaded Native origin epoch required")\n            return callback()\n        return register(ck3_observe_native31_time_command_journal_v1)\n    return decorate\n'

MOD_CLEAN_LEGACY14="def bind_clean_lifecycle(manifest, **kwargs):\n    launch=json.loads((N/'ROOT-ACTUAL-GAME-LAUNCH-C23.json').read_bytes())\n    proof=json.loads((N/'ROOT-CLEAN-CAMPAIGN-MOD-ABSENCE-ACTUAL-C23.json').read_bytes())\n    if (proof.get('game_pid')!=launch['pid']\n            or proof.get('game_creation_filetime')!=launch['creation_filetime']):\n        raise ValueError('actual vanilla evidence belongs to another Game generation')\n    return original_bind_lifecycle({**manifest,'verified_mod_absence':proof},**kwargs)"

RECORDING_LEGACY14='def current_recording_inputs_v1(admission,checked):\n    """Then-actual cold identity; original verify_segment performs live validation."""\n    from uuid import UUID\n    binding=checked(admission[\'recording_binding\'],65536);game=admission[\'new_Game\']\n    require(binding.get(\'schema\')==\'xar.C23-actual-cold-recording-binding/v1\'\n        and binding.get(\'machine_id\')==MACHINE and binding.get(\'status\')==\'ACTUAL_NEW_RECORDING_READY\'\n        and (game[\'pid\'],game[\'creation_filetime\'])!=(OLD_GAME[\'pid\'],OLD_GAME[\'creation_filetime\'])\n        and type(game[\'pid\']) is int and game[\'pid\']>0\n        and type(game[\'creation_filetime\']) is int and game[\'creation_filetime\']>0\n        and binding.get(\'Game_pid\')==game[\'pid\'] and binding.get(\'Game_creation_filetime\')==game[\'creation_filetime\'],\n        \'actual new cold Game and recording binding required\')\n    request=checked(binding[\'request\'],16384);job=checked(binding[\'job\'],65536)\n    started=checked(binding[\'started\'],32768);first=checked(binding[\'first_frame_admission\'],32768)\n    checked(binding[\'publisher_started\'],65536)\n    sid=str(UUID(binding[\'session_id\']));root=Path(request[\'receipt_root\']).resolve()\n    n=Path(admission[\'queue_source\'][\'path\']).resolve().parent;first_path=Path(binding[\'first_frame_admission\'][\'path\']).resolve()\n    require(sid==binding[\'session_id\'] and sid not in (\'2b8912a6-757d-46a4-a8ae-b7702a730a90\',\'79872e3d-e384-4be0-b160-c3608d419525\')\n        and root.is_relative_to(n/\'recordings\') and root.name==sid\n        and request.get(\'session_id\')==job.get(\'session_id\')==first.get(\'recorder_session_id\')==sid\n        and Path(job[\'receipt_root\']).resolve()==root\n        and Path(binding[\'job\'][\'path\']).resolve()==root/\'job.json\'\n        and Path(binding[\'started\'][\'path\']).resolve()==root/\'started.json\'\n        and type(request.get(\'worker_pid\')) is int and request[\'worker_pid\']>0\n        and type(request.get(\'worker_creation_filetime\')) is int and request[\'worker_creation_filetime\']>0\n        and job.get(\'pid\')==started.get(\'game_pid\')==first.get(\'game_pid\')==game[\'pid\']\n        and job.get(\'game_creation_filetime\')==started.get(\'game_creation_filetime\')==first.get(\'game_creation_filetime\')==game[\'creation_filetime\']\n        and started.get(\'state\')==\'recording\' and first.get(\'status\')==\'GREEN\' and first.get(\'machine_id\')==MACHINE\n        and first_path.is_relative_to(n)\n        and first_path.name not in (\'ROOT-SAVED-MAP-RECORDING-ADMITTED-C16.json\',\'ROOT-SAVED-MAP-RECORDING-ADMITTED-C22.json\')\n        and Path(first[\'recording_job_root\']).resolve()==root\n        and first.get(\'publisher_started\')==job.get(\'decision_text_publisher_receipt\')==binding[\'publisher_started\'],\n        \'actual new publisher/recording/Root firstgate tuple differs\')\n    return {\'binding\':binding,\'requested\':request,\'root\':root,\'first_path\':first_path}'
RECORDING_IDENTITY14='def current_recording_inputs_v1(admission: object,checked: object) -> dict[str,object]:\n    """Then-actual cold identity; original verify_segment performs live validation."""\n    from uuid import UUID\n    def _record(value: object) -> dict[str,object]:\n        if not isinstance(value,dict):\n            raise ValueError("recording JSON object required")\n        result: dict[str,object]={}\n        for key,item in value.items():\n            if not isinstance(key,str):\n                raise ValueError("recording JSON keys must be strings")\n            result[key]=item\n        return result\n    def _text(value: object) -> str:\n        if not isinstance(value,str) or not value:\n            raise ValueError("nonempty recording path/session text required")\n        return value\n    def _path(value: object) -> Path:\n        return Path(_text(value))\n    if not callable(checked):\n        raise ValueError("actual checked input loader required")\n    def _checked(reference: object,limit: int) -> dict[str,object]:\n        result: object=checked(reference,limit)\n        return _record(result)\n    def _identity(record: object,pid_key: str,birth_key: str) -> tuple[int,int]:\n        value=_record(record)\n        pid: object=value.get(pid_key);birth: object=value.get(birth_key)\n        if type(pid) is not int or not 0<pid<2**32:\n            raise ValueError("recording "+pid_key+" exact uint32 required")\n        if type(birth) is not int or not 0<birth<2**64:\n            raise ValueError("recording "+birth_key+" exact uint64 int required")\n        return pid,birth\n    admission=_record(admission)\n    if not {\'recording_binding\',\'new_Game\',\'queue_source\'}<=set(admission):\n        raise ValueError("required recording admission fields missing")\n    game=_record(admission.get(\'new_Game\'))\n    game_pid,game_birth=_identity(game,\'pid\',\'creation_filetime\')\n    binding=_checked(admission[\'recording_binding\'],65536)\n    _identity(binding,\'Game_pid\',\'Game_creation_filetime\')\n    require(binding.get(\'schema\')==\'xar.C23-actual-cold-recording-binding/v1\'\n        and binding.get(\'machine_id\')==MACHINE and binding.get(\'status\')==\'ACTUAL_NEW_RECORDING_READY\'\n        and (game_pid,game_birth)!=(OLD_GAME[\'pid\'],OLD_GAME[\'creation_filetime\'])\n        and type(game_pid) is int and game_pid>0\n        and type(game_birth) is int and game_birth>0\n        and binding.get(\'Game_pid\')==game_pid and binding.get(\'Game_creation_filetime\')==game_birth,\n        \'actual new cold Game and recording binding required\')\n    request=_checked(binding[\'request\'],16384);job=_checked(binding[\'job\'],65536)\n    started=_checked(binding[\'started\'],32768);first=_checked(binding[\'first_frame_admission\'],32768)\n    worker_pid,worker_birth=_identity(request,\'worker_pid\',\'worker_creation_filetime\')\n    _identity(job,\'pid\',\'game_creation_filetime\')\n    _identity(started,\'game_pid\',\'game_creation_filetime\')\n    _identity(first,\'game_pid\',\'game_creation_filetime\')\n    _checked(binding[\'publisher_started\'],65536)\n    sid=str(UUID(_text(binding[\'session_id\'])));root=_path(request[\'receipt_root\']).resolve()\n    n=_path(_record(admission[\'queue_source\'])[\'path\']).resolve().parent;first_path=_path(_record(binding[\'first_frame_admission\'])[\'path\']).resolve()\n    require(sid==binding[\'session_id\'] and sid not in (\'2b8912a6-757d-46a4-a8ae-b7702a730a90\',\'79872e3d-e384-4be0-b160-c3608d419525\')\n        and root.is_relative_to(n/\'recordings\') and root.name==sid\n        and request.get(\'session_id\')==job.get(\'session_id\')==first.get(\'recorder_session_id\')==sid\n        and _path(job[\'receipt_root\']).resolve()==root\n        and _path(_record(binding[\'job\'])[\'path\']).resolve()==root/\'job.json\'\n        and _path(_record(binding[\'started\'])[\'path\']).resolve()==root/\'started.json\'\n        and type(worker_pid) is int and worker_pid>0\n        and type(worker_birth) is int and worker_birth>0\n        and job.get(\'pid\')==started.get(\'game_pid\')==first.get(\'game_pid\')==game_pid\n        and job.get(\'game_creation_filetime\')==started.get(\'game_creation_filetime\')==first.get(\'game_creation_filetime\')==game_birth\n        and started.get(\'state\')==\'recording\' and first.get(\'status\')==\'GREEN\' and first.get(\'machine_id\')==MACHINE\n        and first_path.is_relative_to(n)\n        and first_path.name not in (\'ROOT-SAVED-MAP-RECORDING-ADMITTED-C16.json\',\'ROOT-SAVED-MAP-RECORDING-ADMITTED-C22.json\')\n        and _path(first[\'recording_job_root\']).resolve()==root\n        and first.get(\'publisher_started\')==job.get(\'decision_text_publisher_receipt\')==binding[\'publisher_started\'],\n        \'actual new publisher/recording/Root firstgate tuple differs\')\n    return {\'binding\':binding,\'requested\':request,\'root\':root,\'first_path\':first_path}'

def patch_recording_identity_v1(source: bytes) -> bytes:
    """RAM postimage only; deployment retains the original helper and installs this API explicitly."""
    if len(source)>1048576:
        raise ValueError("bounded original helper source required")
    text=source.decode("utf-8")
    nodes=[n for n in ast.parse(text).body
        if isinstance(n,ast.FunctionDef) and n.name=="current_recording_inputs_v1"]
    if len(nodes)!=1 or nodes[0].decorator_list:
        raise ValueError("one original recording helper required")
    old=ast.get_source_segment(text,nodes[0])
    if old!=RECORDING_LEGACY14:
        raise ValueError("actual original recording helper function differs")
    result=_one(text,RECORDING_LEGACY14,RECORDING_IDENTITY14)
    compile(result,"A14-recording-identity-postimage","exec")
    return result.encode()

class ModAbsenceReviewV1(TypedDict):
    schema: Literal["xar.mod-absence-root-review/v1"]
    machine_id: str
    reviewer: Literal["/root"]
    at_utc: str
    actual_game: ExactRef
    environment_manifest: ExactRef
    startup_log_reviewed: Literal[True]
    enabled_mods_known: Literal[True]
    loaded_mods_known: Literal[True]
    enabled_mods: list[str]
    loaded_mods: list[str]
    profile_enabled_mods: ExactRef
    startup_log_snapshot: ExactRef
    startup_log_original_path: str
    startup_log_snapshot_scope: str

class VerifiedModAbsenceV1(ModAbsenceIdentityV1):
    machine_id: str
    status: Literal["ACTUAL_PROFILE_AND_STARTUP_LOG_VERIFIED"]
    reviewer: Literal["/root"]
    at_utc: str
    startup_log_reviewed: Literal[True]
    enabled_mods_known: Literal[True]
    loaded_mods_known: Literal[True]
    enabled_mods: list[str]
    loaded_mods: list[str]
    environment_sha256: str
    profile_dir: str
    profile_enabled_mods: ExactRef
    startup_log_snapshot: ExactRef
    startup_log_original_path: str
    startup_log_snapshot_scope: str
    actual_game: ExactRef
    environment_manifest: ExactRef

def build_mod_absence_proof_v1(
        launch_ref: ExactRef, manifest_ref: ExactRef, reviewed: object
) -> VerifiedModAbsenceV1:
    """No log interpretation: Root supplies an explicit same-generation review."""
    review=_record(reviewed)
    fields={"schema","machine_id","reviewer","at_utc","actual_game","environment_manifest",
        "startup_log_reviewed","enabled_mods_known","loaded_mods_known","enabled_mods",
        "loaded_mods","profile_enabled_mods","startup_log_snapshot",
        "startup_log_original_path","startup_log_snapshot_scope"}
    if (set(review)!=fields or review.get("schema")!="xar.mod-absence-root-review/v1"
            or review.get("machine_id")!=MACHINE_ID or review.get("reviewer")!="/root"
            or review.get("actual_game")!=launch_ref
            or review.get("environment_manifest")!=manifest_ref
            or review.get("startup_log_reviewed") is not True
            or review.get("enabled_mods_known") is not True
            or review.get("loaded_mods_known") is not True
            or review.get("enabled_mods")!=[] or review.get("loaded_mods")!=[]):
        raise ValueError("explicit same-machine same-generation Root review required")
    launch=_record(json.loads(_checked_bytes(launch_ref)))
    manifest=_record(json.loads(_checked_bytes(manifest_ref)))
    identity=build_mod_absence_identity_v1(launch)
    load=_record(manifest.get("load_profile"))
    profile=manifest.get("profile_dir");environment=manifest.get("environment_sha256")
    at=review.get("at_utc");scope=review.get("startup_log_snapshot_scope")
    original=review.get("startup_log_original_path")
    if (launch.get("machine_id")!=MACHINE_ID or load.get("enabled_mods")!=[]
            or not isinstance(profile,str) or not Path(profile).is_absolute()
            or not isinstance(environment,str) or len(environment)!=64
            or any(c not in "0123456789abcdef" for c in environment)
            or not isinstance(at,str) or not at
            or not isinstance(scope,str) or not scope
            or not isinstance(original,str) or not original):
        raise ValueError("actual isolated environment/review fields differ")
    from datetime import datetime
    if datetime.fromisoformat(at).tzinfo is None:
        raise ValueError("explicit observed review timezone required")
    mods_ref=_ref_value(review.get("profile_enabled_mods"))
    snapshot_ref=_ref_value(review.get("startup_log_snapshot"))
    if mods_ref["bytes"]>65536 or not 0<snapshot_ref["bytes"]<=262144:
        raise ValueError("finite actual profile/log evidence required")
    mods_raw=_checked_bytes(mods_ref)
    mods=_record(json.loads(mods_raw))
    if (Path(mods_ref["path"]).resolve()!=Path(profile).resolve()/"dlc_load.json"
            or mods.get("enabled_mods")!=[]
            or load.get("dlc_load_sha256")!=hashlib.sha256(mods_raw).hexdigest()
            or not Path(original).resolve().is_relative_to(Path(profile).resolve()/"logs")):
        raise ValueError("actual isolated profile/log source differs")
    snapshot=_checked_bytes(snapshot_ref)
    if not snapshot:
        raise ValueError("nonempty actual reviewed startup snapshot required")
    return {**identity,"machine_id":MACHINE_ID,
        "status":"ACTUAL_PROFILE_AND_STARTUP_LOG_VERIFIED","reviewer":"/root",
        "at_utc":at,"startup_log_reviewed":True,"enabled_mods_known":True,
        "loaded_mods_known":True,"enabled_mods":[],"loaded_mods":[],
        "environment_sha256":environment,"profile_dir":profile,
        "profile_enabled_mods":mods_ref,"startup_log_snapshot":snapshot_ref,
        "startup_log_original_path":original,"startup_log_snapshot_scope":scope,
        "actual_game":launch_ref,"environment_manifest":manifest_ref}
