from pathlib import Path
import ast
P=Path('C:/workspace/ck3_lyd_runtime_20261004/r10-claim-verifier-source-author-20261005-001')
text=(P/'author_source007-revision-002.py').read_text(encoding='utf-8')
tree=ast.parse(text)
for node in tree.body:
    if isinstance(node,ast.FunctionDef) and node.name=='inventory':print(ast.get_source_segment(text,node))
print('\n'.join(text.splitlines()[174:205]))
