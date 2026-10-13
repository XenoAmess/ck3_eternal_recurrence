"""Resume 0.1.2 headship from the immutable, paid R79 pre-proposal SAVE.

The saved player is still in original Confucianism. This case only skips work
already present in the verified SAVE; it does not grant a nominee or mandate.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from types import FunctionType

from ck3_mod_acceptance_cases import lyd_release012_headship_adapter as fresh


CASE = 'release012-headship-resume'
RESULT = 'lyd-headship-resume-result.json'
SEED_BYTES = 69411120
SEED_SHA256 = 'f91795ad026e42ca5c958a5c50af949bb103381073d1ccb34fc51d05dab24e9d'
SEED_PLAYER = 31254
SEED_DATE = 53144328
PRODUCT_FILES = 83
FORMAL_MANIFEST_SHA256 = 'c3c8a398ff97c9b1af360b642bf235a973020be6613bceb7de196eae616cb1bc'
FORMAL_SOURCE_HEAD = '2d27096c9879f88c52fef0e94a3a6158cc2f6296'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def scoped(name):
    """Bind the existing native protocol to a distinct saved-campaign case."""
    namespace = dict(vars(fresh))
    namespace.update(CASE=CASE, RESULT=RESULT)
    for key in ('load_base', 'run_case', 'verify_case'):
        original = getattr(fresh, key)
        namespace[key] = FunctionType(original.__code__, namespace, original.__name__,
                                      original.__defaults__, original.__closure__)
    return namespace[name]


def seed_identity(seed):
    require(type(seed) is dict and seed.get('bytes') == SEED_BYTES and
            seed.get('sha256') == SEED_SHA256 and seed.get('player_id') == SEED_PLAYER and
            seed.get('date_raw') == SEED_DATE and seed.get('product_inventory') is None,
            'Exact immutable R79 pre-proposal qualification SAVE required')
    path = Path(seed['save']).resolve()
    require(path.is_file() and path.stat().st_size == SEED_BYTES,
            'R79 qualification SAVE absent or size differs')
    with path.open('rb') as source:
        digest = hashlib.file_digest(source, 'sha256').hexdigest()
    require(digest == SEED_SHA256, 'R79 qualification SAVE bytes changed')
    return path


def prepare_case(context):
    from ck3_mod_acceptance_prepare import CONFIG_NAMES, checked_copy, pin, write_json, _outer_from_inner, _finish

    data = context['case_contract']
    require(context['product'] == data['product'] == 'li-yu-dao' and
            context['case'] == data['case_id'] == CASE and
            [p['id'] for p in data['phases'][:3]] == ['baseline', 'preparation', 'institution'] and
            all(p.get('required') is True for p in data['phases'][:3]) and
            data['maximum_natural_days'] == 0,
            'Wrong paused R79 qualification-resume contract')
    deadline = fresh.storage_deadline(data)
    require(deadline - datetime.now(timezone.utc).timestamp() >= 7200,
            'Saved headship needs a fresh two-hour storage and normal-Quit window')
    seed = context['saved_campaign']
    source_save = seed_identity(seed)
    state = Path(context['state_dir']).resolve()
    output = Path(context['output']).resolve()
    require(not state.exists() and not source_save.is_relative_to(state),
            'New isolated state and untouched external SAVE required')
    inputs = context['case_inputs']
    require(set(inputs['plain_configuration']) == set(CONFIG_NAMES),
            'Original four plain configurations required')
    manifest_ref = inputs['formal_release_manifest']
    require(manifest_ref.get('sha256') == FORMAL_MANIFEST_SHA256,
            'Exact reviewed 0.1.2 formal manifest required')
    manifest = json.loads(fresh.checked(manifest_ref))
    require(manifest.get('format_version') == 1 and manifest.get('git_sha') == FORMAL_SOURCE_HEAD and
            manifest.get('mod_version') == '0.1.2' and manifest.get('product_id') == 'mod_li_yu_dao' and
            len(manifest.get('files', [])) == PRODUCT_FILES,
            'Wrong 0.1.2 formal release provenance')
    product = Path(inputs['product_dir']).resolve()
    files = sorted(p for p in product.rglob('*') if p.is_file())
    require(len(files) == PRODUCT_FILES and all(not p.is_symlink() for p in files),
            'Exact 83-file formal product staging required')
    actual_rows = {p.relative_to(product).as_posix(): pin(p) for p in files}
    expected_rows = {row['path']: row for row in manifest['files']}
    require(len(expected_rows) == PRODUCT_FILES and set(actual_rows) == set(expected_rows) and
            all(actual_rows[name]['bytes'] == row['size'] and
                actual_rows[name]['sha256'] == row['sha256']
                for name, row in expected_rows.items()),
            'Formal product bytes differ from reviewed 0.1.2 manifest')
    descriptor = (product / 'descriptor.mod').read_text(encoding='utf-8-sig')
    require('remote_file_id' not in descriptor, 'Formal inner descriptor contains Workshop ID')
    profile = state / 'profile'
    target = profile / 'mod-content/product'
    profile.mkdir(parents=True)
    for name in CONFIG_NAMES:
        checked_copy(inputs['plain_configuration'][name], profile / name)
    for file in files:
        checked_copy(pin(file), target / file.relative_to(product))
    outer = profile / 'mod/product.mod'
    outer.parent.mkdir()
    with outer.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(_outer_from_inner(target / 'descriptor.mod', target))
    write_json(profile / 'dlc_load.json', {'enabled_mods': ['mod/product.mod'], 'disabled_dlcs': []})

    # Compiled business contract is inert metadata, not an enabled fixture mod.
    compiled_path = profile / 'mod-content/fixture/_case_contract.json'
    write_json(compiled_path, {'schema': 'ck3-mod-acceptance-product-assertions-v1',
        'product': context['product'], 'case': CASE, 'config': data,
        'required_markers': [], 'product_marker_minimum': {},
        'original_receipt': {'saved_seed_sha256': SEED_SHA256,
                             'R79_original_representatives_or_votes_inferred': False},
        'assertion_source_pins': [], 'emitter': None,
        'product_descriptor': pin(target / 'descriptor.mod'),
        'whole_product_release_pass': False})
    inventory = output / 'saved-product-inventory.json'
    write_json(inventory, {'schema': 'ck3-saved-campaign-product-only-profile-v1',
        'profile_path': str(profile), 'enabled_mods': ['mod/product.mod'],
        'product_files': [pin(outer), *[pin(p) for p in sorted(target.rglob('*')) if p.is_file()]]})
    profile_files = {p.relative_to(profile).as_posix(): pin(p)
                     for p in sorted(profile.rglob('*')) if p.is_file()}
    resume_receipt = state / 'resume-preparation.json'
    write_json(resume_receipt, {'schema': 'lyd-headship-R79-resume-preparation-v1',
        'prepared_at_utc': datetime.now(timezone.utc).isoformat(),
        'seed': {key: seed[key] for key in ('save', 'bytes', 'sha256', 'player_id', 'date_raw')},
        'seed_source_run': 'bf-202609141645-5434332d4d--li-yu-dao--R0079',
        'formal_release_manifest': manifest_ref,
        'source_save_untouched': True, 'profile_path': str(profile),
        'profile_file_count': len(profile_files),
        'product_file_count': PRODUCT_FILES, 'product_inventory': pin(inventory),
        'assertion_contract': pin(compiled_path), 'runtime_manifest': context['runtime_manifest'],
        'business_pass': False})
    public = _finish(context, profile, {'kind': 'R79-immutable-product-only-resume',
        'resume_receipt': pin(resume_receipt), 'product_inventory': pin(inventory),
        'formal_release_manifest': manifest_ref, 'source_save_sha256': SEED_SHA256,
        'fixture_mounted': False})
    initial = output / 'initial-plan.json'
    write_json(initial, {'steps': []})
    return {'startup': {'mode': 'saved_campaign', 'state_dir': str(state),
        'saved_campaign': {**seed, 'save': str(source_save), 'product_inventory': str(inventory)}},
        'initial_plan': pin(initial), 'startup_evidence': pin(state / 'preparation.json'),
        'profile_preparation': public['preparation'], 'assertion_contract': pin(compiled_path),
        'files': public['files'],
        'runtime_status': 'NOT_RUN', 'business_contract_applicable': True,
        'business_pass': False, 'product_release_pass': False}


def run_case(context, client):
    seed_identity({**context['saved_campaign'], 'product_inventory': None})
    base = scoped('load_base')()
    frame = client.validate_frame(client.snapshot(require_event_free=False), require_event_free=False)
    live = base.binding(frame)
    require(live['actor'] == SEED_PLAYER and live['date_raw'] == SEED_DATE,
            'Actual loaded paused player/date differs from immutable R79 SAVE')
    religion = base.religion(client, live, 'resume-original-religion')
    require(religion.get('faith_id') == 31 and religion.get('rite_id') == 174 and
            religion.get('faith_main_rite_id') == 33,
            'Actual loaded original Confucian white-sand rite differs from R79 SAVE')
    return scoped('run_case')(context, client)


def verify_case(context):
    return scoped('verify_case')(context)
