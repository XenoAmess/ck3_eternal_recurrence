"""Bounded generated-AST policy checks; these are not CK3 iterator tests."""
from __future__ import annotations
import argparse
from copy import deepcopy
from dataclasses import dataclass, field
import json
from pathlib import Path
import sys


ASSETS = 'common/scripted_triggers/lyd_m3_faith_asset_triggers.txt'
C2 = 'common/scripted_triggers/lyd_c2_consent_triggers.txt'
EVENTS = 'events/lyd_c2_consent_events.txt'
MISSING = object()


def need(condition, message):
    if not condition:
        raise ValueError(message)


def definition(block, name):
    return next(e.value for e in block.entries if e.key == name)


@dataclass(eq=False)
class Scope:
    variables: dict = field(default_factory=dict)
    orders: list = field(default_factory=list)
    saints: list = field(default_factory=list)


class Evaluator:
    """Eager sibling conditions; only explicit trigger_if guards skip reads."""
    def __init__(self, definitions):
        self.definitions = definitions
        self.missing_reads = 0

    def resolve(self, path, scope, safe=False):
        need(path.startswith('var:'), 'Unknown scope token ' + path)
        value = scope.variables.get(path[4:], MISSING)
        if value is MISSING and not safe:
            self.missing_reads += 1
            raise ValueError('Absent captured value read: ' + path)
        return value

    def block(self, block, scope):
        answers = []
        i = 0
        while i < len(block.entries):
            e = block.entries[i]
            i += 1
            k, v = e.key, e.value
            if k == 'trigger_if':
                need(v.entries[0].key == 'limit', 'Guard limit must be first')
                condition = self.block(v.entries[0].value, scope)
                fallback = None
                if i < len(block.entries) and block.entries[i].key == 'trigger_else':
                    fallback = block.entries[i].value
                    i += 1
                answer = self.block(Block(v.entries[1:]), scope) if condition else (
                    self.block(fallback, scope) if fallback is not None else True)
            elif k == 'trigger_else':
                raise ValueError('Orphan trigger_else')
            elif k == 'always': answer = v == 'yes'
            elif k == 'NOT': answer = not self.block(v, scope)
            elif k == 'has_variable': answer = v in scope.variables
            elif k == 'exists': answer = isinstance(self.resolve(v, scope, safe=True), Scope)
            elif k in ('any_faith_holy_order', 'any_saint'):
                items = scope.orders if k == 'any_faith_holy_order' else scope.saints
                answer = any([self.block(v, item) for item in items])
            elif k in self.definitions:
                need(v == 'yes', 'Unexpected helper mode')
                answer = self.block(self.definitions[k], scope)
            elif k.startswith('var:') and isinstance(v, Block):
                target = self.resolve(k, scope)
                need(isinstance(target, Scope), 'Captured object is not a faith')
                answer = self.block(v, target)
            elif k.startswith('var:'):
                answer = self.resolve(k, scope) == int(v)
            else:
                raise ValueError('Not a supported read-only trigger: ' + k)
            answers.append(answer)
        return all(answers)


def walk(block):
    for e in block.entries:
        yield e
        if isinstance(e.value, Block): yield from walk(e.value)


def run(source, baseline):
    ast = parse_clausewitz((source / ASSETS).read_text(encoding='utf-8-sig'))
    defs = {e.key: e.value for e in ast.entries}
    name = 'lyd_m3_c2_assets_clear_trigger'
    cases = []

    def check(label, setup, expected, definitions=defs):
        a, b = Scope(), Scope()
        actor = Scope({'lyd_c2_kind': 1, 'lyd_c2_source_faith': a, 'lyd_c2_target_faith': b})
        setup(actor, a, b)
        ev = Evaluator(definitions)
        result = ev.block(definitions[name], actor)
        need(result == expected, label + ' returned wrong policy result')
        need(ev.missing_reads == 0, label + ' performed an unguarded absent read')
        cases.append({'case': label, 'accepted': result, 'expected': expected, 'missing_dereferences': ev.missing_reads})

    check('join_without_assets', lambda actor, a, b: None, True)
    check('source_military_order_blocks', lambda actor, a, b: a.orders.append(Scope()), False)
    check('target_monastic_or_military_order_blocks', lambda actor, a, b: b.orders.append(Scope()), False)
    check('source_registered_saint_blocks', lambda actor, a, b: a.saints.append(Scope()), False)
    check('target_registered_saint_blocks', lambda actor, a, b: b.saints.append(Scope()), False)
    check('detach_without_target_reference', lambda actor, a, b: (actor.variables.update(lyd_c2_kind=2), actor.variables.pop('lyd_c2_target_faith')), True)
    check('detach_source_assets_blocks', lambda actor, a, b: (actor.variables.update(lyd_c2_kind=2), a.orders.append(Scope())), False)
    check('source_reference_absent', lambda actor, a, b: actor.variables.pop('lyd_c2_source_faith'), False)
    check('source_reference_no_object', lambda actor, a, b: actor.variables.update(lyd_c2_source_faith=None), False)
    check('join_target_absent', lambda actor, a, b: actor.variables.pop('lyd_c2_target_faith'), False)
    check('join_target_no_object', lambda actor, a, b: actor.variables.update(lyd_c2_target_faith=None), False)
    check('kind_absent', lambda actor, a, b: actor.variables.pop('lyd_c2_kind'), False)
    check('unknown_kind', lambda actor, a, b: actor.variables.update(lyd_c2_kind=3), False)
    # Independent time-of-check transition: final gate reads current collections.
    a, b = Scope(), Scope()
    actor = Scope({'lyd_c2_kind': 1, 'lyd_c2_source_faith': a, 'lyd_c2_target_faith': b})
    ev = Evaluator(defs)
    need(ev.block(defs[name], actor), 'Empty opening state rejected')
    b.saints.append(Scope())
    need(not ev.block(defs[name], actor), 'Late registered saint was not rechecked')
    cases.append({'case': 'asset_appears_after_open_before_commit', 'accepted': False, 'expected': False, 'missing_dereferences': 0})
    trig = parse_clausewitz((source / C2).read_text(encoding='utf-8-sig'))
    old = parse_clausewitz((baseline / C2).read_text(encoding='utf-8-sig'))
    changed = {'lyd_c2_start_join_trigger', 'lyd_c2_start_detach_trigger', 'lyd_c2_ready_to_confirm_trigger'}

    def strip_added(block):
        entries = []
        for e in block.entries:
            if e.key == 'custom_description' and isinstance(e.value, Block):
                if any(child.key == 'text' and child.value.startswith('lyd_m3_') for child in e.value.entries):
                    continue
            entries.append(Entry(e.key, e.operator, strip_added(e.value) if isinstance(e.value, Block) else e.value))
        return Block(tuple(entries))
    need(strip_added(trig) == old, 'Existing authorization AST changed after removing added asset checks')
    for helper in changed:
        need(any(e.key == 'custom_description' and any(c.key == 'text' and c.value.startswith('lyd_m3_') for c in e.value.entries)
                 for e in walk(definition(trig, helper))), 'Missing opening/final asset guard: ' + helper)
    ready = definition(trig, 'lyd_c2_ready_to_confirm_trigger')
    need(any(e.key == name and e.value == 'yes' for e in walk(ready)), 'Final ready path bypasses asset helper')
    for relative in ('common/scripted_effects/lyd_c2_commit_effects.txt', 'common/scripted_effects/lyd_c2_head_effects.txt',
                     'common/scripted_effects/lyd_c3_head_factory.txt', 'common/scripted_effects/lyd_i3b_commit_effects.txt'):
        need((source / relative).read_bytes() == (baseline / relative).read_bytes(), 'Mutation/fee/factory source changed: ' + relative)
    events = parse_clausewitz((source / EVENTS).read_text(encoding='utf-8-sig'))
    old_events = parse_clausewitz((baseline / EVENTS).read_text(encoding='utf-8-sig'))
    warning = next(e.value for e in definition(events, 'lyd.220').entries if e.key == 'option'
                   and Entry('name', '=', 'lyd_m3_assets_blocked') in e.value.entries)
    need({e.key for e in warning.entries} == {'name', 'trigger', 'custom_tooltip'}, 'Blocked warning has a business effect')
    def strip_warning(block):
        entries = []
        for e in block.entries:
            if e.key == 'option' and Entry('name', '=', 'lyd_m3_assets_blocked') in e.value.entries: continue
            entries.append(Entry(e.key, e.operator, strip_warning(e.value) if isinstance(e.value, Block) else e.value))
        return Block(tuple(entries))
    need(strip_warning(events) == old_events, 'Existing event options/effects changed')
    allowed = {'NOT', 'any_faith_holy_order', 'any_saint', 'always', 'trigger_if', 'limit', 'trigger_else',
               'has_variable', 'exists', 'var:lyd_c2_source_faith', 'var:lyd_c2_target_faith', 'var:lyd_c2_kind',
               'lyd_m3_faith_assets_clear_trigger'}
    need(all(e.key in allowed for d in defs.values() for e in walk(d)), 'Asset policy writes or saves a scope')
    mutants = []
    for key, attribute in [('any_faith_holy_order', 'orders'), ('any_saint', 'saints')]:
        mutated = deepcopy(defs)
        faith = 'lyd_m3_faith_assets_clear_trigger'
        mutated[faith] = Block(tuple(e for e in mutated[faith].entries if not any(c.key == key for c in e.value.entries)))
        a, b = Scope(), Scope()
        getattr(b, attribute).append(Scope())
        actor = Scope({'lyd_c2_kind': 1, 'lyd_c2_source_faith': a, 'lyd_c2_target_faith': b})
        need(Evaluator(mutated).block(mutated[name], actor), 'Policy mutant did not expose the failure')
        mutants.append({'removed_guard': key, 'caught_by_negative_case': True})
    return {'schema': 'lyd.m3.faith-asset-preservation.focused-source.v1', 'status': 'PASS_SOURCE_ONLY',
            'cases': cases, 'case_count': len(cases), 'mutants': mutants,
            'unchanged_authorization_AST': True, 'unchanged_existing_event_AST': True,
            'commit_head_factory_fees_bytes_unchanged': True, 'new_helper_read_only_no_scope_writes': True,
            'native_iterators': None, 'actual_assets': None, 'actual_reload': None,
            'boundary': 'Synthetic evaluation of a generated AST subset; no CK3, SDK, save body or existing full tests.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--parser-root', type=Path, default=Path(__file__).resolve().parents[2] / 'tools')
    args = parser.parse_args()
    global Block, Entry, parse_clausewitz
    sys.path.insert(0, str(args.parser_root))
    from extract_auto_upgrade_buildings import Block, Entry, parse_clausewitz
    result = run(args.source, args.baseline)
    with args.report.open('x', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(json.dumps({'status': result['status'], 'cases': result['case_count'], 'mutants': len(result['mutants']), 'native': None}))


if __name__ == '__main__': main()
