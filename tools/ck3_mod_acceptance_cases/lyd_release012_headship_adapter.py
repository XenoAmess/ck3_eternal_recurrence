"""Original Confucian headship first; all production options use CaseClient once."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import time
from types import FunctionType, SimpleNamespace

from ck3_mod_acceptance_cases import lyd_release012_keypaths_adapter as keypaths

CASE = 'release012-headship-first'
RESULT = 'lyd-headship-first-result.json'
ASSEMBLY = 'ck3_query_confucian_assembly_predicates_v1'
# Leave time for the operator's normal GUI Quit, host/native cleanup, screen
# release, display restoration, and finite storage settlement before expiry.
QUIT_RESERVE = 1800
OPTION_LIMIT = 64


def require(value, message):
    if not value:
        raise ValueError(message)


def checked(ref):
    raw = Path(ref['path']).read_bytes()
    require(len(raw) == ref['bytes'] and hashlib.sha256(raw).hexdigest() == ref['sha256'],
            'Reviewed source/admission bytes changed')
    return raw


def load_base():
    """Reuse current repository primitives without changing their shared globals."""
    namespace = dict(vars(keypaths))
    namespace.update(CASE=CASE, RESULT=RESULT)
    original_bundle = keypaths.native_head_bundle

    def compact_bundle(client, initial, name):
        value = original_bundle(client, initial, name)
        # The original query owns complete G2 evidence; ROOT needs the roster.
        data = value['assembly']
        value['assembly'] = roster(data, initial['actor'], data['faith_id'])
        value['assembly']['full_query_evidence_owner'] = 'original public CaseClient query'
        return value

    namespace['native_head_bundle'] = compact_bundle
    for name in ('prepare_case', 'review_cell', 'verify_case'):
        original = getattr(keypaths, name)
        namespace[name] = FunctionType(original.__code__, namespace, original.__name__,
                                       original.__defaults__, original.__closure__)
    return SimpleNamespace(**namespace)


def storage_deadline(config):
    """Bind the new case to its explicit original admission, never renew it."""
    ref = config.get('storage_admission')
    require(type(ref) is dict, 'Current storage_admission ref3 must be late-bound')
    admission = json.loads(checked(ref))
    deadline = datetime.fromisoformat(
        admission['reservation_expires_at_utc'].replace('Z', '+00:00')).timestamp()
    require(not (Path(ref['path']).parent / 'CLOSED-RESERVATION.actual.json').exists(),
            'Original storage reservation closed')
    return deadline


def roster(data, actor, faith):
    """Actual complete G2 pools; a suggested nominee is never an accepted vote."""
    require(data.get('available') is True and data.get('predicates_complete') is True and
            data.get('played_character_id') == actor and data.get('faith_id') == faith,
            'Complete current Faith predicates absent')
    members, rites = data.get('members'), data.get('rites')
    require(type(members) is list and type(rites) is list, 'Actual Faith pools missing')
    mids = [m.get('character_id') for m in members]
    rids = [r.get('rite_id') for r in rites]
    require(all(type(i) is int and i > 0 for i in mids + rids) and
            len(mids) == len(set(mids)) and len(rids) == len(set(rids)) and
            set(mids) == set(data.get('complete_native_faith_member_ids', [])) and
            set(rids) == set(data.get('complete_native_faith_rite_ids', [])),
            'Complete native pool identities differ')
    require(all(m.get('complete') is True and m.get('alive') is True and
                m.get('faith_id') == faith and m.get('rite_id') in rids for m in members),
            'Incomplete/cross-Faith living member')
    own = [m for m in members if m['character_id'] == actor]
    require(len(own) == 1, 'Actual selected actor absent from Faith pool')
    rows = []
    for rite in rites:
        rid = rite['rite_id']
        counties = rite.get('county_title_ids')
        require(rite.get('complete') is True and type(counties) is list and
                type(rite.get('native_county_count')) is int and
                rite['native_county_count'] == len(counties) and
                len(counties) == len(set(counties)), 'Incomplete native rite county pool')
        population = [m for m in members if m['rite_id'] == rid]
        eligible = [m for m in population if m.get('adult') is True and
                    m.get('imprisoned') is False and m.get('incapable') is False and
                    type(m.get('effective_learning')) in (int, float) and
                    m['effective_learning'] >= 15]
        eligible.sort(key=lambda m: (-m['effective_learning'], m['character_id']))
        rows.append({'rite_id': rid, 'living_members': len(population),
                     'county_count': len(counties), 'dormant': not population and not counties,
                     'elector_count': len(eligible),
                     'suggested_nominee': ({k: eligible[0][k] for k in
                         ('character_id', 'rite_id', 'faith_id', 'effective_learning', 'is_ai')}
                         if eligible else None),
                     'human_member_ids': [m['character_id'] for m in population if m.get('is_ai') is False]})
    active = [r for r in rows if not r['dormant']]
    return {'predicates_complete': True, 'faith_id': faith, 'actor_id': actor,
            'played_rite_id': data.get('played_rite_id'), 'living_member_count': len(members),
            'faith_rite_count': len(rites), 'active_rite_count': len(active), 'rites': rows,
            'actual_actor': own[0], 'all_active_rites_have_qualified_nominee':
                bool(active) and all(r['suggested_nominee'] is not None for r in active),
            'mandate_or_NPC_acceptance_inferred': False}


def faith_preserved(original, current):
    return (original.get('faith_key') == current.get('faith_key') == 'confucian_faith' and
            type(original.get('faith_id')) is int and current.get('faith_id') == original['faith_id'] and
            type(original.get('faith_main_rite_id')) is int and
            current.get('faith_main_rite_id') == original['faith_main_rite_id'])


def prepared_ready(original, current, actual):
    own = actual['actual_actor']
    return (faith_preserved(original, current) and own.get('adult') is True and
            own.get('imprisoned') is False and own.get('incapable') is False and
            type(own.get('effective_learning')) in (int, float) and
            own['effective_learning'] >= 15 and
            actual['all_active_rites_have_qualified_nominee'] is True)


class BoundedClient:
    def __init__(self, client, deadline, base, initial, original):
        self.client, self.deadline, self.base = client, deadline, base
        self.initial, self.original = initial, original
        self.phase_deadline = None
        self.option_actions = 0
        self.last_readiness = None
        self.readiness_checkpoint_phases = set()
        self.requested_readiness_phases = set()

    def __getattr__(self, name):
        return getattr(self.client, name)

    def remaining(self):
        return min(self.client.remaining(), self.deadline - time.time())

    def begin_phase(self, phase):
        require(self.remaining() > QUIT_RESERVE, 'Original normal Quit reserve reached')
        cap = phase.get('maximum_review_seconds')
        self.phase_deadline = min(self.deadline, time.time() + cap) if cap else self.deadline

    def execute_plan(self, steps, name):
        count = sum(s.get('tool') == 'ck3_select_event_option' for s in steps)
        require(self.option_actions + count <= OPTION_LIMIT, '64 original production options exhausted')
        require(self.remaining() > QUIT_RESERVE, 'Original normal Quit reserve reached')
        self.option_actions += count  # consume original intent even on timeout/error
        return self.client.execute_plan(steps, name)

    def read_readiness(self, name):
        current = self.base.religion(self, self.initial, name + '-religion')
        frame, row = self.base.call(self, self.initial, name + '-assembly', ASSEMBLY)
        data = self.base.formal.observe_query(frame, row['result'], 'confucian_assembly_predicates')
        self.last_readiness = {'religion': current,
            'roster': roster(data, self.initial['actor'], self.original['faith_id'])}
        return self.last_readiness

    def root_checkpoint(self, name, request, reserve=QUIT_RESERVE):
        remaining = self.remaining()
        require(remaining > QUIT_RESERVE, 'Original normal Quit reserve reached')
        refresh = (request['phase'] in {'baseline', 'preparation'} and
                   (request['phase'] not in self.readiness_checkpoint_phases or
                    request['phase'] in self.requested_readiness_phases))
        if refresh:
            self.read_readiness(name + '-readiness')
            self.readiness_checkpoint_phases.add(request['phase'])
            self.requested_readiness_phases.discard(request['phase'])
        wait = min(remaining - QUIT_RESERVE, self.phase_deadline - time.time())
        require(wait > 0, 'Fixed phase review deadline reached; normal Quit remains reserved')
        payload = {**request, 'actual_readiness': self.last_readiness,
                   'actual_readiness_fresh_for_this_checkpoint': refresh,
                   'actual_readiness_scope': ('fresh_full_readiness_before_ROOT_response' if refresh else
                                              'retained_full_observation_not_current_frame'),
                   'ROOT_optional_full_readiness_request': (
                       {'status': 'observe', 'request_full_readiness': True}
                       if request['phase'] == 'preparation' else None),
                   'total_submitted_production_options': self.option_actions,
                   'maximum_production_options': OPTION_LIMIT,
                   'effective_storage_deadline_epoch': self.deadline,
                   'fixed_phase_deadline_epoch': self.phase_deadline,
                   'automatic_review_or_facts': False,
                   'ROOT_external_production_option_selection_allowed': False}
        original_reserve = max(float(reserve), self.client.remaining() - wait)
        response = self.client.root_checkpoint(name, payload, reserve=original_reserve)
        if response.get('request_full_readiness') is True:
            require(request['phase'] == 'preparation' and response.get('status') == 'observe',
                    'Full readiness request must be an explicit preparation observe')
            self.requested_readiness_phases.add(request['phase'])
        return response


def prepare_case(context):
    phases = context['case_contract']['phases']
    require([p['id'] for p in phases[:3]] == ['baseline', 'preparation', 'institution'] and
            all(p.get('required') is True for p in phases[:3]) and
            all(p.get('required') is False for p in phases[3:]), 'Headship must precede optional representatives')
    storage_deadline(context['case_contract'])
    return load_base().prepare_case(context)


def run_case(context, client):
    base = load_base()
    compiled, contract_pin = base.generic.compiled_contract(context)
    data = compiled['config']
    deadline = storage_deadline(data)
    require(data['case_id'] == CASE, 'Wrong prepared headship case')
    initial = base.binding(client.validate_frame(client.snapshot(require_event_free=False), require_event_free=False))
    original = base.religion(client, initial, 'headship-original-religion')
    bounded = BoundedClient(client, deadline, base, initial, original)
    result = {'schema': 'lyd-release012-keypaths-result-v1', 'run_id': context['run_id'], 'case': CASE,
        'assertion_contract': contract_pin, 'actual_start_binding': initial, 'original_religion': original,
        'cells': [], 'business_pass': False, 'whole_product_release_pass': False,
        'formal_B4_B5_C3_credit': False, 'all36_live_effect_credit': False, 'new_head_title_id': None}
    consumed = set()
    for phase in data['phases']:
        bounded.begin_phase(phase)
        if phase.get('decision_key'):
            try:
                base.navigate(bounded, initial, 'headship-' + phase['id'], phase['decision_key'])
            except ValueError as error:
                bounded.checkpoint('headship-' + phase['id'] + '-navigation-gap', {'error': str(error),
                    'action_replayed': False, 'business_pass': False})
        cell = base.review_cell(context, bounded, initial, phase, consumed)
        if phase['id'] in {'baseline', 'preparation'}:
            actual = bounded.read_readiness('headship-' + phase['id'] + '-final')
            cell['actual_readiness'] = actual
            cell['qualified'] = cell['qualified'] and faith_preserved(original, actual['religion'])
            if phase['id'] == 'preparation':
                cell['qualified'] = cell['qualified'] and prepared_ready(original, actual['religion'], actual['roster'])
        if phase['id'] == 'institution' and cell['qualified']:
            after = base.native_head_bundle(bounded, initial, 'headship-post-institution')
            before = cell['actual_initial_political_bundle']
            cell['actual_before_head'], cell['actual_after_head'] = before, after
            cell['qualified'] = base.head_qualified(before, after, initial['actor'], original['faith_id'])
            # Post SAVE did not exist at the earlier completion review. Require its real evidence now.
            if cell['qualified']:
                response = bounded.root_checkpoint('headship-post-SAVE-protection', {
                    'schema': 'lyd-release012-root-cell-v1', 'phase': 'institution',
                    'responses': ['complete', 'partial', 'abort'], 'actual_post_bundle': after,
                    'requirements': ['post_SAVE_complete_political_AST_heirs_laws_preserved',
                                     'same_post_checkpoint_Faith_Title_holder_four_fields_law95_qualified'],
                    'instructions': 'Read the actual new post SAVE once through the reviewed bounded helper. '
                        'Join the same checkpoint with actual native object/properties/law95. No R26 or historical world credit.'})
                require(response.get('run_id') == context['run_id'] and
                        response.get('reviewer') == bounded.operator_reviewer, 'Post SAVE review crossed ROOT/run')
                refs = response.get('evidence', [])
                require(type(refs) is list and refs, 'Actual post SAVE evidence absent')
                for ref in refs:
                    base.check_evidence(ref)
                cell['post_SAVE_review'] = response
                cell['qualified'] = response.get('status') == 'complete' and all(
                    response.get('facts', {}).get(k) is True for k in
                    ('post_SAVE_complete_political_AST_heirs_laws_preserved',
                     'same_post_checkpoint_Faith_Title_holder_four_fields_law95_qualified'))
            if cell['qualified']:
                result['new_head_title_id'] = after['title']['head_title_full_id']
        result['cells'].append(cell)
        base.write_once(Path(context['output']) / (phase['id'] + '-cell-result.json'), cell)
        if cell['status'] == 'abort' or phase.get('required') is True and not cell['qualified']:
            break
    required = [p['id'] for p in data['phases'] if p.get('required') is True]
    result['case_contract_qualified'] = all(any(c['phase'] == p and c['qualified'] for c in result['cells']) for p in required)
    result['gui_contract_qualified'] = result['case_contract_qualified']
    result['runtime_status'] = 'REPRESENTATIVE_OBSERVED' if result['case_contract_qualified'] else 'PARTIAL_OR_RED'
    result['submitted_production_options'] = bounded.option_actions
    base.write_once(Path(context['output']) / RESULT, result)
    return result


def verify_case(context):
    return load_base().verify_case(context)
