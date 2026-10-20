"""Patch only the pinned decoder function in a future Queue source."""
from __future__ import annotations

import ast
import hashlib

OLD_BYTES = 860
OLD_SHA256 = "9256c2059269d892ee14d4cdc0e7835d2ea0f7f6162525410d6a6532e7fca1ba"
NEW_BYTES = 996
NEW_SHA256 = "745bff4ba6d5e2b561144bf70a79bae5ddd34332402ed078bfdddca916e5098d"
SEAM = b'    value = result.get("structured_content", result.get("structuredContent"))'
INSERT = (
    b"    from xar_autoplayer.bridge.mcp_tool_result_contract_v1 import require_complete_tool_result\n"
    b"    require_complete_tool_result(result)\n"
)


def transform(source: bytes) -> bytes:
    """Return new UTF-8 source; preserve every byte outside the known function."""
    if type(source) is not bytes or not source or len(source) > 1024 * 1024:
        raise ValueError("bounded Queue source bytes required")
    tree = ast.parse(source.decode("utf-8"))
    matches = [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "decoded"
    ]
    if len(matches) != 1:
        raise ValueError("exactly one decoded function required")
    node = matches[0]
    if (not isinstance(node, ast.FunctionDef) or node.col_offset != 0
            or node.decorator_list or node.end_lineno is None):
        raise ValueError("one top-level synchronous decoder required")
    lines = source.splitlines(keepends=True)
    start = sum(len(line) for line in lines[:node.lineno - 1])
    end = sum(len(line) for line in lines[:node.end_lineno])
    original = source[start:end]
    if len(original) != OLD_BYTES or hashlib.sha256(original).hexdigest() != OLD_SHA256:
        raise ValueError("foreign or already patched decoded function")
    if original.count(SEAM) != 1:
        raise ValueError("one exact decoded body seam required")
    replacement = original.replace(SEAM, INSERT + SEAM, 1)
    if len(replacement) != NEW_BYTES or hashlib.sha256(replacement).hexdigest() != NEW_SHA256:
        raise ValueError("decoder postimage differs")
    result = source[:start] + replacement + source[end:]
    compile(result, "<future-complete-Queue>", "exec")
    return result
