"""Exact two-leaf Source25 transform; no filesystem or runtime mutation."""
import hashlib

BASE_COMMIT = "9b791aae9bb1314162aa5cab923e6cca2892e6d8"
PREFIX = "ck3_autonomous_player/src/xar_autoplayer/"
SCHEDULE = PREFIX + "ordinary_sway_schedule_v1.py"
FORMAL = PREFIX + "sway_formal_consumer.py"
HELPER = PREFIX + "reused_sway_opportunity_v1.py"


def _replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError("M6 exact source anchor mismatch")
    return text.replace(old, new, 1)


def transform_sources(inputs, helper_bytes):
    """Root must bind inputs to the declared canonical Source25 tree."""
    if set(inputs) != {SCHEDULE, FORMAL} or not isinstance(helper_bytes, bytes):
        raise ValueError("M6 source input shape mismatch")
    result = {}
    schedule = inputs[SCHEDULE].decode("utf-8")
    schedule = _replace_once(schedule, "from collections.abc import Mapping\n",
        "from collections.abc import Mapping\n\nfrom .reused_sway_opportunity_v1 import reused_sway_observation_gap_v1\n")
    schedule = _replace_once(schedule,
        "        if not terminal_observed:\n            target = resolved.get(\"target_character_id\")\n",
        "        # Reuse records an observation gap, never an observed end. A fresh\n"
        "        # ordinary target query still owns empty-slot/legal admission.\n"
        "        reused_gap = reused_sway_observation_gap_v1(\n"
        "            resolved, actor_character_id=actor, date_raw=date)\n"
        "        if not terminal_observed and reused_gap is None:\n"
        "            target = resolved.get(\"target_character_id\")\n")
    schedule = _replace_once(schedule,
        '            return {"job": None, "reason": "original_terminal_already_observed", "state": current}\n'
        '        if current.get("last_terminal_action_id") != resolved.get("action_id"):\n',
        '            return {"job": None, "reason": ("original_storage_reused_terminal_unknown"\n'
        '                    if reused_gap is not None else "original_terminal_already_observed"), "state": current}\n'
        '        if terminal_observed and current.get("last_terminal_action_id") != resolved.get("action_id"):\n')
    formal = inputs[FORMAL].decode("utf-8")
    formal = _replace_once(formal, "from .environment import write_json_atomic\n",
        "from .environment import write_json_atomic\nfrom .reused_sway_opportunity_v1 import fresh_empty_sway_slot_after_reuse_v1\n")
    formal = _replace_once(formal,
        '    terminal = resolved.get("terminal_intervention")\n'
        '    if (not isinstance(terminal, Mapping)\n'
        '            or terminal.get("instance_terminal_outcome_observed") is not True):\n',
        '    terminal = resolved.get("terminal_intervention")\n'
        '    reused_gap = fresh_empty_sway_slot_after_reuse_v1(resolved, readback)\n'
        '    if reused_gap is not None:\n'
        '        # Keep the lost old end UNKNOWN; the new UUID gets no old gain.\n'
        '        # consume_sway_private_once already joined this fresh read to its\n'
        '        # current frame and still calls unchanged should_submit_sway.\n'
        '        return {**followup, "decision": "repeat_selected_target",\n'
        '                "previous_instance_observation_gap": reused_gap,\n'
        '                "previous_instance_terminal_observed": False}\n'
        '    if (not isinstance(terminal, Mapping)\n'
        '            or terminal.get("instance_terminal_outcome_observed") is not True):\n')
    result[SCHEDULE] = schedule.encode("utf-8")
    result[FORMAL] = formal.encode("utf-8")
    result[HELPER] = helper_bytes
    for path, data in result.items():
        compile(data, path, "exec")
    return result


def pin(data):
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
