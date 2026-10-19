"""Bounded, diagnostic-only projection of existing campaign-root retry evidence."""
import json
from collections.abc import Mapping

ROOT = 'query-campaign-root-context-v1'
ERRORS = frozenset(('campaign-root snapshot changed or is not ready',
                    'application-main typed query failed or its snapshot changed'))
REASONS = frozenset(('starting_frame_missing_retry_inputs', 'fresh_snapshot_wait_failed',
                    'fresh_snapshot_not_mapping', 'fresh_frame_checks_failed',
                    'shared_readonly_retry_budget_exhausted'))
CHECKS = frozenset(('fresh_public_revision', 'fresh_native_revision', 'paused_ready',
    'same_date', 'same_episode', 'same_living_actor', 'nonterminal', 'no_event',
    'no_interaction', 'same_wars', 'same_armies', 'same_connection', 'single_failed_root_history'))
JSON_LIMIT = 2048


def _text(value, limit):
    if type(value) is not str:
        return None, False
    raw = value[:limit].encode('utf-8', errors='replace')
    return raw[:limit].decode('utf-8', errors='ignore'), len(value) > limit or len(raw) > limit


def _integer(value, *, positive=False):
    return value if type(value) is int and int(positive) <= value <= 2**64-1 else None


def _fields(value, names, *, positive=False):
    if not isinstance(value, Mapping):
        return {}
    return {name: valid for name in names
            if (valid := _integer(value.get(name), positive=positive)) is not None}


def _matched_root(error, diagnostic):
    if not isinstance(diagnostic, Mapping):
        return False
    request = getattr(error, 'native_request_frame', None)
    result = getattr(error, 'native_command_result_frame', None)
    if not isinstance(request, Mapping) or not isinstance(result, Mapping):
        return False
    request_id = request.get('request_id')
    return (diagnostic.get('diagnostic_only') is True
        and diagnostic.get('native_step') == request.get('step') == ROOT
        and diagnostic.get('native_error') == result.get('error') in ERRORS
        and request.get('type') == 'execute_step' and result.get('type') == 'command_result'
        and type(request.get('protocol_version')) is int and request['protocol_version'] == 1
        and type(result.get('protocol_version')) is int and result['protocol_version'] == 1
        and type(request_id) is str and 0 < len(request_id) <= 160
        and diagnostic.get('native_request_id') == result.get('request_id') == request_id
        and _integer(request.get('expected_revision'), positive=True) is not None
        and _integer(diagnostic.get('expected_native_revision'), positive=True) == request['expected_revision']
        and result.get('ok') is False)


def _size(value):
    return len(json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))


def project_campaign_root_retry_diagnostic_v1(error, native_diagnostic):
    """Pure projection; the caller supplies its class-checked native diagnostic.

    Absent evidence does not mean no retry. Frames/history never leave here.
    """
    try:
        if not _matched_root(error, native_diagnostic):
            return None
        projected = {'schema':'xar.campaign-root-readonly-retry-diagnostic/v1',
            'diagnostic_only':True, 'status':'evidence_absent', 'retry_authorized':False,
            'source_native_revision':native_diagnostic['expected_native_revision'],
            'evidence_truncated':False}
        retry = getattr(error, 'read_only_query_retry', None)
        decline = getattr(error, 'read_only_query_retry_decline', None)
        evidence = None
        if isinstance(retry, Mapping) and type(retry.get('second_error')) is str and retry['second_error']:
            projected['status'] = 'second_rejection'
            projected['second_error'], cut = _text(retry['second_error'], 512)
            projected['second_error_truncated'] = cut
            projected['evidence_truncated'] = cut
            evidence = retry
        elif (isinstance(decline, Mapping) and decline.get('status') == 'declined'
              and decline.get('reason') in REASONS):
            projected.update(status='declined', reason=decline['reason'])
            checks = decline.get('failed_checks')
            selected = []
            if type(checks) is list:
                for value in checks[:32]:
                    if type(value) is str and value in CHECKS and value not in selected:
                        selected.append(value)
                    else:
                        projected['evidence_truncated'] = True
                    if len(selected) == 16:
                        break
                projected['evidence_truncated'] |= len(checks) > 32
            elif checks is not None:
                projected['evidence_truncated'] = True
            projected['failed_checks'] = selected
            evidence = decline
        else:
            projected['evidence_meaning'] = 'no_supported_record; retry_entry_or_attempt_unknown'
        if evidence is not None:
            for name in ('old_frame', 'fresh_frame'):
                projected[name] = _fields(evidence.get(name), ('revision', 'native_revision', 'date_raw'))
            for name in ('old_connection', 'fresh_connection'):
                projected[name] = _fields(evidence.get(name), ('bridge_pid', 'connection_generation'), positive=True)
        while _size(projected) > JSON_LIMIT and projected.get('second_error'):
            value = projected['second_error']
            projected['second_error'], _ = _text(value, max(0, len(value.encode('utf-8'))//2))
            projected['second_error_truncated'] = projected['evidence_truncated'] = True
        if _size(projected) > JSON_LIMIT:
            return {'schema':'xar.campaign-root-readonly-retry-diagnostic/v1',
                'diagnostic_only':True, 'status':'evidence_absent', 'retry_authorized':False,
                'evidence_meaning':'projection_unavailable; retry_entry_or_attempt_unknown'}
        return projected
    except Exception:
        # Optional observability must not replace the original error/diagnostic.
        return None
