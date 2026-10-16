"""C phased relay composition. Import/prepare are offline; Root invokes one stage.

No SDK client is created. Live stages use only the explicitly pinned existing
Root file relay. The ordinary same-S0 checkpoint and frozen policy are inputs;
this module never starts/loads a game, records video or changes the C strategy.
"""
from __future__ import annotations
import argparse, ast, hashlib, importlib.util, json, re, sys, time, types
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

# Historical source only. New bundles must bind their source explicitly below.
SOURCE = 'dcda9fde1afa1effb75d46fe99bba4bcd9aeabcb'
DEADLINE = '2026-10-16T07:45:01.597+00:00'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def pin(path, limit=16*1024*1024):
    path = Path(path)
    need(path.stat().st_size <= limit, 'bounded input too large')
    raw = path.read_bytes()
    need(len(raw) <= limit, 'bounded input grew')
    return {'path': str(path.resolve()), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def checked(value, limit=16*1024*1024):
    need(pin(value['path'], limit=limit) == value, 'exact input bytes/SHA changed: ' + value['path'])
    return Path(value['path'])


def load(path, limit=16*1024*1024):
    need(Path(path).suffix.lower()=='.json', 'metadata JSON only; never read opaque save, EXE or media bodies')
    checked(pin(path, limit=limit), limit=limit)
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode('utf-8')
    need(len(raw) <= 1024*1024, 'derived stage receipt exceeds1MiB')
    with path.open('xb') as stream:
        stream.write(raw)
    return pin(path)


def runtime_binding(bundle):
    """Read exact pinned normal-run identities without importing a provider.

    No current HEAD or historical SOURCE is a default admission. The explicit
    bundle intent must match every actual source witness and the frozen plan.
    Live still performs its existing checkout/PID/Robert/transport checks.
    """
    source = bundle.get('source_head')
    need(type(source) is str and re.fullmatch('[0-9a-f]{40}', source) is not None,
         'explicit reviewed bundle source_head is required')
    context = load(checked(bundle['context']))
    proof = load(checked(bundle['runtime_proof']))
    plan = load(checked(bundle['plan']))
    runtime = bundle.get('runtime')
    need(type(runtime) is dict and runtime.get('source_head') == source
         and context.get('source_head') == source and proof.get('source_head') == source
         and (plan.get('build') or {}).get('source_head') == source,
         'explicit C source differs from runtime/context/proof/plan; no implicit migration')
    identity = context.get('identity') or {}
    machine = bundle.get('machine_id')
    need(type(machine) is str and machine and context.get('machine_id') == machine
         and identity.get('machine_id') == machine and proof.get('machine_id') == machine,
         'C context/proof machine binding differs')
    sequence = identity.get('sequence')
    run_id = identity.get('run_id')
    need(type(sequence) is int and sequence > 0 and identity.get('mod_key') == 'vanilla'
         and run_id == machine+'--vanilla--R'+str(sequence).zfill(4)
         and proof.get('run_id') == run_id,
         'C actual context/proof/run ID sequence differs')
    for field, expected in (('run_id', run_id), ('run_sequence', sequence)):
        need(field not in runtime or (type(runtime[field]) is type(expected) and runtime[field] == expected),
             'C runtime '+field+' differs from actual context/proof')
    for field in ('pid', 'process_creation_filetime_100ns',
                  'connection_generation', 'actual_runtime_character_full_id'):
        value = proof.get(field)
        need(type(value) is int and (value >= 0 if field == 'connection_generation' else value > 0),
             'C actual runtime proof identity missing: '+field)
    need(type(proof.get('episode_run_id')) is str and proof['episode_run_id'],
         'C actual runtime episode missing')
    return {'source_head': source, 'machine_id': machine,
            'run_id': run_id, 'run_sequence': sequence}


def provider_arguments(bundle, args, binding):
    """Pass the verified source and allocated sequence to the existing Root IO."""
    return argparse.Namespace(repo=Path(bundle['repo']), context=Path(bundle['context']['path']),
        runtime_proof=Path(bundle['runtime_proof']['path']), runtime_proof_sha256=bundle['runtime_proof']['sha256'],
        request_helper=Path(bundle['request_helper']['path']), request_helper_sha256=bundle['request_helper']['sha256'],
        source_head=binding['source_head'], run_id=binding['run_id'], run_sequence=binding['run_sequence'],
        case_id=bundle['case_id'], card='C', attempt=args.attempt, army_id=bundle['army_id'],
        deadline_utc=DEADLINE, stage=args.stage)


def runtime_total_input(bundle, capacity):
    """Offline local gate; the central reader revalidates before requests."""
    amount = bundle.get('runtime_request_budget_bytes')
    need(type(amount) is int and 17*1024*1024 <= amount < 2**63, 'explicit bounded Root runtime packet budget required')
    if 'runtime_total_budget_input' not in bundle:
        need(amount <= 512*1024*1024, 'runtime budget above512MiB requires explicit total-budget admission')
        return None
    options = bundle['runtime_total_budget_input']
    need(type(options) is dict and set(options) == {'max_runtime_total_bytes','runtime_capacity_admission'}
         and type(options.get('max_runtime_total_bytes')) is int
         and options['max_runtime_total_bytes'] == amount, 'C total budget must equal runtime_request_budget_bytes')
    entry = options.get('runtime_capacity_admission')
    need(isinstance(entry, (list,tuple)) and len(entry) == 2
         and type(entry[0]) is str and type(entry[1]) is str
         and Path(entry[0]).resolve() == Path(bundle['capacity']['path']).resolve()
         and entry[1] == bundle['capacity']['sha256'], 'C runtime admission must be the exact bundle.capacity pin')
    source = bundle['source_head']; ceilings = capacity.get('component_ceiling_bytes') or {}
    scene = capacity.get('scene_root')
    need(capacity.get('admitted') is True and capacity.get('machine_id') == bundle['machine_id']
         and capacity.get('source_head') == source
         and (capacity.get('source_binding') or {}).get('new_clean_integrated_source_head') == source
         and type(scene) is str and Path(scene).is_absolute()
         and Path(scene).resolve() == Path(bundle['context']['path']).resolve().parent,
         'C runtime capacity machine/source/scene differs')
    need(type(ceilings.get('driver')) is int and ceilings['driver'] >= amount
         and type(capacity.get('new_scene_aggregate_bytes')) is int
         and capacity['new_scene_aggregate_bytes'] >= ceilings['driver'], 'C actual Driver ceiling does not admit runtime total')
    review = datetime.fromisoformat(capacity['quota_review_at_utc'].replace('Z','+00:00'))
    need(review.tzinfo is not None and review == datetime.fromisoformat(bundle['deadline_utc'].replace('Z','+00:00'))
         and datetime.now(timezone.utc) < review, 'C runtime capacity expired or deadline differs')
    return deepcopy(options)


def prepare(bundle):
    """Static exact-source check; no provider import, PID probe or request."""
    gaps = []
    entrances = {
        'source_head': 'Root explicitly binds the reviewed source matching current context/proof/runtime/plan; historical dcda is not a new-run default.',
        'modules': 'Pin the reviewed root_relay, dcda_coherent_reader and next_adapter Python sources by exact bytes/SHA.',
        'repo': 'Declare the exact reviewed checkout; existing Root Live verifies its HEAD before runtime use.',
        'plan': 'Freeze exact normal common-S0 plan, via sequence, source/DLL and arrival definition before independent cold arms.',
        'context': 'Root normal allocator emits allocated-context.actual.json for the new C process, never reuse R0176.',
        'runtime_proof': 'Root existing runtime identity probe must read actual PID/create-time/generation/actor/episode.',
        'request_helper': 'Bind the existing Root requests helper to exactly this context ASSETS/RUN and pin its Python source.',
        'capacity': 'Root must admit this future C runtime; the child1MiB preparation budget does not authorize a new scene.',
        'prepared': 'Use ordinary checkpoint prepare receipt with exact checkpoint.source.save bytes/SHA; never open/save-edit opaque S0.',
        'current_loaded_features': 'Bind actual current run preflight/playset/features JSON by source pin and JSON pointer; no invented true flag.',
        'runtime': 'Bind actual cold started_at_utc, source_head and native_dll_sha256 from this run receipts.',
        'evidence_roots': 'Declare exact roots containing current responses and frozen baseline small JSON evidence.',
        'runtime_request_budget_bytes': 'Root must bind admitted future C request/response+case byte budget; do not reuse the child1MiB allocation.',
        'army_id': 'Read selected public Army FullID from fresh normal C snapshot and join native_carmy_id via full strengths.',
        'case_id': 'Choose a new safe independent formal C case ID; do not reuse R12/R13 ledgers.',
    }
    for key, entrance in entrances.items():
        value = bundle.get(key)
        if value is None or value == {} or value == []:
            gaps.append({'field':key, 'construction_entrance':entrance})
    if gaps:
        return {'status':'NEEDS_ROOT_BINDINGS','gaps':gaps,'SDK_calls':0,
                'live_qualification_granted':False,'provider_imported':False}
    need(bundle['deadline_utc'] == DEADLINE, 'original deadline differs; no extension')
    need(type(bundle['modules']) is dict
         and {'root_relay','dcda_coherent_reader','next_adapter'} <= set(bundle['modules']),
         'explicit reviewed C module pins are incomplete')
    for value in bundle['modules'].values():
        path = checked(value)
        need(path.suffix == '.py', 'only explicit reviewed Python modules')
        ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
    for key in ('plan', 'context', 'runtime_proof', 'request_helper', 'capacity', 'prepared'):
        checked(bundle[key])
    binding = runtime_binding(bundle)
    plan = load(checked(bundle['plan']))
    if plan.get('follow_after_arrival_to_day90') is True and plan.get('post_arrival_policy') == 'hold-arrival-position-until-day90':
        need('common_horizon' in bundle['modules'], 'pin the C common_horizon helper before this frozen normal arm')
    capacity = load(bundle['capacity']['path'])
    need(capacity['machine_id'] == bundle['machine_id'] and capacity['admitted'] is True
         and datetime.fromisoformat(capacity['quota_review_at_utc']) == datetime.fromisoformat(DEADLINE),
         'Root capacity or unchanged deadline missing')
    runtime_total_input(bundle, capacity)
    return {'status': 'SOURCE-COMPOSITION-PREPARED', **binding,
            'machine_id': bundle['machine_id'], 'SDK_calls': 0, 'provider_imported': False,
            'live_qualification_granted': False}


def provider(bundle, args):
    """Bind the existing Root relay; only explicit Root run-stage calls this.

    The only base-source edit parameterizes its private ledger directory.
    Request/once-claim/original-response/frame methods are retained verbatim.
    """
    need(prepare(bundle)['status']=='SOURCE-COMPOSITION-PREPARED', 'complete concrete Root bindings before any live phase')
    binding = runtime_binding(bundle)
    base_path = checked(bundle['modules']['root_relay'])
    tree = ast.parse(base_path.read_text(encoding='utf-8-sig'))
    changed = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and node.value == 'locked-routes-helper-a02':
            node.value = 'strategy-c-phased-a03'
            changed += 1
    need(changed == 1, 'reviewed base ledger seam changed')
    base = types.ModuleType('C_pinned_existing_Root_relay')
    base.__file__ = str(base_path)
    exec(compile(ast.fix_missing_locations(tree), str(base_path), 'exec'), base.__dict__)
    base.SOURCE = binding['source_head']
    base.TARGET_ASSETS = Path(bundle['context']['path']).parent.name
    base.RUN_BUDGET = bundle['runtime_request_budget_bytes']
    values = provider_arguments(bundle, args, binding)
    io = base.Live(values)
    io._runtime_budget_base = base
    need(io.c == load(checked(bundle['context'])) and io.transport.CONTEXT == io.c,
         'Root provider transport context differs from the exact reviewed C context')
    io.meta.update(C_explicit_source_binding=binding, C_module_pins=deepcopy(bundle['modules']),
                   C_context=bundle['context'])
    io._refs = {}
    delta = module(checked(bundle['modules']['dcda_coherent_reader']), 'C_existing_coherent_reader')
    io.strength_at = types.MethodType(delta.Live.strength_at, io)
    io.coherent_stop_core = types.MethodType(delta.Live.coherent_stop_core, io)
    sys.path[:0] = [str(io.repo), str(io.repo/'ck3_autonomous_player/src')]
    from xar_autoplayer.bridge import native_driver
    return io, native_driver


class Evidence:
    """Use exact response-local pins; never search latest/glob or copy raw files."""
    def __init__(self, roots, reader, *, input_options=None, runtime=None):
        self.roots = [Path(p).resolve() for p in roots]
        self.reader = reader
        options = (reader.evidence_file_options(input_options, source_head=runtime['source_head'],
            machine_ids=[runtime['machine_id']]) if input_options is not None else {})
        self.limits = reader.Evidence(self.roots[0], **options)
    def check_runtime_pin(self, value, runtime):
        self.limits.check_runtime_pin(value, runtime)
    def json(self, value):
        limit = self.limits.file_limit(value['path'])
        path = checked(value, limit=limit).resolve()
        need(path.suffix == '.json' and any(path.is_relative_to(root) for root in self.roots),
             'JSON source escapes explicit evidence roots')
        return load(path, limit=limit)
    def bound(self, value):
        return self.reader.Evidence.bound(self, value)


class CStages:
    def __init__(self, io, native_driver, bundle):
        self.io, self.nd, self.bundle = io, native_driver, bundle
        self.source_binding = runtime_binding(bundle)
        self.adapter = module(checked(bundle['modules']['next_adapter']), 'C_next_adapter')
        self.horizon = (module(checked(bundle['modules']['common_horizon']), 'C_common_horizon')
                        if 'common_horizon' in bundle['modules'] else None)
        self.c = self.adapter.c
        self.reader = self.adapter._reader()
        self.plan = load(checked(bundle['plan']))
        proof = load(checked(bundle['runtime_proof']))
        self.runtime = {**bundle['runtime'], 'machine_id': bundle['machine_id'],
            'pid': proof['pid'], 'process_create_time_100ns': proof['process_creation_filetime_100ns'],
            'connection_generation': proof['connection_generation'], 'episode': proof['episode_run_id'],
            'player_character_id': proof['actual_runtime_character_full_id']}
        self.evidence = Evidence(bundle['evidence_roots'], self.reader,
            input_options=bundle.get('evidence_input'), runtime=self.runtime)
        self.runtime_budget = self.reader.runtime_total_budget(bundle.get('runtime_total_budget_input',
            {'max_runtime_total_bytes': bundle['runtime_request_budget_bytes'], 'runtime_capacity_admission': None}),
            scene_root=io.assets, source_head=self.runtime['source_head'], machine_id=bundle['machine_id'],
            deadline_utc=bundle['deadline_utc'])
        self.runtime_budget.bind_live(io, base_module=getattr(io, '_runtime_budget_base', None),
            raw_file_max=self.evidence.limits.max_file_bytes)
        self.meta = {**io.meta, 'C_plan': bundle['plan'], 'runtime': self.runtime,
            'phases_chained': False, 'native_save_or_video_body_opened': False}
        self.log = io.case/'state-pins.jsonl'
        fixed = io.case/'C-inputs.actual.json'
        binding = {'plan': bundle['plan'], 'prepared': bundle['prepared'],
                   'runtime': self.runtime, **self.source_binding, 'deadline_utc': DEADLINE,
                   'context': bundle['context'], 'runtime_proof': bundle['runtime_proof'],
                   'request_helper': bundle['request_helper'], 'module_pins': bundle['modules'],
                   **({'evidence_input': deepcopy(bundle['evidence_input'])} if 'evidence_input' in bundle else {}),
                   **({'runtime_total_budget_input': deepcopy(bundle['runtime_total_budget_input'])}
                      if 'runtime_total_budget_input' in bundle else {})}
        if fixed.exists():
            need(load(fixed) == binding, 'C source/S0/policy/runtime changed within this case')
        else:
            write_new(fixed, binding)
    def save_state(self, state, observed, refs):
        if (state['phase'] == 'arrived' and 'common_horizon_anchor' not in state
                and self.plan.get('follow_after_arrival_to_day90') is True
                and self.plan.get('post_arrival_policy') == 'hold-arrival-position-until-day90'):
            need(self.horizon is not None and self.log.exists(), 'first arrival needs pinned helper and original marching state')
            previous = self.saved()
            state = self.horizon.bind_first_arrival(self.plan, previous['state'], state, observed, adapter=self.adapter)
            state['common_horizon_anchor']['previous_state_source'] = json.loads(
                self.log.read_text(encoding='utf-8').splitlines()[-1])
        entries = self.log.read_text(encoding='utf-8').splitlines() if self.log.exists() else []
        value = {'state': state, 'observed': refs, 'observed_day': observed['endpoint']['day']}
        target = self.io.case/f'state-{len(entries):04d}.actual.json'
        ref = write_new(target, value)
        with self.log.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(ref)+'\n')
        return ref
    def saved(self):
        need(self.log.exists() and self.log.stat().st_size <= 1024*1024, 'C state not admitted or state log over cap')
        entries = self.log.read_text(encoding='utf-8').splitlines()
        need(entries and len(entries) <= 512, 'C phase count exhausted')
        return self.evidence.json(json.loads(entries[-1]))
    def packet(self, name, *, stopped=None):
        if stopped is None:
            o, refs = self.io.frame(name)
        else:
            o, refs = self.io.coherent_stop_core(stopped, name)
        s, q = o['snapshot'], o['strength']
        body, _, commander_ref = self.io.request(name+'-commander', 'ck3_query_army_commander_candidates_v1',
            {'army_id': self.io.binding['army_id'], 'expected_revision': s['revision']})
        command = body['body']
        need(command.get('accepted') is True and command.get('read_only') is True
             and all(command.get(qk) == s.get(sk) for qk, sk in
                [('queried_snapshot_id','snapshot_id'), ('queried_revision','revision'), ('queried_native_revision','native_revision')]),
             'READINESS_GAP: bind typed current-commander query to this exact paused snapshot')
        receiver = command.get('army_commander_candidates') or {}
        current = receiver.get('current_commander') or {}
        need(receiver.get('army_id') == self.io.binding['army_id']
             and receiver.get('native_carmy_id') == self.io.binding['native_carmy_id']
             and receiver.get('date_raw') == s['date_raw'] and receiver.get('snapshot_revision') == s['native_revision'],
             'READINESS_GAP: typed commander full-identity/date witness is absent')
        need(current.get('status') == 'available' and type(current.get('character_id')) is int,
             'READINESS_GAP: existing R10 endpoint requires integer commander; preserve absent/unavailable, never fill0')
        after, _ = self.io.snap(name+'-same-frame')
        need(all(s[k] == after[k] for k in ('snapshot_id','revision','native_revision','date_raw')),
             'READINESS_GAP: readonly query frame drift; obtain a new coherent snapshot/whole query pair')
        delta = s['date_raw'] - self.plan['t0_raw']
        need(delta >= 0 and delta % 24 == 0, 'actual date is outside original S0 calendar')
        record = {'day': delta//24, 'snapshot': refs['snapshot'], 'army_result': refs['strength'],
            'strategy_army_ids': [self.io.binding['army_id']],
            'commander': {'source': commander_ref, 'pointer': '/body/army_commander_candidates/current_commander/character_id'},
            'loaded_features': self.bundle['current_loaded_features']}
        observation = self.adapter.read_inputs(self.plan, self.runtime, record, self.evidence)
        self.adapter._whole_data(self.plan, observation)
        return observation, {'endpoint': record, 'frame': refs, 'commander': commander_ref}
    def admit(self):
        need(not self.log.exists(), 'C already admitted; never reset S0 or state')
        need(self.plan.get('status') == 'frozen', 'freeze C exact via sequence before this independent cold arm')
        need(self.runtime['source_head'] == self.plan['build']['source_head'] == self.source_binding['source_head']
             and self.runtime['native_dll_sha256'] == self.plan['build']['native_dll_sha256'], 'C actual source/DLL differs')
        need(datetime.fromisoformat(self.plan['frozen_at_utc'].replace('Z','+00:00')) <
             datetime.fromisoformat(self.runtime['started_at_utc'].replace('Z','+00:00')), 'formal plan must precede independent cold session')
        prepared = load(self.bundle['prepared']['path'])
        source = prepared['checkpoint']['source']['save']
        need(source['sha256'] == self.plan['normal_save']['sha256']
             and source.get('bytes',source.get('size')) == self.plan['normal_save']['bytes'],
             'normal cold prepared checkpoint differs from exact common S0 receipt')
        observation, refs = self.packet('C-S0')
        baseline = self.reader.endpoint(self.plan['baseline'], self.plan, self.evidence)
        need(observation['endpoint'] == baseline, 'fresh C S0 observable baseline differs; no corrective C-only Halt/Move')
        state = self.c.start(self.plan, observation)
        return self.save_state(state, observation, refs)
    def probe_via(self):
        need(self.plan.get('status') != 'frozen' and not self.log.exists(),
             'candidate pilot cannot mutate or reuse a formal C case')
        observation, refs = self.packet('via-pilot')
        need(observation['endpoint']['day'] == 0, 'candidate pilot must remain at S0 with no time advance')
        candidates = self.bundle['ordered_candidate_ids']
        need(type(candidates) is list and 0 < len(candidates) <= 8, 'at most8 explicit caller candidates')
        previews, pins = {}, {}
        for target in candidates:
            row, _, ref = self.io.request('via-preview-'+str(target), 'ck3_execute_step',
                {'step': f"preview-move-army-{self.io.binding['army_id']}-to-{target}",
                 'expected_revision': observation['binding']['revision']})
            previews[target], pins[str(target)] = row['body'], ref
        result = self.adapter.choose_draft_via(self.plan, observation, candidates, previews)
        return write_new(self.io.case/'via-pilot.actual.json', {**self.meta, 'observed': refs,
            'result': result, 'preview_sources': pins, 'formal_C_credit': False,
            'next': 'Freeze exact waypoints and independent A/B/C policy, then cold-load same S0 in new formal case.'})
    def move_once(self):
        saved = self.saved()
        observation, refs = self.packet('before-segment')
        state = self.c.observe(self.plan, saved['state'], observation)
        need(state['phase'] == 'ready', 'C is not ready for its next frozen segment')
        target = self.c.targets(self.plan)[state['target_index']]
        row, _, preview_ref = self.io.request('segment-preview', 'ck3_execute_step',
            {'step': f"preview-move-army-{self.io.binding['army_id']}-to-{target}",
             'expected_revision': observation['binding']['revision']})
        decision = self.adapter.next_decision(self.plan, state, observation, row['body'])
        need(decision['status'] == 'propose_existing_move', 'READINESS_GAP: '+decision['reason'])
        index = state['target_index']
        key = f'leg-{index:02d}-move'
        # Pending state is saved before the existing once-claim/action helper.
        # If its result is unknown, only path-after reads original response.
        self.save_state(decision['next_state'], observation, refs)
        return self.io.action(key, 'ck3_move_army', decision['proposed_call']['arguments'],
            {'before': refs, 'preview': preview_ref, 'expected_route': decision['next_state']['pending_route'],
             'frozen_target': target, 'target_index': index, 'plan': self.bundle['plan']})
    def path_after(self):
        saved = self.saved(); state = saved['state']
        need(state['phase'] == 'pending_move', 'path-after needs exactly one pending segment Move')
        key = f"leg-{state['target_index']:02d}-move"
        original = self.io.action_original(key)
        observation, refs = self.packet('independent-path-after')
        updated = self.c.observe(self.plan, state, observation)
        need(updated['phase'] == 'marching', 'original Move remains unobserved; retain pending, never reissue')
        write_new(self.io.case/(key+'.path-after.actual.json'), {**self.meta, 'action': original,
            'observed': refs, 'whole_DATA_complete': True, 'arrival_claimed': False})
        return self.save_state(updated, observation, refs)
    def advance(self, max_days):
        need(type(max_days) is int and 1 <= max_days <= 30, 'explicit bounded segment batch1..30')
        saved = self.saved(); state = saved['state']
        need(state['phase'] == 'marching', 'advance needs independently applied complete segment route')
        observation, refs = self.packet('advance-start')
        state = self.c.observe(self.plan, state, observation)
        for _ in range(min(max_days,90-state['last_day'])):
            observation, refs, clock = self.exact_day(observation, refs)
            observation['clock'] = clock
            state = self.c.observe(self.plan, state, observation)
            self.save_state(state, observation, refs)
            if state['phase'] != 'marching':
                break
        return {'phase': state['phase'], 'day': state['last_day'], 'arrivals': state['arrivals'],
                'exact_arrival_tick': None, 'next_stage': 'move-once' if state['phase']=='ready' else 'report'}
    def exact_day(self, before, before_refs):
        start = before['endpoint']['date_raw']; target = start+24
        key = 'C-day-'+str(start)
        self.io.claim(key, {'starting_date_raw': start, 'target_date_raw': target, 'before': before_refs,
            'arm_request_id': self.io.args.attempt+'-'+str(self.io.serial+1).zfill(3)+'-C-arm-one-day'})
        step = f'research-arm-tactical-daily-sentinel-v1-{start}-to-{target}-speed-5-mode-terminal-a-0'
        arm, _, arm_ref = self.io.request('C-arm-one-day','ck3_execute_step',
            {'step': step, 'expected_revision': before['binding']['revision']})
        armed = self.nd._normalize_tactical_daily_sentinel_status(arm['body']['tactical_daily_sentinel'])
        self.nd._validate_tactical_daily_sentinel_arm(arm['body'],armed,arm_step=step,
            starting_date_raw=start,target_date_raw=target,speed=5,mode='terminal_or_sentinel',
            watch_army_ids=(),sentinel_scope='exact_one_day')
        self.io.action(key+'-resume','ck3_execute_step',{'step':'resume-map','expected_revision':None},
            {'arm_response':arm_ref,'before':before_refs,'starting_date_raw':start,'target_date_raw':target})
        stopped = None
        for _ in range(60):
            time.sleep(.15)
            current, _ = self.io.snap('C-wait-paused',paused=False)
            if current.get('paused') is True and current['date_raw'] > start:
                stopped = current
                break
        need(stopped is not None, 'exact day has not independently paused; preserve original Arm/Resume, never replay')
        status, _, status_ref = self.io.request('C-clock-status','ck3_execute_step',
            {'step':'research-query-tactical-daily-sentinel-v1','expected_revision':None})
        actual, refs = self.packet('C-post-status',stopped=stopped)
        clock = self.nd._normalize_tactical_daily_sentinel_status(status['body']['tactical_daily_sentinel'])
        self.nd._validate_tactical_daily_sentinel_stop(clock,arm_status=armed,starting_date_raw=start,
            target_date_raw=target,ending_date_raw=actual['endpoint']['date_raw'],elapsed_days=1,
            speed=5,mode='terminal_or_sentinel',watch_army_ids=())
        self.c._clock({'last_day':before['endpoint']['day'],'last_clock_generation':0}, {**actual,'clock':clock})
        write_new(self.io.case/(key+'.clock-complete.actual.json'), {**self.meta,'before':before_refs,
            'after':refs,'arm_response':arm_ref,'status_response':status_ref,'clock':clock})
        return actual, refs, clock
    def advance_common_horizon(self, max_days):
        need(type(max_days) is int and 1 <= max_days <= 30, 'explicit common horizon batch1..30')
        need(self.horizon is not None, 'common horizon needs an exact helper module pin')
        saved = self.saved(); state = saved['state']
        self.horizon.check_saved_state(self.plan, state, adapter=self.adapter)
        if state['last_day'] == 90:
            return {'phase':state['phase'],'day':90,'arrivals':state['arrivals'],
                'common_horizon_complete':True,'new_requests':0,'next_stage':'report'}
        observation, refs = self.packet('common-horizon-start')
        state = self.horizon.read_common_horizon_endpoint(self.plan, state, observation, adapter=self.adapter)
        self.save_state(state, observation, refs)
        for _ in range(min(max_days,90-state['last_day'])):
            observation, refs, clock = self.exact_day(observation, refs)
            observation['clock'] = clock
            state = self.horizon.observe_common_horizon(self.plan, state, observation, adapter=self.adapter)
            self.save_state(state, observation, refs)
        return {'phase':state['phase'],'day':state['last_day'],'arrivals':state['arrivals'],
            'common_horizon_complete':state['last_day']==90,'exact_arrival_tick':None,
            'next_stage':'report' if state['last_day']==90 else 'advance-common-horizon'}
    def recover_day(self, start, *, common_horizon=False):
        """Read original Arm/Resume and fresh status only; never replay actions."""
        need(type(start) is int, 'explicit original day start is required')
        saved=self.saved(); state=saved['state']
        if common_horizon:
            need(self.horizon is not None, 'common recovery needs exact helper module pin')
            self.horizon.check_saved_state(self.plan, state, adapter=self.adapter)
        need(self.plan['t0_raw']+24*state['last_day']==start
             and state['phase']==('arrived' if common_horizon else 'marching') and state['last_day']<90,
             'recovery must begin at the last uncommitted original C march day')
        key='C-day-'+str(start)
        claim=load(self.io.case/(key+'.once.claim.json'))
        need(claim['binding']==self.io.binding and claim['starting_date_raw']==start
             and claim['target_date_raw']==start+24, 'original day claim runtime/date differs')
        resume=self.io.action_original(key+'-resume')
        arm=self.evidence.json(resume['arm_response'])
        armed=self.nd._normalize_tactical_daily_sentinel_status(arm['body']['tactical_daily_sentinel'])
        step=f'research-arm-tactical-daily-sentinel-v1-{start}-to-{start+24}-speed-5-mode-terminal-a-0'
        self.nd._validate_tactical_daily_sentinel_arm(arm['body'],armed,arm_step=step,
            starting_date_raw=start,target_date_raw=start+24,speed=5,mode='terminal_or_sentinel',
            watch_army_ids=(),sentinel_scope='exact_one_day')
        status,_,status_ref=self.io.request('C-recover-clock-status','ck3_execute_step',
            {'step':'research-query-tactical-daily-sentinel-v1','expected_revision':None})
        stopped,_=self.io.snap('C-recover-current-paused')
        actual,refs=self.packet('C-recover-post-status',stopped=stopped)
        clock=self.nd._normalize_tactical_daily_sentinel_status(status['body']['tactical_daily_sentinel'])
        self.nd._validate_tactical_daily_sentinel_stop(clock,arm_status=armed,starting_date_raw=start,
            target_date_raw=start+24,ending_date_raw=actual['endpoint']['date_raw'],elapsed_days=1,
            speed=5,mode='terminal_or_sentinel',watch_army_ids=())
        actual['clock']=clock
        updated=(self.horizon.observe_common_horizon(self.plan,state,actual,adapter=self.adapter)
                 if common_horizon else self.c.observe(self.plan,state,actual))
        write_new(self.io.case/(key+'.readonly-recovery.actual.json'), {**self.meta,
            'original_claim':pin(self.io.case/(key+'.once.claim.json')),'original_resume':resume,
            'fresh_status':status_ref,'after':refs,'clock':clock,'Arm_Resume_reissued':False})
        return self.save_state(updated,actual,refs)
    def report(self):
        saved = self.saved()
        return {'state':saved['state'],'last_endpoint_sources':saved['observed'],
            'winner':None,'full_ABC_eligibility_assessed':False,'fees_qualified':False,
            'dynamic_video_qualified':False,'Root_case_only':True}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('prepare','probe-via','admit','move-once','path-after','advance','recover-day','advance-common-horizon','recover-common-horizon-day','report'))
    parser.add_argument('--bundle',type=Path,required=True)
    parser.add_argument('--attempt',default='Root-explicit-attempt')
    parser.add_argument('--max-days',type=int,default=1)
    parser.add_argument('--day-start-raw',type=int)
    parser.add_argument('--output',type=Path)
    args = parser.parse_args(argv)
    bundle = load(args.bundle)
    if args.stage == 'prepare':
        result = prepare(bundle)
        result.update(machine_id=bundle['machine_id'],observed_at_utc=datetime.now(timezone.utc).isoformat())
        if args.output:
            write_new(args.output,result)
        else:
            print(json.dumps(result))
        return 0 if result['status']=='SOURCE-COMPOSITION-PREPARED' else 2
    io = None
    try:
        io, nd = provider(bundle,args)
        relay = CStages(io,nd,bundle)
        stages = {'probe-via':relay.probe_via,'admit':relay.admit,'move-once':relay.move_once,
            'path-after':relay.path_after,'advance':lambda:relay.advance(args.max_days),
            'recover-day':lambda:relay.recover_day(args.day_start_raw),
            'advance-common-horizon':lambda:relay.advance_common_horizon(args.max_days),
            'recover-common-horizon-day':lambda:relay.recover_day(args.day_start_raw,common_horizon=True),'report':relay.report}
        result = stages[args.stage]()
        ref = write_new(io.attempt/'RESULT.actual.json',{**relay.meta,'result':result})
        print(json.dumps(ref));return 0
    except BaseException as error:
        if io is not None:
            write_new(io.attempt/'FAILURE.actual.json',{**io.meta,'error_type':type(error).__name__,
                'error':str(error)[:4000],'request_pending':io.pending,'action_replay_allowed':False,
                'Root_next':'Read exact original request/response and current paused frame. Preserve once claim; never repeat Move/Arm/Resume.'})
        raise


if __name__ == '__main__':
    raise SystemExit(main())
