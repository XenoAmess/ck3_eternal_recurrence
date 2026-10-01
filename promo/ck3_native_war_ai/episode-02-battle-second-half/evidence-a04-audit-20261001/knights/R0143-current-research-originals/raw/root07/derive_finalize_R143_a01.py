from pathlib import Path
ROOT = Path(__file__).resolve().parent
src = (ROOT.parent / 'root-attempt-06-hidden-modal-ui/finalize_actual_stopped_run_a01.py').read_text(encoding='utf-8')
replacements = {
 'R0142': 'R0143',
 'episode02-e2-05-d26-six-gap-ui-live-20261001-a06': 'episode02-e2-05-d26-six-gap-trace-live-20261001-a07',
 'preparation-attempt-02/native-sdk-attempt-01/completion.json': 'native-sdk-attempt-01/completion.json',
 'war-e2-six-gap-hidden-modal-screen-20261001-a05': 'war-e2-six-gap-trace-diagnostic-screen-20261001-a06',
 '4ad477ee33e15a93e412f711c7b05b216a2e6651': '419cac1a956c7be356d886256c7bc689cda5327d',
 'C:/w/e2cap1001d': 'C:/w/e2cap1001e',
 'R0143_one_actual_day_UI_pairs_full_panel_saved_daily_DTO_export_RED_monitor_overflow_RED_cleanup_restore_screen_released_video_held': 'R0143_one_actual_day_UI_pairs_full_panel_saved_export_RED_managed_cap1217950gt921600_monitor_overflow_RED_actual_cleanup_restore_screen_released_video_held',
 'crosscheck_four_saves_UI_then_minimal_trace_diagnostics_and_reduced_monitor_noise_new_frozen_capture_no_master_intake': 'crosscheck_R0143_four_saves_UI_fix_consistent_transport_caps_and_actual_horizon_field_new_frozen_capture_no_master_intake',
 'root06_and_live_stop_writing_after_this_summary': 'root07_and_live_stop_writing_after_this_summary',
}
for old, new in replacements.items():
    assert old in src, old
    src = src.replace(old, new)
anchor = "    'daily_trace_export_succeeded': False,"
assert src.count(anchor) == 1
src = src.replace(anchor, anchor + "\n    'actual_trace_failure_gate': 'managed_wire_cap',\n    'actual_assembled_output_bytes': 1217950, 'actual_managed_cap_bytes': 921600,\n    'actual_native_diagnostic': identity(LIVE / 'ck3-state/native-session/combat-trace-native-results/native-trace-4ead0bf732864939be657b267125ebbd.json'),\n    'native_diagnostic_flags_zero_do_not_replace_full_trace': True,")
compile(src, 'finalize_actual_stopped_run_a01.py', 'exec')
with (ROOT / 'finalize_actual_stopped_run_a01.py').open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(src)
print('R0143 truthful finalization controller created; old runs unchanged')
