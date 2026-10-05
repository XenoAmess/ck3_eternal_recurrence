import hashlib
import importlib.metadata
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

out=Path(__file__).parent
versions={}
for name in ('fastmcp','mcp'):
    try:
        versions[name]=importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        versions[name]='distribution metadata absent; server not imported or executed'
report={'versions':versions, 'files':[], 'calls':[], 'observed_at_utc':datetime.now().astimezone().isoformat()}
for snap in ('snapshot-001','snapshot-002'):
    manifest=json.loads((out/snap/'capture-manifest.json').read_text(encoding='utf-8'))
    report['files'].extend([{'snapshot':snap,'path':v['relative'],'bytes':v['copied_bytes'],'sha256':v['sha256']} for v in manifest['files']])
    for p in (out/snap/'mcp-client-evidence-001').glob('*.response.json'):
        response=json.loads(p.read_text(encoding='utf-8'))
        start=datetime.fromisoformat(response['started_at_utc'])
        finish=datetime.fromisoformat(response['finished_at_utc'])
        row={'sequence':response['sequence'],'status':response['status'],'started_at_utc':response['started_at_utc'],'finished_at_utc':response['finished_at_utc'],'elapsed_seconds':(finish-start).total_seconds(),'request_sha256':response['request_sha256']}
        if response.get('sdk_result'):
            sdk=json.loads((p.parent/response['sdk_result']).read_text(encoding='utf-8'))
            row['sdk_saved_bytes']=(p.parent/response['sdk_result']).stat().st_size
            row['sdk_top_keys']=list(sdk)
            row['sdk_top_compact_json_bytes']={k:len(json.dumps(v,ensure_ascii=False).encode('utf-8')) for k,v in sdk.items()}
            content=sdk.get('content',[])
            row['text_content_bytes']=[len(v.get('text','').encode('utf-8')) for v in content if isinstance(v,dict) and v.get('type')=='text']
            row['text_structured_same_data']=[json.loads(v['text'])==sdk.get('structuredContent') for v in content if isinstance(v,dict) and v.get('type')=='text']
        report['calls'].append(row)
history=json.loads((out/'snapshot-001/native-state/native-session/driver-state.json').read_text(encoding='utf-8'))['command_history']
report['driver_history_compact_bytes']=len(json.dumps(history,ensure_ascii=False).encode('utf-8'))
report['driver_history_entries']=[{'index':entry['index'],'command':entry['command'],'compact_bytes':len(json.dumps(entry,ensure_ascii=False).encode('utf-8'))} for entry in history]
report['native_receipts']=[]
for p in (out/'snapshot-002/native-evidence/8ffcb8420953481eade4610f3ff61781').glob('*.json'):
    receipt=json.loads(p.read_text(encoding='utf-8'))
    fields={k:len(json.dumps(v,ensure_ascii=False).encode('utf-8')) for k,v in receipt.items()}
    nested=[]
    def walk(v,path='',depth=0):
        if isinstance(v,dict):
            for k,child in v.items():
                if k=='native_command_history':
                    nested.append({'path':path+'/'+k,'length':len(child),'depth':depth})
                walk(child,path+'/'+k,depth+1)
        elif isinstance(v,list):
            for index,child in enumerate(v):
                walk(child,path+'/'+str(index),depth+1)
    walk(receipt)
    row={'path':str(p.relative_to(out)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'status':receipt.get('status'),'recorded_at_utc':receipt.get('recorded_at_utc'),'top_field_compact_bytes':fields,'nested_native_command_history_occurrences':len(nested),'max_history_nesting_depth':max(v['depth'] for v in nested),'nested_history_top_paths':nested[:12]}
    report['native_receipts'].append(row)
report['calls'].sort(key=lambda v:v['sequence'])
(out/'size-analysis.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'versions':report['versions'],'calls':report['calls'],'native_receipts':report['native_receipts'],'driver_history_compact_bytes':report['driver_history_compact_bytes'],'largest_history_entries':sorted(report['driver_history_entries'],key=lambda v:-v['compact_bytes'])[:8]},ensure_ascii=False,indent=2))
