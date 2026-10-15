"""Prepare a new external queue; never import or edit the source runtime."""
from pathlib import Path
import argparse,ast,hashlib,json
def transform(payload):
    text=payload.decode('utf-8-sig');tree=ast.parse(text)
    if not any(isinstance(n,ast.Import) and any(a.name=='os' and a.asname is None for a in n.names) for n in tree.body):
        raise ValueError('existing os import required')
    found=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='artifact_bytes']
    if len(found)!=1:raise ValueError('exact one artifact_bytes method required')
    node=found[0]
    ret=node.body[-1]
    if not isinstance(ret,ast.Return) or not isinstance(ret.value,ast.Call) or not isinstance(ret.value.func,ast.Name) or ret.value.func.id!='sum':
        raise ValueError('original flat sum contract differs')
    gen=ret.value.args[0]
    if not isinstance(gen,ast.GeneratorExp) or len(gen.generators)!=2:
        raise ValueError('original flat directory comprehension differs')
    roots=gen.generators[0].iter
    if not isinstance(roots,ast.Tuple) or len(roots.elts)!=4:
        raise ValueError('four original attempt roots required')
    if ast.unparse(gen.generators[1].iter)!='root.iterdir()':
        raise ValueError('original directory walk differs')
    expected=ast.parse('def artifact_bytes(self):\n    return sum(path.stat().st_size for root in '+ast.unparse(roots)+' if root.is_dir() for path in root.iterdir() if path.is_file())\n').body[0]
    if ast.dump(node)!=ast.dump(expected):
        raise ValueError('exact original flat file accounting contract required')
    body='''def artifact_bytes(self):
    # Same four flat attempt roots; fresh enumeration, no retained byte cache.
    total = 0
    for root in ROOTS:
        if root.is_dir():
            with os.scandir(root) as entries:
                for entry in entries:
                    if entry.is_file(follow_symlinks=False):
                        total += entry.stat(follow_symlinks=False).st_size
    return total
'''.replace('ROOTS',ast.unparse(roots))
    replacement=ast.parse(body).body[0]
    lines=text.splitlines(True)
    indent=' '*node.col_offset
    lines[node.lineno-1:node.end_lineno]=[indent+line if line.strip() else line for line in body.splitlines(True)]
    result=''.join(lines);after=ast.parse(result)
    # Replacing only this method must preserve the rest of the module AST.
    for parent in ast.walk(tree):
        if hasattr(parent,'body') and isinstance(parent.body,list):
            parent.body=[replacement if n is node else n for n in parent.body]
    if ast.dump(tree)!=ast.dump(after):
        raise ValueError('something outside the one method changed')
    return result.encode('utf-8')
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.input.resolve()==a.output.resolve():raise ValueError('source/runtime overwrite is forbidden')
    payload=a.input.read_bytes();result=transform(payload)
    with a.output.open('xb') as f:f.write(result)
    print(json.dumps({'source':str(a.input),'source_sha256':hashlib.sha256(payload).hexdigest(),'candidate':str(a.output),
      'candidate_sha256':hashlib.sha256(result).hexdigest(),'only_function_changed':'artifact_bytes',
      'flat_roots_preserved':True,'no_follow_links':True,'cap_and_volume_guards_changed':False}))
if __name__=='__main__':main()
