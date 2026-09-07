#!/usr/bin/env python3
"""Purpose-split tests for chancellor-task manager recovery drains."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))

import zg361_phase2_promotion_manager_chancellor_contracts as chancellor
import zg361_phase2_promotion_source_production_entry as production
from test_zg361_phase2_manager_recovery_interrupts import (
    _context,
    _manager_contract,
    _scope,
)


REPORT = Path("Z:/ck3_mod_rewrite/_runtime/p2r284restore/report.json")
REPORT_SHA256 = (
    "FD684169835F1A4FDAD7AA6250379F09973C7655ABE26F29E37572FD96A21FEC"
)
EVENT_SOURCE_SHA256 = (
    "EAF95612E4AEC6BF0CEDBC1ACA1C66C8087DD280BC42A60296F824437A5A46EB"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _extract_block(source: str, header: str) -> str:
    header_index = source.index(header)
    open_index = source.index("{", header_index + len(header))
    depth = 0
    for index in range(open_index, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[header_index:index + 1]
    raise AssertionError(f"unterminated source block: {header}")


def _ck3_source(relative_path: str) -> Path | None:
    for game_root in (ROOT, ROOT.parent):
        candidate = game_root / "Crusader Kings III" / "game" / relative_path
        if candidate.is_file():
            return candidate
    return None


class ManagerRecoveryChancellorInterruptTests(unittest.TestCase):
    def test_shortened_truce_notice_matches_exact_r284_shape(self) -> None:
        event_key = "chancellor_task.1002"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=207,
            date_raw=53209248,
            player=32904,
            scopes=[
                _scope("councillor", "character", 29346),
                _scope("councillor_liege", "character", 32904),
                _scope("target", "character", 34838),
            ],
            native_option_indices=(0,),
        )
        checks = production._known_interrupt_checks(
            snapshot={"date_raw": 53209248, "active_event": {"option_count": 1}},
            event={"event_instance_id": 207},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS[event_key],
            chancellor.MANAGER_CHANCELLOR_TIMELINE_CONTRACTS[event_key],
        )
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)
        self.assertEqual(contract["max_occurrences"], 1)

        for scope_index, character_id, failed_check in (
            (0, 32904, "scope:councillor:unique_third_party"),
            (2, 32904, "scope:target:unique_third_party"),
            (2, 29346, "scope:target:differs_from"),
        ):
            drifted = copy.deepcopy(context)
            scope_name = str(drifted["saved_scopes"][scope_index]["name"])
            drifted["saved_scopes"][scope_index] = _scope(
                scope_name, "character", character_id
            )
            drift_checks = production._known_interrupt_checks(
                snapshot={
                    "date_raw": 53209248,
                    "active_event": {"option_count": 1},
                },
                event={"event_instance_id": 207},
                context=drifted,
                event_key=event_key,
                contract=contract,
            )
            self.assertFalse(drift_checks[failed_check])

    def test_r284_checkpoint_matches_registered_contract(self) -> None:
        if not REPORT.is_file():
            self.skipTest("R284 restore report is not present on this machine")
        self.assertEqual(_sha256(REPORT), REPORT_SHA256)
        payload = json.loads(REPORT.read_text(encoding="utf-8-sig"))
        unexpected = payload["entry"]["unexpected_event"]
        contract = _manager_contract("chancellor_task.1002", player=32904)
        checks = production._known_interrupt_checks(
            snapshot=unexpected["snapshot"],
            event=unexpected["event"],
            context=unexpected["query"],
            event_key="chancellor_task.1002",
            contract=contract,
        )
        self.assertTrue(all(checks.values()), checks)

    def test_vanilla_source_has_one_unavoidable_truce_cancellation(self) -> None:
        source = _ck3_source(
            "events/councillor_task_events/chancellor_task_events.txt"
        )
        if source is None:
            self.skipTest("CK3 1.19.0.6 source tree is unavailable")
        self.assertEqual(_sha256(source), EVENT_SOURCE_SHA256)
        block = _extract_block(
            source.read_text(encoding="utf-8-sig"),
            "chancellor_task.1002 =",
        )
        self.assertEqual(len(re.findall(r"(?m)^\toption\s*=\s*\{", block)), 1)
        normalized = " ".join(block.split())
        for required in (
            "save_scope_as = target",
            "name = chancellor_task.1002.a",
            "scope:target = { cancel_truce_one_way = root }",
        ):
            self.assertIn(required, normalized)


if __name__ == "__main__":
    unittest.main()
