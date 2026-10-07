"""Closed readonly metadata and strict public inputs for the actual 24th tool."""
import ast
from pathlib import Path

READONLY_TOOLS = frozenset({'ck3_query_profile_confucian_assembly_predicates_v1', 'ck3_query_profile_confucian_religious_title_v1'})
CHALLENGER_TOOL = 'ck3_query_profile_confucian_challenger_graph_v1'
READONLY_HINTS = {'readOnlyHint': True, 'destructiveHint': False, 'idempotentHint': True, 'openWorldHint': False}

def need(ok, message):
    if not ok: raise ValueError(message)

def check_revision_schema(revision):
    need(type(revision) is dict and revision.get('type') == 'integer'
         and type(revision.get('exclusiveMinimum')) is int and revision['exclusiveMinimum'] == 0
         and type(revision.get('exclusiveMaximum')) is int and revision['exclusiveMaximum'] == 2**64,
         'Readonly revision schema requires strict positive uint64 bounds')

def check_readonly_tool(tool, challenger=False):
    schema = tool.get('inputSchema', {})
    names = ['expected_revision', 'faith_full_ids'] if challenger else ['expected_revision']
    need(schema.get('additionalProperties') is False and schema.get('required') == names
         and set(schema.get('properties', {})) == set(names), 'Exact closed readonly argument schema differs')
    check_revision_schema(schema['properties']['expected_revision'])
    annotations = tool.get('annotations', {})
    need(all(annotations.get(key) is expected for key, expected in READONLY_HINTS.items()), 'Readonly annotations differ from source declaration')
    if challenger:
        selector = schema['properties']['faith_full_ids']
        item = selector.get('items', {})
        need(selector.get('type') == 'array' and selector.get('uniqueItems') is True
             and type(selector.get('minItems')) is int and selector['minItems'] == 1
             and type(selector.get('maxItems')) is int and selector['maxItems'] == 8,
             'Faith selector requires 1..8 unique array items')
        need(item.get('type') == 'integer' and type(item.get('minimum')) is int and item['minimum'] == 0
             and type(item.get('exclusiveMaximum')) is int and item['exclusiveMaximum'] == 2**32 - 1,
             'Faith full ID schema requires strict uint32 excluding invalid sentinel')
    return tool

def validate_challenger_arguments(arguments):
    need(type(arguments) is dict and set(arguments) == {'expected_revision', 'faith_full_ids'}, 'Challenger arguments require exact two fields')
    revision = arguments['expected_revision']
    need(type(revision) is int and 0 < revision < 2**64, 'Challenger revision requires strict positive uint64')
    ids = arguments['faith_full_ids']
    need(type(ids) is list and 1 <= len(ids) <= 8 and all(type(value) is int and 0 <= value < 2**32 - 1 for value in ids)
         and len(ids) == len(set(ids)), 'Faith selector requires 1..8 unique strict valid uint32 IDs')
    return arguments

def number(node):
    if isinstance(node, ast.Constant) and type(node.value) in (int, bool): return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Pow, ast.Sub)):
        left, right = number(node.left), number(node.right)
        return left ** right if isinstance(node.op, ast.Pow) else left - right
    raise ValueError('Unsupported source scalar expression')

def source_declarations(path):
    tree = ast.parse(Path(path).read_text(encoding='utf-8-sig'))
    aliases = {node.targets[0].id: node.value for node in tree.body
               if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)}
    def field(name, base, values):
        alias = aliases[name]
        need(isinstance(alias, ast.Subscript) and isinstance(alias.value, ast.Name) and alias.value.id == 'Annotated'
             and isinstance(alias.slice, ast.Tuple), 'Actual source annotation must be Annotated: ' + name)
        pieces = alias.slice.elts
        need(ast.unparse(pieces[0]) == base, 'Actual source annotation base differs: ' + name)
        declaration = next((x for x in pieces[1:] if isinstance(x, ast.Call) and isinstance(x.func, ast.Name) and x.func.id == 'Field'), None)
        need(declaration is not None, 'Actual source Field declaration missing: ' + name)
        kw = {x.arg: x.value for x in declaration.keywords}
        need(set(values) <= set(kw) and all(type(number(kw[k])) is type(v) and number(kw[k]) == v for k, v in values.items()), 'Actual source strict Field/bounds differ: ' + name)
        return pieces, kw
    field('ConfucianReadonlyRevisionV1', 'int', {'strict': True, 'gt': 0, 'lt': 2**64})
    field('ConfucianFaithFullIdV1', 'int', {'strict': True, 'ge': 0, 'lt': 2**32 - 1})
    pieces, kw = field('ConfucianFaithSelectorV1', 'list[ConfucianFaithFullIdV1]', {'strict': True, 'min_length': 1, 'max_length': 8})
    need(ast.literal_eval(kw['json_schema_extra']) == {'uniqueItems': True}, 'Actual source selector uniqueItems declaration differs')
    validators = [x for x in pieces[1:] if isinstance(x, ast.Call) and isinstance(x.func, ast.Name) and x.func.id == 'AfterValidator']
    need(len(validators) == 1 and len(validators[0].args) == 1 and isinstance(validators[0].args[0], ast.Name), 'Actual unique selector validator missing')
    validator_name = validators[0].args[0].id
    validator = next((x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == validator_name), None)
    need(validator is not None and any(isinstance(x, ast.Raise) for x in ast.walk(validator))
         and any(isinstance(x, ast.Call) and isinstance(x.func, ast.Name) and x.func.id == 'set' for x in ast.walk(validator)), 'Actual source duplicate selector rejection missing')
    tools = {node.name: node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name in READONLY_TOOLS | {CHALLENGER_TOOL}}
    need(set(tools) == READONLY_TOOLS | {CHALLENGER_TOOL}, 'Actual source readonly/challenger declarations missing')
    result = {}
    for name, node in tools.items():
        params = [('expected_revision', 'ConfucianReadonlyRevisionV1')]
        if name == CHALLENGER_TOOL: params.append(('faith_full_ids', 'ConfucianFaithSelectorV1'))
        need([(arg.arg, ast.unparse(arg.annotation)) for arg in node.args.args] == params
             and not node.args.defaults and not node.args.kwonlyargs and node.args.vararg is None and node.args.kwarg is None,
             'Actual source readonly function signature differs: ' + name)
        annotation = next((kw.value for dec in node.decorator_list if isinstance(dec, ast.Call)
                           for kw in dec.keywords if kw.arg == 'annotations'), None)
        need(isinstance(annotation, ast.Call) and isinstance(annotation.func, ast.Name) and annotation.func.id == 'ToolAnnotations', 'Actual source tool annotations missing')
        hints = {kw.arg: ast.literal_eval(kw.value) for kw in annotation.keywords}
        need(hints == READONLY_HINTS, 'Actual source readonly hints differ: ' + name)
        result[name] = {'signature': params, 'annotations': hints}
    factory = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == 'create_server')
    opts = dict(zip((arg.arg for arg in factory.args.kwonlyargs), factory.args.kw_defaults))
    need(all(name in opts and ast.literal_eval(opts[name]) is False for name in ('player_control_tools', 'confucian_readonly_tools', 'confucian_challenger_tools')), 'Actual factory explicit default-off opt-ins differ')
    return result
