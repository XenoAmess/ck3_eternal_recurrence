from pathlib import Path
import ast
import datetime
import hashlib
import json
import os

BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
OUT = Path(__file__).resolve().parent
SOURCE = Path('C:/lr10s1')
HEAD = 'd0f8fa3b9d444828759443aa018bfd7ad31b398d'
SDK = BASE / 'live-attempt-010/mcp-client-evidence-002/0193-r10-0194-after-join-detach-cooldown-query.sdk-result.json'
EXPECTED_SDK = 'bdfc31c44eed5b329106d3651d64f9491c233318a7be19f423f800b796e81193'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_pin(path, expected=None):
    p = Path(path)
    raw = p.read_bytes()
    digest = sha(raw)
    if expected is not None and digest != expected:
        raise ValueError('immutable input SHA mismatch: ' + str(p))
    return raw, dict(path=str(p), bytes=len(raw), sha256=digest)


def write_new(name, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    with (OUT / name).open('xb') as f:
        f.write(raw)


for output in ('REPORT.json', 'SOURCE-EXCERPTS.json', 'SDK193.actual.json', 'INDEX.json'):
    if (OUT / output).exists():
        raise FileExistsError('append-only review output exists: ' + output)

specs = {
    'public_tools': ('tools/ck3_native_profile_mcp.py', '1ab982fc3e46bd6baa507de6c9ca02062811a46991f765a7235b376d98d00fa8', [(517, 524), (749, 760), (829, 859)]),
    'driver': ('ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py', 'b24025f67ec745308754cefd4f182bf3c63356b7a3aa2d5e06d305b34627c751', [(6380, 6389), (6907, 6938)]),
    'query_contract': ('ck3_autonomous_player/src/xar_autoplayer/bridge/ingame_decision_item_contract.py', '79a24b14d6d7462f6eca24011eb090628e7cc2f1bc5852f1741db98c478903ec', [(1, 60)]),
    'action_contract': ('ck3_autonomous_player/src/xar_autoplayer/bridge/ingame_decision_item_action_contract.py', '4d37320c979f7b1bf9bbeaba1ae9cd0d19bd41f81e9ac477d13229d2a616dd87', [(11, 63)]),
    'native_header': ('ck3_autonomous_player/native_bridge/include/xar_bridge/ingame_decision_item_v1.hpp', 'b2d823a8510a99d049762b773ba1bdb21785ffe44e839ceaa6ca3e23f299f51f', [(9, 56)]),
    'native_reader': ('ck3_autonomous_player/native_bridge/src/ingame_decision_item_v1.cpp', '6762b3c89d4c17c66f7e7e310d26ea94458f073da71ae88a5070b19fc7c00f9e', [(150, 167), (278, 305), (326, 406), (433, 456)]),
    'detach_decision': ('mod_li_yu_dao/common/decisions/lyd_c2_consent_decisions.txt', '92d7098453c13ea968e2c1979fc324492b6a2a0e6a734f645585aec7a7cec549', [(1, 21)]),
    'detach_triggers': ('mod_li_yu_dao/common/scripted_triggers/lyd_c2_consent_triggers.txt', '43138d5aced84baec5f381752c4bd0a4f416b231ea9a06d812807b361ec4bda3', [(1, 36), (60, 65)]),
}
pins = {}
texts = {}
excerpts = {}
for name, (relative, expected, spans) in specs.items():
    raw, pins[name] = read_pin(SOURCE / relative, expected)
    text = raw.decode('utf-8-sig')
    texts[name] = text
    lines = text.splitlines()
    excerpts[name] = dict(source=pins[name], ranges=[dict(first=a, last=b, lines=[dict(line=i + 1, text=lines[i]) for i in range(a - 1, b)]) for a, b in spans])

outer = BASE / 'root_prepare_reviewed_consumption_host_request_20261005.py'
raw, pins['root_outer_host_request_builder'] = read_pin(outer, '8b733dd3bc9048b2cad2cf4a7337a70b861841289083c7caf0ad1fcb157efb67')
outer_lines = raw.decode('utf-8-sig').splitlines()
excerpts['root_outer_host_request_builder'] = dict(source=pins['root_outer_host_request_builder'], ranges=[dict(first=28, last=40, lines=[dict(line=i + 1, text=outer_lines[i]) for i in range(27, 40)])])
prior = BASE / 'r10-future-join-consumption-contract-review-20261006-001/REPORT.json'
_, prior_ref = read_pin(prior, '9fba88e82ef1d2cdf49c4af9fb2fbcf973667e42de5da585e415b6212759d108')

tree = ast.parse(texts['public_tools'])
tool_names = {}
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name in ('create_server', 'create_clock_server'):
        tool_names[node.name] = [n.name for n in node.body if isinstance(n, ast.FunctionDef) and n.decorator_list]
assert len(tool_names['create_server']) == 21
assert tool_names['create_clock_server'] == ['ck3_read_profile_native_clock_v1']
assert 'ck3_read_profile_native_clock_v1' not in tool_names['create_server']
query_names = ('ck3_query_profile_decision_item_v1', 'ck3_open_profile_decisions_v1', 'ck3_select_profile_decision_item_v1', 'ck3_confirm_profile_decision_outcome_v1')
assert all(n in tool_names['create_server'] for n in query_names)
assert 'boolean("row_widget_datacontext_verified",false);boolean("action_qualified",false);' in texts['native_reader']
assert 'model observation cannot qualify a widget action' in texts['query_contract']
assert 'if(!button->effective_visible||!button->enabled)continue;' in texts['native_reader']
assert 'date_raw=53144712' in outer_lines[36]

sdk_raw, sdk_ref = read_pin(SDK, EXPECTED_SDK)
assert sdk_ref['bytes'] == 4753
sdk = json.loads(sdk_raw)
receipt = sdk['structuredContent']
assert sdk['isError'] is False and sdk['resultType'] == 'complete'
assert json.loads(sdk['content'][0]['text']) == receipt
result = receipt['result']
required = dict(schema='ck3-ingame-decision-item-v1', step='query-ingame-decision-item-v1', read_only=True,
                native_revision=90, queried_revision=91, connection_generation=1, game_pid=13436,
                played_character_id=31254, date_raw=53144712, group_count=6, row_count=34,
                matching_row_count=1, decision_key='lyd_c2_propose_detach_decision', available=True,
                action_qualified=False, row_widget_datacontext_verified=False, detail_root_visible=False,
                detail_definition_available=False, detail_definition_matches_target=False,
                detail_actor_binding_verified=False, detail_actor_reference_key=-1, detail_decision_key='', unavailable_reason='')
for key, value in required.items():
    assert type(result[key]) is type(value) and result[key] == value, key
for key in ('owner_thread_verified', 'frame_verified', 'source_abi_pins_verified', 'gui_owner_binding_verified', 'decisions_tree_complete', 'decisions_root_visible', 'row_owner_verified'):
    assert result[key] is True, key
assert not any(key in result for key in ('enabled', 'is_valid', 'requirements_satisfied', 'cooldown_rejected'))
assert receipt['status'] == 'native_decision_query_observed'
assert receipt['business_effects_verified'] is False and receipt['full_product_acceptance_credit'] is False
assert receipt['session_id'] == '53bd96329c5541f7a403c5cecf61d8ba'
assert receipt['profile_sha256'] == '2f7140598909b5f34484ab74941ead7e26c32ad416aca0ebfcabc71b93573db6'

report = dict(
    schema='lyd.r10-decision-cooldown-query-boundary-independent-review.v1',
    status='ACTUAL_SDK193_ROW_OBSERVATION_VALIDITY_NOT_EXPOSED',
    recorded_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    source_authority=dict(head=HEAD, export_root=str(SOURCE), basis='ROOT-frozen exact export and per-file immutable bytes; no Git invocation'),
    source_inputs=pins, observed_sdk=sdk_ref, observed_receipt=receipt,
    public_surface=dict(profile_server_tool_count=21, profile_server_tools=tool_names['create_server'], separate_clock_server_tools=tool_names['create_clock_server']),
    findings=[
        dict(id='available', conclusion='Native query available=true means exact-build, fresh paused actor/frame, GUI root/tree/owner and stable unique keyed decision model row observation succeeded. It does not expose product is_valid, requirement satisfaction, or button enabled.', source='native_reader', lines=[326, 379]),
        dict(id='action_qualified', conclusion='The native serializer always writes action_qualified=false and row_widget_datacontext_verified=false; Python normalization requires both false. These are deliberate query credit boundaries, not computed refusal flags. Selecting the detail does not change that meaning.', source='native_reader/query_contract', lines=[400, 24, 25]),
        dict(id='detail', conclusion='Selected detail fields report definition identity, actor binding, tree completeness and visibility only. SDK193 has no selected visible detail. A selected detail query still has no enabled/is_valid field.', source='native_reader/action_contract', lines=[365, 370, 57, 63]),
        dict(id='confirm', conclusion='Internal ConfirmReceiver checks enabled plus visible, tree shape, context and dispatch identity on a mutation path. The public confirm_outcome tool can dispatch a business action; it is not a read-only validity query. fixed_visible_confirm_receiver_unqualified is broad and cannot uniquely attribute cooldown.', source='native_reader/public_tools', lines=[278, 305, 454, 839, 844]),
        dict(id='product_condition', conclusion='DETACH is_shown lacks cooldown checks. is_valid calls lyd_c2_start_detach_trigger, which calls actor rite lyd_c2_school_free_trigger. Presence of lyd_c2_transition_cooldown OR lyd_c2_retry_cooldown on the actual actor rite makes that necessary gate false. Other conditions must not be inferred true from row presence.', source='detach_decision/detach_triggers', lines=[9, 13, 23, 29, 60, 65]),
        dict(id='outer_date', conclusion='The separately read ROOT host-request builder line37 fixes actual_release_context.date_raw=53144712. This is an outer request-builder bound, distinct from the relative-date provider/assembler rules examined previously. A later-day workflow needs an explicitly reviewed successor builder; no change or execution occurs here.', source='root_outer_host_request_builder', lines=[37]),
    ],
    cooldown_acceptance=dict(
        sdk193_actual_row_observation=True,
        sdk193_direct_enabled_observation=False,
        sdk193_direct_is_valid_observation=False,
        sdk193_direct_cooldown_rejection_credit=False,
        saved_actor_rite169_cooldown_presence='PENDING_SEPARATE_POST192_AST_READBACK; no save read in this review',
        sufficient_source_state_evidence='Bind actual source/head and immutable saved actor->rite identity plus cooldown variable presence; combine with the exact necessary trigger chain to infer eligibility=false. Label this source/state eligibility inference, not an observed MCP disabled button.',
        missing_live_dimension='An actual disabled confirm/requirements display or a future separately implemented read-only eligibility observation is needed to claim direct native/UI cooldown refusal. No such new entry point is advertised here.',
        current_public_decision_query_supports_readonly_enabled_or_is_valid=False,
        confirm_as_readonly_probe_allowed=False,
    ),
    prior_report_scope_preserved=dict(report=prior_ref, immutable_bytes_still_exact=True, correction='This append adds the ROOT outer builder, which was outside that earlier source review scope.'),
    actual_flags=dict(game_actions=0, mcp_calls=0, process_reads=0, pipe_calls=0, git_calls=0, main_writes=0,
                      registry_writes=0, host_release_calls=0, provider_binder_emitter_calls=0, save_ast_reads=0,
                      old_tests_rerun=0, candidate_function_execution=0, future_gate_pass=False,
                      business_acceptance_credit=False, full_cycle_acceptance_credit=False),
    method='Static exact source/hash/AST registration inspection plus one existing 4753-byte SDK JSON. Source assertions are report integrity checks, not a runtime test suite.',
)
write_new('SOURCE-EXCERPTS.json', excerpts)
write_new('REPORT.json', report)
with (OUT / 'SDK193.actual.json').open('xb') as f:
    f.write(sdk_raw)
rows = []
for p in sorted(OUT.iterdir(), key=lambda p: p.name):
    if p.is_file() and p.name != 'INDEX.json':
        raw = p.read_bytes()
        rows.append(dict(path=p.name, bytes=len(raw), sha256=sha(raw)))
write_new('INDEX.json', dict(schema='lyd.external-evidence-index.v1', files=rows))
for p in OUT.iterdir():
    if p.is_file():
        os.chmod(p, 0o444)
for name in ('REPORT.json', 'SOURCE-EXCERPTS.json', 'INDEX.json'):
    raw = (OUT / name).read_bytes()
    print(json.dumps(dict(path=str(OUT / name), bytes=len(raw), sha256=sha(raw)), ensure_ascii=True))
