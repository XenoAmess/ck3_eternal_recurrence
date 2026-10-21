"""Actual source checks only. Does not call the media runner or open raw body."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path("C:/ck3-e04-resume-20261020-a01/r03-r191-continuous-review-2245-a01")
SOURCE = ROOT/"source"
CHECKS = SOURCE/"checks"
def pin(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {"path":str(path),"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()}

def one(name: str, argv: list[str]) -> int:
    environment = dict(os.environ)
    environment.update({"PYTHONPATH":"C:/ck3-e04-resume-20261020-a01/r08-mypy1201-tools-2115-a01/Lib",
                        "PYTHONDONTWRITEBYTECODE":"1","TMP":str(CHECKS),"TEMP":str(CHECKS),
                        "PYTHONIOENCODING":"utf-8"})
    before = [pin(path) for path in SOURCE.glob("*.py")]
    started = datetime.now(timezone.utc).isoformat()
    proc: subprocess.Popen[bytes] = subprocess.Popen(argv,cwd=SOURCE,env=environment,
        stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW)
    timed_out = False
    try:
        stdout, stderr = proc.communicate(timeout=90)
    except subprocess.TimeoutExpired:
        timed_out = True
        proc.kill()
        stdout, stderr = proc.communicate()
    code = proc.wait()
    for suffix, data in [("stdout.txt",stdout),("stderr.txt",stderr)]:
        with (CHECKS/(name+"."+suffix)).open("xb") as stream:
            stream.write(data)
    receipt = {"machine_id":"desktop-3fevhd2-1c74096080","started_at_utc":started,
               "observed_at_utc":datetime.now(timezone.utc).isoformat(),"argv":argv,
               "original_Popen_pid":proc.pid,"original_wait_returncode":code,
               "timed_out":timed_out,"owned_process_alive":proc.poll() is None,
               "source_inputs_before":before,
               "stdout":pin(CHECKS/(name+".stdout.txt")),"stderr":pin(CHECKS/(name+".stderr.txt")),
               "raw_media_opened":False,"FFmpeg_probe_game_SDK_UI_calls":0}
    with (CHECKS/(name+".actual.json")).open("x",encoding="utf-8") as stream:
        json.dump(receipt,stream,ensure_ascii=True,separators=(",",":"))
    print(json.dumps(receipt))
    return code

def main(argv: list[str]) -> int:
    if len(argv)!=2 or argv[0] not in ("mypy","tests"):
        raise SystemExit("Usage: run_source_checks.py mypy|tests unique-name")
    CHECKS.mkdir(exist_ok=True)
    mode,name=argv
    if mode=="mypy":
        targets=[str(path) for path in SOURCE.glob("*.py")]
        command=[sys.executable,"-B","-X","utf8","-m","mypy","--config-file",str(CHECKS/"mypy.ini"),
                 "--no-incremental","--cache-dir","nul","--python-version","3.14","--platform","win32",
                 "--check-untyped-defs","--disallow-untyped-defs",*targets]
    else:
        command=[sys.executable,"-B","-X","utf8","-m","unittest","-v","test_r03_pipeline"]
    return one(name,command)
if __name__=="__main__":
    sys.exit(main(sys.argv[1:]))
