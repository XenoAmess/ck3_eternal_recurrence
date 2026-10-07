"""Preserve initial source-model author failure; fix only its loop-local parent read."""
from pathlib import Path
basis=Path(__file__).with_name('author_minimal_candidate.py')
code=basis.read_text(encoding='utf-8')
old='  start=i;line=lines[i]\n'
new="  parent=all(s['active'] for s in stack)\n  start=i;line=lines[i]\n"
if code.count(old)!=1:raise ValueError('Exact model-author correction marker required')
exec(compile(code.replace(old,new,1),str(basis),'exec'),{'__name__':'__main__','__file__':__file__})
