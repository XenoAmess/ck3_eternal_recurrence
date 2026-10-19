"""Future outer-control receipts only; no I/O, Native/Service clocks or policy."""
from __future__ import annotations

from contextvars import ContextVar
from functools import wraps
import math

SCHEMA = 'xar.ck3.full-existing-rpc-rows/v1'
TOOLS = {'ck3_auto_turn': 'AUTO', 'root_current_runtime_metrics': 'MET',
         'ck3_take_semantic_snapshot_private_v1': 'SEM', 'ck3_save_checkpoint': 'SAVE'}
_CURRENT = ContextVar('xar_full_existing_rpc_rows_v1', default=None)


def _number(value):
    return type(value) in (int, float) and math.isfinite(value)


class _Rows:
    def __init__(self, sequence):
        self.sequence = sequence
        self.rows = set()
        self.intervals = []
        self.union_available = True
        self.invalid_elapsed = self.duplicates = 0
        self.tools = {key: {'count': 0, 'elapsed_seconds_sum': 0.0,
                            'error_count': 0, 'client_error_count': 0}
                      for key in TOOLS.values()}

    def record(self, request, row, mono):
        if not isinstance(request, dict) or not isinstance(row, dict):
            return
        sequence, category = request.get('sequence'), TOOLS.get(request.get('tool'))
        if type(sequence) is not int or sequence <= 0 or category is None or row.get('request') != request:
            return
        if sequence in self.rows:
            self.duplicates += 1
            return
        self.rows.add(sequence)
        item = self.tools[category]
        item['count'] += 1
        client_error = row.get('client_error') is not None
        result = row.get('result')
        item['client_error_count'] += int(client_error)
        item['error_count'] += int(client_error or (isinstance(result, dict) and result.get('is_error') is True))
        elapsed = row.get('elapsed_seconds')
        if not _number(elapsed) or elapsed < 0:
            self.invalid_elapsed += 1
            self.union_available = False
            return
        item['elapsed_seconds_sum'] += elapsed
        if not _number(mono) or mono < 0 or not _number(mono + elapsed):
            self.union_available = False
            return
        # Endpoint derives from the original Queue's existing mono+elapsed.
        # Merge overlaps, including identical intervals; never add nested time.
        start, end = mono, mono + elapsed
        merged = []
        for left, right in self.intervals:
            if right < start:
                merged.append((left, right))
            elif end < left:
                merged.append((start, end))
                start, end = left, right
            else:
                start, end = min(start, left), max(end, right)
        merged.append((start, end))
        if len(merged) <= 2048:
            self.intervals = merged
        else:
            self.union_available = False
            self.intervals = []

    def fields(self):
        total = sum(item['elapsed_seconds_sum'] for item in self.tools.values())
        union = sum(end-start for start, end in self.intervals) if self.union_available else None
        return {'full_rpc_rows_v1': {
            'schema': SCHEMA, 'control_sequence': self.sequence,
            'source': 'existing per-row wall: normal Queue includes model_dump; resident row ends before model_dump; excludes later response write/relay/classifier',
            'interval_source': 'existing Queue monotonic start plus existing elapsed_seconds; no new row clock',
            'tools': {key: dict(value) for key, value in self.tools.items()},
            'row_count': len(self.rows), 'duplicate_rows_ignored': self.duplicates,
            'invalid_elapsed_rows': self.invalid_elapsed,
            'elapsed_seconds_sum': total, 'interval_union_seconds': union,
            'overlap_seconds': max(0.0, total-union) if union is not None else None,
            'zero_day_rows_included': True, 'error_rows_included': True,
            'native_only': False, 'CPU_attribution': None}}


def full_rows_v1(*, enabled=False):
    """Disabled returns the original coroutine, with no row clocks or I/O."""
    if type(enabled) is not bool:
        raise ValueError('explicit full-row timing boolean required')
    def decorate(method):
        if not enabled:
            return method
        @wraps(method)
        async def measured(self, session, request, path):
            arguments = request.get('arguments') if isinstance(request, dict) else None
            if (not isinstance(request, dict) or request.get('command') != 'full_loop'
                    or type(request.get('sequence')) is not int
                    or not isinstance(arguments, dict)
                    or type(arguments.get('max_turns')) is not int
                    or not 1 <= request['arguments']['max_turns'] <= 30):
                return await method(self, session, request, path)
            active = _Rows(request['sequence'])
            token = _CURRENT.set(active)
            try:
                self._full_rows_failed_v1 = None
                return await method(self, session, request, path)
            except BaseException:
                try:
                    self._full_rows_failed_v1 = (request['sequence'], active.fields())
                except Exception:
                    pass
                raise
            finally:
                _CURRENT.reset(token)
        return measured
    return decorate


def record_existing_rpc_row_v1(request, row, mono):
    active = _CURRENT.get()
    if active is not None:
        try:
            active.record(request, row, mono)
        except Exception:
            active.union_available = False


def current_full_row_fields_v1():
    active = _CURRENT.get()
    try:
        return {} if active is None else active.fields()
    except Exception:
        return {}


def failed_full_row_fields_v1(queue, request):
    try:
        value = getattr(queue, '_full_rows_failed_v1', None)
        if (request.get('command') == 'full_loop' and isinstance(value, tuple)
                and value[0] == request.get('sequence')):
            return value[1]
    except Exception:
        pass
    return {}


def batch_timing_fields_v1(result, wall):
    """Copy scalars from the already validated small FULL result, no body reads."""
    try:
        summary = result.get('full_rpc_rows_v1')
        fields = dict(wall)
        if not isinstance(summary, dict) or summary.get('schema') != SCHEMA:
            return fields
        tools = summary.get('tools')
        if not isinstance(tools, dict) or set(tools) != set(TOOLS.values()):
            return fields
        for item in tools.values():
            if (set(item) != {'count', 'elapsed_seconds_sum', 'error_count', 'client_error_count'}
                    or any(type(item[k]) is not int or not 0 <= item[k] <= 10000
                           for k in ('count', 'error_count', 'client_error_count'))
                    or not _number(item['elapsed_seconds_sum']) or item['elapsed_seconds_sum'] < 0):
                return fields
        union = summary.get('interval_union_seconds')
        nanoseconds = fields.get('full_wall_ns')
        elapsed = nanoseconds / 1e9 if type(nanoseconds) is int and nanoseconds >= 0 else None
        if summary.get('control_sequence') != fields.get('full_timing_control_sequence'):
            return fields
        fields['full_rpc_rows_v1'] = summary
        fields['full_wall_minus_rpc_union_seconds'] = (
            elapsed-union if _number(elapsed) and _number(union) and elapsed >= union else None)
        fields['full_wall_residual_attribution'] = None
        return fields
    except Exception:
        return dict(wall)
