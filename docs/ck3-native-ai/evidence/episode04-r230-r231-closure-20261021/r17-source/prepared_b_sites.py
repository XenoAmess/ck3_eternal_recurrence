"""Fresh normal-Save coldload; prepare filming before a new stationary window."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import time

import ordinary_supply_b as b
import ordinary_supply_b_a05 as a05
import recovered_b_sites as prior
from final_ordinary_save import save_once
from normal_saved_source import Counts, FilePin, file_pin, read_pin, validate_normal_source, prepare_normal, MACHINE
from site_preparation import checked_review, number, timestamp


@dataclass(frozen=True)
class Settings:
    scene: Path
    schedule: FilePin
    loss: FilePin
    evidence: FilePin | None
    close_reserve: int
    prepare_seconds: int
    hard_deadline: float
    maximum_sites: int
    second_site_reserve: int


def settings(context: Mapping[str, object]) -> Settings:
    value = b.obj(b.obj(context.get('case_inputs'), 'case inputs').get('prepared_b_sites'), 'prepared B settings')
    b.need(set(value) == {'schema', 'scene_root', 'schedule_source_pin', 'adjacent_loss_proof_pin',
        'evidence_capacity_pin', 'business_stop_reserve_seconds', 'preparation_timeout_seconds',
        'scene_hard_deadline_utc', 'maximum_sites', 'second_site_minimum_remaining_seconds'}, 'Exact prepared B settings required')
    close = b.integer(value['business_stop_reserve_seconds'], 'normal Save/GUI reserve')
    wait = b.integer(value['preparation_timeout_seconds'], 'preparation wait')
    sites = b.integer(value['maximum_sites'], 'maximum sites')
    second = b.integer(value['second_site_minimum_remaining_seconds'], 'second-site entry reserve')
    b.need(value['schema'] == 'xar.e04.prepared-b-sites.v1' and close >= 600 and 1 <= wait <= 600 and
           sites in (1, 2) and second >= 1800, 'Bounded preparation and full normal-close reserves required')
    scene = Path(b.text(value['scene_root'], 'new scene root'))
    b.need(scene.is_absolute(), 'Explicit independent scene root required')
    return Settings(scene, file_pin(value['schedule_source_pin']), file_pin(value['adjacent_loss_proof_pin']),
        file_pin(value['evidence_capacity_pin']) if value['evidence_capacity_pin'] is not None else None,
        close, wait, timestamp(value['scene_hard_deadline_utc'], 'scene hard deadline'), sites, second)


def validate_contract(context: Mapping[str, object]) -> None:
    a05.validate_contract(context)
    cfg, selected = b.settings(context), settings(context)
    source = validate_normal_source(context)
    b.need(source.counts == Counts(113, 113, 6, 1) and source.actor == 31254 and source.date_raw == 53149608 and
           cfg['actor_id'] == source.actor and cfg['army_id'] == 18 and cfg['site_province_ids'] == [2624, 2623] and
           cfg['maximum_rich_queries'] == 10 and cfg['maximum_total_days'] == 180 and cfg['prefix'] == 'r17-b-site-a01',
           'Selected finite normal-source lineage and endpoints changed')
    b.need(source.army.get('current_province_id') == 2624 and source.army.get('route_read_status') == 'complete_empty' and
           source.army.get('route_province_ids') == [], 'Normal source must already be at the first stationary site')
    read_pin(selected.loss.json())


def prepare_case(context: Mapping[str, object]) -> dict[str, object]:
    validate_contract(context)
    return prepare_normal(context)


def read_schedule(ref: FilePin, army_id: int) -> dict[str, object]:
    b.need(ref.size <= 32 * 1024 * 1024 and b.pin(ref.path) == ref.json(),
           'Exact retained schedule rich exceeds32MiB or changed bytes')
    rich = b.obj(json.loads(ref.path.read_bytes()), 'retained schedule rich')
    rows = [row for row in b.array(rich.get('army_strengths'), 'retained scheduling rows') if row.get('army_id') == army_id]
    b.need(len(rows) == 1, 'Pinned earlier Army schedule missing or duplicated')
    return rows[0]


class PreparedSites(prior.RecoveredSites):
    def __init__(self, context: Mapping[str, object], client: b.Client, machine: str) -> None:
        # The predecessor constructor contains the separate R229 recovery/98d
        # contract. Reuse its operations, not that source admission or counters.
        a05.Runner.__init__(self, context, client, machine)
        self.source = validate_normal_source(context)
        self.prepared = settings(context)
        b.need(machine == MACHINE and self.prepared.evidence is not None, 'Actual new-scene Evidence32 pin required before business')
        if self.prepared.evidence is None:
            raise ValueError('New-scene Evidence32 capacity remains pending')
        self.continuation = {'business_stop_reserve_seconds': self.prepared.close_reserve}
        self.evidence_capacity = self.prepared.evidence.json()
        self.days = self.source.counts.actual_days
        self.requested_days = self.source.counts.requested_days
        self.rich_count = self.source.counts.rich_queries
        self.moves = {2624}
        self.coldload_validated = False
        self.preparing_index: int | None = None
        self.schedule_row, self.schedule_ref = read_schedule(self.prepared.schedule, self.aid), self.prepared.schedule.json()
        self.result.update(status='NORMAL_SAVE_COLDLOAD_PENDING', same_original_client=True,
            source_run_id=self.source.source_run_id, source_normal_GUI_completed_independently=True,
            source_Save_time_GUI_fields_preserved=True, one_life_identity_proven=False,
            inherited_source_counts=self.source.counts.json(), prior_sea_loss_proof=self.prepared.loss.json(),
            old_rich_is_schedule_only=True, new_scene_rich_query_cap=4, lineage_rich_query_cap=10,
            qualified_stationary_site_count=0, media_approval=False)

    def save(self) -> None:
        inherited = self.source.counts
        self.result['counter_scope'] = 'Legacy counts are cross-run lineage; new_run_counts are this actual Game only'
        self.result['inherited_source_counts'] = inherited.json()
        self.result['new_run_counts'] = {'actual_days': self.days - inherited.actual_days,
            'requested_days': self.requested_days - inherited.requested_days,
            'rich_queries': self.rich_count - inherited.rich_queries, 'Move_submissions': len(self.moves) - inherited.moves}
        self.result['lineage_total_counts'] = {'actual_days': self.days, 'requested_days': self.requested_days,
            'rich_queries': self.rich_count, 'Move_submissions': len(self.moves)}
        b.FiniteB.save(self)

    def coldload_gate(self, frame: dict[str, object]) -> None:
        row = b.army(frame, self.aid, self.actor)
        diag = b.obj(frame.get('diagnostics'), 'fresh coldload diagnostics')
        created = b.process_birth(self.client)
        binding = b.obj(frame.get('managed_campaign_run_binding'), 'fresh managed run')
        b.need(frame.get('date_raw') == self.source.date_raw and row.get('current_province_id') == 2624 and
               row.get('route_read_status') == 'complete_empty' and row.get('route_province_ids') == [] and
               binding.get('run_id') != self.source.source_run_id and
               (b.integer(diag.get('bridge_pid'), 'fresh PID'), str(created)) !=
                   (self.source.source_pid, self.source.source_birth), 'Fresh normal coldload does not reproduce the admitted stationary source')
        self.record('normal-save-new-coldload-gate', {'machine_id': self.machine, 'observed_at_utc': self.now(),
            'frame': frame, 'Army18': row, 'actual_new_created': str(created),
            'source_normal_closure': self.source.provenance, 'no_day_Move_or_speed_before_gate': True})
        self.coldload_validated = True

    def tail_reserve(self) -> int:
        return (self.prepared.close_reserve + b.integer(self.cfg['camera_wait_seconds'], 'camera Start wait') +
                b.integer(self.cfg['pre_readable_seconds'], 'pre-state hold') +
                b.integer(self.cfg['one_day_timeout'], 'original day timeout') +
                b.integer(self.cfg['post_readable_seconds'], 'post-state hold'))

    def preparation_gate(self, frame: dict[str, object], site: int) -> dict[str, object]:
        tail = self.tail_reserve()
        report = b.obj(self.client.guard(tail), 'actual original held report')
        hold = number(report.get('hold_until_utc_estimated'), 'actual original hold deadline')
        process = b.obj(getattr(self.client, '_process', None), 'original retained process')
        legacy_created = number(process.get('create_time'), 'actual retained legacy created')
        birth = str(b.process_birth(self.client))
        live = self.client.output.parent.resolve()
        binding = b.obj(frame.get('managed_campaign_run_binding'), 'actual prepared frame binding')
        b.need(live.name == binding.get('run_id') and self.prepared.scene.resolve() ==
               Path(b.text(binding.get('state_dir'), 'actual state root')).resolve().parent,
               'Prepared scene is not the actual retained Game')
        suffix = str(site + 1).zfill(2)
        config = self.prepared.scene / ('camera-planning-a01/b-site' + suffix + '-a01-input.actual-a01.json')
        reviews = [self.prepared.scene / ('camera-frame-site' + suffix + '-a0' + str(attempt) + '/ROOT-REVIEW.actual.json')
                   for attempt in (1, 2, 3)]
        end = min(time.time() + self.prepared.prepare_seconds, hold - tail, self.prepared.hard_deadline - tail)
        b.need(end > time.time(), 'No bounded camera-preparation time remains before full Save/GUI tail')
        self.record('site-preparation-awaiting', {'schema': 'xar.e04.B-site-preparation-awaiting.v1',
            'machine_id': self.machine, 'observed_at_utc': self.now(), 'site_index': site,
            'actual_frame': frame, 'actual_created': birth, 'actual_hold_deadline': hold,
            'preparation_deadline_utc': datetime.fromtimestamp(end, timezone.utc).isoformat(),
            'full_post_preparation_tail_seconds': tail, 'config_path': str(config),
            'Root_review_candidate_paths': [str(path) for path in reviews],
            'camera_awaiting_created': False, 'new_rich_endpoint_consumed': False, 'Arm_submitted': False})
        ready: dict[str, object] | None = None
        rejected: set[tuple[Path, str]] = set()
        while ready is None:
            self.client.guard(tail)
            b.need(time.time() < end, 'Bounded camera preparation expired; no rich/claim/Start/Arm consumed')
            if config.is_file():
                for review in reviews:
                    if not review.is_file():
                        continue
                    try:
                        ready = checked_review(config_path=config, review_path=review, scene=self.prepared.scene,
                            live=live, prefix=self.prefix, site=site, frame=frame,
                            retained_create_time=legacy_created, now=time.time())
                        break
                    except (ValueError, KeyError, OSError) as error:
                        diagnostic = (review, type(error).__name__ + ': ' + str(error))
                        if diagnostic not in rejected:
                            rejected.add(diagnostic)
                            self.record('preparation-review-not-ready', {'path': str(review), 'error': diagnostic[1],
                                'new_rich_or_Arm_consumed': False, 'original_images_or_review_modified': False})
            if ready is None:
                time.sleep(min(.25, max(.01, end - time.time())))
        self.client.guard(tail)
        b.need(time.time() < end, 'Prepared artifacts arrived after their bounded gate')
        self.record('site-preparation-ready', {**ready, 'actual_created': birth,
            'actual_hold_deadline': hold, 'full_tail_seconds_preserved': tail})
        fresh = self.drain(a05.Runner.snapshot(self, 'site-preparation-independent-after', frame))
        army = b.army(fresh, self.aid, self.actor)
        b.need(fresh.get('date_raw') == frame.get('date_raw') and fresh.get('speed') == 5 and
               army.get('current_province_id') == b.army(frame, self.aid, self.actor).get('current_province_id') and
               army.get('route_read_status') == 'complete_empty' and army.get('route_province_ids') == [],
               'Prepared camera UI changed the actual paused day/speed/stationary site')
        self.client.guard(tail)
        return fresh

    def snapshot(self, label: str, previous: Mapping[str, object] | None = None) -> dict[str, object]:
        frame = a05.Runner.snapshot(self, label, previous)
        if label == 'site-exact-window-before':
            if frame.get('speed') != 5:
                ack = self.call('site-speed-five-once', 'ck3_execute_step',
                    {'step': 'set-speed-5', 'expected_revision': frame['revision']})
                fresh = self.drain(a05.Runner.snapshot(self, 'site-speed-five-independent-after', frame))
                b.need(ack.get('accepted') is True and fresh.get('speed') == 5 and
                       fresh.get('date_raw') == frame.get('date_raw'), 'Actual legal speed5 was not independently observed at the same paused day')
                self.record('actual-site-speed-bridge', {'before': frame, 'ack': ack, 'after': fresh,
                    'old_rich_revision_not_relabelled': True})
                frame = fresh
            b.need(self.preparing_index is not None, 'Actual site index not set before preparation')
            if self.preparing_index is None:
                raise ValueError('Missing current site')
            frame = self.preparation_gate(frame, self.preparing_index)
        return frame

    def site(self, frame: dict[str, object], index: int, province: int) -> dict[str, object]:
        self.preparing_index = index
        try:
            return b.FiniteB.site(self, frame, index, province)
        finally:
            self.preparing_index = None

    def run(self) -> dict[str, object]:
        frame = self.snapshot('normal-save-fresh-coldload')
        self.coldload_gate(frame)
        frame = self.drain(frame)
        features = self.call('new-loaded-features', 'ck3_query_loaded_feature_manifest_v1', {'expected_revision': frame['revision']})
        b.need(features.get('scope') == 'exact-loaded-feature-manifest' and features.get('loaded_feature_manifest_ready') is True,
               'Actual new loaded-feature inventory unavailable')
        self.loaded_features = {'source': self.record('new-loaded-feature-inventory', features), 'pointer': '/loaded_feature_manifest'}
        helper = self.client.output / (self.prefix + '-actual-prepared-helper.py')
        with helper.open('xb') as stream:
            stream.write(Path(__file__).read_bytes())
        self.helper_ref, self.actual_helper_updated = b.pin(helper, self.client.output), True
        for index, province in enumerate((2624, 2623)):
            if index:
                if self.prepared.maximum_sites == 1:
                    self.result['second_site_deferred_reason'] = 'One-site scene selected'
                    break
                try:
                    self.client.guard(self.prepared.second_site_reserve)
                    b.need(time.time() + self.prepared.second_site_reserve < self.prepared.hard_deadline,
                           'Scene deadline lacks full optional second-site room')
                except ValueError as error:
                    self.result['second_site_deferred_reason'] = str(error)
                    break
                frame = self.move(frame, province)
            frame = self.site(frame, index, province)
            observations = self.result['site_observations']
            b.need(isinstance(observations, list), 'Original site observations changed')
            if not isinstance(observations, list) or len(observations) != index + 1:
                self.result['qualified_stationary_site_count'] = len(observations) if isinstance(observations, list) else 0
                self.save()
                return self.result
        observations = self.result['site_observations']
        b.need(isinstance(observations, list), 'Original site observations changed')
        count = len(observations) if isinstance(observations, list) else 0
        self.result.update(status='TWO_ACTUAL_STATIONARY_SITES' if count == 2 else 'ONE_SITE_QUALIFIED_SECOND_DEFERRED',
            qualified_stationary_site_count=count, formal_B_site_qualified=count == 2,
            scope='Actual original stationary consumers only; clip/media review separate; ABC0')
        self.save()
        return self.result


def run_case(context: Mapping[str, object], client: b.Client) -> dict[str, object]:
    from ck3_live_run_id import current_machine_id
    validate_contract(context)
    client.retain_process()
    runner = PreparedSites(context, client, current_machine_id())
    try:
        return runner.run()
    except BaseException as error:
        runner.result.update(status='PREPARED_SITE_FAILURE_PRESERVED_NO_REPLAY', error=type(error).__name__ + ': ' + str(error))
        runner.save()
        raise
    finally:
        try:
            if not runner.coldload_validated:
                raise ValueError('New coldload gate failed; no business Save submitted')
            runner.result['final_ordinary_Save'] = save_once(client, runner.prefix, runner.actor)
        except BaseException as error:
            runner.result['final_ordinary_Save_error'] = type(error).__name__ + ': ' + str(error)
        runner.save()
        client.checkpoint('r17-normal-GUI-owner-handoff', {'machine_id': runner.machine,
            'observed_at_utc': runner.now(), 'business_status': runner.result.get('status'),
            'normal_GUI_completed': False, 'next_owner_action': 'Shared public normal_close; real GUI/native/OS/host waits required'})


def verify_case(context: Mapping[str, object]) -> dict[str, object]:
    return b.verify_case(context)
