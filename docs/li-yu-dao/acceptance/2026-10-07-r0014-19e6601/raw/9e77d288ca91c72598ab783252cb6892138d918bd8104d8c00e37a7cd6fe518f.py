"""Read the actual SteamPath/loginusers offline preference only; no Steam operation."""
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

result = {'observed_at_utc': datetime.now(timezone.utc).isoformat(), 'method': 'SteamPath registry KEY_READ + current loginusers.vdf WantOfflineMode',
          'Steam_mutated': False, 'SDK_calls': 0, 'game_calls': 0, 'lease_mutated': False,
          'fresh_Steam_offline_frame_verified': False, 'next_runtime_requires_fresh_offline_frame_review': True}
try:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Software\\Valve\\Steam', 0, winreg.KEY_READ) as key:
        steam_path, steam_path_type = winreg.QueryValueEx(key, 'SteamPath')
    path = Path(steam_path) / 'config/loginusers.vdf'
    result['SteamPath_registry'] = {'value': steam_path, 'type': steam_path_type}
    result['source'] = ref(path)
    source = path.read_text(encoding='utf-8-sig')
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|[{}]', source)
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
    if cursor != len(tokens) or set(parsed) != {'users'}: raise ValueError('Actual loginusers root shape differs')
    accounts = parsed['users']
    recent = [(key, value) for key, value in accounts.items() if value.get('MostRecent') == '1']
    result['account_count'] = len(accounts); result['MostRecent_account_count'] = len(recent)
    result['observed_preferences'] = [{'account_identity_sha256': hashlib.sha256(key.encode('utf-8')).hexdigest(),
                                      'MostRecent': value.get('MostRecent'), 'WantOfflineMode': value.get('WantOfflineMode'),
                                      'SkipOfflineModeWarning': value.get('SkipOfflineModeWarning')} for key, value in recent]
    result['MostRecent_WantOfflineMode_is_one'] = len(recent) == 1 and recent[0][1].get('WantOfflineMode') == '1'
    result['scope'] = 'Actual MostRecent loginusers preference, corroborative only; not current desktop-frame review'
except Exception as error:
    result['MostRecent_WantOfflineMode_is_one'] = None
    result['read_error'] = type(error).__name__ + ': ' + str(error)
target = OUT / 'STEAM-WANT-OFFLINE-FLAG.readonly.json'
put(target, result)
put(OUT / 'STEAM-FLAG-APPEND-INDEX.json', {'original_closed_boundary_index': ref(OUT / 'INDEX.json'),
                                        'append': ref(target), 'source': ref(__file__),
                                        'previous_unknown_registry_read': ref(OUT / 'STEAM-OFFLINE-FLAG.readonly.json'),
                                        'original_index_unchanged': True, 'Steam_mutated': False})
print(json.dumps({'flag': ref(target), 'append_index': ref(OUT / 'STEAM-FLAG-APPEND-INDEX.json'),
                  'MostRecent_WantOfflineMode_is_one': result['MostRecent_WantOfflineMode_is_one'],
                  'read_error': result.get('read_error')}, ensure_ascii=False, indent=2))
