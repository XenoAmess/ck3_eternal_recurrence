"""Source-bound GUI namespace dependencies of the three existing exit targets.

This is a narrow GUI declaration/reference reader, not a GUI runtime. Native
visibility, fixed-target census and dispatch qualification remain independent.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import re

EXIT_ROOTS = {
    'gui/hud.gui': 'timeline_widget',
    'gui/frontend_ingame_menu.gui': 'ingame_pausemenu',
    'gui/window_resign_confirmation.gui': 'ingame_resign_confirmation',
}
_TOKEN = re.compile(r'#[^\r\n]*|"(?:\\.|[^"\\])*"|[{}=]|[^\s{}=#]+')
_IDENTIFIER = re.compile(r'[A-Za-z_][A-Za-z_0-9]*\Z')
_EXIT_REFERENCE = re.compile(r'\b(?:PauseMenu|ResignConfirmationWindow)\s*\.|\bOnPauseMenu\b')


def _value(token: str) -> str:
    return token[1:-1] if token.startswith('"') else token


def _tokens(content: bytes) -> list[str]:
    return [match.group() for match in _TOKEN.finditer(content.decode('utf-8-sig'))
            if not match.group().startswith('#')]


def _braces(tokens: list[str]) -> dict[int, int]:
    stack, pairs = [], {}
    for index, token in enumerate(tokens):
        if token == '{': stack.append(index)
        elif token == '}':
            if not stack: raise ValueError('GUI source has an unmatched closing brace')
            pairs[stack.pop()] = index
    if stack: raise ValueError('GUI source has an unmatched opening brace')
    return pairs


def _references(tokens: list[str]) -> set[str]:
    return {_value(token).casefold() for token in tokens
            if _IDENTIFIER.fullmatch(_value(token))}


def _definitions(tokens: list[str], pairs: dict[int, int]):
    for index, token in enumerate(tokens[:-2]):
        if token.casefold() not in {'type', 'template'}:
            continue
        name = _value(tokens[index + 1]).casefold()
        if not _IDENTIFIER.fullmatch(name):
            continue
        start = index + 2
        while start < len(tokens) and tokens[start] not in {'{', '}'}:
            start += 1
        if start >= len(tokens) or tokens[start] != '{':
            raise ValueError('GUI declaration has no definition block')
        yield name, _references(tokens[index + 2:pairs[start] + 1]) - {name}


def _named_blocks(tokens: list[str], pairs: dict[int, int]):
    stack = []
    for index, token in enumerate(tokens):
        if token == '{': stack.append(index)
        elif token == '}': stack.pop()
        elif (stack and token.casefold() == 'name' and index + 2 < len(tokens)
              and tokens[index + 1] == '='):
            yield _value(tokens[index + 2]).casefold(), stack[-1], pairs[stack[-1]]


def exit_gui_dependency_contract(game_root: Path, protected_paths: tuple[str, ...]) -> dict:
    """Follow stock global type/template references from native's fixed roots."""
    game_root = game_root.resolve()
    providers = defaultdict(list)
    seeds = set()
    for path in sorted((game_root / 'gui').rglob('*.gui')):
        relative = path.relative_to(game_root).as_posix()
        tokens = _tokens(path.read_bytes())
        pairs = _braces(tokens)
        for name, references in _definitions(tokens, pairs):
            providers[name].append((relative, references))
        if relative in EXIT_ROOTS:
            matches = [(start, end) for name, start, end in _named_blocks(tokens, pairs)
                       if name == EXIT_ROOTS[relative]]
            if len(matches) != 1:
                raise ValueError('Stock exit root is not uniquely source-bound: ' + relative)
            start, end = matches[0]
            seeds.update(_references(tokens[max(0, start - 2):end + 1]))
    pending = list(seeds & providers.keys())
    symbols, paths = set(), set()
    while pending:
        name = pending.pop()
        if name in symbols: continue
        symbols.add(name)
        # Duplicate stock declarations are all protected; do not guess a winner.
        for relative, references in providers[name]:
            paths.add(relative)
            pending.extend((references & providers.keys()) - symbols)
    return {'symbols': symbols, 'dependencies': sorted(paths - set(protected_paths)),
            'fixed_roots': set(EXIT_ROOTS.values()),
            'protected_paths': {path.casefold() for path in paths | set(protected_paths)}}


def verify_unrelated_gui(relative: str, content: bytes, contract: dict) -> None:
    if relative.casefold() in contract['protected_paths']:
        raise ValueError('Mod GUI overrides a protected normal-exit dependency source path: ' + relative)
    tokens = _tokens(content)
    pairs = _braces(tokens)
    overlap = {name for name, _ in _definitions(tokens, pairs)} & contract['symbols']
    if overlap:
        raise ValueError('Mod GUI overrides exit type/template dependencies: ' + ', '.join(sorted(overlap)))
    roots = {name for name, _, _ in _named_blocks(tokens, pairs)} & contract['fixed_roots']
    if roots:
        raise ValueError('Mod GUI redefines a fixed normal-exit root: ' + ', '.join(sorted(roots)))
    if any(_EXIT_REFERENCE.search(_value(token)) for token in tokens):
        raise ValueError('Mod GUI references normal-exit callbacks: ' + relative)
