from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parent.parent
RUN = ROOT/'live-attempt-006'

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def info(p):
    b = p.read_bytes()
    return {'path': str(p), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}

for name in ['r6-report-draft-001', 'r6-report-draft-addendum-001', 'r6-report-draft-addendum-003', 'r6-i2-resources-readback-001', 'r6-event-readback-resume-20261005-001']:
    p = ROOT/name
    ix = p/'INDEX.json'
    row = {'package': name, 'index_present': ix.exists(), 'direct_files': [f.name for f in p.iterdir() if f.is_file()]}
    if ix.exists():
        obj = read(ix)
        row.update(index=info(ix), indexed_files=len(obj['files']), indexed_bytes=sum(r['bytes'] for r in obj['files']))
    print(json.dumps(row, ensure_ascii=False))

for seq, label in [(38, '0037-i2-resources-snapshot'), (39, '0038-i2-resources-fresh'), (40, '0039-i2-resources-ack'), (41, '0040-i2-resources-save'), (42, '0041-i2-detach-open-snapshot'), (43, '0042-i2-detach-open-save'), (44, '0043-i2-detach-source-yes'), (45, '0044-i2-detach-source-yes-save')]:
    prefix = f'{seq:04d}-{label}'
    p = RUN/'mcp-client-evidence'/(prefix+'.sdk-result.json')
    obj = read(p)
    s = obj.get('structuredContent', {})
    row = {'sdk': info(p), 'sdk_top_keys': list(obj), 'structured_keys': list(s), 'isError':obj.get('isError')}
    for key in ['status', 'result', 'snapshot_before', 'snapshot_after']:
        val = s.get(key)
        if key == 'result' and isinstance(val, dict):
            row[key] = {k: val.get(k) for k in ['status','event_selection','checkpoint','submission'] if k in val}
        elif key.startswith('snapshot') and isinstance(val, dict):
            row[key] = {k:val.get(k) for k in ['snapshot_id','revision','date_raw','paused','active_event','played_character_gold','played_character_piety'] if k in val}
        else:
            row[key] = val
    print(json.dumps(row, ensure_ascii=False))

for label in ['0040-i2-resources-save', '0042-i2-detach-open-save', '0044-i2-detach-source-yes-save']:
    p = RUN/'checkpoints'/label/'receipt.json'
    obj = read(p)
    print(json.dumps({'checkpoint':label,'wrapper':info(p),'keys':list(obj),'values':{k:v for k,v in obj.items() if not isinstance(v,(dict,list))}}, ensure_ascii=False))

