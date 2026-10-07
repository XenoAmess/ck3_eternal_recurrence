from pathlib import Path
import json,sys
B=Path('C:/workspace/ck3_lyd_runtime_20261004')
for p in [B/'live-attempt-017/mcp-client-001/0025-r17-027-normal-exit-observe.native-01.json',B/'live-attempt-017/mcp-client-001/0024-r17-026-normal-exit-confirm-desktop.native-01.json',B/'r17-root-bound-close-source-20261007-001/DEPENDENCIES.json',B/'r17-root-bound-close-source-20261007-001/author_closed_boundary.py']:
 print('\nFILE',str(p))
 print(p.read_text(encoding='utf-8-sig'))
for p in [B/'r17-root-bound-close-source-20261007-001/verify_previous_boundary.py',Path('C:/lr17s1/ck3_autonomous_player/src/xar_autoplayer/bridge/normal_exit_contract_v1.py'),B/'r17-root-bound-close-source-20261007-001/guarded_helper_close.py']:
 print('\nSOURCE',str(p))
 lines=p.read_text(encoding='utf-8-sig').splitlines()
 start=1 if p.name.startswith('verify_') else 291 if p.name.startswith('normal_exit_contract') else 269
 print('\n'.join(f'{i}: {lines[i-1]}' for i in range(start,len(lines)+1)))
