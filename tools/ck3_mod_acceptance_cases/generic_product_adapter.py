"""Reuse product emitters/assertions through the public shared case interfaces.

This module owns no host, bridge, engine identity, process, screen input, queue,
allocator, SDK or cleanup. Those operations belong to the public CaseClient.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Protocol, TypeAlias, runtime_checkable

from ck3_mod_acceptance_background_types import (
    FilePin, JsonObject, file_pin, json_object, object_field, text_field,
)

if TYPE_CHECKING:
    from ck3_mod_acceptance_client import CaseClient


class OrdinaryCaptureClient(Protocol):
    def snapshot(self, *, allow_actor_change: bool = False, require_event_free: bool = True) -> object: ...
    def root_checkpoint(self, name: str, request: JsonObject, reserve: int = 90) -> object: ...
    def checkpoint(self, name: str, value: JsonObject) -> object: ...


ORDINARY_REVIEW_ASSERTIONS = (
    'formal_product_only_ordinary_play',
    'selected_gameplay_frames_reviewed',
    'no_fixture_or_debug_visible',
    'normal_gui_actor_changes_reviewed',
)


def ordinary_contract(context: JsonObject) -> JsonObject:
    config = object_field(context, 'case_contract')
    if (set(config) != {'schema', 'product', 'case_id', 'acceptance_scope', 'source_contracts'}
            or config.get('schema') != 'ck3-ordinary-promotion-contract-v1'
            or config.get('acceptance_scope') != 'ordinary_promotion'
            or config.get('product') != context.get('product')
            or config.get('case_id') != context.get('case')):
        raise ValueError('Exact ordinary promotion contract required')
    sources = config.get('source_contracts')
    if not isinstance(sources, list) or not sources or not all(isinstance(s, str) and s for s in sources):
        raise ValueError('Ordinary promotion source contracts required')
    return config


def checked_capture_pin(value: object) -> FilePin:
    from ck3_mod_acceptance_recorder import file_identity
    expected = file_pin(value)
    actual = file_identity(expected['path'])
    if actual != expected:
        raise ValueError('Ordinary capture evidence bytes changed')
    return actual


def prepare_ordinary_capture(context: JsonObject) -> JsonObject:
    from ck3_mod_acceptance_prepare import materialize_product_profile, finish_product_profile
    ordinary_contract(context)
    inputs = object_field(context, 'case_inputs')
    if set(inputs) != {'product_dir', 'formal_product_files', 'plain_configuration'}:
        raise ValueError('Ordinary promotion accepts only formal product and four plain configurations')
    product = Path(text_field(inputs, 'product_dir')).resolve()
    expected = object_field(inputs, 'formal_product_files')
    from ck3_mod_acceptance_recorder import file_identity
    actual = {p.relative_to(product).as_posix(): file_identity(p)
              for p in product.rglob('*') if p.is_file()}
    if not expected or set(actual) != set(expected) or 'descriptor.mod' not in actual:
        raise ValueError('Exact formal product file closure required')
    for name, value in expected.items():
        row = checked_capture_pin(value)
        if row != actual[name]:
            raise ValueError('Formal product source identity differs: ' + name)
    plain = object_field(inputs, 'plain_configuration')
    profile = materialize_product_profile(context, product, plain)
    mounted = {key.removeprefix('mod-content/product/'): file_pin(row)
               for key, row in profile['files'].items() if key.startswith('mod-content/product/')}
    if set(mounted) != set(actual) or any(
            mounted[key]['bytes'] != row['bytes'] or mounted[key]['sha256'] != row['sha256']
            for key, row in actual.items()):
        raise ValueError('Mounted formal product bytes differ')
    profile = finish_product_profile(context, profile, provenance={
        'kind': 'ordinary-gui-promotion', 'fixture_mounted': False,
        'formal_product_files': actual, 'business_acceptance': 'NOT_ASSESSED'})
    initial = Path(text_field(context, 'output')) / 'initial-plan.json'
    write_once(initial, {'steps': []})
    return json_object({'startup': {'mode': 'ordinary_gui_campaign', 'state_dir': profile['state_dir']},
        'initial_plan': pin(initial), 'profile': profile, 'formal_file_count': len(actual),
        'business_contract_applicable': False, 'runtime_status': 'NOT_RUN',
        'business_pass': False, 'product_release_pass': False})


def validate_ordinary_capture_evidence(context: JsonObject, response: JsonObject) -> JsonObject:
    ordinary_contract(context)
    if (response.get('run_id') != context.get('run_id') or response.get('reviewer') != '/root'
            or response.get('status') != 'complete'):
        raise ValueError('Ordinary promotion review crossed run/operator')
    assertions = object_field(response, 'assertions')
    if set(assertions) != set(ORDINARY_REVIEW_ASSERTIONS) or any(
            assertions[name] is not True for name in ORDINARY_REVIEW_ASSERTIONS):
        raise ValueError('Actual Root gameplay frame review required; recorder ACK is insufficient')
    frozen = json_object(read_json(Path(text_field(context, 'run_dir')) / 'frozen-argv.json'))
    if frozen.get('run_id') != context.get('run_id'):
        raise ValueError('Ordinary promotion frozen run differs')
    config_pin = checked_capture_pin(response.get('recorder_config'))
    frozen_config = object_field(object_field(frozen, 'files'), config_pin['path'])
    if frozen_config != {'bytes': config_pin['bytes'], 'sha256': config_pin['sha256']}:
        raise ValueError('Recorder configuration is not allocated to this run')
    config = json_object(read_json(config_pin['path']))
    if config.get('schema') != 'ck3-mod-acceptance-recording-config-v2':
        raise ValueError('Ordinary promotion requires bounded segmented capture')
    capture_root = Path(text_field(config, 'capture_root')).resolve()
    captures = response.get('captures')
    if not isinstance(captures, list) or not 1 <= len(captures) <= 4:
        raise ValueError('Actual bounded capture finals required')
    finals: list[JsonObject] = []
    paths: set[Path] = set()
    for value in captures:
        final_pin = checked_capture_pin(value)
        path = Path(final_pin['path']).resolve()
        if path in paths or not path.is_relative_to(capture_root) or path.name != 'recorder-final.json':
            raise ValueError('Capture final crossed allocated capture root or repeated')
        paths.add(path)
        final = json_object(read_json(path))
        job = object_field(final, 'job')
        raw = checked_capture_pin(final.get('raw'))
        if (final.get('schema') != 'ck3-mod-acceptance-recorder-final-v2'
                or final.get('machine_id') != config.get('machine_id')
                or final.get('result') != 'ENCODED_UNREVIEWED'
                or final.get('budget_qualified') is not True
                or type(final.get('probe_exit_code')) is not int or final['probe_exit_code'] != 0
                or job.get('state') != 'NORMAL_TREE_EMPTY'
                or type(job.get('job_active_processes')) is not int or job['job_active_processes'] != 0
                or Path(raw['path']).resolve() != path.parent / 'raw-gameplay.mkv'):
            raise ValueError('Actual recorder terminal/probe/tree/budget qualification required')
        finals.append(json_object(final_pin))
    evidence = response.get('evidence')
    if not isinstance(evidence, list) or not evidence:
        raise ValueError('Ordinary promotion native and visual evidence required')
    for row in evidence:
        checked_capture_pin(row)
    return json_object({'recorder_config': config_pin, 'captures': finals, 'evidence': evidence,
                        'clean_spans_certified': False, 'human_review_performed': False})


def ordinary_capture_actor_transition(before: JsonObject, after: JsonObject) -> JsonObject:
    def binding(frame: JsonObject) -> tuple[int, int, int]:
        actor = object_field(frame, 'played_character')
        diagnostics = object_field(frame, 'diagnostics')
        hello = object_field(diagnostics, 'hello')
        values = (diagnostics.get('bridge_pid'), diagnostics.get('connection_generation'), actor.get('character_id'))
        if (frame.get('source') != 'injected-dll-named-pipe' or frame.get('backend_id') != 'native-headless'
                or frame.get('episode_projection') != 'native_campaign' or frame.get('map_ready') is not True
                or frame.get('paused') is not True or actor.get('source') != 'native' or actor.get('alive') is not True
                or any(type(value) is not int or value <= 0 for value in values)
                or type(hello.get('pid')) is not int or type(hello.get('connection_generation')) is not int
                or hello.get('ck3_build_match') is not True
                or hello.get('pid') != values[0] or hello.get('connection_generation') != values[1]):
            raise ValueError('Actual ordinary capture native identity required')
        pid, generation, character = values
        if type(pid) is not int or type(generation) is not int or type(character) is not int:
            raise ValueError('Actual ordinary capture integer identity required')
        return pid, generation, character

    initial, final = binding(before), binding(after)
    if initial[:2] != final[:2]:
        raise ValueError('Ordinary capture crossed actual bridge/connection')
    return json_object({'bridge_pid': initial[0], 'connection_generation': initial[1],
                        'initial_actor_id': initial[2], 'final_actor_id': final[2],
                        'actor_changed': initial[2] != final[2],
                        'selection_route': 'normal_gui', 'inheritance_inferred': False})


def run_ordinary_capture(context: JsonObject, client: OrdinaryCaptureClient) -> JsonObject:
    config = ordinary_contract(context)
    profile = Path(text_field(context, 'state_dir')) / 'profile'
    if (read_json(profile / 'dlc_load.json').get('enabled_mods') != ['mod/product.mod']
            or (profile / 'mod/fixture.mod').exists() or (profile / 'mod-content/fixture').exists()):
        raise ValueError('Ordinary promotion requires the formal product alone')
    before = json_object(client.snapshot(require_event_free=False))
    response = json_object(client.root_checkpoint('ordinary-promotion-capture', json_object({
        'scope': config['acceptance_scope'], 'actual_initial_native_frame': before,
        'required_result_fields': ['status', 'run_id', 'reviewer', 'recorder_config', 'captures', 'evidence', 'assertions'],
        'required_assertions': list(ORDINARY_REVIEW_ASSERTIONS),
        'action': 'Normal GUI gameplay and same-keeper bounded recording; no fixture or forced outcomes',
        'business_pass': False}), reserve=180))
    media = validate_ordinary_capture_evidence(context, response)
    after = json_object(client.snapshot(allow_actor_change=True, require_event_free=False))
    transition = ordinary_capture_actor_transition(before, after)
    facts = json_object({'schema': 'ck3-ordinary-promotion-result-v2', 'run_id': context['run_id'],
        'product': context['product'], 'case': context['case'], 'review': response, 'media': media,
        'initial_native_frame': before, 'final_native_frame': after, 'fixture_mounted': False,
        'actor_transition': transition,
        'raw_frame_review_performed_by_root': True,
        'case_contract_qualified': True, 'gui_contract_qualified': True,
        'business_contract_applicable': False, 'business_pass': False, 'product_release_pass': False,
        'result_boundary': 'CAPTURED_UNREVIEWED_NOT_FINAL_VIDEO'})
    client.checkpoint('ordinary-promotion-result', facts)
    return facts


def verify_ordinary_capture(context: JsonObject) -> JsonObject:
    ordinary_contract(context)
    path = Path(text_field(context, 'output')) / 'ordinary-promotion-result.json'
    facts = json_object(read_json(path))
    if any(facts.get(key) != context.get(key) for key in ('run_id', 'product', 'case')):
        raise ValueError('Ordinary promotion result crossed scene')
    if facts.get('schema') != 'ck3-ordinary-promotion-result-v2':
        raise ValueError('Explicit ordinary capture actor contract required')
    validate_ordinary_capture_evidence(context, object_field(facts, 'review'))
    transition = ordinary_capture_actor_transition(
        object_field(facts, 'initial_native_frame'), object_field(facts, 'final_native_frame'))
    if object_field(facts, 'actor_transition') != transition:
        raise ValueError('Ordinary capture actor transition differs from actual frames')
    return facts


def require(value: object, message: str) -> None:
    if not value:
        raise ValueError(message)


def pin(path: str | Path) -> FilePin:
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def read_json(path: str | Path) -> JsonObject:
    return json_object(json.loads(Path(path).read_text(encoding='utf-8-sig')))


def write_once(path: str | Path, value: JsonObject) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def literal_inventory(repo, reference):
    """Read existing literal assertion lists; never import a legacy live runner."""
    path = Path(repo) / reference['path']
    tree = ast.parse(path.read_text(encoding='utf-8-sig'))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == reference['name'] for t in node.targets):
            values = ast.literal_eval(node.value)
            require(isinstance(values, (list, tuple)) and all(isinstance(v, str) for v in values),
                    'Original marker list changed: ' + str(path))
            return list(values), pin(path)
    raise ValueError('Original product assertion list missing: ' + str(path))


def resolve_post_start(context):
    contract = copy.deepcopy(context['case_contract'])
    post = contract['post_start']
    actual = context['case_inputs'].get('post_start', {})
    require(set(actual) <= set(post), 'Unknown ordinary bookmark post-start field')
    for key, value in actual.items():
        require(post[key] is None or post[key] == value, 'Cannot overwrite original product post-start predicate')
        if post[key] is None:
            post[key] = value
    require(all(v is not None for v in post.values()),
            'Original ordinary bookmark government/tier/independence needs actual selected-bookmark input')
    require(type(post['independent']) is bool, 'Actual independence is a strict boolean')
    # Validation/standard tier definitions belong to the one selected helper.
    context = dict(context)
    context['case_contract'] = contract
    return context


def _saved_fixture_startup(context: JsonObject, profile: JsonObject) -> JsonObject:
    """Bind an explicit saved input to the existing role-bound shared inventory."""
    from ck3_mod_acceptance_saved_profile_v2 import write_saved_profile_inventory_v2
    from ck3_mod_acceptance_prepare import fixture_enabled_mods
    saved = object_field(context, 'saved_campaign')
    if set(saved) != {'save', 'bytes', 'sha256', 'player_id', 'date_raw'}:
        raise ValueError('Saved fixture input requires exactly save/bytes/sha256/player_id/date_raw')
    expected = file_pin({'path': text_field(saved, 'save'), 'bytes': saved['bytes'], 'sha256': saved['sha256']})
    actual = pin(expected['path'])
    if actual != expected or Path(expected['path']).suffix.casefold() != '.ck3':
        raise ValueError('Actual immutable external .ck3 input differs from its source pin')
    for field in ('player_id', 'date_raw'):
        value = saved[field]
        if type(value) is not int or not isinstance(value, int) or not 0 < value < 2**31:
            raise ValueError('Saved fixture input requires exact positive bounded integer ' + field)
    profile_path = Path(text_field(profile, 'profile'))
    if Path(expected['path']).is_relative_to(profile_path):
        raise ValueError('Saved fixture input must remain outside the new profile')
    files = object_field(profile, 'files')
    product_files = [file_pin(row) for relative, row in files.items()
                     if relative.startswith(('mod/', 'mod-content/'))]
    enabled = fixture_enabled_mods(profile_path)
    from ck3_mod_acceptance_saved_profile_v2 import Role
    roles: dict[str, Role] = {descriptor: ('case_fixture' if descriptor == 'mod/fixture.mod' else 'formal_product')
                                 for descriptor in enabled}
    inventory = write_saved_profile_inventory_v2(Path(text_field(context, 'output')) / 'saved-fixture-inventory-v2.json',
        profile=profile_path, mode='enabled', enabled_mods=enabled,
        product_files=product_files, roles=roles)
    return json_object({'mode': 'saved_campaign', 'state_dir': text_field(context, 'state_dir'),
        'saved_campaign': {**saved, 'product_inventory': inventory['path']}})


def _prepare_fixture_case(context):
    from ck3_mod_acceptance_prepare import (invoke_fixture_prepare, materialize_fixture_profile,
                                           compatibility_mods, compatibility_mods_json)
    context = resolve_post_start(context)
    config = context['case_contract']
    require(config['product'] == context['product'], 'Case crossed canonical product')
    inputs = context['case_inputs']
    compatibility = compatibility_mods(inputs)
    product_loading = config.get('product_loading', 'present')
    require(product_loading in ('present', 'absent'), 'Explicit product loading mode required')
    if product_loading == 'absent':
        require(inputs.get('product_dir') is None, 'Pre-product case cannot mount a formal product')
        require(not compatibility, 'Pre-product case cannot mount compatibility mods')
        product = None
    else:
        product = Path(inputs['product_dir']).resolve()
        require((product / 'descriptor.mod').is_file(), 'Already built exact product projection required')
    output = Path(context['output'])
    emitter = config.get('fixture_emitter')
    prebuilt = config.get('fixture_source')
    emitted = None
    if prebuilt is not None:
        from ck3_mod_acceptance_prepare import materialize_prebuilt_fixture
        if prebuilt != {'kind': 'prebuilt_manifest'} or emitter is not None:
            raise ValueError('Prebuilt fixture source cannot include a legacy emitter')
        fixture, prebuilt_receipt, prebuilt_emission = materialize_prebuilt_fixture(
            json_object(context), inputs.get('prebuilt_fixture_manifest'), output / 'prebuilt-fixture')
        receipt = json_object(prebuilt_receipt)
        emitted = json_object(prebuilt_emission)
    elif emitter:
        generated = output / 'original-fixture-emission'
        args = [s.format(output=str(generated), repo=context['repo_root'], product_dir=str(product))
                for s in emitter['arguments']]
        emitted = invoke_fixture_prepare(context, Path(context['repo_root']) / emitter['path'], args)
        fixture = generated / emitter.get('fixture_subdir', '')
        receipt = read_json(Path(str(generated) + emitter['receipt_suffix']) if 'receipt_suffix' in emitter
                            else generated / emitter['receipt_relative'])
    else:
        # Product-only load boundary: no business effect, actor or marker setter.
        if product is None:
            raise ValueError('A pre-product fixture requires an explicit frozen fixture source')
        fixture = output / 'empty-load-carrier'
        fixture.mkdir()
        text = (product / 'descriptor.mod').read_text(encoding='utf-8-sig')
        text = re.sub(r'^\s*(?:path|remote_file_id)\s*=.*\n?', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*name\s*=.*$', 'name="Acceptance load carrier (no business scripts)"', text, flags=re.MULTILINE)
        (fixture / 'descriptor.mod').write_text(text, encoding='utf-8')
        receipt = {'required_markers': [], 'fixture_contains_business_effects': False}
    required = list(receipt.get('required_markers', receipt.get('expected_pass_markers', [])))
    source_pins = []
    if not required and config.get('marker_inventory'):
        required, source = literal_inventory(context['repo_root'], config['marker_inventory'])
        source_pins.append(source)
    for name in ('required_start', 'required_end', 'required_additional_marker'):
        if receipt.get(name):
            required.append(receipt[name])
    required += receipt.get('required_additional_markers', [])
    required = list(dict.fromkeys(required))
    require(required or config['acceptance_scope'] == 'static_and_basicload', 'Full business case has no original assertions')
    compiled = {
        'schema': 'ck3-mod-acceptance-product-assertions-v1', 'product': context['product'],
        'case': context['case'], 'config': config, 'required_markers': required,
        'product_marker_minimum': receipt.get('required_product_markers_minimum', {}),
        'original_receipt': receipt, 'assertion_source_pins': source_pins,
        'emitter': emitted, 'product_descriptor': pin(product / 'descriptor.mod') if product is not None else None,
        'whole_product_release_pass': False,
        'compatibility_mods': compatibility_mods_json(compatibility),
        'enabled_mods': (['mod/' + mod.mount_name + '.mod' for mod in compatibility]
                         + (['mod/product.mod'] if product is not None else []) + ['mod/fixture.mod']),
    }
    write_once(fixture / '_case_contract.json', compiled)
    profile = materialize_fixture_profile(context, fixture, product, inputs['plain_configuration'],
                                          compatibility=compatibility)
    initial = output / 'initial-plan.json'
    write_once(initial, {'steps': []})
    startup: JsonObject = {'mode': 'fixture', 'state_dir': profile['state_dir'],
               'fixture_start_policy': profile['fixture_start_policy']}
    if config.get('startup_mode') == 'saved_campaign':
        require(product_loading == 'present', 'Saved fixture startup requires the actual formal product')
        # Materialization caches a private (module, identity) engine in context.
        # Only the saved-startup public fields belong to the JSON boundary.
        startup = _saved_fixture_startup(json_object({
            'saved_campaign': context['saved_campaign'], 'output': context['output'],
            'state_dir': context['state_dir']}), json_object(profile))
    if config.get('frontend_rules'):
        rules = output / 'frontend-rules-plan.json'
        write_once(rules, {'schema': 'ck3-frontend-rules-plan-v1', 'schema_version': 1,
                           'rules': config['frontend_rules']})
        startup['frontend_rules_plan'] = str(rules)
    return {'startup': startup,
            'initial_plan': pin(initial), 'profile_preparation': profile,
            'assertion_contract': pin(Path(profile['profile']) / 'mod-content/fixture/_case_contract.json'),
            'business_contract_applicable': config['acceptance_scope'] != 'static_and_basicload',
            'runtime_status': 'NOT_RUN', 'business_pass': False, 'product_release_pass': False}


def compiled_contract(context):
    path = Path(context['state_dir']) / 'profile/mod-content/fixture/_case_contract.json'
    contract = read_json(path)
    require(contract['product'] == context['product'] and contract['case'] == context['case'],
            'Prepared assertion contract crossed product/case')
    return contract, pin(path)


def marker_observation(raw, compiled):
    text = raw.decode('utf-8-sig', errors='replace')
    counts = {marker: text.count(marker) for marker in compiled['required_markers']}
    duplicate = {marker: count for marker, count in counts.items() if count > 1}
    missing = [marker for marker, count in counts.items() if count == 0]
    minima = {marker: {'actual': text.count(marker), 'minimum': minimum}
              for marker, minimum in compiled['product_marker_minimum'].items()}
    failures = [line for line in text.splitlines() if any(prefix in line for prefix in compiled['config']['failure_prefixes'])
                and any(token in line for token in ('TEST FAIL', 'MECHANISM CASE FAIL', ': FAIL '))]
    return {'counts': counts, 'missing': missing, 'duplicates': duplicate, 'failure_lines': failures,
            'product_marker_minimum': minima, 'qualified': not missing and not duplicate and not failures
            and all(v['actual'] >= v['minimum'] for v in minima.values())}


def root_phase(client, context, name, requirements, snapshot, source_contract):
    response = client.root_checkpoint(name, {
        'product': context['product'], 'case': context['case'], 'scope': source_contract['config']['acceptance_scope'],
        'action': 'Use original production UI / typed current context and original verifiers; preserve actual evidence',
        'required_assertions': requirements, 'actual_snapshot': snapshot,
        'original_contract_sources': source_contract['config']['source_contracts'],
        'no_business_PASS_from_ACK': True, 'no_replay_after_submission': True,
    }, reserve=90)
    require(response.get('run_id') == context['run_id'] and response.get('reviewer') == '/root', 'Root phase crossed live scene')
    assertions = response.get('assertions', {})
    require(all(assertions.get(key) is True for key in requirements), 'Original product GUI/semantic requirements incomplete')
    require(response.get('evidence'), 'Actual original GUI/readback evidence required')
    for row in response['evidence']:
        actual = pin(row['path'])
        require(actual['bytes'] == row['bytes'] and actual['sha256'] == row['sha256'].lower(), 'Root evidence bytes changed')
    client.checkpoint(name + '-accepted', response)
    return response


@runtime_checkable
class FixtureDayClient(Protocol):
    def advance_day(self, days: int = 1, timeout: float = 300,
                    allow_event_boundary: bool = False,
                    allow_actor_change: bool = False) -> dict[str, object]: ...
    def execute_plan(self, steps: list[dict[str, object]], name: str,
                     timeout: float | None = None,
                     reserve: int = 90) -> list[dict[str, object]]: ...


def _advance_fixture_day(client: FixtureDayClient, config: object,
                         sequence: object, timeout: object) -> JsonObject:
    """Use the public bounded day route, preserving explicit succession waits."""
    if not isinstance(client, FixtureDayClient):
        raise ValueError('Fixture day requires the public natural-day client contract')
    policy = json_object(config)
    actor_change = policy.get('allow_actor_change', False)
    transitions = policy.get('actor_transition_days', [])
    if type(actor_change) is not bool or not isinstance(actor_change, bool):
        raise ValueError('Fixture actor-change policy must be a literal boolean')
    if not isinstance(transitions, list) or any(
            type(day) is not int or not isinstance(day, int) or day <= 0
            for day in transitions):
        raise ValueError('Fixture transition days must be positive integer sequences')
    if len(transitions) != len(set(transitions)):
        raise ValueError('Fixture transition day sequences must be unique')
    if type(sequence) is not int or not isinstance(sequence, int) or sequence <= 0:
        raise ValueError('Fixture day sequence must be a positive integer')
    if (type(timeout) not in (int, float) or not isinstance(timeout, (int, float))
            or not math.isfinite(timeout) or timeout <= 0):
        raise ValueError('Fixture day timeout must be finite and positive')
    if sequence in transitions:
        # The public day method has no wait-for-successor argument. Preserve
        # this existing, explicitly selected legacy contract without replay.
        name = 'product-natural-day-' + str(sequence).zfill(3)
        step: dict[str, object] = {'id': name, 'kind': 'advance_day', 'days': 1,
                                  'timeout': timeout, 'wait_for_played_character_change': True}
        rows = client.execute_plan([step], name)
        if len(rows) != 1:
            raise ValueError('One actual fixture transition day row required')
        return json_object(rows[0])
    return json_object(client.advance_day(days=1, timeout=timeout,
                       allow_event_boundary=True, allow_actor_change=actor_change))


def _fixture_boundary(frame: object) -> Literal['event', 'notification'] | None:
    snapshot = json_object(frame)
    if snapshot.get('active_event') is not None:
        return 'event'
    if snapshot.get('pending_character_interaction') is not None:
        return 'notification'
    return None


def _require_fixture_boundary_resolved(before: object, after: object,
                                       boundary: Literal['event', 'notification']) -> None:
    key = 'active_event' if boundary == 'event' else 'pending_character_interaction'
    original = json_object(json_object(before).get(key))
    original_id = original.get('instance_id')
    if type(original_id) is not int or not isinstance(original_id, int) or original_id <= 0:
        raise ValueError('Actual boundary requires a positive native instance ID')
    current = json_object(after).get(key)
    if current is None:
        return
    current_id = json_object(current).get('instance_id')
    if (type(current_id) is not int or not isinstance(current_id, int)
            or current_id <= 0 or current_id == original_id):
        raise ValueError('Actual boundary remains unresolved; never advance or replay')


def _run_fixture_case(context, client):
    compiled, binding = compiled_contract(context)
    config = compiled['config']
    frame = client.snapshot(require_event_free=False)
    frames = [{'day': 0, 'snapshot': frame}]
    initial_date = frame.get('date_raw')
    require(type(initial_date) is int, 'Actual initial native calendar is required')
    phases = {}
    static_load_only = config['acceptance_scope'] == 'static_and_basicload'
    profile = Path(context['state_dir']) / 'profile'
    enabled_value = read_json(profile / 'dlc_load.json')['enabled_mods']
    if not isinstance(enabled_value, list):
        raise ValueError('Actual enabled_mods must be a string array')
    enabled: list[str] = []
    for descriptor in enabled_value:
        if not isinstance(descriptor, str) or not descriptor:
            raise ValueError('Actual enabled_mods must contain nonempty descriptor paths')
        enabled.append(descriptor)
    expected_enabled = compiled.get('enabled_mods',
        ['mod/fixture.mod'] if config.get('product_loading', 'present') == 'absent'
        else ['mod/product.mod', 'mod/fixture.mod'])
    require(enabled == expected_enabled, 'Actual independent mod load order differs from the prepared contract')
    if config.get('product_loading', 'present') == 'absent':
        require('mod/product.mod' not in enabled and not (profile / 'mod/product.mod').exists()
                and not (profile / 'mod-content/product').exists(), 'Pre-product campaign unexpectedly mounted a product')
    else:
        require('mod/product.mod' in enabled, 'Actual prepared product is not mounted')
        require((profile / 'mod/product.mod').is_file() and (profile / 'mod-content/product/descriptor.mod').is_file(),
                'Actual product descriptors missing')
    observed = {'qualified': static_load_only, 'counts': {}, 'missing': [], 'duplicates': {}, 'failure_lines': [], 'product_marker_minimum': {}}
    if not static_load_only:
        sequence = 0
        boundary_sequence = 0
        while True:
            require(type(frame.get('date_raw')) is int and frame['date_raw'] >= initial_date,
                    'Actual native calendar moved backwards')
            day = (frame['date_raw'] - initial_date) / 24
            require(day <= config['maximum_natural_days'], 'Shared case natural calendar upper bound exceeded')
            observed = marker_observation(client.log_bytes(), compiled)
            require(not observed['failure_lines'] and not observed['duplicates'], 'Original product fixture failed; never replay')
            for phase in config['gui_phases']:
                if phase['id'] in phases:
                    continue
                ready = (phase.get('at_day') is not None and day >= phase['at_day']) or any(
                    observed['counts'].get(marker, 0) for marker in phase.get('when_markers', []))
                if ready:
                    phases[phase['id']] = root_phase(client, context, phase['id'], phase['requirements'], frame, compiled)
                    frame = client.snapshot(allow_actor_change=config.get('allow_actor_change', False), require_event_free=False)
                    frames.append({'day': day, 'after_gui': phase['id'], 'snapshot': frame})
                    require(type(frame.get('date_raw')) is int and frame['date_raw'] >= initial_date,
                            'Actual native calendar after GUI is required')
                    day = (frame['date_raw'] - initial_date) / 24
                    require(day <= config['maximum_natural_days'], 'GUI phase exceeded shared case calendar bound')
                    observed = marker_observation(client.log_bytes(), compiled)
            # An actual event is handled by Root from its current instance. Never
            # invent an option index or claim that dispatch proves a GUI outcome.
            boundary = _fixture_boundary(frame)
            if boundary is not None:
                boundary_sequence += 1
                name = 'actual-' + boundary + '-boundary-' + str(boundary_sequence).zfill(3)
                assertion = ('actual_current_event_resolved_with_typed_or_reviewed_original_evidence'
                             if boundary == 'event' else
                             'actual_pending_character_interaction_resolved_with_typed_or_reviewed_original_evidence')
                phases[name] = root_phase(client, context, name, [assertion], frame, compiled)
                successor = client.snapshot(allow_actor_change=config.get('allow_actor_change', False), require_event_free=False)
                _require_fixture_boundary_resolved(frame, successor, boundary)
                frame = successor
                frames.append({'day': (frame['date_raw'] - initial_date) / 24,
                               'after_boundary': name, 'snapshot': frame})
                continue
            if observed['qualified'] and all(phase['id'] in phases for phase in config['gui_phases']):
                break
            require(day < config['maximum_natural_days'], 'Shared case day upper bound reached; missing original product assertions retained')
            sequence += 1
            row = _advance_fixture_day(client, config, sequence, context['case_spec']['budgets']['command_timeout'])
            value = row['result']
            require(value.get('requested_days') == 1 and
                    (value.get('requested_interval_complete') is True or value.get('event_boundary') is not None),
                    'Neither actual day completion nor an actual event boundary was observed')
            before, after = value['before'], value['after']
            require(type(after.get('date_raw')) is int and type(before.get('date_raw')) is int,
                    'Actual natural interval is missing native calendar fields')
            elapsed = after['date_raw'] - before['date_raw']
            require(
                    ((24 <= elapsed < 48) if value.get('requested_interval_complete') is True
                     else 0 <= elapsed < 48), 'Actual natural interval/event boundary is malformed')
            if after.get('played_character', {}).get('alive') is False and config.get('continue_as_heir_requirements'):
                phases['original-continue-as-heir'] = root_phase(client, context, 'original-continue-as-heir',
                    config['continue_as_heir_requirements'], after, compiled)
            # Full actual rows remain retained by the common client. Refresh from
            # the same live owner, admitting only the original actor transition.
            frame = client.snapshot(allow_actor_change=config.get('allow_actor_change', False), require_event_free=False)
            frames.append({'day': (frame['date_raw'] - initial_date) / 24, 'sequence': sequence, 'snapshot': frame})
        observed = marker_observation(client.log_bytes(), compiled)
        require(observed['qualified'], 'Original marker assertions remain incomplete after GUI/day work')
    process = getattr(client, '_process', None)
    facts = {'schema': 'ck3-mod-acceptance-product-case-facts-v1', 'run_id': context['run_id'],
        'product': context['product'], 'case': context['case'], 'compiled_contract': binding,
        'acceptance_scope': config['acceptance_scope'], 'business_contract_applicable': not static_load_only,
        'load_boundary_qualified': True, 'actual_native_frames': frames, 'actual_process': process,
        'enabled_mods': enabled, 'product_outer': pin(profile / 'mod/product.mod'),
        'product_inner': pin(profile / 'mod-content/product/descriptor.mod'),
        'marker_observation': observed, 'root_phases': phases,
        'case_contract_qualified': observed['qualified'], 'gui_contract_qualified': static_load_only or all(
            phase['id'] in phases for phase in config['gui_phases']),
        'result_boundary': 'LOAD_BOUNDARY_PASS' if static_load_only else 'SOURCE_CASE_OBSERVED_PENDING_PRODUCT_AGGREGATION',
        'pending_product_business': config.get('uncovered_product_business', []),
        'business_pass': False, 'product_release_pass': False}
    client.checkpoint('generic-product-case-result', facts)
    return facts


def _verify_fixture_case(context):
    path = Path(context['output']) / 'generic-product-case-result.json'
    if not path.is_file():
        return {'case_contract_qualified': False, 'gui_contract_qualified': False,
                'business_pass': False, 'product_release_pass': False, 'status': 'NOT_RUN'}
    facts = read_json(path)
    require(facts['run_id'] == context['run_id'] and facts['product'] == context['product'] and facts['case'] == context['case'],
            'Original actual case result crossed run/product/case')
    compiled, binding = compiled_contract(context)
    require(binding == facts['compiled_contract'], 'Prepared original assertion contract changed')
    for phase in facts['root_phases'].values():
        require(phase.get('run_id') == context['run_id'] and phase.get('reviewer') == '/root', 'Root evidence crossed session')
        for row in phase['evidence']:
            actual = pin(row['path'])
            require(actual['bytes'] == row['bytes'] and actual['sha256'] == row['sha256'].lower(), 'Root evidence changed')
    # Complete product release aggregation is owned by Root, including distinct
    # business cells, current version credit and publication/cache obligations.
    result = copy.deepcopy(facts)
    result.update(business_pass=False, product_release_pass=False,
                  verification_scope=compiled['config']['acceptance_scope'])
    return result


class SavedReadbackClient(Protocol):
    def snapshot(self, allow_actor_change: bool = False,
                 require_event_free: bool = True) -> JsonObject: ...
    def retain_process(self) -> JsonObject: ...
    def root_checkpoint(self, name: str, request: JsonObject,
                        reserve: int = 90) -> JsonObject: ...
    def checkpoint(self, name: str, value: JsonObject) -> object: ...


SAVED_READBACK_MODE: Literal['monthly-natural-v1'] = 'monthly-natural-v1'
SAVED_READBACK_REQUIREMENTS = (
    'actual_new_pid_and_creation_identity_bound_to_this_loaded_run',
    'same_source_checkpoint_player_date_and_twelve_full_character_ids',
    'source_and_cold_saves_independently_decoded_and_exactly_compared',
    'eight_experience_two_three_alive_zero_dead_absent_and_exact_month_partner_lists',
    'zero_calendar_days_zero_fixture_initializations_zero_business_replay',
)


@dataclass(frozen=True)
class MissingValue:
    state: Literal['missing'] = 'missing'

    def to_json(self) -> JsonObject:
        return {'state': self.state}


@dataclass(frozen=True)
class NullValue:
    state: Literal['null'] = 'null'

    def to_json(self) -> JsonObject:
        return {'state': self.state}


@dataclass(frozen=True)
class IntegerValue:
    value: int
    state: Literal['value'] = 'value'

    def to_json(self) -> JsonObject:
        return {'state': self.state, 'value': self.value}


@dataclass(frozen=True)
class PartnerValues:
    value: tuple[int, ...]
    state: Literal['value'] = 'value'

    def to_json(self) -> JsonObject:
        return json_object({'state': self.state, 'value': list(self.value)})


ScalarState: TypeAlias = MissingValue | NullValue | IntegerValue
PartnerState: TypeAlias = MissingValue | NullValue | PartnerValues


def _sr_absent(row: JsonObject, label: str) -> MissingValue | NullValue | None:
    if row.get('state') == 'missing':
        _sr_keys(row, {'state'}, label)
        return MissingValue()
    if row.get('state') == 'null':
        _sr_keys(row, {'state'}, label)
        return NullValue()
    if row.get('state') != 'value':
        raise ValueError(label + ' must preserve missing, null or value explicitly')
    _sr_keys(row, {'state', 'value'}, label)
    return None


def _sr_scalar_from_validated_json(value: object, label: str) -> ScalarState:
    row = json_object(value)
    absent = _sr_absent(row, label)
    return absent if absent is not None else IntegerValue(_sr_integer(row['value'], label, positive=False))


def _sr_partners_from_validated_json(value: object, label: str) -> PartnerState:
    row = json_object(value)
    absent = _sr_absent(row, label)
    if absent is not None:
        return absent
    identities = tuple(sorted(_sr_character_id(item, label + ' full character ID')
                              for item in _sr_list(row['value'], label)))
    if len(identities) != len(set(identities)):
        raise ValueError(label + ' contains duplicate partners')
    return PartnerValues(identities)


@dataclass(frozen=True)
class SavedReadbackMode:
    reference_names: tuple[str, ...]
    expected_experience: dict[str, ScalarState]
    pairs: tuple[tuple[str, str], ...]
    passive_fixture_files: tuple[str, ...]
    product_file_count: int
    mode: Literal['monthly-natural-v1'] = SAVED_READBACK_MODE

    @classmethod
    def from_validated_json(cls, value: object) -> SavedReadbackMode:
        row = json_object(value)
        _sr_keys(row, {'mode', 'reference_names', 'expected_experience', 'pairs',
                       'passive_fixture_files', 'product_file_count'}, 'Saved-readback mode')
        count = _sr_integer(row['product_file_count'], 'Exact source runtime file count')
        if row['mode'] != SAVED_READBACK_MODE or count != 35:
            raise ValueError('Monthly saved readback requires its explicit mode and exact 35-file product projection')
        names = tuple(_sr_text(item, 'Root reference') for item in _sr_list(row['reference_names'], 'Root references'))
        if len(names) != 12 or len(set(names)) != 12 or any(not name.startswith('sxanf_ref_') for name in names):
            raise ValueError('Exactly twelve unique explicit fixture references required')
        expected = json_object(row['expected_experience'])
        _sr_keys(expected, set(names), 'Experience expectations')
        experiences = {name: _sr_scalar_from_validated_json(expected[name], 'Expected experience') for name in names}
        values = tuple(experiences.values())
        if (values.count(IntegerValue(2)) != 8 or values.count(IntegerValue(0)) != 3
                or values.count(MissingValue()) != 1):
            raise ValueError('Eight eligible XP2, three living XP0 and one dead missing-XP expectation required')
        pairs: list[tuple[str, str]] = []
        paired: list[str] = []
        for raw in _sr_list(row['pairs'], 'Eligible pairs'):
            pair = tuple(_sr_text(item, 'Pair reference') for item in _sr_list(raw, 'Pair'))
            if (len(pair) != 2 or pair[0] == pair[1]
                    or any(experiences.get(name) != IntegerValue(2) for name in pair)):
                raise ValueError('Each eligible pair must bind two distinct expected XP2 references')
            pairs.append((pair[0], pair[1]))
            paired.extend(pair)
        if len(paired) != 8 or len(set(paired)) != 8:
            raise ValueError('Exactly four disjoint eligible pairs required')
        files = tuple(_sr_text(item, 'Passive fixture member') for item in _sr_list(row['passive_fixture_files'], 'Passive fixture files'))
        if len(files) != len(set(files)) or 'descriptor.mod' not in files:
            raise ValueError('Explicit unique passive fixture inventory including descriptor required')
        for name in files:
            if Path(name).is_absolute() or '..' in Path(name).parts or name.startswith(('tools/', 'docs/', 'common/on_action/')):
                raise ValueError('Passive dependencies cannot include a registrar or escape their source')
        return cls(names, experiences, tuple(pairs), files, count)

    def to_json(self) -> JsonObject:
        return json_object({'mode': self.mode, 'reference_names': list(self.reference_names),
            'expected_experience': {name: state.to_json() for name, state in self.expected_experience.items()},
            'pairs': [list(pair) for pair in self.pairs], 'passive_fixture_files': list(self.passive_fixture_files),
            'product_file_count': self.product_file_count})


@dataclass(frozen=True)
class CharacterReadback:
    character_id: int
    alive: bool
    experience: ScalarState
    month: ScalarState
    partners: PartnerState

    @classmethod
    def from_validated_json(cls, value: object) -> CharacterReadback:
        row = json_object(value)
        _sr_keys(row, {'character_id', 'alive', 'experience', 'month', 'partners'}, 'Character readback')
        alive = row['alive']
        if not isinstance(alive, bool):
            raise ValueError('Actual boolean alive state required')
        return cls(_sr_character_id(row['character_id'], 'Full character ID'), alive,
                   _sr_scalar_from_validated_json(row['experience'], 'Experience'),
                   _sr_scalar_from_validated_json(row['month'], 'Month'),
                   _sr_partners_from_validated_json(row['partners'], 'Partners'))

    def to_json(self) -> JsonObject:
        return json_object({'character_id': self.character_id, 'alive': self.alive,
            'experience': self.experience.to_json(), 'month': self.month.to_json(), 'partners': self.partners.to_json()})


@dataclass(frozen=True)
class TwelveCharacters:
    records: dict[str, CharacterReadback]

    @classmethod
    def from_validated_json(cls, value: object, mode: SavedReadbackMode) -> TwelveCharacters:
        rows = json_object(value)
        _sr_keys(rows, set(mode.reference_names), 'Saved readback twelve references')
        records = {name: CharacterReadback.from_validated_json(rows[name]) for name in mode.reference_names}
        if len({record.character_id for record in records.values()}) != 12:
            raise ValueError('Unique full IDs required')
        for name, record in records.items():
            if (record.experience != mode.expected_experience[name]
                    or (isinstance(record.experience, MissingValue) and record.alive)
                    or (isinstance(record.experience, IntegerValue) and not record.alive)):
                raise ValueError('Actual saved experience does not match the monthly final checkpoint')
        for first_name, second_name in mode.pairs:
            first, second = records[first_name], records[second_name]
            if (first.month != second.month or not isinstance(first.month, IntegerValue) or first.month.value <= 0
                    or first.partners != PartnerValues((second.character_id,))
                    or second.partners != PartnerValues((first.character_id,))):
                raise ValueError('Exact current-month bidirectional single-partner lists required')
        months = {record.month.value for name, record in records.items()
                  if mode.expected_experience[name] == IntegerValue(2) and isinstance(record.month, IntegerValue)}
        if len(months) != 1:
            raise ValueError('All eight eligible characters must retain the same final calendar month')
        return cls(records)

    def to_json(self) -> JsonObject:
        return json_object({name: record.to_json() for name, record in self.records.items()})


@dataclass(frozen=True)
class SavedReadbackOrigin:
    machine_id: str
    run_id: str
    process_id: int
    checkpoint: FilePin
    player_id: int
    date_raw: int
    readback: FilePin
    characters: TwelveCharacters

    @classmethod
    def from_validated_json(cls, value: object, mode: SavedReadbackMode,
                            current_run: object) -> SavedReadbackOrigin:
        import ck3_live_run_id as ids
        row = json_object(value)
        _sr_keys(row, {'schema', 'machine_id', 'run_id', 'reviewer', 'process_id', 'checkpoint',
                       'player_id', 'date_raw', 'readback', 'characters'}, 'Saved-readback origin')
        machine = ids.current_machine_id()
        run = _sr_text(row['run_id'], 'Origin run ID')
        sequence = run.rsplit('--R', 1)[-1]
        canonical_run = (re.fullmatch(r'[0-9]{4,}', sequence) is not None
                         and ids.format_run_id(machine, 'superman-qiang', int(sequence), external_mod=True) == run)
        if (row['schema'] != 'ck3-mod-acceptance-saved-readback-origin-v1' or row['machine_id'] != machine
                or row['reviewer'] != '/root' or not canonical_run or run == current_run):
            raise ValueError('Actual same-machine distinct source run and explicit Root origin required')
        checkpoint = _sr_checked(row['checkpoint'])
        if Path(checkpoint['path']).suffix.casefold() != '.ck3' or checkpoint['bytes'] <= 0:
            raise ValueError('Actual immutable source .ck3 checkpoint required')
        _, readback = _sr_read(row['readback'])
        return cls(machine, run, _sr_integer(row['process_id'], 'Origin process ID'), checkpoint,
                   _sr_character_id(row['player_id'], 'Origin player full ID'),
                   _sr_integer(row['date_raw'], 'Origin saved date'), readback,
                   TwelveCharacters.from_validated_json(row['characters'], mode))

    def to_json(self) -> JsonObject:
        return json_object({'schema': 'ck3-mod-acceptance-saved-readback-origin-v1', 'reviewer': '/root',
            'machine_id': self.machine_id, 'run_id': self.run_id, 'process_id': self.process_id,
            'checkpoint': self.checkpoint, 'player_id': self.player_id, 'date_raw': self.date_raw,
            'readback': self.readback, 'characters': self.characters.to_json()})


def _sr_creation_time(value: object) -> int | float:
    if (type(value) not in (int, float) or not isinstance(value, (int, float))
            or not math.isfinite(value) or value <= 0):
        raise ValueError('Actual retained process creation time must be finite and positive')
    return value


@dataclass(frozen=True)
class RetainedProcess:
    pid: int
    create_time: int | float

    @classmethod
    def from_validated_json(cls, value: object) -> RetainedProcess:
        row = json_object(value)
        if row.get('retained_synchronize_query_handle_acquired') is not True:
            raise ValueError('Actual retained process identity must remain independently qualified')
        return cls(_sr_integer(row.get('pid'), 'Retained actual cold PID'), _sr_creation_time(row.get('create_time')))

    def to_json(self) -> JsonObject:
        return {'pid': self.pid, 'create_time': self.create_time, 'retained_synchronize_query_handle_acquired': True}


@dataclass(frozen=True)
class ColdProcessEvidence:
    run_id: str
    machine_id: str
    pid: int
    create_time: int | float
    birth_filetime: str

    @classmethod
    def from_validated_json(cls, value: object) -> ColdProcessEvidence:
        row = json_object(value)
        birth = _sr_text(row.get('birth_filetime'), 'Actual cold creation FILETIME')
        if re.fullmatch(r'[1-9][0-9]*', birth) is None or not 0 < int(birth) < 2**64:
            raise ValueError('Actual creation FILETIME must be a canonical decimal uint64 string')
        return cls(_sr_text(row.get('run_id'), 'Process run'), _sr_text(row.get('machine_id'), 'Process machine'),
                   _sr_integer(row.get('pid'), 'Independent actual cold PID'), _sr_creation_time(row.get('create_time')), birth)

    def to_json(self) -> JsonObject:
        return {'run_id': self.run_id, 'machine_id': self.machine_id, 'pid': self.pid,
                'create_time': self.create_time, 'birth_filetime': self.birth_filetime}


@dataclass(frozen=True)
class SavedReadbackContract:
    mode: SavedReadbackMode
    origin: SavedReadbackOrigin
    origin_pin: FilePin
    product_projection: FilePin
    passive_source_pins: dict[str, FilePin]

    def to_json(self, context: JsonObject) -> JsonObject:
        return json_object({'schema': 'ck3-mod-acceptance-saved-readback-contract-v1',
            'product': context['product'], 'case': context['case'], 'config': context['case_contract'],
            'origin': self.origin.to_json(), 'origin_pin': self.origin_pin,
            'product_projection': self.product_projection, 'passive_source_pins': self.passive_source_pins,
            'requirements': list(SAVED_READBACK_REQUIREMENTS), 'whole_product_release_pass': False})


@dataclass(frozen=True)
class SavedColdReadback:
    source_checkpoint: FilePin
    source_readback: FilePin
    cold_checkpoint: FilePin
    cold_readback: FilePin
    cold_checkpoint_response: FilePin
    process_evidence: FilePin
    process_id: int
    player_id: int
    date_raw: int
    characters: TwelveCharacters

    @classmethod
    def from_validated_json(cls, value: object, mode: SavedReadbackMode) -> SavedColdReadback:
        row = json_object(value)
        _sr_keys(row, {'source_checkpoint', 'source_readback', 'cold_checkpoint', 'cold_readback',
                       'cold_checkpoint_response', 'process_evidence', 'process_id', 'player_id', 'date_raw', 'characters'}, 'Saved-readback response')
        return cls(_sr_checked(row['source_checkpoint']), _sr_checked(row['source_readback']),
                   _sr_checked(row['cold_checkpoint']), _sr_read(row['cold_readback'])[1],
                   _sr_checked(row['cold_checkpoint_response']), _sr_checked(row['process_evidence']),
                   _sr_integer(row['process_id'], 'Actual cold PID'), _sr_character_id(row['player_id'], 'Cold player full ID'),
                   _sr_integer(row['date_raw'], 'Cold saved date'), TwelveCharacters.from_validated_json(row['characters'], mode))

    def to_json(self) -> JsonObject:
        return json_object({'source_checkpoint': self.source_checkpoint, 'source_readback': self.source_readback,
            'cold_checkpoint': self.cold_checkpoint, 'cold_readback': self.cold_readback,
            'cold_checkpoint_response': self.cold_checkpoint_response, 'process_evidence': self.process_evidence,
            'process_id': self.process_id, 'player_id': self.player_id, 'date_raw': self.date_raw,
            'characters': self.characters.to_json()})


@dataclass(frozen=True)
class SavedRootResponse:
    run_id: str
    evidence: tuple[FilePin, ...]
    readback: SavedColdReadback

    @classmethod
    def from_validated_json(cls, value: object, mode: SavedReadbackMode) -> SavedRootResponse:
        row = json_object(value)
        if row.get('reviewer') != '/root':
            raise ValueError('Saved-readback Root response crossed actual run/reviewer')
        assertions = json_object(row.get('assertions'))
        if set(assertions) != set(SAVED_READBACK_REQUIREMENTS) or any(item is not True for item in assertions.values()):
            raise ValueError('All exact saved-readback Root assertions require boolean true')
        evidence = tuple(_sr_checked(item) for item in _sr_list(row.get('evidence'), 'Root evidence'))
        if not evidence:
            raise ValueError('Actual independent saved-readback evidence required')
        return cls(_sr_text(row.get('run_id'), 'Root response run'), evidence,
                   SavedColdReadback.from_validated_json(row.get('saved_readback'), mode))

    def to_json(self) -> JsonObject:
        return json_object({'run_id': self.run_id, 'reviewer': '/root',
            'assertions': {name: True for name in SAVED_READBACK_REQUIREMENTS},
            'evidence': list(self.evidence), 'saved_readback': self.readback.to_json()})


@dataclass(frozen=True)
class NativeSavedCheckpoint:
    date_raw: int
    checkpoint: FilePin

    @classmethod
    def from_validated_json(cls, value: object) -> NativeSavedCheckpoint:
        row = json_object(value)
        if row.get('status') != 'saved' or row.get('episode_projection') != 'native_campaign':
            raise ValueError('Actual native cold SAVE result required; ACK is insufficient')
        return cls(_sr_integer(row.get('date_raw'), 'Actual cold SAVE date'),
                   _sr_checked({'path': _sr_text(row.get('path'), 'Actual cold SAVE path'),
                                'bytes': _sr_integer(row.get('size'), 'Actual cold SAVE bytes'),
                                'sha256': _sr_text(row.get('sha256'), 'Actual cold SAVE SHA256')}))



def _sr_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise ValueError(label + ' must be a nonempty canonical string')
    return value


def _sr_integer(value: object, label: str, *, positive: bool = True) -> int:
    if type(value) is not int or not isinstance(value, int) or (positive and value <= 0):
        raise ValueError(label + ' must be an exact integer; bool and float are rejected')
    return value


def _sr_character_id(value: object, label: str) -> int:
    identity = _sr_integer(value, label)
    if identity > 0xffffffff:
        raise ValueError(label + ' must be an actual complete uint32 CharacterID')
    return identity


def _sr_list(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(label + ' must be an explicit JSON array')
    return list(value)


def _sr_keys(value: JsonObject, fields: set[str], label: str) -> None:
    if set(value) != fields:
        raise ValueError(label + ' has unknown or missing fields')


def _sr_pin(path: Path) -> FilePin:
    before = path.stat()
    if not path.is_file() or path.is_symlink():
        raise ValueError('Evidence must be an ordinary pinned file')
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
        raise ValueError('Evidence changed while being pinned')
    return {'path': str(path.resolve()), 'bytes': after.st_size, 'sha256': digest.hexdigest()}


def _sr_checked(value: object) -> FilePin:
    row = json_object(value)
    _sr_keys(row, {'path', 'bytes', 'sha256'}, 'Evidence pin')
    path = Path(_sr_text(row['path'], 'Evidence path'))
    size = _sr_integer(row['bytes'], 'Evidence bytes', positive=False)
    sha = _sr_text(row['sha256'], 'Evidence SHA256')
    if not path.is_absolute() or size < 0 or re.fullmatch(r'[0-9a-f]{64}', sha) is None:
        raise ValueError('Absolute file path, nonnegative size and lowercase SHA256 required')
    actual = _sr_pin(path)
    if actual['bytes'] != size or actual['sha256'] != sha:
        raise ValueError('Original pinned evidence changed')
    return actual


def _sr_read(value: object) -> tuple[JsonObject, FilePin]:
    reference = _sr_checked(value)
    if not 0 < reference['bytes'] <= 16 * 1024 * 1024:
        raise ValueError('Bounded nonempty JSON evidence required')
    raw = Path(reference['path']).read_bytes()
    return json_object(json.loads(raw)), reference


def _sr_write(path: Path, value: JsonObject) -> FilePin:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, allow_nan=False, indent=2)
        stream.write('\n')
    return _sr_pin(path)


def _sr_enabled(context: JsonObject) -> bool:
    contract = json_object(context.get('case_contract'))
    if 'saved_readback' not in contract:
        return False
    mode = json_object(contract['saved_readback'])
    if mode.get('mode') != SAVED_READBACK_MODE:
        raise ValueError('Unknown saved-readback branch; no fixture fallback')
    return True


def _sr_contract(context: JsonObject) -> SavedReadbackMode:
    contract = json_object(context.get('case_contract'))
    if (contract.get('product') != context.get('product') or contract.get('case_id') != context.get('case')
            or context.get('product') != 'superman-qiang'):
        raise ValueError('Monthly saved-readback contract crossed its canonical product/case')
    if type(contract.get('maximum_natural_days')) is not int or contract.get('maximum_natural_days') != 0:
        raise ValueError('Saved readback requires the explicit zero-day branch')
    return SavedReadbackMode.from_validated_json(contract.get('saved_readback'))


def _sr_field(value: object, label: str, *, partners: bool = False) -> ScalarState | PartnerState:
    return (_sr_partners_from_validated_json(value, label) if partners
            else _sr_scalar_from_validated_json(value, label))


def _sr_characters(value: object, mode: SavedReadbackMode) -> TwelveCharacters:
    return TwelveCharacters.from_validated_json(value, mode)


def _sr_origin(context: JsonObject, mode: SavedReadbackMode) -> tuple[SavedReadbackOrigin, FilePin]:
    inputs = json_object(context.get('case_inputs'))
    origin, reference = _sr_read(inputs.get('saved_readback_origin'))
    return SavedReadbackOrigin.from_validated_json(origin, mode, context.get('run_id')), reference


def _sr_prepare(context: JsonObject) -> JsonObject:
    from ck3_mod_acceptance_prepare import materialize_product_profile, finish_product_profile, _outer_from_inner
    mode = _sr_contract(context)
    origin, origin_pin = _sr_origin(context, mode)
    inputs = json_object(context['case_inputs'])
    product = Path(_sr_text(inputs.get('product_dir'), 'Product projection')).resolve()
    passive = Path(_sr_text(inputs.get('passive_fixture_dir'), 'Passive fixture source')).resolve()
    if product == passive or not (product / 'descriptor.mod').is_file():
        raise ValueError('Distinct original product and passive dependency projections required')
    projection, projection_pin = _sr_read(inputs.get('product_projection'))
    source_files = json_object(projection.get('files'))
    declared_count = _sr_integer(projection.get('file_count'), 'Source runtime projection count')
    actual_names = {path.relative_to(product).as_posix() for path in product.rglob('*') if path.is_file()}
    if (declared_count != mode.product_file_count or len(source_files) != declared_count
            or set(source_files) != actual_names):
        raise ValueError('Source runtime projection must bind exactly the actual 35-file product')
    for name, raw in source_files.items():
        if Path(name).is_absolute() or '..' in Path(name).parts:
            raise ValueError('Product runtime projection member escapes its root')
        reference = _sr_checked(raw)
        if Path(reference['path']).resolve() != (product / name).resolve():
            raise ValueError('Product source projection crossed its actual file path')
        if name.endswith('.txt') and 'on_game_start_after_lobby' in (product / name).read_text(encoding='utf-8-sig'):
            raise ValueError('Saved product projection cannot contain a cold-start registrar')
    members = mode.passive_fixture_files
    sources: dict[str, FilePin] = {}
    for name in members:
        source = (passive / name).resolve()
        if not source.is_relative_to(passive):
            raise ValueError('Passive dependency escaped original source')
        reference = _sr_pin(source)
        if source.suffix.casefold() == '.txt' and 'on_game_start_after_lobby' in source.read_text(encoding='utf-8-sig'):
            raise ValueError('Saved profile cannot contain a cold-start registrar')
        sources[name] = reference
    profile = json_object(materialize_product_profile(context, product, json_object(inputs.get('plain_configuration'))))
    profile_path = Path(_sr_text(profile.get('profile'), 'Prepared profile'))
    output = Path(_sr_text(context['output'], 'Preparation output'))
    target = profile_path / 'mod-content/passive-saved-dependencies'
    for name, reference in sources.items():
        destination = target / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(reference['path'], destination)
        copied = _sr_pin(destination)
        if copied['bytes'] != reference['bytes'] or copied['sha256'] != reference['sha256']:
            raise ValueError('Passive dependency changed during the profile copy')
    outer = profile_path / 'mod/passive-saved-dependencies.mod'
    with outer.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(_outer_from_inner(target / 'descriptor.mod', target))
    enabled = ['mod/product.mod', 'mod/passive-saved-dependencies.mod']
    (profile_path / 'dlc_load.json').write_text(json.dumps({'enabled_mods': enabled, 'disabled_dlcs': []}) + '\n', encoding='utf-8')
    product_inventory = _sr_read(profile['product_inventory'])[0]
    products = _sr_list(product_inventory.get('product_files'), 'Product inventory')
    products.extend([_sr_pin(outer), *[_sr_pin(target / name) for name in members]])
    inventory_path = output / 'saved-readback-product-inventory.json'
    inventory = _sr_write(inventory_path, json_object({'schema': 'ck3-saved-campaign-product-only-profile-v1',
        'profile_path': str(profile_path.resolve()), 'enabled_mods': enabled, 'product_files': products}))
    profile['product_inventory'] = json_object(inventory)
    profile['files'] = json_object({path.relative_to(profile_path).as_posix(): _sr_pin(path)
                                   for path in sorted(profile_path.rglob('*')) if path.is_file()})
    compiled = SavedReadbackContract(mode, origin, origin_pin, projection_pin, sources)
    compiled_path = profile_path / 'saved-readback-contract.json'
    compiled_pin = _sr_write(compiled_path, compiled.to_json(context))
    profile['files'] = json_object({path.relative_to(profile_path).as_posix(): _sr_pin(path)
                                   for path in sorted(profile_path.rglob('*')) if path.is_file()})
    finished = json_object(finish_product_profile(context, profile, provenance={'kind': 'saved-readback-passive-dependencies',
        'origin': origin_pin, 'passive_files': sources}))
    initial = _sr_write(output / 'initial-plan.json', {'steps': []})
    seed = origin.checkpoint
    saved_campaign: JsonObject = {
        'save': seed['path'], 'bytes': seed['bytes'], 'sha256': seed['sha256'],
        'player_id': origin.player_id, 'date_raw': origin.date_raw, 'product_inventory': inventory['path']}
    startup: JsonObject = {'mode': 'saved_campaign', 'state_dir': context['state_dir'],
                           'saved_campaign': saved_campaign}
    return json_object({'startup': startup,
        'initial_plan': initial, 'profile_preparation': finished, 'assertion_contract': compiled_pin,
        'files': finished['files'], 'runtime_status': 'NOT_RUN', 'business_contract_applicable': True,
        'business_pass': False, 'product_release_pass': False})


def _sr_compiled(context: JsonObject) -> tuple[SavedReadbackContract, FilePin]:
    path = Path(_sr_text(context['state_dir'], 'State directory')) / 'profile/saved-readback-contract.json'
    row, reference = _sr_read(_sr_pin(path))
    _sr_keys(row, {'schema', 'product', 'case', 'config', 'origin', 'origin_pin', 'product_projection',
                   'passive_source_pins', 'requirements', 'whole_product_release_pass'}, 'Prepared saved-readback contract')
    if (row['schema'] != 'ck3-mod-acceptance-saved-readback-contract-v1'
            or row['product'] != context.get('product') or row['case'] != context.get('case')
            or row['config'] != context.get('case_contract')
            or row['requirements'] != list(SAVED_READBACK_REQUIREMENTS)
            or row['whole_product_release_pass'] is not False):
        raise ValueError('Cold prepared contract crossed actual selected case/config')
    mode = _sr_contract(context)
    origin, origin_pin = _sr_origin(context, mode)
    prepared_origin = SavedReadbackOrigin.from_validated_json(row['origin'], mode, context.get('run_id'))
    if prepared_origin != origin or _sr_checked(row['origin_pin']) != origin_pin:
        raise ValueError('Original source checkpoint/readback contract changed')
    sources = {name: _sr_checked(pin) for name, pin in json_object(row['passive_source_pins']).items()}
    if set(sources) != set(mode.passive_fixture_files):
        raise ValueError('Prepared passive dependency inventory changed')
    return SavedReadbackContract(mode, origin, origin_pin, _sr_checked(row['product_projection']), sources), reference


def _sr_snapshot(frame: JsonObject, origin: SavedReadbackOrigin) -> None:
    played = json_object(frame.get('played_character'))
    if (frame.get('episode_projection') != 'native_campaign' or frame.get('paused') is not True
            or _sr_integer(frame.get('date_raw'), 'Actual cold date') != origin.date_raw
            or _sr_character_id(played.get('character_id'), 'Actual player full ID') != origin.player_id
            or 'active_event' not in frame or frame.get('active_event') is not None):
        raise ValueError('Actual cold campaign must remain paused at the original actor/date with no active event')


def _sr_response(value: object, context: JsonObject, compiled: SavedReadbackContract,
                 process: RetainedProcess) -> SavedRootResponse:
    response = SavedRootResponse.from_validated_json(value, compiled.mode)
    if response.run_id != context.get('run_id'):
        raise ValueError('Saved-readback Root response crossed actual run/reviewer')
    origin, data = compiled.origin, response.readback
    if (data.source_checkpoint != origin.checkpoint or data.source_readback != origin.readback
            or data.process_id != process.pid or data.process_id == origin.process_id
            or data.player_id != origin.player_id or data.date_raw != origin.date_raw):
        raise ValueError('Cold Root readback crossed immutable source or actual new process/actor/date')
    saved = NativeSavedCheckpoint.from_validated_json(_sr_read(data.cold_checkpoint_response)[0])
    if saved.date_raw != origin.date_raw or saved.checkpoint != data.cold_checkpoint:
        raise ValueError('Actual native cold SAVE result differs from the decoded checkpoint')
    identity = ColdProcessEvidence.from_validated_json(_sr_read(data.process_evidence)[0])
    if (data.cold_checkpoint['path'] == origin.checkpoint['path']
            or Path(data.cold_checkpoint['path']).suffix.casefold() != '.ck3'
            or identity.run_id != response.run_id or identity.machine_id != origin.machine_id
            or identity.pid != process.pid or identity.create_time != process.create_time):
        raise ValueError('Distinct cold save and matching actual retained process evidence required')
    if data.characters != origin.characters:
        raise ValueError('Cold identities, alive state, experience, month or partner lists changed')
    declared = {(pin['path'], pin['bytes'], pin['sha256']) for pin in response.evidence}
    for pin in (data.cold_checkpoint, data.cold_readback, data.cold_checkpoint_response,
                data.process_evidence, origin.checkpoint, origin.readback):
        if (pin['path'], pin['bytes'], pin['sha256']) not in declared:
            raise ValueError('Every source/cold/process artifact must be in the exact Root evidence list')
    return response


def _sr_run(context: JsonObject, client: SavedReadbackClient) -> JsonObject:
    compiled, binding = _sr_compiled(context)
    origin = compiled.origin
    before = json_object(client.snapshot(require_event_free=True))
    _sr_snapshot(before, origin)
    process = RetainedProcess.from_validated_json(client.retain_process())
    if process.pid == origin.process_id:
        raise ValueError('A genuinely new retained Game process is required')
    request = json_object({'product': context['product'], 'case': context['case'],
        'action': 'Save exactly one new paused cold checkpoint through the existing queue; independently decode and compare all twelve identities and XP/month/partner-list states.',
        'required_assertions': list(SAVED_READBACK_REQUIREMENTS), 'origin': origin.to_json(),
        'actual_snapshot': before, 'actual_process': process.to_json(),
        'no_calendar_advance_or_initialization': True, 'normal_close_pending': True})
    response = _sr_response(client.root_checkpoint('saved-readback-exact-cold-checkpoint', request, reserve=90),
                            context, compiled, process)
    after = json_object(client.snapshot(require_event_free=True))
    _sr_snapshot(after, origin)
    facts = json_object({'schema': 'ck3-mod-acceptance-saved-readback-facts-v1',
        'run_id': context['run_id'], 'product': context['product'], 'case': context['case'],
        'compiled_contract': binding, 'actual_process': process.to_json(), 'before': before, 'after': after,
        'root_response': response.to_json(), 'natural_days_advanced': 0,
        'case_contract_qualified': True, 'gui_contract_qualified': True,
        'business_contract_applicable': True, 'business_pass': False, 'product_release_pass': False})
    client.checkpoint('generic-product-case-result', facts)
    return facts


def _sr_verify(context: JsonObject) -> JsonObject:
    path = Path(_sr_text(context['output'], 'Case output')) / 'generic-product-case-result.json'
    if not path.is_file():
        return {'status': 'NOT_RUN', 'business_pass': False, 'product_release_pass': False,
                'case_contract_qualified': False, 'gui_contract_qualified': False}
    facts, _ = _sr_read(_sr_pin(path))
    compiled, binding = _sr_compiled(context)
    if (facts.get('schema') != 'ck3-mod-acceptance-saved-readback-facts-v1'
            or facts.get('run_id') != context.get('run_id') or facts.get('product') != context.get('product')
            or facts.get('case') != context.get('case') or facts.get('compiled_contract') != json_object(binding)
            or type(facts.get('natural_days_advanced')) is not int or facts.get('natural_days_advanced') != 0):
        raise ValueError('Original cold result crossed actual prepared run or zero-day boundary')
    _sr_snapshot(json_object(facts.get('before')), compiled.origin)
    _sr_snapshot(json_object(facts.get('after')), compiled.origin)
    _sr_response(facts.get('root_response'), context, compiled, RetainedProcess.from_validated_json(facts.get('actual_process')))
    return json_object({**facts, 'verification_scope': 'monthly-natural-exact-cold-saved-readback',
                        'business_pass': False, 'product_release_pass': False})


def prepare_case(context: JsonObject) -> JsonObject:
    context = json_object(context)
    if object_field(context, 'case_contract').get('acceptance_scope') == 'ordinary_promotion':
        return prepare_ordinary_capture(context)
    if _sr_enabled(context):
        return _sr_prepare(context)
    return json_object(_prepare_fixture_case(context))


def run_case(context: JsonObject, client: CaseClient) -> JsonObject:
    context = json_object(context)
    if object_field(context, 'case_contract').get('acceptance_scope') == 'ordinary_promotion':
        return run_ordinary_capture(context, client)
    if _sr_enabled(context):
        return _sr_run(context, client)
    return json_object(_run_fixture_case(context, client))


def verify_case(context: JsonObject) -> JsonObject:
    context = json_object(context)
    if object_field(context, 'case_contract').get('acceptance_scope') == 'ordinary_promotion':
        return verify_ordinary_capture(context)
    if _sr_enabled(context):
        return _sr_verify(context)
    return json_object(_verify_fixture_case(context))
