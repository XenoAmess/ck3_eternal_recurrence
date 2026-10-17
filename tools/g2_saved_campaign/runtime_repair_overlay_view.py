"""Pure future-overlay banner renderer; never changes the running overlay."""
from datetime import datetime
from pathlib import Path


def repair_banner(state, *, session, game_pid, game_creation_filetime, now):
    if not isinstance(state, dict) or state.get('schema') != 'xar.runtime-repair-status/v1':
        return ''
    binding = state.get('binding') or {}
    if (Path(binding.get('session', '')).resolve() != Path(session).resolve()
            or binding.get('game_pid') != game_pid
            or binding.get('game_creation_filetime') != game_creation_filetime):
        return ''
    phase = state.get('phase')
    if phase in ('repairing', 'repair_applied_waiting_for_progress'):
        reason = state.get('pause_reason')
        return str(reason)[:100] + ' · 正在修复中' if isinstance(reason, str) else ''
    if phase != 'resolved' or not isinstance(state.get('expires_at_utc'), str):
        return ''
    try:
        expires = datetime.fromisoformat(state['expires_at_utc'].replace('Z', '+00:00'))
    except ValueError:
        return ''
    if now >= expires or not isinstance(state.get('recovery_proof'), dict):
        return ''
    return str(state.get('repair_message', '修复已完成'))[:160] + ' · 已恢复推进'
