"""Source-derived per-Title outer request inputs for actual291B3B0.

The wrapper receives Model and a composed PC, then appends an owned copy to
the inline Model+10 container at literal100000. These are projected requests;
this module does not write a Model or reconstruct its historical aggregate.
"""
from __future__ import annotations

from collections.abc import Mapping

from .battle_context_source_inputs_contract import _integer
from .battle_person_first_title_vector_12004 import (
    FIELD_NAME as FIRST_VECTOR_FIELD,
    normalize_person_first_title_vector_12004,
)
from .battle_person_local_titles_12004 import (
    FIELD_NAME as LOCAL_TITLES_FIELD,
    compose_local_title_composer_blocks_from_current_source_inputs_12004,
    normalize_person_local_titles_12004,
)

OUTER_WEIGHT_Q100000 = 100000  # Actual291B4AD MOV R8D,100000.


def _context(section, leaf, field):
    if not isinstance(section, Mapping):
        raise ValueError("Required native input unavailable: " + field)
    character = _integer(section.get("character_id"), "current_person_state.character_id", 32, unsigned=True)
    if leaf is None or leaf["character_id"] != character:
        raise ValueError(field + " full CharacterID join unavailable or mismatched")
    model = leaf["selected_model_identity"]
    try:
        inline_destination = hex(int(model, 16) + 0x10)
    except (TypeError, ValueError) as error:
        raise ValueError("Required native input unavailable: selected_model_identity") from error
    return model, inline_destination


def _request(model, destination, family, phase, native_index, identity, block):
    return {
        "source_family": family,
        "phase": phase,
        "native_index": native_index,
        "title_identity": identity,
        "selected_model_identity": model,
        "inline_destination_identity": destination,
        "property_block": block,
        "weight_q100000": OUTER_WEIGHT_Q100000,
        "actual_model_write_performed": False,
        "full_helper_ready": False,
    }


def project_person_first_title_composer_outer_requests_12004(
        section, phase=None, native_index=None):
    """Project zero or one unit request per observed composer occurrence.

    Primary and supplemental readiness are independent. A selected complete
    composer can be used while another occurrence or source family is partial.
    """
    if not isinstance(section, Mapping):
        raise ValueError("Required native input unavailable: " + FIRST_VECTOR_FIELD)
    leaf = normalize_person_first_title_vector_12004(section.get(FIRST_VECTOR_FIELD))
    model, destination = _context(section, leaf, FIRST_VECTOR_FIELD)
    selected = phase is not None or native_index is not None
    if selected:
        if phase not in ("phase_a", "phase_b") or native_index is None:
            raise ValueError("A selected Title occurrence requires phase and native_index")
        index = _integer(native_index, FIRST_VECTOR_FIELD + ".native_index", 32, unsigned=True)
        rows = leaf[phase]["rows"]
        if index >= len(rows):
            raise ValueError("Required native input unavailable: selected Title occurrence")
        occurrences = [(phase, rows[index])]
    else:
        if not (leaf["producer_ready"] and leaf["family_input_ready"] and leaf["composer_ready"]):
            raise ValueError("Required native input unavailable: " + (leaf["reason"] or FIRST_VECTOR_FIELD))
        occurrences = [(name, row) for name in ("phase_a", "phase_b")
                       for row in leaf[name]["rows"]]
    from ..simulation.battle_person_after_gated_tail_12003 import fold_after_gated_blocks_12003
    requests = []
    for name, row in occurrences:
        if not row["ready"]:
            raise ValueError("Required native input unavailable: " + (row["reason"] or FIRST_VECTOR_FIELD))
        if row["emitted"] is False:
            continue
        element = row["element"]
        if (row["emitted"] is not True or element is None
                or not element["input_ready"] or not element["composer"]["ready"]):
            raise ValueError("Required native input unavailable: emitted Title composer")
        block = fold_after_gated_blocks_12003([
            {"keys_count": pc["count_i32"],
             "keys_u16": pc["properties"]["keys_u16"],
             "values_q64": pc["properties"]["values_q64"]}
            for pc in element["composer"]["source_pcs"]
        ])
        # Actual291ED6A skips this caller's outer wrapper for count0.
        if block["keys_count"] != 0:
            requests.append(_request(model, destination, "first_title_vector",
                                     name, row["native_index"], element["identity"], block))
    return tuple(requests)


def project_person_local_title_composer_outer_requests_12004(
        section, native_index=None):
    """Reuse the local family's already observed composer and caller admission."""
    if not isinstance(section, Mapping):
        raise ValueError("Required native input unavailable: " + LOCAL_TITLES_FIELD)
    leaf = normalize_person_local_titles_12004(section.get(LOCAL_TITLES_FIELD))
    model, destination = _context(section, leaf, LOCAL_TITLES_FIELD)
    blocks = compose_local_title_composer_blocks_from_current_source_inputs_12004(
        section, native_index=native_index)
    requests = []
    for row in blocks:
        if row["outer_append_demanded"]:
            index = row["native_index"]
            identity = leaf["rows"][index]["resolution"]["selected_identity"]
            requests.append(_request(model, destination, "local_titles", None,
                                     index, identity, row["property_block"]))
    return tuple(requests)
