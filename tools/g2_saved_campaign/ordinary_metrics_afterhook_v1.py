"""One source-only repair for the frozen Clean queue's ordinary MET path."""
from __future__ import annotations
import ast


def bind_clean_metrics_afterhook_v1(source):
    """Preserve every other path; let MET reach the existing cooperative MRO."""
    def require(ok, why):
        if not ok:
            raise ValueError('ordinary MET afterhook source differs: ' + why)
    tree = ast.parse(source)
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef)
               and n.name == 'CleanRobertMainMenuQueue']
    require(len(classes) == 1, 'one Clean class required')
    cls = classes[0]
    require(len(cls.bases) == 1 and isinstance(cls.bases[0], ast.Name)
            and cls.bases[0].id == 'SavedCampaignSemanticQueue', 'reviewed Clean base required')
    methods = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'check_after']
    require(len(methods) == 1, 'one check_after required')
    method = methods[0]
    require([n.arg for n in method.args.args] == ['self', 'tool', 'arguments', 'body'], 'check_after signature')
    require(not any(isinstance(n, ast.Compare) and isinstance(n.left, ast.Name) and n.left.id == 'tool'
                    and any(isinstance(c, ast.Name) and c.id == 'METRICS' for c in n.comparators)
                    for n in ast.walk(method)), 'MET already handled; do not apply twice')
    calls = [n for n in method.body if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
             and isinstance(n.value.func, ast.Attribute) and n.value.func.attr == 'check_after'
             and isinstance(n.value.func.value, ast.Name) and n.value.func.value.id == 'ColdQueue']
    require(len(calls) == 1, 'one ordinary static Cold afterhook required')
    call = calls[0]
    require([n.id if isinstance(n, ast.Name) else None for n in call.value.args]
            == ['self', 'tool', 'arguments', 'body'] and not call.value.keywords, 'original delegation arguments')
    index = method.body.index(call)
    require(index > 0 and isinstance(method.body[index-1], ast.Assign)
            and [n.id if isinstance(n, ast.Name) else None for n in method.body[index-1].targets] == ['first_save'],
            'ordinary first_save boundary required')
    lines = source.splitlines(keepends=True)
    before = method.body[index-1].lineno - 1
    require(lines[before].strip() == 'first_save = tool == SAVE and self.initial_save is None', 'exact first_save source')
    newline = '\r\n' if lines[before].endswith('\r\n') else '\n'
    insertion = ('        if tool == METRICS:' + newline
                 + '            return super().check_after(tool, arguments, body)' + newline)
    result = ''.join(lines[:before]) + insertion + ''.join(lines[before:])
    ast.parse(result)
    return result
