"""Preserve truthful R0142 completion and current task-bus progress."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess
import sys
import psutil

ROOT = Path(__file__).resolve().parent
LIVE = Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-ui-live-20261001-a06')
BUS = Path('D:/workspace/.codex-task-bus/bin/codex_task_bus.py')
BUS_SHA = 'B3C44B42F7BDF401B593D863E3210106A46412DCD7D89F8596C74F4C27392DEE'
def identity(path):
    p = Path(path).resolve()
    b = p.read_bytes()
    return {'path': str(p), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest().upper()}
def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))
def write(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')
def require(ok, message):
    if not ok:
        raise RuntimeError(message)

evidence = LIVE / 'scoped-ui-research-attempt-01'
completion_path = ROOT / 'preparation-attempt-02/native-sdk-attempt-01/completion.json'
completion = read(completion_path)
require(completion['jobs'] and all(row['exit_code'] == 0 for row in completion['jobs']), 'Actual owner SDK did not complete successfully')
blocked = [p.info for p in psutil.process_iter(['pid', 'name']) if (p.info['name'] or '').lower() in ('ck3.exe', 'ffmpeg.exe', 'obs64.exe', 'xar_ck3_bridge_injector.exe')]
require(not blocked, 'Actual game or recording process remains')
restore = ROOT / 'display-restore-and-release-attempt-01/display-restore'
review = {'reviewer': '/root', 'at_utc': datetime.now(timezone.utc).isoformat(),
          'original_pixels_actually_reviewed': True,
          'reviewed_image': identity(restore / 'original-desktop-after-mode.png'),
          'readback': identity(restore / 'readback.json'),
          'observations': ['Root viewed restored original1024x768 desktop; Steam library page and current offline banner are visible. This is a post-run restoration observation, not a new prelaunch freshness proof.'],
          'human_movie_signoff': False}
write(ROOT / 'display-restoration-root-review-a01.json', review)
require(identity(BUS)['sha256'] == BUS_SHA, 'Task bus CLI changed')
argv = [sys.executable, str(BUS), '--expected-cli-sha256', BUS_SHA, 'status', '--task', 'war-episode02-mechanism-evidence-20261001', '--state', 'running', '--repo', 'C:/w/e2research1001',
        '--summary', 'R0142_one_actual_day_UI_pairs_full_panel_saved_daily_DTO_export_RED_monitor_overflow_RED_cleanup_restore_screen_released_video_held',
        '--next-step', 'crosscheck_four_saves_UI_then_minimal_trace_diagnostics_and_reduced_monitor_noise_new_frozen_capture_no_master_intake']
result = subprocess.run(argv, capture_output=True, timeout=30)
for name, data in [('business-status-stdout.bin', result.stdout), ('business-status-stderr.bin', result.stderr)]:
    with (ROOT / name).open('xb') as f:
        f.write(data)
write(ROOT / 'business-status-result-a01.json', {'argv': argv, 'returncode': result.returncode,
      'stdout': identity(ROOT / 'business-status-stdout.bin'), 'stderr': identity(ROOT / 'business-status-stderr.bin')})
require(result.returncode == 0, 'Business progress update failed')
screen_path = Path('D:/workspace/.codex-task-bus/tasks/war-e2-six-gap-hidden-modal-screen-20261001-a05.json')
screen = read(screen_path)
require(screen['resources'] == [] and screen['state'] == 'done', 'Actual screen lease not released')
monitor_path = LIVE / 'ck3-output/interactive-requests-responses/variable-monitor-finish-once.json'
monitor = read(monitor_path)['body']
payload = monitor['scoped_variable_monitor']
require(monitor['accepted'] is False and monitor['status'] == 'failed' and payload['failure_flags'] == 8 and payload['truncated'] is True and payload['detours_uninstalled'] is True, 'Actual monitor RED differs')
summary = {
    'at_utc': datetime.now(timezone.utc).isoformat(), 'run_id': 'desktop-3fevhd2-1c74096080--vanilla--R0142',
    'frozen_source_head': '4ad477ee33e15a93e412f711c7b05b216a2e6651',
    'frozen_checkout': 'C:/w/e2cap1001d', 'independent_private_branch': True,
    'before_date_raw': 53146848, 'after_date_raw': 53146872, 'actual_days_advanced': 1,
    'victim_id': 33437, 'related_id': 34120, 'combat_id': 16777218,
    'before_review': identity(evidence / 'before-ui-root-review.json'),
    'after_review': identity(evidence / 'after-ui-root-review.json'),
    'before_pair': identity(evidence / 'before-saved-pair.json'), 'after_pair': identity(evidence / 'after-saved-pair.json'),
    'one_day_truthful_trace_RED': identity(evidence / 'one-day-finished.json'),
    'daily_trace_export_succeeded': False,
    'monitor_original_response': identity(monitor_path),
    'monitor_accepted': False, 'monitor_failure_flags': 8, 'monitor_truncated': True, 'monitor_detours_uninstalled': True,
    'actual_sdk_completion': identity(completion_path), 'blocked_processes': blocked,
    'display_root_review': identity(ROOT / 'display-restoration-root-review-a01.json'),
    'screen_release_receipt': identity(ROOT / 'display-restore-and-release-attempt-01/screen-release-CAS.json'),
    'screen_final_state': screen, 'business_progress_result': identity(ROOT / 'business-status-result-a01.json'),
    'UI_endpoint_evidence': 'actual_original_pairs_and_unobscured_full_battle_panel_pending_independent_contract_review',
    'pending_mechanisms': ['full_selector_actual_trace', 'unique_death_for_controlled_window', 'complete13domain_variable_causal_chain'],
    'global_mutable_bundle_complete': False, 'movie_modified': False, 'human_movie_signoff': False,
    'master_intake_or_integration': False,
    'process_assets_permanently_preserved': True,
    'root06_and_live_stop_writing_after_this_summary': True,
}
write(ROOT / 'actual-stopped-run-summary-a01.json', summary)
print(json.dumps(identity(ROOT / 'actual-stopped-run-summary-a01.json')))
