"""Count verified registry event selections in the retained factual lineage."""

from collections.abc import Mapping, Sequence

from ..bridge.event_contract import parse_event_option_step
from ..bridge.event_window_context_contract import QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP


def observed_event_occurrences_v1(commands, *, event_key, played_character_id, character_id_reader):
    """Return unknown for an unbound selection; never count reads as occurrences.

    Native history plus expanded Service rows may contain the same selection
    twice. The original instance and starting public frame identify one choice.
    This counts observed selections, not disease acquisition or a cure.
    """
    if not isinstance(commands, Sequence) or isinstance(commands, (str, bytes)):
        return {"status": "unavailable", "count": None, "reason": "event_history_unavailable"}
    queries = {}
    for row in commands:
        if not isinstance(row, Mapping) or row.get("ok") is not True:
            continue
        result = row.get("result")
        if not isinstance(result, Mapping) or result.get("step") != QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP:
            continue
        context = result.get("current_event_window_context")
        if (result.get("accepted") is not True or not isinstance(context, Mapping)
                or context.get("status") != "available"):
            continue
        instance = context.get("current_event_instance_id")
        native = context.get("snapshot_revision")
        public = result.get("queried_revision")
        snapshot_id = result.get("queried_snapshot_id")
        key = context.get("event_definition_key")
        actor = character_id_reader(context.get("root_scope"))
        if (type(instance) is not int or instance <= 0 or type(native) is not int or native <= 0
                or type(public) is not int or public < 0 or not isinstance(snapshot_id, str) or not snapshot_id
                or not isinstance(key, str) or not key or actor is None
                or result.get("current_event_instance_id") != instance
                or result.get("queried_native_revision") != native
                or result.get("snapshot_revision") != native
                or result.get("date_raw") != context.get("date_raw")):
            continue
        frame = instance, snapshot_id, public
        identity = key, actor
        if frame in queries and queries[frame] != identity:
            return {"status": "unavailable", "count": None, "reason": "conflicting_event_query_identity"}
        queries[frame] = identity
    observed = set()
    for row in commands:
        if not isinstance(row, Mapping):
            continue
        command = row.get("command")
        number = parse_event_option_step(command)
        if number is None:
            continue
        result = row.get("result")
        selection = result.get("event_selection") if isinstance(result, Mapping) else None
        if (row.get("ok") is not True or not isinstance(result, Mapping)
                or result.get("accepted") is not True or not isinstance(selection, Mapping)
                or selection.get("status") != "event_instance_advanced"
                or selection.get("postcondition_verified") is not True
                or selection.get("selected_option_number") != number
                or selection.get("selected_native_option_index") != number - 1
                or selection.get("new_event_instance_id") == selection.get("old_event_instance_id")):
            return {"status": "unavailable", "count": None, "reason": "unverified_historical_event_selection"}
        instance = selection.get("old_event_instance_id")
        snapshot_id = selection.get("starting_snapshot_id")
        public = selection.get("starting_revision")
        if (type(instance) is not int or instance <= 0 or not isinstance(snapshot_id, str)
                or type(public) is not int):
            return {"status": "unavailable", "count": None, "reason": "historical_selection_frame_unavailable"}
        frame = instance, snapshot_id, public
        identity = queries.get(frame)
        if identity is None:
            return {"status": "unavailable", "count": None, "reason": "historical_selection_event_identity_unavailable"}
        if identity == (event_key, played_character_id):
            observed.add(frame)
    return {"status": "available", "count": len(observed), "reason": None}
