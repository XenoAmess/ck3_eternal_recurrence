"""Join original arm files; never launch, restore, allocate or submit any action."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from pathlib import Path
import re
from faith_e02_artifact_pair_contract import (ARTIFACT, DATE, PLAYER, SAVE_BYTES, SAVE_SHA, SITE, Object, Pin,
    array, field, frame, integer, json_value, mapping, object_value, parse_pin, pin, read, require, text, write_once)

RESULT = 'artifact-pair-arm-result.json'


def decimal(value: object) -> int:
    original = text(value, 'canonical signed decimal')
    require(re.fullmatch(r'0|-?[1-9][0-9]*', original) is not None, 'No float/exponent/leading-zero decimal identities')
    result = int(original)
    require(-(2**63) <= result <= 2**63-1, 'Signed native raw range exceeded')
    return result


def actors(value: object) -> dict[int, Object]:
    result: dict[int, Object] = {}
    for x in array(value, 'two real recipient readings'):
        row = object_value(x)
        target = integer(field(row, 'character_id'), 'full recipient ID', 1, 2**32-2)
        require(target not in result and integer(field(row, 'raw_scale'), 'raw scale') == 100000 and
                field(row, 'site_attribution_observed') is False and field(row, 'cache_generation_time_known') is False,
                'Duplicate/unqualified recipient reading')
        decimal(field(row, 'raw_decimal'))
        integer(field(row, 'rite_id'), 'actual Rite fullID', 0, 2**32-2)
        integer(field(row, 'faith_id'), 'actual Faith fullID', 0, 2**32-2)
        text(field(row, 'original_breakdown'), 'complete original Knight text', empty=True)
        result[target] = row
    require(set(result) == {15893, 10322}, 'Same two named actual recipients required')
    return result


def combine(personal: object, enshrine: object) -> Object:
    p, e = object_value(personal), object_value(enshrine)
    for row, arm in ((p, 'personal'), (e, 'enshrine')):
        require(field(row, 'schema') == 'faith-e02-artifact-pair-arm-result-v1' and field(row, 'arm') == arm and
                field(row, 'status') == 'ARM_OBSERVED_PAIR_PENDING' and field(row, 'error') is None and
                field(row, 'world_post_confirmed') is True and field(row, 'unknown_original_action') is False and
                field(row, 'site_attribution_observed') is False and field(row, 'total_payment_observed') is False,
                'Both original arms must have independent known poststate; never fill a failed arm from another scene')
    require(field(p, 'pair_core') == field(e, 'pair_core') and field(p, 'machine_id') == field(e, 'machine_id'),
            'Mother, native cohort, previous retained history, artifact/site/recipients/metric must be identical')
    core = mapping(field(p, 'pair_core'), 'immutable pair contract projection')
    require(set(core) == {'pair_id', 'machine_id', 'saved_sha256', 'saved_bytes', 'artifact_id', 'holy_site_id',
        'recipient_ids', 'metric', 'native_dll', 'native_qualification', 'previous_pending', 'previous_known_world_result'},
        'Complete exact two-arm source binding required')
    require(text(core['pair_id'], 'pair identity') != '' and text(core['machine_id'], 'machine identity') == field(p, 'machine_id') and
            core['saved_sha256'] == SAVE_SHA and integer(core['saved_bytes'], 'C2 bytes') == SAVE_BYTES and
            integer(core['artifact_id'], 'paired artifact', 0, 2**32-2) == ARTIFACT and
            integer(core['holy_site_id'], 'paired holy site', 0, 2**32-2) == SITE and core['metric'] == 'knight_effectiveness_raw' and
            [integer(x, 'recipient ID', 1, 2**32-2) for x in array(core['recipient_ids'], 'explicit pair recipients')] == [15893, 10322],
            'A different input/metric cannot receive this comparison label')
    for key in ('native_dll', 'native_qualification', 'previous_pending', 'previous_known_world_result'):
        parse_pin(core[key], verify=False)  # Preserve original pins even if later retention reclaims an input.
    require(text(field(p, 'run_id'), 'personal allocated run') != text(field(e, 'run_id'), 'enshrine allocated run') and
            integer(field(p, 'actual_pid'), 'personal actual PID', 1) != integer(field(e, 'actual_pid'), 'enshrine actual PID', 1),
            'Two genuinely independent managed worlds/processes required')
    p0, e0 = field(p, 'before'), field(e, 'before')
    # Direct same-source baseline equality is required, not inferred from the save name.
    require(p0 == e0, 'Actual initial wallets/site inventory/grades/recipients/Knight text differ; paired comparison confounded')
    before = actors(field(p0, 'actors'))
    p_after = actors(field(field(p, 'after'), 'actors'))
    e_after = actors(field(field(e, 'after'), 'actors'))
    pairs: list[Object] = []
    for target in (15893, 10322):
        base, own, holy = before[target], p_after[target], e_after[target]
        for current in (own, holy):
            require(field(current, 'rite_id') == field(base, 'rite_id') and field(current, 'faith_id') == field(base, 'faith_id'),
                    'Recipient own Rite/Faith changed across arms')
        b, x, y = decimal(field(base, 'raw_decimal')), decimal(field(own, 'raw_decimal')), decimal(field(holy, 'raw_decimal'))
        pairs.append({'character_id': target, 'baseline': base, 'personal_after': own, 'enshrine_after': holy,
                      'personal_delta_raw_decimal': str(x-b), 'enshrine_delta_raw_decimal': str(y-b),
                      'enshrine_minus_personal_raw_decimal': str(y-x), 'raw_scale': 100000,
                      'single_site_contribution_attributed': False})
    wallet_deltas: Object = {}
    for name, row in (('personal', p), ('enshrine', e)):
        base_wallet = mapping(field(field(row, 'before'), 'wallet'), 'original wallet')
        after_wallet = mapping(field(field(row, 'after'), 'wallet'), 'after wallet')
        delta: Object = {}
        for resource in ('gold', 'prestige', 'piety'):
            key = resource + '_raw_decimal'
            delta[key] = str(decimal(field(after_wallet, key)) - decimal(field(base_wallet, key)))
        wallet_deltas[name] = delta
    return {'schema': 'faith-e02-artifact-pair-comparison-v1', 'pair_core': json_value(field(p, 'pair_core')),
            'machine_id': json_value(field(p, 'machine_id')), 'observed_at_utc': datetime.now(timezone.utc).isoformat(),
            'status': 'SAME_SOURCE_TWO_ARMS_OBSERVED', 'named_metric': 'knight_effectiveness_raw',
            'recipient_comparisons': json_value(pairs), 'observed_wallet_deltas': wallet_deltas,
            'total_payment_observed': False, 'site_attribution_observed': False,
            'selected_site_contribution_raw': None, 'cache_generation_time_known': False,
            'gameplay_submitted_by_join': False, 'business_pass': False, 'product_release_pass': False,
            'a2_draft_evidence': json_value(field(p, 'a2')), 'already_closed_equipment_film_slot_reopened': False}


def stable_read(path: Path) -> tuple[Object, Pin]:
    require(path.is_file() and not path.is_symlink(), 'Original regular file required')
    before = pin(path)
    value = read(path)
    require(pin(path) == before, 'Original bytes changed while reading')
    return value, before


def load_original_arm(path: Path, arm: str) -> tuple[Object, Pin]:
    require(path.name == RESULT and path.parent.name == arm and path.is_absolute(),
            'Use the immutable fixed pair-root/arm/original result; no arbitrary offline replacement')
    row, arm_pin = stable_read(path)
    core, _ = stable_read(path.parent.parent / 'pair-core.json')
    require(core == field(row, 'pair_core'), 'Original pair-core record differs')
    for key in ('native_dll', 'native_qualification', 'previous_pending', 'previous_known_world_result'):
        parse_pin(field(core, key))
    sources = [parse_pin(x) for x in array(field(row, 'caller_sources'), 'original selected caller sources')]
    require(len(sources) == 3 and {Path(x['path']).name for x in sources} == {
        'faith_e02_artifact_pair_contract.py', 'faith_e02_artifact_pair_queue.py', 'faith_e02_artifact_pair_adapter.py'},
        'Original three caller sources must still match their executed bytes')
    public_records = [parse_pin(x) for x in array(field(row, 'public_native_record_pins'), 'original public control records')]
    require(len(public_records) > 0, 'Actual immutable CaseClient rows are required, not a self-reported status')
    outputs = {Path(x['path']).parent for x in public_records}
    require(len(outputs) == 1, 'Original controls crossed public case outputs')
    output = next(iter(outputs))
    require(output.name == 'case-output' and output.parent.name == field(row, 'run_id'),
            'Only the actual common managed case-output path may substantiate this result')
    actual_copy, actual_copy_pin = stable_read(output / RESULT)
    require(actual_copy == row and actual_copy_pin['bytes'] == arm_pin['bytes'] and actual_copy_pin['sha256'] == arm_pin['sha256'],
            'The pair copy must be the same original public adapter bytes')
    run_id = text(field(row, 'run_id'), 'actual managed run')
    actual_pid = integer(field(row, 'actual_pid'), 'actual PID', 1)
    actual_generation = text(field(row, 'actual_connection_generation_decimal'), 'actual generation decimal')
    require(re.fullmatch('[1-9][0-9]*', actual_generation) is not None, 'Canonical positive generation required')
    for record in public_records:
        control, checked = stable_read(Path(record['path']))
        require(checked == record and Path(record['path']).name.endswith('.actual-results.json'), 'Public control source changed')
        for step in array(field(control, 'rows'), 'actual original rows'):
            if 'after_snapshot' not in mapping(step, 'original control row'):
                require(field(step, 'ok') is False, 'A successful original row cannot omit its native frame')
                continue  # An unknown/failed ACK contributes no current-frame proof.
            current = frame(field(step, 'after_snapshot'), run_id)
            require(current.player == PLAYER and current.date == DATE and current.pid == actual_pid and
                    str(current.generation) == actual_generation, 'Original public native rows crossed the paired world')
    # native-report.json is appendable through normal Quit. Its case-return observation
    # is retained as such; immutable CaseClient rows above provide the actual join proof.
    observed_report = field(row, 'original_native_report')
    if observed_report is not None: parse_pin(observed_report, verify=False)
    return row, arm_pin


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--personal', required=True, type=Path)
    parser.add_argument('--enshrine', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    personal, personal_pin = load_original_arm(args.personal, 'personal')
    enshrine, enshrine_pin = load_original_arm(args.enshrine, 'enshrine')
    require(args.personal.parent.parent.resolve() == args.enshrine.parent.parent.resolve(), 'One stable actual pair evidence root')
    result = combine(personal, enshrine)
    result['original_arm_records'] = [object_value(personal_pin), object_value(enshrine_pin)]
    result['immutable_public_control_sources_verified'] = True
    result['normal_close_qualified_by_join'] = False
    write_once(args.output, result)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
