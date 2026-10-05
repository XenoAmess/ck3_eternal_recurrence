"""Fixed project broker installation logic. Import is side-effect free."""
from contextlib import ExitStack
from pathlib import Path
import base64
import hashlib
import json
import ntpath
import time
import uuid

INSTALL_ROOT = r'C:\Program Files\XAR CK3 Project EXE Broker'
TASK_FOLDER = r'\XAR CK3 Project EXE Broker'
TASK_NAME = 'RegisterDeclaredProjectExecutables'
SYSTEM = 'S-1-5-18'
ADMINS = 'S-1-5-32-544'
OWNER = 'S-1-5-21-4063940640-1897558599-686929869-1001'

def raw_json(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')

def sha(data):
    return hashlib.sha256(data).hexdigest()

def _pairs(rows):
    out = {}
    for key, value in rows:
        if key in out:
            raise ValueError('duplicate JSON key')
        out[key] = value
    return out

def strict_json(data):
    return json.loads(data.decode('utf-8'), object_pairs_hook=_pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))

def relative_path(value):
    if not isinstance(value, str) or '\\' in value or value.startswith('/'):
        raise ValueError('portable relative path required')
    if any(part in ('', '.', '..') for part in value.split('/')) or ':' in value:
        raise ValueError('unsafe relative path')
    return value

def task_spec(owner_sid):
    # list2cmdline is solely argument serialization; this module runs no command.
    import subprocess
    arguments = subprocess.list2cmdline(['-I', '-S', '-B',
        ntpath.join(INSTALL_ROOT, 'broker_bootstrap.py'), '--config',
        ntpath.join(INSTALL_ROOT, 'policy.json')])
    return {'folder': TASK_FOLDER, 'name': TASK_NAME,
        'path': TASK_FOLDER + '\\' + TASK_NAME,
        'action': {'path': ntpath.join(INSTALL_ROOT, 'runtime', 'python.exe'),
            'arguments': arguments, 'working_directory': INSTALL_ROOT},
        'principal': {'user_id': SYSTEM, 'logon_type': 5, 'run_level': 1},
        'triggers_count': 0, 'allow_demand_start': True,
        'multiple_instances': 1, 'execution_time_limit': 'PT4M',
        'sddl': 'O:BAG:BAD:P(A;;GA;;;SY)(A;;GA;;;BA)(A;;GRGX;;;' + owner_sid + ')'}

def make_request(policy_bytes, manifest_bytes, request_id):
    policy = strict_json(policy_bytes)
    return raw_json({'schema': 'xar.project-exe-broker.request.v1',
        'request_id': request_id, 'installation_id': policy['installation_id'],
        'expected_policy_sha256': sha(policy_bytes), 'producer_kind': 'cmake-file-api-v2',
        'manifest_b64': base64.b64encode(manifest_bytes).decode('ascii'),
        'manifest_sha256': sha(manifest_bytes)})

def verify_receipt(receipt_bytes, request_bytes, manifest_bytes, policy_bytes, outputs):
    receipt = strict_json(receipt_bytes)
    request = strict_json(request_bytes)
    policy = strict_json(policy_bytes)
    identity = receipt.get('broker_identity')
    expected = {'installation_id': policy['installation_id'], 'owner_sid': policy['owner_sid'],
        'request_id': request['request_id'], 'request_sha256': sha(request_bytes),
        'manifest_bytes_sha256': sha(manifest_bytes), 'policy_sha256': sha(policy_bytes),
        'runtime_manifest_sha256': policy['runtime_manifest_sha256'],
        'runtime_verified': True, 'protected_code': True,
        'request_owner_sid': policy['owner_sid'], 'actual_token_sid': SYSTEM}
    if identity != expected or receipt.get('status') != 'verified':
        raise ValueError('missing exact verified SYSTEM broker identity')
    if receipt.get('admin_token') is not True or receipt.get('system_token_sid') != SYSTEM:
        raise ValueError('actual SYSTEM/admin receipt required')
    if any(receipt.get(key) is not True for key in ('observed_prior_settings_preserved',
            'observed_extensions_unchanged', 'observed_processes_unchanged')):
        raise ValueError('prior settings preservation not proved')
    before, after = receipt.get('before_settings'), receipt.get('after_settings')
    expected_keys = {'ExclusionPath', 'ExclusionExtension', 'ExclusionProcess'}
    for settings in (before, after):
        if not isinstance(settings, dict) or set(settings) != expected_keys:
            raise ValueError('fresh complete settings required')
        if any(not isinstance(v, list) or any(not isinstance(x, str) for x in v) for v in settings.values()):
            raise ValueError('invalid setting arrays')
    normalize = lambda xs: {ntpath.normcase(ntpath.normpath(x)) for x in xs}
    if not normalize(before['ExclusionPath']) <= normalize(after['ExclusionPath']):
        raise ValueError('prior paths lost')
    for key in ('ExclusionExtension', 'ExclusionProcess'):
        if set(before[key]) != set(after[key]):
            raise ValueError('non-path setting changed')
    files = receipt.get('files')
    if not isinstance(files, list):
        raise ValueError('actual output identities missing')
    for output in outputs:
        matches = [row for row in files if isinstance(row, dict) and
                   ntpath.normcase(row.get('path', '')) == ntpath.normcase(output['path'])]
        if len(matches) != 1 or matches[0].get('size') != output['size'] or matches[0].get('sha256') != output['sha256']:
            raise ValueError('output identity mismatch')
        path = ntpath.normcase(ntpath.normpath(output['path']))
        if path not in normalize(after['ExclusionPath']) or path not in normalize(receipt.get('verified_requested_paths', [])):
            raise ValueError('exact output not actually excluded')
    return receipt

def load_bundle(package, expected_sha, safety):
    package = Path(package)
    with ExitStack() as stack:
        manifest_lease = stack.enter_context(safety.lock_file(str(package / 'bundle-manifest.json')))
        raw = manifest_lease.read_bytes(2 * 1024 * 1024)
        if sha(raw) != expected_sha:
            raise ValueError('approved bundle manifest SHA mismatch')
        manifest = strict_json(raw)
        if set(manifest) != {'schema', 'installation_id', 'owner_sid', 'files', 'initial_manifests'}:
            raise ValueError('unexpected bundle schema')
        if manifest['schema'] != 'xar.project-exe-broker.bundle.v1' or manifest['owner_sid'] != OWNER:
            raise ValueError('unexpected package/owner')
        if str(uuid.UUID(manifest['installation_id'])) != manifest['installation_id']:
            raise ValueError('canonical installation UUID required')
        frozen = []
        seen = set()
        for row in manifest['files']:
            if set(row) != {'path', 'size', 'sha256'} or type(row['size']) is not int:
                raise ValueError('invalid file inventory')
            relative = relative_path(row['path'])
            if relative.casefold() in seen:
                raise ValueError('duplicate inventory path')
            seen.add(relative.casefold())
            lease = stack.enter_context(safety.lock_file(str(package / relative)))
            data = lease.read_bytes(max(row['size'], 1))
            if len(data) != row['size'] or sha(data) != row['sha256']:
                raise ValueError('candidate source bytes changed: ' + relative)
            frozen.append((row, data))
        manifest_lease.revalidate()
    return manifest, frozen

def prepare_plan(package, expected_sha, safety):
    manifest, frozen = load_bundle(package, expected_sha, safety)
    data = {row['path']: content for row, content in frozen}
    policy_bytes = data['policy.json']
    policy = strict_json(policy_bytes)
    if policy['owner_sid'] != OWNER or policy['runtime_root'].replace('/', '\\') != INSTALL_ROOT:
        raise ValueError('fixed policy identity mismatch')
    if policy['installation_id'] != manifest['installation_id']:
        raise ValueError('installation identity mismatch')
    if sha(data['runtime-seal.json']) != policy['runtime_manifest_sha256']:
        raise ValueError('policy seal hash mismatch')
    seal = strict_json(data['runtime-seal.json'])
    if set(seal) != {'schema', 'installation_id', 'python_version', 'files'} or seal['installation_id'] != policy['installation_id']:
        raise ValueError('seal identity mismatch')
    for row in seal['files']:
        relative = relative_path(row['path'])
        if relative not in data or len(data[relative]) != row['size'] or sha(data[relative]) != row['sha256']:
            raise ValueError('seal differs from approved package')
    install_manifest = strict_json(data['installation-manifest.json'])
    spec = task_spec(OWNER)
    if install_manifest['policy']['sha256'] != sha(policy_bytes) or install_manifest['runtime_seal']['sha256'] != sha(data['runtime-seal.json']):
        raise ValueError('installation manifest hash mismatch')
    if install_manifest['task'] != {k: v for k, v in spec.items() if k not in ('multiple_instances', 'execution_time_limit', 'sddl')}:
        raise ValueError('installation task manifest mismatch')
    initial = []
    for row in manifest['initial_manifests']:
        raw = data[relative_path(row['path'])]
        if sha(raw) != row['sha256']:
            raise ValueError('initial build manifest changed')
        initial.append((row, raw))
    if len(initial) != 2 or sum(len(row['outputs']) for row, _ in initial) != 4:
        raise ValueError('exact initial two manifests/four outputs required')
    return {'manifest': manifest, 'frozen': frozen, 'policy_bytes': policy_bytes,
        'task': spec, 'initial': initial,
        'summary': {'status': 'prepared_only', 'bundle_sha256': expected_sha,
            'files': len(frozen), 'bytes': sum(len(content) for _, content in frozen),
            'fixed_root': INSTALL_ROOT, 'task': spec, 'settings_changed': False}}

def install(plan, adapter, safety, output_receipt):
    facts = dict(plan['summary'])
    facts.update(status='installing', build_succeeded=None, settings_status='not_started', phases=[])
    try:
        token = adapter.token_identity()
        if token.get('admin') is not True or token.get('sid') != OWNER:
            raise ValueError('one-time elevated authorized owner token required')
        if adapter.path_exists(INSTALL_ROOT) or adapter.task_exists(plan['task']):
            raise FileExistsError('existing installation/task refused; no overwrite')
        facts['phases'].append('source_bundle_frozen')
        adapter.create_fresh_protected_root(INSTALL_ROOT, OWNER)
        for row, data in plan['frozen']:
            adapter.copy_new_protected_file(INSTALL_ROOT, row['path'], data, row['sha256'], OWNER)
        adapter.create_fixed_data_directories(INSTALL_ROOT, OWNER)
        facts['acl_inventory'] = adapter.verify_complete_install(plan)
        facts['phases'].append('all_code_config_leaf_acl_and_bytes_verified')
        adapter.register_task_new(plan['task'])
        facts['task_readback'] = adapter.verify_task(plan['task'])
        facts['phases'].append('fixed_system_task_actual_definition_acl_verified')
        pending = []
        for baseline, manifest_bytes in plan['initial']:
            request_id = str(uuid.uuid4())
            request_bytes = make_request(plan['policy_bytes'], manifest_bytes, request_id)
            # Adapter verifies all declared current baseline output identities first.
            adapter.verify_initial_outputs(baseline['outputs'])
            adapter.publish_owner_request(request_id, request_bytes, OWNER)
            pending.append((baseline, manifest_bytes, request_id, request_bytes))
        adapter.run_fixed_task(plan['task'])
        facts['settings_status'] = 'pending_actual_SYSTEM_receipts'
        deadline = time.monotonic() + 180
        results = []
        facts['initial_results'] = results
        for baseline, manifest_bytes, request_id, request_bytes in pending:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('shared initial receipt window elapsed')
            raw = adapter.wait_fixed_receipt(request_id, timeout=remaining)
            receipt = verify_receipt(raw, request_bytes, manifest_bytes, plan['policy_bytes'], baseline['outputs'])
            results.append({'request_id': request_id, 'request_sha256': sha(request_bytes),
                'receipt_sha256': sha(raw), 'status': receipt['status'], 'files': baseline['outputs']})
        facts['settings_status'] = 'verified'
        facts['status'] = 'installed_initial_outputs_verified'
        facts['ordinary_token_future_no_uac_status'] = 'pending_actual_ordinary_token_run_and_SYSTEM_receipt'
    except Exception as error:
        facts['status'] = 'installation_failed_or_partial'
        facts['error'] = type(error).__name__ + ': ' + str(error)
        facts['retained_partial_installation'] = True
    finally:
        adapter.write_new_external_receipt(output_receipt, raw_json(facts))
    return facts
