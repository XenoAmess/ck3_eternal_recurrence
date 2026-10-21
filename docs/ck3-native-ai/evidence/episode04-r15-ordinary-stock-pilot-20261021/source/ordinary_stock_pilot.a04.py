"""Finite ordinary-campaign coastal stock pilot on the original public client.

No formal A/B/C, growth-site, physical DATA, or maintenance-payment award.
The shared public entry owns normal Save/Quit and the original host lifecycle.
"""
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol
import hashlib

from ck3_mod_acceptance_cases import r10_prepare_adapter as base


class Client(Protocol):
    output: Path
    def retain_process(self) -> object: ...
    def guard(self, reserve: float = 90) -> object: ...
    def snapshot(self, allow_actor_change: bool = False,
                 require_event_free: bool = True) -> object: ...
    def advance_day(self, days: int = 1, timeout: float = 300,
                    allow_event_boundary: bool = False,
                    allow_actor_change: bool = False) -> object: ...
    def checkpoint(self, name: str, value: object) -> Path: ...
    def root_checkpoint(self, name: str, request: object, reserve: float = 90) -> object: ...


class Relay(Protocol):
    client: Client
    def request(self, identifier: str, tool: str, arguments: dict[str, object],
                timeout: float | None = None) -> object: ...


def need(value: bool, reason: str) -> None:
    if not value:
        raise ValueError(reason)


def obj(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(label + ' must be an object')
    result: dict[str, object] = {}
    for key, child in value.items():
        if not isinstance(key, str):
            raise ValueError(label + ' has a non-string key')
        result[key] = child
    return result


def integer(value: object, label: str) -> int:
    if type(value) is not int:
        raise ValueError(label + ' must retain an integer')
    return value


def rows(value: object, label: str) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise ValueError(label + ' must be an array')
    return [obj(row, label + ' row') for row in value]


def config(context: Mapping[str, object]) -> dict[str, object]:
    value = obj(obj(context['case_inputs'], 'case inputs').get('ordinary_stock_pilot'), 'pilot settings')
    need(set(value) == {'actor_id', 'origin_province_id', 'split_once_authorized',
                        'maximum_day_requests', 'one_day_timeout'}, 'Exact finite pilot settings required')
    need(integer(value['actor_id'], 'actor') == 31254 and
         integer(value['origin_province_id'], 'origin') == 2624, 'This pilot is the admitted coastal source')
    need(type(value['split_once_authorized']) is bool, 'Split authorization must be explicit bool')
    need(integer(value['maximum_day_requests'], 'day request cap') == 1, 'Pilot permits at most one day request')
    timeout = integer(value['one_day_timeout'], 'day timeout')
    need(1 <= timeout <= 300, 'Finite day timeout required')
    return value


def validate_contract(context: Mapping[str, object]) -> None:
    base.validate_contract(context)
    config(context)


def prepare_case(context: Mapping[str, object]) -> object:
    validate_contract(context)
    return base.prepare_case(context)


def unit(frame: Mapping[str, object], army_id: int) -> dict[str, object]:
    found = [row for row in rows(frame.get('player_armies'), 'player armies') if row.get('army_id') == army_id]
    need(len(found) == 1, 'Fresh public Army identity missing or ambiguous')
    return found[0]


def stationary(row: Mapping[str, object], *, actor: int, province: int | None = None) -> bool:
    return (row.get('source') == 'native' and row.get('controllable') is True and
            row.get('owner_character_id') == actor and row.get('in_combat') is False and
            row.get('retreating') is False and row.get('army_state') == 'regular' and
            row.get('route_read_status') == 'complete_empty' and row.get('route_province_ids') == [] and
            row.get('move_target_province_id') is None and
            (province is None or row.get('current_province_id') == province))


def bound(frame: Mapping[str, object], previous: Mapping[str, object] | None, actor: int) -> None:
    need(frame.get('paused') is True and frame.get('map_ready') is True, 'Actual paused MapReady frame required')
    need('episode_run_id' in frame, 'Episode presence required; explicit null is legal')
    need(obj(frame.get('played_character'), 'played character').get('character_id') == actor, 'Actual coastal actor changed')
    if previous is not None:
        first, last = obj(previous.get('diagnostics'), 'before diagnostics'), obj(frame.get('diagnostics'), 'diagnostics')
        need(all(first.get(k) == last.get(k) for k in ('bridge_pid', 'connection_generation')) and
             previous['episode_run_id'] == frame['episode_run_id'], 'Original native campaign lifetime changed')


class EventPolicyView:
    """Only the data used by the existing pure event-policy consumer."""
    def __init__(self, context: Mapping[str, object], actor: int) -> None:
        self.context = context
        self.binding: dict[str, object] = {'actor_character_id': actor}


def choose_displayed(context: Mapping[str, object], actor: int, typed: dict[str, object],
                     options: list[dict[str, object]], frame: dict[str, object]) -> tuple[dict[str, object], dict[str, object]]:
    from ck3_mod_acceptance_cases.faith_e02_pilgrimage_journey import _Journey
    value: object = _Journey.choose_event_option(EventPolicyView(context, actor), typed, options, frame, frame)
    need(isinstance(value, tuple) and len(value) == 2, 'Existing pure event policy result invalid')
    if not isinstance(value, tuple):
        raise ValueError('Existing pure event policy tuple missing')
    return obj(value[0], 'chosen native option'), obj(value[1], 'existing event policy')


class Pilot:
    def __init__(self, context: Mapping[str, object], client: Client, relay: Relay, machine: str) -> None:
        self.context, self.client, self.relay, self.machine = context, client, relay, machine
        self.cfg = config(context)
        self.actor = integer(self.cfg['actor_id'], 'actor')
        self.serial = 0
        self.used_events: set[int] = set()
        self.used_interactions: set[int] = set()
        self.result: dict[str, object] = {
            'machine_id': machine, 'observed_at_utc': datetime.now(timezone.utc).isoformat(),
            'status': 'STARTED', 'split_submissions': 0, 'day_requests': 0,
            'stock_growth_observed': False, 'formal_B_site_qualified': False,
            'formal_ABC_completed': 0, 'business_pass': False, 'research_card_closed': False,
            'R05_natural_candidates': [], 'second_site_submitted': False,
            'scope': 'Ordinary source survey/split/one natural interval; independent endpoints only'}

    def save(self) -> None:
        self.client.checkpoint('ordinary-stock-pilot-result', self.result)

    def record(self, name: str, value: object) -> None:
        self.client.checkpoint(name, value)

    def call(self, name: str, tool: str, arguments: dict[str, object]) -> dict[str, object]:
        self.client.guard(90)
        self.serial += 1
        envelope = obj(self.relay.request('stock-pilot-' + str(self.serial) + '-' + name,
                                         tool, arguments, timeout=120), 'common request envelope')
        need(envelope.get('is_error') is False, 'Original common request failed; no replay')
        return obj(envelope.get('body'), 'native result')

    def snapshot(self, name: str, previous: Mapping[str, object] | None = None) -> dict[str, object]:
        frame = obj(self.relay.client.snapshot(require_event_free=False), 'fresh snapshot')
        bound(frame, previous, self.actor)
        self.record('stock-pilot-' + name, frame)
        return frame

    def drain(self, frame: dict[str, object]) -> dict[str, object]:
        while frame.get('active_event') is not None or frame.get('pending_character_interaction') is not None:
            need(len(self.used_events) + len(self.used_interactions) < 16, 'Finite modal limit reached')
            event = frame.get('active_event')
            if event is not None:
                active = obj(event, 'active event'); identity = integer(active.get('instance_id'), 'event instance')
                need(identity > 0 and identity not in self.used_events, 'Unknown/consumed event cannot be submitted again')
                body = self.call('event-context', 'ck3_query_current_event_window_context_v1',
                                 {'event_instance_id': identity, 'expected_revision': frame['revision']})
                typed = obj(body.get('current_event_window_context'), 'typed event')
                options = rows(typed.get('options'), 'displayed event options')
                need(typed.get('schema') == 'current-event-window-context-v1' and typed.get('status') == 'available' and
                     typed.get('current_event_instance_id') == identity and typed.get('date_raw') == frame['date_raw'] and
                     typed.get('snapshot_revision') == frame['native_revision'] and
                     obj(typed.get('readiness'), 'event readiness').get('option_presentation_ready') is True and
                     bool(options) and [r.get('rendered_index') for r in options] == list(range(len(options))),
                     'Actual native displayed event order unavailable')
                fresh = self.snapshot('event-' + str(identity) + '-fresh-before-selection', frame)
                need(fresh['date_raw'] == frame['date_raw'] and
                     obj(fresh.get('active_event'), 'fresh active event').get('instance_id') == identity,
                     'Original event changed before sole selection')
                frame = fresh
                first, policy = choose_displayed(self.context, self.actor, typed, options, frame)
                need(first.get('shown') is True and first.get('enabled') is True,
                     'First displayed native event option unavailable')
                number = integer(first.get('native_option_index'), 'native option index') + 1
                capture = {'frame': frame, 'typed_context': typed, 'actual_displayed_options': options,
                           'selected_option_number': number, 'policy': policy,
                           'offline_definition_analysis_required': True}
                self.record('stock-pilot-event-' + str(identity) + '-before', capture)
                self.used_events.add(identity)
                ack = self.call('event-select-once', 'ck3_select_event_option',
                                {'event_instance_id': identity, 'option_number': number, 'expected_revision': frame['revision']})
                after = self.snapshot('event-' + str(identity) + '-after', frame)
                gone = after.get('active_event') is None or obj(after.get('active_event'), 'after event').get('instance_id') != identity
                self.record('stock-pilot-event-' + str(identity) + '-receipt', {'ack': ack, 'old_instance_gone': gone})
                need(ack.get('accepted') is True and gone, 'Event outcome unknown; no replay')
            else:
                pending = obj(frame.get('pending_character_interaction'), 'pending interaction')
                identity = integer(pending.get('instance_id'), 'interaction instance')
                need(identity > 0 and identity not in self.used_interactions, 'Unknown/consumed interaction cannot replay')
                body = self.call('interaction-context', 'ck3_query_pending_character_interaction_context_v1',
                                 {'pending_interaction_id': identity, 'expected_revision': frame['revision']})
                typed = obj(body.get('pending_character_interaction_context'), 'typed interaction')
                legality = obj(obj(typed.get('legality'), 'interaction legality').get('reject'), 'reject legality')
                routing = obj(typed.get('routing'), 'interaction routing')
                need(typed.get('schema') == 'pending-character-interaction-context-v1' and typed.get('status') == 'available' and
                     typed.get('pending_interaction_id') == identity and typed.get('date_raw') == frame['date_raw'] and
                     typed.get('snapshot_revision') == frame['native_revision'] and legality.get('allowed') is True and
                     routing.get('played_character_id') == self.actor and routing.get('auto_accept_notification') is False,
                     'Original ordinary left-reject channel unavailable')
                self.record('stock-pilot-interaction-' + str(identity) + '-before',
                            {'frame': frame, 'typed_context': typed, 'accept': False, 'offline_definition_analysis_required': True})
                fresh = self.snapshot('interaction-' + str(identity) + '-fresh-before-reply', frame)
                need(fresh['date_raw'] == frame['date_raw'] and
                     obj(fresh.get('pending_character_interaction'), 'fresh pending interaction').get('instance_id') == identity,
                     'Original interaction changed before sole reply')
                frame = fresh
                self.used_interactions.add(identity)
                ack = self.call('interaction-reject-once', 'ck3_reply_pending_character_interaction',
                                {'interaction_instance_id': identity, 'accept': False, 'expected_revision': frame['revision']})
                after = self.snapshot('interaction-' + str(identity) + '-after', frame)
                gone = after.get('pending_character_interaction') is None or obj(after.get('pending_character_interaction'), 'after interaction').get('instance_id') != identity
                self.record('stock-pilot-interaction-' + str(identity) + '-receipt', {'ack': ack, 'old_instance_gone': gone})
                need(ack.get('accepted') is False and obj(ack.get('interaction_result'), 'interaction result').get('status') == 'rejected' and gone,
                     'Interaction outcome unknown; no replay')
            frame = after
        return frame

    def strengths(self, name: str, frame: Mapping[str, object], ids: list[int], *, full: bool) -> list[dict[str, object]]:
        arguments: dict[str, object] = {'army_ids': ids, 'expected_revision': frame['revision'],
                                      'profile': 'observed_history_full_v1' if full else 'ordinary_core_v1'}
        if full:
            arguments.update(ordered_refill_entry_mode='observed_prepared', ordered_besieging_entry_mode='observed_prepared')
        body = self.call(name, 'ck3_query_army_strengths', arguments)
        need(body.get('accepted') is True and body.get('army_strengths_profile') == arguments['profile'],
             'Actual query acceptance/profile differs')
        found = rows(body.get('army_strengths') if full else body.get('armies'),
                     'full-wire Army rows' if full else 'ordinary compact Army rows')
        need(len(found) == len(ids) and {integer(r.get('army_id'), 'strength Army') for r in found} == set(ids),
             'Current exact Army query scope incomplete')
        return found

    def core_stock(self, row: Mapping[str, object]) -> dict[str, object]:
        identity = integer(row.get('army_id'), 'core Army')
        need(row.get('status') in ('available', 'unavailable'), 'Current compact Army status invalid')
        need('current_supply_raw' in row and 'current_supply_scale' in row and 'unavailable_reason' in row,
             'Actual compact nullable fields must be present')
        stock = row['current_supply_raw']
        if row['status'] == 'available':
            need(integer(row['current_supply_scale'], 'compact stock scale') == 100000, 'Actual compact stock scale differs')
            need(integer(stock, 'compact current stock') >= 0, 'Current compact stock unavailable')
        else:
            need(stock is None and row['current_supply_scale'] is None, 'Unavailable core must preserve null stock and scale')
        return {'army_id': identity, 'status': row['status'], 'stock_raw': stock,
                'scale': row['current_supply_scale'], 'unavailable_reason': row['unavailable_reason'],
                'capacity_raw': None, 'final_monthly_rate_raw': None,
                'capacity_rate_available_from_core': False}

    def stock(self, row: Mapping[str, object]) -> dict[str, object]:
        need(row.get('status') == 'available', 'Current Army strength unavailable')
        stock = integer(row.get('current_supply_raw'), 'stock')
        cap = integer(row.get('current_supply_capacity_raw'), 'stock capacity')
        rate = integer(row.get('current_supply_change_monthly_raw'), 'final monthly rate')
        need(row.get('current_supply_scale') == 100000 and row.get('current_supply_capacity_scale') == 100000 and
             row.get('current_supply_change_monthly_scale') == 100000, 'Actual supply scales differ')
        return {'army_id': integer(row.get('army_id'), 'Army'), 'stock_raw': stock, 'capacity_raw': cap,
                'final_monthly_rate_raw': rate, 'scale': 100000, 'headroom_positive_rate': 0 <= stock < cap and rate > 0}

    def run(self) -> dict[str, object]:
        frame = self.drain(self.snapshot('initial'))
        roster = rows(frame.get('player_armies'), 'player armies')
        eligible = [r for r in roster if stationary(r, actor=self.actor)]
        ids = [integer(r.get('army_id'), 'eligible Army') for r in eligible]
        self.result['eligible_armies'] = eligible
        if not ids:
            self.result['status'] = 'NO_ELIGIBLE_ARMY'; self.save(); return self.result
        core = self.strengths('initial-core-survey', frame, ids, full=False)
        survey = [self.core_stock(r) for r in core]
        self.result['initial_stock_survey'] = survey
        self.result['R05_natural_stock_candidates'] = [r for r in survey if type(r['stock_raw']) is int and
                                                       0 <= integer(r['stock_raw'], 'stock') < 1000000]
        self.result['R05_natural_candidates'] = []
        self.result['R05_rate_and_fences_status'] = 'Not supplied by ordinary_core; full observation required for any low-stock candidate'
        choices = [r for r in eligible if stationary(r, actor=self.actor, province=2624)]
        need(len(choices) == 1, 'Exactly one fresh controlled coastal Army required; old Army IDs are not authority')
        parent = integer(choices[0]['army_id'], 'fresh coastal Army')
        frame = self.drain(self.snapshot('parent-full-before', frame))
        parent_full = self.strengths('parent-full', frame, [parent], full=True)[0]
        parent_stock = self.stock(parent_full)
        self.result['parent_baseline'] = parent_stock
        chosen = parent
        if parent_stock['headroom_positive_rate'] is not True:
            if self.cfg['split_once_authorized'] is not True:
                self.result['status'] = 'FULL_OR_NONPOSITIVE_NO_SPLIT_AUTHORIZATION'; self.save(); return self.result
            before = self.drain(self.snapshot('split-before', frame))
            need(stationary(unit(before, parent), actor=self.actor, province=2624), 'Fresh split source changed')
            self.result['split_submissions'] = 1; self.save()
            ack = self.call('split-once', 'ck3_execute_step',
                            {'step': 'split-army-half-' + str(parent), 'expected_revision': before['revision']})
            self.result['split_ack'] = ack
            after = self.drain(self.snapshot('split-after', before))
            need(after['date_raw'] == before['date_raw'], 'Split changed natural date')
            old_ids = {integer(r.get('army_id'), 'before roster Army') for r in rows(before['player_armies'], 'before roster')}
            new = [r for r in rows(after['player_armies'], 'after roster') if r.get('army_id') not in old_ids]
            need(ack.get('accepted') is True and len(new) == 1 and
                 stationary(new[0], actor=self.actor, province=2624), 'Original split not independently resolved; no replay')
            chosen = integer(new[0]['army_id'], 'actual split child')
            core_after = self.strengths('split-core-independent', after, [parent, chosen], full=False)
            self.result['split_independent_core'] = [self.core_stock(r) for r in core_after]
            frame = after
        frame = self.drain(self.snapshot('chosen-baseline-before', frame))
        need(stationary(unit(frame, chosen), actor=self.actor, province=2624), 'Selected child is not stationary at origin')
        baseline = self.stock(self.strengths('chosen-full-baseline', frame, [chosen], full=True)[0])
        self.result['chosen_army_id'] = chosen; self.result['chosen_baseline'] = baseline
        if baseline['headroom_positive_rate'] is not True:
            self.result['status'] = 'NO_ACTUAL_CHILD_HEADROOM_AND_POSITIVE_RATE'; self.save(); return self.result
        before_day = self.drain(self.snapshot('day-before', frame))
        need(stationary(unit(before_day, chosen), actor=self.actor, province=2624), 'Selected Army moved before day')
        need(before_day['date_raw'] == frame['date_raw'], 'Baseline natural date changed before day')
        self.client.guard(90)
        self.result['day_requests'] = 1; self.save()
        day = obj(self.client.advance_day(1, integer(self.cfg['one_day_timeout'], 'timeout'),
                                          allow_event_boundary=True), 'original day row')
        self.record('stock-pilot-original-day', day)
        value = obj(day.get('result'), 'original day result')
        need(day.get('ok') is True and not day.get('error'), 'Original day result unknown; no replay')
        after = self.drain(self.snapshot('day-after', before_day))
        need(stationary(unit(after, chosen), actor=self.actor, province=2624), 'Army moved/combat after interval')
        elapsed = integer(after.get('date_raw'), 'after date') - integer(before_day.get('date_raw'), 'before date')
        self.result['elapsed_hours'] = elapsed
        post = self.stock(self.strengths('chosen-full-post', after, [chosen], full=True)[0])
        self.result['chosen_post'] = post
        delta = integer(post['stock_raw'], 'post stock') - integer(baseline['stock_raw'], 'baseline stock')
        self.result['stock_delta_raw'] = delta
        complete = value.get('requested_interval_complete') is True and value.get('event_boundary') is None and elapsed == 24
        self.result['stock_growth_observed'] = complete and delta > 0
        self.result['status'] = 'ONE_DAY_STOCK_GROWTH_OBSERVED' if complete and delta > 0 else 'FINITE_INTERVAL_NO_QUALIFIED_GROWTH'
        self.result['remaining'] = ['Full callback-chain/cohort qualification before awarding B site',
                                    'Fresh legal preview and bounded independent second-site observation at2619',
                                    'R05 full fences only if naturally below10 and finalrate negative']
        self.save()
        return self.result


def run_case(context: Mapping[str, object], client: Client) -> dict[str, object]:
    from ck3_live_run_id import current_machine_id
    validate_contract(context)
    client.retain_process()
    from ck3_mod_acceptance_full_army import FullArmyResultClient
    client = FullArmyResultClient(client, prefix='r15-stock-hotfix-a01')
    machine = current_machine_id()
    relay: Relay = base.CommonRequestRelay(context, client, machine=machine)
    pilot = Pilot(context, client, relay, machine)
    source = Path(__file__).resolve(); raw = source.read_bytes()
    client.checkpoint('stock-pilot-actual-adapter-source', {'machine_id': machine,
        'observed_at_utc': datetime.now(timezone.utc).isoformat(), 'path': str(source),
        'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
        'base_adapter_path': str(Path(base.__file__).resolve())})
    try:
        result = pilot.run()
    except BaseException as error:
        pilot.result['status'] = 'FAILED_PRESERVED_NO_REPLAY'
        pilot.result['error'] = type(error).__name__ + ': ' + str(error)
        pilot.save()
        raise
    client.checkpoint('r10-common-preparation-result', result)
    client.root_checkpoint('r15-pilot-handoff', {
        'scope': 'Finite pilot complete; retain same paused native campaign for same-owner continuation or normal close',
        'pilot_result': result}, reserve=90)
    return result


def verify_case(context: Mapping[str, object]) -> dict[str, object]:
    result = obj(base.verify_case(context), 'shared R10 verifier')
    result.update(formal_B_site_qualified=False, formal_ABC_completed=0, business_pass=False,
                  research_card_closed=False, scope='Finite ordinary stock pilot; shared normal closure remains owner-managed')
    return result
