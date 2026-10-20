"""One fresh-base, two-environment qualification against actual closed receipts."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import traceback

CHILD = r'''
import importlib, importlib.util, hashlib, json, os, re, subprocess, sys
from pathlib import Path
p=json.load(sys.stdin)
assert Path(sys.executable).resolve()==Path(p["python"]).resolve()
assert os.environ.get("PYTHONDONTWRITEBYTECODE")=="1"
host=Path(p["host"]).resolve()
tools=str(host/"tools")
assert tools in os.environ["PYTHONPATH"].split(os.pathsep)
prefix=p["hotfix"].split("\nspec=importlib.util.spec_from_file_location(")
assert len(prefix)==2
exec(compile(prefix[0],p["hotfix_path"],"exec"),
     {"__file__":p["hotfix_path"],"__name__":"_actual_hotfix_prefix"})
assert tools in os.environ["PYTHONPATH"].split(os.pathsep)
assert tools in sys.path
capture_path=Path(p["capture"])
raw=capture_path.read_bytes()
assert len(raw)==73689 and hashlib.sha256(raw).hexdigest()==p["capture_sha"]
spec=importlib.util.spec_from_file_location("_closure_real_capture",capture_path)
capture=importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)
validator=importlib.import_module("ck3_capture_closed_receipt")
vp=Path(validator.__file__).resolve()
assert vp==host/"tools/ck3_capture_closed_receipt.py"
assert hashlib.sha256(vp.read_bytes()).hexdigest()==p["validator_sha"]
assert Path(capture.read_capture_closed_receipt.__code__.co_filename).resolve()==capture_path.resolve()
request=json.loads(Path(p["request"]).read_bytes())
launch=json.loads(Path(p["launch"]).read_bytes())
root=Path(request["receipt_root"]).resolve()
assert root.name==request["session_id"]==p["session_id"]
assert root.parent==Path(p["runtime"])/"recordings"
result=capture.read_capture_closed_receipt(
 root,session_id=request["session_id"],game_pid=launch["pid"],
 game_creation_filetime=launch["creation_filetime"],
 recording_worker_pid=request["worker_pid"],recording_root=root.parent)
assert result["status"]=="CAPTURE_CLOSED_VERIFIED"
assert result["video_body_read"] is False and result["process_or_Game_OBS_calls"]==0
completed_path=root/"completed.json"
assert completed_path.stat().st_size<=1048576
completed=json.loads(completed_path.read_bytes())
closed=json.loads((root/"capture_closed.json").read_bytes())
assert completed["state"]=="completed"
assert completed["path"]==closed["output_path"]
assert completed["bytes"]==closed["output_bytes"]==Path(closed["output_path"]).stat().st_size
assert re.fullmatch("[a-f0-9]{64}",completed["sha256"])
origins={"capture":str(capture_path.resolve()),"ck3_capture_closed_receipt":str(vp)}
for name in p["stdlib_imports"]:
 module=importlib.import_module(name)
 origin=Path(module.__file__).resolve()
 assert origin.is_relative_to(Path(sys.base_prefix).resolve())
 origins[name]=str(origin)
report={"layer":p["layer"],"python":str(Path(sys.executable).resolve()),
 "module_origins":origins,"post_prefix_pythonpath":os.environ["PYTHONPATH"],
 "validation":result,
 "completed_receipt_sha256":hashlib.sha256(completed_path.read_bytes()).hexdigest(),
 "media_bytes":completed["bytes"],"media_sha256_field":completed["sha256"],
 "media_body_bytes_read":0,"capture_validator_mocked":False}
if p["layer"]==0:
 child=dict(p,layer=1)
 run=subprocess.run([p["python"],"-B","-X","utf8","-c",p["child_code"]],
  input=json.dumps(child),text=True,encoding="utf-8",capture_output=True,
  cwd=p["runtime"],env=dict(os.environ),timeout=30,check=False,
  creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
 assert run.returncode==0,(run.returncode,run.stderr)
 nested=json.loads(run.stdout)
 assert nested["module_origins"]==origins
 assert nested["validation"]==result
 assert nested["post_prefix_pythonpath"]==report["post_prefix_pythonpath"]
 report["inherited_environment_layer"]=nested
print(json.dumps(report))
'''


def load(path):
    return json.loads(Path(path).read_bytes())


def pin(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def write_new(path, value):
    with Path(path).open("xb") as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("runtime", "frozen-host", "task-spec", "admission", "artifact-root", "proof"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--session-id", required=True)
    a = parser.parse_args()
    source = Path(__file__).with_name("prepare_recording_validator_closure_v1.py")
    spec = importlib.util.spec_from_file_location("_validator_closure_producer", source)
    producer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(producer)
    admission = load(a.admission)
    assert admission["machine_id"] == producer.MACHINE_ID
    assert admission["status"] == "SOURCE_AND_SYNTHETIC_QUALIFICATION_ADMITTED"
    assert datetime.now(timezone.utc) < datetime.fromisoformat(admission["review_at_utc"])
    task = load(a.task_spec)
    assert task["machine_id"] == producer.MACHINE_ID
    assert Path(task["cwd"]).resolve() == a.runtime.resolve()
    assert pin(task["stage"])["sha256"] == task["stage_sha256"]
    proof = {"schema": "xar.recording-validator-closure-qualification/v1",
             "machine_id": producer.MACHINE_ID, "observed_at_utc": datetime.now(timezone.utc).isoformat(),
             "admission": pin(a.admission), "original_Task_SPEC": pin(a.task_spec),
             "source_pins": [pin(source), pin(__file__)],
             "scope": "one local two-layer base-Python qualification; no Game/OBS/Task/desktop calls"}
    try:
        projection = producer.plan(runtime=a.runtime, frozen_host=a.frozen_host)
        blob = subprocess.check_output([
            "git", "-C", str(a.frozen_host), "show",
            producer.HOST_HEAD + ":tools/ck3_capture_closed_receipt.py"])
        assert hashlib.sha256(blob).hexdigest() == producer.VALIDATOR_SHA
        assert blob == (a.frozen_host / "tools/ck3_capture_closed_receipt.py").read_bytes()
        env = dict(os.environ)
        env.update(task["env"])
        env["PYTHONPATH"] = producer.pythonpath_v1(task["env"]["PYTHONPATH"], a.frozen_host)
        payload = {"python": task["python"], "runtime": str(a.runtime.resolve()),
                   "host": str(a.frozen_host.resolve()), "layer": 0,
                   "hotfix": projection["hotfix"].decode(),
                   "hotfix_path": str(a.runtime / "presentation-c23/hotfix_provider.py"),
                   "capture": str(a.runtime / "presentation-c23/ck3_obs_capture_png_retry_c23.py"),
                   "capture_sha": producer.CAPTURE_SHA, "validator_sha": producer.VALIDATOR_SHA,
                   "stdlib_imports": producer.STD_IMPORTS,
                   "request": str(a.runtime / "ROOT-OBS-RECORDING-REQUESTED-C23.json"),
                   "launch": str(a.runtime / "ROOT-ACTUAL-GAME-LAUNCH-C23.json"),
                   "session_id": a.session_id, "child_code": CHILD}
        run = subprocess.run([task["python"], "-B", "-X", "utf8", "-c", CHILD],
                             input=json.dumps(payload), text=True, encoding="utf-8",
                             capture_output=True, cwd=a.runtime, env=env, timeout=60,
                             check=False, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        assert run.returncode == 0, (run.returncode, run.stderr)
        detail = json.loads(run.stdout)
        staging = producer.prepare_staging(root=a.artifact_root / "projection", projection=projection)
        detail_path = a.artifact_root / "QUALIFICATION-DETAIL.json"
        write_new(detail_path, detail)
        proof.update(status="PASS", directbase_two_layers=2, validator_mocked=False,
                     frozen_validator_tracked_blob_exact=True, detail=pin(detail_path),
                     staged_projection=staging,
                     media_bytes=detail["media_bytes"], media_sha256_field=detail["media_sha256_field"],
                     video_body_bytes_read=0, media_finalization_rehashed=False,
                     closure_status=detail["validation"]["status"],
                     original_A04_stage_exit_preserved=1, actual_runtime_written=False,
                     limitation="Import/media validation closure verified; no new retained-worker/Task lifecycle claimed")
    except Exception:
        proof.update(status="FAILED", failure=traceback.format_exc()[-8000:],
                     actual_runtime_written=False)
        write_new(a.proof, proof)
        print(json.dumps({"status": proof["status"], "proof": pin(a.proof)}))
        raise
    write_new(a.proof, proof)
    print(json.dumps({"status": proof["status"], "proof": pin(a.proof),
                      "source_pins": proof["source_pins"], "staging": proof["staged_projection"]}))


if __name__ == "__main__":
    main()

