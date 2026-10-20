from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

from r11_visual_contract_a02 import FilePin, load_map, object_map

ROOT = Path(__file__).resolve().parent
OLD = Path('C:/ck3-e04-resume-20261015-a01/live12004-t0-control-a01')
RESP = OLD / 'desktop-3fevhd2-1c74096080--vanilla--R0174/responses'
MACHINE = 'desktop-3fevhd2-1c74096080'


def need(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def army(row: dict[str, object]) -> dict[str, object]:
    body = object_map(row.get('body'), 'native body')
    need(row.get('machine_id') == MACHINE and row.get('is_error') is False, 'Native source/machine error')
    player = object_map(body.get('played_character'), 'played character')
    need(type(player.get('character_id')) is int and player.get('character_id') == 31254, 'Wrong Robert')
    wars = body.get('active_wars')
    need(isinstance(wars, list), 'Wars unavailable')
    if not isinstance(wars, list):
        raise ValueError('Wars unavailable')
    for value in wars:
        war = object_map(value, 'war')
        allies = war.get('allied_armies')
        if not isinstance(allies, list):
            continue
        for entry in allies:
            candidate = object_map(entry, 'army')
            if type(candidate.get('army_id')) is int and candidate.get('army_id') == 18:
                need(candidate.get('owner_character_id') == 31254, 'Wrong army owner')
                return candidate
    raise ValueError('Army18 unavailable')


def main() -> None:
    env = dict(os.environ)
    env.update(PYTHONPATH='C:/ck3-e04-resume-20261020-a01/r08-mypy1201-tools-2115-a01/Lib',
        PYTHONDONTWRITEBYTECODE='1', TMP=str(ROOT), TEMP=str(ROOT))
    args = [sys.executable, '-B', '-m', 'mypy', '--config-file', str(ROOT / 'mypy-a02.ini'),
        '--no-incremental', '--cache-dir', 'nul', '--python-version', '3.14', '--platform', 'win32',
        '--disallow-untyped-defs', '--check-untyped-defs', str(Path(__file__)), str(ROOT / 'r11_visual_contract_a02.py')]
    proc: subprocess.Popen[bytes] = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    try:
        stdout, stderr = proc.communicate(timeout=90)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate(timeout=10)
        raise
    print(json.dumps({'mypy_original_pid': proc.pid, 'original_wait': proc.returncode,
        'stdout': stdout.decode('utf8'), 'stderr': stderr.decode('utf8')}), flush=True)
    need(proc.returncode == 0, 'Root verifier actual static check failed')
    recipe = load_map(ROOT / 'R11-ONCE-CONTACT-RECIPE.prepared-a02.json')
    refs = recipe.get('native_proof_refs')
    need(isinstance(refs, list), 'Frozen native proof references missing')
    if not isinstance(refs, list):
        raise ValueError('References unavailable')
    checked = []
    for value in refs:
        ref = FilePin.parse(value, 'native proof pin')
        need(FilePin.read(Path(ref.path)) == ref, 'Historical native pin differs')
        checked.append(ref.wire())
    ai = FilePin.read(ROOT / 'AI-CONTINUOUS-REVIEW.actual-a01.json')
    need(ai.bytes == 3878 and ai.sha256 == '03e54fbff13e77f515a8cdd9dbc06e0aeea7456fe962026e35474979fa6fa0e0', 'AI review pin differs')
    visual = load_map(Path(ai.path))
    need(object_map(visual.get('coverage'), 'coverage').get('all_rows_actually_viewed') is True, 'Incomplete actual visual review')
    before = load_map(RESP / '030-t0-halt-a01-10-before-halt.json')
    after = load_map(RESP / '031-halt-readonly-a01-halt-readonly-01.json')
    final = load_map(RESP / 'r174-control-d01-a01-d01-12-final.json')
    route = army(before).get('route_province_ids')
    need(isinstance(route, list) and len(route) > 1, 'Before route not multi-hop')
    for row, expected in ((after, 53145048), (final, 53145072)):
        body = object_map(row.get('body'), 'body')
        need(body.get('date_raw') == expected and body.get('paused') is True, 'After date/pause differs')
        unit = army(row)
        need(unit.get('current_province_id') == 2624 and unit.get('route_province_ids') == [] and
            unit.get('route_read_status') == 'complete_empty' and unit.get('move_target_province_id') is None and
            unit.get('army_state_code') == 1, 'Independent Halt/stationary postcondition differs')
    clock = load_map(RESP / 'r174-control-d01-a01-d01-09-clock-query-0.json')
    sentinel = object_map(object_map(clock.get('body'), 'clock body').get('tactical_daily_sentinel'), 'sentinel')
    need(sentinel.get('generation') == 1 and sentinel.get('starting_date_raw') == 53145048 and
        sentinel.get('trigger_date_raw') == 53145072 and sentinel.get('completed_daily_ticks') == 1 and
        sentinel.get('overshoot_days') == 0 and sentinel.get('pause_observed') is True, 'One exact day differs')
    record = {'schema': 'xar.e04.R11-root-formal-adjudication.v1', 'machine_id': MACHINE,
        'observed_at_utc': datetime.now(timezone.utc).isoformat(), 'status': 'FORMAL_R11_PASS',
        'original_M_unchanged': True, 'original_M_lines': [145, 149],
        'native_pins_independently_checked': checked, 'AI_actual_all38_review': ai.wire(),
        'Root_actual_contact_sheets': [0, 2, 3, 15, 37], 'Root_actual_old_fullres_frames': [0, 60],
        'Root_viewed_all600_claim': False, 'source_frames_half_open': [0, 600],
        'selected_seconds_half_open': [0, 20], 'necessary_evidence_occlusion_detected': False,
        'native_postconditions': {'army_id': 18, 'actor': 31254, 'province': 2624,
            'after_empty_route_null_target_regular': True, 'exact_day_raw': [53145048, 53145072],
            'stationary_next_day': True, 'nextday_within_selected_clip': False},
        'boundaries': ['Short prestate disclosed; M149 contains no six-second minimum.',
            'Exact Halt PTS is null; visible transition only bracketed (0,2].',
            'Original immediate-after stale route and runner exit1 preserved; later independent empty-route read is separate.',
            'Ordinary R0173 save continuation; no new ABC fresh-T0 credit.',
            'AI contact review is not human1x signoff or whole-film completion.'],
        'formal_r11_credit': 1, 'formal_total_before': 5, 'formal_total_after': 6, 'formal_target': 11,
        'research_total_unchanged': [10,14], 'B_unchanged': [0,2], 'ABC_unchanged': [0,3],
        'new_game_started': False, 'new_recording': False, 'human1x': False, 'whole_film_complete': False}
    output = ROOT / 'ROOT-R11-FORMAL-ADJUDICATION.actual-a01.json'
    body = (json.dumps(record, ensure_ascii=False, indent=2) + '\n').encode('utf8')
    need(sum(p.stat().st_size for p in ROOT.iterdir() if p.is_file() and not p.name.startswith('contact-')) + len(body) < 262144,
        'Metadata budget exceeded')
    with output.open('xb') as stream:
        stream.write(body)
    print(json.dumps(FilePin.read(output).wire()), flush=True)


if __name__ == '__main__':
    main()
