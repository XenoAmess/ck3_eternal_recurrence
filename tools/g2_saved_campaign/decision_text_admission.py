"""Explicit new-provider gate. File publication is never a pixel/draw receipt."""
from pathlib import Path
import hashlib
import re

try:
    from . import decision_text_publisher as publisher
except ImportError:
    import decision_text_publisher as publisher

FIRST_SCHEMA = 'xar.ck3.decision-text-first-frame/v1'

def _digest(path):
    return publisher.pin(path, 1024 * 1024)['sha256']

def verify_segment(n, r, launch, root, first_path, read, aware, now):
    """Same call shape as the historical gate, with no legacy display identity."""
    n, root, first_path = Path(n).resolve(), Path(root).resolve(), Path(first_path).resolve()
    if not root.is_relative_to(n / 'recordings') or not first_path.is_relative_to(n):
        raise ValueError('Recording/review escaped its admitted session')
    job, started, first = read(root / 'job.json'), read(root / 'started.json'), read(first_path, 32768)
    game = {'pid': launch.get('pid'), 'creation_filetime': launch.get('creation_filetime'),
            'hwnd': job.get('hwnd'), 'desktop_id': job.get('desktop_id')}
    bound = publisher.read_text_binding(job['decision_text_publisher_receipt'], game=game)
    storage = job.get('storage')
    if (job.get('continuous') is not True or any(job.get(k) is not None for k in ('deadline_utc', 'duration_seconds', 'max_output_bytes'))
            or job.get('pid') != launch.get('pid') or job.get('game_creation_filetime') != launch.get('creation_filetime')
            or type(job.get('game_creation_filetime')) is not int or job['game_creation_filetime'] <= 0
            or any(job.get('launch', {}).get(k) != launch.get(k) for k in ('creation_date', 'pipe'))
            or Path(job['receipt_root']).resolve() != root or job.get('capture_mode') != 'game_decision_text'
            or job.get('overlay') is not None or job.get('decision_text_publisher') != bound
            or job.get('decision_text_file') != bound['decision_text_file']
            or started.get('state') != 'recording' or started.get('game_pid') != launch.get('pid')
            or started.get('game_creation_filetime') != job['game_creation_filetime']
            or started.get('capture_mode') != 'game_decision_text' or started.get('decision_source') is not True
            or started.get('decision_text_publisher') != bound
            or first.get('status') != 'GREEN' or first.get('machine_id') != bound['machine_id']
            or first.get('game_pid') != launch['pid'] or first.get('game_creation_filetime') != launch['creation_filetime']
            or first.get('game_creation_date') != launch['creation_date'] or first.get('recorder_session_id') != job.get('session_id')
            or first.get('publisher_started') != job['decision_text_publisher_receipt']
            or Path(first['recording_job_root']).resolve() != root
            or not aware(started['at_utc']) <= aware(first['at_utc']) <= now()
            or not isinstance(storage, dict) or type(storage.get('disk_reserve_bytes')) is not int or storage['disk_reserve_bytes'] <= 0):
        raise ValueError('Exact new text-publisher recording/source/pixel/storage binding differs')
    policy = job.get('decision_display_policy') or {}
    started_policy = started.get('decision_display_policy') or {}
    if any(x.get('legacy_blue_overlay_retired') is not True or x.get('legacy_window_count_at_start') != 0 for x in (policy, started_policy)):
        raise ValueError('Actual pre-job and pre-OBS retired-window checks required')
    settings = started.get('decision_settings') or {}
    if settings.get('read_from_file') is not True or Path(settings.get('file', '')).resolve() != Path(bound['decision_text_file']).resolve():
        raise ValueError('OBS did not bind the exact independent publisher text file')
    if first.get('reviewer') == '/root':
        if (first.get('schema') != FIRST_SCHEMA or first.get('decision_text_visible') is not True
                or first.get('before_selection_game_pixels_reviewed') is not True
                or first.get('before_selection_decision_pixels_reviewed') is not True
                or first.get('legacy_blue_window_visible') is not False
                or first.get('stage') not in ('frontend', 'saved_map')
                or (first['stage'] == 'frontend' and first.get('frontend_visible') is not True)
                or (first['stage'] == 'saved_map' and first.get('Game_map_visible') is not True)):
            raise ValueError('Explicit actual Root game+new-text pixel review required')
        frame = first['frame']
        if aware(frame['at_utc']) != aware(first['at_utc']): raise ValueError('Root review must identify the actual frame time')
        for key in ('game', 'scene'):
            item = frame[key]; path = Path(item['path']).resolve()
            if (not path.is_relative_to(root) or path.name.startswith('recording-latest-')
                    or type(item.get('bytes')) is not int or not 0 < item['bytes'] <= 8 * 1024**2
                    or not re.fullmatch('[0-9a-f]{64}', str(item.get('sha256', '')))):
                raise ValueError('Exact frozen Root-reviewed frame pins required')
            if publisher.pin(path, 8 * 1024**2) != item: raise ValueError('Root-reviewed frame changed')
    elif first.get('reviewer') == 'automatic_text_continuity':
        try:
            from .automatic_continuity import verify_automatic_text_continuity_receipt
        except ImportError:
            from automatic_continuity import verify_automatic_text_continuity_receipt
        verify_automatic_text_continuity_receipt(receipt=first, job=job, started=started,
            frame=first['frame'], session_root=n, now_utc=now())
    else:
        raise ValueError('Legacy overlay admission cannot qualify new text recording')
    admission_path = Path(storage['admission_path']).resolve()
    if _digest(admission_path) != storage.get('admission_sha256') or _digest(n / 'STORAGE-ADMISSION.json') != storage.get('admission_sha256'):
        raise ValueError('Exact storage admission differs')
    admission = read(admission_path)
    approved = storage.get('approved_output_roots')
    if (admission.get('status') != 'ADMITTED' or admission.get('machine_id') != bound['machine_id']
            or not isinstance(approved, list) or not approved
            or not any(Path(job['recording_root']).resolve().is_relative_to(Path(p).resolve()) for p in approved)
            or not all(any(Path(p).resolve().is_relative_to(Path(a).resolve()) for a in admission['approved_output_roots']) for p in approved)):
        raise ValueError('Recording storage admission/scope/machine differs')
    if any((root / name).exists() for name in ('failed.json', 'completed.json', 'closed-file-probe.json', 'capture_closed.json')):
        raise ValueError('Recording is terminal')
    return job, started, first
