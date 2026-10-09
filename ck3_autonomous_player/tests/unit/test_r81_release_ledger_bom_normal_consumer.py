"""Root-only FIRST for the actual small R81 release ledger BOM failure.

Only a private byte copy is consumed. The normal release planner and its
production reader are real; the paused planning frame is a fixture seam.
"""
from __future__ import annotations

import codecs
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from xar_autoplayer.prisoner_release_formal_consumer import (
    _LEDGER, plan_release_formal, read_release_ledger,
)


def test_actual_r81_bom_release_ledger_is_consumed_by_normal_plan(tmp_path):
    capture = Path(os.environ["XAR_R81_RELEASE_LEDGER_CAPTURE"])
    original_bytes = capture.read_bytes()
    assert len(original_bytes) == 44935
    assert original_bytes.startswith(codecs.BOM_UTF8)
    # Reproduce the actual legacy decoder error from the same captured bytes.
    with pytest.raises(json.JSONDecodeError, match="Unexpected UTF-8 BOM"):
        json.loads(original_bytes.decode("utf-8"))

    fixture_state = tmp_path / "private-release-state"
    fixture_state.mkdir()
    copy = fixture_state / _LEDGER
    copy.write_bytes(original_bytes)
    actual_value = json.loads(original_bytes.decode("utf-8-sig"))
    ledger = read_release_ledger(fixture_state)
    assert ledger == {"pending": actual_value["pending"],
                      "resolved": actual_value.get("resolved")}
    pending = ledger["pending"]
    # These are synthetic outer planning-frame inputs, not a new game read.
    snapshot = {"paused": True, "map_ready": True,
                "played_character": {"character_id": 29829},
                "native_revision": (pending.get("pre_native_revision", 1)
                                    if isinstance(pending, dict) else 1),
                "date_raw": (pending.get("pre_date_raw", 53288600)
                             if isinstance(pending, dict) else 53288600),
                "active_event": None, "pending_character_interaction": None,
                "active_wars": [], "native_command_history": []}
    planned = {"plan": {"phase": "fixture-normal-life",
                         "selected_step": "life-advance"}}
    driver = SimpleNamespace(state_dir=fixture_state,
                             allow_private_prisoner_ransom_action=True)
    consumed = plan_release_formal(driver, planned, snapshot)
    assert isinstance(consumed["plan"], dict)
    if isinstance(pending, dict):
        assert consumed["plan"]["prisoner_release_pending"] == pending
    else:
        assert consumed == planned
    # Production readers must not rewrite either the BOM or the opaque data.
    assert copy.read_bytes() == original_bytes
    output = os.environ.get("XAR_R81_RELEASE_LEDGER_BOM_FIRST_OUTPUT")
    if output:
        Path(output).write_text(json.dumps({
            "schema": "xar.r81-release-ledger-bom-normal-consumer.v1",
            "capture": str(capture), "capture_bytes": len(original_bytes),
            "prefix3_hex": original_bytes[:3].hex(),
            "legacy_json_bom_error_reproduced": True,
            "production_reader_consumed": True,
            "normal_plan_consumed": True, "private_copy_bytes_unchanged": True,
            "pending_present": isinstance(pending, dict),
            "resolved_present": isinstance(ledger["resolved"], dict),
            "native_calls": 0, "game_calls": 0, "capability_credit": 0,
            "frame_origin": "synthetic outer planning frame",
        }, indent=2) + "\n", encoding="utf-8")
