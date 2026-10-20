"""Append the one new Service validator to the existing owner source closure."""
import ast

RELATIVE_HELPER = "bridge/player_heir_projection_service_contract_v1.py"


def transform_owner_epoch_v1(source):
    functions = [node for node in ast.walk(ast.parse(source))
                 if isinstance(node, ast.FunctionDef) and node.name == "owner_source_epoch_v1"]
    if len(functions) != 1:
        raise ValueError("one original owner source epoch required")
    node = functions[0]
    lines = source.splitlines(keepends=True)
    original = "".join(lines[node.lineno - 1:node.end_lineno])
    old = '"bridge/native_loaded_provider_origin_io_v1.py", "bridge/native_preload_mapped_images_v1.py")'
    new = ('"bridge/native_loaded_provider_origin_io_v1.py", "bridge/native_preload_mapped_images_v1.py",\n'
           '             "' + RELATIVE_HELPER + '")')
    if original.count(old) != 1 or RELATIVE_HELPER in original:
        raise ValueError("owner source epoch preimage differs")
    changed = original.replace(old, new)
    output = "".join(lines[:node.lineno - 1]) + changed + "".join(lines[node.end_lineno:])
    compile(output, "<qualified-M7-owner-epoch-transform>", "exec")
    if output.replace(changed, original, 1) != source:
        raise ValueError("epoch transform changed bytes outside owner_source_epoch_v1")
    return output
