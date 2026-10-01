"""Save root's completed R0143 original-pixel review after the main save."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('_reviewed_before', ROOT / 'scoped_ui_research_a09.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
cfg = m.read(ROOT / 'current-run-bindings.json')
live, output, evidence, transport, steps = m.bind(cfg)
m.require((evidence / 'before-saved-pair.json').is_file() and not (evidence / 'one-day-intent.json').exists() and not (evidence / 'variable-monitor-begin-intent.json').exists(), 'Actual before save and unarmed daily window required')
snap, sr, values = m.snapshot(output, transport, steps, 'before-root-review-readonly-source', cfg['before_date_raw'])
body, rr = transport.call(output, 'before-root-review-combat-readonly', 'ck3_query_ingame_ui_window_v1', {'window_kind': 'combat', 'expected_revision': values['revision']}, 120)
m.verify_window(body, 'combat', cfg['combat_id'], values, cfg)
m.geometry_gate(body, cfg, True)
names = ['before-victim-character-window.png', 'before-killer-character-window.png', 'before-combat-fit-window.png', 'before-left-knights-fallback-desktop-original.png', 'before-right-knights-fallback-desktop-original.png']
review = {'reviewer': '/root', 'at_utc': datetime.now(timezone.utc).isoformat(), 'source_binding': m.identity(ROOT / 'current-run-bindings.json'),
    'original_pixels_actually_reviewed': True, 'reviewed_images': [m.identity(evidence / name) for name in names],
    'observations': ['Victim33437 original page shows alive, age31 and displayed prowess4.',
        'Related34120 original page shows alive, age27, displayed prowess7 and prestige301.',
        'Full fitted original combat frame shows both commanders, center readings and complete bottom rows11/19 without an overlapping tooltip.',
        'Original left tooltip shows all11 rows including victim at prowess4; original right tooltip shows all19 rows including related at prowess7.',
        'All originals are paused1066-12-29; each role frame and desktop tooltip has current native before/post snapshot receipts.',
        'Tooltip fallback uses measured1280x720 previews, original2560x1440 desktop sources and mapped moves with originalPNG/JSON receipts, foreground2491964/PID17420.',
        'Native hover guard implementation is unchanged from the source-bound R0142 RTTI rejection diagnosis. No native hover rejection is fabricated for R0143.',
        'The mouse was moved to an inspected blank character-pane region before monitor BEGIN; no day has yet been submitted.'],
    'full_panel_original_image': m.identity(evidence / 'before-combat-fit-window.png'),
    'source_values': values, 'source_snapshot': sr, 'current_native_combat_readback': rr, 'current_native_combat_body': body,
    'UI_getter_full_ordered_roster_IDs_proven': False, 'native_ordered_rosters_require_same_run_phase_ring': True,
    'monitor_window': 'Not armed during UI; begins immediately before original day',
    'pointer_receipts': [m.identity(evidence / n) for n in ['before-left-knights-mapped-move.png.json', 'before-right-knights-mapped-move.png.json', 'before-combat-blank-ui-mapped-move.png.json']],
    'human_movie_signoff': False, 'six_gaps_not_yet_closed': True, 'global_mutable_bundle_complete': False}
m.write(evidence / 'before-ui-root-review.json', review)
print(m.identity(evidence / 'before-ui-root-review.json'))
