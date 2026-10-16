"""Replay immutable R189 checks with explicit rejection even under python -O.

The two original verifiers remain unchanged and separately pinned. Only their
Assert nodes become If-not/Raise nodes before execution. All source paths are
relative to this package, unless the caller explicitly selects external roots.
"""
from pathlib import Path
import argparse,ast,hashlib,json

PINS = {'actual': {'bytes': 3095, 'sha256': 'ac5469bcecceba1b30dd5e854ae945c4391364671c3863a5ce9c3aafc762a993'}, 'source': {'bytes': 3178, 'sha256': '76267a3162fbd19d9a483ae061d182e67c4ab5e6d6746ae0feb81e34c6f31872'}}

class ExplicitChecks(ast.NodeTransformer):
    def __init__(self): self.count=0
    def visit_Assert(self,node):
        self.count+=1
        message=node.msg or ast.Constant('Frozen check failed at original line '+str(node.lineno))
        return ast.copy_location(ast.If(test=ast.UnaryOp(op=ast.Not(),operand=node.test),body=[ast.Raise(exc=ast.Call(func=ast.Name(id='ValueError',ctx=ast.Load()),args=[message],keywords=[]),cause=None)],orelse=[]),node)

def run_one(path,pin):
    data=path.read_bytes()
    if len(data)!=pin['bytes'] or hashlib.sha256(data).hexdigest()!=pin['sha256']:
        raise ValueError('Frozen verifier source pin differs: '+path.name)
    transform=ExplicitChecks();tree=transform.visit(ast.parse(data,filename=str(path)))
    ast.fix_missing_locations(tree)
    if not transform.count or any(isinstance(n,ast.Assert)for n in ast.walk(tree)):
        raise ValueError('Original check transformation differs')
    namespace={'__name__':'__main__','__file__':str(path)}
    exec(compile(tree,str(path),'exec',optimize=0),namespace)
    return dict(file=path.name,sha256=pin['sha256'],explicit_checks=transform.count)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    p.add_argument('--source-root',type=Path)
    a=p.parse_args();source=a.source_root or a.root/'source'
    results=[run_one(a.root/'verify_portable.py',PINS['actual']),run_one(source/'verify_source.py',PINS['source'])]
    print(json.dumps(dict(status='PASS_EXPLICIT_FROZEN_CHECKS',checks=results,offline_replay=True,new_live_observation=False,paid_or_receiver_credit_added=False)))
if __name__=='__main__':main()
