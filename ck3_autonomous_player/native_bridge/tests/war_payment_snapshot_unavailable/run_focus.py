from pathlib import Path
import argparse,json,subprocess,sys
sys.dont_write_bytecode=True
p=argparse.ArgumentParser();p.add_argument("--repo",type=Path,required=True);p.add_argument("--exe",type=Path,required=True);a=p.parse_args()
sys.path.insert(0,str(a.repo.resolve()))
from tools.ck3_live_run_id import current_machine_id
machine=current_machine_id()
argv=[str(a.exe.resolve()),"--machine-id",machine]
r=subprocess.run(argv,capture_output=True,text=True,encoding="utf-8",timeout=30)
sys.stdout.write(r.stdout);sys.stderr.write(r.stderr)
rows=[json.loads(x) for x in r.stdout.splitlines() if x.strip()]
summary=next((x for x in reversed(rows) if x.get("summary")),None)
ok=r.returncode==0 and summary is not None and summary.get("checks")==65 and summary.get("failures")==0 and all(x.get("machine_id")==machine for x in rows)
raise SystemExit(0 if ok else 1)
