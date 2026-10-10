"""Strict owned natural Army phase transport; every frame keeps its boundary."""
from __future__ import annotations
from copy import deepcopy
from .army_daily_assault_roster_admission_contract import _typed as _roster_typed
from .army_daily_assault_active_table_contract import normalize_current_daily_assault_table_v1

_SHAPES = {}
def _shape(name, declaration):
    _SHAPES[name] = dict(field.split('=', 1) for field in declaration.split())

def _typed(value, kind, name):
    if kind.endswith('?'):
        if value is None: return
        kind = kind[:-1]
    if kind.endswith('[]'):
        if type(value) is not list or len(value) > 65536:
            raise ValueError(f'{name} native array is malformed')
        for i, item in enumerate(value): _typed(item, kind[:-2], f'{name}[{i}]')
        return
    if kind in _SHAPES:
        fields = _SHAPES[kind]
        if type(value) is not dict or set(value) != set(fields):
            raise ValueError(f'{name} exact owned shape is malformed')
        for key, child in fields.items(): _typed(value[key], child, f'{name}.{key}')
        return
    if kind.startswith('roster:'):
        _roster_typed(value, kind[7:], name); return
    if kind == 'table':
        if value is None: raise ValueError(f'{name} table missing')
        normalize_current_daily_assault_table_v1(value); return
    if kind == 'raw':
        _raw(value, name); return
    if kind == 'str':
        if type(value) is not str: raise ValueError(f'{name} text malformed')
    elif kind == 'bool':
        if type(value) is not bool: raise ValueError(f'{name} bool malformed')
    elif kind[0] in 'iu' and kind[1:].isdigit():
        bits = int(kind[1:]); lower = 0 if kind[0] == 'u' else -(1 << (bits-1))
        upper = 1 << bits if kind[0] == 'u' else 1 << (bits-1)
        if type(value) is not int or not lower <= value < upper:
            raise ValueError(f'{name} integer malformed')
    else: raise ValueError(f'{name} unsupported type')

def _raw(value, name, depth=0):
    if depth > 24: raise ValueError(f'{name} nested copy malformed')
    if value is None or type(value) in (bool, str): return
    if type(value) is int and -(1 << 63) <= value < (1 << 64): return
    if type(value) is list and len(value) <= 65536:
        for item in value: _raw(item, name, depth+1)
        return
    if type(value) is dict and len(value) <= 128 and all(type(key) is str for key in value):
        for item in value.values(): _raw(item, name, depth+1)
        return
    raise ValueError(f'{name} raw owned field malformed')

_shape('Token', 'clock_identity=u64 sequence=u64 thread_id=u32?')
_shape('Roster', 'boundary=str capture_rva=u64 capture_event=Token begin_identity=u64? end_identity=u64? count=i32? complete=bool ordered_full_ids=u32[]')
_shape('Scope', 'observed=bool phase=str actual_entry_rva=u64 caller_return_rva=u64 primary_manager_identity=u64 secondary_manager_identity=u64 game_state_identity=u64 session_identity=u64? entry_event=Token date_raw=u64? prefix_date_raw=u64? absolute_day_raw=u32? entry_c0_raw=u8? saved_c0_raw=u8? saved_mask02_admitted=bool? saved_c0_observed_rva=u64 saved_c0_event=Token original_army_roster=Roster')
_shape('PhaseRecord', 'scope=Scope original_called=bool original_returned=bool raw_return_bits=u64 returned_event=Token returned_date_raw=u64? returned_absolute_day_raw=u32? returned_c0_raw=u8? same_clock_thread_order=bool?')
_shape('Phase', 'schema_version=u32 source=str membership_basis=str subject_full_carmy_id_u32=u32 records=PhaseRecord[]')
_shape('Boundary', 'query_sequence=u64? game_date_raw_i32=i32? absolute_day_raw_i32=i32? calendar_flags_raw_u8=u8? callsite_rva=u32 native_occurrence_index=i32? executable_sha256=str frame_identity=str primary_manager_identity=str original_roster_capture_identity=str selected_army_identity=str stage=str')
_shape('AppendInput', 'native_occurrence_index=i32 requested_army_full_id_u32=u32? selected_siege_full_id_u32=u32? selected_army_full_id_u32=u32? selected_siege_fnv1a_u32=u32? army_append_input_ready=bool army_append=bool? arrg_append_inputs_ready=bool ordered_arrg_full_ids_u32=u32[]?')
_shape('PreparationInput', 'boundary_binding_ready=bool ordered_append_inputs_ready=bool current_group_frame_matches=bool current_group_records_ready=bool actual_callback_execution_observed=bool full_future_table_placement_ready=bool full_daily_assault_ready=bool full_monthly_execution_ready=bool source=str unavailable_reason=str boundary=Boundary original_roster=roster:RawReferences removal_queue=roster:RawReferences occurrence_inputs=roster:RosterAdmissionOccurrence[] ordered_append_inputs=AppendInput[] current_group_records=table?')
_shape('PreparationActive', 'incoming_primary_manager=u64 incoming_selected_army=u64 caller_return_rva=u64 callsite_rva=u64 actual_caller_iterator=u64 actual_caller_end=u64 native_occurrence_index=i32? local_start_index=i32? requested_army_full_id_u32=u32? iterator_entry_full_id_u32=u32? selected_army_full_id_raw_u32=u32? observed=bool parent_bound=bool original_occurrence_bound=bool parent=Scope entry_event=Token')
_shape('PreparationSnapshot', 'selected_army_full_id_raw_u32=u32? game_state_identity_raw=u64? game_date_raw_u64=u64? absolute_day_raw_u32=u32? calendar_flags_raw_u8=u8? game_state_matches_parent=bool? source_inputs_ready=bool selected_occurrence=roster:RosterAdmissionOccurrence removal_queue=roster:RawReferences copied_stage_input=PreparationInput?')
_shape('PreparationEvent', 'sequence=u64 original_rax_raw_u64=u64 capture_failure_flags=u32 original_called=bool original_returned=bool same_selected_army_generation_after=bool? active=PreparationActive before=PreparationSnapshot after=PreparationSnapshot returned_event=Token')
_shape('Preparation', 'schema_version=u32 source=str membership_basis=str observer_installed=bool current_session_guard=bool oldest_available_sequence=u64 latest_sequence=u64 overwritten_events=u64 unattributed_capture_failures=u64 dropped_owned_copy_events=u64 events=PreparationEvent[]')
_shape('DeniedCount', 'physical_slot_i64=i64 arrg=bool actual_count_raw_i32=i32')
_shape('PlacementSnapshot', 'receiver_table_identity=u64 entries_identity=u64? occupied_count_raw_i32=i32? mask_raw_i32=i32? tail_distance_raw_u8=u8? load_factor_f32_bits_u32=u32? table_allocator_identity=u64? read_calls=u64 read_bytes=u64 admitted_reference_count=u64 native_empty_storage_matches=bool? current_primary_table_matches_receiver=bool? capture_complete=bool budget_exhausted=bool stage=str capture_event=Token physical_table=table denied_vector_counts=DeniedCount[]')
_shape('PlacementEvent', 'sequence=u64 caller_return_rva=u64 incoming_table_identity=u64 incoming_output_identity=u64 incoming_key_identity=u64 incoming_hash_raw_u32=u32 incoming_key_raw_u32=u32? selected_army_full_id_at_placement_u32=u32? original_rax_raw_u64=u64 returned_entry_identity=u64? returned_inserted_raw_u8=u8? returned_physical_slot_i64=i64? capture_failure_flags=u32 entries_identity_changed=bool? parent_bound=bool recursive=bool original_called=bool original_returned=bool preparation=PreparationActive entry_event=Token returned_event=Token before=PlacementSnapshot after=PlacementSnapshot')
_shape('PlacementProjection', 'placement_sequence=u64 matched_preparation_event=PreparationEvent? mapping_ready=bool unavailable_reason=str projected_stage=str projection=raw?')
_shape('Placement', 'schema_version=u32 source=str membership_basis=str observer_installed=bool current_session_guard=bool oldest_available_sequence=u64 latest_sequence=u64 overwritten_events=u64 unattributed_capture_failures=u64 events=PlacementEvent[] conditional_preparation_append_projections=PlacementProjection[]')
_shape('CoreOccurrence', 'stored_index=i32 raw_full_id=i32? resolved_full_id=i32? physical_token=u64 used_fallback=bool? unavailable_reason=str')
_shape('CorePersistent', 'physical_token=u64 resolved_full_id=i32? unavailable_reason=str physical_values=raw')
_shape('CoreData', 'record_index=i32 persistent_regiment_id=i32? chunk_index=i32? persistent_physical_token=u64 state_raw=i32? native_record_admitted=bool unavailable_reason=str')
_shape('CoreArRg', 'occurrence=CoreOccurrence resolved_magic_14_raw=u32? native_refresh_admitted=bool? native_loss_writer_skipped=bool? native_record_count=i32? records_complete=bool unavailable_reason=str records=CoreData[]')
_shape('CoreArmy', 'physical_token=u64 resolved_full_id=i32? native_arrg_occurrence_count=i32? unavailable_reason=str arrg_occurrences=CoreArRg[]')
_shape('CoreFrame', 'native_persistent_occurrence_count=i32? native_army_refresh_occurrence_count=i32? capture_complete=bool persistent_occurrences=CoreOccurrence[] army_refresh_occurrences=CoreOccurrence[] persistent_objects=CorePersistent[] army_objects=CoreArmy[] missing_inputs=str[]')
_shape('CoreEvent', 'journal_sequence=u64 manager_identity=u64 caller_return_rva=u64 raw_return_bits=u64 entry_date_raw=u64? returned_date_raw=u64? observed=bool original_called=bool original_returned=bool entry_provenance_complete=bool return_provenance_complete=bool parent_scope=Scope entry_event=Token returned_event=Token entry=CoreFrame returned=CoreFrame provenance_failures=str[]')
_shape('Core', 'schema_version=u32 source=str membership_basis=str observer_initialized=bool observer_installed=bool latest_journal_sequence=u64 overwritten_events=u64 publication_failures=u64 events=CoreEvent[]')
_shape('ConsumerVector', 'data_identity=u64? capacity_raw_i32=i32? count_raw_i32=i32? allocator_identity=u64? references_complete=bool ordered_full_ids_u32=u32?[]')
_shape('Resolved', 'requested_full_id_u32=u32? object_identity=u64? selected_full_id_u32=u32? used_fallback=bool?')
_shape('ConsumerArmy', 'native_index=i32 resolution=Resolved regiment_roster=ConsumerVector native_whole_current_soldiers=i32?')
_shape('ConsumerGroup', 'native_index=i32 physical_slot_i64=i64 control_raw_u8=u8? hash_raw_u32=u32? siege_full_id_u32=u32? siege_resolution=Resolved province_identity=u64? province_magic_raw_u32=u32? province_full_id_u32=u32? breach_level_raw_i32=i32? native_current_expected_loss=i32? natural_budget_observed=bool budget_entry_event=Token budget_returned_event=Token besieging_dependencies_complete=bool armies=ConsumerVector arrgs=ConsumerVector army_occurrences=ConsumerArmy[]')
_shape('ConsumerTable', 'entries_identity=u64? occupied_count_raw_i32=i32? mask_raw_i32=i32? end_slot_raw_i32=i32? tail_distance_raw_u8=u8? end_marker_control_raw_u8=u8? load_factor_f32_bits_u32=u32? controls_complete=bool raw_references_complete=bool physical_controls=u8?[] groups=ConsumerGroup[]')
_shape('ConsumerPhysical', 'object_identity=u64 maximum_soldiers=i32? current_soldiers=i32? persistent_regiment_id=i32? own_chunk_ordinal=i32? army_regiment_id=i32? state_raw_i32=i32?')
_shape('ConsumerData', 'native_index=i32 persistent_full_id_u32=u32? data_chunk_ordinal=i32? persistent_resolution=Resolved persistent_identity_valid=bool? ready=bool physical=ConsumerPhysical?')
_shape('ConsumerRegiment', 'resolution=Resolved magic_raw_u32=u32? identity_valid=bool? native_loss_writer_skipped=bool? current_soldiers=i32? maximum_soldiers=i32? definition_type_raw_i32=i32? data_identity=u64? data_capacity_raw_i32=i32? data_count_raw_i32=i32? data_complete=bool same_instance_after=bool? same_data_header_after=bool? data_records=ConsumerData[]')
_shape('ConsumerParent', 'active=bool exact_post_date_parent=bool actual_entry_rva=u64 caller_return_rva=u64? manager_identity=u64 entry_event=Token phase_entry_event=Token date_raw=u64? absolute_day_raw=u32?')
_shape('ConsumerEvent', 'journal_sequence=u64 capture_stage=str parent=ConsumerParent returned_event=Token original_called=bool original_returned=bool current_session_guard=bool actual=bool raw_return_bits=u64 capture_failure_flags=u32 entry_table=ConsumerTable returned_table=ConsumerTable entry_pending_queue=ConsumerVector returned_pending_queue=ConsumerVector entry_regiments=ConsumerRegiment[] returned_regiments=ConsumerRegiment[] entry_dependencies_complete=bool returned_dependencies_complete=bool conditional_stage_binding_ready=bool full_daily=bool full_monthly=bool')
_shape('Consumer', 'schema_version=u32 source=str membership_basis=str observer_installed=bool current_session_guard=bool latest_journal_sequence=u64 overwritten_events=u64 events=ConsumerEvent[]')
_shape('ReleaseVector', 'data_address=u64? count_raw_i32=i32? capacity_raw_i32=i32? allocator_address=u64? allocator_matches_expected=bool? expected_allocator_rva_u32=u32 payload_complete=bool payload_count=u32 raw_full_ids_u32=u32[]')
_shape('ReleaseEvent', 'sequence=u64 entry_event=Token returned_event=Token thread_id=u32 consumer_entry_event=Token natural_parent_entry_event=Token exact_post_date_parent=bool primary_manager_address=u64 source_consumer_rva=u64 consumer_caller_return_rva=u64? passed_date_raw64=u64? absolute_day_raw=u32? caller_return_rva=u64 callsite_rva=u64 record_plus10_address=u64 entries_address=u64? physical_slot=u64? control_before=u8? control_at_record_return=u8? occupied_count_before=i32? occupied_count_at_record_return=i32? arrgs_before=ReleaseVector armies_before=ReleaseVector arrgs_after=ReleaseVector armies_after=ReleaseVector original_returned=bool original_rax_raw_u64=u64 same_parent_at_return=bool same_clock_thread_order=bool? capture_failure_flags=u32 post_stage=str actual=bool')
_shape('Release', 'schema_version=u32 source_contract_game_version=str source_executable_sha256=str source_release_rva=u64 source=str membership_basis=str observer_installed=bool current_session_guard=bool oldest_available_sequence=u64 latest_sequence=u64 overwritten_events=u64 unattributed_capture_failures=u64 ignored_noncanonical_receivers=u64 event_count=u64 events=ReleaseEvent[]')
_shape('DueList', 'buffer_identity=u64? capacity=i32? count=i32? complete=bool ordered_full_ids=u32[]')
_shape('DuePhysical', 'requested_full_id=u32 physical_identity=u64 resolution_complete=bool used_native_fallback=bool selected_full_id=u32? magic=u32?')
_shape('DueChunk', 'ordinal=i32 physical_identity=u64 maximum=i32? current=i32? owner_full_id=u32? stored_ordinal=i32? association_full_id=u32? byte14=u8? state=i32? date_raw64=u64?')
_shape('DueReference', 'source_ref_identity=u64 owner_full_id=u32? ordinal=i32? receiver=DuePhysical chunk=DueChunk?')
_shape('DueArRg', 'receiver=DuePhysical current38=i32? maximum3c=i32? army140=u32? owner144=u32? character148=u32? state14c=i32? source_refs_identity=u64? source_ref_count=i32? source_refs_complete=bool source_refs=DueReference[]')
_shape('DueRecord', 'physical_identity=u64 date_low32=i32? pending_count=i32? character_count=i32? pending_refs_complete=bool character_ids_complete=bool pending_refs=DueReference[] character_full_ids=u32[]')
_shape('DueArmy', 'receiver=DuePhysical unit124=u32? combat128=u32? combat_receiver=DuePhysical source_combat_skip=bool? gathering_count=i32? gathering_buffer_identity=u64? gathering_records_complete=bool gathering_records=DueRecord[] arrg_roster=DueList arrg=DueArRg[] finished_date190=u64? statistics130_hex=str?')
_shape('DuePersistent', 'receiver=DuePhysical prepared148=i64? chunks=DueChunk[]')
_shape('DueSnapshot', 'primary_identity=u64 date_pointer_identity=u64 event=Token passed_date_raw64=u64? game_state_date_raw64=u64? absolute_day_raw=u32? current_c0_raw=u8? queue158=DueList persistent_roster30=DueList army_roster50=DueList queued_armies=DueArmy[] roster_armies=DueArmy[] persistent=DuePersistent[] entry_due_refs_at_return=DueReference[] returned_ref_fields_basis=str entry_queue_extent_backing_full_ids=u32[] entry_queue_extent_backing_complete=bool all_declared_reads_complete=bool missing_fields=str[]')
_shape('DueEvent', 'observed=bool original_called=bool original_returned=bool actual_boundary_admitted=bool actual_poststage_observed=bool actual_return_rva=u64 raw_return_bits=u64 actual_saved_mask=u8? saved_mask_parent_observation_admitted=bool? same_clock_thread_order=bool? active_parent_unchanged=bool? unavailable_reason=str parent=Scope entry=DueSnapshot returned=DueSnapshot')
_shape('DueLocations', 'queue_count_load=u64 queue_fullid_load=u64 due_date_compare=u64 chunk_bind_call=u64 army_refresh_call=u64')
_shape('Due', 'schema=str source=str callee_rva=u64 caller_return_rva=u64 logical_source_end_exclusive=u64 source_exe_sha256=str refresh_cache_basis=str internal_refresh_callback_observed=bool source_locations=DueLocations prediction_ready=bool whole_daily_monthly_ready=bool records=DueEvent[]')
_shape('CleanupRoster', 'boundary=str capture_rva=u64 capture_event=Token begin_identity=u64? end_identity=u64? count=i32? complete=bool copied_occurrence_count=u64 ordered_full_ids=u32[]')
_shape('CleanupScope', 'observed=bool phase=str actual_entry_rva=u64 caller_return_rva=u64 primary_manager_identity=u64 secondary_manager_identity=u64 game_state_identity=u64 session_identity=u64? entry_event=Token date_raw=u64? prefix_date_raw=u64? absolute_day_raw=u32? entry_c0_raw=u8? saved_c0_raw=u8? saved_mask02_admitted=bool? saved_c0_observed_rva=u64 saved_c0_event=Token original_army_roster=CleanupRoster')
_shape('CleanupSlot', 'physical_index=i32 record_identity=u64 vtable_identity=u64? slot0_target_identity=u64? slot0_matches_known_mode0_source=bool? requested_regi_full_id=u32? ordinal=i32? selection=str indexed_regi_full_id=u32? selected_regi_full_id=u32? selected_magic_14=u32? selected_regi_identity=u64? selected_regi_valid=bool? computed_chunk_identity=u64? date_1c_raw64=u64? complete=bool unavailable_reason=str')
_shape('CleanupFrame', 'primary_manager_identity=u64 header_identity=u64 passed_date_pointer_identity=u64 passed_date_raw64=u64? buffer_identity=u64? live_count_raw_i32=i32? copied_physical_extent=u64 header_complete=bool physical_copy_complete=bool complete=bool truncated=bool original_backing_address_preserved=bool? unavailable_reason=str physical_slots=CleanupSlot[]')
_shape('CleanupEvent', 'journal_ordinal=u64 actual_entry_rva=u64 caller_return_rva=u64 source_call_admitted=bool saved_mask02_admitted_by_literal_call=bool? phase=CleanupScope before_event=Token before_copied_event=Token returned_event=Token after_copied_event=Token before=CleanupFrame after=CleanupFrame original_called=bool original_returned=bool raw_return_bits=u64? same_clock_thread_order=bool? phase_date_matches_passed_date=bool? capture_failure_flags=u32')
_shape('CleanupJournal', 'status=str source=str actual_entry_rva=u64 literal_caller_return_rva=u64 snapshot_basis=str conditional_predictor_executed=bool observer_installed=bool oldest_available_ordinal=u64 latest_ordinal=u64 overwritten_records=u64 unattributed_invocations=u64 dropped_record_copies=u64 event_count=u64 events=CleanupEvent[]')
_shape('Cleanup', 'membership_basis=str journal=CleanupJournal')
_shape('PrefixQueue', 'data_identity=u64? end_identity=u64? capacity_raw_i32=i32? count_raw_i32=i32? bounds_valid=bool? copy_bound_admitted=bool? copied_complete=bool ordered_full_ids=u32[]')
_shape('PrefixSnapshot', 'source_c8=PrefixQueue destination_158=PrefixQueue supplied_date_raw_u64=u64? game_date_raw_u64=u64? absolute_day_raw_u32=u32? calendar_c0_raw_u8=u8? conditional_no_work_arm=bool? positive_physical_transition_complete=bool')
_shape('PrefixParent', 'observed=bool phase_raw=u32 actual_entry_rva=u64 caller_return_rva=u64 primary_manager_identity=u64 secondary_manager_identity=u64 game_state_identity=u64 date_raw_u64=u64? absolute_day_raw_u32=u32?')
_shape('PrefixRoster', 'boundary_raw=u32 capture_rva=u64 capture_event=Token begin_identity=u64? end_identity=u64? count_raw_i32=i32? complete=bool ordered_full_ids=u32[]')
_shape('PrefixEvent', 'sequence=u64 primary_manager_identity=u64 date_argument_identity=u64 caller_return_rva=u64 parent_bound=bool parent_entry_event=Token parent=PrefixParent entry_event=Token returned_event=Token original_called=bool original_returned=bool incoming_rax_raw_u64=u64 original_rax_raw_u64=u64 capture_failure_flags=u32 before=PrefixSnapshot after=PrefixSnapshot original_roster_capture_complete=bool captured_original_roster=PrefixRoster')
_shape('PrefixJournal', 'observer_installed=bool current_session_guard=bool oldest_available_sequence=u64 latest_sequence=u64 overwritten_events=u64 unattributed_capture_failures=u64 events=PrefixEvent[]')
_shape('Prefix', 'membership_basis=str journals=PrefixJournal[]')

FAMILIES = {
    'army_natural_phase_observations_v1': ('Phase', 'owned_native_natural_army_phase_records'),
    'actual_army_regular_core_observations_v1': ('Core', 'native_natural_army_regular_core_entry_return'),
    'actual_army_daily_assault_preparation_observations_v1': ('Preparation', 'native_natural_army_daily_assault_preparation_entry_return'),
    'actual_army_assault_placement_observations_v1': ('Placement', 'native_natural_army_assault_placement_entry_return'),
    'army_actual_assault_consumer_observations_v1': ('Consumer', 'native_actual_assault_consumer_entry_return'),
    'actual_army_assault_group_release_observations_v1': ('Release', 'native_natural_assault_record_entry_return'),
    'native_gathering_due_natural_stage_12004': ('Due', 'native_gathering_due_natural_stage_12004'),
    'actual_army_cleanup_observations_v1': ('Cleanup', None),
    'actual_army_pre_date_prefix_observations_v1': ('Prefix', None),
}

def _token_key(token):
    return token['clock_identity'], token['sequence'], token['thread_id']

def _ordered(start, end):
    return (start['clock_identity'] != 0 and start['clock_identity'] == end['clock_identity']
            and start['sequence'] > 0 and start['sequence'] < end['sequence']
            and start['thread_id'] is not None and start['thread_id'] == end['thread_id'])

def normalize_army_observed_phase_family_12004(key, value, *, expected_carmy_id):
    if value is None: return None
    if expected_carmy_id is None: raise ValueError('owned Army phase has no exact full CArmy ID')
    shape, source = FAMILIES[key]
    _typed(value, shape, key)
    if source is not None and value['source'] != source:
        raise ValueError('owned Army source malformed')
    if 'schema_version' in value and value['schema_version'] != 1:
        raise ValueError('owned Army schema version malformed')
    # The family owners validate source-specific completeness and chronology.
    # Incomplete unrelated stages do not become shared readiness gates.
    if shape == 'Phase':
        from .army_observed_phase_validation_12004 import validate_phase_12004 as validate
    elif shape == 'Core':
        from .army_observed_core_validation_12004 import validate_core_12004 as validate
    elif shape == 'Preparation':
        from .army_observed_preparation_validation_12004 import validate_preparation_12004 as validate
    elif shape == 'Placement':
        from .army_observed_placement_validation_12004 import validate_placement_12004 as validate
    elif shape == 'Consumer':
        from .army_observed_consumer_validation_12004 import validate_consumer_12004 as validate
    elif shape == 'Release':
        from .army_observed_release_validation_12004 import validate_release_12004 as validate
    elif shape == 'Due':
        from .army_observed_due_validation_12004 import validate_due_12004 as validate
    elif shape == 'Cleanup':
        from .army_observed_cleanup_validation_12004 import validate_cleanup_12004 as validate
    else:
        from .army_observed_prefix_validation_12004 import validate_prefix_12004 as validate
    # The Army row retains its signed int32 transport. Observed rosters carry
    # the same full generation as a raw unsigned DWORD, including generation0.
    validate(value, expected_carmy_id=expected_carmy_id & 0xFFFFFFFF)
    return deepcopy(value)
