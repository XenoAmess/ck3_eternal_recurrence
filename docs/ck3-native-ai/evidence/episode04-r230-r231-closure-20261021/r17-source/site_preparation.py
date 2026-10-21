"""Read existing TakeSpec/Root-review artifacts before consuming a rich window."""
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from pathlib import Path

import ordinary_supply_b as b
from normal_saved_source import file_pin, read_pin


def number(value: object, label: str) -> float:
    if type(value) not in (int, float):
        raise ValueError(label + ' must be an actual numeric clock')
    if not isinstance(value, (int, float)):
        raise ValueError(label + ' is not numeric')
    result = float(value)
    b.need(0 < result < float('inf'), label + ' is not finite and positive')
    return result


def timestamp(value: object, label: str) -> float:
    parsed = datetime.fromisoformat(b.text(value, label).replace('Z', '+00:00'))
    b.need(parsed.tzinfo is not None, label + ' requires an explicit timezone')
    return parsed.timestamp()


def verify_file(value: object) -> dict[str, object]:
    ref = file_pin(value)
    b.need(b.pin(ref.path) == ref.json(), 'Prepared original artifact bytes changed')
    return ref.json()


def checked_review(*, config_path: Path, review_path: Path, scene: Path, live: Path,
                   prefix: str, site: int, frame: Mapping[str, object],
                   retained_create_time: float, now: float) -> dict[str, object]:
    """No UI/SDK/recorder action; validate the existing actual artifact contracts."""
    config_ref, review_ref = b.pin(config_path), b.pin(review_path)
    config, review = read_pin(config_ref), read_pin(review_ref)
    binding = b.obj(frame.get('managed_campaign_run_binding'), 'actual prepared-window binding')
    diag = b.obj(frame.get('diagnostics'), 'actual prepared-window diagnostics')
    run = b.text(binding.get('run_id'), 'actual run')
    pid = b.integer(diag.get('bridge_pid'), 'actual PID')
    coordination = live / (prefix + '-camera-site-' + str(site))
    b.need(config.get('schema') == 'xar.e04.owned-window-take-input.v1' and
           config.get('machine_id') == 'desktop-3fevhd2-1c74096080' and
           Path(b.text(config.get('scene_root'), 'TakeSpec scene')).resolve() == scene.resolve() and
           Path(b.text(config.get('run_dir'), 'TakeSpec live')).resolve() == live.resolve() and live.name == run and
           config.get('content_kind') == 'army-supply' and b.integer(config.get('army_id'), 'TakeSpec Army') == 18 and
           config.get('camera_output_name') == coordination.name and
           Path(b.text(config.get('camera_awaiting'), 'camera awaiting')).resolve() == coordination / 'before-action-camera-awaiting.json' and
           Path(b.text(config.get('camera_signal'), 'camera signal')).resolve() == coordination / 'before-action-camera-started.json',
           'Prepared TakeSpec belongs to another scene/run/site/Army')
    cap_ref = verify_file(config.get('capacity'))
    cap = read_pin(cap_ref)
    bounds = b.obj(cap.get('capture_bounds'), 'actual film bounds')
    components = b.obj(cap.get('component_ceiling_bytes'), 'actual film components')
    b.need(cap.get('admitted') is True and cap.get('budget_status') == 'GREEN' and
           cap.get('machine_id') == config.get('machine_id') and cap.get('run_id') == run and
           cap.get('source_head') == config.get('source_head') and
           Path(b.text(cap.get('scene_root'), 'film scene')).resolve() == scene.resolve() and
           Path(b.text(cap.get('raw_workdir'), 'film raw root')).resolve() ==
               Path(b.text(config.get('raw_root'), 'TakeSpec raw root')).resolve() and
           Path(b.text(config.get('raw_root'), 'TakeSpec raw root')).resolve().parent == scene.resolve() and
           b.integer(components.get('raw'), 'film raw bytes') == b.integer(config.get('raw_budget_bytes'), 'TakeSpec raw bytes') and
           b.integer(bounds.get('max_recording_seconds'), 'film recording seconds') == b.integer(config.get('recording_seconds'), 'TakeSpec seconds') and
           b.integer(bounds.get('recording_hard_stop_seconds'), 'film hard seconds') == b.integer(config.get('hard_terminal_seconds'), 'TakeSpec hard seconds') and
           bounds.get('client_only') is True and timestamp(cap.get('quota_review_at_utc'), 'film quota deadline') > now,
           'Actual film capacity does not admit the prepared scene/window')
    b.need(review.get('schema') == 'xar.e04.owned-client-root-review.v1' and
           review.get('machine_id') == config.get('machine_id') and review.get('run_id') == run and
           review.get('reviewer') == '/root' and review.get('root_reviewed_window_only') is True and
           review.get('root_reviewed_no_hover') is True and review.get('content') == 'army-supply' and
           review.get('visual_supply_value_claimed_by_code') is False and
           review.get('human_final_video_approval') is False and
           0 <= now - timestamp(review.get('reviewed_at_utc'), 'Root reviewed time') <= 120,
           'Fresh actual Root army-supply/no-hover image review is not ready')
    capture_ref = verify_file(review.get('capture'))
    b.need(Path(b.text(capture_ref.get('path'), 'capture path')).parent == review_path.parent,
           'Root review points outside its frame directory')
    capture = read_pin(capture_ref)
    source = b.obj(capture.get('source'), 'actual original owned-client capture')
    b.need(capture.get('schema') == 'xar.e04.owned-client-original-frame.v1' and
           capture.get('machine_id') == config.get('machine_id') and capture.get('run_id') == run and
           capture.get('source_head') == config.get('source_head') and capture.get('capacity') == cap_ref and
           b.integer(capture.get('pid'), 'capture PID') == pid == b.integer(source.get('owned_ck3_pid'), 'capture owner PID') and
           number(source.get('owned_ck3_create_time'), 'capture legacy created') == retained_create_time and
           source.get('occluding_windows') == [] and
           b.integer(source.get('hwnd'), 'capture HWND') == b.integer(source.get('foreground_hwnd'), 'capture foreground HWND') and
           source.get('output_size') == config.get('expected_client_size') and
           capture.get('recording_started') is False and capture.get('whole_desktop_recorded') is False and
           0 <= now - timestamp(capture.get('observed_at_utc'), 'capture observed time') <= 180,
           'Prepared Root capture is stale or belongs to another actual owned Game')
    desktop, client = verify_file(capture.get('desktop_original')), verify_file(capture.get('client_original'))
    b.need(review.get('client_original') == client, 'Root review does not bind the original client pixels')
    return {'config': config_ref, 'Root_review': review_ref, 'capture': capture_ref,
            'desktop_original': desktop, 'client_original': client, 'capacity': cap_ref,
            'recording_started': False, 'native_snapshot_rechecked_after_this_review_required': True}
