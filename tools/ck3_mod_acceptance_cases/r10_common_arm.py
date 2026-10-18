"""Formal staged R10 IO on one already-owned public CaseClient.

Normal constructor, actual public allocation ID, normal-source/profile proof.
The old relay constructors are not instantiated, renamed or bypassed. Their
pure consumers/business methods are composed over this explicit common IO.
"""
from pathlib import Path
from datetime import datetime, timezone
from copy import deepcopy
from types import SimpleNamespace
import importlib
import json
import re
import subprocess
import sys
import time

from .r10_prepare_adapter import CommonRequestRelay, module, need, pin, small_json


def full_query_with_one_same_date_rebound(io, name, frame, refs, ids):
    """The existing R05 explicit drift only; never retry an action/lost result."""
    from xar_autoplayer.bridge.r05_supply_observation_case import StrengthRevisionDrift, frame_identity
    def query(current, suffix):
        return io.request(name + '-strengths' + suffix, 'ck3_query_army_strengths', {
            'army_ids': ids, 'expected_revision': current['revision'], 'profile': 'observed_history_full_v1',
            'ordered_refill_entry_mode': 'observed_prepared', 'ordered_besieging_entry_mode': 'observed_prepared'})
    try:
        row, query_refs = query(frame, '')
        return frame, refs, row, query_refs
    except StrengthRevisionDrift as first:
        fresh, fresh_refs = io.snapshot(name + '-readonly-rebound')
        proof = {'first_RED': first.proof, 'before': frame, 'fresh': fresh, 'retry_limit': 1,
                 'action_or_day_replayed': False}
        io.client.checkpoint(name + '-readonly-rebound-frames', proof)
        need(frame.get('paused') is True and fresh.get('paused') is True
             and frame['date_raw'] == fresh['date_raw'] and frame_identity(frame) == frame_identity(fresh),
             'Readonly full-result rebound crossed date/paused/lifetime')
        need(all(f.get('active_event') is None and f.get('pending_character_interaction') is None for f in (frame, fresh)),
             'Readonly full-result rebound found pending modal')
        def selected(f):
            rows = {r['army_id']: r for r in f['player_armies']}
            need(set(ids) <= set(rows), 'Readonly rebound selected Army disappeared')
            return {aid: (rows[aid]['owner_character_id'], rows[aid]['current_province_id']) for aid in ids}
        need(selected(frame) == selected(fresh), 'Readonly rebound selected owner/location changed')
        row, query_refs = query(fresh, '-rebound-once')
        return fresh, fresh_refs, row, query_refs


def _common_origin_checkpoint(normal, source, machine, plan):
    """Join original small common records; keep null native episode/lifecycle.

    The exact profile preparation already validated the opaque save bytes via
    checkpoint_source. Recheck its original metadata chain, never rehash Save.
    """
    need(normal.get('machine_id') == machine
         and source.get('normal_source_kind') == 'original-common-native-campaign-with-normal-closure'
         and source.get('original_episode_fields_preserved') is True
         and source.get('source_run_id') == normal.get('source_run_id'), 'Actual common normal-source preparation absent')
    need(normal['actual_save']['pointer'] == '/rows/0/result/checkpoint'
         and normal['independent_after']['pointer'] == '/rows/0/after_snapshot', 'Original common normal pointers differ')
    saved_rows = small_json(normal['actual_save']['reference'])['rows']
    after_rows = small_json(normal['independent_after']['reference'])['rows']
    need(len(saved_rows) == len(after_rows) == 1, 'Ambiguous common normal-source rows')
    row, independent = saved_rows[0], after_rows[0]
    action, body = row.get('plan') or {}, row.get('result') or {}
    need(row.get('ok') is True and (action.get('tool') == 'ck3_save_checkpoint'
         or (action.get('tool') == 'ck3_execute_step' and (action.get('args') or {}).get('step') == 'save-checkpoint'))
         and body.get('accepted') is True and body.get('step') == 'save-checkpoint', 'Original common normal Save unavailable')
    need(independent.get('ok') is True and (independent.get('plan') or {}).get('tool') == 'ck3_take_snapshot'
         and row['id'] != independent['id'] and row['finished_at'] <= independent['started_at'], 'Independent normal Save after-frame absent')
    saved = body.get('checkpoint') or {}; frame = row.get('after_snapshot') or {}
    actor = (frame.get('played_character') or {}).get('character_id')
    pid = (frame.get('diagnostics') or {}).get('bridge_pid'); gen = (frame.get('diagnostics') or {}).get('connection_generation')
    run = normal['source_run_id']; date = saved.get('date_raw'); player = frame.get('local_player_id')
    origin_ref = normal['normal_campaign_provenance']['profile']; origin = small_json(origin_ref)
    need(origin_ref['sha256'] == source['build_receipt']['sha256']
         and origin.get('fixture_mounted') is False and origin.get('game_version') == plan['build']['version']
         and str(origin.get('steam_build_id')) == str(plan['build']['steam_build'])
         and origin.get('exe_sha256') == plan['build']['exe_sha256']
         and small_json(origin['files']['dlc_load.json']) == {'enabled_mods': [], 'disabled_dlcs': []}, 'Original normal profile/build differs')
    need(type(actor) is int and actor > 0 and type(player) is int and player >= 0 and type(pid) is int and pid > 0
         and gen is not None and type(date) is int and saved.get('status') == 'saved'
         and saved.get('episode_projection') == 'native_campaign'
         and Path(saved['path']).resolve().parent == Path(origin['profile_dir']).resolve() / 'save games', 'Original common native campaign source differs')
    aid = normal['independent_after']['army']['army_id']
    for current in (frame, independent.get('after_snapshot') or {}):
        diag = current.get('diagnostics') or {}; binding = current.get('managed_campaign_run_binding') or {}
        owners = [a for a in current.get('player_armies', []) if a.get('army_id') == aid]
        need(current.get('episode_projection') == 'native_campaign' and current.get('date_raw') == date
             and current.get('paused') is True and current.get('map_ready') is True
             and (current.get('played_character') or {}).get('character_id') == actor and current.get('local_player_id') == player
             and diag.get('bridge_pid') == pid and diag.get('connection_generation') == gen and binding.get('run_id') == run
             and Path(binding.get('state_dir', '')).resolve() == Path(origin['state_dir']).resolve()
             and len(owners) == 1 and owners[0].get('owner_character_id') == actor, 'Original common source frame/owner drift')
    life = saved.get('succession_lifecycle')
    need(saved.get('episode_character_id') in (None, actor) and saved.get('episode_run_id') in (None, run)
         and life == source.get('source_lifecycle')
         and (life is None or (isinstance(life, dict) and life.get('lifecycle') == 'ordinary_campaign_succession' and life.get('xar_enabled') == 'xar_off'
         and life.get('source') == 'pure-vanilla-enabled-mods-empty' and life.get('pact_contract') == 'absent_by_fresh_campaign_xar_off_contract')),
         'Original common lifecycle conflicts; never manufacture an episode')
    need(saved['sha256'] == source['save']['sha256'] == normal['source']['sha256']
         and saved['size'] == source['save']['bytes'] == normal['source']['bytes'], 'Prepared common opaque source identity differs')
    closure = normal['closure']; cleanup = small_json(closure['cleanup']); close = small_json(closure['normal_close'])
    host = small_json(closure['host_original_wait']); clean = cleanup.get('cleanup') or {}
    retained = close.get('retained_handle') or {}; native = close.get('native_zero_proof') or {}; shut = native.get('shutdown') or {}
    bound = cleanup.get('actual_binding') or {}
    need(cleanup.get('machine_id') == machine and cleanup.get('run_id') == run and clean.get('errors') == []
         and clean.get('normal_Save_verified') is True and clean.get('sampling_OFF_clear_verified') is True
         and (clean.get('Save_result') or {}).get('checkpoint') == saved and bound.get('pid') == pid
         and bound.get('run_id') == run and type(bound.get('create_time')) in (int, float)
         and bound['create_time'] > 0 and bound['create_time'] == retained.get('create_time'), 'Original common cleanup/Save binding differs')
    need(close.get('normal_close_qualified') is True and retained.get('actual_retained_os0') is True
         and retained.get('pid') == pid and retained.get('exit_code') == 0 and native.get('pid') == pid
         and native.get('process_exit_code') == 0 and shut.get('ck3_pid') == pid and shut.get('tree_gone') is True
         and shut.get('cleanup_proven') is True and host.get('run_id') == run
         and host.get('actual_original_popen_wait') is True and host.get('returncode') == 0, 'Original common normal closure unverified')
    return saved, actor


def validate_normal_common_source(context, prepared, frozen, profile, inventory, normal, *,
                                  machine, source_head, plan):
    """Pure join of exact common DTOs; never infer vanilla from product/run ID."""
    need(context.get('schema') == 'ck3-mod-acceptance-run-context-v1', 'Actual public common context required')
    run_id = context.get('run_id')
    need(type(run_id) is str and run_id == frozen.get('run_id')
         and Path(context['run_dir']).name == run_id, 'Actual public allocated run differs')
    need(frozen.get('identity_allocation', {}).get('machine_id') == machine,
         'Actual common allocator machine differs')
    need(prepared.get('schema') == 'ck3-mod-acceptance-prepared-case-v1'
         and prepared.get('product') == context.get('product') and prepared.get('case') == context.get('case'),
         'Common prepared product/case differs')
    startup = prepared.get('startup', {})
    seed = startup.get('saved_campaign', {})
    need(startup.get('mode') == 'saved_campaign' and Path(startup['state_dir']).resolve() == Path(frozen['state_dir']).resolve(),
         'Actual common prepared state/mode differs')
    need(inventory.get('schema') == 'ck3-saved-campaign-vanilla-profile-v1'
         and inventory.get('enabled_mods') == [] and inventory.get('product_files') == []
         and profile.get('fixture_mounted') is False,
         'Normal vanilla must be proved by actual empty-mod profile, not mod_key')
    need(Path(inventory['profile_path']).resolve() == Path(profile['profile_dir']).resolve()
         == Path(startup['state_dir']).resolve() / 'profile', 'Actual normal profile paths differ')
    if normal.get('schema') == 'xar.e04.normal-source-promotion-candidate.v1':
        saved, actual_actor = _common_origin_checkpoint(normal,
            profile.get('provenance', {}).get('normal_checkpoint', {}), machine, plan)
    else:
        saved = normal.get('body', {}).get('checkpoint', {})
        life = saved.get('succession_lifecycle') or {}
        need(normal.get('is_error') is False and normal.get('body', {}).get('accepted') is True
             and saved.get('status') == 'saved' and life.get('lifecycle') == 'ordinary_campaign_succession'
             and life.get('xar_enabled') == 'xar_off' and life.get('source') == 'pure-vanilla-enabled-mods-empty'
             and life.get('pact_contract') == 'absent_by_fresh_campaign_xar_off_contract',
             'Actual normal-source Save/lifecycle unavailable')
        actual_actor = saved.get('episode_character_id')
    common = plan.get('normal_save', {})
    need(seed.get('sha256') == saved.get('sha256') == common.get('sha256')
         and seed.get('bytes') == saved.get('size') == common.get('bytes')
         and seed.get('player_id') == actual_actor
         and seed.get('date_raw') == saved.get('date_raw') == plan.get('t0_raw'),
         'Normal source/prepared/frozen common S0 differs')
    source = profile.get('provenance', {}).get('normal_checkpoint', {})
    need(source.get('save', {}).get('sha256') == common['sha256']
         and source.get('save', {}).get('bytes') == common['bytes']
         and source.get('actor_id') == seed['player_id'] and source.get('date_raw') == seed['date_raw'],
         'Profile preparation does not bind actual normal checkpoint')
    need(plan.get('build', {}).get('source_head') == source_head, 'Actual source differs from frozen plan')
    return {'machine_id': machine, 'run_id': run_id, 'mod_key': frozen.get('mod_key'),
        'normal_save_sha256': common['sha256'], 'actor': seed['player_id'], 'date_raw': seed['date_raw'],
        'normal_source': 'actual_normal_Save_and_empty_mod_profile', 'original_context_modified': False}


A_ONLY_SCHEMA = 'xar.e04.r10-independent-a-case.v1'


def independent_a_phase(context):
    """An explicit new public case; the joint A/B/C case keeps its old gate."""
    if context['case_contract'].get('schema') != A_ONLY_SCHEMA:
        return None
    need(context.get('case') == 'r10-independent-a'
         and context['case_inputs']['arm'].get('label') == 'A', 'Independent A case/label differs')
    phase = context['case_inputs']['arm'].get('phase')
    need(phase in ('collect-baseline', 'execute'), 'Explicit independent A phase required')
    return phase


def public_plan_baseline(context, plan, evidence, compare):
    """Select the existing A-only consumer without weakening joint PLAN."""
    phase = independent_a_phase(context)
    if phase is None:
        return compare.check_plan(plan, evidence)
    need(plan.get('execution_scope') == 'independent-A-only'
         and plan.get('strategies', {}).get('B') is None
         and plan.get('strategies', {}).get('C') is None
         and plan.get('compare_fees') is False,
         'Independent A neither supplies B/C sites nor qualifies fee/joint comparison')
    if phase == 'collect-baseline':
        need(plan.get('status') == 'baseline-capture' and plan.get('baseline') is None
             and plan.get('original_regiment_ids') == [], 'Readonly A baseline seed differs')
        return None
    need(plan.get('status') == 'frozen', 'Independent A execution requires a frozen plan')
    a = importlib.import_module('strategy_a')
    return a._whole(plan['baseline'], plan, evidence)[0]


class CommonArmIO:
    """Current public run constructor, complete packets, once actions and clocks."""
    def __init__(self, context, client):
        from ck3_live_run_id import current_machine_id
        from ck3_mod_acceptance_cases.r08_writer_common_adapter import retained_creation_filetime
        self.context = context
        self.client = client
        self.repo = Path(context['repo_root']).resolve()
        self.run = Path(context['run_dir']).resolve()
        self.settings = context['case_inputs']['arm']
        self.machine = current_machine_id()
        self.source = subprocess.check_output(['git', '-C', str(self.repo), 'rev-parse', 'HEAD'], text=True).strip()
        self.plan = small_json(self.settings['plan'])
        self.prepared = client.selection.prepared
        need(self.prepared is not None, 'Actual common prepared case required')
        profile_ref = self.prepared['preparation']['profile_preparation']['preparation']
        profile = small_json(profile_ref)
        inventory_ref = self.prepared['preparation']['profile_preparation']['product_inventory']
        inventory = small_json(inventory_ref)
        normal_ref = context['case_inputs']['normal_checkpoint_receipt']
        normal = small_json(normal_ref)
        need(profile.get('provenance', {}).get('normal_checkpoint', {}).get('receipt', {}).get('sha256') == normal_ref['sha256']
             == self.plan.get('normal_save', {}).get('save_receipt', {}).get('sha256'),
             'Actual normal-source receipt pin differs from prepared profile or frozen S0')
        normal_binding = validate_normal_common_source(client.context, self.prepared, client.frozen,
            profile, inventory, normal, machine=self.machine, source_head=self.source, plan=self.plan)
        need(self.settings['label'] in ('A', 'B', 'C'), 'Formal arm label required')
        self.label = self.settings['label']
        self.state_dir = Path(self.prepared['startup']['state_dir']).resolve()
        self.native_session = self.state_dir / 'native-session'
        self.deadline = datetime.fromisoformat(self.settings['deadline_utc'].replace('Z', '+00:00'))
        need(self.deadline.tzinfo is not None, 'Explicit actual arm UTC deadline required')
        self.capacity_ref = self.settings['capacity_admission']
        self.capacity = small_json(self.capacity_ref)
        cap = self.capacity
        need(cap.get('admitted') is True and cap.get('root_atomic_adoption_required') is False
             and cap.get('policy_version') == '1.0.0' and cap.get('machine_id') == self.machine
             and cap.get('source_head') == self.source and cap.get('run_id') == self.run.name,
             'Actual Root-adopted common run capacity required')
        need(cap.get('root_adopted_at_utc') and cap.get('source_binding', {}).get('new_clean_integrated_source_head') == self.source
             and datetime.fromisoformat(cap['quota_review_at_utc'].replace('Z', '+00:00')) == self.deadline,
             'Actual capacity source/deadline differs')
        roots = cap['component_roots']
        need(Path(roots['driver']).resolve() == self.run and Path(roots['profile']).resolve() == self.state_dir,
             'Capacity does not cover actual common run and prepared profile')
        self.runtime_total_budget_bytes = self.settings['max_runtime_total_bytes']
        need(type(self.runtime_total_budget_bytes) is int and 17 * 1024 * 1024 <= self.runtime_total_budget_bytes
             <= cap['component_ceiling_bytes']['driver'], 'Explicit driver bound exceeds actual Root capacity')
        self.packet_limit = self.settings['max_evidence_file_bytes']
        need(self.packet_limit in (16 * 1024 * 1024, 32 * 1024 * 1024), 'Existing complete evidence bound required')
        self.relay = CommonRequestRelay(context, client, machine=self.machine)
        self.client = self.relay.client
        self.client.retain_process()
        created = retained_creation_filetime(self.client)
        frame = self.client.snapshot()
        need(frame['diagnostics']['bridge_pid'] == self.client._process['pid']
             and frame['played_character']['character_id'] == normal_binding['actor'], 'Actual common runtime actor/PID differs')
        self.binding = {'pid': self.client._process['pid'], 'process_create_time_100ns': created,
            'generation': frame['diagnostics']['connection_generation'], 'actor': frame['played_character']['character_id'],
            'episode': frame['episode_run_id'], 'army_id': context['case_inputs']['army_id'],
            'native_carmy_id': context['case_inputs'].get('native_carmy_id')}
        need(type(self.binding['native_carmy_id']) is int and self.binding['native_carmy_id'] != -1,
             'Actual resolved CArmy full ID required before formal arm')
        self.case = Path(context['output']) / ('r10-' + self.label)
        self.case.mkdir(exist_ok=False)
        self.ledger = self.case
        self.serial = 0
        self.pending = False
        self.normal_save_attempted = False
        self.last = frame
        self.assets = self.run
        self.a = SimpleNamespace(army_id=self.binding['army_id'], attempt='arm-' + self.label.lower(),
            stage='baseline', merge_destination='source', merge_source_army_id=None, resume_baseline_strength_response=None)
        self.attempt = self.case / 'baseline'
        self.attempt.mkdir()
        self.meta = {'machine_id': self.machine, 'source_head': self.source, 'run_id': self.run.name,
            'binding': self.binding, 'case': 'R10-' + self.label, 'normal_common_source': normal_binding,
            'normal_source_receipt': normal_ref, 'common_profile_preparation': profile_ref,
            'capacity_admission': self.capacity_ref, 'actual_common_ID_preserved': True,
            'SDK_connection_created': False, 'research_card_closed': False}
        proof = self.client.checkpoint('r10-' + self.label + '-actual-common-runtime-proof', {
            **self.meta, 'created_filetime_100ns': created, 'public_frozen_argv': client.context['frozen_argv'],
            'public_prepared_case': client.context['prepared_case'], 'runtime_source': 'same_retained_common_OS_handle_and_native_snapshot'})
        base = self.repo / 'promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02'
        self.base = base
        sys.path.insert(0, str(base / 'comparison'))
        self.c = importlib.import_module('r10_compare')
        need(Path(self.c.__file__).resolve() == base / 'comparison/r10_compare.py', 'Comparison module source differs')
        projection = module(base / 'root_runtime_projection.py', 'r10_common_filetime_projection')
        dll = self.client.selection.manifest['native']['dll']['sha256']
        evidence_options = ({'capacity_admissions': [{'path': self.capacity_ref['path'], 'sha256': self.capacity_ref['sha256']}],
            'expected_source_head': self.source, 'expected_machine_ids': [self.machine]} if self.packet_limit > 16 * 1024 * 1024 else {})
        self.e = self.c.Evidence(Path(self.settings['evidence_root']), max_file_bytes=self.packet_limit, **evidence_options)
        self.runtime = {'machine_id': self.machine, 'started_at_utc': projection.filetime_utc(created),
            'pid': self.binding['pid'], 'process_create_time_100ns': created,
            'connection_generation': self.binding['generation'], 'episode': self.binding['episode'],
            'player_character_id': self.binding['actor'], 'source_head': self.source,
            'native_dll_sha256': dll, 'source_proof': self.relative(pin(proof))}
        self.independent_a_phase = independent_a_phase(context)
        if self.independent_a_phase != 'collect-baseline':
            frozen = datetime.fromisoformat(self.plan['frozen_at_utc'].replace('Z', '+00:00'))
            need(frozen < datetime.fromisoformat(self.runtime['started_at_utc']),
                 'Formal arm must independently cold-start after plan freeze')
        need(self.plan['build']['native_dll_sha256'] == dll, 'Frozen plan DLL differs from current common DLL')
        public_plan_baseline(context, self.plan, self.e, self.c)
        self.r = module(base / 'split_merge/root_relay.py', 'r10_existing_split_business')
        from xar_autoplayer.bridge import army_split_merge_observation_12004 as observation
        from xar_autoplayer.bridge.army_replenishment_records_contract import normalize_regiment_replenishment_records_v1
        self.observation = observation
        self.normalize = normalize_regiment_replenishment_records_v1
        self.consumer = module(base / 'split_merge/army_split_transfer_assertions_12004.py', 'r10_existing_split_consumer')
        self._clock = ClockFacade(self)
        self.guard()
        feature_frame, _ = self.snapshot('cold-loaded-features-frame')
        feature_row, feature_refs = self.request('cold-loaded-features', 'ck3_query_loaded_feature_manifest_v1',
            {'expected_revision': feature_frame['revision']})
        feature_body = feature_row['body']
        need(feature_body.get('accepted') is True and feature_body.get('loaded_feature_manifest_ready') is True
             and all(feature_body.get('queried_' + key) == feature_frame[key]
                     for key in ('snapshot_id', 'revision', 'native_revision')),
             'Actual independently cold loaded-feature manifest unavailable or crossed frame')
        features = {key: deepcopy(feature_body[key]) for key in
                    ('build', 'effective_feature_flags', 'script_dlc_keys', 'entitlements')}
        feature_view = self.client.checkpoint('r10-' + self.label + '-cold-loaded-features', {
            'machine_id': self.machine, 'loaded_features': features, 'original_native_source': feature_refs['response'],
            'scope': 'actual native semantic loaded features, excludes observation date/revision; entitlements remain provenance-unclosed'})
        self.features = {'source': self.relative(pin(feature_view)), 'pointer': '/loaded_features'}
        self.e.bound(self.features)

    def relative(self, ref):
        path = Path(ref['path']).resolve()
        need(path.is_relative_to(self.e.root), 'Actual small evidence must be under explicit evidence root')
        return {**ref, 'path': path.relative_to(self.e.root).as_posix()}

    def guard(self, extra=0):
        need(datetime.now(timezone.utc) < self.deadline, 'Original arm deadline reached')
        need(small_json(self.capacity_ref) == self.capacity, 'Original Root capacity changed')
        self.client.guard(reserve=180)
        need(self.client.remaining() > 180 + extra, 'Original arm normal-close reserve reached')
        used = 0
        seen = set()
        for root in (self.run, self.native_session):
            if not root.exists(): continue
            for path in root.rglob('*'):
                if path.is_file():
                    actual = path.resolve()
                    if actual not in seen:
                        seen.add(actual); used += path.stat().st_size
        # The original wire range and all three full-body copies persist:
        # normalized-full, public envelope, and the relay response envelope.
        from ck3_mod_acceptance_army_wire import MAX_RANGE
        next_full_bytes = MAX_RANGE + 3 * self.packet_limit
        need(used + next_full_bytes + 16 * 1024 * 1024 <= self.runtime_total_budget_bytes,
              'Actual runtime cannot reserve original wire, three full results and normal-close metadata')

    def request(self, name, tool, arguments):
        self.guard()
        self.serial += 1
        identifier = self.a.attempt + '-' + str(self.serial).zfill(3) + '-' + name
        req = self.run / 'requests' / (identifier + '.json')
        res = self.run / 'responses' / req.name
        req.parent.mkdir(exist_ok=True); res.parent.mkdir(exist_ok=True)
        self.r.write_new(req, {'request_id': identifier, 'tool': tool, 'arguments': arguments,
            'transport_origin': 'derived_common_case_intent_not_SDK_request'})
        self.pending = True
        error = None
        try:
            row = self.relay.request(identifier, tool, arguments, timeout=self.settings['one_day_timeout_seconds'])
        except ValueError as original_error:
            # The common envelope was already durably written for an explicit
            # completed control error; a queue timeout/lost result has no such
            # envelope and must propagate without another query.
            stored = self.relay.refs.get(identifier, {})
            if stored.get('status') != 'error': raise
            row = small_json(stored['envelope'], self.packet_limit)
            error = original_error
        # B's existing stage readers consume the envelope, never a fake Driver ref.
        raw = (json.dumps(row, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
        need(len(raw) <= self.packet_limit, 'Derived common envelope exceeds admitted evidence size')
        with res.open('xb') as stream: stream.write(raw)
        self.pending = False
        if error is not None:
            from xar_autoplayer.bridge.r05_supply_observation_case import is_strength_revision_drift, StrengthRevisionDrift
            original_rows = json.loads(Path(row['common_original']['path']).read_bytes())['rows']
            failure = original_rows[0]
            derived = (row.get('wire_full_result_proof') or {}).get('derived_error')
            if derived is not None: failure = {'ok': False, 'error': derived}
            if tool == 'ck3_query_army_strengths' and is_strength_revision_drift(failure):
                raise StrengthRevisionDrift({'common_error_envelope': pin(res), 'original_common_row': row['common_original']}) from error
            raise error
        if tool == 'ck3_execute_step' and str(arguments.get('step', '')).startswith('research-arm-tactical-daily-sentinel-v1-'):
            from xar_autoplayer.bridge.native_driver import _normalize_tactical_daily_sentinel_status
            status = _normalize_tactical_daily_sentinel_status(row['body']['tactical_daily_sentinel'])
            if status['state'] == 'armed':
                self._clock.active_clock = {'armed': status, 'start': status['starting_date_raw'],
                    'target': status['target_date_raw'], 'original_arm_source': pin(res)}
        return row, {'request': pin(req), 'response': pin(res)}

    def snapshot(self, name, *, paused=True):
        row, refs = self.request(name, 'ck3_take_snapshot', {'include_native_command_history': False})
        frame = row['body']
        self.client.validate_frame(frame, require_event_free=False, require_paused=paused is not False)
        need(frame['diagnostics']['bridge_pid'] == self.binding['pid']
             and frame['diagnostics']['connection_generation'] == self.binding['generation']
             and frame['episode_run_id'] == self.binding['episode']
             and frame['played_character']['character_id'] == self.binding['actor'], 'Actual common frame crossed lifetime')
        self.last = frame
        return frame, refs

    def packet(self, name, *, army_ids=None, split_before_roster=None, raw_file_limit=None, required_army_id=None):
        from xar_autoplayer.bridge.war_cash_private_transport_v1 import normalize_war_cash_current_resources_v1
        frame, refs = self.snapshot(name + '-frame')
        self.r.validate_frame(frame, self.binding)
        ids = self.r.selected_query_ids(frame, army_ids, split_before_roster=split_before_roster)
        capabilities, cap_refs = self.request(name + '-caps', 'ck3_get_capabilities', {})
        frame, refs, result, query_refs = full_query_with_one_same_date_rebound(self, name, frame, refs, ids)
        q = result['body']
        need(q.get('status') == 'available' and (q.get('army_strengths_query_scope') or {}).get('army_ids') == ids,
             'Actual complete selected common full result unavailable')
        self.observation.compare_split_merge_cohorts(q['army_strengths'], q['army_strengths'])
        public_id = result['common_public_step_id']
        qpath = Path(self.client.output) / (public_id + '-derived-normalized-full.json')
        qref = pin(qpath)
        need(json.loads(qpath.read_bytes()) == q, 'Canonical derived full result differs from common response')
        need(qref['bytes'] <= (self.packet_limit if raw_file_limit is None else raw_file_limit(qpath)),
             'Complete common result exceeds existing evidence bound')
        commanders, commander_refs = {}, {}
        for army in q['army_strengths']:
            aid = army['army_id']
            row, ref = self.request(name + '-cmd-' + str(aid), 'ck3_query_army_commander_candidates_v1',
                {'army_id': aid, 'expected_revision': frame['revision']})
            self.observation.read_bound_current_commander(row['body'], frame,
                army_id=aid, native_carmy_id=army['native_carmy_id'])
            commanders[str(aid)] = row['body']; commander_refs[str(aid)] = ref
        cash, cash_ref = self.request(name + '-cash', 'ck3_query_war_cash_current_resources_private_v1',
            {'expected_revision': frame['revision']})
        money = normalize_war_cash_current_resources_v1(cash['body'], snapshot=frame)
        gold = money['current_treasury']
        need(type(gold) is dict and type(gold.get('raw')) is int and gold.get('scale') == 100000,
             'Actual same-frame current treasury unavailable; never fill zero')
        check, check_ref = self.snapshot(name + '-check')
        self.r.same_frame(frame, check)
        derived = {**frame, 'played_character_gold': dict(gold)}
        view = self.client.checkpoint(public_id + '-wallet-frame', {
            'machine_id': self.machine, 'is_error': False, 'body': derived,
            'transport_origin': 'derived_same_frame_native_snapshot_and_cash_current_treasury',
            'snapshot_source': refs['response'], 'cash_source': cash_ref['response'],
            'original_public_snapshot_modified': False})
        return {'frame': derived, 'query': q, 'commanders': commanders, 'capabilities': capabilities['body'],
            'strategy_army_ids': ids, 'excluded_unavailable_cohorts': [],
            'refs': {'snapshot': {**refs, 'response': pin(view)}, 'capabilities': cap_refs,
                'strength_response': query_refs, 'strength_raw': qref, 'commanders': commander_refs,
                'same_frame_readback': check_ref},
            'complete_result_representation': 'production_normalized_native_wire_not_original_Driver',
            'original_wire_proof': result['wire_full_result_proof']}

    def endpoint(self, name, *, army_ids=None):
        packet = self.packet(name, army_ids=army_ids or [self.a.army_id], raw_file_limit=self.e.file_limit)
        refs = packet['refs']; frame = packet['frame']
        delta = frame['date_raw'] - self.plan['t0_raw']
        need(type(delta) is int and 0 <= delta <= 2160 and delta % 24 == 0, 'Actual absolute R10 natural day required')
        ep = {'day': delta // 24, 'snapshot': self.relative(refs['snapshot']['response']),
            'army_result': self.relative(refs['strength_raw']), 'strategy_army_ids': packet['strategy_army_ids'],
            'commander': {'source': self.relative(refs['commanders'][str(packet['strategy_army_ids'][0])]['response']),
                          'pointer': '/body/army_commander_candidates/current_commander/character_id'},
            'loaded_features': self.features}
        self.c.endpoint(ep, self.plan, self.e, self.runtime)
        return ep

    def preview(self, endpoint, target):
        frame = self.c.frame(self.e.json(endpoint['snapshot']), self.runtime)
        row, refs = self.request('preview', 'ck3_execute_step', {
            'step': 'preview-move-army-' + str(self.a.army_id) + '-to-' + str(target),
            'expected_revision': frame['revision']})
        return row['body'], self.relative(refs['response'])

    def claim(self, name, value):
        return self.r.write_new(self.case / (name + '.once.claim.json'), {**self.meta, **value, 'retry_allowed': False})

    def exact_day(self, before_endpoint):
        frame = self.c.frame(self.e.json(before_endpoint['snapshot']), self.runtime)
        need(before_endpoint['day'] < 90, 'Actual absolute D90 reached')
        after, clock = self._clock.exact_day({'frame': frame})
        ref = self.client.checkpoint(self.a.attempt + '-clock-' + str(after['date_raw']), {
            'machine_id': self.machine, 'body': {'clock': clock['stopped']},
            'runtime': self.binding, 'native_status_source': self._clock.last_call_refs,
            'original_clock_adapter': 'r05_supply_observation_case.ObservationIO.exact_day'})
        return after, ref

    def finish_once(self):
        """Pause, converge only our known clock, and Save once before GUI Quit."""
        need(not self.normal_save_attempted, 'Original terminal Save already attempted; never replay')
        self.guard(self.settings['one_day_timeout_seconds'])
        frame, _ = self.snapshot('terminal-current-frame', paused=False)
        if frame.get('paused') is not True:
            self.claim('terminal-pause', {'date_raw': frame['date_raw']})
            self.request('terminal-pause-once', 'ck3_execute_step', {'step': 'pause-map', 'expected_revision': None})
            frame, _ = self.snapshot('terminal-paused-frame')
        owned = self._clock.active_clock
        clock = self._clock.clock_status()
        if owned is not None:
            need(clock['generation'] == owned['armed']['generation'], 'Terminal owned clock generation changed')
            if clock['state'] == 'armed':
                self.claim('terminal-cancel-clock', {'generation': clock['generation']})
                canceled, _ = self.request('terminal-cancel-clock-once', 'ck3_execute_step', {
                    'step': 'research-cancel-tactical-daily-sentinel-v1-generation-' + str(clock['generation']),
                    'expected_revision': None})
                need(canceled['body'].get('accepted') is True and canceled['body'].get('status') == 'canceled',
                     'Original owned clock cancellation unverified')
        # Unknown Arm result grants neither a replacement Arm nor cancellation
        # of an unproved generation. The original GUI Quit still closes scene.
        frame, _ = self.snapshot('terminal-save-frame')
        self.claim('terminal-save', {'actor': self.binding['actor'], 'date_raw': frame['date_raw']})
        self.normal_save_attempted = True
        saved, refs = self.request('terminal-save-once', 'ck3_execute_step',
            {'step': 'save-checkpoint', 'expected_revision': frame['revision']})
        checkpoint = saved.get('body', {}).get('checkpoint', {})
        need(saved.get('body', {}).get('accepted') is True and checkpoint.get('status') == 'saved'
             and checkpoint.get('episode_character_id') == self.binding['actor']
             and checkpoint.get('date_raw') == frame['date_raw'], 'Actual terminal normal Save unverified; never replay')
        return {'normal_Save_actual': refs, 'original_clock_status': clock,
                'unknown_arm_claim': self._clock.unknown_clock_claim, 'normal_GUI_Quit_pending': True}

    # Reuse business algorithms as functions over this normally constructed IO.
    # No legacy Relay instance, __new__, constructor skip or AST rewrite occurs.
    def saved(self, *a, **k): return self.r.Relay.saved(self, *a, **k)
    def save_packet(self, *a, **k): return self.r.Relay.save_packet(self, *a, **k)
    def baseline(self, *a, **k): return self.r.Relay.baseline(self, *a, **k)
    def submit_once(self, *a, **k): return self.r.Relay.submit_once(self, *a, **k)
    def original(self, *a, **k): return self.r.Relay.original(self, *a, **k)
    def post_split(self, *a, **k): return self.r.Relay.post_split(self, *a, **k)
    def unchanged_others(self, *a, **k): return self.r.Relay.unchanged_others(self, *a, **k)


class ClockFacade:
    """Reuse current exact-day and native modal continuation on this same owner."""
    def __init__(self, io):
        self.io = io; self.client = io.client
        self.context = {**io.context, 'machine_id': io.machine}
        self.actor = io.binding['actor']; self.episode = io.binding['episode']; self.pid = io.binding['pid']
        self.settings = {'speed': 5, 'one_day_timeout_seconds': io.settings['one_day_timeout_seconds'],
            'poll_interval_seconds': io.settings['poll_interval_seconds'],
            'maximum_modal_choices': io.settings['maximum_modal_choices']}
        self.clock = time.monotonic; self.sleep = time.sleep
        self.modals = []; self.active_clock = None; self.unknown_clock_claim = None
    def room(self, extra=0): self.io.guard(extra)
    def claim(self, label, value): return self.io.claim(label, value)
    def call(self, label, tool, args, **kwargs):
        row, refs = self.io.request(label, tool, args)
        self.last_call_refs = refs
        return row['body']
    def snapshot(self, label, *, paused=None, **kwargs): return self.io.snapshot(label, paused=paused is True)[0]
    def clock_status(self, **kwargs):
        from xar_autoplayer.bridge.r05_supply_observation_case import ObservationIO
        return ObservationIO.clock_status(self, **kwargs)
    def handle_modals(self, frame):
        from xar_autoplayer.bridge.r05_supply_observation_case import ObservationIO
        return ObservationIO.handle_modals(self, frame)
    def exact_day(self, before):
        from xar_autoplayer.bridge.r05_supply_observation_case import ObservationIO
        return ObservationIO.exact_day(self, before)
