"""Join an ordinary native Save to its separately observed normal closure.

This input contract does not rewrite the Save-time GUI=false fields, synthesize
an R08 sampling-OFF receipt, or claim a one-life/native episode identity.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import importlib
import json
from pathlib import Path

import ordinary_supply_b as b
from recovery_seed import rehash
from ck3_mod_acceptance_cases.ordinary_save_contract import native_owner

MACHINE = 'desktop-3fevhd2-1c74096080'
SCHEMA = 'xar.e04.normal-ordinary-save-source.v1'


@dataclass(frozen=True)
class FilePin:
    path: Path
    size: int
    sha256: str

    def json(self) -> dict[str, object]:
        return {'path': str(self.path), 'bytes': self.size, 'sha256': self.sha256}


def file_pin(value: object) -> FilePin:
    row = b.obj(value, 'file pin')
    b.need(set(row) == {'path', 'bytes', 'sha256'}, 'Exact file pin required')
    path = Path(b.text(row['path'], 'file path'))
    size = b.integer(row['bytes'], 'file bytes')
    sha = b.text(row['sha256'], 'file SHA256')
    b.need(path.is_absolute() and size >= 0 and len(sha) == 64 and
           all(c in '0123456789abcdef' for c in sha), 'Canonical file pin required')
    return FilePin(path, size, sha)


def read_pin(value: object) -> dict[str, object]:
    ref = file_pin(value)
    b.need(ref.size <= 1024 * 1024 and b.pin(ref.path) == ref.json(), 'Pinned small original changed')
    return b.obj(json.loads(ref.path.read_bytes()), 'pinned original JSON')


@dataclass(frozen=True)
class Counts:
    actual_days: int
    requested_days: int
    rich_queries: int
    moves: int

    @classmethod
    def parse(cls, value: object) -> Counts:
        row = b.obj(value, 'source counts')
        b.need(set(row) == {'actual_days', 'requested_days', 'rich_queries', 'Move_submissions'},
               'Exact lineage count contract required')
        numbers = tuple(b.integer(row[k], k) for k in
                        ('actual_days', 'requested_days', 'rich_queries', 'Move_submissions'))
        b.need(all(n >= 0 for n in numbers) and numbers[0] <= numbers[1], 'Invalid lineage counts')
        return cls(*numbers)

    def json(self) -> dict[str, object]:
        return {'actual_days': self.actual_days, 'requested_days': self.requested_days,
                'rich_queries': self.rich_queries, 'Move_submissions': self.moves}


@dataclass(frozen=True)
class NormalSeed:
    save: dict[str, object]
    actor: int
    local_player: int
    date_raw: int
    source_run_id: str
    source_pid: int
    source_birth: str
    army: dict[str, object]
    counts: Counts
    provenance: dict[str, object]


def canonical_u64(value: object, label: str) -> str:
    text = b.text(value, label)
    b.need(text.isascii() and text.isdecimal() and str(int(text)) == text and int(text) < 2**64,
           label + ' must be a canonical decimal u64 string')
    return text


def control(ref: object, tool: str) -> tuple[dict[str, object], dict[str, object]]:
    rows = b.array(read_pin(ref).get('rows'), 'original control rows')
    b.need(len(rows) == 1, 'Single original control required')
    row = rows[0]
    plan = b.obj(row.get('plan'), 'original plan')
    b.need(row.get('ok') is True and not row.get('error') and plan.get('tool') == tool,
           'Original control failed, unknown, or has a different tool')
    return row, b.obj(row.get('result'), 'original control result')


def validate_normal_source(context: Mapping[str, object]) -> NormalSeed:
    inputs = b.obj(context.get('case_inputs'), 'case inputs')
    b.need(not {'ordinary_save_recovery', 'normal_checkpoint_receipt',
                'normal_checkpoint_build_receipt'} & inputs.keys(), 'Separate normal ordinary-source contract required')
    cfg = b.obj(inputs.get('normal_ordinary_save'), 'normal ordinary Save source')
    pin_names = {'save_receipt_pin', 'before_pin', 'save_result_pin', 'after_pin', 'normal_close_pin',
                 'host_wait_pin', 'owner_closed_pin', 'source_identity_pin', 'source_loaded_dll_pin',
                 'source_prepared_pin', 'source_runtime_pin'}
    b.need(set(cfg) == pin_names | {'schema', 'machine_id', 'source_counts'}, 'Exact normal-source fields required')
    b.need(cfg['schema'] == SCHEMA and cfg['machine_id'] == MACHINE, 'Normal source schema/machine differs')
    refs = {name: file_pin(cfg[name]) for name in pin_names}
    receipt, close, host = (read_pin(cfg[name]) for name in
                            ('save_receipt_pin', 'normal_close_pin', 'host_wait_pin'))
    owner, identity, loaded = (read_pin(cfg[name]) for name in
                               ('owner_closed_pin', 'source_identity_pin', 'source_loaded_dll_pin'))
    counts = Counts.parse(cfg['source_counts'])
    b.need(Counts.parse(owner.get('lineage_counts')) == counts, 'Source lineage counters changed')
    b.need(owner.get('resource_status') == 'ALL_ORIGINAL_OWNERS_CLOSED' and
           owner.get('normal_GUI_and_retained_OS0_native0_host0') is True and
           b.integer(owner.get('all_scene_author_writers'), 'source active writers') == 0 and
           b.integer(owner.get('future_scene_writes'), 'source future writers') == 0,
           'Original source owners/writers are not actually closed')
    b.need(receipt.get('machine_id') == owner.get('machine_id') == identity.get('machine_id') ==
           loaded.get('machine_id') == MACHINE, 'Original normal source belongs to another machine')
    b.need(receipt.get('status') == 'ORDINARY_SAVE_AND_INDEPENDENT_REHASH_VERIFIED' and
           b.integer(receipt.get('Save_submissions'), 'Save submissions') == 1 and
           receipt.get('one_life_identity_proven') is False, 'Ordinary Save was not independently verified')
    before_row, before = control(cfg['before_pin'], 'ck3_take_snapshot')
    saved_row, saved = control(cfg['save_result_pin'], 'ck3_save_checkpoint')
    after_row, after = control(cfg['after_pin'], 'ck3_take_snapshot')
    b.need(b.text(before_row.get('finished_at'), 'before finished') <= b.text(saved_row.get('started_at'), 'Save started')
           and b.text(saved_row.get('finished_at'), 'Save finished') <= b.text(after_row.get('started_at'), 'after started')
           and before_row.get('id') != after_row.get('id'), 'Independent original Save bracketing order differs')
    old, new = native_owner(before), native_owner(after)
    b.need((old.actor, old.local_player, old.pid, old.generation, old.pipe, old.date_raw, old.run) ==
           (new.actor, new.local_player, new.pid, new.generation, new.pipe, new.date_raw, new.run) and
           new.native_revision > old.native_revision and new.snapshot_id != old.snapshot_id,
           'Original Save brackets changed owner/date or were not independently refreshed')
    birth = canonical_u64(identity.get('created'), 'actual source FILETIME')
    b.need(identity.get('run_id') == owner.get('run_id') == host.get('run_id') == old.run.run_id and
           b.integer(identity.get('pid'), 'source PID') == old.pid == b.integer(loaded.get('pid'), 'loaded PID') and
           canonical_u64(loaded.get('created'), 'loaded source FILETIME') == birth and
           loaded.get('exact_process_and_module_rechecked') is True,
           'Source exact PID/FILETIME/run/loaded-module evidence differs')
    originals = b.array(owner.get('original_evidence'), 'closed owner original evidence')
    for name in ('save_receipt_pin', 'normal_close_pin', 'host_wait_pin'):
        b.need(refs[name].json() in originals, 'Closed owner does not bind the selected original: ' + name)
    review = b.obj(close.get('operator_normal_gui_review'), 'actual operator GUI review')
    retained = b.obj(close.get('retained_handle'), 'actual retained handle')
    native = b.obj(close.get('native_zero_proof'), 'actual native zero proof')
    shutdown = b.obj(native.get('shutdown'), 'actual shutdown')
    b.need(review.get('machine_id') == MACHINE and review.get('run_id') == old.run.run_id and
           review.get('normal_gui_quit') is True and review.get('direct_reviewed') is True and
           review.get('autosave_unchecked_observed') is True and review.get('pid') == old.pid and
           review.get('create_time') == retained.get('create_time') and
           close.get('normal_close_qualified') is True and close.get('cleanup_ok') is True and
           retained.get('actual_retained_os0') is True and b.integer(retained.get('pid'), 'retained PID') == old.pid and
           b.integer(retained.get('exit_code'), 'retained exit') == 0 and
           b.integer(native.get('pid'), 'native PID') == old.pid and
           b.integer(native.get('process_exit_code'), 'native exit') == 0 and
           b.integer(shutdown.get('ck3_pid'), 'shutdown PID') == old.pid and
           shutdown.get('tree_gone') is True and shutdown.get('cleanup_proven') is True and
           host.get('actual_original_popen_wait') is True and b.integer(host.get('returncode'), 'original host exit') == 0,
           'Actual normal GUI/retained OS0/native0/original host0 is not fully proven')
    prepared, runtime = (read_pin(cfg[name]) for name in ('source_prepared_pin', 'source_runtime_pin'))
    manifest = read_pin(runtime.get('manifest'))
    preparation = b.obj(prepared.get('preparation'), 'source preparation')
    profile = b.obj(preparation.get('profile_preparation'), 'source vanilla profile')
    profile_receipt = read_pin(profile.get('preparation'))
    startup = b.obj(prepared.get('startup'), 'source startup')
    paths = b.obj(runtime.get('paths'), 'source runtime paths')
    native_ref = b.obj(manifest.get('native_source_index'), 'native source index')
    native_index = read_pin({'path': paths['native_source_index'], 'bytes': native_ref['bytes'],
                             'sha256': native_ref['sha256']})
    game = b.obj(manifest.get('game'), 'frozen source game')
    hello = b.obj(b.obj(before.get('diagnostics'), 'source diagnostics').get('hello'), 'source native hello')
    b.need(manifest.get('machine_id') == preparation.get('machine_id') == native_index.get('machine_id') == MACHINE and
           runtime.get('manifest') == prepared.get('runtime_manifest') and profile.get('vanilla_profile') is True and
           profile.get('fixture_mounted') is False and b.integer(profile.get('product_file_count'), 'source products') == 0 and
           startup.get('state_dir') == profile_receipt.get('state_dir') == old.run.state_dir and
           profile_receipt.get('fixture_mounted') is False and
           profile_receipt.get('game_version') == game.get('version') == '1.20.0.4' and
           profile_receipt.get('exe_sha256') == game.get('exe_sha256') ==
               b.text(hello.get('expected_ck3_sha256'), 'native expected EXE').lower() and
           hello.get('ck3_build_match') is True and
           b.obj(native_index.get('runtime_native_tools'), 'source native tools').get('dll') == loaded.get('module') and
           native_index.get('frozen_file_id') == loaded.get('file_id'), 'Source vanilla EXE/profile/loaded DLL binding differs')
    proof = b.obj(receipt.get('ordinary_save_proof'), 'ordinary Save proof')
    fact = b.obj(proof.get('file'), 'original materialized file')
    independent = b.obj(receipt.get('independent_consumer_file_rehash'), 'independent source file rehash')
    b.need(proof.get('status') == 'verified' and proof.get('scope') == 'producer_materialization_and_native_bracketing' and
           proof.get('one_life_identity_proven') is False and proof.get('same_retained_case_client') is True and
           proof.get('independent_after_request') is True and proof.get('actor') == old.actor and
           proof.get('managed_run_id') == old.run.run_id and proof.get('before_snapshot_id') == old.snapshot_id and
           proof.get('after_snapshot_id') == new.snapshot_id and saved == receipt.get('original_Save_result'),
           'Ordinary Save proof does not join the retained original brackets')
    ck = b.obj(saved.get('checkpoint'), 'saved checkpoint')
    submission = b.obj(saved.get('submission'), 'Save submission')
    b.need(saved.get('step') == 'save-checkpoint' and saved.get('accepted') is True and
           saved.get('backend_id') == 'native-headless' and
           b.obj(saved.get('materialization'), 'materialization').get('available') is True and
           b.integer(submission.get('sequence'), 'Save sequence') > 0 and
           b.integer(submission.get('date_raw'), 'Save date') == old.date_raw and
           {'episode_run_id', 'episode_character_id', 'succession_lifecycle'} <= ck.keys() and
           all(ck[k] is None for k in ('episode_run_id', 'episode_character_id', 'succession_lifecycle')) and
           ck.get('status') == 'saved' and ck.get('strategy') == 'native-autosave-command-v1' and
           ck.get('episode_projection') == 'native_campaign' and ck.get('date_raw') == old.date_raw == fact.get('date_raw') and
           b.integer(ck.get('size'), 'Save size') == b.integer(fact.get('bytes'), 'verified size') ==
               b.integer(independent.get('bytes'), 'independent size') and
           ck.get('sha256') == fact.get('sha256') == independent.get('sha256') and
           independent.get('same_handle') is True and independent.get('consumer_rehashed_file') is True,
           'Original producer/ordinary episode/independent file facts differ')
    source_path = Path(b.text(ck.get('path'), 'producer Save path')).resolve()
    b.need(source_path == Path(b.text(fact.get('path'), 'proof Save path')).resolve() ==
           Path(b.text(independent.get('path'), 'independent Save path')).resolve() ==
           (Path(old.run.state_dir) / 'profile/save games/xar_checkpoint.ck3').resolve(), 'Save paths differ')
    seed = b.obj(context.get('saved_campaign'), 'new saved-campaign input')
    b.need(b.integer(seed.get('player_id'), 'selected actor') == old.actor and
           b.integer(seed.get('date_raw'), 'selected date') == old.date_raw and
           b.integer(seed.get('bytes'), 'selected bytes') == fact.get('bytes') and seed.get('sha256') == fact.get('sha256'),
           'Selected saved-campaign input differs from the normal source')
    rehash(Path(b.text(seed.get('save'), 'selected Save path')).resolve(strict=True), fact)
    source_armies = b.array(after.get('player_armies'), 'saved source armies')
    selected = [row for row in source_armies if row.get('army_id') == 18]
    b.need(len(selected) == 1, 'Selected source Army18 missing/duplicated')
    army = b.army(after, 18, old.actor)
    provenance: dict[str, object] = {'kind': 'normal-ordinary-save-with-independent-normal-closure',
        'schema': SCHEMA, 'machine_id': MACHINE, 'source_run_id': old.run.run_id,
        'original_sources': cfg, 'source_exact_created': birth, 'one_life_identity_proven': False,
        'original_Save_time_GUI_fields_preserved': True, 'normal_GUI_completed_independently': True,
        'source_game_state_claimed': False, 'fresh_coldload_identity_route_required_before_actions': True,
        'legacy_retained_handle_create_time_preserved_without_FILETIME_reconstruction': True,
        'inherited_lineage_counts': counts.json()}
    return NormalSeed(seed, old.actor, old.local_player, old.date_raw, old.run.run_id, old.pid, birth, army, counts, provenance)


def prepare_normal(context: Mapping[str, object]) -> dict[str, object]:
    seed = validate_normal_source(context)
    from ck3_live_run_id import current_machine_id
    b.need(current_machine_id() == MACHINE, 'Normal preparation target machine differs')
    module = importlib.import_module('ck3_mod_acceptance_prepare')
    materialize: object = getattr(module, 'materialize_product_profile')
    finish: object = getattr(module, 'finish_product_profile')
    if not callable(materialize) or not callable(finish):
        raise ValueError('Existing public profile primitives are not callable')
    values = b.obj(context.get('case_inputs'), 'case inputs')
    profile = b.obj(materialize(context, None, values['plain_configuration']), 'actual materialized profile')
    finished = b.obj(finish(context, profile, provenance={**seed.provenance,
        'formal_ABC_arm': False, 'open_kaishek': {'status': 'not-applicable',
        'reason': 'No script/IR changes; normal ordinary native Save source only.'}}), 'finished profile')
    initial = Path(b.text(context.get('output'), 'preparation output')) / 'initial-plan.json'
    with initial.open('xb') as stream:
        stream.write(b'{"steps": []}\n')
    inventory = b.obj(profile.get('product_inventory'), 'vanilla product inventory')
    return {'machine_id': MACHINE, 'startup': {'mode': 'saved_campaign', 'state_dir': profile['state_dir'],
        'saved_campaign': {**seed.save, 'product_inventory': inventory['path']}}, 'initial_plan': b.pin(initial),
        'profile_preparation': finished, 'files': profile['files'], 'fixture_mounted': False,
        'runtime_status': 'NOT_RUN', 'formal_ABC_arm': False, 'business_contract_applicable': False, 'business_pass': False}
