from pathlib import Path
import hashlib, json, subprocess
root = Path('C:/workspace/ck3_eternal_recurrence').resolve()
out = Path(__file__).parent / 'NEW-TEXT-LF.actual.json'
assert not out.exists()
paths = subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z'], cwd=root).decode('utf-8').split('\0')
rows=[]
for rel in paths:
    if not rel or not (rel.startswith('mod_li_yu_dao/tools/') or rel.startswith('tools/lyd_i3b_checkpoint_readback/') or rel.startswith('docs/li-yu-dao/')):
        continue
    path = (root / rel).resolve()
    assert path.is_relative_to(root)
    if path.suffix not in ('.py','.json','.md') or '/acceptance/' in rel:
        continue
    before=path.read_bytes()
    before.decode('utf-8-sig')
    if b'\r\n' not in before:
        continue
    assert 'saved_faith_semantics_12003.json' not in rel, 'Hash-bound semantics file needs explicit review'
    assert b'GENERATED FILE' not in before[:256], 'Generator must own generated source'
    after=before.replace(b'\r\n', b'\n')
    path.write_bytes(after)
    rows.append({'path':rel,'before_bytes':len(before),'before_sha256':hashlib.sha256(before).hexdigest(),'after_bytes':len(after),'after_sha256':hashlib.sha256(after).hexdigest()})
out.write_text(json.dumps({'schema':'lyd.new-source-canonical-LF.v1','changes':rows,'historical_raw_files_changed':False,'generated_files_changed':False},ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'receipt':str(out),'changed_files':len(rows),'paths':[r['path'] for r in rows]},ensure_ascii=False))
