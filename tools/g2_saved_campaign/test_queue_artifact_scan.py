"""Portable file-accounting checks; no Game/SDK/OBS/process calls."""
from pathlib import Path
from types import SimpleNamespace
import ast,hashlib,importlib.util,json,os,tempfile
import prepare_queue_artifact_scan as patcher

BASE=Path(__file__).resolve().parent
FIXTURE=BASE/'fixtures/queue_artifact_scan.py'

def counter(class_name,env):
    tree=ast.parse(FIXTURE.read_text(encoding='utf-8'))
    cls=next(c for c in tree.body if isinstance(c,ast.ClassDef) and c.name==class_name)
    fn=next(f for f in cls.body if isinstance(f,ast.FunctionDef) and f.name=='artifact_bytes')
    exec(compile(ast.Module(body=[fn],type_ignores=[]),str(FIXTURE),'exec'),env)
    return env['artifact_bytes']

def main():
    checks=[]
    with tempfile.TemporaryDirectory(prefix='artifact-scan-offline-',dir=BASE) as directory:
        n=Path(directory).resolve()
        assert n.is_relative_to(BASE) and n.name.startswith('artifact-scan-offline-')
        roots=[n/'in',n/'out',n/'p11-display-responses',n/'q']
        for root in roots:root.mkdir()
        for i,root in enumerate(roots):(root/'small.json').write_bytes(b'x'*(i+1))
        (roots[0]/'nested').mkdir();(roots[0]/'nested/ignored.json').write_bytes(b'ignored')
        (n/'p12-display-responses').mkdir()
        (n/'p12-display-responses/small.json').write_bytes(b'x'*3)
        env={'INBOX':roots[0],'OUTBOX':roots[1],'N':n,'Q':roots[3],'os':os}
        old=counter('BeforeQueueFixture',dict(env))
        new=counter('P12QueueFixture',dict(env))
        assert old(None)==new(None)==10
        (roots[1]/'small.json').write_bytes(b'x'*100)
        assert old(None)==new(None)==108
    checks.append({'name':'flat totals match, nested files remain outside original scope, next scan sees resized file','status':'GREEN'})
    calls=[]
    class Entry:
        def __init__(self,file):self.file=file
        def is_file(self,*,follow_symlinks):
            assert follow_symlinks is False;return self.file
        def stat(self,*,follow_symlinks):
            assert follow_symlinks is False and self.file;calls.append('stat')
            return SimpleNamespace(st_size=7)
    class Scan:
        def __enter__(self):return iter([Entry(True),Entry(False)])
        def __exit__(self,*args):pass
    class Root:
        def is_dir(self):return True
        def __truediv__(self,name):return self
    env={'INBOX':Root(),'OUTBOX':Root(),'N':Root(),'Q':Root(),'os':SimpleNamespace(scandir=lambda root:Scan())}
    assert counter('P12QueueFixture',env)(None)==28 and len(calls)==4
    checks.append({'name':'nofollow flags required, skipped entry is never statted, one DirEntry stat per counted file','status':'GREEN'})
    tree=ast.parse(FIXTURE.read_text(encoding='utf-8'))
    before=next(c for c in tree.body if isinstance(c,ast.ClassDef) and c.name=='BeforeQueueFixture')
    payload=ast.unparse(ast.Module(body=[ast.Import(names=[ast.alias(name='os')]),before],type_ignores=[])).encode()
    malformed=payload.decode().replace(' if path.is_file()', '')
    try:patcher.transform(malformed.encode())
    except ValueError:pass
    else:raise AssertionError('altered accounting contract must be rejected')
    changed=patcher.transform(payload)
    patched=next(f for f in ast.walk(ast.parse(changed)) if isinstance(f,ast.FunctionDef) and f.name=='artifact_bytes')
    after=next(c for c in tree.body if isinstance(c,ast.ClassDef) and c.name=='P12QueueFixture')
    actual=next(f for f in after.body if isinstance(f,ast.FunctionDef) and f.name=='artifact_bytes')
    for node in ast.walk(actual):
        if isinstance(node,ast.Constant) and node.value=='p12-display-responses':
            node.value='p11-display-responses'
    assert ast.dump(patched)==ast.dump(actual)
    provenance=json.loads((BASE/'fixtures/queue_artifact_scan_provenance.json').read_text(encoding='utf-8'))
    checks.append({'name':'generic patch preserves caller roots and yields exact frozen P12 method AST after prefix adaptation','status':'GREEN',
                   'source_queue_sha256':provenance['source_methods'][1]['source_sha256']})
    print(json.dumps({'status':'GREEN','checks':checks,'runtime_calls':0}))
if __name__=='__main__':main()
