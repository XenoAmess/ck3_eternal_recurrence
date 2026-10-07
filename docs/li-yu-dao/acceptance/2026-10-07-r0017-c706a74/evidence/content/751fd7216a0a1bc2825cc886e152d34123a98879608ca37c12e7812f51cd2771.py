from pathlib import Path
import json
B=Path('C:/workspace/ck3_lyd_runtime_20261004');OLD=B/'r17-root-bound-close-source-20261007-001'
for name in ['DEPENDENCIES.json','INDEX.json','author_closed_boundary.py']:
 p=OLD/name;print('\n',name);print(p.read_text(encoding='utf-8-sig'))
p=OLD/'verify_previous_boundary.py';lines=p.read_text(encoding='utf-8-sig').splitlines()
print('\n'.join(f'{i}: {lines[i-1]}' for i in range(1,73)))
