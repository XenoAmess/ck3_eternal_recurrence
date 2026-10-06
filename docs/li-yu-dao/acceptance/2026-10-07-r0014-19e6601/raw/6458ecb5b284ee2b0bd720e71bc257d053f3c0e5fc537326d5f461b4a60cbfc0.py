"""Append actual account offline field names/values; no guessed key spelling."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, re, winreg

BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
OUT = BASE / 'r14-actual-closed-boundary-20261007-001'

def ref(path):
    path = Path(path).resolve(); raw = path.read_bytes()
    return {'path': path.as_posix(), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def put(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n')

with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Software\\Valve\\Steam', 0, winreg.KEY_READ) as key:
    steam_path, kind = winreg.QueryValueEx(key, 'SteamPath')
path = Path(steam_path) / 'config/loginusers.vdf'
raw = path.read_bytes()
tokens = re.findall(r'"(?:\\.|[^"\\])*"|[{}]', raw.decode('utf-8-sig'))
cursor = 0
def parse():
    global cursor
    rows = {}
    while cursor < len(tokens) and tokens[cursor] != '}':
        key = json.loads(tokens[cursor]); cursor += 1
        if tokens[cursor] == '{':
            cursor += 1; value = parse()
            if cursor >= len(tokens) or tokens[cursor] != '}': raise ValueError('Actual Valve KV close brace missing')
            cursor += 1
        else:
            value = json.loads(tokens[cursor]); cursor += 1
        if key in rows: raise ValueError('Duplicate actual Valve KV key')
        rows[key] = value
    return rows

parsed = parse()
assert cursor == len(tokens) and set(parsed) == {'users'}
rows = []
for account, values in parsed['users'].items():
    fields = {key: value for key, value in values.items() if 'offline' in key.casefold() or key.casefold() == 'mostrecent'}
    rows.append({'account_identity_sha256': hashlib.sha256(account.encode('utf-8')).hexdigest(), 'actual_offline_and_selector_fields': fields})
result = {'observed_at_utc': datetime.now(timezone.utc).isoformat(), 'source': ref(path), 'SteamPath_registry': {'value': steam_path, 'type': kind},
          'account_count': len(rows), 'actual_account_fields': rows,
          'MostRecent_selector_scope': 'No selector is invented if the actual field is absent.',
          'corroborative_preference_only': True, 'fresh_Steam_offline_frame_verified': False,
          'next_runtime_requires_fresh_offline_frame_review': True, 'Steam_mutated': False, 'SDK_calls': 0, 'game_calls': 0, 'lease_mutated': False,
          'earlier_single_WantOfflineMode_selector_note': 'Missing exact MostRecent/WantOfflineMode does not prove online; actual named fields here are authoritative for this preference.'}
target = OUT / 'STEAM-ACTUAL-OFFLINE-FIELDS.readonly.json'
put(target, result)
put(OUT / 'STEAM-FLAG-APPEND-INDEX-002.json', {'original_closed_boundary_index': ref(OUT / 'INDEX.json'), 'append': ref(target),
                                            'source': ref(__file__), 'earlier_selector_read': ref(OUT / 'STEAM-WANT-OFFLINE-FLAG.readonly.json'),
                                            'original_index_unchanged': True, 'Steam_mutated': False})
print(json.dumps({'flag': ref(target), 'append_index': ref(OUT / 'STEAM-FLAG-APPEND-INDEX-002.json'), 'actual_account_fields': rows}, ensure_ascii=False, indent=2))
