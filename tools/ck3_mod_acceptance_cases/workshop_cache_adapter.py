"""One published Workshop cache boundary through the shared menu-only runtime.

The SDK download is an existing external operation. This adapter verifies its
receipt and exact formal cache, prepares only ordinary profile inputs, and
records combined managed-profile/main-menu evidence. It owns no process,
native command, campaign, screen, allocator or normal-exit implementation.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path, PurePosixPath
import re

from ck3_mod_acceptance_prepare import CONFIG_NAMES, materialize_product_profile
from ck3_mod_acceptance_prepare import pin, require, write_json


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def checked_json(row):
    actual = pin(row['path'])
    require(actual['bytes'] == row['bytes'] and actual['sha256'] == row['sha256'].lower(),
            'Frozen Workshop input changed: ' + actual['path'])
    return read_json(actual['path']), actual


def canonical_product(context):
    inventory = read_json(context['canonical_products_path'])
    require(inventory['schema'] == 'ck3.workshop-products.v1', 'Canonical Workshop registry required')
    matches = [row for row in inventory['products'] if row['key'] == context['product']]
    require(len(matches) == 1, 'Unique canonical player product required')
    product = matches[0]
    selected = context['product_spec']
    require(product['directory'] == selected['directory'] and
            product['workshop_item_id'] == selected['workshop_item_id'], 'Selected product differs from canonical registry')
    item = product['workshop_item_id']
    require(isinstance(item, str) and re.fullmatch(r'[1-9][0-9]*', item),
            'Published canonical Workshop item required; development-only product has no cache case')
    forbidden = inventory['forbidden_upstream_target_ids'] + product['forbidden_upstream_ids']
    require(item not in forbidden, 'Upstream Workshop target forbidden')
    require(str(inventory['consumer_app_id']) == '1158310', 'Canonical CK3 consumer app required')
    return product, item


def validate_contract(context):
    contract = context['case_contract']
    require(context['case'] == 'workshop_cache' and contract['schema'] == 'ck3-mod-acceptance-workshop-cache-v1',
            'Shared Workshop cache case required')
    require(contract['checks'] == ['sdk_download_exact_formal', 'game_cache_mounted_and_normal0'] and
            contract['business_contract_applicable'] is False and
            contract['independent_engine_vfs_path_readback_required'] is False,
            'Cache scope is exact files plus combined actual menu load and original normal0')
    canonical_product(context)


def validate_download(value, item, cache):
    # Existing call_tool envelopes preserve the original structured SDK result.
    if 'tool' in value:
        require(value.get('tool') == 'workshop_native_download' and value.get('ok') is True,
                'Actual native SDK download result required')
        value = value['result']
    require(value.get('ok') is True and value.get('status') == 'complete' and value.get('started') is True and
            value.get('error') is None, 'Native download did not complete')
    require(str(value.get('app_id')) == '1158310' and str(value.get('item_id')) == item,
            'Native SDK app/item differs from canonical product')
    callback = value.get('callback', {})
    require(str(callback.get('app_id')) == '1158310' and str(callback.get('item_id')) == item and
            type(callback.get('result')) is int and callback['result'] == 1, 'Actual SDK success callback missing')
    require(Path(value['install_info']['path']).resolve() == cache, 'SDK installed cache path differs')
    flags = value.get('state_flags', {})
    require(flags.get('installed') is True and all(flags.get(key) is False for key in
            ('needs_update', 'downloading', 'download_pending')), 'SDK cache installation still pending')
    if 'worker_exit_code' in value:
        require(value['worker_exit_code'] == 0, 'Original SDK worker failed')
    return value


def validate_manifest(manifest, item):
    require(manifest.get('format_version') == 1 and str(manifest.get('workshop_item_id')) == item,
            'Exact formal manifest must identify canonical item')
    require(isinstance(manifest.get('git_tag'), str) and manifest['git_tag'] and
            re.fullmatch(r'[0-9a-fA-F]{40}', str(manifest.get('git_sha'))), 'Tagged formal release identity required')
    entries = manifest.get('files')
    require(isinstance(entries, list) and entries, 'Formal file inventory required')
    paths = []
    for row in entries:
        relative = row.get('path')
        require(isinstance(relative, str) and relative and '\\' not in relative and ':' not in relative,
                'Formal paths must be safe relative POSIX paths')
        path = PurePosixPath(relative)
        require(not path.is_absolute() and '..' not in path.parts and path.as_posix() == relative,
                'Formal path escaped cache')
        require(type(row.get('size')) is int and row['size'] >= 0 and
                re.fullmatch(r'[0-9a-f]{64}', str(row.get('sha256'))), 'Formal file size/SHA missing')
        paths.append(relative)
    require(len(paths) == len(set(paths)) and 'descriptor.mod' in paths, 'Formal inventory duplicate or descriptor absent')
    return manifest


def prepare_case(context):
    validate_contract(context)
    _, item = canonical_product(context)
    inputs = context['case_inputs']
    require(set(inputs) == {'cache_path', 'formal_manifest', 'native_download_receipt', 'plain_configuration'},
            'Cache input is existing downloaded cache, exact formal manifest, actual SDK receipt and four plain configs')
    cache = Path(inputs['cache_path']).resolve()
    require(cache.is_dir() and tuple(part.lower() for part in cache.parts[-4:]) == ('workshop', 'content', '1158310', item),
            'Actual published Steam Workshop cache leaf required')
    require(not Path(inputs['cache_path']).is_symlink(), 'Cache leaf symlink forbidden')
    require(all(not Path(context[key]).resolve().is_relative_to(cache) for key in ('state_dir', 'output')),
            'Preparation output must remain outside actual SDK cache')
    download, download_pin = checked_json(inputs['native_download_receipt'])
    validate_download(download, item, cache)
    manifest, manifest_pin = checked_json(inputs['formal_manifest'])
    validate_manifest(manifest, item)
    # Reuse the existing exact-byte verifier and its sole descriptor exception.
    # Its formal ZIP/product-specific wrapper is deliberately not called here.
    from verify_zhongguo_workshop_cache import _verify_cache
    descriptor = (cache / 'descriptor.mod').read_bytes()
    policy = 'launcher-injected' if b'remote_file_id' in descriptor else 'canonical'
    records, descriptor_state = _verify_cache(cache, manifest, policy)
    cache_files = [{'path': str(cache / relative), 'bytes': row['size'], 'sha256': row['sha256']}
                   for relative, row in records.items()]
    prepared_context = dict(context, workshop_cache_item_id=item)
    profile = materialize_product_profile(prepared_context, cache, inputs['plain_configuration'],
                                          workshop_cache_files=cache_files)
    require(set(profile['files']) == set(CONFIG_NAMES) | {'mod/product.mod', 'dlc_load.json'},
            'Cache profile must contain only six ordinary input files')
    output = Path(context['output'])
    strict = output / 'workshop-cache-exact-formal.json'
    write_json(strict, {'schema': 'ck3-workshop-cache-shared-exact-formal-v1', 'result': 'EXACT_FORMAL_CACHE',
        'product': context['product'], 'item_id': item, 'cache_path': str(cache),
        'formal_manifest': manifest_pin, 'native_download_receipt': download_pin,
        'formal_git_tag': manifest['git_tag'], 'formal_git_sha': manifest['git_sha'],
        'descriptor': descriptor_state, 'file_count': len(records), 'files': cache_files})
    preparation = output / 'profile-preparation.json'
    write_json(preparation, {'schema': 'ck3-mod-acceptance-prepared-workshop-cache-v1',
        'runtime_status': 'NOT_RUN', 'state_dir': profile['state_dir'], 'profile_dir': profile['profile'],
        'files': profile['files'], 'cache_path': str(cache), 'workshop_item_id': item,
        'exact_cache': pin(strict), 'product_inventory': profile['product_inventory'],
        'fixture_mounted': False, 'cache_content_copied': False, 'campaign_started': False,
        'business_acceptance': 'NOT_ASSESSED'})
    startup_path = Path(profile['state_dir']) / 'preparation.json'
    write_json(startup_path, {'schema': 'ck3-mod-acceptance-profile-startup-evidence-v1',
        'profile_dir': str(Path(profile['profile']).resolve()), 'profile_files': list(profile['files']),
        'profile_input_sha256': {name: row['sha256'] for name, row in profile['files'].items()},
        'preparation': pin(preparation), 'runtime_status': 'NOT_RUN'})
    initial = output / 'initial-plan.json'
    write_json(initial, {'steps': []})
    return {'startup': {'mode': 'workshop_cache', 'state_dir': profile['state_dir']},
        'initial_plan': pin(initial), 'profile_preparation': pin(preparation),
        'startup_evidence': pin(startup_path), 'exact_cache': pin(strict), 'files': profile['files'],
        'business_contract_applicable': False, 'runtime_status': 'NOT_RUN',
        'business_pass': False, 'product_release_pass': False}


def wmi_epoch(value):
    require(isinstance(value, str) and re.fullmatch(r'\d{14}\.\d{6}[+-]\d{3}', value),
            'Actual original WMI process creation timestamp required')
    offset = int(value[-3:]) * (1 if value[-4] == '+' else -1)
    return datetime.strptime(value[:-4], '%Y%m%d%H%M%S.%f').replace(
        tzinfo=timezone(timedelta(minutes=offset))).timestamp()


def combined_menu_observation(context, report, process):
    require(isinstance(process, dict) and process.get('retained_synchronize_query_handle_acquired') is True,
            'Original client retained process identity required')
    launch = report.get('frontend_mod_load_launch', {})
    observed = report.get('frontend_mod_load_observation', {})
    profile_binding = report.get('frontend_mod_load_profile', {})
    profile = (Path(context['state_dir']) / 'profile').resolve()
    startup_path = Path(context['state_dir']) / 'preparation.json'
    startup_pin = pin(startup_path)
    startup = read_json(startup_path)
    require(launch.get('status') == 'ACTUAL_SINGLE_MENU_LAUNCH_RECORDED' and
            launch.get('pid') == process['pid'] and
            abs(wmi_epoch(launch.get('ck3_creation_date')) - process['create_time']) < .01,
            'Actual menu launch differs from retained process identity')
    require(Path(launch['profile_dir']).resolve() == profile and
            launch.get('continue_last_save') is False and launch.get('load_save_name') is None,
            'Actual menu launch profile or route differs')
    command = launch.get('actual_command')
    require(isinstance(command, list) and command, 'Actual launch command missing')
    userdirs = [arg.split('=', 1)[1] for arg in command if arg.startswith('-userdir=')]
    require(len(userdirs) == 1 and Path(userdirs[0].strip('"')).resolve() == profile and
            not any(arg.lower().startswith(('-continuelastsave', '-loadsave')) for arg in command),
            'Actual launch must use only current menu profile, with no campaign restore')
    require(Path(profile_binding['profile_dir']).resolve() == profile and
            Path(profile_binding['preparation_path']).resolve() == startup_path.resolve() and
            profile_binding.get('preparation_sha256') == startup_pin['sha256'] and
            profile_binding.get('preparation') == startup, 'Actual host profile preparation binding changed')
    preparation, preparation_pin = checked_json(startup['preparation'])
    strict, strict_pin = checked_json(preparation['exact_cache'])
    require(set(startup['profile_files']) == set(CONFIG_NAMES) | {'mod/product.mod', 'dlc_load.json'} and
            startup['profile_input_sha256'] == {name: row['sha256'] for name, row in preparation['files'].items()},
            'Actual menu profile must bind only original six product-only files')
    require(preparation.get('fixture_mounted') is False and preparation.get('cache_content_copied') is False,
            'Cache profile copied or mounted fixture')
    enabled = read_json(profile / 'dlc_load.json')
    require(enabled.get('enabled_mods') == ['mod/product.mod'], 'Only actual cache product descriptor may be enabled')
    outer = profile / 'mod/product.mod'
    require(pin(outer) == preparation['files']['mod/product.mod'] and
            pin(profile / 'dlc_load.json') == preparation['files']['dlc_load.json'], 'Mounted descriptor selection changed')
    text = outer.read_text(encoding='utf-8-sig')
    paths = re.findall(r'^path="([^"]+)"$', text, flags=re.MULTILINE)
    ids = re.findall(r'^remote_file_id="([0-9]+)"$', text, flags=re.MULTILINE)
    _, item = canonical_product(context)
    require(len(paths) == 1 and Path(paths[0]).resolve() == Path(strict['cache_path']).resolve() and
            ids == [item] and strict['item_id'] == item and strict['product'] == context['product'],
            'Actual mounted profile differs from verified canonical cache')
    identity = observed.get('identity', {})
    proof = observed.get('proof', {})
    native = identity.get('native_build', {})
    require(observed.get('status') == context['case_contract']['menu_observation_status'] and
            identity.get('bridge_pid') == process['pid'] and
            type(identity.get('connection_generation')) is int and identity['connection_generation'] > 0 and
            isinstance(identity.get('pipe_name'), str) and identity['pipe_name'] and
            native.get('version') == context['shared_game']['version'] and
            str(native.get('executable_sha256')).lower() == context['shared_game']['exe_sha256'].lower(),
            'Actual native menu identity differs from selected shared game/process')
    require(proof.get('status') == 'CONSISTENT_VISIBLE_FRONTEND_SCOPE' and proof.get('route') == 'main_menu' and
            proof.get('scope_root_name') == 'mainmenu_panel_bottom' and
            type(proof.get('consecutive_consistent_observations')) is int and
            proof['consecutive_consistent_observations'] >= 2 and proof.get('widgets'),
            'Original actual complete visible menu proof missing')
    require(observed.get('campaign_started') is False and observed.get('actions_submitted') == 0,
            'Cache boundary submitted campaign/action')
    return {'load_evidence_kind': context['case_contract']['load_evidence_kind'],
        'combined_managed_cache_profile_and_actual_menu_load': True,
        'independent_engine_vfs_path_readback': 'UNKNOWN', 'actual_cache_mount_proven_by_independent_vfs': False,
        'actual_process': process, 'actual_launch': launch, 'actual_native_menu_observation': observed,
        'actual_host_profile_binding': profile_binding, 'profile_preparation': preparation_pin,
        'startup_evidence': startup_pin, 'exact_cache': strict_pin, 'cache_path': strict['cache_path'],
        'item_id': item, 'file_count': strict['file_count'], 'product_outer': pin(outer)}


def run_case(context, client):
    validate_contract(context)
    client.guard()
    report = client.read_report()
    require(report.get('error') is None, 'Original shared host error preserved')
    facts = combined_menu_observation(context, report, getattr(client, '_process', None))
    facts.update(schema='ck3-mod-acceptance-workshop-cache-case-facts-v1', run_id=context['run_id'],
        product=context['product'], case=context['case'], case_contract_qualified=True,
        gui_contract_qualified=True, business_contract_applicable=False,
        business_pass=False, product_release_pass=False,
        result_boundary='EXACT_FORMAL_CACHE_AND_COMBINED_ACTUAL_MENU_LOAD_PENDING_ORIGINAL_NORMAL0')
    client.checkpoint('workshop-cache-case-result', facts)
    return facts


def verify_case(context):
    validate_contract(context)
    path = Path(context['output']) / 'workshop-cache-case-result.json'
    if not path.is_file():
        return {'case_contract_qualified': False, 'gui_contract_qualified': False,
            'business_contract_applicable': False, 'business_pass': False,
            'product_release_pass': False, 'status': 'NOT_RUN'}
    facts = read_json(path)
    require(facts['run_id'] == context['run_id'] and facts['product'] == context['product'] and
            facts['case'] == context['case'], 'Cache result crossed original run/product/case')
    for key in ('profile_preparation', 'startup_evidence', 'exact_cache', 'product_outer'):
        checked_json(facts[key]) if key != 'product_outer' else require(pin(facts[key]['path']) == facts[key],
                                                                       'Actual cache outer changed')
    combined_menu_observation(context, {'frontend_mod_load_launch': facts['actual_launch'],
        'frontend_mod_load_observation': facts['actual_native_menu_observation'],
        'frontend_mod_load_profile': facts['actual_host_profile_binding']}, facts['actual_process'])
    return {**facts, 'verification_scope': 'workshop_cache_only; existing common normal0 required',
        'business_contract_applicable': False, 'business_pass': False, 'product_release_pass': False}
