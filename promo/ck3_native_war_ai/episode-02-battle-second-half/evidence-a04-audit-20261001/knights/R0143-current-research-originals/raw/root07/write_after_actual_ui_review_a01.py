"""Preserve root's actually viewed R0143 after UI, with failed trace gates intact."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('_reviewed_after', ROOT / 'scoped_ui_research_a09.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
cfg = m.read(ROOT / 'current-run-bindings.json')
live, output, evidence, transport, steps = m.bind(cfg)
day = m.read(evidence / 'one-day-finished.json')
monitor = m.read(evidence / 'variable-monitor-finish.json')
m.require((evidence / 'after-saved-pair.json').is_file(), 'Actual after immutable checkpoint required')
m.require(monitor['scoped_variable_monitor']['detours_uninstalled'] is True, 'Monitor must already be uninstalled')
snap, sr, values = m.snapshot(output, transport, steps, 'after-root-review-readonly-source', cfg['after_date_raw'])
body, rr = transport.call(output, 'after-root-review-combat-readonly', 'ck3_query_ingame_ui_window_v1', {'window_kind': 'combat', 'expected_revision': values['revision']}, 120)
m.verify_window(body, 'combat', cfg['combat_id'], values, cfg)
m.geometry_gate(body, cfg, True)
names = ['after-victim-character-window.png', 'after-killer-character-window.png', 'after-combat-fit-window.png', 'after-left-knights-fallback-desktop-original.png', 'after-right-knights-fallback-desktop-original.png', 'after-combat-all-visible-desktop-original.png']
review = {'reviewer': '/root', 'at_utc': datetime.now(timezone.utc).isoformat(), 'source_binding': m.identity(ROOT / 'current-run-bindings.json'),
    'original_pixels_actually_reviewed': True, 'reviewed_images': [m.identity(evidence / name) for name in names],
    'observations': ['Victim33437 original page shows skull/death marker, age31, displayed prowess2; before original showed alive/prowess4.',
        'Related34120 original page remains alive, age27, displayed prowess7 and prestige451; before original showed prestige301.',
        'Full fitted and final blank-pointer original combat frames show both commanders, center readings and complete bottom rows10/19 without overlapping tooltip.',
        'Left tooltip contains all10 rows, with victim removed; right tooltip contains all19 rows including related at displayed prowess7.',
        'All after originals show paused1066-12-30 and have same-run source snapshots; no additional day submitted.',
        'Mapped hover fallback used individually measured1280x720 preview rectangles, original2560x1440 desktop sources, actual foreground2491964/PID17420 and PNG/JSON move receipts.',
        'The native hover guard is unchanged. No R0143 native hover error has been invented.',
        'Actual trace FINISH failed managed_wire_cap: assembled1217950 bytes exceeds921600 cap; valid native fragment flags do not substitute the missing full exported DTO.',
        'Actual variable monitor is uninstalled but has failure_flags8/truncated; its partial records cannot prove complete state coverage.'],
    'full_panel_original_image': m.identity(evidence / 'after-combat-all-visible-desktop-original.png'),
    'source_values': values, 'source_snapshot': sr, 'current_native_combat_readback': rr, 'current_native_combat_body': body,
    'day_finish_receipt': m.identity(evidence / 'one-day-finished.json'), 'monitor_finish_receipt': m.identity(evidence / 'variable-monitor-finish.json'),
    'trace_export_complete': False, 'variable_monitor_complete': False,
    'UI_getter_full_ordered_roster_IDs_proven': False,
    'pointer_receipts': [m.identity(evidence / n) for n in ['after-left-knights-mapped-move.png.json', 'after-right-knights-mapped-move.png.json', 'after-combat-blank-ui-mapped-move.png.json']],
    'human_movie_signoff': False, 'six_gaps_not_yet_closed': True, 'global_mutable_bundle_complete': False}
m.write(evidence / 'after-ui-root-review.json', review)
print(m.identity(evidence / 'after-ui-root-review.json'))
