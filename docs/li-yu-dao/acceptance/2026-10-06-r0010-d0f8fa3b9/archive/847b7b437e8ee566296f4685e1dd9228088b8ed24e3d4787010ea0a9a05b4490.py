from pathlib import Path
O=Path(__file__).resolve().parent
for name in ['common/decisions/lyd_c3_leadership_decisions.txt','common/scripted_effects/lyd_c3_challenger_effects.txt',
             'common/scripted_effects/lyd_c3_lifecycle_effects.txt','common/scripted_effects/lyd_i3b_setup_effects.txt',
             'common/scripted_effects/lyd_i3b_commit_effects.txt','common/scripted_effects/lyd_i3b_response_effects.txt',
             'common/scripted_triggers/lyd_c3_leadership_triggers.txt','common/scripted_triggers/lyd_i3b_institution_triggers.txt',
             'common/scripted_triggers/lyd_c2_consent_triggers.txt','events/lyd_c2_consent_events.txt','events/lyd_c3_leadership_events.txt','events/lyd_i3b_institution_events.txt']:
    path=O/'snapshot-001/diff'/(name+'.diff')
    print('PATH',name);print(path.read_text(encoding='utf-8'))
