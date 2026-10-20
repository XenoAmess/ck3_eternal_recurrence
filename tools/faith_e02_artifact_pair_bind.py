"""Bind thin cases to an existing shared runtime and fresh scene admissions; no launch."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from pathlib import Path
import faith_e02_artifact_pair_queue as Q
from ck3_mod_acceptance_cases.faith_e02_artifact_pair_adapter import FLAGS
from faith_e02_artifact_pair_contract import (ARTIFACT, CASE_PREFIX, DATE, PLAYER, RECIPIENTS, SAVE_BYTES,
    SAVE_SHA, SITE, Object, field, integer, json_value, mapping, object_value, parse_contract, parse_pin,
    pin, read, require, text, write_once)

OLD = Path('C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b14-a01')
PENDING = OLD / 'state-a01/native-session/holy-site-relic-action-intents/02990f36bbe8dd7a1ca527216a08140b565fc1697257128fe1e0c8f9724741c9.pending.json'
WORLD = OLD / 'live/4-8e1c2f1861--faith-engine--R0007/case-output/firstfour-integrated-result.json'
MOTHER = Path('C:/workspace/ck3-faith-and-power-20261017/episode01/scenario/saves/C2-nadjaf-adopted-funded.ck3')


def bind(runtime_path: Path, configuration_path: Path, states: tuple[Path, Path], admissions: tuple[Path, Path],
         pair_root: Path, pair_id: str, output: Path, draft: object = None) -> Object:
    require(not output.exists(), 'Fresh metadata output only; no overwrite')
    runtime = read(runtime_path)
    manifest_ref = parse_pin(field(runtime, 'manifest'))
    manifest = read(Path(manifest_ref['path']))
    machine = text(field(runtime, 'machine_id'), 'current machine')
    require(field(manifest, 'machine_id') == machine, 'Runtime/manifest machine differ')
    paths = field(runtime, 'paths')
    dll = pin(Path(text(field(paths, 'dll'), 'shared DLL path')))
    declared = field(field(manifest, 'native'), 'dll')
    require(integer(field(declared, 'bytes'), 'manifest DLL bytes') == dll['bytes'] and field(declared, 'sha256') == dll['sha256'],
            'Shared manifest DLL changed')
    qualification = parse_pin(field(manifest, 'native_input_identity_evidence'))
    configuration = read(configuration_path)
    saved: Object = {'save': str(MOTHER), 'bytes': SAVE_BYTES, 'sha256': SAVE_SHA, 'player_id': PLAYER, 'date_raw': DATE}
    require(pin(MOTHER)['sha256'] == SAVE_SHA and MOTHER.stat().st_size == SAVE_BYTES, 'Original C2 not available')
    base = Path(__file__).resolve().parent
    dependencies = [pin(base / 'faith_e02_artifact_pair_contract.py'), pin(base / 'faith_e02_artifact_pair_queue.py'),
                    pin(base / 'ck3_mod_acceptance_cases/faith_e02_artifact_pair_adapter.py')]
    require(states[0].resolve() != states[1].resolve() and pair_root.is_absolute(), 'Two distinct fresh managed profiles; stable separate pair evidence root')
    cases: list[Object] = []
    inventory: Object = {'schema': 'faith-mechanism-experiment-inventory-v1', 'products': [
        {'key': 'faith-engine', 'workshop_item_id': None, 'player_product': False, 'independent_mechanism_experiment': True}]}
    # Validate every source/admission/contract before creating the first metadata file.
    prepared: list[tuple[str, Object, Object]] = []
    for index, arm in enumerate(('personal', 'enshrine')):
        state = states[index]
        require(state.is_absolute() and not state.exists(), 'New actual managed profile must be allocated by public prepare, not this binder')
        admission = pin(admissions[index])
        grant = read(admissions[index])
        expiry = datetime.fromisoformat(text(field(grant, 'expires_at_utc'), 'fresh admission expiry').replace('Z', '+00:00'))
        require(field(grant, 'machine_id') == machine and field(grant, 'active') is True and expiry.tzinfo is not None and
                datetime.now(timezone.utc) < expiry, 'Fresh scene admission required; no closed B14/B18 grant reuse')
        contract: Object = {'schema': 'faith-e02-artifact-pair-case-v1', 'product': 'faith-engine',
            'case': CASE_PREFIX + arm + '-v1', 'arm': arm, 'pair_id': pair_id, 'machine_id': machine,
            'saved_input': saved, 'pair_evidence_root': str(pair_root), 'artifact_id': ARTIFACT, 'holy_site_id': SITE,
            'recipient_ids': list(RECIPIENTS), 'metric': 'knight_effectiveness_raw',
            'native_cohort': {'dll': json_value(dll), 'qualification': json_value(qualification)},
            'previous_enshrine': {'pending': json_value(pin(PENDING)), 'world_result': json_value(pin(WORLD))},
            'draft': json_value(draft) if index == 0 else None, 'dependencies': json_value(dependencies),
            'max_public_calls': 96, 'profile': {'enabled_mods': [], 'product_files': []}}
        parse_contract(contract)
        inputs: Object = {'configuration': configuration, 'storage_admission': json_value(admission)}
        prepared.append((arm, contract, inputs))
        cases.append({'id': CASE_PREFIX + arm + '-v1', 'status': 'blocked',
            'adapter': {'path': str(base / 'ck3_mod_acceptance_cases/faith_e02_artifact_pair_adapter.py'),
                        'config': str(output / (arm + '-contract.json'))},
            'initial_plan': str(output / 'initial-plan.json'), 'startup': {'mode': 'saved_campaign',
                'state_dir': str(state), 'saved_campaign': {**saved, 'product_inventory': str(output / 'inventory.json')}},
            'budgets': {'command_timeout': 20, 'readiness_timeout': 1800, 'timeout': 5400, 'hold_seconds': 3000, 'poll_interval': 0.5},
            'required_mcp_tools': json_value(sorted(Q.REQUIRED)), 'opt_in_read_only_mcp_tools': json_value(sorted(Q.OPTIN_READONLY)),
            **FLAGS, 'business_contract_applicable': False, 'whole_product_acceptance_credit': False})
    for arm, contract, inputs in prepared:
        write_once(output / (arm + '-contract.json'), contract)
        write_once(output / (arm + '-inputs.json'), inputs)
    write_once(output / 'initial-plan.json', {'steps': [Q.step('artifact-pair-opening-snapshot', 'ck3_take_snapshot', {'include_native_command_history': False})]})
    write_once(output / 'inventory.json', inventory)
    products: Object = {'schema': 'ck3-mod-acceptance-products-v1', 'product_inventory': str(output / 'inventory.json'),
        'products': {'faith-engine': {'external_mod': True, 'runtime_mod_key': 'faith-engine',
            'workshop_item_id': None, 'cases': json_value(cases)}}}
    write_once(output / 'products.json', products)
    receipt: Object = {'schema': 'artifact-pair-bind-v1', 'machine_id': machine,
        'observed_at_utc': datetime.now(timezone.utc).isoformat(), 'runtime': json_value(pin(runtime_path)),
        'native_qualification': json_value(qualification), 'native_dll': json_value(dll),
        'products': json_value(pin(output / 'products.json')), 'allocation_performed': False,
        'game_started': False, 'case_tools_dispatched': False}
    write_once(output / 'BIND.actual.json', receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('runtime', 'configuration', 'personal-state', 'enshrine-state', 'personal-admission', 'enshrine-admission', 'pair-root', 'output'):
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--pair-id', required=True)
    parser.add_argument('--draft-json', type=Path)
    args = parser.parse_args()
    bind(args.runtime, args.configuration, (args.personal_state, args.enshrine_state),
         (args.personal_admission, args.enshrine_admission), args.pair_root, args.pair_id, args.output,
         None if args.draft_json is None else read(args.draft_json))
    return 0


if __name__ == '__main__': raise SystemExit(main())
