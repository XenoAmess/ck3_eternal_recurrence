from pathlib import Path
import collections,json
roots={
 'controller':Path('C:/Users/1/ck3-e2-six-gap-research-20261001/root-attempt-04-scoped-ui'),
 'live':Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-ui-live-20261001-a04'),
 'ui_diagnosis':Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001/R0140-ui-binding-diagnosis-other-a01'),
 'ui_repair':Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001/R0140-ui-binding-repair-other-a01'),
 'monitor_diagnosis':Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001/knight-selector-causality-research-attempt-01/R0140-failed-UI-monitor-diagnostic-attempt-03'),
 'monitor_repair':Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001/knight-selector-causality-research-attempt-01/monitor-thread-semantics-repair-attempt-01'),
}
keywords=['binding','manifest','completion','final-snapshot','private-source','abort','monitor','cleanup','release','restor','commit','result','freeze']
for group,root in roots.items():
 files=[p for p in root.rglob('*') if p.is_file()]
 counts=collections.Counter(p.suffix.lower() for p in files)
 keys=[str(p.relative_to(root)).replace('\\','/') for p in files if p.suffix=='.json' and
       any(k in p.name.lower() for k in keywords) and len(p.relative_to(root).parts)<4]
 print(json.dumps({'group':group,'files':len(files),'bytes':sum(p.stat().st_size for p in files),'suffix_counts':counts,
                   'key_json_paths':keys},ensure_ascii=False))
