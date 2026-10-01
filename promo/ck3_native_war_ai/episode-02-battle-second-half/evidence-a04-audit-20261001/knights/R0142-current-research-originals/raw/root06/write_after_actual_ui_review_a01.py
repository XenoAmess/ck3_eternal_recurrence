"""Record root's completed inspection; preserve trace RED separately."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('_actual_after_review', ROOT / 'scoped_ui_research_a08.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
cfg = m.read(ROOT / 'current-run-bindings.json')
live, output, evidence, transport, steps = m.bind(cfg)
m.require((evidence / 'after-saved-pair.json').is_file(), 'Actual after save required')
day = m.read(evidence / 'one-day-finished.json')
snap, sr, values = m.snapshot(output, transport, steps, 'after-root-review-readonly-source', cfg['after_date_raw'])
body, rr = transport.call(output, 'after-root-review-combat-readonly', 'ck3_query_ingame_ui_window_v1', {'window_kind': 'combat', 'expected_revision': values['revision']}, 120)
m.verify_window(body, 'combat', cfg['combat_id'], values, cfg)
m.geometry_gate(body, cfg, True)
names = ['after-victim-character-window.png', 'after-killer-character-window.png', 'after-combat-fit-window.png', 'after-left-knights-fallback-desktop-original.png', 'after-right-knights-fallback-desktop-original.png', 'after-combat-all-visible-desktop-original.png']
review = {
    'reviewer': '/root', 'at_utc': datetime.now(timezone.utc).isoformat(),
    'source_binding': m.identity(ROOT / 'current-run-bindings.json'),
    'original_pixels_actually_reviewed': True,
    'reviewed_images': [m.identity(evidence / name) for name in names],
    'observations': [
        'Victim33437 original page shows skull/death status, age31 and displayed prowess2; the before page displayed4. Endpoint and display observations do not imply complete causal writes.',
        'Related34120 original page shows alive, age27, displayed prowess7 and prestige451; before page displayed prestige301.',
        'After left original tooltip contains all10 visible rows and no victim name; before contained11 including victim.',
        'After right original tooltip contains all19 visible rows including related character at displayed prowess7.',
        'The final original combat image includes outer borders, both commanders, combat stats and bottom knight rows10/19 without overlapping tooltip.',
        'All after originals are paused1066-12-30; exactly one game day was advanced in this run.',
        'Native hover failure remains RED. Mouse fallback uses original screenshot, explicit measured1280x720 preview rectangle, foreground984144 and coordinate-map image receipts.',
        'Daily trace FINISH failed managed DTO export; selector, unique death and complete mutable causal chain remain pending.'
    ],
    'full_panel_original_image': m.identity(evidence / 'after-combat-all-visible-desktop-original.png'),
    'source_values': values, 'source_snapshot': sr,
    'current_native_combat_readback': rr, 'current_native_combat_body': body,
    'pointer_receipts': [m.identity(evidence / name) for name in ['after-left-knights-mapped-move.png.json', 'after-right-knights-mapped-move.png.json', 'after-combat-clear-tooltip-mapped-move.png.json', 'after-combat-blank-ui-mapped-move.png.json']],
    'day_finished_identity': m.identity(evidence / 'one-day-finished.json'),
    'UI_getter_full_ordered_roster_IDs_proven': False,
    'native_ordered_rosters_require_same_run_phase_ring': True,
    'daily_trace_export_succeeded': False,
    'native_hover_provider_stays_RED': True,
    'human_movie_signoff': False, 'six_gaps_not_yet_closed': True,
    'global_mutable_bundle_complete': False,
}
m.write(evidence / 'after-ui-root-review.json', review)
print(m.identity(evidence / 'after-ui-root-review.json'))
