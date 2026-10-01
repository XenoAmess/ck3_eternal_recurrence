"""Create-only review of frozen file bytes; no live process, native calls or input."""
from pathlib import Path
import datetime, hashlib, json, re

OUT = Path(__file__).parent
LIVE = Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-ui-live-20261001-a06')
REPORT = OUT / 'static-and-raw-readback-a01.json'

def identity(p):
    raw = p.read_bytes()
    return {'path': str(p.resolve()), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest().upper()}

def exact_copy(p, relative):
    target = OUT / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = p.read_bytes()
    with target.open('xb') as f:
        f.write(raw)
    source, copied = identity(p), identity(target)
    assert source['bytes'] == copied['bytes'] and source['sha256'] == copied['sha256']
    return {'original': source, 'copy': copied, 'equal_bytes_and_SHA256': True}

def write_json(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')

static = json.loads(REPORT.read_text('utf-8'))
source_identity = next(r['original'] for r in static['exact_copies'] if r['original']['path'].endswith('ingame_ui_navigation_v1.cpp'))
additions = []
values = {}
for rel in [
    'ck3-output/interactive-requests-responses/army-combat-route-source.json',
    'ck3-output/interactive-requests-responses/army-combat-route-readonly.json',
    'ck3-output/interactive-requests/army-combat-route-readonly.json',
]:
    p = LIVE / rel
    assert p.is_file(), str(p)
    additions.append(exact_copy(p, Path('exact/current-routing-query-a02') / rel))
    value = json.loads(p.read_text('utf-8-sig'))
    if isinstance(value.get('body'), dict):
        values[Path(rel).name] = value
        receipt = value['body'].get('native_ui_raw_return_receipt')
        if isinstance(receipt, dict):
            original = Path(receipt['path'])
            observed = identity(original)
            assert observed['bytes'] == receipt['bytes'] and observed['sha256'] == receipt['sha256'].upper()
            additions.append(exact_copy(original, Path('exact/native-routing-query-return-a02') / original.name))

route_envelope = values['army-combat-route-readonly.json']
body = route_envelope['body']
assert route_envelope['result'] == 'CALL_COMPLETED'
assert body['status'] == 'observed' and body['available'] and body['accepted']
assert body['window_kind'] == 'combat' and body['window_name'] == 'combat_window'
assert body['current_subject_id'] == 16777218 and body['subject_id_available'] and body['effective_visible']
assert body['dispatch_invoked'] is False
assert body['date_raw'] == 53146848 and body['paused'] is True
assert body['played_character_id'] == 29829 and body['native_revision'] == 4 and body['thread_id'] == 7144
assert body['episode_run_id'] == 'native-29829-a892e2bcf200'
assert body['application_owner_thread_verified'] and body['gui_owner_binding_verified']
assert body['executable_sha256'] == static['executable']['sha256']

fields = [
    'schema', 'status', 'accepted', 'available', 'window_kind', 'window_name',
    'window_exists', 'effective_visible', 'enabled', 'requested_subject_id',
    'subject_id_available', 'current_subject_id', 'dispatch_invoked', 'date_raw',
    'paused', 'played_character_id', 'native_revision', 'pump_epoch', 'thread_id',
    'application_owner_thread_verified', 'gui_owner_binding_verified',
    'gui_context_address', 'gui_owner_address', 'rng_owner_thread_id',
    'episode_run_id', 'queried_snapshot_id', 'queried_revision',
    'queried_native_revision', 'queried_connection_generation',
    'combat_roster_full_ids_available', 'combat_knights_read_available',
    'left_knight_count', 'right_knight_count',
]
route_fields = {k: body[k] for k in fields if k in body}
geo = body['combat_geometry']
route_fields['combat_geometry'] = geo
route_fields['UI_markup_ids_are_not_native_ordered_roster'] = {
    side: [int(x) for x in re.findall(r'ONCLICK:CHARACTER,(\d+)', body[side + '_knight_breakdown'])]
    for side in ['left', 'right']
}

functions = {r['name']: r for r in static['functions']}
route_instructions = {int(i['rva'], 16): i for i in functions['RouteSelectedUnitViews']['instructions']}
anchors = [
    (0xA7F0F2, 'call', '0xa812f0', 'SelectUnit invokes original selected-unit view routing'),
    (0xA814E0, 'mov', 'eax, dword ptr [rcx + 0x178]', 'Public CUnit to native CArmy full ID'),
    (0xA8151F, 'mov', 'eax, dword ptr [rcx + 0x128]', 'Generation-validated CArmy to Combat full ID'),
    (0xA81552, 'cmp', 'dword ptr [rcx + 8], eax', 'Original CCombat generation/full ID validation'),
    (0xA81561, 'call', 'qword ptr [rax + 8]', 'Original CCombat virtual predicate partitions selected unit items'),
    (0xA8156A, 'jne', '0xa81570', 'Predicate true group is rbp-1; predicate false rbp-19'),
    (0xA81824, 'cmp', 'dword ptr [rbp - 0xd], 0', 'Ordinary army group count gate'),
    (0xA818AB, 'mov', 'edx, 6', 'Original ordinary ArmyView selector; selected UnitItems Any payload'),
    (0xA818B3, 'call', '0xa79700', 'Original OpenViewData ordinary ArmyView'),
    (0xA8191C, 'test', 'esi, esi', 'Combat item group count gate'),
    (0xA819A5, 'mov', 'ebx, dword ptr [rcx + 0x128]', 'Actual selected native Army Combat ID becomes payload value'),
    (0xA81A07, 'mov', 'dword ptr [rbp - 0x51], ebx', 'Typed primitive Any inline CombatID payload'),
    (0xA81A17, 'mov', 'edx, 0x1a', 'Original CombatView selector'),
    (0xA81A1F, 'call', '0xa79700', 'Original OpenViewData CombatView'),
]
static_checks = []
for rva, mnemonic, operands, meaning in anchors:
    instructions = route_instructions if rva >= 0xA812F0 else {int(i['rva'], 16): i for i in functions['SelectUnit']['instructions']}
    i = instructions[rva]
    assert i['mnemonic'] == mnemonic and i['operands'] == operands, (hex(rva), i)
    static_checks.append({'rva': hex(rva), 'original_instruction': i, 'meaning': meaning, 'exact_bytes_matched': True})

# Record original MCP chronology, using an immutable bounded prefix at the route query.
# This is a file read only, not a call to the running process.
mcp = LIVE / 'ck3-output/mcp-calls.jsonl'
prefix = []
calls = []
target_raw_sha = body['native_ui_raw_return_receipt']['sha256']
matched_target_query = False
with mcp.open('rb') as f:
    for number, line in enumerate(f, 1):
        value = json.loads(line.decode('utf-8-sig'))
        timestamp = value.get('at') or value.get('timestamp') or ''
        prefix.append(line)
        tool = value.get('tool') or value.get('tool_name') or value.get('name')
        if isinstance(tool, str) and ('ingame_ui' in tool or 'select_army' in tool or 'open_combat' in tool):
            result_body = value.get('body') or {}
            calls.append({'line': number, 'at': timestamp, 'tool': tool,
                          'arguments': value.get('arguments'), 'is_error': value.get('is_error'),
                          'original_line_bytes': len(line), 'original_line_sha256': hashlib.sha256(line).hexdigest().upper(),
                          'body_fields': {k: result_body[k] for k in fields if isinstance(result_body, dict) and k in result_body}})
        current_body = value.get('body') or {}
        if isinstance(current_body, dict) and current_body.get('native_ui_raw_return_receipt', {}).get('sha256') == target_raw_sha:
            matched_target_query = True
            break
assert matched_target_query, 'Exact original native query return must identify MCP cutoff'
prefix_path = OUT / 'mcp-calls-bounded-prefix-through-routing-query-a02.jsonl'
with prefix_path.open('xb') as f:
    f.writelines(prefix)

select_calls = [c for c in calls if 'select_army' in c['tool'] and c['body_fields'].get('dispatch_invoked') is True]
route_calls = [c for c in calls if 'query_ingame_ui' in c['tool'] and c['body_fields'].get('current_subject_id') == 16777218]
assert select_calls and route_calls, 'Actual select and query must be present in preserved original MCP prefix'
selected = select_calls[-1]
queried = route_calls[-1]
assert selected['line'] < queried['line']
between = [c for c in calls if selected['line'] < c['line'] <= queried['line']]
assert not any('open_combat' in c['tool'] for c in between), 'A later explicit openCombat would not prove SelectUnit routing'

result = {
    'schema': 'ck3.R0142.in-combat-army-stock-routing-independent-review/v1',
    'timestamp_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'scope': 'Only frozen source, original file bytes, and static exact EXE reads. No process RPM, native requests, screen/input, Git or source edits.',
    'current_run_identity': static['current_run_identity'],
    'status': 'STOCK_ROUTING_CONFIRMED_STATIC_AND_CURRENT_UI_READBACK',
    'conclusion_zh': '原版 SelectUnit 对处于战斗的军队走 CombatView 路由。R0142 原动作已实际调用并返回，本轮随后只读查询确认 CombatWindow 的 full CombatID 为16777218且有效可见；ArmyWindow 隐藏符合原版路由，不等于动作未执行。没有重复选择军队或以截图猜ID。',
    'original_source': source_identity,
    'original_EXE': static['executable'],
    'base_static_and_readback_report': identity(REPORT),
    'additional_exact_copies': additions,
    'exact_static_instruction_checks': static_checks,
    'source_anchors': [
        {'path': source_identity['path'], 'line': 143, 'meaning': 'InvokeUnit calls original SelectUnit(handler, full publicCUnitID, true), not arbitrary OpenViewData(view6) uint32'},
        {'path': source_identity['path'], 'line': 558, 'meaning': 'Full CUnit/nativeCArmy generation and actor/back-reference admission before invocation'},
        {'path': source_identity['path'], 'line': 527, 'meaning': 'Pure query reads existing named CombatWindow; query does not call an open action'},
    ],
    'current_UI_readback': route_fields,
    'current_UI_query_original': additions[1]['original'],
    'MCP_log_bounded_prefix': identity(prefix_path),
    'MCP_UI_calls_in_bounded_prefix': calls,
    'MCP_actual_select_to_original_combat_query': {'select_line': selected['line'], 'query_line': queried['line'], 'intervening_explicit_openCombat': False, 'raw_original_prefix_preserved': True},
    'causal_limits': [
        'The static exact-build branch and actual original dispatch plus same-paused combat query support stock routing. No internal branch runtime detour or original branch trace was installed for this query.',
        'accepted/acknowledged_verification_pending alone proves neither army visible nor combat identity; actual combat fullID is provided by later query.',
        'The UI predicate at CCombat vtable+8 is interpreted by its downstream original view routes, not claimed as a separately named ABI getter.',
        'Actual combat window geometry still reports content_inside_viewport=false and fit_required=true. This report does not close full-panel pixel evidence.',
        'left/right UI knight getters return 11/19 and markup includes33437/34120. combat_roster_full_ids_available=false; UI markup is not substituted for the native ordered combat roster14/13.',
        'Readbacks belong to paused before date53146848 only. No next-day character/roster/state transition is proved here; all six research obligations require their own evidence.',
    ],
    'observer_did_not': {'game_call': True, 'RPM': True, 'memory_write': True, 'desktop_action': True, 'source_edit': True, 'Git': True, 'video_edit_or_render': True},
    'script': identity(Path(__file__)),
}
result['prior_finalizer_failure_preserved'] = {'script': identity(OUT/'finalize_routing_review_a01.py'), 'reason': 'Incorrect envelope-at cutoff excluded original MCP query; a01 assertion failed before report. a02 cuts exact raw-return SHA instead.', 'old_prefix': identity(OUT/'mcp-calls-bounded-prefix-through-routing-query-a01.jsonl')}
report_path = OUT / 'routing-review-final-a02.json'
write_json(report_path, result)
receipt_path = OUT / 'routing-review-final-receipt-a02.json'
write_json(receipt_path, {'schema': 'ck3.create-only-review-receipt/v1', 'review': identity(report_path), 'additional_copy_count': len(additions), 'all_copy_checks': True, 'static_instruction_checks': len(static_checks), 'status': result['status']})
print(json.dumps({'review': identity(report_path), 'receipt': identity(receipt_path), 'query': route_fields, 'MCP_UI_call_count': len(calls)}, ensure_ascii=False))
