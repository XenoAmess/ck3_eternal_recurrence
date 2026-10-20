"""Create-only same-Game A12 recording02 graph; composition performs no writes."""
from __future__ import annotations
import ast
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

MACHINE="xenoamess-full-tower-eb9d2c1186"
ROOT=Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep")
U=ROOT/"robert30-v20261019-campaign01/runtime-a12"
P=U/"presentation-c23"
O=ROOT/"p51-fresh1066-v20261019-prepare01/c23-source23-native30-cold100"
TASK=O/"tasks/spec-display-a12-recording02"
GAME=(106220,134369831434087677)
CAPTURE="ck3_obs_capture_startup240_recording02.py"
OWNER="start_new_game_display_recording02.py"
MANIFEST="SOURCE-PINS-A12-RECORDING02.json"
PIN_CAPTURE=(76250,"1b7fad4f9497c0f1f78e73be24a8effc9b0f043080005f151c5dd9257958173a")
PIN_OWNER=(14940,"56d6db9a181d10263c7238cfedd7f828076dfce3557a91460dc42b71e4c92ccb")
PIN_MANIFEST=(6700,"9f4db23346d4ec374dcb9a21473fd4b3b4099841f1d017fe76e64548f35d7d36")
PIN_PROFILE=(3968,"18c26451b7efbb59174f164dede0a35867eb5e3e7cb964956b03780db9e6cefa")
PIN_TASK=(3999,"eb30aae10ce98ee9c7cae2168cfeeb0c5156515ba61916aef93fb950642999dd")
def require(ok: bool, why: str) -> None:
    if not ok: raise ValueError("A12 recording02: "+why)
def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()
def encode(value: Any) -> bytes:
    return (json.dumps(value,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
def pin(path: Path, raw: bytes) -> dict[str,Any]:
    return dict(path=str(path.resolve()),bytes=len(raw),sha256=sha(raw))
def finite(path: Path, limit: int=131072) -> bytes:
    require(path.is_file() and path.stat().st_size<=limit,"bounded actual file required")
    return path.read_bytes()
def exact(path: Path, expected: tuple[int,str]) -> bytes:
    raw=finite(path)
    require((len(raw),sha(raw))==expected,"source pin differs: "+str(path))
    return raw
def checked(ref: dict[str,Any]) -> bytes:
    return exact(Path(ref["path"]),(ref["bytes"],ref["sha256"]))
def swap(text: str, before: str, after: str, count: int=1) -> str:
    require(text.count(before)==count,"exact source seam required")
    return text.replace(before,after,count)

def capture_source(raw: bytes) -> bytes:
    require((len(raw),sha(raw))==PIN_CAPTURE,"exact frozen 2x capture")
    text=raw.decode()
    pairs=[
      ("        for _ in range(120):","        startup_deadline = time.monotonic() + 240.0\n        while time.monotonic() < startup_deadline:"),
      ('            "port": self.profile["port"], "argv": argv})',
       '            "port": self.profile["port"], "argv": argv,\n            "startup_budget_seconds": 240.0, "startup_budget_scope": "owned_OBS_initialization_only"})'),
      ('raise TimeoutError("owned OBS listener did not become ready")',
       'raise TimeoutError("owned OBS did not become ready within its 240s startup budget")')]
    for a,b in pairs:text=swap(text,a,b)
    inverse=text
    for a,b in reversed(pairs):inverse=swap(inverse,b,a)
    require(inverse.encode()==raw,"capture changed beyond initialization budget")
    result=text.encode();compile(result,str(P/CAPTURE),"exec");return result

EXTERNAL_BINDING_HELPER="""def _recording02_started_reference(path, api):
    binding=api.read(path)
    if (binding.get('schema')!='xar.ck3.decision-text-publisher-binding/v1'
            or binding.get('machine_id')!=SPEC['machine_id']
            or binding.get('publisher_sources')!=api.source_pins()
            or binding.get('OBS_draw_ack') is not False):
        raise ValueError('Exact recording02 publisher binding required')
    reference=binding['publisher_started']
    api.validate_started(reference,machine_id=SPEC['machine_id'])
    return reference


"""
def owner_source(raw: bytes, capture: bytes, nonce: str, q: Path) -> bytes:
    require((len(raw),sha(raw))==PIN_OWNER,"exact frozen A12 owner")
    text=raw.decode();tree=ast.parse(text)
    node=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="SPEC" for t in n.targets))
    spec=ast.literal_eval(node.value)
    require(spec["generation"]=="Source28-A12" and spec["target_runtime"]==str(U),"source owner generation")
    spec.update(generation="Source28-A12-RECORDING02",display_nonce=nonce,
      source_manifest=MANIFEST,profile=str((q/"PROFILE.json").relative_to(U)),
      config=str((q/"publisher-config.json").relative_to(U)),state=str((q/"publisher").relative_to(U)),
      text=str((q/"live-decision.txt").relative_to(U)),binding=str((q/"publisher-binding.json").relative_to(U)),
      requested=str((q/"recording-requested.json").relative_to(U)),
      current_recording=str((q/"current-recording-requested.json").relative_to(U)),
      first_admission=str((q/"FIRST-FRAME-ADMITTED.json").relative_to(U)),
      map_admission=str((q/"MAP-ADMITTED.json").relative_to(U)))
    segment=ast.get_source_segment(text,node)
    pairs=[(segment,"SPEC="+repr(spec),1),
      ("ck3_obs_capture_png_retry_c23.py",CAPTURE,2),
      ("len(raw)==76250","len(raw)=="+str(len(capture)),2),
      (PIN_CAPTURE[1],sha(capture),3),
      ("def main():",EXTERNAL_BINDING_HELPER+"def main():",1),
      ("api_module.started_reference(N,api)==reference","_recording02_started_reference(binding,api)==reference",1)]
    for a,b,count in pairs:text=swap(text,a,b,count)
    inverse=text
    for a,b,count in reversed(pairs):inverse=swap(inverse,b,a,count)
    require(inverse.encode()==raw,"owner changed outside exact recording02 namespace")
    result=text.encode();compile(result,str(P/OWNER),"exec");return result

def prior_closure() -> list[dict[str,Any]]:
    rows=[
      (U/"ROOT-A12-LATE-OWNED-OBS-CLOSE-RESULT01.json",(560,"2f8afcf4111418779fa8f68606a153b9a1cb4ccdd98d51eadbfc9fb666c73b03")),
      (U/"decision-text-publisher-c23/OWNER-CLOSED.json",(722,"27dbb018521e855a63ee1807300013c9493fa7434c9f4c25588f9bead106874f")),
      (O/"tasks/spec-display-a12/CLOSED.json",(745,"555b5d00369e586fcede94bf1179c8898deca35fb1280344adc90a4f1639ba7f")),
      (U/"ROOT-A12-DISPLAY01-UNREGISTER01.json",(1980,"a0e0437155c588e954a432623c104d3f8804a9fc13313fc8e6ca86c7f0c86dff"))]
    docs=[json.loads(exact(p,e)) for p,e in rows]
    a,b,c,d=docs
    require(a["machine_id"]==b["machine_id"]==c["machine_id"]==MACHINE
      and a["pid"]==67848 and int(a["creation_filetime"])==134369836079170766
      and a["exit_code"]==0 and a["normal_exit_observed"] is True
      and b["kernel_exit_observed"] is True and b["exit_code"]==0
      and c["child_exit_code"]==1 and c["job_active_after_stage"]==0
      and c["forced_remaining_cleanup"] is False
      and d["returncode"]==0 and json.loads(d["stdout"])["actual"]["absent_after"] is True,
      "actual previous OBS/publisher/Task closure required")
    return [pin(p,exact(p,e)) for p,e in rows]

def compose(plan: dict[str,Any]) -> tuple[dict[Path,bytes],dict[str,Any]]:
    require(set(plan)=={"schema","machine_id","observed_at_utc","display_nonce","task_nonce","full_storage_ref"}
      and plan["schema"]=="xar.A12-recording02-compose-input/v1" and plan["machine_id"]==MACHINE,"exact plan")
    nonce,tn=plan["display_nonce"],plan["task_nonce"]
    require(all(isinstance(x,str) and re.fullmatch("[0-9a-f]{32}",x) for x in [nonce,tn])
      and nonce!=tn and nonce not in ["66757c17b7e84c5795623621f7a7f9a3","6ac63c3d9e384f26a58cefb9064e6139"]
      and tn not in ["66757c17b7e84c5795623621f7a7f9a3","6ac63c3d9e384f26a58cefb9064e6139"],"fresh independent nonces")
    observed=datetime.fromisoformat(plan["observed_at_utc"].replace("Z","+00:00"))
    fullraw=checked(plan["full_storage_ref"]);full=json.loads(fullraw)
    require(fullraw==finite(U/"STORAGE-ADMISSION.json") and full["machine_id"]==MACHINE
      and full["status"]=="ADMITTED" and observed.tzinfo is not None
      and observed<=datetime.now(timezone.utc)<datetime.fromisoformat(full["review_at_utc"]),"actual canonical full and deadline")
    refs=prior_closure();q=U/("recording02-"+nonce)
    require(not q.exists() and not TASK.exists(),"fresh output namespace and Task")
    oldmanifest=exact(P/"SOURCE-PINS-C23.json",PIN_MANIFEST);manifest=json.loads(oldmanifest)
    require(manifest["machine_id"]==MACHINE and len(manifest["files"])==18,"complete source manifest")
    for row in manifest["files"]:checked(row)
    capture=capture_source(exact(P/"ck3_obs_capture_png_retry_c23.py",PIN_CAPTURE))
    owner=owner_source(exact(P/"start_new_game_display.py",PIN_OWNER),capture,nonce,q)
    outputs={P/CAPTURE:capture,P/OWNER:owner}
    rows=[]
    for row in manifest["files"]:
        rel=row["relative_path"]
        if rel=="presentation-c23/ck3_obs_capture_png_retry_c23.py":rows.append(pin(P/CAPTURE,capture)|{"relative_path":"presentation-c23/"+CAPTURE})
        elif rel=="presentation-c23/start_new_game_display.py":rows.append(pin(P/OWNER,owner)|{"relative_path":"presentation-c23/"+OWNER})
        else:rows.append(row)
    require(len(rows)==18 and sum(r["relative_path"].startswith("@") for r in rows)==1,"source closure 18")
    outputs[P/MANIFEST]=encode(dict(manifest,files=rows))
    profile=json.loads(exact(U/"ROOT-OBS-PROFILE-C23.json",PIN_PROFILE))
    profile.update(profile_name="ManagedWindowCapture-"+nonce,collection_name="ManagedWindowCapture-"+nonce,
      prepared_at_utc=plan["observed_at_utc"],storage_review_at_utc=full["review_at_utc"],recording_root=str(U/"recordings"),
      A12_recording02_nonce=nonce)
    profile.pop("A12_display_nonce",None)
    dep=Path("Z:/ck3_mod_rewrite/tools/g2_saved_campaign/prepare_c23_a05_display_v1.py")
    exact(dep,(19174,"e8ffb353b51eb7ae258e58e503f28e372cbae9b53d0c5577e2627fdf339a346c"))
    if str(dep.parent) not in sys.path:sys.path.insert(0,str(dep.parent))
    import prepare_c23_a05_display_v1 as primitive
    profile["storage"]=primitive.storage_binding_v1(fullraw,canonical_path=str(U/"STORAGE-ADMISSION.json"))
    outputs[q/"PROFILE.json"]=encode(profile)
    outputs.update(primitive._portable_companions(profile,capture))
    oldtask=json.loads(exact(O/"tasks/spec-display-a12/SPEC.json",PIN_TASK));task=copy.deepcopy(oldtask)
    launchraw=finite(U/"ROOT-ACTUAL-GAME-LAUNCH-C23.json");launch=json.loads(launchraw)
    placementraw=finite(U/"ROOT-GAME-PLACEMENT-C23.json");placement=json.loads(placementraw)
    require((launch["pid"],launch["creation_filetime"])==GAME
      and (placement["pid"],placement["creation_filetime"])==GAME
      and placement["status"]=="GREEN" and placement["client_rect"]==[0,0,1280,720]
      and placement["foreground_unchanged"] is True and placement["current_desktop_unchanged"] is True,"same actual placed Game")
    task.update(nonce=tn,task_name="XARG2ManagedOwner-"+tn,root=str(TASK),stage=str(P/OWNER),stage_sha256=sha(owner))
    args=task["stage_args"];args[args.index("--obs-profile")+1]=str(q/"PROFILE.json");task["stage_args"]=args
    require(set(task["env"])=={"PYTHONDONTWRITEBYTECODE","PYTHONPATH"} and task["role"]=="display_owner","original typed display environment")
    outputs[TASK/"SPEC.json"]=encode(task)
    pointer_names=["ROOT-DECISION-TEXT-PUBLISHER-BINDING-C23.json","ROOT-CURRENT-OBS-RECORDING-REQUESTED-C23.json"]
    oldpointers=[]
    for name in pointer_names:
        raw=finite(U/name);ref=pin(U/name,raw);archive=q/("PREVIOUS-"+name)
        outputs[archive]=raw;oldpointers.append(dict(canonical=str(U/name),expected_old=ref,archive=pin(archive,raw)))
    intent=dict(schema="xar.A12-recording02-pointer-activation-intent/v1",machine_id=MACHINE,Game=list(GAME),
      previous=oldpointers,new_binding=str(q/"publisher-binding.json"),new_current_recording=str(q/"current-recording-requested.json"),
      condition="ONLY_AFTER_ACTUAL_NEW_REQUEST_JOB_STARTED_FIRSTGATE_PUBLISHER_VALIDATED",
      compare_and_swap_required=True,old_failed_recording="d215445f-53b0-4fc9-a450-0cf29dd093c4",
      original_140_modified=False,CURRENT_REQUEST_P37_modified=False)
    outputs[q/"ACTIVATION-INTENT.json"]=encode(intent)
    approved=[Path(x).resolve() for x in full["approved_output_roots"]]
    require(all(any(p.resolve().is_relative_to(r) for r in approved) for p in outputs),"approved output paths")
    require(not any(p.exists() for p in outputs),"every output create-only")
    logical=sum(map(len,outputs.values()));allocated=sum(((len(b)+4095)//4096)*4096 for b in outputs.values())
    review=dict(schema="xar.A12-recording02-RAM-review/v1",machine_id=MACHINE,observed_at_utc=plan["observed_at_utc"],
      status="RAM_ONLY_NOT_ADOPTED",Game=list(GAME),startup_budget_seconds=240,startup_budget_is_business_timeout=False,
      Task_SPEC=pin(TASK/"SPEC.json",outputs[TASK/"SPEC.json"]),files=[pin(p,b) for p,b in outputs.items()],
      source_manifest_rows=18,shared_frozen_publisher_path=str(P/"g2_saved_campaign/decision_text_publisher.py"),
      full_storage_ref=plan["full_storage_ref"],storage_review_at_utc=full["review_at_utc"],prior_closure=refs,
      old_runtime_or_profile_writes=0,Game_OBS_Task_RPC_calls=0,
      required_directories=[str(q),str(TASK),str(U/"recordings"),str(Path(profile["config_root"])/"basic/profiles"/profile["profile_name"])],
      new_binding=str(q/"publisher-binding.json"),new_current_recording=str(q/"current-recording-requested.json"),
      firstgate=str(q/"FIRST-FRAME-ADMITTED.json"),activation_intent=intent,
      logical_bytes=logical,allocation_4KiB_upper=allocated,FS_and_receipt_not_included=True)
    return outputs,review
