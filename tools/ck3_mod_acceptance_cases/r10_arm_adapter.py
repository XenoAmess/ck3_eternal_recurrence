"""Public R10 staged arms; same original CaseClient for the complete scene.

Root issues stage commands through existing root_checkpoint, not a new SDK or
host. This executes existing state machines and preserves their real failures.
It never certifies an arm, causal ledger, movie or the joint comparison.
"""
from pathlib import Path
from copy import deepcopy
from types import SimpleNamespace
import json

from . import r10_prepare_adapter as normal
from .r10_common_arm import CommonArmIO


def validate_contract(context):
    normal.need(context['case_contract'].get('schema') == 'xar.e04.r10-common-arm-case.v1', 'Common arm case contract differs')
    if not context.get('case_inputs'): return
    arm = context['case_inputs']['arm']
    normal.need(arm.get('label') in ('A', 'B', 'C'), 'Explicit independent arm label required')
    for key in ('plan', 'capacity_admission'):
        normal.need(type(arm.get(key)) is dict and {'path','bytes','sha256'} <= set(arm[key]), 'Exact arm ' + key + ' pin required')
    for key in ('max_runtime_total_bytes', 'max_evidence_file_bytes', 'one_day_timeout_seconds', 'maximum_modal_choices', 'maximum_stages'):
        normal.need(type(arm.get(key)) is int and arm[key] > 0, 'Explicit bounded arm ' + key + ' required')
    normal.need(type(arm.get('poll_interval_seconds')) in (float, int) and 0 < arm['poll_interval_seconds'] <= 2,
                'Explicit bounded polling interval required')


def prepare_case(context):
    validate_contract(context)
    # Reuse the exact ordinary source/profile preparation as a library. This
    # does not alter the original frozen arm inputs kept by the public entry.
    base = {**context, 'case_contract': {'schema': 'xar.e04.r10-common-preparation.v1'},
            'case_inputs': {**context['case_inputs'], 'phase': 'readiness'}}
    result = normal.prepare_case(base)
    result.update(formal_arm_executor_connected=True, formal_arm_label=context['case_inputs']['arm']['label'],
                  formal_arm_qualified=False, business_pass=False)
    return result


class Stages:
    def __init__(self, io):
        self.io = io; self.state = None; self.days = []; self.observations = []; self.first_arrival = None
        self.A = normal.importlib.import_module('strategy_a')
        self.C = normal.module(io.base / 'strategy_c/strategy_c.py', 'r10_common_C_state')
        self.CH = normal.module(io.base / 'strategy_c/common_horizon.py', 'r10_common_C_horizon')
        self.CN = normal.module(io.base / 'strategy_c/strategy_c_next_decision.py', 'r10_common_C_next')
        self.B = None
        if io.label == 'B':
            next_b = normal.module(io.base / 'comparison/strategy_b_next.py', 'r10_common_B_next')
            growth = normal.module(io.base / 'comparison/strategy_b_site_growth.py', 'r10_common_B_sites')
            qualified = growth.qualify_plan_sites(io.plan, io.e, next_b.b)
            io.client.checkpoint('r10-B-two-sites-qualified', qualified)
            self.B_module = normal.module(io.base / 'comparison/strategy_b_stages.py', 'r10_common_B_stages')
            self.B_next = next_b

    def save(self, name, value):
        return self.io.r.write_new(self.io.attempt / (name + '.actual.json'), {**self.io.meta,
            'state': deepcopy(value), 'formal_arm_qualified': False, 'research_card_closed': False})

    def endpoint(self, name):
        return self.io.endpoint(name)

    def C_observation(self, ep, clock=None):
        obs = self.C.read_observation(self.io.plan, self.io.runtime, ep, self.io.e)
        if clock is not None: obs['clock'] = clock
        return obs

    def baseline(self):
        io = self.io
        normal.need(self.state is None, 'Cold baseline already consumed; never reset arm')
        ep = self.endpoint('cold-start')
        normal.need(ep['day'] == 0, 'Actual independent cold frame is not common T0')
        cold = io.c.endpoint(ep, io.plan, io.e, io.runtime)
        normal.need(cold == io.c.check_plan(io.plan, io.e), 'Actual independent cold observables differ from common S0')
        self.cold = ep; self.observations = [ep]
        if io.label == 'A':
            _, preview = io.preview(ep, io.plan['goal_province_id'])
            self.state = self.A.admit(io.plan, io.runtime, io.plan['normal_save']['sha256'], ep, preview, io.e)
        elif io.label == 'C':
            self.state = self.C.start(io.plan, self.C_observation(ep))
        else:
            # Initial admission is not a fabricated completed ARM/disposition.
            cold_input = {'schema': 'xar.e04.r10.cold-arm-input.v1', 'label': 'B', 'runtime': io.runtime,
                'loaded_save_sha256': io.plan['normal_save']['sha256'], 'cold_start': ep}
            self.B = self.B_module.BStages(io.r, io, self.B_next, io.plan,
                plan_pin=io.settings['plan'], evidence=io.e, s0_arm=cold_input)
            self.B.run('baseline')
            self.state = self.B.state
        return self.save('baseline', self.state)

    def move(self, *, post=False):
        io = self.io
        normal.need(self.state is not None, 'Actual cold baseline required')
        key = 'whole-move-' + (str(self.state.get('target_index', 0)) if io.label == 'C' else 'A')
        if post:
            original = io.r.load(io.case / (key + '.submission.actual.json'), io.packet_limit)
            normal.need(original['row'].get('is_error') is False and original['row'].get('body', {}).get('accepted') is True,
                        'Original Move rejected/unknown; never replay')
            ep = self.endpoint('move-post')
            self.state = (self.A.observe_move(self.state, ep, io.e) if io.label == 'A'
                          else self.C.observe(io.plan, self.state, self.C_observation(ep)))
            self.observations.append(ep)
            return self.save('move-post', self.state)
        ep = self.endpoint('move-before')
        if io.label == 'A':
            normal.need(self.state['move_postcondition'] is None and not self.state['days'], 'A initial Move already consumed')
            proposed = self.state['proposed_call']
            # Existing A consumer requires the fresh preview equal its frozen
            # baseline; revalidate this immediate snapshot before submission.
            _, preview = io.preview(ep, io.plan['goal_province_id'])
            route = self.A._preview(preview, ep, io.plan, io.e, io.runtime)
            normal.need(route == self.state['route'], 'Immediate A native preview differs from frozen direct route')
            frame = io.c.frame(io.e.json(ep['snapshot']), io.runtime)
            proposed = {'tool': proposed['tool'], 'arguments': {**proposed['arguments'], 'expected_revision': frame['revision']}}
        else:
            target = self.C.targets(io.plan)[self.state['target_index']]
            preview, _ = io.preview(ep, target)
            new, proposal = self.C.propose_move(io.plan, self.state, self.C_observation(ep), preview)
            proposed = {'tool': proposal['tool'], 'arguments': {k: proposal[k]
                for k in ('army_id', 'target_province_id', 'expected_revision')}}
            self.state = new
        io.claim(key, {'proposed_call': proposed, 'before': ep, 'state_before_submit': deepcopy(self.state)})
        row, refs = io.request('whole-move-once', proposed['tool'], proposed['arguments'])
        return io.r.write_new(io.case / (key + '.submission.actual.json'), {**io.meta, 'row': row, 'refs': refs,
            'actual_route_postcondition': False, 'ACK_is_arrival': False})

    def advance(self):
        io = self.io
        normal.need(self.state is not None, 'Actual baseline required')
        before = self.endpoint('day-before')
        if io.label == 'A':
            normal.need(before['day'] == len(self.state['days']), 'A day sequence differs; never replay')
        else:
            normal.need(before['day'] == self.state['last_day'], 'C day sequence differs; never replay')
            normal.need(self.state['phase'] in ('marching', 'arrived'), 'C waypoint requires one actual next Move before another day')
            if self.state['phase'] == 'arrived': self.CH.read_common_horizon_endpoint(io.plan, self.state, self.C_observation(before), adapter=self.CN)
        _, clock_ref = io.exact_day(before)
        ep = self.endpoint('day-after')
        clock = io.c.body(io.r.load(clock_ref))['clock']
        row = {'day': ep['day'], 'clock_source': io.relative(normal.pin(clock_ref)),
            'paused_snapshot': ep['snapshot'], 'strategy_army_ids': ep['strategy_army_ids']}
        if io.label == 'A':
            self.state = self.A.update(self.state, row, ep, io.e)
        else:
            obs = self.C_observation(ep, clock)
            previous = self.state
            self.state = (self.CH.observe_common_horizon(io.plan, previous, obs, adapter=self.CN)
                if previous['phase'] == 'arrived' else self.C.observe(io.plan, previous, obs))
            if previous['phase'] == 'marching' and self.state['phase'] == 'arrived' and io.plan['follow_after_arrival_to_day90']:
                self.state = self.CH.bind_first_arrival(io.plan, previous, self.state, obs, adapter=self.CN)
        self.days.append(row); self.observations.append(ep)
        return self.save('day-' + str(ep['day']).zfill(3), self.state)

    def run(self, command):
        io = self.io
        stage = command['stage']
        if stage == 'baseline': return self.baseline()
        normal.need(self.state is not None, 'Baseline stage required before continuation')
        if io.label != 'B':
            if stage == 'Move-once': return self.move()
            if stage == 'Move-post': return self.move(post=True)
            normal.need(stage in ('advance', 'advance-common-horizon'), 'Unknown existing whole-arm stage')
            return self.advance()
        io.a.move_army_id = command.get('army_id')
        io.a.day_start_raw = command.get('day_start_raw')
        io.a.days = 1
        normal_stage = io.base / 'comparison/strategy_b_normal_stages.py'
        common_horizon = io.base / 'comparison/strategy_b_common_horizon.py'
        io.a.normal_stages = normal_stage; io.a.normal_stages_sha256 = normal.pin(normal_stage)['sha256']
        io.a.common_horizon = common_horizon; io.a.common_horizon_sha256 = normal.pin(common_horizon)['sha256']
        arrival = command.get('arrival_arm')
        io.a.arrival_arm = Path(arrival['path']) if arrival else None
        io.a.arrival_arm_sha256 = arrival['sha256'] if arrival else None
        result = self.B.run(stage)
        self.state = self.B.state
        return result


def _run_case_steps(context, client, io):
    stages = Stages(io)
    results = []
    # The explicit Root stage mailbox is owned by this original run and hold.
    # It is operational coordination, not human media review or a new approval.
    for number in range(io.settings['maximum_stages']):
        io.guard()
        name = 'r10-' + io.label + '-stage-' + str(number).zfill(4)
        command = io.client.root_checkpoint(name, {
            'schema': 'xar.e04.r10-common-stage-request.v1', 'machine_id': io.machine,
            'label': io.label, 'state': deepcopy(stages.state), 'previous_results': results[-1:],
            'action': 'Root provides one existing strategy stage, or finish; no SDK/session creation',
            'formal_arm_or_media_approval_inferred': False}, reserve=300)
        normal.need(command.get('machine_id') == io.machine and command.get('label') == io.label,
                    'Actual Root stage command crossed machine/arm')
        if command.get('stage') == 'finish':
            result = {'machine_id': io.machine, 'label': io.label, 'actual_public_run_id': io.run.name,
                'stage_results': results, 'state': stages.state, 'actual_day_records': stages.days,
                'formal_arm_qualified': False, 'business_pass': False, 'joint_ABC_completed': False,
                'scope': 'Actual staged operations only. Original causal ledgers/complete policy trace/joint comparison remain separate.'}
            return result
        io.a.stage = command['stage']; io.a.attempt = 'arm-' + io.label.lower() + '-' + str(number).zfill(4)
        io.attempt = io.case / io.a.attempt; io.attempt.mkdir(exist_ok=False)
        result = stages.run(command)
        result = normal.pin(result) if isinstance(result, (Path, str)) else result
        results.append({'stage': command['stage'], 'result': result})
        io.client.checkpoint(name + '-result', results[-1])
    raise ValueError('Original bounded stage count exhausted; retain actual state and normally close')


def run_case(context, client):
    validate_contract(context)
    io = CommonArmIO(context, client)
    primary = None
    try:
        result = _run_case_steps(context, client, io)
    except BaseException as error:
        primary = error
        raise
    finally:
        try:
            cleanup = io.finish_once()
        except BaseException as error:
            io.client.checkpoint('r10-common-arm-cleanup-failure-preserved', {
                'machine_id': io.machine, 'error': type(error).__name__ + ': ' + str(error),
                'primary_error': str(primary) if primary else None,
                'normal_Save_attempted': io.normal_save_attempted, 'unknown_Save_replayed': False})
            if primary is None: raise
    result['terminal_cleanup'] = cleanup
    io.client.checkpoint('r10-common-arm-stage-result', result)
    return result


def verify_case(context):
    path = Path(context['output']) / 'r10-common-arm-stage-result.json'
    result = json.loads(path.read_bytes()) if path.is_file() else {}
    return {'machine_id': result.get('machine_id', 'unknown'), 'actual_staged_result_available': bool(result),
        'case_contract_qualified': False, 'gui_contract_qualified': False,
        'business_pass': False, 'joint_ABC_completed': False,
        'reason': 'Staged execution does not automatically qualify original physical/payment ledgers or final comparison'}
