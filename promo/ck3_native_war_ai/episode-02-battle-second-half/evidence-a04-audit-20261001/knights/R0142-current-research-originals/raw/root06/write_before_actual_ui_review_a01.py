"""Record completed root inspection of this exact pre-day original UI."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_actual_before_review',ROOT/'scoped_ui_research_a08.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
cfg=m.read(ROOT/'current-run-bindings.json');live,output,evidence,transport,steps=m.bind(cfg)
m.require((evidence/'before-saved-pair.json').is_file() and not (evidence/'one-day-intent.json').exists(),'Actual before save required and no day retry')
snap,sr,values=m.snapshot(output,transport,steps,'before-root-review-readonly-source',cfg['before_date_raw'])
body,rr=transport.call(output,'before-root-review-combat-readonly','ck3_query_ingame_ui_window_v1',{'window_kind':'combat','expected_revision':values['revision']},120)
m.verify_window(body,'combat',cfg['combat_id'],values,cfg);m.geometry_gate(body,cfg,True)
names=['before-victim-character-window.png','before-killer-character-window.png','before-combat-fit-window.png','before-left-knights-fallback-desktop-original.png','before-right-knights-fallback-desktop-original.png']
review={'reviewer':'/root','at_utc':datetime.now(timezone.utc).isoformat(),'source_binding':m.identity(ROOT/'current-run-bindings.json'),
    'original_pixels_actually_reviewed':True,'reviewed_images':[m.identity(evidence/name) for name in names],
    'observations':['Victim original character page shows living character age31, displayed prowess4; fullID33437 is independently bound by native query.',
        'Related original character page shows living character age27, displayed prowess7; fullID34120 is independently bound by native query.',
        'Fitted combat frame visibly includes its outer bottom edge and both bottom knight rows. Current full combatID16777218 is independently bound.',
        'Original left tooltip visibly lists all11 rows, including the victim name at displayed prowess4.',
        'Original right tooltip visibly lists all19 rows, including the related character name at displayed prowess7.',
        'All originals show paused 1066-12-29. Tooltip selection used measured desktop-coordinate-map mouse moves; original native hover rejection is retained.',
        'The left move completed but mapper image receipt used an incorrect .json extension and failed its capture; the failed sidecar remains. A separate fresh raw desktop capture proves the actual left tooltip; the move was not retried.'],
    'full_panel_original_image':m.identity(evidence/'before-combat-fit-window.png'),
    'source_values':values,'source_snapshot':sr,'current_native_combat_readback':rr,'current_native_combat_body':body,
    'UI_getter_full_ordered_roster_IDs_proven':False,'native_ordered_rosters_require_same_run_phase_ring':True,
    'native_hover_provider_stays_RED':True,'optional_eligible_list_owner_failure_retained':True,
    'human_movie_signoff':False,'six_gaps_not_yet_closed':True}
m.write(evidence/'before-ui-root-review.json',review)
print(m.identity(evidence/'before-ui-root-review.json'))
