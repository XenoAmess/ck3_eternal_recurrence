from pathlib import Path
import json
R=Path('C:/workspace/ck3_lyd_runtime_20261004/live-attempt-017')
p=R/'mcp-client-001/ready.json';v=json.loads(p.read_bytes());print('READY',json.dumps(v,ensure_ascii=False))
for d in ['mcp-client-001','native-evidence','root-initial-requests-001']:
 p=R/d
 if p.exists():
  for q in sorted(p.iterdir()):
   if q.is_file():print('FILE',q.name,q.stat().st_size)
for p in R.iterdir():
 if p.is_file():print('ROOTFILE',p.name,p.stat().st_size)
