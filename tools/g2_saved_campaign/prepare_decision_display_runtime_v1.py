"""Pure source transformation for a future cold runtime, never an active tree.

Root must include the returned queue/feed and the shared contract/feed/view in
that future runtime's source manifest, provider pins and owner admission graph.
"""
from __future__ import annotations

import ast


def _function(source: str, name: str) -> ast.FunctionDef:
    matches = [node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and node.name == name]
    if len(matches) != 1:
        raise ValueError("expected one top-level " + name)
    return matches[0]


def _replace(source: str, node: ast.AST, replacement: str) -> str:
    begin = getattr(node, "lineno", None)
    end = getattr(node, "end_lineno", None)
    if type(begin) is not int or type(end) is not int:
        raise ValueError("source span unavailable")
    lines = source.splitlines(keepends=True)
    return "".join(lines[:begin - 1]) + replacement + "\n" + "".join(lines[end:])


def transform_queue(source: bytes) -> bytes:
    text = source.decode("utf-8")
    compact = _function(text, "compact_plan")
    if "prewar_force_admission" not in ast.get_source_segment(text, compact).__str__():
        raise ValueError("unsupported old result compact; review required")
    text = _replace(text, compact, '''def compact_plan(plan: object) -> dict[str, object]:
    from decision_display_contract_v1 import project_plan
    return project_plan(plan)
''')
    projection = _function(text, "display_projection")
    old = ast.get_source_segment(text, projection)
    if old is None or "raw response retained" not in old or "army_strengths" not in old:
        raise ValueError("unsupported old result projection; review required")
    text = _replace(text, projection, '''def display_projection(row: object, body: object) -> dict[str, object]:
    from decision_display_contract_v1 import project_result
    return project_result(row, body)
''')
    ast.parse(text)
    return text.encode("utf-8")


def transform_feed(source: bytes) -> bytes:
    text = source.decode("utf-8")
    if "display_actual = {**actual, **plan}" in text:
        raise ValueError("display migration already applied")
    function = _function(text, "publish_before_submit")
    lines = text.splitlines(keepends=True)
    marker = [node for node in function.body if isinstance(node, ast.Assign)
              and any(isinstance(target, ast.Name) and target.id == "stamp" for target in node.targets)]
    if len(marker) != 1 or "event_choice_utility" not in text:
        raise ValueError("expected the reviewed event-aware pre-submit producer")
    line = marker[0].lineno - 1
    # Retain the source-reviewed event explanation/proof already added to plan.
    addition = '''    from decision_display_contract_v1 import project_plan
    display_actual = {**actual, **plan}
    plan = project_plan(display_actual)
'''
    lines.insert(line, addition)
    text = "".join(lines)
    function = _function(text, "publish_before_submit")
    rows = [node for node in function.body if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "row" for target in node.targets)]
    if len(rows) != 1 or rows[0].end_lineno is None:
        raise ValueError("actual callback row assignment missing")
    lines = text.splitlines(keepends=True)
    lines.insert(rows[0].end_lineno, "    row[\"source_namespace\"] = (N / \"p37-responses\").name\n")
    text = "".join(lines)
    function = _function(text, "publish_before_submit")
    first = function.body[0].lineno - 1
    lines = text.splitlines(keepends=True)
    lines[function.lineno - 1] = "def publish_before_submit(observation: object) -> None:\n"
    lines.insert(first, "    from decision_display_contract_v1 import record\n    observation = record(observation)\n")
    result = "".join(lines)
    ast.parse(result)
    return result.encode("utf-8")
