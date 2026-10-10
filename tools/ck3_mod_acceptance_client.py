"""One held-session case client using the existing once-only control queue."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def require(value, message):
    if not value:
        raise ValueError(message)


def write_once(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def resolve_operator_reviewer(selection):
    """Read the same allocated reviewer/delegation identity for run and verify."""
    from ck3_mod_acceptance import path_at, check_pin
    context = selection.context
    base = selection.context_path.parent
    frozen_ref = context['frozen_argv']
    frozen_path = path_at(frozen_ref['path'], base)
    check_pin(frozen_path, frozen_ref)
    frozen = read_json(frozen_path)
    require(frozen.get('run_id') == context.get('run_id') == selection.run_dir.name and
            frozen.get('argv') == selection.argv and
            frozen.get('runtime_environment', {}) == selection.runtime_environment,
            'Actual reviewer crossed allocated frozen run/runtime/case')
    persisted = read_json(selection.context_path)
    require(persisted.get('run_id') == context.get('run_id') and
            persisted.get('reviewer') == context.get('reviewer') and
            persisted.get('operator_delegation') == context.get('operator_delegation'),
            'Actual reviewer differs from persisted allocated context')
    reference = context.get('operator_delegation')
    if reference is None:
        require('operator_delegation' not in context, 'Explicit operator delegation cannot be null')
        reviewer = context.get('reviewer')
        require(isinstance(reviewer, str) and reviewer and reviewer.strip() == reviewer,
                'Actual allocated run reviewer required; never claim Root review')
        require(frozen.get('reviewer', reviewer) == reviewer,
                'Actual run reviewer differs from the frozen allocated context')
        return reviewer
    require(isinstance(reference, dict), 'Exact operator delegation pin required')
    path = path_at(reference.get('path'), base)
    check_pin(path, reference)
    value = read_json(path)
    require(isinstance(value, dict) and set(value) == {'schema', 'run_id', 'screen_task', 'frozen_argv',
        'delegated_by', 'delegate_reviewer', 'scopes'} and
        value.get('schema') == 'ck3-mod-acceptance-operator-delegation-v1', 'Operator delegation contract differs')
    require(context.get('reviewer') == '/root' and value['delegated_by'] == '/root' and
        value['run_id'] == frozen['run_id'] == selection.run_dir.name and
        value['screen_task'] == frozen.get('screen_task') and
        isinstance(value['screen_task'], str) and value['screen_task'], 'Operator delegation crossed Root run or screen')
    require(isinstance(value['scopes'], list) and len(value['scopes']) == 2 and
        set(value['scopes']) == {'ui', 'checkpoint'}, 'Operator delegation is limited to UI/checkpoints')
    reviewer = value['delegate_reviewer']
    require(isinstance(reviewer, str) and reviewer.strip() == reviewer and reviewer and reviewer != '/root',
            'Actual delegate reviewer required; never claim Root review')
    actual = check_pin(frozen_path, frozen_ref)
    declared = value['frozen_argv']
    require(isinstance(declared, dict) and path_at(declared.get('path'), base) == frozen_path,
            'Operator delegation selected another frozen argv')
    check_pin(frozen_path, declared)
    require(declared['bytes'] == actual['bytes'] and declared['sha256'] == actual['sha256'],
            'Operator delegation frozen argv pin differs')
    return reviewer


class CaseClient:
    def __init__(self, selection, output=None):
        require(selection.context, 'Actual allocated run context required')
        self.selection = selection
        self.context = selection.context
        self.live = selection.run_dir
        self.state = selection.state_dir
        self.output = Path(output) if output else self.live / 'case-output'
        require(not self.output.exists(), 'Case output already consumed; never replay')
        self.output.mkdir(parents=True)
        self.report_path = self.live / 'native-report.json'
        self._report_stat = None
        self._report = None
        self._hold = None
        self._started = time.time()
        self._binding = None
        self._seq = 0
        self._log_cache = {}
        self.manifest = selection.manifest
        from ck3_mod_acceptance import path_at
        self.frozen = read_json(path_at(selection.context['frozen_argv']['path'], selection.context_path.parent))
        self.keeper = path_at(self.context['keeper_root'], selection.context_path.parent)
        self.operator_reviewer = self.resolve_operator_reviewer()
        self._handle = None
        self._kernel = None
        self._process = None
        write_once(self.output / 'case-once.json', {
            'run_id': self.frozen['run_id'], 'product': selection.product_key,
            'case': selection.case['id'], 'host_argv': selection.argv,
            'runtime_manifest': str(selection.manifest_path), 'business_acceptance': 'NOT_ASSESSED'})

    def resolve_operator_reviewer(self):
        return resolve_operator_reviewer(self.selection)

    def read_report(self, allow_error=False):
        # Decode an unchanged multi-MiB report once, not once per polling tick.
        deadline = time.monotonic() + 1.5
        while True:
            try:
                stat = self.report_path.stat()
                key = (stat.st_size, stat.st_mtime_ns)
                if key != self._report_stat:
                    raw = self.report_path.read_bytes()
                    after = self.report_path.stat()
                    if key != (after.st_size, after.st_mtime_ns):
                        raise PermissionError('Report changed during read')
                    value = json.loads(raw)
                    self._report, self._report_stat = value, key
                value = self._report
                break
            except (PermissionError, json.JSONDecodeError):
                if time.monotonic() >= deadline:
                    raise
                time.sleep(.1)
        require(Path(value['state_dir']).resolve() == self.state.resolve(), 'Report state differs from actual allocated case')
        require(Path(value['agent_source_root']).resolve() == self.selection.manifest_path_key(self.manifest['source_root']),
                'Report source differs from one shared runtime')
        hold = value.get('hold_until_utc_estimated')
        if type(hold) in (int, float):
            require(self._hold is None or self._hold == hold, 'Original hold deadline changed')
            self._hold = hold
        if not allow_error:
            require(not value.get('error') and value.get('status') not in ('ERROR', 'RED'),
                    'Actual shared host failed; preserve error and do not replay')
        return value

    def remaining(self):
        budgets = self.selection.case['budgets']
        deadline = self._hold if self._hold is not None else self._started + budgets['timeout'] + budgets['hold_seconds'] + 120
        return deadline - time.time()

    def guard(self, reserve=90, *, failure_shutdown=False):
        require(self.remaining() > reserve, 'Original normal Quit reserve reached')
        keeper = self.keeper
        journal = keeper / 'journal.jsonl'
        lease = json.loads(journal.read_text(encoding='utf-8').splitlines()[-1])
        require(lease.get('result') == 'OWNED_CAS' and not (keeper / 'report.json').exists(),
                'Original screen keeper no longer owns this held scene')
        require(lease['lease']['task_id'] == self.frozen['screen_task'], 'Current keeper crossed actual allocation')
        report = self.read_report(allow_error=failure_shutdown)
        if failure_shutdown:
            retained = getattr(self, '_failure_shutdown_retained', None)
            require(reserve == 0 and self.native_failure_shutdown_proof(report) is not None,
                    'Failure lifecycle guard requires complete native/thread proof and preserved error')
            require(isinstance(retained, dict) and retained.get('actual_retained_os0') is True and
                    retained.get('pid') == self._process['pid'] and retained.get('create_time') == self._process['create_time'],
                    'Failure lifecycle guard requires the actual retained same-process OS exit0')
        require(report.get('phase') == 'hold' and not report.get('finished_at') and
                not report.get('hold_finished_by_control_plan') and (reserve==0 or not report.get('cleanup_ok')),
                'Original held session is no longer active')
        return report

    def wait_hold(self):
        preparation = (self.selection.prepared or {}).get('preparation', {})
        budget = 'timeout' if preparation.get('initial_plan_original_business') is True else 'readiness_timeout'
        limit = time.monotonic() + self.selection.case['budgets'][budget]
        self._readiness_limit = limit
        while time.monotonic() < limit:
            try:
                report = self.read_report(allow_error=True)
            except FileNotFoundError:
                time.sleep(.1); continue
            # A failed original startup can already own a real held process.
            # Retain it before the unchanged business-error gate rejects entry.
            self.retain_held_process(report)
            report = self.read_report()
            require(not report.get('finished_at'), 'Shared host ended before case entry')
            if report.get('phase') == 'hold' and all(row.get('finished_at') for row in report.get('steps', [])):
                self.guard()
                self.retain_process()
                return report
            time.sleep(.1)
        raise TimeoutError('Original case readiness budget elapsed')

    def retain_held_process(self, report=None, *, wait=False):
        """Retain only an actual allocated hold; never manufacture a launch."""
        while True:
            if report is None:
                try:
                    report = self.read_report(allow_error=True)
                except FileNotFoundError:
                    return False
            if (report.get('finished_at') or report.get('hold_finished_by_control_plan') or
                    not (self.state / 'control/ck3.json').is_file()):
                return False
            if report.get('phase') == 'hold':
                if self._handle is None:
                    self.retain_process()
                return self._handle is not None
            # Reuse only the readiness interval already started by wait_hold.
            # A new cleanup attempt must not create or extend that interval.
            if (not wait or time.monotonic() >= getattr(self, '_readiness_limit', time.monotonic()) or
                    self.remaining() <= 0):
                return False
            time.sleep(.1)
            report = None

    def await_steps(self, steps, timeout=None, reserve=90):
        limit = time.monotonic() + (timeout or self.selection.case['budgets']['command_timeout'])
        identifiers = [step['id'] for step in steps]
        while time.monotonic() < limit:
            report = self.read_report(allow_error=True) if reserve==0 else self.guard(reserve)
            rows = []
            for step in steps:
                found = [row for row in report.get('steps', []) if row.get('id') == step['id']]
                require(len(found) <= 1, 'Duplicate actual step: ' + step['id'])
                if found and found[0].get('finished_at'):
                    row = found[0]
                    if not step.get('continue_on_error', False):
                        require(row.get('ok') is True and not row.get('error'), 'Actual case step failed: ' + step['id'])
                    rows.append(row)
            if len(rows) == len(identifiers):
                return rows
            time.sleep(.1)
        raise TimeoutError('Original step budget elapsed; submitted steps never replay')

    def execute_plan(self, steps, name, timeout=None, reserve=90):
        require(reserve == 90 or reserve == 0 and len(steps) == 1 and steps[0].get('kind') == 'finish_hold',
                'Only proved native0 lifecycle completion can use the original Quit reserve')
        failure_shutdown = len(steps) == 1 and steps[0].get('failure_shutdown') is True
        require(not failure_shutdown or reserve == 0, 'Failure shutdown uses only the original lifecycle reserve')
        if reserve == 0:
            report = self.read_report(allow_error=failure_shutdown)
            proof = self.native_failure_shutdown_proof(report) if failure_shutdown else self.native_zero_proof(report)
            require(proof is not None, 'Original complete native0 lifecycle predicate did not admit finish_hold')
        report = self.guard(reserve, failure_shutdown=failure_shutdown)
        require(all(row.get('finished_at') for row in report.get('steps', [])), 'Existing controls still in flight')
        require(isinstance(steps, list) and steps, 'Nonempty original plan required')
        require(Path(name).name == name, 'Control name must be a basename')
        ids = [step['id'] for step in steps]
        require(len(ids) == len(set(ids)) and not set(ids) & {row.get('id') for row in report.get('steps', [])},
                'Original control IDs already consumed; never replay')
        path = self.output / 'plans' / (name + '.json')
        write_once(path, {'steps': steps})
        queue_ref = self.selection.runtime['control_queue']
        from ck3_mod_acceptance import path_at, check_pin
        queue = path_at(queue_ref['path'], self.selection.runtime_path.parent)
        check_pin(queue, queue_ref)
        argv = [str(self.selection.locations['python']), '-B', '-X', 'utf8', str(queue),
                '--live', str(self.live), '--plan', str(path), '--name', name + '.json']
        environment = dict(os.environ); environment.update(self.selection.runtime_environment)
        with (self.output / (name + '.stdout.log')).open('xb') as stdout, (self.output / (name + '.stderr.log')).open('xb') as stderr:
            result = subprocess.run(argv, cwd=self.selection.locations['repo_root'], env=environment,
                                    stdout=stdout, stderr=stderr, timeout=max(1, min(300, self.remaining()-reserve)))
        write_once(self.output / (name + '.queue-result.json'), {'argv': argv, 'exit_code': result.returncode})
        require(result.returncode == 0, 'Original once-only queue failed; inspect without replay')
        rows = self.await_steps(steps, timeout, reserve)
        write_once(self.output / (name + '.actual-results.json'), {'rows': rows, 'business_PASS_inferred': False})
        return rows

    def validate_frame(self, frame, allow_actor_change=False, require_event_free=True, require_paused=True):
        require(isinstance(frame, dict), 'Actual full native snapshot required')
        for key, expected in {'source':'injected-dll-named-pipe', 'backend_id':'native-headless',
                              'map_ready':True,
                              'episode_projection':'native_campaign'}.items():
            require(frame.get(key) == expected and (expected is not True or frame.get(key) is True),
                    'Actual full snapshot guard failed: ' + key)
        require(not require_paused or frame.get('paused') is True, 'Actual full paused snapshot required')
        require(not require_event_free or frame.get('active_event') is None, 'Actual event boundary requires the original case branch')
        actor = frame['played_character']; diagnostics = frame['diagnostics']; hello = diagnostics['hello']
        require(actor.get('alive') is True and actor.get('source') == 'native', 'Actual native actor must be alive')
        binding = (diagnostics['bridge_pid'], diagnostics['connection_generation'], actor['character_id'])
        require(all(type(value) is int and value > 0 for value in binding), 'Actual native identity missing')
        game = self.manifest['game']
        require(hello.get('expected_ck3_version') == game['version'] and
                str(hello.get('expected_ck3_sha256', '')).lower() == game['exe_sha256'].lower() and
                hello.get('ck3_build_match') is True, 'Actual native snapshot differs from shared exact build')
        require(hello.get('pid') == binding[0] and hello.get('connection_generation') == binding[1], 'Actual hello owner differs')
        if self._binding is not None:
            require(binding[:2] == self._binding[:2] and (allow_actor_change or binding[2] == self._binding[2]),
                    'Actual native owner/actor changed')
        self._binding = binding
        return frame

    def snapshot(self, allow_actor_change=False, require_event_free=True):
        self._seq += 1
        name = 'case-snapshot-' + str(self._seq).zfill(4)
        row = self.execute_plan([{'id':name, 'tool':'ck3_take_snapshot',
                                 'args':{'include_native_command_history':False}, 'fresh_revision':True}], name)[0]
        return self.validate_frame(row['result'], allow_actor_change, require_event_free)

    def advance_day(self, days=1, timeout=300, allow_event_boundary=False, allow_actor_change=False):
        require(type(days) is int and days == 1, 'Use one original natural day per submitted step')
        self._seq += 1
        name = 'case-natural-day-' + str(self._seq).zfill(4)
        step = {'id':name,'kind':'advance_day','days':1,'timeout':timeout}
        if allow_event_boundary is True:
            step['allow_event_boundary'] = True
            if allow_actor_change is True:
                step['allow_actor_change'] = True
        row = self.execute_plan([step], name, timeout)[0]
        value = row['result']
        if allow_event_boundary and value.get('event_boundary') is not None:
            self.validate_frame(value['before'])
            self.validate_frame(value['after'], allow_actor_change=allow_actor_change, require_event_free=False)
            return row
        require(value.get('requested_days') == 1 and value.get('requested_interval_complete') is True and
                value.get('event_boundary') is None, 'Original actual day interval/event boundary not proved')
        before, after = self.validate_frame(value['before']), self.validate_frame(value['after'],allow_actor_change=allow_actor_change)
        elapsed = value.get('elapsed_hours')
        require(type(elapsed) is int and 24 <= elapsed < 48 and after['date_raw']-before['date_raw'] == elapsed,
                'Original actual 24h interval is not proved')
        return row

    def log_bytes(self, name='debug.log', maximum=64*1024*1024):
        require(name in ('debug.log','error.log'), 'Only original CK3 logs are read')
        path = self.state / 'profile/logs' / name
        stat = path.stat(); key = (stat.st_size,stat.st_mtime_ns)
        require(stat.st_size <= maximum, 'Original diagnostic log bound exceeded')
        if self._log_cache.get(name, (None,None))[0] != key:
            raw = path.read_bytes(); after=path.stat()
            require(key == (after.st_size,after.st_mtime_ns), 'Actual debug log changed during read')
            self._log_cache[name] = (key,raw)
        return self._log_cache[name][1]

    def checkpoint(self, name, value):
        write_once(self.output / (name + '.json'), value)
        return self.output / (name + '.json')

    def query_appointment_pool(self, *, requested_title_id, requested_title_key, expected_law,
                               navigation_step_id=None, title_reference_step_id=None, breakdown_character_id=None):
        """Read current window only; join every page inside the retained paused scene."""
        from ck3_mod_acceptance_appointment import TOOL, CASES, navigation_anchor, title_reference, frame_binding, join_pages
        from ck3_mod_acceptance import pin
        case=self.selection.case
        require(case['id'] in CASES and TOOL in case.get('required_mcp_tools',[]) and
                TOOL in case.get('opt_in_read_only_mcp_tools',[]), 'Appointment read requires explicit UI/government case opt in')
        self.guard()
        frame=self.snapshot(); binding=frame_binding(frame)
        require(self._process and self._process['pid']==binding[0] and
                self._process.get('retained_synchronize_query_handle_acquired') is True,
                'Appointment collection lacks original retained same-process handle')
        require((navigation_step_id is None)!=(title_reference_step_id is None),
                'Exactly one independent navigation or native title reference required')
        reference_id=navigation_step_id if navigation_step_id is not None else title_reference_step_id
        matches=[r for r in self.read_report().get('steps',[]) if r.get('id')==reference_id]
        require(len(matches)==1, 'Independent current typed reference step missing/duplicated')
        if navigation_step_id is not None:
            reference=navigation_anchor(matches[0],frame,requested_title_id,requested_title_key)
            reference_kind='navigation'
        else:
            reference=title_reference(matches[0],frame,requested_title_id,requested_title_key)
            reference_kind='title_reference'
        self._seq+=1; name='case-appointment-'+str(self._seq).zfill(4)
        holderrow=self.execute_plan([{'id':name+'-input-holder','tool':'ck3_query_title_holder_v1',
            'args':{'title_id':requested_title_id},'fresh_revision':True}],name+'-input-holder')[0]
        holder=holderrow.get('result',{}).get('title_holder',{})
        require(holder.get('available') is True and holder.get('title_key_available') is True and
                holder.get('title_id')==requested_title_id and holder.get('title_key')==requested_title_key and
                holder.get('actor_character_id')==binding[2] and holder.get('date_raw')==binding[5] and
                frame_binding(self.validate_frame(holderrow['after_snapshot']))==binding,
                'Independent requested title key/holder crossed current scene')
        rows=[]; offset=0
        while True:
            identifier=name+'-page-'+str(offset).zfill(4)
            args={'requested_title_id':requested_title_id,'candidate_offset':offset,'candidate_limit':64}
            if breakdown_character_id is not None: args['breakdown_character_id']=breakdown_character_id
            row=self.execute_plan([{'id':identifier,'tool':TOOL,'args':args,'fresh_revision':True}],identifier)[0]
            self.validate_frame(row['after_snapshot']);rows.append(row)
            v=row.get('result',{}).get('title_appointment',{})
            end=v.get('next_offset');count=v.get('full_candidate_count')
            require(type(end) is int and type(count) is int and offset<end<=min(offset+64,count)<=4096,
                    'Appointment page did not make bounded progress')
            if end==count: break
            offset=end
        proof=join_pages(rows,frame,requested_title_id=requested_title_id,requested_title_key=requested_title_key,
                         expected_law=expected_law,breakdown_character_id=breakdown_character_id)
        require(holder.get('holder_character_id')==proof['requested_holder_character_id'] and
                (reference_kind=='navigation' or reference['holder_character_id']==proof['requested_holder_character_id']),
                'Independent input title holder differs from native normalization holder')
        proof.update(run_id=self.frozen['run_id'],retained_process=dict(self._process),
                     input_title_holder=holder,page_rows=rows,**{reference_kind:reference})
        require(frame_binding(self.snapshot())==binding, 'Complete pool crossed final paused frame')
        path=self.checkpoint(name+'-complete-pool',proof); reference=pin(path)
        if not hasattr(self,'_appointment_receipts'): self._appointment_receipts={}
        self._appointment_receipts[str(path.resolve())]=(reference,proof)
        return {'appointment_pool':reference,'proof':proof,'business_acceptance':'NOT_ASSESSED'}

    def appointment_receipt(self, reference, frame=None, *, completed_score_phase=False):
        """Only this held client's actual collector can supply business record data."""
        from ck3_mod_acceptance import pin
        from ck3_mod_acceptance_appointment import frame_binding
        require(isinstance(reference,dict) and isinstance(reference.get('path'),str), 'Actual pool receipt pin required')
        saved=getattr(self,'_appointment_receipts',{}).get(str(Path(reference['path']).resolve()))
        require(saved is not None and saved[0]==reference==pin(Path(reference['path'])) and
                saved[1]['run_id']==self.frozen['run_id'], 'Pool receipt was not generated by this held scene')
        if frame is not None:
            current=list(frame_binding(frame)); prior=saved[1]['binding']
            # Off/on/off are separate observations. Each was internally joined at
            # one native revision; toggling can legitimately change that revision.
            require(prior==current or completed_score_phase is True and prior[:4]==current[:4] and prior[5:]==current[5:],
                    'Pool receipt crossed current retained paused scene')
        return saved[1]

    def root_checkpoint(self, name, request, reserve=90, *, read_only_appointment=False):
        action_sequence=0
        if read_only_appointment:
            from ck3_mod_acceptance_appointment import TOOL, CASES
            require(self.selection.case['id'] in CASES and TOOL in self.selection.case.get('opt_in_read_only_mcp_tools',[]),
                    'Checkpoint appointment read is not declared by this case')
            request={**request,'read_only_action':{'action':'appointment-full-pool','tool':TOOL,
                'request_path':str(self.output/(name+'-readonly-request-{sequence:04d}.json')),
                'response_path':str(self.output/(name+'-readonly-response-{sequence:04d}.json')),
                'initial_sequence':0,'run_id':self.frozen['run_id'],'reviewer':self.operator_reviewer,
                'required_arguments':['requested_title_id','requested_title_key','expected_law'],
                'exactly_one_reference':['navigation_step_id','title_reference_step_id'],
                'optional_arguments':['breakdown_character_id'],'does_not_navigate_or_sign_off':True}}
        path = self.checkpoint(name + '-awaiting', {'run_id':self.frozen['run_id'],
            'original_hold_deadline':self._hold,'reserve_seconds':reserve, **request,
            'operator_reviewer':self.operator_reviewer})
        print('CK3_ROOT_CHECKPOINT ' + str(path), flush=True)
        response = self.output / (name + '-root-result.json')
        while self.remaining() > reserve:
            self.guard(reserve)
            if read_only_appointment:
                action_name=name+'-readonly-'+str(action_sequence).zfill(4)
                action_path=self.output/(name+'-readonly-request-'+str(action_sequence).zfill(4)+'.json')
                if action_path.is_file():
                    action=read_json(action_path)
                    require(set(action)=={'action','run_id','reviewer','sequence','arguments'} and
                            action['action']=='appointment-full-pool' and action['run_id']==self.frozen['run_id'] and
                            action['reviewer']==self.operator_reviewer and action['sequence']==action_sequence,
                            'Read-only checkpoint action crossed current operator/run/sequence')
                    from ck3_mod_acceptance_appointment import collection_arguments
                    args=collection_arguments(action['arguments'])
                    self.checkpoint(action_name+'-once-intent',action)
                    try:
                        result=self.query_appointment_pool(**args)
                    except ValueError as error:
                        if not str(error).startswith('Appointment collection rejected:'):
                            raise
                        # R66 returned native data, but the stale window cache
                        # failed collection. Keep the original paused checkpoint
                        # so its owner can reopen the window and use a new request.
                        report=self.guard(reserve)
                        self.validate_frame(self.snapshot())
                        submitted=report.get('steps',[])
                        require(all(row.get('finished_at') and row.get('ok') is True and
                                    not row.get('error') for row in submitted),
                                'Appointment retry requires completed healthy host steps')
                        result={'collection_status':'REJECTED','error':str(error),
                            'business_pass':False,'business_acceptance':'NOT_ASSESSED',
                            'original_hold_deadline':self._hold,
                            'submitted_steps_never_replayed':True,
                            'submitted_step_evidence':[{key:row.get(key) for key in
                                ('id','finished_at','ok','error')} for row in submitted]}
                    self.checkpoint(name+'-readonly-response-'+str(action_sequence).zfill(4),result)
                    action_sequence+=1
            if response.is_file():
                value = read_json(response)
                require(value.get('run_id') == self.frozen['run_id'] and value.get('reviewer') == self.operator_reviewer, 'Root checkpoint crossed scene')
                return value
            time.sleep(.25)
        raise TimeoutError('Original normal Quit reserve reached; pending Root phase remains GAP')

    def retain_process(self):
        """Retain the actual managed CK3 handle before any business or GUI action."""
        if self._handle is not None:
            return self._process
        import ctypes, psutil
        control = self.state / 'control/ck3.json'
        record = read_json(control)
        pid = record['ck3_pid']
        require(type(pid) is int and pid > 0, 'Actual managed CK3 PID is invalid')
        process = psutil.Process(pid)
        require(process.name().lower() == 'ck3.exe', 'Managed PID is not CK3')
        creation = process.create_time()
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.OpenProcess.argtypes = [ctypes.c_uint32,ctypes.c_int,ctypes.c_uint32]
        kernel.OpenProcess.restype = ctypes.c_void_p
        kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p,ctypes.c_uint32]
        kernel.WaitForSingleObject.restype = ctypes.c_uint32
        kernel.GetExitCodeProcess.argtypes = [ctypes.c_void_p,ctypes.POINTER(ctypes.c_uint32)]
        kernel.GetExitCodeProcess.restype = ctypes.c_int
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        handle = kernel.OpenProcess(0x100000|0x1000,False,pid)
        require(handle and psutil.Process(pid).create_time() == creation and read_json(control) == record,
                'Actual process/control changed during handle acquisition')
        self._handle, self._kernel = handle, kernel
        self._process = {'pid':pid,'create_time':creation,'retained_synchronize_query_handle_acquired':True}
        self.checkpoint('retained-current-process-identity',self._process)
        return self._process

    def _native_exit_proof(self, report, name):
        # Reuse complete pure predicates from the one selected shared host.
        import ast, copy, re
        source = self.selection.manifest_path_key(self.manifest['host'])
        tree = ast.parse(source.read_text(encoding='utf-8-sig'))
        names = {'finished_native_process_exit_zero_proof', 'finished_native_exit_zero_proof',
                 'finished_native_failure_shutdown_proof'}
        nodes = [n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
        if name not in {n.name for n in nodes}:
            return None  # An old immutable host has no new failure-lifecycle provider.
        namespace = {'datetime':datetime,'re':re,'copy':copy}
        exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),namespace)
        return namespace[name](report,report.get('managed_session_done') is True,
                               {'bridge_pid':self._process['pid']} if self._process else None)

    def native_zero_proof(self, report):
        return self._native_exit_proof(report, 'finished_native_exit_zero_proof')

    def native_failure_shutdown_proof(self, report):
        return self._native_exit_proof(report, 'finished_native_failure_shutdown_proof')

    def start_normal_quit_automation(self, request, config):
        from ck3_mod_acceptance import check_pin
        require(self.remaining() > 0, 'Original normal Quit deadline expired')
        for row in config.values():check_pin(Path(row['path']), row)
        result_path = self.output/'normal-quit-automation-result.json'
        require(not result_path.exists() and not (self.output/'normal-quit-automation-dispatch.json').exists() and
                not (self.live/'case-output/normal-quit-template-automation-once.intent.json').exists() and
                not (self.output/'normal-quit-template-route-01').exists(),
                'Normal Quit automation already consumed; never replay')
        self.focus_retained_process_for_quit()
        argv = [str(self.selection.locations['python']), '-B', '-X', 'utf8', config['helper']['path'],
            '--repo-root', str(self.selection.locations['repo_root']),
            '--matcher', config['matcher']['path'], '--matcher-bytes', str(config['matcher']['bytes']),
            '--matcher-sha256', config['matcher']['sha256'],
            '--templates', config['templates']['path'], '--templates-bytes', str(config['templates']['bytes']),
            '--templates-sha256', config['templates']['sha256'],
            '--live', str(self.live.resolve()), '--keeper-root', str(self.keeper.resolve()),
            '--quit-request', str(request.resolve()), '--expected-reviewer', self.normal_quit_reviewer(),
            '--pid', str(self._process['pid']),
            '--create-time', str(self._process['create_time']), '--original-deadline', str(self._hold),
            '--output', str(self.output.resolve()), '--execute']
        self.checkpoint('normal-quit-automation-dispatch', {'argv':argv, 'pins':config,
            'human_review_claimed':False, 'original_hold_deadline':self._hold})
        environment = dict(os.environ); environment.update(self.selection.runtime_environment)
        with (self.output/'normal-quit-automation.stdout.log').open('xb') as stdout, (self.output/'normal-quit-automation.stderr.log').open('xb') as stderr:
            return subprocess.Popen(argv, cwd=self.selection.locations['repo_root'], env=environment,
                                    stdout=stdout, stderr=stderr)

    def focus_retained_process_for_quit(self):
        """Focus the sole visible window of the retained process, without input."""
        import psutil, win32gui, win32process
        import desktop_coordinate_map as coords
        from record_native_capability_segment import bring_forward
        require(self._handle is not None and self._process is not None, 'Actual retained process required for Quit focus')
        require(not (self.output/'normal-quit-foreground.json').exists(), 'Quit focus already consumed; never replay')
        pid, creation = self._process['pid'], self._process['create_time']

        def guard_owner():
            require(self.remaining() > 0, 'Original Quit deadline reached; no focus or extension')
            actual = psutil.Process(pid)
            require(actual.name().lower() == 'ck3.exe' and actual.create_time() == creation and
                    read_json(self.state/'control/ck3.json').get('ck3_pid') == pid,
                    'Actual retained PID/create-time/control changed before Quit focus')
            lease = json.loads((self.keeper/'journal.jsonl').read_text(encoding='utf-8').splitlines()[-1])
            require(lease.get('result') == 'OWNED_CAS' and lease['lease']['task_id'] == self.frozen['screen_task'] and
                    not (self.keeper/'report.json').exists(), 'Original keeper no longer owns Quit focus')

        guard_owner()
        windows = []
        def collect(hwnd, _):
            if win32gui.IsWindowVisible(hwnd) and win32process.GetWindowThreadProcessId(hwnd)[1] == pid:
                windows.append(hwnd)
        win32gui.EnumWindows(collect, None)
        require(len(windows) == 1, 'Retained CK3 must own exactly one visible HWND; no focus guess')
        hwnd = windows[0]
        before = coords.foreground_state()
        activation_error = None
        guard_owner()
        require(win32gui.IsWindowVisible(hwnd) and win32process.GetWindowThreadProcessId(hwnd)[1] == pid,
                'Actual Quit HWND ownership changed before focus')
        if before['foreground_hwnd'] != hwnd or before['foreground_pid'] != pid or not before['focus_hwnd']:
            try:
                bring_forward(hwnd)  # Existing native focus primitive: no mouse or keyboard.
            except Exception as error:
                activation_error = type(error).__name__ + ': ' + str(error)
        limit = min(time.time() + 2, self._hold)
        while True:
            guard_owner()
            after = coords.foreground_state()
            success = (after['foreground_hwnd'] == hwnd and after['foreground_pid'] == pid and after['focus_hwnd'] > 0)
            if success or time.time() >= limit:
                break
            time.sleep(.05)
        receipt = {'pid':pid, 'create_time':creation, 'hwnd':hwnd, 'before':before, 'after':after,
            'success':success, 'activation_error':activation_error, 'original_hold_deadline':self._hold,
            'mouse_or_keyboard_input':False, 'human_review_claimed':False, 'business_pass':False}
        self.checkpoint('normal-quit-foreground', receipt)
        require(success, 'Actual retained CK3 foreground/focus was not observed; no helper dispatch')
        return receipt

    def validate_normal_quit_automation(self, value, request, config):
        from ck3_mod_acceptance import check_pin
        require(isinstance(value, dict) and value.get('schema') == 'ck3.common-normal-quit-automation.v1' and
            value.get('status') == 'GUI_QUIT_ROUTE_COMPLETE_NATIVE_PROOF_PENDING' and
            value.get('automation_actor') == 'template-automation', 'Normal Quit automation receipt contract differs')
        for key, expected in {'route_complete':True, 'human_review_claimed':False,
                'autosave_unchecked_observed':True, 'final_click_completed':True, 'actual_os0_proven':False,
                'actual_native0_proven':False, 'finish_hold_dispatched':False, 'business_pass':False}.items():
            require(value.get(key) is expected, 'Normal Quit automation qualification differs: '+key)
        require(value.get('run_id') == self.frozen['run_id'] and type(value.get('pid')) is int and
            value['pid'] == self._process['pid'] and type(value.get('create_time')) in (int,float) and
            value['create_time'] == self._process['create_time'] and type(value.get('hwnd')) is int and value['hwnd'] > 0 and
            type(value.get('original_hold_deadline')) in (int,float) and value['original_hold_deadline'] == self._hold,
            'Normal Quit automation crossed scene or original deadline')
        for key, expected in {'quit_request':check_pin(request, value.get('quit_request', {})), **config}.items():
            row = value.get(key)
            require(isinstance(row,dict) and Path(row.get('path','')).resolve() == Path(expected['path']).resolve(),
                    'Normal Quit automation source path differs: '+key)
            require(row.get('bytes') == expected['bytes'] and row.get('sha256') == expected['sha256'],
                    'Normal Quit automation source pin differs: '+key)
            check_pin(Path(row['path']),row)
        require(isinstance(value.get('steps'),list) and value['steps'] and
            isinstance(value.get('evidence'),list) and value['evidence'], 'Original GUI route evidence required')
        for row in value['evidence']:check_pin(Path(row['path']),row)
        final = value.get('final_click')
        require(isinstance(final,dict) and final in value['evidence'], 'Canonical final mapped click receipt required')
        check_pin(Path(final['path']),final)
        mapped = read_json(final['path'])
        require(mapped.get('click_completed') is True and isinstance(mapped.get('failures'),list) and
                set(mapped['failures']) <= {'foreground_changed_after_click'},
                'Canonical final mapped click failed')
        final_steps = [row for row in value['steps'] if row.get('final') is True]
        require(len(final_steps) == 1 and final_steps[0].get('mapping_receipt') == final and
                final_steps[0].get('click_completed') is True, 'Final route step differs from canonical receipt')
        return value

    def normal_quit_reviewer(self):
        """Use the exact UI delegate, otherwise the validated actual run reviewer."""
        return self.resolve_operator_reviewer()

    def validate_manual_normal_quit_review(self, review, *, require_mapped=False):
        from ck3_mod_acceptance import check_pin
        require(isinstance(review,dict) and review.get('run_id')==self.frozen['run_id'] and
                review.get('reviewer')==self.normal_quit_reviewer() and review.get('normal_gui_quit') is True,
                'Normal Quit actual operator review is missing or crossed scene')
        evidence=review.get('evidence')
        require(isinstance(evidence,list) and evidence,'Original GUI Quit evidence required')
        for row in evidence:check_pin(Path(row['path']),row)
        if require_mapped:
            require(type(review.get('pid')) is int and review['pid']==self._process['pid'] and
                    type(review.get('create_time')) in (int,float) and review['create_time']==self._process['create_time'] and
                    type(review.get('original_hold_deadline')) in (int,float) and review['original_hold_deadline']==self._hold,
                    'Manual Quit crossed actual retained process or original deadline')
            require(review.get('autosave_unchecked_observed') is True,'Actual unchecked autosave observation required')
            screenshot=review.get('autosave_unchecked_screenshot');final=review.get('final_click')
            require(isinstance(screenshot,dict) and screenshot in evidence and isinstance(final,dict) and final in evidence,
                    'Original unchecked screenshot and canonical final click must be pinned evidence')
            from PIL import Image
            with Image.open(screenshot['path']) as image:
                image.verify()
            with Image.open(screenshot['path']) as image:
                dimensions=list(image.size)
            mapped=read_json(final['path'])
            require(mapped.get('click_completed') is True and isinstance(mapped.get('failures'),list) and
                    set(mapped['failures']) <= {'foreground_changed_after_click'},'Manual canonical final mapped click failed')
            require(Path(mapped.get('source_image','')).resolve()==Path(screenshot['path']).resolve() and
                    mapped.get('source_image_size')==dimensions,'Manual final click must use the actual original unchecked screenshot')
            receipt=[row for row in evidence if Path(row['path']).resolve()==Path(mapped.get('receipt_path','')).resolve()]
            require(len(receipt)==1,'Canonical after-click screenshot must be pinned evidence')
            with Image.open(receipt[0]['path']) as image:image.verify()
        return review

    def normal_close(self, disposition):
        """Request normal GUI Quit, then prove retained OS0 and shared native0."""
        import ctypes
        require(self._handle is not None, 'No retained game handle; never manufacture OS exit')
        request=self.checkpoint('normal-quit-awaiting',{'run_id':self.frozen['run_id'],'reviewer':self.normal_quit_reviewer(),
            'pid':self._process['pid'],'create_time':self._process['create_time'],
            'original_hold_deadline':self._hold,'disposition':disposition,
            'live':str(self.live.resolve()),'keeper_root':str(self.keeper.resolve()),'screen_task':self.frozen['screen_task'],
            'action':'Authorized operator normal GUI Quit to desktop; preserve original images, mapped clicks and unchecked autosave state',
            'host_error_preserved':self.read_report(allow_error=True).get('error')})
        print('CK3_ROOT_CHECKPOINT '+str(request),flush=True)
        response=self.output/'normal-quit-root-result.json'
        config = getattr(self.selection, 'normal_quit_automation', None)
        automation = None
        report=self.read_report(allow_error=True)
        automation_failure = None
        manual_required = config is None
        helper_finished = False
        if config is not None:
            try:
                process = self.start_normal_quit_automation(request, config)
                while self.remaining()>0 and process.poll() is None:
                    report=self.read_report(allow_error=True)
                    time.sleep(.1)
                exit_code = process.poll()
                self.checkpoint('normal-quit-automation-process', {'exit_code':exit_code,
                    'original_hold_deadline':self._hold, 'human_review_claimed':False})
                if exit_code is not None:
                    require(exit_code == 0, 'Normal Quit automation failed; preserved route is not replayed')
                    helper_finished = True
            except Exception as error:
                automation_failure = self.checkpoint('normal-quit-automation-failure-preserved', {
                    'error':type(error).__name__+': '+str(error),
                    'original_hold_deadline':self._hold, 'helper_result':str(self.output/'normal-quit-automation-result.json'),
                    'automation_replayed':False, 'retained_handle_closed':False, 'business_pass':False})
                manual_required = True
            if helper_finished:
                # An exit0 receipt with forged identity or source pins remains a hard rejection.
                automation = self.validate_normal_quit_automation(
                    read_json(self.output/'normal-quit-automation-result.json'), request, config)
        if manual_required and self.remaining()>0:
            manual=self.checkpoint('manual-quit-awaiting', {
                'status':'MANUAL_QUIT_AWAITING_ORIGINAL_DEADLINE', 'run_id':self.frozen['run_id'],
                'reviewer':self.normal_quit_reviewer(), 'pid':self._process['pid'],
                'create_time':self._process['create_time'], 'original_hold_deadline':self._hold,
                'response_path':str(response), 'automation_failure_preserved':str(automation_failure) if automation_failure else None,
                'required_evidence':'Actual operator original unchecked screenshot and canonical final mapped Quit receipt; normal GUI Quit only',
                'helper_replay_or_new_budget':False, 'business_pass':False})
            print('CK3_MANUAL_QUIT_CHECKPOINT '+str(manual),flush=True)
            while self.remaining()>0 and not response.is_file():
                report=self.read_report(allow_error=True)
                time.sleep(.1)
        review=read_json(response) if manual_required and response.is_file() else None
        if review is not None:
            review=self.validate_manual_normal_quit_review(review, require_mapped=automation_failure is not None)
        while self.remaining()>0 and self._kernel.WaitForSingleObject(self._handle,0)==258:
            time.sleep(.1)
        signaled=self._kernel.WaitForSingleObject(self._handle,0)==0
        code=ctypes.c_uint32()
        available=bool(signaled and self._kernel.GetExitCodeProcess(self._handle,ctypes.byref(code)))
        os0=available and code.value==0
        retained={'signaled':signaled,'exit_code':code.value if available else None,'actual_retained_os0':os0,**self._process}
        self.checkpoint('actual-retained-handle-os-exit',retained)
        self._failure_shutdown_retained = retained if (review or automation) and os0 else None
        proof=None
        failure_proof=None
        while self.remaining()>0:
            report=self.read_report(allow_error=True)
            proof=self.native_zero_proof(report)
            failure_proof=self.native_failure_shutdown_proof(report)
            if proof is not None or failure_proof is not None or report.get('finished_at'):break
            time.sleep(.1)
        finished=None
        if proof is not None and not report.get('finished_at'):
            finished=self.execute_plan([{'id':'acceptance-normal-exit-finish-hold','kind':'finish_hold',
                'expect':{'hold_finished':True}}],'acceptance-normal-exit-finish-hold',reserve=0)
        elif failure_proof is not None and (review or automation) and os0 and not report.get('finished_at'):
            finished=self.execute_plan([{'id':'acceptance-failure-exit-finish-hold','kind':'finish_hold',
                'failure_shutdown':True, 'expect':{'hold_finished':True,'failure_preserved':True,
                    'business_pass':False,'normal_close_qualified':False}}],
                'acceptance-failure-exit-finish-hold',reserve=0)
        while self.remaining()>0:
            report=self.read_report(allow_error=True)
            if report.get('finished_at'):break
            time.sleep(.1)
        result={'root_normal_gui_review':review,'operator_normal_gui_review':review,
            'normal_quit_automation':automation,'normal_quit_automation_failure_preserved':str(automation_failure) if automation_failure else None,
            'retained_handle':retained,'native_zero_proof':proof,
            'finish_hold_rows':finished,'host_finished_at':report.get('finished_at'),
            'managed_thread_finished':report.get('managed_session_thread_finished'),
            'cleanup_ok':report.get('cleanup_ok'),'host_error':report.get('error'),
            'failure_shutdown_proof':failure_proof,
            'failure_preserved':bool(failure_proof is not None and report.get('error') == failure_proof['host_error']),
            'failure_lifecycle_completed':bool((review or automation) and os0 and failure_proof is not None and
                report.get('finished_at') and report.get('managed_session_thread_finished') is True and
                report.get('cleanup_ok') is True and report.get('error') == failure_proof['host_error'] and
                isinstance(finished,list) and len(finished) == 1 and finished[0].get('ok') is True and
                report.get('post_failure_exit_finish_hold',{}).get('proof') == failure_proof),
            'business_pass':False,
            'normal_close_qualified':bool((review or automation) and os0 and proof is not None and report.get('finished_at') and
                report.get('managed_session_thread_finished') is True and report.get('cleanup_ok') is True and not report.get('error'))}
        self.checkpoint('normal-close-result',result)
        return result

    def close_handle(self):
        if self._handle is not None:
            self._kernel.CloseHandle(self._handle);self._handle=None
