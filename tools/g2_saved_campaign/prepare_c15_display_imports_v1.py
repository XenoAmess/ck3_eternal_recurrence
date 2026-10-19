"""Four display imports and one current-recording pointer before C15 startup."""
import ast
import hashlib
from pathlib import Path

T = Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime')
INPUTS = {
    'root_p37c15_sdk_queue.py': ('04d94805f25ef4ff95c02c161b62ca4eb09957e19949123f6d3191bd83b762e9',
        'root_p37c11_overlay_relay', 'root_p37c15_overlay_relay', 3),
    'root_p37c15_mcp_entry.py': ('0bf791d80bbe9509497f156acffab9d3752709955b74aa17a5ed111919b2b3f0',
        'root_p37c11_compact_decision_feed', 'root_p37c15_compact_decision_feed', 1),
}


def build_sources():
    outputs = {}
    for name, (digest, before, after, count) in INPUTS.items():
        raw = (T/name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError('different still-unloaded C15 source: ' + name)
        tree = ast.parse(raw)
        nodes = [node for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module == before]
        if len(nodes) != count or raw.count(('from '+before+' import ').encode()) != count:
            raise ValueError('different exact C15 display-import seam')
        changed = raw.replace(('from '+before+' import ').encode(), ('from '+after+' import ').encode())
        for node in nodes:
            node.module = after
        pointer_before = b'ROOT-CURRENT-OBS-RECORDING-REQUESTED-C6.json'
        pointer_after = b'ROOT-CURRENT-OBS-RECORDING-REQUESTED-C15.json'
        if name == 'root_p37c15_sdk_queue.py':
            pointers = [node for node in ast.walk(tree) if isinstance(node, ast.Constant)
                and node.value == pointer_before.decode()]
            if len(pointers) != 1 or raw.count(pointer_before) != 1:
                raise ValueError('different single old current-recording pointer')
            pointers[0].value = pointer_after.decode()
            changed = changed.replace(pointer_before, pointer_after, 1)
        if ast.dump(ast.parse(changed), include_attributes=False) != ast.dump(tree, include_attributes=False):
            raise ValueError('display import changed another AST field')
        inverse = changed.replace(('from '+after+' import ').encode(), ('from '+before+' import ').encode())
        if name == 'root_p37c15_sdk_queue.py':
            inverse = inverse.replace(pointer_after, pointer_before, 1)
        if inverse != raw:
            raise ValueError('non-import source byte change')
        compile(changed, name, 'exec')
        outputs[name] = changed
    return outputs
