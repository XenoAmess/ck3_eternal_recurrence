"""Refine actual halt diagnostics into brief display reasons; frozen v3 intact.

Root-only display metadata. No action/cycle credit, Game/SDK/OBS operation,
process restart, Driver/SAVE/video read, or new incident during refinement.
"""
import argparse
import hashlib
import importlib.util
from pathlib import Path
import sys

SOURCE = Path(__file__).with_name('runtime_repair_status_v2_all_stops.py')
if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != 'ef3944da5fe25a30578b241b0b2a8a53a423c569f6baf3813f1a64c25291e446':
    raise ValueError('Frozen all-stops observer changed')
spec = importlib.util.spec_from_file_location('repair_status_v3_exact_base', SOURCE)
v3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v3)
core = v3.core


def diagnostic_reason(row):
    """Extract real native_error even when the enclosing result is is_error."""
    wrapper = row.get('result')
    if not isinstance(wrapper, dict):
        return None
    body = wrapper.get('structured_content', wrapper.get('structuredContent'))
    if not isinstance(body, dict):
        return None
    diagnostics = body.get('diagnostics')
    rejection = diagnostics.get('native_command_rejection') if isinstance(diagnostics, dict) else None
    if not isinstance(rejection, dict):
        return None
    error, step = rejection.get('native_error'), rejection.get('native_step')
    request_id = rejection.get('native_request_id')
    if (wrapper.get('is_error', wrapper.get('isError')) is not True
            or not isinstance(error, str) or not error.strip()
            or not isinstance(step, str) or not step
            or not isinstance(request_id, str) or not request_id):
        return None
    raw = error.strip()
    if step == 'query-campaign-root-context-v1' and raw == 'paused application-main boundary is not ready':
        brief = '暂停读取边界未就绪，自动推进暂停'
        mapping = 'campaign_root_paused_boundary_not_ready'
    else:
        brief = '自动推进受阻：' + ' '.join(raw.split())[:80]
        mapping = 'unknown_native_error_preserved'
    return brief, {'mapping': mapping, 'native_request_id': request_id,
        'native_step': step, 'native_error': error,
        'json_pointer': ['result', 'structured_content', 'diagnostics',
                         'native_command_rejection', 'native_error'],
        'diagnostic_only': rejection.get('diagnostic_only'),
        'Native_business_result_or_failure_cause_beyond_text_inferred': False}


class ReasonPublisher(v3.AllStopsPublisher):
    def refine_current(self):
        state = self.state()
        if state is None or state.get('phase') not in ('repairing', 'repair_applied_waiting_for_progress'):
            return None
        source_pin = state.get('halt_receipt') or {}
        halt_path = Path(source_pin.get('path', '')).resolve(strict=True)
        if core.pin(halt_path) != source_pin:
            raise ValueError('Original immutable halt receipt changed')
        halt = core.read(halt_path)
        original = halt.get('original_response')
        if not isinstance(original, str):
            # SDK custody and recording-only events do not have a Native AUTO
            # rejection. Keep their already truthful reasons; never invent
            # a gameplay stop from an OBS waiting state.
            return None
        original_path = Path(original).resolve(strict=True)
        if original_path.parent != self.outbox.resolve():
            raise ValueError('Original failed AUTO must be in the bound SDK outbox')
        row = core.read(original_path)
        if row.get('request') != state.get('original_request'):
            raise ValueError('Original failed AUTO request differs from this incident')
        extracted = diagnostic_reason(row)
        if extracted is None:
            return None
        brief, evidence = extracted
        evidence['original_response'] = core.pin(original_path)
        if state.get('pause_reason') == brief and state.get('reason_evidence') == evidence:
            return {'status': 'SAME_INCIDENT_REASON_ALREADY_REFINED', 'incident_id': state['incident_id']}
        audit_path = self.store / (state['incident_id'] + '-REASON-REFINED-' +
            evidence['original_response']['sha256'][:12] + '.json')
        before = state['pause_reason']
        audit = {'schema': 'xar.runtime-repair-reason-refinement/v1',
            'at_utc': core.utc().isoformat(), 'binding': self.binding,
            'incident_id': state['incident_id'], 'original_current_state': core.pin(self.current),
            'before_pause_reason': before, 'after_pause_reason': brief, 'reason_evidence': evidence,
            'new_incident_created': False, 'new_business_credit': 0, 'new_cycle_credit': 0,
            'Game_MCP_OBS_Desktop_calls': 0, 'phase_preserved': state['phase']}
        core.atomic(audit_path, audit)
        state.update(pause_reason=brief, reason_evidence=evidence,
                     reason_refinement_version=4, reason_refinement=core.pin(audit_path))
        relay = self.emit(state)
        return {'status': 'SAME_INCIDENT_REASON_REFINED', 'incident_id': state['incident_id'],
                'pause_reason': brief, 'audit': core.pin(audit_path), 'relay': relay,
                'new_incident_created': False, 'new_business_credit': 0}

    def observe_halt(self):
        super().observe_halt()
        state = self.state()
        incident = (state or {}).get('incident_id')
        if incident is None or incident == getattr(self, '_reason_incident_seen', None):
            return
        self._reason_incident_seen = incident
        self.refine_current()


def main():
    if 'refine-current' in sys.argv[1:]:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument('--session', type=Path, required=True)
        parser.add_argument('--sdk-prefix', required=True)
        parser.add_argument('command', choices=['refine-current'])
        args = parser.parse_args()
        publisher = ReasonPublisher(args.session, args.sdk_prefix)
        try:
            with core.writer_lock(publisher.store):
                result = publisher.refine_current()
            if result is None:
                raise ValueError('No matching original Native diagnostic in the active repair incident')
            import json
            print(json.dumps(result, ensure_ascii=False), flush=True)
        finally:
            publisher.close()
        return
    core.Publisher = ReasonPublisher
    try:
        core.main()
    finally:
        for publisher in v3.v2.ACTIVE_PUBLISHERS:
            publisher.close()


if __name__ == '__main__':
    main()
