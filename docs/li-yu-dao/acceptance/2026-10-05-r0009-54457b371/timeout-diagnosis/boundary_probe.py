import hashlib
import importlib.metadata
import json
from pathlib import Path

out=Path(__file__).parent
report={}
for snap in ('snapshot-001','snapshot-002'):
    m=json.loads((out/snap/'capture-manifest.json').read_text(encoding='utf-8'))
    report[snap]={v['relative']:{'bytes':v['copied_bytes'],'sha256':v['sha256']} for v in m['files'] if v['relative'].endswith(('server.stderr.log','stdout.bin','driver-state.json'))}
    for v in m['files']:
        if v['relative'].endswith('server.stderr.log'):
            lines=(out/snap/v['relative']).read_text(encoding='utf-8',errors='replace').splitlines()
            report[snap]['server_stderr_line_count']=len(lines)
            report[snap]['server_stderr_tail']=lines[-10:]
report['sdk_sources']=[]
dist=importlib.metadata.distribution('mcp')
for file in dist.files:
    normalized=str(file).replace('\\','/')
    if normalized in ('mcp/client/stdio/__init__.py','mcp/shared/session.py','mcp/server/mcpserver.py','mcp/server/stdio.py') or normalized.endswith('mcp/server/mcpserver/server.py'):
        path=Path(dist.locate_file(file))
        report['sdk_sources'].append({'path':str(path),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
native=out/'snapshot-002/native-evidence/8ffcb8420953481eade4610f3ff61781/0056-snapshot.json'
value=json.loads(native.read_text(encoding='utf-8'))
report['snapshot_diagnostics']=value['snapshot']['diagnostics']
report['confirm_claims']={}
for path in (out/'snapshot-002/native-state/native-session/ingame-decision-item-actions').glob('*'):
    if path.stat().st_size<6000:
        report['confirm_claims'][path.name]=json.loads(path.read_text(encoding='utf-8'))
(out/'boundary-analysis.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
