"""One reversible MCP error-return span; no output writer or runtime operations."""
import ast
import hashlib

ACTUAL_SHA = 'b4d2fab30a5c8cd8a0291c3759d9a0518b31df55698002d8ea6e7e64ad3bfb4a'
MASTER_SHA = 'c34e7d5454d0a877c83fd4969c734437208bc756fc5d2d3fdcbfae5e50462722'
OLD = '''            return CallToolResult(
                content=[TextContent(type="text", text=f"Error executing tool ck3_auto_turn: {error}")],
                is_error=True,
                structured_content={"error_type": type(error).__name__,
                                    "diagnostics": {diagnostic_key: diagnostic}},
            )'''
NEW = '''            diagnostics = {diagnostic_key: diagnostic}
            if diagnostic_key == "native_command_rejection":
                from .campaign_root_retry_diagnostic_v1 import project_campaign_root_retry_diagnostic_v1

                retry_diagnostic = project_campaign_root_retry_diagnostic_v1(error, diagnostic)
                if retry_diagnostic is not None:
                    diagnostics["campaign_root_readonly_retry_v1"] = retry_diagnostic
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error executing tool ck3_auto_turn: {error}")],
                is_error=True,
                structured_content={"error_type": type(error).__name__,
                                    "diagnostics": diagnostics},
            )'''


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def transform_mcp_source_v1(source, *, expected_sha256=ACTUAL_SHA):
    if type(source) is not bytes or expected_sha256 not in (ACTUAL_SHA, MASTER_SHA) or sha(source) != expected_sha256:
        raise ValueError('campaign-root MCP observability: frozen input differs')
    text = source.decode('utf-8')
    if text.count(OLD) != 1 or NEW in text:
        raise ValueError('campaign-root MCP observability: unique untouched error span required')
    candidate = text.replace(OLD, NEW, 1)
    if candidate.replace(NEW, OLD, 1) != text:
        raise ValueError('campaign-root MCP observability: inverse bytes differ')
    compile(candidate, 'xar_autoplayer/bridge/mcp_server.py', 'exec', dont_inherit=True)
    before, after = ast.parse(text), ast.parse(candidate)
    original = [node for node in ast.walk(before) if isinstance(node, ast.FunctionDef) and node.name == 'ck3_auto_turn']
    changed = [node for node in ast.walk(after) if isinstance(node, ast.FunctionDef) and node.name == 'ck3_auto_turn']
    if len(original) != 1 or len(changed) != 1:
        raise ValueError('campaign-root MCP observability: actual AUTO handler ambiguous')
    inverse = ast.parse(candidate.replace(NEW, OLD, 1))
    if ast.dump(inverse, include_attributes=False) != ast.dump(before, include_attributes=False):
        raise ValueError('campaign-root MCP observability: inverse AST differs')
    raw = candidate.encode()
    return raw, {'base_sha256':expected_sha256, 'base_bytes':len(source),
        'candidate_bytes':len(raw), 'candidate_sha256':sha(raw), 'span_count':1,
        'source_offset':source.index(OLD.encode()), 'inverse_bytes_and_AST_exact':True,
        'original_error_content_and_native_diagnostic_preserved':True,
        'new_helper':'xar_autoplayer/bridge/campaign_root_retry_diagnostic_v1.py',
        'new_retry_or_Game_calls':0, 'outputs_materialized':False}
