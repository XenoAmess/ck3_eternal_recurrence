"""Root-only source candidate: python helper.py CONFIG EXPECTED_CONFIG_SHA256.
Schema xar.native.closure.rsp/v1. Operational imports use only the exact frozen
Source13 bytes. This helper never calls module.run, compile_all or compile_worker.
Original compiler artifacts are read and verified; only the three explicitly
admitted new archive/inspection/link jobs execute. No retry or runtime credit.
New metadata is create-only BUILD89/closure02; original RESULT and jobs stay intact.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import types

PRODUCER_SHA = '24a592d1f78eb31c474421d9e9e2bdff2415155f84add95f9049272e1e82a5c2'
MAX_JSON = 33554432

def need(ok, reason):
    if not ok:
        raise RuntimeError(reason)

def object_pairs(pairs):
    result = {}
    for k, v in pairs:
        need(k not in result, 'duplicate JSON key: ' + k)
        result[k] = v
    return result

def finite_float(value):
    result = float(value)
    need(math.isfinite(result), 'nonfinite JSON number')
    return result

def invalid_constant(value):
    raise RuntimeError('nonfinite JSON constant: ' + value)

def read_bound(path, limit=MAX_JSON):
    p = Path(path)
    need(p.is_absolute(), 'absolute input path')
    with p.open('rb') as stream:
        raw = stream.read(limit + 1)
    need(len(raw) <= limit, 'oversized input')
    return raw, hashlib.sha256(raw).hexdigest()

def json_ref(ref, limit=MAX_JSON):
    raw, digest = read_bound(ref['path'], limit)
    need(digest == ref['sha256'], 'input bytes changed: ' + ref['path'])
    return json.loads(raw.decode('utf-8-sig'), object_pairs_hook=object_pairs,
                      parse_float=finite_float, parse_constant=invalid_constant)

def frozen_module(ref):
    need(ref['sha256'] == PRODUCER_SHA, 'only the reviewed frozen Source13 module')
    raw, digest = read_bound(ref['path'], 65536)
    need(digest == PRODUCER_SHA, 'frozen producer bytes')
    module = types.ModuleType('_root_frozen_source13_closure')
    module.__file__ = ref['path']
    # Future Root-authorized operational import, from the hash-bound bytes rather
    # than a second path read or a cached pyc. __name__ is never __main__.
    exec(compile(raw, ref['path'], 'exec', dont_inherit=True), module.__dict__)
    return module

def pointer(body, value):
    need(isinstance(value, str) and value.startswith('/'), 'explicit JSON pointer')
    for token in value[1:].split('/'):
        token = token.replace('~1', '/').replace('~0', '~')
        body = body[int(token)] if isinstance(body, list) else body[token]
    return body

def pinned_json(f, ref, limit=MAX_JSON):
    f.clock()
    body = json_ref(ref, limit)
    f.clock()
    return body

def same(f, left, right, reason):
    need(f.key(left) == f.key(right), reason)

def original_stop(f, cfg, old, scheduler):
    result = pinned_json(f, cfg['original_result_stop_reference'], 2097152)
    thin = pinned_json(f, cfg['original_stop_thin_reference'], 2097152)
    request = pinned_json(f, cfg['original_archive_request_reference'], 2097152)
    archive_result = pinned_json(f, cfg['original_archive_result_reference'], 2097152)
    need(result['status'] == 'STOPPED_OR_UNKNOWN_NO_RETRY' and
         result['manifest_sha256'] == cfg['original_manifest_reference']['sha256'], 'original build really stopped with exact manifest')
    need(archive_result['status'] == 'NOT_STARTED_NO_RETRY' and archive_result['process_started'] is False and
         archive_result['pid'] is None and archive_result['exit_code'] is None and archive_result['exit_observed'] is False,
         'original archive was not started')
    need(archive_result['direct_child_reaped'] is False and archive_result['descendant_cleanup_proven'] is False,
         'original archive cleanup state')
    need(archive_result['error_type'] == result['error_type'] == 'FileNotFoundError' and '206' in archive_result['error'], 'original CreateProcess Win206')
    need(len(old['archives']) == 1 and old['archives'][0]['job_id'] == 'a0001', 'original archive owner')
    job = old['archives'][0]
    base = Path(job['job_root']) / 'stage'
    same(f, cfg['original_archive_request_reference']['path'], base.with_suffix('.request.json'), 'original request location')
    same(f, cfg['original_archive_result_reference']['path'], base.with_suffix('.result.json'), 'original result location')
    for body in (request, archive_result):
        need(body['job_id'] == job['job_id'] and body['argv'] == job['argv'] and body['cwd'] == job['cwd'] and
             body['shell'] is False and body['automatic_retry'] is False, 'original archive request/result binding')
    assertions = cfg.get('original_stop_thin_assertions', [])
    need(all(pointer(thin, v['pointer']) == v['value'] for v in assertions), 'Root original stop thin assertions')
    jobs = old['compile_jobs']
    need(scheduler['status'] == 'ALL_COMPILES_ACTUAL_VERIFIED' and scheduler['errors'] == [] and
         scheduler['all_submitted_futures_settled'] is True and scheduler['unsettled_job_ids'] == [] and
         scheduler['undispatched_job_ids'] == [] and scheduler['shutdown_wait_observed'] is True,
         'original scheduler actual settlement')
    need(scheduler['submitted_job_ids'] == [j['job_id'] for j in jobs] and
         scheduler['verified_indices'] == sorted(j['index'] for j in jobs), 'exact original submitted/verified owners')
    return result

def verify_compilers(f, old, old_sha, context, header, header_sha, policy):
    jobs = old['compile_jobs']
    need(old['mode'] == 'rebuild917' and old['retained_objects'] == [] and len(jobs) == 917, 'original all917 fresh mode')
    ids = [j['index'] for j in jobs]
    need(all(type(i) is int for i in ids) and set(ids) == set(range(1, 918)) and len(set(ids)) == 917, 'original unique all917 indices')
    need(len({j['job_id'] for j in jobs}) == 917, 'original unique compiler job ids')
    f.selected_owners(old, old_sha, jobs, [])
    verified, objects, hashes = {}, {}, {}
    for j in jobs:
        f.clock()
        base = Path(j['job_root']) / 'stage'
        need(f.inside(base, [old['output_root']]), 'old compiler scope')
        request_ref, result_ref, verified_ref = (f.file_ref(base.with_suffix(s)) for s in
                                               ('.request.json', '.result.json', '.verified.json'))
        req, res, v = (pinned_json(f, r, 2097152) for r in (request_ref, result_ref, verified_ref))
        env = f.environment(j, policy)
        for body in (req, res):
            need(body['job_id'] == j['job_id'] and body['argv'] == j['argv'] and body['cwd'] == j['cwd'] and
                 body['shell'] is False and body['automatic_retry'] is False and
                 body['timeout_seconds'] == j['timeout_seconds'] and body['environment_settings'] == j['environment'] and
                 body['actual_environment'] == env and body['environment_source'] == 'Root_admitted_settings_only', 'original actual compiler request/result')
        need(req['status'] == 'NOT_STARTED' and req['process_started'] is False and req['pid'] is None,
             'original request is an original prelaunch request')
        need(res['status'] == 'PROCESS_EXIT_OBSERVED' and res['process_started'] is True and res['exit_observed'] is True and
             type(res['exit_code']) is int and res['exit_code'] == 0 and res['direct_child_reaped'] is True and
             type(res['pid']) is int and res['pid'] > 0 and res['descendant_cleanup_proven'] is False, 'actual original compiler success')
        need(v['status'] == 'COMPILE_VERIFIED_NEW_ENVIRONMENT' and v['index'] == j['index'] and v['job_id'] == j['job_id'] and
             v['owner_tuple'] == j['owner_tuple'] and v['recipe_kind'] == j['recipe_kind'] and
             v['old_actual_recipe_claimed'] == j.get('old_actual_recipe_claimed'), 'original verified owner/provenance')
        for name in ('source_head', 'sdk_source_root', 'header_head', 'abi_inputs', 'sdk_freeze_sha256', 'compile_configuration_refs'):
            need(v[name] == context[name], 'original source/config qualification: ' + name)
        same(f, v['source'], j['source'], 'original actual source')
        same(f, v['object'], j['output'], 'original actual object')
        need(v['source_sha256'] == j['source_sha256'] and f.sha(j['source']) == j['source_sha256'], 'original source bytes')
        need(v['object_sha256'] == f.sha(j['output']), 'original object bytes')
        need(v['actual_stage'] == f.actual_stage(j, base), 'original verified actual argv/pid/raw request/result refs')
        need(v['actual_stage']['request_ref'] == request_ref and v['actual_stage']['result_ref'] == result_ref, 'original immutable request/result hashes')
        need(v['raw_dependencies_ref'] == f.file_ref(j['dependencies_file']), 'original dependency raw ref')
        need(v['dependencies'] == f.dependencies(j, header, header_sha, policy, context['abi_inputs']), 'rehash original Data.Source/Includes/Version')
        need(all(f.sha(r['path']) == r['sha256'] for r in context['abi_inputs'] + context['compile_configuration_refs']), 'original ABI/config bytes')
        # Frozen Source13 writes this reference after its original verified file;
        # add it in memory, never pretend it was present in that raw file.
        need('verified_ref' not in v, 'unexpected rewritten original verified body')
        v['verified_ref'] = verified_ref
        verified[j['index']], objects[j['index']], hashes[f.key(j['output'])] = v, j['output'], v['object_sha256']
    return verified, objects, hashes

def manifest_equivalence(f, cfg, old, new):
    need(new['compile_jobs'] == old['compile_jobs'] and new['retained_objects'] == old['retained_objects'] == [] and
         new['mode'] == old['mode'] == 'rebuild917', 'derived compiler inputs are identical, never dispatch them')
    for name in ('source_head', 'sdk_freeze_receipt', 'abi_inputs', 'selected_owner_lineage', 'selected_owner_map'):
        need(new[name] == old[name], 'unchanged original source/owner qualification: ' + name)
    same(f, new['output_root'], old['output_root'], 'existing BUILD89 root unchanged')
    need(Path(new['output_root']).is_dir(), 'existing original build root')
    expected_ids = ['a0002', 'i0002', 'l0002']
    need(len(new['archives']) == 1 and new['archives'][0]['job_id'] == expected_ids[0] and
         new['archives'][0]['inspection_job']['job_id'] == expected_ids[1] and new['link']['job_id'] == expected_ids[2], 'only three new closure jobs')
    a, link = new['archives'][0], new['link']
    need(a['member_indices'] == old['archives'][0]['member_indices'] and a['inputs'] == old['archives'][0]['inputs'] and
         link['direct_object_indices'] == old['link']['direct_object_indices'], 'original archive/direct owner membership')
    substitutions = cfg['authorized_closure_path_substitutions']
    need(substitutions and all(isinstance(v['original'], str) and isinstance(v['final'], str) for v in substitutions), 'Root explicit closure path transformations')
    replacements = [(v['original'], v['final']) for v in substitutions]
    permitted = set()
    for prior, current in ((old['archives'][0], a), (old['link'], link)):
        need(current['kind'] == prior['kind'] and current['tool_sha256'] == prior['tool_sha256'] and
             f.key(current['argv'][0]) == f.key(prior['argv'][0]), 'original selected closure tools unchanged')
        prior_tokens, prior_roles = f.expanded(prior, cfg['original_manifest_reference']['sha256'])
        tokens, roles = f.expanded(current, cfg['derived_manifest_ref']['sha256'])
        for flag in ('/OUT:', '/PDB:', '/IMPLIB:', '/ILK:', '/MAP:'):
            if f.option_present(prior_tokens, flag):
                before, after = f.opt(prior_tokens, flag), f.opt(tokens, flag)
                need(f.inside(before, [prior['job_root']]) and f.inside(after, [current['job_root']]), 'private closure output transformation')
                permitted.add((before, after))
        expected = []
        for token in prior_tokens:
            for original, final in replacements:
                token = token.replace(original, final)
            expected.append(token)
        need(tokens == expected and roles == prior_roles, 'Root reviewed expanded order/roles/path transformations')
    need(len(set(replacements)) == len(replacements) and set(replacements).issubset(permitted), 'only exact private output substitutions, no root replacement')
    return expected_ids

def run(config_path, config_sha):
    cfg = json_ref({'path': config_path, 'sha256': config_sha}, 2097152)
    need(cfg['schema'] == 'xar.native.closure.rsp/v1', 'closure config schema')
    f = frozen_module(cfg['frozen_producer_ref'])
    new = json_ref(cfg['derived_manifest_ref'])
    new_sha = cfg['derived_manifest_ref']['sha256']
    need(new['schema'] == 'xar.native.parallel.production/v1', 'derived manifest schema')
    a = f.receipt(new['build_admission'], 'ADMITTED', new_sha)
    f.DEADLINE = datetime.fromisoformat(a['deadline_utc'])
    need(f.DEADLINE.tzinfo is not None, 'explicit closure deadline')
    f.clock()
    old = pinned_json(f, cfg['original_manifest_reference'])
    old_sha = cfg['original_manifest_reference']['sha256']
    scheduler = pinned_json(f, cfg['original_scheduler_reference'], 2097152)
    original_stop(f, cfg, old, scheduler)
    allowed_ids = manifest_equivalence(f, cfg, old, new)
    build = f.abs_path(new['output_root'])
    metadata = f.abs_path(cfg['metadata_root'])
    same(f, metadata, build / 'closure02', 'only new closure02 metadata')
    need(not metadata.exists(), 'closure02 must be create-only')
    need(a['scope'] == 'native-closure' and a['original_manifest_sha256'] == old_sha and
         a['original_result_stop_sha256'] == cfg['original_result_stop_reference']['sha256'] and
         a['original_scheduler_sha256'] == cfg['original_scheduler_reference']['sha256'] and
         a['zero_compiler_invocations'] is True and a['exclusive_output_owner_verified'] is True and a['allowed_job_ids'] == allowed_ids,
         'Root explicit new closure admission')
    same(f, a['metadata_root'], metadata, 'admitted new metadata root')
    same(f, a['approved_output_root'], build, 'admitted existing BUILD89 output root')
    sdk, header, header_sha, freeze_sha, frozen = f.source_admission(new, new_sha, new['source_head'])
    need(a['source_head'] == new['source_head'] and a['sdk_freeze_sha256'] == freeze_sha, 'closure/source pin')
    old_policy = f.receipt(old['environment_policy'], 'ADMITTED_NEW_ENVIRONMENT', old_sha)
    policy = f.receipt(new['environment_policy'], 'ADMITTED_NEW_ENVIRONMENT', new_sha)
    f.selected_owners(new, new_sha, new['compile_jobs'], [])
    closure = f.receipt(new['archive_link_policy'], 'ADMITTED_EXACT_ARCHIVE_LINK_CLOSURE', new_sha)
    need(closure['source_head'] == new['source_head'] and closure['selected_inputs_complete'] is True, 'new Root closure qualification')
    need(new['abi_inputs'] == frozen['abi_inputs'] and old_policy['source_head'] == new['source_head'] and
         old_policy['sdk_freeze_sha256'] == freeze_sha, 'original source/ABI/policy pin')
    context = {'source_head': new['source_head'], 'sdk_source_root': str(sdk), 'header_head': new['source_head'],
               'abi_inputs': new['abi_inputs'], 'sdk_freeze_sha256': freeze_sha,
               'compile_configuration_refs': old_policy['compile_configuration_refs']}
    f.parallel_admission(a)
    for name in ('max_output_bytes', 'checkpoint_reserve_bytes', 'min_free_memory_bytes'):
        f.positive(a[name], 'explicit closure reservation')
    need(a['volume_free_min_bytes'], 'explicit closure volumes')
    for value in a['volume_free_min_bytes'].values():
        f.positive(value, 'explicit volume reserve')
    f.budget(a, build)
    verified, objects, hashes = verify_compilers(f, old, old_sha, context, header, header_sha, old_policy)
    archive, link = new['archives'][0], new['link']
    stages = [archive, archive['inspection_job'], link]
    f.private_scopes(stages)
    old_roots = [Path(j['job_root']).resolve() for j in old['compile_jobs'] + old['archives'] +
                 [j['inspection_job'] for j in old['archives']] + [old['link']]]
    new_roots = [Path(j['job_root']).resolve() for j in stages] + [metadata]
    need(all(not left.is_relative_to(right) and not right.is_relative_to(left)
             for left in new_roots for right in old_roots), 'fresh namespace never overlaps any original job')
    need(len({Path(v).name.casefold() for v in objects.values()}) == 917, 'original unique object basenames')
    need(archive['inputs'] == [objects[i] for i in archive['member_indices']], 'archive exact original objects')
    owners = archive['member_indices'] + link['direct_object_indices']
    need(len(owners) == 917 and set(owners) == set(range(1, 918)), 'all917 archive/direct owners')
    env = {}
    for j in stages:
        f.common(j, build)
        env[j['job_id']] = f.environment(j, policy)
        need(not f.inside(j['job_root'], [metadata]), 'new job files distinct from closure metadata')
    f.admit_inspection(archive, build)
    for j in (archive, link):
        f.inputs(j, new_sha)
        need(j['responsefiles'] and any(t.startswith('@') for t in j['argv']), 'explicit admitted compact RSP closure')
    metadata.mkdir()
    f.write(metadata / 'CLOSURE-REQUEST.json', {'schema': cfg['schema'], 'config_ref': {'path': config_path, 'sha256': config_sha},
            'derived_manifest_ref': cfg['derived_manifest_ref'], 'frozen_producer_ref': cfg['frozen_producer_ref'],
            'original_manifest_reference': cfg['original_manifest_reference'], 'original_result_stop_reference': cfg['original_result_stop_reference'],
            'original_scheduler_reference': cfg['original_scheduler_reference'], 'actual_compiler_invocations_in_this_closure': 0})
    control = f.Dispatch()
    archive_actual, link_inputs, link_actual = [], None, None
    try:
        for j in (archive, link):
            f.inputs(j, new_sha)
            expected = {f.key(r['path']): r['sha256'] for r in j['immutable_inputs']}
            selected = []
            for value in j['inputs']:
                digest = f.sha(value)
                need(digest == (hashes[f.key(value)] if f.key(value) in hashes else expected[f.key(value)]), 'actual selected input bytes')
                selected.append({'path': str(f.abs_path(value)), 'sha256': digest})
            base = f.stage(j, control, f.budget(a, build, next_job=j), env[j['job_id']], a['parallel_policy']['cleanup_wait_seconds'])
            hashes[f.key(j['output'])] = f.sha(j['output'])
            actual = f.actual_stage(j, base)
            value = {'status': 'STAGE_VERIFIED', 'job_id': j['job_id'], 'actual_stage': actual,
                     'output_ref': f.file_ref(j['output']), 'ordered_inputs': selected}
            if j['kind'] == 'archive':
                value['actual_members'] = f.inspect_archive(j, objects, control, a, build, env)
                archive_actual.append(value)
            else:
                tokens, roles = f.expanded(j, new_sha)
                link_inputs = {'actual_stage': actual, 'expanded_tokens': tokens, 'token_roles': roles, 'ordered_inputs': selected}
                link_actual = dict(value, dll_path=j['output'], dll_sha256=hashes[f.key(j['output'])])
            f.write(base.with_suffix('.verified.json'), value)
        need(f.sha(cfg['original_manifest_reference']['path']) == old_sha and
             f.sha(cfg['derived_manifest_ref']['path']) == new_sha, 'manifest originals remain immutable')
        refs, fresh = f.actual_packets(metadata, new, context, new['compile_jobs'], [], verified, {}, archive_actual, link_actual, link_inputs)
        need(fresh is True, 'actual original whole917 source identity')
        f.budget(a, build)
        f.write(metadata / 'RESULT.json', {'status': 'BUILD_OUTPUTS_VERIFIED_NO_RUNTIME_CREDIT', 'manifest_sha256': new_sha,
                'source_head': new['source_head'], 'owners': 917, 'mode': 'rebuild917', 'actual_compile_verified': 917,
                'actual_new_dependency_outputs': 917, 'actual_compiler_invocations_in_this_closure': 0,
                'actual_dependency_outputs_created_in_this_closure': 0, 'individually_qualified_retained': 0,
                'all_cpp_at_new_head': True, 'all_cpp_compiled_at_declared_source_head': True,
                'actual_packets': refs, 'original_compile_manifest_reference': cfg['original_manifest_reference'],
                'original_result_stop_reference': cfg['original_result_stop_reference'], 'original_scheduler_reference': cfg['original_scheduler_reference'],
                'Game_or_SDK_started': False, 'automatic_retry': False, 'descendant_cleanup_proven': False})
    except BaseException as original:
        f.failure_receipt(metadata / 'RESULT.json', {'status': 'STOPPED_OR_UNKNOWN_NO_RETRY', **f.error_data(original),
                          'actual_compiler_invocations_in_this_closure': 0, 'actual_dependency_outputs_created_in_this_closure': 0,
                          'original_compile_manifest_reference': cfg['original_manifest_reference'],
                          'original_result_stop_reference': cfg['original_result_stop_reference'], 'original_scheduler_reference': cfg['original_scheduler_reference'],
                          'original_files_retained': True, 'descendant_cleanup_proven': False}, original)
        raise

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config')
    parser.add_argument('expected_config_sha256')
    args = parser.parse_args()
    try:
        run(args.config, args.expected_config_sha256)
    except BaseException as original:
        print(json.dumps({'status': 'STOPPED_OR_UNKNOWN_NO_RETRY', 'error_type': type(original).__name__,
                          'error': str(original), 'diagnostics': getattr(original, '__notes__', []), 'automatic_retry': False}))
        return 2
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
