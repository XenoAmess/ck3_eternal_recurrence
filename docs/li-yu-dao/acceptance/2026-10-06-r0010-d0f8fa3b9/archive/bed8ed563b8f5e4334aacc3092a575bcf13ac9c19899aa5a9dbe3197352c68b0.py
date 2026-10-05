import json
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
d=read(HERE/'COMPLETE-RITE-FAITH-AST-DIFF.json');row=d['complete_Rite_AST_diffs']['before167']['rites']['159']['changed_variable_rows']['lyd_c2_target_yes'];r=read(BASE/'r10-actual-post-source-sign-readback-20261005-001/REASON-EVIDENCE.json')['source_files']['common/scripted_effects/lyd_c2_vote_effects.txt'];print(json.dumps({'exact_actual_Rite159_target_yes_row_diff':row,'frozen_vote_effect_refs':r},ensure_ascii=False,indent=2))
