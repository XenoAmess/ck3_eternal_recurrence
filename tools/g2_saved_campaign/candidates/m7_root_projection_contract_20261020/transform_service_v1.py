"""RAM-only exact-method transform; no runtime or repository file writer."""
import ast

METHOD = "query_campaign_root_context_v1"
PROJECTION = "player_heir_fixed_dynasty_projection_v1"
HELPER_TARGET = "xar_autoplayer/bridge/player_heir_projection_service_contract_v1.py"


def method_source(source):
    nodes = [node for node in ast.walk(ast.parse(source))
             if isinstance(node, ast.FunctionDef) and node.name == METHOD]
    if len(nodes) != 1:
        raise ValueError("one original campaign-root Service method required")
    node = nodes[0]
    lines = source.splitlines(keepends=True)
    return "".join(lines[node.lineno - 1:node.end_lineno]), node


def transform_service_v1(source):
    original, node = method_source(source)
    old = "            or set(result) != required_result_keys\n"
    new = ("            or not required_result_keys <= set(result)\n"
           "            or set(result) - required_result_keys - {\"" + PROJECTION + "\"}\n")
    anchor = "        build = {\n"
    added = (
        "        if \"" + PROJECTION + "\" in result:\n"
        "            from .player_heir_projection_service_contract_v1 import (\n"
        "                validate_player_heir_projection_service_v1,\n"
        "            )\n"
        "            validate_player_heir_projection_service_v1(\n"
        "                result[\"" + PROJECTION + "\"], root=normalized, result=result,\n"
        "            )\n"
        "\n")
    if original.count(old) != 1 or original.count(anchor) != 1 or PROJECTION in original:
        raise ValueError("campaign-root Service preimage differs")
    changed = original.replace(old, new).replace(anchor, added + anchor)
    lines = source.splitlines(keepends=True)
    output = "".join(lines[:node.lineno - 1]) + changed + "".join(lines[node.end_lineno:])
    compile(output, "<qualified-campaign-root-Service-transform>", "exec")
    if output.replace(changed, original, 1) != source:
        raise ValueError("Service transform changed bytes outside the original method")
    return output
