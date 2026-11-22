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


def _saved_fixture_startup(context: JsonObject, profile: JsonObject, *,
                           issuer_refund_toast: bool = False) -> JsonObject:
    """Bind saved input; the sole caller passes its already validated case flag."""
    if type(issuer_refund_toast) is not bool:
        raise ValueError('Exact internal issuer refund/toast startup flag required')
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
        if field == 'player_id' and issuer_refund_toast:
            if type(value) is not int:
                raise ValueError('Issuer refund/toast startup requires an exact signed32 CharacterID')
            _irt_character(str(value))
        elif type(value) is not int or not isinstance(value, int) or not 0 < value < 2**31:
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
    coin_campaign = _coin_campaign_enabled(json_object(context))
    if coin_campaign:
        _coin_campaign_inputs(json_object(context))
    issuer_refund_toast = _issuer_refund_toast_enabled(json_object(context))
    if issuer_refund_toast:
        _irt_inputs(json_object(context))
    news_delivery_daily = _news_delivery_daily_enabled(json_object(context))
    if news_delivery_daily:
        _ndd_inputs(json_object(context))
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
        if coin_campaign:
            from ck3_mod_acceptance_background_types import CONTINUOUS14_PASSIVE_STORY_TYPES_V1
            passive = fixture / 'common/story_cycles/xfma_coin_campaign_passive.txt'
            passive.parent.mkdir(parents=True)
            passive.write_text(''.join(name + ' = { visible = no }\n'
                for name in CONTINUOUS14_PASSIVE_STORY_TYPES_V1), encoding='utf-8-sig')
        if issuer_refund_toast:
            from ck3_mod_acceptance_background_types import CONTINUOUS14_PASSIVE_STORY_TYPES_V1
            passive = fixture / 'common/story_cycles/xfma_issuer_refund_toast_passive.txt'
            passive.parent.mkdir(parents=True)
            passive.write_text(''.join(name + ' = { visible = no }\n'
                for name in CONTINUOUS14_PASSIVE_STORY_TYPES_V1), encoding='utf-8-sig')
        if news_delivery_daily:
            from ck3_mod_acceptance_background_types import CONTINUOUS14_PASSIVE_STORY_TYPES_V1
            passive = fixture / 'common/story_cycles/xfma_news_delivery_daily_passive.txt'
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
    require(required or config['acceptance_scope'] == 'static_and_basicload' or continuous14 or liquidity14 or futures_gui or redemption_gui or redemption_existing or independent_seed or coin_campaign or issuer_refund_toast or news_delivery_daily,
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
        startup = _saved_fixture_startup(startup_context, json_object(profile),
                                         issuer_refund_toast=issuer_refund_toast)
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
                    pending_interaction_policy: PendingInteractionPolicy = "stop_at_boundary",
                    current_toast_queries: bool = False) -> dict[str, object]: ...
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
    if policy.get('case_id') == ISSUER_REFUND_TOAST_CASE:
        return json_object(client.advance_day(days=1, timeout=timeout, allow_event_boundary=True,
                           allow_actor_change=False, current_toast_queries=True))
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


COIN_CAMPAIGN_CASE = 'coin-campaign-gui'
COIN_CAMPAIGN_SCOPE = 'actual_existing_entity_bound_coin_charter_promotion_and_two_coin_same_day_spot_only'
COIN_CAMPAIGN_CELLS = ('house_or_dynasty_binding_readback', 'title_binding_readback',
    'paid_A_charter_promotion', 'two_coin_same_day_buy_sell_isolation')
COIN_CAMPAIGN_CONTRACT = {
    'schema': 'ck3-coin-campaign-gui-contract-v1', 'physical_save_maximum': 3,
    'physical_save_max_bytes': 268435456, 'observer_arm': False,
    'financial_daily_coverage_verified': False, 'manipulation_causal_success_pass': False,
    'global_news_delivery_pass': False, 'all_AI_eligibility_or_new_issuance_pass': False,
    'performance_pass': False, 'whole_product_release_pass': False,
}
COIN_CAMPAIGN_PHASES = (
    ('bind-current-campaign-baseline', (
        'actual_minimized_non_topmost_no_foreground_source_and_case_scope_bound',
        'actual_latest_scenario_source_and_one_new_same_date_baseline_SAVE_match_without_replay',
        'actual_PRIMARY_two_distinct_coins_typed_entity_refs_and_real_independent_funded_depth_are_pinned',
        'actual_prospective_three_SAVE_budget_original_deadline_and_normal_exit_reserve_remain_valid')),
    ('charter-promotion-two-coin-orders-and-reconciliation', (
        'actual_observed_A_promotion_uses_normal_frozen_charter_once_and_100cent_PRIMARY_fee_or_is_explicitly_NOT_OBSERVED',
        'actual_each_physical_SAVE_and_promotion_audience_unknowns_retained_without_delivery_or_forced_price_claims',
        'actual_new_A_and_B_buy_and_sell_order_results_prices_lots_beneficiaries_fees_and_remaining_obligations_are_separately_reconciled_or_each_missing_cell_NOT_OBSERVED',
        'actual_terminal_physical_SAVE_retains_all_old_obligations_and_independent_cash_coin_reserved_fee_graph',
        'actual_original_UNKNOWN_or_failures_are_not_replayed_or_reclassified_and_normal_close_is_independently_required')),
)




ISSUER_REFUND_TOAST_CASE = 'issuer-refund-toast'
ISSUER_REFUND_TOAST_SCOPE = 'normal_paid_micro_company_subscription_refund_and_local_native_toast_observed_cells'
ISSUER_REFUND_TOAST_CONTRACT: JsonObject = json_object({"schema":"ck3-issuer-refund-toast-contract-v1","physical_save_maximum":3,"physical_save_max_bytes":268435456,"entity_type":6,"registration_fee_cents":100,"subscription_cents":100,"readonly_toast_queries":2,"day_timeout_seconds":300,"normal_close_reserve_seconds":180,"observer_arm":False,"direct_business_setters":False,"forced_AI_or_death":False,"all_human_delivery_pass":False,"financial_daily_coverage_verified":False,"whole_product_release_pass":False})
ISSUER_REFUND_TOAST_PHASES: tuple[tuple[str, int, tuple[str, ...]], ...] = (
    ("bind-issuer-refund-baseline", 0, ("actual_minimized_latest_source_and_current_actor_bound", "actual_new_D0_baseline_archive_audit_raw_whole_and_PRIMARY_or_NOT_OBSERVED", "actual_normal_issuer_eligibility_checked_without_business_setters", "actual_three_checkpoint_budget_deadline_and_normal_exit_reserve_valid",)),
    ("normal-issuer-subscribe-abort", 0, ("actual_fresh_normal_micro_company_registration_subscription_abort_or_NOT_OBSERVED", "actual_D0_fee_reservation_refund_and_old_obligations_reconciled_or_NOT_OBSERVED", "actual_original_actions_failures_and_all_checkpoints_retained_without_replay", "actual_new_coin_and_subscription_identities_absent_from_complete_baseline",)),
    ("one-day-native-toast-and-source-join", 1, ("actual_one_original_public_day_attempt_then_two_readonly_toast_queries_or_boundary_retained", "actual_postquery_physical_source_named_identities_and_completed_frame_join_reviewed", "actual_missing_new_kind10_delivery_is_NOT_OBSERVED_and_normal_close_required",)),
)

def _issuer_refund_toast_enabled(context: JsonObject) -> bool:
    config = object_field(context, 'case_contract')
    if context.get('case') != ISSUER_REFUND_TOAST_CASE and 'issuer_refund_toast_contract' not in config:
        return False
    from ck3_mod_acceptance_background_types import CONTINUOUS14_PASSIVE_STORY_TYPES_V1
    contract = object_field(config, 'issuer_refund_toast_contract')
    integers = {k for k, v in ISSUER_REFUND_TOAST_CONTRACT.items() if type(v) is int}
    if (context.get('product') != 'financial-markets' or context.get('case') != ISSUER_REFUND_TOAST_CASE
            or config.get('product') != context['product'] or config.get('case_id') != context['case']
            or config.get('schema') != 'ck3-mod-acceptance-product-case-v1'
            or config.get('execution_purpose') != 'product_acceptance'
            or config.get('acceptance_scope') != ISSUER_REFUND_TOAST_SCOPE
            or config.get('startup_mode') != 'saved_campaign' or config.get('allow_actor_change') is not False
            or config.get('product_loading', 'present') != 'present'
            or type(config.get('maximum_natural_days')) is not int or config.get('maximum_natural_days') != 1
            or config.get('pending_interaction_policy') != 'stop_at_boundary'
            or config.get('business_contract_applicable') is not True or config.get('whole_product_release_pass') is not False
            or contract != ISSUER_REFUND_TOAST_CONTRACT
            or any(type(contract.get(k)) is not int for k in integers)
            or any(contract.get(k) is not False for k, v in ISSUER_REFUND_TOAST_CONTRACT.items() if v is False)
            or config.get('passive_story_types') != list(CONTINUOUS14_PASSIVE_STORY_TYPES_V1)
            or any(k in config for k in ('fixture_source', 'fixture_emitter', 'marker_inventory', 'clock_purpose',
                                         'continuous14_contract', 'frontend_rules'))):
        raise ValueError('Exact one-day normal issuer refund/toast contract required')
    phases = config.get('gui_phases')
    if not isinstance(phases, list) or len(phases) != 3:
        raise ValueError('Three original issuer refund/toast Root phases required')
    for row, (name, day, requirements) in zip(phases, ISSUER_REFUND_TOAST_PHASES):
        value = json_object(row)
        if (set(value) != {'id', 'at_day', 'requirements'} or value.get('id') != name
                or type(value.get('at_day')) is not int or value.get('at_day') != day
                or value.get('requirements') != list(requirements)):
            raise ValueError('Original [0,0,1] issuer refund/toast phases changed')
    return True


def issuer_refund_toast_plan_matches(context: object, steps: object, name: object, timeout: object) -> bool:
    """Only this exact case may compose its existing day plus two readonly rows."""
    selected = json_object(context)
    if not _issuer_refund_toast_enabled(selected):
        return False
    if (not isinstance(name, str) or re.fullmatch(r'case-natural-day-[0-9]{4,}', name) is None
            or type(timeout) is not int or timeout != 300
            or not isinstance(steps, list) or len(steps) != 3):
        return False
    from ck3_mod_acceptance_native_day import STEP
    first = json_object(steps[0])
    normal = (type(first.get('days')) is int and type(first.get('timeout')) is int
        and first == {'id': name, 'kind': 'advance_day', 'days': 1,
                      'timeout': timeout, 'allow_event_boundary': True})
    args = first.get('args')
    revision = args.get('expected_revision') if isinstance(args, dict) else None
    native = (set(first) == {'id', 'tool', 'args', 'fresh_revision'} and first.get('id') == name
        and first.get('tool') == 'ck3_execute_step' and first.get('fresh_revision') is False
        and isinstance(args, dict) and set(args) == {'step', 'expected_revision'}
        and args.get('step') == STEP and type(revision) is int and isinstance(revision, int)
        and revision >= 0)
    expected = [{'id': name + '-toast0' + str(i), 'kind': 'tool',
                 'tool': 'ck3_query_current_interface_toast_v1', 'args': {}} for i in (1, 2)]
    return (normal or native) and steps[1:] == expected


def _irt_inputs(context: JsonObject) -> JsonObject:
    if not _issuer_refund_toast_enabled(context):
        raise ValueError('Selected issuer refund/toast case required')
    inputs = object_field(context, 'case_inputs')
    allowed = {'product_dir', 'plain_configuration', 'post_start', 'issuer_refund_toast'}
    if (set(inputs) not in (allowed, allowed | {'steam_manifest'})
            or context.get('execution_mode') == 'gui_only' or context.get('gui_saved_input') is not None):
        raise ValueError('Only original saved source and normal product inputs allowed')
    binding = object_field(inputs, 'issuer_refund_toast')
    if (set(binding) != {'source_archive', 'scenario_id'} or not isinstance(binding.get('scenario_id'), str)
            or re.fullmatch(r'[a-z][a-z0-9_-]{2,63}', str(binding['scenario_id'])) is None):
        raise ValueError('Explicit current source/scenario required; no predicted new identities')
    ref = file_pin(binding.get('source_archive'))
    if ref['bytes'] > 1024 * 1024:
        raise ValueError('Bounded original source archive metadata required')
    checked_capture_pin(ref)
    source = json_object(read_json(ref['path'])); save = file_pin(source.get('archive'))
    startup = object_field(context, 'saved_campaign')
    actor_id = startup.get('player_id')
    if (source.get('schema') != 'ck3-financial-checkpoint-archive-v1'
            or source.get('exact_copy') is not True or source.get('same_file') is not False
            or type(source.get('date_raw')) is not int or type(startup.get('date_raw')) is not int
            or source['date_raw'] != startup['date_raw'] or startup.get('save') != save['path']
            or type(startup.get('bytes')) is not int or startup['bytes'] != save['bytes']
            or startup.get('sha256') != save['sha256']
            or type(actor_id) is not int
            or not isinstance(source.get('machine_id'), str)):
        raise ValueError('Latest archive must exactly bind this public saved startup')
    _irt_character(str(actor_id))
    return binding


def _irt_number(value: object, *, positive: bool = False) -> int:
    return int(_coin_campaign_uint(value, positive=positive))


def _irt_character(value: object) -> str:
    """Keep the SDK/Java signed32 CharacterID bits; -1 is the invalid sentinel."""
    if (not isinstance(value, str) or re.fullmatch(r'0|-?[1-9][0-9]{0,9}', value) is None
            or not -2147483648 <= int(value) <= 2147483647 or value == '-1'):
        raise ValueError('Canonical signed32 CharacterID other than -1 required')
    return value


def _irt_cell(value: object, phase: JsonObject) -> JsonObject:
    cell = json_object(value)
    if cell.get('status') == 'NOT_OBSERVED':
        evidence = cell.get('evidence')
        if (set(cell) != {'status', 'reason', 'evidence'} or not isinstance(cell.get('reason'), str)
                or not cell['reason'] or not isinstance(evidence, list)):
            raise ValueError('Unobserved eligibility/refund/toast needs exact status/reason/evidence')
        for ref in evidence:
            _futures_gui_evidence(ref, phase)
    elif cell.get('status') != 'OBSERVED':
        raise ValueError('Only actual OBSERVED or explicit NOT_OBSERVED cells allowed')
    return cell


def _irt_phase(context: JsonObject, phases: JsonObject, index: int) -> JsonObject:
    phase = object_field(phases, ISSUER_REFUND_TOAST_PHASES[index][0])
    _coin_campaign_phase(context, phase, tuple(ISSUER_REFUND_TOAST_PHASES[index][2]))
    return phase


def _irt_baseline(context: JsonObject, phases: JsonObject, date: int) -> JsonObject:
    binding = _irt_inputs(context)
    if object_field(context, 'saved_campaign').get('date_raw') != date:
        raise ValueError('Initial issuer date differs from current source')
    phase = _irt_phase(context, phases, 0)
    if phase.get('source_archive') != binding['source_archive']:
        raise ValueError('Baseline cannot replace the admitted source archive')
    _futures_gui_evidence(phase['source_archive'], phase)
    _futures_gui_archive(phase.get('baseline_archive'), phase, date)
    for k in ('baseline_audit', 'baseline_raw', 'baseline_whole'):
        _futures_gui_evidence(phase.get(k), phase)
    cell = _irt_cell(phase.get('eligibility'), phase)
    if cell['status'] == 'NOT_OBSERVED':
        return phase
    if set(cell) != {'status', 'PRIMARY', 'checks', 'evidence'}:
        raise ValueError('Exact normal eligibility and legal PRIMARY facts required')
    account = object_field(cell, 'PRIMARY')
    if (set(account) != {'native_id', 'permanent_id', 'holder_character_id', 'free_cents', 'reserved_cents'}
            or _irt_character(account.get('holder_character_id')) != _irt_character(str(object_field(context, 'saved_campaign')['player_id']))
            or _irt_number(account.get('native_id'), positive=True) >= 4294967295
            or _irt_number(account.get('permanent_id'), positive=True) <= 0
            or _irt_number(account.get('free_cents')) < 200):
        raise ValueError('Known same-holder private PRIMARY with at least200c required; no forced topup')
    _irt_number(account.get('reserved_cents'))
    checks = object_field(cell, 'checks')
    evidence = cell.get('evidence')
    if (set(checks) != {'adult_living_human', 'PRIMARY_legal_unfrozen', 'normal_company_micro_registration_enabled',
                        'no_pending_offer_or_issue_cooldown', 'no_business_setters'}
            or any(v is not True for v in checks.values()) or not isinstance(evidence, list) or not evidence):
        raise ValueError('Actual normal eligibility must be independently reviewed')
    for ref in evidence:
        _futures_gui_evidence(ref, phase)
    return phase


def _irt_refund(context: JsonObject, phases: JsonObject, date: int) -> JsonObject:
    baseline = _irt_baseline(context, phases, date); phase = _irt_phase(context, phases, 1)
    cell = _irt_cell(phase.get('refund'), phase)
    if cell['status'] == 'NOT_OBSERVED':
        return cell
    if object_field(baseline, 'eligibility').get('status') != 'OBSERVED':
        raise ValueError('Unobserved eligibility cannot become an actual paid refund')
    if set(cell) != {'status', 'before_archive', 'after_archive', 'gui_actions',
                     'facts', 'audit', 'raw', 'whole', 'reconciliation'}:
        raise ValueError('Exact actual D0 refund cell required')
    if cell.get('before_archive') != baseline.get('baseline_archive'):
        raise ValueError('Refund must start at this run baseline')
    before = _futures_gui_archive(cell['before_archive'], phase, date)
    after = _futures_gui_archive(cell['after_archive'], phase, date)
    if before['path'] == after['path'] or before['sha256'] == after['sha256']:
        raise ValueError('Distinct physical D0 before/refund endpoints required')
    actions = object_field(cell, 'gui_actions')
    if set(actions) != {'registration', 'subscription', 'abort'}:
        raise ValueError('Only the three normal issuer actions may supply this refund')
    for key, count in (('registration', 2), ('subscription', 1), ('abort', 2)):
        actual_actions = actions[key]
        if not isinstance(actual_actions, list) or len(actual_actions) != count:
            raise ValueError('Actual query/button and current event/confirmation pairs required')
        _coin_campaign_actions(actual_actions, phase)
    for key in ('audit', 'raw', 'whole', 'reconciliation'):
        _futures_gui_evidence(cell[key], phase)
    facts = object_field(cell, 'facts')
    if set(facts) != {'coin', 'issue_receipt', 'subscription', 'before', 'after'}:
        raise ValueError('Raw-backed actual coin/receipt/reservation and ledger fields required')
    account = object_field(object_field(baseline, 'eligibility'), 'PRIMARY')
    coin, issue = object_field(facts, 'coin'), object_field(facts, 'issue_receipt')
    sub, first, last = (object_field(facts, k) for k in ('subscription', 'before', 'after'))
    coin_keys = {'native_id', 'xfm_coin_id', 'xfm_entity_type', 'xfm_controller', 'xfm_listing_state',
                 'xfm_trading_open', 'xfm_refund_news_recorded', 'xfm_news_kind', 'xfm_news_actor',
                 'xfm_news_fact_counter', 'xfm_news_last_fact', 'xfm_actual_raised_cents', 'xfm_external_raised_cents'}
    issue_keys = {'xfm_issue_receipt_version', 'xfm_issue_receipt_coin_id', 'xfm_issue_receipt_actor',
                  'xfm_issue_receipt_payer', 'xfm_issue_receipt_payer_id', 'xfm_issue_receipt_day',
                  'xfm_issue_receipt_is_ai', 'xfm_issue_receipt_fee_cents', 'xfm_issue_receipt_free_before',
                  'xfm_issue_receipt_free_pre_fee', 'xfm_issue_receipt_free_after', 'xfm_issue_receipt_reserved_before',
                  'xfm_issue_receipt_reserved_after', 'xfm_issue_receipt_fees_before', 'xfm_issue_receipt_fees_after',
                  'xfm_issue_receipt_topup_cents'}
    sub_keys = {'native_id', 'xfm_reservation_id', 'xfm_account', 'xfm_subscription_coin',
                'xfm_subscription_buyer', 'xfm_subscription_paid_cents', 'xfm_subscription_units',
                'xfm_subscription_state', 'xfm_status', 'xfm_remaining_cents'}
    ledger_keys = {'free_cents', 'reserved_cents', 'exchange_fee_cents', 'financial_day'}
    if (set(coin) != coin_keys or set(issue) != issue_keys or set(sub) != sub_keys
            or set(first) != ledger_keys or set(last) != ledger_keys):
        raise ValueError('Missing/unknown raw financial fields cannot be zero/defaulted')
    character_fields = {'xfm_controller', 'xfm_news_actor', 'xfm_issue_receipt_actor', 'xfm_subscription_buyer'}
    for values in (coin, issue, sub, first, last):
        for field, value in values.items():
            if field in character_fields:
                _irt_character(value)
            else:
                _irt_number(value)
    actor = account['holder_character_id']
    if (_irt_number(coin['native_id'], positive=True) >= 4294967295 or _irt_number(coin['xfm_coin_id'], positive=True) <= 0
            or coin['xfm_controller'] != actor or coin['xfm_news_actor'] != actor
            or any(_irt_number(coin[k]) != v for k, v in
                   {'xfm_entity_type': 6, 'xfm_listing_state': 6, 'xfm_trading_open': 0,
                    'xfm_refund_news_recorded': 1, 'xfm_news_kind': 10,
                    'xfm_actual_raised_cents': 100, 'xfm_external_raised_cents': 0}.items())
            or _irt_number(coin['xfm_news_fact_counter'], positive=True) != _irt_number(coin['xfm_news_last_fact'], positive=True)):
        raise ValueError('Actual new company refund-close and first kind10 source required')
    f, r, e = (_irt_number(first[k]) for k in ('free_cents', 'reserved_cents', 'exchange_fee_cents'))
    if (first['free_cents'] != account['free_cents'] or first['reserved_cents'] != account['reserved_cents']
            or first['financial_day'] != last['financial_day']
            or _irt_number(last['free_cents']) != f - 100 or _irt_number(last['reserved_cents']) != r
            or _irt_number(last['exchange_fee_cents']) != e + 100):
        raise ValueError('Actual fee100 plus subscription/refund100 must reconcile at unchanged D0')
    expected_issue = {'xfm_issue_receipt_version': '1', 'xfm_issue_receipt_coin_id': coin['xfm_coin_id'],
        'xfm_issue_receipt_actor': actor, 'xfm_issue_receipt_payer': account['native_id'],
        'xfm_issue_receipt_payer_id': account['permanent_id'], 'xfm_issue_receipt_day': first['financial_day'],
        'xfm_issue_receipt_is_ai': '0', 'xfm_issue_receipt_fee_cents': '100',
        'xfm_issue_receipt_free_before': str(f), 'xfm_issue_receipt_free_pre_fee': str(f),
        'xfm_issue_receipt_free_after': str(f - 100), 'xfm_issue_receipt_reserved_before': str(r),
        'xfm_issue_receipt_reserved_after': str(r), 'xfm_issue_receipt_fees_before': str(e),
        'xfm_issue_receipt_fees_after': str(e + 100), 'xfm_issue_receipt_topup_cents': '0'}
    if issue != expected_issue:
        raise ValueError('Version1 actual payer/fee debit-credit receipt required; nominal paid is insufficient')
    expected_sub = {'xfm_account': account['native_id'], 'xfm_subscription_coin': coin['native_id'],
        'xfm_subscription_buyer': actor, 'xfm_subscription_paid_cents': '100',
        'xfm_subscription_units': '500', 'xfm_subscription_state': '3', 'xfm_status': '2', 'xfm_remaining_cents': '0'}
    if (_irt_number(sub['native_id'], positive=True) >= 4294967295
            or _irt_number(sub['xfm_reservation_id'], positive=True) <= 0
            or any(sub[k] != v for k, v in expected_sub.items())):
        raise ValueError('Same PRIMARY real100c subscription reservation must actually be released')
    return cell


def _irt_capture(context: JsonObject, reference: object, phase: JsonObject) -> JsonObject:
    ref = _futures_gui_evidence(reference, phase)
    output = Path(text_field(context, 'output')).resolve()
    if Path(ref['path']).resolve().parent != output or ref['bytes'] > 1024 * 1024:
        raise ValueError('Only this held client bounded current-toast capture allowed')
    capture = json_object(read_json(ref['path']))
    if (capture.get('schema') != 'ck3-issuer-refund-toast-day-capture-v1' or capture.get('run_id') != context['run_id']
            or capture.get('product') != 'financial-markets' or capture.get('case') != ISSUER_REFUND_TOAST_CASE):
        raise ValueError('Original day/toast capture crossed run')
    plan_ref = checked_capture_pin(capture.get('plan')); result_ref = checked_capture_pin(capture.get('actual_results'))
    for actual_ref in (plan_ref, result_ref):
        if Path(actual_ref['path']).resolve().parent not in (output, output / 'plans'):
            raise ValueError('Actual current case plan/results required')
    planned = json_object(read_json(plan_ref['path'])); result = json_object(read_json(result_ref['path']))
    rows, queries, steps = result.get('rows'), capture.get('queries'), planned.get('steps')
    if (not isinstance(steps, list) or not issuer_refund_toast_plan_matches(context, planned.get('steps'), capture.get('name'), 300)
            or not isinstance(rows, list) or len(rows) != 3 or not isinstance(queries, list) or len(queries) != 2):
        raise ValueError('One original natural day immediately followed by two readonly query rows required')
    for index, (row_value, step) in enumerate(zip(rows, steps)):
        row = json_object(row_value)
        if row.get('id') != json_object(step)['id'] or row.get('plan') != step or row.get('ok') is not True or not row.get('finished_at') or row.get('error'):
            raise ValueError('Original completed public rows required; no ACK-only delivery')
        if index:
            item = json_object(queries[index - 1]); dto = checked_capture_pin(item.get('dto'))
            if (set(item) != {'id', 'dto'} or item.get('id') != row['id']
                    or Path(dto['path']).resolve().parent != output
                    or dto['bytes'] > 256 * 1024 or read_json(dto['path']) != row.get('result')):
                raise ValueError('Exact current normalized DTO must match its retained original row')
            original_dto = json_object(read_json(dto['path']))
            if (original_dto.get('schema') != 'ck3_1210_current_interface_toast_result_v1'
                    or original_dto.get('step') != 'query-current-interface-toast-v1' or original_dto.get('game_version') != '1.21.0'
                    or original_dto.get('executable_sha256') != '2F2B236A16223891C2DA8B167F5F3738D2AE3E6D69DE1B4FBE190A5402998ACC'
                    or original_dto.get('read_only') is not True or original_dto.get('effect_attempted') is not False):
                raise ValueError('Original exact266 public readonly toast DTO required; no version/ABI relaxation')
    return capture


def _irt_named(toast: JsonObject, name: str, kind: str) -> str:
    found: list[JsonObject] = []
    for key in ('guiScopes', 'scriptScopes'):
        rows = toast.get(key)
        if not isinstance(rows, list):
            raise ValueError('Original typed named scope lists required')
        found += [json_object(row) for row in rows if json_object(row).get('name') == name]
    if (not found or any(row != found[0] for row in found)
            or found[0].get('kind') != kind or found[0].get('available') is not True):
        raise ValueError('Known matching named recipient/display-entry/actor required')
    value = (_irt_character(found[0].get('identity')) if kind == 'CHARACTER'
             else _coin_campaign_uint(found[0].get('identity')))
    if kind == 'STORY' and int(value) >= 4294967295:
        raise ValueError('Canonical valid uint32 StoryID required')
    return value



def _irt_public_named(dto: JsonObject, name: str, tag: int) -> str:
    """Bind only the three required public named IDs; the qualified SDK/Java owns full DTO parsing."""
    found: list[JsonObject] = []
    for key in ('saved_gui_scopes', 'saved_script_scopes'):
        values = dto.get(key)
        if not isinstance(values, list):
            raise ValueError('Original public named scope lists required')
        found += [json_object(row) for row in values if json_object(row).get('name') == name]
    if (not found or any(row != found[0] for row in found)
            or set(found[0]) != {'name', 'kind', 'observed_tag', 'identity_available', 'identity', 'unavailable_reason'}
            or found[0].get('observed_tag') != tag or type(found[0].get('observed_tag')) is not int
            or found[0].get('identity_available') is not True or found[0].get('unavailable_reason') is not None
            or found[0].get('kind') != ('character' if tag == 4 else 'story')):
        raise ValueError('Actual admitted public named identity required')
    value = (_irt_character(found[0].get('identity')) if tag == 4
             else _coin_campaign_uint(found[0].get('identity')))
    if tag == 22 and int(value) >= 4294967295:
        raise ValueError('Canonical valid uint32 StoryID required')
    return value


def _irt_toast(context: JsonObject, phase: JsonObject, capture: JsonObject, refund: JsonObject,
               terminal_save: FilePin, terminal_date: int) -> bool:
    cell = _irt_cell(phase.get('toast'), phase)
    if cell['status'] == 'NOT_OBSERVED':
        return False
    joins = cell.get('joins')
    if set(cell) != {'status', 'joins'} or not isinstance(joins, list) or len(joins) != 2:
        raise ValueError('Two actual source-joined typed observations required')
    queries = capture.get('queries')
    if not isinstance(queries, list) or len(queries) != 2:
        raise ValueError('Original two query captures required')
    reports: list[JsonObject] = []
    for reference, item in zip(joins, queries):
        proof = _futures_gui_evidence(reference, phase)
        if proof['bytes'] > 4 * 1024 * 1024:
            raise ValueError('Bounded existing NewsToastDelivery report required')
        report = json_object(read_json(proof['path'])); request = object_field(report, 'request')
        report_keys = {'schema', 'machineId', 'request', 'producers', 'newsScriptSources', 'toast',
                       'assessment', 'reason', 'entries', 'sources', 'passes', 'sourceJoinMatched',
                       'deliveryConfirmed', 'allHumanDeliveryConfirmed', 'gameStarted', 'financialCertified'}
        source_archive = object_field(_irt_inputs(context), 'source_archive')
        machine = read_json(file_pin(source_archive)['path']).get('machine_id')
        if (set(report) != report_keys
                or set(request) != {'schemaVersion', 'machineId', 'repository', 'toast', 'save', 'decoder'}
                or type(request.get('schemaVersion')) is not int or request.get('schemaVersion') != 1
                or request.get('machineId') != machine or report.get('machineId') != machine
                or Path(text_field(request, 'repository')).resolve() != Path(text_field(context, 'repo_root')).resolve()
                or not isinstance(report.get('producers'), dict)
                or not isinstance(report.get('newsScriptSources'), list) or not report['newsScriptSources']):
            raise ValueError('Complete existing typed Java report/request and current machine/repository required')
        if (report.get('schema') != 'xfm-news-toast-source-join-candidate-v1'
                or request.get('toast') != json_object(item)['dto'] or request.get('save') != terminal_save
                or any(report.get(k) is not False for k in
                       ('deliveryConfirmed', 'allHumanDeliveryConfirmed', 'gameStarted', 'financialCertified'))):
            raise ValueError('Actual unchanged source-pinned Java toast report required; no new credit flags')
        original = json_object(read_json(file_pin(json_object(item)['dto'])['path']))
        observation = object_field(report, 'toast'); identity = object_field(observation, 'identity')
        fields = {'snapshotId': 'snapshot_id', 'nativeRevision': 'native_revision', 'publicRevision': 'public_revision',
                  'gamePid': 'game_pid', 'connectionGeneration': 'connection_generation', 'querySequence': 'query_sequence',
                  'ownerThreadId': 'owner_thread_id', 'completedApplicationFrame': 'completed_application_frame',
                  'viewerCharacterId': 'viewer_played_character_id', 'dateRaw': 'date_raw'}
        raw_stage = original.get('stage')
        if not isinstance(raw_stage, str):
            raise ValueError('Original public toast stage must be exact text')
        if (any(identity.get(k) != original.get(v) or type(identity.get(k)) is not type(original.get(v))
                for k, v in fields.items())
                or observation.get('stage') != {'visible_pending_frame': 'VISIBLE_PENDING_FRAME',
                    'visible': 'VISIBLE', 'empty': 'EMPTY', 'hidden': 'HIDDEN', 'unavailable': 'UNAVAILABLE'}.get(raw_stage)
                or observation.get('title') != original.get('title') or observation.get('description') != original.get('description')):
            raise ValueError('Typed Java toast observation differs from its exact original DTO')
        if observation.get('stage') in ('VISIBLE', 'VISIBLE_PENDING_FRAME'):
            for name, kind, tag in (('xfm_news_recipient', 'CHARACTER', 4),
                                    ('xfm_news_display_entry', 'STORY', 22), ('xfm_news_actor', 'CHARACTER', 4)):
                if _irt_named(observation, name, kind) != _irt_public_named(original, name, tag):
                    raise ValueError('Typed named identity differs from original Native DTO')
        reports.append(report)
    first, second = (object_field(v, 'toast') for v in reports)
    if first.get('stage') not in ('VISIBLE_PENDING_FRAME', 'VISIBLE') or second.get('stage') != 'VISIBLE':
        raise ValueError('Available/empty/hidden/pending cannot be reported as observed delivery')
    a, b = object_field(first, 'identity'), object_field(second, 'identity')
    for key in ('gamePid', 'connectionGeneration', 'ownerThreadId', 'viewerCharacterId', 'dateRaw'):
        if a.get(key) != b.get(key):
            raise ValueError('Current native process/generation/thread/actor/date changed')
    actor = str(object_field(context, 'saved_campaign')['player_id'])
    process = object_field(capture, 'retained_process'); pid = process.get('pid')
    if type(pid) is not int or not isinstance(pid, int) or pid <= 0 or a.get('gamePid') != pid:
        raise ValueError('Native toast must belong to this retained Game process')
    original_rows = json_object(read_json(file_pin(capture['actual_results'])['path'])).get('rows')
    if not isinstance(original_rows, list) or len(original_rows) != 3:
        raise ValueError('Original day and two query result rows required')
    for identity, row in zip((a, b), original_rows[1:]):
        full = object_field(json_object(row), 'after_snapshot')
        diagnostics = object_field(full, 'diagnostics'); played = object_field(full, 'played_character')
        if (full.get('paused') is not True or full.get('date_raw') != identity.get('dateRaw')
                or diagnostics.get('bridge_pid') != identity.get('gamePid')
                or str(diagnostics.get('connection_generation')) != identity.get('connectionGeneration')
                or played.get('character_id') != identity.get('viewerCharacterId')):
            raise ValueError('Original query Full and normalized toast owner/date must agree')
    if (a.get('viewerCharacterId') != int(actor) or a.get('dateRaw') != terminal_date
            or _irt_number(b.get('completedApplicationFrame'), positive=True) <= _irt_number(a.get('completedApplicationFrame'), positive=True)
            or first.get('title') != second.get('title') or first.get('description') != second.get('description')):
        raise ValueError('Same actual message needs a strictly newer completed application frame')
    names = [('xfm_news_recipient', 'CHARACTER'), ('xfm_news_display_entry', 'STORY'), ('xfm_news_actor', 'CHARACTER')]
    identities = [_irt_named(first, n, k) for n, k in names]
    if identities != [_irt_named(second, n, k) for n, k in names] or identities[0] != actor or identities[2] != actor:
        raise ValueError('Actual new recipient/display-entry/actor identities required')
    report = reports[1]
    if report.get('sourceJoinMatched') is not True or report.get('assessment') != 'LOCAL_NATIVE_JOIN_MATCH' or report.get('reason') != 'NONE':
        raise ValueError('Only a true offline original Native/source join may support the local observation')
    entries, sources, passes = report.get('entries'), report.get('sources'), report.get('passes')
    if (not isinstance(entries, list) or len(entries) != 1 or not isinstance(sources, list) or len(sources) != 1
            or not isinstance(passes, list) or len(passes) != 3):
        raise ValueError('Original one discovery plus two complete source reads required')
    entry, source = json_object(entries[0]), json_object(sources[0])
    coin = object_field(object_field(refund, 'facts'), 'coin')
    if (entry.get('storyId') != identities[1] or entry.get('sourceStoryId') != coin['native_id']
            or source.get('storyId') != coin['native_id'] or source.get('storyCycle') != 'xfm_finance_coin'
            or type(entry.get('kind')) is not int or entry.get('kind') != 10
            or type(source.get('kind')) is not int or source.get('kind') != 10
            or entry.get('eventId') != coin['xfm_news_fact_counter']
            or source.get('factCounter') != entry.get('eventId') or source.get('lastFact') != entry.get('eventId')
            or entry.get('actorCharacterId') != int(actor) or source.get('actorCharacterId') != int(actor)
            or entry.get('day') != object_field(object_field(refund, 'facts'), 'before')['financial_day']):
        raise ValueError('An older queue item is not this actual new refund kind10')
    return True


def _irt_review(context: JsonObject, compiled: JsonObject, phases: JsonObject, date: int, terminal_date: int,
                capture_reference: object = None) -> JsonObject:
    prepared_context = dict(context)
    prepared_context['case_contract'] = object_field(compiled, 'config')
    prepared = json_object(resolve_post_start(prepared_context))
    context = json_object(resolve_post_start(context))
    if not _issuer_refund_toast_enabled(context) or prepared['case_contract'] != context['case_contract']:
        raise ValueError('Prepared issuer refund/toast config changed')
    base = _irt_baseline(context, phases, date)
    allowed = {row[0] for row in ISSUER_REFUND_TOAST_PHASES}
    for name in set(phases) - allowed:
        match = re.fullmatch(r'actual-(event|notification)-boundary-[0-9]{3,}', name)
        if match is None:
            raise ValueError('Unknown issuer refund/toast Root phase')
        assertion = ('actual_current_event_resolved_with_typed_or_reviewed_original_evidence'
                     if match[1] == 'event' else
                     'actual_pending_character_interaction_resolved_with_typed_or_reviewed_original_evidence')
        _coin_campaign_phase(context, object_field(phases, name), (assertion,))
    if not date <= terminal_date <= date + 24:
        raise ValueError('At most one original issuer natural day allowed')
    refunded = False; visible = False; refund: JsonObject = {}; receipts: object = [base['baseline_archive']]
    if ISSUER_REFUND_TOAST_PHASES[1][0] in phases:
        refund = _irt_refund(context, phases, date)
        refunded = refund['status'] == 'OBSERVED'
        stage = _irt_phase(context, phases, 1)
        receipts = stage.get('physical_archives', [])
        if not isinstance(receipts, list) or not receipts or receipts[0] != base['baseline_archive']:
            raise ValueError('Complete actual ordered SAVE list must start at current baseline')
        if refunded and receipts != [base['baseline_archive'], refund['after_archive']]:
            raise ValueError('Successful D0 refund requires exactly its two endpoint checkpoints')
    if ISSUER_REFUND_TOAST_PHASES[2][0] in phases:
        if not refunded:
            raise ValueError('A failed or unobserved business producer cannot advance for proof')
        final = _irt_phase(context, phases, 2)
        receipts = final.get('physical_archives')
        if (not isinstance(receipts, list) or not 2 <= len(receipts) <= 3
                or receipts[:2] != [base['baseline_archive'], refund['after_archive']]):
            raise ValueError('Complete actual checkpoints must preserve both D0 endpoints')
        if capture_reference is None:
            _irt_cell(final.get('toast'), final)
            if terminal_date != date or object_field(final, 'toast').get('status') != 'NOT_OBSERVED':
                raise ValueError('No queries dispatched at a pre-day boundary means zero-day NOT_OBSERVED')
        else:
            if len(receipts) != 3:
                raise ValueError('Actual post-query source must be the third physical checkpoint')
            terminal_save = _futures_gui_archive(receipts[2], final, terminal_date)
            for key in ('terminal_audit', 'terminal_raw', 'terminal_whole'):
                _futures_gui_evidence(final.get(key), final)
            if final.get('day_capture') != capture_reference:
                raise ValueError("Root review must use this held client's original capture")
            capture = _irt_capture(context, capture_reference, final)
            visible = _irt_toast(context, final, capture, refund, terminal_save, terminal_date)
            if visible and terminal_date != date + 24:
                raise ValueError('One actual completed natural day required for new refund delivery credit')
    elif capture_reference is not None or terminal_date != date:
        raise ValueError('No natural day/queries allowed before actual refund review')
    if not isinstance(receipts, list):
        raise ValueError('Original physical checkpoint list required')
    saves: set[str] = set()
    for index, ref in enumerate(receipts):
        phase = _irt_phase(context, phases, 2 if ISSUER_REFUND_TOAST_PHASES[2][0] in phases else (1 if len(receipts) > 1 else 0))
        saved = _futures_gui_archive(ref, phase, terminal_date if index == 2 else date)
        if saved['path'] in saves:
            raise ValueError('No archive alias can hide another physical SAVE')
        saves.add(saved['path'])
    if not 1 <= len(saves) <= 3:
        raise ValueError('Original at-most-three checkpoint budget changed')
    return json_object({'issuer_refund_toast': {'refund_observed': refunded, 'new_kind10_local_toast_observed': visible},
        'retained_physical_checkpoint_count': len(saves), 'physical_archives': receipts,
        'natural_days_advanced': (terminal_date - date) // 24,
        'case_contract_qualified': refunded and visible, 'issuer_refund_toast_case_qualified': refunded and visible,
        'status': 'OBSERVED_LOCAL_SCOPE' if refunded and visible else 'NOT_OBSERVED',
        'global_news_delivery_pass': False, 'all_human_delivery_pass': False,
        'financial_daily_coverage_verified': False, 'business_pass': False, 'product_release_pass': False,
        'result_boundary': 'ISSUER_REFUND_AND_LOCAL_NATIVE_JOIN_ONLY' if refunded and visible else 'ISSUER_REFUND_TOAST_NOT_OBSERVED'})


def _coin_campaign_uint(value: object, *, positive: bool = True) -> str:
    if (not isinstance(value, str) or re.fullmatch(r'0|[1-9][0-9]{0,19}', value) is None
            or int(value) > 18446744073709551615 or (positive and value == '0')):
        raise ValueError('Exact canonical decimal identity/amount required; absent is not zero')
    return value


def _coin_campaign_enabled(context: JsonObject) -> bool:
    config = object_field(context, 'case_contract')
    if context.get('case') != COIN_CAMPAIGN_CASE and 'coin_campaign_contract' not in config:
        return False
    from ck3_mod_acceptance_background_types import CONTINUOUS14_PASSIVE_STORY_TYPES_V1
    contract = object_field(config, 'coin_campaign_contract')
    phases = config.get('gui_phases')
    if (context.get('product') != 'financial-markets' or context.get('case') != COIN_CAMPAIGN_CASE
            or config.get('product') != context['product'] or config.get('case_id') != context['case']
            or config.get('schema') != 'ck3-mod-acceptance-product-case-v1'
            or config.get('execution_purpose') != 'product_acceptance'
            or config.get('acceptance_scope') != COIN_CAMPAIGN_SCOPE
            or config.get('startup_mode') != 'saved_campaign' or config.get('allow_actor_change') is not False
            or config.get('product_loading', 'present') != 'present'
            or type(config.get('maximum_natural_days')) is not int or config.get('maximum_natural_days') != 0
            or config.get('pending_interaction_policy') != 'stop_at_boundary'
            or config.get('business_contract_applicable') is not True or config.get('whole_product_release_pass') is not False
            or contract != COIN_CAMPAIGN_CONTRACT
            or any(type(contract.get(k)) is not int for k in ('physical_save_maximum', 'physical_save_max_bytes'))
            or any(contract.get(k) is not False for k in COIN_CAMPAIGN_CONTRACT
                   if k not in ('schema', 'physical_save_maximum', 'physical_save_max_bytes'))
            or config.get('passive_story_types') != list(CONTINUOUS14_PASSIVE_STORY_TYPES_V1)
            or not isinstance(phases, list) or len(phases) != 2
            or any(k in config for k in ('fixture_source', 'fixture_emitter', 'marker_inventory',
                                        'clock_purpose', 'continuous14_contract', 'frontend_rules'))):
        raise ValueError('Exact zero-day coin campaign acceptance contract required')
    for value, (name, requirements) in zip(phases, COIN_CAMPAIGN_PHASES):
        phase = json_object(value)
        if (set(phase) != {'id', 'at_day', 'requirements'} or phase.get('id') != name
                or type(phase.get('at_day')) is not int or phase.get('at_day') != 0
                or phase.get('requirements') != list(requirements)):
            raise ValueError('Only the two original same-day campaign Root phases are allowed')
    return True


def _coin_campaign_inputs(context: JsonObject) -> JsonObject:
    if not _coin_campaign_enabled(context):
        raise ValueError('Selected coin campaign contract required')
    inputs = object_field(context, 'case_inputs')
    if (set(inputs) not in ({'product_dir', 'plain_configuration', 'post_start', 'coin_campaign'},
                           {'product_dir', 'plain_configuration', 'post_start', 'coin_campaign', 'steam_manifest'})
            or context.get('execution_mode') == 'gui_only' or context.get('gui_saved_input') is not None):
        raise ValueError('Only current saved product/plain configuration and explicit campaign bindings allowed')
    binding = object_field(inputs, 'coin_campaign')
    if (set(binding) != {'source_archive', 'scenario_id', 'coin_a', 'coin_b'}
            or not isinstance(binding.get('scenario_id'), str)
            or re.fullmatch(r'[a-z][a-z0-9_-]{2,63}', str(binding.get('scenario_id'))) is None):
        raise ValueError('Actual scenario/latest source and two distinct coins required')
    coins: list[JsonObject] = []
    for key, allowed in (('coin_a', (2, 3)), ('coin_b', (4,))):
        coin = object_field(binding, key)
        if (set(coin) != {'native_id', 'permanent_id', 'entity_type'}
                or type(coin.get('entity_type')) is not int or coin.get('entity_type') not in allowed):
            raise ValueError('A must be actual house/dynasty, B actual title; no synthetic entity binding')
        _coin_campaign_uint(coin.get('native_id')); _coin_campaign_uint(coin.get('permanent_id'))
        coins.append(coin)
    if coins[0]['native_id'] == coins[1]['native_id'] or coins[0]['permanent_id'] == coins[1]['permanent_id']:
        raise ValueError('Two different actual coins are required')
    reference = file_pin(binding.get('source_archive'))
    if reference['bytes'] > 1024 * 1024 or Path(reference['path']).suffix.lower() != '.json':
        raise ValueError('Bounded source archive metadata required')
    checked_capture_pin(reference)
    archive = json_object(read_json(reference['path']))
    saved = object_field(context, 'saved_campaign'); source = file_pin(archive.get('archive'))
    actor_id = saved.get('player_id')
    if (archive.get('schema') != 'ck3-financial-checkpoint-archive-v1' or archive.get('exact_copy') is not True
            or archive.get('same_file') is not False or type(archive.get('date_raw')) is not int
            or archive.get('date_raw') != saved.get('date_raw')
            or saved.get('save') != source['path'] or type(saved.get('bytes')) is not int
            or saved.get('bytes') != source['bytes'] or saved.get('sha256') != source['sha256']
            or type(saved.get('date_raw')) is not int
            or type(actor_id) is not int or not isinstance(actor_id, int) or actor_id <= 0):
        raise ValueError('Explicit latest scenario archive must exactly bind the public saved startup')
    return binding


def _coin_campaign_phase(context: JsonObject, phase: JsonObject, requirements: tuple[str, ...]) -> None:
    assertions = object_field(phase, 'assertions')
    if (phase.get('run_id') != context['run_id'] or phase.get('reviewer') != '/root'
            or set(assertions) != set(requirements) or any(v is not True for v in assertions.values())):
        raise ValueError('Current literal Root campaign review required; no PASS from dispatch')


def _coin_campaign_actions(value: object, phase: JsonObject) -> None:
    if not isinstance(value, list) or not 1 <= len(value) <= 64:
        raise ValueError('Bounded original current query/action pairs required')
    for item in value:
        action = json_object(item)
        if set(action) != {'query', 'activation'}:
            raise ValueError('Each normal action needs its own original fresh query')
        for reference in action.values():
            _futures_gui_evidence(reference, phase)


def _coin_campaign_baseline(context: JsonObject, phases: JsonObject, date: int) -> JsonObject:
    binding = _coin_campaign_inputs(context)
    if object_field(context, 'saved_campaign').get('date_raw') != date:
        raise ValueError('Actual initial campaign date differs from declared saved source')
    phase = object_field(phases, COIN_CAMPAIGN_PHASES[0][0])
    _coin_campaign_phase(context, phase, COIN_CAMPAIGN_PHASES[0][1])
    _futures_gui_archive(phase.get('baseline_archive'), phase, date)
    for key in ('baseline_audit', 'baseline_raw', 'baseline_whole'):
        _futures_gui_evidence(phase.get(key), phase)
    actual = object_field(phase, 'campaign_bindings')
    account = object_field(actual, 'PRIMARY')
    if (set(actual) != {'source_archive', 'scenario_id', 'coin_a', 'coin_b', 'PRIMARY'}
            or any(actual.get(k) != v for k, v in binding.items())
            or set(account) != {'native_id', 'permanent_id', 'holder_character_id'}
            or account.get('holder_character_id') != str(object_field(context, 'saved_campaign')['player_id'])):
        raise ValueError('Actual PRIMARY/source/scenario/A/B baseline binding differs')
    for key in ('native_id', 'permanent_id', 'holder_character_id'):
        _coin_campaign_uint(account.get(key))
    return actual


def _coin_campaign_review(context: JsonObject, compiled: JsonObject, phases: JsonObject, date: int) -> JsonObject:
    context = json_object(resolve_post_start(context))
    if not _coin_campaign_enabled(context) or compiled.get('config') != context['case_contract']:
        raise ValueError('Prepared coin campaign contract changed')
    binding = _coin_campaign_baseline(context, phases, date)
    account = object_field(binding, 'PRIMARY')
    baseline = object_field(phases, COIN_CAMPAIGN_PHASES[0][0])
    transaction = object_field(phases, COIN_CAMPAIGN_PHASES[1][0])
    _coin_campaign_phase(context, transaction, COIN_CAMPAIGN_PHASES[1][1])
    receipts = transaction.get('physical_archives')
    if not isinstance(receipts, list) or not 1 <= len(receipts) <= 3:
        raise ValueError('Every actual SAVE attempt must be retained within three archives')
    archives: dict[str, FilePin] = {}
    for reference in receipts:
        saved = _futures_gui_archive(reference, transaction, date)
        if saved['path'] in archives:
            raise ValueError('Archive aliases cannot hide an extra physical checkpoint')
        archives[saved['path']] = saved
    baseline_save = _futures_gui_archive(baseline.get('baseline_archive'), baseline, date)
    if not receipts or receipts[0] != baseline.get('baseline_archive') or archives.get(baseline_save['path']) != baseline_save:
        raise ValueError('Current baseline must be first in the complete physical checkpoint list')
    cells = object_field(transaction, 'coin_campaign_gui')
    if set(cells) != set(COIN_CAMPAIGN_CELLS):
        raise ValueError('All four campaign cells must explicitly be observed or not observed')
    observed: list[str] = []; missing: list[str] = []
    paid_archive: object = None
    for name in COIN_CAMPAIGN_CELLS:
        cell = object_field(cells, name)
        if cell.get('status') == 'NOT_OBSERVED':
            evidence = cell.get('evidence')
            if (set(cell) != {'status', 'reason', 'evidence'}
                    or not isinstance(cell.get('reason'), str) or not cell.get('reason')
                    or not isinstance(evidence, list)):
                raise ValueError('Unknown permission, type, depth or fill must remain NOT_OBSERVED')
            for reference in evidence:
                _futures_gui_evidence(reference, transaction)
            missing.append(name)
            continue
        assertions = object_field(cell, 'assertions')
        if name in COIN_CAMPAIGN_CELLS[:2]:
            role = 'coin_a' if name == COIN_CAMPAIGN_CELLS[0] else 'coin_b'
            required = {'actual_typed_bound_entity_reference_preserved', 'actual_independent_named_entity_source_corroborates_reference',
                        'actual_source_and_current_coin_permanent_identity_and_entity_binding_match'}
            reference = object_field(cell, 'entity_reference')
            if (set(cell) != {'status', 'coin_role', 'entity_reference', 'named_entity_source', 'assertions', 'audit', 'raw'}
                    or cell.get('coin_role') != role or set(reference) != {'serialized_type', 'identity'}
                    or not isinstance(reference.get('serialized_type'), str)
                    or re.fullmatch(r'[a-z_]{1,64}', str(reference.get('serialized_type'))) is None
                    or reference.get('serialized_type') in ('unknown', 'missing', 'null', 'value')
                    or not isinstance(reference.get('identity'), str) or not 1 <= len(str(reference.get('identity'))) <= 256):
                raise ValueError('A typed entity reference and independent named source required; coin names do not prove binding')
            _futures_gui_evidence(cell.get('named_entity_source'), transaction)
        else:
            required = {'actual_normal_fresh_GUI_only_no_unknown_replay', 'actual_current_PRIMARY_not_restricted_money',
                        'actual_independent_cash_coin_fee_and_all_old_obligations_reconciled'}
            keys = {'status', 'assertions', 'before_archive', 'after_archive', 'gui_actions', 'audit', 'raw', 'reconciliation'}
            if name == 'paid_A_charter_promotion':
                keys |= {'paid_cents', 'route'}
                required |= {'actual_frozen_A_payer_controller_nonce_charter_event_once',
                             'actual_PRIMARY_100cent_fee_and_A_advertising_plus100_B_unchanged',
                             'actual_no_price_or_recipient_delivery_credit_from_ad_reached'}
                if (type(cell.get('paid_cents')) is not int or cell.get('paid_cents') != 100
                        or cell.get('route') != 'xfm_market_charter/xfm_issuer.100/xfm_issuer_promote'
                        or cell.get('before_archive') != baseline.get('baseline_archive')):
                    raise ValueError('Only the real100cent A charter route can receive promotion credit')
                paid_archive = cell.get('after_archive')
            else:
                keys.add('trades')
                required |= {'actual_four_new_A_B_buy_sell_fills_not_submission_or_quotes',
                             'actual_coin_switch_each_order_uses_selected_asset_only_and_distinct_beneficiary'}
                if cell.get('before_archive') != (paid_archive if paid_archive is not None else baseline.get('baseline_archive')):
                    raise ValueError('Trade endpoints must follow the actual paid checkpoint, never skip the fee leg')
                trades = cell.get('trades')
                if not isinstance(trades, list) or len(trades) != 4:
                    raise ValueError('Both coins require independent real BUY and SELL fills')
                order_ids: set[str] = set(); native_ids: set[str] = set()
                for item, (role, side) in zip(trades, (('coin_a', 'BUY'), ('coin_b', 'BUY'), ('coin_a', 'SELL'), ('coin_b', 'SELL'))):
                    trade = json_object(item); coin = object_field(binding, role)
                    if (set(trade) != {'coin_role', 'side', 'coin_native_id', 'coin_id', 'order_native_id', 'order_id',
                            'requested_lots', 'filled_units', 'gross_cents', 'fee_cents', 'counterparty_account_native_id',
                            'counterparty_beneficial_owner_id', 'gui_actions', 'execution_reconciliation'}
                            or trade.get('coin_role') != role or trade.get('side') != side
                            or trade.get('coin_native_id') != coin['native_id'] or trade.get('coin_id') != coin['permanent_id']
                            or type(trade.get('requested_lots')) is not int or trade.get('requested_lots') != 1):
                        raise ValueError('Actual A BUY,B BUY,A SELL,B SELL one-lot operations must bind their own asset')
                    native = _coin_campaign_uint(trade.get('order_native_id')); permanent = _coin_campaign_uint(trade.get('order_id'))
                    if native in native_ids or permanent in order_ids:
                        raise ValueError('Four new order identities required; no duplicate/replay credit')
                    native_ids.add(native); order_ids.add(permanent)
                    _coin_campaign_uint(trade.get('filled_units')); _coin_campaign_uint(trade.get('gross_cents'))
                    _coin_campaign_uint(trade.get('fee_cents'), positive=False)
                    if (_coin_campaign_uint(trade.get('counterparty_account_native_id')) == account['native_id']
                            or _coin_campaign_uint(trade.get('counterparty_beneficial_owner_id')) == account['holder_character_id']):
                        raise ValueError('A self-beneficiary or own account cannot supply independent demand')
                    _coin_campaign_actions(trade.get('gui_actions'), transaction)
                    _futures_gui_evidence(trade.get('execution_reconciliation'), transaction)
            if set(cell) != keys:
                raise ValueError('Unknown or incomplete campaign transaction cell')
            before = _futures_gui_archive(cell.get('before_archive'), transaction, date)
            after = _futures_gui_archive(cell.get('after_archive'), transaction, date)
            if (before['path'] == after['path'] or (before['bytes'], before['sha256']) == (after['bytes'], after['sha256'])
                    or archives.get(before['path']) != before or archives.get(after['path']) != after):
                raise ValueError('Distinct actual current checkpoint endpoints are required')
            _coin_campaign_actions(cell.get('gui_actions'), transaction)
            _futures_gui_evidence(cell.get('reconciliation'), transaction)
        if cell.get('status') != 'OBSERVED' or set(assertions) != required or any(v is not True for v in assertions.values()):
            raise ValueError('Only individually reviewed real campaign proof receives credit')
        for key in ('audit', 'raw'):
            _futures_gui_evidence(cell.get(key), transaction)
        observed.append(name)
    complete = not missing
    if complete and len(archives) != 3:
        raise ValueError('Complete promotion and dual-coin business requires its three actual checkpoints')
    return json_object({'coin_campaign_gui': cells, 'campaign_bindings': binding,
        'physical_archives': receipts, 'retained_physical_checkpoint_count': len(archives),
        'observed_cells': observed, 'not_observed_cells': missing, 'natural_days_advanced': 0,
        'case_contract_qualified': complete, 'coin_campaign_case_qualified': complete,
        'status': 'OBSERVED_LOCAL_SCOPE' if complete else 'PARTIAL',
        'financial_daily_coverage_verified': False, 'manipulation_causal_success_pass': False,
        'global_news_delivery_pass': False, 'all_AI_eligibility_or_new_issuance_pass': False,
        'performance_pass': False, 'business_pass': False, 'product_release_pass': False,
        'result_boundary': 'CAMPAIGN_LOCAL_OBSERVATIONS_ONLY' if complete else 'PARTIAL_CAMPAIGN_NOT_OBSERVED'})


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
    if _news_delivery_daily_enabled(json_object(context)):
        return _run_news_delivery_daily(context, client)
    compiled, binding = compiled_contract(context)
    config = compiled['config']
    futures_gui = _futures_gui_transactions_enabled(json_object(context))
    redemption_gui = _redemption_gui_enabled(json_object(context))
    redemption_existing = _redemption_existing_enabled(json_object(context))
    independent_seed = _independent_financial_seed_enabled(json_object(context))
    coin_campaign = _coin_campaign_enabled(json_object(context))
    issuer_refund_toast = _issuer_refund_toast_enabled(json_object(context))
    if futures_gui or redemption_gui or redemption_existing or independent_seed or coin_campaign or issuer_refund_toast:
        context = resolve_post_start(context)
        require(config == context['case_contract'], 'Prepared selected GUI config differs')
    pending_policy = _fixture_pending_interaction_policy(config)
    inbox_observations: list[JsonObject] = []
    frame = client.snapshot(require_event_free=False)
    frames = [{'day': 0, 'snapshot': frame}]
    initial_date = frame.get('date_raw')
    require(type(initial_date) is int, 'Actual initial native calendar is required')
    phases = {}
    refund_toast_stop = False; refund_toast_day_attempted = False; refund_toast_capture = None
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
                if issuer_refund_toast and phase['id'] == ISSUER_REFUND_TOAST_PHASES[2][0] and refund_toast_day_attempted:
                    ready = True  # A real boundary is retained, never followed by a second day attempt.
                if ready:
                    phases[phase['id']] = root_phase(client, context, phase['id'], phase['requirements'], frame, compiled)
                    if issuer_refund_toast and phase['id'] == ISSUER_REFUND_TOAST_PHASES[0][0]:
                        actual_base = _irt_baseline(json_object(context), json_object(phases), initial_date)
                        refund_toast_stop = object_field(actual_base, 'eligibility')['status'] == 'NOT_OBSERVED'
                    if issuer_refund_toast and phase['id'] == ISSUER_REFUND_TOAST_PHASES[1][0]:
                        refund_toast_stop = _irt_refund(json_object(context), json_object(phases), initial_date)['status'] == 'NOT_OBSERVED'
                    if coin_campaign and phase['id'] == COIN_CAMPAIGN_PHASES[0][0]:
                        _coin_campaign_baseline(json_object(context), json_object(phases), initial_date)
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
                    if issuer_refund_toast and refund_toast_stop:
                        break
            if issuer_refund_toast and (refund_toast_stop or
                    refund_toast_day_attempted and ISSUER_REFUND_TOAST_PHASES[2][0] in phases):
                break
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
            if issuer_refund_toast:
                require(not refund_toast_day_attempted, 'Issuer toast day was already attempted; never retry')
                refund_toast_day_attempted = True  # Consume before dispatch; UNKNOWN must not submit another day.
            row = _advance_fixture_day(client, config, sequence, context['case_spec']['budgets']['command_timeout'])
            value = row['result']
            if issuer_refund_toast:
                refund_toast_capture = row.get('current_toast_capture')
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
    if issuer_refund_toast:
        facts['issuer_refund_toast_day_capture'] = refund_toast_capture
        facts.update(_irt_review(json_object(context), json_object(compiled), json_object(phases),
            initial_date, frame['date_raw'], refund_toast_capture))
    if coin_campaign:
        facts.update(_coin_campaign_review(json_object(context), json_object(compiled), json_object(phases), initial_date))
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
    if _news_delivery_daily_enabled(json_object(context)):
        review = _ndd_review(json_object(context), json_object(compiled), json_object(facts['root_phases']),
            facts['news_daily_captures'], facts['actual_native_frames'], facts['news_daily_stop_reason'])
        require(all(facts.get(k) == v for k, v in review.items()), 'Original daily news statuses or local credit changed')
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
    if _issuer_refund_toast_enabled(json_object(context)):
        frames = facts.get('actual_native_frames')
        require(isinstance(frames, list) and bool(frames), 'Original bounded issuer toast frames required')
        dates = [json_object(json_object(row)['snapshot']).get('date_raw') for row in frames]
        require(all(type(day) is int for day in dates) and dates == sorted(dates),
                'Actual issuer toast dates must be ordered integers')
        review = _irt_review(json_object(context), json_object(compiled), json_object(facts['root_phases']),
            dates[0], dates[-1], facts.get('issuer_refund_toast_day_capture'))
        require(all(facts.get(k) == v for k, v in review.items()), 'Original issuer refund/toast credit changed')
    if _coin_campaign_enabled(json_object(context)):
        frames = facts.get('actual_native_frames')
        require(isinstance(frames, list) and bool(frames), 'Actual same-date campaign frames required')
        date = json_object(json_object(frames[0])['snapshot']).get('date_raw')
        if type(date) is not int or not isinstance(date, int):
            raise ValueError('Actual initial campaign date required')
        review = _coin_campaign_review(json_object(context), json_object(compiled),
            json_object(facts['root_phases']), date)
        require(all(facts.get(k) == v for k, v in review.items()), 'Original campaign credit changed')
        require(all(json_object(json_object(row)['snapshot']).get('date_raw') == date for row in frames),
                'Campaign GUI must remain on the original native date')
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
        FUTURES_NATURAL14_CASE_V1, futures_natural14_contract_matches)
    config = object_field(context, 'case_contract')
    selected = context.get('case') == FUTURES_NATURAL14_CASE_V1 or 'futures_natural_liquidity14_contract' in config
    if selected and not futures_natural14_contract_matches(context.get('product'), context.get('case'), config):
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


def _futures_natural14_review_v1(context: JsonObject, compiled: JsonObject,
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



def _futures_natural14_uint(value: object, *, zero: bool = False) -> str:
    if (not isinstance(value, str) or re.fullmatch(r'0|[1-9][0-9]{0,19}', value) is None
            or (not zero and value == '0')):
        raise ValueError('Explicit exact decimal identity/quantity required; missing is unknown')
    return value


def _futures_natural14_ref(row: JsonObject, key: str, kind: str = 'story') -> str:
    reference = object_field(object_field(row, 'scopeReferences'), key)
    require(reference.get('serializedType') == kind, 'Actual typed scope reference required')
    value = reference.get('nativeId')
    return _irt_character(value) if kind == 'char' else _futures_natural14_uint(value)


def _futures_natural14_rows(audit_pin: object, raw_pin: object, whole_pin: object,
                            phase: JsonObject, save: FilePin) -> dict[str, JsonObject]:
    records: dict[str, JsonObject] = {}
    for name, ref in (('audit', audit_pin), ('raw', raw_pin), ('whole', whole_pin)):
        records[name] = _redemption_existing_metadata(_futures_gui_evidence(ref, phase))
    financial = object_field(object_field(records['audit'], 'audit'), 'financial')
    first = object_field(financial, 'first')
    coverage = object_field(first, 'streamingCoverage')
    raw, whole = records['raw'], object_field(records['whole'], 'digest')
    require(financial.get('second') == [] and first.get('save') == save
        and coverage.get('passes') == 2 and coverage.get('completeStreamBytes') == str(save['bytes'])
        and coverage.get('completeStreamSha256') == save['sha256']
        and object_field(first, 'audit').get('assessment') == 'CANDIDATE_INVARIANTS_HOLD'
        and records['audit'].get('financialCertified') is False and financial.get('financialCertified') is False,
        'Complete unchanged two-pass candidate audit required, never a product certification')
    require(object_field(raw, 'request').get('save') == save and raw.get('fullStreamPasses') == 1
        and raw.get('inputUnchangedAtGuards') is True and raw.get('completeStreamBytes') == str(save['bytes'])
        and raw.get('completeStreamSha256') == save['sha256'] and raw.get('financialCertified') is False,
        'Original exact Raw EOF/source required')
    require(whole.get('save') == save and whole.get('completePasses') == 2
        and whole.get('inputUnchanged') is True and whole.get('completeStreamBytes') == str(save['bytes'])
        and whole.get('completeStreamSha256') == save['sha256'], 'Complete whole canonical source required')
    stories, canonical, selected = first.get('stories'), whole.get('records'), raw.get('stories')
    if (not isinstance(stories, list) or not isinstance(canonical, list)
            or not isinstance(selected, list) or not 1 <= len(selected) <= 16):
        raise ValueError('Actual audit/whole/Raw record arrays required')
    rows: dict[str, JsonObject] = {}
    hashes: dict[str, str] = {}
    for item in canonical:
        row = json_object(item); identity = _futures_natural14_uint(row.get('nativeId'))
        digest = row.get('canonicalTokenSha256')
        require(identity not in hashes and isinstance(digest, str) and re.fullmatch(r'[a-f0-9]{64}', digest) is not None,
            'Unique actual whole canonical record identity/hash required')
        hashes[identity] = str(digest)
    for item in stories:
        row = json_object(item); identity = _futures_natural14_uint(row.get('nativeId'))
        require(identity not in rows and identity in hashes, 'Unique audit identity must belong to full whole graph')
        rows[identity] = row
    selected_ids: set[str] = set()
    for item in selected:
        row = json_object(item); identity = _futures_natural14_uint(row.get('id'))
        require(identity not in selected_ids and identity in rows
            and row.get('producerCanonicalTokenSha256') == hashes[identity],
            'Each retained Raw record must join the actual whole canonical hash')
        selected_ids.add(identity)
    return rows


def _futures_natural14_story(rows: dict[str, JsonObject], native: object, permanent: object,
                             kind: str) -> JsonObject:
    identity = _futures_natural14_uint(native); number = _futures_natural14_uint(permanent)
    row = rows.get(identity)
    require(row is not None, 'Actual complete audit lacks the requested record')
    actual = json_object(row)
    require(actual.get('type') == kind and actual.get('permanentId') == {'present': True, 'decimal': number}
        and sum(r.get('type') == kind and r.get('permanentId') == actual['permanentId'] for r in rows.values()) == 1,
        'Unique exact type/native/permanent identity required')
    return actual


def _futures_natural14_target(rows: dict[str, JsonObject], target: JsonObject, actor: str) -> JsonObject:
    position = _futures_natural14_story(rows, target['native_id'], target['position_id'], 'xfm_futures_position')
    account = _futures_natural14_story(rows, target['account_native_id'], target['account_id'], 'xfm_finance_account')
    _futures_natural14_story(rows, target['contract_native_id'], target['contract_id'], 'xfm_futures_contract')
    numbers = object_field(position, 'exactIntegers'); side = target.get('side')
    require(side in ('long', 'short') and numbers.get('xfm_status') == '0'
        and int(_futures_natural14_uint(numbers.get('xfm_lots'))) >= 1
        and int(_futures_natural14_uint(numbers.get('xfm_mark_cents'))) > 0
        and 'xfm_pending_payment' not in numbers
        and _futures_natural14_ref(position, 'xfm_contract') == target['contract_native_id']
        and _futures_natural14_ref(position, 'xfm_' + str(side) + '_account') == target['account_native_id']
        and _futures_natural14_ref(position, 'xfm_' + ('short' if side == 'long' else 'long') + '_account') != target['account_native_id']
        and _futures_natural14_ref(account, 'xfm_holder', 'char') == actor,
        'Target must actually be open, owned on exactly the declared side, priced and without pending payment')
    return position


def _futures_natural14_order(rows: dict[str, JsonObject], order: JsonObject, target: JsonObject) -> JsonObject:
    row = _futures_natural14_story(rows, order.get('order_native_id'), order.get('order_id'), 'xfm_futures_order')
    numbers = object_field(row, 'exactIntegers')
    side = 'SELL' if target['side'] == 'long' else 'BUY'
    require(order.get('side') == side and type(order.get('lots')) is int and order['lots'] == 1
        and type(order.get('leverage')) is int and order['leverage'] == 1
        and order.get('close_position_id') == target['position_id']
        and order.get('account_native_id') == target['account_native_id']
        and order.get('contract_native_id') == target['contract_native_id']
        and numbers.get('xfm_side') == ('2' if side == 'SELL' else '1')
        and numbers.get('xfm_leverage') == '1' and numbers.get('xfm_reduce_order') == '1'
        and int(_futures_natural14_uint(numbers.get('xfm_remaining_lots'), zero=True)) <= 1
        and int(_futures_natural14_uint(numbers.get('xfm_filled_gross_cents'), zero=True)) >= 0
        and _futures_natural14_ref(row, 'xfm_account') == target['account_native_id']
        and _futures_natural14_ref(row, 'xfm_contract') == target['contract_native_id']
        and _futures_natural14_ref(row, 'xfm_close_position') == target['native_id'],
        'One original normal close order must match actual target, side, account and contract')
    return row


def _futures_natural14_review_v2(context: JsonObject, compiled: JsonObject,
                                phases: JsonObject, diagnostic: JsonObject) -> JsonObject:
    require(_futures_natural14_enabled(context) and compiled.get('config') == context['case_contract'],
        'Prepared natural futures v2 case differs')
    _futures_natural14_diagnostic(diagnostic)
    specs = object_field(compiled, 'config').get('gui_phases')
    if not isinstance(specs, list) or len(specs) != 3:
        raise ValueError('Exactly the declared three v2 phases required')
    require(set(phases) == {str(json_object(s)['id']) for s in specs}, 'No additional operation phase')
    reviews: list[JsonObject] = []
    for spec_value in specs:
        spec = json_object(spec_value); phase = object_field(phases, str(spec['id']))
        requirements = spec.get('requirements')
        if not isinstance(requirements, list) or any(not isinstance(k, str) for k in requirements):
            raise ValueError('Explicit finite phase requirements required')
        _coin_campaign_phase(context, phase, tuple(str(k) for k in requirements))
        require(not any(key in phase for key in ('sell_orders', 'opening_orders')),
            'V1 two-order payloads and additional opening orders are outside v2')
        reviews.append(phase)
    initial, ending = object_field(diagnostic, 'before').get('date_raw'), object_field(diagnostic, 'after').get('date_raw')
    require(type(initial) is int and type(ending) is int, 'Actual integer endpoint dates required')
    if not isinstance(initial, int) or not isinstance(ending, int) or ending != initial + 336:
        raise ValueError('One original fourteen-day interval required')
    receipts: list[FilePin] = []
    saves: list[FilePin] = []
    endpoints: list[dict[str, JsonObject]] = []
    for phase, date in zip(reviews, (initial, initial, ending)):
        receipt = _futures_gui_evidence(phase.get('physical_archive'), phase)
        save = _futures_gui_archive(receipt, phase, date)
        receipts.append(receipt); saves.append(save)
        endpoints.append(_futures_natural14_rows(phase.get('audit'), phase.get('raw'), phase.get('whole'), phase, save))
    require(len({s['path'] for s in saves}) == 3 and reviews[2].get('physical_archives') == receipts,
        'Exactly three distinct actual SAVEs in [0,0,14] order required')
    for reference in receipts:
        _futures_gui_evidence(reference, reviews[2])
    target = object_field(reviews[0], 'target_position')
    names = {'native_id', 'position_id', 'account_native_id', 'account_id', 'contract_native_id', 'contract_id',
        'side', 'source_archive', 'source_audit', 'source_raw', 'source_whole'}
    require(set(target) == names, 'One explicit actual source target; no predicted identity or default')
    for name in ('native_id', 'position_id', 'account_native_id', 'account_id', 'contract_native_id', 'contract_id'):
        _futures_natural14_uint(target[name])
    source_save = _futures_gui_archive(target['source_archive'], reviews[0], initial)
    startup = object_field(context, 'saved_campaign')
    actor = _irt_character(str(startup.get('player_id')))
    require(startup.get('save') == source_save['path'] and startup.get('bytes') == source_save['bytes']
        and startup.get('sha256') == source_save['sha256'] and startup.get('date_raw') == initial
        and source_save['path'] not in {s['path'] for s in saves}, 'Target source must be actual admitted startup, not a new SAVE')
    source_rows = _futures_natural14_rows(target['source_audit'], target['source_raw'], target['source_whole'], reviews[0], source_save)
    source_position = _futures_natural14_target(source_rows, target, actor)
    baseline_position = _futures_natural14_target(endpoints[0], target, actor)
    require(source_position == baseline_position, 'D0 target cannot silently change between source and baseline')
    operations = object_field(reviews[1], 'close_orders')
    cells = object_field(reviews[2], 'futures_natural_liquidity14')
    require(set(operations) == {'reduce'} and set(cells) == {'reduce'}, 'V2 admits only one close; no opening SHORT or extra cell')
    order = object_field(operations, 'reduce'); cell = _irt_cell(cells['reduce'], reviews[2])
    same_day_owned_orders = {identity for identity, row in endpoints[1].items()
        if identity not in endpoints[0] and row.get('type') == 'xfm_futures_order'
        and _futures_natural14_ref(row, 'xfm_account') == target['account_native_id']}
    admitted_orders = ({_futures_natural14_uint(order.get('order_native_id'))}
        if order.get('status') == 'PLACED' else set())
    require(same_day_owned_orders == admitted_orders,
        'Actual D0 audit may contain only this one new owned close, never an undeclared opening SHORT')
    if order.get('status') == 'PLACED':
        original_order_native = _futures_natural14_uint(order.get('order_native_id'))
        original_order_id = _futures_natural14_uint(order.get('order_id'))
        require(not any(row.get('type') == 'xfm_futures_order'
            and row.get('permanentId') == {'present': True, 'decimal': original_order_id}
            for rows in (source_rows, endpoints[0]) for row in rows.values()),
            'An existing permanent order ID cannot be relabeled as a new close')
        require(original_order_native not in source_rows and original_order_native not in endpoints[0],
            'Close must be a new original operation, never an old order replay')
        _futures_natural14_order(endpoints[1], order, target)
        actions = order.get('gui_actions')
        if not isinstance(actions, list) or not 1 <= len(actions) <= 64:
            raise ValueError('Retained finite fresh normal GUI query/activation pairs required')
        for value in actions:
            action = json_object(value)
            require(set(action) == {'query', 'activation'}, 'Each original action retains its fresh query')
            for action_reference in action.values():
                _futures_gui_evidence(action_reference, reviews[1])
        _futures_gui_evidence(order.get('reservation_reconciliation'), reviews[1])
    else:
        require(set(order) == {'status', 'reason', 'evidence'} and order.get('status') == 'NOT_PLACED',
            'Unplaced close remains explicit; no synthetic pending')
        _irt_cell({**order, 'status': 'NOT_OBSERVED'}, reviews[1])
    if cell.get('status') == 'OBSERVED':
        require(order.get('status') == 'PLACED' and set(cell) == {'status', 'order_native_id', 'order_id',
            'before_archive', 'order_archive', 'after_archive', 'p1_position_native_id', 'assertions',
            'order_position_reconciliation', 'margin_cash_fee_counterparty_reconciliation'},
            'Actual P1, target and reconciliation required; submission/dates are not a fill')
        require(cell['order_native_id'] == order['order_native_id'] and cell['order_id'] == order['order_id']
            and [cell['before_archive'], cell['order_archive'], cell['after_archive']] == receipts,
            'Observation must belong to this original close and three actual checkpoints')
        final_order = _futures_natural14_order(endpoints[2], order, target)
        require(object_field(final_order, 'exactIntegers').get('xfm_remaining_lots') == '0',
            'Actual one-lot close must have no remaining quantity')
        p1_native = _futures_natural14_uint(cell.get('p1_position_native_id'))
        require(p1_native not in endpoints[0] and p1_native in endpoints[2], 'P1 recipient must be new and retained at endpoint')
        p1 = endpoints[2][p1_native]; numbers = object_field(p1, 'exactIntegers')
        own = 'sell' if target['side'] == 'long' else 'buy'
        other = 'buy' if own == 'sell' else 'sell'
        require(p1.get('type') == 'xfm_futures_position' and numbers.get('xfm_fill_receipt_version') == '1'
            and numbers.get('xfm_fill_' + own + '_order_id') == order['order_id']
            and numbers.get('xfm_fill_' + own + '_account_id') == target['account_id']
            and numbers.get('xfm_fill_' + own + '_intent') == '1'
            and numbers.get('xfm_fill_' + own + '_close_source_id') == target['position_id']
            and numbers.get('xfm_fill_slice_source_position_id') == target['position_id']
            and numbers.get('xfm_fill_lots') == '1'
            and object_field(final_order, 'exactIntegers').get('xfm_filled_gross_cents') == numbers.get('xfm_fill_mark_cents')
            and int(_futures_natural14_uint(numbers.get('xfm_fill_mark_cents'))) > 0
            and _futures_natural14_ref(p1, 'xfm_contract') == target['contract_native_id'],
            'Immutable positive-fill slice must name this order, owned close side and original source position')
        counter_id = _futures_natural14_uint(numbers.get('xfm_fill_' + other + '_account_id'))
        counters = [r for r in endpoints[2].values() if r.get('type') == 'xfm_finance_account'
            and r.get('permanentId') == {'present': True, 'decimal': counter_id}]
        require(counter_id != target['account_id'] and len(counters) == 1, 'Actual unique independent counterparty account required')
        own_account = _futures_natural14_story(endpoints[2], target['account_native_id'], target['account_id'], 'xfm_finance_account')
        require(_futures_natural14_ref(counters[0], 'xfm_holder', 'char') != _futures_natural14_ref(own_account, 'xfm_holder', 'char')
            and _futures_natural14_ref(counters[0], 'xfm_beneficial_owner', 'char') != _futures_natural14_ref(own_account, 'xfm_beneficial_owner', 'char'),
            'Counterparty cannot be the same holder/beneficiary')
        final_position = _futures_natural14_story(endpoints[2], target['native_id'], target['position_id'], 'xfm_futures_position')
        require(int(_futures_natural14_uint(object_field(final_position, 'exactIntegers').get('xfm_lots'), zero=True))
            <= int(_futures_natural14_uint(object_field(baseline_position, 'exactIntegers').get('xfm_lots'))) - 1,
            'Actual source exposure must decrease; new-position counts alone are insufficient')
        assertions = object_field(cell, 'assertions')
        required = {'actual_original_close_and_P1_slice_source_and_owned_side_bound',
            'actual_remaining_leg_holder_and_beneficiary_constraints_reconciled',
            'actual_paired_collateral_fees_cash_and_unrelated_assets_reconciled',
            'actual_no_self_trade_synthetic_counterparty_or_forced_fill'}
        require(set(assertions) == required and all(v is True for v in assertions.values()), 'Explicit actual financial reconciliation required')
        for key in ('order_position_reconciliation', 'margin_cash_fee_counterparty_reconciliation'):
            _futures_gui_evidence(cell[key], reviews[2])
    observed = cell.get('status') == 'OBSERVED'
    return json_object({'futures_natural_liquidity14': cells, 'close_orders': operations, 'target_position': target,
        'physical_archives': receipts, 'retained_physical_checkpoint_count': 3,
        'observed_cells': ['reduce'] if observed else [], 'not_observed_cells': [] if observed else ['reduce'],
        'natural_days_advanced': 14, 'financial_daily_coverage_verified': False, 'business_pass': False,
        'performance_pass': False, 'derivatives_acceptance_pass': False, 'product_release_pass': False,
        'result_boundary': 'NATURAL_OWNED_POSITION_REDUCE_LOCAL_OBSERVATION_ONLY'})


def _futures_natural14_review(context: JsonObject, compiled: JsonObject,
                             phases: JsonObject, diagnostic: JsonObject) -> JsonObject:
    from ck3_mod_acceptance_background_types import futures_natural14_contract_matches_v2
    if futures_natural14_contract_matches_v2(context.get('product'), context.get('case'), context.get('case_contract')):
        return _futures_natural14_review_v2(context, compiled, phases, diagnostic)
    return _futures_natural14_review_v1(context, compiled, phases, diagnostic)


def _futures_natural14_result_schema(context: JsonObject) -> str:
    contract = object_field(object_field(context, 'case_contract'), 'futures_natural_liquidity14_contract')
    return ('ck3-futures-natural-liquidity14-result-v2' if contract.get('schema') ==
        'ck3-futures-natural-liquidity14-contract-v2' else 'ck3-futures-natural-liquidity14-result-v1')


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
        require(current['date_raw'] == before['date_raw'], 'Declared normal business operations stay on day0')
        phases[str(spec['id'])] = root_phase(client, context, spec['id'], spec['requirements'], current, compiled)
    row = client.continuous14_diagnostic(); value = json_object(row['result'])
    require(object_field(value, 'before')['date_raw'] == before['date_raw'], 'Clock cannot start after unobserved days')
    spec = json_object(specs[2])
    phases[str(spec['id'])] = root_phase(client, context, spec['id'], spec['requirements'], object_field(value, 'after'), compiled)
    facts = json_object({'schema': _futures_natural14_result_schema(context), 'run_id': context['run_id'],
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
    require(facts.get('schema') == _futures_natural14_result_schema(context)
        and facts.get('run_id') == context['run_id'] and facts.get('case') == context['case']
        and facts.get('product') == context['product'] and facts.get('compiled_contract') == binding,
        'Natural futures original result crossed run/case/source')
    review = _futures_natural14_review(context, compiled, object_field(facts, 'root_phases'), object_field(facts, 'diagnostic_result'))
    require(all(facts.get(k) == v for k, v in review.items()), 'Retained result differs from actual original evidence')
    return json_object({**facts, **review, 'verification_scope': ('natural_owned_position_reduce_local_observation_only' if _futures_natural14_result_schema(context) == 'ck3-futures-natural-liquidity14-result-v2' else 'natural_short_reduce_local_observations_only')})


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


NEWS_DELIVERY_DAILY_CASE = 'news-delivery-daily'
NEWS_DELIVERY_DAILY_SCOPE = 'local_native_daily_news_observation_only'
NEWS_DELIVERY_DAILY_CONTRACT: JsonObject = json_object({'schema': 'ck3-news-delivery-daily-contract-v1', 'maximum_daily_attempts': 3, 'maximum_natural_days': 3, 'physical_save_maximum': 2, 'physical_save_max_bytes': 268435456, 'readonly_toast_queries_per_day': 2, 'day_timeout_seconds': 300, 'normal_close_reserve_seconds': 180, 'stop_on_visible_candidate': True, 'stop_on_event_boundary': True, 'business_actions': False, 'observer_arm': False, 'direct_business_setters': False, 'forced_AI_or_death': False, 'financial_daily_coverage_verified': False, 'all_human_delivery_pass': False, 'whole_product_release_pass': False})
NEWS_DELIVERY_DAILY_PHASES = (('bind-news-delivery-baseline', 0, ('actual_latest_physical_source_and_same_actor_date_loaded_without_business_actions', 'actual_one_new_baseline_archive_audit_raw_whole_and_cold_comparison_pinned', 'actual_two_SAVE_three_day_original_deadline_and_180second_exit_reserve_valid', 'actual_baseline_owned_window_sample_minimized_non_topmost_nonforeground_and_all_requested_paths_background')), ('retain-daily-toast-and-news-source-join', 3, ('actual_each_once_day_is_immediately_followed_by_two_readonly_toast_queries_in_its_original_plan', 'actual_same_owner_paused_dates_and_all_original_attempts_including_empty_or_boundary_retained', 'actual_second_physical_SAVE_and_terminal_news_cursor_raw_whole_sources_pinned', 'actual_visible_news_recipient_source_event_content_localization_join_or_explicit_NOT_OBSERVED', 'actual_no_issuance_promotion_delisting_forced_event_or_foreground_action_requested_and_no_daily_coverage_or_all_human_credit_inferred')))

def _news_delivery_daily_enabled(context: JsonObject) -> bool:
    config = object_field(context, 'case_contract')
    if context.get('case') != NEWS_DELIVERY_DAILY_CASE and 'news_delivery_daily_contract' not in config:
        return False
    from ck3_mod_acceptance_background_types import CONTINUOUS14_PASSIVE_STORY_TYPES_V1
    contract = object_field(config, 'news_delivery_daily_contract')
    integers = {k for k, v in NEWS_DELIVERY_DAILY_CONTRACT.items() if type(v) is int}
    if (context.get('product') != 'financial-markets' or context.get('case') != NEWS_DELIVERY_DAILY_CASE
            or config.get('product') != context['product'] or config.get('case_id') != context['case']
            or config.get('schema') != 'ck3-mod-acceptance-product-case-v1'
            or config.get('execution_purpose') != 'product_acceptance'
            or config.get('acceptance_scope') != NEWS_DELIVERY_DAILY_SCOPE
            or config.get('startup_mode') != 'saved_campaign' or config.get('allow_actor_change') is not False
            or config.get('product_loading', 'present') != 'present'
            or type(config.get('maximum_natural_days')) is not int or config.get('maximum_natural_days') != 3
            or config.get('pending_interaction_policy') != 'stop_at_boundary'
            or config.get('business_contract_applicable') is not False or config.get('whole_product_release_pass') is not False
            or contract != NEWS_DELIVERY_DAILY_CONTRACT
            or any(type(contract.get(k)) is not bool or contract.get(k) is not v for k, v in NEWS_DELIVERY_DAILY_CONTRACT.items() if type(v) is bool)
            or any(type(contract.get(k)) is not int for k in integers)
            or any(contract.get(k) is not False for k, v in NEWS_DELIVERY_DAILY_CONTRACT.items() if v is False)
            or config.get('passive_story_types') != list(CONTINUOUS14_PASSIVE_STORY_TYPES_V1)
            or any(k in config for k in ('fixture_source', 'fixture_emitter', 'marker_inventory', 'clock_purpose',
                                         'continuous14_contract', 'frontend_rules'))):
        raise ValueError('Exact three-day local news observation contract required')
    phases = config.get('gui_phases')
    if not isinstance(phases, list) or len(phases) != 2:
        raise ValueError('Two original daily news Root phases required')
    for row, (name, day, requirements) in zip(phases, NEWS_DELIVERY_DAILY_PHASES):
        value = json_object(row)
        if (set(value) != {'id', 'at_day', 'requirements'} or value.get('id') != name
                or type(value.get('at_day')) is not int or value.get('at_day') != day
                or value.get('requirements') != list(requirements)):
            raise ValueError('Original [0,3] daily news phases changed')
    return True

def news_delivery_daily_plan_matches(context: object, steps: object, name: object, timeout: object) -> bool:
    """Only this exact case may compose its existing day plus two readonly rows."""
    selected = json_object(context)
    if not _news_delivery_daily_enabled(selected):
        return False
    if (not isinstance(name, str) or re.fullmatch(r'case-natural-day-[0-9]{4,}', name) is None
            or type(timeout) is not int or timeout != 300
            or not isinstance(steps, list) or len(steps) != 3):
        return False
    from ck3_mod_acceptance_native_day import STEP
    first = json_object(steps[0])
    normal = (type(first.get('days')) is int and type(first.get('timeout')) is int
        and first == {'id': name, 'kind': 'advance_day', 'days': 1,
                      'timeout': timeout, 'allow_event_boundary': True})
    args = first.get('args')
    revision = args.get('expected_revision') if isinstance(args, dict) else None
    native = (set(first) == {'id', 'tool', 'args', 'fresh_revision'} and first.get('id') == name
        and first.get('tool') == 'ck3_execute_step' and first.get('fresh_revision') is False
        and isinstance(args, dict) and set(args) == {'step', 'expected_revision'}
        and args.get('step') == STEP and type(revision) is int and isinstance(revision, int)
        and revision >= 0)
    expected = [{'id': name + '-toast0' + str(i), 'kind': 'tool',
                 'tool': 'ck3_query_current_interface_toast_v1', 'args': {}} for i in (1, 2)]
    return (normal or native) and steps[1:] == expected

def _ndd_inputs(context: JsonObject) -> JsonObject:
    if not _news_delivery_daily_enabled(context):
        raise ValueError('Selected daily news case required')
    inputs = object_field(context, 'case_inputs')
    allowed = {'product_dir', 'plain_configuration', 'post_start', 'news_delivery_daily'}
    if (set(inputs) not in (allowed, allowed | {'steam_manifest'})
            or context.get('execution_mode') == 'gui_only' or context.get('gui_saved_input') is not None):
        raise ValueError('Only original saved source and normal product inputs allowed')
    binding = object_field(inputs, 'news_delivery_daily')
    if (set(binding) != {'source_archive', 'scenario_id'} or not isinstance(binding.get('scenario_id'), str)
            or re.fullmatch(r'[a-z][a-z0-9_-]{2,63}', str(binding['scenario_id'])) is None):
        raise ValueError('Explicit current source/scenario required; no predicted new identities')
    ref = file_pin(binding.get('source_archive'))
    if ref['bytes'] > 1024 * 1024:
        raise ValueError('Bounded original source archive metadata required')
    checked_capture_pin(ref)
    source = json_object(read_json(ref['path'])); save = file_pin(source.get('archive'))
    startup = object_field(context, 'saved_campaign')
    actor_id = startup.get('player_id')
    if (source.get('schema') != 'ck3-financial-checkpoint-archive-v1'
            or source.get('exact_copy') is not True or source.get('same_file') is not False
            or type(source.get('date_raw')) is not int or type(startup.get('date_raw')) is not int
            or source['date_raw'] != startup['date_raw'] or startup.get('save') != save['path']
            or type(startup.get('bytes')) is not int or startup['bytes'] != save['bytes']
            or startup.get('sha256') != save['sha256']
            or type(actor_id) is not int
            or not isinstance(source.get('machine_id'), str)):
        raise ValueError('Latest archive must exactly bind this public saved startup')
    _irt_character(str(actor_id))
    return binding

def _ndd_capture(context: JsonObject, reference: object, phase: JsonObject) -> JsonObject:
    ref = _futures_gui_evidence(reference, phase)
    output = Path(text_field(context, 'output')).resolve()
    if Path(ref['path']).resolve().parent != output or ref['bytes'] > 1024 * 1024:
        raise ValueError('Only this held client bounded current-toast capture allowed')
    capture = json_object(read_json(ref['path']))
    if (capture.get('schema') != 'ck3-news-delivery-daily-capture-v1' or capture.get('run_id') != context['run_id']
            or capture.get('product') != 'financial-markets' or capture.get('case') != NEWS_DELIVERY_DAILY_CASE):
        raise ValueError('Original day/toast capture crossed run')
    plan_ref = checked_capture_pin(capture.get('plan')); result_ref = checked_capture_pin(capture.get('actual_results'))
    for actual_ref in (plan_ref, result_ref):
        if Path(actual_ref['path']).resolve().parent not in (output, output / 'plans'):
            raise ValueError('Actual current case plan/results required')
    planned = json_object(read_json(plan_ref['path'])); result = json_object(read_json(result_ref['path']))
    rows, queries, steps = result.get('rows'), capture.get('queries'), planned.get('steps')
    if (not isinstance(steps, list) or not news_delivery_daily_plan_matches(context, planned.get('steps'), capture.get('name'), 300)
            or not isinstance(rows, list) or len(rows) != 3 or not isinstance(queries, list) or len(queries) != 2):
        raise ValueError('One original natural day immediately followed by two readonly query rows required')
    for index, (row_value, step) in enumerate(zip(rows, steps)):
        row = json_object(row_value)
        if row.get('id') != json_object(step)['id'] or row.get('plan') != step or row.get('ok') is not True or not row.get('finished_at') or row.get('error'):
            raise ValueError('Original completed public rows required; no ACK-only delivery')
        if index:
            item = json_object(queries[index - 1]); dto = checked_capture_pin(item.get('dto'))
            if (set(item) != {'id', 'dto'} or item.get('id') != row['id']
                    or Path(dto['path']).resolve().parent != output
                    or dto['bytes'] > 256 * 1024 or read_json(dto['path']) != row.get('result')):
                raise ValueError('Exact current normalized DTO must match its retained original row')
            original_dto = json_object(read_json(dto['path']))
            if (original_dto.get('schema') != 'ck3_1210_current_interface_toast_result_v1'
                    or original_dto.get('step') != 'query-current-interface-toast-v1' or original_dto.get('game_version') != '1.21.0'
                    or original_dto.get('executable_sha256') != '2F2B236A16223891C2DA8B167F5F3738D2AE3E6D69DE1B4FBE190A5402998ACC'
                    or original_dto.get('read_only') is not True or original_dto.get('effect_attempted') is not False):
                raise ValueError('Original exact266 public readonly toast DTO required; no version/ABI relaxation')
    projection = checked_capture_pin(capture.get('day_projection'))
    if Path(projection['path']).resolve().parent != output or projection['bytes'] > 4 * 1024 * 1024:
        raise ValueError('Actual same-client normalized original day projection required')
    capture['day_projection'] = {'path': projection['path'], 'bytes': projection['bytes'], 'sha256': projection['sha256']}
    return capture

def _ndd_toast(context: JsonObject, phase: JsonObject, capture: JsonObject,
               terminal_save: FilePin, terminal_date: int) -> bool:
    cell = _irt_cell(phase.get('toast'), phase)
    if cell['status'] == 'NOT_OBSERVED':
        return False
    joins = cell.get('joins')
    if set(cell) != {'status', 'capture', 'joins', 'localization_sources'} or not isinstance(joins, list) or len(joins) != 2:
        raise ValueError('Two actual source-joined typed observations required')
    queries = capture.get('queries')
    if not isinstance(queries, list) or len(queries) != 2:
        raise ValueError('Original two query captures required')
    reports: list[JsonObject] = []
    for reference, item in zip(joins, queries):
        proof = _futures_gui_evidence(reference, phase)
        if proof['bytes'] > 4 * 1024 * 1024:
            raise ValueError('Bounded existing NewsToastDelivery report required')
        report = json_object(read_json(proof['path'])); request = object_field(report, 'request')
        report_keys = {'schema', 'machineId', 'request', 'producers', 'newsScriptSources', 'toast',
                       'assessment', 'reason', 'entries', 'sources', 'passes', 'sourceJoinMatched',
                       'deliveryConfirmed', 'allHumanDeliveryConfirmed', 'gameStarted', 'financialCertified'}
        source_archive = object_field(_ndd_inputs(context), 'source_archive')
        machine = read_json(file_pin(source_archive)['path']).get('machine_id')
        if (set(report) != report_keys
                or set(request) != {'schemaVersion', 'machineId', 'repository', 'toast', 'save', 'decoder'}
                or type(request.get('schemaVersion')) is not int or request.get('schemaVersion') != 1
                or request.get('machineId') != machine or report.get('machineId') != machine
                or Path(text_field(request, 'repository')).resolve() != Path(text_field(context, 'repo_root')).resolve()
                or not isinstance(report.get('producers'), dict)
                or not isinstance(report.get('newsScriptSources'), list) or not report['newsScriptSources']):
            raise ValueError('Complete existing typed Java report/request and current machine/repository required')
        if (report.get('schema') != 'xfm-news-toast-source-join-candidate-v1'
                or request.get('toast') != json_object(item)['dto'] or request.get('save') != terminal_save
                or any(report.get(k) is not False for k in
                       ('deliveryConfirmed', 'allHumanDeliveryConfirmed', 'gameStarted', 'financialCertified'))):
            raise ValueError('Actual unchanged source-pinned Java toast report required; no new credit flags')
        original = json_object(read_json(file_pin(json_object(item)['dto'])['path']))
        observation = object_field(report, 'toast'); identity = object_field(observation, 'identity')
        fields = {'snapshotId': 'snapshot_id', 'nativeRevision': 'native_revision', 'publicRevision': 'public_revision',
                  'gamePid': 'game_pid', 'connectionGeneration': 'connection_generation', 'querySequence': 'query_sequence',
                  'ownerThreadId': 'owner_thread_id', 'completedApplicationFrame': 'completed_application_frame',
                  'viewerCharacterId': 'viewer_played_character_id', 'dateRaw': 'date_raw'}
        raw_stage = original.get('stage')
        if not isinstance(raw_stage, str):
            raise ValueError('Original public toast stage must be exact text')
        if (any(identity.get(k) != original.get(v) or type(identity.get(k)) is not type(original.get(v))
                for k, v in fields.items())
                or observation.get('stage') != {'visible_pending_frame': 'VISIBLE_PENDING_FRAME',
                    'visible': 'VISIBLE', 'empty': 'EMPTY', 'hidden': 'HIDDEN', 'unavailable': 'UNAVAILABLE'}.get(raw_stage)
                or observation.get('title') != original.get('title') or observation.get('description') != original.get('description')):
            raise ValueError('Typed Java toast observation differs from its exact original DTO')
        if observation.get('stage') in ('VISIBLE', 'VISIBLE_PENDING_FRAME'):
            for name, kind, tag in (('xfm_news_recipient', 'CHARACTER', 4),
                                    ('xfm_news_display_entry', 'STORY', 22), ('xfm_news_actor', 'CHARACTER', 4)):
                if _irt_named(observation, name, kind) != _irt_public_named(original, name, tag):
                    raise ValueError('Typed named identity differs from original Native DTO')
        reports.append(report)
    first, second = (object_field(v, 'toast') for v in reports)
    if first.get('stage') not in ('VISIBLE_PENDING_FRAME', 'VISIBLE') or second.get('stage') != 'VISIBLE':
        raise ValueError('Available/empty/hidden/pending cannot be reported as observed delivery')
    a, b = object_field(first, 'identity'), object_field(second, 'identity')
    for key in ('gamePid', 'connectionGeneration', 'ownerThreadId', 'viewerCharacterId', 'dateRaw'):
        if a.get(key) != b.get(key):
            raise ValueError('Current native process/generation/thread/actor/date changed')
    actor = str(object_field(context, 'saved_campaign')['player_id'])
    process = object_field(capture, 'retained_process'); pid = process.get('pid')
    if type(pid) is not int or not isinstance(pid, int) or pid <= 0 or a.get('gamePid') != pid:
        raise ValueError('Native toast must belong to this retained Game process')
    original_rows = json_object(read_json(file_pin(capture['actual_results'])['path'])).get('rows')
    if not isinstance(original_rows, list) or len(original_rows) != 3:
        raise ValueError('Original day and two query result rows required')
    for identity, row in zip((a, b), original_rows[1:]):
        full = object_field(json_object(row), 'after_snapshot')
        diagnostics = object_field(full, 'diagnostics'); played = object_field(full, 'played_character')
        if (full.get('paused') is not True or full.get('date_raw') != identity.get('dateRaw')
                or diagnostics.get('bridge_pid') != identity.get('gamePid')
                or str(diagnostics.get('connection_generation')) != identity.get('connectionGeneration')
                or played.get('character_id') != identity.get('viewerCharacterId')):
            raise ValueError('Original query Full and normalized toast owner/date must agree')
    if (a.get('viewerCharacterId') != int(actor) or a.get('dateRaw') != terminal_date
            or _irt_number(b.get('completedApplicationFrame'), positive=True) <= _irt_number(a.get('completedApplicationFrame'), positive=True)
            or first.get('title') != second.get('title') or first.get('description') != second.get('description')):
        raise ValueError('Same actual message needs a strictly newer completed application frame')
    names = [('xfm_news_recipient', 'CHARACTER'), ('xfm_news_display_entry', 'STORY'), ('xfm_news_actor', 'CHARACTER')]
    if _irt_number(b.get('querySequence'), positive=True) <= _irt_number(a.get('querySequence'), positive=True):
        raise ValueError('Two distinct original Native query sequences must advance')
    identities = [_irt_named(first, n, k) for n, k in names]
    if identities != [_irt_named(second, n, k) for n, k in names] or identities[0] != actor :
        raise ValueError('Actual new recipient/display-entry/actor identities required')
    report = reports[1]
    if report.get('sourceJoinMatched') is not True or report.get('assessment') != 'LOCAL_NATIVE_JOIN_MATCH' or report.get('reason') != 'NONE':
        raise ValueError('Only a true offline original Native/source join may support the local observation')
    entries, sources, passes = report.get('entries'), report.get('sources'), report.get('passes')
    if (not isinstance(entries, list) or len(entries) != 1 or not isinstance(sources, list) or len(sources) != 1
            or not isinstance(passes, list) or len(passes) != 3):
        raise ValueError('Original one discovery plus two complete source reads required')
    entry, source = json_object(entries[0]), json_object(sources[0])
    news_actor = _irt_character(str(entry.get('actorCharacterId')))
    news_kind, news_scene = entry.get('kind'), entry.get('scene')
    if (entry.get('storyId') != identities[1] or source.get('storyId') != entry.get('sourceStoryId')
            or news_actor != identities[2] or source.get('actorCharacterId') != entry.get('actorCharacterId')
            or type(news_kind) is not int or not 1 <= news_kind <= 10 or source.get('kind') != news_kind
            or type(news_scene) is not int or not 1 <= news_scene <= 20 or source.get('scene') != news_scene
            or source.get('factCounter') != entry.get('eventId') or source.get('lastFact') != entry.get('eventId')):
        raise ValueError('Actual current news/source revision, kind, scene and remote actor must join exactly')
    _irt_number(entry.get('newsId'), positive=True); _irt_number(entry.get('eventId'), positive=True)
    _irt_number(entry.get('day'))
    stem = ('xfm_crisis_scene_' + str(news_scene)) if news_kind == 5 else ('xfm_news_kind_' + str(news_kind))
    if first.get('title') != stem + '_title' or first.get('description') != stem + '_desc':
        raise ValueError('Native message content must retain exact production localization keys; no inferred rendered text')
    localizations = cell.get('localization_sources')
    expected_paths = [Path(text_field(context, 'repo_root')) / ('mod_financial_markets/localization/' + folder + '/' + name)
        for folder, name in [('simp_chinese', 'xfm_crisis_l_simp_chinese.yml' if news_kind == 5 else 'xfm_news_l_simp_chinese.yml'), ('english', 'xfm_crisis_l_english.yml' if news_kind == 5 else 'xfm_news_l_english.yml')]]
    if not isinstance(localizations, list) or len(localizations) != 2:
        raise ValueError('Two exact production localization sources required')
    for reference, expected_path in zip(localizations, expected_paths):
        actual = _futures_gui_evidence(reference, phase)
        if Path(actual['path']).resolve() != expected_path.resolve() or actual['bytes'] > 1024 * 1024:
            raise ValueError('Localization source is not the current exact financial production leaf')
        # Scene narrative strings live in the same news localization catalog.
        text = expected_path.read_text(encoding='utf-8-sig')
        if any(not re.search(r'(?m)^\s*' + re.escape(stem + suffix) + r':[0-9]+\s+"[^\r\n]+"\s*$', text)
               for suffix in ('_title', '_desc')):
            raise ValueError('Actual localization key/value is missing; no substitute text accepted')
    return True

def _ndd_phase(context: JsonObject, phases: JsonObject, index: int) -> JsonObject:
    phase = object_field(phases, NEWS_DELIVERY_DAILY_PHASES[index][0])
    _coin_campaign_phase(context, phase, tuple(NEWS_DELIVERY_DAILY_PHASES[index][2]))
    return phase


def _ndd_baseline(context: JsonObject, phases: JsonObject, date: int) -> JsonObject:
    binding = _ndd_inputs(context); phase = _ndd_phase(context, phases, 0)
    if object_field(context, 'saved_campaign').get('date_raw') != date or phase.get('source_archive') != binding['source_archive']:
        raise ValueError('News baseline must bind the actual saved source/actor/date')
    _futures_gui_evidence(phase['source_archive'], phase)
    _futures_gui_archive(phase.get('baseline_archive'), phase, date)
    for name in ('baseline_audit', 'baseline_raw', 'baseline_whole', 'cold_comparison'):
        _futures_gui_evidence(phase.get(name), phase)
    return phase


def _ndd_candidate(capture: JsonObject) -> bool:
    queries = capture.get('queries')
    if not isinstance(queries, list) or len(queries) != 2:
        raise ValueError('Exactly two actual query DTOs required')
    a, b = [json_object(read_json(file_pin(json_object(q)['dto'])['path'])) for q in queries]
    if a.get('stage') not in ('visible_pending_frame', 'visible') or b.get('stage') != 'visible':
        return False
    try:
        identities = [tuple(_irt_public_named(v, n, tag) for n, tag in
            (('xfm_news_recipient', 4), ('xfm_news_display_entry', 22), ('xfm_news_actor', 4))) for v in (a, b)]
    except ValueError:
        return False
    return (identities[0] == identities[1] and a.get('title') == b.get('title')
        and a.get('description') == b.get('description')
        and int(str(b.get('completed_application_frame'))) > int(str(a.get('completed_application_frame'))))


def _ndd_review(context: JsonObject, compiled: JsonObject, phases: JsonObject,
                captures: list[JsonObject], frames: list[JsonObject], stop_reason: str) -> JsonObject:
    prepared_context = dict(context); prepared_context['case_contract'] = object_field(compiled, 'config')
    prepared = json_object(resolve_post_start(prepared_context)); context = json_object(resolve_post_start(context))
    if not _news_delivery_daily_enabled(context) or prepared['case_contract'] != context['case_contract']:
        raise ValueError('Prepared daily news contract changed')
    if set(phases) != {p[0] for p in NEWS_DELIVERY_DAILY_PHASES} or not 1 <= len(frames) <= 5 or not 0 <= len(captures) <= 3:
        raise ValueError('Exactly two Root phases and at most three original daily captures required')
    initial = object_field(frames[0], 'snapshot'); date = initial.get('date_raw')
    actor = object_field(context, 'saved_campaign').get('player_id')
    if type(date) is not int or initial.get('paused') is not True or object_field(initial, 'played_character').get('character_id') != actor:
        raise ValueError('Actual paused initial actor/date required')
    base = _ndd_baseline(context, phases, date); final = _ndd_phase(context, phases, 1)
    terminal = object_field(frames[-1], 'snapshot'); end = terminal.get('date_raw')
    if type(end) is not int or not date <= end <= date + 72 or terminal.get('paused') is not True:
        raise ValueError('Daily news actual natural calendar exceeded three days or did not pause')
    receipts = final.get('physical_archives')
    if not isinstance(receipts, list) or len(receipts) != 2 or receipts[0] != base['baseline_archive']:
        raise ValueError('Exactly baseline and terminal physical SAVE receipts required')
    before = _futures_gui_archive(receipts[0], final, date); after = _futures_gui_archive(receipts[1], final, end)
    if before['path'] == after['path']:
        raise ValueError('Two receipt aliases cannot substitute one physical SAVE')
    for name in ('terminal_audit', 'terminal_raw', 'terminal_whole', 'news_reconciliation'):
        _futures_gui_evidence(final.get(name), final)
    if final.get('daily_captures') != captures:
        raise ValueError('Terminal must retain every original client day capture in order')
    if len(frames) != 1 + len(captures) + (1 if stop_reason == 'event_boundary' else 0):
        raise ValueError('Every retained daily/boundary frame must correspond to its original attempt')
    actual_captures = []; previous = initial; transport_owner = None
    for capture_index, reference in enumerate(captures):
        capture = _ndd_capture(context, reference, final)
        projected = json_object(read_json(file_pin(capture['day_projection'])['path']))
        value = object_field(projected, 'result'); first, last = object_field(value, 'before'), object_field(value, 'after')
        first_date, last_date = first.get('date_raw'), last.get('date_raw')
        if type(first_date) is not int or type(last_date) is not int or first_date != previous.get('date_raw') or last_date != first_date + 24:
            raise ValueError('Each captured original day must be exactly the next24 raw hours')
        for f in (first, last):
            if f.get('paused') is not True or object_field(f, 'played_character').get('character_id') != actor:
                raise ValueError('Original day endpoints must pause the same actor')
            if object_field(f, 'diagnostics').get('bridge_pid') != object_field(initial, 'diagnostics').get('bridge_pid') or object_field(f, 'diagnostics').get('connection_generation') != object_field(initial, 'diagnostics').get('connection_generation'):
                raise ValueError('Original daily transport owner changed')
        if frames[capture_index + 1].get('snapshot') != last:
            raise ValueError('Retained paused frame differs from the original day projection')
        if type(value.get('requested_days')) is not int or value.get('requested_days') != 1 or value.get('requested_interval_complete') is not True or value.get('event_boundary') is not None:
            raise ValueError('Captured day must be one completed original native day')
        queries = capture.get('queries')
        if not isinstance(queries, list) or len(queries) != 2:
            raise ValueError('Two actual immediate query records required')
        for q in queries:
            dto = json_object(read_json(file_pin(json_object(q)['dto'])['path']))
            if dto.get('date_raw') != last.get('date_raw') or dto.get('viewer_played_character_id') != actor or dto.get('game_pid') != object_field(last, 'diagnostics').get('bridge_pid') or str(dto.get('connection_generation')) != str(object_field(last, 'diagnostics').get('connection_generation')):
                raise ValueError('Every immediate toast query must retain its same paused day/owner')
            thread = dto.get('owner_thread_id')
            if type(thread) is not int or thread <= 0:
                raise ValueError('Every actual toast query needs its owner thread')
            owner = (dto.get('game_pid'), str(dto.get('connection_generation')), thread)
            if transport_owner is not None and owner != transport_owner:
                raise ValueError('Daily toast application-main owner changed')
            transport_owner = owner
        actual_captures.append(capture); previous = last
    previous_date = previous.get('date_raw')
    if type(previous_date) is not int or end < previous_date or end - previous_date >= 24:
        raise ValueError('Terminal date does not match captured days or a bounded original event boundary')
    if end != previous_date and stop_reason != 'event_boundary':
        raise ValueError('Unrecorded native date increment has no original boundary')
    if stop_reason not in ('visible_candidate', 'three_days_completed', 'event_boundary'):
        raise ValueError('Unknown daily news stop reason')
    if stop_reason == 'event_boundary' and 'event_boundary' not in frames[-1]:
        raise ValueError('Original boundary observation must be retained explicitly')
    if stop_reason == 'three_days_completed' and len(captures) != 3:
        raise ValueError('Three-day completion requires three actual days, never interpolation')
    if stop_reason == 'visible_candidate' and (not actual_captures or not _ndd_candidate(actual_captures[-1])):
        raise ValueError('Early stop requires the actual final Native visible candidate')
    cell = _irt_cell(final.get('toast'), final); observed = False
    if cell['status'] == 'OBSERVED':
        if not captures or cell.get('capture') != captures[-1] or stop_reason != 'visible_candidate':
            raise ValueError('Only the final immediately captured candidate can be source-joined')
        observed = _ndd_toast(context, final, actual_captures[-1], after, end)
    return json_object({'local_native_news_observed': observed, 'case_contract_qualified': observed,
        'gui_contract_qualified': True, 'status': 'OBSERVED_LOCAL_SCOPE' if observed else 'NOT_OBSERVED',
        'physical_archives': receipts, 'retained_physical_checkpoint_count': 2,
        'native_elapsed_raw_hours': end - date,
        'natural_days_advanced': (end - date) // 24 if (end - date) % 24 == 0 else None, 'daily_attempts_with_queries': len(captures),
        'all_human_delivery_pass': False, 'global_news_delivery_pass': False,
        'financial_daily_coverage_verified': False, 'business_pass': False, 'product_release_pass': False,
        'localization_rendered_text_pass': False,
        'result_boundary': 'LOCAL_NATIVE_NEWS_SOURCE_JOIN_ONLY' if observed else 'DAILY_NEWS_NOT_OBSERVED'})


def _run_news_delivery_daily(context, client):
    compiled, binding = compiled_contract(context); context = resolve_post_start(context)
    require(compiled['config'] == context['case_contract'], 'Prepared daily news config differs')
    profile = Path(context['state_dir']) / 'profile'; config = compiled['config']
    enabled = read_json(profile / 'dlc_load.json')['enabled_mods']
    require(enabled == compiled.get('enabled_mods', ['mod/product.mod', 'mod/fixture.mod']), 'Actual product/passive-only mounts differ')
    first = client.snapshot(require_event_free=False); client.validate_frame(first, require_event_free=False)
    require(first.get('paused') is True, 'Initial native Full must pause')
    frames = [{'day': 0, 'snapshot': first}]; phases = {}; captures = []; reason = 'three_days_completed'
    base = root_phase(client, context, NEWS_DELIVERY_DAILY_PHASES[0][0], list(NEWS_DELIVERY_DAILY_PHASES[0][2]), first, compiled)
    phases[NEWS_DELIVERY_DAILY_PHASES[0][0]] = base
    _ndd_baseline(json_object(context), json_object(phases), first['date_raw'])
    for index in range(3):
        client.guard(180)  # Actual original hold deadline, never renewed.
        row = client.advance_day(days=1, timeout=300, allow_event_boundary=True,
            allow_actor_change=False, pending_interaction_policy='stop_at_boundary', current_toast_queries=True)
        value = object_field(json_object(row), 'result')
        if value.get('event_boundary') is not None:
            boundary_after = object_field(value, 'after'); client.validate_frame(boundary_after, require_event_free=False)
            frames.append({'day': (boundary_after['date_raw'] - first['date_raw']) / 24, 'snapshot': boundary_after, 'event_boundary': value['event_boundary']})
            reason = 'event_boundary'; break  # No retry, event selection, forced reply or extra day.
        require(value.get('requested_interval_complete') is True, 'Original natural day did not complete')
        after = object_field(value, 'after')
        require(after.get('date_raw') == first['date_raw'] + 24 * (index + 1) and after.get('paused') is True,
                'Actual native daily pause is not the exact next24 hours')
        reference = row.get('current_toast_capture'); checked_capture_pin(reference); captures.append(json_object(reference))
        frames.append({'day': index + 1, 'snapshot': after})
        capture = json_object(read_json(file_pin(reference)['path']))
        if _ndd_candidate(capture):
            reason = 'visible_candidate'; break  # Source qualification happens only after terminal SAVE/readback.
    final_frame = client.snapshot(require_event_free=False); client.validate_frame(final_frame, require_event_free=False)
    require(final_frame.get('date_raw') == frames[-1]['snapshot']['date_raw'] and final_frame.get('paused') is True,
            'No unrecorded natural day is accepted between last query/boundary and terminal Root phase')
    final = root_phase(client, context, NEWS_DELIVERY_DAILY_PHASES[1][0], list(NEWS_DELIVERY_DAILY_PHASES[1][2]), final_frame, compiled)
    phases[NEWS_DELIVERY_DAILY_PHASES[1][0]] = final
    review = _ndd_review(json_object(context), json_object(compiled), json_object(phases), captures, frames, reason)
    facts = {'schema': 'ck3-mod-acceptance-product-case-facts-v1', 'run_id': context['run_id'],
        'product': context['product'], 'case': context['case'], 'compiled_contract': binding,
        'acceptance_scope': config['acceptance_scope'], 'business_contract_applicable': False,
        'load_boundary_qualified': True, 'actual_native_frames': frames, 'actual_process': getattr(client, '_process', None),
        'enabled_mods': enabled, 'product_outer': pin(profile / 'mod/product.mod'),
        'product_inner': pin(profile / 'mod-content/product/descriptor.mod'),
        'marker_observation': marker_observation(client.log_bytes(), compiled), 'root_phases': phases,
        'news_daily_captures': captures, 'news_daily_stop_reason': reason, **review}
    client.checkpoint('generic-product-case-result', facts)
    return facts


