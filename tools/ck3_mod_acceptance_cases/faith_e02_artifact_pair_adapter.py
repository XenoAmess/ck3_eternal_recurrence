"""Two actual managed C2 scenes; one equip or one enshrine, never replay unknown."""
from __future__ import annotations
from ck3_mod_acceptance_saved_profile_v2 import materialize_saved_profile_v2
from datetime import datetime, timezone
import importlib
import subprocess
from pathlib import Path
from typing import Protocol, runtime_checkable
import faith_e02_artifact_pair_queue as Q
from faith_e02_artifact_pair_contract import (ARTIFACT, DATE, PLAYER, RECIPIENTS, SAVE_BYTES, SAVE_SHA, SITE,
    CasePort, Contract, Frame, Object, Pin, array, boolean, digest, field, frame, integer, item,
    json_value, knight, mapping, object_value, parse_contract, parse_pin, pin, read, require, sha, text,
    wallet, write_once)

RESULT = 'artifact-pair-arm-result.json'
FLAGS = {'opt_in_player_artifact_personal_use_actions': True, 'opt_in_player_inventory_window_open': True,
    'opt_in_player_inventory_window_close': True, 'opt_in_holy_site_relic_actions': True,
    'opt_in_holy_site_creation_ui': True, 'opt_in_holy_site_creation_create_once': False,
    'opt_in_player_rite_creation_actions': False, 'opt_in_player_pilgrimage_execution': False}


@runtime_checkable
class Preparation(Protocol):
    def finish_product_profile(self, context: object, profile: object, *, provenance: Object) -> object: ...


@runtime_checkable
class MachineReader(Protocol):
    def current_machine_id(self) -> str: ...


def validate_contract(context: object) -> Contract:
    c = parse_contract(field(context, 'case_contract'))
    spec = mapping(field(context, 'case_spec'), 'selected public case')
    require(field(context, 'case') == 'faith-engine-e02-artifact-pair-' + c.arm + '-v1' and
            field(context, 'product') == 'faith-engine', 'Selected public product/case differs')
    for key, expected in FLAGS.items():
        require(field(spec, key) is expected, 'Explicit independent opt-in/default false required: ' + key)
    for key, expected_tools in [('required_mcp_tools', Q.REQUIRED), ('opt_in_read_only_mcp_tools', Q.OPTIN_READONLY)]:
        tools = [text(x, 'declared tool') for x in array(field(spec, key), key)]
        require(len(tools) == len(set(tools)) and set(tools) == expected_tools, 'Exact finite tool declaration: ' + key)
    require(field(spec, 'whole_product_acceptance_credit') is False and field(spec, 'business_contract_applicable') is False,
            'Neither arm qualifies whole film or product release')
    budgets = mapping(field(spec, 'budgets'), 'public hold budget')
    require(integer(field(budgets, 'hold_seconds'), 'hold seconds', 2400, 14400) >= 2400 and
            integer(field(budgets, 'timeout'), 'outer timeout', 3000, 18000) >= 3000,
            'Finite review/once/post/normal Quit time required')
    require(c.pair_root.is_absolute() and not c.pair_root.is_symlink(), 'Stable absolute evidence root required')
    own_paths = {Path(__file__).resolve(), Path(Q.__file__).resolve(), Path(parse_contract.__code__.co_filename).resolve()}
    require({Path(x['path']).resolve() for x in c.dependencies} == own_paths, 'Exactly the three selected caller sources must be pinned')
    return c


def prepare_case(context: object) -> Object:
    c = validate_contract(context)
    reader = importlib.import_module('ck3_live_run_id')
    require(isinstance(reader, MachineReader), 'Canonical machine reader API unavailable')
    require(reader.current_machine_id() == c.machine_id, 'Executing machine differs')
    inputs = mapping(field(context, 'case_inputs'), 'prepared input bindings')
    admission = parse_pin(field(inputs, 'storage_admission'))
    grant = read(Path(admission['path']))
    expiry = datetime.fromisoformat(text(field(grant, 'expires_at_utc'), 'grant expiry').replace('Z', '+00:00'))
    require(field(grant, 'machine_id') == c.machine_id and field(grant, 'active') is True and
            expiry.tzinfo is not None and datetime.now(timezone.utc) < expiry, 'Fresh authorized scene admission required')
    saved = object_value(field(context, 'saved_campaign'))
    require(saved == field(field(context, 'case_contract'), 'saved_input'), 'Prepared mother differs from declared C2')
    mother = Path(c.save_path)
    require(mother.is_absolute() and mother.is_file() and not mother.is_symlink() and mother.suffix.lower() == '.ck3',
            'Original immutable C2 mother required')
    before = mother.stat()
    actual = pin(mother)
    after = mother.stat()
    require(actual['bytes'] == SAVE_BYTES and actual['sha256'] == SAVE_SHA and
            (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), 'C2 original bytes changed')
    module = importlib.import_module('ck3_mod_acceptance_prepare')
    require(isinstance(module, Preparation), 'Shared public preparation API unavailable')
    profile = materialize_saved_profile_v2(context, None, field(inputs, 'configuration'), source_role=None)
    profile = module.finish_product_profile(context, profile, provenance={
        'machine_id': c.machine_id, 'kind': 'C2-artifact-paired-independent-' + c.arm,
        'saved_input': saved, 'storage_admission': json_value(admission), 'world_actions_performed': False,
        'preparation_mod_mounted': False, 'actual_restore_observed': False})
    p = mapping(profile, 'shared profile')
    return {'startup': {'mode': 'saved_campaign', 'state_dir': json_value(field(p, 'state_dir')),
                       'saved_campaign': {**saved, 'product_inventory': json_value(field(field(p, 'product_inventory'), 'path'))}},
            'profile': json_value(profile), 'initial_plan': json_value(field(field(context, 'case_spec'), 'initial_plan')),
            'runtime_status': 'NOT_RUN', 'business_pass': False, 'product_release_pass': False}


def check_history(c: Contract) -> str:
    pending = read(Path(c.prior_pending['path']))
    intent = mapping(field(pending, 'intent'), 'retained original SDK intent')
    old = read(Path(c.prior_result['path']))
    old_run = text(field(old, 'run_id'), 'original actual R0007')
    require(field(pending, 'machine_id') == c.machine_id == field(old, 'machine_id') and
            field(field(intent, 'scope'), 'managed_run_id') == old_run and
            field(intent, 'operation') == 'enshrine_relic' and integer(field(intent, 'subject_id'), 'old site') == SITE and
            integer(field(intent, 'relic_artifact_id'), 'old artifact') == ARTIFACT,
            'The retained old 267 intent must not be deleted, rotated or disguised')
    require(field(old, 'enshrine_owner_slot_inventory_observed') is True and field(old, 'unknown_original_action') is False,
            'Previous action unknown: no new experiment/replay authorization may be inferred')
    settle(field(old, 'enshrine_action_after'), field(old, 'enshrine_site_after'),
           field(old, 'enshrine_permissions_after'), expected_slot=1)
    return old_run


def settle(action: object, site: object, permissions: object, *, expected_slot: int) -> Object:
    for value in (action, site, permissions):
        require(field(value, 'available') is True and field(value, 'read_only') is True and
                integer(field(value, 'played_character_id'), 'post actor') == PLAYER and
                integer(field(value, 'date_raw'), 'post date') == DATE and
                integer(field(value, 'requested_holy_site_id'), 'post site') == SITE, 'Independent current owner/site/permission unavailable')
    own = mapping(field(action, 'artifact_ownership'), 'actual resolved artifact owner')
    require(field(own, 'available') is True and field(own, 'object_resolved') is True and
            integer(field(own, 'artifact_id'), 'post artifact') == ARTIFACT and
            field(own, 'character_owner_id') is None and integer(field(own, 'holy_site_owner_id'), 'post holy-site owner') == SITE and
            field(own, 'player_owned_reference_member') is False and
            field(field(own, 'site_equipped_slot_member'), 'available') is True and
            field(field(own, 'site_equipped_slot_member'), 'value') is True, 'Actual site ownership not independently observed')
    inventory = mapping(field(site, 'inventory'), 'actual site inventory')
    require(field(inventory, 'available') is True and ARTIFACT in [integer(x, 'site artifact') for x in array(field(inventory, 'artifact_ids'), 'site refs')], 'Actual site inventory missing 267')
    p_inv = mapping(field(permissions, 'player_inventory'), 'actual player inventory')
    require(field(p_inv, 'available') is True and field(p_inv, 'owner_matches_player') is True and
            ARTIFACT not in [integer(x, 'player artifact') for x in array(field(p_inv, 'artifact_ids'), 'player refs')], 'Actual player inventory still contains 267 or unknown')
    slots = mapping(field(permissions, 'site_inventory_slots'), 'actual site slots')
    require(field(slots, 'available') is True, 'Native site slots unavailable')
    matches = [mapping(x, 'site slot') for x in array(field(slots, 'slots'), 'site slots')
               if integer(field(x, 'slot_index'), 'actual slot') == expected_slot]
    require(len(matches) == 1 and integer(field(matches[0], 'artifact_id'), 'actual slotted artifact') == ARTIFACT,
            'Original destination slot does not independently contain 267')
    return {'artifact_id': ARTIFACT, 'character_owner_id': None, 'holy_site_owner_id': SITE,
            'effective_slot_index': expected_slot, 'player_inventory_contains_artifact': False,
            'owner_slot_inventory_observed': True, 'total_payment_observed': False}


class Session:
    def __init__(self, client: CasePort, c: Contract) -> None:
        self.client = client
        self.c = c
        self.run_id = text(field(client.frozen, 'run_id'), 'real allocated run ID')
        self.calls = 0
        self.sequence = 0
        self.owner: Frame | None = None
        self.last: object = None
        self.evidence: list[Pin] = []
        self.world_claimed = False
        self.world_confirmed = False
        self.last_record: Pin | None = None

    def current_owner(self) -> Frame:
        if self.owner is None: raise ValueError('Actual current native owner frame missing')
        return self.owner

    def budget(self, n: int) -> None:
        require(self.calls + n <= self.c.max_calls, 'Finite public request budget exhausted')
        self.client.guard(reserve=120 + 300 + n * 20 + 10)

    def bind(self, value: object) -> Frame:
        raw = mapping(value, 'actual frame')
        if field(raw, 'active_event') is not None or field(raw, 'pending_character_interaction') is not None:
            # The common public lifecycle owns notification handling. Root must perform the
            # original displayed first/left legal option (health.1015 specialist takes priority).
            # The controlled comparison stops even after that mandatory continuation succeeds.
            require(self.last_record is not None, 'Original interruption native record must be preserved first')
            response = self.client.root_checkpoint('artifact-pair-native-interruption', {
                'original_native_frame_record': json_value(self.last_record), 'mandatory_existing_native_interruption_policy': True,
                'first_displayed_option_or_legal_original_left_button': True,
                'health_1015_specialist_priority': True, 'comparison_confounded': True,
                'remaining_public_calls': self.c.max_calls - self.calls}, reserve=120)
            require(field(response, 'native_interruption_continued') is True and
                    field(response, 'original_instance_independently_absent') is True,
                    'Mandatory native interruption handling is incomplete; preserve original instance')
            self.calls += integer(field(response, 'actual_public_calls_used'), 'Root interruption public calls', 1,
                                  self.c.max_calls - self.calls)
            raise ValueError('CONTROLLED_COMPARISON_CONFOUNDED_BY_NATIVE_INTERRUPTION')
        current = frame(value, self.run_id)
        require(current.player == PLAYER and current.date == DATE, 'C2 player/date changed; stop controlled experiment')
        if self.owner is not None:
            require((current.pid, current.generation, current.player, current.date) ==
                    (self.owner.pid, self.owner.generation, self.owner.player, self.owner.date), 'Actual world/process changed; never restart as retry')
        self.owner = current
        self.last = value
        return current

    def snapshot(self) -> Frame:
        self.budget(1)
        self.calls += 1
        value = self.client.snapshot(require_event_free=False)
        originals = list(self.client.output.glob('case-snapshot-*.actual-results.json'))
        if originals:
            original = max(originals, key=lambda x: x.stat().st_mtime_ns)
            rows = array(field(read(original), 'rows'), 'original snapshot rows')
            require(len(rows) == 1 and field(rows[0], 'result') == value, 'Snapshot original record differs from returned frame')
            self.last_record = pin(original)
        return self.bind(value)

    def batch(self, requests: list[tuple[str, Object]]) -> list[Object]:
        self.budget(len(requests))
        self.sequence += 1
        name = 'artifact-pair-' + self.c.arm + '-' + str(self.sequence).zfill(4)
        steps = [Q.step(name + '-' + str(i), tool, args) for i, (tool, args) in enumerate(requests)]
        Q.validate({'steps': steps})
        self.calls += len(requests)
        actual = self.client.output / (name + '.actual-results.json')
        try:
            raw_rows = self.client.execute_plan(steps, name, timeout=20 * len(steps))
        finally:
            if actual.is_file():
                original_record = pin(actual)
                self.evidence.append(original_record)
                self.last_record = original_record
        rows = array(raw_rows, 'real CaseClient public rows')
        require(len(rows) == len(steps), 'Missing original public response: never resubmit')
        result: list[Object] = []
        for row in rows:
            self.bind(field(row, 'after_snapshot'))
            # Public successful control rows omit this optional diagnostic entirely.
            require(field(row, 'ok') is True and mapping(row, 'public row').get('error') is None,
                    'Original public call rejected; no automatic retry')
            result.append(object_value(field(row, 'result')))
        return result

    def call(self, tool: str, args: Object | None = None) -> Object:
        return self.batch([(tool, {} if args is None else args)])[0]

    def pair(self, tool: str, args: Object, read_tool: str, read_args: Object) -> Object:
        return self.batch([(tool, args), (read_tool, read_args)])[1]

    def review(self, label: str, projection: Object, approval: str) -> Object:
        self.budget(0)
        response = object_value(self.client.root_checkpoint('artifact-pair-' + label,
            {'native_projection': projection, 'native_projection_sha256': digest(projection),
             'requested_review': approval, 'no_gameplay_command_authorized_by_ack': True}, reserve=120))
        require(field(response, 'run_id') == self.run_id and field(response, 'reviewer') == self.client.operator_reviewer and
                field(response, 'status') == 'complete' and field(response, approval) is True and
                field(response, 'original_image_directly_reviewed') is True and
                field(response, 'reviewed_native_observation_sha256') == digest(projection), 'Fresh Root image/native review is incomplete')
        image = parse_pin(field(response, 'original_image'))
        require(Path(image['path']).read_bytes().startswith(b'\x89PNG\r\n\x1a\n'), 'Actual original PNG required')
        return response

    def sample(self) -> Object:
        self.snapshot()
        starting_wallet = wallet(self.last)
        observations: list[object] = []
        for target in RECIPIENTS:
            value = self.call(Q.KNIGHT, {'character_id': target})
            observations.append(knight(value, self.current_owner(), target))
        site = self.call(Q.RELIC, {'holy_site_id': SITE})
        require(field(site, 'available') is True and field(site, 'read_only') is True, 'Actual target site unavailable')
        county = mapping(field(site, 'county_context'), 'target county')
        require(field(county, 'available') is True and integer(field(county, 'county_holder_id'), 'actual second beneficiary') == RECIPIENTS[1],
                'Second actor must remain the actual selected site county holder')
        return {'actors': json_value(observations), 'wallet': json_value(starting_wallet),
                'site': {key: json_value(field(site, key)) for key in ('requested_holy_site_id', 'player_rite_id', 'player_faith_id',
                    'county_context', 'cached_world_state', 'inventory')}, 'date_raw': DATE,
                'site_attribution_observed': False, 'cache_generation_time_known': False}

    def window(self, close: bool) -> None:
        query = Q.CLOSE_QUERY if close else Q.WINDOW
        args: Object = {} if close else {'window_kind': 'inventory'}
        initial = self.call(query, args)
        require(field(initial, 'available') is True and field(initial, 'needs_recovery') is False,
                'Inventory current state unavailable or a retained unknown intent is pending')
        current = field(initial, 'current')
        require(field(current, 'available') is True, 'Actual inventory current view unavailable')
        hidden = field(current, 'native_visible') is False and field(current, 'effective_visible') is False
        if (close and hidden) or (not close and not hidden and field(current, 'root_present') is True and
                                 field(current, 'native_visible') is True and field(current, 'effective_visible') is True and
                                 field(current, 'current_player_selected') is True):
            return
        submitted = self.call(Q.CLOSE if close else Q.OPEN)
        require(field(submitted, 'once_intent_consumed') is True and field(submitted, 'needs_recovery') is True,
                'Inventory action had no fresh own ticket; never borrow an old native sequence')
        sequence = integer(field(submitted, 'intent_sequence'), 'own actual inventory sequence', 1)
        for _ in range(3):
            after = self.call(Q.CLOSE_POST if close else Q.OPEN_POST, {'expected_intent_sequence': sequence})
            require(integer(field(after, 'intent_sequence'), 'post actual sequence', 1) == sequence, 'Inventory post crossed original intent')
            if field(after, 'desired_window_observed') is True:
                verify = self.call(Q.WINDOW, {'window_kind': 'inventory'})
                actual_view = field(verify, 'current')
                require(field(verify, 'available') is True and field(actual_view, 'available') is True and
                        field(actual_view, 'native_visible') is (not close) and field(actual_view, 'effective_visible') is (not close),
                        'Independent inventory current visibility differs')
                return
        raise ValueError('Original inventory action unknown; no automatic replay')


def quote(value: object) -> Object:
    require(field(value, 'available') is True and field(value, 'read_only') is True and
            field(value, 'loaded_source_pins_verified') is True and field(value, 'selected_artifact_matches_request') is True and
            field(value, 'preview_identity_available') is True, 'Real selected native relic quote unavailable')
    require(integer(field(value, 'requested_artifact_id'), 'quote item') == ARTIFACT and
            integer(field(value, 'requested_holy_site_id'), 'quote site') == SITE, 'Selected quote identity differs')
    own = field(value, 'artifact_ownership')
    require(field(own, 'available') is True and field(own, 'object_resolved') is True and
            field(own, 'character_owner_matches_player') is True and field(own, 'player_owned_reference_member') is True and
            field(own, 'holy_site_owner_id') is None and field(field(own, 'player_equipped_slot_member'), 'value') is False,
            'The actual personally owned unequipped artifact is required before enshrine')
    permissions = field(value, 'permissions')
    for source in ('artifact_permissions', 'current_buttons'):
        allowed = field(field(permissions, source), 'can_enshrine')
        require(field(allowed, 'available') is True and field(allowed, 'value') is True, 'Original native CanEnshrine is not explicitly allowed')
    destination = field(value, 'destination')
    require(field(destination, 'available') is True and field(destination, 'original_picker_called') is True and
            field(destination, 'replacing_artifact_id') is None, 'No site-relic replacement in this experiment')
    original = field(value, 'selected_action_effect_description')
    disabled = field(value, 'enshrine_disabled_tooltip')
    require(field(original, 'available') is True and field(disabled, 'available') is True, 'Complete original forecast/disabled text unavailable')
    return {'artifact_id': ARTIFACT, 'holy_site_id': SITE,
            'effective_slot_index': integer(field(destination, 'effective_slot_index'), 'actual destination slot', 0, 4095),
            'replacing_artifact_id': None, 'preview_sha256': sha(field(value, 'preview_identity_sha256')),
            'original_effect_description': text(field(original, 'text'), 'original selected effect', empty=True),
            'original_disabled_tooltip': text(field(disabled, 'text'), 'original disabled tooltip', empty=True)}


def draft(session: Session) -> Object | None:
    choice = session.c.draft
    if choice is None: return None
    state = session.pair('ck3_open_holy_site_creation_window_v1', {}, Q.CREATION, {})
    require(field(state, 'models_available') is True and field(state, 'models_complete') is True, 'Complete original draft models required')
    state = session.pair('ck3_select_holy_site_creation_type_v1', {'type_key': choice.type_key}, Q.CREATION, {})
    require(field(state, 'models_available') is True and field(state, 'models_complete') is True and
            field(state, 'selected_type_key') == choice.type_key, 'Read candidates for the actual selected type, not the initial default type')
    candidates = [integer(x, 'native barony candidate') for x in array(field(state, 'potential_barony_title_ids'), 'native candidates')]
    require(choice.first_barony_id in candidates and choice.second_barony_id in candidates,
            'PRE_NATIVE_CANDIDATE_BLOCKED: outside native list is not an original location refusal')
    require(choice.artifact_id in [integer(x, 'eligible artifact') for x in array(field(state, 'enshrinable_artifact_ids'), 'eligible artifacts')],
            'PRE_NATIVE_ARTIFACT_BLOCKED: no original refusal may be inferred')
    selected = [integer(x, 'selected artifact') for x in array(field(state, 'selected_artifact_ids'), 'draft selection')]
    require(not selected or selected == [choice.artifact_id], 'Do not silently remove another selected draft artifact')
    if choice.artifact_id not in selected:
        session.pair('ck3_set_holy_site_creation_artifact_selection_v1', {'artifact_id': choice.artifact_id, 'selected': True}, Q.CREATION, {})
    observations: list[Object] = []
    for location in (choice.first_barony_id, choice.second_barony_id):
        value = session.pair('ck3_select_holy_site_creation_barony_v1', {'barony_title_id': location}, Q.CREATION, {})
        require(field(value, 'available') is True and field(value, 'selection_available') is True and
                field(value, 'selected_type_key') == choice.type_key and integer(field(value, 'selected_barony_title_id'), 'selected native location') == location and
                [integer(x, 'selected draft fullID', 0, 2**32-2) for x in array(field(value, 'selected_artifact_ids'), 'selected draft artifacts')] == [choice.artifact_id] and
                field(value, 'normal_requirements_legality_observed') is True and field(value, 'create_tooltip_available') is True and
                field(value, 'native_rarity_sum_observed') is True and field(value, 'native_enabled_observed') is True and
                field(value, 'bypass_requirements_observed') is True and integer(field(value, 'bypass_requirements_raw'), 'ordinary requirements') == 0,
                'Independent selected draft context incomplete')
        available_quote = boolean(field(value, 'cached_resource_quote_available'), 'actual quote availability')
        raw_quote = field(value, 'cached_resource_vector_raw')
        quoted: list[str] | None = None
        if available_quote:
            raw_rows = array(raw_quote, 'complete original resource vector')
            require(len(raw_rows) == 10, 'All ten resources must be present')
            quoted = [str(integer(x, 'native resource raw', -(2**63), 2**63-1)) for x in raw_rows]
        else: require(raw_quote is None, 'Unavailable original quote must be null')
        observations.append({**{key: json_value(field(value, key)) for key in ('selected_type_key', 'selected_barony_title_id',
            'selected_artifact_ids', 'normal_requirements_can_create', 'native_create_button_enabled', 'create_tooltip')},
            'native_rarity_sum_raw_decimal': str(integer(field(value, 'native_rarity_sum_raw'), 'original rarity sum', -(2**63), 2**63-1)),
            'cached_resource_quote_available': available_quote, 'cached_resource_vector_raw_decimal': json_value(quoted)})
    require(field(observations[0], 'normal_requirements_can_create') is False and
            field(observations[1], 'normal_requirements_can_create') is True and
            text(field(observations[0], 'create_tooltip'), 'complete actual refusal') != '', 'Two native candidate places did not yield refusal/allowed contrast')
    require(field(observations[0], 'native_rarity_sum_raw_decimal') == field(observations[1], 'native_rarity_sum_raw_decimal'),
            'Rarity confounder changed between candidate places')
    projection: Object = {'locations': json_value(observations), 'create_dispatched': False,
                          'pre_native_rejection_is_original_refusal': False}
    review = session.review('draft-two-locations', projection, 'location_specific_refusal_observed')
    return {**projection, 'root_review': review, 'draft_only': True, 'alternative_current_draft_preserved': True}


def perform_personal(s: Session) -> Object:
    s.window(False)
    before = s.call(Q.ITEM, {'artifact_id': ARTIFACT})
    observed = item(before, s.current_owner())
    require(not observed['equipped'] and observed['can_equip'] is True and observed['effective_slot_index'] is not None and
            observed['replacing_artifact_id'] is None, 'Only one legal empty personal slot, no toggle/replacement')
    s.review('equip', object_value(observed), 'equip_approved')
    fresh = s.call(Q.ITEM, {'artifact_id': ARTIFACT})
    require(item(fresh, s.current_owner()) == observed, 'Personal quote/slot changed after review')
    claim(s)
    submitted = s.call(Q.EQUIP, {'artifact_id': ARTIFACT, 'desired_equipped': True,
        'expected_slot_index': observed['effective_slot_index'], 'expected_replacing_artifact_id': None, 'policy_positive': True})
    require(field(submitted, 'once_intent_consumed') is True, 'Personal submit did not claim this original intent')
    sequence = integer(field(submitted, 'intent_sequence'), 'own actual equip sequence', 1)
    for _ in range(3):
        post = s.call(Q.EQUIP_POST, {'artifact_id': ARTIFACT, 'expected_intent_sequence': sequence})
        require(integer(field(post, 'intent_sequence'), 'post exact intent', 1) == sequence, 'Equip post crossed original intent')
        if field(post, 'desired_inventory_state_observed') is True:
            value = s.call(Q.ITEM, {'artifact_id': ARTIFACT})
            after = item(value, s.current_owner())
            require(after['equipped'] and after['equipped_slot_index'] == observed['effective_slot_index'], 'Fresh independent owner/slot did not confirm equip')
            s.world_confirmed = True
            return {'original_sequence_decimal': str(sequence), 'independent_item': json_value(after),
                    'personal_owner_slot_observed': True, 'old_equipment_film_slot_reopened': False}
    raise ValueError('Equip original intent unknown; retain original SDK lock and never retry')


def perform_enshrine(s: Session) -> Object:
    s.window(True)
    ui = s.pair(Q.SITE_OPEN, {'holy_site_id': SITE}, Q.WINDOW, {'window_kind': 'holy_site'})
    require(field(ui, 'available') is True and field(ui, 'effective_visible') is True and
            integer(field(ui, 'current_subject_id'), 'actual visible site') == SITE, 'Original selected holy-site window not visible')
    selected = s.pair(Q.SELECT_ITEM, {'holy_site_id': SITE, 'artifact_id': ARTIFACT}, Q.ACTION,
                      {'holy_site_id': SITE, 'artifact_id': ARTIFACT})
    proposed = quote(selected)
    s.review('enshrine', proposed, 'enshrine_approved')
    require(quote(s.call(Q.ACTION, {'holy_site_id': SITE, 'artifact_id': ARTIFACT})) == proposed, 'Original full quote changed after review')
    claim(s)
    ack_unknown = False
    try:
        s.call(Q.DONATE, {'holy_site_id': SITE, 'artifact_id': ARTIFACT,
            'expected_effective_slot_index': proposed['effective_slot_index'], 'expected_replacing_empty': True,
            'expected_preview_sha256': proposed['preview_sha256'], 'expected_replacing_artifact_id': None})
    except (ValueError, TimeoutError, subprocess.TimeoutExpired):
        ack_unknown = True  # Never resubmit; independent world reads may still prove the retained original outcome.
    # The retained SDK pending file is never removed, including after known world success.
    action = s.call(Q.ACTION, {'holy_site_id': SITE, 'artifact_id': ARTIFACT})
    site = s.call(Q.RELIC, {'holy_site_id': SITE})
    permissions = s.call(Q.PERMISSION, {'holy_site_id': SITE, 'artifact_id': ARTIFACT})
    result = settle(action, site, permissions, expected_slot=integer(proposed['effective_slot_index'], 'original slot'))
    s.world_confirmed = True
    return {**result, 'original_quote': proposed, 'ack_unknown': ack_unknown, 'retained_sdk_claim_cleared': False}


def pair_core(c: Contract) -> Object:
    return {'pair_id': c.pair_id, 'machine_id': c.machine_id, 'saved_sha256': SAVE_SHA, 'saved_bytes': SAVE_BYTES,
            'artifact_id': ARTIFACT, 'holy_site_id': SITE, 'recipient_ids': list(RECIPIENTS),
            'metric': 'knight_effectiveness_raw', 'native_dll': json_value(c.native_dll),
            'native_qualification': json_value(c.native_qualification), 'previous_pending': json_value(c.prior_pending),
            'previous_known_world_result': json_value(c.prior_result)}


def claim(s: Session) -> None:
    require(not s.world_claimed, 'One artifact world action per arm; unknown is never retried')
    owner = s.current_owner()
    # Additional evidence latch only. SDK/native ledgers remain at their existing managed state paths.
    write_once(s.c.pair_root / (s.c.arm + '.original-world-action.json'), {
        'schema': 'artifact-pair-evidence-claim-v1', 'pair_core_sha256': digest(pair_core(s.c)),
        'run_id': s.run_id, 'pid': owner.pid, 'connection_generation_decimal': str(owner.generation),
        'native_ledger_location_overridden': False, 'unknown_may_be_replayed': False})
    s.world_claimed = True


def run_case(context: object, client: object) -> Object:
    c = validate_contract(context)
    require(isinstance(client, CasePort), 'Existing public CaseClient interface required')
    if not isinstance(client, CasePort): raise ValueError('Existing public CaseClient required')
    s = Session(client, c)
    result: Object = {'schema': 'faith-e02-artifact-pair-arm-result-v1', 'arm': c.arm, 'pair_core': pair_core(c),
        'machine_id': c.machine_id, 'run_id': s.run_id, 'observed_at_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'PARTIAL', 'business_pass': False, 'product_release_pass': False, 'automatic_retry': False,
        'site_attribution_observed': False, 'selected_site_contribution_raw': None, 'total_payment_observed': False,
        'normal_close_pending': True, 'unknown_original_action': False, 'a2': None, 'before': None, 'after': None,
        'world_post': None, 'error': None}
    try:
        manifest = mapping(client.manifest, 'selected shared runtime manifest')
        native_dll = field(field(manifest, 'native'), 'dll')
        require(field(manifest, 'machine_id') == c.machine_id and
                integer(field(native_dll, 'bytes'), 'selected DLL bytes') == c.native_dll['bytes'] and
                sha(field(native_dll, 'sha256')) == c.native_dll['sha256'] and
                field(manifest, 'native_input_identity_evidence') == c.native_qualification,
                'Current shared runtime must bind this exact qualified native cohort, never a private replacement')
        old_run = check_history(c)
        require(s.run_id != old_run, 'Old known-success R0007 cannot be replayed')
        opening = s.snapshot()
        require(Path(text(field(field(s.last, 'managed_campaign_run_binding'), 'state_dir'), 'actual managed state')).resolve() == client.state.resolve(),
                'Actual allocated state differs; never choose a new private ledger path')
        result['actual_pid'] = opening.pid
        result['actual_connection_generation_decimal'] = str(opening.generation)
        core_path = c.pair_root / 'pair-core.json'
        if core_path.exists(): require(read(core_path) == pair_core(c), 'Pair mother/cohort/history changed between arms')
        else: write_once(core_path, pair_core(c))
        require(not (c.pair_root / (c.arm + '.original-world-action.json')).exists(),
                'This arm already has an original action; reuse known evidence or retain unknown, never create a new ledger root')
        other = c.pair_root / ('enshrine' if c.arm == 'personal' else 'personal') / RESULT
        if other.exists():
            previous = read(other)
            require(field(previous, 'run_id') != s.run_id and integer(field(previous, 'actual_pid'), 'other actual PID') != opening.pid,
                    'Two arms require genuinely independent allocated native processes/worlds')
        result['a2'] = draft(s)
        result['before'] = s.sample()
        result['world_post'] = perform_personal(s) if c.arm == 'personal' else perform_enshrine(s)
        result['after'] = s.sample()
        result['status'] = 'ARM_OBSERVED_PAIR_PENDING'
    except Exception as error:
        result['error'] = type(error).__name__ + ': ' + str(error)
        result['unknown_original_action'] = s.world_claimed and not s.world_confirmed
    result['public_calls_used'] = s.calls
    result['public_calls_cap'] = c.max_calls
    result['original_action_claimed'] = s.world_claimed
    result['world_post_confirmed'] = s.world_confirmed
    result['public_native_record_pins'] = json_value(s.evidence)
    native_report = client.output.parent / 'native-report.json'
    result['original_native_report'] = json_value(pin(native_report)) if native_report.is_file() else None
    result['caller_sources'] = json_value(list(c.dependencies))
    target = client.output / RESULT
    write_once(target, result)
    # A missing/unknown arm never overwrites a prior result or changes a retained SDK claim.
    write_once(c.pair_root / c.arm / RESULT, result)
    return result


def verify_case(context: object) -> Object:
    c = validate_contract(context)
    return {'schema': 'faith-e02-artifact-pair-verification-v1', 'arm': c.arm,
            'business_pass': False, 'product_release_pass': False,
            'runtime_status': 'USE_ORIGINAL_ARM_AND_PAIR_RESULT', 'pair_comparison_requires_join': True}
