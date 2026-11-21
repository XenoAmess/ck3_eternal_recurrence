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

from ck3_mod_acceptance_native_day import (
    PendingInteractionPolicy, admit_pending_interaction_policy_v1,
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
    if context.get('execution_mode') == 'gui_only':
        from ck3_mod_acceptance_prepare import make_gui_saved_startup
        return json_object(make_gui_saved_startup(context, profile))
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
    _fixture_pending_interaction_policy(config)
    require(config['product'] == context['product'], 'Case crossed canonical product')
    # Select from public fields; materialization later caches a private engine module.
    liquidity14 = _futures_natural14_enabled(json_object({
        'product': context['product'], 'case': context['case'], 'case_contract': config}))
    continuous14 = _continuous14_enabled(json_object({
        'product': context['product'], 'case': context['case'], 'case_contract': config}))
    futures_gui = _futures_gui_transactions_enabled(json_object({
        'product': context['product'], 'case': context['case'], 'case_contract': config}))
    redemption_gui = _redemption_gui_enabled(json_object({
        'product': context['product'], 'case': context['case'], 'case_contract': config}))
    redemption_existing = _redemption_existing_enabled(json_object({
        'product': context['product'], 'case': context['case'], 'case_contract': config}))
    if redemption_existing:
        _redemption_existing_history(json_object(context))
    independent_seed = _independent_financial_seed_enabled(json_object(context))
    if independent_seed:
        _independent_financial_seed_inputs(json_object(context))
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
        if continuous14:
            from ck3_mod_acceptance_background_types import CONTINUOUS14_PASSIVE_STORY_TYPES_V1
            if config.get('passive_story_types') != list(CONTINUOUS14_PASSIVE_STORY_TYPES_V1):
                raise ValueError('Exact finite passive observation story catalog required')
            passive = fixture / 'common/story_cycles/xfma_clock_cadence_passive.txt'
            passive.parent.mkdir(parents=True)
            passive.write_text(''.join(name + ' = { visible = no }\n'
                for name in CONTINUOUS14_PASSIVE_STORY_TYPES_V1), encoding='utf-8-sig')
        if liquidity14:
            from ck3_mod_acceptance_background_types import CONTINUOUS14_PASSIVE_STORY_TYPES_V1
            passive = fixture / 'common/story_cycles/xfma_futures_natural_passive.txt'
            passive.parent.mkdir(parents=True)
            passive.write_text(''.join(name + ' = { visible = no }\n'
                for name in CONTINUOUS14_PASSIVE_STORY_TYPES_V1), encoding='utf-8-sig')
        if futures_gui:
            from ck3_mod_acceptance_background_types import CONTINUOUS14_PASSIVE_STORY_TYPES_V1
            # Reuse only the finite passive declarations; no observer/timer/ARM is mounted.
            passive = fixture / 'common/story_cycles/xfma_futures_gui_passive.txt'
            passive.parent.mkdir(parents=True)
            passive.write_text(''.join(name + ' = { visible = no }\n'
                for name in CONTINUOUS14_PASSIVE_STORY_TYPES_V1), encoding='utf-8-sig')
        if redemption_gui:
            from ck3_mod_acceptance_background_types import CONTINUOUS14_PASSIVE_STORY_TYPES_V1
            passive = fixture / 'common/story_cycles/xfma_redemption_gui_passive.txt'
            passive.parent.mkdir(parents=True)
            passive.write_text(''.join(name + ' = { visible = no }\n'
                for name in CONTINUOUS14_PASSIVE_STORY_TYPES_V1), encoding='utf-8-sig')
        if redemption_existing:
            from ck3_mod_acceptance_background_types import CONTINUOUS14_PASSIVE_STORY_TYPES_V1
            passive = fixture / 'common/story_cycles/xfma_redemption_existing_passive.txt'
            passive.parent.mkdir(parents=True)
            passive.write_text(''.join(name + ' = { visible = no }\n'
                for name in CONTINUOUS14_PASSIVE_STORY_TYPES_V1), encoding='utf-8-sig')
        if independent_seed:
            from ck3_mod_acceptance_background_types import CONTINUOUS14_PASSIVE_STORY_TYPES_V1
            passive = fixture / 'common/story_cycles/xfma_independent_financial_seed_passive.txt'
            passive.parent.mkdir(parents=True)
            passive.write_text(''.join(name + ' = { visible = no }\n'
                for name in CONTINUOUS14_PASSIVE_STORY_TYPES_V1), encoding='utf-8-sig')
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
    require(required or config['acceptance_scope'] == 'static_and_basicload' or continuous14 or liquidity14 or futures_gui or redemption_gui or redemption_existing or independent_seed,
            'Full business case has no original assertions')
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
        startup_context = json_object({
            'saved_campaign': context['saved_campaign'], 'output': context['output'],
            'state_dir': context['state_dir']})
        if context.get('execution_mode') == 'gui_only':
            for key in ('execution_mode', 'case_inputs', 'runtime_manifest', 'repo_root', 'gui_saved_input'):
                startup_context[key] = context[key]
        startup = _saved_fixture_startup(startup_context, json_object(profile))
    if config.get('frontend_rules'):
        rules = output / 'frontend-rules-plan.json'
        write_once(rules, {'schema': 'ck3-frontend-rules-plan-v1', 'schema_version': 1,
                           'rules': config['frontend_rules']})
        startup['frontend_rules_plan'] = str(rules)
    return {'startup': startup,
            'initial_plan': pin(initial), 'profile_preparation': profile,
            'assertion_contract': pin(Path(profile['profile']) / 'mod-content/fixture/_case_contract.json'),
            'business_contract_applicable': config['acceptance_scope'] != 'static_and_basicload'
                and not continuous14 and not independent_seed,
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
                    allow_actor_change: bool = False,
                    pending_interaction_policy: PendingInteractionPolicy = "stop_at_boundary") -> dict[str, object]: ...
    def execute_plan(self, steps: list[dict[str, object]], name: str,
                     timeout: float | None = None,
                     reserve: int = 90) -> list[dict[str, object]]: ...


def _fixture_pending_interaction_policy(config: object) -> PendingInteractionPolicy:
    selected = json_object(config)
    return admit_pending_interaction_policy_v1(selected.get('pending_interaction_policy', 'stop_at_boundary'),
        product=selected.get('product'), case=selected.get('case_id'))


def _advance_fixture_day(client: FixtureDayClient, config: object,
                         sequence: object, timeout: object) -> JsonObject:
    """Use the public bounded day route, preserving explicit succession waits."""
    if not isinstance(client, FixtureDayClient):
        raise ValueError('Fixture day requires the public natural-day client contract')
    policy = json_object(config)
    pending_policy = _fixture_pending_interaction_policy(policy)
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
    if pending_policy == "observe_unanswered_inbox":
        require(not actor_change and not transitions,
                'Inbox observation does not enter a succession or legacy transition route')
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
    if pending_policy == "observe_unanswered_inbox":
        return json_object(client.advance_day(days=1, timeout=timeout,
                           allow_event_boundary=True, allow_actor_change=actor_change,
                           pending_interaction_policy=pending_policy))
    return json_object(client.advance_day(days=1, timeout=timeout,
                       allow_event_boundary=True, allow_actor_change=actor_change))


def _fixture_boundary(frame: object, pending_policy: PendingInteractionPolicy = 'stop_at_boundary') -> Literal['event', 'notification'] | None:
    snapshot = json_object(frame)
    if snapshot.get('active_event') is not None:
        return 'event'
    if snapshot.get('pending_character_interaction') is not None and pending_policy == 'stop_at_boundary':
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



FUTURES_GUI_TRANSACTION_CELLS = ('long', 'short', 'leverage_selection', 'add_margin', 'withdraw_margin', 'reduce')
FUTURES_GUI_PHYSICAL_SAVE_MAXIMUM = 6
FUTURES_GUI_PHYSICAL_SAVE_MAX_BYTES = 256 * 1024 * 1024
FUTURES_GUI_TRANSACTION_CONTRACT = {
    'schema': 'ck3-futures-gui-transactions-contract-v1', 'physical_save_maximum': 6,
    'physical_save_max_bytes': 256 * 1024 * 1024, 'observer_arm': False,
    'cell_statuses': ['OBSERVED', 'NOT_OBSERVED'], 'cells': list(FUTURES_GUI_TRANSACTION_CELLS),
    'financial_clock_credit': False, 'derivatives_acceptance_credit': False,
}
FUTURES_GUI_CELL_ASSERTIONS = {
    'long': 'actual_new_long_position_and_independent_funded_counterparty_fill',
    'short': 'actual_new_short_position_and_independent_funded_counterparty_fill',
    'leverage_selection': 'actual_ticket_leverage_within_current_asset_max_and_existing_positions_unchanged',
    'add_margin': 'actual_selected_side_reservation_increase_equals_private_wallet_debit',
    'withdraw_margin': 'actual_safe_surplus_release_equals_private_wallet_credit',
    'reduce': 'actual_new_reduce_order_filled_and_exposure_reduced_with_real_counterparty',
}
FUTURES_GUI_COMMON_ASSERTIONS = (
    'actual_current_gui_row_ticket_account_and_permanent_identities_bound',
    'actual_operation_is_new_and_no_historical_cancel_or_reduction_replayed',
    'actual_before_after_physical_save_audit_and_raw_share_the_unchanged_native_date',
    'actual_margin_fees_cash_counterparty_and_unrelated_assets_independently_reconciled',
)


def _futures_gui_transactions_enabled(context: JsonObject) -> bool:
    config = object_field(context, 'case_contract')
    selected = context.get('case') == 'futures-gui-transactions' or 'futures_gui_transactions_contract' in config
    if not selected:
        return False
    from ck3_mod_acceptance_background_types import CONTINUOUS14_PASSIVE_STORY_TYPES_V1
    contract = object_field(config, 'futures_gui_transactions_contract')
    if (type(contract.get('physical_save_maximum')) is not int
            or type(contract.get('physical_save_max_bytes')) is not int
            or any(contract.get(key) is not False for key in
                   ('observer_arm', 'financial_clock_credit', 'derivatives_acceptance_credit'))):
        raise ValueError('Futures GUI uses exact integer bounds and false credit/ARM flags')
    phases = config.get('gui_phases')
    if (context.get('product') != 'financial-markets' or context.get('case') != 'futures-gui-transactions'
            or config.get('product') != context['product'] or config.get('case_id') != context['case']
            or config.get('schema') != 'ck3-mod-acceptance-product-case-v1' or config.get('execution_purpose') != 'product_acceptance'
            or config.get('acceptance_scope') != 'zero_day_normal_futures_gui_observed_cells_only'
            or config.get('startup_mode') != 'saved_campaign' or config.get('allow_actor_change') is not False
            or config.get('product_loading', 'present') != 'present'
            or type(config.get('maximum_natural_days')) is not int or config.get('maximum_natural_days') != 0
            or config.get('futures_gui_transactions_contract') != FUTURES_GUI_TRANSACTION_CONTRACT
            or config.get('passive_story_types') != list(CONTINUOUS14_PASSIVE_STORY_TYPES_V1)
            or config.get('pending_interaction_policy', 'stop_at_boundary') != 'stop_at_boundary'
            or any(key in config for key in ('fixture_source', 'fixture_emitter', 'marker_inventory', 'continuous14_contract', 'clock_purpose'))
            or config.get('whole_product_release_pass') is not False or config.get('business_contract_applicable') is not True
            or not isinstance(phases, list) or len(phases) != 2):
        raise ValueError('Exact independent zero-day futures GUI contract required')
    for value, expected in zip(phases, ('bind-current-financial-baseline', 'normal-gui-transactions-and-saved-reconciliation')):
        phase = json_object(value)
        if (phase.get('id') != expected or type(phase.get('at_day')) is not int or phase.get('at_day') != 0
                or phase.get('when_markers') is not None or not phase.get('requirements')):
            raise ValueError('Futures GUI uses only the two existing same-day Root phases')
    return True


# This is a declared independent reproduction fork, never a mainline rollback.
INDEPENDENT_FINANCIAL_SEED_SOURCE: JsonObject = json_object({'schema': 'ck3-independent-financial-source-seed-v1',
 'machine_id': '4-8e1c2f1861',
 'source_run_id': '4-8e1c2f1861--financial-markets--R0052',
 'source_reports': {'archive': {'path': 'C:\\workspace\\ck3-market-task-20261118\\financial-physical-saves-continuous16\\clock17-terminal01\\ARCHIVE.actual.json',
                                'bytes': 7553,
                                'sha256': 'c4d59bec66d957539355e15bce767b9b5b5b1ea7cbddfebc89f88194c84a488c'},
                    'whole': {'path': 'C:\\workspace\\ck3-market-task-20261118\\clock17-terminal01-whole-digest\\report.json',
                              'bytes': 5016818,
                              'sha256': 'f3b279e70adab90a713ce08d501b3b9ed78c79ca9233199206b6e4f667e9f7d7'},
                    'raw': {'path': 'C:\\workspace\\ck3-market-task-20261118\\clock17-terminal01-actor-raw\\report.json',
                            'bytes': 1531748,
                            'sha256': '935c39f7f3cf108074d8af73c4be6d94edf58c4429e78aa41a7f44e46ecdd88a'},
                    'actor_wallet': {'path': 'C:\\workspace\\ck3-market-task-20261118\\clock17-terminal01-actor-wallet01.json',
                                     'bytes': 6704,
                                     'sha256': 'e019dc8d35bd46ba915e0644e1262edb6c5059b9affd52b1829c8e785cbc96c6'}},
 'save': {'path': 'C:\\workspace\\ck3-market-task-20261118\\financial-physical-saves-continuous16\\clock17-terminal01\\xar_checkpoint.ck3',
          'bytes': 206234918,
          'sha256': '46061b6c7602347aab3a44625a8fe323a893218e932b13fc32eb1df2e86b0e98'},
 'actor_id': 31254,
 'date_raw': 53150016,
 'financial_day': 233,
 'physical_save_maximum': 1,
 'physical_save_max_bytes': 268435456,
 'observer_arm': False,
 'business_actions': False,
 'new_game_claim': False,
 'mainline_continuation': False,
 'R54_recovery_or_progress_credit': False})
INDEPENDENT_FINANCIAL_SEED_REQUIREMENTS = ('actual_explicit_new_independent_scenario_namespace_and_R52_source_never_mainline_rollback_or_R54_recovery',
 'actual_new_owned_saved_campaign_process_profile_actor_date_and_starting_gold_from_this_run',
 'actual_no_new_orders_money_price_position_ai_or_observer_actions_and_no_replay_of_R53_231_232',
 'actual_one_new_same_date_SAVE_current_audit_raw_complete_whole_globals_news_and_PRIMARY_match_the_declared_seed',
 'actual_all_R53_R54_original_actions_failures_archives_and_unresolved_claims_remain_retained_without_reclassification',
 'actual_minimized_non_topmost_no_foreground_activation_for_entire_run')


def _independent_financial_seed_enabled(context: JsonObject) -> bool:
    config = object_field(context, 'case_contract')
    if context.get('case') != 'independent-futures-seed' and 'independent_seed_contract' not in config:
        return False
    from ck3_mod_acceptance_background_types import CONTINUOUS14_PASSIVE_STORY_TYPES_V1
    source = object_field(config, 'independent_seed_contract')
    phases = config.get('gui_phases')
    if (not isinstance(phases, list) or len(phases) != 1
            or type(json_object(phases[0]).get('at_day')) is not int):
        raise ValueError('Exactly one independent same-day Root phase required')
    if (context.get('product') != 'financial-markets' or context.get('case') != 'independent-futures-seed'
            or config.get('product') != context['product'] or config.get('case_id') != context['case']
            or config.get('schema') != 'ck3-mod-acceptance-product-case-v1'
            or config.get('execution_purpose') != 'product_acceptance'
            or config.get('acceptance_scope') != 'independent_saved_financial_reproduction_seed_only'
            or config.get('startup_mode') != 'saved_campaign' or config.get('allow_actor_change') is not False
            or type(config.get('maximum_natural_days')) is not int or config.get('maximum_natural_days') != 0
            or config.get('product_loading', 'present') != 'present'
            or config.get('pending_interaction_policy') != 'stop_at_boundary'
            or config.get('business_contract_applicable') is not False or config.get('whole_product_release_pass') is not False
            or config.get('passive_story_types') != list(CONTINUOUS14_PASSIVE_STORY_TYPES_V1)
            or source != INDEPENDENT_FINANCIAL_SEED_SOURCE
            or any(type(source.get(key)) is not int for key in
                   ('actor_id', 'date_raw', 'financial_day', 'physical_save_maximum', 'physical_save_max_bytes'))
            or any(source.get(key) is not False for key in ('observer_arm', 'business_actions', 'new_game_claim',
                   'mainline_continuation', 'R54_recovery_or_progress_credit'))
            or config.get('gui_phases') != [{'id': 'bind-independent-reproduction-seed', 'at_day': 0,
                   'requirements': list(INDEPENDENT_FINANCIAL_SEED_REQUIREMENTS)}]
            or any(key in config for key in ('fixture_source', 'fixture_emitter', 'marker_inventory', 'clock_purpose',
                   'continuous14_contract', 'futures_natural_liquidity_contract', 'frontend_rules'))):
        raise ValueError('Exact independent R52 seed contract required; no mainline recovery or new-game claim')
    return True


def _independent_financial_seed_inputs(context: JsonObject) -> JsonObject:
    if not _independent_financial_seed_enabled(context):
        raise ValueError('Independent seed case required')
    inputs = object_field(context, 'case_inputs')
    if (set(inputs) != {'product_dir', 'plain_configuration', 'post_start', 'independent_scenario'}
            or context.get('execution_mode') == 'gui_only' or context.get('gui_saved_input') is not None):
        raise ValueError('Independent seed accepts only the formal product, plain configuration and explicit scenario')
    scenario = object_field(inputs, 'independent_scenario')
    if (set(scenario) != {'scenario_id', 'source_run_id', 'source_archive', 'mainline_continuation',
                         'production_recovery', 'new_game_claim', 'historical_R54_credit', 'replay_existing_orders'}
            or not isinstance(scenario.get('scenario_id'), str)
            or re.fullmatch(r'[a-z][a-z0-9_-]{2,63}', str(scenario.get('scenario_id'))) is None
            or scenario.get('source_run_id') != INDEPENDENT_FINANCIAL_SEED_SOURCE['source_run_id']
            or scenario.get('source_archive') != object_field(INDEPENDENT_FINANCIAL_SEED_SOURCE, 'source_reports')['archive']
            or any(scenario.get(key) is not False for key in ('mainline_continuation', 'production_recovery',
                   'new_game_claim', 'historical_R54_credit')) or scenario.get('replay_existing_orders') != []):
        raise ValueError('Explicit independent scenario and exact intact R52 source required')
    saved = object_field(context, 'saved_campaign')
    expected = file_pin(INDEPENDENT_FINANCIAL_SEED_SOURCE.get('save'))
    if (not {'save', 'bytes', 'sha256', 'player_id', 'date_raw'} <= set(saved)
            or set(saved) - {'save', 'bytes', 'sha256', 'player_id', 'date_raw', 'product_inventory'}
            or saved.get('save') != expected['path'] or type(saved.get('bytes')) is not int
            or saved.get('bytes') != expected['bytes'] or saved.get('sha256') != expected['sha256']
            or type(saved.get('player_id')) is not int or saved.get('player_id') != INDEPENDENT_FINANCIAL_SEED_SOURCE['actor_id']
            or type(saved.get('date_raw')) is not int or saved.get('date_raw') != INDEPENDENT_FINANCIAL_SEED_SOURCE['date_raw']):
        raise ValueError('Independent scenario must load exactly the retained pre-order R52 archive')
    for reference in object_field(INDEPENDENT_FINANCIAL_SEED_SOURCE, 'source_reports').values():
        checked_capture_pin(reference)  # Metadata only; saved startup owns physical SAVE validation/copy.
    return scenario


def _independent_financial_seed_review(context: JsonObject, compiled: JsonObject,
                                      phases: JsonObject, frame: JsonObject) -> JsonObject:
    context = json_object(resolve_post_start(context))
    scenario = _independent_financial_seed_inputs(context)
    if compiled.get('config') != context['case_contract']:
        raise ValueError('Prepared independent seed contract differs')
    source = INDEPENDENT_FINANCIAL_SEED_SOURCE
    date = source['date_raw']
    if type(date) is not int or not isinstance(date, int):
        raise ValueError('Exact independent seed integer calendar required')
    source_reports = object_field(source, 'source_reports')
    source_save = file_pin(source.get('save'))
    actor = object_field(frame, 'played_character')
    if (type(frame.get('date_raw')) is not int or frame.get('date_raw') != date or frame.get('paused') is not True
            or type(actor.get('character_id')) is not int or actor.get('character_id') != source['actor_id']):
        raise ValueError('Actual independent seed actor, paused state and original date required')
    phase = object_field(phases, 'bind-independent-reproduction-seed')
    assertions = object_field(phase, 'assertions')
    if (phase.get('run_id') != context['run_id'] or phase.get('reviewer') != '/root'
            or any(assertions.get(key) is not True for key in INDEPENDENT_FINANCIAL_SEED_REQUIREMENTS)):
        raise ValueError('Explicit current Root independent seed review required')
    evidence = object_field(phase, 'independent_seed')
    if (set(evidence) != {'scenario_id', 'source_archive', 'physical_archives', 'baseline_archive',
                         'audit', 'raw', 'whole', 'actor_wallet', 'whole_comparison', 'metadata_comparison'}
            or evidence.get('scenario_id') != scenario['scenario_id']
            or evidence.get('source_archive') != source_reports['archive']
            or evidence.get('physical_archives') != [evidence.get('baseline_archive')]):
        raise ValueError('One actual new checkpoint and exact independent source evidence required')
    save = _futures_gui_archive(evidence.get('baseline_archive'), phase, date)
    if Path(save['path']).resolve() == Path(source_save['path']).resolve():
        raise ValueError('A historical source archive is not a new independent checkpoint')
    references: dict[str, FilePin] = {}
    records: dict[str, JsonObject] = {}
    for key in ('audit', 'raw', 'whole', 'actor_wallet', 'whole_comparison', 'metadata_comparison'):
        reference = _futures_gui_evidence(evidence.get(key), phase)
        if reference['bytes'] > 64 * 1024 * 1024:
            raise ValueError('Independent seed metadata exceeds existing finite 64MiB bound')
        references[key] = reference
        records[key] = json_object(read_json(reference['path']))
    whole = records['whole_comparison']
    if (whole.get('schema') != 'ck3-continuous14-whole-financial-news-record-differences-v1'
            or whole.get('before') != source_reports['whole'] or whole.get('after') != references['whole']
            or whole.get('before_save') != source_save or whole.get('after_save') != save
            or whole.get('dates_raw') != [date, date] or whole.get('exact_whole_selected_records_equal') is not True
            or any(whole.get(key) != [] for key in ('missing', 'added', 'changed'))):
        raise ValueError('Existing whole comparator must prove exact source/current complete financial graph equality')
    metadata = records['metadata_comparison']
    before, after = object_field(metadata, 'before'), object_field(metadata, 'after')
    if (metadata.get('schema') != 'ck3-continuous14-financial-globals-news-cursor-differences-v1'
            or before.get('report') != source_reports['raw'] or after.get('report') != references['raw']
            or before.get('save') != source_save or after.get('save') != save
            or before.get('dateRaw') != date or after.get('dateRaw') != date
            or metadata.get('exactSelectedGlobalAndNewsState') is not True
            or metadata.get('globalDifferences') != [] or metadata.get('newsDifferences') != []):
        raise ValueError('Existing metadata comparator must preserve all selected globals and news')
    financial = object_field(object_field(records['audit'], 'audit'), 'financial')
    # FinancialAuditMain.first streams the same SAVE twice. second is a list
    # of optional additional SAVE comparisons, not the second streaming pass.
    endpoint = object_field(financial, 'first')
    coverage = object_field(endpoint, 'streamingCoverage')
    if (financial.get('second') != [] or endpoint.get('save') != save or coverage.get('passes') != 2
            or coverage.get('completeStreamBytes') != str(save['bytes'])
            or coverage.get('completeStreamSha256') != save['sha256']
            or object_field(endpoint, 'audit').get('assessment') != 'CANDIDATE_INVARIANTS_HOLD'
            or records['audit'].get('financialCertified') is not False or financial.get('financialCertified') is not False):
        raise ValueError('Current independent complete two-pass candidate audit required')
    raw = records['raw']
    if (object_field(raw, 'request').get('save') != save or raw.get('fullStreamPasses') != 1
            or raw.get('inputUnchangedAtGuards') is not True or raw.get('completeStreamBytes') != str(save['bytes'])
            or raw.get('completeStreamSha256') != save['sha256'] or raw.get('financialCertified') is not False):
        raise ValueError('Current exact Raw one-pass EOF and unchanged source required')
    wallet = records['actor_wallet']
    retained_wallet = json_object(read_json(file_pin(source_reports.get('actor_wallet'))['path']))
    request = object_field(wallet, 'request')
    if (wallet.get('schema') != 'ck3-captured-actor-wallet-metadata-v1'
            or request.get('archiveReceipt') != evidence['baseline_archive'] or request.get('rawReport') != references['raw']
            or wallet.get('actorNativeId') != str(source['actor_id']) or wallet.get('nativeDateRaw') != date
            or any(wallet.get(key) != retained_wallet.get(key) for key in ('actorVariables', 'PRIMARY_source_variable',
                   'PRIMARY_pointer_available', 'PRIMARY_native_reference_when_available'))):
        raise ValueError('Actual captured actor variables and PRIMARY must match the declared source seed')
    return json_object({'independent_scenario': scenario, 'independent_seed_evidence': evidence,
        'independent_seed_qualified': True, 'business_contract_applicable': False,
        'mainline_continuation_credit': False, 'R54_recovery_or_progress_credit': False,
        'new_game_credit': False, 'business_pass': False, 'product_release_pass': False})


def _futures_gui_evidence(value: object, phase: JsonObject) -> FilePin:
    reference = file_pin(value)
    evidence = phase.get('evidence')
    if not isinstance(evidence, list) or reference not in evidence or pin(reference['path']) != reference:
        raise ValueError('Futures GUI cell must reference its actual retained Root phase evidence')
    return reference


def _futures_gui_archive(value: object, phase: JsonObject, date: int) -> FilePin:
    reference = _futures_gui_evidence(value, phase)
    if reference['bytes'] > 1024 * 1024:
        raise ValueError('Archive metadata exceeds bounded receipt size')
    receipt = json_object(read_json(reference['path']))
    save = file_pin(receipt.get('archive'))
    source = file_pin(receipt.get('source'))
    native = object_field(receipt, 'original_checkpoint_result')
    checkpoint = object_field(native, 'checkpoint')
    materialization = object_field(native, 'materialization')
    # Native accepted/submitted does not itself confirm physical SAVE. Preserve
    # its actual false flag; the SDK checkpoint + independent archive are proof.
    if (receipt.get('schema') != 'ck3-financial-checkpoint-archive-v1' or receipt.get('exact_copy') is not True
            or receipt.get('same_file') is not False
            or type(receipt.get('date_raw')) is not int or receipt.get('date_raw') != date
            or native.get('accepted') is not True or native.get('physical_save_confirmed') is not False
            or checkpoint.get('status') != 'saved' or materialization.get('available') is not True
            or type(checkpoint.get('date_raw')) is not int or checkpoint.get('date_raw') != date
            or type(checkpoint.get('size')) is not int or checkpoint.get('size') != source['bytes']
            or checkpoint.get('sha256') != source['sha256']
            or checkpoint.get('path') != source['path']
            or source['bytes'] != save['bytes'] or source['sha256'] != save['sha256']
            or save['bytes'] <= 0 or save['bytes'] > FUTURES_GUI_PHYSICAL_SAVE_MAX_BYTES
            or Path(source['path']).resolve() == Path(save['path']).resolve()):
        raise ValueError('Accepted saved/materialized SDK checkpoint and independent exact same-day archive required')
    # Count the archived SAVE identity, never the metadata receipt pathname.
    return {'path': str(Path(save['path']).resolve()), 'bytes': save['bytes'], 'sha256': save['sha256']}


def _futures_gui_transactions_review(context: JsonObject, compiled: JsonObject,
                                     phases: JsonObject, date: int) -> JsonObject:
    context = json_object(resolve_post_start(context))
    if not _futures_gui_transactions_enabled(context) or compiled.get('config') != context['case_contract']:
        raise ValueError('Prepared futures GUI contract changed')
    config = object_field(compiled, 'config')
    declared_phases = config['gui_phases']
    if not isinstance(declared_phases, list):
        raise ValueError('Two original Root phases required')
    for value in declared_phases:
        spec = json_object(value)
        phase = object_field(phases, str(spec['id']))
        assertions = object_field(phase, 'assertions')
        requirements = spec['requirements']
        if (phase.get('run_id') != context['run_id'] or phase.get('reviewer') != '/root'
                or not isinstance(requirements, list) or any(assertions.get(str(key)) is not True for key in requirements)):
            raise ValueError('Original Root baseline/transaction review incomplete')
    baseline = object_field(phases, 'bind-current-financial-baseline')
    baseline_archive = _futures_gui_archive(baseline.get('baseline_archive'), baseline, date)
    for key in ('baseline_audit', 'baseline_raw'):
        _futures_gui_evidence(baseline.get(key), baseline)
    transaction = object_field(phases, 'normal-gui-transactions-and-saved-reconciliation')
    cells = object_field(transaction, 'futures_gui_transactions')
    if set(cells) != set(FUTURES_GUI_TRANSACTION_CELLS):
        raise ValueError('Every finite futures GUI cell must explicitly be observed or not observed')
    archive_receipts = transaction.get('physical_archives')
    if not isinstance(archive_receipts, list) or not 1 <= len(archive_receipts) <= FUTURES_GUI_PHYSICAL_SAVE_MAXIMUM:
        raise ValueError('All actual checkpoints, including unfilled/rejected attempts, must fit the six-archive proposal')
    archives: dict[str, FilePin] = {}
    for reference in archive_receipts:
        saved = _futures_gui_archive(reference, transaction, date)
        if saved['path'] in archives:
            raise ValueError('Physical checkpoint is listed more than once through receipt aliases')
        archives[saved['path']] = saved
    if archives.get(baseline_archive['path']) != baseline_archive:
        raise ValueError('Actual baseline checkpoint must be retained in the complete archive list')
    observed: list[str] = []
    missing: list[str] = []
    for name in FUTURES_GUI_TRANSACTION_CELLS:
        cell = object_field(cells, name)
        if cell.get('status') == 'NOT_OBSERVED':
            if set(cell) != {'status', 'reason', 'evidence'} or not isinstance(cell.get('reason'), str) or not cell['reason']:
                raise ValueError('Missing qualification/liquidity/fill remains explicitly NOT_OBSERVED')
            evidence = cell['evidence']
            if not isinstance(evidence, list):
                raise ValueError('Unobserved evidence must be an explicit list')
            for reference in evidence:
                _futures_gui_evidence(reference, transaction)
            missing.append(name)
            continue
        if cell.get('status') != 'OBSERVED' or set(cell) != {'status', 'assertions', 'before_archive', 'after_archive', 'gui_actions', 'audit', 'raw'}:
            raise ValueError('Unknown or incomplete futures GUI cell result')
        assertions = object_field(cell, 'assertions')
        required = {*FUTURES_GUI_COMMON_ASSERTIONS, FUTURES_GUI_CELL_ASSERTIONS[name]}
        if set(assertions) != required or any(value is not True for value in assertions.values()):
            raise ValueError('Only individually reviewed real business receives local observation credit')
        before = _futures_gui_archive(cell['before_archive'], transaction, date)
        after = _futures_gui_archive(cell['after_archive'], transaction, date)
        if before['path'] == after['path'] or (before['bytes'], before['sha256']) == (after['bytes'], after['sha256']):
            raise ValueError('An unchanged reused checkpoint cannot prove both operation endpoints')
        if archives.get(before['path']) != before or archives.get(after['path']) != after:
            raise ValueError('Observed cell endpoint is absent from the complete actual checkpoint list')
        actions = cell['gui_actions']
        if not isinstance(actions, list) or not 1 <= len(actions) <= 64:
            raise ValueError('Actual bounded normal GUI query/activation receipts required')
        for value in actions:
            action = json_object(value)
            if set(action) != {'query', 'activation'}:
                raise ValueError('Each normal GUI activation needs its own actual query')
            _futures_gui_evidence(action['query'], transaction)
            _futures_gui_evidence(action['activation'], transaction)
        for key in ('audit', 'raw'):
            _futures_gui_evidence(cell[key], transaction)
        observed.append(name)
    if len(archives) > FUTURES_GUI_PHYSICAL_SAVE_MAXIMUM:
        raise ValueError('Futures GUI checkpoint proposal exceeded; no extra SAVE/replay authority')
    return json_object({'futures_gui_transactions': cells, 'physical_archives': archive_receipts,
        'observed_cells': observed, 'not_observed_cells': missing,
        'retained_physical_checkpoint_count': len(archives), 'natural_days_advanced': 0,
        'financial_clock_qualified': False, 'derivatives_acceptance_pass': False,
        'business_pass': False, 'product_release_pass': False,
        'result_boundary': 'LOCAL_GUI_OBSERVATIONS_ONLY_NOT_FULL_DERIVATIVES_ACCEPTANCE'})


REDEMPTION_GUI_CELLS = ('prefunded_publish', 'independent_ai_redemption', 'expired_remainder_return')
REDEMPTION_GUI_CONTRACT = {
    'schema': 'ck3-redemption-gui-contract-v1', 'physical_save_maximum': 3,
    'physical_save_max_bytes': 256 * 1024 * 1024, 'prefunded_budget_cents': 1000,
    'window_duration_days': [7, 30], 'observer_arm': False,
    'cell_statuses': ['OBSERVED', 'NOT_OBSERVED'], 'cells': list(REDEMPTION_GUI_CELLS),
    'financial_clock_credit': False, 'whole_product_acceptance_credit': False,
    'toast_delivery_required': False,
}
REDEMPTION_GUI_COMMON_ASSERTIONS = (
    'actual_current_run_coin_window_accounts_and_permanent_identities_bound',
    'actual_new_normal_business_only_no_rearm_renotice_replay_or_synthetic_assets',
    'actual_physical_save_audit_raw_and_complete_financial_graph_independently_reconciled',
    'actual_cash_units_reservations_supply_and_unrelated_accounts_conserved',
)
REDEMPTION_GUI_CELL_ASSERTIONS = {
    'prefunded_publish': 'actual_normal_gui_and_current_xfm_redemption_1_confirmation_prefunded_exactly_1000_from_issuer',
    'independent_ai_redemption': 'actual_new_receipt_from_natural_ai_attention_and_independent_private_holder_not_player_self_redemption',
    'expired_remainder_return': 'actual_financial_expiry_positive_escrow_remainder_and_normal_gui_xfm_redemption_3_confirmation_returned_once',
}
REDEMPTION_GUI_PHASES = ('bind-redemption-cold-baseline', 'normal-gui-prefund-and-publish', 'natural-redemption-and-expired-remainder')


def _redemption_gui_enabled(context: JsonObject) -> bool:
    config = object_field(context, 'case_contract')
    if context.get('case') != 'redemption-gui' and 'redemption_gui_contract' not in config:
        return False
    from ck3_mod_acceptance_background_types import CONTINUOUS14_PASSIVE_STORY_TYPES_V1
    contract = object_field(config, 'redemption_gui_contract')
    phases = config.get('gui_phases')
    durations = contract.get('window_duration_days')
    if (context.get('product') != 'financial-markets' or context.get('case') != 'redemption-gui'
            or config.get('product') != context['product'] or config.get('case_id') != context['case']
            or config.get('schema') != 'ck3-mod-acceptance-product-case-v1'
            or config.get('execution_purpose') != 'product_acceptance'
            or config.get('acceptance_scope') != 'normal_gui_prefunded_redemption_observed_cells_only'
            or config.get('startup_mode') != 'saved_campaign' or config.get('allow_actor_change') is not False
            or config.get('product_loading', 'present') != 'present'
            or type(config.get('maximum_natural_days')) is not int or config.get('maximum_natural_days') != 35
            or contract != REDEMPTION_GUI_CONTRACT
            or not isinstance(durations, list)
            or any(type(value) is not int for value in durations)
            or any(type(contract.get(key)) is not int for key in
                   ('physical_save_maximum', 'physical_save_max_bytes', 'prefunded_budget_cents'))
            or any(contract.get(key) is not False for key in
                   ('observer_arm', 'financial_clock_credit', 'whole_product_acceptance_credit', 'toast_delivery_required'))
            or config.get('passive_story_types') != list(CONTINUOUS14_PASSIVE_STORY_TYPES_V1)
            or config.get('pending_interaction_policy', 'stop_at_boundary') != 'stop_at_boundary'
            or any(key in config for key in ('fixture_source', 'fixture_emitter', 'marker_inventory', 'continuous14_contract', 'clock_purpose'))
            or config.get('whole_product_release_pass') is not False or config.get('business_contract_applicable') is not True
            or not isinstance(phases, list) or len(phases) != 3):
        raise ValueError('Exact independent redemption GUI contract required')
    for value, name, day in zip(phases, REDEMPTION_GUI_PHASES, (0, 0, 35)):
        phase = json_object(value)
        if (phase.get('id') != name or type(phase.get('at_day')) is not int or phase['at_day'] != day
                or phase.get('when_markers') is not None or not phase.get('requirements')):
            raise ValueError('Redemption uses only the existing D0/D0/D35 Root phase loop')
    return True


def _redemption_integer(value: object, *, minimum: int = 1, maximum: int = 2**31 - 1) -> int:
    if type(value) is not int or not isinstance(value, int) or not minimum <= value <= maximum:
        raise ValueError('Exact bounded redemption integer required; missing values are not zero')
    return value


def _redemption_gui_archive(value: object, phase: JsonObject, date: int, context: JsonObject) -> FilePin:
    reference = _futures_gui_evidence(value, phase)
    if reference['bytes'] > 1024 * 1024:
        raise ValueError('Redemption archive metadata exceeds one MiB')
    receipt = json_object(read_json(reference['path']))
    source, saved = file_pin(receipt.get('source')), file_pin(receipt.get('archive'))
    native = object_field(receipt, 'original_checkpoint_result')
    checkpoint, materialization = object_field(native, 'checkpoint'), object_field(native, 'materialization')
    if (receipt.get('schema') != 'ck3-financial-checkpoint-archive-v1'
            or receipt.get('exact_copy') is not True or receipt.get('same_file') is not False
            or type(receipt.get('date_raw')) is not int or receipt['date_raw'] != date
            or native.get('accepted') is not True or native.get('physical_save_confirmed') is not False
            or checkpoint.get('status') != 'saved' or materialization.get('available') is not True
            or type(checkpoint.get('date_raw')) is not int or checkpoint['date_raw'] != date
            or type(checkpoint.get('size')) is not int or checkpoint['size'] != source['bytes']
            or checkpoint.get('path') != source['path'] or checkpoint.get('sha256') != source['sha256']
            or (saved['bytes'], saved['sha256']) != (source['bytes'], source['sha256'])
            or not 0 < saved['bytes'] <= 256 * 1024 * 1024
            or Path(saved['path']).resolve() == Path(source['path']).resolve()
            or not Path(source['path']).resolve().is_relative_to(Path(text_field(context, 'state_dir')).resolve() / 'profile')):
        raise ValueError('Actual current-run saved/materialized checkpoint and independent bounded archive required')
    return {'path': str(Path(saved['path']).resolve()), 'bytes': saved['bytes'], 'sha256': saved['sha256']}


def _redemption_gui_cell(cell: JsonObject, name: str, phase: JsonObject) -> bool:
    if cell.get('status') == 'NOT_OBSERVED':
        if set(cell) != {'status', 'reason', 'evidence'} or not isinstance(cell.get('reason'), str) or not cell['reason']:
            raise ValueError('Unobserved redemption requires an explicit reason')
        evidence = cell['evidence']
        if not isinstance(evidence, list):
            raise ValueError('Unobserved redemption evidence must be a list')
        for value in evidence:
            _futures_gui_evidence(value, phase)
        return False
    required = {*REDEMPTION_GUI_COMMON_ASSERTIONS, REDEMPTION_GUI_CELL_ASSERTIONS[name]}
    assertions = object_field(cell, 'assertions')
    if cell.get('status') != 'OBSERVED' or set(assertions) != required or any(value is not True for value in assertions.values()):
        raise ValueError('Only individually reconciled real redemption business receives local credit')
    for key in ('audit', 'raw', 'whole_graph'):
        _futures_gui_evidence(cell.get(key), phase)
    return True


def _redemption_gui_actions(cell: JsonObject, phase: JsonObject) -> None:
    actions = cell.get('gui_actions')
    if not isinstance(actions, list) or not 1 <= len(actions) <= 64:
        raise ValueError('Original bounded normal GUI queries and activations required')
    for value in actions:
        action = json_object(value)
        if set(action) != {'query', 'activation'}:
            raise ValueError('Each normal GUI activation needs its own fresh query evidence')
        for reference in action.values():
            _futures_gui_evidence(reference, phase)
    confirmation = object_field(cell, 'confirmation')
    if set(confirmation) != {'context', 'selection', 'after_snapshot'}:
        raise ValueError('Actual current event context/selection/after-snapshot required; no fixed option instance')
    for reference in confirmation.values():
        _futures_gui_evidence(reference, phase)


def _redemption_gui_baseline(context: JsonObject, phases: JsonObject, date: int) -> FilePin:
    baseline = object_field(phases, REDEMPTION_GUI_PHASES[0])
    before = _redemption_gui_archive(baseline.get('baseline_archive'), baseline, date, context)
    for key in ('baseline_audit', 'baseline_raw', 'baseline_whole_graph'):
        _futures_gui_evidence(baseline.get(key), baseline)
    source_receipt = _futures_gui_evidence(baseline.get('source_archive'), baseline)
    if source_receipt['bytes'] > 1024 * 1024:
        raise ValueError('Bounded source archive receipt required')
    source = json_object(read_json(source_receipt['path']))
    source_save, startup = file_pin(source.get('archive')), object_field(context, 'saved_campaign')
    if (source.get('schema') != 'ck3-financial-checkpoint-archive-v1' or source.get('exact_copy') is not True
            or type(source.get('date_raw')) is not int or source['date_raw'] != date or startup.get('date_raw') != date
            or (source_save['bytes'], source_save['sha256']) != (startup.get('bytes'), startup.get('sha256'))
            or source_save['path'] == before['path']):
        raise ValueError('Actual prior source archive and separate new cold baseline must bind prepared saved input')
    return before


def _redemption_gui_publication(context: JsonObject, phases: JsonObject, date: int) -> JsonObject:
    before = _redemption_gui_baseline(context, phases, date)
    startup = object_field(context, 'saved_campaign')
    phase = object_field(phases, REDEMPTION_GUI_PHASES[1])
    cell = object_field(phase, 'redemption_publication')
    if not _redemption_gui_cell(cell, 'prefunded_publish', phase):
        raise ValueError('Publication must actually succeed before the natural observation interval')
    if set(cell) != {'status', 'assertions', 'before_archive', 'after_archive', 'gui_actions', 'confirmation',
                     'audit', 'raw', 'whole_graph', 'window'}:
        raise ValueError('Exact retained publication proof required')
    _redemption_gui_actions(cell, phase)
    first = _redemption_gui_archive(cell['before_archive'], phase, date, context)
    after = _redemption_gui_archive(cell['after_archive'], phase, date, context)
    if first != before or first['path'] == after['path'] or (first['bytes'], first['sha256']) == (after['bytes'], after['sha256']):
        raise ValueError('Publication must use the distinct new baseline and post-publication physical saves')
    window = object_field(cell, 'window')
    names = {'coin_native_id', 'coin_id', 'window_native_id', 'window_id', 'issuer_native_id', 'issuer_id',
             'escrow_native_id', 'escrow_id', 'publisher_id', 'controller_id', 'price_cents', 'initial_budget_cents',
             'remaining_cents', 'paid_cents', 'paid_units', 'reclaimed_cents', 'created_financial_day',
             'expiry_financial_day', 'duration_days', 'status'}
    if set(window) != names:
        raise ValueError('Actual complete window terms required; missing fields are not zero')
    window_values: dict[str, int] = {key: _redemption_integer(value,
        minimum=0 if key in {'paid_cents', 'paid_units', 'reclaimed_cents', 'created_financial_day'} else 1)
        for key, value in window.items()}
    if (window_values['coin_native_id'] != 55 or window_values['coin_id'] != 1 or window_values['publisher_id'] != startup.get('player_id')
            or window_values['controller_id'] != window_values['publisher_id'] or window_values['issuer_native_id'] == window_values['escrow_native_id']
            or window_values['issuer_id'] == window_values['escrow_id'] or window_values['initial_budget_cents'] != 1000
            or window_values['remaining_cents'] != 1000 or any(window_values[key] != 0 for key in ('paid_cents', 'paid_units', 'reclaimed_cents'))
            or not 1 <= window_values['price_cents'] <= 1000 or window_values['status'] != 1
            or window_values['duration_days'] not in (7, 30)
            or window_values['expiry_financial_day'] != window_values['created_financial_day'] + window_values['duration_days']):
        raise ValueError('Actual coin55 new dedicated prefunded window must preserve the normal confirmed terms')
    return cell


def _redemption_gui_review(context: JsonObject, compiled: JsonObject, phases: JsonObject,
                           initial_date: int, terminal_date: int) -> JsonObject:
    context = json_object(resolve_post_start(context))
    if not _redemption_gui_enabled(context) or compiled.get('config') != context['case_contract']:
        raise ValueError('Prepared redemption contract changed')
    declared_phases = object_field(compiled, 'config').get('gui_phases')
    if not isinstance(declared_phases, list):
        raise ValueError('Original current-run Root redemption phases required')
    for value in declared_phases:
        spec = json_object(value)
        phase = object_field(phases, str(spec['id']))
        assertions = object_field(phase, 'assertions')
        requirements = spec.get('requirements')
        if (phase.get('run_id') != context['run_id'] or phase.get('reviewer') != '/root'
                or not isinstance(requirements, list)
                or any(assertions.get(str(key)) is not True for key in requirements)):
            raise ValueError('Original current-run Root redemption phases required')
    publication = _redemption_gui_publication(context, phases, initial_date)
    window_values: dict[str, int] = {key: _redemption_integer(value,
        minimum=0 if key in {'paid_cents', 'paid_units', 'reclaimed_cents', 'created_financial_day'} else 1)
        for key, value in object_field(publication, 'window').items()}
    terminal = object_field(phases, REDEMPTION_GUI_PHASES[2])
    cells = object_field(terminal, 'redemption_gui_cells')
    if set(cells) != set(REDEMPTION_GUI_CELLS) or cells['prefunded_publish'] != publication:
        raise ValueError('All three finite cells required; original publication cannot be rewritten')
    receipts = terminal.get('physical_archives')
    if not isinstance(receipts, list) or len(receipts) != 3:
        raise ValueError('Exactly three physical checkpoints including all attempts required; no replay authority')
    dates = (initial_date, initial_date, terminal_date)
    archives = [_redemption_gui_archive(value, terminal, date, context) for value, date in zip(receipts, dates)]
    if len({row['path'] for row in archives}) != 3:
        raise ValueError('Archive receipt aliases cannot multiply one physical SAVE')
    baseline = object_field(phases, REDEMPTION_GUI_PHASES[0])
    if (archives[0] != _redemption_gui_archive(baseline['baseline_archive'], baseline, initial_date, context)
            or archives[1] != _redemption_gui_archive(publication['after_archive'], object_field(phases, REDEMPTION_GUI_PHASES[1]), initial_date, context)
            or terminal_date != initial_date + 35 * 24):
        raise ValueError('Actual cold/published/terminal endpoints and bounded natural calendar required')
    for key in ('terminal_audit', 'terminal_raw', 'terminal_whole_graph'):
        _futures_gui_evidence(terminal.get(key), terminal)
    observed, missing = ['prefunded_publish'], []
    for name in REDEMPTION_GUI_CELLS[1:]:
        cell = object_field(cells, name)
        if not _redemption_gui_cell(cell, name, terminal):
            missing.append(name)
            continue
        specific = {'receipt'} if name == 'independent_ai_redemption' else {'reclaim', 'gui_actions', 'confirmation'}
        if set(cell) != {'status', 'assertions', 'before_archive', 'after_archive', 'audit', 'raw', 'whole_graph', *specific}:
            raise ValueError('Exact individually reviewed redemption cell required')
        before = _redemption_gui_archive(cell['before_archive'], terminal, initial_date, context)
        after = _redemption_gui_archive(cell['after_archive'], terminal, terminal_date, context)
        if before != archives[1] or after != archives[2] or (before['bytes'], before['sha256']) == (after['bytes'], after['sha256']):
            raise ValueError('Observed natural business requires distinct published/terminal physical endpoints')
        if name == 'independent_ai_redemption':
            receipt = object_field(cell, 'receipt')
            keys = {'native_id', 'id', 'coin_native_id', 'coin_id', 'window_native_id', 'window_id', 'payer_native_id', 'payer_id',
                    'payee_native_id', 'payee_id', 'holder_id', 'beneficiary_id', 'controller_id', 'paid_units', 'paid_cents',
                    'price_cents', 'financial_day', 'status'}
            if set(receipt) != keys:
                raise ValueError('Actual new immutable redemption receipt witness required')
            receipt_values: dict[str, int] = {key: _redemption_integer(value, minimum=0 if key == 'financial_day' else 1)
                for key, value in receipt.items()}
            if (any(receipt_values[key] != window_values[key] for key in ('coin_native_id', 'coin_id', 'window_native_id', 'window_id', 'price_cents', 'controller_id'))
                    or receipt_values['payer_native_id'] != window_values['escrow_native_id'] or receipt_values['payer_id'] != window_values['escrow_id']
                    or receipt_values['payee_native_id'] in (window_values['escrow_native_id'], window_values['issuer_native_id'])
                    or receipt_values['payee_id'] in (window_values['escrow_id'], window_values['issuer_id'])
                    or receipt_values['holder_id'] != receipt_values['beneficiary_id'] or receipt_values['holder_id'] == window_values['publisher_id']
                    or receipt_values['paid_units'] != 100 or receipt_values['paid_cents'] != window_values['price_cents'] or receipt_values['status'] != 1
                    or not window_values['created_financial_day'] <= receipt_values['financial_day'] < window_values['expiry_financial_day']):
                raise ValueError('Only a real independently owned natural one-lot AI redemption receives this cell')
        else:
            _redemption_gui_actions(cell, terminal)
            reclaim = object_field(cell, 'reclaim')
            keys = {'window_native_id', 'window_id', 'financial_day', 'remaining_before_cents', 'reclaimed_delta_cents',
                    'remaining_after_cents', 'escrow_after_cents', 'status'}
            if set(reclaim) != keys:
                raise ValueError('Actual financial expiry and positive remainder transfer required')
            reclaim_values: dict[str, int] = {key: _redemption_integer(value, minimum=0) for key, value in reclaim.items()}
            if (reclaim_values['window_native_id'] != window_values['window_native_id'] or reclaim_values['window_id'] != window_values['window_id']
                    or reclaim_values['financial_day'] < window_values['expiry_financial_day']
                    or not 0 < reclaim_values['remaining_before_cents'] <= 1000
                    or reclaim_values['reclaimed_delta_cents'] != reclaim_values['remaining_before_cents']
                    or reclaim_values['remaining_after_cents'] != 0 or reclaim_values['escrow_after_cents'] != 0 or reclaim_values['status'] != 4):
                raise ValueError('Calendar age alone or an empty escrow does not prove a real expired fund return')
        observed.append(name)
    # Optional toast DTO/query originals may occur in phase evidence. They never
    # add a delivery cell: queued news and current-interface delivery differ.
    return json_object({'redemption_gui_cells': cells, 'physical_archives': receipts,
        'observed_cells': observed, 'not_observed_cells': missing, 'retained_physical_checkpoint_count': 3,
        'natural_days_advanced': 35, 'financial_clock_qualified': False,
        'business_pass': False, 'product_release_pass': False, 'toast_delivery_qualified': False,
        'result_boundary': 'LOCAL_REDEMPTION_OBSERVATIONS_ONLY_NOT_WHOLE_PRODUCT_ACCEPTANCE'})


REDEMPTION_EXISTING_PHASES = ('bind-existing-redemption-window', 'observe-existing-window-expiry')
REDEMPTION_EXISTING_CELLS = ('independent_ai_redemption', 'expired_remainder_return')
REDEMPTION_EXISTING_CONTRACT = {
    'schema': 'ck3-redemption-existing-window-contract-v1',
    'current_physical_save_maximum': 1, 'physical_save_max_bytes': 384 * 1024 * 1024,
    'historical_physical_save_count': 2, 'retained_distinct_physical_save_count': 3,
    'observer_arm': False, 'republish': False, 'current_publication_credit': False,
    'cold_same_day_complete_graph_credit': False, 'financial_clock_credit': False,
    'whole_product_acceptance_credit': False,
    'cells': list(REDEMPTION_EXISTING_CELLS), 'cell_statuses': ['OBSERVED', 'NOT_OBSERVED'],
}
REDEMPTION_EXISTING_HISTORY = {'path': 'C:\\workspace\\ck3_eternal_recurrence\\tools\\ck3_mod_acceptance_cases\\financial_markets_redemption_r42_history.json', 'bytes': 2913, 'sha256': '14f2a4df7425cabf2ac5fbaf46ecb9277ba7d0fcedb979cd09bafce687b0ed69'}


def _redemption_existing_enabled(context: JsonObject) -> bool:
    config = object_field(context, 'case_contract')
    if context.get('case') != 'redemption-existing-window' and 'redemption_existing_window_contract' not in config:
        return False
    from ck3_mod_acceptance_background_types import CONTINUOUS14_PASSIVE_STORY_TYPES_V1
    contract = object_field(config, 'redemption_existing_window_contract')
    if (context.get('product') != 'financial-markets' or context.get('case') != 'redemption-existing-window'
            or config.get('product') != context['product'] or config.get('case_id') != context['case']
            or config.get('schema') != 'ck3-mod-acceptance-product-case-v1'
            or config.get('execution_purpose') != 'product_acceptance'
            or config.get('acceptance_scope') != 'existing_prefunded_window_natural_local_observations_only'
            or config.get('startup_mode') != 'saved_campaign' or config.get('allow_actor_change') is not False
            or config.get('product_loading', 'present') != 'present'
            or type(config.get('maximum_natural_days')) is not int or config['maximum_natural_days'] != 35
            or contract != REDEMPTION_EXISTING_CONTRACT
            or any(type(contract.get(key)) is not int for key in ('current_physical_save_maximum',
                'physical_save_max_bytes', 'historical_physical_save_count', 'retained_distinct_physical_save_count'))
            or any(contract.get(key) is not False for key in ('observer_arm', 'republish',
                'current_publication_credit', 'cold_same_day_complete_graph_credit',
                'financial_clock_credit', 'whole_product_acceptance_credit'))
            or config.get('source_history_manifest') != REDEMPTION_EXISTING_HISTORY
            or config.get('passive_story_types') != list(CONTINUOUS14_PASSIVE_STORY_TYPES_V1)
            or config.get('pending_interaction_policy', 'stop_at_boundary') != 'stop_at_boundary'
            or any(key in config for key in ('fixture_source', 'fixture_emitter', 'marker_inventory',
                'continuous14_contract', 'clock_purpose', 'redemption_gui_contract'))
            or config.get('whole_product_release_pass') is not False or config.get('business_contract_applicable') is not True):
        raise ValueError('Exact source-bound existing redemption continuation contract required')
    phases = config.get('gui_phases')
    if not isinstance(phases, list) or len(phases) != 2:
        raise ValueError('Existing redemption has only D0 binding and D35 terminal phases')
    for value, name, day in zip(phases, REDEMPTION_EXISTING_PHASES, (0, 35)):
        phase = json_object(value)
        requirements = phase.get('requirements')
        if (phase.get('id') != name or type(phase.get('at_day')) is not int or phase['at_day'] != day
                or phase.get('when_markers') is not None or not isinstance(requirements, list)
                or not requirements or any(not isinstance(key, str) or not key for key in requirements)):
            raise ValueError('Exact finite D0/D35 existing-window phases required')
    return True


def _redemption_existing_metadata(value: object) -> JsonObject:
    reference = file_pin(value)
    if reference['bytes'] > 64 * 1024 * 1024 or Path(reference['path']).suffix.lower() == '.ck3':
        raise ValueError('Bounded immutable metadata only; no SAVE content read')
    if checked_capture_pin(reference) != reference:
        raise ValueError('Existing-window metadata changed')
    return json_object(read_json(reference['path']))


def _redemption_existing_window(value: object) -> dict[str, int]:
    window = json_object(value)
    names = {'coin_native_id', 'coin_id', 'window_native_id', 'window_id', 'issuer_native_id', 'issuer_id',
        'escrow_native_id', 'escrow_id', 'publisher_id', 'controller_id', 'price_cents', 'initial_budget_cents',
        'remaining_cents', 'paid_cents', 'paid_units', 'reclaimed_cents', 'created_financial_day',
        'expiry_financial_day', 'duration_days', 'status'}
    if set(window) != names:
        raise ValueError('Exact retained window fields required; no missing-value default')
    return {key: _redemption_integer(item, minimum=0 if key in {'paid_cents', 'paid_units',
        'reclaimed_cents', 'created_financial_day'} else 1) for key, item in window.items()}


def _redemption_existing_archive(value: object, date: int, context: JsonObject, *, current: bool) -> FilePin:
    receipt = _redemption_existing_metadata(value)
    source, saved = file_pin(receipt.get('source')), file_pin(receipt.get('archive'))
    native = object_field(receipt, 'original_checkpoint_result')
    checkpoint, materialization = object_field(native, 'checkpoint'), object_field(native, 'materialization')
    maximum = 384 * 1024 * 1024 if current else 256 * 1024 * 1024
    if (receipt.get('schema') != 'ck3-financial-checkpoint-archive-v1'
            or receipt.get('exact_copy') is not True or receipt.get('same_file') is not False
            or type(receipt.get('date_raw')) is not int or receipt['date_raw'] != date
            or native.get('accepted') is not True or native.get('physical_save_confirmed') is not False
            or checkpoint.get('status') != 'saved' or materialization.get('available') is not True
            or type(checkpoint.get('date_raw')) is not int or checkpoint['date_raw'] != date
            or type(checkpoint.get('size')) is not int or checkpoint['size'] != source['bytes']
            or checkpoint.get('path') != source['path'] or checkpoint.get('sha256') != source['sha256']
            or (saved['bytes'], saved['sha256']) != (source['bytes'], source['sha256'])
            or not 0 < saved['bytes'] <= maximum
            or Path(saved['path']).resolve() == Path(source['path']).resolve()
            or (current and not Path(source['path']).resolve().is_relative_to(
                Path(text_field(context, 'state_dir')).resolve() / 'profile'))):
        raise ValueError('Actual bounded saved/materialized independent archive required')
    return saved


def _redemption_existing_history(context: JsonObject) -> JsonObject:
    config = object_field(context, 'case_contract')
    reference = file_pin(config.get('source_history_manifest'))
    if reference != REDEMPTION_EXISTING_HISTORY:
        raise ValueError('Arbitrary foreign-run proof is not an approved source history')
    history = _redemption_existing_metadata(reference)
    expected_keys = {'schema', 'machine_id', 'historical_run_id', 'source_date_raw', 'actor_id',
        'baseline_archive', 'published_archive', 'baseline_pipeline', 'published_pipeline', 'reconciliation',
        'publication_review', 'closure_before_release', 'closure_released', 'window',
        'publication_phase_consumed', 'historical_case_acceptance_pass', 'historical_natural_days',
        'current_publication_credit', 'cold_same_day_complete_graph_credit', 'financialCertified'}
    if (set(history) != expected_keys or history.get('schema') != 'ck3-redemption-r42-source-history-v1'
            or history.get('machine_id') != '4-8e1c2f1861'
            or history.get('historical_run_id') != '4-8e1c2f1861--financial-markets--R0042'
            or context.get('run_id') == history['historical_run_id']
            or type(history.get('source_date_raw')) is not int or history['source_date_raw'] != 53147328
            or type(history.get('actor_id')) is not int or history['actor_id'] != 31254
            or type(history.get('historical_natural_days')) is not int or history['historical_natural_days'] != 0
            or any(history.get(key) is not False for key in ('publication_phase_consumed',
                'historical_case_acceptance_pass', 'current_publication_credit',
                'cold_same_day_complete_graph_credit', 'financialCertified'))):
        raise ValueError('Historical R42 GAP must remain historical and unconsumed')
    rows = {key: _redemption_existing_metadata(history[key]) for key in ('baseline_pipeline',
        'published_pipeline', 'reconciliation', 'publication_review', 'closure_before_release', 'closure_released')}
    recon, review = rows['reconciliation'], rows['publication_review']
    closed, released = rows['closure_before_release'], rows['closure_released']
    source_date = _redemption_integer(history.get('source_date_raw'))
    before = _redemption_existing_archive(history['baseline_archive'], source_date, context, current=False)
    source = _redemption_existing_archive(history['published_archive'], source_date, context, current=False)
    startup = object_field(context, 'saved_campaign')
    _redemption_existing_window(history.get('window'))
    if (any(row.get('run_id') != history['historical_run_id'] for row in rows.values())
            or recon.get('window') != history['window'] or object_field(review, 'redemption_publication').get('window') != history['window']
            or recon.get('baseline_pipeline') != history['baseline_pipeline'] or recon.get('published_pipeline') != history['published_pipeline']
            or rows['baseline_pipeline'].get('archive') != history['baseline_archive']
            or rows['published_pipeline'].get('archive') != history['published_archive']
            or any(rows[name].get('checkpoint_readback_and_reports_completed') is not True for name in ('baseline_pipeline', 'published_pipeline'))
            or closed.get('normal_close_qualified') is not True or closed.get('case_acceptance_pass') is not False
            or closed.get('public_run_actual_exit_code') != 2 or closed.get('public_verify_actual_exit_code') != 2
            or closed.get('new_calendar_days') != 0 or closed.get('latest_physical_checkpoint') != history['published_archive']
            or released.get('closure') != history['closure_before_release'] or released.get('actual_resources') != []
            or released.get('actual_public_closed_lease') is not True
            or (source['bytes'], source['sha256']) != (startup.get('bytes'), startup.get('sha256'))
            or startup.get('date_raw') != history['source_date_raw'] or startup.get('player_id') != history['actor_id']
            or before['path'] == source['path'] or (before['bytes'], before['sha256']) == (source['bytes'], source['sha256'])):
        raise ValueError('Exact retained paid forward source, local reconciliation and normal closure required')
    return history


def _redemption_existing_binding(context: JsonObject, phase: JsonObject, date: int) -> JsonObject:
    history = _redemption_existing_history(context)
    if phase.get('source_history_manifest') != REDEMPTION_EXISTING_HISTORY or date != history['source_date_raw']:
        raise ValueError('Current D0 must bind the exact paid source history without new baseline SAVE')
    snapshot_ref = _futures_gui_evidence(phase.get('current_snapshot'), phase)
    snapshot = _redemption_existing_metadata(snapshot_ref)
    actor, binding = object_field(snapshot, 'played_character'), object_field(snapshot, 'managed_campaign_run_binding')
    if (type(snapshot.get('date_raw')) is not int or snapshot['date_raw'] != date or snapshot.get('paused') is not True
            or snapshot.get('source') != 'injected-dll-named-pipe' or actor.get('source') != 'native'
            or type(actor.get('character_id')) is not int or actor['character_id'] != history['actor_id']
            or actor.get('alive') is not True or binding.get('run_id') != context['run_id']
            or Path(text_field(binding, 'state_dir')).resolve() != Path(text_field(context, 'state_dir')).resolve()
            or _redemption_existing_window(phase.get('window')) != _redemption_existing_window(history['window'])):
        raise ValueError('New cold Native actor/date, retained window identity and readonly GUI route required')
    queries = phase.get('window_queries')
    if not isinstance(queries, list) or not 1 <= len(queries) <= 16:
        raise ValueError('Current read-only window GUI queries required; historical publication is not current GUI')
    for reference in queries:
        _futures_gui_evidence(reference, phase)
    _futures_gui_evidence(phase.get('source_history_manifest'), phase)
    return history


def _redemption_existing_review(context: JsonObject, compiled: JsonObject, phases: JsonObject,
                                initial_date: int, terminal_date: int) -> JsonObject:
    context = json_object(resolve_post_start(context))
    if not _redemption_existing_enabled(context) or compiled.get('config') != context['case_contract']:
        raise ValueError('Prepared existing-window contract changed')
    specs = object_field(compiled, 'config')['gui_phases']
    if not isinstance(specs, list):
        raise ValueError('Actual declared Root phase list required')
    for value in specs:
        spec = json_object(value); phase = object_field(phases, str(spec['id']))
        assertions = object_field(phase, 'assertions'); requirements = spec['requirements']
        if (phase.get('run_id') != context['run_id'] or phase.get('reviewer') != '/root'
                or not isinstance(requirements, list) or any(assertions.get(str(key)) is not True for key in requirements)):
            raise ValueError('Both current-run Root judgments are required; no historical phase replay')
    history = _redemption_existing_binding(context, object_field(phases, REDEMPTION_EXISTING_PHASES[0]), initial_date)
    if terminal_date != initial_date + 35 * 24:
        raise ValueError('Exactly 35 new natural days required; never financial expiry by calendar alone')
    terminal = object_field(phases, REDEMPTION_EXISTING_PHASES[1])
    receipts = terminal.get('physical_archives')
    if not isinstance(receipts, list) or len(receipts) != 3 or receipts[:2] != [history['baseline_archive'], history['published_archive']]:
        raise ValueError('Historical two plus exactly one new terminal archive required; no new D0 SAVE')
    for reference in receipts:
        _futures_gui_evidence(reference, terminal)
    saved = [_redemption_existing_archive(reference, date, context, current=current)
        for reference, date, current in zip(receipts, (initial_date, initial_date, terminal_date), (False, False, True))]
    if len({row['path'] for row in saved}) != 3 or (saved[1]['bytes'], saved[1]['sha256']) == (saved[2]['bytes'], saved[2]['sha256']):
        raise ValueError('Distinct original physical SAVE sources required; receipt aliases do not add endpoints')
    pipeline = _redemption_existing_metadata(_futures_gui_evidence(terminal.get('terminal_pipeline'), terminal))
    if (pipeline.get('schema') != 'ck3-continuous14-checkpoint-original-pipeline-v1'
            or pipeline.get('run_id') != context['run_id'] or pipeline.get('kind') != 'terminal'
            or pipeline.get('archive') != receipts[2] or pipeline.get('source_baseline_archive') != history['published_archive']
            or pipeline.get('actual_date_raw') != terminal_date or pipeline.get('prior_date_raw') != initial_date
            or pipeline.get('checkpoint_readback_and_reports_completed') is not True
            or pipeline.get('all_original_steps_accepted_with_explicit_exit_policy') is not True
            or pipeline.get('consumed_completed_SAVE_count') != 1 or pipeline.get('reserve_seconds') != 180):
        raise ValueError('One current terminal pipeline must compare against actual historical published source')
    steps = pipeline.get('original_steps')
    if not isinstance(steps, list) or not steps:
        raise ValueError('Original terminal pipeline operations required')
    for value in steps:
        step = json_object(value)
        wait = _redemption_existing_metadata(step.get('original_wait'))
        operation = text_field(step, 'operation')
        allowed = (0, 2) if operation.startswith(('COMPARE-metadata-', 'COMPARE-whole-records-')) else (0,)
        if (wait.get('actual_original_popen_wait') is not True or type(wait.get('returncode')) is not int
                or wait['returncode'] not in allowed or type(step.get('returncode')) is not int
                or step['returncode'] != wait['returncode']):
            raise ValueError('Terminal original operation failed; no retry or invented successful summary')
        for role in ('stdout', 'stderr'):
            checked_capture_pin(wait.get(role))
    for key, role in (('terminal_audit', 'audit'), ('terminal_raw', 'actor_raw'), ('terminal_whole_graph', 'whole_digest')):
        if _futures_gui_evidence(terminal.get(key), terminal) != pipeline.get(role):
            raise ValueError('Current terminal pipeline evidence crossed source/role')
    for role in ('metadata_comparison', 'whole_record_comparison'):
        _futures_gui_evidence(pipeline.get(role), terminal)
    selected_ref = _futures_gui_evidence(terminal.get('terminal_selected_raw'), terminal)
    selected = _redemption_existing_metadata(selected_ref)
    raw_request = object_field(selected, 'request')
    raw_stories = selected.get('stories')
    requested_ids = raw_request.get('storyIds')
    if not isinstance(raw_stories, list) or not 1 <= len(raw_stories) <= 16:
        raise ValueError('Bounded explicit terminal story readback required')
    covered = {text_field(json_object(value), 'id') for value in raw_stories}
    source_window = _redemption_existing_window(history['window'])
    required_ids = {'52', *[str(source_window[key]) for key in
        ('coin_native_id', 'window_native_id', 'issuer_native_id', 'escrow_native_id')]}
    if (selected.get('status') != 'UNQUALIFIED_EXACT_STORY_DIAGNOSTIC'
            or selected.get('machineId') != history['machine_id']
            or raw_request.get('save') != saved[2] or raw_request.get('archiveReceipt') != receipts[2]
            or raw_request.get('expectedDateRaw') != terminal_date or raw_request.get('actorIds') != ['31254']
            or not isinstance(requested_ids, list) or not all(isinstance(value, str) for value in requested_ids)
            or set(requested_ids) != covered or len(requested_ids) != len(covered)
            or len(covered) != len(raw_stories) or not required_ids <= covered
            or type(selected.get('fullStreamPasses')) is not int or selected.get('fullStreamPasses') != 1
            or selected.get('completeStreamBytes') != str(saved[2]['bytes'])
            or selected.get('completeStreamSha256') != saved[2]['sha256']
            or selected.get('inputUnchangedAtGuards') is not True or not isinstance(selected.get('before'), dict)
            or not selected.get('before') or selected.get('before') != selected.get('after')
            or selected.get('actorTablePathObserved') is not True):
        raise ValueError('Actual same-archive complete-EOF exact window/account raw evidence required')
    cells = object_field(terminal, 'redemption_existing_cells')
    if set(cells) != set(REDEMPTION_EXISTING_CELLS):
        raise ValueError('Only current natural AI receipt and expired return cells are eligible')
    window = _redemption_existing_window(history['window']); observed: list[str] = []; missing: list[str] = []
    for name in REDEMPTION_EXISTING_CELLS:
        cell = object_field(cells, name)
        if not _redemption_gui_cell(cell, name, terminal):
            missing.append(name); continue
        specific = {'receipt'} if name == 'independent_ai_redemption' else {'reclaim', 'gui_actions', 'confirmation'}
        if set(cell) != {'status', 'assertions', 'before_archive', 'after_archive', 'audit', 'raw', 'whole_graph', *specific}:
            raise ValueError('Closed current local business cell required')
        if (cell['before_archive'] != receipts[1] or cell['after_archive'] != receipts[2]
                or cell['audit'] != terminal['terminal_audit'] or cell['raw'] != selected_ref
                or cell['whole_graph'] != terminal['terminal_whole_graph']):
            raise ValueError('Observed cell must use historical paid source and current independently read terminal')
        if name == 'independent_ai_redemption':
            receipt = object_field(cell, 'receipt')
            keys = {'native_id', 'id', 'coin_native_id', 'coin_id', 'window_native_id', 'window_id', 'payer_native_id', 'payer_id',
                'payee_native_id', 'payee_id', 'holder_id', 'beneficiary_id', 'controller_id', 'paid_units', 'paid_cents',
                'price_cents', 'financial_day', 'status', 'identity_version', 'is_ai', 'primary_known',
                'primary_native_id', 'primary_id', 'used_primary'}
            if set(receipt) != keys:
                raise ValueError('Exact actual immutable natural AI receipt required')
            values = {key: _redemption_integer(value, minimum=0 if key == 'financial_day' else 1) for key, value in receipt.items()}
            if (not {str(values['native_id']), str(values['payee_native_id'])} <= covered
                    or any(values[key] != window[key] for key in ('coin_native_id', 'coin_id', 'window_native_id', 'window_id', 'price_cents', 'controller_id'))
                    or values['payer_native_id'] != window['escrow_native_id'] or values['payer_id'] != window['escrow_id']
                    or values['payee_native_id'] in (window['escrow_native_id'], window['issuer_native_id'])
                    or values['payee_id'] in (window['escrow_id'], window['issuer_id'])
                    or values['holder_id'] != values['beneficiary_id'] or values['holder_id'] == window['publisher_id']
                    or any(values[key] != 1 for key in ('identity_version', 'is_ai', 'primary_known', 'used_primary'))
                    or values['primary_native_id'] != values['payee_native_id'] or values['primary_id'] != values['payee_id']
                    or values['paid_units'] != 100 or values['paid_cents'] != window['price_cents'] or values['status'] != 1
                    or not window['created_financial_day'] <= values['financial_day'] < window['expiry_financial_day']):
                raise ValueError('Only an actual independently owned natural redemption gains AI local credit')
        else:
            _redemption_gui_actions(cell, terminal)
            reclaim = object_field(cell, 'reclaim')
            keys = {'window_native_id', 'window_id', 'financial_day', 'remaining_before_cents', 'reclaimed_delta_cents',
                'remaining_after_cents', 'escrow_before_cents', 'escrow_after_cents', 'issuer_free_before_cents',
                'issuer_free_after_cents', 'issuer_reserved_before_cents', 'issuer_reserved_after_cents',
                'reclaimed_before_cents', 'reclaimed_after_cents', 'status', 'receipt_version', 'actor_id',
                'coin_native_id', 'coin_id', 'issuer_native_id', 'issuer_id', 'escrow_native_id', 'escrow_id',
                'initial_cents', 'paid_before_cents', 'paid_after_cents', 'status_before',
                'escrow_reserved_before_cents', 'escrow_reserved_after_cents'}
            if set(reclaim) != keys:
                raise ValueError('Actual isolated current pre/post reclaim cash and window counters required')
            values = {key: _redemption_integer(value, minimum=0) for key, value in reclaim.items()}
            if (values['window_native_id'] != window['window_native_id'] or values['window_id'] != window['window_id']
                    or values['receipt_version'] != 1 or values['actor_id'] != window['controller_id']
                    or any(values[key] != window[key] for key in ('coin_native_id', 'coin_id',
                        'issuer_native_id', 'issuer_id', 'escrow_native_id', 'escrow_id'))
                    or values['initial_cents'] != window['initial_budget_cents']
                    or values['initial_cents'] != values['paid_before_cents'] + values['remaining_before_cents'] + values['reclaimed_before_cents']
                    or values['paid_after_cents'] != values['paid_before_cents'] or values['reclaimed_before_cents'] != 0
                    or values['status_before'] not in (1, 2)
                    or values['escrow_reserved_before_cents'] != 0 or values['escrow_reserved_after_cents'] != 0
                    or values['financial_day'] < window['expiry_financial_day']
                    or not 0 < values['remaining_before_cents'] <= window['initial_budget_cents']
                    or values['reclaimed_delta_cents'] != values['remaining_before_cents']
                    or values['escrow_before_cents'] != values['remaining_before_cents']
                    or values['issuer_free_after_cents'] - values['issuer_free_before_cents'] != values['reclaimed_delta_cents']
                    or values['reclaimed_after_cents'] - values['reclaimed_before_cents'] != values['reclaimed_delta_cents']
                    or values['issuer_reserved_before_cents'] != values['issuer_reserved_after_cents']
                    or values['remaining_after_cents'] != 0 or values['escrow_after_cents'] != 0 or values['status'] != 4):
                raise ValueError('Financial expiry and positive once-only escrow-to-issuer return required')
        observed.append(name)
    return json_object({'redemption_existing_cells': cells, 'physical_archives': receipts,
        'source_history_manifest': REDEMPTION_EXISTING_HISTORY, 'historical_publication_run_id': history['historical_run_id'],
        'historical_publication_phase_consumed': False, 'historical_case_acceptance_pass': False,
        'current_publication_credit': False, 'cold_same_day_complete_graph_credit': False,
        'observed_cells': observed, 'not_observed_cells': missing, 'natural_days_advanced': 35,
        'current_physical_checkpoint_count': 1, 'retained_physical_checkpoint_count': 3,
        'financial_clock_qualified': False, 'financialCertified': False, 'business_pass': False,
        'product_release_pass': False, 'toast_delivery_qualified': False,
        'result_boundary': 'EXISTING_WINDOW_LOCAL_RETURN_OR_AI_RECEIPT_ONLY_NOT_R42_OR_WHOLE_PRODUCT_PASS'})


def _run_fixture_case(context, client):
    compiled, binding = compiled_contract(context)
    config = compiled['config']
    futures_gui = _futures_gui_transactions_enabled(json_object(context))
    redemption_gui = _redemption_gui_enabled(json_object(context))
    redemption_existing = _redemption_existing_enabled(json_object(context))
    independent_seed = _independent_financial_seed_enabled(json_object(context))
    if futures_gui or redemption_gui or redemption_existing or independent_seed:
        context = resolve_post_start(context)
        require(config == context['case_contract'], 'Prepared selected GUI config differs')
    pending_policy = _fixture_pending_interaction_policy(config)
    inbox_observations: list[JsonObject] = []
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
                    if redemption_existing and phase['id'] == REDEMPTION_EXISTING_PHASES[0]:
                        _redemption_existing_binding(json_object(context), json_object(phases[phase['id']]), initial_date)
                    if redemption_gui and phase['id'] == REDEMPTION_GUI_PHASES[0]:
                        _redemption_gui_baseline(json_object(context), json_object(phases), initial_date)
                    if redemption_gui and phase['id'] == REDEMPTION_GUI_PHASES[1]:
                        _redemption_gui_publication(json_object(context), json_object(phases), initial_date)
                    frame = client.snapshot(allow_actor_change=config.get('allow_actor_change', False), require_event_free=False)
                    frames.append({'day': day, 'after_gui': phase['id'], 'snapshot': frame})
                    require(type(frame.get('date_raw')) is int and frame['date_raw'] >= initial_date,
                            'Actual native calendar after GUI is required')
                    day = (frame['date_raw'] - initial_date) / 24
                    require(day <= config['maximum_natural_days'], 'GUI phase exceeded shared case calendar bound')
                    observed = marker_observation(client.log_bytes(), compiled)
            # An actual event is handled by Root from its current instance. Never
            # invent an option index or claim that dispatch proves a GUI outcome.
            boundary = _fixture_boundary(frame, pending_policy)
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
            if pending_policy == 'observe_unanswered_inbox':
                inbox_observations.append(json_object(value['pending_interaction_observation']))
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
    product_absent = config.get('product_loading', 'present') == 'absent'
    if product_absent:
        require(not (profile / 'mod/product.mod').exists() and not (profile / 'mod-content/product').exists(),
                'Pre-product campaign unexpectedly mounted a product')
    process = getattr(client, '_process', None)
    facts = {'schema': 'ck3-mod-acceptance-product-case-facts-v1', 'run_id': context['run_id'],
        'product': context['product'], 'case': context['case'], 'compiled_contract': binding,
        'acceptance_scope': config['acceptance_scope'], 'business_contract_applicable': not static_load_only and not independent_seed,
        'load_boundary_qualified': True, 'actual_native_frames': frames, 'actual_process': process,
        'enabled_mods': enabled, 'product_outer': None if product_absent else pin(profile / 'mod/product.mod'),
        'product_inner': None if product_absent else pin(profile / 'mod-content/product/descriptor.mod'),
        'marker_observation': observed, 'root_phases': phases,
        'case_contract_qualified': observed['qualified'], 'gui_contract_qualified': static_load_only or all(
            phase['id'] in phases for phase in config['gui_phases']),
        'result_boundary': 'LOAD_BOUNDARY_PASS' if static_load_only else 'SOURCE_CASE_OBSERVED_PENDING_PRODUCT_AGGREGATION',
        'pending_product_business': config.get('uncovered_product_business', []),
        'business_pass': False, 'product_release_pass': False}
    if pending_policy == 'observe_unanswered_inbox':
        facts['pending_interaction_policy'] = pending_policy
        facts['pending_interaction_observations'] = inbox_observations
    if futures_gui:
        facts.update(_futures_gui_transactions_review(json_object(context), json_object(compiled), json_object(phases), initial_date))
    if redemption_gui:
        facts.update(_redemption_gui_review(json_object(context), json_object(compiled), json_object(phases),
            initial_date, frame['date_raw']))
    if redemption_existing:
        facts.update(_redemption_existing_review(json_object(context), json_object(compiled), json_object(phases),
            initial_date, frame['date_raw']))
    if independent_seed:
        facts.update(_independent_financial_seed_review(json_object(context), json_object(compiled),
            json_object(phases), json_object(frames[0]['snapshot'])))
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
    if _futures_gui_transactions_enabled(json_object(context)):
        context = resolve_post_start(context)
        frames = facts.get('actual_native_frames')
        require(isinstance(frames, list) and bool(frames), 'Original same-day native frames required')
        date = json_object(json_object(frames[0])['snapshot']).get('date_raw')
        require(type(date) is int, 'Actual initial native date required')
        review = _futures_gui_transactions_review(json_object(context), json_object(compiled),
            json_object(facts['root_phases']), date)
        require(all(facts.get(key) == value for key, value in review.items()), 'Original cell statuses or credit changed')
        require(all(json_object(json_object(row)['snapshot']).get('date_raw') == date for row in frames),
                'Futures GUI must remain on the original native date')
    if _redemption_gui_enabled(json_object(context)):
        frames = facts.get('actual_native_frames')
        require(isinstance(frames, list) and bool(frames), 'Original bounded redemption frames required')
        dates = [json_object(json_object(row)['snapshot']).get('date_raw') for row in frames]
        require(all(type(value) is int for value in dates), 'Actual redemption native dates required')
        initial_date, terminal_date = dates[0], dates[-1]
        require(all(initial_date <= value <= initial_date + 35 * 24 for value in dates), 'Redemption calendar bounds changed')
        require(dates == sorted(dates), 'Redemption calendar moved backwards')
        review = _redemption_gui_review(json_object(context), json_object(compiled),
            json_object(facts['root_phases']), initial_date, terminal_date)
        require(all(facts.get(key) == value for key, value in review.items()), 'Original redemption credit changed')
    if _redemption_existing_enabled(json_object(context)):
        frames = facts.get('actual_native_frames')
        require(isinstance(frames, list) and bool(frames), 'Original existing-window native frames required')
        dates: list[int] = []
        for row in frames:
            date = json_object(json_object(row)['snapshot']).get('date_raw')
            if type(date) is not int or not isinstance(date, int):
                raise ValueError('Actual existing-window native dates required')
            dates.append(date)
        initial_date, terminal_date = dates[0], dates[-1]
        require(dates == sorted(dates) and all(initial_date <= value <= initial_date + 35 * 24 for value in dates),
                'Existing-window natural dates moved backwards or exceeded35')
        review = _redemption_existing_review(json_object(context), json_object(compiled),
            json_object(facts['root_phases']), initial_date, terminal_date)
        require(all(facts.get(key) == value for key, value in review.items()), 'Existing-window local credit changed')
    if _independent_financial_seed_enabled(json_object(context)):
        frames = facts.get('actual_native_frames')
        require(isinstance(frames, list) and bool(frames), 'Actual independent seed frames required')
        first = json_object(json_object(frames[0])['snapshot'])
        require(all(json_object(json_object(row)['snapshot']).get('date_raw') == first.get('date_raw')
                    for row in frames), 'Independent seed must remain on the original date')
        review = _independent_financial_seed_review(json_object(context), json_object(compiled),
            json_object(facts['root_phases']), first)
        require(all(facts.get(key) == value for key, value in review.items()), 'Independent seed facts changed')
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


def _futures_natural14_enabled(context: JsonObject) -> bool:
    from ck3_mod_acceptance_background_types import (
        FUTURES_NATURAL14_CASE_V1, futures_natural14_contract_matches_v1)
    config = object_field(context, 'case_contract')
    selected = context.get('case') == FUTURES_NATURAL14_CASE_V1 or 'futures_natural_liquidity14_contract' in config
    if selected and not futures_natural14_contract_matches_v1(context.get('product'), context.get('case'), config):
        raise ValueError('Exact independent natural futures14 contract required')
    return selected


def _futures_natural14_diagnostic(value: JsonObject) -> None:
    from ck3_mod_acceptance_background_types import (
        continuous14_contract_matches_v1, continuous14_status_sample_v1, continuous14_endpoint_v1)
    require(value.get('schema') == 'ck3-continuous14-diagnostic-result-v2'
        and value.get('state') == 'COMPLETE_DIAGNOSTIC_ONLY'
        and value.get('requested_interval_complete') is True and value.get('elapsed_hours') == 336
        and continuous14_contract_matches_v1(value.get('contract'))
        and all(value.get(k) is False for k in ('financial_daily_coverage_verified',
            'business_pass', 'performance_pass', 'product_release_pass')), 'Original status-only interval incomplete')
    samples = value.get('samples')
    if not isinstance(samples, list) or len(samples) != 14:
        raise ValueError('Fourteen original status samples required')
    for day, item in enumerate(samples):
        sample = json_object(item)
        require(sample == continuous14_status_sample_v1(value.get('before'), sample.get('status'),
            value.get('arm'), day, sample.get('owner_before'), sample.get('owner_after'))
            and sample.get('day') == day + 1, 'Native interval owner/count changed')
    continuous14_endpoint_v1(value.get('before'), value.get('after'), value.get('arm'), json_object(samples[-1])['status'])


def _futures_natural14_review(context: JsonObject, compiled: JsonObject,
                             phases: JsonObject, diagnostic: JsonObject) -> JsonObject:
    require(_futures_natural14_enabled(context) and compiled.get('config') == context['case_contract'],
        'Prepared natural futures case differs')
    _futures_natural14_diagnostic(diagnostic)
    config = object_field(compiled, 'config')
    specs = config['gui_phases']
    if not isinstance(specs, list):
        raise ValueError('Original three phases required')
    require(set(phases) == {str(json_object(s)['id']) for s in specs}, 'Only the three original Root phases are accepted')
    reviews: list[JsonObject] = []
    for item in specs:
        spec = json_object(item); phase = object_field(phases, str(spec['id']))
        assertions = object_field(phase, 'assertions')
        requirements = spec.get('requirements')
        if not isinstance(requirements, list):
            raise ValueError('Actual finite Root requirements required')
        require(phase.get('run_id') == context['run_id'] and phase.get('reviewer') == '/root'
            and all(assertions.get(str(key)) is True for key in requirements), 'Original Root review incomplete')
        evidence = phase.get('evidence')
        if not isinstance(evidence, list) or not evidence:
            raise ValueError('Original phase evidence required')
        for reference in evidence:
            _futures_gui_evidence(reference, phase)
        reviews.append(phase)
    initial = object_field(diagnostic, 'before')['date_raw']
    terminal_date = object_field(diagnostic, 'after')['date_raw']
    if type(initial) is not int or not isinstance(initial, int) or type(terminal_date) is not int or not isinstance(terminal_date, int) or terminal_date != initial + 336:
        raise ValueError('Original14 native calendar interval required')
    archives: list[FilePin] = []
    receipts: list[FilePin] = []
    for phase, date in zip(reviews, (initial, initial, terminal_date)):
        archive_reference = file_pin(phase.get('physical_archive'))
        archives.append(_futures_gui_archive(archive_reference, phase, date))
        receipts.append(archive_reference)
        for key in ('audit', 'raw', 'whole'):
            _futures_gui_evidence(phase.get(key), phase)
    require(len({a['path'] for a in archives}) == 3, 'Three distinct original physical SAVEs required')
    require(reviews[2].get('physical_archives') == receipts,
        'Terminal must retain all and only the three original SAVE receipts in phase order')
    for retained_archive_reference in receipts:
        _futures_gui_evidence(retained_archive_reference, reviews[2])
    orders = object_field(reviews[1], 'sell_orders')
    require(set(orders) == {'short', 'reduce'}, 'Both original same-day order outcomes must be explicit')
    cells = object_field(reviews[2], 'futures_natural_liquidity14')
    require(set(cells) == {'short', 'reduce'}, 'Only SHORT and reduce cells are in scope')
    placed_ids: set[str] = set()
    observed: list[str] = []
    missing: list[str] = []
    for name in ('short', 'reduce'):
        order = object_field(orders, name)
        status = order.get('status')
        require(status in ('PLACED', 'NOT_PLACED'), 'Order admission never implies fill')
        if status == 'PLACED':
            require(order.get('side') == 'SELL' and type(order.get('lots')) is int and order.get('lots') == 1
                and type(order.get('leverage')) is int and order.get('leverage') == (2 if name == 'short' else 1),
                'Only original SHORT2x1 and old LONG reduce1 SELL tickets are allowed')
            require(order.get('close_position_id') == (None if name == 'short' else '150'),
                'Close marker belongs only to original LONG150 reduction')
            for key in ('order_native_id', 'order_id', 'account_native_id', 'contract_native_id'):
                val = order.get(key)
                require(isinstance(val, str) and re.fullmatch(r'[1-9][0-9]{0,19}', val) is not None,
                    'Actual order/account/contract identities must be explicit exact decimal strings')
            require(order['order_native_id'] not in placed_ids, 'Two operations cannot reuse one order identity')
            placed_ids.add(str(order['order_native_id']))
            actions = order.get('gui_actions')
            if not isinstance(actions, list) or not 1 <= len(actions) <= 64:
                raise ValueError('Original normal GUI receipts required')
            for item in actions:
                action = json_object(item)
                require(set(action) == {'query', 'activation'}, 'Each action must retain its own fresh query')
                for reference in action.values():
                    _futures_gui_evidence(reference, reviews[1])
            _futures_gui_evidence(order.get('reservation_reconciliation'), reviews[1])
        else:
            require(set(order) == {'status', 'reason', 'evidence'} and isinstance(order['reason'], str) and order['reason'],
                'Unplaced operation must keep its actual reason')
            unplaced_evidence = order.get('evidence')
            if not isinstance(unplaced_evidence, list):
                raise ValueError('Unplaced evidence must be explicit')
            for reference in unplaced_evidence:
                _futures_gui_evidence(reference, reviews[1])
        cell = object_field(cells, name)
        if cell.get('status') == 'NOT_OBSERVED':
            require(set(cell) == {'status', 'reason', 'evidence'} and isinstance(cell.get('reason'), str) and cell['reason'],
                'No actual fill or qualification remains NOT_OBSERVED')
            missing_evidence = cell.get('evidence')
            if not isinstance(missing_evidence, list):
                raise ValueError('Actual unobserved evidence must be an explicit list')
            for reference in missing_evidence:
                _futures_gui_evidence(reference, reviews[2])
            missing.append(name)
            continue
        require(status == 'PLACED' and cell.get('status') == 'OBSERVED' and set(cell) == {
            'status', 'order_native_id', 'order_id', 'before_archive', 'order_archive', 'after_archive',
            'assertions', 'order_position_reconciliation', 'margin_cash_fee_counterparty_reconciliation'},
            'Only a source-bound real filled original order may be observed')
        require(cell['order_native_id'] == order['order_native_id'] and cell['order_id'] == order['order_id']
            and cell['before_archive'] == receipts[0] and cell['order_archive'] == receipts[1] and cell['after_archive'] == receipts[2],
            'A different order or dates-only endpoint claim cannot substitute for this operation')
        required = {'actual_original_order_filled_quantity_from_source_and_terminal_records',
            'actual_position_and_permanent_ids_and_selected_side_bound',
            'actual_independent_counterparty_account_holder_and_beneficiary_not_self',
            'actual_paired_collateral_fees_cash_and_unrelated_assets_reconciled',
            'actual_short_side_leverage2' if name == 'short' else 'actual_old_long150_exposure_reduced_by_original_reduce_order'}
        assertions = object_field(cell, 'assertions')
        require(set(assertions) == required and all(v is True for v in assertions.values()),
            'Dates or matching amounts alone never prove a real fill/reduction')
        for key in ('order_position_reconciliation', 'margin_cash_fee_counterparty_reconciliation'):
            _futures_gui_evidence(cell[key], reviews[2])
        observed.append(name)
    placed = [object_field(orders, n) for n in ('short', 'reduce') if object_field(orders, n).get('status') == 'PLACED']
    require(len({str(o['account_native_id']) for o in placed}) <= 1 and len({str(o['contract_native_id']) for o in placed}) <= 1,
        'Both SELLs must be this same account and contract, never opposite player accounts')
    return json_object({'futures_natural_liquidity14': cells, 'sell_orders': orders,
        'physical_archives': receipts, 'retained_physical_checkpoint_count': 3,
        'observed_cells': observed, 'not_observed_cells': missing, 'natural_days_advanced': 14,
        'financial_daily_coverage_verified': False, 'business_pass': False, 'performance_pass': False,
        'derivatives_acceptance_pass': False, 'product_release_pass': False,
        'result_boundary': 'NATURAL_SHORT_REDUCE_LOCAL_OBSERVATIONS_ONLY'})


def _futures_natural14_run(context: JsonObject, client: CaseClient) -> JsonObject:
    context = json_object(resolve_post_start(context))
    require(_futures_natural14_enabled(context), 'Independent natural futures14 case required')
    compiled, binding = compiled_contract(context)
    config = object_field(compiled, 'config')
    require(config == context['case_contract'], 'Prepared natural futures case differs')
    specs = config['gui_phases']; before = json_object(client.snapshot())
    if not isinstance(specs, list) or len(specs) != 3:
        raise ValueError('Original three phases required')
    phases: JsonObject = {}
    for item in specs[:2]:
        spec = json_object(item)
        current = json_object(client.snapshot())
        require(current['date_raw'] == before['date_raw'], 'Both ordinary SELL operations stay on day0')
        phases[str(spec['id'])] = root_phase(client, context, spec['id'], spec['requirements'], current, compiled)
    row = client.continuous14_diagnostic(); value = json_object(row['result'])
    require(object_field(value, 'before')['date_raw'] == before['date_raw'], 'Clock cannot start after unobserved days')
    spec = json_object(specs[2])
    phases[str(spec['id'])] = root_phase(client, context, spec['id'], spec['requirements'], object_field(value, 'after'), compiled)
    facts = json_object({'schema': 'ck3-futures-natural-liquidity14-result-v1', 'run_id': context['run_id'],
        'product': context['product'], 'case': context['case'], 'compiled_contract': binding,
        'diagnostic_result': value, 'root_phases': phases, 'case_contract_qualified': True,
        'gui_contract_qualified': True, 'business_contract_applicable': True,
        **_futures_natural14_review(context, compiled, json_object(phases), value)})
    client.checkpoint('futures-natural-liquidity14-result', facts)
    return facts


def _futures_natural14_verify(context: JsonObject) -> JsonObject:
    context = json_object(resolve_post_start(context))
    require(_futures_natural14_enabled(context), 'Independent natural futures14 case required')
    path = Path(text_field(context, 'output')) / 'futures-natural-liquidity14-result.json'
    if not path.is_file():
        return json_object({'status': 'PARTIAL_NOT_COMPLETED', 'case_contract_qualified': False,
            'gui_contract_qualified': False, 'business_contract_applicable': True,
            'business_pass': False, 'performance_pass': False, 'product_release_pass': False})
    facts = json_object(read_json(path)); compiled, binding = compiled_contract(context)
    require(facts.get('schema') == 'ck3-futures-natural-liquidity14-result-v1'
        and facts.get('run_id') == context['run_id'] and facts.get('case') == context['case']
        and facts.get('product') == context['product'] and facts.get('compiled_contract') == binding,
        'Natural futures original result crossed run/case/source')
    review = _futures_natural14_review(context, compiled, object_field(facts, 'root_phases'), object_field(facts, 'diagnostic_result'))
    require(all(facts.get(k) == v for k, v in review.items()), 'Retained result differs from actual original evidence')
    return json_object({**facts, **review, 'verification_scope': 'natural_short_reduce_local_observations_only'})


def _continuous14_enabled(context: JsonObject) -> bool:
    from ck3_mod_acceptance_background_types import continuous14_contract_matches_v1
    config = object_field(context, 'case_contract')
    if context.get('case') == 'futures-natural-liquidity14':
        _futures_natural14_enabled(context)
        return False
    selected = context.get('case') == 'clock-cadence-continuous14' or config.get('clock_purpose') == 'continuous14_diagnostic'
    if selected and (context.get('product') != 'financial-markets' or context.get('case') != 'clock-cadence-continuous14'
            or config.get('product') != context['product'] or config.get('case_id') != context['case']
            or config.get('clock_purpose') != 'continuous14_diagnostic'
            or config.get('acceptance_scope') != 'clock_cadence_diagnostic_only'
            or config.get('maximum_natural_days') != 14 or config.get('startup_mode') != 'saved_campaign'
            or not continuous14_contract_matches_v1(config.get('continuous14_contract'))
            or config.get('business_contract_applicable') is not False
            or config.get('whole_product_release_pass') is not False):
        raise ValueError('Exact independent continuous14 diagnostic contract required')
    return selected


def _continuous14_run(context: JsonObject, client: CaseClient) -> JsonObject:
    require(_continuous14_enabled(context), 'Independent continuous14 case required')
    context = resolve_post_start(context)
    compiled, binding = compiled_contract(context)
    config = compiled['config']
    require(config == context['case_contract'], 'Prepared continuous14 contract differs')
    before = client.snapshot()
    phases = config['gui_phases']
    require([phase['at_day'] for phase in phases] == [0, 14], 'Continuous14 permits baseline/terminal SAVE phases only')
    baseline = root_phase(client, context, phases[0]['id'], phases[0]['requirements'], before, compiled)
    # Baseline phase has independently saved/read the real exchange. There is no observer ARM.
    row = client.continuous14_diagnostic()
    value = json_object(row['result'])
    require(object_field(value, 'before')['date_raw'] == before['date_raw'], 'Actual experiment start moved after baseline SAVE')
    terminal = root_phase(client, context, phases[1]['id'], phases[1]['requirements'], object_field(value, 'after'), compiled)
    facts: JsonObject = {'schema': 'ck3-continuous14-case-result-v2', 'run_id': context['run_id'],
        'product': context['product'], 'case': context['case'], 'compiled_contract': binding,
        'diagnostic_result': value, 'financial_daily_coverage_verified': False, 'root_phases': {phases[0]['id']: baseline, phases[1]['id']: terminal},
        'case_contract_qualified': True, 'gui_contract_qualified': True,
        'result_boundary': 'CONTINUOUS14_DIAGNOSTIC_ONLY', 'business_contract_applicable': False,
        'business_pass': False, 'performance_pass': False, 'product_release_pass': False}
    client.checkpoint('continuous14-case-result', facts)
    return facts


def _continuous14_verify(context: JsonObject) -> JsonObject:
    require(_continuous14_enabled(context), 'Independent continuous14 case required')
    path = Path(text_field(context, 'output')) / 'continuous14-case-result.json'
    if not path.is_file():
        return {'case_contract_qualified': False, 'gui_contract_qualified': False, 'status': 'NOT_COMPLETED',
            'business_contract_applicable': False, 'business_pass': False, 'performance_pass': False,
            'product_release_pass': False}
    facts = json_object(read_json(path))
    compiled, binding = compiled_contract(context)
    require(facts.get('run_id') == context['run_id'] and facts.get('product') == context['product']
            and facts.get('case') == context['case'] and facts.get('compiled_contract') == binding,
            'Continuous14 result crossed its pinned run/product/case')
    from ck3_mod_acceptance_background_types import (
        continuous14_contract_matches_v1, continuous14_status_sample_v1, continuous14_endpoint_v1)
    diagnostic = object_field(facts, 'diagnostic_result')
    require(continuous14_contract_matches_v1(diagnostic.get('contract'))
            and diagnostic.get('requested_interval_complete') is True
            and diagnostic.get('schema') == 'ck3-continuous14-diagnostic-result-v2'
            and diagnostic.get('state') == 'COMPLETE_DIAGNOSTIC_ONLY'
            and diagnostic.get('financial_daily_coverage_verified') is False, 'Continuous14 diagnostic incomplete')
    samples = diagnostic.get('samples')
    if not isinstance(samples, list) or len(samples) != 14:
        raise ValueError('Continuous14 has missing actual samples')
    for day, item in enumerate(samples):
        sample = json_object(item)
        require(sample == continuous14_status_sample_v1(diagnostic.get('before'), sample.get('status'),
            diagnostic.get('arm'), day, sample.get('owner_before'), sample.get('owner_after'))
            and sample.get('day') == day + 1, 'Continuous14 actual native status sample differs')
    continuous14_endpoint_v1(diagnostic.get('before'), diagnostic.get('after'),
        diagnostic.get('arm'), json_object(samples[-1])['status'])
    responses = object_field(facts, 'root_phases')
    require(set(responses) == {phase['id'] for phase in compiled['config']['gui_phases']},
            'Both original physical SAVE/readback phases required')
    for phase in compiled['config']['gui_phases']:
        response = object_field(responses, phase['id'])
        require(response.get('run_id') == context['run_id'] and response.get('reviewer') == '/root'
                and all(object_field(response, 'assertions').get(key) is True for key in phase['requirements'])
                and response.get('evidence'), 'Continuous14 original Root SAVE/readback review incomplete')
        evidence = response.get('evidence')
        if not isinstance(evidence, list) or not evidence:
            raise ValueError('Continuous14 original Root SAVE/readback review incomplete')
        for item in evidence:
            evidence_pin = json_object(item)
            require(pin(text_field(evidence_pin, 'path')) == evidence_pin,
                    'Continuous14 original physical evidence changed')
    return {**facts, 'verification_scope': 'clock_cadence_diagnostic_only',
        'financial_daily_coverage_verified': False, 'business_pass': False,
        'performance_pass': False, 'product_release_pass': False}


def prepare_case(context: JsonObject) -> JsonObject:
    context = json_object(context)
    if object_field(context, 'case_contract').get('acceptance_scope') == 'ordinary_promotion':
        return prepare_ordinary_capture(context)
    if _sr_enabled(context):
        return _sr_prepare(context)
    return json_object(_prepare_fixture_case(context))


def run_case(context: JsonObject, client: CaseClient) -> JsonObject:
    context = json_object(context)
    if _futures_natural14_enabled(context):
        return _futures_natural14_run(context, client)
    if _continuous14_enabled(context):
        return _continuous14_run(context, client)
    if object_field(context, 'case_contract').get('acceptance_scope') == 'ordinary_promotion':
        return run_ordinary_capture(context, client)
    if _sr_enabled(context):
        return _sr_run(context, client)
    return json_object(_run_fixture_case(context, client))


def verify_case(context: JsonObject) -> JsonObject:
    context = json_object(context)
    if _futures_natural14_enabled(context):
        return _futures_natural14_verify(context)
    if _continuous14_enabled(context):
        return _continuous14_verify(context)
    if object_field(context, 'case_contract').get('acceptance_scope') == 'ordinary_promotion':
        return verify_ordinary_capture(context)
    if _sr_enabled(context):
        return _sr_verify(context)
    return json_object(_verify_fixture_case(context))
