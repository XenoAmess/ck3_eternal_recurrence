"""Test-only Java-emitter -> common import -> Saved verifier/host-copy consumer.

The save/configuration bytes are authored software fixtures and never launched.
This test does not inspect, modify, or load a managed live profile.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('repo-root', 'shared-source', 'manifest', 'scratch'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    repository = args.repo_root.resolve()
    shared = args.shared_source.resolve()
    scratch = args.scratch.resolve()
    scratch.mkdir()
    sys.path[:0] = [str(shared / 'tools'), str(shared / 'ck3_autonomous_player/src')]
    from ck3_mod_acceptance_background_types import FilePin, json_object
    from ck3_mod_acceptance_prepare import CONFIG_NAMES, materialize_prebuilt_fixture, pin
    from ck3_mod_acceptance_saved_profile_v2 import materialize_saved_profile_v2
    from test_saved_campaign_profile_inventory_v2 import ProfileSpec, actual_host_preparer
    from xar_autoplayer.saved_campaign_profile_inventory_v2 import parse_inventory, verify_inventory

    manifest = pin(args.manifest)
    row = json_object(json.loads(Path(manifest['path']).read_bytes()))
    runtime = scratch / 'authored-import-runtime.json'
    runtime.write_text(json.dumps({'machine_id': row['machine_id']}), encoding='utf-8')
    fixture, receipt, materialized = materialize_prebuilt_fixture(json_object({
        'product': 'financial-markets', 'case': row['case_id'], 'repo_root': str(repository),
        'runtime_manifest': pin(runtime), 'case_inputs': {'prebuilt_fixture_manifest': manifest}}),
        manifest, scratch / 'imported-fixture')
    if receipt['fixture_contains_business_effects'] or materialized['game_started']:
        raise ValueError('Observer import cannot claim business execution or a game launch')
    if (fixture / 'common/on_action/xfma_start.txt').exists():
        raise ValueError('Saved observer retained a cold-start registrar')
    configs: dict[str, FilePin] = {}
    for index, name in enumerate(CONFIG_NAMES):
        path = scratch / ('authored-config-' + str(index))
        path.write_bytes(b'AUTHORED SOFTWARE FIXTURE; NEVER USED BY A GAME\n')
        configs[name] = pin(path)
    prepared = materialize_saved_profile_v2({'state_dir': str(scratch / 'state'),
        'output': str(scratch / 'prepared')}, fixture, configs, source_role='case_fixture')
    profile = Path(prepared['profile'])
    inventory_path = Path(prepared['product_inventory']['path'])
    inventory = parse_inventory(json.loads(inventory_path.read_bytes()))
    checked = verify_inventory(inventory, profile=profile, actual_enabled_mods=['mod/product.mod'])
    if len(checked.projections) != 1 or checked.projections[0].role != 'case_fixture':
        raise ValueError('Observer projection was relabeled instead of fixing its emitted content')
    source = scratch / 'authored-software-copy-input.ck3'
    source.write_bytes(b'AUTHORED COPY TEST BYTES ONLY; NEVER A CK3 ENGINE SAVE\n')
    source_pin = pin(source)
    host_args = argparse.Namespace(saved_campaign_save=source, saved_campaign_save_bytes=source_pin['bytes'],
        saved_campaign_save_sha256=source_pin['sha256'], saved_campaign_player_id=31254,
        saved_campaign_date_raw=53144328, saved_campaign_product_inventory=inventory_path)
    copied = json_object(actual_host_preparer()(host_args, ProfileSpec(profile, Path(prepared['state_dir']))))
    copied_path = copied.get('copied_save_path')
    if not isinstance(copied_path, str) or Path(copied_path).read_bytes() != source.read_bytes():
        raise ValueError('Actual host copy consumer did not preserve the original input bytes')
    if copied.get('source_game_state_claimed') is not False or copied.get('product_acceptance_proven') is not False:
        raise ValueError('Software copy cannot grant engine or product acceptance')
    result = {'schema': 'financial-observer-saved-consumer-test-v1', 'source_role': 'case_fixture',
        'saved_inventory_verified': True, 'host_copy_readback_verified': True,
        'game_started': False, 'business_acceptance_proven': False,
        'emitted_manifest': manifest, 'copied_input': source_pin,
        'inventory': prepared['product_inventory']}
    (scratch / 'actual-result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
