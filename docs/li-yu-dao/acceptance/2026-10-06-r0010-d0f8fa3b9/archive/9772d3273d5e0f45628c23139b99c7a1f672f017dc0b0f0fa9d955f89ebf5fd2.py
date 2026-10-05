from pathlib import Path
import hashlib,json
B=Path('C:/workspace/ck3_lyd_runtime_20261004');M=Path('C:/workspace/ck3_eternal_recurrence/mod_li_yu_dao')
C2=B/'c2-preview-scopefix-full-candidate-20261005-003'
def sha(d):return hashlib.sha256(d).hexdigest()
v=json.loads((C2/'DELTA.json').read_bytes())
for row in v['scope_relative_to_ready_candidate']['authored']:
    if Path(row['path']).name.startswith('test_'):continue
    a=Path(row['after_ref']).read_bytes();b=(M/row['path']).read_bytes()
    print('C2AUTHOR',row['path'],'SOURCE_SHA',sha(a),'CURRENT_SHA',sha(b),'SOURCE_CRLF',a.count(b'\r\n'),'CURRENT_CRLF',b.count(b'\r\n'),
          'LF_NORMALIZED_EXACT',a.replace(b'\r\n',b'\n')==b)
for rel in ['r9-root-c2-lf-canonicalization-20261005-001','r9-root-c2-presence-apply-20261005-001']:
    p=B/rel;print('DIRECTORY',rel,[f.name for f in p.iterdir()])
    for path in p.glob('*.json'):
        raw=path.read_bytes();v=json.loads(raw);print('RECEIPT',path.name,len(raw),sha(raw),'KEYS',list(v))
        print(json.dumps(v,ensure_ascii=False)[:2500])
