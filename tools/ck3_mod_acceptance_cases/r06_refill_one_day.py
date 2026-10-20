"""One natural refill day on the caller's public CaseClient.

The shared entry owns SDK, game and normal closure. This module owns one
separately qualified thirty-second observer, never retries an unknown action,
and consumes the original full native response before clearing its journal.
"""
from contextlib import redirect_stdout
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
import copy
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import time

from .r10_prepare_adapter import need, pin, small_json, module
from . import r04_county_entry as common

LIVE = Path('ck3_autonomous_player/native_bridge/research/refill_add_live_12004')
FLAGS = {'XAR_ENABLE_REFILL_ADD_HWPROBE_12004': 'ON',
         'XAR_ENABLE_REFILL_STACK_Q_COLD_12004': 'OFF',
         'XAR_ENABLE_REFILL_V3_COLD_PROBE_12004': 'OFF',
         'XAR_ENABLE_REFILL_CARRIER_THREAD_DISCOVERY_12004': 'ON',
         'XAR_ENABLE_REFILL_V5_COLD_PROBE_12004': 'OFF'}


def read(path, maximum=262144):
    path = Path(path)
    need(path.is_file() and 0 < path.stat().st_size <= maximum, 'Bounded R06 input required: ' + str(path))
    return json.loads(path.read_bytes())


def checked(ref, maximum=262144):
    path = Path(ref['path'])
    need(path.is_file() and 0 < path.stat().st_size <= maximum, 'Bounded exact R06 input required')
    need(pin(path) == ref, 'Exact R06 input changed')
    return read(path, maximum)


def write(path, value, maximum=262144):
    data = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    need(len(data) <= maximum, 'R06 output exceeds its exact bound')
    with Path(path).open('xb') as stream:
        stream.write(data)
    return pin(path)


def settings(value):
    required = {'scene_root', 'capacity_admission', 'producer', 'expected_source_save_sha256',
                'expected_start_date_raw', 'source_province_id', 'actor_id', 'army_id',
                'native_carmy_id', 'driver_limit_bytes', 'profile_limit_bytes', 'deadline_utc', 'prefix'}
    need(type(value) is dict and required <= set(value), 'Explicit complete R06 settings required')
    defaults = dict(camera_timeout_seconds=600, ready_timeout_seconds=12,
                    observer_total_timeout_seconds=50, one_day_timeout=20,
                    normal_close_reserve=900, cleanup_save_reserve=120,
                    next_full_reserve_bytes=64*1024*1024, max_packet_bytes=32*1024*1024,
                    mirror_limit_bytes=67*1024*1024, cleanup_mirror_reserve_bytes=3*1024*1024,
                    poll_seconds=.25, speed=5, max_modal_choices=64)
    need(set(value) <= required | set(defaults), 'Unknown R06 setting')
    a = SimpleNamespace(**{**defaults, **value})
    for key in ('expected_start_date_raw', 'source_province_id', 'actor_id',
                'driver_limit_bytes', 'profile_limit_bytes', 'next_full_reserve_bytes'):
        need(type(getattr(a, key)) is int and getattr(a, key) > 0, 'Positive R06 ' + key + ' required')
    need(type(a.army_id) is int and 0 <= a.army_id < 2**31 and
         type(a.native_carmy_id) is int and -(2**31) <= a.native_carmy_id < 2**31 and a.native_carmy_id != -1,
         'R06 actual full Army IDs required')
    need(re.fullmatch('[0-9a-f]{64}', a.expected_source_save_sha256 or '') is not None, 'R06 source SHA required')
    need(re.fullmatch('[A-Za-z][A-Za-z0-9_-]{0,47}', a.prefix or '') is not None, 'Unique R06 prefix required')
    for key, low, high in (('camera_timeout_seconds', 1, 900), ('ready_timeout_seconds', 1, 20),
                           ('observer_total_timeout_seconds', 35, 60), ('one_day_timeout', 2, 25)):
        v = getattr(a, key)
        need(type(v) in (int, float) and math.isfinite(v) and low <= v <= high, 'Finite R06 ' + key + ' required')
    need(a.normal_close_reserve >= 900 and a.cleanup_save_reserve >= 120, 'Original close reserves required')
    deadline = datetime.fromisoformat(a.deadline_utc.replace('Z', '+00:00'))
    need(deadline.tzinfo is not None, 'Timezone-aware R06 deadline required')
    need(type(a.producer) is dict, 'Explicit qualified producer inputs required')
    return a


def validate_contract(context):
    a = settings(context['case_inputs']['r06_refill_one_day'])
    need(context['case_inputs'].get('r04_county_entry') is None, 'R04 and R06 are mutually exclusive')
    seed = context.get('saved_campaign') or {}
    if seed:
        need(seed.get('sha256') == a.expected_source_save_sha256 and
             seed.get('date_raw') == a.expected_start_date_raw and seed.get('player_id') == a.actor_id,
             'R06 selected normal save/date/actor differs')
    if context.get('run_id') is None:
        need(a.capacity_admission is None,'Prepare R06 with explicit null capacity; allocation supplies the real run ID')
    else:
        need(a.capacity_admission is not None,'Actual R06 requires its post-allocate capacity binding')
    return a


def contains(value, predicate):
    if isinstance(value, dict):
        return predicate(value) or any(contains(v, predicate) for v in value.values())
    return isinstance(value, list) and any(contains(v, predicate) for v in value)


def verify_producer(producer, *, machine_id, native_tree):
    """Actual receipts, never an authored boolean standing in for qualification."""
    required = {'qualification', 'build_result', 'SYSTEM_receipt', 'cold_result', 'source_dir',
                'observer_exe', 'observer_exe_sha256', 'native_build_source_head', 'native_tree',
                'carrier_module_path', 'carrier_source_epoch', 'cmake_defines'}
    need(required == set(producer), 'Complete exact R06 producer fields required')
    p = producer
    q = checked(p['qualification'], 1024*1024)
    build = checked(p['build_result'])
    system = checked(p['SYSTEM_receipt'], 4*1024*1024)
    cold = checked(p['cold_result'], 1024*1024)
    need(q.get('machine_id') == machine_id and q.get('production_bytes_qualified') is True
         and q.get('focused_cold_qualified') is True, 'Actual same-machine production/cold qualification required')
    need(q.get('native_build_source_head', q.get('source_head')) == p['native_build_source_head']
         and q.get('native_tree') == p['native_tree'] == native_tree, 'Coherent actual native source/tree differs')
    need(p['cmake_defines'] == FLAGS and contains(q, lambda d: all(d.get(k) == v for k, v in FLAGS.items())),
         'Actual live worker five compile flags differ')
    need(build.get('built') is True and Path(build['source_dir']).resolve() == Path(p['source_dir']).resolve(),
         'Actual worker build/source directory differs')
    need(system.get('status') == 'verified' and system.get('admin_token') is True
         and system.get('system_token_sid') == 'S-1-5-18', 'Actual SYSTEM verification required')
    need(build.get('defender_exclusions', {}).get('receipt_sha256') == p['SYSTEM_receipt']['sha256'],
         'Worker build/SYSTEM exact receipt differs')
    exe = Path(p['observer_exe']).resolve()
    need(exe.name == 'refill_add_hwprobe_12004.exe' and exe.is_file(), 'Actual production observer required')
    match = lambda d: (d.get('sha256') == p['observer_exe_sha256'] and type(d.get('path')) is str
                       and Path(d['path']).resolve() == exe)
    need(contains(q, match) and contains(system, match), 'Qualified observer EXE not bound to Q and SYSTEM')
    need(contains(q, lambda d: d.get('sha256') == p['build_result']['sha256']), 'Q does not bind actual worker build')
    need(cold.get('status') == 'PASS' and cold.get('case_count') == 2 and
         len(cold.get('cases', [])) == 2 and all(c.get('status') == 'PASS' for c in cold['cases']),
         'Both actual V5 cold cases required')
    need(contains(q, lambda d: d.get('sha256') == p['cold_result']['sha256']), 'Q does not bind actual cold result')
    need(p['carrier_source_epoch'] == 20261018 and type(p['carrier_source_epoch']) is int and
         Path(p['carrier_module_path']).is_absolute() and Path(p['carrier_module_path']).name.lower() == 'xar_ck3_bridge.dll',
         'Actual source-bound carrier module required')
    need(Path(p['source_dir']).is_absolute() and Path(p['source_dir']).name == 'refill_add_live_12004'
         and Path(p['source_dir']).is_dir(), 'Existing frozen worker source required')
    return q


def validate_admission(value, *, expected, producer, native_tree):
    """Root's fresh metadata admission is distinct from actual debugger READY."""
    need(value.get('schema') == 'xar.r06.public_worker_source_admission.v1' and
         all(type(value.get(k)) is type(v) and value[k] == v for k, v in expected.items()),
         'Fresh Root worker admission identity differs')
    observed = datetime.fromisoformat(value['observed_at_utc'].replace('Z', '+00:00')).timestamp()
    need(0 <= time.time() - observed <= 300, 'Root worker metadata admission expired')
    n, reserve = value.get('maximum_owned_threads'), value.get('birth_reserve_generations')
    census = checked(value['thread_census'])
    need(census.get('machine_id') == expected['machine_id'] and census.get('run_id') == expected['run_id']
         and census.get('pid') == expected['bridge_pid']
         and census.get('process_creation_FILETIME') == expected['process_creation_filetime'], 'OS census owner differs')
    samples = census.get('snapshots')
    need(type(samples) is list and len(samples) == 3 and all(s.get('complete') is True for s in samples),
         'Three complete OS metadata snapshots required')
    union = set()
    for sample in [*samples, value['latest_thread_snapshot']]:
        sampled=datetime.fromisoformat(sample['observed_at_utc'].replace('Z','+00:00')).timestamp()
        need(0<=time.time()-sampled<=300,'OS thread metadata snapshot expired')
        need(sample.get('complete') is True and sample.get('unresolved') == [] and
             type(sample.get('os_list_count')) is int and 1<=sample['os_list_count']<=256 and
             sample.get('os_list_count') == len(sample.get('generations', [])), 'Complete fourth OS metadata snapshot required')
        need(len({r[0] for r in sample['generations']}) == len(sample['generations']), 'Duplicate OS TID in one census')
        for row in sample['generations']:
            need(type(row) is list and len(row) == 2 and all(type(v) is int and v > 0 for v in row),
                 'Exact OS TID/creation metadata required')
            union.add(tuple(row))
    need(type(n) is int and 1 <= n <= 256 and type(reserve) is int and reserve > 0
         and len(union) + reserve <= n, 'OS union plus explicit positive birth reserve exceeds N<=256')
    module = value['actual_module']
    need(module.get('pid') == expected['bridge_pid'] and module.get('process_created_filetime') == expected['process_creation_filetime']
         and module.get('complete_module_metadata_enumeration') is True
         and Path(module['module']['path']).resolve() == Path(producer['carrier_module_path']).resolve(),
         'Actual loaded carrier module/PID FILETIME differs')
    need(value.get('native_qualification') == producer['qualification'] and value.get('native_tree') == native_tree,
         'Root admission does not bind actual native qualification')
    return n


def verify_runtime(selection, producer, native_tree):
    qualified=selection.manifest.get('qualification',{})
    need(qualified.get('actual_producer')==producer['qualification'] and qualified.get('native_tree')==native_tree
         and Path(selection.paths['dll']).resolve()==Path(producer['carrier_module_path']).resolve(),
         'Selected shared runtime DLL/qualification differs from admitted producer')


def verify_observer_bytes(actual_path, producer):
    """Read the executable at the final launch boundary, including same-path rebuilds."""
    path=Path(actual_path).resolve()
    need(path==Path(producer['observer_exe']).resolve(),'Prepared observer path differs from qualified producer')
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        before=os.fstat(stream.fileno())
        need(0<before.st_size<=16*1024*1024,'Bounded actual observer executable required')
        for chunk in iter(lambda:stream.read(1024*1024),b''):
            digest.update(chunk)
        after=os.fstat(stream.fileno())
    identity=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
    need(identity(before)==identity(after),'Observer executable changed during final hash')
    need(identity(after)==identity(path.stat()),'Observer path was replaced during final hash')
    actual=digest.hexdigest()
    need(actual==producer['observer_exe_sha256'],'Actual observer EXE SHA differs from qualified Q/SYSTEM bytes')
    return dict(path=str(path),bytes=after.st_size,sha256=actual,
                observed_at_utc=datetime.now(timezone.utc).isoformat(),
                actual_payload_rehashed_here=True,st_dev=after.st_dev,st_ino=after.st_ino,
                mtime_ns=after.st_mtime_ns)


def revalidate_before_launch(probe, admission_pin, *, expected, producer, native_tree):
    """Camera waits confer no freshness or permission to use changed EXE bytes."""
    admission=checked(admission_pin)
    n=validate_admission(admission,expected=expected,producer=producer,native_tree=native_tree)
    need(probe.prepared.get('maximum_owned_threads')==n,'Prepared N differs from revalidated Root admission')
    verify_producer(producer,machine_id=expected['machine_id'],native_tree=native_tree)
    exe=verify_observer_bytes(probe.prepared['native_argv'][0],producer)
    need(validate_admission(admission,expected=expected,producer=producer,native_tree=native_tree)==n,
         'Root admission changed or expired during final producer verification')
    return dict(source_admission=admission_pin,maximum_owned_threads=n,
                native_qualification=producer['qualification'],observer_exe=exe,
                observed_at_utc=datetime.now(timezone.utc).isoformat(),
                actual_worker_launch_or_day_qualified=False)


def native_inputs(before, originals, proof):
    """Preserve actual null episode from original public rows, never an alias."""
    frame = copy.deepcopy(originals.frames[(before['frame']['snapshot_id'], before['frame']['revision'])])
    row = originals.queries[proof['public_control_name']]
    after = row.get('after_snapshot')
    keys = ('snapshot_id', 'revision', 'native_revision', 'date_raw', 'episode_run_id', 'episode_projection')
    need(type(after) is dict and all(frame.get(k) == after.get(k) for k in keys), 'Original paired full-query frames differ')
    need(frame.get('episode_projection') == 'native_campaign' and frame.get('episode_run_id') is None,
         'Actual ordinary native null episode required')
    packet = copy.deepcopy(before['query'])
    need(all(packet.get(q) == frame[k] for q, k in
             (('queried_snapshot_id', 'snapshot_id'), ('queried_revision', 'revision'),
              ('queried_native_revision', 'native_revision'), ('queried_date_raw', 'date_raw'))), 'Actual query frame differs')
    packet['queried_episode_run_id'] = None
    return frame, packet


def prepare_inputs(prepare, paths, packet_path):
    """Only one exact selected packet gets the existing 32MiB exception."""
    original = prepare.read
    target = Path(packet_path).resolve()
    def bounded(path, limit=2*1024*1024):
        return original(path, 32*1024*1024 if Path(path).resolve() == target else limit)
    prepare.read = bounded
    return original


class OriginalRows(common.PreservedCaseQueue):
    def __init__(self, client):
        super().__init__(client)
        self.frames, self.queries = {}, {}
    def execute_plan(self, steps, name, *args, **kwargs):
        rows = super().execute_plan(steps, name, *args, **kwargs)
        if len(rows) == len(steps) == 1 and rows[0].get('ok') is True and not rows[0].get('error'):
            if steps[0]['tool'] == 'ck3_take_snapshot':
                f = rows[0]['result']
                self.frames[(f['snapshot_id'], f['revision'])] = copy.deepcopy(f)
            if steps[0]['tool'] == 'ck3_query_army_strengths':
                self.queries[name] = copy.deepcopy(rows[0])
        return rows


class Probe:
    def __init__(self, repo, prepared_path, output, a):
        self.repo, self.path, self.output, self.a = repo, prepared_path, output, a
        self.prepared = read(prepared_path)
        self.validator = module(repo/LIVE/'launch_live_refill_add.py', 'r06_worker_launcher')
        self.validator.validate_prepared_ready_scope(self.prepared)
        self.process = None
        self.restored = False
        self.pair = None
    def start(self, prelaunch, claim):
        need(self.process is None, 'Observer launch already claimed; never replay')
        need(not getattr(self, 'launch_claimed', False), 'Observer launch already claimed; never replay')
        self.output.mkdir(exist_ok=False)
        self.streams = [(self.output/n).open('xb') for n in ('supervisor.stdout', 'supervisor.stderr')]
        argv = [sys.executable, '-B', '-X', 'utf8', str(self.repo/LIVE/'launch_live_refill_add.py'),
                '--prepared', str(self.path), '--prepared-sha256', pin(self.path)['sha256'],
                '--output-root', str(self.output/'supervisor')]
        try:
            # Validate at the actual Popen boundary, after camera coordination
            # and all potentially slow preparation. Failure launches nothing.
            self.prelaunch_verification=prelaunch()
            claim()
            self.launch_claimed = True
            self.started = time.monotonic()
            self.process = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=self.streams[0], stderr=self.streams[1],
                                            creationflags=subprocess.CREATE_NO_WINDOW)
        except BaseException:
            for stream in self.streams: stream.close()
            raise
        return self.prelaunch_verification
    def remaining(self):
        return self.started + 30 - time.monotonic()
    def ready(self):
        until = self.started + self.a.ready_timeout_seconds
        path = self.output/'supervisor/READY.actual.json'
        while time.monotonic() < until:
            if path.is_file():
                receipt = read(path)
                actual = checked(receipt['ready'], 16384)
                self.validator.validate_actual_ready(self.prepared, actual, self.prepared['ready_must_match'])
                need(receipt.get('ready_verified') is True and receipt.get('observer_alive_at_check') is True
                     and self.process.poll() is None, 'Observer not alive at actual READY')
                self.ready_receipt = pin(path)
                return receipt
            need(self.process.poll() is None, 'Observer exited before READY; no day/rearm')
            time.sleep(.05)
        raise TimeoutError('Actual R06 READY absent; no day/rearm')
    def finish(self):
        need(self.process is not None, 'Observer not launched')
        if self.process.poll() is None:
            self.process.wait(timeout=max(.01, self.started+self.a.observer_total_timeout_seconds-time.monotonic()))
        for stream in self.streams:
            if not stream.closed:
                stream.flush(); stream.close()
        ex = read(self.output/'supervisor/EXIT.actual.json')
        argv = self.prepared['native_argv']
        self.raw_path = Path(argv[argv.index('--raw')+1])
        need(self.raw_path.stat().st_size <= 131072, 'Native raw bound exceeded')
        raw = self.raw_path.read_bytes()
        rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
        terminals = [r for r in rows if r.get('kind') == 'terminal']
        need(len(terminals) == 1, 'Unique native restoration terminal required')
        terminal = terminals[0]
        expected = self.prepared['ready_must_match']
        need(ex.get('target_pid') == expected['pid'] and
             ex.get('process_created_filetime') == expected['process_created_filetime'], 'Native exit scope differs')
        self.restored = (ex.get('launcher_error') is None and terminal.get('debug_registers_cleared') is True
                         and terminal.get('detached') is True and self.process.returncode in (0, 1))
        self.exit = dict(supervisor=pin(self.output/'supervisor/EXIT.actual.json'), native_terminal=terminal,
                         native_restore_verified=self.restored)
        return self.exit
    def paired(self):
        if self.pair is not None:
            return self.pair
        need(self.process.poll() == 0, 'No successful completed observer pair')
        self.finish()
        receipt = checked(self.ready_receipt)
        ex = read(self.output/'supervisor/EXIT.actual.json')
        need(self.restored and ex.get('ready_verified') is True and ex.get('observer_exit_code') == 0
             and ex.get('observer_pid') == receipt.get('observer_pid'), 'Actual paired exit/READY differs')
        binding = read(self.path.parent/'owner-binding.json', 16384)
        contract = module(self.repo/'ck3_autonomous_player/src/xar_autoplayer/bridge/army_target_instruction_core_proof_12004.py',
                          'r06_actual_worker_contract')
        physical, carrier, *_ = contract._worker_wire(self.raw_path.read_bytes(), binding)
        need(physical.get('actual_ADD_observed') is True and physical.get('clean_detach_and_register_restore') is True,
             'Completed worker raw lacks strict pair/restore')
        self.pair = dict(native_restore_verified=True, native_core_token=carrier['invocation_token'],
                         selected_thread_id=physical['selected_thread_id'], selected_thread_generation=physical['selected_thread_generation'])
        return self.pair


def guarded_call(probe, call, context):
    """After actual paired exit, allow only export/stop; never another mutation."""
    base_timeout = context['command_timeout']
    def invoke(label, tool, args, **kwargs):
        if kwargs.get('cleanup'):
            return call(label, tool, args, **kwargs)
        if probe.process.poll() is None and probe.remaining() > 2:
            timeout = min(base_timeout, probe.remaining()-2)
        else:
            allowed = tool in ('ck3_take_snapshot', 'ck3_query_army_strengths', 'ck3_query_army_observer_research_sampling_v1')
            allowed |= tool == 'ck3_execute_step' and args.get('step') in ('research-query-tactical-daily-sentinel-v1', 'pause-map')
            allowed |= tool == 'ck3_set_army_observer_research_sampling_v1' and args.get('enabled') is False
            need(allowed, 'Observer expired/exited: no new Arm/Resume/Continue')
            probe.paired()
            timeout = min(base_timeout, 10)
        previous = context['command_timeout']
        context['command_timeout'] = timeout
        try:
            return call(label, tool, args, **kwargs)
        finally:
            context['command_timeout'] = previous
    return invoke


def require_restored_for_save(probe):
    need(probe is None or not getattr(probe, 'launch_claimed', False) or probe.restored,
         'Observer restoration absent: Save withheld')


def run_case(context, client):
    from ck3_live_run_id import current_machine_id
    from ck3_mod_acceptance_full_army import FullArmyResultClient
    from ck3_mod_acceptance_cases.r08_writer_common_adapter import retained_creation_filetime
    from xar_autoplayer.bridge.r05_supply_observation_case import ObservationIO
    from xar_autoplayer.bridge.army_observer_research_sampling_control import normalize_result
    from xar_autoplayer.bridge.army_source_derived_next_daily_supply_frame_contract import normalize_source_derived_next_daily_supply_frame_inputs_v1
    a = validate_contract(context)
    repo = Path(context['repo_root']).resolve()
    machine = current_machine_id()
    head = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
    tree = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD:ck3_autonomous_player/native_bridge'], text=True).strip()
    verify_producer(a.producer, machine_id=machine, native_tree=tree)
    verify_runtime(client.selection,a.producer,tree)
    cap = small_json(a.capacity_admission)
    retained = client.retain_process()
    report = client.read_report()
    binding = common.actual_binding(client.selection, Path(a.scene_root), retained, report, cap,
                                    machine_id=machine, source_head=head, a=a)
    binding['process_creation_filetime'] = retained_creation_filetime(client)
    if context.get('r06_post_allocate_scope') is not None:
        binding['post_allocate_scope']=context['r06_post_allocate_scope']
    binding['saved_campaign_source'] = common.bound_saved_campaign_source(report, client.frozen, client.selection.prepared, binding,
        sha=a.expected_source_save_sha256, date_raw=a.expected_start_date_raw, actor=a.actor_id, state_dir=client.selection.state_dir)
    deadline = datetime.fromtimestamp(min(datetime.fromisoformat(a.deadline_utc.replace('Z', '+00:00')).timestamp(), binding['hold']), timezone.utc)
    need(min(client.remaining(),deadline.timestamp()-time.time()) >= 2100, 'R06 MapReady lacks original 2100-second room')
    originals = OriginalRows(client)
    wrapped = FullArmyResultClient(originals, prefix=a.prefix)
    frame = wrapped.snapshot(require_event_free=False)
    init = dict(pid=binding['pid'], army_id=a.army_id, carmy_id=a.native_carmy_id, episode=frame['episode_run_id'],
                independent_after=dict(actor_id=a.actor_id, generation=frame['diagnostics']['connection_generation'], province_id=a.source_province_id))
    options = common.observation_options(SimpleNamespace(**{**vars(a), 'max_days': 1}), deadline)
    io = ObservationIO(wrapped, options, context=dict(output=str(client.output), machine_id=machine,
        command_timeout=context['case_inputs'].get('budgets', {}).get('command_timeout', 120)), initialization=init)
    result = dict(machine_id=machine, run_id=context['run_id'], actual_binding=binding, actual_days=0, exact_day_verified=False,
                  actual_ADD_observed=False, status='ENTERED', full_R06_qualified=False, Move_attempts=0)
    probe = None
    def fence(f, date):
        unit = common.selected_unit(f, a.army_id)
        need(f.get('paused') is True and f.get('map_ready') is True and f['date_raw'] == date
             and f['played_character']['character_id'] == a.actor_id and f['played_character'].get('alive') is True
             and f['diagnostics']['bridge_pid'] == binding['pid'] and f['diagnostics']['connection_generation'] == init['independent_after']['generation']
             and unit['owner_character_id'] == a.actor_id and unit['current_province_id'] == a.source_province_id
             and unit.get('route_province_ids') == [] and unit.get('move_target_province_id') is None
             and unit.get('in_combat') is False and unit.get('retreating') is False, 'Actual R06 date/owner/stationary Army fence differs')
    def sample(label, current=None):
        common.runtime_bytes(client.selection, cap, limit=a.driver_limit_bytes, profile_limit=a.profile_limit_bytes,
                             reserve=a.next_full_reserve_bytes*2)
        f = current or io.snapshot(label+'-before', paused=True)
        q = io.call(label+'-full', 'ck3_query_army_strengths', dict(army_ids=[a.army_id], profile='observed_history_full_v1',
                    ordered_refill_entry_mode='fixed_chunk0_prepare', ordered_besieging_entry_mode='observed_prepared', expected_revision=f['revision']), readonly_strength=True)
        after = io.snapshot(label+'-independent-after', paused=True)
        need(f['date_raw'] == after['date_raw'] and f['native_revision'] == after['native_revision'], 'R06 full query crossed native frame')
        rows = [r for r in q['army_strengths'] if r['army_id'] == a.army_id]
        need(len(rows) == 1 and rows[0]['status'] == 'available' and rows[0]['native_carmy_id'] == a.native_carmy_id, 'Complete same Army full query required')
        return dict(frame=f, query=q, army=rows[0])
    def sampling(enabled, family, cleanup=False):
        f = io.snapshot('sampling-'+family, paused=True, cleanup=cleanup)
        args = dict(observer_family=family, expected_revision=f['revision'])
        if enabled is not None:
            args['enabled'] = enabled
        if enabled is True:
            args['regular_core_full_carmy_ids'] = [a.native_carmy_id]
        tool = 'ck3_query_army_observer_research_sampling_v1' if enabled is None else 'ck3_set_army_observer_research_sampling_v1'
        b = io.call('sampling-'+family, tool, args, cleanup=cleanup)
        mode = 'query' if enabled is None else 'enable' if enabled else 'disable'
        v = normalize_result({k:b[k] for k in ('step','accepted','status','army_observer_research_sampling_v1','backend_id')},
                             expected_step=mode+'-army-observer-research-sampling-v1', observer_family=family)
        need(b.get('queried_revision') == f['revision'] and b.get('queried_native_revision') == f['native_revision']
             and b.get('queried_date_raw') == f['date_raw'] and v.get('accepted') is True, 'Actual sampling source/ACK differs')
        return v
    try:
        if frame.get('active_event') is not None or frame.get('pending_character_interaction') is not None:
            frame = io.handle_modals(frame)
        fence(frame, a.expected_start_date_raw)
        off = sampling(None, 'all')
        need(all(not x['capture_enabled'] and not x['busy'] and x['retained_records'] == 0 for x in off['army_observer_research_sampling_v1'].values()), 'Initial all OFF/clear required')
        before = sample('r06-q-gate')
        prepare = module(repo/LIVE/'prepare_live_refill_add.py', 'r06_worker_prepare')
        clock = normalize_source_derived_next_daily_supply_frame_inputs_v1(before['army'].get('source_derived_next_daily_supply_frame_inputs_v1'),
                    expected_army_id=a.army_id, expected_carmy_id=a.native_carmy_id)
        need(clock is not None and clock['ready'] is True and clock.get('source_derived_full_cdate64_ready') is True
             and clock['current_date_raw_i32'] == a.expected_start_date_raw and clock['source_derived_next_date_raw_i32'] == a.expected_start_date_raw+24
             and clock['source_derived_next_calendar_day_u8'] == 0, 'Fresh native full64 month-boundary gate unavailable')
        native, packet = native_inputs(before, originals, wrapped.full_proofs[-1])
        target = prepare.select_positive_prepare_target(native, packet, army_id=a.army_id, mode='fixed_chunk0_prepare')
        need(all(x.get('native_can_replenish') is True and x.get('native_chunk_can_replenish') is True for x in target['selected_eligibility']), 'Actual Can/chunkCan required')
        expected = dict(machine_id=machine, run_id=context['run_id'], bridge_pid=binding['pid'],
                        process_creation_filetime=binding['process_creation_filetime'], date_raw=a.expected_start_date_raw)
        signal = Path(client.output)/'r06-before-observer-started.json'
        need(not signal.exists(), 'R06 signal already exists before awaiting; no stale admission')
        target_summary={k:target[k] for k in ('regi_full_id_u32','physical_slot','arrg_full_id_i32','army_full_id_i32',
                       'q_index','conditional_shared_q_i32','native_unit_position_eligible')}
        client.checkpoint('r06-before-observer-awaiting', dict(**expected, observed_at_utc=datetime.now(timezone.utc).isoformat(),
            signal_path=str(signal), producer=a.producer, conditional_positive_target=target_summary,
            q_gate_full_parent_proof=wrapped.full_proofs[-1], next_calendar=clock,
            maximum_actual_days=1, observer_started=False, maximum_wait_seconds=a.camera_timeout_seconds))
        until = time.monotonic()+a.camera_timeout_seconds
        while not signal.is_file():
            io.room(a.one_day_timeout)
            need(time.monotonic() < until, 'R06 Root admission/camera wait expired')
            time.sleep(a.poll_seconds)
        start = read(signal)
        need(all(type(start.get(k)) is type(v) and start[k] == v for k,v in expected.items()),
             'R06 actual owner admission identity differs')
        admission = checked(start['source_admission'])
        n = validate_admission(admission, expected=expected, producer=a.producer, native_tree=tree)
        frame = io.snapshot('after-camera', paused=True); fence(frame, a.expected_start_date_raw)
        on = sampling(True, 'regular_core')
        states = sampling(None, 'all')['army_observer_research_sampling_v1']
        need(states['regular_core']['capture_enabled'] is True and all(not v['capture_enabled'] for k,v in states.items() if k != 'regular_core'), 'Only scoped regular_core ON required')
        result['sampling_ON'] = on
        before = sample('r06-before')
        native, packet = native_inputs(before, originals, wrapped.full_proofs[-1])
        chosen = prepare.select_positive_prepare_target(native, packet, army_id=a.army_id, mode='fixed_chunk0_prepare')
        need(chosen['regi_full_id_u32'] == target['regi_full_id_u32'] and chosen['physical_slot'] == target['physical_slot'], 'Target changed during Root wait')
        inputs = Path(client.output)/'r06-worker-prepare-inputs'; inputs.mkdir()
        paths = {k:inputs/(k+'.json') for k in ('frame', 'diagnostics', 'army-packet')}
        write(paths['frame'], native, 2*1024*1024); write(paths['diagnostics'], native['diagnostics'], 2*1024*1024)
        write(paths['army-packet'], packet, 32*1024*1024)
        p = a.producer
        gate = dict(schema='xar.ck3.refill_ADD_12004.live_owner_admission.v1', machine_id=machine,
            exact_executable_sha256=context['shared_game']['exe_sha256'], episode_run_id=None, episode_projection='native_campaign',
            scene_sequence=int(context['run_id'].rsplit('R',1)[1]), scene_run_id=context['run_id'], new_live_build_and_SYSTEM_verified=True,
            next_scene_capacity_and_observer_admitted=True, source_dir=p['source_dir'], target='refill_add_hwprobe_12004', cmake_defines=FLAGS,
            observer_thread_policy='carrier_owned_target', maximum_owned_threads=n, carrier_bridge_source_epoch=p['carrier_source_epoch'],
            carrier_source_and_runtime_verified=True, carrier_bridge_module_path=p['carrier_module_path'], observer_exe=p['observer_exe'],
            source_admission_receipt_sha256=start['source_admission']['sha256'], observer_exe_sha256=p['observer_exe_sha256'],
            build_result_sha256=p['build_result']['sha256'], SYSTEM_receipt_sha256=p['SYSTEM_receipt']['sha256'])
        gate_path=inputs/'owner-admission.json'; write(gate_path,gate)
        prepared=Path(client.output)/'r06-worker-prepared'
        oldread=prepare_inputs(prepare,paths,paths['army-packet']); oldargv=sys.argv
        sys.argv=['prepare','--repo',str(repo),'--frame',str(paths['frame']),'--diagnostics',str(paths['diagnostics']),
            '--army-packet',str(paths['army-packet']),'--live-build-admission',str(gate_path),'--output-root',str(prepared),
            '--army-id',str(a.army_id),'--ordered-refill-entry-mode','fixed_chunk0_prepare','--regiment',str(target['regi_full_id_u32']),
            '--slot',str(target['physical_slot']),'--timeout-ms','30000','--read-process-identity']
        try:
            with redirect_stdout(StringIO()): prepare.main()
        finally:
            prepare.read=oldread;sys.argv=oldargv
        # The canonical window_take actor already owns this standard protocol.
        # All full-query preparation and Root census work precede camera Start.
        camera_expected = {k:v for k,v in expected.items() if k != 'process_creation_filetime'}
        camera_signal = Path(client.output)/'before-action-camera-started.json'
        need(not camera_signal.exists(), 'Canonical camera signal predates R06 awaiting')
        client.checkpoint('before-action-camera-awaiting', dict(**camera_expected,
            observed_at_utc=datetime.now(timezone.utc).isoformat(), action_kind='exact-day',
            signal_path=str(camera_signal), coordination_only=True, maximum_wait_seconds=a.camera_timeout_seconds,
            terminal_result_path=str(Path(client.output)/'R06-REFILL-TERMINAL.json'),
            prepared_observer=pin(prepared/'PREPARED.actual.json'), observer_started=False, clock_action_submitted=False))
        until=time.monotonic()+a.camera_timeout_seconds
        while not camera_signal.is_file():
            io.room(a.one_day_timeout)
            need(time.monotonic()<until,'Canonical R06 camera Start absent')
            time.sleep(a.poll_seconds)
        camera_start=read(camera_signal)
        need(all(type(camera_start.get(k)) is type(v) and camera_start[k]==v for k,v in camera_expected.items())
             and camera_start.get('camera_started') is True, 'Canonical camera Start owner differs')
        camera=checked(camera_start['start_receipt'],1024*1024)
        need(camera.get('machine_id')==machine and camera.get('run_id')==context['run_id']
             and camera.get('one_ffmpeg_job') is True,'Actual single camera Start receipt required')
        checked(camera['canonical_process_ready'])
        camera_after=io.snapshot('r06-after-camera',paused=True)
        fence(camera_after,a.expected_start_date_raw)
        need(camera_after['native_revision']==before['frame']['native_revision'],'Native frame changed after prepared positive target')
        result['camera_start']=camera_start['start_receipt']
        probe=Probe(repo,prepared/'PREPARED.actual.json',Path(client.output)/'r06-worker-launch',a)
        result['prelaunch_verification']=probe.start(lambda:revalidate_before_launch(probe,start['source_admission'],
            expected=expected,producer=a.producer,native_tree=tree),
            lambda:io.claim('observer-launch-once',dict(prepared=pin(probe.path))))
        client.checkpoint('R06-WORKER-PRELAUNCH-VERIFIED',result['prelaunch_verification'])
        result['worker_READY']=probe.ready()
        original_call=io.call;io.call=guarded_call(probe,original_call,io.context)
        f=io.snapshot('r06-one-day-before',paused=True);fence(f,a.expected_start_date_raw)
        need(probe.process.poll() is None and probe.remaining()>4,'Observer window exhausted before Arm')
        io.settings['one_day_timeout_seconds']=min(a.one_day_timeout,probe.remaining()-2)
        end, day=io.exact_day(dict(frame=f));result.update(actual_days=1,clock=day,exact_day_verified=day['exact_day_verified'])
        fence(end,a.expected_start_date_raw+24)
        after=sample('r06-after',end)
        result['worker_exit']=probe.finish();need(probe.restored,'Native restore/detach unverified; Save withheld')
        proof_path=Path(client.output)/'R06-FULL-PARENT-PROOF.json';write(proof_path,wrapped.full_proofs[-1],16384)
        consumer=module(repo/LIVE/'consume_live_refill_add.py','r06_target_consumer')
        item_path=Path(client.output)/'R06-TARGET-INSTRUCTION.json';target_path=Path(client.output)/'R06-TARGET-PROOF.json'
        with redirect_stdout(StringIO()):
            consumer.main(['--raw',str(probe.raw_path),'--binding',str(prepared/'owner-binding.json'),
                '--create-target-core-proof',str(target_path),'--full-parent-proof',str(proof_path),'--output',str(item_path)])
        item=read(item_path)
        need(item.get('actual_ADD_observed') is True and item.get('same_core_invocation_join_ready') is True,'Strict target ADD/Core join unavailable')
        result.update(status='TARGET_INSTRUCTION_ADD_SAME_NATURAL_CORE_QUALIFIED',actual_ADD_observed=True,
                      target_instruction_item=pin(item_path),target_proof=pin(target_path),global_physical_closure_qualification_granted=False)
    except BaseException as error:
        result.update(status='STOPPED_ERROR_PRESERVED_NO_REPLAY',error=dict(type=type(error).__name__,message=str(error)))
    finally:
        errors=[]
        if probe is not None and probe.process is not None:
            try: result['worker_exit']=probe.finish()
            except BaseException as error: errors.append('observer: '+str(error))
        # Cleanup uses the original public queue after the finite observer window.
        if 'original_call' in locals():io.call=original_call
        cleanup=dict(errors=errors,normal_Save_verified=False,sampling_OFF_clear_verified=False)
        try:
            io.call('cleanup-pause','ck3_execute_step',dict(step='pause-map',expected_revision=None),cleanup=True)
            if io.active_clock is not None or io.unknown_clock_claim is not None:
                status=io.clock_status(cleanup=True)
                if status['state']=='armed':
                    io.call('cleanup-stop-clock','ck3_execute_step',dict(step='research-cancel-tactical-daily-sentinel-v1-generation-'+str(status['generation']),expected_revision=None),cleanup=True)
            sampling(False,'all',True);off=sampling(None,'all',True)
            cleanup['sampling_OFF_clear_verified']=all(not s['capture_enabled'] and not s['busy'] and s['retained_records']==0 for s in off['army_observer_research_sampling_v1'].values())
            need(cleanup['sampling_OFF_clear_verified'],'Actual all OFF/clear unavailable')
            require_restored_for_save(probe)
            f=io.snapshot('Save-before',paused=True,cleanup=True)
            cleanup['last_paused_frame']=f
            saved=io.call('Save-once','ck3_save_checkpoint',dict(expected_revision=f['revision']),cleanup=True)
            post=io.snapshot('Save-independent-after',paused=True,cleanup=True)
            ck=saved.get('checkpoint') or {}
            cleanup.update(Save_result=saved,Save_after=post,normal_Save_verified=ck.get('status')=='saved' and ck.get('date_raw')==f['date_raw']==post['date_raw'])
        except BaseException as error:errors.append('cleanup: '+str(error))
        final_frame=cleanup.get('Save_after') or cleanup.get('last_paused_frame') or {}
        final_raw=final_frame.get('date_raw')
        if type(final_raw) is int and final_raw>=a.expected_start_date_raw and (final_raw-a.expected_start_date_raw)%24==0:
            result.update(actual_days=(final_raw-a.expected_start_date_raw)//24,
                          actual_days_basis='independent cleanup paused endpoint; exact-day proof reported separately')
        result.update(cleanup=cleanup,modals=io.modals,full_wire_proofs=wrapped.full_proofs,
                      native_restore_verified=probe is None or not getattr(probe,'launch_claimed',False) or probe.restored)
        client.checkpoint('R06-WORKER-RESULT',result)
        client.checkpoint('R06-REFILL-TERMINAL',dict(machine_id=machine,run_id=context['run_id'],status=result['status'],
            actual_days=result['actual_days'],exact_day_verified=result['exact_day_verified'],actual_ADD_observed=result['actual_ADD_observed'],
            finaldate=final_raw,OFFclear=cleanup['sampling_OFF_clear_verified'],
            Save=cleanup['normal_Save_verified'],native_restore_verified=result['native_restore_verified'],errors=errors,full_R06_qualified=False))
    return result


def verify_case(context):
    path=Path(context['output'])/'R06-WORKER-RESULT.json'
    value=read(path,1024*1024) if path.is_file() else {}
    return dict(actual_days=value.get('actual_days',0),actual_ADD_observed=value.get('actual_ADD_observed') is True,
                full_R06_qualified=False,business_pass=False,normal_close_owned_by_shared_entry=True)
