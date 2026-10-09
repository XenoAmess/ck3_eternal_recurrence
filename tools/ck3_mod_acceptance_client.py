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
        self._handle = None
        self._kernel = None
        self._process = None
        write_once(self.output / 'case-once.json', {
            'run_id': self.frozen['run_id'], 'product': selection.product_key,
            'case': selection.case['id'], 'host_argv': selection.argv,
            'runtime_manifest': str(selection.manifest_path), 'business_acceptance': 'NOT_ASSESSED'})

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

    def guard(self, reserve=90):
        require(self.remaining() > reserve, 'Original normal Quit reserve reached')
        keeper = self.keeper
        journal = keeper / 'journal.jsonl'
        lease = json.loads(journal.read_text(encoding='utf-8').splitlines()[-1])
        require(lease.get('result') == 'OWNED_CAS' and not (keeper / 'report.json').exists(),
                'Original screen keeper no longer owns this held scene')
        require(lease['lease']['task_id'] == self.frozen['screen_task'], 'Current keeper crossed actual allocation')
        report = self.read_report()
        require(report.get('phase') == 'hold' and not report.get('finished_at') and
                not report.get('hold_finished_by_control_plan') and (reserve==0 or not report.get('cleanup_ok')),
                'Original held session is no longer active')
        return report

    def wait_hold(self):
        preparation = (self.selection.prepared or {}).get('preparation', {})
        budget = 'timeout' if preparation.get('initial_plan_original_business') is True else 'readiness_timeout'
        limit = time.monotonic() + self.selection.case['budgets'][budget]
        while time.monotonic() < limit:
            try:
                report = self.read_report()
            except FileNotFoundError:
                time.sleep(.1); continue
            require(not report.get('finished_at'), 'Shared host ended before case entry')
            if report.get('phase') == 'hold' and all(row.get('finished_at') for row in report.get('steps', [])):
                self.guard()
                self.retain_process()
                return report
            time.sleep(.1)
        raise TimeoutError('Original case readiness budget elapsed')

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
        if reserve == 0:
            require(self.native_zero_proof(self.read_report()) is not None, 'Original native0 predicate did not admit finish_hold')
        report = self.guard(reserve)
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

    def root_checkpoint(self, name, request, reserve=90):
        path = self.checkpoint(name + '-awaiting', {'run_id':self.frozen['run_id'],
            'original_hold_deadline':self._hold,'reserve_seconds':reserve, **request})
        print('CK3_ROOT_CHECKPOINT ' + str(path), flush=True)
        response = self.output / (name + '-root-result.json')
        while self.remaining() > reserve:
            self.guard(reserve)
            if response.is_file():
                value = read_json(response)
                require(value.get('run_id') == self.frozen['run_id'] and value.get('reviewer') == '/root', 'Root checkpoint crossed scene')
                return value
            time.sleep(.25)
        raise TimeoutError('Original normal Quit reserve reached; pending Root phase remains GAP')

    def retain_process(self):
        """Retain the actual managed CK3 handle before any business or GUI action."""
        if self._handle is not None:
            return self._process
        import ctypes, psutil
        control = self.state / 'control/ck3.json'
        pid = read_json(control)['ck3_pid']
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
        require(handle and psutil.Process(pid).create_time() == creation, 'Actual process changed during handle acquisition')
        self._handle, self._kernel = handle, kernel
        self._process = {'pid':pid,'create_time':creation,'retained_synchronize_query_handle_acquired':True}
        self.checkpoint('retained-current-process-identity',self._process)
        return self._process

    def native_zero_proof(self, report):
        # Execute this one pure predicate from the selected shared host bytes,
        # not a product-local copy or a reduced list of shutdown conditions.
        import ast, copy, re
        source = self.selection.manifest_path_key(self.manifest['host'])
        tree = ast.parse(source.read_text(encoding='utf-8-sig'))
        node = next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='finished_native_exit_zero_proof')
        namespace = {'datetime':datetime,'re':re,'copy':copy}
        exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),namespace)
        return namespace[node.name](report,report.get('managed_session_done') is True,
                                    {'bridge_pid':self._process['pid']} if self._process else None)

    def normal_close(self, disposition):
        """Request Root GUI Quit, then prove retained OS0 and shared native0."""
        import ctypes
        require(self._handle is not None, 'No retained game handle; never manufacture OS exit')
        request=self.checkpoint('normal-quit-awaiting',{'run_id':self.frozen['run_id'],'reviewer':'/root',
            'pid':self._process['pid'],'create_time':self._process['create_time'],
            'original_hold_deadline':self._hold,'disposition':disposition,
            'action':'Root normal GUI Quit to desktop; preserve actual images and autosave state',
            'host_error_preserved':self.read_report(allow_error=True).get('error')})
        print('CK3_ROOT_CHECKPOINT '+str(request),flush=True)
        response=self.output/'normal-quit-root-result.json'
        while self.remaining()>0 and not response.is_file():
            report=self.read_report(allow_error=True)
            time.sleep(.1)
        review=read_json(response) if response.is_file() else None
        if review is not None:
            require(review.get('run_id')==self.frozen['run_id'] and review.get('reviewer')=='/root' and
                    review.get('normal_gui_quit') is True,'Normal Quit Root review is missing or crossed scene')
            from ck3_mod_acceptance import check_pin
            require(review.get('evidence'),'Original GUI Quit evidence required')
            for row in review['evidence']:check_pin(Path(row['path']),row)
        while self.remaining()>0 and self._kernel.WaitForSingleObject(self._handle,0)==258:
            time.sleep(.1)
        signaled=self._kernel.WaitForSingleObject(self._handle,0)==0
        code=ctypes.c_uint32()
        available=bool(signaled and self._kernel.GetExitCodeProcess(self._handle,ctypes.byref(code)))
        os0=available and code.value==0
        retained={'signaled':signaled,'exit_code':code.value if available else None,'actual_retained_os0':os0,**self._process}
        self.checkpoint('actual-retained-handle-os-exit',retained)
        proof=None
        while self.remaining()>0:
            report=self.read_report(allow_error=True)
            proof=self.native_zero_proof(report)
            if proof is not None or report.get('finished_at'):break
            time.sleep(.1)
        finished=None
        if proof is not None and not report.get('finished_at'):
            finished=self.execute_plan([{'id':'acceptance-normal-exit-finish-hold','kind':'finish_hold',
                'expect':{'hold_finished':True}}],'acceptance-normal-exit-finish-hold',reserve=0)
        while self.remaining()>0:
            report=self.read_report(allow_error=True)
            if report.get('finished_at'):break
            time.sleep(.1)
        result={'root_normal_gui_review':review,'retained_handle':retained,'native_zero_proof':proof,
            'finish_hold_rows':finished,'host_finished_at':report.get('finished_at'),
            'managed_thread_finished':report.get('managed_session_thread_finished'),
            'cleanup_ok':report.get('cleanup_ok'),'host_error':report.get('error'),
            'normal_close_qualified':bool(review and os0 and proof is not None and report.get('finished_at') and
                report.get('managed_session_thread_finished') is True and report.get('cleanup_ok') is True and not report.get('error'))}
        self.checkpoint('normal-close-result',result)
        return result

    def close_handle(self):
        if self._handle is not None:
            self._kernel.CloseHandle(self._handle);self._handle=None
