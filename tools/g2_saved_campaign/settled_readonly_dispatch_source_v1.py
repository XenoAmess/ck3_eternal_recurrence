"""Clear stale successful readonly caller context before a clean local control."""
from __future__ import annotations
import ast
import copy
import hashlib

C3_QUEUE_SHA = '18bfcbe93b17c625b80fa2701a29e44229f2a554b5daee75c32544c677e9c2b6'

GUARD = '''
if command is not None and getattr(queue, "halted", None) is None:
    dispatch_state = getattr(queue, "full_loop_state", None)
    dispatch_attempt = getattr(queue, "current_attempt", None)
    if isinstance(dispatch_state, dict) and isinstance(dispatch_attempt, dict):
        dispatch_row = dispatch_attempt.get("row")
        dispatch_request = dispatch_attempt.get("request")
        if (all(dispatch_state.get(k) is None for k in ("pending_cycle", "pending_checkpoint",
                "terminal", "pending_natural_succession", "pending_unsafe_route_halt"))
                and isinstance(dispatch_request, dict) and isinstance(dispatch_row, dict)
                and dispatch_request.get("tool") in {SEMANTIC, METRICS}
                and dispatch_row.get("request") == dispatch_request
                and dispatch_row.get("client_error") is None
                and isinstance(dispatch_row.get("result"), dict)
                and dispatch_row["result"].get("result_type") == "complete"
                and dispatch_row["result"].get("is_error") is False):
            queue.current_attempt = None
'''


def transform(raw, *, expected_sha256=C3_QUEUE_SHA):
    if len(raw) > 1024**2 or hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError('Exact reviewed owner Queue source required')
    source = raw.decode('utf-8-sig')
    tree = ast.parse(source)
    loop = next(node for node in tree.body if isinstance(node, ast.AsyncFunctionDef)
        and node.name == 'run_request_loop')
    assignments = [node for node in ast.walk(loop) if isinstance(node, ast.Assign)
        and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == 'command']
    if len(assignments) != 1 or ast.unparse(assignments[0].value) != "request.get('command')":
        raise ValueError('One reviewed local dispatch seam required')
    anchor = assignments[0]
    lines = source.splitlines(keepends=True)
    indent = lines[anchor.lineno - 1][:anchor.col_offset]
    block = ''.join(indent + line + '\n' if line else '\n' for line in GUARD.strip().splitlines())
    lines.insert(anchor.end_lineno, block)
    changed = ''.join(lines).encode('utf-8')
    expected = copy.deepcopy(tree)
    expected_loop = next(node for node in expected.body if isinstance(node, ast.AsyncFunctionDef)
        and node.name == 'run_request_loop')
    def inject(node):
        for _, value in ast.iter_fields(node):
            if isinstance(value, list):
                for i, child in enumerate(list(value)):
                    if isinstance(child, ast.Assign) and child.lineno == anchor.lineno:
                        value.insert(i + 1, ast.parse(GUARD).body[0])
                        return True
                    if isinstance(child, ast.AST) and inject(child):
                        return True
            elif isinstance(value, ast.AST) and inject(value):
                return True
        return False
    if not inject(expected_loop) or ast.dump(expected) != ast.dump(ast.parse(changed)):
        raise AssertionError('Source changed beyond the one clean readonly caller guard')
    return changed
