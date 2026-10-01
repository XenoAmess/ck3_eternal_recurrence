from pathlib import Path
import hashlib
import json
ROOT=Path(__file__).resolve().parent
src=ROOT/'run_required_ui_stage_a08.py';dst=ROOT/'run_active_battle_ui_stage_a09.py'
raw=src.read_bytes()
needle=b"for kind in ('knights','combat'):"
assert raw.count(needle)==1
new=raw.replace(needle,b"for kind in ('combat',):")
needle2=b"'army_selection_retried':False,'never_advances_a_day':True,'human_movie_signoff':False})"
assert new.count(needle2)==1
new=new.replace(needle2,b"'army_selection_retried':False,'eligible_military_list_entry_failure_preserved':True,'roster_UI_scope':'Current combat left/right knight tooltips, independently joined to same-run native full-ID combat rosters','never_advances_a_day':True,'human_movie_signoff':False})")
with dst.open('xb') as stream:stream.write(new)
def ident(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest().upper()}
with (ROOT/'active-battle-stage-derivation-a09.json').open('x',encoding='utf-8',newline='\n') as stream:
    json.dump({'original':ident(src),'derived':ident(dst),
        'purpose':'Six requested gaps use active combat rosters; the unrelated eligible military list is not substituted for those rosters',
        'changes':['Collect current combat window directly; do not retry failed eligible list action','Explicitly preserve prior failed optional checks and roster scope'],
        'controller_bytes_changed':False,'native_source_changed':False,'no_day_advance_by_stage':True,'human_movie_signoff':False},stream,indent=2);stream.write('\n')
print(str(dst))
