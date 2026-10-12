"""Root-only candidate: python helper.py CONFIG EXPECTED_CONFIG_SHA256.
Schema xar.native.link.rc/v1. One explicit new l0003 link, with exact resource
tool inputs available in PATH. Never compile, archive, LIST, retry an old job,
disable MANIFEST, or infer auxiliary-tool invocation. Original files stay intact.
Operational imports are from exact hash-bound frozen Source14/13 source bytes.
"""
from __future__ import annotations
import argparse
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import types

SOURCE14_SHA = '438290cf8544db4f03d4242d2e7d475f3c8e97bef820376d7bb1653d007a2fdb'
SOURCE13_SHA = '24a592d1f78eb31c474421d9e9e2bdff2415155f84add95f9049272e1e82a5c2'
AUX_SHA = '293bad86c9a920296157b4cef9fca19f34ebaa087d6144c05852a87ba98536cc'

def need(ok, why):
    if not ok:
        raise RuntimeError(why)

def pairs(items):
    result = {}
    for k, v in items:
        need(k not in result, 'duplicate JSON key')
        result[k] = v
    return result

def finite_float(value):
    result = float(value)
    need(math.isfinite(result), 'nonfinite JSON number')
    return result

def invalid_constant(value):
    raise RuntimeError('nonfinite JSON constant: ' + value)

def bounded_ref(ref, limit=33554432):
    p = Path(ref['path'])
    need(p.is_absolute(), 'absolute input')
    with p.open('rb') as stream:
        raw = stream.read(limit + 1)
    need(len(raw) <= limit and hashlib.sha256(raw).hexdigest() == ref['sha256'], 'bound immutable input bytes')
    return raw

def read_json(ref, limit=33554432):
    return json.loads(bounded_ref(ref, limit).decode('utf-8-sig'), object_pairs_hook=pairs,
                      parse_float=finite_float, parse_constant=invalid_constant)

def source14(ref):
    need(ref['sha256'] == SOURCE14_SHA, 'exact frozen Source14 module')
    raw = bounded_ref(ref, 65536)
    module = types.ModuleType('_root_frozen_source14_link')
    module.__file__ = ref['path']
    exec(compile(raw, ref['path'], 'exec', dont_inherit=True), module.__dict__)
    return module

def actual_success(f, job, policy):
    base = Path(job['job_root']) / 'stage'
    req_ref, res_ref = f.file_ref(base.with_suffix('.request.json')), f.file_ref(base.with_suffix('.result.json'))
    req, res = read_json(req_ref, 2097152), read_json(res_ref, 2097152)
    env = f.environment(job, policy)
    for body in (req, res):
        need(body['job_id'] == job['job_id'] and body['argv'] == job['argv'] and body['cwd'] == job['cwd'] and
             body['shell'] is False and body['automatic_retry'] is False and body['environment_settings'] == job['environment'] and
             body['actual_environment'] == env and body['timeout_seconds'] == job['timeout_seconds'], 'actual successful old stage binding')
    need(req['status'] == 'NOT_STARTED' and req['process_started'] is False and req['pid'] is None, 'original old request')
    need(res['status'] == 'PROCESS_EXIT_OBSERVED' and res['process_started'] is True and res['exit_observed'] is True and
         type(res['exit_code']) is int and res['exit_code'] == 0 and res['direct_child_reaped'] is True and
         type(res['pid']) is int and res['pid'] > 0 and res['descendant_cleanup_proven'] is False, 'original stage actual exit0/reaped')
    return f.actual_stage(job, base)

def old_archive(f, manifest, mf_sha, policy, objects, hashes):
    need(len(manifest['archives']) == 1, 'one original closure02 archive')
    a = manifest['archives'][0]
    i = a['inspection_job']
    need(a['job_id'] == 'a0002' and i['job_id'] == 'i0002' and a['kind'] == 'archive' and
         i['kind'] == 'archive_inspection' and i['archive_job_id'] == a['job_id'], 'original successful archive/LIST owners')
    f.inputs(a, mf_sha)
    av_ref = f.file_ref(Path(a['job_root']) / 'stage.verified.json')
    iv_ref = f.file_ref(Path(i['job_root']) / 'stage.verified.json')
    av, iv = read_json(av_ref, 4194304), read_json(iv_ref, 4194304)
    need(av['status'] == 'STAGE_VERIFIED' and av['job_id'] == a['job_id'] and av['actual_stage'] == actual_success(f, a, policy), 'original actual archive verified')
    need(av['output_ref'] == f.file_ref(a['output']) and iv['library'] == av['output_ref'], 'original library bytes')
    expected_inputs = [{'path': str(f.abs_path(p)), 'sha256': hashes[f.key(p)]} for p in a['inputs']]
    need(a['inputs'] == [objects[n] for n in a['member_indices']] and av['ordered_inputs'] == expected_inputs, 'actual old archive object inputs')
    need(i['inputs'] == [a['output']] and i['expected_member_indices'] == a['member_indices'] and
         i['expected_member_basenames'] == [Path(objects[n]).name for n in a['member_indices']], 'original LIST owner expectations')
    need(len(i['argv']) == 4 and i['argv'][1].upper() == '/NOLOGO' and i['argv'][2].upper() == '/LIST' and
         f.key(i['argv'][3]) == f.key(a['output']) and f.key(i['argv'][0]) == f.key(a['argv'][0]) and
         i['tool_sha256'] == a['tool_sha256'], 'actual old bounded LIST recipe')
    need(iv['archive_job_id'] == a['job_id'] and iv['actual_inspection'] == actual_success(f, i, policy) and
         iv['stdout_ref'] == f.file_ref(Path(i['job_root']) / 'stage.stdout') and
         iv['stderr_ref'] == f.file_ref(Path(i['job_root']) / 'stage.stderr'), 'actual old LIST raw refs')
    names = {Path(objects[n]).name.casefold(): n for n in a['member_indices']}
    need(len(names) == len(a['member_indices']) == 597, 'unique exact597 old archive owners')
    members = []
    for line in Path(iv['stdout_ref']['path']).read_text(encoding=i['stdout_encoding'], errors='strict').splitlines():
        value = line.strip()
        if value:
            name = Path(value).name.casefold()
            need(name in names, 'unknown old LIST member/banner')
            members.append({'actual_member': value, 'index': names[name], 'object': objects[names[name]]})
    need([v['index'] for v in members] == a['member_indices'] and iv['ordered_members'] == members, 'actual old ordered597 LIST')
    need('verified_ref' not in iv, 'old LIST body never rewritten')
    iv['verified_ref'] = iv_ref
    need(av['actual_members'] == iv, 'old archive references actual LIST evidence')
    hashes[f.key(a['output'])] = av['output_ref']['sha256']
    return av

def failed_link(f, cfg, old, policy):
    result = read_json(cfg['closure02_result_stop_reference'], 2097152)
    thin = read_json(cfg['closure02_stop_thin_reference'], 2097152)
    l = old['link']
    need(l['job_id'] == 'l0002' and result['status'] == 'STOPPED_OR_UNKNOWN_NO_RETRY', 'original closure02 really stopped at link')
    base = Path(l['job_root']) / 'stage'
    req, res = (read_json(f.file_ref(base.with_suffix(s)), 2097152) for s in ('.request.json', '.result.json'))
    for body in (req, res):
        need(body['job_id'] == l['job_id'] and body['argv'] == l['argv'] and body['cwd'] == l['cwd'] and
             body['environment_settings'] == l['environment'] and body['actual_environment'] == f.environment(l, policy) and
             body['shell'] is False and body['automatic_retry'] is False, 'old failed link raw binding')
    need(res['status'] == 'FAILED_OR_TIMEOUT_CHILD_OBSERVED' and res['process_started'] is True and res['exit_observed'] is True and
         type(res['exit_code']) is int and res['exit_code'] == 1158 and res['direct_child_reaped'] is True and
         type(res['pid']) is int and res['pid'] > 0 and res['descendant_cleanup_proven'] is False, 'actual old LNK1158 exit/reaped')
    need(not base.with_suffix('.verified.json').exists(), 'old link has no success receipt')
    stdout = base.with_suffix('.stdout').read_text(encoding=cfg['old_link_stdout_encoding'], errors='strict')
    need('LNK1158' in stdout and 'rc.exe' in stdout, 'old actual missing resource compiler diagnostic')
    need(all(pointer(thin, v['pointer']) == v['value'] for v in cfg.get('closure02_thin_assertions', [])), 'actual old thin assertions')
    return result

def pointer(body, path):
    need(isinstance(path, str) and path.startswith('/'), 'exact JSON pointer')
    for item in path[1:].split('/'):
        item = item.replace('~1', '/').replace('~0', '~')
        body = body[int(item)] if isinstance(body, list) else body[item]
    return body

def resource_inputs(f, cfg):
    ref = cfg['newauxiliary_tools_reference']
    need(ref['sha256'] == AUX_SHA and ref['bytes'] == 1856, 'exact Root installed resource tool pin metadata')
    need(Path(ref['path']).stat().st_size == ref['bytes'], 'resource pin metadata size')
    body = read_json(ref, 8192)
    need(body['status'] == 'ROOT_INSTALLED_EXACT_LINK_RESOURCE_INPUTS_PINNED_NO_TOOL_EXECUTION', 'actual resource input pin status')
    roles = [v['role'] for v in body['tools']]
    need(len(roles) == 4 and set(roles) == {'resource_compiler', 'resource_compiler_library', 'manifest_tool_available', 'resource_converter_available'}, 'exact four resource roles')
    directory = body['explicit_resource_tool_directory_to_prepend_to_new_link_PATH']
    need(Path(directory).is_absolute() and Path(directory).is_dir(), 'explicit existing resource tool directory')
    for tool in body['tools']:
        f.clock()
        need(tool['invocation_observed'] is False and Path(tool['path']).stat().st_size == tool['bytes'] and
             f.sha(tool['path']) == tool['sha256'], 'actual resource input file bytes, no invocation inference')
        if tool['role'] == 'resource_compiler':
            need(Path(tool['path']).name.casefold() == 'rc.exe' and f.key(Path(tool['path']).parent) == f.key(directory), 'exact rc PATH directory')
    return directory, body

def equivalent_link(f, cfg, old, new, directory):
    need(new['compile_jobs'] == old['compile_jobs'] and new['archives'] == old['archives'] and
         new['retained_objects'] == old['retained_objects'] == [] and new['mode'] == old['mode'] == 'rebuild917', 'no compiler/archive/LIST input changes')
    for key in ('source_head', 'sdk_freeze_receipt', 'abi_inputs', 'selected_owner_lineage', 'selected_owner_map', 'output_root'):
        need(new[key] == old[key], 'original source/owner identity: ' + key)
    before, after = old['link'], new['link']
    need(after['kind'] == before['kind'] == 'link' and after['job_id'] == 'l0003' and
         after['direct_object_indices'] == before['direct_object_indices'] and
         f.key(after['argv'][0]) == f.key(before['argv'][0]) and after['tool_sha256'] == before['tool_sha256'], 'only explicit new link job')
    old_tokens, old_roles = f.expanded(before, cfg['closure02_manifest_reference']['sha256'])
    tokens, roles = f.expanded(after, cfg['derived_manifest_ref']['sha256'])
    permitted = set()
    for flag in ('/OUT:', '/PDB:', '/IMPLIB:', '/ILK:', '/MAP:'):
        if f.option_present(old_tokens, flag):
            x, y = f.opt(old_tokens, flag), f.opt(tokens, flag)
            need(f.inside(x, [before['job_root']]) and f.inside(y, [after['job_root']]), 'private new link output transformation')
            permitted.add((x, y))
    substitutions = [(v['original'], v['final']) for v in cfg['authorized_link_path_substitutions']]
    need(substitutions and len(set(substitutions)) == len(substitutions) and set(substitutions).issubset(permitted), 'only exact link private path transformations')
    expected = []
    for token in old_tokens:
        for x, y in substitutions:
            token = token.replace(x, y)
        expected.append(token)
    need(tokens == expected and roles == old_roles, 'preserve actual link options/order/roles, including MANIFEST')
    env_old, env_new = before['environment'], after['environment']
    need(set(env_old) == set(env_new), 'no additional ambient environment keys')
    for key in env_old:
        if key == 'PATH':
            need(env_old[key]['state'] == env_new[key]['state'] == 'value' and
                 env_new[key]['value'] == directory + ';' + env_old[key]['value'], 'only exact rc directory PATH prepend')
        elif key in ('TMP', 'TEMP'):
            need(env_new[key]['state'] == 'value' and f.key(env_new[key]['value']) == f.key(after[key.lower()]), 'only new private link temps')
        else:
            need(env_new[key] == env_old[key], 'unchanged explicit old link environment')
    return after

def run(path, digest):
    cfg = read_json({'path': path, 'sha256': digest}, 2097152)
    need(cfg['schema'] == 'xar.native.link.rc/v1', 'new link config schema')
    prior_helper = source14(cfg['frozen_source14_reference'])
    need(cfg['frozen_producer_ref']['sha256'] == SOURCE13_SHA, 'exact Source13 stage module')
    f = prior_helper.frozen_module(cfg['frozen_producer_ref'])
    new = read_json(cfg['derived_manifest_ref'])
    new_sha = cfg['derived_manifest_ref']['sha256']
    a = f.receipt(new['build_admission'], 'ADMITTED', new_sha)
    f.DEADLINE = datetime.fromisoformat(a['deadline_utc'])
    need(f.DEADLINE.tzinfo is not None, 'explicit unchanged closure deadline')
    f.clock()
    old = read_json(cfg['closure02_manifest_reference'])
    old_sha = cfg['closure02_manifest_reference']['sha256']
    old_a = f.receipt(old['build_admission'], 'ADMITTED', old_sha)
    need(a['deadline_utc'] == old_a['deadline_utc'] and a['max_output_bytes'] == old_a['max_output_bytes'] and
         a['volume_free_min_bytes'] == old_a['volume_free_min_bytes'] and
         a['checkpoint_reserve_bytes'] == old_a['checkpoint_reserve_bytes'] and
         a['min_free_memory_bytes'] == old_a['min_free_memory_bytes'], 'original deadline/output/checkpoint/volume/memory floors')
    for field in ('max_output_bytes', 'checkpoint_reserve_bytes', 'min_free_memory_bytes'):
        f.positive(a[field], 'explicit positive closure resource reservation')
    original_cfg = read_json(cfg['closure02_helper_config_reference'], 2097152)
    closure_request_ref = f.file_ref(Path(cfg['closure02_result_stop_reference']['path']).parent / 'CLOSURE-REQUEST.json')
    closure_request = read_json(closure_request_ref, 2097152)
    need(closure_request['derived_manifest_ref'] == cfg['closure02_manifest_reference'] and
         f.key(closure_request['config_ref']['path']) == f.key(cfg['closure02_helper_config_reference']['path']) and
         closure_request['config_ref']['sha256'] == cfg['closure02_helper_config_reference']['sha256'], 'actual original closure request manifest/config binding')
    need(original_cfg['derived_manifest_ref'] == cfg['closure02_manifest_reference'] and
         original_cfg['frozen_producer_ref'] == cfg['frozen_producer_ref'], 'original successful archive closure inputs')
    original = read_json(original_cfg['original_manifest_reference'])
    need(all(closure_request[k] == original_cfg[k] for k in ('original_manifest_reference', 'original_result_stop_reference', 'original_scheduler_reference')),
         'actual original closure request compiler/stop/scheduler refs')
    original_sha = original_cfg['original_manifest_reference']['sha256']
    scheduler = read_json(original_cfg['original_scheduler_reference'], 2097152)
    prior_helper.original_stop(f, original_cfg, original, scheduler)
    need(original['compile_jobs'] == old['compile_jobs'] and original['retained_objects'] == [], 'original unchanged917 compiler jobs')
    old_policy = f.receipt(old['environment_policy'], 'ADMITTED_NEW_ENVIRONMENT', old_sha)
    failed_link(f, cfg, old, old_policy)
    directory, tool_pins = resource_inputs(f, cfg)
    link = equivalent_link(f, cfg, old, new, directory)
    build = f.abs_path(new['output_root'])
    preparation, metadata = f.abs_path(cfg['preparation_root']), f.abs_path(cfg['metadata_root'])
    need(f.key(preparation) == f.key(build / 'closure03-preparation') and f.key(metadata) == f.key(build / 'closure03') and
         preparation.is_dir() and not metadata.exists(), 'exact separate preparation/results namespaces')
    need(f.inside(cfg['derived_manifest_ref']['path'], [preparation]), 'new manifest kept out of full old RENDER')
    need(a['scope'] == 'native-link-closure' and a['allowed_job_ids'] == ['l0003'] and a['zero_compiler_invocations'] is True and
         a['zero_archive_invocations'] is True and a['zero_inspection_invocations'] is True and
         a['exclusive_output_owner_verified'] is True and a['original_closure_manifest_sha256'] == old_sha and
         a['original_closure_result_stop_sha256'] == cfg['closure02_result_stop_reference']['sha256'],
         'Root explicit single new link admission')
    need(f.key(a['approved_output_root']) == f.key(build) and f.key(a['metadata_root']) == f.key(metadata), 'admitted whole existing BUILD89')
    sdk, header, header_sha, freeze_sha, frozen = f.source_admission(new, new_sha, new['source_head'])
    original_policy = f.receipt(original['environment_policy'], 'ADMITTED_NEW_ENVIRONMENT', original_sha)
    context = {'source_head': new['source_head'], 'sdk_source_root': str(sdk), 'header_head': new['source_head'],
               'abi_inputs': new['abi_inputs'], 'sdk_freeze_sha256': freeze_sha, 'compile_configuration_refs': original_policy['compile_configuration_refs']}
    need(new['abi_inputs'] == frozen['abi_inputs'] and a['source_head'] == context['source_head'] and
         a['sdk_freeze_sha256'] == freeze_sha, 'original unchanged frozen source/ABI input')
    f.selected_owners(new, new_sha, new['compile_jobs'], [])
    policy = f.receipt(new['environment_policy'], 'ADMITTED_NEW_ENVIRONMENT', new_sha)
    closure = f.receipt(new['archive_link_policy'], 'ADMITTED_EXACT_ARCHIVE_LINK_CLOSURE', new_sha)
    need(closure['source_head'] == new['source_head'] and closure['selected_inputs_complete'] is True, 'new explicit link inputs qualification')
    f.parallel_admission(a)
    f.budget(a, build)
    verified, objects, hashes = prior_helper.verify_compilers(f, original, original_sha, context, header, header_sha, original_policy)
    archive = old_archive(f, old, old_sha, old_policy, objects, hashes)
    old_link_base = Path(old['link']['job_root']) / 'stage'
    origin_refs = {'original_compile_manifest_reference': original_cfg['original_manifest_reference'],
                   'original_result_stop_reference': original_cfg['original_result_stop_reference'],
                   'original_scheduler_reference': original_cfg['original_scheduler_reference'],
                   'closure02_manifest_reference': cfg['closure02_manifest_reference'],
                   'closure02_helper_config_reference': cfg['closure02_helper_config_reference'],
                   'closure02_result_stop_reference': cfg['closure02_result_stop_reference'],
                   'closure02_stop_thin_reference': cfg['closure02_stop_thin_reference'],
                   'closure02_request_reference': closure_request_ref,
                   'failed_link_request_reference': f.file_ref(old_link_base.with_suffix('.request.json')),
                   'failed_link_result_reference': f.file_ref(old_link_base.with_suffix('.result.json')),
                   'failed_link_stdout_reference': f.file_ref(old_link_base.with_suffix('.stdout')),
                   'failed_link_stderr_reference': f.file_ref(old_link_base.with_suffix('.stderr')),
                   'archive_verified_reference': f.file_ref(Path(old['archives'][0]['job_root']) / 'stage.verified.json'),
                   'inspection_verified_reference': archive['actual_members']['verified_ref'],
                   'actual_archive_reference': archive['output_ref'],
                   'actual_list_stdout_reference': archive['actual_members']['stdout_ref'],
                   'actual_list_stderr_reference': archive['actual_members']['stderr_ref']}
    f.private_scopes([link])
    f.common(link, build)
    env = f.environment(link, policy)
    original_roots = [Path(j['job_root']).resolve() for j in old['compile_jobs'] + old['archives'] +
                      [j['inspection_job'] for j in old['archives']] + [old['link']]]
    need(all(not Path(link['job_root']).resolve().is_relative_to(p) and not p.is_relative_to(Path(link['job_root']).resolve())
             for p in original_roots), 'l0003 never overwrites an original namespace')
    need(not f.inside(link['job_root'], [preparation, metadata]) and not f.inside(metadata, [link['job_root']]), 'link/preparation/results isolated')
    f.inputs(link, new_sha)
    need(link['responsefiles'] and any(v.startswith('@') for v in link['argv']), 'explicit new compact link RSP')
    metadata.mkdir()
    f.write(metadata / 'LINK-REQUEST.json', {'schema': cfg['schema'], 'config_ref': {'path': path, 'sha256': digest},
            'derived_manifest_ref': cfg['derived_manifest_ref'], 'newauxiliary_tools_reference': cfg['newauxiliary_tools_reference'],
            'actual_compiler_invocations_in_this_closure': 0, 'actual_archive_invocations_in_this_closure': 0,
            'actual_inspection_invocations_in_this_closure': 0})
    stage_attempted = False
    try:
        expected = {f.key(v['path']): v['sha256'] for v in link['immutable_inputs']}
        selected = []
        for item in link['inputs']:
            observed = f.sha(item)
            need(observed == (hashes[f.key(item)] if f.key(item) in hashes else expected[f.key(item)]), 'actual unchanged selected link input bytes')
            selected.append({'path': str(f.abs_path(item)), 'sha256': observed})
        resource_inputs(f, cfg)
        cap = f.budget(a, build, next_job=link)
        stage_attempted = True
        base = f.stage(link, f.Dispatch(), cap, env, a['parallel_policy']['cleanup_wait_seconds'])
        resource_inputs(f, cfg)
        actual = f.actual_stage(link, base)
        result = {'status': 'STAGE_VERIFIED', 'job_id': link['job_id'], 'actual_stage': actual,
                  'output_ref': f.file_ref(link['output']), 'ordered_inputs': selected}
        f.write(base.with_suffix('.verified.json'), result)
        tokens, roles = f.expanded(link, new_sha)
        link_inputs = {'actual_stage': actual, 'expanded_tokens': tokens, 'token_roles': roles, 'ordered_inputs': selected}
        link_actual = dict(result, dll_path=link['output'], dll_sha256=result['output_ref']['sha256'])
        need(f.sha(cfg['derived_manifest_ref']['path']) == new_sha and f.sha(cfg['closure02_manifest_reference']['path']) == old_sha,
             'manifest source bytes unchanged')
        refs, fresh = f.actual_packets(metadata, new, context, new['compile_jobs'], [], verified, {}, [archive], link_actual, link_inputs)
        need(fresh is True, 'actual original whole917 source identity')
        f.budget(a, build)
        f.write(metadata / 'RESULT.json', {'status': 'BUILD_OUTPUTS_VERIFIED_NO_RUNTIME_CREDIT', 'manifest_sha256': new_sha,
                'source_head': new['source_head'], 'owners': 917, 'mode': 'rebuild917', 'actual_compile_verified': 917,
                'actual_new_dependency_outputs': 917, 'actual_compiler_invocations_in_this_closure': 0,
                'actual_dependency_outputs_created_in_this_closure': 0, 'actual_archive_invocations_in_this_closure': 0,
                'actual_inspection_invocations_in_this_closure': 0, 'individually_qualified_retained': 0,
                'actual_link_invocations_in_this_closure': 1,
                'all_cpp_at_new_head': True, 'all_cpp_compiled_at_declared_source_head': True, 'actual_packets': refs,
                **origin_refs,
                'newauxiliary_tools_reference': cfg['newauxiliary_tools_reference'], 'auxiliary_tools_invocation_inferred': False,
                'Game_or_SDK_started': False, 'automatic_retry': False, 'descendant_cleanup_proven': False})
    except BaseException as original_error:
        link_count = 0 if not stage_attempted else None
        if stage_attempted:
            try:
                observed = read_json(f.file_ref(Path(link['job_root']) / 'stage.result.json'), 2097152)
                need(observed['job_id'] == link['job_id'] and observed['argv'] == link['argv'] and
                     type(observed['process_started']) is bool, 'actual new link invocation evidence')
                link_count = int(observed['process_started'])
            except BaseException as diagnostic:
                original_error.add_note('Link invocation evidence unproved: ' + type(diagnostic).__name__ + ': ' + str(diagnostic))
        f.failure_receipt(metadata / 'RESULT.json', {'status': 'STOPPED_OR_UNKNOWN_NO_RETRY', **f.error_data(original_error),
                'actual_compiler_invocations_in_this_closure': 0, 'actual_dependency_outputs_created_in_this_closure': 0,
                'actual_archive_invocations_in_this_closure': 0, 'actual_inspection_invocations_in_this_closure': 0,
                'actual_link_invocations_in_this_closure': link_count,
                **origin_refs,
                'newauxiliary_tools_reference': cfg['newauxiliary_tools_reference'], 'original_files_retained': True,
                'descendant_cleanup_proven': False}, original_error)
        raise

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config')
    parser.add_argument('expected_config_sha256')
    args = parser.parse_args()
    try:
        run(args.config, args.expected_config_sha256)
    except BaseException as error:
        print(json.dumps({'status': 'STOPPED_OR_UNKNOWN_NO_RETRY', 'error_type': type(error).__name__, 'error': str(error),
                          'diagnostics': getattr(error, '__notes__', []), 'automatic_retry': False}))
        return 2
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
