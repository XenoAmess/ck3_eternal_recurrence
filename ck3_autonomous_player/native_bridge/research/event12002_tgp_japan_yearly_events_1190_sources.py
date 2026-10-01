"""Read the bounded .1190 migration inputs; never open a game process."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

EVENT = 'tgp_japan_yearly_events.1190'
EXE_SHA = 'AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D'
RELS = (
    'events/dlc/tgp/tgp_japan_yearly_events_ariana.txt',
    'common/on_action/dlc/tgp/tgp_japan_yearly_on_actions.txt',
    'common/on_action/yearly_on_actions.txt',
    'common/script_values/00_stress_values.txt',
    'common/script_values/00_basic_values.txt',
    'common/script_values/00_county_control_values.txt',
)
TOKEN = re.compile(r'#[^\n]*|"(?:\\.|[^"\\])*"|!=|\?=|<=|>=|[{}=<>]|[^\s{}=<>#]+')


def tokens(text: str) -> list[str]:
    return [m.group() for m in TOKEN.finditer(text) if not m.group().startswith('#')]


def block(text: str, key: str) -> dict[str, object]:
    match = re.search(r'^\s*' + re.escape(key) + r'\s*=\s*\{', text, re.M)
    if match is None:
        raise ValueError(f'missing block: {key}')
    # Token positions ignore braces embedded in comments and quoted strings.
    opening = text.index('{', match.start(), match.end())
    depth = 0
    end = None
    for t in TOKEN.finditer(text, opening):
        if t.group() == '{':
            depth += 1
        elif t.group() == '}':
            depth -= 1
            if depth == 0:
                end = t.end()
                break
    if end is None:
        raise ValueError(f'unclosed block: {key}')
    start = match.start()
    while start < opening and text[start].isspace():
        start += 1
    value = text[start:end]
    return {
        'first_line': text.count('\n', 0, start) + 1,
        'last_line': text.count('\n', 0, end) + 1,
        'text': value,
        'tokens': tokens(value),
        'text_sha256': hashlib.sha256(value.encode('utf-8')).hexdigest(),
    }


def field_values(text: str, names: tuple[str, ...]) -> dict[str, object]:
    result: dict[str, object] = {}
    for name in names:
        m = re.search(r'^\s*' + re.escape(name) + r'\s*=\s*([^\r\n#]+)', text, re.M)
        if m is None:
            raise ValueError(f'missing value: {name}')
        result[name] = {'line': text.count('\n', 0, m.start()) + 1, 'authored_value': m.group(1).strip()}
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--old-game', type=Path, required=True)
    parser.add_argument('--new-game', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    versions: dict[str, object] = {}
    texts: dict[str, dict[str, str]] = {}
    for build, root in (('1.19.0.6', args.old_game), ('1.20.0.2', args.new_game)):
        files = {}
        texts[build] = {}
        for rel in RELS:
            data = (root / rel).read_bytes()
            texts[build][rel] = data.decode('utf-8-sig')
            files[rel] = {'path': str(root / rel), 'sha256': hashlib.sha256(data).hexdigest().upper(), 'size': len(data)}
        versions[build] = {
            'files': files,
            'event': block(texts[build][RELS[0]], EVENT),
            'values': field_values(texts[build][RELS[3]], ('major_stress_impact_gain', 'minor_stress_impact_gain', 'medium_stress_impact_loss', 'minor_stress_impact_loss', 'major_stress_impact_loss')),
            'japanese_pool': block(texts[build][RELS[1]], 'tgp_japan_yearly_events'),
            'prestige_loss': block(texts[build][RELS[4]], 'minor_prestige_loss'),
            'prestige_dread': field_values(texts[build][RELS[4]], ('minor_prestige_value', 'medium_dread_loss')),
            'county_control': field_values(texts[build][RELS[5]], ('medium_county_control_loss',)),
        }
    old = versions['1.19.0.6']
    new = versions['1.20.0.2']
    old_tokens = old['event']['tokens']
    new_tokens = new['event']['tokens']
    renamed = ['stress_impact' if x == 'stress_and_fulfillment_impact' else x for x in new_tokens]
    differences = [
        {'token_index': i, 'old': a, 'new': b}
        for i, (a, b) in enumerate(zip(old_tokens, new_tokens)) if a != b
    ]
    if old_tokens != renamed or len(differences) != 3:
        raise ValueError('unexpected .1190 ordered-token difference')
    # This is input equality, not runtime effect equivalence or live acceptance.
    value_equal = {k: old['values'][k]['authored_value'] == new['values'][k]['authored_value'] for k in old['values']}
    result = {
        'schema': 'xar.ck3.event12002.tgp-japan-yearly-1190.sources.v1',
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'event_key': EVENT,
        'exact_new_exe_sha256': EXE_SHA,
        'process_accessed': False,
        'live_acceptance_performed': False,
        'versions': versions,
        'comparison': {
            'only_event_token_changes': differences,
            'event_tokens_equal_after_helper_rename': old_tokens == renamed,
            'event_whole_body_equal': old_tokens == new_tokens,
            'japanese_pool_tokens_equal': old['japanese_pool']['tokens'] == new['japanese_pool']['tokens'],
            'direct_stress_values_equal': value_equal,
            'prestige_loss_tokens_equal': old['prestige_loss']['tokens'] == new['prestige_loss']['tokens'],
            'prestige_dread_values_equal': {k: old['prestige_dread'][k]['authored_value'] == new['prestige_dread'][k]['authored_value'] for k in old['prestige_dread']},
            'county_control_equal': old['county_control']['medium_county_control_loss']['authored_value'] == new['county_control']['medium_county_control_loss']['authored_value'],
        },
        'reused_native_helper_review': {
            'document': 'docs/ck3-native-ai/event-stress-and-fulfillment-1.20.0.2-source-review.md',
            'artifact': 'Z:/ck3_mod_rewrite/artifacts/nonwar-offline-1.20.0.2/events/stress-fulfillment-source-review.json',
            'artifact_sha256': '486d54b7b22d66e4920ecc3004dcf9b2b279e04744aae8dc2294fb594833c6b3',
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'result': 'source-confirmed', 'event_lines': {k: [v['event']['first_line'], v['event']['last_line']] for k, v in versions.items()}, 'values': {k: v['values'] for k, v in versions.items()}, 'comparison': result['comparison'], 'output': str(args.output), 'output_sha256': hashlib.sha256(args.output.read_bytes()).hexdigest()}, ensure_ascii=False))


if __name__ == '__main__':
    main()
