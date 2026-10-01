"""Read-only independent endpoint verification; never calls CK3 or writes inputs."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image

ROOT = Path('C:/Users/1/ck3-e2-six-gap-research-20261001/root-attempt-07-trace-diagnostic')
LIVE = Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-trace-live-20261001-a07')
E = LIVE / 'scoped-ui-research-attempt-01'
OUT = Path(__file__).parent
CACHE = {}
CHECKS = []

def require(condition, message):
    if not condition:
        raise ValueError(message)
    CHECKS.append(message)

def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def identity(path):
    path = Path(path).resolve()
    st = path.stat()
    key = (str(path), st.st_size, st.st_mtime_ns)
    if key not in CACHE:
        h = hashlib.sha256()
        with path.open('rb') as f:
            for block in iter(lambda: f.read(1024 * 1024), b''):
                h.update(block)
        after = path.stat()
        require((st.st_size, st.st_mtime_ns) == (after.st_size, after.st_mtime_ns), f'stable bytes: {path}')
        CACHE[key] = {'path': str(path), 'bytes': st.st_size, 'sha256': h.hexdigest().upper()}
    return CACHE[key]

def verify_ref(ref):
    actual = identity(ref['path'])
    require(actual['bytes'] == ref['bytes'] and actual['sha256'] == ref['sha256'].upper(), f'original exact ref: {ref["path"]}')
    return actual

def receipt_body(receipt):
    require(receipt['result'] == 'CALL_COMPLETED' and receipt['error'] is None, 'completed original receipt')
    verify_ref(receipt['request'])
    verify_ref(receipt['response'])
    envelope = load(receipt['response']['path'])
    require(isinstance(envelope.get('body'), dict), 'original envelope has body')
    return envelope['body']

B = load(ROOT / 'current-run-bindings.json')
SESSION = B['native_session_binding']

def normalized(body):
    wars = [x for x in body.get('active_wars', []) if isinstance(x, dict)]
    war = next((x for x in wars if x.get('war_id') == B['war_id']), {})
    army = next((x for x in war.get('allied_armies', []) if x.get('army_id') == B['public_unit_id']), {})
    diagnostics = body['diagnostics']
    return {'date_raw': body['date_raw'], 'paused': body['paused'], 'actor': body['played_character']['character_id'],
            'revision': body['revision'], 'native_revision': body['native_revision'], 'snapshot_id': body['snapshot_id'],
            'war_ids': [x['war_id'] for x in wars], 'army_id': army.get('army_id'), 'army_state': army.get('army_state'),
            'episode_run_id': body['episode_run_id'], 'connection_generation': diagnostics['connection_generation'],
            'bridge_pid': diagnostics['bridge_pid'], 'native_hello_session_generation': diagnostics['hello']['session_generation']}

def snapshot(receipt, values, phase):
    actual = normalized(receipt_body(receipt))
    require(actual == values, f'{phase}: values recomputed from original snapshot')
    require(all(actual[k] == v for k, v in SESSION.items()), f'{phase}: actual native session identity')
    require(actual['date_raw'] == B[f'{phase}_date_raw'] and actual['paused'] is True, f'{phase}: exact paused date')
    require(actual['actor'] == B['actor_id'] and actual['army_id'] == B['public_unit_id'] and actual['army_state'] == 'combat' and B['war_id'] in actual['war_ids'], f'{phase}: actor/War4/Army18 combat scope')
    require(type(actual['native_revision']) is int and actual['native_revision'] > 0 and actual['snapshot_id'] == f'native:{actual["native_revision"]}', f'{phase}: real revision/snapshot binding')
    return actual

def ui_body(body, values, kind, subject):
    require(body['schema'] == 'ck3-ingame-ui-window-v1', 'actual UI schema')
    require(all(body[k] is True for k in ['accepted', 'available', 'window_exists', 'effective_visible', 'subject_id_available', 'application_owner_thread_verified', 'gui_owner_binding_verified']), f'{kind}: actual visible subject and verified owner')
    require(body['window_kind'] == kind and body['current_subject_id'] == subject, f'{kind}: full subject ID {subject}')
    pairs = {'date_raw': 'date_raw', 'paused': 'paused', 'played_character_id': 'actor', 'native_revision': 'native_revision', 'queried_revision': 'revision', 'queried_native_revision': 'native_revision', 'queried_snapshot_id': 'snapshot_id', 'episode_run_id': 'episode_run_id', 'queried_connection_generation': 'connection_generation'}
    require(all(body[k] == values[v] for k, v in pairs.items()), f'{kind}: original UI matches fresh snapshot')
    require(body['gui_context_address'] > 0 and body['gui_context_address'] == body['gui_owner_address'] and body['thread_id'] > 0 and body['pump_epoch'] > 0, f'{kind}: actual context/owner/thread/epoch')
    verify_ref(body['native_ui_raw_return_receipt'])

def ui_binding(filename, phase, kind, subject):
    doc = load(E / filename)
    verify_ref(doc['source_binding'])
    values = snapshot(doc['source_snapshot'], doc['source_values'], phase)
    require(snapshot(doc['query_snapshot'], doc['query_values'], phase) == values and snapshot(doc['post_pixels_snapshot'], doc['post_pixels_values'], phase) == values, f'{filename}: same pause/revisions before and after pixels')
    before = receipt_body(doc['readback'])
    after = receipt_body(doc['post_pixels_readback'])
    require(before == doc['readback_body'] and after == doc['post_pixels_readback_body'], f'{filename}: UI bodies equal original envelopes')
    for body in (before, after):
        ui_body(body, values, kind, subject)
    owner_fields = ('gui_context_address', 'gui_owner_address', 'thread_id', 'current_subject_id')
    require(all(before[k] == after[k] for k in owner_fields) and after['pump_epoch'] > before['pump_epoch'], f'{filename}: postpixels same owner/subject with fresh epoch')
    img = doc['image']
    require(img['pid'] == SESSION['bridge_pid'] and img['creation_time'] == 1790857417.4866428 and img['hwnd'] == 2491964 and img['rect'] == [0, 0, 2560, 1440], f'{filename}: actual WGC process/window')
    verify_ref(img['image'])
    with Image.open(img['image']['path']) as image:
        require(image.size == (2560, 1440), f'{filename}: original image dimensions')
    if kind == 'combat':
        g = before['combat_geometry']
        require(g == after['combat_geometry'] and g['available'] is True and g['combat_id'] == B['combat_id'] and g['content_inside_viewport'] is True and g['fit_required'] is False and g['stock_margin_source_verified'] is True, f'{phase}: stable complete combat geometry')
        require(g['coordinate_space'] == 'native_gui_absolute' and g['stock_margin_source_sha256'] == '7FEE98B7341E21607ED3BB9089C51EF890D229DB6C16865C88133C3BA3579236', f'{phase}: stock GUI geometry units/margins')
        v, u = g['viewport'], g['content_union']
        require(v['width'] > 0 and v['height'] > 0 and u['width'] > 0 and u['height'] > 0 and u['x'] >= v['x'] - .01 and u['y'] >= v['y'] - .01 and u['x'] + u['width'] <= v['x'] + v['width'] + .01 and u['y'] + u['height'] <= v['y'] + v['height'] + .01, f'{phase}: independently bounded union')
        require(before['tree']['truncated'] is False and after['tree']['truncated'] is False, f'{phase}: target-window tree untruncated')
        stable = []
        for row in doc['stable_read_only_observations']:
            b = receipt_body(row['native_receipt'])
            require(b == row['body'], f'{phase}: original stable body')
            ui_body(b, values, kind, subject)
            stable.append(b)
        require(len(stable) >= 2 and all(b['thread_id'] == before['thread_id'] for b in stable) and all(stable[i]['pump_epoch'] < stable[i+1]['pump_epoch'] for i in range(len(stable)-1)), f'{phase}: at least two increasing same-thread stable observations')
        fields = ['combat_geometry', 'left_knight_count', 'right_knight_count', 'left_knight_breakdown', 'right_knight_breakdown', 'hover_state_available', 'hovered_widget_name', 'hovered_ui_side', 'hovered_combat_id']
        require(all(all(b[k] == before[k] for k in fields) for b in stable + [after]), f'{phase}: geometry/roster/hover stable around original pixels')
    return doc

def desktop(filename, phase):
    d = load(E / filename)
    values = d['current_paused_source']
    require(snapshot(d['snapshot'], values, phase) == snapshot(d['post_snapshot'], values, phase), f'{filename}: original desktop bracket same pause/session/revision')
    require(d['foreground_pid'] == SESSION['bridge_pid'] and d['foreground_hwnd'] == 2491964 and d['desktop_size'] == d['original_image_size'] == [2560,1440] and d['input_mouse_keyboard'] is False, f'{filename}: original foreground and dimensions')
    verify_ref(d['original'])
    with Image.open(d['original']['path']) as image:
        require(image.size == (2560,1440), f'{filename}: raw dimensions')
    return d

def main():
    require(B['source_commit'] == '419cac1a956c7be356d886256c7bc689cda5327d' and B['run_id'] == 'desktop-3fevhd2-1c74096080--vanilla--R0143', 'actual frozen source and desktop run')
    for pin in B['pins']:
        verify_ref(pin)
    originals = []
    fit = {}
    review = {}
    saves = {}
    for phase in ('before', 'after'):
        for role, subject in [('victim', B['victim_id']), ('killer', B['killer_id'])]:
            d = ui_binding(f'{phase}-{role}-character-original-ui-binding.json', phase, 'character', subject)
            originals.append(d['image']['image'])
        fit[phase] = ui_binding(f'{phase}-combat-fit-full-combat-panel-binding.json', phase, 'combat', B['combat_id'])
        if phase == 'before':
            originals.append(fit[phase]['image']['image'])
        for side in ('left', 'right'):
            d = desktop(f'{phase}-{side}-knights-fallback-desktop-source.json', phase)
            originals.append(d['original'])
        r = load(E / f'{phase}-ui-root-review.json')
        values = snapshot(r['source_snapshot'], r['source_values'], phase)
        body = receipt_body(r['current_native_combat_readback'])
        require(body == r['current_native_combat_body'], f'{phase}: root current combat body is exact original')
        ui_body(body, values, 'combat', B['combat_id'])
        review[phase] = body
        s = load(E / f'{phase}-saved-pair.json')
        snapshot(s['snapshot'], s['source_values'], phase)
        saved = receipt_body(s['save'])
        require(saved == s['save_body'] and saved['checkpoint']['date_raw'] == B[f'{phase}_date_raw'] and saved['checkpoint']['episode_run_id'] == SESSION['episode_run_id'], f'{phase}: actual saved endpoint')
        verify_ref(s['immutable'])
        require(s['immutable']['sha256'].lower() == saved['checkpoint']['sha256'].lower() and s['immutable']['bytes'] == saved['checkpoint']['size'], f'{phase}: immutable saved bytes')
        saves[phase] = s['immutable']
    originals.append(desktop('after-combat-all-visible-desktop-source.json', 'after')['original'])
    require(saves['before']['sha256'] != saves['after']['sha256'] and B['after_date_raw'] - B['before_date_raw'] == 24, 'distinct endpoint saves and exactly +24 date')
    require(review['before']['left_knight_count'] == 11 and review['after']['left_knight_count'] == 10 and review['before']['right_knight_count'] == review['after']['right_knight_count'] == 19, 'current original UI counts left11->10/right19->19')
    require('ONCLICK:CHARACTER,33437 ' in review['before']['left_knight_breakdown'] and 'ONCLICK:CHARACTER,33437 ' not in review['after']['left_knight_breakdown'] and all('ONCLICK:CHARACTER,34120 ' in review[p]['right_knight_breakdown'] for p in ('before','after')), 'current semantic markup binds victim removal and related retention')
    day = load(E / 'one-day-finished.json')
    snapshot(day['post_day_snapshot'], day['post_day_values'], 'after')
    actual_day = receipt_body(day['one_day'])
    require(actual_day == day['one_day_body'] and actual_day['requested_horizon_days'] == 1 and actual_day['elapsed_days'] == 1 and actual_day['paused'] is True and actual_day['starting_date_raw'] == B['before_date_raw'] and actual_day['ending_date_raw'] == B['after_date_raw'], 'one actual requested horizon day and exact paused endpoint')
    require(day['day_postcondition_verified'] is True and day['trace_retry_or_extra_day'] is False and day['trace_finish_body'] is None and day['complete_causal_chain'] == 'pending independent original records and save verification' and day['trace_finish']['result'] == 'RED', 'one real day, truthful trace RED without retry')
    verify_ref(day['trace_finish']['request']); verify_ref(day['trace_finish']['response'])
    stop_original = load(ROOT / 'actual-stopped-run-summary-a01.json')
    verify_ref(stop_original['actual_native_diagnostic'])
    native_diagnostic = load(stop_original['actual_native_diagnostic']['path'])
    d = native_diagnostic['original_parsed_command_result']['trace_publish_diagnostic']
    require(d['failure_gate'] == 'managed_wire_cap' and d['assembled_output_bytes'] == 1217950 and d['managed_cap_bytes'] == 921600 and d['drain_failure_flags'] == d['scoped_failure_flags'] == 0 and d['drain_record_count'] == 7 and d['scoped_record_count'] == 184 and d['detours_uninstalled'] is True, 'actual typed managed cap diagnostic, valid fragments do not equal export')
    day['independent_trace_status'] = 'RED_MANAGED_WIRE_CAP'

    monitor = load(LIVE / 'ck3-output/interactive-requests-responses/variable-monitor-finish-once.json')['body']
    m = monitor['scoped_variable_monitor']
    require(monitor['accepted'] is False and m['failure_flags'] == 8 and m['truncated'] is True and m['detours_uninstalled'] is True, 'native monitor overflow RED/uninstalled retained')
    stop = load(ROOT / 'actual-stopped-run-summary-a01.json')
    verify_ref(stop['actual_sdk_completion'])
    complete = load(stop['actual_sdk_completion']['path'])
    require(all(j['exit_code'] == 0 and j['state'] == 'exited' for j in complete['jobs']) and all(v == [] for v in complete['process_gates'].values()), 'actual SDK exited0 with no process resources')
    require(stop['screen_final_state']['state'] == 'done' and stop['screen_final_state']['resources'] == [] and stop['screen_final_state']['last_sequence'] == 3490, 'screen CAS released3490')
    report = {'schema': 'ck3.R0143.independent-UI-endpoint-review/v1', 'at_utc': datetime.now(timezone.utc).isoformat(), 'reviewer': '/root/a04_other_mechanisms',
              'evidence_layer': 'CURRENT_R0143_ORIGINAL_NATIVE_READBACK_PLUS_DIRECT_ORIGINAL_PIXEL_REVIEW', 'no_game_or_screen_actions': True,
              'binding': B, 'checks_passed': len(CHECKS), 'checks': CHECKS, 'reviewed_original_images': originals, 'immutable_saved_endpoints': saves,
              'pixel_review_method': 'Direct functions.view_image detail=original of ten existing source PNGs; no OCR, crop, generated image or new capture. Historical pending-review flags remain unchanged.',
              'six_gaps': [
                  {'key': 'nextday_character_ui', 'status': 'closed', 'scope': 'Same-run victim33437 and related34120 original character windows, paused12/29->12/30; victim displayed prowess4->2 and alive->dead; related alive/prowess7->7/prestige301->451. No deathcause/weapon attribution implied.'},
                  {'key': 'knight_roster_change_ui', 'status': 'closed', 'scope': 'Current combat16777218 original left full visible list11->10 removes victim33437 semantic name; right19->19 retains related34120. Native GetKnightsBreakdown ONCLICK full IDs plus original pixels; these are UI counts, not ordered active native14->13 roster proof.'},
                  {'key': 'complete_battle_window_ui', 'status': 'closed', 'scope': 'Before fitted original and after unobscured original show outer borders, commanders, central stats and all lower composition rows inside2560x1440; stable native geometry/tree binding supports pixels. Both before and after battle panel have no overlapping tooltip.'},
                  {'key': 'knight_selector', 'status': 'pending', 'gap': 'Same-run complete actual selector prefix/range/shared/source/TLS path not exported; daily FINISH RED.'},
                  {'key': 'unique_actual_death_execution_path', 'status': 'pending', 'gap': 'Endpoint death/UI removal alone cannot prove unique death execution or all rival-path exclusions; daily export RED and monitor native overflow.'},
                  {'key': 'full_13_domain_mutable_state_chain', 'status': 'pending', 'gap': 'flags8/truncatedtrue monitor FINISH cannot support complete chain; strict mechanism verifier NOT_RUN.'}],
              'native_hover_provider': 'UNCHANGED_SOURCE_BOUND_R0142_DERIVED_RTTI_LIMITATION; no new R0143 hover rejection fabricated; actual list pixels from individually bound coordinate-map fallback',
              'optional_eligible_military_list': 'NOT_NEEDED_FOR_CURRENT_ACTIVE_COMBAT_UI; prior R0142 eligible owner RED never substituted for current combat list',
              'daily_trace_status': day['independent_trace_status'], 'original_typed_trace_diagnostic': stop_original['actual_native_diagnostic'], 'typed_diagnostic_fields': d, 'consumer_finish_delay': 'Wrong requested_days field versus actual requested_horizon_days aborted immediate controller after real +24; unique fresh finish continuation, no second day or retry', 'monitor_failure_flags': 8, 'monitor_truncated': True,
              'global_mutable_bundle_complete': False, 'video_modified': False, 'human_movie_signoff': False, 'master_intake_or_integration': False,
              'UI_review_does_not_upgrade_old_failed_attempts': True}
    path = OUT / 'independent-UI-endpoint-review-a02.json'
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(report, f, ensure_ascii=False, indent=2); f.write('\n')
    print(json.dumps({'review': identity(path), 'checks_passed': len(CHECKS), 'UI_closed': 3, 'mechanisms_pending': 3}, ensure_ascii=False))

if __name__ == '__main__':
    main()
