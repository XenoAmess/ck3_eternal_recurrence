"""Detached optional native value-scope observation; never default missing to zero."""
NAMES = {'serial': 'lyd_i3b_event_serial', 'nonce': 'lyd_i3b_event_nonce', 'phase': 'lyd_i3b_event_phase'}


def observe(context, state, before_frame, event_contract):
    # Caller has already authenticated this original SDK/native query, exact
    # checkpoint-before frame and unchanged save transition using the Title hook.
    current = event_contract.normalize_current_event_window_context_v1(
        context, expected_event_instance_id=context['current_event_instance_id'],
        expected_date_raw=before_frame['date_raw'], expected_snapshot_revision=before_frame['native_revision'])
    observations, missing = {}, []
    for field, name in NAMES.items():
        rows = [row for row in current['saved_scopes'] if row['name'] == name]
        if len(rows) > 1:
            raise ValueError('duplicate native numeric scope ' + name)
        if not rows or 'numeric_value' not in rows[0]['scope']:
            observations[field] = {'status': 'UNKNOWN', 'scope_name': name, 'native_value': None, 'matches_saved_round': None}
            missing.append(field)
            continue
        scope = rows[0]['scope']
        if scope['raw_type_index'] != 1 or scope['type_key'] != 'value' or scope['subtype'] != 0:
            raise ValueError('native numeric scope type/subtype differs ' + name)
        numeric = scope['numeric_value']
        value = numeric['integer_value']
        if not isinstance(value, str):
            raise ValueError('formal round native numeric scope must be exact integer ' + name)
        expected = state['round'][field]
        if type(expected) is not int or int(value) != expected:
            raise ValueError('native numeric scope differs from actual saved round ' + name)
        observations[field] = {'status': 'ACTUAL_NATIVE_VALUE_SCOPE_SAVED_ROUND_MATCH', 'scope_name': name,
            'native_value': dict(numeric), 'observed_integer': int(value), 'saved_round_value': expected,
            'matches_saved_round': True}
    return {'schema': 'lyd.author.optional-native-event-value-scopes.v1',
        'status': 'UNKNOWN' if len(missing) == 3 else 'INCOMPLETE_NATIVE_VALUE_SCOPE_OBSERVATION' if missing else 'ALL_THREE_NATIVE_VALUE_SCOPES_MATCH_ACTUAL_SAVED_ROUND',
        'before_frame': dict(before_frame), 'event_definition_key': current['event_definition_key'],
        'event_instance_id': current['current_event_instance_id'], 'fields': observations, 'missing_fields': missing,
        'missing_preserved_as_unknown': True, 'old_formal_event_context_qualification': state.get('formal_event_context_qualification'),
        'formal_callback_flow_qualified': None, 'actual_pass': None, 'formal_mandate_credit': None}
