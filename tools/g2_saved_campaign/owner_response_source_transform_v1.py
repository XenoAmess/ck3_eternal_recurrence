"""Strict source-only transformation for a future qualified owner generation."""
from __future__ import annotations

import ast
import hashlib
import re

EXPECTED_ROW = '''row = {"started_at_utc": started, "ended_at_utc": now().isoformat(),
"elapsed_seconds": time.monotonic() - mono, "request": request, "result": dumped,
"mcp_result_projection_json_utf8_bytes": len(json.dumps(dumped, ensure_ascii=False,
separators=(",", ":")).encode("utf-8"))}'''


def transform_owner_source_v1(source: bytes, *, expected_source_sha256: str,
                              helper_module: str = "owner_response_json_once_v1") -> bytes:
    """Only replace success encoding and split the existing local atomic writer.

    Root must bind the actual future source hash/helper pin in its normal source
    closure.  This function grants no owner, SDK or Native runtime qualification.
    No import or execution of the supplied owner module occurs.
    """
    if hashlib.sha256(source).hexdigest() != expected_source_sha256:
        raise ValueError("actual owner source SHA mismatch")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", helper_module):
        raise ValueError("one explicit helper module identifier required")
    text = source.decode("utf-8-sig")
    tree = ast.parse(text)
    if any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in {
            "atomic_payload_v1", "_owner_response_success_row_once_v1"} for n in ast.walk(tree)):
        raise ValueError("owner already contains candidate symbol")
    atomics = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "atomic"]
    expected_row = ast.parse(EXPECTED_ROW).body[0]
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef) and n.name == "call"
             and any(isinstance(row, ast.Assign) and ast.dump(row) == ast.dump(expected_row)
                     for row in ast.walk(n))]
    if len(atomics) != 1 or len(calls) != 1:
        raise ValueError("one original atomic and owner call required")
    atomic, call = atomics[0], calls[0]
    expected_atomic = ast.parse('''def atomic(path, value, *, replace=False, limit=REPLY_RESERVE):
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
''').body[0]
    if (ast.dump(atomic.args) != ast.dump(expected_atomic.args)
            or ast.dump(atomic.body[0]) != ast.dump(expected_atomic.body[0])):
        raise ValueError("original atomic encoder contract differs")
    rows = [n for n in ast.walk(call) if isinstance(n, ast.Assign)
            and ast.dump(n) == ast.dump(expected_row)]
    writes = [n for n in ast.walk(call) if isinstance(n, ast.Expr)
              and ast.dump(n) == ast.dump(ast.parse("atomic(response, row)").body[0])]
    if len(rows) != 1 or len(writes) != 1:
        raise ValueError("original successful row/write contract differs")
    row, write = rows[0], writes[0]
    tries = [n for n in ast.walk(call) if isinstance(n, ast.Try) and row in n.body]
    if len(tries) != 1 or len(tries[0].handlers) != 1:
        raise ValueError("original RPC unknown-outcome boundary differs")
    attempt = tries[0]
    if not isinstance(attempt.handlers[0].type, ast.Name) or attempt.handlers[0].type.id != "Exception":
        raise ValueError("original RPC exception handler differs")

    newline = "\r\n" if b"\r\n" in source else "\n"
    lines = text.splitlines(keepends=True)
    changes = []

    def segment(node):
        return "".join(lines[node.lineno - 1:node.end_lineno])

    original_atomic = segment(atomic)
    original_header = lines[atomic.lineno - 1]
    original_payload = segment(atomic.body[0])
    payload_atomic = original_atomic.replace("def atomic(path, value,", "def atomic_payload_v1(path, payload,", 1)
    payload_atomic = payload_atomic.replace(original_payload,
        "    if not isinstance(payload, bytes):" + newline
        + "        raise TypeError('atomic payload must be bytes')" + newline, 1)
    wrapper = (f"from {helper_module} import prepare_success_response_row_v1 as _owner_response_success_row_once_v1" + newline
               + newline + original_header
               + "    payload = json.dumps(value, ensure_ascii=False, separators=(\",\", \":\")).encode(\"utf-8\")" + newline
               + "    return atomic_payload_v1(path, payload, replace=replace, limit=limit)" + newline
               + newline + payload_atomic)
    changes.append((atomic.lineno - 1, atomic.end_lineno, wrapper))
    row_indent = " " * row.col_offset
    row_new = (row_indent + "row, response_payload = _owner_response_success_row_once_v1(" + newline
               + row_indent + "    started_at_utc=started, ended_at_utc=now().isoformat()," + newline
               + row_indent + "    elapsed_seconds=time.monotonic() - mono, request=request, result=dumped)" + newline)
    changes.append((row.lineno - 1, row.end_lineno, row_new))
    try_indent = " " * attempt.col_offset
    changes.append((attempt.lineno - 1, attempt.lineno - 1,
                    try_indent + "response_payload = None" + newline))
    write_indent = " " * write.col_offset
    write_new = (write_indent + "if response_payload is None:" + newline
                 + write_indent + "    atomic(response, row)" + newline
                 + write_indent + "else:" + newline
                 + write_indent + "    atomic_payload_v1(response, response_payload)" + newline)
    changes.append((write.lineno - 1, write.end_lineno, write_new))
    for start, end, replacement in sorted(changes, reverse=True):
        lines[start:end] = [replacement]
    transformed = "".join(lines)
    ast.parse(transformed)
    result = transformed.encode("utf-8")
    return (b"\xef\xbb\xbf" if source.startswith(b"\xef\xbb\xbf") else b"") + result
