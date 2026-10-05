from pathlib import Path
import json
B=Path('C:/workspace/ck3_lyd_runtime_20261004')
M=Path('C:/workspace/ck3_eternal_recurrence/mod_li_yu_dao')
print('BUILDER FIRST120')
print('\n'.join((M/'tools/build_release.py').read_text(encoding='utf-8-sig').splitlines()[:120]))
for rel in ['root-c3-i3b-apply-20261005-001/APPLIED.json','root-c3-optional-guards-apply-20261005-001/APPLIED.json',
            'root-c3-guards-final-l0-20261005-001/policy/preview.json','root-c3-guards-final-l0-20261005-001/product/static.json']:
    p=B/rel;print('INPUT',rel);v=json.loads(p.read_bytes());print(json.dumps(v,ensure_ascii=False)[:17000])
author=B/'r10-claim-verifier-source-author-20261005-001'
print('AUTHOR ROOT FILES',[p.name for p in author.iterdir()])
for path in sorted(author.rglob('ROOT-SOURCE-PIN-RECORD.actual.json')):
    print('ROOT SOURCE PIN PATH',str(path));print(path.read_text(encoding='utf-8')[:15000])
print('R9 PRODUCTION ROOT',[str(p) for p in (Path('C:/lr9s2')/'production').iterdir()] if (Path('C:/lr9s2')/'production').is_dir() else 'MISSING')
