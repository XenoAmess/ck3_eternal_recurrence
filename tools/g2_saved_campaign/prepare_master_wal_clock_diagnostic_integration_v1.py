"""Exact, reversible source-only Master splice; no Git, SDK or state directory.

Evidence level: bytes/AST checks establish source composition, not runtime
performance or Game/Native acceptance. Production inputs are never loaded as
modules here, and candidate Driver/MCP copies are retained only in RAM.
"""
from __future__ import annotations

import ast
import copy
import difflib
import hashlib
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
PREFIX = 'ck3_autonomous_player/src/xar_autoplayer/bridge/'
A0 = 'tools/g2_saved_campaign/candidates/a0_clock_diagnostic_20261020/'
WAL_PRODUCER = 'tools/g2_saved_campaign/prepare_succession_binding_refresh_wal_v1.py'
BEFORE = {
    'native_driver.py': (1642268, '1b87bf888a6d323d3101a45376b26491aeefa9501dcaa0f3da72d04f9d975ea9'),
    'mcp_server.py': (268839, '1955e0ac452b7ea4c38da48e2010366b19423712d0e8b0877fb9c536d23bd472'),
}
AFTER = {
    'native_driver.py': (1645555, 'd61248aefb548175c5ee823c44e31b79ef0114165417aee55ab502654503b699'),
    'mcp_server.py': (269100, 'f273241c62f06602e36e9d0ec322c9e4b633639b0908fba6c72d2892ed9841a3'),
}
HELPER = 'exact_clock_failure_diagnostic_v1.py'
HELPER_PIN = (6624, '8bf4dc3413fae7634999e3bd1b3509c2b9f2b9a58e0a13ee1abb7a477c52276f')
WAL_INPUT = (10331, '2323491006b60bee56f96a8b18e4458b1e702fb8982cdf7213ef7234e30ba690')
OWNER_METHODS = {'__init__', 'retain_succession_expectation_v1',
    '_try_persist_driver_state_wal_append_v1', '_persist_driver_state',
    '_advance_exact_day_with_sentinel'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def pin(raw):
    return len(raw), hashlib.sha256(raw).hexdigest()


def literal(raw, name):
    found = [node.value for node in ast.parse(raw).body
             if isinstance(node, ast.Assign)
             and any(isinstance(t, ast.Name) and t.id == name for t in node.targets)]
    require(len(found) == 1, 'nonunique declaration: ' + name)
    return ast.literal_eval(found[0])


def source_edits():
    wal_raw = (REPO / WAL_PRODUCER).read_bytes()
    a0_raw = (REPO / A0 / 'prepare_candidate.py').read_bytes()
    require(pin(wal_raw) == (7340, 'a4a40ee6c7426aae5579320f9426af29017e4cd2bdde56b2a090798b5377ac43'), 'WAL donor changed')
    require(pin(a0_raw) == (7579, 'c243f2184f04fe484d3a7cc72fd12e0d1b4d057bed5afdac99474d1864853287'), 'a0 donor changed')
    wal = literal(wal_raw, 'EDITS')
    clock = literal(a0_raw, 'DRIVER_EDITS')
    old, new = clock[-1]
    unsafe = literal(a0_raw, '_old_diagnostic_block')
    safe = literal(a0_raw, '_safe_diagnostic_block')
    require(new.count(unsafe) == 1, 'safe diagnostic declaration missing')
    clock[-1] = old, new.replace(unsafe, safe, 1)
    return tuple(wal), tuple(clock), tuple(literal(a0_raw, 'MCP_EDITS'))


def splice(raw, edits, *, reverse=False):
    for old, new in reversed(edits) if reverse else edits:
        if reverse:
            old, new = new, old
        old, new = old.encode(), new.encode()
        require(raw.count(old) == 1, 'exact hunk occurrence is not one')
        raw = raw.replace(old, new, 1)
    return raw


def function(raw, name):
    found = [n for n in ast.walk(ast.parse(raw))
             if isinstance(n, ast.FunctionDef) and n.name == name]
    require(len(found) == 1, 'nonunique function: ' + name)
    return found[0]


def driver_methods(raw):
    classes = [n for n in ast.parse(raw).body if isinstance(n, ast.ClassDef)
               and n.name == 'NativeHeadlessGameplayDriver']
    require(len(classes) == 1, 'Driver class is not unique')
    return {n.name: n for n in classes[0].body if isinstance(n, ast.FunctionDef)}


def ast_scope(before, after, name):
    old, new = ast.parse(before), ast.parse(after)
    if name == 'native_driver.py':
        old_methods, new_methods = driver_methods(before), driver_methods(after)
        require(old_methods.keys() == new_methods.keys(), 'Driver methods changed shape')
        changed = {key for key in old_methods
                   if ast.dump(old_methods[key]) != ast.dump(new_methods[key])}
        require(changed == OWNER_METHODS, 'unowned Driver methods changed')
        old_class = next(n for n in old.body if isinstance(n, ast.ClassDef)
                         and n.name == 'NativeHeadlessGameplayDriver')
        new_class = next(n for n in new.body if isinstance(n, ast.ClassDef)
                         and n.name == 'NativeHeadlessGameplayDriver')
        new_class.body = [copy.deepcopy(old_methods[n.name])
                         if isinstance(n, ast.FunctionDef) and n.name in OWNER_METHODS
                         else n for n in new_class.body]
    else:
        original = function(before, 'ck3_auto_turn')
        for parent in ast.walk(new):
            for _, value in ast.iter_fields(parent):
                if isinstance(value, list):
                    for index, node in enumerate(value):
                        if isinstance(node, ast.FunctionDef) and node.name == 'ck3_auto_turn':
                            value[index] = copy.deepcopy(original)
    require(ast.dump(old) == ast.dump(new), 'AST outside owned methods changed')


def compose(driver, mcp):
    inputs = {'native_driver.py': driver, 'mcp_server.py': mcp}
    for name, raw in inputs.items():
        require(pin(raw) == BEFORE[name], 'foreign Master input: ' + name)
    wal, clock, mcp_edits = source_edits()
    outputs = {'native_driver.py': splice(splice(driver, wal), clock),
               'mcp_server.py': splice(mcp, mcp_edits)}
    require(splice(splice(driver, clock), wal) == outputs['native_driver.py'], 'Driver edits do not commute')
    require(splice(splice(outputs['native_driver.py'], clock, reverse=True), wal, reverse=True) == driver,
            'entire Driver inverse changed')
    require(splice(outputs['mcp_server.py'], mcp_edits, reverse=True) == mcp, 'entire MCP inverse changed')
    for name, raw in outputs.items():
        require(pin(raw) == AFTER[name], 'candidate output differs: ' + name)
        ast_scope(inputs[name], raw, name)
        compile(raw, PREFIX + name, 'exec', dont_inherit=True)
    return outputs


def installed():
    data = {name: (REPO / PREFIX / name).read_bytes() for name in AFTER}
    for name, raw in data.items():
        require(pin(raw) == AFTER[name], 'installed production leaf differs: ' + name)
    wal, clock, mcp_edits = source_edits()
    before = {'native_driver.py': splice(splice(data['native_driver.py'], clock, reverse=True), wal, reverse=True),
              'mcp_server.py': splice(data['mcp_server.py'], mcp_edits, reverse=True)}
    require(compose(before['native_driver.py'], before['mcp_server.py']) == data, 'installed composition differs')
    require(pin((REPO / PREFIX / HELPER).read_bytes()) == HELPER_PIN, 'canonical diagnostic helper differs')
    require(pin((REPO / PREFIX / 'succession_binding_refresh_wal_v1.py').read_bytes()) == WAL_INPUT,
            'existing WAL helper changed')
    return before, data


def patch_bytes(before, after):
    return ''.join(''.join(difflib.unified_diff(before[n].decode().splitlines(True),
                       after[n].decode().splitlines(True), fromfile='a/' + PREFIX + n,
                       tofile='b/' + PREFIX + n)) for n in AFTER).encode()


def apply_patch_text():
    before = {name: (REPO / PREFIX / name).read_bytes() for name in BEFORE}
    after = compose(before['native_driver.py'], before['mcp_server.py'])
    helper = (REPO / A0 / 'xar_autoplayer/bridge' / HELPER).read_bytes()
    require(pin(helper) == HELPER_PIN, 'a0 helper differs')
    require(not (REPO / PREFIX / HELPER).exists(), 'canonical helper already exists')
    rows = ['*** Begin Patch\n']
    for name in AFTER:
        rows.append('*** Update File: ' + PREFIX + name + '\n')
        diff = list(difflib.unified_diff(before[name].decode().splitlines(True), after[name].decode().splitlines(True)))
        rows.extend('@@\n' if line.startswith('@@') else line for line in diff[2:])
    rows.append('*** Add File: ' + PREFIX + HELPER + '\n')
    rows.extend('+' + line + '\n' for line in helper.decode().splitlines())
    rows.append('*** End Patch\n')
    return ''.join(rows)


if __name__ == '__main__':
    if sys.argv[1:] == ['--emit-apply-patch']:
        print(apply_patch_text(), end='')
    else:
        require(not sys.argv[1:], 'unexpected arguments')
        before, after = installed()
        print(json.dumps({'whole_inverse': True, 'outside_owned_AST_equal': True,
                          'outputs': {n: dict(bytes=len(b), sha256=pin(b)[1]) for n, b in after.items()},
                          'patch_bytes': len(patch_bytes(before, after))}))
