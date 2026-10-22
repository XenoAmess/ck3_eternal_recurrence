"""Select source-defined native event options; no OCR or rendered-order guesses."""
from __future__ import annotations

from dataclasses import dataclass
import re

from acceptance_contract import Frame, Object, array, field, integer, mapping, native_id, require, text
from living_artifacts_core import render_core_events
from ck3_text_projection import blocks


def source_option_index(event_key: str, option_key: str) -> int:
    source = render_core_events()
    definitions = blocks(source)
    selected = [item for item in definitions if item.key == event_key]
    require(len(selected) == 1, "Unique generated event definition required")
    event = selected[0]
    options = [item for item in definitions if item.key == "option" and event.opening < item.start < event.end]
    found: list[int] = []
    for index, option in enumerate(options):
        name = re.match(r"\s*name\s*=\s*([A-Za-z0-9_.]+)\b", source[option.opening + 1:option.end - 1])
        require(name is not None, "Generated event option lacks its explicit first name")
        if name is not None and name[1] == option_key:
            found.append(index)
    require(len(found) == 1, "Unique generated option key required")
    return found[0]


@dataclass(frozen=True)
class ManagementChoice:
    event_key: str
    option_key: str
    instance_id: int
    native_option_index: int
    rendered_index: int
    resolved_name: str

    def arguments(self) -> Object:
        return {"event_instance_id": self.instance_id, "option_number": self.native_option_index + 1}


def management_choice(value: object, *, frame: Frame, instance_id: int, event_key: str, option_key: str) -> ManagementChoice:
    instance_id = integer(instance_id, "requested native event instance", 1, 2**31 - 1)
    require(event_key in ("xalw.10", "xalw.11", "xalw.12"), "Only real management events belong to this route")
    row = mapping(field(value, "current_event_window_context"), "actual native event window")
    require(row.get("schema") == "current-event-window-context-v1" and integer(field(row, "schema_version"), "event schema", 1, 1) == 1 and
            row.get("status") == "available" and row.get("event_definition_key") == event_key and
            integer(field(row, "current_event_instance_id"), "native event instance", 1, 2**31 - 1) == instance_id and
            integer(field(row, "date_raw"), "event date", 1) == frame.date_raw and
            integer(field(row, "snapshot_revision"), "event revision", 1) == frame.native_revision and
            integer(field(row, "window_match_count"), "actual window count", 1, 1) == 1,
            "Actual event identity/date/window is unavailable or changed")
    require(field(field(row, "readiness"), "option_presentation_ready") is True, "Native displayed options are unavailable")
    root = field(row, "root_scope")
    identity = field(root, "typed_identity")
    require(field(root, "status") == "available" and field(root, "type_key") == "character" and
            field(identity, "status") == "available" and field(identity, "kind") == "character" and
            native_id(field(identity, "character_id"), "event root actor") == frame.player_id,
            "Management event belongs to another actual actor")
    source = field(value, "source")
    require(field(source, "paused") is True and integer(field(source, "date_raw"), "query source date", 1) == frame.date_raw and
            integer(field(source, "native_revision"), "query native revision", 1) == frame.native_revision,
            "Management query lost its paused frame")
    desired = source_option_index(event_key, option_key)
    available = array(field(row, "options"), "actual displayed options")
    require(len(available) <= 64, "Native event option list exceeds its bound")
    found: list[ManagementChoice] = []
    seen: set[int] = set()
    for rendered, raw in enumerate(available):
        option = mapping(raw, "actual option")
        index = integer(field(option, "native_option_index"), "native option index", 0, 63)
        require(index not in seen and integer(field(option, "rendered_index"), "actual displayed index", 0, 63) == rendered and
                field(option, "shown") is True and type(field(option, "enabled")) is bool,
                "Displayed option identity/order/types differ")
        seen.add(index)
        if index == desired:
            require(option["enabled"] is True, "Requested original management choice is disabled")
            found.append(ManagementChoice(event_key, option_key, instance_id, index, rendered, text(field(option, "resolved_name"), "displayed option name")))
    require(len(found) == 1, "Requested original management choice is not displayed")
    return found[0]
