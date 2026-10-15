"""Known native schema compatibility preserves submission/readback boundaries."""
import copy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.army_commander_assignment import (
    commander_assignment_readback_v1,
    normalize_army_commander_assignment_v1,
)


def submitted_result(schema="ck3_12004_army_commander_assignment_v1"):
    # Compact shape of the N42 closed P03 original assignment receipt. These
    # constants are a parser fixture, not evidence of an applied commander.
    return {
        "step": "assign-army-commander-v1-army-318767248-to-character-34232",
        "accepted": True, "status": "submitted_verification_pending", "read_only": False,
        "command_sequence": 1, "snapshot_revision": 3, "date_raw": 53327184,
        "army_commander_assignment": {
            "schema": schema, "status": "submitted", "snapshot_revision": 3, "date_raw": 53327184,
            "army_id": 318767248, "native_carmy_id": 285212887, "owner_character_id": 40526,
            "requested_commander_character_id": 34232, "prior_commander_character_id": None,
            "final_eligibility_observable": True, "can_assign": True,
            "native_command_validation_observable": True, "native_command_valid": True,
            "command_submitted": True, "verification_pending": True, "unavailable_reason": None,
        },
    }


def normalize(result):
    return normalize_army_commander_assignment_v1(
        result, expected_army_id=318767248, expected_commander_character_id=34232,
        expected_snapshot_revision=3, expected_date_raw=53327184)


@pytest.mark.parametrize("schema", ["ck3_12003_army_commander_assignment_v1", "ck3_12004_army_commander_assignment_v1"])
def test_known_schema_keeps_assignment_unverified_until_independent_readback(schema):
    assignment = normalize(submitted_result(schema))
    assert assignment["schema"] == schema and assignment["verification_pending"] is True
    readback = {"status": "available", "date_raw": 53327184, "snapshot_revision": 4,
                "army_id": 318767248, "native_carmy_id": 285212887, "owner_character_id": 40526,
                "current_commander": {"status": "available", "character_id": 34232}}
    assert commander_assignment_readback_v1(assignment, readback, expected_date_raw=53327184)["verified"] is True
    wrong = copy.deepcopy(readback)
    wrong["current_commander"]["character_id"] = 34233
    assert commander_assignment_readback_v1(assignment, wrong, expected_date_raw=53327184)["verified"] is False


@pytest.mark.parametrize("key,value", [
    ("schema", "ck3_12005_army_commander_assignment_v1"), ("schema", None),
    ("army_id", 318767249), ("requested_commander_character_id", 34233),
    ("status", "applied"), ("command_submitted", False), ("verification_pending", False),
    ("can_assign", False), ("native_command_valid", False),
])
def test_schema_compatibility_does_not_relax_native_guards(key, value):
    result = submitted_result()
    result["army_commander_assignment"][key] = value
    with pytest.raises(ValueError):
        normalize(result)


@pytest.mark.parametrize("key,value", [("snapshot_revision", 4), ("date_raw", 53327185), ("accepted", False)])
def test_schema_compatibility_does_not_relax_source_envelope(key, value):
    result = submitted_result()
    result[key] = value
    with pytest.raises(ValueError):
        normalize(result)
