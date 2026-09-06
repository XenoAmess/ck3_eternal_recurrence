#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression tests for the checked-in Simplified Chinese copy ledger."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

from gen_zg361_copy_audit_ledger import (
    INDEX_PATH,
    OUTPUT_ROOT,
    REPO_ROOT,
    build_outputs,
    check_outputs,
    read_events,
)


class CopyAuditLedgerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.expected, cls.index = build_outputs()

    def test_checked_in_ledger_is_current(self) -> None:
        self.assertEqual(check_outputs(self.expected), [])

    def test_scope_is_complete_and_machine_checks_are_green(self) -> None:
        summary = self.index["summary"]
        self.assertEqual(self.index["machine_checks_status"], "pass")
        self.assertEqual(summary["machine_failure_count"], 0)
        self.assertGreater(summary["visible_events"], 600)
        self.assertGreater(summary["final_localization_keys"], 4_900)
        self.assertGreater(summary["visible_option_bindings"], 1_800)
        self.assertEqual(summary["dead_option_loc"]["missing_visible_option_count"], 0)

    def test_inline_hidden_dispatch_events_are_not_player_visible(self) -> None:
        events, duplicates = read_events()
        self.assertEqual(duplicates, [])
        by_key = {event.key: event for event in events}
        inline_hidden = {
            "zg361mg.101",
            "zg361mg.102",
            "zg361mg.103",
            "zg361mg.200",
            "zg361mg.201",
            "zg361mg.202",
            "zg361mg.203",
            "zg361mg.204",
            "zg361mg.250",
        }
        self.assertTrue(all(by_key[key].hidden for key in inline_hidden))
        self.assertEqual(self.index["summary"]["visible_events"], 626)
        self.assertEqual(self.index["summary"]["hidden_events"], 383)

    def test_human_semantic_judgment_is_not_auto_promoted(self) -> None:
        self.assertEqual(self.index["ledger_status"], "review")
        self.assertEqual(self.index["human_semantic_review_status"], "review")
        self.assertEqual(self.index["live_render_validation_status"], "pending")
        manual = [
            item
            for item in self.index["open_items"]
            if item["kind"] == "manual_semantic_review"
        ]
        self.assertEqual(len(manual), 1)
        self.assertEqual(manual[0]["count"], self.index["summary"]["visible_events"])

    def test_shards_are_bounded_and_match_index_hashes(self) -> None:
        self.assertGreater(len(self.index["shards"]), 20)
        for shard in self.index["shards"]:
            path = REPO_ROOT / shard["path"]
            data = path.read_bytes()
            with self.subTest(path=shard["path"]):
                self.assertLessEqual(len(data), 200_000)
                self.assertEqual(len(data), shard["bytes"])
                self.assertEqual(hashlib.sha256(data).hexdigest(), shard["sha256"])

    def test_shards_cover_each_visible_event_and_final_loc_key_once(self) -> None:
        event_keys: list[str] = []
        loc_keys: list[str] = []
        for path in sorted(OUTPUT_ROOT.rglob("*.json")):
            if path == INDEX_PATH:
                continue
            payload = json.loads(path.read_text(encoding="utf-8"))
            if payload["kind"] == "events":
                event_keys.extend(record["event_key"] for record in payload["records"])
            elif payload["kind"] == "localization":
                loc_keys.extend(record["key"] for record in payload["records"])
        self.assertEqual(len(event_keys), self.index["summary"]["visible_events"])
        self.assertEqual(len(event_keys), len(set(event_keys)))
        self.assertEqual(len(loc_keys), self.index["summary"]["final_localization_keys"])
        self.assertEqual(len(loc_keys), len(set(loc_keys)))

    def test_source_inventory_hashes_the_actual_bytes(self) -> None:
        inventory = self.index["source_snapshot"]["files"]
        self.assertGreater(len(inventory), 100)
        for item in inventory:
            path = REPO_ROOT / item["path"]
            with self.subTest(path=item["path"]):
                self.assertEqual(
                    hashlib.sha256(path.read_bytes()).hexdigest(), item["sha256"]
                )
                self.assertEqual(item["authority"]["status"], "pass")

        authority_review = [
            item
            for item in self.index["open_items"]
            if item["kind"] == "authority_source_not_unique"
        ]
        self.assertEqual(authority_review, [])


if __name__ == "__main__":
    unittest.main()
