from pathlib import Path
import re,json
BASE=Path('C:/workspace/ck3_lyd_runtime_20261004')
MOD=Path('C:/workspace/ck3_eternal_recurrence/mod_li_yu_dao')
R9=Path('C:/lr9s2/mod_li_yu_dao')
print('CURRENT RELEASE AUTHORITY')
text=(MOD/'tools/build_release.py').read_text(encoding='utf-8-sig')
for line_no,line in enumerate(text.splitlines(),1):
    if any(key in line for key in ['ALLOW','RUNTIME','FILES','include','manifest','70','production']):print(str(line_no)+':'+line)
print('ROOT RELEVANT DIRECTORIES')
for path in sorted(BASE.iterdir()):
    if path.is_dir() and any(x in path.name.lower() for x in ['c3','i3b','guard','source-author','c2','r10','leadership']):print(path.name)
print('CURRENT MOD COUNTS',len([p for p in MOD.rglob('*') if p.is_file()]))
print('R9 MOD COUNTS',len([p for p in R9.rglob('*') if p.is_file()]))
print('R9 RUNTIME PREFIXES',sorted({p.relative_to(R9).parts[0] for p in R9.rglob('*') if p.is_file()}))
