from pathlib import Path
import json
B=Path('C:/workspace/ck3_lyd_runtime_20261004')
for p in [B/'r17-root-client-execution-20261007-001/RESULT.actual.json',B/'r17-root-keeper-execution-20261007-001/RESULT.actual.json',B/'live-attempt-017/root-holder-execution-002/RESULT.actual.json',B/'r17-root-screen-release-20261007-001/RELEASE.actual.json']:
 print('\nFILE',p);print(p.read_text(encoding='utf-8-sig'))
p=B/'r17-helper-identity-holder-inputs-20261007-001/RUNTIME.actual.json';o=json.loads(p.read_bytes())
print('\nRUNTIME relevant');print(json.dumps(o.get('game_original_handle_owner'),ensure_ascii=True,indent=2))
